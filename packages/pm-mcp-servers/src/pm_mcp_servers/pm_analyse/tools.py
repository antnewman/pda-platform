"""
PM-Analyse MCP Server Tools.

Provides 6 analysis tools for project risk, forecasting, health, outliers,
mitigations, and baseline comparison. All tools return structured JSON responses
with AnalysisMetadata and proper error handling.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from pm_mcp_servers.shared import project_store

from .analyzers import BaselineComparator, HealthAnalyzer, OutlierDetector
from .forecasters import ForecastEngine
from .models import AnalysisDepth, AnalysisMetadata, ForecastMethod
from .risk_engine import RiskEngine

logger = logging.getLogger(__name__)


# ============================================================================
# Tool 1: Identify Risks
# ============================================================================


async def identify_risks(params: dict[str, Any]) -> dict[str, Any]:
    """
    Identify project risks using AI-powered risk engine.

    Args:
        params: {
            "project_id": str,
            "focus_areas": Optional[List[str]],  # ["schedule", "cost", "resource", ...]
            "depth": Optional[str]  # "quick", "standard", "deep"
        }

    Returns:
        {
            "risks": List[Risk],
            "summary": {
                "total_risks": int,
                "critical_count": int,
                "high_count": int,
                "by_category": Dict[str, int]
            },
            "metadata": AnalysisMetadata
        }
        or {"error": {"code": str, "message": str, "suggestion": str}}
    """
    # Create metadata
    analysis_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)
    metadata = AnalysisMetadata(
        analysis_id=analysis_id,
        analysis_type="risk_identification",
        started_at=started_at,
        depth=AnalysisDepth(params.get("depth", "standard"))
    )

    try:
        # Validate parameters
        project_id = params.get("project_id")
        if not project_id:
            return {
                "error": {
                    "code": "MISSING_PARAMETER",
                    "message": "project_id is required",
                    "suggestion": "Provide a valid project_id from load_project"
                }
            }

        # Get project from store
        project = project_store.get(project_id)
        if not project:
            return {
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": f"Project {project_id} not found in store",
                    "suggestion": "Load project first using pm-data load_project tool"
                }
            }

        # Extract parameters
        focus_areas = params.get("focus_areas")
        depth = AnalysisDepth(params.get("depth", "standard"))

        # Run risk analysis
        engine = RiskEngine()
        risks = engine.analyze(
            project=project,
            focus_areas=focus_areas,
            depth=depth
        )

        # Update metadata
        metadata.tasks_analyzed = len(getattr(project, 'tasks', []))
        metadata.overall_confidence = sum(r.confidence for r in risks) / len(risks) if risks else 0.85
        metadata.complete()

        # Calculate summary statistics
        critical_count = sum(1 for r in risks if r.severity.value == "critical")
        high_count = sum(1 for r in risks if r.severity.value == "high")

        # Count by category
        by_category: dict[str, int] = {}
        for risk in risks:
            cat = risk.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "risks": [r.to_dict() for r in risks],
            "summary": {
                "total_risks": len(risks),
                "critical_count": critical_count,
                "high_count": high_count,
                "by_category": by_category
            },
            "metadata": metadata.to_dict()
        }

    except Exception as e:
        logger.exception(f"Error in identify_risks: {e}")
        metadata.warnings.append(str(e))
        metadata.complete()

        return {
            "error": {
                "code": "ANALYSIS_ERROR",
                "message": f"Risk identification failed: {str(e)}",
                "suggestion": "Check project data quality and try again"
            },
            "metadata": metadata.to_dict()
        }


# ============================================================================
# Tool 2: Forecast Completion
# ============================================================================


async def forecast_completion(params: dict[str, Any]) -> dict[str, Any]:
    """
    Forecast project completion date using multiple methods.

    Args:
        params: {
            "project_id": str,
            "method": Optional[str],  # "earned_value", "monte_carlo", "ml_ensemble", ...
            "confidence_level": Optional[float],  # 0.50-0.95
            "scenarios": Optional[bool],  # Generate scenario forecasts
            "depth": Optional[str]  # "quick", "standard", "deep"
        }

    Returns:
        {
            "forecast": Forecast,
            "metadata": AnalysisMetadata
        }
        or {"error": {...}}
    """
    # Create metadata
    analysis_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)
    metadata = AnalysisMetadata(
        analysis_id=analysis_id,
        analysis_type="completion_forecast",
        started_at=started_at,
        depth=AnalysisDepth(params.get("depth", "standard"))
    )

    try:
        # Validate parameters
        project_id = params.get("project_id")
        if not project_id:
            return {
                "error": {
                    "code": "MISSING_PARAMETER",
                    "message": "project_id is required",
                    "suggestion": "Provide a valid project_id from load_project"
                }
            }

        # Get project from store
        project = project_store.get(project_id)
        if not project:
            return {
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": f"Project {project_id} not found in store",
                    "suggestion": "Load project first using pm-data load_project tool"
                }
            }

        # Extract parameters
        method_str = params.get("method", "ml_ensemble")
        try:
            method = ForecastMethod(method_str)
        except ValueError:
            return {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": f"Invalid forecast method: {method_str}",
                    "suggestion": "Use one of: earned_value, monte_carlo, reference_class, simple_extrapolation, ml_ensemble"
                }
            }

        confidence_level = params.get("confidence_level", 0.80)
        scenarios = params.get("scenarios", True)
        depth = AnalysisDepth(params.get("depth", "standard"))

        # Run forecast
        engine = ForecastEngine()
        forecast = engine.forecast(
            project=project,
            method=method,
            confidence_level=confidence_level,
            scenarios=scenarios,
            depth=depth
        )

        # Update metadata
        metadata.tasks_analyzed = len(getattr(project, 'tasks', []))
        metadata.overall_confidence = forecast.confidence
        metadata.complete()

        return {
            "forecast": forecast.to_dict(),
            "metadata": metadata.to_dict()
        }

    except Exception as e:
        logger.exception(f"Error in forecast_completion: {e}")
        metadata.warnings.append(str(e))
        metadata.complete()

        return {
            "error": {
                "code": "FORECAST_ERROR",
                "message": f"Forecast failed: {str(e)}",
                "suggestion": "Check project has sufficient data for forecasting"
            },
            "metadata": metadata.to_dict()
        }


# ============================================================================
# Tool 3: Detect Outliers
# ============================================================================


async def detect_outliers(params: dict[str, Any]) -> dict[str, Any]:
    """
    Detect anomalies in project data.

    Args:
        params: {
            "project_id": str,
            "sensitivity": Optional[float],  # 0.5-2.0, default 1.0
            "focus_areas": Optional[List[str]]  # ["duration", "progress", "float", "dates"]
        }

    Returns:
        {
            "outliers": List[Outlier],
            "summary": {
                "total_outliers": int,
                "critical_count": int,
                "by_field": Dict[str, int]
            },
            "metadata": AnalysisMetadata
        }
        or {"error": {...}}
    """
    # Create metadata
    analysis_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)
    metadata = AnalysisMetadata(
        analysis_id=analysis_id,
        analysis_type="outlier_detection",
        started_at=started_at,
        depth=AnalysisDepth.STANDARD
    )

    try:
        # Validate parameters
        project_id = params.get("project_id")
        if not project_id:
            return {
                "error": {
                    "code": "MISSING_PARAMETER",
                    "message": "project_id is required",
                    "suggestion": "Provide a valid project_id from load_project"
                }
            }

        # Get project from store
        project = project_store.get(project_id)
        if not project:
            return {
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": f"Project {project_id} not found in store",
                    "suggestion": "Load project first using pm-data load_project tool"
                }
            }

        # Extract parameters
        sensitivity = params.get("sensitivity", 1.0)
        focus_areas = params.get("focus_areas")

        # Validate sensitivity
        if not 0.5 <= sensitivity <= 2.0:
            return {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": f"Sensitivity must be between 0.5 and 2.0, got {sensitivity}",
                    "suggestion": "Use 0.5 for less sensitive, 2.0 for more sensitive detection"
                }
            }

        # Run outlier detection
        detector = OutlierDetector()
        outliers = detector.detect(
            project=project,
            sensitivity=sensitivity,
            focus_areas=focus_areas
        )

        # Update metadata
        metadata.tasks_analyzed = len(getattr(project, 'tasks', []))
        metadata.overall_confidence = sum(o.confidence for o in outliers) / len(outliers) if outliers else 0.80
        metadata.complete()

        # Calculate summary statistics
        critical_count = sum(1 for o in outliers if o.severity.value == "critical")

        # Count by field
        by_field: dict[str, int] = {}
        for outlier in outliers:
            field = outlier.field_name
            by_field[field] = by_field.get(field, 0) + 1

        return {
            "outliers": [o.to_dict() for o in outliers],
            "summary": {
                "total_outliers": len(outliers),
                "critical_count": critical_count,
                "by_field": by_field
            },
            "metadata": metadata.to_dict()
        }

    except Exception as e:
        logger.exception(f"Error in detect_outliers: {e}")
        metadata.warnings.append(str(e))
        metadata.complete()

        return {
            "error": {
                "code": "OUTLIER_DETECTION_ERROR",
                "message": f"Outlier detection failed: {str(e)}",
                "suggestion": "Check project data quality and try again"
            },
            "metadata": metadata.to_dict()
        }


# ============================================================================
# Tool 4: Assess Health
# ============================================================================


async def assess_health(params: dict[str, Any]) -> dict[str, Any]:
    """
    Assess multi-dimensional project health.

    Args:
        params: {
            "project_id": str,
            "include_trends": Optional[bool],  # default True
            "weights": Optional[Dict[str, float]]  # Custom dimension weights
        }

    Returns:
        {
            "health": HealthAssessment,
            "metadata": AnalysisMetadata
        }
        or {"error": {...}}
    """
    # Create metadata
    analysis_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)
    metadata = AnalysisMetadata(
        analysis_id=analysis_id,
        analysis_type="health_assessment",
        started_at=started_at,
        depth=AnalysisDepth.STANDARD
    )

    try:
        # Validate parameters
        project_id = params.get("project_id")
        if not project_id:
            return {
                "error": {
                    "code": "MISSING_PARAMETER",
                    "message": "project_id is required",
                    "suggestion": "Provide a valid project_id from load_project"
                }
            }

        # Get project from store
        project = project_store.get(project_id)
        if not project:
            return {
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": f"Project {project_id} not found in store",
                    "suggestion": "Load project first using pm-data load_project tool"
                }
            }

        # Extract parameters
        include_trends = params.get("include_trends", True)
        weights = params.get("weights")

        # Validate weights if provided
        if weights:
            weight_sum = sum(weights.values())
            if not 0.99 <= weight_sum <= 1.01:  # Allow small floating point errors
                return {
                    "error": {
                        "code": "INVALID_PARAMETER",
                        "message": f"Weights must sum to 1.0, got {weight_sum}",
                        "suggestion": "Ensure dimension weights sum to exactly 1.0"
                    }
                }

        # Run health assessment
        analyzer = HealthAnalyzer()
        health = analyzer.assess(
            project=project,
            include_trends=include_trends,
            weights=weights
        )

        # Update metadata
        metadata.tasks_analyzed = len(getattr(project, 'tasks', []))
        metadata.overall_confidence = health.confidence
        metadata.complete()

        return {
            "health": health.to_dict(),
            "metadata": metadata.to_dict()
        }

    except Exception as e:
        logger.exception(f"Error in assess_health: {e}")
        metadata.warnings.append(str(e))
        metadata.complete()

        return {
            "error": {
                "code": "HEALTH_ASSESSMENT_ERROR",
                "message": f"Health assessment failed: {str(e)}",
                "suggestion": "Check project has sufficient data for health assessment"
            },
            "metadata": metadata.to_dict()
        }


# ============================================================================
# Tool 5: Suggest Mitigations
# ============================================================================


async def suggest_mitigations(params: dict[str, Any]) -> dict[str, Any]:
    """
    Generate mitigation strategies for identified risks.

    Args:
        params: {
            "project_id": str,
            "risk_ids": Optional[List[str]],  # Specific risks to mitigate
            "focus_areas": Optional[List[str]],  # Focus on specific risk categories
            "depth": Optional[str]  # "quick", "standard", "deep"
        }

    Returns:
        {
            "mitigations": List[Mitigation],
            "summary": {
                "total_mitigations": int,
                "high_effectiveness_count": int,
                "by_strategy": Dict[str, int]
            },
            "metadata": AnalysisMetadata
        }
        or {"error": {...}}
    """
    # Create metadata
    analysis_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)
    metadata = AnalysisMetadata(
        analysis_id=analysis_id,
        analysis_type="mitigation_generation",
        started_at=started_at,
        depth=AnalysisDepth(params.get("depth", "standard"))
    )

    try:
        # Validate parameters
        project_id = params.get("project_id")
        if not project_id:
            return {
                "error": {
                    "code": "MISSING_PARAMETER",
                    "message": "project_id is required",
                    "suggestion": "Provide a valid project_id from load_project"
                }
            }

        # Get project from store
        project = project_store.get(project_id)
        if not project:
            return {
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": f"Project {project_id} not found in store",
                    "suggestion": "Load project first using pm-data load_project tool"
                }
            }

        # Extract parameters
        risk_ids = params.get("risk_ids")
        focus_areas = params.get("focus_areas")
        depth = AnalysisDepth(params.get("depth", "standard"))

        # First identify risks
        engine = RiskEngine()
        all_risks = engine.analyze(
            project=project,
            focus_areas=focus_areas,
            depth=depth
        )

        # Filter to specific risks if requested
        if risk_ids:
            risks_to_mitigate = [r for r in all_risks if r.id in risk_ids]
            if not risks_to_mitigate:
                return {
                    "error": {
                        "code": "NO_RISKS_FOUND",
                        "message": "None of the specified risk_ids were found",
                        "suggestion": "Run identify_risks first to get valid risk IDs"
                    }
                }
        else:
            risks_to_mitigate = all_risks

        # Generate mitigations
        mitigations = engine.generate_mitigations(risks_to_mitigate)

        # Update metadata
        metadata.tasks_analyzed = len(getattr(project, 'tasks', []))
        metadata.overall_confidence = sum(m.confidence for m in mitigations) / len(mitigations) if mitigations else 0.80
        metadata.complete()

        # Calculate summary statistics
        high_effectiveness = sum(1 for m in mitigations if m.effectiveness >= 0.75)

        # Count by strategy
        by_strategy: dict[str, int] = {}
        for mitigation in mitigations:
            strategy = mitigation.strategy
            by_strategy[strategy] = by_strategy.get(strategy, 0) + 1

        return {
            "mitigations": [m.to_dict() for m in mitigations],
            "summary": {
                "total_mitigations": len(mitigations),
                "high_effectiveness_count": high_effectiveness,
                "by_strategy": by_strategy
            },
            "metadata": metadata.to_dict()
        }

    except Exception as e:
        logger.exception(f"Error in suggest_mitigations: {e}")
        metadata.warnings.append(str(e))
        metadata.complete()

        return {
            "error": {
                "code": "MITIGATION_ERROR",
                "message": f"Mitigation generation failed: {str(e)}",
                "suggestion": "Check project has sufficient data for risk analysis"
            },
            "metadata": metadata.to_dict()
        }


# ============================================================================
# Tool 6: Compare Baseline
# ============================================================================


async def compare_baseline(params: dict[str, Any]) -> dict[str, Any]:
    """
    Compare current project state against baseline.

    Args:
        params: {
            "project_id": str,
            "baseline_type": Optional[str],  # "current", "original", "approved"
            "threshold": Optional[float]  # Minimum variance % to report (0-100)
        }

    Returns:
        {
            "variances": List[BaselineVariance],
            "summary": {
                "total_variances": int,
                "critical_count": int,
                "average_variance_pct": float,
                "by_field": Dict[str, int]
            },
            "metadata": AnalysisMetadata
        }
        or {"error": {...}}
    """
    # Create metadata
    analysis_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)
    metadata = AnalysisMetadata(
        analysis_id=analysis_id,
        analysis_type="baseline_comparison",
        started_at=started_at,
        depth=AnalysisDepth.STANDARD
    )

    try:
        # Validate parameters
        project_id = params.get("project_id")
        if not project_id:
            return {
                "error": {
                    "code": "MISSING_PARAMETER",
                    "message": "project_id is required",
                    "suggestion": "Provide a valid project_id from load_project"
                }
            }

        # Get project from store
        project = project_store.get(project_id)
        if not project:
            return {
                "error": {
                    "code": "PROJECT_NOT_FOUND",
                    "message": f"Project {project_id} not found in store",
                    "suggestion": "Load project first using pm-data load_project tool"
                }
            }

        # Extract parameters
        baseline_type = params.get("baseline_type", "current")
        threshold = params.get("threshold", 0.0)

        # Validate threshold
        if not 0.0 <= threshold <= 100.0:
            return {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": f"Threshold must be between 0.0 and 100.0, got {threshold}",
                    "suggestion": "Use 0 to see all variances, higher values to filter small changes"
                }
            }

        # Run baseline comparison
        comparator = BaselineComparator()
        variances = comparator.compare(
            project=project,
            baseline_type=baseline_type,
            threshold=threshold
        )

        # Update metadata
        metadata.tasks_analyzed = len(getattr(project, 'tasks', []))
        metadata.overall_confidence = 0.90  # Baseline comparison is high confidence
        if not variances:
            metadata.warnings.append("No baseline data found for comparison")
        metadata.complete()

        # Calculate summary statistics
        critical_count = sum(1 for v in variances if v.severity.value == "critical")

        # Calculate average variance percentage
        avg_variance = sum(abs(v.variance_percent) for v in variances) / len(variances) if variances else 0

        # Count by field
        by_field: dict[str, int] = {}
        for variance in variances:
            field = variance.field_name
            by_field[field] = by_field.get(field, 0) + 1

        return {
            "variances": [v.to_dict() for v in variances],
            "summary": {
                "total_variances": len(variances),
                "critical_count": critical_count,
                "average_variance_pct": avg_variance,
                "by_field": by_field
            },
            "metadata": metadata.to_dict()
        }

    except Exception as e:
        logger.exception(f"Error in compare_baseline: {e}")
        metadata.warnings.append(str(e))
        metadata.complete()

        return {
            "error": {
                "code": "BASELINE_COMPARISON_ERROR",
                "message": f"Baseline comparison failed: {str(e)}",
                "suggestion": "Check project has baseline data set"
            },
            "metadata": metadata.to_dict()
        }


# ============================================================================
# Tool 7: Detect Narrative Divergence
# ============================================================================


async def detect_narrative_divergence(params: dict[str, Any]) -> dict[str, Any]:
    """
    Detect divergences between a written project narrative and quantitative data.

    Compares a free-text narrative against data stored in the AssuranceStore for the
    project. Uses the Claude API to identify specific factual claims in the narrative
    and classify each as SUPPORTED, CONTRADICTED, or UNVERIFIABLE against the data.

    Args:
        params: {
            "project_id": str,
            "narrative_text": str,
            "confidence_threshold": Optional[float]  # default 0.7
        }

    Returns:
        {
            "project_id": str,
            "overall_assessment": str,  # ALIGNED / MINOR_DIVERGENCE / DIVERGENT / HIGHLY_DIVERGENT
            "divergence_score": float,  # 0.0-1.0
            "claims_assessed": int,
            "contradictions": int,
            "flags": List[dict],
            "supported_claims": List[dict],
            "unverifiable_claims": List[dict],
            "data_used": List[str],
            "data_gaps": List[str]
        }
        or {"error": {"code": str, "message": str, "suggestion": str}}
    """
    import os

    # ------------------------------------------------------------------ #
    # 1. Validate inputs                                                   #
    # ------------------------------------------------------------------ #
    project_id = params.get("project_id")
    if not project_id:
        return {
            "error": {
                "code": "MISSING_PARAMETER",
                "message": "project_id is required",
                "suggestion": "Provide a valid project_id from load_project",
            }
        }

    narrative_text = params.get("narrative_text")
    if not narrative_text or not narrative_text.strip():
        return {
            "error": {
                "code": "MISSING_PARAMETER",
                "message": "narrative_text is required and must not be empty",
                "suggestion": "Provide the project narrative text to analyse",
            }
        }

    confidence_threshold = float(params.get("confidence_threshold", 0.7))
    if not 0.0 <= confidence_threshold <= 1.0:
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": f"confidence_threshold must be between 0.0 and 1.0, got {confidence_threshold}",
                "suggestion": "Use a value between 0.0 and 1.0 (default: 0.7)",
            }
        }

    # ------------------------------------------------------------------ #
    # 2. Check API key                                                     #
    # ------------------------------------------------------------------ #
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "error": {
                "code": "API_KEY_MISSING",
                "message": "ANTHROPIC_API_KEY environment variable is not set",
                "suggestion": "Set the ANTHROPIC_API_KEY environment variable to use detect_narrative_divergence",
            }
        }

    # ------------------------------------------------------------------ #
    # 3. Gather quantitative data from the AssuranceStore                 #
    # ------------------------------------------------------------------ #
    from pathlib import Path
    from pm_data_tools.db.store import AssuranceStore

    raw_db_path = params.get("db_path")
    db_path = Path(raw_db_path) if raw_db_path else None
    store = AssuranceStore(db_path=db_path)

    data_summary: dict[str, Any] = {}
    data_used: list[str] = []
    data_gaps: list[str] = []

    # Risks
    try:
        risks = store.get_risks(project_id)
        if risks:
            open_risks = [r for r in risks if r.get("status") == "OPEN"]
            high_risks = [r for r in risks if r.get("risk_score", 0) >= 12]
            data_summary["risks"] = {
                "total": len(risks),
                "open": len(open_risks),
                "high_score_count": len(high_risks),
                "top_risks": [
                    {
                        "title": r.get("title"),
                        "category": r.get("category"),
                        "risk_score": r.get("risk_score"),
                        "likelihood": r.get("likelihood"),
                        "impact": r.get("impact"),
                        "status": r.get("status"),
                    }
                    for r in risks[:5]
                ],
            }
            data_used.append("risks")
        else:
            data_gaps.append("no risk register data")
    except Exception:
        data_gaps.append("no risk register data")

    # Gate readiness
    try:
        gate_rows = store.get_gate_readiness_history(project_id)
        if gate_rows:
            latest_gate = gate_rows[-1]
            data_summary["gate_readiness"] = {
                "gate": latest_gate.get("gate"),
                "readiness": latest_gate.get("readiness"),
                "composite_score": latest_gate.get("composite_score"),
                "assessed_at": latest_gate.get("assessed_at"),
            }
            data_used.append("gate_readiness")
        else:
            data_gaps.append("no gate readiness data")
    except Exception:
        data_gaps.append("no gate readiness data")

    # Financial baselines
    try:
        financial_baselines = store.get_financial_baselines(project_id)
        if financial_baselines:
            latest_baseline = financial_baselines[-1]
            data_summary["financial_baseline"] = {
                "label": latest_baseline.get("label"),
                "total_budget": latest_baseline.get("total_budget"),
                "created_at": latest_baseline.get("created_at"),
            }
            data_used.append("financial_baseline")
        else:
            data_gaps.append("no financial baseline data")
    except Exception:
        data_gaps.append("no financial baseline data")

    # Financial actuals
    try:
        actuals = store.get_financial_actuals(project_id)
        if actuals:
            latest_actual = actuals[-1]
            total_spend = sum(a.get("actual_spend", 0) for a in actuals)
            data_summary["financial_actuals"] = {
                "periods_recorded": len(actuals),
                "total_spend_to_date": total_spend,
                "latest_period": latest_actual.get("period"),
                "latest_actual_spend": latest_actual.get("actual_spend"),
            }
            data_used.append("financial_actuals")
        else:
            data_gaps.append("no financial actuals data")
    except Exception:
        data_gaps.append("no financial actuals data")

    # Benefits
    try:
        benefits = store.get_benefits(project_id)
        if benefits:
            by_status: dict[str, int] = {}
            for b in benefits:
                s = b.get("status", "UNKNOWN")
                by_status[s] = by_status.get(s, 0) + 1
            data_summary["benefits"] = {
                "total": len(benefits),
                "by_status": by_status,
            }
            data_used.append("benefits")
        else:
            data_gaps.append("no benefits data")
    except Exception:
        data_gaps.append("no benefits data")

    # Change requests (change pressure)
    try:
        change_requests = store.get_change_requests(project_id)
        if change_requests:
            approved = [c for c in change_requests if c.get("status") == "APPROVED"]
            total_cost_impact = sum(
                c.get("impact_cost", 0) or 0 for c in change_requests
            )
            total_schedule_impact = sum(
                c.get("impact_schedule_days", 0) or 0 for c in change_requests
            )
            data_summary["change_requests"] = {
                "total": len(change_requests),
                "approved": len(approved),
                "total_cost_impact": total_cost_impact,
                "total_schedule_impact_days": total_schedule_impact,
            }
            data_used.append("change_requests")
        else:
            data_gaps.append("no change request data")
    except Exception:
        data_gaps.append("no change request data")

    # ------------------------------------------------------------------ #
    # 4. Build Claude prompt                                               #
    # ------------------------------------------------------------------ #
    data_text = json.dumps(data_summary, indent=2, default=str)

    system_prompt = (
        "You are an independent assurance reviewer. "
        "Your job is to compare a project narrative against quantitative data "
        "and identify divergences that may indicate optimism bias or misrepresentation. "
        "Be rigorous and specific. Only flag claims that are explicitly or implicitly "
        "contradicted by the data. Do not infer data that is not present."
    )

    user_prompt = f"""You are reviewing a project narrative against quantitative assurance data.

