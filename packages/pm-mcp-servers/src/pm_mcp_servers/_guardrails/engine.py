"""Core engine for deterministic output-guardrail evaluation.

Implements the reference architecture from *Verified Autonomy* §8.3
(Newman et al., May 2026, DOI 10.5281/zenodo.19096229). The engine is
deliberately storage- and transport-agnostic: it takes a candidate
output dict and a list of :class:`Rule` objects, walks every rule, and
returns an :class:`EvaluationResult` carrying the verdict plus a full
audit trail of every rule's outcome.

The paper's two design properties this module satisfies:

* **Transparency.** Every rule's condition is a plain Python callable.
  No probability, no sampling, no model. A regulator can read the rule
  and re-derive the verdict by hand.
* **Auditability.** The result records every rule evaluated, not just
  the fired ones. A clean output and a violation-laden output produce
  trails of the same shape, so a downstream audit-chain consumer can
  detect tampering by recomputing the trail.

A rule's ``condition`` returns ``True`` when the rule is **violated**.
This matches the paper's convention and avoids the readability trap of
double negatives ("returns True when the output is acceptable").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

__all__ = [
    "Severity",
    "Verdict",
    "Rule",
    "RuleEvaluation",
    "EvaluationResult",
    "evaluate",
]


# ─────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────


class Severity(str, Enum):
    """What happens when a rule is violated.

    String-valued so it can be safely embedded in JSON audit trails.

    * ``BLOCK`` — violation rejects the entire output. Hard fail-safe.
    * ``WARN`` — violation flags the output but allows it to pass. The
      consumer sees a ``_guardrail_flags`` annotation.
    * ``UNKNOWN`` — the rule could not decide (typically because its
      condition raised an exception). The paper's convention is that
      UNKNOWN does **not** itself trigger rejection — it is recorded
      in the trail and treated as advisory. A policy that wants to
      treat condition errors as blocking should wrap the condition
      to return ``True`` on error.
    * ``INFO`` — purely informational. Never affects the verdict. Used
      for rules that record context for the audit trail without
      gating behaviour (e.g. "output mentions GDPR; reviewer may want
      to verify lawful basis").
    """

    BLOCK = "BLOCK"
    WARN = "WARN"
    UNKNOWN = "UNKNOWN"
    INFO = "INFO"


class Verdict(str, Enum):
    """Final outcome of running all rules.

    * ``APPROVED`` — no ``BLOCK`` or ``WARN`` rule fired.
    * ``FLAGGED`` — at least one ``WARN`` rule fired; no ``BLOCK`` fired.
    * ``REJECTED`` — at least one ``BLOCK`` rule fired.
    """

    APPROVED = "APPROVED"
    FLAGGED = "FLAGGED"
    REJECTED = "REJECTED"


# ─────────────────────────────────────────────────────────────────────────
# Rule
# ─────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Rule:
    """A single deterministic rule.

    Attributes:
        name: Short identifier, e.g. ``"max_amount"``. Appears in audit
            trail and in the rejection/flag annotation.
        description: Plain-English explanation suitable for showing to
            a human reviewer.
        severity: What to do when the rule is violated. See
            :class:`Severity`.
        condition: Callable taking the candidate output dict, returning
            ``True`` iff the rule is **violated**. Pure functions are
            strongly preferred; the engine catches exceptions and
            records the outcome as ``UNKNOWN``.
    """

    name: str
    description: str
    severity: Severity
    condition: Callable[[dict[str, Any]], bool]


# ─────────────────────────────────────────────────────────────────────────
# Evaluation outcome per-rule + aggregate
# ─────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RuleEvaluation:
    """Per-rule audit-trail entry.

    A complete trail of these is returned regardless of verdict — every
    rule's outcome is recorded, not just the ones that fired. This is
    what makes the trail useful as audit evidence: a consumer can
    re-derive the verdict from the trail without needing the rule
    callables themselves.

    Attributes:
        rule_name: The :class:`Rule.name`.
        severity: The rule's :class:`Severity`.
        violated: ``True`` iff the condition returned ``True``.
        message: Description string (typically the rule's description,
            or an error message if the condition raised).
        error: Exception class name if the condition raised; ``None``
            otherwise.
    """

    rule_name: str
    severity: Severity
    violated: bool
    message: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable representation."""
        return {
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "violated": self.violated,
            "message": self.message,
            "error": self.error,
        }


@dataclass(frozen=True)
class EvaluationResult:
    """Outcome of running a policy against an output dict.

    Attributes:
        verdict: The overall :class:`Verdict`.
        evaluations: Per-rule audit trail. One entry per rule in the
            policy, in policy order.
        triggered: The subset of ``evaluations`` where ``violated`` is
            ``True``. Convenience for consumers that just want the
            fired rules.
    """

    verdict: Verdict
    evaluations: list[RuleEvaluation] = field(default_factory=list)
    triggered: list[RuleEvaluation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable representation."""
        return {
            "verdict": self.verdict.value,
            "evaluations": [e.to_dict() for e in self.evaluations],
            "triggered": [e.to_dict() for e in self.triggered],
        }


# ─────────────────────────────────────────────────────────────────────────
# Evaluator
# ─────────────────────────────────────────────────────────────────────────


def evaluate(output: dict[str, Any], policy: list[Rule]) -> EvaluationResult:
    """Run every rule in ``policy`` against ``output`` and return the result.

    The verdict is determined by the highest-severity rule that fired:
    any ``BLOCK`` → ``REJECTED``; any ``WARN`` and no ``BLOCK`` →
    ``FLAGGED``; otherwise → ``APPROVED``. ``UNKNOWN`` and ``INFO``
    outcomes are recorded in the trail but do not change the verdict.

    A rule whose condition raises is treated as a **violation at the
    rule's nominal severity** — a fail-safe interpretation that prevents
    a crashing ``BLOCK`` rule from silently downgrading to ``APPROVED``
    (audit finding P3.F07). The error type is recorded in the trail
    entry so a reviewer can distinguish "rule fired" from "rule
    crashed; we treated the crash as a violation".

    Args:
        output: The candidate output dict (typically a tool's parsed
            JSON response).
        policy: Ordered list of :class:`Rule`. Evaluation is in order;
            all rules are evaluated even after one fires (so the trail
            is complete).

    Returns:
        :class:`EvaluationResult` with the verdict and full trail.
    """
    evaluations: list[RuleEvaluation] = []
    triggered: list[RuleEvaluation] = []
    any_block = False
    any_warn = False

    for rule in policy:
        try:
            violated = bool(rule.condition(output))
        except Exception as exc:
            # Condition raised — audit finding P3.F07 fail-safe.
            #
            # Previously this branch recorded UNKNOWN severity and
            # `violated=False`, which meant a crashing BLOCK rule
            # silently downgraded to APPROVED — exactly the case
            # the framework should fail-safe on.
            #
            # The fix preserves the rule's *nominal* severity and
            # records the entry as a violation. A crashing BLOCK
            # therefore rejects, a crashing WARN flags, and a
            # crashing INFO is still recorded but does not alter
            # the verdict (matches its design intent).
            entry = RuleEvaluation(
                rule_name=rule.name,
                severity=rule.severity,
                violated=True,
                message=(
                    f"{rule.description} (condition raised: {exc}; "
                    f"treated as violation under audit P3.F07 fail-safe)"
                ),
                error=type(exc).__name__,
            )
            evaluations.append(entry)
            triggered.append(entry)
            if rule.severity == Severity.BLOCK:
                any_block = True
            elif rule.severity == Severity.WARN:
                any_warn = True
            continue

        entry = RuleEvaluation(
            rule_name=rule.name,
            severity=rule.severity,
            violated=violated,
            message=rule.description,
        )
        evaluations.append(entry)

        if violated:
            triggered.append(entry)
            if rule.severity == Severity.BLOCK:
                any_block = True
            elif rule.severity == Severity.WARN:
                any_warn = True
            # UNKNOWN/INFO: recorded but do not affect verdict.

    if any_block:
        verdict = Verdict.REJECTED
    elif any_warn:
        verdict = Verdict.FLAGGED
    else:
        verdict = Verdict.APPROVED

    return EvaluationResult(
        verdict=verdict,
        evaluations=evaluations,
        triggered=triggered,
    )
