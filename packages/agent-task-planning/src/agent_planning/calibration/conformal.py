"""Split-conformal prediction for classification and regression.

Implements the reference architecture from *Verified Autonomy* §7.3
(Newman et al., May 2026, DOI 10.5281/zenodo.19096229), which in turn
follows Angelopoulos & Bates (2023). Two flavours of conformal
prediction:

* **Classification — prediction sets.**
  :func:`calibrate_conformal` computes a quantile threshold from a
  calibration set whose true labels are known.
  :func:`conformal_predict` then turns the model's class probabilities
  for new samples into *sets* of possible labels: the set is
  guaranteed (under exchangeability) to contain the true label with
  probability at least ``1 - alpha``, *no matter how miscalibrated the
  underlying probabilities are*. :func:`evaluate_coverage` measures
  the empirical coverage on a held-out test set.

* **Regression — prediction band around a point estimate.**
  :func:`conformal_predict_band` takes a single point estimate and a
  history of calibration residuals (signed errors from past
  predictions) and returns a symmetric ``(low, high)`` band whose
  width is the (1 - alpha) quantile of the absolute residuals. This is
  the use case the platform's Monte Carlo and benchmark-percentile
  tools need: they don't have a probabilistic model to sample from,
  but they do have a track record of past forecast errors.

Both flavours rely only on exchangeability of the calibration and
test points — they do **not** assume the model is calibrated, well-
specified, or even probabilistic.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

__all__ = [
    "calibrate_conformal",
    "conformal_predict",
    "evaluate_coverage",
    "conformal_predict_band",
]


# ─────────────────────────────────────────────────────────────────────────
# Classification
# ─────────────────────────────────────────────────────────────────────────


def calibrate_conformal(
    y_cal: Sequence[int] | np.ndarray,
    probs_cal: Sequence[float] | np.ndarray,
    alpha: float = 0.1,
) -> float:
    """Compute the conformal quantile from a calibration set.

    The non-conformity score used here is ``1 - p_true`` where
    ``p_true`` is the predicted probability of the true class. Higher
    scores mean the model was more wrong; the quantile of these scores
    is the threshold below which a class is "plausible".

    The finite-sample correction is the ceiling
    ``ceil((n + 1) * (1 - alpha)) / n`` quantile, which guarantees
    marginal coverage at least ``1 - alpha`` for exchangeable data
    (Angelopoulos & Bates 2023, Theorem 2.1).

    Args:
        y_cal: True class labels for the calibration set, 1-D of
            length ``n``.
        probs_cal: Predicted class probabilities for the calibration
            set, 2-D of shape ``(n, n_classes)``.
        alpha: Target miscoverage rate in ``(0, 1)``. ``alpha = 0.1``
            gives 90% nominal coverage.

    Returns:
        Threshold ``q_hat`` in ``[0, 1]`` to pass to
        :func:`conformal_predict`.

    Raises:
        ValueError: On shape mismatch or invalid ``alpha``.
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1); got {alpha}")

    y_arr = np.asarray(y_cal, dtype=int)
    p_arr = np.asarray(probs_cal, dtype=float)

    if p_arr.ndim != 2:
        raise ValueError(
            f"probs_cal must be 2-D (n, n_classes); got ndim={p_arr.ndim}"
        )
    if y_arr.shape[0] != p_arr.shape[0]:
        raise ValueError(
            "y_cal and probs_cal must have the same first dimension; "
            f"got {y_arr.shape[0]} vs {p_arr.shape[0]}"
        )
    if y_arr.size == 0:
        raise ValueError("calibrate_conformal requires at least one sample")

    n = y_arr.shape[0]
    p_true = p_arr[np.arange(n), y_arr]
    nonconformity = 1.0 - p_true

    # Finite-sample-corrected quantile level.
    level = min(1.0, np.ceil((n + 1) * (1.0 - alpha)) / n)
    # np.quantile uses a slightly different interpolation than the
    # paper's reference; the manual sort-and-index approach below
    # matches Angelopoulos & Bates exactly.
    sorted_scores = np.sort(nonconformity)
    idx = int(np.ceil((n + 1) * (1.0 - alpha))) - 1
    idx = max(0, min(idx, n - 1))
    return float(sorted_scores[idx])


