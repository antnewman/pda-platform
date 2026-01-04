"""
Tests for PM-Analyse risk identification engine.

Tests all risk detection methods and mitigation generation.
"""

from datetime import date, timedelta

import pytest

from pm_mcp_servers.pm_analyse.models import AnalysisDepth, RiskCategory, Severity
from pm_mcp_servers.pm_analyse.risk_engine import RiskEngine

from .conftest import MockCost, MockTask


class TestRiskEngineBasics:
    """Tests for basic risk engine functionality."""

    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        engine = RiskEngine()
        assert engine.risks == []

    def test_analyze_empty_project(self, empty_project):
        """Test analyzing project with no tasks."""
        engine = RiskEngine()
        risks = engine.analyze(empty_project)
        assert isinstance(risks, list)

    def test_analyze_returns_risks(self, basic_project):
        """Test analyze returns risk objects."""
        engine = RiskEngine()
        risks = engine.analyze(basic_project)
        assert isinstance(risks, list)
        for risk in risks:
            assert hasattr(risk, 'id')
            assert hasattr(risk, 'category')
            assert hasattr(risk, 'confidence')


class TestScheduleRiskDetection:
    """Tests for schedule risk detection."""

    def test_detect_overdue_task(self, overdue_task):
        """Test detection of overdue tasks."""
        from .conftest import MockProject
        project = MockProject(tasks=[overdue_task])

        engine = RiskEngine()
        risks = engine.analyze(project, focus_areas=["schedule"])

        schedule_risks = [r for r in risks if r.category == RiskCategory.SCHEDULE]
        assert len(schedule_risks) > 0

        overdue_risks = [r for r in schedule_risks if "Overdue" in r.name]
        assert len(overdue_risks) > 0

    def test_detect_critical_overdue(self):
        """Test critical overdue task detection."""
        from .conftest import MockProject
        task = MockTask(
            id='task-1',
            name='Very Late Task',
            finish_date=date.today() - timedelta(days=20),
            percent_complete=30
        )
        project = MockProject(tasks=[task])

        engine = RiskEngine()
        risks = engine.analyze(project, focus_areas=["schedule"])

        critical_risks = [r for r in risks if r.severity == Severity.CRITICAL]
        assert len(critical_risks) > 0

    def test_detect_baseline_slippage(self, task_with_baseline):
        """Test detection of baseline slippage."""
        from .conftest import MockProject
        project = MockProject(tasks=[task_with_baseline])

        engine = RiskEngine()
        risks = engine.analyze(project, focus_areas=["schedule"])

        slip_risks = [r for r in risks if "Slip" in r.name]
        assert len(slip_risks) > 0
        assert slip_risks[0].category == RiskCategory.SCHEDULE

    def test_detect_low_float(self, critical_task):
        """Test detection of low float on critical path."""
        from .conftest import MockProject
        project = MockProject(tasks=[critical_task])

        engine = RiskEngine()
        risks = engine.analyze(project, focus_areas=["schedule"])

        float_risks = [r for r in risks if "Float" in r.name]
        assert len(float_risks) > 0

    def test_detect_negative_float(self):
        """Test detection of negative float."""
        from .conftest import MockProject
        task = MockTask(
            id='task-1',
            name='Negative Float Task',
            is_critical=True,
            total_float=-5
        )
        project = MockProject(tasks=[task])

        engine = RiskEngine()
        risks = engine.analyze(project, focus_areas=["schedule"])

        neg_float_risks = [r for r in risks if "Negative Float" in r.name]
        assert len(neg_float_risks) > 0
        assert neg_float_risks[0].severity == Severity.CRITICAL

    def test_skip_summary_tasks(self, summary_task, simple_task):
        """Test that summary tasks are skipped."""
        from .conftest import MockProject
        project = MockProject(tasks=[summary_task, simple_task])

        engine = RiskEngine()
        risks = engine.analyze(project, focus_areas=["schedule"])

        # Should only analyze work tasks, not summary tasks
        for risk in risks:
            assert summary_task.id not in risk.related_tasks


