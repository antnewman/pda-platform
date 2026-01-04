"""
Data models for PM Analysis Module.

This module provides comprehensive data structures for project management analysis,
including risk assessment, health monitoring, forecasting, and variance tracking.

All models include JSON serialization support via to_dict() methods.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# Enumerations
# ============================================================================


class Severity(str, Enum):
    """Risk or issue severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RiskCategory(str, Enum):
    """Categories for risk classification."""

    SCHEDULE = "schedule"
    COST = "cost"
    RESOURCE = "resource"
    QUALITY = "quality"
    SCOPE = "scope"
    TECHNICAL = "technical"
    EXTERNAL = "external"
    ORGANIZATIONAL = "organizational"
    STAKEHOLDER = "stakeholder"


class HealthStatus(str, Enum):
    """Overall health status indicators."""

    HEALTHY = "healthy"
    AT_RISK = "at_risk"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AnalysisDepth(str, Enum):
    """Depth of analysis to perform."""

    QUICK = "quick"          # Basic metrics only
    STANDARD = "standard"    # Standard analysis with key insights
    DEEP = "deep"           # Comprehensive analysis with all details


class ForecastMethod(str, Enum):
    """Methods for project completion forecasting."""

    EARNED_VALUE = "earned_value"          # EVM-based forecasting (EAC, ETC)
    MONTE_CARLO = "monte_carlo"            # Probabilistic simulation
    REFERENCE_CLASS = "reference_class"    # Historical reference data
    SIMPLE_EXTRAPOLATION = "simple_extrapolation"  # Linear projection
    ML_ENSEMBLE = "ml_ensemble"            # Ensemble of methods


class TrendDirection(str, Enum):
    """Trend direction indicators."""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    UNKNOWN = "unknown"


# ============================================================================
# Core Data Models
# ============================================================================


@dataclass
class Evidence:
    """Audit trail for AI findings."""

    source: str
    description: str
    data_point: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "source": self.source,
            "description": self.description,
            "data_point": self.data_point,
            "confidence": self.confidence
        }


@dataclass
class Risk:
    """Identified risk with AI confidence."""

    id: str
    name: str
    description: str
    category: RiskCategory
    probability: int  # 1-5
    impact: int       # 1-5
    score: int        # probability * impact
    confidence: float  # 0.0-1.0
    evidence: List[Evidence] = field(default_factory=list)
    related_tasks: List[str] = field(default_factory=list)
    suggested_mitigation: Optional[str] = None
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate probability, impact, and confidence are in valid ranges."""
        if not 1 <= self.probability <= 5:
            raise ValueError(f"Probability must be between 1 and 5, got {self.probability}")
        if not 1 <= self.impact <= 5:
            raise ValueError(f"Impact must be between 1 and 5, got {self.impact}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    @property
    def severity(self) -> Severity:
        """Derive severity from score."""
        if self.score >= 20:
            return Severity.CRITICAL
        if self.score >= 15:
            return Severity.HIGH
        if self.score >= 9:
            return Severity.MEDIUM
        if self.score >= 4:
            return Severity.LOW
        return Severity.INFO

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "probability": self.probability,
            "impact": self.impact,
            "score": self.score,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "evidence": [e.to_dict() for e in self.evidence],
            "related_tasks": self.related_tasks,
            "suggested_mitigation": self.suggested_mitigation,
            "detected_at": self.detected_at.isoformat() if isinstance(self.detected_at, datetime) else str(self.detected_at)
        }


@dataclass
class Mitigation:
    """Risk mitigation strategy."""

    id: str
    risk_id: str
    strategy: str
    description: str
    effort: str  # low/medium/high
    effectiveness: float  # 0.0-1.0
    confidence: float
    implementation_steps: List[str] = field(default_factory=list)
    resource_requirements: List[str] = field(default_factory=list)
    timeline_days: Optional[int] = None

    def __post_init__(self):
        """Validate effectiveness and confidence ranges."""
        if not 0.0 <= self.effectiveness <= 1.0:
            raise ValueError(f"Effectiveness must be between 0.0 and 1.0, got {self.effectiveness}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if self.effort not in ("low", "medium", "high"):
            raise ValueError(f"Effort must be low/medium/high, got {self.effort}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "id": self.id,
            "risk_id": self.risk_id,
            "strategy": self.strategy,
            "description": self.description,
            "effort": self.effort,
            "effectiveness": self.effectiveness,
            "confidence": self.confidence,
            "implementation_steps": self.implementation_steps,
            "resource_requirements": self.resource_requirements,
            "timeline_days": self.timeline_days
        }


@dataclass
class Outlier:
    """Detected anomaly."""

    id: str
    task_id: str
    task_name: str
    field_name: str
    value: Any
    expected_range: tuple[Any, Any]
    deviation_score: float
    severity: Severity
    confidence: float
    explanation: str
    evidence: List[Evidence] = field(default_factory=list)

    def __post_init__(self):
        """Validate confidence range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "field": self.field_name,
            "value": self.value,
            "expected_range": list(self.expected_range),
            "deviation_score": self.deviation_score,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "evidence": [e.to_dict() for e in self.evidence]
        }


