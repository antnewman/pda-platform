"""Loader for the L7 RedTeam corpus YAML files.

Audit finding P4.F10. The L7 harness shipped without a corpus. This
module loads the checked-in starter corpus (``corpus/v1.yaml``) into
the :class:`PolicyRule` and :class:`TestCase` objects the harness
consumes. Future corpora can ship as ``v2.yaml`` etc. so the v1
contract stays stable for downstream consumers.

The loader resolves the embedded Python-style expressions
``"A" * N`` in the ``prompt`` field at load time so oversized-input
test cases can be expressed compactly without putting megabytes of
literal text in the YAML.
"""

from __future__ import annotations

from pathlib import Path

import yaml  # transitive via mcp / starlette

from pm_mcp_servers._redteam.harness import (
    FindingSeverity,
    PolicyRule,
    TestCase,
)

__all__ = [
    "DEFAULT_CORPUS_PATH",
    "load_corpus",
]


DEFAULT_CORPUS_PATH: Path = Path(__file__).parent / "corpus" / "v1.yaml"


def load_corpus(
    path: Path | None = None,
) -> tuple[list[PolicyRule], list[TestCase]]:
    """Parse a corpus YAML and return ``(policy, tests)``.

    Args:
        path: Optional override; defaults to :data:`DEFAULT_CORPUS_PATH`.

    Returns:
        Tuple ``(policy, tests)`` ready to hand to
        :class:`pm_mcp_servers._redteam.RedTeamHarness`.
    """
    target = path or DEFAULT_CORPUS_PATH
    raw = yaml.safe_load(target.read_text(encoding="utf-8"))

    policy = [
        PolicyRule(
            name=p["name"],
            description=p["description"],
            forbidden_patterns=tuple(p["forbidden_patterns"]),
            severity=FindingSeverity[p["severity"]],
        )
        for p in raw.get("policy", [])
    ]

    tests = [
        TestCase(
            test_case_id=t["test_case_id"],
            prompt=_resolve_prompt(t),
            category=t.get("category", "uncategorised"),
            target_rules=tuple(t.get("target_rules", ()) or ()),
        )
        for t in raw.get("tests", [])
    ]

    return policy, tests


def _resolve_prompt(test_dict: dict) -> str:
    """Return the resolved prompt string for a test-case dict.

    Supports two encodings:

    * ``prompt: "..."`` — a literal string, used directly.
    * ``prompt_repeat: {char: "A", count: 60000}`` — a compact form
      for oversized-input cases. The loader expands it at parse time
      so the YAML stays readable.

    Exactly one of the two keys must be present.
    """
    if "prompt" in test_dict:
        return str(test_dict["prompt"])
    if "prompt_repeat" in test_dict:
        spec = test_dict["prompt_repeat"]
        return str(spec["char"]) * int(spec["count"])
    raise ValueError(
        f"Test case {test_dict.get('test_case_id')!r} must declare "
        "either 'prompt' or 'prompt_repeat'."
    )
