"""GMPP data aggregation from multiple project management sources.

This module aggregates project data from various PM tools and systems into
complete GMPP quarterly reports, including:
- Financial performance calculations
- Schedule variance analysis
- Benefits realisation tracking
- Confidence scoring per field
- Data lineage tracking
"""

from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from pm_data_tools.models import Project, DeliveryConfidence
from pm_data_tools.gmpp.models import (
    QuarterlyReport,
    QuarterPeriod,
    FinancialPerformance,
    SchedulePerformance,
    BenefitsPerformance,
    DCANarrative,
    ReviewLevel,
)


class GMPPDataAggregator:
    """Aggregate project data from multiple sources into GMPP quarterly reports.

    This class provides comprehensive data aggregation for UK Government Major
    Projects Portfolio quarterly returns, pulling data from PM systems and
    calculating performance metrics with confidence scoring.

    Example:
        >>> aggregator = GMPPDataAggregator()
        >>> report = await aggregator.aggregate_quarterly_report(
        ...     project=project,
        ...     quarter="Q2",
        ...     financial_year="2025-26"
        ... )
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize data aggregator.

        Args:
            api_key: Anthropic API key for narrative generation (optional)
        """
        self.api_key = api_key

    async def aggregate_quarterly_report(
        self,
        project: Project,
        quarter: str,
        financial_year: str,
        previous_quarter_report: Optional[QuarterlyReport] = None,
        generate_narratives: bool = True,
    ) -> QuarterlyReport:
        """Generate complete GMPP quarterly report from project data.

        Args:
            project: Canonical project object
            quarter: Quarter period (Q1, Q2, Q3, Q4)
            financial_year: Financial year (format: "2025-26")
            previous_quarter_report: Previous quarter's report for delta calculations
            generate_narratives: Whether to generate AI narratives (requires API key)

        Returns:
            Complete quarterly report with all sections

        Raises:
            ValueError: If required data is missing
        """
        # Extract financial performance
        financial = self._extract_financial_performance(project)

        # Extract schedule performance
        schedule = self._extract_schedule_performance(project)

        # Extract benefits performance
        benefits = self._extract_benefits_performance(project)

        # Determine DCA rating
        dca_rating = self._map_dca_rating(project.delivery_confidence)

        # Check if DCA changed
        previous_dca = None
        dca_changed = False
        dca_change_rationale = None

        if previous_quarter_report:
            previous_dca = previous_quarter_report.dca_rating
            dca_changed = dca_rating != previous_dca

            if dca_changed:
                dca_change_rationale = self._generate_dca_change_rationale(
                    project,
                    dca_rating,
                    previous_dca
                )

        # Build project context for narrative generation
        project_context = self._extract_project_context(
            project,
            financial,
            schedule,
            benefits
        )

        # Generate AI narratives
        if generate_narratives and self.api_key:
            from pm_data_tools.gmpp.narratives import NarrativeGenerator

            generator = NarrativeGenerator(self.api_key)

            dca_narrative = await generator.generate_dca_narrative(
                project_data=project_context,
                dca_rating=dca_rating
            )

            cost_narrative = await generator.generate_cost_narrative(
                project_data=project_context
            )

            schedule_narrative = await generator.generate_schedule_narrative(
                project_data=project_context
            )

            benefits_narrative = await generator.generate_benefits_narrative(
                project_data=project_context
            )

            risk_narrative = await generator.generate_risk_narrative(
                project_data=project_context
            )

        else:
            # Create placeholder narratives if not generating
            placeholder_narrative = DCANarrative(
                text="[Narrative pending - AI generation disabled or API key not configured]",
                confidence=0.0,
                review_level=ReviewLevel.EXPERT_REQUIRED,
                generated_at=datetime.utcnow(),
                samples_used=0,
                review_reason="Narrative generation disabled"
            )

            dca_narrative = placeholder_narrative
            cost_narrative = placeholder_narrative
            schedule_narrative = placeholder_narrative
            benefits_narrative = placeholder_narrative
            risk_narrative = placeholder_narrative

        # Extract SRO details
        sro_name, sro_email = self._extract_sro_details(project)

        # Build quarterly report
        report = QuarterlyReport(
            # Reporting period
            quarter=QuarterPeriod(quarter),
            financial_year=financial_year,
            reporting_date=date.today(),
            # Project identification
            project_id=str(project.id),
            nista_project_code=self._generate_nista_code(project, financial_year, quarter),
            project_name=project.name,
            department=project.department or "Unknown Department",
            sro_name=sro_name,
            sro_email=sro_email,
            # Delivery confidence
            dca_rating=dca_rating,
            dca_narrative=dca_narrative,
            previous_dca_rating=previous_dca,
            dca_changed=dca_changed,
            dca_change_rationale=dca_change_rationale,
            # Performance metrics
            financial=financial,
            schedule=schedule,
            benefits=benefits,
            # Narratives
            cost_narrative=cost_narrative,
            schedule_narrative=schedule_narrative,
            benefits_narrative=benefits_narrative,
            risk_narrative=risk_narrative,
            # Metadata
            data_sources=self._extract_data_sources(project),
            confidence_scores=self._calculate_confidence_scores(project, financial, schedule, benefits),
            missing_fields=self._identify_missing_fields(project),
            validation_warnings=self._generate_validation_warnings(financial, schedule, benefits),
        )

        return report

    def _extract_financial_performance(self, project: Project) -> FinancialPerformance:
        """Extract financial performance metrics from project.

        Args:
            project: Canonical project object

        Returns:
            Financial performance metrics
        """
        # Convert to £ millions
        baseline_cost = (project.whole_life_cost.amount / 1_000_000) if project.whole_life_cost else Decimal("0")
        forecast_cost = (project.budgeted_cost.amount / 1_000_000) if project.budgeted_cost else baseline_cost
        actual_cost = (project.actual_cost.amount / 1_000_000) if project.actual_cost else None

        # Calculate variance
        variance_amount = forecast_cost - baseline_cost
        variance_percent = float((variance_amount / baseline_cost * 100)) if baseline_cost > 0 else 0.0

        # Calculate confidence based on data freshness and source
        confidence = self._score_financial_confidence(project)

        return FinancialPerformance(
            baseline_cost=baseline_cost,
            forecast_cost=forecast_cost,
            actual_cost=actual_cost,
            variance_percent=variance_percent,
            variance_amount=variance_amount,
            confidence=confidence,
        )

    def _extract_schedule_performance(self, project: Project) -> SchedulePerformance:
        """Extract schedule performance metrics from project.

        Args:
            project: Canonical project object

        Returns:
            Schedule performance metrics
        """
        baseline_completion = project.start_date.date() if project.start_date else date.today()
        forecast_completion = project.finish_date.date() if project.finish_date else baseline_completion

        # Calculate variance in weeks
        delta = (forecast_completion - baseline_completion).days
        variance_weeks = delta // 7

        # Check if critical path is at risk
        critical_path_at_risk = variance_weeks > 4 or self._has_high_schedule_risks(project)

        # Calculate confidence
        confidence = self._score_schedule_confidence(project)

        return SchedulePerformance(
            baseline_completion=baseline_completion,
            forecast_completion=forecast_completion,
            actual_completion=None,  # TODO: Extract if project completed
            variance_weeks=variance_weeks,
            critical_path_at_risk=critical_path_at_risk,
            confidence=confidence,
        )

    def _extract_benefits_performance(self, project: Project) -> BenefitsPerformance:
        """Extract benefits realisation metrics from project.

        Args:
            project: Canonical project object

        Returns:
            Benefits performance metrics
        """
        # Convert to £ millions
        total_planned = (project.monetised_benefits.amount / 1_000_000) if project.monetised_benefits else Decimal("0")
        forecast_total = total_planned  # TODO: Extract forecast if available
        realised_to_date = Decimal("0")  # TODO: Extract realised benefits tracking

        # Calculate realisation rate
        realisation_rate = float(realised_to_date / total_planned) if total_planned > 0 else 0.0

        # Calculate confidence
        confidence = self._score_benefits_confidence(project)

        return BenefitsPerformance(
            total_planned=total_planned,
            realised_to_date=realised_to_date,
            forecast_total=forecast_total,
            realisation_rate=realisation_rate,
            confidence=confidence,
        )

    def _map_dca_rating(self, delivery_confidence: Optional[DeliveryConfidence]) -> str:
        """Map DeliveryConfidence enum to GMPP DCA rating string.

        Args:
            delivery_confidence: Delivery confidence enum

        Returns:
            GMPP DCA rating (GREEN, AMBER, RED, EXEMPT)
        """
        if not delivery_confidence:
            return "EXEMPT"

        mapping = {
            DeliveryConfidence.GREEN: "GREEN",
            DeliveryConfidence.AMBER: "AMBER",
            DeliveryConfidence.RED: "RED",
            DeliveryConfidence.EXEMPT: "EXEMPT",
        }

        return mapping.get(delivery_confidence, "EXEMPT")

    def _extract_sro_details(self, project: Project) -> tuple[str, str]:
        """Extract SRO name and email from project.

        Args:
            project: Canonical project object

        Returns:
            Tuple of (sro_name, sro_email)
        """
        sro_name = project.senior_responsible_owner or "Unknown SRO"
        sro_email = "sro@example.gov.uk"  # TODO: Extract from resource if available

        # Try to find SRO in resources
        for resource in project.resources:
            if "sro" in resource.name.lower() or "senior responsible" in resource.name.lower():
                sro_name = resource.name
                # TODO: Extract email if available in resource custom fields
                break

        return sro_name, sro_email

    def _generate_nista_code(self, project: Project, financial_year: str, quarter: str) -> str:
        """Generate NISTA project code.

        Args:
            project: Canonical project object
            financial_year: Financial year (e.g., "2025-26")
            quarter: Quarter (Q1-Q4)

        Returns:
            NISTA project code (format: DEPT_NNNN_YYYY-QN)
        """
        dept = (project.department or "UNKNOWN")[:3].upper()
        year = financial_year.split("-")[0]
        # Use project ID hash for unique number
        project_num = abs(hash(str(project.id))) % 10000

        return f"{dept}_{project_num:04d}_{year}-{quarter}"

    def _extract_project_context(
        self,
        project: Project,
        financial: FinancialPerformance,
        schedule: SchedulePerformance,
        benefits: BenefitsPerformance,
    ) -> Dict:
        """Build project context for narrative generation.

        Args:
            project: Canonical project object
            financial: Financial performance metrics
            schedule: Schedule performance metrics
            benefits: Benefits performance metrics

        Returns:
            Dictionary of project context data
        """
        return {
            "project_name": project.name,
            "department": project.department or "Unknown",
            "baseline_cost": float(financial.baseline_cost),
            "forecast_cost": float(financial.forecast_cost),
            "cost_variance_percent": financial.variance_percent,
            "baseline_completion": schedule.baseline_completion.isoformat(),
            "forecast_completion": schedule.forecast_completion.isoformat(),
            "schedule_variance_weeks": schedule.variance_weeks,
            "total_benefits": float(benefits.total_planned),
            "realised_benefits": float(benefits.realised_to_date),
            "high_risks_count": len([r for r in project.risks if r.is_high_risk]),
            "critical_issues": self._extract_critical_issues(project),
            "achievements": self._extract_achievements(project),
            "risk_summary": self._extract_risk_summary(project),
        }

    def _extract_critical_issues(self, project: Project) -> str:
        """Extract critical issues from project.

        Args:
            project: Canonical project object

        Returns:
            Summary of critical issues
        """
        high_risks = [r for r in project.risks if r.is_high_risk and r.status.value not in ["CLOSED", "MATERIALISED"]]

        if not high_risks:
            return "No critical issues reported this quarter"

        issues = [f"- {risk.name}: {risk.description or 'No details'}" for risk in high_risks[:3]]
        return "\n".join(issues)

    def _extract_achievements(self, project: Project) -> str:
        """Extract key achievements from project.

        Args:
            project: Canonical project object

        Returns:
            Summary of achievements
        """
        # TODO: Extract from completed milestones
        completed_milestones = [t for t in project.tasks if t.is_milestone and t.actual_finish is not None]

        if not completed_milestones:
            return "No major milestones completed this quarter"

        achievements = [f"- {milestone.name} completed" for milestone in completed_milestones[:3]]
        return "\n".join(achievements)

    def _extract_risk_summary(self, project: Project) -> str:
        """Extract risk summary from project.

        Args:
            project: Canonical project object

        Returns:
            Risk summary text
        """
        high_risks = len([r for r in project.risks if r.is_high_risk])
        medium_risks = len([r for r in project.risks if r.is_medium_risk])
        low_risks = len([r for r in project.risks if r.is_low_risk])

        return f"{high_risks} high risks, {medium_risks} medium risks, {low_risks} low risks"

    def _has_high_schedule_risks(self, project: Project) -> bool:
        """Check if project has high schedule-related risks.

        Args:
            project: Canonical project object

        Returns:
            True if high schedule risks present
        """
        from pm_data_tools.models.risk import RiskCategory

        schedule_risks = [
            r for r in project.risks
            if r.category == RiskCategory.SCHEDULE and r.is_high_risk
        ]

        return len(schedule_risks) > 0

    def _score_financial_confidence(self, project: Project) -> float:
        """Calculate confidence score for financial data.

        Args:
            project: Canonical project object

        Returns:
            Confidence score (0.0-1.0)
        """
        score = 1.0

        # Reduce confidence if costs are missing
        if not project.whole_life_cost:
            score *= 0.5
        if not project.budgeted_cost:
            score *= 0.8

        # Reduce confidence based on data age (if available in source)
        # TODO: Check project.source.last_updated

        return max(0.0, min(1.0, score))

    def _score_schedule_confidence(self, project: Project) -> float:
        """Calculate confidence score for schedule data.

        Args:
            project: Canonical project object

        Returns:
            Confidence score (0.0-1.0)
        """
        score = 1.0

        # Reduce confidence if dates are missing
        if not project.start_date:
            score *= 0.5
        if not project.finish_date:
            score *= 0.5

        return max(0.0, min(1.0, score))

    def _score_benefits_confidence(self, project: Project) -> float:
        """Calculate confidence score for benefits data.

        Args:
            project: Canonical project object

        Returns:
            Confidence score (0.0-1.0)
        """
        score = 1.0

        # Reduce confidence if benefits not defined
        if not project.monetised_benefits:
            score *= 0.3

        return max(0.0, min(1.0, score))

    def _extract_data_sources(self, project: Project) -> List[str]:
        """Extract list of data sources used.

        Args:
            project: Canonical project object

        Returns:
            List of source system names
        """
        sources = []

        if project.source:
            tool = project.source.tool or "Unknown Tool"
            sources.append(tool)

        if project.risks:
            sources.append("Risk Register")

        return sources or ["Manual Entry"]

    def _calculate_confidence_scores(
        self,
        project: Project,
        financial: FinancialPerformance,
        schedule: SchedulePerformance,
        benefits: BenefitsPerformance,
    ) -> Dict[str, float]:
        """Calculate field-level confidence scores.

        Args:
            project: Canonical project object
            financial: Financial performance metrics
            schedule: Schedule performance metrics
            benefits: Benefits performance metrics

        Returns:
            Dictionary of field names to confidence scores
        """
        return {
            "financial": financial.confidence,
            "schedule": schedule.confidence,
            "benefits": benefits.confidence,
            "risks": 0.9 if project.risks else 0.5,
        }

    def _identify_missing_fields(self, project: Project) -> List[str]:
        """Identify recommended fields that are missing.

        Args:
            project: Canonical project object

        Returns:
            List of missing field names
        """
        missing = []

        if not project.description:
            missing.append("description")
        if not project.senior_responsible_owner:
            missing.append("senior_responsible_owner")
        if not project.project_manager:
            missing.append("project_manager")
        if not project.department:
            missing.append("department")
        if not project.monetised_benefits:
            missing.append("monetised_benefits")

        return missing

    def _generate_validation_warnings(
        self,
        financial: FinancialPerformance,
        schedule: SchedulePerformance,
        benefits: BenefitsPerformance,
    ) -> List[str]:
        """Generate validation warnings.

        Args:
            financial: Financial performance metrics
            schedule: Schedule performance metrics
            benefits: Benefits performance metrics

        Returns:
            List of warning messages
        """
        warnings = []

        # Cost variance warnings
        if abs(financial.variance_percent) > 10:
            warnings.append(f"Cost variance > 10% ({financial.variance_percent:.1f}%) - explain in narrative")

        # Schedule variance warnings
        if abs(schedule.variance_weeks) > 4:
            warnings.append(f"Schedule variance > 4 weeks ({schedule.variance_weeks} weeks) - consider escalation")

        # Benefits warnings
        if benefits.realisation_rate < 0.3 and benefits.total_planned > 0:
            warnings.append("Benefits realisation < 30% - verify tracking")

        return warnings

    def _generate_dca_change_rationale(
        self,
        project: Project,
        current_dca: str,
        previous_dca: str,
    ) -> str:
        """Generate rationale for DCA rating change.

        Args:
            project: Canonical project object
            current_dca: Current DCA rating
            previous_dca: Previous DCA rating

        Returns:
            Rationale text
        """
        # TODO: Use AI to generate more sophisticated rationale
        if current_dca > previous_dca:
            return "Project status deteriorated due to emerging risks and schedule delays"
        else:
            return "Project status improved due to successful mitigation actions"
