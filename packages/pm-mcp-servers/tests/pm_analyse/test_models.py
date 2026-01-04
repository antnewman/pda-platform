"""
Tests for PM-Analyse data models.

Tests all data model classes, validation, and to_dict() serialization.
"""

from datetime import date, datetime, timedelta

import pytest

from pm_mcp_servers.pm_analyse.models import (
    AnalysisDepth,
    AnalysisMetadata,
    BaselineVariance,
    Evidence,
    Forecast,
    ForecastMethod,
    HealthAssessment,
    HealthDimension,
    HealthStatus,
    Mitigation,
    Outlier,
    Risk,
    RiskCategory,
    Severity,
    TrendDirection,
)


class TestEvidence:
    """Tests for Evidence model."""

    def test_evidence_creation(self):
        """Test creating evidence object."""
        ev = Evidence(
            source="test_source",
            description="Test description",
            data_point="value=100",
            confidence=0.95
        )
        assert ev.source == "test_source"
        assert ev.description == "Test description"
        assert ev.data_point == "value=100"
        assert ev.confidence == 0.95

    def test_evidence_to_dict(self):
        """Test evidence serialization."""
        ev = Evidence(
            source="analysis",
            description="Test",
            data_point="x=5",
            confidence=0.8
        )
        data = ev.to_dict()
        assert data["source"] == "analysis"
        assert data["description"] == "Test"
        assert data["data_point"] == "x=5"
        assert data["confidence"] == 0.8

    def test_evidence_optional_fields(self):
        """Test evidence with optional fields."""
        ev = Evidence(source="test", description="desc")
        assert ev.data_point is None
        assert ev.confidence == 1.0


