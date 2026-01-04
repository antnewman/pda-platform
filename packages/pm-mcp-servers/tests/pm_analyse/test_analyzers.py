"""
Tests for PM-Analyse Analyzers.

Tests OutlierDetector, HealthAnalyzer, and BaselineComparator classes
with 25+ test cases covering normal operation, edge cases, and error handling.
"""

from datetime import date, timedelta

import pytest

from pm_mcp_servers.pm_analyse.analyzers import (
    BaselineComparator,
    HealthAnalyzer,
    OutlierDetector,
)
from pm_mcp_servers.pm_analyse.models import (
    HealthStatus,
    Severity,
    TrendDirection,
)

# Import mock classes from conftest
from .conftest import MockProject, MockTask, MockResource, MockCost


class TestOutlierDetector:
    """Tests for OutlierDetector class."""

    def test_detector_initialization(self):
        """Test outlier detector can be initialized."""
        detector = OutlierDetector()
        assert detector is not None
        assert hasattr(detector, 'detect')

    def test_detect_empty_project(self, empty_project):
        """Test detection on project with no tasks."""
        detector = OutlierDetector()
        outliers = detector.detect(empty_project)
        assert isinstance(outliers, list)
        assert len(outliers) == 0

    def test_detect_simple_project(self, simple_task):
        """Test detection returns outliers as list."""
        from tests.pm_analyse.conftest import MockProject
        project = MockProject(tasks=[simple_task])
        detector = OutlierDetector()
        outliers = detector.detect(project)
        assert isinstance(outliers, list)

    def test_detect_duration_outliers_long_task(self, long_duration_task):
        """Test detection of tasks with unusually long duration."""
        from .conftest import MockProject
        project = MockProject(tasks=[long_duration_task])
        detector = OutlierDetector()
        outliers = detector.detect(project, focus_areas=["duration"])
        # Long task (200 days) should exceed max threshold
        assert len(outliers) > 0
        assert any(o.field == "duration" for o in outliers)

    def test_detect_progress_outliers_stuck_task(self, stuck_task):
        """Test detection of stuck tasks."""
        from .conftest import MockProject
        project = MockProject(tasks=[stuck_task])
        detector = OutlierDetector()
        outliers = detector.detect(project, focus_areas=["progress"])
        # Stuck task should be detected
        assert len(outliers) > 0
        assert any(o.field == "percent_complete" for o in outliers)

    def test_detect_float_outliers_negative_float(self):
        """Test detection of negative float (critical)."""
        from .conftest import MockProject, MockTask
        task = MockTask(
            id='task-1',
            name='Critical Float Task',
            total_float=-10,
            is_critical=False
        )
        project = MockProject(tasks=[task])
        detector = OutlierDetector()
        outliers = detector.detect(project, focus_areas=["float"])
        assert len(outliers) > 0
        critical_float = [o for o in outliers if o.field == "total_float" and o.severity == Severity.CRITICAL]
        assert len(critical_float) > 0

    def test_detect_float_outliers_excessive(self):
        """Test detection of excessive float on non-critical tasks."""
        from .conftest import MockProject, MockTask
        task = MockTask(
            id='task-1',
            name='Loose Task',
            total_float=100,
            is_critical=False
        )
        project = MockProject(tasks=[task])
        detector = OutlierDetector()
        outliers = detector.detect(project, focus_areas=["float"])
        assert any(o.field == "total_float" for o in outliers)

    def test_detect_date_outliers_invalid_dates(self):
        """Test detection of impossible dates (finish before start)."""
        from .conftest import MockProject, MockTask
        task = MockTask(
            id='task-1',
            name='Invalid Date Task',
            start_date=date.today(),
            finish_date=date.today() - timedelta(days=1)
        )
        project = MockProject(tasks=[task])
        detector = OutlierDetector()
        outliers = detector.detect(project, focus_areas=["dates"])
        assert len(outliers) > 0
        assert any(o.field == "dates" and o.severity == Severity.CRITICAL for o in outliers)

    def test_detect_date_outliers_overdue_incomplete(self):
        """Test detection of overdue incomplete tasks."""
        from .conftest import MockProject, MockTask
        task = MockTask(
            id='task-1',
            name='Overdue Task',
            start_date=date.today() - timedelta(days=60),
            finish_date=date.today() - timedelta(days=40),
            percent_complete=50
        )
        project = MockProject(tasks=[task])
        detector = OutlierDetector()
        outliers = detector.detect(project, focus_areas=["dates"])
        assert len(outliers) > 0

    def test_detect_with_sensitivity_low(self, complex_project):
        """Test detection with low sensitivity (less sensitive)."""
        detector = OutlierDetector()
        outliers = detector.detect(complex_project, sensitivity=0.5)
        assert isinstance(outliers, list)

    def test_detect_with_sensitivity_high(self, complex_project):
        """Test detection with high sensitivity (more sensitive)."""
        detector = OutlierDetector()
        outliers = detector.detect(complex_project, sensitivity=2.0)
        assert isinstance(outliers, list)

    def test_detect_focus_single_area(self, complex_project):
        """Test detection focusing on single area."""
        detector = OutlierDetector()
        outliers = detector.detect(complex_project, focus_areas=["duration"])
        assert all(o.field in ["duration"] for o in outliers)

    def test_detect_focus_multiple_areas(self, complex_project):
        """Test detection focusing on multiple areas."""
        detector = OutlierDetector()
        outliers = detector.detect(
            complex_project,
            focus_areas=["duration", "progress"]
        )
        for outlier in outliers:
            assert outlier.field in ["duration", "percent_complete"]

    def test_detect_summary_tasks_excluded(self):
        """Test that summary tasks are excluded from detection."""
        from .conftest import MockProject, MockTask
        summary = MockTask(
            id='summary-1',
            name='Summary Task',
            is_summary=True
        )
        work_task = MockTask(id='task-1', name='Work Task')
        project = MockProject(tasks=[summary, work_task])
        detector = OutlierDetector()
        outliers = detector.detect(project)
        # Should only analyze work_task
        assert all(o.task_id != 'summary-1' for o in outliers)

    def test_detect_outlier_has_evidence(self):
        """Test that detected outliers include evidence."""
        from .conftest import MockProject, MockTask
        task = MockTask(
            id='task-1',
            name='Test Task',
            start_date=date.today(),
            finish_date=date.today() - timedelta(days=1)
        )
        project = MockProject(tasks=[task])
        detector = OutlierDetector()
        outliers = detector.detect(project)
        assert all(len(o.evidence) > 0 for o in outliers)

    def test_detect_outlier_has_confidence(self):
        """Test that detected outliers have confidence scores."""
        from .conftest import MockProject, MockTask
        task = MockTask(
            id='task-1',
            name='Test Task',
            start_date=date.today(),
            finish_date=date.today() - timedelta(days=1)
        )
        project = MockProject(tasks=[task])
        detector = OutlierDetector()
        outliers = detector.detect(project)
        assert all(0.0 <= o.confidence <= 1.0 for o in outliers)

    def test_detect_date_outlier_100_percent_future_finish(self):
        """Test detection of impossible progress (100% but future finish)."""
        from .conftest import MockProject, MockTask
        task = MockTask(
            id='task-1',
            name='Impossible Progress Task',
            start_date=date.today() - timedelta(days=10),
            finish_date=date.today() + timedelta(days=10),
            percent_complete=100
        )
        project = MockProject(tasks=[task])
        detector = OutlierDetector()
        outliers = detector.detect(project, focus_areas=["progress"])
        assert len(outliers) > 0
        assert any(o.severity == Severity.HIGH for o in outliers)


