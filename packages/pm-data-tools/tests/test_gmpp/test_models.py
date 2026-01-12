"""Unit tests for GMPP data models."""

import pytest
from datetime import date, datetime
from decimal import Decimal

from pm_data_tools.gmpp.models import (
    QuarterPeriod,
    ReviewLevel,
    DCANarrative,
    FinancialPerformance,
    SchedulePerformance,
    BenefitsPerformance,
    QuarterlyReport,
)


def test_quarter_period_enum():
    """Test QuarterPeriod enum values."""
    assert QuarterPeriod.Q1 == "Q1"
    assert QuarterPeriod.Q2 == "Q2"
    assert QuarterPeriod.Q3 == "Q3"
    assert QuarterPeriod.Q4 == "Q4"


def test_review_level_enum():
    """Test ReviewLevel enum values."""
    assert ReviewLevel.NONE == "NONE"
    assert ReviewLevel.SPOT_CHECK == "SPOT_CHECK"
    assert ReviewLevel.DETAILED_REVIEW == "DETAILED_REVIEW"
    assert ReviewLevel.EXPERT_REQUIRED == "EXPERT_REQUIRED"


def test_dca_narrative_valid():
    """Test DCANarrative model with valid data."""
    narrative = DCANarrative(
        text=" ".join(["test"] * 150),  # ~150 words
        confidence=0.87,
        review_level=ReviewLevel.NONE,
        generated_at=datetime.utcnow(),
        samples_used=5
    )

    assert narrative.confidence == 0.87
    assert narrative.review_level == ReviewLevel.NONE
    assert narrative.samples_used == 5


def test_dca_narrative_word_count_validation():
    """Test DCANarrative validates word count."""
    # Too short (< 100 words)
    with pytest.raises(ValueError, match="too short"):
        DCANarrative(
            text="Too short",
            confidence=0.9,
            review_level=ReviewLevel.NONE,
            generated_at=datetime.utcnow(),
            samples_used=5
        )

    # Too long (> 250 words)
    with pytest.raises(ValueError, match="too long"):
        DCANarrative(
            text=" ".join(["test"] * 300),  # ~300 words
            confidence=0.9,
            review_level=ReviewLevel.NONE,
            generated_at=datetime.utcnow(),
            samples_used=5
        )


def test_financial_performance_valid():
    """Test FinancialPerformance model with valid data."""
    financial = FinancialPerformance(
        baseline_cost=Decimal("25.00"),
        forecast_cost=Decimal("24.30"),
        actual_cost=Decimal("18.50"),
        variance_percent=-2.8,
        variance_amount=Decimal("-0.70"),
        confidence=0.92
    )

    assert financial.baseline_cost == Decimal("25.00")
    assert financial.forecast_cost == Decimal("24.30")
    assert financial.variance_percent == -2.8


def test_financial_performance_positive_forecast():
    """Test FinancialPerformance validates positive forecast."""
    with pytest.raises(ValueError, match="must be positive"):
        FinancialPerformance(
            baseline_cost=Decimal("25.00"),
            forecast_cost=Decimal("0"),  # Invalid: must be positive
            variance_percent=-100,
            variance_amount=Decimal("-25.00"),
            confidence=0.9
        )


def test_schedule_performance_valid():
    """Test SchedulePerformance model with valid data."""
    schedule = SchedulePerformance(
        baseline_completion=date(2026, 3, 31),
        forecast_completion=date(2026, 5, 15),
        variance_weeks=6,
        critical_path_at_risk=True,
        confidence=0.88
    )

    assert schedule.variance_weeks == 6
    assert schedule.critical_path_at_risk is True


def test_benefits_performance_valid():
    """Test BenefitsPerformance model with valid data."""
    benefits = BenefitsPerformance(
        total_planned=Decimal("45.00"),
        realised_to_date=Decimal("18.00"),
        forecast_total=Decimal("43.50"),
        realisation_rate=0.40,
        confidence=0.85
    )

    assert benefits.total_planned == Decimal("45.00")
    assert benefits.realisation_rate == 0.40


