"""Statistical aggregation and outlier detection for confidence extraction."""

from collections import Counter
from statistics import mean, median, stdev
from typing import Any, Optional

from .models import OutlierReport


def compute_iqr(values: list[float]) -> tuple[float, float, float]:
    """Compute IQR bounds for outlier detection.

    Returns:
        Tuple of (q1, q3, iqr)
    """
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    q1_idx = n // 4
    q3_idx = (3 * n) // 4
    q1 = sorted_vals[q1_idx]
    q3 = sorted_vals[q3_idx]
    iqr = q3 - q1
    return q1, q3, iqr


def detect_numeric_outliers(
    values: list[float],
    sample_indices: list[int],
    field_name: str,
    iqr_multiplier: float = 1.5
) -> tuple[float, list[OutlierReport]]:
    """Detect outliers in numeric values using IQR method.

    Returns:
        Tuple of (consensus_value, list of outlier reports)
    """
    if len(values) < 3:
        # Not enough data for meaningful outlier detection
        return median(values), []

    q1, q3, iqr = compute_iqr(values)
    lower_bound = q1 - (iqr_multiplier * iqr)
    upper_bound = q3 + (iqr_multiplier * iqr)

    consensus = median(values)
    outliers = []

    # Compute range for normalisation
    value_range = max(values) - min(values) if max(values) != min(values) else 1

    for idx, (value, sample_idx) in enumerate(zip(values, sample_indices)):
        if value < lower_bound or value > upper_bound:
            divergence = abs(value - consensus) / value_range

            if value < lower_bound:
                reason = f"{field_name} value {value} is below lower bound {lower_bound:.2f} (Q1 - 1.5*IQR)"
            else:
                reason = f"{field_name} value {value} is above upper bound {upper_bound:.2f} (Q3 + 1.5*IQR)"

            outliers.append(OutlierReport(
                field=field_name,
                consensus_value=consensus,
                outlier_value=value,
                sample_index=sample_idx,
                divergence_score=min(divergence, 1.0),
                reason=reason
            ))

    return consensus, outliers


def aggregate_numeric(values: list[float]) -> dict[str, float]:
    """Aggregate numeric values with statistics.

    Returns:
        Dict with median, mean, min, max, stdev
    """
    result = {
        "median": median(values),
        "mean": mean(values),
        "min": min(values),
        "max": max(values),
    }
    if len(values) > 1:
        result["stdev"] = stdev(values)
    else:
        result["stdev"] = 0.0
    return result


def aggregate_categorical(values: list[str]) -> tuple[str, float]:
    """Aggregate categorical values using mode.

    Returns:
        Tuple of (mode_value, agreement_ratio)
    """
    counter = Counter(values)
    mode_value, mode_count = counter.most_common(1)[0]
    agreement = mode_count / len(values)
    return mode_value, agreement


def aggregate_text_exact(values: list[str]) -> tuple[str, float]:
    """Aggregate text values using exact match mode.

    Returns:
        Tuple of (most_common_value, agreement_ratio)
    """
    # Normalise whitespace
    normalised = [" ".join(v.split()) for v in values]
    return aggregate_categorical(normalised)


def aggregate_list_fields(values: list[list[str]]) -> tuple[list[str], float]:
    """Aggregate list fields by finding common items.

    Returns:
        Tuple of (common_items, coverage_ratio)
    """
    if not values:
        return [], 0.0

    # Count occurrences of each item across all samples
    item_counts: Counter = Counter()
    for item_list in values:
        for item in item_list:
            normalised = " ".join(item.split()).lower()
            item_counts[normalised] += 1

    # Items appearing in majority of samples
    threshold = len(values) / 2
    common_items = [item for item, count in item_counts.items() if count >= threshold]

    # Coverage: what fraction of items are common
    total_unique = len(item_counts)
    coverage = len(common_items) / total_unique if total_unique > 0 else 1.0

    return common_items, coverage


def compute_field_confidence(
    values: list[Any],
    field_type: str
) -> float:
    """Compute confidence score for a single field.

    Args:
        values: List of extracted values for this field
        field_type: One of 'numeric', 'categorical', 'text', 'list'

    Returns:
        Confidence score 0.0-1.0
    """
    if not values:
        return 0.0

    if field_type == "numeric":
        # For numeric: use coefficient of variation (lower = higher confidence)
        try:
            numeric_values = [float(v) for v in values if v is not None]
            if len(numeric_values) < 2:
                return 1.0 if numeric_values else 0.0
            m = mean(numeric_values)
            if m == 0:
                return 1.0 if stdev(numeric_values) == 0 else 0.5
            cv = stdev(numeric_values) / abs(m)
            # Map CV to confidence: CV=0 -> conf=1, CV>=1 -> conf=0
            return max(0.0, 1.0 - cv)
        except (ValueError, TypeError):
            return 0.0

    elif field_type in ("categorical", "text"):
        # For categorical/text: use agreement ratio
        non_null = [v for v in values if v is not None and str(v).strip()]
        if not non_null:
            return 0.0
        _, agreement = aggregate_categorical([str(v) for v in non_null])
        return agreement

    elif field_type == "list":
        # For lists: use coverage ratio
        list_values = [v for v in values if isinstance(v, list)]
        if not list_values:
            return 0.0
        _, coverage = aggregate_list_fields(list_values)
        return coverage

    return 0.5  # Unknown type


def compute_overall_confidence(field_confidences: dict[str, float]) -> float:
    """Compute overall confidence from field confidences.

    Uses weighted average, with lower confidence fields weighted more heavily
    (conservative approach).
    """
    if not field_confidences:
        return 0.0

    # Weight lower confidence fields more heavily
    weighted_sum = 0.0
    weight_sum = 0.0

    for field, conf in field_confidences.items():
        # Inverse weighting: low confidence fields get higher weight
        weight = 2.0 - conf  # Weight ranges from 1.0 to 2.0
        weighted_sum += conf * weight
        weight_sum += weight

    return weighted_sum / weight_sum if weight_sum > 0 else 0.0


def check_early_stop(
    extractions: list[dict[str, Any]],
    threshold: float,
    key_fields: Optional[list[str]] = None
) -> bool:
    """Check if samples agree enough to stop early.

    Args:
        extractions: List of extraction results so far
        threshold: Agreement threshold (e.g., 0.6 for 3/5)
        key_fields: Fields to check for agreement (None = all fields)

    Returns:
        True if early stopping criteria met
    """
    if len(extractions) < 3:
        return False

    # Get all fields to check
    all_fields = set()
    for ext in extractions:
        all_fields.update(ext.keys())

    fields_to_check = key_fields if key_fields else list(all_fields)

    # Check agreement on each field
    agreements = []
    for field in fields_to_check:
        values = [ext.get(field) for ext in extractions if field in ext]
        if not values:
            continue

        # Simple agreement: most common value ratio
        counter = Counter([str(v) for v in values])
        if counter:
            _, count = counter.most_common(1)[0]
            agreements.append(count / len(values))

    if not agreements:
        return False

    # Average agreement across fields
    avg_agreement = sum(agreements) / len(agreements)
    return avg_agreement >= threshold
