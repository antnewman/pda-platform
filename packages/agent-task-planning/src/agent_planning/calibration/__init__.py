"""Calibration and conformal-prediction primitives.

Verified Autonomy Layer 4 (Calibration and Conformal Prediction), §7.3
reference implementation. Three families of primitives:

* **Calibration measurement.** :func:`compute_ece` returns the Expected
  Calibration Error with full reliability-diagram bin data. The bin
  data lets a consumer render the calibration plot or display
  confidence-vs-accuracy gaps to a reviewer.

* **Calibration correction.** :func:`find_temperature` and
  :func:`apply_temperature_scaling` implement Guo et al. (2017)
  temperature scaling — a single scalar T fit by minimising the
  negative log-likelihood on a held-out validation split. Recalibrating
  with ``T`` produces probabilities whose ECE is materially lower
  without changing the argmax classification.

* **Conformal prediction.** :func:`calibrate_conformal`,
  :func:`conformal_predict`, and :func:`evaluate_coverage` implement
  split-conformal classification from Angelopoulos & Bates (2023) —
  prediction *sets* with a marginal coverage guarantee independent of
  the underlying model's miscalibration. :func:`conformal_predict_band`
  is the regression variant the Monte Carlo / benchmark-percentile
  pipelines use: a point estimate plus a history of residuals
  produces a band whose width is calibrated to the requested
  miscoverage rate.

The implementations follow the paper's reference architecture (numpy +
scipy, no sklearn dependency in the conformal path). They are written
for transparency rather than scale — production deployments may swap
for MAPIE or sklearn-conformal-prediction once the API stabilises.

The module imports numpy and scipy at top level. Both are already
pulled in by the platform's deployment (sklearn brings scipy
transitively), so this is a no-cost addition. Stand-alone consumers
that don't need the calibration extras can simply not import this
sub-module.
"""

from agent_planning.calibration.conformal import (
    calibrate_conformal,
    conformal_predict,
    conformal_predict_band,
    evaluate_coverage,
)
from agent_planning.calibration.ece import ECEBin, ECEResult, compute_ece
from agent_planning.calibration.temperature import (
    apply_temperature_scaling,
    find_temperature,
)

__all__ = [
    # ECE
    "ECEBin",
    "ECEResult",
    "compute_ece",
    # Temperature scaling
    "find_temperature",
    "apply_temperature_scaling",
    # Conformal prediction
    "calibrate_conformal",
    "conformal_predict",
    "evaluate_coverage",
    "conformal_predict_band",
]
