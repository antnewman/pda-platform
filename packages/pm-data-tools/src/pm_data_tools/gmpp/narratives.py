"""AI-powered narrative generation for GMPP quarterly reports.

This module uses the agent-task-planning framework to generate professional
civil service narratives with confidence scoring and multi-sample consensus.
"""

from typing import Dict
from datetime import datetime

from agent_planning import ConfidenceExtractor
from agent_planning.providers import AnthropicProvider
from agent_planning.confidence import CustomSchema
from agent_planning.guardrails import GuardrailConfig

from pm_data_tools.gmpp.models import DCANarrative, ReviewLevel


# Custom schema for GMPP narratives
GMPP_DCA_SCHEMA = CustomSchema(
    name="GMPP DCA Narrative",
    extraction_prompt="""Generate a Delivery Confidence Assessment narrative
suitable for UK Government GMPP quarterly reporting.

Requirements:
- 150-200 words
- Professional civil service style (suitable for ministers and Parliament)
- Objective and factual tone
- No marketing language, hyperbole, or promotional content
- Explain DCA rating with evidence from project data
- Mention key achievements this quarter
- Describe critical issues and their impact
- Outline mitigation actions being taken

Return as JSON with field: narrative_text""",
    aggregation_fields={"text": ["narrative_text"]},
)

GMPP_COST_SCHEMA = CustomSchema(
    name="GMPP Cost Narrative",
    extraction_prompt="""Generate a cost performance narrative for UK Government
GMPP quarterly reporting.

Requirements:
- 150-200 words
- Professional civil service style
- Explain cost variance (if any) with evidence
- Describe cost management actions
- Mention any budget reallocations or contingency usage

Return as JSON with field: narrative_text""",
    aggregation_fields={"text": ["narrative_text"]},
)

GMPP_SCHEDULE_SCHEMA = CustomSchema(
    name="GMPP Schedule Narrative",
    extraction_prompt="""Generate a schedule performance narrative for UK Government
GMPP quarterly reporting.

Requirements:
- 150-200 words
- Professional civil service style
- Explain schedule variance (if any) with evidence
- Describe critical path status
- Mention any schedule recovery actions

Return as JSON with field: narrative_text""",
    aggregation_fields={"text": ["narrative_text"]},
)

GMPP_BENEFITS_SCHEMA = CustomSchema(
    name="GMPP Benefits Narrative",
    extraction_prompt="""Generate a benefits realisation narrative for UK Government
GMPP quarterly reporting.

Requirements:
- 150-200 words
- Professional civil service style
- Describe benefits realised to date
- Explain any variance from plan
- Mention benefits tracking and measurement approach

Return as JSON with field: narrative_text""",
    aggregation_fields={"text": ["narrative_text"]},
)

GMPP_RISK_SCHEMA = CustomSchema(
    name="GMPP Risk Narrative",
    extraction_prompt="""Generate a risk status narrative for UK Government
GMPP quarterly reporting.

Requirements:
- 150-200 words
- Professional civil service style
- Summarize key risks (high priority)
- Describe mitigation actions in progress
- Mention any risks closed or newly identified this quarter

Return as JSON with field: narrative_text""",
    aggregation_fields={"text": ["narrative_text"]},
)