class TestCostRiskDetection:
    """Tests for cost risk detection."""

    def test_detect_cost_overrun_forecast(self):
        """Test detection of forecast cost overrun."""
        from .conftest import MockProject
        project = MockProject(
            budget=MockCost(100000),
            forecast_cost=MockCost(130000)  # 30% over
        )

        engine = RiskEngine()
        risks = engine.analyze(project, focus_areas=["cost"])

        cost_risks = [r for r in risks if r.category == RiskCategory.COST]
        assert len(cost_risks) > 0
        assert any("Overrun" in r.name for r in cost_risks)

    def test_detect_critical_cost_overrun(self):
        """Test detection of critical cost overrun."""
        from .conftest import MockProject
        project = MockProject(
            budget=MockCost(100000),
            forecast_cost=MockCost(150000)  # 50% over - critical
        )

        engine = RiskEngine()
        risks = engine.analyze(project, focus_areas=["cost"])

        critical_risks = [r for r in risks if r.severity == Severity.CRITICAL]
        assert len(critical_risks) > 0

    def test_detect_budget_depletion(self):
        """Test detection of budget depletion risk."""
        from .conftest import MockProject
        project = MockProject(
            budget=MockCost(100000),
            actual_cost=MockCost(95000)  # 95% spent
        )

        engine = RiskEngine()
        risks = engine.analyze(project, focus_areas=["cost"])

        depletion_risks = [r for r in risks if "Depletion" in r.name]
        assert len(depletion_risks) > 0

    def test_cost_with_numeric_values(self):
        """Test cost analysis with numeric values instead of objects."""
        from .conftest import MockProject
        project = MockProject()
        project.budget = 100000
        project.forecast_cost = 125000

        engine = RiskEngine()
        risks = engine.analyze(project, focus_areas=["cost"])

        # Should still detect overrun
        cost_risks = [r for r in risks if r.category == RiskCategory.COST]
        assert len(cost_risks) > 0


class TestResourceRiskDetection:
    """Tests for resource risk detection."""

    def test_detect_resource_overallocation(self, overallocated_resource):
        """Test detection of overallocated resources."""
        from .conftest import MockProject
        project = MockProject(resources=[overallocated_resource])

        engine = RiskEngine()
        risks = engine.analyze(project, focus_areas=["resource"])

        resource_risks = [r for r in risks if r.category == RiskCategory.RESOURCE]
        assert len(resource_risks) > 0
        assert any("Overallocation" in r.name for r in resource_risks)

    def test_no_risk_for_normal_allocation(self, normal_resource):
        """Test no risk for normally allocated resources."""
        from .conftest import MockProject
        project = MockProject(resources=[normal_resource])

        engine = RiskEngine()
        risks = engine.analyze(project, focus_areas=["resource"])

        # Should not flag normal allocation
        overalloc_risks = [r for r in risks if "Overallocation" in r.name]
        assert len(overalloc_risks) == 0


class TestScopeRiskDetection:
    """Tests for scope risk detection."""

    def test_detect_missing_milestones(self, project_no_milestones):
        """Test detection of missing milestones."""
        engine = RiskEngine()
        risks = engine.analyze(project_no_milestones, focus_areas=["scope"])

        milestone_risks = [r for r in risks if "Milestone" in r.name]
        assert len(milestone_risks) > 0

    def test_detect_incomplete_task_definitions(self, project_no_milestones):
        """Test detection of tasks without descriptions."""
        engine = RiskEngine()
        risks = engine.analyze(project_no_milestones, focus_areas=["scope"])

        definition_risks = [r for r in risks if "Incomplete" in r.name or "definition" in r.description.lower()]
        assert len(definition_risks) > 0

    def test_no_milestone_risk_for_small_projects(self):
        """Test no milestone risk for small projects."""
        from .conftest import MockProject
        # Only 5 tasks - should not trigger milestone warning
        tasks = [MockTask(id=f't{i}', name=f'Task {i}') for i in range(5)]
        project = MockProject(tasks=tasks)

        engine = RiskEngine()
        risks = engine.analyze(project, focus_areas=["scope"])

        milestone_risks = [r for r in risks if "Milestone" in r.name]
        assert len(milestone_risks) == 0


class TestTechnicalRiskDetection:
    """Tests for technical risk detection."""

    def test_detect_dependency_bottleneck(self, project_with_bottleneck):
        """Test detection of dependency bottlenecks."""
        engine = RiskEngine()
        risks = engine.analyze(project_with_bottleneck, focus_areas=["technical"])

        bottleneck_risks = [r for r in risks if "Bottleneck" in r.name]
        assert len(bottleneck_risks) > 0
        assert bottleneck_risks[0].category == RiskCategory.TECHNICAL


class TestExternalRiskDetection:
    """Tests for external risk detection."""

    def test_import_from_risk_register(self, project_with_risk_register):
        """Test importing risks from risk register."""
        engine = RiskEngine()
        risks = engine.analyze(project_with_risk_register, focus_areas=["external"])

        external_risks = [r for r in risks if r.category == RiskCategory.EXTERNAL]
        assert len(external_risks) == 2  # Two risks in register

        # Check risk details are imported
        vendor_risk = [r for r in external_risks if "Vendor" in r.name]
        assert len(vendor_risk) > 0