PROJECT NARRATIVE:
{narrative_text}

QUANTITATIVE DATA FROM ASSURANCE STORE:
{data_text}

Instructions:
1. Identify specific factual claims made in the narrative (explicit or implicit).
2. For each claim, assess it against the quantitative data as one of:
   - SUPPORTED: the data confirms the claim
   - CONTRADICTED: the data contradicts the claim
   - UNVERIFIABLE: no relevant data is available to assess the claim
3. For any CONTRADICTED claim, assign a severity: HIGH, MEDIUM, or LOW.
   - HIGH: material misrepresentation (e.g. claiming on-track when SPI < 0.8, claiming budget is fine when spend is near or over)
   - MEDIUM: concerning divergence but not necessarily misleading (e.g. overstating benefits progress)
   - LOW: minor overstatement or tone that does not match data
4. Quote the exact phrase from the narrative and cite the specific evidence from the data.
5. For each claim, provide your confidence in the assessment (0.0-1.0).

Respond in the following JSON format exactly:
{{
  "claims": [
    {{
      "claim": "<exact phrase or paraphrase from narrative>",
      "verdict": "SUPPORTED" | "CONTRADICTED" | "UNVERIFIABLE",
      "severity": "HIGH" | "MEDIUM" | "LOW" | null,
      "evidence": "<specific data point or reason>",
      "confidence": <float 0.0-1.0>
    }}
  ]
}}