class NarrativeGenerator:
    """AI-powered narrative generation for GMPP reports.

    Uses the agent-task-planning framework to generate professional civil service
    narratives with multi-sample consensus and confidence scoring.

    Example:
        >>> generator = NarrativeGenerator(api_key="sk-ant-...")
        >>> narrative = await generator.generate_dca_narrative(
        ...     project_data={"project_name": "HS2", ...},
        ...     dca_rating="AMBER"
        ... )
        >>> print(f"Confidence: {narrative.confidence:.2%}")
        >>> print(narrative.text)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        samples: int = 5,
        confidence_threshold: float = 0.6,
    ):
        """Initialize narrative generator.

        Args:
            api_key: Anthropic API key
            model: Claude model to use (default: Sonnet 4)
            samples: Number of samples for consensus (default: 5)
            confidence_threshold: Minimum confidence for early stopping (default: 0.6)
        """
        self.api_key = api_key
        self.model = model
        self.samples = samples
        self.confidence_threshold = confidence_threshold

        # Configure provider
        self.provider = AnthropicProvider(api_key=api_key, model=model)

        # Configure guardrails
        guardrails = GuardrailConfig(
            confidence_samples=samples,
            confidence_temperature=0.7,
            confidence_early_stop_threshold=confidence_threshold,
            max_cost_usd=2.0,  # Per narrative
        )

        # Initialize extractor
        self.extractor = ConfidenceExtractor(self.provider, guardrails)

    async def generate_dca_narrative(
        self,
        project_data: Dict,
        dca_rating: str,
    ) -> DCANarrative:
        """Generate Delivery Confidence Assessment narrative.

        Args:
            project_data: Project context dictionary
            dca_rating: DCA rating (GREEN, AMBER, RED, etc.)

        Returns:
            DCA narrative with confidence metadata
        """
        prompt = self._build_dca_prompt(project_data, dca_rating)

        result = await self.extractor.extract(
            query=prompt,
            schema=GMPP_DCA_SCHEMA,
            samples=self.samples,
            early_stop=True,
        )

        return self._result_to_narrative(result)

    async def generate_cost_narrative(self, project_data: Dict) -> DCANarrative:
        """Generate cost performance narrative.

        Args:
            project_data: Project context dictionary

        Returns:
            Cost narrative with confidence metadata
        """
        prompt = self._build_cost_prompt(project_data)

        result = await self.extractor.extract(
            query=prompt,
            schema=GMPP_COST_SCHEMA,
            samples=self.samples,
            early_stop=True,
        )

        return self._result_to_narrative(result)

    async def generate_schedule_narrative(self, project_data: Dict) -> DCANarrative:
        """Generate schedule performance narrative.

        Args:
            project_data: Project context dictionary

        Returns:
            Schedule narrative with confidence metadata
        """
        prompt = self._build_schedule_prompt(project_data)

        result = await self.extractor.extract(
            query=prompt,
            schema=GMPP_SCHEDULE_SCHEMA,
            samples=self.samples,
            early_stop=True,
        )

        return self._result_to_narrative(result)

    async def generate_benefits_narrative(self, project_data: Dict) -> DCANarrative:
        """Generate benefits realisation narrative.

        Args:
            project_data: Project context dictionary

        Returns:
            Benefits narrative with confidence metadata
        """
        prompt = self._build_benefits_prompt(project_data)

        result = await self.extractor.extract(
            query=prompt,
            schema=GMPP_BENEFITS_SCHEMA,
            samples=self.samples,
            early_stop=True,
        )

        return self._result_to_narrative(result)

    async def generate_risk_narrative(self, project_data: Dict) -> DCANarrative:
        """Generate risk status narrative.

        Args:
            project_data: Project context dictionary

        Returns:
            Risk narrative with confidence metadata
        """
        prompt = self._build_risk_prompt(project_data)

        result = await self.extractor.extract(
            query=prompt,
            schema=GMPP_RISK_SCHEMA,
            samples=self.samples,
            early_stop=True,
        )

        return self._result_to_narrative(result)

    def _build_dca_prompt(self, project_data: Dict, dca_rating: str) -> str:
        """Build context-rich prompt for DCA narrative generation.

        Args:
            project_data: Project context dictionary
            dca_rating: DCA rating

        Returns:
            Formatted prompt
        """
        return f"""
Generate a Delivery Confidence Assessment narrative for UK Government GMPP quarterly reporting.

Project: {project_data['project_name']}
Department: {project_data.get('department', 'Unknown')}
DCA Rating: {dca_rating}

Financial Performance:
- Baseline cost: £{project_data.get('baseline_cost', 0):.1f}M
- Forecast cost: £{project_data.get('forecast_cost', 0):.1f}M
- Variance: {project_data.get('cost_variance_percent', 0):.1f}%

Schedule Performance:
- Baseline completion: {project_data.get('baseline_completion', 'Not set')}
- Forecast completion: {project_data.get('forecast_completion', 'Not set')}
- Variance: {project_data.get('schedule_variance_weeks', 0)} weeks

Benefits Performance:
- Total planned: £{project_data.get('total_benefits', 0):.1f}M
- Realised to date: £{project_data.get('realised_benefits', 0):.1f}M

Key Achievements This Quarter:
{project_data.get('achievements', 'None reported')}

Critical Issues:
{project_data.get('critical_issues', 'None reported')}

Risk Status:
{project_data.get('risk_summary', 'No summary available')}

Generate a professional narrative (150-200 words) explaining why this {dca_rating}
rating is justified. The narrative must be suitable for ministerial reporting and
Parliamentary scrutiny. Use objective, factual language. Mention key achievements,
describe critical issues and their impact, and outline mitigation actions being taken.
"""

    def _build_cost_prompt(self, project_data: Dict) -> str:
        """Build prompt for cost narrative.

        Args:
            project_data: Project context dictionary

        Returns:
            Formatted prompt
        """
        variance = project_data.get('cost_variance_percent', 0)
        direction = "over" if variance > 0 else "under"

        return f"""