class TestRisk:
    """Tests for Risk model."""

    def test_risk_creation(self):
        """Test creating risk object."""
        risk = Risk(
            id="risk-1",
            name="Test Risk",
            description="Risk description",
            category=RiskCategory.SCHEDULE,
            probability=4,
            impact=5,
            score=20,
            confidence=0.90
        )
        assert risk.id == "risk-1"
        assert risk.probability == 4
        assert risk.impact == 5
        assert risk.score == 20

    def test_risk_severity_calculation(self):
        """Test severity is derived from score."""
        risk = Risk(
            id="r1", name="Critical", description="", category=RiskCategory.SCHEDULE,
            probability=5, impact=5, score=25, confidence=0.9
        )
        assert risk.severity == Severity.CRITICAL

        risk2 = Risk(
            id="r2", name="High", description="", category=RiskCategory.COST,
            probability=5, impact=3, score=15, confidence=0.9
        )
        assert risk2.severity == Severity.HIGH

        risk3 = Risk(
            id="r3", name="Medium", description="", category=RiskCategory.RESOURCE,
            probability=3, impact=3, score=9, confidence=0.9
        )
        assert risk3.severity == Severity.MEDIUM

    def test_risk_validation_probability(self):
        """Test probability must be 1-5."""
        with pytest.raises(ValueError, match="Probability must be between 1 and 5"):
            Risk(
                id="r", name="Bad", description="", category=RiskCategory.SCHEDULE,
                probability=6, impact=3, score=18, confidence=0.9
            )

        with pytest.raises(ValueError, match="Probability must be between 1 and 5"):
            Risk(
                id="r", name="Bad", description="", category=RiskCategory.SCHEDULE,
                probability=0, impact=3, score=0, confidence=0.9
            )

    def test_risk_validation_impact(self):
        """Test impact must be 1-5."""
        with pytest.raises(ValueError, match="Impact must be between 1 and 5"):
            Risk(
                id="r", name="Bad", description="", category=RiskCategory.SCHEDULE,
                probability=3, impact=10, score=30, confidence=0.9
            )

    def test_risk_validation_confidence(self):
        """Test confidence must be 0.0-1.0."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Risk(
                id="r", name="Bad", description="", category=RiskCategory.SCHEDULE,
                probability=3, impact=3, score=9, confidence=1.5
            )

    def test_risk_to_dict(self):
        """Test risk serialization."""
        risk = Risk(
            id="risk-1",
            name="Schedule Risk",
            description="Task delayed",
            category=RiskCategory.SCHEDULE,
            probability=4,
            impact=4,
            score=16,
            confidence=0.85,
            evidence=[Evidence(source="test", description="data", confidence=0.9)],
            related_tasks=["task-1", "task-2"],
            suggested_mitigation="Add resources"
        )
        data = risk.to_dict()
        assert data["id"] == "risk-1"
        assert data["category"] == "schedule"
        assert data["severity"] == "high"
        assert len(data["evidence"]) == 1
        assert len(data["related_tasks"]) == 2


class TestMitigation:
    """Tests for Mitigation model."""

    def test_mitigation_creation(self):
        """Test creating mitigation object."""
        mit = Mitigation(
            id="mit-1",
            risk_id="risk-1",
            strategy="Fast-track",
            description="Accelerate schedule",
            effort="high",
            effectiveness=0.75,
            confidence=0.80,
            implementation_steps=["Step 1", "Step 2"],
            resource_requirements=["PM", "Team"],
            timeline_days=14
        )
        assert mit.effort == "high"
        assert mit.effectiveness == 0.75
        assert len(mit.implementation_steps) == 2

    def test_mitigation_validation_effectiveness(self):
        """Test effectiveness must be 0.0-1.0."""
        with pytest.raises(ValueError, match="Effectiveness must be between 0.0 and 1.0"):
            Mitigation(
                id="m", risk_id="r", strategy="s", description="d",
                effort="low", effectiveness=1.5, confidence=0.8
            )

    def test_mitigation_validation_confidence(self):
        """Test confidence must be 0.0-1.0."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Mitigation(
                id="m", risk_id="r", strategy="s", description="d",
                effort="low", effectiveness=0.7, confidence=2.0
            )

    def test_mitigation_validation_effort(self):
        """Test effort must be low/medium/high."""
        with pytest.raises(ValueError, match="Effort must be low/medium/high"):
            Mitigation(
                id="m", risk_id="r", strategy="s", description="d",
                effort="extreme", effectiveness=0.7, confidence=0.8
            )

    def test_mitigation_to_dict(self):
        """Test mitigation serialization."""
        mit = Mitigation(
            id="mit-1",
            risk_id="risk-1",
            strategy="Test",
            description="Desc",
            effort="medium",
            effectiveness=0.8,
            confidence=0.9,
            timeline_days=7
        )
        data = mit.to_dict()
        assert data["effort"] == "medium"
        assert data["timeline_days"] == 7


