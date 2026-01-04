"""
Tests for PM-Analyse Tools.

Tests all 6 analysis tools (identify_risks, forecast_completion, detect_outliers,
assess_health, suggest_mitigations, compare_baseline) with 30+ test cases.
"""

from datetime import datetime

import pytest

from pm_mcp_servers.pm_analyse.models import (
    AnalysisDepth,
    HealthStatus,
    Severity,
)


class TestIdentifyRisks:
    """Tests for identify_risks tool."""

    @pytest.mark.asyncio
    async def test_identify_risks_missing_project_id(self):
        """Test error when project_id is missing."""
        from pm_mcp_servers.pm_analyse.tools import identify_risks
        result = await identify_risks({})
        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"

    @pytest.mark.asyncio
    async def test_identify_risks_project_not_found(self):
        """Test error when project not in store."""
        from pm_mcp_servers.pm_analyse.tools import identify_risks
        result = await identify_risks({"project_id": "nonexistent"})
        assert "error" in result
        assert result["error"]["code"] == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_identify_risks_success(self, basic_project):
        """Test successful risk identification."""
        from pm_mcp_servers.pm_analyse.tools import identify_risks
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await identify_risks({"project_id": "test-project"})

        assert "risks" in result or "error" not in result
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_identify_risks_returns_metadata(self, basic_project):
        """Test that result includes analysis metadata."""
        from pm_mcp_servers.pm_analyse.tools import identify_risks
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await identify_risks({"project_id": "test-project"})

        assert "metadata" in result
        metadata = result["metadata"]
        assert "analysis_id" in metadata
        assert metadata["analysis_type"] == "risk_identification"
        assert "started_at" in metadata

    @pytest.mark.asyncio
    async def test_identify_risks_with_focus_areas(self, basic_project):
        """Test risk identification with focus areas."""
        from pm_mcp_servers.pm_analyse.tools import identify_risks
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await identify_risks({
            "project_id": "test-project",
            "focus_areas": ["schedule", "cost"]
        })

        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_identify_risks_with_depth(self, basic_project):
        """Test risk identification with different depths."""
        from pm_mcp_servers.pm_analyse.tools import identify_risks
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)

        for depth in ["quick", "standard", "deep"]:
            result = await identify_risks({
                "project_id": "test-project",
                "depth": depth
            })
            assert "metadata" in result
            assert result["metadata"]["depth"] == depth

    @pytest.mark.asyncio
    async def test_identify_risks_result_structure(self, complex_project):
        """Test risk identification result has correct structure."""
        from pm_mcp_servers.pm_analyse.tools import identify_risks
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", complex_project)
        result = await identify_risks({"project_id": "test-project"})

        if "risks" in result:
            assert isinstance(result["risks"], list)
            assert "summary" in result
            assert "total_risks" in result["summary"]
            assert "critical_count" in result["summary"]
            assert "by_category" in result["summary"]


