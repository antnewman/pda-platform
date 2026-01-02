"""Tests for aggregation functions."""

import pytest
from agent_planning.confidence.aggregation import (
    compute_iqr,
    detect_numeric_outliers,
    aggregate_numeric,
    aggregate_categorical,
    aggregate_list_fields,
    compute_field_confidence,
    compute_overall_confidence,
    check_early_stop,
)


class TestNumericAggregation:
    """Tests for numeric aggregation."""

    def test_compute_iqr(self):
        """Test IQR computation."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        q1, q3, iqr = compute_iqr(values)
        assert q1 == 3
        assert q3 == 8
        assert iqr == 5

    def test_aggregate_numeric(self):
        """Test numeric aggregation."""
        values = [10, 12, 15, 18, 20]
        result = aggregate_numeric(values)
        assert result["median"] == 15
        assert result["mean"] == 15
        assert result["min"] == 10
        assert result["max"] == 20

    def test_detect_outliers_with_outlier(self):
        """Test outlier detection when outlier present."""
        values = [10, 12, 11, 13, 100]  # 100 is outlier
        sample_indices = [0, 1, 2, 3, 4]
        consensus, outliers = detect_numeric_outliers(
            values, sample_indices, "test_field"
        )

        assert consensus == 12  # Median
        assert len(outliers) == 1
        assert outliers[0].outlier_value == 100

    def test_detect_outliers_no_outliers(self):
        """Test outlier detection when no outliers present."""
        values = [10, 11, 12, 13, 14]
        sample_indices = [0, 1, 2, 3, 4]
        consensus, outliers = detect_numeric_outliers(
            values, sample_indices, "test_field"
        )

        assert len(outliers) == 0


class TestCategoricalAggregation:
    """Tests for categorical aggregation."""

    def test_aggregate_categorical_unanimous(self):
        """Test categorical aggregation with unanimous agreement."""
        values = ["High", "High", "High", "High", "High"]
        mode, agreement = aggregate_categorical(values)
        assert mode == "High"
        assert agreement == 1.0

    def test_aggregate_categorical_majority(self):
        """Test categorical aggregation with majority."""
        values = ["High", "High", "High", "Medium", "Low"]
        mode, agreement = aggregate_categorical(values)
        assert mode == "High"
        assert agreement == 0.6

    def test_aggregate_categorical_split(self):
        """Test categorical aggregation with split."""
        values = ["High", "High", "Medium", "Medium", "Low"]
        mode, agreement = aggregate_categorical(values)
        assert mode in ["High", "Medium"]
        assert agreement == 0.4


class TestListAggregation:
    """Tests for list field aggregation."""

    def test_aggregate_lists_common_items(self):
        """Test list aggregation finds common items."""
        values = [
            ["risk1", "risk2", "risk3"],
            ["risk1", "risk2", "risk4"],
            ["risk1", "risk2", "risk5"],
        ]
        common, coverage = aggregate_list_fields(values)

        # risk1 and risk2 appear in all 3
        assert "risk1" in common
        assert "risk2" in common
        assert coverage > 0


class TestConfidenceComputation:
    """Tests for confidence score computation."""

    def test_numeric_confidence_high(self):
        """Test numeric confidence with low variation."""
        values = [10.0, 10.1, 10.0, 9.9, 10.0]
        conf = compute_field_confidence(values, "numeric")
        assert conf > 0.8

    def test_numeric_confidence_low(self):
        """Test numeric confidence with high variation."""
        values = [10.0, 50.0, 100.0, 5.0, 200.0]
        conf = compute_field_confidence(values, "numeric")
        assert conf < 0.5

    def test_categorical_confidence(self):
        """Test categorical confidence."""
        values = ["A", "A", "A", "B", "C"]
        conf = compute_field_confidence(values, "categorical")
        assert conf == 0.6

    def test_overall_confidence(self):
        """Test overall confidence computation."""
        field_conf = {
            "field1": 0.9,
            "field2": 0.8,
            "field3": 0.7,
        }
        overall = compute_overall_confidence(field_conf)
        assert 0.7 <= overall <= 0.9


class TestEarlyStopping:
    """Tests for early stopping logic."""

    def test_early_stop_triggers_on_agreement(self):
        """Test early stop triggers with agreement."""
        extractions = [
            {"risk": "Data quality", "severity": "High"},
            {"risk": "Data quality", "severity": "High"},
            {"risk": "Data quality", "severity": "High"},
        ]
        assert check_early_stop(extractions, threshold=0.6)

    def test_early_stop_not_triggered_on_disagreement(self):
        """Test early stop doesn't trigger with disagreement."""
        extractions = [
            {"risk": "Data quality", "severity": "High"},
            {"risk": "Resource issue", "severity": "Medium"},
            {"risk": "Schedule slip", "severity": "Low"},
        ]
        assert not check_early_stop(extractions, threshold=0.6)

    def test_early_stop_requires_minimum_samples(self):
        """Test early stop requires minimum samples."""
        extractions = [
            {"risk": "Data quality"},
            {"risk": "Data quality"},
        ]
        # Should not stop with only 2 samples
        assert not check_early_stop(extractions, threshold=0.6)