@dataclass
class Forecast:
    """Completion prediction."""

    forecast_date: date
    confidence_interval: tuple[date, date]
    confidence_level: float
    method: ForecastMethod
    variance_days: int
    on_track: bool
    confidence: float
    factors: List[str] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    scenarios: Dict[str, date] = field(default_factory=dict)

    def __post_init__(self):
        """Validate confidence values."""
        if not 0.0 <= self.confidence_level <= 1.0:
            raise ValueError(f"Confidence level must be between 0.0 and 1.0, got {self.confidence_level}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "forecast_date": self.forecast_date.isoformat() if isinstance(self.forecast_date, date) else str(self.forecast_date),
            "confidence_interval": [
                d.isoformat() if isinstance(d, date) else str(d)
                for d in self.confidence_interval
            ],
            "confidence_level": self.confidence_level,
            "method": self.method.value,
            "variance_days": self.variance_days,
            "on_track": self.on_track,
            "confidence": self.confidence,
            "factors": self.factors,
            "evidence": [e.to_dict() for e in self.evidence],
            "scenarios": {
                k: v.isoformat() if isinstance(v, date) else str(v)
                for k, v in self.scenarios.items()
            }
        }


@dataclass
class HealthDimension:
    """Single health dimension."""

    name: str
    score: float  # 0-100
    status: HealthStatus
    trend: TrendDirection
    issues: List[str] = field(default_factory=list)
    weight: float = 0.2

    def __post_init__(self):
        """Validate score and weight ranges."""
        if not 0.0 <= self.score <= 100.0:
            raise ValueError(f"Score must be between 0.0 and 100.0, got {self.score}")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {self.weight}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "name": self.name,
            "score": self.score,
            "status": self.status.value,
            "trend": self.trend.value,
            "issues": self.issues,
            "weight": self.weight
        }


@dataclass
class HealthAssessment:
    """Overall health assessment."""

    overall_score: float
    overall_status: HealthStatus
    dimensions: List[HealthDimension]
    top_concerns: List[str]
    recommendations: List[str]
    confidence: float
    assessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate score and confidence ranges."""
        if not 0.0 <= self.overall_score <= 100.0:
            raise ValueError(f"Overall score must be between 0.0 and 100.0, got {self.overall_score}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "overall_score": self.overall_score,
            "overall_status": self.overall_status.value,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "top_concerns": self.top_concerns,
            "recommendations": self.recommendations,
            "confidence": self.confidence,
            "assessed_at": self.assessed_at.isoformat() if isinstance(self.assessed_at, datetime) else str(self.assessed_at)
        }


@dataclass
class BaselineVariance:
    """Variance from baseline."""

    task_id: str
    task_name: str
    field_name: str
    baseline_value: Any
    current_value: Any
    variance: float
    variance_percent: float
    severity: Severity
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "field": self.field_name,
            "baseline_value": str(self.baseline_value) if self.baseline_value else None,
            "current_value": str(self.current_value) if self.current_value else None,
            "variance": self.variance,
            "variance_percent": self.variance_percent,
            "severity": self.severity.value,
            "explanation": self.explanation
        }


@dataclass
class AnalysisMetadata:
    """Analysis run metadata."""

    analysis_id: str
    analysis_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    depth: AnalysisDepth = AnalysisDepth.STANDARD
    tasks_analyzed: int = 0
    overall_confidence: float = 0.0
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate confidence range."""
        if not 0.0 <= self.overall_confidence <= 1.0:
            raise ValueError(f"Overall confidence must be between 0.0 and 1.0, got {self.overall_confidence}")

    def complete(self) -> None:
        """Mark complete and calculate duration."""
        self.completed_at = datetime.now(timezone.utc)
        delta = self.completed_at - self.started_at
        self.duration_ms = int(delta.total_seconds() * 1000)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "analysis_id": self.analysis_id,
            "analysis_type": self.analysis_type,
            "started_at": self.started_at.isoformat() if isinstance(self.started_at, datetime) else str(self.started_at),
            "completed_at": self.completed_at.isoformat() if self.completed_at and isinstance(self.completed_at, datetime) else (str(self.completed_at) if self.completed_at else None),
            "duration_ms": self.duration_ms,
            "depth": self.depth.value,
            "tasks_analyzed": self.tasks_analyzed,
            "overall_confidence": self.overall_confidence,
            "warnings": self.warnings
        }
