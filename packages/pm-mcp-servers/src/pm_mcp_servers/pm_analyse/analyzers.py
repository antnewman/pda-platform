"""
Analyzers for project health, outliers, and baseline comparison.

This module provides three analyzer classes:
- OutlierDetector: Detects anomalies in task data
- HealthAnalyzer: Calculates multi-dimensional project health scores
- BaselineComparator: Compares current vs baseline values
"""

import uuid
from datetime import date, datetime
from statistics import mean, stdev
from typing import Any, List, Optional

from .models import (
    BaselineVariance,
    Evidence,
    HealthAssessment,
    HealthDimension,
    HealthStatus,
    Outlier,
    Severity,
    TrendDirection,
)


class OutlierDetector:
    """
    Detects anomalies in task data across multiple dimensions.

    Identifies outliers in:
    - Duration (unusually long or short tasks)
    - Progress (stuck or unrealistic completion rates)
    - Float (abnormal schedule flexibility)
    - Dates (impossible or suspicious scheduling)
    """

    # Thresholds for outlier detection
    DURATION_MIN_DAYS = 1
    DURATION_MAX_DAYS = 180
    DURATION_STDEV_MULTIPLIER = 2.5
    PROGRESS_STUCK_THRESHOLD = 0.05  # 5% change in 30 days
    FLOAT_NEGATIVE_CRITICAL = -5
    FLOAT_EXCESSIVE_DAYS = 30
    PAST_DATE_CRITICAL_DAYS = 30

    def __init__(self):
        """Initialize the outlier detector."""
        pass

    def detect(
        self,
        project: Any,
        sensitivity: float = 1.0,
        focus_areas: Optional[List[str]] = None
    ) -> List[Outlier]:
        """
        Detect outliers in project data.

        Args:
            project: Project object to analyze
            sensitivity: Detection sensitivity (0.5-2.0, default 1.0)
            focus_areas: Optional list of areas to focus on
                         ["duration", "progress", "float", "dates"]

        Returns:
            List of detected outliers with confidence scores
        """
        outliers: List[Outlier] = []
        tasks = getattr(project, 'tasks', [])

        # Filter to work tasks only
        work_tasks = [t for t in tasks if not getattr(t, 'is_summary', False)]

        if not work_tasks:
            return outliers

        # Determine which checks to run
        all_areas = ["duration", "progress", "float", "dates"]
        areas = focus_areas if focus_areas else all_areas

        # Adjust thresholds based on sensitivity
        duration_multiplier = self.DURATION_STDEV_MULTIPLIER / sensitivity
        float_threshold = self.FLOAT_EXCESSIVE_DAYS * sensitivity

        if "duration" in areas:
            outliers.extend(self._detect_duration_outliers(
                work_tasks, duration_multiplier
            ))

        if "progress" in areas:
            outliers.extend(self._detect_progress_outliers(work_tasks))

        if "float" in areas:
            outliers.extend(self._detect_float_outliers(
                work_tasks, float_threshold
            ))

        if "dates" in areas:
            outliers.extend(self._detect_date_outliers(work_tasks))

        return outliers

    def _detect_duration_outliers(
        self,
        tasks: List[Any],
        stdev_multiplier: float
    ) -> List[Outlier]:
        """Detect tasks with unusual durations."""
        outliers: List[Outlier] = []

        # Calculate duration statistics
        durations = []
        for task in tasks:
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

                duration = (finish - start).days
                durations.append(duration)

        if len(durations) < 3:
            return outliers

        # Calculate mean and standard deviation
        avg_duration = mean(durations)
        std_duration = stdev(durations) if len(durations) > 1 else 0

        # Detect outliers
        for task in tasks:
            task_id = str(getattr(task, 'id', ''))
            task_name = getattr(task, 'name', 'Unnamed Task')
            start = getattr(task, 'start_date', None)
            finish = getattr(task, 'finish_date', None)

            if not start or not finish:
                continue

            if isinstance(start, str):
                start = datetime.fromisoformat(start).date()
            elif isinstance(start, datetime):
                start = start.date()

            if isinstance(finish, str):
                finish = datetime.fromisoformat(finish).date()
            elif isinstance(finish, datetime):
                finish = finish.date()

            duration = (finish - start).days

            # Check for excessively long tasks
            if duration > self.DURATION_MAX_DAYS:
                deviation = abs(duration - avg_duration) / (std_duration if std_duration > 0 else 1)
                outliers.append(Outlier(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    task_name=task_name,
                    field_name="duration",
                    value=duration,
                    expected_range=(self.DURATION_MIN_DAYS, self.DURATION_MAX_DAYS),
                    deviation_score=min(deviation, 10.0),
                    severity=Severity.HIGH,
                    confidence=0.90,
                    explanation=f"Task duration of {duration} days exceeds maximum threshold",
                    evidence=[Evidence(
                        source="duration_analysis",
                        description=f"Duration: {duration} days, Max: {self.DURATION_MAX_DAYS}",
                        data_point=f"duration={duration}",
                        confidence=1.0
                    )]
                ))

            # Check for statistical outliers
            elif std_duration > 0 and abs(duration - avg_duration) > (stdev_multiplier * std_duration):
                deviation = abs(duration - avg_duration) / std_duration
                severity = Severity.MEDIUM if duration > avg_duration else Severity.LOW

                outliers.append(Outlier(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    task_name=task_name,
                    field_name="duration",
                    value=duration,
                    expected_range=(
                        max(0, avg_duration - stdev_multiplier * std_duration),
                        avg_duration + stdev_multiplier * std_duration
                    ),
                    deviation_score=deviation,
                    severity=severity,
                    confidence=0.75,
                    explanation=f"Task duration of {duration} days is {deviation:.1f} standard deviations from average ({avg_duration:.1f} days)",
                    evidence=[Evidence(
                        source="statistical_analysis",
                        description=f"Avg: {avg_duration:.1f}, StdDev: {std_duration:.1f}",
                        data_point=f"z_score={deviation:.2f}",
                        confidence=0.80
                    )]
                ))

        return outliers

    def _detect_progress_outliers(self, tasks: List[Any]) -> List[Outlier]:
        """Detect tasks with suspicious progress patterns."""
        outliers = []
        today = date.today()

        for task in tasks:
            task_id = str(getattr(task, 'id', ''))
            task_name = getattr(task, 'name', 'Unnamed Task')
            percent_complete = getattr(task, 'percent_complete', 0)
            start_date = getattr(task, 'start_date', None)
            finish_date = getattr(task, 'finish_date', None)

            if not start_date or not finish_date:
                continue

            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date).date()
            elif isinstance(start_date, datetime):
                start_date = start_date.date()

            if isinstance(finish_date, str):
                finish_date = datetime.fromisoformat(finish_date).date()
            elif isinstance(finish_date, datetime):
                finish_date = finish_date.date()

            # Check for stuck tasks (started but no progress)
            if start_date < today and percent_complete < 5:
                days_started = (today - start_date).days
                if days_started > 7:
                    outliers.append(Outlier(
                        id=str(uuid.uuid4()),
                        task_id=task_id,
                        task_name=task_name,
                        field_name="percent_complete",
                        value=percent_complete,
                        expected_range=(5, 100),
                        deviation_score=days_started / 7.0,
                        severity=Severity.MEDIUM,
                        confidence=0.80,
                        explanation=f"Task started {days_started} days ago but only {percent_complete}% complete",
                        evidence=[Evidence(
                            source="progress_tracking",
                            description=f"Started: {start_date}, Progress: {percent_complete}%",
                            data_point=f"days_started={days_started}",
                            confidence=0.85
                        )]
                    ))

            # Check for impossible progress (100% but not finished yet)
            if percent_complete == 100 and finish_date > today:
                outliers.append(Outlier(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    task_name=task_name,
                    field_name="percent_complete",
                    value=percent_complete,
                    expected_range=(0, 99),
                    deviation_score=5.0,
                    severity=Severity.HIGH,
                    confidence=0.95,
                    explanation=f"Task marked 100% complete but finish date is {finish_date} (future)",
                    evidence=[Evidence(
                        source="data_validation",
                        description=f"Complete: {percent_complete}%, Finish: {finish_date}",
                        data_point="inconsistent_completion",
                        confidence=1.0
                    )]
                ))

        return outliers

    def _detect_float_outliers(
        self,
        tasks: List[Any],
        excessive_threshold: float
    ) -> List[Outlier]:
        """Detect tasks with abnormal float values."""
        outliers = []

        for task in tasks:
            task_id = str(getattr(task, 'id', ''))
            task_name = getattr(task, 'name', 'Unnamed Task')
            total_float = getattr(task, 'total_float', None)
            is_critical = getattr(task, 'is_critical', False)

            if total_float is None:
                continue

            # Check for negative float
            if total_float < self.FLOAT_NEGATIVE_CRITICAL:
                outliers.append(Outlier(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    task_name=task_name,
                    field_name="total_float",
                    value=total_float,
                    expected_range=(0, excessive_threshold),
                    deviation_score=abs(total_float),
                    severity=Severity.CRITICAL,
                    confidence=0.95,
                    explanation=f"Task has critical negative float of {total_float} days",
                    evidence=[Evidence(
                        source="schedule_analysis",
                        description=f"Total Float: {total_float} days",
                        data_point=f"float={total_float}",
                        confidence=1.0
                    )]
                ))

            # Check for excessive float on non-critical tasks
            elif not is_critical and total_float > excessive_threshold:
                outliers.append(Outlier(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    task_name=task_name,
                    field_name="total_float",
                    value=total_float,
                    expected_range=(0, excessive_threshold),
                    deviation_score=total_float / excessive_threshold,
                    severity=Severity.LOW,
                    confidence=0.70,
                    explanation=f"Task has excessive float of {total_float} days (may indicate loose constraints)",
                    evidence=[Evidence(
                        source="schedule_analysis",
                        description=f"Total Float: {total_float} days",
                        data_point=f"float={total_float}",
                        confidence=0.75
                    )]
                ))

        return outliers

    def _detect_date_outliers(self, tasks: List[Any]) -> List[Outlier]:
        """Detect impossible or suspicious date values."""
        outliers = []
        today = date.today()

        for task in tasks:
            task_id = str(getattr(task, 'id', ''))
            task_name = getattr(task, 'name', 'Unnamed Task')
            start_date = getattr(task, 'start_date', None)
            finish_date = getattr(task, 'finish_date', None)
            percent_complete = getattr(task, 'percent_complete', 0)

            if not start_date or not finish_date:
                continue

            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date).date()
            elif isinstance(start_date, datetime):
                start_date = start_date.date()

            if isinstance(finish_date, str):
                finish_date = datetime.fromisoformat(finish_date).date()
            elif isinstance(finish_date, datetime):
                finish_date = finish_date.date()

            # Check for finish before start
            if finish_date < start_date:
                outliers.append(Outlier(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    task_name=task_name,
                    field_name="dates",
                    value=f"Start: {start_date}, Finish: {finish_date}",
                    expected_range=("start <= finish", "start <= finish"),
                    deviation_score=10.0,
                    severity=Severity.CRITICAL,
                    confidence=1.0,
                    explanation="Finish date is before start date (impossible)",
                    evidence=[Evidence(
                        source="date_validation",
                        description=f"Start: {start_date}, Finish: {finish_date}",
                        data_point="invalid_date_sequence",
                        confidence=1.0
                    )]
                ))

            # Check for overdue incomplete tasks far in the past
            if finish_date < today and percent_complete < 100:
                days_overdue = (today - finish_date).days
                if days_overdue > self.PAST_DATE_CRITICAL_DAYS:
                    outliers.append(Outlier(
                        id=str(uuid.uuid4()),
                        task_id=task_id,
                        task_name=task_name,
                        field_name="finish_date",
                        value=finish_date,
                        expected_range=(today, today),
                        deviation_score=days_overdue / 7.0,
                        severity=Severity.HIGH,
                        confidence=0.90,
                        explanation=f"Task {days_overdue} days overdue but only {percent_complete}% complete",
                        evidence=[Evidence(
                            source="schedule_tracking",
                            description=f"Finish: {finish_date}, Today: {today}",
                            data_point=f"days_overdue={days_overdue}",
                            confidence=0.95
                        )]
                    ))

        return outliers


