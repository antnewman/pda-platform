"""
Integration tests for PM-Analyse module.

Tests end-to-end workflows combining multiple analyzers and tools,
verifying component interactions and data flow with 10+ test cases.
"""

from datetime import date, timedelta

import pytest

from pm_mcp_servers.pm_analyse.models import (
    HealthStatus,
    Severity,
)


class TestAnalysisWorkflows:
    """Integration tests for complete analysis workflows."""

    def test_outlier_detection_feeds_health_assessment(self, complex_project):
        """Test that outlier detection and health assessment work together."""
        from pm_mcp_servers.pm_analyse.analyzers import (
            OutlierDetector,
            HealthAnalyzer,
        )

        detector = OutlierDetector()
        analyzer = HealthAnalyzer()

        outliers = detector.detect(complex_project)
        assessment = analyzer.assess(complex_project)

        # Both should complete without errors
        assert isinstance(outliers, list)
        assert assessment.overall_score >= 0

    def test_risk_identification_and_mitigation_flow(self, complex_project):
        """Test risk identification followed by mitigation generation."""
        from pm_mcp_servers.pm_analyse.risk_engine import RiskEngine

        engine = RiskEngine()
        risks = engine.analyze(complex_project)

        if risks:
            mitigations = engine.generate_mitigations(risks[:3])
            assert all(m.risk_id for m in mitigations)
            assert all(m.strategy for m in mitigations)

    def test_baseline_comparison_with_health_assessment(self, task_with_baseline):
        """Test baseline comparison integrated with health assessment."""
        from .conftest import MockProject
        from pm_mcp_servers.pm_analyse.analyzers import (
            BaselineComparator,
            HealthAnalyzer,
        )

        project = MockProject(tasks=[task_with_baseline])
        comparator = BaselineComparator()
        analyzer = HealthAnalyzer()

        variances = comparator.compare(project)
        assessment = analyzer.assess(project)

        # Both should work together
        assert isinstance(variances, list)
        assert assessment.overall_score >= 0
        # Variances should impact health status
        if variances:
            assert assessment.overall_status in [
                HealthStatus.AT_RISK,
                HealthStatus.CRITICAL
            ]

    def test_complete_project_analysis_workflow(self, complex_project):
        """Test complete analysis workflow on complex project."""
        from pm_mcp_servers.pm_analyse.analyzers import (
            OutlierDetector,
            HealthAnalyzer,
            BaselineComparator,
        )
        from pm_mcp_servers.pm_analyse.risk_engine import RiskEngine
        from pm_mcp_servers.pm_analyse.forecasters import ForecastEngine

        # Run all analyses
        detector = OutlierDetector()
        outliers = detector.detect(complex_project)

        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(complex_project)

        comparator = BaselineComparator()
        variances = comparator.compare(complex_project)

        engine = RiskEngine()
        risks = engine.analyze(complex_project)

        forecast_engine = ForecastEngine()
        forecast = forecast_engine.forecast(complex_project)

        # All components should complete
        assert isinstance(outliers, list)
        assert assessment is not None
        assert isinstance(variances, list)
        assert isinstance(risks, list)
        assert forecast is not None

    def test_outlier_detection_consistency(self, complex_project):
        """Test that outlier detection produces consistent results."""
        from pm_mcp_servers.pm_analyse.analyzers import OutlierDetector

        detector = OutlierDetector()
        outliers1 = detector.detect(complex_project)
        outliers2 = detector.detect(complex_project)

        # Same project should produce same number of outliers
        assert len(outliers1) == len(outliers2)

    def test_health_assessment_consistency(self, basic_project):
        """Test that health assessment produces consistent results."""
        from pm_mcp_servers.pm_analyse.analyzers import HealthAnalyzer

        analyzer = HealthAnalyzer()
        assessment1 = analyzer.assess(basic_project)
        assessment2 = analyzer.assess(basic_project)

        # Same project should produce same overall score
        assert assessment1.overall_score == assessment2.overall_score

    def test_multiple_analysis_depths(self, complex_project):
        """Test analysis with different depth levels."""
        from pm_mcp_servers.pm_analyse.risk_engine import RiskEngine
        from pm_mcp_servers.pm_analyse.models import AnalysisDepth

        engine = RiskEngine()

        risks_quick = engine.analyze(
            complex_project,
            depth=AnalysisDepth.QUICK
        )
        risks_standard = engine.analyze(
            complex_project,
            depth=AnalysisDepth.STANDARD
        )
        risks_deep = engine.analyze(
            complex_project,
            depth=AnalysisDepth.DEEP
        )

        # All should complete
        assert isinstance(risks_quick, list)
        assert isinstance(risks_standard, list)
        assert isinstance(risks_deep, list)
        # Deeper analysis may find more risks
        assert len(risks_deep) >= len(risks_quick)

    def test_analysis_on_empty_vs_populated_project(self):
        """Test analysis behavior on empty vs populated projects."""
        from .conftest import MockProject, MockTask
        from pm_mcp_servers.pm_analyse.analyzers import HealthAnalyzer

        empty_project = MockProject()
        task = MockTask(id='t1', name='Task 1', percent_complete=50)
        populated_project = MockProject(tasks=[task])

        analyzer = HealthAnalyzer()
        empty_assessment = analyzer.assess(empty_project)
        populated_assessment = analyzer.assess(populated_project)

        # Both should complete
        assert empty_assessment is not None
        assert populated_assessment is not None
        # Both should have valid scores
        assert 0 <= empty_assessment.overall_score <= 100
        assert 0 <= populated_assessment.overall_score <= 100

    def test_analysis_result_data_integrity(self, complex_project):
        """Test that analysis results maintain data integrity."""
        from pm_mcp_servers.pm_analyse.analyzers import OutlierDetector

        detector = OutlierDetector()
        outliers = detector.detect(complex_project)

        # Verify all outliers have required fields
        for outlier in outliers:
            assert outlier.id
            assert outlier.task_id
            assert outlier.task_name
            assert outlier.field
            assert 0.0 <= outlier.confidence <= 1.0
            assert outlier.severity in [
                Severity.CRITICAL,
                Severity.HIGH,
                Severity.MEDIUM,
                Severity.LOW
            ]
            assert outlier.explanation
            # Evidence should be present for outliers
            assert len(outlier.evidence) > 0

    def test_tool_integration_with_project_store(self, basic_project):
        """Test tool execution with project store integration."""
        from pm_mcp_servers.pm_analyse.tools import identify_risks
        from pm_mcp_servers.shared import project_store
        import asyncio

        project_store.add("integration-test", basic_project)

        async def run_test():
            result = await identify_risks({"project_id": "integration-test"})
            assert "metadata" in result
            return result

        result = asyncio.run(run_test())
        assert result is not None
