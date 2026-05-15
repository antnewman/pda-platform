"""Expected Calibration Error and reliability-diagram binning.

Implements the equal-width binning ECE estimator from Guo et al. (2017),
matching the reference in *Verified Autonomy* §7.3 (Newman et al.,
May 2026, DOI 10.5281/zenodo.19096229).

A perfectly calibrated classifier has confidence equal to accuracy on
every subset of its predictions. ECE estimates the gap by binning
predictions by their top-class probability and computing the weighted
mean absolute difference between mean confidence and mean accuracy
within each bin.

The function returns a structured :class:`ECEResult` that includes
per-bin counts, means, and gap so consumers can either summarise (the
scalar ECE) or render the reliability diagram (the bin data).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

__all__ = ["ECEBin", "ECEResult", "compute_ece"]


@dataclass(frozen=True)
class ECEBin:
    """Per-bin reliability-diagram data.

    Attributes:
        lower: Inclusive lower edge of the bin (in [0, 1]).
        upper: Exclusive upper edge of the bin (except the top bin,
            which is inclusive on the right so ``confidence == 1.0``
            falls in).
        count: Number of samples falling in this bin.
        mean_confidence: Mean predicted top-class probability in the
            bin. ``nan`` if the bin is empty.
        mean_accuracy: Mean correctness (0/1) in the bin. ``nan`` if
            the bin is empty.
        gap: ``|mean_confidence - mean_accuracy|``. ``nan`` if empty.
    """

    lower: float
    upper: float
    count: int
    mean_confidence: float
    mean_accuracy: float
    gap: float


@dataclass(frozen=True)
class ECEResult:
    """Outcome of :func:`compute_ece`.

    Attributes:
        ece: The scalar Expected Calibration Error in [0, 1]. Lower is
            better; a perfectly calibrated classifier has ``ece == 0``.
        bins: Per-bin reliability data, in ascending order. Length is
            ``n_bins``.
        n_samples: Total number of samples evaluated.
    """

    ece: float
    bins: list[ECEBin]
    n_samples: int


def compute_ece(
    y_true: Sequence[int] | np.ndarray,
    y_probs: Sequence[float] | np.ndarray,
    n_bins: int = 15,
) -> ECEResult:
    """Compute Expected Calibration Error from labels and predicted probabilities.

    Two input shapes for ``y_probs`` are accepted:

    * 1-D of shape ``(n,)`` — interpreted as the predicted probability
      of the positive class in a binary problem. ``y_true`` is then
      treated as 0/1 labels and the prediction is ``y_probs >= 0.5``.
    * 2-D of shape ``(n, n_classes)`` — interpreted as full softmax
      probabilities. The top-class probability is used as confidence
      and the argmax is the prediction.

    Args:
        y_true: True class labels (0-indexed integers).
        y_probs: Predicted probabilities. See shape rules above.
        n_bins: Number of equal-width bins on ``[0, 1]``. Default 15
            from the paper. Must be ``>= 1``.

    Returns:
        :class:`ECEResult` with the scalar ECE and per-bin diagnostics.

    Raises:
        ValueError: On length mismatch, empty input, or invalid
            ``n_bins``.
    """
    if n_bins < 1:
        raise ValueError(f"n_bins must be >= 1; got {n_bins}")

    y_true_arr = np.asarray(y_true)
    y_probs_arr = np.asarray(y_probs, dtype=float)

    if y_true_arr.size == 0:
        raise ValueError("compute_ece requires at least one sample")
    if y_true_arr.shape[0] != y_probs_arr.shape[0]:
        raise ValueError(
            "y_true and y_probs must have the same first dimension; "
            f"got {y_true_arr.shape[0]} vs {y_probs_arr.shape[0]}"
        )

    if y_probs_arr.ndim == 1:
        # Binary case: y_probs is P(class 1).
        confidence = np.where(
            y_probs_arr >= 0.5, y_probs_arr, 1.0 - y_probs_arr
        )
        prediction = (y_probs_arr >= 0.5).astype(int)
    elif y_probs_arr.ndim == 2:
        confidence = y_probs_arr.max(axis=1)
        prediction = y_probs_arr.argmax(axis=1)
    else:
        raise ValueError(
            f"y_probs must be 1-D or 2-D; got ndim={y_probs_arr.ndim}"
        )

    correct = (prediction == y_true_arr).astype(float)

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bins: list[ECEBin] = []
    n_total = y_true_arr.shape[0]
    ece_sum = 0.0

    for i in range(n_bins):
        lower = float(bin_edges[i])
        upper = float(bin_edges[i + 1])
        # Last bin is inclusive on the right so confidence == 1.0 is
        # captured instead of dropped.
        if i == n_bins - 1:
            mask = (confidence >= lower) & (confidence <= upper)
        else:
            mask = (confidence >= lower) & (confidence < upper)

        count = int(mask.sum())
        if count == 0:
            bins.append(
                ECEBin(
                    lower=lower,
                    upper=upper,
                    count=0,
                    mean_confidence=float("nan"),
                    mean_accuracy=float("nan"),
                    gap=float("nan"),
                )
            )
            continue

        bin_conf = float(confidence[mask].mean())
        bin_acc = float(correct[mask].mean())
        gap = abs(bin_conf - bin_acc)
        ece_sum += (count / n_total) * gap
        bins.append(
            ECEBin(
                lower=lower,
                upper=upper,
                count=count,
                mean_confidence=bin_conf,
                mean_accuracy=bin_acc,
                gap=gap,
            )
        )

    return ECEResult(ece=float(ece_sum), bins=bins, n_samples=n_total)