class HealthAnalyzer:
    """
    Calculates multi-dimensional project health scores.

    Assesses health across five dimensions:
    1. Schedule Health: On-time performance, critical path status
    2. Cost Health: Budget adherence, forecast accuracy
    3. Scope Health: Deliverable completion, change control
    4. Resource Health: Allocation, availability, utilization
    5. Quality Health: Defect rates, acceptance criteria met
    """

    def __init__(self):
        """Initialize the health analyzer."""
        pass

    def assess(
        self,
        project: Any,
        include_trends: bool = True,
        weights: Optional[dict] = None
    ) -> HealthAssessment:
        """
        Assess overall project health across all dimensions.

        Args:
            project: Project object to analyze
            include_trends: Whether to calculate trend directions
            weights: Optional custom weights for dimensions
                     (default: equal weight of 0.2 each)

        Returns:
            HealthAssessment with overall score and dimension breakdowns
        """
        # Default equal weights
        default_weights = {
            "schedule": 0.2,
            "cost": 0.2,
            "scope": 0.2,
            "resource": 0.2,
            "quality": 0.2
        }
        dimension_weights = weights if weights else default_weights

        # Calculate each dimension
        schedule_dim = self._assess_schedule_health(project, dimension_weights.get("schedule", 0.2))
        cost_dim = self._assess_cost_health(project, dimension_weights.get("cost", 0.2))
        scope_dim = self._assess_scope_health(project, dimension_weights.get("scope", 0.2))
        resource_dim = self._assess_resource_health(project, dimension_weights.get("resource", 0.2))
        quality_dim = self._assess_quality_health(project, dimension_weights.get("quality", 0.2))

        dimensions = [schedule_dim, cost_dim, scope_dim, resource_dim, quality_dim]

        # Calculate overall score (weighted average)
        overall_score = sum(d.score * d.weight for d in dimensions)

        # Determine overall status
        if overall_score >= 80:
            overall_status = HealthStatus.HEALTHY
        elif overall_score >= 60:
            overall_status = HealthStatus.AT_RISK
        else:
            overall_status = HealthStatus.CRITICAL

        # Collect top concerns (issues from dimensions with lowest scores)
        all_issues = []
        for dim in sorted(dimensions, key=lambda d: d.score):
            all_issues.extend(dim.issues)
        top_concerns = all_issues[:5]  # Top 5 concerns

        # Generate recommendations
        recommendations = self._generate_recommendations(dimensions)

        # Calculate confidence (based on data availability)
        confidence = self._calculate_confidence(project, dimensions)

        return HealthAssessment(
            overall_score=overall_score,
            overall_status=overall_status,
            dimensions=dimensions,
            top_concerns=top_concerns,
            recommendations=recommendations,
            confidence=confidence
        )

    def _assess_schedule_health(self, project: Any, weight: float) -> HealthDimension:
        """Assess schedule health dimension."""
        tasks = getattr(project, 'tasks', [])
        work_tasks = [t for t in tasks if not getattr(t, 'is_summary', False)]

        if not work_tasks:
            return HealthDimension(
                name="Schedule",
                score=50.0,
                status=HealthStatus.UNKNOWN,
                trend=TrendDirection.UNKNOWN,
                issues=["No task data available"],
                weight=weight
            )

        issues = []
        score = 100.0
        today = date.today()

        # Check for overdue tasks
        overdue_tasks = []
        for task in work_tasks:
            finish_date = getattr(task, 'finish_date', None)
            percent_complete = getattr(task, 'percent_complete', 0)

            if finish_date and percent_complete < 100:
                if isinstance(finish_date, str):
                    finish_date = datetime.fromisoformat(finish_date).date()
                elif isinstance(finish_date, datetime):
                    finish_date = finish_date.date()

                if finish_date < today:
                    overdue_tasks.append(task)

        if overdue_tasks:
            overdue_pct = (len(overdue_tasks) / len(work_tasks)) * 100
            score -= min(overdue_pct * 0.5, 30)  # Up to -30 points
            issues.append(f"{len(overdue_tasks)} tasks overdue ({overdue_pct:.1f}%)")

        # Check critical path status
        critical_tasks = [t for t in work_tasks if getattr(t, 'is_critical', False)]
        if critical_tasks:
            critical_overdue = [t for t in critical_tasks if t in overdue_tasks]
            if critical_overdue:
                score -= 20
                issues.append(f"{len(critical_overdue)} critical tasks overdue")

        # Check baseline variance
        baseline_slip_count = 0
        for task in work_tasks:
            baseline_finish = getattr(task, 'baseline_finish', None)
            current_finish = getattr(task, 'finish_date', None)

            if baseline_finish and current_finish:
                if isinstance(baseline_finish, str):
                    baseline_finish = datetime.fromisoformat(baseline_finish).date()
                elif isinstance(baseline_finish, datetime):
                    baseline_finish = baseline_finish.date()

                if isinstance(current_finish, str):
                    current_finish = datetime.fromisoformat(current_finish).date()
                elif isinstance(current_finish, datetime):
                    current_finish = current_finish.date()

                if current_finish > baseline_finish:
                    baseline_slip_count += 1

        if baseline_slip_count > 0:
            slip_pct = (baseline_slip_count / len(work_tasks)) * 100
            if slip_pct > 20:
                score -= min(slip_pct * 0.3, 20)  # Up to -20 points
                issues.append(f"{baseline_slip_count} tasks slipping from baseline ({slip_pct:.1f}%)")

        # Determine status
        if score >= 80:
            status = HealthStatus.HEALTHY
        elif score >= 60:
            status = HealthStatus.AT_RISK
        else:
            status = HealthStatus.CRITICAL

        # Trend (simplified - would need historical data for real trend)
        trend = TrendDirection.STABLE
        if len(issues) > 2:
            trend = TrendDirection.DECLINING
        elif len(issues) == 0:
            trend = TrendDirection.IMPROVING

        return HealthDimension(
            name="Schedule",
            score=max(0.0, score),
            status=status,
            trend=trend,
            issues=issues,
            weight=weight
        )

    def _assess_cost_health(self, project: Any, weight: float) -> HealthDimension:
        """Assess cost health dimension."""
        budget = getattr(project, 'budget', None)
        actual_cost = getattr(project, 'actual_cost', None)
        forecast_cost = getattr(project, 'forecast_cost', None)

        issues = []
        score = 100.0

        # Extract numeric values
        budget_amount = self._get_cost_value(budget)
        actual_amount = self._get_cost_value(actual_cost)
        forecast_amount = self._get_cost_value(forecast_cost)

        if not budget_amount:
            return HealthDimension(
                name="Cost",
                score=50.0,
                status=HealthStatus.UNKNOWN,
                trend=TrendDirection.UNKNOWN,
                issues=["No budget data available"],
                weight=weight
            )

        # Check forecast variance
        if forecast_amount:
            variance_pct = ((forecast_amount - budget_amount) / budget_amount) * 100
            if variance_pct > 0:
                score -= min(variance_pct, 40)  # Up to -40 points
                issues.append(f"Forecast {variance_pct:.1f}% over budget")

        # Check spending rate
        if actual_amount:
            spent_pct = (actual_amount / budget_amount) * 100
            if spent_pct > 90:
                score -= 20
                issues.append(f"{spent_pct:.1f}% of budget spent")
            elif spent_pct > 100:
                score -= 40
                issues.append(f"Budget exceeded by {spent_pct - 100:.1f}%")

        # Determine status
        if score >= 80:
            status = HealthStatus.HEALTHY
        elif score >= 60:
            status = HealthStatus.AT_RISK
        else:
            status = HealthStatus.CRITICAL

        trend = TrendDirection.STABLE
        if len(issues) > 1:
            trend = TrendDirection.DECLINING

        return HealthDimension(
            name="Cost",
            score=max(0.0, score),
            status=status,
            trend=trend,
            issues=issues,
            weight=weight
        )

    def _assess_scope_health(self, project: Any, weight: float) -> HealthDimension:
        """Assess scope health dimension."""
        tasks = getattr(project, 'tasks', [])
        work_tasks = [t for t in tasks if not getattr(t, 'is_summary', False)]

        if not work_tasks:
            return HealthDimension(
                name="Scope",
                score=50.0,
                status=HealthStatus.UNKNOWN,
                trend=TrendDirection.UNKNOWN,
                issues=["No task data available"],
                weight=weight
            )

        issues = []
        score = 100.0

        # Check for milestones
        milestones = [t for t in tasks if getattr(t, 'is_milestone', False)]
        if len(work_tasks) > 10 and len(milestones) == 0:
            score -= 15
            issues.append("No milestones defined")

        # Check for task definitions
        undefined_count = sum(1 for t in work_tasks if not getattr(t, 'notes', '').strip())
        if undefined_count > len(work_tasks) * 0.3:
            score -= 20
            issues.append(f"{undefined_count} tasks lack descriptions")

        # Check completion rate
        completed = sum(1 for t in work_tasks if getattr(t, 'percent_complete', 0) == 100)
        completion_pct = (completed / len(work_tasks)) * 100

        # Determine status
        if score >= 80:
            status = HealthStatus.HEALTHY
        elif score >= 60:
            status = HealthStatus.AT_RISK
        else:
            status = HealthStatus.CRITICAL

        trend = TrendDirection.STABLE

        return HealthDimension(
            name="Scope",
            score=max(0.0, score),
            status=status,
            trend=trend,
            issues=issues,
            weight=weight
        )

    def _assess_resource_health(self, project: Any, weight: float) -> HealthDimension:
        """Assess resource health dimension."""
        resources = getattr(project, 'resources', [])

        if not resources:
            return HealthDimension(
                name="Resource",
                score=75.0,
                status=HealthStatus.HEALTHY,
                trend=TrendDirection.STABLE,
                issues=[],
                weight=weight
            )

        issues = []
        score = 100.0

        # Check for overallocation
        overallocated = [r for r in resources if getattr(r, 'max_units', 1.0) > 1.2]
        if overallocated:
            score -= min(len(overallocated) * 10, 30)
            issues.append(f"{len(overallocated)} resources overallocated")

        # Determine status
        if score >= 80:
            status = HealthStatus.HEALTHY
        elif score >= 60:
            status = HealthStatus.AT_RISK
        else:
            status = HealthStatus.CRITICAL

        trend = TrendDirection.STABLE

        return HealthDimension(
            name="Resource",
            score=max(0.0, score),
            status=status,
            trend=trend,
            issues=issues,
            weight=weight
        )

    def _assess_quality_health(self, project: Any, weight: float) -> HealthDimension:
        """Assess quality health dimension."""
        # Quality metrics are often not available in standard PM data
        # This is a placeholder implementation
        return HealthDimension(
            name="Quality",
            score=75.0,
            status=HealthStatus.HEALTHY,
            trend=TrendDirection.STABLE,
            issues=[],
            weight=weight
        )

    def _generate_recommendations(self, dimensions: List[HealthDimension]) -> List[str]:
        """Generate recommendations based on dimension health."""
        recommendations = []

        for dim in sorted(dimensions, key=lambda d: d.score):
            if dim.status == HealthStatus.CRITICAL:
                recommendations.append(f"URGENT: Address critical {dim.name.lower()} issues immediately")
            elif dim.status == HealthStatus.AT_RISK:
                recommendations.append(f"Monitor and improve {dim.name.lower()} health")

        if not recommendations:
            recommendations.append("Continue current project management practices")

        return recommendations[:5]  # Top 5 recommendations

    def _calculate_confidence(self, project: Any, dimensions: List[HealthDimension]) -> float:
        """Calculate confidence in health assessment."""
        # Base confidence
        confidence = 0.70

        # Increase if we have more data
        if getattr(project, 'tasks', []):
            confidence += 0.10
        if getattr(project, 'budget', None):
            confidence += 0.10
        if getattr(project, 'resources', []):
            confidence += 0.05

        return min(confidence, 0.95)

    def _get_cost_value(self, cost: Any) -> Optional[float]:
        """Extract numeric value from cost object or number."""
        if cost is None:
            return None
        if isinstance(cost, (int, float)):
            return float(cost)
        if hasattr(cost, 'amount'):
            amount = getattr(cost, 'amount')
            if isinstance(amount, (int, float)):
                return float(amount)
        return None


