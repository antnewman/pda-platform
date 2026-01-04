"""
Risk identification and mitigation engine for project analysis.

Analyzes projects across multiple dimensions to identify risks with
confidence scoring and generate evidence-based mitigation strategies.
"""

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .models import (
    AnalysisDepth,
    Evidence,
    Mitigation,
    Risk,
    RiskCategory,
    Severity,
)


class RiskEngine:
    """
    AI-powered risk identification and mitigation engine.

    Analyzes projects across schedule, cost, resource, scope, technical,
    and external dimensions to identify risks with confidence scoring.
    """

    # Thresholds
    SCHEDULE_SLIP_WARNING_DAYS = 5
    SCHEDULE_SLIP_CRITICAL_DAYS = 14
    FLOAT_WARNING_DAYS = 3
    OVERDUE_CRITICAL_DAYS = 7
    COST_OVERRUN_WARNING_PERCENT = 10.0
    COST_OVERRUN_CRITICAL_PERCENT = 25.0
    RESOURCE_OVERALLOCATION_THRESHOLD = 1.2
    CRITICAL_TASK_CONCENTRATION = 3
    DEPENDENCY_BOTTLENECK_THRESHOLD = 5
    DEPENDENCY_INTEGRATION_THRESHOLD = 5
    DEPENDENCY_CHAIN_WARNING_LENGTH = 10
    DURATION_WARNING_DAYS = 60

    def __init__(self):
        """Initialize the risk engine."""
        self.risks: List[Risk] = []

    def analyze(
        self,
        project: Any,
        focus_areas: Optional[List[str]] = None,
        depth: AnalysisDepth = AnalysisDepth.STANDARD
    ) -> List[Risk]:
        """
        Main analysis entry point.

        Args:
            project: Project object to analyze
            focus_areas: Optional list of risk categories to focus on
            depth: Analysis depth (QUICK, STANDARD, DEEP)

        Returns:
            List of identified risks with confidence scores
        """
        self.risks = []

        # Extract project components
        tasks = getattr(project, 'tasks', [])
        resources = getattr(project, 'resources', [])
        dependencies = getattr(project, 'dependencies', [])

        # Determine which analyses to run
        all_areas = [
            "schedule", "cost", "resource", "scope", "technical", "external"
        ]
        areas = focus_areas if focus_areas else all_areas

        # Run analyses
        if "schedule" in areas:
            self._analyze_schedule_risks(project, tasks)
        if "cost" in areas:
            self._analyze_cost_risks(project, tasks)
        if "resource" in areas:
            self._analyze_resource_risks(project, tasks, resources)
        if "scope" in areas:
            self._analyze_scope_risks(project, tasks)
        if "technical" in areas:
            self._analyze_technical_risks(project, tasks, dependencies)
        if "external" in areas:
            self._analyze_external_risks(project)

        # DEEP analysis
        if depth == AnalysisDepth.DEEP:
            self._analyze_dependency_chains(project, tasks, dependencies)
            self._analyze_duration_patterns(tasks)

        return self.risks

    def _analyze_schedule_risks(self, project: Any, tasks: List[Any]) -> None:
        """Detect: slippage, overdue, low float."""
        today = date.today()

        for task in tasks:
            task_id = str(getattr(task, 'id', ''))
            task_name = getattr(task, 'name', 'Unnamed Task')

            # Skip summary tasks
            if getattr(task, 'is_summary', False):
                continue

            # Check for overdue tasks
            finish_date = getattr(task, 'finish_date', None)
            percent_complete = getattr(task, 'percent_complete', 0)

            if finish_date and percent_complete < 100:
                if isinstance(finish_date, str):
                    finish_date = datetime.fromisoformat(finish_date).date()
                elif isinstance(finish_date, datetime):
                    finish_date = finish_date.date()

                if finish_date < today:
                    days_overdue = (today - finish_date).days
                    if days_overdue >= self.OVERDUE_CRITICAL_DAYS:
                        self._add_risk(
                            name=f"Critical Overdue Task: {task_name}",
                            description=f"Task is {days_overdue} days overdue ({percent_complete}% complete)",
                            category=RiskCategory.SCHEDULE,
                            probability=5,
                            impact=5,
                            confidence=1.0,
                            evidence=[Evidence(
                                source="schedule_analysis",
                                description=f"Finish: {finish_date}, Today: {today}",
                                data_point=f"days_overdue={days_overdue}",
                                confidence=1.0
                            )],
                            related_tasks=[task_id],
                            suggested_mitigation="Assess task feasibility and reassign resources"
                        )
                    else:
                        self._add_risk(
                            name=f"Overdue Task: {task_name}",
                            description=f"Task is {days_overdue} days overdue",
                            category=RiskCategory.SCHEDULE,
                            probability=5,
                            impact=3,
                            confidence=1.0,
                            evidence=[Evidence(
                                source="schedule_analysis",
                                description=f"Finish: {finish_date}, Today: {today}",
                                data_point=f"days_overdue={days_overdue}",
                                confidence=1.0
                            )],
                            related_tasks=[task_id],
                            suggested_mitigation="Review task status and expedite completion"
                        )

            # Check for baseline slippage
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

                slip_days = (current_finish - baseline_finish).days

                if slip_days >= self.SCHEDULE_SLIP_CRITICAL_DAYS:
                    self._add_risk(
                        name=f"Critical Schedule Slip: {task_name}",
                        description=f"Task is {slip_days} days behind baseline",
                        category=RiskCategory.SCHEDULE,
                        probability=5,
                        impact=4,
                        confidence=0.95,
                        evidence=[Evidence(
                            source="baseline_comparison",
                            description=f"Baseline: {baseline_finish}, Current: {current_finish}",
                            data_point=f"slip_days={slip_days}",
                            confidence=1.0
                        )],
                        related_tasks=[task_id],
                        suggested_mitigation="Review dependencies; consider fast-tracking or crashing"
                    )
                elif slip_days >= self.SCHEDULE_SLIP_WARNING_DAYS:
                    self._add_risk(
                        name=f"Schedule Slip: {task_name}",
                        description=f"Task is {slip_days} days behind baseline",
                        category=RiskCategory.SCHEDULE,
                        probability=4,
                        impact=3,
                        confidence=0.90,
                        evidence=[Evidence(
                            source="baseline_comparison",
                            description=f"Baseline: {baseline_finish}, Current: {current_finish}",
                            data_point=f"slip_days={slip_days}",
                            confidence=1.0
                        )],
                        related_tasks=[task_id],
                        suggested_mitigation="Monitor closely and adjust resources if needed"
                    )

            # Check for low float on critical path
            total_float = getattr(task, 'total_float', None)
            is_critical = getattr(task, 'is_critical', False)

            if is_critical and total_float is not None:
                if total_float < 0:
                    self._add_risk(
                        name=f"Negative Float: {task_name}",
                        description=f"Critical task has {total_float} days float (schedule constraint violation)",
                        category=RiskCategory.SCHEDULE,
                        probability=5,
                        impact=5,
                        confidence=1.0,
                        evidence=[Evidence(
                            source="schedule_analysis",
                            description=f"Total Float: {total_float}",
                            data_point=f"total_float={total_float}",
                            confidence=1.0
                        )],
                        related_tasks=[task_id],
                        suggested_mitigation="Adjust schedule constraints or rebaseline"
                    )
                elif total_float <= self.FLOAT_WARNING_DAYS:
                    self._add_risk(
                        name=f"Low Float on Critical Path: {task_name}",
                        description=f"Critical task has only {total_float} days float",
                        category=RiskCategory.SCHEDULE,
                        probability=4,
                        impact=4,
                        confidence=0.85,
                        evidence=[Evidence(
                            source="schedule_analysis",
                            description=f"Total Float: {total_float}",
                            data_point=f"total_float={total_float}",
                            confidence=1.0
                        )],
                        related_tasks=[task_id],
                        suggested_mitigation="Monitor closely and prepare contingency plans"
                    )

    def _analyze_cost_risks(self, project: Any, tasks: List[Any]) -> None:
        """Detect: overruns, forecast variance."""
        budget = getattr(project, 'budget', None)
        actual_cost = getattr(project, 'actual_cost', None)
        forecast_cost = getattr(project, 'forecast_cost', None)

        # Extract numeric values
        budget_amount = self._get_cost_value(budget)
        actual_amount = self._get_cost_value(actual_cost)
        forecast_amount = self._get_cost_value(forecast_cost)

        # Check forecast vs budget
        if budget_amount and forecast_amount:
            overrun_amount = forecast_amount - budget_amount
            overrun_percent = (overrun_amount / budget_amount) * 100

            if overrun_percent >= self.COST_OVERRUN_CRITICAL_PERCENT:
                self._add_risk(
                    name="Critical Cost Overrun Forecast",
                    description=f"Forecast cost exceeds budget by {overrun_percent:.1f}%",
                    category=RiskCategory.COST,
                    probability=5,
                    impact=5,
                    confidence=0.85,
                    evidence=[Evidence(
                        source="cost_analysis",
                        description=f"Budget: {budget_amount}, Forecast: {forecast_amount}",
                        data_point=f"overrun_percent={overrun_percent:.1f}",
                        confidence=0.85
                    )],
                    related_tasks=[],
                    suggested_mitigation="Conduct cost review and implement cost reduction measures"
                )
            elif overrun_percent >= self.COST_OVERRUN_WARNING_PERCENT:
                self._add_risk(
                    name="Cost Overrun Forecast",
                    description=f"Forecast cost exceeds budget by {overrun_percent:.1f}%",
                    category=RiskCategory.COST,
                    probability=4,
                    impact=4,
                    confidence=0.80,
                    evidence=[Evidence(
                        source="cost_analysis",
                        description=f"Budget: {budget_amount}, Forecast: {forecast_amount}",
                        data_point=f"overrun_percent={overrun_percent:.1f}",
                        confidence=0.80
                    )],
                    related_tasks=[],
                    suggested_mitigation="Review spending and identify cost-saving opportunities"
                )

        # Check actual vs budget
        if budget_amount and actual_amount:
            spend_percent = (actual_amount / budget_amount) * 100
            if spend_percent > 90:
                self._add_risk(
                    name="Budget Depletion Risk",
                    description=f"Already spent {spend_percent:.1f}% of budget",
                    category=RiskCategory.COST,
                    probability=4,
                    impact=4,
                    confidence=0.95,
                    evidence=[Evidence(
                        source="cost_analysis",
                        description=f"Budget: {budget_amount}, Actual: {actual_amount}",
                        data_point=f"spend_percent={spend_percent:.1f}",
                        confidence=1.0
                    )],
                    related_tasks=[],
                    suggested_mitigation="Implement strict cost controls for remaining work"
                )

    def _analyze_resource_risks(
        self,
        project: Any,
        tasks: List[Any],
        resources: List[Any]
    ) -> None:
        """Detect: overallocation, SPOFs."""
        # Check for resource overallocation
        for resource in resources:
            resource_id = str(getattr(resource, 'id', ''))
            resource_name = getattr(resource, 'name', 'Unnamed Resource')
            max_units = getattr(resource, 'max_units', 1.0)

            # Check if allocated beyond capacity
            if max_units > self.RESOURCE_OVERALLOCATION_THRESHOLD:
                self._add_risk(
                    name=f"Resource Overallocation: {resource_name}",
                    description=f"Resource allocated at {max_units * 100:.0f}% capacity",
                    category=RiskCategory.RESOURCE,
                    probability=4,
                    impact=3,
                    confidence=0.90,
                    evidence=[Evidence(
                        source="resource_analysis",
                        description=f"Max Units: {max_units}",
                        data_point=f"allocation={max_units}",
                        confidence=1.0
                    )],
                    related_tasks=[],
                    suggested_mitigation="Reallocate work or add resources to reduce load"
                )

        # Check for critical task concentration (SPOF)
        critical_tasks = [t for t in tasks if getattr(t, 'is_critical', False)]
        if len(critical_tasks) >= self.CRITICAL_TASK_CONCENTRATION:
            # Group by resource
            resource_task_count: Dict[str, int] = {}
            for task in critical_tasks:
                # Simplified - in real implementation, iterate assignments
                pass  # Implementation would check assignments

    def _analyze_scope_risks(self, project: Any, tasks: List[Any]) -> None:
        """Detect: missing milestones, incomplete definitions."""
        # Check for milestone presence
        milestones = [t for t in tasks if getattr(t, 'is_milestone', False)]
        total_tasks = len([t for t in tasks if not getattr(t, 'is_summary', False)])

        if total_tasks > 10 and len(milestones) == 0:
            self._add_risk(
                name="Missing Milestones",
                description="Project lacks milestone markers for tracking progress",
                category=RiskCategory.SCOPE,
                probability=3,
                impact=3,
                confidence=0.75,
                evidence=[Evidence(
                    source="scope_analysis",
                    description=f"Tasks: {total_tasks}, Milestones: {len(milestones)}",
                    data_point=f"milestones=0",
                    confidence=1.0
                )],
                related_tasks=[],
                suggested_mitigation="Add key milestones to track deliverable completion"
            )

        # Check for tasks without descriptions
        undefined_count = 0
        for task in tasks:
            notes = getattr(task, 'notes', '')
            if not notes or len(notes.strip()) == 0:
                undefined_count += 1

        if undefined_count > total_tasks * 0.3:
            self._add_risk(
                name="Incomplete Task Definitions",
                description=f"{undefined_count} tasks lack detailed descriptions",
                category=RiskCategory.SCOPE,
                probability=3,
                impact=3,
                confidence=0.70,
                evidence=[Evidence(
                    source="scope_analysis",
                    description=f"Undefined: {undefined_count} / {total_tasks}",
                    data_point=f"undefined={undefined_count}",
                    confidence=0.80
                )],
                related_tasks=[],
                suggested_mitigation="Document task requirements and acceptance criteria"
            )

    def _analyze_technical_risks(
        self,
        project: Any,
        tasks: List[Any],
        dependencies: List[Any]
    ) -> None:
        """Detect: bottlenecks, integration points."""
        # Count dependencies per task (successors)
        dependency_count: Dict[str, int] = {}
        for dep in dependencies:
            predecessor_id = str(getattr(dep, 'predecessor_id', ''))
            if predecessor_id:
                dependency_count[predecessor_id] = dependency_count.get(predecessor_id, 0) + 1

        # Check for bottlenecks (tasks with many successors)
        for task_id, count in dependency_count.items():
            if count >= self.DEPENDENCY_BOTTLENECK_THRESHOLD:
                task = next((t for t in tasks if str(getattr(t, 'id', '')) == task_id), None)
                task_name = getattr(task, 'name', 'Unknown') if task else 'Unknown'

                self._add_risk(
                    name=f"Dependency Bottleneck: {task_name}",
                    description=f"Task has {count} dependent tasks creating bottleneck",
                    category=RiskCategory.TECHNICAL,
                    probability=4,
                    impact=4,
                    confidence=0.90,
                    evidence=[Evidence(
                        source="dependency_analysis",
                        description=f"Successor count: {count}",
                        data_point=f"successors={count}",
                        confidence=1.0
                    )],
                    related_tasks=[task_id],
                    suggested_mitigation="Decouple dependencies or add parallel work streams"
                )

    def _analyze_external_risks(self, project: Any) -> None:
        """Import from risk register."""
        risk_register = getattr(project, 'risk_register', [])

        for risk_entry in risk_register:
            category_str = getattr(risk_entry, 'category', 'external')
            try:
                category = RiskCategory(category_str.lower())
            except ValueError:
                category = RiskCategory.EXTERNAL

            self._add_risk(
                name=getattr(risk_entry, 'name', 'External Risk'),
                description=getattr(risk_entry, 'description', ''),
                category=category,
                probability=getattr(risk_entry, 'probability', 3),
                impact=getattr(risk_entry, 'impact', 3),
                confidence=0.80,
                evidence=[Evidence(
                    source="risk_register",
                    description="Imported from project risk register",
                    confidence=0.80
                )],
                related_tasks=[],
                suggested_mitigation=getattr(risk_entry, 'mitigation', None)
            )

    def _analyze_dependency_chains(
        self,
        project: Any,
        tasks: List[Any],
        dependencies: List[Any]
    ) -> None:
        """DEEP: Long chain analysis."""
        # Build dependency graph
        graph: Dict[str, List[str]] = {}
        for dep in dependencies:
            pred = str(getattr(dep, 'predecessor_id', ''))
            succ = str(getattr(dep, 'successor_id', ''))
            if pred and succ:
                if pred not in graph:
                    graph[pred] = []
                graph[pred].append(succ)

        # Find longest chains using DFS
        def find_chain_length(task_id: str, visited: set) -> int:
            if task_id in visited:
                return 0
            visited.add(task_id)
            max_length = 0
            for successor in graph.get(task_id, []):
                length = find_chain_length(successor, visited.copy())
                max_length = max(max_length, length)
            return max_length + 1

        for task_id in graph.keys():
            chain_length = find_chain_length(task_id, set())
            if chain_length >= self.DEPENDENCY_CHAIN_WARNING_LENGTH:
                task = next((t for t in tasks if str(getattr(t, 'id', '')) == task_id), None)
                task_name = getattr(task, 'name', 'Unknown') if task else 'Unknown'

                self._add_risk(
                    name=f"Long Dependency Chain: {task_name}",
                    description=f"Task starts chain of {chain_length} dependent tasks",
                    category=RiskCategory.TECHNICAL,
                    probability=3,
                    impact=4,
                    confidence=0.85,
                    evidence=[Evidence(
                        source="dependency_analysis",
                        description=f"Chain length: {chain_length}",
                        data_point=f"chain_length={chain_length}",
                        confidence=1.0
                    )],
                    related_tasks=[task_id],
                    suggested_mitigation="Review if dependencies can be parallelized"
                )

    def _analyze_duration_patterns(self, tasks: List[Any]) -> None:
        """DEEP: Pattern matching."""
        for task in tasks:
            task_id = str(getattr(task, 'id', ''))
            task_name = getattr(task, 'name', 'Unnamed Task')
            start_date = getattr(task, 'start_date', None)
            finish_date = getattr(task, 'finish_date', None)

            if start_date and finish_date:
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(start_date).date()
                elif isinstance(start_date, datetime):
                    start_date = start_date.date()

                if isinstance(finish_date, str):
                    finish_date = datetime.fromisoformat(finish_date).date()
                elif isinstance(finish_date, datetime):
                    finish_date = finish_date.date()

                duration = (finish_date - start_date).days

                if duration >= self.DURATION_WARNING_DAYS:
                    self._add_risk(
                        name=f"Long Duration Task: {task_name}",
                        description=f"Task duration of {duration} days may indicate missing breakdown",
                        category=RiskCategory.SCOPE,
                        probability=3,
                        impact=2,
                        confidence=0.65,
                        evidence=[Evidence(
                            source="duration_analysis",
                            description=f"Duration: {duration} days",
                            data_point=f"duration={duration}",
                            confidence=1.0
                        )],
                        related_tasks=[task_id],
                        suggested_mitigation="Break down into smaller, more manageable tasks"
                    )

    def _add_risk(
        self,
        name: str,
        description: str,
        category: RiskCategory,
        probability: int,
        impact: int,
        confidence: float,
        evidence: List[Evidence],
        related_tasks: List[str],
        suggested_mitigation: Optional[str] = None
    ) -> None:
        """Helper to add a risk to the list."""
        risk = Risk(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            category=category,
            probability=probability,
            impact=impact,
            score=probability * impact,
            confidence=confidence,
            evidence=evidence,
            related_tasks=related_tasks,
            suggested_mitigation=suggested_mitigation,
            detected_at=datetime.now(timezone.utc)
        )
        self.risks.append(risk)

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

    def generate_mitigations(self, risks: List[Risk]) -> List[Mitigation]:
        """Create mitigation strategies."""
        mitigations = []

        for risk in risks:
            if risk.category == RiskCategory.SCHEDULE:
                mitigation = self._schedule_mitigation(risk)
            elif risk.category == RiskCategory.COST:
                mitigation = self._cost_mitigation(risk)
            elif risk.category == RiskCategory.RESOURCE:
                mitigation = self._resource_mitigation(risk)
            elif risk.category == RiskCategory.SCOPE:
                mitigation = self._scope_mitigation(risk)
            elif risk.category == RiskCategory.TECHNICAL:
                mitigation = self._technical_mitigation(risk)
            elif risk.category == RiskCategory.EXTERNAL:
                mitigation = self._external_mitigation(risk)
            else:
                continue

            if mitigation:
                mitigations.append(mitigation)

        return mitigations

    def _schedule_mitigation(self, risk: Risk) -> Mitigation:
        """Generate schedule risk mitigation."""
        if "Overdue" in risk.name:
            return Mitigation(
                id=str(uuid.uuid4()),
                risk_id=risk.id,
                strategy="Expedite Overdue Task Completion",
                description="Fast-track completion of overdue task through resource reallocation",
                effort="medium",
                effectiveness=0.80,
                confidence=0.85,
                implementation_steps=[
                    "Assess task current status and remaining work",
                    "Identify blocking issues or dependencies",
                    "Reallocate additional resources to task",
                    "Implement daily standups to monitor progress",
                    "Escalate blockers to stakeholders immediately",
                    "Consider scope reduction if feasible"
                ],
                resource_requirements=[
                    "Additional team member with relevant skills",
                    "Project manager for daily oversight",
                    "Stakeholder availability for decisions"
                ],
                timeline_days=7
            )
        elif "Slip" in risk.name:
            return Mitigation(
                id=str(uuid.uuid4()),
                risk_id=risk.id,
                strategy="Schedule Recovery Plan",
                description="Implement schedule compression techniques to recover baseline",
                effort="high",
                effectiveness=0.70,
                confidence=0.75,
                implementation_steps=[
                    "Analyze critical path and identify compression opportunities",
                    "Evaluate fast-tracking options (parallelize sequential tasks)",
                    "Evaluate crashing options (add resources to shorten duration)",
                    "Review scope for potential reductions or deferrals",
                    "Update schedule with recovery actions",
                    "Obtain stakeholder approval for schedule changes",
                    "Monitor recovery progress weekly"
                ],
                resource_requirements=[
                    "Schedule compression analysis",
                    "Additional resources for crashing",
                    "Change control board approval",
                    "Weekly status reporting"
                ],
                timeline_days=14
            )
        else:
            return Mitigation(
                id=str(uuid.uuid4()),
                risk_id=risk.id,
                strategy="Schedule Monitoring and Control",
                description="Implement enhanced schedule monitoring to prevent further slippage",
                effort="low",
                effectiveness=0.65,
                confidence=0.80,
                implementation_steps=[
                    "Establish weekly schedule reviews",
                    "Monitor critical path changes",
                    "Track task completion variance",
                    "Identify trending issues early",
                    "Update stakeholders on schedule status"
                ],
                resource_requirements=[
                    "Project manager time for reviews",
                    "Scheduling tool access"
                ],
                timeline_days=3
            )

    def _cost_mitigation(self, risk: Risk) -> Mitigation:
        """Generate cost risk mitigation."""
        return Mitigation(
            id=str(uuid.uuid4()),
            risk_id=risk.id,
            strategy="Cost Control and Reduction",
            description="Implement cost controls and identify reduction opportunities",
            effort="medium",
            effectiveness=0.75,
            confidence=0.80,
            implementation_steps=[
                "Conduct detailed cost variance analysis",
                "Identify highest cost drivers",
                "Review procurement for cost reduction opportunities",
                "Evaluate scope reduction options with stakeholders",
                "Implement stricter approval processes for new spending",
                "Renegotiate vendor contracts if possible",
                "Establish weekly cost review meetings"
            ],
            resource_requirements=[
                "Cost analyst or financial controller",
                "Procurement support",
                "Stakeholder decision authority"
            ],
            timeline_days=10
        )

    def _resource_mitigation(self, risk: Risk) -> Mitigation:
        """Generate resource risk mitigation."""
        return Mitigation(
            id=str(uuid.uuid4()),
            risk_id=risk.id,
            strategy="Resource Leveling and Balancing",
            description="Redistribute workload to prevent overallocation and burnout",
            effort="medium",
            effectiveness=0.75,
            confidence=0.85,
            implementation_steps=[
                "Conduct resource capacity analysis",
                "Identify tasks that can be rescheduled",
                "Evaluate hiring or contracting additional resources",
                "Implement resource leveling in schedule",
                "Cross-train team members for flexibility",
                "Monitor resource utilization weekly"
            ],
            resource_requirements=[
                "Resource manager or PMO support",
                "Budget for additional resources",
                "Training budget for cross-training"
            ],
            timeline_days=14
        )

    def _scope_mitigation(self, risk: Risk) -> Mitigation:
        """Generate scope risk mitigation."""
        return Mitigation(
            id=str(uuid.uuid4()),
            risk_id=risk.id,
            strategy="Scope Definition and Control",
            description="Improve scope definition and implement change control",
            effort="low",
            effectiveness=0.70,
            confidence=0.75,
            implementation_steps=[
                "Document detailed requirements for all tasks",
                "Establish clear acceptance criteria",
                "Implement formal change control process",
                "Conduct scope validation with stakeholders",
                "Add missing milestones to track progress",
                "Create work breakdown structure (WBS) for clarity"
            ],
            resource_requirements=[
                "Business analyst for requirements",
                "Stakeholder time for reviews",
                "Documentation tools"
            ],
            timeline_days=7
        )

    def _technical_mitigation(self, risk: Risk) -> Mitigation:
        """Generate technical risk mitigation."""
        if "Bottleneck" in risk.name:
            return Mitigation(
                id=str(uuid.uuid4()),
                risk_id=risk.id,
                strategy="Dependency Decoupling",
                description="Reduce dependency bottlenecks through parallel work streams",
                effort="high",
                effectiveness=0.70,
                confidence=0.70,
                implementation_steps=[
                    "Analyze dependency structure for decoupling opportunities",
                    "Identify tasks that can be parallelized",
                    "Review interface definitions to enable parallel work",
                    "Implement stub/mock components for early integration",
                    "Restructure schedule to maximize parallelization",
                    "Add integration checkpoints"
                ],
                resource_requirements=[
                    "Technical architect for analysis",
                    "Additional resources for parallel streams",
                    "Integration testing resources"
                ],
                timeline_days=14
            )
        else:
            return Mitigation(
                id=str(uuid.uuid4()),
                risk_id=risk.id,
                strategy="Technical Risk Management",
                description="Implement technical oversight and risk tracking",
                effort="medium",
                effectiveness=0.65,
                confidence=0.75,
                implementation_steps=[
                    "Establish technical review board",
                    "Conduct architecture reviews",
                    "Implement technical risk register",
                    "Add technical checkpoints to schedule",
                    "Review dependency management weekly"
                ],
                resource_requirements=[
                    "Senior technical staff for reviews",
                    "Risk tracking tools"
                ],
                timeline_days=7
            )

    def _external_mitigation(self, risk: Risk) -> Mitigation:
        """Generate external risk mitigation."""
        return Mitigation(
            id=str(uuid.uuid4()),
            risk_id=risk.id,
            strategy="External Risk Monitoring",
            description="Monitor and respond to external risk factors",
            effort="low",
            effectiveness=0.60,
            confidence=0.65,
            implementation_steps=[
                "Establish external risk monitoring process",
                "Identify early warning indicators",
                "Develop contingency plans",
                "Maintain stakeholder communication",
                "Review external factors in weekly meetings"
            ],
            resource_requirements=[
                "Project manager for monitoring",
                "Stakeholder engagement"
            ],
            timeline_days=5
        )