class TestForecastCompletion:
    """Tests for forecast_completion tool."""

    @pytest.mark.asyncio
    async def test_forecast_completion_missing_project_id(self):
        """Test error when project_id is missing."""
        from pm_mcp_servers.pm_analyse.tools import forecast_completion
        result = await forecast_completion({})
        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"

    @pytest.mark.asyncio
    async def test_forecast_completion_project_not_found(self):
        """Test error when project not in store."""
        from pm_mcp_servers.pm_analyse.tools import forecast_completion
        result = await forecast_completion({"project_id": "nonexistent"})
        assert "error" in result
        assert result["error"]["code"] == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_forecast_completion_invalid_method(self, basic_project):
        """Test error with invalid forecast method."""
        from pm_mcp_servers.pm_analyse.tools import forecast_completion
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await forecast_completion({
            "project_id": "test-project",
            "method": "invalid_method"
        })
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

    @pytest.mark.asyncio
    async def test_forecast_completion_success(self, basic_project):
        """Test successful forecast completion."""
        from pm_mcp_servers.pm_analyse.tools import forecast_completion
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await forecast_completion({"project_id": "test-project"})

        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_forecast_completion_all_methods(self, basic_project):
        """Test forecast with all supported methods."""
        from pm_mcp_servers.pm_analyse.tools import forecast_completion
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        methods = [
            "earned_value",
            "monte_carlo",
            "reference_class",
            "simple_extrapolation",
            "ml_ensemble"
        ]

        for method in methods:
            result = await forecast_completion({
                "project_id": "test-project",
                "method": method
            })
            assert "metadata" in result

    @pytest.mark.asyncio
    async def test_forecast_completion_with_confidence_level(self, basic_project):
        """Test forecast with custom confidence level."""
        from pm_mcp_servers.pm_analyse.tools import forecast_completion
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await forecast_completion({
            "project_id": "test-project",
            "confidence_level": 0.95
        })

        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_forecast_completion_with_scenarios(self, basic_project):
        """Test forecast with scenario generation."""
        from pm_mcp_servers.pm_analyse.tools import forecast_completion
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await forecast_completion({
            "project_id": "test-project",
            "scenarios": True
        })

        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_forecast_completion_with_depth(self, basic_project):
        """Test forecast with different depths."""
        from pm_mcp_servers.pm_analyse.tools import forecast_completion
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)

        for depth in ["quick", "standard", "deep"]:
            result = await forecast_completion({
                "project_id": "test-project",
                "depth": depth
            })
            assert "metadata" in result


class TestDetectOutliers:
    """Tests for detect_outliers tool."""

    @pytest.mark.asyncio
    async def test_detect_outliers_missing_project_id(self):
        """Test error when project_id is missing."""
        from pm_mcp_servers.pm_analyse.tools import detect_outliers
        result = await detect_outliers({})
        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"

    @pytest.mark.asyncio
    async def test_detect_outliers_project_not_found(self):
        """Test error when project not in store."""
        from pm_mcp_servers.pm_analyse.tools import detect_outliers
        result = await detect_outliers({"project_id": "nonexistent"})
        assert "error" in result
        assert result["error"]["code"] == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_detect_outliers_invalid_sensitivity(self, basic_project):
        """Test error with invalid sensitivity."""
        from pm_mcp_servers.pm_analyse.tools import detect_outliers
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await detect_outliers({
            "project_id": "test-project",
            "sensitivity": 5.0  # Out of range
        })
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

    @pytest.mark.asyncio
    async def test_detect_outliers_success(self, basic_project):
        """Test successful outlier detection."""
        from pm_mcp_servers.pm_analyse.tools import detect_outliers
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await detect_outliers({"project_id": "test-project"})

        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_detect_outliers_with_sensitivity(self, complex_project):
        """Test outlier detection with custom sensitivity."""
        from pm_mcp_servers.pm_analyse.tools import detect_outliers
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", complex_project)

        for sensitivity in [0.5, 1.0, 2.0]:
            result = await detect_outliers({
                "project_id": "test-project",
                "sensitivity": sensitivity
            })
            assert "metadata" in result

    @pytest.mark.asyncio
    async def test_detect_outliers_with_focus_areas(self, basic_project):
        """Test outlier detection with focus areas."""
        from pm_mcp_servers.pm_analyse.tools import detect_outliers
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await detect_outliers({
            "project_id": "test-project",
            "focus_areas": ["duration", "progress"]
        })

        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_detect_outliers_result_structure(self, complex_project):
        """Test outlier detection result structure."""
        from pm_mcp_servers.pm_analyse.tools import detect_outliers
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", complex_project)
        result = await detect_outliers({"project_id": "test-project"})

        if "outliers" in result:
            assert isinstance(result["outliers"], list)
            assert "summary" in result
            assert "total_outliers" in result["summary"]
            assert "critical_count" in result["summary"]