def conformal_predict(
    probs: Sequence[float] | np.ndarray,
    q_hat: float,
) -> list[set[int]]:
    """Turn class probabilities into conformal prediction sets.

    A class ``c`` is included in the set for sample ``i`` iff
    ``probs[i, c] >= 1 - q_hat`` (equivalently, the non-conformity
    score ``1 - probs[i, c]`` does not exceed the threshold).

    Args:
        probs: 2-D array of predicted probabilities,
            ``(n_samples, n_classes)``.
        q_hat: Threshold from :func:`calibrate_conformal`.

    Returns:
        List of length ``n_samples``; each element is a set of class
        indices. Sets may be empty (very high ``q_hat`` cannot
        recommend any class) or contain multiple classes.

    Raises:
        ValueError: On invalid shape or ``q_hat`` outside ``[0, 1]``.
    """
    if not 0.0 <= q_hat <= 1.0:
        raise ValueError(f"q_hat must be in [0, 1]; got {q_hat}")

    p_arr = np.asarray(probs, dtype=float)
    if p_arr.ndim != 2:
        raise ValueError(
            f"probs must be 2-D (n, n_classes); got ndim={p_arr.ndim}"
        )

    cutoff = 1.0 - q_hat
    sets: list[set[int]] = []
    for row in p_arr:
        sets.append({int(c) for c, p in enumerate(row) if p >= cutoff})
    return sets


def evaluate_coverage(
    y_true: Sequence[int] | np.ndarray,
    prediction_sets: list[set[int]],
) -> float:
    """Fraction of samples whose true label is in the predicted set.

    Args:
        y_true: True class labels, 1-D of length ``n``.
        prediction_sets: Output of :func:`conformal_predict`, length
            ``n``.

    Returns:
        Empirical coverage in ``[0, 1]``.

    Raises:
        ValueError: On length mismatch.
    """
    y_arr = np.asarray(y_true, dtype=int)
    if y_arr.shape[0] != len(prediction_sets):
        raise ValueError(
            "y_true and prediction_sets must have the same length; "
            f"got {y_arr.shape[0]} vs {len(prediction_sets)}"
        )
    if y_arr.size == 0:
        return 0.0

    covered = sum(int(int(y) in s) for y, s in zip(y_arr, prediction_sets))
    return covered / y_arr.shape[0]


# ─────────────────────────────────────────────────────────────────────────
# Regression — band around a point estimate
# ─────────────────────────────────────────────────────────────────────────


def conformal_predict_band(
    point_estimate: float,
    calibration_residuals: Sequence[float] | np.ndarray,
    alpha: float = 0.2,
) -> tuple[float, float]:
    """Return a symmetric conformal band around ``point_estimate``.

    The band width is the (1 - alpha) quantile of the absolute
    calibration residuals (signed errors from past predictions, but
    only the magnitudes are used). Under exchangeability the band
    covers the next true value with probability at least ``1 - alpha``.

    This is the right primitive for the platform's Monte Carlo and
    benchmark-percentile pipelines: there is no probabilistic model
    to sample from at predict time, only a single point estimate, but
    there is a track record of historical residuals from which
    coverage can be calibrated.

    Args:
        point_estimate: The single forecast value, e.g. a P50.
        calibration_residuals: 1-D iterable of signed residuals
            ``y_true - y_pred`` from past calibration points. Absolute
            values are used; the sign carries no information here.
        alpha: Target miscoverage rate in ``(0, 1)``. Default 0.2
            (80% nominal coverage), matching the paper's reference.

    Returns:
        ``(low, high)`` tuple where ``high - low`` is twice the
        calibrated half-width and the band is symmetric around
        ``point_estimate``.

    Raises:
        ValueError: On invalid ``alpha`` or empty calibration set.
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1); got {alpha}")

    residuals = np.abs(np.asarray(calibration_residuals, dtype=float))
    n = residuals.shape[0]
    if n == 0:
        raise ValueError("conformal_predict_band requires at least one residual")

    sorted_resid = np.sort(residuals)
    idx = int(np.ceil((n + 1) * (1.0 - alpha))) - 1
    idx = max(0, min(idx, n - 1))
    half_width = float(sorted_resid[idx])

    return point_estimate - half_width, point_estimate + half_width
