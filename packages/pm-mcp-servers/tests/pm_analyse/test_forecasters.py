"""Tests for PM-Analyse forecasting engine - all 5 forecast methods."""
from datetime import date, timedelta
import pytest
from pm_mcp_servers.pm_analyse.forecasters import ForecastEngine
from pm_mcp_servers.pm_analyse.models import AnalysisDepth, ForecastMethod
from .conftest import MockTask, MockProject

class TestForecastEngineBasics:
    def test_engine_initialization(self):
        engine = ForecastEngine()
        assert engine is not None
    
    def test_forecast_returns_forecast_object(self, basic_project):
        engine = ForecastEngine()
        forecast = engine.forecast(basic_project)
        assert hasattr(forecast, 'forecast_date')
        assert hasattr(forecast, 'confidence')
    
    def test_forecast_empty_project(self, empty_project):
        engine = ForecastEngine()
        forecast = engine.forecast(empty_project)
        assert forecast is not None

class TestEarnedValueMethod:
    def test_earned_value_forecast(self, complex_project):
        engine = ForecastEngine()
        forecast = engine.forecast(complex_project, method=ForecastMethod.EARNED_VALUE)
        assert forecast.method == ForecastMethod.EARNED_VALUE
        assert forecast.forecast_date is not None
    
    def test_evm_with_progress(self):
        tasks = [MockTask(id=f't{i}', start_date=date.today() - timedelta(days=30), finish_date=date.today() + timedelta(days=30), percent_complete=50) for i in range(5)]
        project = MockProject(tasks=tasks, start_date=date.today() - timedelta(days=30), finish_date=date.today() + timedelta(days=30))
        engine = ForecastEngine()
        forecast = engine.forecast(project, method=ForecastMethod.EARNED_VALUE)
        assert any("SPI" in f for f in forecast.factors)
    
    def test_evm_confidence_interval(self, complex_project):
        engine = ForecastEngine()
        forecast = engine.forecast(complex_project, method=ForecastMethod.EARNED_VALUE)
        assert len(forecast.confidence_interval) == 2
        assert forecast.confidence_interval[0] <= forecast.forecast_date <= forecast.confidence_interval[1]
    
    def test_evm_variance_calculation(self, complex_project):
        engine = ForecastEngine()
        forecast = engine.forecast(complex_project, method=ForecastMethod.EARNED_VALUE)
        assert hasattr(forecast, 'variance_days')

class TestMonteCarloMethod:
    def test_monte_carlo_forecast(self, complex_project):
        engine = ForecastEngine()
        forecast = engine.forecast(complex_project, method=ForecastMethod.MONTE_CARLO)
        assert forecast.method == ForecastMethod.MONTE_CARLO
    
    def test_monte_carlo_iterations_quick(self, basic_project):
        engine = ForecastEngine()
        forecast = engine.forecast(basic_project, method=ForecastMethod.MONTE_CARLO, depth=AnalysisDepth.QUICK)
        assert forecast.forecast_date is not None
    
    def test_monte_carlo_iterations_deep(self, basic_project):
        engine = ForecastEngine()
        forecast = engine.forecast(basic_project, method=ForecastMethod.MONTE_CARLO, depth=AnalysisDepth.DEEP)
        assert forecast.forecast_date is not None
    
    def test_monte_carlo_scenarios(self, basic_project):
        engine = ForecastEngine()
        forecast = engine.forecast(basic_project, method=ForecastMethod.MONTE_CARLO)
        assert "optimistic" in forecast.scenarios
        assert "pessimistic" in forecast.scenarios

class TestReferenceClassMethod:
    def test_reference_class_forecast(self, complex_project):
        engine = ForecastEngine()
        forecast = engine.forecast(complex_project, method=ForecastMethod.REFERENCE_CLASS)
        assert forecast.method == ForecastMethod.REFERENCE_CLASS
    
    def test_reference_class_it_projects(self):
        project = MockProject(start_date=date.today(), finish_date=date.today() + timedelta(days=100), project_type='it')
        engine = ForecastEngine()
        forecast = engine.forecast(project, method=ForecastMethod.REFERENCE_CLASS)
        assert forecast.variance_days > 0
    
    def test_reference_class_infrastructure(self):
        project = MockProject(start_date=date.today(), finish_date=date.today() + timedelta(days=100), project_type='infrastructure')
        engine = ForecastEngine()
        forecast = engine.forecast(project, method=ForecastMethod.REFERENCE_CLASS)
        assert forecast.variance_days > 0

class TestSimpleExtrapolationMethod:
    def test_simple_extrapolation_forecast(self, complex_project):
        engine = ForecastEngine()
        forecast = engine.forecast(complex_project, method=ForecastMethod.SIMPLE_EXTRAPOLATION)
        assert forecast.method == ForecastMethod.SIMPLE_EXTRAPOLATION
    
    def test_extrapolation_with_progress(self):
        tasks = [MockTask(id='t1', start_date=date.today() - timedelta(days=20), finish_date=date.today() + timedelta(days=80), percent_complete=20)]
        project = MockProject(tasks=tasks, start_date=date.today() - timedelta(days=20), finish_date=date.today() + timedelta(days=80))
        engine = ForecastEngine()
        forecast = engine.forecast(project, method=ForecastMethod.SIMPLE_EXTRAPOLATION)
        assert forecast.forecast_date is not None

class TestMLEnsembleMethod:
    def test_ensemble_forecast(self, complex_project):
        engine = ForecastEngine()
        forecast = engine.forecast(complex_project, method=ForecastMethod.ML_ENSEMBLE)
        assert forecast.method == ForecastMethod.ML_ENSEMBLE
    
    def test_ensemble_combines_methods(self, basic_project):
        engine = ForecastEngine()
        forecast = engine.forecast(basic_project, method=ForecastMethod.ML_ENSEMBLE)
        assert len(forecast.evidence) >= 4
    
    def test_ensemble_scenarios(self, basic_project):
        engine = ForecastEngine()
        forecast = engine.forecast(basic_project, method=ForecastMethod.ML_ENSEMBLE)
        assert "optimistic" in forecast.scenarios

class TestConfidenceIntervals:
    def test_confidence_interval_ordering(self, basic_project):
        engine = ForecastEngine()
        forecast = engine.forecast(basic_project)
        lower, upper = forecast.confidence_interval
        assert lower <= forecast.forecast_date <= upper
    
    def test_different_confidence_levels(self, basic_project):
        engine = ForecastEngine()
        f80 = engine.forecast(basic_project, confidence_level=0.80)
        f95 = engine.forecast(basic_project, confidence_level=0.95)
        assert f80.confidence_level == 0.80
        assert f95.confidence_level == 0.95
