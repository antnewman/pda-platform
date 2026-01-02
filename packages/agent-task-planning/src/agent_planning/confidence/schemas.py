"""PM-specific extraction schemas for confidence extraction."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class SchemaType(Enum):
    """Built-in schema types for PM extraction."""
    RISK = "risk"
    ESTIMATE = "estimate"
    RECOMMENDATION = "recommendation"
    MILESTONE = "milestone"
    BARRIER = "barrier"
    OUTCOME_MEASURE = "outcome_measure"
    STAKEHOLDER_IMPACT = "stakeholder_impact"
    CUSTOM = "custom"


@dataclass
class RiskItem:
    """A single risk item extracted from analysis."""
    description: str
    category: str                           # Technical, Commercial, Schedule, Resource, External
    probability: int                        # 1-5 scale
    impact: int                             # 1-5 scale
    mitigation: str
    owner: Optional[str] = None
    status: str = "Open"                    # Open, Mitigating, Closed, Accepted
    id: Optional[str] = None                # Auto-generated if not provided

    @property
    def score(self) -> int:
        """Risk score (probability x impact)."""
        return self.probability * self.impact


@dataclass
class EstimateItem:
    """An estimate with uncertainty."""
    description: str
    value: float                            # Point estimate
    unit: str                               # days, hours, GBP, etc.
    range_low: Optional[float] = None       # Lower bound
    range_high: Optional[float] = None      # Upper bound
    optimistic: Optional[float] = None      # For three-point estimates
    pessimistic: Optional[float] = None     # For three-point estimates
    assumptions: list[str] = field(default_factory=list)
    confidence_notes: Optional[str] = None


@dataclass
class RecommendationItem:
    """A recommended action."""
    action: str
    rationale: str
    priority: str                           # High, Medium, Low
    owner: Optional[str] = None             # Suggested owner
    timeframe: Optional[str] = None         # When to complete
    dependencies: list[str] = field(default_factory=list)


@dataclass
class MilestoneItem:
    """A project milestone."""
    name: str
    description: str
    target_date: Optional[str] = None       # ISO format or descriptive
    dependencies: list[str] = field(default_factory=list)
    deliverables: list[str] = field(default_factory=list)


@dataclass
class BarrierItem:
    """A barrier or blocker (aligned with PDATF White Paper structure)."""
    description: str
    barrier_theme: str                      # Leadership, Data, Digital, Skills, Procurement, Risk
    severity: str                           # High, Medium, Low
    affected_personas: list[str]            # Project Lead, Programme Lead, Business Lead
    recommended_actions: list[str]
    success_metrics: list[str] = field(default_factory=list)


@dataclass
class OutcomeMeasureItem:
    """An outcome measure or KPI."""
    measure: str
    description: str
    target: Optional[str] = None
    baseline: Optional[str] = None
    measurement_method: Optional[str] = None
    frequency: Optional[str] = None         # How often measured


@dataclass
class StakeholderImpactItem:
    """Impact on a stakeholder group."""
    stakeholder: str
    impact_description: str
    sentiment: str                          # Positive, Negative, Neutral, Mixed
    actions_required: list[str] = field(default_factory=list)
    communication_needs: Optional[str] = None


# Schema definitions for extraction prompts
SCHEMA_DEFINITIONS = {
    SchemaType.RISK: {
        "name": "Risk Analysis",
        "output_class": RiskItem,
        "extraction_prompt": """Extract risk items with these fields:
- description: Clear description of the risk
- category: One of Technical, Commercial, Schedule, Resource, External
- probability: 1-5 scale (1=Very Low, 5=Very High)
- impact: 1-5 scale (1=Very Low, 5=Very High)
- mitigation: Recommended mitigation action
- owner: Who should own this risk (if identifiable)
- status: Current status (default to Open)

Return as a JSON array of risk objects.""",
        "aggregation_fields": {
            "numeric": ["probability", "impact"],
            "categorical": ["category", "status"],
            "text": ["description", "mitigation", "owner"]
        }
    },

    SchemaType.ESTIMATE: {
        "name": "Effort/Cost Estimate",
        "output_class": EstimateItem,
        "extraction_prompt": """Extract estimates with these fields:
