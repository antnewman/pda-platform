"""Four-tier escalation router with OR-condition fail-safe.

Verified Autonomy Layer 2 (Outlier Detection as Hard Escalation), §5.3
reference implementation. Routes AI tool outputs to human review on
either of two independent triggers: statistical outliers in repeated
model samples, OR low confidence. Each can fire alone; the system
fails safe by escalating whenever either fires.

The four tiers (in descending order of urgency):

  EXPERT_REQUIRED   Any outlier detected OR confidence < 0.4
                    Route to a domain expert. Output is not acted upon
                    until reviewed.
  DETAILED_REVIEW   No outliers AND 0.4 <= confidence < 0.6
                    A human reads every output.
  SPOT_CHECK        No outliers AND 0.6 <= confidence < 0.8
                    Periodic sampling — a proportion reviewed.
  NONE              No outliers AND confidence >= 0.8
                    Auto-process.

Usage::

    from agent_planning.escalation import route, EscalationLevel

    decision = route(
        values=[10.0, 10.2, 10.1, 10.0, 10.1, 100.0],
        labels=["agent_A", "agent_B", "agent_C", "agent_D", "agent_E", "agent_G"],
        confidence=0.95,
    )

    decision.level          # EscalationLevel.EXPERT_REQUIRED
    decision.reason         # plain-English why
    decision.consensus      # 10.1 — the median, agreed reference
    decision.outliers       # list of OutlierReport with reason strings
"""

from agent_planning.escalation.router import (
    EscalationLevel,
    RoutingDecision,
    route,
)

__all__ = [
    "EscalationLevel",
    "RoutingDecision",
    "route",
]
