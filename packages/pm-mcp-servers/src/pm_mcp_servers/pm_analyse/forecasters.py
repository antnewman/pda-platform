"""
Forecasting engine for project completion prediction.

Implements multiple forecasting methods including EVM, Monte Carlo simulation,
reference class forecasting, and ensemble methods with confidence intervals.
"""

import random
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import (
    AnalysisDepth,
    Evidence,
    Forecast,
    ForecastMethod,
)


class ForecastEngine:
    """
    Multi-method forecasting engine for project completion prediction.

    Supports earned value, Monte Carlo, reference class, extrapolation,
    and ensemble forecasting with confidence intervals.
    """

    # Ensemble weights for ML_ENSEMBLE method
    ENSEMBLE_WEIGHTS = {
        ForecastMethod.EARNED_VALUE: 0.35,
        ForecastMethod.MONTE_CARLO: 0.25,
        ForecastMethod.REFERENCE_CLASS: 0.25,
        ForecastMethod.SIMPLE_EXTRAPOLATION: 0.15,
    }

    # Historical overrun factors (Flyvbjerg research)
    REFERENCE_CLASS_FACTORS = {
        "it": 1.27,          # IT projects: 27% overrun
        "infrastructure": 1.44,  # Infrastructure: 44% overrun
        "default": 1.20      # Conservative default: 20% overrun
    }

    def __init__(self):
        """Initialize the forecast engine."""
        pass

    def forecast(
        self,
        project: Any,
        method: ForecastMethod = ForecastMethod.ML_ENSEMBLE,
        confidence_level: float = 0.80,
        scenarios: bool = True,
        depth: AnalysisDepth = AnalysisDepth.STANDARD
    ) -> Forecast:
        """
        Main forecast entry point.

        Args:
            project: Project object to forecast
            method: Forecasting method to use
            confidence_level: Confidence level for interval (0.50-0.95)
            scenarios: Whether to generate scenario forecasts
            depth: Analysis depth

        Returns:
            Forecast with predicted completion date and confidence interval
        """
        tasks = getattr(project, 'tasks', [])
        baseline_finish = getattr(project, 'finish_date', None)

        # Calculate project status
        status = self._calculate_status(project, tasks)

        # Convert baseline_finish to date
        if baseline_finish:
            if isinstance(baseline_finish, str):
                baseline_finish = datetime.fromisoformat(baseline_finish).date()
            elif isinstance(baseline_finish, datetime):
                baseline_finish = baseline_finish.date()

        # Run forecast method
        if method == ForecastMethod.EARNED_VALUE:
            forecast = self._earned_value_forecast(project, tasks, status, baseline_finish)
        elif method == ForecastMethod.MONTE_CARLO:
            forecast = self._monte_carlo_forecast(project, tasks, status, baseline_finish, depth)
        elif method == ForecastMethod.REFERENCE_CLASS:
            forecast = self._reference_class_forecast(project, tasks, status, baseline_finish)
        elif method == ForecastMethod.SIMPLE_EXTRAPOLATION:
            forecast = self._simple_extrapolation_forecast(project, tasks, status, baseline_finish)
        elif method == ForecastMethod.ML_ENSEMBLE:
            forecast = self._ensemble_forecast(project, tasks, status, baseline_finish, depth)
        else:
            # Fallback to ensemble
            forecast = self._ensemble_forecast(project, tasks, status, baseline_finish, depth)

        # Generate scenarios if requested
        if scenarios and method != ForecastMethod.ML_ENSEMBLE:
            forecast.scenarios = self._generate_scenarios(forecast.forecast_date, status)

        return forecast

    def _calculate_status(self, project: Any, tasks: List[Any]) -> Dict:
        """Calculate SPI, percent complete, etc."""
        today = date.today()

        # Filter out summary tasks
        work_tasks = [t for t in tasks if not getattr(t, 'is_summary', False)]

        if not work_tasks:
            return {
                "percent_complete": 0.0,
                "spi": 1.0,
                "tasks_total": 0,
                "tasks_completed": 0,
                "days_elapsed": 0,
                "confidence": 0.5
            }

        # Calculate percent complete (weighted by duration if available)
        total_duration: float = 0.0
        completed_duration: float = 0.0

        for task in work_tasks:
            start = getattr(task, 'start_date', None)
            finish = getattr(task, 'finish_date', None)

            if start and finish:
                if isinstance(start, str):
                    start = datetime.fromisoformat(start).date()
                elif isinstance(start, datetime):
                    start = start.date()

                if isinstance(finish, str):
                    finish = datetime.fromisoformat(finish).date()
                elif isinstance(finish, datetime):
                    finish = finish.date()

                duration = (finish - start).days + 1
                total_duration += duration

                percent = getattr(task, 'percent_complete', 0) / 100.0
                completed_duration += duration * percent

        percent_complete = (completed_duration / total_duration * 100) if total_duration > 0 else 0

        # Calculate SPI (Schedule Performance Index)
        # SPI = Earned Value / Planned Value
        # Simplified: actual_progress / planned_progress
        project_start = getattr(project, 'start_date', None)
        project_finish = getattr(project, 'finish_date', None)

        spi = 1.0
        days_elapsed = 0
        confidence = 0.7

        if project_start and project_finish:
            if isinstance(project_start, str):
                project_start = datetime.fromisoformat(project_start).date()
            elif isinstance(project_start, datetime):
                project_start = project_start.date()

            if isinstance(project_finish, str):
                project_finish = datetime.fromisoformat(project_finish).date()
            elif isinstance(project_finish, datetime):
                project_finish = project_finish.date()

            total_duration = (project_finish - project_start).days
            days_elapsed = (today - project_start).days

            if total_duration > 0 and days_elapsed > 0:
                planned_progress = (days_elapsed / total_duration) * 100
                if planned_progress > 0:
                    spi = percent_complete / planned_progress
                    confidence = 0.85 if days_elapsed > 30 else 0.70

        return {
            "percent_complete": percent_complete,
            "spi": spi,
            "tasks_total": len(work_tasks),
            "tasks_completed": len([t for t in work_tasks if getattr(t, 'percent_complete', 0) == 100]),
            "days_elapsed": days_elapsed,
            "confidence": confidence
        }

    def _earned_value_forecast(
        self,
        project: Any,
        tasks: List[Any],
        status: Dict,
        baseline_finish: Optional[date]
    ) -> Forecast:
        """EVM: Completion = Today + (Remaining / SPI)."""
        today = date.today()
        percent_complete = status["percent_complete"]
        spi = status["spi"]

        if not baseline_finish:
            baseline_finish = today + timedelta(days=90)

        # Calculate remaining work
        remaining_percent = 100 - percent_complete

        # Estimate days to completion using SPI
        project_start = getattr(project, 'start_date', None)
        if project_start:
            if isinstance(project_start, str):
                project_start = datetime.fromisoformat(project_start).date()
            elif isinstance(project_start, datetime):
                project_start = project_start.date()

            baseline_duration = (baseline_finish - project_start).days
            remaining_baseline_days = (remaining_percent / 100) * baseline_duration

            # Adjust by SPI
            if spi > 0:
                remaining_actual_days = remaining_baseline_days / spi
            else:
                remaining_actual_days = remaining_baseline_days * 2

            forecast_date = today + timedelta(days=int(remaining_actual_days))
        else:
            # Fallback
            forecast_date = baseline_finish

        # Calculate variance
        variance_days = (forecast_date - baseline_finish).days if baseline_finish else 0
        on_track = variance_days <= 5

        # Confidence interval (wider for lower SPI)
        confidence = status["confidence"]
        interval_days = int(abs(variance_days) * 0.3) + 5
        confidence_interval = (
            forecast_date - timedelta(days=interval_days),
            forecast_date + timedelta(days=interval_days)
        )

        return Forecast(
            forecast_date=forecast_date,
            confidence_interval=confidence_interval,
            confidence_level=0.80,
            method=ForecastMethod.EARNED_VALUE,
            variance_days=variance_days,
            on_track=on_track,
            confidence=confidence,
            factors=[
                f"SPI: {spi:.2f}",
                f"{percent_complete:.1f}% complete",
                f"Remaining: {remaining_percent:.1f}%"
            ],
            evidence=[
                Evidence(
                    source="earned_value_analysis",
                    description=f"Schedule Performance Index: {spi:.2f}",
                    data_point=f"spi={spi:.2f}",
                    confidence=confidence
                ),
                Evidence(
                    source="progress_tracking",
                    description=f"Project {percent_complete:.1f}% complete",
                    data_point=f"percent_complete={percent_complete:.1f}",
                    confidence=0.90
                )
            ]
        )

    def _monte_carlo_forecast(
        self,
        project: Any,
        tasks: List[Any],
        status: Dict,
        baseline_finish: Optional[date],
        depth: AnalysisDepth
    ) -> Forecast:
        """Simulation with triangular distribution variability."""
        today = date.today()

        # Determine iteration count based on depth
        iterations = {
            AnalysisDepth.QUICK: 100,
            AnalysisDepth.STANDARD: 500,
            AnalysisDepth.DEEP: 1000
        }.get(depth, 500)

        simulated_dates = []

        # Run Monte Carlo simulation
        for _ in range(iterations):
            sim_date = self._simulate_completion(project, tasks, status, today)
            simulated_dates.append(sim_date)

        # Sort results
        simulated_dates.sort()

        # Calculate percentiles
        p50_idx = int(len(simulated_dates) * 0.50)
        p20_idx = int(len(simulated_dates) * 0.20)
        p80_idx = int(len(simulated_dates) * 0.80)

        forecast_date = simulated_dates[p50_idx]  # Median
        confidence_interval = (simulated_dates[p20_idx], simulated_dates[p80_idx])

        # Calculate variance
        variance_days = (forecast_date - baseline_finish).days if baseline_finish else 0
        on_track = variance_days <= 5

        return Forecast(
            forecast_date=forecast_date,
            confidence_interval=confidence_interval,
            confidence_level=0.80,
            method=ForecastMethod.MONTE_CARLO,
            variance_days=variance_days,
            on_track=on_track,
            confidence=0.75,
            factors=[
                f"{iterations} simulations run",
                f"P50 forecast",
                f"{status['percent_complete']:.1f}% complete"
            ],
            evidence=[
                Evidence(
                    source="monte_carlo_simulation",
                    description=f"{iterations} iterations with triangular distribution",
                    data_point=f"iterations={iterations}",
                    confidence=0.75
                )
            ],
            scenarios={
                "optimistic": simulated_dates[int(len(simulated_dates) * 0.10)],
                "likely": forecast_date,
                "pessimistic": simulated_dates[int(len(simulated_dates) * 0.90)]
            }
        )

    def _simulate_completion(
        self,
        project: Any,
        tasks: List[Any],
        status: Dict,
        today: date
    ) -> date:
        """Run single Monte Carlo simulation."""
        percent_complete = status["percent_complete"]
        remaining_percent = 100 - percent_complete

        # Get baseline duration
        project_start = getattr(project, 'start_date', None)
        project_finish = getattr(project, 'finish_date', None)

        if project_start and project_finish:
            if isinstance(project_start, str):
                project_start = datetime.fromisoformat(project_start).date()
            elif isinstance(project_start, datetime):
                project_start = project_start.date()

            if isinstance(project_finish, str):
                project_finish = datetime.fromisoformat(project_finish).date()
            elif isinstance(project_finish, datetime):
                project_finish = project_finish.date()

            baseline_duration = (project_finish - project_start).days
        else:
            baseline_duration = 90

        remaining_baseline_days = (remaining_percent / 100) * baseline_duration

        # Apply triangular distribution variability
        # min: 0.7x, mode: 1.0x, max: 1.5x
        variability = random.triangular(0.7, 1.5, 1.0)
        simulated_days = remaining_baseline_days * variability

        return today + timedelta(days=int(simulated_days))

    def _reference_class_forecast(
        self,
        project: Any,
        tasks: List[Any],
        status: Dict,
        baseline_finish: Optional[date]
    ) -> Forecast:
        """Historical overrun factors (Flyvbjerg research)."""
        if not baseline_finish:
            baseline_finish = date.today() + timedelta(days=90)

        # Determine project type
        project_type = getattr(project, 'project_type', 'default').lower()
        overrun_factor = self.REFERENCE_CLASS_FACTORS.get(
            project_type,
            self.REFERENCE_CLASS_FACTORS["default"]
        )

        # Calculate adjusted completion
        project_start = getattr(project, 'start_date', None)
        if project_start:
            if isinstance(project_start, str):
                project_start = datetime.fromisoformat(project_start).date()
            elif isinstance(project_start, datetime):
                project_start = project_start.date()

            baseline_duration = (baseline_finish - project_start).days
            adjusted_duration = int(baseline_duration * overrun_factor)
            forecast_date = project_start + timedelta(days=adjusted_duration)
        else:
            # Apply factor to remaining time
            today = date.today()
            remaining = (baseline_finish - today).days
            adjusted_remaining = int(remaining * overrun_factor)
            forecast_date = today + timedelta(days=adjusted_remaining)

        variance_days = (forecast_date - baseline_finish).days
        on_track = variance_days <= 5

        # Confidence interval based on historical variance
        interval_days = int(abs(variance_days) * 0.4)
        confidence_interval = (
            forecast_date - timedelta(days=interval_days),
            forecast_date + timedelta(days=interval_days)
        )

        return Forecast(
            forecast_date=forecast_date,
            confidence_interval=confidence_interval,
            confidence_level=0.80,
            method=ForecastMethod.REFERENCE_CLASS,
            variance_days=variance_days,
            on_track=on_track,
            confidence=0.70,
            factors=[
                f"Reference class: {project_type}",
                f"Historical overrun: {(overrun_factor - 1) * 100:.0f}%",
                f"Applied factor: {overrun_factor:.2f}"
            ],
            evidence=[
                Evidence(
                    source="reference_class_forecasting",
                    description=f"Historical data for {project_type} projects",
                    data_point=f"overrun_factor={overrun_factor}",
                    confidence=0.70
                )
            ]
        )

    def _simple_extrapolation_forecast(
        self,
        project: Any,
        tasks: List[Any],
        status: Dict,
        baseline_finish: Optional[date]
    ) -> Forecast:
        """Linear projection based on current progress rate."""
        today = date.today()
        percent_complete = status["percent_complete"]
        days_elapsed = status["days_elapsed"]

        if percent_complete > 0 and days_elapsed > 0:
            # Calculate days per percent
            days_per_percent = days_elapsed / percent_complete
            remaining_percent = 100 - percent_complete
            remaining_days = int(remaining_percent * days_per_percent)

            forecast_date = today + timedelta(days=remaining_days)
        else:
            # Fallback to baseline
            forecast_date = baseline_finish if baseline_finish else today + timedelta(days=90)

        variance_days = (forecast_date - baseline_finish).days if baseline_finish else 0
        on_track = variance_days <= 5

        # Confidence interval
        interval_days = max(int(abs(variance_days) * 0.25), 7)
        confidence_interval = (
            forecast_date - timedelta(days=interval_days),
            forecast_date + timedelta(days=interval_days)
        )

        return Forecast(
            forecast_date=forecast_date,
            confidence_interval=confidence_interval,
            confidence_level=0.80,
            method=ForecastMethod.SIMPLE_EXTRAPOLATION,
            variance_days=variance_days,
            on_track=on_track,
            confidence=0.65,
            factors=[
                f"{percent_complete:.1f}% complete in {days_elapsed} days",
                f"Rate: {days_elapsed / percent_complete if percent_complete > 0 else 0:.1f} days/%",
                "Linear extrapolation"
            ],
            evidence=[
                Evidence(
                    source="linear_extrapolation",
                    description=f"Progress rate: {percent_complete / days_elapsed if days_elapsed > 0 else 0:.2f}%/day",
                    data_point=f"rate={percent_complete / days_elapsed if days_elapsed > 0 else 0:.2f}",
                    confidence=0.65
                )
            ]
        )

    def _ensemble_forecast(
        self,
        project: Any,
        tasks: List[Any],
        status: Dict,
        baseline_finish: Optional[date],
        depth: AnalysisDepth
    ) -> Forecast:
        """Weighted ensemble of all methods."""
        # Run all methods
        evm_forecast = self._earned_value_forecast(project, tasks, status, baseline_finish)
        mc_forecast = self._monte_carlo_forecast(project, tasks, status, baseline_finish, depth)
        ref_forecast = self._reference_class_forecast(project, tasks, status, baseline_finish)
        simple_forecast = self._simple_extrapolation_forecast(project, tasks, status, baseline_finish)

        # Calculate weighted average of dates
        forecasts = {
            ForecastMethod.EARNED_VALUE: evm_forecast,
            ForecastMethod.MONTE_CARLO: mc_forecast,
            ForecastMethod.REFERENCE_CLASS: ref_forecast,
            ForecastMethod.SIMPLE_EXTRAPOLATION: simple_forecast
        }

        # Convert dates to days from today for averaging
        today = date.today()
        weighted_days = 0.0
        total_weight = 0.0

        for method, weight in self.ENSEMBLE_WEIGHTS.items():
            forecast = forecasts[method]
            days = (forecast.forecast_date - today).days
            weighted_days += days * weight
            total_weight += weight

        avg_days = int(weighted_days / total_weight) if total_weight > 0 else 0
        forecast_date = today + timedelta(days=avg_days)

        # Calculate ensemble confidence interval (use widest)
        min_date = min(f.confidence_interval[0] for f in forecasts.values())
        max_date = max(f.confidence_interval[1] for f in forecasts.values())
        confidence_interval = (min_date, max_date)

        variance_days = (forecast_date - baseline_finish).days if baseline_finish else 0
        on_track = variance_days <= 5

        # Combine evidence
        evidence = []
        for method, forecast in forecasts.items():
            evidence.append(Evidence(
                source="ensemble",
                description=f"{method.value}: {forecast.forecast_date}",
                data_point=f"{method.value}_days={(forecast.forecast_date - today).days}",
                confidence=self.ENSEMBLE_WEIGHTS[method]
            ))

        return Forecast(
            forecast_date=forecast_date,
            confidence_interval=confidence_interval,
            confidence_level=0.80,
            method=ForecastMethod.ML_ENSEMBLE,
            variance_days=variance_days,
            on_track=on_track,
            confidence=0.80,
            factors=[
                "Ensemble of 4 methods",
                f"EVM: {evm_forecast.forecast_date}",
                f"Monte Carlo: {mc_forecast.forecast_date}",
                f"Reference: {ref_forecast.forecast_date}"
            ],
            evidence=evidence,
            scenarios={
                "optimistic": min(f.forecast_date for f in forecasts.values()),
                "likely": forecast_date,
                "pessimistic": max(f.forecast_date for f in forecasts.values())
            }
        )

    def _generate_scenarios(self, base_date: date, status: Dict) -> Dict[str, date]:
        """Generate optimistic/likely/pessimistic scenarios."""
        spi = status.get("spi", 1.0)

        # Optimistic: +10% performance
        optimistic_days = int((base_date - date.today()).days * 0.90)
        optimistic = date.today() + timedelta(days=max(0, optimistic_days))

        # Likely: base forecast
        likely = base_date

        # Pessimistic: -20% performance
        pessimistic_days = int((base_date - date.today()).days * 1.20)
        pessimistic = date.today() + timedelta(days=pessimistic_days)

        return {
            "optimistic": optimistic,
            "likely": likely,
            "pessimistic": pessimistic
        }
