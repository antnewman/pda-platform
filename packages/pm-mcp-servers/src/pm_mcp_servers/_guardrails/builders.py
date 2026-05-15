"""Helper rule builders for the most common guardrail conditions.

Hand-writing a :class:`pm_mcp_servers._guardrails.Rule` is straightforward
but the four cases below cover the vast majority of policies, and the
builders keep policy definitions short and self-documenting::

    policy = [
        build_required_field_rule("verdict"),
        build_allowed_values_rule("verdict", {"GREEN", "AMBER", "RED"}),
        build_range_rule("confidence", lower=0.0, upper=1.0),
        build_forbidden_phrase_rule(
            "narrative",
            phrases=["100% certain", "guaranteed"],
            severity=Severity.BLOCK,
        ),
    ]

Each builder accepts a ``severity`` keyword (default ``BLOCK``) and
returns a :class:`Rule` whose ``condition`` is the corresponding check.

A condition returns ``True`` iff the rule is **violated** — matching
the engine's convention.
"""

from __future__ import annotations

from typing import Any, Iterable

from pm_mcp_servers._guardrails.engine import Rule, Severity

__all__ = [
    "build_range_rule",
    "build_required_field_rule",
    "build_allowed_values_rule",
    "build_forbidden_phrase_rule",
]


# ─────────────────────────────────────────────────────────────────────────
# Internal helper for nested field lookup
# ─────────────────────────────────────────────────────────────────────────


_MISSING = object()


def _resolve(output: dict[str, Any], path: str) -> Any:
    """Resolve a dotted path against ``output``. Return ``_MISSING`` if
    any segment is absent. Lists are not traversed (use the dict shape
    the tool actually returns)."""
    cursor: Any = output
    for segment in path.split("."):
        if isinstance(cursor, dict) and segment in cursor:
            cursor = cursor[segment]
        else:
            return _MISSING
    return cursor


# ─────────────────────────────────────────────────────────────────────────
# Builders
# ─────────────────────────────────────────────────────────────────────────


def build_range_rule(
    field: str,
    *,
    lower: float | None = None,
    upper: float | None = None,
    severity: Severity = Severity.BLOCK,
    name: str | None = None,
    description: str | None = None,
) -> Rule:
    """Build a rule that fires when a numeric field is outside ``[lower, upper]``.

    Either bound may be ``None`` to indicate one-sided. A missing or
    non-numeric value also fires (the policy should add a
    ``build_required_field_rule`` separately if the field is mandatory,
    but a range rule that ignored missing values would be a footgun).

    Args:
        field: Dotted path to the field, e.g. ``"confidence"`` or
            ``"summary.score"``.
        lower: Inclusive lower bound. ``None`` for no lower bound.
        upper: Inclusive upper bound. ``None`` for no upper bound.
        severity: Severity on violation (default ``BLOCK``).
        name: Override the auto-generated rule name.
        description: Override the auto-generated description.
    """
    if lower is None and upper is None:
        raise ValueError("build_range_rule requires at least one of lower/upper")

    bounds = _format_bounds(lower, upper)
    final_name = name or f"range:{field}{bounds}"
    final_desc = description or f"Field '{field}' must be within {bounds}."

    def condition(output: dict[str, Any]) -> bool:
        value = _resolve(output, field)
        if value is _MISSING:
            return True
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return True
        if lower is not None and numeric < lower:
            return True
        if upper is not None and numeric > upper:
            return True
        return False

    return Rule(
        name=final_name,
        description=final_desc,
        severity=severity,
        condition=condition,
    )


def build_required_field_rule(
    field: str,
    *,
    severity: Severity = Severity.BLOCK,
    name: str | None = None,
    description: str | None = None,
) -> Rule:
    """Build a rule that fires when a field is missing or ``None``.

    Empty strings and empty containers are **not** treated as missing —
    use a follow-up rule if those should also fire.
    """
    final_name = name or f"required:{field}"
    final_desc = description or f"Field '{field}' is required and must be non-null."

    def condition(output: dict[str, Any]) -> bool:
        value = _resolve(output, field)
        return value is _MISSING or value is None

    return Rule(
        name=final_name,
        description=final_desc,
        severity=severity,
        condition=condition,
    )


def build_allowed_values_rule(
    field: str,
    allowed: Iterable[Any],
    *,
    severity: Severity = Severity.BLOCK,
    name: str | None = None,
    description: str | None = None,
) -> Rule:
    """Build a rule that fires when a field's value is not in ``allowed``.

    A missing field also fires.
    """
    allowed_set = frozenset(allowed)
    if not allowed_set:
        raise ValueError("build_allowed_values_rule requires a non-empty allowed set")

    allowed_repr = ", ".join(repr(v) for v in sorted(allowed_set, key=str))
    final_name = name or f"allowed:{field}"
    final_desc = (
        description
        or f"Field '{field}' must be one of: {allowed_repr}."
    )

    def condition(output: dict[str, Any]) -> bool:
        value = _resolve(output, field)
        if value is _MISSING:
            return True
        return value not in allowed_set

    return Rule(
        name=final_name,
        description=final_desc,
        severity=severity,
        condition=condition,
    )


def build_forbidden_phrase_rule(
    field: str,
    phrases: Iterable[str],
    *,
    severity: Severity = Severity.BLOCK,
    case_sensitive: bool = False,
    name: str | None = None,
    description: str | None = None,
) -> Rule:
    """Build a rule that fires when a text field contains any forbidden phrase.

    The dominant builder for AI-authored prose. Use this to reject
    outputs that overclaim certainty ("100% certain", "guaranteed"),
    leak template scaffolding ("INSERT NARRATIVE HERE"), or otherwise
    breach the policy.

    The match is case-insensitive by default; pass ``case_sensitive=True``
    to require an exact substring match.

    Args:
        field: Dotted path to the text field.
        phrases: Forbidden substrings.
        severity: Severity on violation (default ``BLOCK``).
        case_sensitive: When ``False`` (default), the field text and the
            phrases are both lowercased before substring testing.
        name: Override the auto-generated rule name.
        description: Override the auto-generated description.
    """
    phrase_list = [p for p in phrases if p]
    if not phrase_list:
        raise ValueError("build_forbidden_phrase_rule requires at least one phrase")

    needles = (
        tuple(phrase_list)
        if case_sensitive
        else tuple(p.lower() for p in phrase_list)
    )

    quoted = ", ".join(repr(p) for p in phrase_list)
    final_name = name or f"forbidden_phrase:{field}"
    final_desc = (
        description
        or f"Field '{field}' must not contain: {quoted}."
    )

    def condition(output: dict[str, Any]) -> bool:
        value = _resolve(output, field)
        if value is _MISSING or value is None:
            # Missing text fields cannot contain forbidden phrases.
            # Compose with build_required_field_rule if needed.
            return False
        text = str(value)
        if not case_sensitive:
            text = text.lower()
        return any(needle in text for needle in needles)

    return Rule(
        name=final_name,
        description=final_desc,
        severity=severity,
        condition=condition,
    )


# ─────────────────────────────────────────────────────────────────────────
# Internal: bound formatting for auto-generated names
# ─────────────────────────────────────────────────────────────────────────


def _format_bounds(lower: float | None, upper: float | None) -> str:
    if lower is not None and upper is not None:
        return f"[{lower}, {upper}]"
    if lower is not None:
        return f">= {lower}"
    return f"<= {upper}"
