"""Decorator that plugs the guardrail engine in front of an MCP tool.

Most MCP tools in the platform return ``list[TextContent]`` where each
``TextContent.text`` is a JSON-serialised dict. :func:`wrap_tool_output`
takes such a handler and a policy, runs the handler, parses each
JSON payload, evaluates the policy, and:

* **APPROVED** — returns the original handler output untouched.
* **FLAGGED** — re-serialises each parsed dict with an added
  ``_guardrail_flags`` field carrying the verdict and triggered-rule
  details. Original fields are preserved unchanged.
* **REJECTED** — returns a single ``TextContent`` carrying a structured
  rejection JSON. The original output is **not** returned (this is the
  hard fail-safe).

When an :class:`AuditChain` instance is passed, every evaluation is
recorded via :meth:`AuditChain.record` so the trail is tamper-evident
end-to-end. Without a chain, the engine still produces full evaluations
but they are returned only inside the response annotation (FLAGGED) or
the rejection JSON (REJECTED).

The wrapper preserves the handler's async-ness and signature: the
returned callable awaits the original handler with the same arguments.
Non-JSON ``TextContent`` items are passed through unchanged (the engine
has nothing to evaluate against an opaque string blob).
"""

from __future__ import annotations

import functools
import json
from typing import Any, Awaitable, Callable, TYPE_CHECKING

from mcp.types import TextContent

from pm_mcp_servers._guardrails.engine import (
    EvaluationResult,
    Rule,
    Verdict,
    evaluate,
)

if TYPE_CHECKING:
    from pm_data_tools.audit import AuditChain

__all__ = ["wrap_tool_output"]


Handler = Callable[..., Awaitable[list[TextContent]]]


def wrap_tool_output(
    handler: Handler,
    policy: list[Rule],
    *,
    action: str | None = None,
    audit_chain: "AuditChain | None" = None,
) -> Handler:
    """Wrap an MCP tool handler with deterministic output guardrails.

    Args:
        handler: The async tool handler. Must return
            ``list[TextContent]``. Each ``TextContent`` whose ``.text``
            parses as JSON-object is evaluated against the policy.
        policy: Ordered list of :class:`Rule`. Empty policy is allowed
            and results in every output being APPROVED (the engine runs
            but has nothing to fire on).
        action: Optional action label used as the ``action`` field on
            audit-chain entries. Defaults to ``"GUARDRAIL_EVAL"``.
        audit_chain: Optional :class:`AuditChain` instance. When set,
            every evaluation is appended to the chain so the verdict
            and trail are tamper-evidently recorded.

    Returns:
        A new async callable that delegates to ``handler`` and applies
        the guardrails to its output.
    """
    chain_action = action or "GUARDRAIL_EVAL"

    @functools.wraps(handler)
    async def wrapped(*args: Any, **kwargs: Any) -> list[TextContent]:
        original = await handler(*args, **kwargs)
        if not original:
            return original

        rebuilt: list[TextContent] = []
        for item in original:
            # Pass through anything that isn't a JSON-object response.
            parsed = _try_parse_json_object(item)
            if parsed is None:
                rebuilt.append(item)
                continue

            result = evaluate(parsed, policy)
            _record_to_audit_chain(audit_chain, chain_action, parsed, result)

            if result.verdict == Verdict.APPROVED:
                rebuilt.append(item)
                continue

            if result.verdict == Verdict.FLAGGED:
                annotated = dict(parsed)
                annotated["_guardrail_flags"] = result.to_dict()
                rebuilt.append(
                    TextContent(type="text", text=json.dumps(annotated))
                )
                continue

            # REJECTED — hard fail-safe. Replace with structured error
            # JSON; do not include the original prose.
            rebuilt.append(
                TextContent(
                    type="text",
                    text=json.dumps(_rejection_payload(result)),
                )
            )

        return rebuilt

    return wrapped


# ─────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────


def _try_parse_json_object(item: TextContent) -> dict[str, Any] | None:
    """Return the parsed dict if ``item.text`` is a JSON object;
    otherwise ``None``. Lists, scalars, and non-JSON strings are
    treated as not-our-business and passed through."""
    if not isinstance(item, TextContent):
        return None
    text = getattr(item, "text", None)
    if not isinstance(text, str):
        return None
    try:
        loaded = json.loads(text)
    except (ValueError, TypeError):
        return None
    if isinstance(loaded, dict):
        return loaded
    return None


# Audit finding P3.F11. The rejection envelope is a public contract
# between the platform and any consumer that parses tool errors. Tag
# every payload with a schema_version so future structural changes can
# advertise compatibility breaks; consumers can branch on the value.
REJECTION_ENVELOPE_SCHEMA_VERSION = 1


def _rejection_payload(result: EvaluationResult) -> dict[str, Any]:
    """Build the structured-error response that replaces a REJECTED output."""
    return {
        "error": "guardrail_rejected",
        "schema_version": REJECTION_ENVELOPE_SCHEMA_VERSION,
        "verdict": result.verdict.value,
        "message": (
            "Output rejected by deterministic guardrail policy. "
            "Inspect `triggered` for the failing rules."
        ),
        "triggered": [e.to_dict() for e in result.triggered],
        "evaluations": [e.to_dict() for e in result.evaluations],
    }


def _record_to_audit_chain(
    chain: "AuditChain | None",
    action: str,
    output: dict[str, Any],
    result: EvaluationResult,
) -> None:
    """Append a guardrail evaluation to an audit chain, if provided.

    The audit entry's input is the candidate output dict; the output is
    the full evaluation result (verdict + trail). Decision is the
    verdict string. Failures here are non-fatal: the wrapper logs and
    continues so a misconfigured chain does not break the tool.
    """
    if chain is None:
        return
    try:
        chain.record(
            input_data=output,
            output_data=result.to_dict(),
            decision=result.verdict.value,
            action=action,
            metadata={"triggered_count": len(result.triggered)},
        )
    except Exception:
        # Audit failures must not break tool output. They will be
        # caught by chain.verify() later if the chain is malformed.
        pass