Only output the JSON. Do not add any commentary before or after."""

    # ------------------------------------------------------------------ #
    # 5. Call Claude                                                       #
    # ------------------------------------------------------------------ #
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw_response = message.content[0].text
    except Exception as exc:
        return {
            "error": {
                "code": "API_CALL_FAILED",
                "message": f"Claude API call failed: {exc}",
                "suggestion": "Check ANTHROPIC_API_KEY is valid and the API is reachable",
            }
        }

    # ------------------------------------------------------------------ #
    # 6. Parse response                                                    #
    # ------------------------------------------------------------------ #
    try:
        # Strip markdown code fences if present
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
        parsed = json.loads(cleaned)
        all_claims = parsed.get("claims", [])
    except Exception:
        return {
            "error": {
                "code": "PARSE_ERROR",
                "message": "Failed to parse Claude API response as JSON",
                "suggestion": "This is an internal error — try again or contact support",
                "raw_response": raw_response[:500],
            }
        }

    # ------------------------------------------------------------------ #
    # 7. Build structured output                                           #
    # ------------------------------------------------------------------ #
    _SEVERITY_WEIGHT = {"HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.25}

    flags: list[dict[str, Any]] = []
    supported_claims: list[dict[str, Any]] = []
    unverifiable_claims: list[dict[str, Any]] = []

    for claim_data in all_claims:
        verdict = claim_data.get("verdict", "UNVERIFIABLE")
        confidence = float(claim_data.get("confidence", 0.0))

        if verdict == "SUPPORTED":
            supported_claims.append(
                {
                    "claim": claim_data.get("claim", ""),
                    "evidence": claim_data.get("evidence", ""),
                }
            )
        elif verdict == "CONTRADICTED":
            # Only include flags that meet the confidence threshold
            if confidence >= confidence_threshold:
                flags.append(
                    {
                        "claim": claim_data.get("claim", ""),
                        "verdict": "CONTRADICTED",
                        "severity": claim_data.get("severity") or "LOW",
                        "evidence": claim_data.get("evidence", ""),
                        "confidence": round(confidence, 3),
                    }
                )
        elif verdict == "UNVERIFIABLE":
            unverifiable_claims.append(
                {
                    "claim": claim_data.get("claim", ""),
                    "reason": claim_data.get("evidence", "No quantitative data available"),
                }
            )

    # Divergence score: weighted proportion of assessed claims that are contradicted
    total_claims = len(all_claims)
    if total_claims == 0:
        divergence_score = 0.0
    else:
        weighted_contradictions = sum(
            _SEVERITY_WEIGHT.get(f.get("severity", "LOW"), 0.25) for f in flags
        )
        divergence_score = min(1.0, weighted_contradictions / total_claims)

    contradictions = len(flags)

    # Overall assessment
    high_contradiction_count = sum(1 for f in flags if f.get("severity") == "HIGH")
    if contradictions == 0:
        overall_assessment = "ALIGNED"
    elif high_contradiction_count >= 2:
        overall_assessment = "HIGHLY_DIVERGENT"
    elif high_contradiction_count >= 1 or contradictions >= 3:
        overall_assessment = "DIVERGENT"
    else:
        overall_assessment = "MINOR_DIVERGENCE"

    return {
        "project_id": project_id,
        "overall_assessment": overall_assessment,
        "divergence_score": round(divergence_score, 3),
        "claims_assessed": total_claims,
        "contradictions": contradictions,
        "flags": flags,
        "supported_claims": supported_claims,
        "unverifiable_claims": unverifiable_claims,
        "data_used": data_used,
        "data_gaps": data_gaps,
    }

# ============================================================================
# Tool 7: Detect Narrative Divergence
# ============================================================================


async def detect_narrative_divergence(params: dict[str, Any]) -> dict[str, Any]:
    """
    Detect divergences between a written project narrative and quantitative data.

    Compares a free-text narrative against data stored in the AssuranceStore for the
    project. Uses the Claude API to identify specific factual claims in the narrative
    and classify each as SUPPORTED, CONTRADICTED, or UNVERIFIABLE against the data.

    Args:
        params: {
            "project_id": str,
            "narrative_text": str,
            "confidence_threshold": Optional[float]  # default 0.7
        }

    Returns:
        {
            "project_id": str,
            "overall_assessment": str,  # ALIGNED / MINOR_DIVERGENCE / DIVERGENT / HIGHLY_DIVERGENT
            "divergence_score": float,  # 0.0–1.0
            "claims_assessed": int,
            "contradictions": int,
            "flags": List[dict],
            "supported_claims": List[dict],
            "unverifiable_claims": List[dict],
            "data_used": List[str],
            "data_gaps": List[str]
        }
        or {"error": {"code": str, "message": str, "suggestion": str}}
    """
    import os

    # ------------------------------------------------------------------ #
    # 1. Validate inputs                                                   #
    # ------------------------------------------------------------------ #
    project_id = params.get("project_id")
    if not project_id:
        return {
            "error": {
                "code": "MISSING_PARAMETER",
                "message": "project_id is required",
                "suggestion": "Provide a valid project_id from load_project",
            }
        }

    narrative_text = params.get("narrative_text")
    if not narrative_text or not narrative_text.strip():
        return {
            "error": {
                "code": "MISSING_PARAMETER",
                "message": "narrative_text is required and must not be empty",
                "suggestion": "Provide the project narrative text to analyse",
            }
        }

    confidence_threshold = float(params.get("confidence_threshold", 0.7))
    if not 0.0 <= confidence_threshold <= 1.0:
        return {
            "error": {
                "code": "INVALID_PARAMETER",
                "message": f"confidence_threshold must be between 0.0 and 1.0, got {confidence_threshold}",
                "suggestion": "Use a value between 0.0 and 1.0 (default: 0.7)",
            }
        }

    # ------------------------------------------------------------------ #
    # 2. Check API key                                                     #
    # ------------------------------------------------------------------ #
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "error": {
                "code": "API_KEY_MISSING",
                "message": "ANTHROPIC_API_KEY environment variable is not set",
                "suggestion": "Set the ANTHROPIC_API_KEY environment variable to use detect_narrative_divergence",
            }
        }

    # ------------------------------------------------------------------ #
    # 3. Gather quantitative data from the AssuranceStore                 #
    # ------------------------------------------------------------------ #
    from pathlib import Path
    from pm_data_tools.db.store import AssuranceStore

    raw_db_path = params.get("db_path")
    db_path = Path(raw_db_path) if raw_db_path else None
    store = AssuranceStore(db_path=db_path)

    data_summary: dict[str, Any] = {}
    data_used: list[str] = []
    data_gaps: list[str] = []

    # Risks
    try:
        risks = store.get_risks(project_id)
        if risks:
            open_risks = [r for r in risks if r.get("status") == "OPEN"]
            high_risks = [r for r in risks if r.get("risk_score", 0) >= 12]
            data_summary["risks"] = {
                "total": len(risks),
                "open": len(open_risks),
                "high_score_count": len(high_risks),
                "top_risks": [
                    {
                        "title": r.get("title"),
                        "category": r.get("category"),
                        "risk_score": r.get("risk_score"),
                        "likelihood": r.get("likelihood"),
                        "impact": r.get("impact"),
                        "status": r.get("status"),
                    }
                    for r in risks[:5]
                ],
            }
            data_used.append("risks")
        else:
            data_gaps.append("no risk register data")
    except Exception:
        data_gaps.append("no risk register data")

    # Gate readiness
    try:
        gate_rows = store.get_gate_readiness_history(project_id)
        if gate_rows:
            latest_gate = gate_rows[-1]
            data_summary["gate_readiness"] = {
                "gate": latest_gate.get("gate"),
                "readiness": latest_gate.get("readiness"),
                "composite_score": latest_gate.get("composite_score"),
                "assessed_at": latest_gate.get("assessed_at"),
            }
            data_used.append("gate_readiness")
        else:
            data_gaps.append("no gate readiness data")
    except Exception:
        data_gaps.append("no gate readiness data")

    # Financial baselines
    try:
        financial_baselines = store.get_financial_baselines(project_id)
        if financial_baselines:
            latest_baseline = financial_baselines[-1]
            data_summary["financial_baseline"] = {
                "label": latest_baseline.get("label"),
                "total_budget": latest_baseline.get("total_budget"),
                "created_at": latest_baseline.get("created_at"),
            }
            data_used.append("financial_baseline")
        else:
            data_gaps.append("no financial baseline data")
    except Exception:
        data_gaps.append("no financial baseline data")

    # Financial actuals
    try:
        actuals = store.get_financial_actuals(project_id)
        if actuals:
            latest_actual = actuals[-1]
            total_spend = sum(a.get("actual_spend", 0) for a in actuals)
            data_summary["financial_actuals"] = {
                "periods_recorded": len(actuals),
                "total_spend_to_date": total_spend,
                "latest_period": latest_actual.get("period"),
                "latest_actual_spend": latest_actual.get("actual_spend"),
            }
            data_used.append("financial_actuals")
        else:
            data_gaps.append("no financial actuals data")
    except Exception:
        data_gaps.append("no financial actuals data")

    # Benefits
    try:
        benefits = store.get_benefits(project_id)
        if benefits:
            by_status: dict[str, int] = {}
            for b in benefits:
                s = b.get("status", "UNKNOWN")
                by_status[s] = by_status.get(s, 0) + 1
            data_summary["benefits"] = {
                "total": len(benefits),
                "by_status": by_status,
            }
            data_used.append("benefits")
        else:
            data_gaps.append("no benefits data")
    except Exception:
        data_gaps.append("no benefits data")

    # Change requests (change pressure)
    try:
        change_requests = store.get_change_requests(project_id)
        if change_requests:
            approved = [c for c in change_requests if c.get("status") == "APPROVED"]
            total_cost_impact = sum(
                c.get("impact_cost", 0) or 0 for c in change_requests
            )
            total_schedule_impact = sum(
                c.get("impact_schedule_days", 0) or 0 for c in change_requests
            )
            data_summary["change_requests"] = {
                "total": len(change_requests),
                "approved": len(approved),
                "total_cost_impact": total_cost_impact,
                "total_schedule_impact_days": total_schedule_impact,
            }
            data_used.append("change_requests")
        else:
            data_gaps.append("no change request data")
    except Exception:
        data_gaps.append("no change request data")

    # ------------------------------------------------------------------ #
    # 4. Build Claude prompt                                               #
    # ------------------------------------------------------------------ #
    data_text = json.dumps(data_summary, indent=2, default=str)

    system_prompt = (
        "You are an independent assurance reviewer. "
        "Your job is to compare a project narrative against quantitative data "
        "and identify divergences that may indicate optimism bias or misrepresentation. "
        "Be rigorous and specific. Only flag claims that are explicitly or implicitly "
        "contradicted by the data. Do not infer data that is not present."
    )

    user_prompt = f"""You are reviewing a project narrative against quantitative assurance data.

