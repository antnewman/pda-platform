"""Base planner interface."""

from abc import ABC, abstractmethod
from typing import Optional

from agent_planning.core.state import ExecutionResult, TaskState
from agent_planning.guardrails.limits import GuardrailConfig


class BasePlanner(ABC):
    """
    Abstract base class for all planners.

    Subclasses must implement the execute method.
    """

    def __init__(
        self,
        provider: "BaseProvider",  # type: ignore  # Forward reference
        guardrails: Optional[GuardrailConfig] = None,
    ):
        """
        Initialise the planner.

        Args:
            provider: The LLM provider to use
            guardrails: Optional guardrail configuration
        """
        self.provider = provider
        self.guardrails = guardrails or GuardrailConfig()

    @abstractmethod
    async def execute(self, objective: str) -> ExecutionResult:
        """
        Execute the planning process for the given objective.

        Args:
            objective: The task or goal to accomplish

        Returns:
            ExecutionResult containing the outcome
        """
        pass

    @abstractmethod
    async def plan(self, objective: str, state: TaskState) -> TaskState:
        """
        Generate or update a plan for the objective.

        Args:
            objective: The task or goal
            state: Current task state

        Returns:
            Updated TaskState with new/modified tasks
        """
        pass