class TestOutlier:
    """Tests for Outlier model."""

    def test_outlier_creation(self):
        """Test creating outlier object."""
        outlier = Outlier(
            id="out-1",
            task_id="task-1",
            task_name="Task",
            field="duration",
            value=100,
            expected_range=(10, 30),
            deviation_score=5.2,
            severity=Severity.HIGH,
            confidence=0.85,
            explanation="Duration too long"
        )
        assert outlier.field == "duration"
        assert outlier.deviation_score == 5.2

    def test_outlier_validation_confidence(self):
        """Test confidence validation."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Outlier(
                id="o", task_id="t", task_name="T", field="f", value=1,
                expected_range=(0, 10), deviation_score=1.0,
                severity=Severity.LOW, confidence=1.5, explanation="x"
            )

    def test_outlier_to_dict(self):
        """Test outlier serialization."""
        outlier = Outlier(
            id="out-1",
            task_id="t1",
            task_name="Task",
            field="progress",
            value=0,
            expected_range=(10, 90),
            deviation_score=2.5,
            severity=Severity.MEDIUM,
            confidence=0.8,
            explanation="No progress"
        )
        data = outlier.to_dict()
        assert data["field"] == "progress"
        assert data["expected_range"] == [10, 90]


class TestForecast:
    """Tests for Forecast model."""

    def test_forecast_creation(self):
        """Test creating forecast object."""
        today = date.today()
        forecast = Forecast(
            forecast_date=today + timedelta(days=30),
            confidence_interval=(today + timedelta(days=25), today + timedelta(days=35)),
            confidence_level=0.80,
            method=ForecastMethod.EARNED_VALUE,
            variance_days=5,
            on_track=True,
            confidence=0.85
        )
        assert forecast.variance_days == 5
        assert forecast.on_track is True

    def test_forecast_validation_confidence_level(self):
        """Test confidence_level validation."""
        with pytest.raises(ValueError, match="Confidence level must be between 0.0 and 1.0"):
            Forecast(
                forecast_date=date.today(),
                confidence_interval=(date.today(), date.today()),
                confidence_level=1.5,
                method=ForecastMethod.EARNED_VALUE,
                variance_days=0,
                on_track=True,
                confidence=0.8
            )

    def test_forecast_validation_confidence(self):
        """Test confidence validation."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Forecast(
                forecast_date=date.today(),
                confidence_interval=(date.today(), date.today()),
                confidence_level=0.8,
                method=ForecastMethod.EARNED_VALUE,
                variance_days=0,
                on_track=True,
                confidence=-0.1
            )

    def test_forecast_to_dict(self):
        """Test forecast serialization."""
        today = date.today()
        forecast = Forecast(
            forecast_date=today + timedelta(days=10),
            confidence_interval=(today + timedelta(days=8), today + timedelta(days=12)),
            confidence_level=0.80,
            method=ForecastMethod.MONTE_CARLO,
            variance_days=2,
            on_track=True,
            confidence=0.75,
            scenarios={"optimistic": today + timedelta(days=5)}
        )
        data = forecast.to_dict()
        assert data["method"] == "monte_carlo"
        assert "scenarios" in data


class TestHealthDimension:
    """Tests for HealthDimension model."""

    def test_health_dimension_creation(self):
        """Test creating health dimension."""
        dim = HealthDimension(
            name="Schedule",
            score=85.0,
            status=HealthStatus.HEALTHY,
            trend=TrendDirection.STABLE,
            weight=0.2
        )
        assert dim.score == 85.0
        assert dim.status == HealthStatus.HEALTHY

    def test_health_dimension_validation_score(self):
        """Test score must be 0-100."""
        with pytest.raises(ValueError, match="Score must be between 0.0 and 100.0"):
            HealthDimension(
                name="Test",
                score=150.0,
                status=HealthStatus.HEALTHY,
                trend=TrendDirection.STABLE
            )

    def test_health_dimension_validation_weight(self):
        """Test weight must be 0-1."""
        with pytest.raises(ValueError, match="Weight must be between 0.0 and 1.0"):
            HealthDimension(
                name="Test",
                score=80.0,
                status=HealthStatus.HEALTHY,
                trend=TrendDirection.STABLE,
                weight=1.5
            )

    def test_health_dimension_to_dict(self):
        """Test dimension serialization."""
        dim = HealthDimension(
            name="Cost",
            score=70.0,
            status=HealthStatus.AT_RISK,
            trend=TrendDirection.DECLINING,
            issues=["Over budget"],
            weight=0.25
        )
        data = dim.to_dict()
        assert data["name"] == "Cost"
        assert data["status"] == "at_risk"
        assert data["trend"] == "declining"


