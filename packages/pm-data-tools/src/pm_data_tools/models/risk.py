"""Risk model for project risk register.

Risks represent identified threats or opportunities to project objectives,
with probability, impact, and mitigation tracking aligned with GMPP standards.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional
from uuid import UUID

from .base import SourceInfo, CustomField


class RiskStatus(Enum):
    """Risk status."""

    IDENTIFIED = "identified"
    ANALYSED = "analysed"
    MITIGATING = "mitigating"
    CLOSED = "closed"
    ACCEPTED = "accepted"
    MATERIALISED = "materialised"


class RiskCategory(Enum):
    """Risk categories (aligned with NISTA/GMPP)."""

    TECHNICAL = "technical"
    COMMERCIAL = "commercial"
    SCHEDULE = "schedule"
    RESOURCE = "resource"
    EXTERNAL = "external"
    GOVERNANCE = "governance"


@dataclass(frozen=True)
class Risk:
    """Risk register entry.

    Represents an identified risk with probability/impact assessment,
    mitigation plans, and ownership tracking. Aligned with UK Government
    GMPP risk management standards.
    """

    # Identity
    id: UUID
    name: str
    source: SourceInfo

    # Description
    description: Optional[str] = None
    cause: Optional[str] = None
    effect: Optional[str] = None

    # Classification
    category: RiskCategory = RiskCategory.TECHNICAL
    status: RiskStatus = RiskStatus.IDENTIFIED

    # Assessment (1-5 scale, aligned with GMPP)
    probability: Optional[int] = None  # 1=Very Low, 5=Very High
    impact: Optional[int] = None  # 1=Very Low, 5=Very High

    # Response
    mitigation: Optional[str] = None
    contingency: Optional[str] = None
    owner: Optional[str] = None

    # Dates
    identified_date: Optional[date] = None
    target_resolution_date: Optional[date] = None

    # Linked tasks
    related_task_ids: list[UUID] = field(default_factory=list)

    # Extensions
    custom_fields: list[CustomField] = field(default_factory=list)

    def __str__(self) -> str:
        """String representation."""
        score_str = f" (score={self.score})" if self.score else ""
        return f"Risk({self.name}, {self.category.value}, {self.status.value}{score_str})"

    @property
    def score(self) -> Optional[int]:
        """Calculate risk score (probability × impact).

        Returns:
            Risk score (1-25), or None if probability or impact missing.
        """
        if self.probability is not None and self.impact is not None:
            return self.probability * self.impact
        return None

    @property
    def is_high_risk(self) -> bool:
        """Check if risk is high severity (score >= 15).

        Returns:
            True if risk score is 15 or higher.
        """
        return self.score is not None and self.score >= 15

    @property
    def is_medium_risk(self) -> bool:
        """Check if risk is medium severity (score 6-14).

        Returns:
            True if risk score is between 6 and 14.
        """
        return self.score is not None and 6 <= self.score < 15

    @property
    def is_low_risk(self) -> bool:
        """Check if risk is low severity (score <= 5).

        Returns:
            True if risk score is 5 or lower.
        """
        return self.score is not None and self.score <= 5
