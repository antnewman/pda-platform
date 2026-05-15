"""Regression tests for the four-tier escalation router (Layer 2 foundation).

Anchored to the architectural properties the paper §5.3 demands:

1. Each routing path is reachable from a clean input.
2. The OR fail-safe is exact: outliers and low confidence each
   independently trigger EXPERT_REQUIRED, even at perfect confidence
   or with no outliers respectively.
3. Threshold boundaries are predictable (exactly at threshold → which
   side?).
4. Plain-English reason strings are present on every outlier flag and
   on the decision itself.
5. Configurable thresholds work.
"""

from __future__ import annotations

import pytest

from agent_planning.escalation import (
    EscalationLevel,
    RoutingDecision,
    route,
)


# ─────────────────────────────────────────────────────────────────────────
# 1. Reachability — each routing path
# ─────────────────────────────────────────────────────────────────────────


class TestReachability:
    """Clean data + each confidence band reaches the expected tier."""

    CLEAN = [10.0, 10.1, 10.2, 10.0, 10.1, 10.2]

    def test_clean_data_high_confidence_routes_none(self):
        result = route(values=self.CLEAN, confidence=0.95)
        assert result.level == EscalationLevel.NONE
        assert not result.triggered_by_outliers
        assert not result.triggered_by_confidence

    def test_clean_data_medium_confidence_routes_spot_check(self):
        result = route(values=self.CLEAN, confidence=0.7)
        assert result.level == EscalationLevel.SPOT_CHECK
        assert not result.triggered_by_outliers
        assert not result.triggered_by_confidence

    def test_clean_data_low_confidence_routes_detailed(self):
        result = route(values=self.CLEAN, confidence=0.5)
        assert result.level == EscalationLevel.DETAILED_REVIEW
        assert not result.triggered_by_outliers
        assert not result.triggered_by_confidence

    def test_clean_data_very_low_confidence_routes_expert(self):
        result = route(values=self.CLEAN, confidence=0.2)
        assert result.level == EscalationLevel.EXPERT_REQUIRED
        assert not result.triggered_by_outliers
        assert result.triggered_by_confidence


# ─────────────────────────────────────────────────────────────────────────
# 2. OR fail-safe — the critical property
# ─────────────────────────────────────────────────────────────────────────


class TestOrFailsafe:
    """The OR condition is the architectural fail-safe: outliers OR low
    confidence each independently trigger escalation. Both can fire
    simultaneously."""

    def test_outlier_overrides_perfect_confidence(self):
        """The flagship test from paper §5.3. Six tight values plus one
        wild outlier triggers EXPERT_REQUIRED even at confidence = 1.0."""
        values = [10.0, 10.0, 10.1, 10.1, 10.2, 10.2, 100.0]
        result = route(values=values, confidence=1.0)
        assert result.level == EscalationLevel.EXPERT_REQUIRED
        assert result.triggered_by_outliers
        assert not result.triggered_by_confidence

    def test_low_confidence_overrides_no_outliers(self):
        """Confidence alone, with clean data, is sufficient to fire
        EXPERT_REQUIRED."""
        result = route(values=[5.0, 5.0, 5.0, 5.0, 5.0], confidence=0.1)
        assert result.level == EscalationLevel.EXPERT_REQUIRED
        assert not result.triggered_by_outliers
        assert result.triggered_by_confidence

    def test_both_triggers_fire_simultaneously(self):
        """If both triggers fire, both flags are true."""
        values = [10.0, 10.1, 10.0, 10.2, 10.0, 100.0]
        result = route(values=values, confidence=0.1)
        assert result.level == EscalationLevel.EXPERT_REQUIRED
        assert result.triggered_by_outliers
        assert result.triggered_by_confidence


# ─────────────────────────────────────────────────────────────────────────
# 3. Threshold boundaries
# ─────────────────────────────────────────────────────────────────────────


class TestThresholdBoundaries:
    """At-exactly-the-threshold semantics: thresholds are upper bounds
    (strict less-than) for each tier."""

    CLEAN = [10.0, 10.1, 10.2, 10.0, 10.1, 10.2]

    def test_at_spot_threshold_routes_none(self):
        """confidence == spot_threshold (0.8) → NONE, not SPOT_CHECK."""
        result = route(values=self.CLEAN, confidence=0.8)
        assert result.level == EscalationLevel.NONE

    def test_just_below_spot_threshold_routes_spot_check(self):
        result = route(values=self.CLEAN, confidence=0.79)
        assert result.level == EscalationLevel.SPOT_CHECK

    def test_at_detailed_threshold_routes_spot_check(self):
        """confidence == detailed_threshold (0.6) → SPOT_CHECK, not DETAILED_REVIEW."""
        result = route(values=self.CLEAN, confidence=0.6)
        assert result.level == EscalationLevel.SPOT_CHECK

    def test_at_expert_threshold_routes_detailed_review(self):
        """confidence == expert_threshold (0.4) → DETAILED_REVIEW, not EXPERT_REQUIRED."""
        result = route(values=self.CLEAN, confidence=0.4)
        assert result.level == EscalationLevel.DETAILED_REVIEW

    def test_just_below_expert_threshold_routes_expert(self):
        result = route(values=self.CLEAN, confidence=0.39)
        assert result.level == EscalationLevel.EXPERT_REQUIRED


