"""Pydantic models for GMPP quarterly reporting.

This module defines the data structures for UK Government Major Projects Portfolio
(GMPP) quarterly returns, including delivery confidence assessments, performance
metrics, and AI-generated narratives with confidence scoring.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class QuarterPeriod(str, Enum):
    """UK Government financial year quarters.

    Financial year runs April-March:
    - Q1: April - June
    - Q2: July - September
    - Q3: October - December
    - Q4: January - March
    """

    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"


class ReviewLevel(str, Enum):
    """Human review recommendation levels based on AI confidence.

    - NONE: High confidence (>= 80%), no review needed
    - SPOT_CHECK: Medium-high confidence (60-80%), quick verification recommended
    - DETAILED_REVIEW: Medium confidence (40-60%), careful review required
    - EXPERT_REQUIRED: Low confidence (< 40%), expert human review mandatory
    """

    NONE = "NONE"
    SPOT_CHECK = "SPOT_CHECK"
    DETAILED_REVIEW = "DETAILED_REVIEW"
    EXPERT_REQUIRED = "EXPERT_REQUIRED"


class DCANarrative(BaseModel):
    """Delivery Confidence Assessment narrative with AI confidence metadata.

    Attributes:
        text: Professional narrative text (150-200 words for GMPP compliance)
        confidence: AI confidence score (0.0-1.0) based on multi-sample consensus
        review_level: Recommended human review level
        generated_at: Timestamp of generation
        samples_used: Number of AI samples used for consensus
        review_reason: Optional explanation for why review is recommended
    """

    text: str = Field(
        ...,
        description="Professional civil service narrative (150-200 words recommended; bounds enforced by validate_word_count)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI confidence score from multi-sample consensus"
    )
    review_level: ReviewLevel = Field(
        ...,
        description="Recommended human review level based on confidence"
    )
    generated_at: datetime = Field(
        ...,
        description="UTC timestamp of narrative generation"
    )
    samples_used: int = Field(
        ...,
        ge=1,
        le=10,
        description="Number of AI samples used (typically 3-5)"
    )
    review_reason: str | None = Field(
        None,
        description="Explanation for why review is recommended (if applicable)"
    )

    @field_validator("text")
    @classmethod
    def validate_word_count(cls, v: str) -> str:
        """Validate narrative is within recommended word count."""
        word_count = len(v.split())
        if word_count < 100:
            raise ValueError(f"Narrative too short ({word_count} words), minimum 100 words recommended")
        if word_count > 250:
            raise ValueError(f"Narrative too long ({word_count} words), maximum 250 words recommended")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "The project maintains an AMBER delivery confidence assessment this quarter. "
                       "Significant progress has been achieved in Phase 1 delivery, with 85% of planned "
                       "milestones completed on schedule. However, critical resource constraints in the "
                       "data migration workstream have emerged, creating a 6-week delay risk to the "
                       "overall programme timeline. The project team has implemented mitigation actions "
                       "including additional contractor support and revised phasing of deliverables. "
                       "Cost performance remains within approved tolerances, with forecast whole life "
                       "cost at £24.3M against a £25M baseline. Key risks around third-party API "
                       "dependencies are being actively managed through enhanced governance and "
                       "contingency planning. Benefits realisation tracking shows 40% of planned "
                       "financial benefits achieved to date, in line with expectations.",
                "confidence": 0.87,
                "review_level": "NONE",
                "generated_at": "2025-07-15T10:30:00Z",
                "samples_used": 5,
                "review_reason": None
            }
        }
    }


class FinancialPerformance(BaseModel):
    """Cost performance metrics for GMPP quarterly reporting.

    All monetary values in £ millions to align with NISTA standard.
    """

    baseline_cost: Decimal = Field(
        ...,
        decimal_places=2,
        description="Approved baseline whole life cost (£ millions)"
    )
    forecast_cost: Decimal = Field(
        ...,
        decimal_places=2,
        description="Current forecast whole life cost (£ millions)"
    )
    actual_cost: Decimal | None = Field(
        None,
        decimal_places=2,
        description="Actual cost incurred to date (£ millions)"
    )
    variance_percent: float = Field(
        ...,
        description="Cost variance as percentage of baseline"
    )
    variance_amount: Decimal = Field(
        ...,
        decimal_places=2,
        description="Absolute cost variance (£ millions)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Data confidence score based on source reliability"
    )

    @field_validator("forecast_cost")
    @classmethod
    def validate_forecast_positive(cls, v: Decimal) -> Decimal:
        """Ensure forecast cost is positive."""
        if v <= 0:
            raise ValueError("Forecast cost must be positive")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "baseline_cost": "25.00",
                "forecast_cost": "24.30",
                "actual_cost": "18.50",
                "variance_percent": -2.8,
                "variance_amount": "-0.70",
                "confidence": 0.92
            }
        }
    }


class SchedulePerformance(BaseModel):
    """Schedule performance metrics for GMPP quarterly reporting."""

    baseline_completion: date = Field(
        ...,
        description="Approved baseline completion date"
    )
    forecast_completion: date = Field(
        ...,
        description="Current forecast completion date"
    )
    actual_completion: date | None = Field(
        None,
        description="Actual completion date (if project completed)"
    )
    variance_weeks: int = Field(
        ...,
        description="Schedule variance in weeks (positive = delay, negative = ahead)"
    )
    critical_path_at_risk: bool = Field(
        ...,
        description="Whether critical path is at risk of further delay"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Data confidence score based on source reliability"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "baseline_completion": "2026-03-31",
                "forecast_completion": "2026-05-15",
                "actual_completion": None,
                "variance_weeks": 6,
                "critical_path_at_risk": True,
                "confidence": 0.88
            }
        }
    }


class BenefitsPerformance(BaseModel):
    """Benefits realisation tracking for GMPP quarterly reporting.

    All monetary values in £ millions to align with NISTA standard.
    """

    total_planned: Decimal = Field(
        ...,
        decimal_places=2,
        description="Total planned monetised benefits (£ millions)"
    )
    realised_to_date: Decimal = Field(
        ...,
        decimal_places=2,
        ge=0,
        description="Benefits realised to date (£ millions)"
    )
    forecast_total: Decimal = Field(
        ...,
        decimal_places=2,
        description="Forecast total benefits realisation (£ millions)"
    )
    realisation_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Benefits realisation rate (0.0-1.0)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Data confidence score based on source reliability"
    )

    @model_validator(mode="after")
    def validate_realised_not_exceed_forecast(self) -> "BenefitsPerformance":
        """Validate realised benefits don't exceed forecast.

        Implemented as a model-level validator so it runs after both
        ``realised_to_date`` and ``forecast_total`` are populated, regardless
        of field declaration order.
        """
        if self.realised_to_date > self.forecast_total:
            raise ValueError(
                f"Realised benefits ({self.realised_to_date}M) cannot exceed "
                f"forecast total ({self.forecast_total}M)"
            )
        return self

    @classmethod
    def from_benefits_register(
        cls,
        project_id: str,
        db_path: str | None = None,
    ) -> "BenefitsPerformance":
        """Create a BenefitsPerformance from the BRM benefits register.

        Derives total_planned, realised_to_date, forecast_total, and
        realisation_rate from registered benefits data, making the benefits
        register the single source of truth for GMPP quarterly reporting.

        Args:
            project_id: The project identifier.
            db_path: Optional path to the SQLite store.

        Returns:
            A :class:`BenefitsPerformance` populated from register data.
        """
        from pathlib import Path

        from pm_data_tools.assurance.benefits import (
            BenefitStatus,
            BenefitsTracker,
            FinancialType,
        )
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore(db_path=Path(db_path) if db_path else None)
        tracker = BenefitsTracker(store=store)
        report = tracker.analyse_health(project_id)
        benefits = tracker.get_benefits(project_id)

        # Total planned: sum of target values for financial benefits
        financial_types = (FinancialType.CASH_RELEASING, FinancialType.NON_CASH_RELEASING)
        total_planned = Decimal(str(sum(
            b.target_value or 0.0
            for b in benefits
            if not b.is_disbenefit and b.financial_type in financial_types
        )))

        # Realised: sum of current values for ACHIEVED financial benefits
        realised = Decimal(str(sum(
            b.current_actual_value or 0.0
            for b in benefits
            if not b.is_disbenefit
            and b.status == BenefitStatus.ACHIEVED
            and b.financial_type in financial_types
        )))

        # Forecast: use current actuals for realizing + target for planned
        forecast = Decimal(str(sum(
            (b.current_actual_value if b.status in (BenefitStatus.REALIZING, BenefitStatus.ACHIEVED)
             else b.target_value) or 0.0
            for b in benefits
            if not b.is_disbenefit and b.financial_type in financial_types
        )))

        # Ensure forecast >= realised
        if forecast < realised:
            forecast = realised

        rate = float(realised / total_planned) if total_planned > 0 else 0.0

        return cls(
            total_planned=total_planned,
            realised_to_date=realised,
            forecast_total=forecast,
            realisation_rate=min(rate, 1.0),
            confidence=report.overall_health_score,
        )

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_planned": "45.00",
                "realised_to_date": "18.00",
                "forecast_total": "43.50",
                "realisation_rate": 0.40,
                "confidence": 0.85
            }
        }
    }


class QuarterlyReport(BaseModel):
    """Complete GMPP quarterly return with all required sections.

    This model represents a full UK Government Major Projects Portfolio quarterly
    return, including project identification, delivery confidence assessment,
    performance metrics, and AI-generated narratives with confidence scoring.
    """

    # ========== Reporting Period ==========
    quarter: QuarterPeriod = Field(
        ...,
        description="Reporting quarter (Q1-Q4 of UK financial year)"
    )
    financial_year: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="Financial year in format YYYY-YY (e.g., '2025-26')"
    )
    reporting_date: date = Field(
        ...,
        description="Date of report generation"
    )

    # ========== Project Identification ==========
    project_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Internal project identifier"
    )
    nista_project_code: str = Field(
        ...,
        pattern=r"^[A-Z]+_\d+_\d{4}-Q[1-4]$",
        description="NISTA project code (format: DEPT_NNNN_YYYY-QN)"
    )
    project_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Official project name"
    )
    department: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="UK Government department (e.g., 'Department for Transport')"
    )
    sro_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Senior Responsible Owner full name"
    )
    sro_email: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        description="SRO email address"
    )

    # ========== Delivery Confidence Assessment ==========
    dca_rating: str = Field(
        ...,
        pattern=r"^(GREEN|AMBER/GREEN|AMBER|AMBER/RED|RED|EXEMPT)$",
        description="Delivery Confidence Assessment rating"
    )
    dca_narrative: DCANarrative = Field(
        ...,
        description="AI-generated DCA narrative with confidence metadata"
    )
    previous_dca_rating: str | None = Field(
        None,
        pattern=r"^(GREEN|AMBER/GREEN|AMBER|AMBER/RED|RED|EXEMPT)$",
        description="DCA rating from previous quarter"
    )
    dca_changed: bool = Field(
        default=False,
        description="Whether DCA rating changed from previous quarter"
    )
    dca_change_rationale: str | None = Field(
        None,
        max_length=500,
        description="Rationale for DCA rating change (if changed)"
    )

    # ========== Performance Metrics ==========
    financial: FinancialPerformance = Field(
        ...,
        description="Financial performance metrics"
    )
    schedule: SchedulePerformance = Field(
        ...,
        description="Schedule performance metrics"
    )
    benefits: BenefitsPerformance = Field(
        ...,
        description="Benefits realisation performance"
    )

    # ========== Narratives (AI-generated with confidence) ==========
    cost_narrative: DCANarrative = Field(
        ...,
        description="AI-generated cost performance narrative"
    )
    schedule_narrative: DCANarrative = Field(
        ...,
        description="AI-generated schedule performance narrative"
    )
    benefits_narrative: DCANarrative = Field(
        ...,
        description="AI-generated benefits realisation narrative"
    )
    risk_narrative: DCANarrative = Field(
        ...,
        description="AI-generated risk status narrative"
    )

    # ========== Metadata ==========
    data_sources: list[str] = Field(
        default_factory=list,
        description="List of data sources used (e.g., 'MS Project', 'Jira', 'Manual entry')"
    )
    confidence_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Field-level confidence scores (field_name -> score)"
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="List of recommended fields that are missing"
    )
    validation_warnings: list[str] = Field(
        default_factory=list,
        description="Non-critical validation warnings"
    )

    @model_validator(mode="after")
    def validate_rationale_if_changed(self) -> "QuarterlyReport":
        """Require rationale if DCA changed.

        Implemented as a model-level validator because pydantic v2 field
        validators do not run when the field is omitted at construction time;
        omitting ``dca_change_rationale`` while setting ``dca_changed=True``
        must still raise.
        """
        if self.dca_changed and not self.dca_change_rationale:
            raise ValueError("DCA change rationale required when dca_changed is True")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "quarter": "Q2",
                "financial_year": "2025-26",
                "reporting_date": "2025-07-15",
                "project_id": "DFT-HSR-001",
                "nista_project_code": "DFT_0123_2025-Q2",
                "project_name": "High Speed Rail Phase 2",
                "department": "Department for Transport",
                "sro_name": "Jane Smith",
                "sro_email": "jane.smith@dft.gov.uk",
                "dca_rating": "AMBER",
                "dca_narrative": {
                    "text": "...",  # Full example in DCANarrative
                    "confidence": 0.87,
                    "review_level": "NONE",
                    "generated_at": "2025-07-15T10:30:00Z",
                    "samples_used": 5
                },
                "previous_dca_rating": "GREEN",
                "dca_changed": True,
                "dca_change_rationale": "Resource constraints emerged in Q2 affecting delivery timeline",
                "financial": {
                    "baseline_cost": "25.00",
                    "forecast_cost": "24.30",
                    "actual_cost": "18.50",
                    "variance_percent": -2.8,
                    "variance_amount": "-0.70",
                    "confidence": 0.92
                },
                "schedule": {
                    "baseline_completion": "2026-03-31",
                    "forecast_completion": "2026-05-15",
                    "actual_completion": None,
                    "variance_weeks": 6,
                    "critical_path_at_risk": True,
                    "confidence": 0.88
                },
                "benefits": {
                    "total_planned": "45.00",
                    "realised_to_date": "18.00",
                    "forecast_total": "43.50",
                    "realisation_rate": 0.40,
                    "confidence": 0.85
                },
                "cost_narrative": {"text": "...", "confidence": 0.85, "review_level": "NONE", "generated_at": "2025-07-15T10:30:00Z", "samples_used": 5},
                "schedule_narrative": {"text": "...", "confidence": 0.82, "review_level": "SPOT_CHECK", "generated_at": "2025-07-15T10:30:00Z", "samples_used": 5},
                "benefits_narrative": {"text": "...", "confidence": 0.88, "review_level": "NONE", "generated_at": "2025-07-15T10:30:00Z", "samples_used": 5},
                "risk_narrative": {"text": "...", "confidence": 0.79, "review_level": "SPOT_CHECK", "generated_at": "2025-07-15T10:30:00Z", "samples_used": 5},
                "data_sources": ["MS Project", "Risk Register", "Benefits Tracker"],
                "confidence_scores": {
                    "financial": 0.92,
                    "schedule": 0.88,
                    "benefits": 0.85
                },
                "missing_fields": [],
                "validation_warnings": ["Schedule variance > 4 weeks - consider escalation"]
            }
        }
    }
