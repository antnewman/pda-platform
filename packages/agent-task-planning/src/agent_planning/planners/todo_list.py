"""To-Do List planner implementation."""

import asyncio
import time
from typing import Optional

import structlog

from agent_planning.core.planner import BasePlanner
from agent_planning.core.state import ExecutionResult, TaskState
from agent_planning.core.task import Task, TaskStatus
from agent_planning.guardrails.limits import GuardrailConfig, GuardrailViolation
from agent_planning.providers.base import BaseProvider

logger = structlog.get_logger()


PLANNING_SYSTEM_PROMPT = """You maintain a structured to-do list for complex work.

CONSTRAINTS:
- Maximum {max_tasks} tasks per objective
- Each task must be achievable with your available tools
- Do not plan actions you cannot execute
- If a task fails 3 times, mark it failed and continue
- If you are uncertain, ask for clarification before planning

FORMAT (use these symbols in your responses):
- ☐ pending task
- ◐ in-progress task
- ✓ completed task
- ✗ failed task
- ⊘ blocked task

RULES:
- Create a plan before starting multi-step work
- Update the list after completing each step
- If you discover new requirements, add tasks
- If a task becomes irrelevant, mark completed with "[skipped]"
- Never plan more than 2 tasks ahead in detail
- Stop and report if you detect you're making no progress

SAFETY:
- Do not execute irreversible actions without confirmation
- Report estimated cost/time before expensive operations
- Surface any uncertainties in your plan

When responding, always show the current task list state."""