PROJECT NARRATIVE:
{narrative_text}

QUANTITATIVE DATA FROM ASSURANCE STORE:
{data_text}

Instructions:
1. Identify specific factual claims made in the narrative (explicit or implicit).
2. For each claim, assess it against the quantitative data as one of:
   - SUPPORTED: the data confirms the claim
   - CONTRADICTED: the data contradicts the claim
   - UNVERIFIABLE: no relevant data is available to assess the claim
3. For any CONTRADICTED claim, assign a severity: HIGH, MEDIUM, or LOW.
   - HIGH: material misrepresentation (e.g. claiming on-track when SPI < 0.8, claiming budget is fine when spend is near or over)
   - MEDIUM: concerning divergence but not necessarily misleading (e.g. overstating benefits progress)
   - LOW: minor overstatement or tone that does not match data
4. Quote the exact phrase from the narrative and cite the specific evidence from the data.
5. For each claim, provide your confidence in the assessment (0.0–1.0).

Respond in the following JSON format exactly:
{{
  "claims": [
    {{
      "claim": "<exact phrase or paraphrase from narrative>",
      "verdict": "SUPPORTED" | "CONTRADICTED" | "UNVERIFIABLE",
      "severity": "HIGH" | "MEDIUM" | "LOW" | null,
      "evidence": "<specific data point or reason>",
      "confidence": <float 0.0-1.0>
    }}
  ]
}}