class TestHealthAnalyzer:
    """Tests for HealthAnalyzer class."""

    def test_analyzer_initialization(self):
        """Test health analyzer can be initialized."""
        analyzer = HealthAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, 'assess')

    def test_assess_empty_project(self, empty_project):
        """Test health assessment on empty project."""
        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(empty_project)
        assert assessment is not None
        assert 0.0 <= assessment.overall_score <= 100.0

    def test_assess_basic_project(self, basic_project):
        """Test health assessment on basic project."""
        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(basic_project)
        assert assessment.overall_score > 0
        assert assessment.overall_status in [
            HealthStatus.HEALTHY,
            HealthStatus.AT_RISK,
            HealthStatus.CRITICAL
        ]

    def test_assess_complex_project(self, complex_project):
        """Test health assessment on complex project."""
        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(complex_project)
        assert len(assessment.dimensions) == 5
        assert all(d.name in [
            "Schedule", "Cost", "Scope", "Resource", "Quality"
        ] for d in assessment.dimensions)

    def test_assess_has_all_dimensions(self, basic_project):
        """Test that assessment includes all 5 dimensions."""
        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(basic_project)
        dimension_names = {d.name for d in assessment.dimensions}
        expected = {"Schedule", "Cost", "Scope", "Resource", "Quality"}
        assert dimension_names == expected

    def test_assess_overall_score_range(self, basic_project):
        """Test that overall score is within valid range."""
        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(basic_project)
        assert 0.0 <= assessment.overall_score <= 100.0

    def test_assess_confidence_range(self, basic_project):
        """Test that confidence is within valid range."""
        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(basic_project)
        assert 0.0 <= assessment.confidence <= 1.0

    def test_assess_dimension_scores_valid(self, complex_project):
        """Test that dimension scores are within valid range."""
        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(complex_project)
        assert all(0.0 <= d.score <= 100.0 for d in assessment.dimensions)

    def test_assess_dimension_weights_valid(self, basic_project):
        """Test that dimension weights are within valid range."""
        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(basic_project)
        assert all(0.0 <= d.weight <= 1.0 for d in assessment.dimensions)

    def test_assess_custom_weights(self, basic_project):
        """Test assessment with custom dimension weights."""
        analyzer = HealthAnalyzer()
        custom_weights = {
            "schedule": 0.4,
            "cost": 0.3,
            "scope": 0.15,
            "resource": 0.1,
            "quality": 0.05
        }
        assessment = analyzer.assess(basic_project, weights=custom_weights)
        assert assessment is not None

    def test_assess_healthy_project(self):
        """Test assessment recognizes healthy project."""
        from .conftest import MockProject, MockTask, MockResource, MockCost
        tasks = [
            MockTask(id='t1', name='Task 1', percent_complete=80),
            MockTask(id='t2', name='Task 2', percent_complete=90)
        ]
        project = MockProject(
            tasks=tasks,
            resources=[MockResource()],
            budget=MockCost(100000),
            actual_cost=MockCost(50000),
            forecast_cost=MockCost(95000)
        )
        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(project)
        # Good progress and budget should result in healthy status
        assert assessment.overall_status in [
            HealthStatus.HEALTHY,
            HealthStatus.AT_RISK
        ]

    def test_assess_critical_project(self, project_over_budget):
        """Test assessment recognizes critical project."""
        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(project_over_budget)
        # Over budget project should be at risk or critical
        assert assessment.overall_status in [
            HealthStatus.AT_RISK,
            HealthStatus.CRITICAL
        ]

    def test_assess_with_trends(self, basic_project):
        """Test assessment includes trend information."""
        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(basic_project, include_trends=True)
        assert all(d.trend != TrendDirection.UNKNOWN for d in assessment.dimensions)

    def test_assess_dimensions_have_status(self, basic_project):
        """Test that all dimensions have health status."""
        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(basic_project)
        assert all(
            d.status in [
                HealthStatus.HEALTHY,
                HealthStatus.AT_RISK,
                HealthStatus.CRITICAL,
                HealthStatus.UNKNOWN
            ]
            for d in assessment.dimensions
        )

    def test_assess_has_recommendations(self, complex_project):
        """Test that assessment includes recommendations."""
        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(complex_project)
        assert isinstance(assessment.recommendations, list)
        assert len(assessment.recommendations) > 0

    def test_assess_has_top_concerns(self, basic_project):
        """Test that assessment includes top concerns."""
        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(basic_project)
        assert isinstance(assessment.top_concerns, list)

    def test_assess_to_dict(self, basic_project):
        """Test that assessment can be serialized to dict."""
        analyzer = HealthAnalyzer()
        assessment = analyzer.assess(basic_project)
        data = assessment.to_dict()
        assert "overall_score" in data
        assert "overall_status" in data
        assert "dimensions" in data
        assert "recommendations" in data


