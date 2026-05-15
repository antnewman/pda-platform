"""Red-team harness implementation.

Pure Python, no external dependencies. Transparent pattern matching
(case-insensitive substring) over deliberate ML classifier opacity —
per paper §10.5, the reference implementation prioritises auditability
over detection power. Production deployments can swap the matcher for
a semantic classifier; the architecture (policy, suite, harness,
report) stays the same.
"""

from __future__ import annotations

import traceback
from collections import Counter
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable

__all__ = [
    "Finding",
    "FindingSeverity",
    "PolicyRule",
    "RedTeamHarness",
    "Report",
    "TestCase",
]


# ─────────────────────────────────────────────────────────────────────────
# Severity
# ─────────────────────────────────────────────────────────────────────────


class FindingSeverity(IntEnum):
    """Severity ratings for findings.

    Ordered numerically so the harness can pick the *highest* severity
    among multiple violations on the same test case (Python ``max``
    works directly on IntEnum). String representation via ``.name`` is
    JSON-friendly via the ``Report.to_dict`` shape.
    """

    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# ─────────────────────────────────────────────────────────────────────────
# Policy
# ─────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PolicyRule:
    """One thing the system under test must never do.

    Attributes:
        name: Unique identifier (e.g. ``no_credential_leakage``).
            Used by ``TestCase.target_rules`` to scope which rules
            apply to a given test case.
        description: Human-readable statement of what the rule checks.
            Shown in the report.
        forbidden_patterns: Tuple of substrings that must NOT appear in
            the system's output (case-insensitive). The rule fires when
            any pattern is found.
        severity: How serious a violation is. Higher = worse.
    """

    name: str
    description: str
    forbidden_patterns: tuple[str, ...]
    severity: FindingSeverity

    def matches(self, output: str) -> tuple[str, ...]:
        """Return the patterns from this rule that appear in ``output``
        (case-insensitive substring). Empty tuple means no violation."""
        haystack = output.lower()
        hits = tuple(p for p in self.forbidden_patterns if p.lower() in haystack)
        return hits


# ─────────────────────────────────────────────────────────────────────────
# Test case
# ─────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TestCase:
    """One adversarial test case.

    Attributes:
        test_case_id: Unique identifier for the test (e.g. ``tc-003``).
        prompt: The input passed to the system under test.
        category: Grouping label for the report (``baseline``,
            ``prompt_injection``, ``credential_extraction``, etc.).
            Useful for aggregated views.
        description: Human-readable account of what this case probes.
        target_rules: Optional tuple of rule names that this case is
            designed to provoke. If empty, ALL rules are evaluated
            against the output. The harness still evaluates non-target
            rules against the output as a sanity check; the
            ``target_rules`` field is documentation, not gating.
    """

    test_case_id: str
    prompt: str
    category: str = "general"
    description: str = ""
    target_rules: tuple[str, ...] = ()


# ─────────────────────────────────────────────────────────────────────────
# Finding
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class Finding:
    """The outcome of running one test case.

    Attributes:
        test_case_id: From the input :class:`TestCase`.
        category: From the input :class:`TestCase`.
        severity: The HIGHEST severity among violated rules. ``NONE``
            if no rule violated. ``CRITICAL`` if the system raised
            an exception (a crash counts as critical).
        passed: True iff no rule was violated and no exception raised.
        violated_rules: Names of rules whose patterns appeared in the
            output, in original list order. Empty if no violations.
        output: What the system under test returned, or ``None`` if
            it raised.
        error: Traceback of the exception if the system crashed, else
            ``None``.
    """

    test_case_id: str
    category: str
    severity: FindingSeverity
    passed: bool
    violated_rules: list[str] = field(default_factory=list)
    output: str | None = None
    error: str | None = None