class TodoListPlanner(BasePlanner):
    """
    Planner that maintains an explicit to-do list with status tracking.

    This is the recommended pattern for multi-step workflows requiring
    visibility and control.

    Example:
        provider = AnthropicProvider(api_key="...")
        planner = TodoListPlanner(provider=provider)
        result = await planner.execute("Research and summarise AI trends")
    """

    def __init__(
        self,
        provider: BaseProvider,
        guardrails: Optional[GuardrailConfig] = None,
        system_prompt: Optional[str] = None,
    ):
        """
        Initialise the TodoListPlanner.

        Args:
            provider: LLM provider to use
            guardrails: Guardrail configuration
            system_prompt: Custom system prompt (uses default if not provided)
        """
        super().__init__(provider, guardrails)
        self._system_prompt = system_prompt

    @property
    def system_prompt(self) -> str:
        """Get the system prompt with guardrail values interpolated."""
        if self._system_prompt:
            return self._system_prompt
        return PLANNING_SYSTEM_PROMPT.format(
            max_tasks=self.guardrails.max_tasks,
        )

    async def execute(self, objective: str) -> ExecutionResult:
        """
        Execute the planning process for the given objective.

        Args:
            objective: The task or goal to accomplish

        Returns:
            ExecutionResult containing the outcome
        """
        start_time = time.time()
        state = TaskState(objective=objective)
        total_tokens = 0
        total_cost = 0.0

        log = logger.bind(objective=objective[:50])
        log.info("Starting execution")

        try:
            # Initial planning
            state = await self.plan(objective, state)
            log.info("Initial plan created", task_count=len(state.tasks))

            # Execute until complete or guardrails hit
            while not state.is_complete:
                state.iteration += 1

                # Check guardrails
                self._check_guardrails(state, total_cost, start_time)

                # Get next task
                task = state.get_next_pending()
                if task is None:
                    # No pending tasks but not complete means blocked
                    blocked = [t for t in state.tasks if t.status == TaskStatus.BLOCKED]
                    if blocked:
                        log.warning("Execution blocked", blocked_tasks=len(blocked))
                        break
                    # Check for in-progress tasks
                    if state.get_in_progress():
                        await asyncio.sleep(0.1)
                        continue
                    break

                # Execute the task
                task.mark_in_progress()
                log.info("Executing task", task=task.content[:50], attempt=task.attempts)

                try:
                    result, tokens, cost = await self._execute_task(task, state)
                    total_tokens += tokens
                    total_cost += cost

                    task.mark_completed(result)
                    log.info("Task completed", task=task.content[:50])

                except Exception as e:
                    task.mark_failed(str(e))
                    log.warning("Task failed", task=task.content[:50], error=str(e))

                    # Retry logic
                    if task.attempts < 3:
                        task.status = TaskStatus.PENDING

                # Replan if needed
                if self._should_replan(state):
                    state = await self.plan(objective, state)

            # Generate final output
            final_output = await self._synthesise_output(state)
            duration = time.time() - start_time

            success = all(
                t.status in {TaskStatus.COMPLETED, TaskStatus.SKIPPED}
                for t in state.tasks
            )

            log.info(
                "Execution complete",
                success=success,
                iterations=state.iteration,
                tokens=total_tokens,
            )

            return ExecutionResult(
                success=success,
                tasks=state.tasks,
                total_iterations=state.iteration,
                total_tokens=total_tokens,
                total_cost_usd=total_cost,
                duration_seconds=duration,
                final_output=final_output,
            )

        except GuardrailViolation as e:
            duration = time.time() - start_time
            log.error("Guardrail violation", error=str(e))
            return ExecutionResult(
                success=False,
                tasks=state.tasks,
                total_iterations=state.iteration,
                total_tokens=total_tokens,
                total_cost_usd=total_cost,
                duration_seconds=duration,
                error=str(e),
            )

        except Exception as e:
            duration = time.time() - start_time
            log.exception("Unexpected error")
            return ExecutionResult(
                success=False,
                tasks=state.tasks,
                total_iterations=state.iteration,
                total_tokens=total_tokens,
                total_cost_usd=total_cost,
                duration_seconds=duration,
                error=str(e),
            )

    async def plan(self, objective: str, state: TaskState) -> TaskState:
        """
        Generate or update a plan for the objective.

        Args:
            objective: The task or goal
            state: Current task state

        Returns:
            Updated TaskState with new/modified tasks
        """
        prompt = f"""Objective: {objective}

Current state:
{state.to_prompt_context() if state.tasks else "No tasks yet."}

Create or update the task list. Output ONLY a JSON array of tasks:
[
  {{"content": "task description", "status": "pending"}},
  ...
]"""

        response = await self.provider.complete(
            messages=[{"role": "user", "content": prompt}],
            system=self.system_prompt,
        )

        # Parse tasks from response
        tasks = self._parse_tasks(response.content)

        # Merge with existing state
        for task_data in tasks:
            # Check if task already exists
            existing = None
            for t in state.tasks:
                if t.content == task_data["content"]:
                    existing = t
                    break

            if existing is None:
                state.add_task(task_data["content"])

        return state

    def _check_guardrails(
        self,
        state: TaskState,
        current_cost: float,
        start_time: float,
    ) -> None:
        """Check all guardrails and raise if violated."""
        if state.iteration >= self.guardrails.max_iterations:
            raise GuardrailViolation(
                f"Maximum iterations ({self.guardrails.max_iterations}) exceeded"
            )

        if len(state.tasks) > self.guardrails.max_tasks:
            raise GuardrailViolation(
                f"Maximum tasks ({self.guardrails.max_tasks}) exceeded"
            )

        if current_cost >= self.guardrails.max_cost_usd:
            raise GuardrailViolation(
                f"Maximum cost (${self.guardrails.max_cost_usd}) exceeded"
            )

        elapsed = time.time() - start_time
        if elapsed >= self.guardrails.timeout_seconds:
            raise GuardrailViolation(
                f"Timeout ({self.guardrails.timeout_seconds}s) exceeded"
            )

    def _should_replan(self, state: TaskState) -> bool:
        """Determine if replanning is needed."""
        # Replan every 5 completed tasks
        completed = len(state.get_completed())
        return completed > 0 and completed % 5 == 0

    async def _execute_task(
        self,
        task: Task,
        state: TaskState,
    ) -> tuple[str, int, float]:
        """
        Execute a single task.

        Returns:
            Tuple of (result, tokens_used, cost_usd)
        """
        prompt = f"""You are executing task: {task.content}

Context (completed tasks):
{chr(10).join(f"- {t.content}: {t.result}" for t in state.get_completed())}

Execute this task and provide the result. Be concise and factual."""

        response = await self.provider.complete(
            messages=[{"role": "user", "content": prompt}],
            system=self.system_prompt,
        )

        return response.content, response.tokens_used, response.cost_usd

    async def _synthesise_output(self, state: TaskState) -> str:
        """Synthesise a final output from completed tasks."""
        prompt = f"""Objective: {state.objective}

Completed tasks and results:
{chr(10).join(f"- {t.content}: {t.result}" for t in state.get_completed())}

Provide a clear, concise summary addressing the original objective."""

        response = await self.provider.complete(
            messages=[{"role": "user", "content": prompt}],
            system="You are a helpful assistant. Summarise the work done concisely.",
        )

        return response.content

    def _parse_tasks(self, content: str) -> list[dict]:
        """Parse tasks from LLM response."""
        import json
        import re

        # Try to find JSON array in response
        json_match = re.search(r'\[[\s\S]*\]', content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback: parse line by line
        tasks = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Remove status symbols
                for symbol in ['☐', '◐', '✓', '✗', '⊘', '-', '*', '•']:
                    line = line.lstrip(symbol).strip()
                if line:
                    tasks.append({"content": line, "status": "pending"})

        return tasks
