"""Input validation seam at the MCP dispatch boundary.

Built in response to audit findings P4.F01 (prompt-injection via
``project_id``), P4.F03 (no input-size limits), and partially P4.F07
(MCP ``inputSchema`` declared but not enforced).

The platform's single dispatch seam is
``pm_mcp_servers.pda_platform.server.call_tool``. Every MCP tool call
funnels through it. Adding validation there closes the security gap
across all 126 tools without per-tool changes.

Two public helpers:

* :func:`sanitise_arguments` — mutate-and-return a new arguments dict
  with potentially-dangerous fields rewritten or rejected.
  Currently:
    - ``project_id``: must match ``^[A-Za-z0-9._\\-]{1,256}$``; rejected
      with a structured ``ValidationError`` otherwise.
    - any free-text field is capped at :data:`MAX_STRING_LENGTH`
      characters.
* :func:`validate_payload_size` — reject when the JSON-serialised
  arguments exceed :data:`MAX_PAYLOAD_BYTES`.

Both raise :class:`ValidationError`, which the dispatcher catches and
renders to the operator as a structured rejection envelope rather than
letting the bad input flow further.
"""

from __future__ import annotations

import json
import re
from typing import Any

__all__ = [
    "ValidationError",
    "MAX_STRING_LENGTH",
    "MAX_PAYLOAD_BYTES",
    "PROJECT_ID_PATTERN",
    "sanitise_arguments",
    "validate_payload_size",
]


# Maximum length for any single string field flowing into a tool.
# Prose fields (narrative_text, lesson recommendations) get this cap;
# identifier fields get a smaller cap via dedicated validators.
MAX_STRING_LENGTH = 50_000

# Maximum total bytes for the JSON-serialised arguments payload.
# 1 MiB is comfortably above any realistic legitimate use; well below
# the platform's effective memory ceiling.
MAX_PAYLOAD_BYTES = 1_000_000

# Identifier shape: alphanumeric, dot, hyphen, underscore, length-bounded.
# Designed for `project_id`, but reusable for any opaque identifier
# field. Excludes whitespace, newlines, prompt-injection escape sequences.
PROJECT_ID_PATTERN = re.compile(r"^[A-Za-z0-9._\-]{1,256}$")

# Identifier-shaped fields: any of these in `arguments` must match
# :data:`PROJECT_ID_PATTERN`.
_IDENTIFIER_FIELDS = frozenset(
    {
        "project_id",
        "run_id",
        "review_id",
        "report_id",
        "assumption_id",
        "risk_id",
        "lesson_id",
        "change_id",
        "benefit_id",
    }
)


class ValidationError(Exception):
    """Raised when arguments fail dispatch-layer validation.

    The dispatcher catches this and returns a structured rejection
    envelope to the consumer (status 400-equivalent). Carries a
    ``field`` attribute pinpointing the bad input.
    """

    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


def sanitise_arguments(arguments: Any) -> dict[str, Any]:
    """Return a validated arguments dict or raise ``ValidationError``.

    Performs per-field validation:
      * identifier fields must match :data:`PROJECT_ID_PATTERN`;
      * string fields are capped at :data:`MAX_STRING_LENGTH`;
      * dicts and lists are recursed for nested string fields.

    Returns the input unchanged if every check passes. The intent is
    cheap defence-in-depth, not exhaustive normalisation — invalid
    inputs are rejected loudly rather than silently fixed up.
    """
    if not isinstance(arguments, dict):
        # MCP guarantees a dict; defend against schema-violating clients.
        return {}

    for key, value in arguments.items():
        if key in _IDENTIFIER_FIELDS and isinstance(value, str):
            if not PROJECT_ID_PATTERN.fullmatch(value):
                raise ValidationError(
                    f"Field '{key}' must match {PROJECT_ID_PATTERN.pattern} "
                    "(alphanumeric, dot, hyphen, underscore; max 256 chars).",
                    field=key,
                )
        if isinstance(value, str) and len(value) > MAX_STRING_LENGTH:
            raise ValidationError(
                f"Field '{key}' exceeds {MAX_STRING_LENGTH}-character limit "
                f"({len(value)} chars).",
                field=key,
            )
        # Light recursion into nested structures; we do not deep-validate
        # arbitrary JSON because MCP schemas are heterogenous. Catching
        # any string overrun anywhere is a stronger guarantee than
        # whitelisting which fields to check.
        if isinstance(value, dict):
            sanitise_arguments(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    sanitise_arguments(item)
                elif isinstance(item, str) and len(item) > MAX_STRING_LENGTH:
                    raise ValidationError(
                        f"Field '{key}' contains a string entry exceeding "
                        f"{MAX_STRING_LENGTH} chars.",
                        field=key,
                    )

    return arguments


def validate_payload_size(arguments: Any) -> None:
    """Raise ``ValidationError`` if the serialised payload is too large.

    Cheap upper-bound check at the dispatch boundary; runs before
    per-field validation. Prevents a 100 MB JSON blob from being
    iterated character-by-character downstream.
    """
    try:
        serialised = json.dumps(arguments, default=str)
    except (TypeError, ValueError):
        # Non-serialisable payload — let downstream handle the type
        # error; size check does not apply.
        return
    if len(serialised) > MAX_PAYLOAD_BYTES:
        raise ValidationError(
            f"Arguments payload exceeds {MAX_PAYLOAD_BYTES} bytes "
            f"({len(serialised)} bytes).",
        )