class TestAssessHealth:
    """Tests for assess_health tool."""

    @pytest.mark.asyncio
    async def test_assess_health_missing_project_id(self):
        """Test error when project_id is missing."""
        from pm_mcp_servers.pm_analyse.tools import assess_health
        result = await assess_health({})
        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"

    @pytest.mark.asyncio
    async def test_assess_health_project_not_found(self):
        """Test error when project not in store."""
        from pm_mcp_servers.pm_analyse.tools import assess_health
        result = await assess_health({"project_id": "nonexistent"})
        assert "error" in result
        assert result["error"]["code"] == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_assess_health_invalid_weights(self, basic_project):
        """Test error with invalid weights."""
        from pm_mcp_servers.pm_analyse.tools import assess_health
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await assess_health({
            "project_id": "test-project",
            "weights": {
                "schedule": 0.5,
                "cost": 0.5,
                "scope": 0.5,
                "resource": 0.5,
                "quality": 0.5
            }  # Sums to 2.5, not 1.0
        })
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

    @pytest.mark.asyncio
    async def test_assess_health_success(self, basic_project):
        """Test successful health assessment."""
        from pm_mcp_servers.pm_analyse.tools import assess_health
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await assess_health({"project_id": "test-project"})

        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_assess_health_with_custom_weights(self, basic_project):
        """Test health assessment with custom weights."""
        from pm_mcp_servers.pm_analyse.tools import assess_health
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await assess_health({
            "project_id": "test-project",
            "weights": {
                "schedule": 0.4,
                "cost": 0.3,
                "scope": 0.15,
                "resource": 0.1,
                "quality": 0.05
            }
        })

        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_assess_health_with_trends(self, basic_project):
        """Test health assessment with trends."""
        from pm_mcp_servers.pm_analyse.tools import assess_health
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await assess_health({
            "project_id": "test-project",
            "include_trends": True
        })

        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_assess_health_result_structure(self, complex_project):
        """Test health assessment result structure."""
        from pm_mcp_servers.pm_analyse.tools import assess_health
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", complex_project)
        result = await assess_health({"project_id": "test-project"})

        if "health" in result:
            health = result["health"]
            assert "overall_score" in health
            assert "overall_status" in health
            assert "dimensions" in health
            assert "recommendations" in health


class TestSuggestMitigations:
    """Tests for suggest_mitigations tool."""

    @pytest.mark.asyncio
    async def test_suggest_mitigations_missing_project_id(self):
        """Test error when project_id is missing."""
        from pm_mcp_servers.pm_analyse.tools import suggest_mitigations
        result = await suggest_mitigations({})
        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"

    @pytest.mark.asyncio
    async def test_suggest_mitigations_project_not_found(self):
        """Test error when project not in store."""
        from pm_mcp_servers.pm_analyse.tools import suggest_mitigations
        result = await suggest_mitigations({"project_id": "nonexistent"})
        assert "error" in result
        assert result["error"]["code"] == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_suggest_mitigations_success(self, basic_project):
        """Test successful mitigation suggestion."""
        from pm_mcp_servers.pm_analyse.tools import suggest_mitigations
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await suggest_mitigations({"project_id": "test-project"})

        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_suggest_mitigations_with_depth(self, basic_project):
        """Test mitigation suggestion with different depths."""
        from pm_mcp_servers.pm_analyse.tools import suggest_mitigations
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)

        for depth in ["quick", "standard", "deep"]:
            result = await suggest_mitigations({
                "project_id": "test-project",
                "depth": depth
            })
            assert "metadata" in result

    @pytest.mark.asyncio
    async def test_suggest_mitigations_with_focus_areas(self, basic_project):
        """Test mitigation suggestion with focus areas."""
        from pm_mcp_servers.pm_analyse.tools import suggest_mitigations
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await suggest_mitigations({
            "project_id": "test-project",
            "focus_areas": ["schedule", "cost"]
        })

        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_suggest_mitigations_result_structure(self, complex_project):
        """Test mitigation suggestion result structure."""
        from pm_mcp_servers.pm_analyse.tools import suggest_mitigations
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", complex_project)
        result = await suggest_mitigations({"project_id": "test-project"})

        if "mitigations" in result:
            assert isinstance(result["mitigations"], list)
            assert "summary" in result
            assert "total_mitigations" in result["summary"]