# ─────────────────────────────────────────────────────────────────────────
# 4. Plain-English reasons
# ─────────────────────────────────────────────────────────────────────────


class TestReasons:
    """Both outlier flags and the routing decision itself carry
    plain-English reasons a reviewer can act on."""

    def test_decision_reason_names_both_triggers_when_outlier_fires(self):
        values = [10.0, 10.1, 10.0, 10.2, 10.0, 100.0]
        result = route(values=values, confidence=0.95)
        assert "outlier" in result.reason.lower()
        assert "OR fail-safe" in result.reason or "fail-safe" in result.reason.lower()

    def test_decision_reason_names_confidence_when_low(self):
        result = route(values=[5.0, 5.0, 5.0, 5.0, 5.0], confidence=0.1)
        assert "confidence" in result.reason.lower()
        assert "0.10" in result.reason or "0.1" in result.reason

    def test_each_outlier_has_a_reason_string(self):
        values = [10.0, 10.1, 10.0, 10.2, 10.0, 100.0]
        result = route(values=values, confidence=0.95, field_name="cost_estimate")
        assert len(result.outliers) >= 1
        for outlier in result.outliers:
            assert isinstance(outlier.reason, str)
            assert outlier.reason  # non-empty
            assert "cost_estimate" in outlier.reason

    def test_labels_appear_in_outlier_reasons_when_supplied(self):
        values = [10.0, 10.1, 10.0, 10.2, 10.0, 100.0]
        labels = ["agent_A", "agent_B", "agent_C", "agent_D", "agent_E", "agent_G"]
        result = route(values=values, confidence=0.95, labels=labels)
        # The outlier is at index 5 — label "agent_G"
        assert any("agent_G" in o.reason for o in result.outliers)


# ─────────────────────────────────────────────────────────────────────────
# 5. Configurable thresholds
# ─────────────────────────────────────────────────────────────────────────


class TestConfigurableThresholds:
    """Production deployments may want tighter or looser thresholds."""

    CLEAN = [10.0, 10.1, 10.2, 10.0, 10.1, 10.2]

    def test_tighter_thresholds_escalate_more(self):
        """A deployment that wants any output below 90% confidence to
        get human review can set spot_threshold = 0.9."""
        loose = route(values=self.CLEAN, confidence=0.85)
        tight = route(
            values=self.CLEAN,
            confidence=0.85,
            expert_threshold=0.6,
            detailed_threshold=0.7,
            spot_threshold=0.9,
        )
        assert loose.level == EscalationLevel.NONE
        assert tight.level == EscalationLevel.SPOT_CHECK

    def test_thresholds_used_recorded_in_decision(self):
        result = route(
            values=self.CLEAN,
            confidence=0.5,
            expert_threshold=0.2,
            detailed_threshold=0.5,
            spot_threshold=0.9,
        )
        assert result.thresholds_used == (0.2, 0.5, 0.9)


# ─────────────────────────────────────────────────────────────────────────
# 6. Input validation
# ─────────────────────────────────────────────────────────────────────────


class TestInputValidation:
    """The router rejects nonsensical inputs with a clear error."""

    def test_empty_values_rejected(self):
        with pytest.raises(ValueError, match="at least one value"):
            route(values=[], confidence=0.5)

    def test_confidence_above_one_rejected(self):
        with pytest.raises(ValueError, match=r"confidence must be"):
            route(values=[1.0], confidence=1.5)

    def test_confidence_below_zero_rejected(self):
        with pytest.raises(ValueError, match=r"confidence must be"):
            route(values=[1.0], confidence=-0.1)

    def test_non_increasing_thresholds_rejected(self):
        with pytest.raises(ValueError, match="strictly increasing"):
            route(
                values=[1.0],
                confidence=0.5,
                expert_threshold=0.5,
                detailed_threshold=0.4,
                spot_threshold=0.3,
            )


# ─────────────────────────────────────────────────────────────────────────
# 7. to_dict round-trip
# ─────────────────────────────────────────────────────────────────────────


class TestToDict:
    """The decision's to_dict shape is the contract for MCP tool
    responses and audit chain entries that include the decision."""

    def test_to_dict_is_json_serialisable(self):
        import json
        values = [10.0, 10.1, 10.0, 10.2, 10.0, 100.0]
        result = route(values=values, confidence=0.95)
        json.dumps(result.to_dict())

    def test_to_dict_preserves_all_fields(self):
        values = [10.0, 10.1, 10.0, 10.2, 10.0, 100.0]
        result = route(values=values, confidence=0.95, labels=None)
        d = result.to_dict()
        assert d["level"] == "EXPERT_REQUIRED"
        assert d["triggered_by_outliers"] is True
        assert d["triggered_by_confidence"] is False
        assert d["confidence"] == 0.95
        assert "consensus" in d
        assert len(d["outliers"]) >= 1
        for outlier in d["outliers"]:
            assert "field" in outlier
            assert "reason" in outlier


# ─────────────────────────────────────────────────────────────────────────
# 8. EscalationLevel enum
# ─────────────────────────────────────────────────────────────────────────


class TestEscalationLevel:
    """The level enum has descriptive strings and serialises cleanly."""

    def test_each_level_has_description(self):
        for level in EscalationLevel:
            assert level.description
            assert isinstance(level.description, str)

    def test_levels_are_string_serialisable(self):
        import json
        for level in EscalationLevel:
            assert json.dumps(level.value) == f'"{level.value}"'
