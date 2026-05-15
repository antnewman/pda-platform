"""Formally-verified monotonicity of confidence→RAG mappings.

Implements the reference verification kernel from *Verified Autonomy*
§12.3 (Newman et al., May 2026, DOI 10.5281/zenodo.19096229) using the
Z3 SMT solver.

The mapping under verification is a step function:

  value(x) = labels[0]   if x < thresholds[0]
           = labels[1]   if thresholds[0] <= x < thresholds[1]
           = labels[i]   if thresholds[i-1] <= x < thresholds[i]
           = labels[N]   if x >= thresholds[N-1]

The labels are interpreted as an ordered enum: ``labels[0] < labels[1]
< … < labels[N]``. The property proven (or refuted) is:

  ∀ x1, x2 ∈ domain. x1 <= x2 ⇒ value(x1) <= value(x2)

i.e. raising the input never lowers the output. For the canonical
RAG mapping (``RED < AMBER < GREEN`` at thresholds ``[40, 70]`` over
the domain ``[0, 100]``), this is true and Z3 reports
:attr:`ProofResult.status` as ``PROVEN``. A broken mapping (e.g.
swapped labels at a threshold) produces a concrete counterexample
``(x1, x2)`` showing the inversion.

Z3 is invoked at proof time only. Importing this module is cheap; the
heavy lifting happens inside :func:`verify_rag_mapping`. The solver
runs on real-valued arithmetic — exhaustive over the entire (uncountable)
domain — rather than checking a finite set of sample points.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Sequence

__all__ = [
    "DEFAULT_RAG_THRESHOLDS",
    "DEFAULT_RAG_LABELS",
    "ProofResult",
    "verify_rag_mapping",
    "evaluate_rag",
]


# ─────────────────────────────────────────────────────────────────────────
# Defaults — source of truth: pm_mcp_servers.pm_assumptions._rag
# ─────────────────────────────────────────────────────────────────────────


DEFAULT_RAG_THRESHOLDS: tuple[float, ...] = (40.0, 70.0)
"""The default confidence-score thresholds, copied from pm-assumptions.

``RED`` for scores below 40, ``AMBER`` for 40–69, ``GREEN`` for 70+.
A score of exactly 40 is AMBER; a score of exactly 70 is GREEN. The
convention is that the threshold is the *lower* bound of the higher
band (left-closed, right-open intervals)."""


DEFAULT_RAG_LABELS: tuple[str, ...] = ("RED", "AMBER", "GREEN")
"""The default ordered labels. ``RED < AMBER < GREEN`` by index."""


DEFAULT_RAG_ORDERING: dict[str, int] = {"RED": 0, "AMBER": 1, "GREEN": 2}
"""The canonical semantic ranking for RAG labels.

The verifier proves monotonicity *with respect to this ordering*, not
with respect to the labels' position in the supplied list. So if a
caller accidentally writes ``labels=("GREEN", "AMBER", "RED")`` (in
descending instead of ascending order), the verifier produces a
counterexample rather than declaring the mapping "monotone in
position-order" — which would always be vacuously true.

