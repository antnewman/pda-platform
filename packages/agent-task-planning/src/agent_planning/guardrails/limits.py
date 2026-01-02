"""Guardrail configuration and limits."""

from typing import Optional
from pydantic import BaseModel, Field


class GuardrailViolation(Exception):
    """Raised when a guardrail is violated."""
    pass


class GuardrailConfig(BaseModel):
    """
    Configuration for execution guardrails.

    All limits are non-bypassable once set.

    Attributes:
        max_tasks: Maximum number of tasks allowed per objective
        max_iterations: Maximum execution loop iterations
        max_cost_usd: Maximum spend in USD
        timeout_seconds: Maximum execution time
        max_retries_per_task: Maximum retry attempts per task
        require_approval_for: Actions requiring human approval
    """

    max_tasks: int = Field(default=15, ge=1, le=100)
    max_iterations: int = Field(default=50, ge=1, le=500)
    max_cost_usd: float = Field(default=5.0, ge=0.0)
    timeout_seconds: float = Field(default=300.0, ge=1.0)
    max_retries_per_task: int = Field(default=3, ge=0, le=10)
    require_approval_for: list[str] = Field(default_factory=list)

    # Content validation
    blocked_patterns: list[str] = Field(default_factory=list)
    allowed_tools: Optional[list[str]] = None

    # Confidence extraction settings
    confidence_enabled: bool = False
    confidence_samples: int = Field(default=5, ge=1, le=20)
    confidence_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    confidence_early_stop_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    confidence_review_thresholds: dict[str, float] = Field(
        default_factory=lambda: {
            "none": 0.8,           # >= 0.8: no review
            "spot_check": 0.6,    # >= 0.6: spot check
            "detailed": 0.4,      # >= 0.4: detailed review
            # < 0.4: expert required
        }
    )

    def requires_approval(self, action: str) -> bool:
        """Check if an action requires human approval."""
        action_lower = action.lower()
        return any(
            keyword in action_lower
            for keyword in self.require_approval_for
        )