Only output the JSON. Do not add any commentary before or after."""

    # ------------------------------------------------------------------ #
    # 5. Call Claude                                                       #
    # ------------------------------------------------------------------ #
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw_response = message.content[0].text
    except Exception as exc:
        return {
            "error": {
                "code": "API_CALL_FAILED",
                "message": f"Claude API call failed: {exc}",
                "suggestion": "Check ANTHROPIC_API_KEY is valid and the API is reachable",
            }
        }

    # ------------------------------------------------------------------ #
    # 6. Parse response                                                    #
    # ------------------------------------------------------------------ #
    try:
        # Strip markdown code fences if present
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
        parsed = json.loads(cleaned)
        all_claims = parsed.get("claims", [])
    except Exception:
        return {
            "error": {
                "code": "PARSE_ERROR",
                "message": "Failed to parse Claude API response as JSON",
                "suggestion": "This is an internal error — try again or contact support",
                "raw_response": raw_response[:500],
            }
        }

    # ------------------------------------------------------------------ #
    # 7. Build structured output                                           #
    # ------------------------------------------------------------------ #
    _SEVERITY_WEIGHT = {"HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.25}

    flags: list[dict[str, Any]] = []
    supported_claims: list[dict[str, Any]] = []
    unverifiable_claims: list[dict[str, Any]] = []

    for claim_data in all_claims:
        verdict = claim_data.get("verdict", "UNVERIFIABLE")
        confidence = float(claim_data.get("confidence", 0.0))

        if verdict == "SUPPORTED":
            supported_claims.append(
                {
                    "claim": claim_data.get("claim", ""),
                    "evidence": claim_data.get("evidence", ""),
                }
            )
        elif verdict == "CONTRADICTED":
            # Only include flags that meet the confidence threshold
            if confidence >= confidence_threshold:
                flags.append(
                    {
                        "claim": claim_data.get("claim", ""),
                        "verdict": "CONTRADICTED",
                        "severity": claim_data.get("severity") or "LOW",
                        "evidence": claim_data.get("evidence", ""),
                        "confidence": round(confidence, 3),
                    }
                )
        elif verdict == "UNVERIFIABLE":
            unverifiable_claims.append(
                {
                    "claim": claim_data.get("claim", ""),
                    "reason": claim_data.get("evidence", "No quantitative data available"),
                }
            )

    # Divergence score: weighted proportion of assessed claims that are contradicted
    total_claims = len(all_claims)
    if total_claims == 0:
        divergence_score = 0.0
    else:
        weighted_contradictions = sum(
            _SEVERITY_WEIGHT.get(f.get("severity", "LOW"), 0.25) for f in flags
        )
        divergence_score = min(1.0, weighted_contradictions / total_claims)

    contradictions = len(flags)

    # Overall assessment
    high_contradiction_count = sum(1 for f in flags if f.get("severity") == "HIGH")
    if contradictions == 0:
        overall_assessment = "ALIGNED"
    elif high_contradiction_count >= 2:
        overall_assessment = "HIGHLY_DIVERGENT"
    elif high_contradiction_count >= 1 or contradictions >= 3:
        overall_assessment = "DIVERGENT"
    else:
        overall_assessment = "MINOR_DIVERGENCE"

    return {
        "project_id": project_id,
        "overall_assessment": overall_assessment,
        "divergence_score": round(divergence_score, 3),
        "claims_assessed": total_claims,
        "contradictions": contradictions,
        "flags": flags,
        "supported_claims": supported_claims,
        "unverifiable_claims": unverifiable_claims,
        "data_used": data_used,
        "data_gaps": data_gaps,
    }
