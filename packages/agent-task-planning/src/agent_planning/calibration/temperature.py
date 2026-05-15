"""Temperature scaling for post-hoc calibration.

Implements the single-scalar recalibration from Guo et al. (2017),
matching the reference in *Verified Autonomy* §7.3.

The recipe: take a model's pre-softmax logits and a validation set of
ground-truth labels. Find the scalar ``T`` that minimises the
negative log-likelihood of ``softmax(logits / T)``. Applying the same
``T`` at inference produces probabilities whose ECE is materially
lower than the raw softmax without changing the argmax classification.

This module is intentionally minimal: numpy + scipy, no torch
dependency. Production deployments may prefer a torch-based fit for
GPU re-calibration, but for the per-tool calibration sets the platform
uses (typically a few hundred to a few thousand samples) the
scipy-scalar solver is fast and transparent.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import logsumexp

__all__ = ["find_temperature", "apply_temperature_scaling"]


# ─────────────────────────────────────────────────────────────────────────
# Apply
# ─────────────────────────────────────────────────────────────────────────


def apply_temperature_scaling(
    logits: Sequence[float] | np.ndarray,
    temperature: float,
) -> np.ndarray:
    """Apply softmax to ``logits / temperature``.

    Args:
        logits: 2-D array of shape ``(n_samples, n_classes)`` or 1-D of
            shape ``(n_classes,)``.
        temperature: Positive scalar. ``temperature == 1.0`` returns
            the raw softmax; ``temperature > 1.0`` softens the
            distribution; ``temperature < 1.0`` sharpens it.

    Returns:
        Softmax probabilities of the same shape as ``logits``, summing
        to 1 along the class axis.

    Raises:
        ValueError: If ``temperature <= 0``.
    """
    if temperature <= 0.0:
        raise ValueError(f"temperature must be > 0; got {temperature}")

    logits_arr = np.asarray(logits, dtype=float)
    scaled = logits_arr / temperature
    if scaled.ndim == 1:
        scaled = scaled.reshape(1, -1)
        squeeze = True
    else:
        squeeze = False
    # Numerically stable softmax via log-sum-exp.
    log_probs = scaled - logsumexp(scaled, axis=1, keepdims=True)
    probs = np.exp(log_probs)
    return probs[0] if squeeze else probs


# ─────────────────────────────────────────────────────────────────────────
# Fit
# ─────────────────────────────────────────────────────────────────────────


def _negative_log_likelihood(
    temperature: float,
    logits: np.ndarray,
    y_true: np.ndarray,
) -> float:
    """NLL of the temperature-scaled probabilities for the true labels."""
    if temperature <= 0.0:
        return float("inf")
    scaled = logits / temperature
    log_probs = scaled - logsumexp(scaled, axis=1, keepdims=True)
    # Pick out the log-prob of the true class for each sample.
    correct_logp = log_probs[np.arange(y_true.shape[0]), y_true]
    return float(-correct_logp.mean())


def find_temperature(
    logits: Sequence[float] | np.ndarray,
    y_true: Sequence[int] | np.ndarray,
    *,
    bracket: tuple[float, float] = (0.05, 10.0),
) -> float:
    """Find the temperature that minimises NLL on the calibration set.

    Args:
        logits: 2-D array of shape ``(n_samples, n_classes)`` carrying
            the model's pre-softmax logits on the calibration set.
        y_true: 1-D array of true class indices (length ``n_samples``).
        bracket: Search bracket for the scalar minimisation. The
            default ``(0.05, 10.0)`` covers the practical range for
            modern overconfident classifiers; widen if the calibration
            set is extremely overconfident or underconfident.

    Returns:
        The optimised temperature ``T > 0``.

    Raises:
        ValueError: On shape mismatch, empty input, or invalid bracket.
    """
    logits_arr = np.asarray(logits, dtype=float)
    y_true_arr = np.asarray(y_true, dtype=int)

    if logits_arr.ndim != 2:
        raise ValueError(
            f"logits must be 2-D (n_samples, n_classes); got ndim={logits_arr.ndim}"
        )
    if y_true_arr.size == 0:
        raise ValueError("find_temperature requires at least one sample")
    if logits_arr.shape[0] != y_true_arr.shape[0]:
        raise ValueError(
            "logits and y_true must have the same first dimension; "
            f"got {logits_arr.shape[0]} vs {y_true_arr.shape[0]}"
        )
    if not (0.0 < bracket[0] < bracket[1]):
        raise ValueError(
            f"bracket must be strictly positive and increasing; got {bracket}"
        )

    result = minimize_scalar(
        _negative_log_likelihood,
        args=(logits_arr, y_true_arr),
        bounds=bracket,
        method="bounded",
        options={"xatol": 1e-4},
    )
    if not result.success:
        # Fall back to the bracket midpoint with a warning in the
        # message; the paper notes the bounded-scalar method is robust
        # in practice but we don't want to silently return a random
        # value if the optimiser bails.
        raise RuntimeError(
            f"Temperature optimisation did not converge: {result.message}"
        )
    return float(result.x)
