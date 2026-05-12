"""Regression tests for the generic AuditChain primitive.

Anchored to the bug classes the chain must close, matching the paper's
§11.3–§11.4 specification:

1. Tamper detection — modifying any past entry must be caught.
2. HMAC authenticity — verifying with the wrong key must fail.
3. Canonical serialisation — structurally identical inputs must always
   produce the same hash, regardless of dict ordering.
4. Consistency hash — the structural-consistency primitive (§11.4)
   must be stable across replays of structurally identical inputs.
"""

from __future__ import annotations

import pytest

from pm_data_tools.audit import (
    AuditChain,
    AuditEntry,
    canonical_serialise,
    compute_consistency_hash,
)


# ─────────────────────────────────────────────────────────────────────────
# 1. Tamper detection
# ─────────────────────────────────────────────────────────────────────────


class TestTamperDetection:
    """The chain detects modification of any past entry."""

    def test_clean_chain_verifies(self):
        chain = AuditChain()
        chain.record(
            input_data={"project": "PROJ-001", "amount": 5000},
            output_data={"verdict": "APPROVED"},
            decision="APPROVED",
        )
        chain.record(
            input_data={"project": "PROJ-002", "amount": 15000},
            output_data={"verdict": "REJECTED", "rule": "max_amount"},
            decision="REJECTED",
        )

        result = chain.verify()
        assert result.is_valid
        assert result.status == "VALID"

    def test_modified_decision_caught(self):
        """If anyone edits an entry's decision field after the fact, the
        recomputed hash mismatches the stored hash and verify() reports
        TAMPERED."""
        chain = AuditChain()
        chain.record(
            input_data={"amount": 15000},
            output_data={"verdict": "REJECTED"},
            decision="REJECTED",
        )
        # Tamper: change the decision in place
        chain._entries[0].decision = "APPROVED"  # noqa: SLF001

        result = chain.verify()
        assert not result.is_valid
        assert result.status == "TAMPERED"
        assert result.failed_at_index == 0

    def test_chain_link_break_caught(self):
        """If anyone re-orders or substitutes an entry such that the
        previous_entry_hash no longer matches, verify() catches it."""
        chain = AuditChain()
        chain.record(input_data={"i": 1}, output_data={"o": 1}, decision="A")
        chain.record(input_data={"i": 2}, output_data={"o": 2}, decision="B")

        # Tamper: corrupt the chain link on entry 1
        chain._entries[1].previous_entry_hash = "deadbeef" * 8  # noqa: SLF001

        result = chain.verify()
        assert not result.is_valid
        assert result.failed_at_index == 1

    def test_empty_chain_is_empty_not_valid(self):
        chain = AuditChain()
        result = chain.verify()
        assert result.status == "EMPTY"
        assert not result.is_valid

    def test_first_entry_has_no_previous_hash(self):
        chain = AuditChain()
        entry = chain.record(input_data={}, output_data={}, decision="X")
        assert entry.previous_entry_hash is None

    def test_second_entry_chains_to_first(self):
        chain = AuditChain()
        first = chain.record(input_data={"a": 1}, output_data={"b": 2}, decision="A")
        second = chain.record(input_data={"c": 3}, output_data={"d": 4}, decision="B")
        assert second.previous_entry_hash == first.entry_hash


# ─────────────────────────────────────────────────────────────────────────
# 2. HMAC authenticity
# ─────────────────────────────────────────────────────────────────────────


class TestHmacSigning:
    """A chain constructed with a signing key produces HMAC hashes; the
    chain cannot be verified with the wrong key (or with no key)."""

    def test_signed_chain_verifies_with_correct_key(self):
        chain = AuditChain(signing_key="correct-key")
        chain.record(input_data={"a": 1}, output_data={"b": 2}, decision="X")
        chain.record(input_data={"c": 3}, output_data={"d": 4}, decision="Y")

        exported = chain.export_json()
        reimported = AuditChain.from_json(exported, signing_key="correct-key")
        assert reimported.verify().is_valid

    def test_signed_chain_fails_verification_with_wrong_key(self):
        chain = AuditChain(signing_key="correct-key")
        chain.record(input_data={"a": 1}, output_data={"b": 2}, decision="X")

        exported = chain.export_json()
        reimported = AuditChain.from_json(exported, signing_key="wrong-key")
        result = reimported.verify()
        assert not result.is_valid
        assert result.status == "TAMPERED"

    def test_signed_chain_fails_verification_without_key(self):
        """Verifying a signed chain without the signing key cannot succeed
        because the recomputed plain SHA-256 differs from the stored HMAC."""
        chain = AuditChain(signing_key="some-key")
        chain.record(input_data={}, output_data={}, decision="X")

        exported = chain.export_json()
        reimported = AuditChain.from_json(exported)  # no signing_key
        assert not reimported.verify().is_valid

    def test_unsigned_chain_hash_differs_from_signed(self):
        """Same data, signed vs unsigned, must produce different hashes —
        proving the signing key is materially part of the integrity check."""
        unsigned = AuditChain()
        unsigned_entry = unsigned.record(input_data={"x": 1}, output_data={"y": 2}, decision="A")

        signed = AuditChain(signing_key="key")
        signed_entry = signed.record(input_data={"x": 1}, output_data={"y": 2}, decision="A")

        assert unsigned_entry.entry_hash != signed_entry.entry_hash


# ─────────────────────────────────────────────────────────────────────────
# 3. Canonical serialisation
# ─────────────────────────────────────────────────────────────────────────