Callers who use non-RAG labels supply their own ``label_ordering``
dict to :func:`verify_rag_mapping`.
"""


DEFAULT_DOMAIN: tuple[float, float] = (0.0, 100.0)
"""The default confidence-score domain. pm-assumptions uses 0–100."""


# ─────────────────────────────────────────────────────────────────────────
# Result type
# ─────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ProofResult:
    """Outcome of running :func:`verify_rag_mapping`.

    Attributes:
        status: ``"PROVEN"`` if Z3 confirmed monotonicity over the
            entire domain. ``"COUNTEREXAMPLE"`` if Z3 found a pair of
            inputs that violates monotonicity (i.e. ``x1 <= x2`` but
            ``value(x1) > value(x2)``). ``"UNKNOWN"`` if the solver
            could not decide (rare for this class of constraints; can
            happen with very long thresholds or unusual configuration).
        message: Plain-English explanation suitable for surfacing to a
            developer or auditor.
        counterexample: When ``status == "COUNTEREXAMPLE"``, a pair
            ``(x1, x2)`` with ``x1 <= x2`` and ``value(x1) > value(x2)``.
            Otherwise ``None``.
        counterexample_labels: When ``status == "COUNTEREXAMPLE"``, the
            label values at ``x1`` and ``x2`` respectively. Otherwise
            ``None``.
        thresholds: The thresholds verified (for the audit trail).
        labels: The labels verified (for the audit trail).
        domain: The domain verified.
    """

    status: Literal["PROVEN", "COUNTEREXAMPLE", "UNKNOWN"]
    message: str
    counterexample: tuple[float, float] | None = None
    counterexample_labels: tuple[str, str] | None = None
    thresholds: tuple[float, ...] = field(default_factory=tuple)
    labels: tuple[str, ...] = field(default_factory=tuple)
    domain: tuple[float, float] = field(default_factory=lambda: DEFAULT_DOMAIN)

    @property
    def is_proven(self) -> bool:
        """``True`` iff the solver confirmed monotonicity."""
        return self.status == "PROVEN"


# ─────────────────────────────────────────────────────────────────────────
# Python evaluation helper (independent of Z3)
# ─────────────────────────────────────────────────────────────────────────


def evaluate_rag(
    value: float,
    thresholds: Sequence[float] = DEFAULT_RAG_THRESHOLDS,
    labels: Sequence[str] = DEFAULT_RAG_LABELS,
) -> str:
    """Apply the threshold step-function mapping at ``value``.

    Pure-Python reference implementation, used by the verifier to
    re-derive the counterexample's labels (and by tests). Behaviour
    matches pm-assumptions' ``_rag`` exactly: thresholds are
    left-closed, right-open — ``value == thresholds[i]`` falls in the
    band labelled ``labels[i + 1]``.

    Args:
        value: The numeric input.
        thresholds: Ascending threshold sequence of length N.
        labels: Ordered label sequence of length N + 1.

    Returns:
        The label whose band contains ``value``.

    Raises:
        ValueError: If ``len(labels) != len(thresholds) + 1`` or
            thresholds are not strictly ascending.
    """
    if len(labels) != len(thresholds) + 1:
        raise ValueError(
            f"labels must have length len(thresholds) + 1; "
            f"got len(labels)={len(labels)}, len(thresholds)={len(thresholds)}"
        )
    for i in range(len(thresholds) - 1):
        if thresholds[i] >= thresholds[i + 1]:
            raise ValueError(
                f"thresholds must be strictly ascending; got {list(thresholds)}"
            )
    for i, t in enumerate(thresholds):
        if value < t:
            return labels[i]
    return labels[-1]


# ─────────────────────────────────────────────────────────────────────────
# Z3 verification
# ─────────────────────────────────────────────────────────────────────────


def verify_rag_mapping(
    thresholds: Sequence[float] = DEFAULT_RAG_THRESHOLDS,
    labels: Sequence[str] = DEFAULT_RAG_LABELS,
    domain: tuple[float, float] = DEFAULT_DOMAIN,
    label_ordering: dict[str, int] | None = None,
) -> ProofResult:
    """Prove that the threshold step-function mapping is monotone non-decreasing.

    Uses Z3 to search exhaustively over the real-valued domain for a
    pair ``(x1, x2)`` with ``x1 <= x2`` and
    ``ordering(value(x1)) > ordering(value(x2))``. If the search is
    unsat, monotonicity is proven. If sat, the model is returned as a
    concrete counterexample.

    The verification uses an explicit label ordering — *not* the
    labels' position in ``labels``. This is what catches the common
    bug of writing labels in descending instead of ascending order
    (e.g. ``labels=("GREEN", "AMBER", "RED")``): the verifier finds
    a counterexample where input increases but the semantic rank
    decreases. Verifying "monotone in position-order" would be
    vacuously true and useless.

    Args:
        thresholds: Ascending sequence of threshold values. Length N.
        labels: Label sequence assigned to each band. Length N + 1.
        domain: ``(lower, upper)`` over which to verify. Defaults to
            the pm-assumptions confidence-score domain ``(0, 100)``.
        label_ordering: Dict mapping each label string to its semantic
            rank (small = low, large = high). If ``None``, the default
            is :data:`DEFAULT_RAG_ORDERING` for the canonical RAG
            labels; otherwise every label in ``labels`` must appear
            as a key in ``label_ordering``.

    Returns:
        :class:`ProofResult` with ``status`` ``"PROVEN"``,
        ``"COUNTEREXAMPLE"``, or ``"UNKNOWN"``.

    Raises:
        ImportError: If ``z3-solver`` is not installed. Z3 is an
            optional dependency surfaced via the ``verified`` extras.
        ValueError: On malformed thresholds/labels/domain or missing
            ordering entries.
    """
    # Deferred import — keeps the package importable when z3 is not
    # installed (the verifier is opt-in).
    try:
        import z3
    except ImportError as exc:  # pragma: no cover — environment-specific
        raise ImportError(
            "verify_rag_mapping requires the z3-solver package. "
            "Install with: pip install z3-solver"
        ) from exc

    # ── Validate inputs ────────────────────────────────────────────────

    if len(thresholds) < 1:
        raise ValueError("At least one threshold is required")
    if len(labels) != len(thresholds) + 1:
        raise ValueError(
            f"labels must have length len(thresholds) + 1; "
            f"got len(labels)={len(labels)}, len(thresholds)={len(thresholds)}"
        )
    for i in range(len(thresholds) - 1):
        if thresholds[i] >= thresholds[i + 1]:
            raise ValueError(
                f"thresholds must be strictly ascending; got {list(thresholds)}"
            )
    lower, upper = domain
    if not lower < upper:
        raise ValueError(f"domain must be strictly increasing; got {domain}")

    # Resolve label ordering. If the user didn't pass one, default to
    # the canonical RAG ordering for labels we recognise; otherwise
    # fall back to position-order (which is trivially monotone but
    # documented as such).
    if label_ordering is None:
        if set(labels) <= set(DEFAULT_RAG_ORDERING.keys()):
            ordering = DEFAULT_RAG_ORDERING
        else:
            ordering = {label: i for i, label in enumerate(labels)}
    else:
        missing = [label for label in labels if label not in label_ordering]
        if missing:
            raise ValueError(
                f"label_ordering missing entries for: {missing}. "
                "Every label in `labels` must have a rank."
            )
        ordering = label_ordering

    # The per-band semantic rank, in band order (= labels order).
    band_ranks = [ordering[label] for label in labels]

    # ── Build Z3 problem ───────────────────────────────────────────────

    # Two real-valued unknowns in the domain.
    x1 = z3.Real("x1")
    x2 = z3.Real("x2")

    # value(x) = semantic rank of the band x falls in.
    # Encode as an If-expression mirroring evaluate_rag, but emitting
    # the band's rank rather than its index.
    def band_rank_for(x: z3.ArithRef) -> z3.ArithRef:
        expr: z3.ArithRef = z3.IntVal(band_ranks[-1])
        for i in range(len(thresholds) - 1, -1, -1):
            expr = z3.If(x < thresholds[i], z3.IntVal(band_ranks[i]), expr)
        return expr

    v1 = band_rank_for(x1)
    v2 = band_rank_for(x2)

    solver = z3.Solver()
    solver.add(x1 >= lower, x1 <= upper)
    solver.add(x2 >= lower, x2 <= upper)
    # Look for the counterexample: x1 <= x2 ∧ value(x1) > value(x2).
    solver.add(x1 <= x2)
    solver.add(v1 > v2)

    check = solver.check()

    if check == z3.unsat:
        return ProofResult(
            status="PROVEN",
            message=(
                f"Monotonicity proven by Z3 over domain "
                f"[{lower}, {upper}] for thresholds {list(thresholds)} "
                f"with labels {list(labels)}."
            ),
            thresholds=tuple(thresholds),
            labels=tuple(labels),
            domain=domain,
        )

    if check == z3.sat:
        model = solver.model()
        cx1 = _z3_real_to_float(model[x1])
        cx2 = _z3_real_to_float(model[x2])
        lcx1 = evaluate_rag(cx1, thresholds, labels)
        lcx2 = evaluate_rag(cx2, thresholds, labels)
        return ProofResult(
            status="COUNTEREXAMPLE",
            message=(
                f"Monotonicity refuted. value({cx1}) = {lcx1!r} but "
                f"value({cx2}) = {lcx2!r}, even though {cx1} <= {cx2}. "
                f"Inspect thresholds {list(thresholds)} and labels "
                f"{list(labels)} — labels must be ordered to match the "
                f"thresholds' ordering."
            ),
            counterexample=(cx1, cx2),
            counterexample_labels=(lcx1, lcx2),
            thresholds=tuple(thresholds),
            labels=tuple(labels),
            domain=domain,
        )

    # z3.unknown — solver could not decide.
    return ProofResult(
        status="UNKNOWN",
        message=(
            "Z3 could not decide monotonicity within its time/resource "
            "budget. Consider simplifying the thresholds, narrowing the "
            "domain, or running with a longer time bound."
        ),
        thresholds=tuple(thresholds),
        labels=tuple(labels),
        domain=domain,
    )


# ─────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────


def _z3_real_to_float(value) -> float:
    """Coerce a Z3 model's Real value to a Python float.

    Z3 returns rationals; ``.as_fraction()`` is exact but yields a
    ``Fraction`` we then float-cast. Returns ``0.0`` for ``None``
    (which Z3 can return for variables whose value is irrelevant to
    the unsat core).
    """
    if value is None:
        return 0.0
    try:
        return float(value.as_fraction())
    except AttributeError:
        return float(str(value))
