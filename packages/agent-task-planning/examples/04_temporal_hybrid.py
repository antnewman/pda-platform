#!/usr/bin/env python3
"""
Hybrid architecture: Deterministic orchestration with probabilistic subtasks.

This pattern wraps LLM-based planning inside a deterministic workflow engine
(Temporal). The outer workflow guarantees execution order and provides
reliability, while agents handle flexible subtasks.

This is the pattern used at Members of the PDA Task Force for production systems.

Note: Requires temporalio package: pip install temporalio
"""

from dataclasses import dataclass
from datetime import timedelta

# Note: This is a reference implementation.
# For actual use, install temporalio and configure a Temporal server.

try:
    from temporalio import workflow, activity
    from temporalio.client import Client
    from temporalio.worker import Worker
    TEMPORAL_AVAILABLE = True
except ImportError:
    TEMPORAL_AVAILABLE = False
    print("Temporal not installed. This example shows the pattern only.")
    print("Install with: pip install temporalio")


@dataclass
class ResearchInput:
    """Input for the research workflow."""
    topic: str
    max_sources: int = 5


@dataclass
class ResearchOutput:
    """Output from the research workflow."""
    summary: str
    sources: list[str]
    confidence: float


if TEMPORAL_AVAILABLE:

    @activity.defn
    async def gather_sources(topic: str, max_sources: int) -> list[str]:
        """
        Deterministic activity: Always gathers sources the same way.

        In production, this would call a search API with fixed parameters.
        """
        # Simulated source gathering
        return [
            f"https://example.com/article/{topic.replace(' ', '-')}/{i}"
            for i in range(max_sources)
        ]


    @activity.defn
    async def agent_analyse(sources: list[str], topic: str) -> dict:
        """
        Probabilistic activity: Agent decides how to analyse.

        This is where the LLM-based planning happens, wrapped in
        a deterministic activity with timeout and retry policies.
        """
        from agent_planning import TodoListPlanner
        from agent_planning.providers import AnthropicProvider
        import os

        provider = AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))
        planner = TodoListPlanner(provider=provider)

        result = await planner.execute(
            f"Analyse these sources about '{topic}' and extract key insights: "
            f"{', '.join(sources)}"
        )

        return {
            "analysis": result.final_output,
            "tasks_completed": len([t for t in result.tasks if t.status.value == "completed"]),
            "cost": result.total_cost_usd,
        }


    @activity.defn
    async def format_report(analysis: dict, topic: str) -> ResearchOutput:
        """
        Deterministic activity: Always formats reports the same way.

        No LLM involved, just structured formatting.
        """
        return ResearchOutput(
            summary=analysis.get("analysis", "No analysis available"),
            sources=analysis.get("sources", []),
            confidence=0.85 if analysis.get("tasks_completed", 0) > 3 else 0.5,
        )


    @workflow.defn
    class ResearchWorkflow:
        """
        Deterministic workflow with probabilistic subtask.

        Benefits:
        - Outer workflow is auditable and reproducible
        - Timeouts prevent runaway agent behaviour
        - Failed activities can be retried with backoff
        - State is persisted, survives process restarts
        - Agent flexibility where needed, determinism where required
        """

        @workflow.run
        async def run(self, input: ResearchInput) -> ResearchOutput:
            # Step 1: Deterministic source gathering
            sources = await workflow.execute_activity(
                gather_sources,
                args=[input.topic, input.max_sources],
                start_to_close_timeout=timedelta(minutes=2),
            )

            # Step 2: Probabilistic analysis (agent plans how to analyse)
            analysis = await workflow.execute_activity(
                agent_analyse,
                args=[sources, input.topic],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy={
                    "maximum_attempts": 3,
                    "initial_interval": timedelta(seconds=1),
                    "maximum_interval": timedelta(seconds=30),
                },
            )

            # Step 3: Deterministic formatting
            report = await workflow.execute_activity(
                format_report,
                args=[analysis, input.topic],
                start_to_close_timeout=timedelta(minutes=1),
            )

            return report


async def main():
    """Run the hybrid workflow."""
    if not TEMPORAL_AVAILABLE:
        print("\nTo run this example:")
        print("1. pip install temporalio")
        print("2. Start a Temporal server (or use Temporal Cloud)")
        print("3. Run this script again")
        return

    # Connect to Temporal
    client = await Client.connect("localhost:7233")

    # Start the workflow
    result = await client.execute_workflow(
        ResearchWorkflow.run,
        ResearchInput(topic="AI agent planning", max_sources=3),
        id="research-ai-planning",
        task_queue="research-queue",
    )

    print(f"Research complete!")
    print(f"Summary: {result.summary[:200]}...")
    print(f"Confidence: {result.confidence}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