def test_benefits_performance_realised_validation():
    """Test BenefitsPerformance validates realised doesn't exceed forecast."""
    with pytest.raises(ValueError, match="cannot exceed forecast"):
        BenefitsPerformance(
            total_planned=Decimal("45.00"),
            realised_to_date=Decimal("50.00"),  # Invalid: > forecast
            forecast_total=Decimal("43.50"),
            realisation_rate=1.0,
            confidence=0.85
        )


def test_quarterly_report_valid():
    """Test QuarterlyReport model with complete valid data."""
    # Create narratives
    narrative = DCANarrative(
        text=" ".join(["test"] * 150),
        confidence=0.87,
        review_level=ReviewLevel.NONE,
        generated_at=datetime.utcnow(),
        samples_used=5
    )

    # Create financial performance
    financial = FinancialPerformance(
        baseline_cost=Decimal("25.00"),
        forecast_cost=Decimal("24.30"),
        variance_percent=-2.8,
        variance_amount=Decimal("-0.70"),
        confidence=0.92
    )

    # Create schedule performance
    schedule = SchedulePerformance(
        baseline_completion=date(2026, 3, 31),
        forecast_completion=date(2026, 5, 15),
        variance_weeks=6,
        critical_path_at_risk=True,
        confidence=0.88
    )

    # Create benefits performance
    benefits = BenefitsPerformance(
        total_planned=Decimal("45.00"),
        realised_to_date=Decimal("18.00"),
        forecast_total=Decimal("43.50"),
        realisation_rate=0.40,
        confidence=0.85
    )

    # Create quarterly report
    report = QuarterlyReport(
        quarter=QuarterPeriod.Q2,
        financial_year="2025-26",
        reporting_date=date.today(),
        project_id="DFT-HSR-001",
        nista_project_code="DFT_0123_2025-Q2",
        project_name="High Speed Rail Phase 2",
        department="Department for Transport",
        sro_name="Jane Smith",
        sro_email="jane.smith@dft.gov.uk",
        dca_rating="AMBER",
        dca_narrative=narrative,
        financial=financial,
        schedule=schedule,
        benefits=benefits,
        cost_narrative=narrative,
        schedule_narrative=narrative,
        benefits_narrative=narrative,
        risk_narrative=narrative,
    )

    assert report.quarter == QuarterPeriod.Q2
    assert report.financial_year == "2025-26"
    assert report.project_name == "High Speed Rail Phase 2"
    assert report.dca_rating == "AMBER"


def test_quarterly_report_dca_change_rationale_required():
    """Test QuarterlyReport requires rationale when DCA changed."""
    narrative = DCANarrative(
        text=" ".join(["test"] * 150),
        confidence=0.87,
        review_level=ReviewLevel.NONE,
        generated_at=datetime.utcnow(),
        samples_used=5
    )

    financial = FinancialPerformance(
        baseline_cost=Decimal("25.00"),
        forecast_cost=Decimal("24.30"),
        variance_percent=-2.8,
        variance_amount=Decimal("-0.70"),
        confidence=0.92
    )

    schedule = SchedulePerformance(
        baseline_completion=date(2026, 3, 31),
        forecast_completion=date(2026, 5, 15),
        variance_weeks=6,
        critical_path_at_risk=True,
        confidence=0.88
    )

    benefits = BenefitsPerformance(
        total_planned=Decimal("45.00"),
        realised_to_date=Decimal("18.00"),
        forecast_total=Decimal("43.50"),
        realisation_rate=0.40,
        confidence=0.85
    )

    # DCA changed but no rationale provided
    with pytest.raises(ValueError, match="rationale required"):
        QuarterlyReport(
            quarter=QuarterPeriod.Q2,
            financial_year="2025-26",
            reporting_date=date.today(),
            project_id="DFT-HSR-001",
            nista_project_code="DFT_0123_2025-Q2",
            project_name="High Speed Rail Phase 2",
            department="Department for Transport",
            sro_name="Jane Smith",
            sro_email="jane.smith@dft.gov.uk",
            dca_rating="AMBER",
            dca_narrative=narrative,
            previous_dca_rating="GREEN",
            dca_changed=True,  # Changed but no rationale
            financial=financial,
            schedule=schedule,
            benefits=benefits,
            cost_narrative=narrative,
            schedule_narrative=narrative,
            benefits_narrative=narrative,
            risk_narrative=narrative,
        )
