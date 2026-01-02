"""Outlier mining module for diverse approach discovery."""

from .miner import OutlierMiner, mine, mine_batch
from .config import (
    MiningConfig,
    TemperatureSchedule,
    PromptDiversification,
    SaturationMethod,
)
from .models import (
    MiningCandidate,
    MiningResult,
    BatchMiningResult,
    ClusterInfo,
    DifferenceReport,
    DifferenceType,
    AssumptionReport,
    QualityScore,
    SaturationSignal,
)

__all__ = [
    # Main classes
    "OutlierMiner",

    # Convenience functions
    "mine",
    "mine_batch",

    # Configuration
    "MiningConfig",
    "TemperatureSchedule",
    "PromptDiversification",
    "SaturationMethod",

    # Result models
    "MiningCandidate",
    "MiningResult",
    "BatchMiningResult",
    "ClusterInfo",
    "DifferenceReport",
    "DifferenceType",
    "AssumptionReport",
    "QualityScore",
    "SaturationSignal",
]
