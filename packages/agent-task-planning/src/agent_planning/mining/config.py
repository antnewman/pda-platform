"""Configuration for outlier mining."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TemperatureSchedule(Enum):
    """Temperature scheduling strategies for diverse generation."""
    FIXED = "fixed"                        # Constant temperature
    LINEAR_INCREASE = "linear_increase"    # Gradually increase temp
    EXPONENTIAL = "exponential"            # Slow start, fast end
    RANDOM = "random"                      # Random temp each sample
    EXPLORE_EXPLOIT = "explore_exploit"    # High early, low late (EAD style)


class PromptDiversification(Enum):
    """Prompt diversification strategies."""
    NONE = "none"                         # No diversification
    ROLE_INJECTION = "role_injection"     # Inject different roles
    INSTRUCTION_VARIATION = "instruction" # Vary instructions
    PERSPECTIVE_SHIFT = "perspective"     # Shift perspectives
    ALL = "all"                           # All strategies combined


class SaturationMethod(Enum):
    """Methods for detecting saturation."""
    NONE = "none"                         # No saturation detection
    SEMANTIC = "semantic"                 # Embedding similarity plateau
    STRUCTURAL = "structural"             # Schema consistency plateau
    COMBINED = "combined"                 # Both signals combined


@dataclass
class MiningConfig:
    """Configuration for outlier mining."""

    # === Sampling Settings ===
    samples: int = 32                          # How many to generate (sweet spot: 20-50)
    max_samples: int = 64                      # Absolute maximum if saturation not reached

    # Temperature settings
    temperature_start: float = 0.7             # Starting temperature
    temperature_end: float = 1.0               # Ending temperature
    temperature_schedule: TemperatureSchedule = TemperatureSchedule.LINEAR_INCREASE

    # Min-p sampling (research-validated improvement)
    use_min_p: bool = True
    min_p: float = 0.05                        # Min probability threshold
    top_p: float = 0.9                         # Nucleus sampling

    # Prompt diversification
    diversification: PromptDiversification = PromptDiversification.ROLE_INJECTION

    # === Quality Filtering ===
    quality_threshold: float = 0.6             # Minimum quality to include
    check_semantic_entropy: bool = True        # Detect potential hallucinations
    entropy_threshold: float = 0.7             # Above this = likely confabulation

    # === Clustering Settings ===
    # UMAP dimensionality reduction
    umap_n_components: int = 10                # Reduce to this many dimensions
    umap_n_neighbors: int = 15                 # Local vs global structure
    umap_min_dist: float = 0.1                 # Minimum distance between points

    # HDBSCAN clustering
    hdbscan_min_cluster_size: int = 2          # Minimum samples per cluster
    hdbscan_min_samples: int = 1               # Core point threshold
    allow_singleton_clusters: bool = True      # True outliers as single-item clusters

    # === Scoring Weights ===
    novelty_weight: float = 0.4                # Weight for novelty score
    coherence_weight: float = 0.3              # Weight for coherence score
    coverage_weight: float = 0.3               # Weight for coverage score

    # === Saturation Detection ===
    saturation_method: SaturationMethod = SaturationMethod.COMBINED
    saturation_window: int = 8                 # Check every N samples
    saturation_threshold: float = 0.8          # Consistency threshold for stopping
    min_samples_before_saturation: int = 16    # Don't stop before this

    # === Characterisation ===
    characterise_clusters: bool = True         # Generate cluster summaries
    extract_assumptions: bool = True           # Extract implicit assumptions
    explain_differences: bool = True           # Pairwise difference explanations
    characterisation_model: Optional[str] = None  # Use different model for characterisation

    # === Output ===
    max_candidates_returned: int = 5           # Top N candidates to return
    include_consensus_baseline: bool = True    # Include what consensus mode would return
    include_all_clusters: bool = True          # Include cluster summaries for all

    # === Efficiency ===
    parallel_generation: bool = True           # Generate samples in parallel
    max_concurrent: int = 5                    # Max concurrent API calls
    embedding_batch_size: int = 32             # Batch size for embedding
    cache_embeddings: bool = True              # Cache embeddings for similar queries

    def get_temperature(self, sample_index: int, total_samples: int) -> float:
        """Get temperature for a given sample based on schedule."""
        if self.temperature_schedule == TemperatureSchedule.FIXED:
            return self.temperature_start

        progress = sample_index / max(total_samples - 1, 1)

        if self.temperature_schedule == TemperatureSchedule.LINEAR_INCREASE:
            return self.temperature_start + progress * (self.temperature_end - self.temperature_start)

        elif self.temperature_schedule == TemperatureSchedule.EXPONENTIAL:
            # Slow start, fast end
            import math
            exp_progress = (math.exp(progress * 2) - 1) / (math.exp(2) - 1)
            return self.temperature_start + exp_progress * (self.temperature_end - self.temperature_start)

        elif self.temperature_schedule == TemperatureSchedule.RANDOM:
            import random
            return random.uniform(self.temperature_start, self.temperature_end)

        elif self.temperature_schedule == TemperatureSchedule.EXPLORE_EXPLOIT:
            # High early (explore), low late (exploit) - EAD style
            if progress < 0.5:
                return self.temperature_end  # Explore
            else:
                return self.temperature_start  # Exploit

        return self.temperature_start
