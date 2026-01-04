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
from typing import Any, Dict, List, Optional

from pm_mcp_servers.shared import project_store

from .analyzers import BaselineComparator, HealthAnalyzer, OutlierDetector
from .forecasters import ForecastEngine
from .models import AnalysisDepth, AnalysisMetadata, ForecastMethod
from .risk_engine import RiskEngine

logger = logging.getLogger(__name__)


# ============================================================================
# Tool 1: Identify Risks
# ============================================================================


async def identify_risks(params: Dict[str, Any]) -> Dict[str, Any]:
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
        by_category: Dict[str, int] = {}
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


async def forecast_completion(params: Dict[str, Any]) -> Dict[str, Any]:
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


async def detect_outliers(params: Dict[str, Any]) -> Dict[str, Any]:
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
        by_field: Dict[str, int] = {}
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


async def assess_health(params: Dict[str, Any]) -> Dict[str, Any]:
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


async def suggest_mitigations(params: Dict[str, Any]) -> Dict[str, Any]:
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
        by_strategy: Dict[str, int] = {}
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


async def compare_baseline(params: Dict[str, Any]) -> Dict[str, Any]:
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
        by_field: Dict[str, int] = {}
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