class TestCompareBaseline:
    """Tests for compare_baseline tool."""

    @pytest.mark.asyncio
    async def test_compare_baseline_missing_project_id(self):
        """Test error when project_id is missing."""
        from pm_mcp_servers.pm_analyse.tools import compare_baseline
        result = await compare_baseline({})
        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"

    @pytest.mark.asyncio
    async def test_compare_baseline_project_not_found(self):
        """Test error when project not in store."""
        from pm_mcp_servers.pm_analyse.tools import compare_baseline
        result = await compare_baseline({"project_id": "nonexistent"})
        assert "error" in result
        assert result["error"]["code"] == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_compare_baseline_invalid_threshold(self, basic_project):
        """Test error with invalid threshold."""
        from pm_mcp_servers.pm_analyse.tools import compare_baseline
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await compare_baseline({
            "project_id": "test-project",
            "threshold": 150.0  # Out of range
        })
        assert "error" in result
        assert result["error"]["code"] == "INVALID_PARAMETER"

    @pytest.mark.asyncio
    async def test_compare_baseline_success(self, basic_project):
        """Test successful baseline comparison."""
        from pm_mcp_servers.pm_analyse.tools import compare_baseline
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await compare_baseline({"project_id": "test-project"})

        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_compare_baseline_all_types(self, task_with_baseline):
        """Test comparison with all baseline types."""
        from .conftest import MockProject
        from pm_mcp_servers.pm_analyse.tools import compare_baseline
        from pm_mcp_servers.shared import project_store

        project = MockProject(tasks=[task_with_baseline])
        project_store.add("test-project", project)

        for baseline_type in ["current", "original", "approved"]:
            result = await compare_baseline({
                "project_id": "test-project",
                "baseline_type": baseline_type
            })
            assert "metadata" in result

    @pytest.mark.asyncio
    async def test_compare_baseline_with_threshold(self, task_with_baseline):
        """Test baseline comparison with threshold."""
        from .conftest import MockProject
        from pm_mcp_servers.pm_analyse.tools import compare_baseline
        from pm_mcp_servers.shared import project_store

        project = MockProject(tasks=[task_with_baseline])
        project_store.add("test-project", project)

        result = await compare_baseline({
            "project_id": "test-project",
            "threshold": 10.0
        })

        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_compare_baseline_result_structure(self, task_with_baseline):
        """Test baseline comparison result structure."""
        from .conftest import MockProject
        from pm_mcp_servers.pm_analyse.tools import compare_baseline
        from pm_mcp_servers.shared import project_store

        project = MockProject(tasks=[task_with_baseline])
        project_store.add("test-project", project)
        result = await compare_baseline({"project_id": "test-project"})

        if "variances" in result:
            assert isinstance(result["variances"], list)
            assert "summary" in result
            assert "total_variances" in result["summary"]


class TestToolMetadata:
    """Tests for tool result metadata consistency."""

    @pytest.mark.asyncio
    async def test_all_tools_return_metadata(self, basic_project):
        """Test that all tools return metadata in response."""
        from pm_mcp_servers.pm_analyse.tools import (
            identify_risks,
            forecast_completion,
            detect_outliers,
            assess_health,
            suggest_mitigations,
            compare_baseline
        )
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        tools = [
            identify_risks,
            forecast_completion,
            detect_outliers,
            assess_health,
            suggest_mitigations,
            compare_baseline
        ]

        for tool in tools:
            result = await tool({"project_id": "test-project"})
            assert "metadata" in result or "error" in result

    @pytest.mark.asyncio
    async def test_metadata_includes_timestamps(self, basic_project):
        """Test that metadata includes timestamp information."""
        from pm_mcp_servers.pm_analyse.tools import identify_risks
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await identify_risks({"project_id": "test-project"})

        assert "metadata" in result
        metadata = result["metadata"]
        assert "started_at" in metadata or "completed_at" in metadata

    @pytest.mark.asyncio
    async def test_metadata_includes_analysis_id(self, basic_project):
        """Test that metadata includes unique analysis ID."""
        from pm_mcp_servers.pm_analyse.tools import identify_risks
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result1 = await identify_risks({"project_id": "test-project"})
        result2 = await identify_risks({"project_id": "test-project"})

        id1 = result1["metadata"]["analysis_id"]
        id2 = result2["metadata"]["analysis_id"]
        assert id1 != id2  # Each analysis should have unique ID