class TestCanonicalSerialisation:
    """Structurally identical inputs always produce the same serialisation
    string, regardless of how the caller built the dict."""

    def test_key_order_does_not_matter(self):
        a = canonical_serialise({"x": 1, "y": 2, "z": 3})
        b = canonical_serialise({"z": 3, "y": 2, "x": 1})
        c = canonical_serialise({"y": 2, "z": 3, "x": 1})
        assert a == b == c

    def test_nested_dict_key_order_does_not_matter(self):
        a = canonical_serialise({"outer": {"x": 1, "y": 2}, "z": 3})
        b = canonical_serialise({"z": 3, "outer": {"y": 2, "x": 1}})
        assert a == b

    def test_whitespace_is_minimal(self):
        s = canonical_serialise({"x": 1, "y": [1, 2, 3]})
        # No spaces around colons or commas
        assert ": " not in s
        assert ", " not in s

    def test_two_chains_with_different_key_order_produce_same_hash(self):
        chain_a = AuditChain()
        a = chain_a.record(
            input_data={"project": "P", "amount": 100},
            output_data={"verdict": "OK", "score": 95},
            decision="OK",
        )

        chain_b = AuditChain()
        b = chain_b.record(
            input_data={"amount": 100, "project": "P"},
            output_data={"score": 95, "verdict": "OK"},
            decision="OK",
            timestamp=a.timestamp,  # force the same timestamp for parity
        )

        # The first entry has no previous_entry_hash, so the only sources
        # of variation are the dict orderings — which canonical_serialise
        # must absorb.
        assert a.input_hash == b.input_hash
        assert a.output_hash == b.output_hash
        assert a.entry_hash == b.entry_hash


# ─────────────────────────────────────────────────────────────────────────
# 4. Structural consistency hash (paper §11.4)
# ─────────────────────────────────────────────────────────────────────────


class TestConsistencyHash:
    """The §11.4 primitive: structurally identical decisions hash the
    same way; structurally different decisions hash differently."""

    def test_identical_decisions_hash_identically(self):
        d1 = {"verdict": "REJECTED", "critical_count": 3, "high_count": 1}
        d2 = {"verdict": "REJECTED", "critical_count": 3, "high_count": 1}
        assert compute_consistency_hash(d1) == compute_consistency_hash(d2)

    def test_key_order_does_not_affect_hash(self):
        d1 = {"verdict": "REJECTED", "critical_count": 3, "high_count": 1}
        d2 = {"high_count": 1, "critical_count": 3, "verdict": "REJECTED"}
        assert compute_consistency_hash(d1) == compute_consistency_hash(d2)

    def test_different_decisions_hash_differently(self):
        approved = {"verdict": "APPROVED", "critical_count": 0, "high_count": 0}
        rejected = {"verdict": "REJECTED", "critical_count": 3, "high_count": 1}
        assert compute_consistency_hash(approved) != compute_consistency_hash(rejected)

    def test_count_difference_detected(self):
        """The exact use case from the paper §11.4 LOGIC.md study: same
        verdict, different supporting counts, should be flagged as
        structurally different."""
        a = {"verdict": "REQUEST_CHANGES", "critical_count": 3, "high_count": 1}
        b = {"verdict": "REQUEST_CHANGES", "critical_count": 2, "high_count": 2}
        assert compute_consistency_hash(a) != compute_consistency_hash(b)


# ─────────────────────────────────────────────────────────────────────────
# 5. Export / import round-trip
# ─────────────────────────────────────────────────────────────────────────


class TestRoundTrip:
    """A chain that goes through export → JSON string → from_json
    re-verifies cleanly. The chain survives transport between processes."""

    def test_round_trip_preserves_validity(self):
        chain = AuditChain()
        chain.record(input_data={"a": 1}, output_data={"b": 2}, decision="A")
        chain.record(input_data={"c": 3}, output_data={"d": 4}, decision="B")
        chain.record(input_data={"e": 5}, output_data={"f": 6}, decision="C")

        json_str = chain.export_json()
        reimported = AuditChain.from_json(json_str)

        assert len(reimported) == 3
        assert reimported.verify().is_valid

    def test_round_trip_preserves_entry_fields(self):
        chain = AuditChain()
        original = chain.record(
            input_data={"x": 1},
            output_data={"y": 2},
            decision="DECIDE",
            action="loan_assessment",
            metadata={"model_version": "v1.2.0"},
        )

        json_str = chain.export_json()
        reimported = AuditChain.from_json(json_str)
        restored = reimported.entries[0]

        assert restored.action == original.action
        assert restored.decision == original.decision
        assert restored.metadata == original.metadata
        assert restored.input_hash == original.input_hash
        assert restored.output_hash == original.output_hash
        assert restored.entry_hash == original.entry_hash

    def test_from_json_rejects_non_array(self):
        with pytest.raises(ValueError, match="JSON array"):
            AuditChain.from_json('{"not": "an array"}')


# ─────────────────────────────────────────────────────────────────────────
# 6. Entry dataclass round-trip
# ─────────────────────────────────────────────────────────────────────────


class TestEntryDataclass:
    """The AuditEntry dataclass round-trips through to_dict / from_dict."""

    def test_entry_to_dict_and_back(self):
        chain = AuditChain()
        original = chain.record(input_data={}, output_data={}, decision="X")

        d = original.to_dict()
        restored = AuditEntry.from_dict(d)

        assert restored.action == original.action
        assert restored.decision == original.decision
        assert restored.input_hash == original.input_hash
        assert restored.output_hash == original.output_hash
        assert restored.entry_hash == original.entry_hash
        assert restored.timestamp == original.timestamp
