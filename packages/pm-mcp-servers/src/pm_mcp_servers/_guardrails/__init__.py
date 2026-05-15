"""Deterministic output-guardrail engine for MCP tool responses.

Verified Autonomy Layer 5 (Deterministic Guardrails), §8.3 reference
implementation. Implements the "model proposes, rule decides" pattern:
an AI-authored tool produces output, which is then run through a list
of deterministic rules before reaching the consumer. The rules are
transparent, auditable, and unambiguous — there is no probability or
sampling involved.

Three primary types:

* :class:`Severity` — ``BLOCK`` (rule violation rejects output entirely),
  ``WARN`` (rule violation flags but allows), ``UNKNOWN`` (rule could not
  decide; rare — typically used when the condition errored), ``INFO``
  (informational only; never affects verdict).
* :class:`Verdict` — ``APPROVED`` (no BLOCK/WARN fired), ``FLAGGED``
  (one or more WARN fired but no BLOCK), ``REJECTED`` (one or more BLOCK
  fired).
* :class:`Rule` — name + description + severity + boolean condition.
  The condition takes the candidate output dict and returns ``True``
  when the rule is **violated** (matches the paper's convention).

The evaluation engine (:func:`evaluate`) walks every rule and returns
an :class:`EvaluationResult` carrying the verdict plus an audit trail
of every rule evaluation. The trail is independent of severity — every
rule's outcome is recorded so a reviewer can see which rules passed,
which fired, and (with an :class:`AuditChain` attached) verify the
trail's integrity later.

Helper rule builders cover the common cases:

* :func:`build_range_rule` — numeric value must be within bounds.
* :func:`build_required_field_rule` — field must exist and be non-null.
* :func:`build_allowed_values_rule` — value must be in a fixed set.
* :func:`build_forbidden_phrase_rule` — text must not contain certain
  phrases (case-insensitive). The most-used builder for AI-authored
  prose; rejects outputs that overclaim certainty ("100% certain",
  "guaranteed"), invent unsupported facts, or otherwise drift outside
  the policy.

The decorator :func:`wrap_tool_output` plugs the engine in front of an
MCP tool handler. APPROVED output passes through unchanged; FLAGGED
output gets a ``_guardrail_flags`` annotation; REJECTED output is
replaced with a structured error JSON. All three cases write an entry
to an optional :class:`AuditChain` so the verdict is tamper-evidently
recorded.
"""

from pm_mcp_servers._guardrails.builders import (
    build_allowed_values_rule,
    build_forbidden_phrase_rule,
    build_range_rule,
    build_required_field_rule,
)
from pm_mcp_servers._guardrails.engine import (
    EvaluationResult,
    Rule,
    RuleEvaluation,
    Severity,
    Verdict,
    evaluate,
)
from pm_mcp_servers._guardrails.wrapper import wrap_tool_output

__all__ = [
    # Engine
    "Rule",
    "RuleEvaluation",
    "EvaluationResult",
    "Severity",
    "Verdict",
    "evaluate",
    # Builders
    "build_range_rule",
    "build_required_field_rule",
    "build_allowed_values_rule",
    "build_forbidden_phrase_rule",
    # Wrapper
    "wrap_tool_output",
]