class TestBaselineComparator:
    """Tests for BaselineComparator class."""

    def test_comparator_initialization(self):
        """Test baseline comparator can be initialized."""
        comparator = BaselineComparator()
        assert comparator is not None
        assert hasattr(comparator, 'compare')

    def test_compare_empty_project(self, empty_project):
        """Test comparison on project with no tasks."""
        comparator = BaselineComparator()
        variances = comparator.compare(empty_project)
        assert isinstance(variances, list)
        assert len(variances) == 0

    def test_compare_no_baseline_data(self, basic_project):
        """Test comparison on project without baseline data."""
        comparator = BaselineComparator()
        variances = comparator.compare(basic_project)
        assert isinstance(variances, list)
        # No baseline data means no variances
        assert len(variances) == 0

    def test_compare_with_baseline_variance(self, task_with_baseline):
        """Test comparison detects baseline variance."""
        from .conftest import MockProject
        project = MockProject(tasks=[task_with_baseline])
        comparator = BaselineComparator()
        variances = comparator.compare(project)
        assert len(variances) > 0
        assert any(v.field == "finish_date" for v in variances)

    def test_compare_variance_attributes(self, task_with_baseline):
        """Test variance has all required attributes."""
        from .conftest import MockProject
        project = MockProject(tasks=[task_with_baseline])
        comparator = BaselineComparator()
        variances = comparator.compare(project)
        assert all(v.task_id for v in variances)
        assert all(v.task_name for v in variances)
        assert all(v.field for v in variances)
        assert all(v.severity in [
            Severity.CRITICAL,
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW
        ] for v in variances)

    def test_compare_with_threshold(self, task_with_baseline):
        """Test comparison with variance threshold."""
        from .conftest import MockProject
        project = MockProject(tasks=[task_with_baseline])
        comparator = BaselineComparator()
        variances_all = comparator.compare(project, threshold=0)
        variances_filtered = comparator.compare(project, threshold=50)
        # Filtered should have fewer or equal variances
        assert len(variances_filtered) <= len(variances_all)

    def test_compare_variance_severity_classification(self, task_with_baseline):
        """Test variance severity is correctly classified."""
        from .conftest import MockProject
        project = MockProject(tasks=[task_with_baseline])
        comparator = BaselineComparator()
        variances = comparator.compare(project)
        # Task slips 15 days, should be critical (>14 days)
        assert any(v.severity == Severity.CRITICAL for v in variances)

    def test_compare_variance_percentage(self, task_with_baseline):
        """Test variance includes percentage calculation."""
        from .conftest import MockProject
        project = MockProject(tasks=[task_with_baseline])
        comparator = BaselineComparator()
        variances = comparator.compare(project)
        assert all(isinstance(v.variance_percent, float) for v in variances)

    def test_compare_to_dict(self, task_with_baseline):
        """Test that variance can be serialized to dict."""
        from .conftest import MockProject
        project = MockProject(tasks=[task_with_baseline])
        comparator = BaselineComparator()
        variances = comparator.compare(project)
        if variances:
            data = variances[0].to_dict()
            assert "task_id" in data
            assert "field" in data
            assert "variance" in data
            assert "severity" in data

    def test_compare_multiple_tasks_with_variance(self):
        """Test comparison with multiple tasks having variance."""
        from .conftest import MockProject, MockTask
        tasks = [
            MockTask(
                id='task-1',
                name='Task 1',
                start_date=date.today(),
                finish_date=date.today() + timedelta(days=25),
                baseline_finish=date.today() + timedelta(days=10),
                baseline_start=date.today(),
                baseline_duration=10
            ),
            MockTask(
                id='task-2',
                name='Task 2',
                start_date=date.today(),
                finish_date=date.today() + timedelta(days=20),
                baseline_finish=date.today() + timedelta(days=5),
                baseline_start=date.today(),
                baseline_duration=5
            )
        ]
        project = MockProject(tasks=tasks)
        comparator = BaselineComparator()
        variances = comparator.compare(project)
        assert len(variances) >= 2

    def test_compare_pulls_in_vs_slips(self):
        """Test comparison detects both slippage and pull-in."""
        from .conftest import MockProject, MockTask
        slip_task = MockTask(
            id='task-slip',
            name='Slipping Task',
            start_date=date.today(),
            finish_date=date.today() + timedelta(days=20),
            baseline_finish=date.today() + timedelta(days=10)
        )
        pullin_task = MockTask(
            id='task-pullin',
            name='Pull-in Task',
            start_date=date.today(),
            finish_date=date.today() + timedelta(days=5),
            baseline_finish=date.today() + timedelta(days=10)
        )
        project = MockProject(tasks=[slip_task, pullin_task])
        comparator = BaselineComparator()
        variances = comparator.compare(project)
        # Should detect both positive and negative variance
        assert any(v.variance > 0 for v in variances)
        assert any(v.variance < 0 for v in variances)

    def test_compare_summary_tasks_excluded(self):
        """Test that summary tasks are excluded from comparison."""
        from .conftest import MockProject, MockTask
        summary = MockTask(
            id='summary-1',
            name='Summary Task',
            is_summary=True
        )
        work_task = MockTask(
            id='task-1',
            name='Work Task',
            baseline_finish=date.today(),
            finish_date=date.today() + timedelta(days=10)
        )
        project = MockProject(tasks=[summary, work_task])
        comparator = BaselineComparator()
        variances = comparator.compare(project)
        # Should only compare work_task
        assert all(v.task_id != 'summary-1' for v in variances)
