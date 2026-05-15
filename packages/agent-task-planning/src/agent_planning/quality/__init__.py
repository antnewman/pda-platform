"""Quality scoring and potential-hallucinations flagging.

Verified Autonomy Layer 3 (Making Failures Visible), §6.3 reference
implementation. Three-output-category architecture: results the system
trusts, results the system rejects, and results the system is
*suspicious of* — published explicitly to human reviewers rather than
silently filtered.

The key insight from the paper §6.5: a system that silently filters its
bad outputs appears more reliable than one that shows you which outputs
it does not trust. The quality-score primitive computes a composite
score from coherence, relevance, completeness, and an entropy penalty;
the flagging primitive identifies samples whose semantic entropy crosses
a threshold (the model produced markedly different outputs across runs
for the same prompt — a reliable proxy for confabulation risk).

Usage::

    from agent_planning.quality import (
        compute_quality_score, flag_potential_hallucinations,
        compute_pass_rate, Sample,
    )

    score = compute_quality_score(
        coherence=0.60, relevance=0.65, completeness=0.55,
        semantic_entropy=0.75,
    )
    score.overall              # 0.49 (below 0.6 threshold)
    score.passed_threshold     # False

    samples = [
        Sample(id="s1", quality=compute_quality_score(0.9, 0.9, 0.9, 0.2)),
        Sample(id="s2", quality=compute_quality_score(0.6, 0.6, 0.6, 0.8)),
    ]
    flagged = flag_potential_hallucinations(samples)  # ["s2"]
    pass_rate = compute_pass_rate(samples)            # 0.5
"""

from agent_planning.quality.scoring import (
    DEFAULT_HALLUCINATION_THRESHOLD,
    DEFAULT_QUALITY_THRESHOLD,
    QualityScore,
    Sample,
    compute_pass_rate,
    compute_quality_score,
    flag_potential_hallucinations,
)

__all__ = [
    "DEFAULT_HALLUCINATION_THRESHOLD",
    "DEFAULT_QUALITY_THRESHOLD",
    "QualityScore",
    "Sample",
    "compute_pass_rate",
    "compute_quality_score",
    "flag_potential_hallucinations",
]