class TestDeepAnalysis:
    """Tests for deep analysis features."""

    def test_dependency_chain_analysis(self, project_with_long_chain):
        """Test long dependency chain detection in deep mode."""
        engine = RiskEngine()
        risks = engine.analyze(
            project_with_long_chain,
            focus_areas=["technical"],
            depth=AnalysisDepth.DEEP
        )

        chain_risks = [r for r in risks if "Chain" in r.name]
        assert len(chain_risks) > 0

    def test_duration_pattern_analysis(self, long_duration_task):
        """Test long duration task detection in deep mode."""
        from .conftest import MockProject
        project = MockProject(tasks=[long_duration_task])

        engine = RiskEngine()
        risks = engine.analyze(
            project,
            focus_areas=["technical"],
            depth=AnalysisDepth.DEEP
        )

        duration_risks = [r for r in risks if "Long Duration" in r.name]
        assert len(duration_risks) > 0

    def test_deep_analysis_not_run_in_standard_mode(self, long_duration_task):
        """Test deep analysis features not run in standard mode."""
        from .conftest import MockProject
        project = MockProject(tasks=[long_duration_task])

        engine = RiskEngine()
        risks = engine.analyze(
            project,
            focus_areas=["technical"],
            depth=AnalysisDepth.STANDARD
        )

        # Duration pattern analysis should not run in standard mode
        duration_risks = [r for r in risks if "Long Duration" in r.name]
        assert len(duration_risks) == 0


class TestFocusAreas:
    """Tests for focus area filtering."""

    def test_focus_on_schedule_only(self, complex_project):
        """Test analyzing schedule risks only."""
        engine = RiskEngine()
        risks = engine.analyze(complex_project, focus_areas=["schedule"])

        # Should only have schedule risks
        categories = {r.category for r in risks}
        assert categories == {RiskCategory.SCHEDULE}

    def test_focus_on_multiple_areas(self, complex_project):
        """Test analyzing multiple specific areas."""
        engine = RiskEngine()
        risks = engine.analyze(complex_project, focus_areas=["schedule", "cost"])

        categories = {r.category for r in risks}
        assert categories.issubset({RiskCategory.SCHEDULE, RiskCategory.COST})

    def test_all_areas_when_none_specified(self, complex_project):
        """Test all areas analyzed when focus_areas=None."""
        engine = RiskEngine()
        risks = engine.analyze(complex_project, focus_areas=None)

        # Should have risks from multiple categories
        categories = {r.category for r in risks}
        assert len(categories) > 1


class TestMitigationGeneration:
    """Tests for mitigation strategy generation."""

    def test_generate_mitigations_for_risks(self, complex_project):
        """Test mitigation generation."""
        engine = RiskEngine()
        risks = engine.analyze(complex_project)

        mitigations = engine.generate_mitigations(risks)
        assert isinstance(mitigations, list)
        assert len(mitigations) == len(risks)

    def test_schedule_mitigation_for_overdue(self):
        """Test schedule mitigation for overdue tasks."""
        from pm_mcp_servers.pm_analyse.models import Risk

        risk = Risk(
            id="r1",
            name="Overdue Task: Test",
            description="Task overdue",
            category=RiskCategory.SCHEDULE,
            probability=5,
            impact=4,
            score=20,
            confidence=0.9
        )

        engine = RiskEngine()
        mitigations = engine.generate_mitigations([risk])

        assert len(mitigations) == 1
        assert "Expedite" in mitigations[0].strategy
        assert mitigations[0].risk_id == "r1"
        assert len(mitigations[0].implementation_steps) > 0

    def test_cost_mitigation(self):
        """Test cost mitigation generation."""
        from pm_mcp_servers.pm_analyse.models import Risk

        risk = Risk(
            id="r1",
            name="Cost Overrun",
            description="Budget exceeded",
            category=RiskCategory.COST,
            probability=4,
            impact=5,
            score=20,
            confidence=0.85
        )

        engine = RiskEngine()
        mitigations = engine.generate_mitigations([risk])

        assert len(mitigations) == 1
        assert "Cost Control" in mitigations[0].strategy

    def test_mitigation_has_required_fields(self, complex_project):
        """Test mitigations have all required fields."""
        engine = RiskEngine()
        risks = engine.analyze(complex_project)
        mitigations = engine.generate_mitigations(risks)

        for mit in mitigations:
            assert mit.id
            assert mit.risk_id
            assert mit.strategy
            assert mit.description
            assert mit.effort in ["low", "medium", "high"]
            assert 0.0 <= mit.effectiveness <= 1.0
            assert 0.0 <= mit.confidence <= 1.0