Generate a cost performance narrative for UK Government GMPP quarterly reporting.

Project: {project_data['project_name']}
Financial Status:
- Baseline whole life cost: £{project_data.get('baseline_cost', 0):.1f}M
- Current forecast: £{project_data.get('forecast_cost', 0):.1f}M
- Variance: {abs(variance):.1f}% {direction} baseline

Explain the cost performance in 150-200 words, suitable for ministerial reporting.
If there is variance, explain the causes and management actions being taken.
Describe any budget reallocations, contingency usage, or cost control measures.
Use professional civil service style.
"""

    def _build_schedule_prompt(self, project_data: Dict) -> str:
        """Build prompt for schedule narrative.

        Args:
            project_data: Project context dictionary

        Returns:
            Formatted prompt
        """
        variance = project_data.get('schedule_variance_weeks', 0)
        status = "delayed" if variance > 0 else "ahead of schedule" if variance < 0 else "on track"

        return f"""
Generate a schedule performance narrative for UK Government GMPP quarterly reporting.

Project: {project_data['project_name']}
Schedule Status:
- Baseline completion: {project_data.get('baseline_completion', 'Not set')}
- Forecast completion: {project_data.get('forecast_completion', 'Not set')}
- Variance: {abs(variance)} weeks ({status})

Explain the schedule performance in 150-200 words, suitable for ministerial reporting.
Describe the critical path status, any schedule risks, and recovery actions being taken.
Use professional civil service style.
"""

    def _build_benefits_prompt(self, project_data: Dict) -> str:
        """Build prompt for benefits narrative.

        Args:
            project_data: Project context dictionary

        Returns:
            Formatted prompt
        """
        total = project_data.get('total_benefits', 0)
        realised = project_data.get('realised_benefits', 0)
        rate = (realised / total * 100) if total > 0 else 0

        return f"""
Generate a benefits realisation narrative for UK Government GMPP quarterly reporting.

Project: {project_data['project_name']}
Benefits Status:
- Total planned benefits: £{total:.1f}M
- Benefits realised to date: £{realised:.1f}M
- Realisation rate: {rate:.1f}%

Explain benefits realisation in 150-200 words, suitable for ministerial reporting.
Describe benefits achieved, tracking approach, and any variance from plan.
Use professional civil service style.
"""

    def _build_risk_prompt(self, project_data: Dict) -> str:
        """Build prompt for risk narrative.

        Args:
            project_data: Project context dictionary

        Returns:
            Formatted prompt
        """
        high_risks = project_data.get('high_risks_count', 0)

        return f"""
Generate a risk status narrative for UK Government GMPP quarterly reporting.

Project: {project_data['project_name']}
Risk Status:
- {project_data.get('risk_summary', 'No summary available')}

Critical Issues:
{project_data.get('critical_issues', 'None reported')}

Explain the risk status in 150-200 words, suitable for ministerial reporting.
Describe key risks (high priority), mitigation actions in progress, and any
risks closed or newly identified this quarter. Use professional civil service style.
"""

    def _result_to_narrative(self, result) -> DCANarrative:
        """Convert ConfidenceResult to DCANarrative.

        Args:
            result: ConfidenceResult from extractor

        Returns:
            DCA narrative model
        """
        # Map confidence to review level
        review_level = self._map_review_level(result.confidence, result.review_level.value)

        # Build review reason if needed
        review_reason = None
        if result.outliers:
            outlier_count = len(result.outliers)
            review_reason = f"{outlier_count} outlier(s) detected in narrative generation"
        elif result.confidence < 0.8:
            review_reason = f"Low confidence ({result.confidence:.2%}) - human review recommended"

        return DCANarrative(
            text=result.consensus.get("narrative_text", "[Generation failed]"),
            confidence=result.confidence,
            review_level=ReviewLevel(review_level),
            generated_at=datetime.utcnow(),
            samples_used=result.samples_used,
            review_reason=review_reason,
        )

    def _map_review_level(self, confidence: float, agent_review_level: str) -> str:
        """Map confidence score to review level.

        Args:
            confidence: Confidence score (0.0-1.0)
            agent_review_level: Review level from agent

        Returns:
            ReviewLevel enum value
        """
        # Use agent's recommendation if available
        if agent_review_level in ["NONE", "SPOT_CHECK", "DETAILED_REVIEW", "EXPERT_REQUIRED"]:
            return agent_review_level

        # Fallback to confidence-based mapping
        if confidence >= 0.8:
            return "NONE"
        elif confidence >= 0.6:
            return "SPOT_CHECK"
        elif confidence >= 0.4:
            return "DETAILED_REVIEW"
        else:
            return "EXPERT_REQUIRED"
