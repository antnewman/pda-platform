"""Tests for Risk model."""

import pytest
from datetime import date
from uuid import uuid4

from pm_data_tools.models import Risk, RiskStatus, RiskCategory, SourceInfo


@pytest.fixture
def source_info() -> SourceInfo:
    """Test source info."""
    return SourceInfo(tool="test")


class TestRiskStatus:
    """Tests for RiskStatus enum."""

    def test_enum_values(self) -> None:
        """Test RiskStatus enum values."""
        assert RiskStatus.IDENTIFIED.value == "identified"
        assert RiskStatus.ANALYSED.value == "analysed"
        assert RiskStatus.MITIGATING.value == "mitigating"


class TestRiskCategory:
    """Tests for RiskCategory enum."""

    def test_enum_values(self) -> None:
        """Test RiskCategory enum values."""
        assert RiskCategory.TECHNICAL.value == "technical"
        assert RiskCategory.COMMERCIAL.value == "commercial"
        assert RiskCategory.SCHEDULE.value == "schedule"


class TestRisk:
    """Tests for Risk model."""

    def test_creation_minimal(self, source_info: SourceInfo) -> None:
        """Test Risk creation with minimal fields."""
        risk = Risk(
            id=uuid4(),
            name="Test Risk",
            source=source_info,
        )

        assert risk.name == "Test Risk"
        assert risk.category == RiskCategory.TECHNICAL
        assert risk.status == RiskStatus.IDENTIFIED

    def test_creation_complete(self, source_info: SourceInfo) -> None:
        """Test Risk creation with all fields."""
        task_id = uuid4()

        risk = Risk(
            id=uuid4(),
            name="Budget Overrun",
            source=source_info,
            description="Risk of budget overrun",
            cause="Underestimated costs",
            effect="Project delays",
            category=RiskCategory.COMMERCIAL,
            status=RiskStatus.MITIGATING,
            probability=4,
            impact=5,
            mitigation="Regular cost reviews",
            owner="Project Manager",
            identified_date=date(2025, 1, 1),
            related_task_ids=[task_id],
        )

        assert risk.name == "Budget Overrun"
        assert risk.probability == 4
        assert risk.impact == 5
        assert risk.owner == "Project Manager"

    def test_score_calculation(self, source_info: SourceInfo) -> None:
        """Test risk score calculation."""
        risk = Risk(
            id=uuid4(),
            name="Test",
            source=source_info,
            probability=4,
            impact=5,
        )

        assert risk.score == 20

    def test_score_none_when_missing(self, source_info: SourceInfo) -> None:
        """Test score returns None when data missing."""
        risk = Risk(
            id=uuid4(),
            name="Test",
            source=source_info,
            probability=4,
        )

        assert risk.score is None

    def test_is_high_risk(self, source_info: SourceInfo) -> None:
        """Test is_high_risk property."""
        risk = Risk(
            id=uuid4(),
            name="Test",
            source=source_info,
            probability=5,
            impact=5,
        )

        assert risk.is_high_risk is True
        assert risk.is_medium_risk is False
        assert risk.is_low_risk is False

    def test_is_medium_risk(self, source_info: SourceInfo) -> None:
        """Test is_medium_risk property."""
        risk = Risk(
            id=uuid4(),
            name="Test",
            source=source_info,
            probability=3,
            impact=3,
        )

        assert risk.is_high_risk is False
        assert risk.is_medium_risk is True
        assert risk.is_low_risk is False

    def test_is_low_risk(self, source_info: SourceInfo) -> None:
        """Test is_low_risk property."""
        risk = Risk(
            id=uuid4(),
            name="Test",
            source=source_info,
            probability=1,
            impact=2,
        )

        assert risk.is_high_risk is False
        assert risk.is_medium_risk is False
        assert risk.is_low_risk is True

    def test_str_representation(self, source_info: SourceInfo) -> None:
        """Test string representation."""
        risk = Risk(
            id=uuid4(),
            name="Test Risk",
            source=source_info,
            category=RiskCategory.SCHEDULE,
            probability=3,
            impact=4,
        )

        result = str(risk)
        assert "Test Risk" in result
        assert "schedule" in result
        assert "score=12" in result