# ─────────────────────────────────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class Report:
    """Aggregated outcome of a full run.

    Attributes:
        findings: One :class:`Finding` per test case, in order.
        pass_rate: Fraction of test cases that produced no violations
            and no crashes. In ``[0.0, 1.0]``.
        summary_by_severity: Count of findings at each non-NONE severity.
            ``{CRITICAL: 2, HIGH: 1}`` means two critical, one high.
            Severities with zero findings are omitted.
        summary_by_category: Per-category counts of findings (severity
            non-NONE).
        report_text: Plain-text report suitable for sending to a
            security team. Includes per-test line items plus the
            summary tables.
    """

    findings: list[Finding]
    pass_rate: float
    summary_by_severity: dict[FindingSeverity, int]
    summary_by_category: dict[str, int]
    report_text: str

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable representation. Severities flatten to names."""
        return {
            "findings": [
                {
                    "test_case_id": f.test_case_id,
                    "category": f.category,
                    "severity": f.severity.name,
                    "passed": f.passed,
                    "violated_rules": list(f.violated_rules),
                    "output": f.output,
                    "error": f.error,
                }
                for f in self.findings
            ],
            "pass_rate": self.pass_rate,
            "summary_by_severity": {
                sev.name: count for sev, count in self.summary_by_severity.items()
            },
            "summary_by_category": dict(self.summary_by_category),
            "report_text": self.report_text,
        }


# ─────────────────────────────────────────────────────────────────────────
# Harness
# ─────────────────────────────────────────────────────────────────────────


class RedTeamHarness:
    """Run a corpus of adversarial test cases against a system under test.

    Args:
        system_under_test: A callable taking ``str`` (the prompt) and
            returning ``str`` (the output). Could be a wrapper around
            an MCP tool, an LLM call, a stub, anything.
        policy: List of :class:`PolicyRule` describing the forbidden
            patterns.

    The harness does not mutate either argument; reusing it across
    suites is safe.
    """

    def __init__(
        self,
        system_under_test: Callable[[str], str],
        policy: list[PolicyRule],
    ):
        self.system_under_test = system_under_test
        self.policy = list(policy)

    # ── Public API ──────────────────────────────────────────────────────

    def run_one(self, test_case: TestCase) -> Finding:
        """Run a single test case through the system, evaluate against
        the full policy, return a Finding."""
        try:
            output = self.system_under_test(test_case.prompt)
        except Exception as exc:  # noqa: BLE001 — we capture all crash types
            # A crashing system is a finding, not a harness failure.
            tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            return Finding(
                test_case_id=test_case.test_case_id,
                category=test_case.category,
                severity=FindingSeverity.CRITICAL,
                passed=False,
                violated_rules=[],
                output=None,
                error=tb,
            )

        # Evaluate the output against every rule in the policy
        violated: list[PolicyRule] = []
        for rule in self.policy:
            if rule.matches(output):
                violated.append(rule)

        if not violated:
            return Finding(
                test_case_id=test_case.test_case_id,
                category=test_case.category,
                severity=FindingSeverity.NONE,
                passed=True,
                violated_rules=[],
                output=output,
                error=None,
            )

        highest = max(r.severity for r in violated)
        return Finding(
            test_case_id=test_case.test_case_id,
            category=test_case.category,
            severity=highest,
            passed=False,
            violated_rules=[r.name for r in violated],
            output=output,
            error=None,
        )

    def run_suite(self, tests: list[TestCase]) -> Report:
        """Run every test case, aggregate into a :class:`Report`."""
        findings = [self.run_one(tc) for tc in tests]

        passed_count = sum(1 for f in findings if f.passed)
        pass_rate = passed_count / len(findings) if findings else 0.0

        # Severity counts (non-NONE only)
        sev_counter: Counter[FindingSeverity] = Counter()
        for f in findings:
            if f.severity != FindingSeverity.NONE:
                sev_counter[f.severity] += 1

        # Category counts (non-passed only — categories with passes are noise
        # in the security view)
        cat_counter: Counter[str] = Counter()
        for f in findings:
            if not f.passed:
                cat_counter[f.category] += 1

        report_text = self._format_report(findings, pass_rate, sev_counter, cat_counter)

        return Report(
            findings=findings,
            pass_rate=pass_rate,
            summary_by_severity=dict(sev_counter),
            summary_by_category=dict(cat_counter),
            report_text=report_text,
        )

    # ── Internal ───────────────────────────────────────────────────────

    @staticmethod
    def _format_report(
        findings: list[Finding],
        pass_rate: float,
        sev_counter: Counter[FindingSeverity],
        cat_counter: Counter[str],
    ) -> str:
        """Compose the human-readable report text."""
        lines: list[str] = []
        lines.append("Red-team harness report")
        lines.append("=======================")
        lines.append("")

        # Per-test line items
        for f in findings:
            status = "PASS" if f.passed else f"FAIL [{f.severity.name}]"
            extra = ""
            if f.violated_rules:
                extra = f" — violated: {', '.join(f.violated_rules)}"
            elif f.error:
                extra = " — system crashed (see Finding.error)"
            lines.append(f"  {f.test_case_id:8s} {status:20s} {f.category}{extra}")

        lines.append("")
        lines.append(f"Pass rate: {pass_rate * 100:.1f}% "
                     f"({sum(1 for f in findings if f.passed)}/{len(findings)} tests passed)")

        if sev_counter:
            lines.append("")
            lines.append("Findings by severity:")
            for sev in sorted(sev_counter, reverse=True):  # CRITICAL first
                lines.append(f"  {sev.name:10s} {sev_counter[sev]}")

        if cat_counter:
            lines.append("")
            lines.append("Findings by category:")
            for cat in sorted(cat_counter):
                lines.append(f"  {cat:30s} {cat_counter[cat]}")

        return "\n".join(lines)