class BaselineComparator:
    """
    Compares current project state against baseline.

    Identifies variances in:
    - Schedule (date slippage)
    - Duration (scope changes)
    - Cost (budget changes)
    - Progress (performance issues)
    """

    # Variance thresholds
    SCHEDULE_WARNING_DAYS = 5
    SCHEDULE_CRITICAL_DAYS = 14
    DURATION_WARNING_PERCENT = 20
    DURATION_CRITICAL_PERCENT = 50
    COST_WARNING_PERCENT = 10
    COST_CRITICAL_PERCENT = 25

    def __init__(self):
        """Initialize the baseline comparator."""
        pass

    def compare(
        self,
        project: Any,
        baseline_type: str = "current",
        threshold: float = 0.0
    ) -> List[BaselineVariance]:
        """
        Compare current values against baseline.

        Args:
            project: Project object with baseline data
            baseline_type: Type of baseline to compare against
                          ("current", "original", "approved")
            threshold: Minimum variance percentage to report (0-100)

        Returns:
            List of baseline variances with severity classification
        """
        variances = []
        tasks = getattr(project, 'tasks', [])
        work_tasks = [t for t in tasks if not getattr(t, 'is_summary', False)]

        for task in work_tasks:
            task_id = str(getattr(task, 'id', ''))
            task_name = getattr(task, 'name', 'Unnamed Task')

            # Compare finish dates
            baseline_finish = getattr(task, 'baseline_finish', None)
            current_finish = getattr(task, 'finish_date', None)

            if baseline_finish and current_finish:
                if isinstance(baseline_finish, str):
                    baseline_finish = datetime.fromisoformat(baseline_finish).date()
                elif isinstance(baseline_finish, datetime):
                    baseline_finish = baseline_finish.date()

                if isinstance(current_finish, str):
                    current_finish = datetime.fromisoformat(current_finish).date()
                elif isinstance(current_finish, datetime):
                    current_finish = current_finish.date()

                variance_days = (current_finish - baseline_finish).days

                if abs(variance_days) > 0:
                    # Determine severity
                    if abs(variance_days) >= self.SCHEDULE_CRITICAL_DAYS:
                        severity = Severity.CRITICAL
                    elif abs(variance_days) >= self.SCHEDULE_WARNING_DAYS:
                        severity = Severity.HIGH
                    else:
                        severity = Severity.MEDIUM

                    # Calculate percentage (relative to task duration)
                    baseline_start = getattr(task, 'baseline_start', None)
                    if baseline_start:
                        if isinstance(baseline_start, str):
                            baseline_start = datetime.fromisoformat(baseline_start).date()
                        elif isinstance(baseline_start, datetime):
                            baseline_start = baseline_start.date()

                        baseline_duration = (baseline_finish - baseline_start).days
                        variance_percent = (variance_days / baseline_duration * 100) if baseline_duration > 0 else 0
                    else:
                        variance_percent = 0

                    if abs(variance_percent) >= threshold:
                        variances.append(BaselineVariance(
                            task_id=task_id,
                            task_name=task_name,
                            field_name="finish_date",
                            baseline_value=baseline_finish,
                            current_value=current_finish,
                            variance=float(variance_days),
                            variance_percent=variance_percent,
                            severity=severity,
                            explanation=f"Finish date {'slipped' if variance_days > 0 else 'pulled in'} by {abs(variance_days)} days"
                        ))

            # Compare durations
            baseline_duration = getattr(task, 'baseline_duration', None)
            start_date = getattr(task, 'start_date', None)
            finish_date = getattr(task, 'finish_date', None)

            if baseline_duration and start_date and finish_date:
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(start_date).date()
                elif isinstance(start_date, datetime):
                    start_date = start_date.date()

                if isinstance(finish_date, str):
                    finish_date = datetime.fromisoformat(finish_date).date()
                elif isinstance(finish_date, datetime):
                    finish_date = finish_date.date()

                current_duration = (finish_date - start_date).days

                # Get baseline duration as days
                if hasattr(baseline_duration, 'to_days'):
                    baseline_days = int(baseline_duration.to_days())
                else:
                    baseline_days = int(baseline_duration)

                duration_variance = current_duration - baseline_days
                duration_variance_pct = (duration_variance / baseline_days * 100) if baseline_days > 0 else 0

                if abs(duration_variance_pct) >= self.DURATION_WARNING_PERCENT:
                    if abs(duration_variance_pct) >= self.DURATION_CRITICAL_PERCENT:
                        severity = Severity.CRITICAL
                    else:
                        severity = Severity.HIGH

                    if abs(duration_variance_pct) >= threshold:
                        variances.append(BaselineVariance(
                            task_id=task_id,
                            task_name=task_name,
                            field_name="duration",
                            baseline_value=baseline_days,
                            current_value=current_duration,
                            variance=float(duration_variance),
                            variance_percent=duration_variance_pct,
                            severity=severity,
                            explanation=f"Duration {'increased' if duration_variance > 0 else 'decreased'} by {abs(duration_variance)} days ({abs(duration_variance_pct):.1f}%)"
                        ))

        return variances