class TestHealthAssessment:
    """Tests for HealthAssessment model."""

    def test_health_assessment_creation(self):
        """Test creating health assessment."""
        dims = [
            HealthDimension(
                name="Schedule",
                score=80.0,
                status=HealthStatus.HEALTHY,
                trend=TrendDirection.STABLE
            )
        ]
        assessment = HealthAssessment(
            overall_score=80.0,
            overall_status=HealthStatus.HEALTHY,
            dimensions=dims,
            top_concerns=[],
            recommendations=["Continue monitoring"],
            confidence=0.85
        )
        assert assessment.overall_score == 80.0
        assert len(assessment.dimensions) == 1

    def test_health_assessment_validation_score(self):
        """Test overall_score validation."""
        with pytest.raises(ValueError, match="Overall score must be between 0.0 and 100.0"):
            HealthAssessment(
                overall_score=120.0,
                overall_status=HealthStatus.HEALTHY,
                dimensions=[],
                top_concerns=[],
                recommendations=[],
                confidence=0.8
            )

    def test_health_assessment_validation_confidence(self):
        """Test confidence validation."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            HealthAssessment(
                overall_score=80.0,
                overall_status=HealthStatus.HEALTHY,
                dimensions=[],
                top_concerns=[],
                recommendations=[],
                confidence=1.2
            )

    def test_health_assessment_to_dict(self):
        """Test assessment serialization."""
        dims = [
            HealthDimension(
                name="Schedule",
                score=75.0,
                status=HealthStatus.HEALTHY,
                trend=TrendDirection.IMPROVING
            )
        ]
        assessment = HealthAssessment(
            overall_score=75.0,
            overall_status=HealthStatus.HEALTHY,
            dimensions=dims,
            top_concerns=["None"],
            recommendations=["Continue"],
            confidence=0.9
        )
        data = assessment.to_dict()
        assert data["overall_status"] == "healthy"
        assert len(data["dimensions"]) == 1


class TestBaselineVariance:
    """Tests for BaselineVariance model."""

    def test_baseline_variance_creation(self):
        """Test creating baseline variance."""
        var = BaselineVariance(
            task_id="task-1",
            task_name="Task",
            field="finish_date",
            baseline_value=date.today(),
            current_value=date.today() + timedelta(days=10),
            variance=10.0,
            variance_percent=20.0,
            severity=Severity.HIGH,
            explanation="Slipped 10 days"
        )
        assert var.variance == 10.0
        assert var.variance_percent == 20.0

    def test_baseline_variance_to_dict(self):
        """Test variance serialization."""
        var = BaselineVariance(
            task_id="t1",
            task_name="Task",
            field="duration",
            baseline_value=10,
            current_value=15,
            variance=5.0,
            variance_percent=50.0,
            severity=Severity.CRITICAL,
            explanation="Duration increased"
        )
        data = var.to_dict()
        assert data["field"] == "duration"
        assert data["severity"] == "critical"


class TestAnalysisMetadata:
    """Tests for AnalysisMetadata model."""

    def test_analysis_metadata_creation(self):
        """Test creating analysis metadata."""
        meta = AnalysisMetadata(
            analysis_id="analysis-1",
            analysis_type="risk_identification",
            started_at=datetime.utcnow(),
            depth=AnalysisDepth.STANDARD,
            tasks_analyzed=50,
            overall_confidence=0.85
        )
        assert meta.analysis_type == "risk_identification"
        assert meta.tasks_analyzed == 50

    def test_analysis_metadata_validation_confidence(self):
        """Test overall_confidence validation."""
        with pytest.raises(ValueError, match="Overall confidence must be between 0.0 and 1.0"):
            AnalysisMetadata(
                analysis_id="a1",
                analysis_type="test",
                started_at=datetime.utcnow(),
                overall_confidence=1.5
            )

    def test_analysis_metadata_complete(self):
        """Test complete() method."""
        meta = AnalysisMetadata(
            analysis_id="a1",
            analysis_type="test",
            started_at=datetime.utcnow()
        )
        assert meta.completed_at is None
        assert meta.duration_ms is None

        meta.complete()
        assert meta.completed_at is not None
        assert meta.duration_ms is not None
        assert meta.duration_ms >= 0

    def test_analysis_metadata_to_dict(self):
        """Test metadata serialization."""
        meta = AnalysisMetadata(
            analysis_id="a1",
            analysis_type="forecast",
            started_at=datetime.utcnow(),
            depth=AnalysisDepth.DEEP,
            tasks_analyzed=100,
            overall_confidence=0.9
        )
        meta.complete()
        data = meta.to_dict()
        assert data["analysis_type"] == "forecast"
        assert data["depth"] == "deep"
        assert "duration_ms" in data