- description: What is being estimated
- value: Point estimate (numeric)
- unit: Unit of measurement (days, hours, GBP, USD, etc.)
- range_low: Lower bound of reasonable range
- range_high: Upper bound of reasonable range
- assumptions: List of key assumptions
- confidence_notes: Any notes about estimate confidence

Return as a JSON array of estimate objects.""",
        "aggregation_fields": {
            "numeric": ["value", "range_low", "range_high"],
            "text": ["description", "unit", "confidence_notes"],
            "list": ["assumptions"]
        }
    },

    SchemaType.RECOMMENDATION: {
        "name": "Recommendations",
        "output_class": RecommendationItem,
        "extraction_prompt": """Extract recommendations with these fields:
- action: The recommended action (clear, actionable)
- rationale: Why this is recommended
- priority: High, Medium, or Low
- owner: Suggested owner or responsible party
- timeframe: When this should be completed
- dependencies: What this depends on

Return as a JSON array of recommendation objects.""",
        "aggregation_fields": {
            "categorical": ["priority"],
            "text": ["action", "rationale", "owner", "timeframe"],
            "list": ["dependencies"]
        }
    },

    SchemaType.MILESTONE: {
        "name": "Milestones",
        "output_class": MilestoneItem,
        "extraction_prompt": """Extract milestones with these fields:
- name: Short milestone name
- description: What this milestone represents
- target_date: Target completion date
- dependencies: What must complete before this
- deliverables: What is delivered at this milestone

Return as a JSON array of milestone objects.""",
        "aggregation_fields": {
            "text": ["name", "description", "target_date"],
            "list": ["dependencies", "deliverables"]
        }
    },

    SchemaType.BARRIER: {
        "name": "Barriers and Blockers",
        "output_class": BarrierItem,
        "extraction_prompt": """Extract barriers/blockers with these fields:
- description: Clear description of the barrier
- barrier_theme: One of Leadership, Data, Digital, Skills, Procurement, Risk
- severity: High, Medium, or Low
- affected_personas: Who is affected (Project Lead, Programme Lead, Business Lead)
- recommended_actions: Actions to overcome this barrier
- success_metrics: How to measure if barrier is overcome

Return as a JSON array of barrier objects.""",
        "aggregation_fields": {
            "categorical": ["barrier_theme", "severity"],
            "text": ["description"],
            "list": ["affected_personas", "recommended_actions", "success_metrics"]
        }
    },

    SchemaType.OUTCOME_MEASURE: {
        "name": "Outcome Measures",
        "output_class": OutcomeMeasureItem,
        "extraction_prompt": """Extract outcome measures/KPIs with these fields:
- measure: Name of the measure
- description: What it measures and why it matters
- target: Target value or state
- baseline: Current baseline if known
- measurement_method: How it will be measured
- frequency: How often it will be measured

Return as a JSON array of outcome measure objects.""",
        "aggregation_fields": {
            "text": ["measure", "description", "target", "baseline", "measurement_method", "frequency"]
        }
    },

    SchemaType.STAKEHOLDER_IMPACT: {
        "name": "Stakeholder Impacts",
        "output_class": StakeholderImpactItem,
        "extraction_prompt": """Extract stakeholder impacts with these fields:
- stakeholder: The stakeholder group or individual
- impact_description: How they are impacted
- sentiment: Positive, Negative, Neutral, or Mixed
- actions_required: Actions needed to address this stakeholder
- communication_needs: What communication is needed

Return as a JSON array of stakeholder impact objects.""",
        "aggregation_fields": {
            "categorical": ["sentiment"],
            "text": ["stakeholder", "impact_description", "communication_needs"],
            "list": ["actions_required"]
        }
    }
}


def get_schema_definition(schema_type: SchemaType) -> dict:
    """Get the schema definition for a given type."""
    if schema_type == SchemaType.CUSTOM:
        raise ValueError("Custom schemas must provide their own definition")
    return SCHEMA_DEFINITIONS[schema_type]


@dataclass
class CustomSchema:
    """Define a custom extraction schema."""
    name: str
    extraction_prompt: str
    aggregation_fields: dict[str, list[str]]
    output_class: Optional[type] = None  # Optional dataclass for typed output
