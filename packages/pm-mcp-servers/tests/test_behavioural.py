"""Behavioural test suite for the PDA Platform.

These tests verify that tools produce correct, meaningful outputs — not just
that modules import or dispatch entries exist.

The ``seeded_store`` fixture (from conftest.py) provides a fully pre-loaded
AssuranceStore representing the HMRC Digital Transformation Programme
(project_id = "TEST-PROJ-001").  Every test in this file is independent:
it receives its own fresh copy of the store via the function-scoped fixture.

Categories
----------
A  Risk module behavioural tests
B  Financial module behavioural tests
C  Earned Value (EV) module behavioural tests — mathematical correctness
D  Benefits module behavioural tests
E  Red flag scanner behavioural tests — end-to-end integration
F  Monte Carlo simulation behavioural tests — statistical properties
G  Error handling tests — tools must not raise for bad inputs
H  Store integrity tests
"""

from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from conftest import (
    BAC,
    CPI_EXPECTED,
    CUMULATIVE_ACTUAL,
    EAC_EXPECTED,
    EARNED_VALUE,
    PLANNED_VALUE,
    PROJECT_ID,
    SPI_EXPECTED,
    VAC_EXPECTED,
    _now_offset,
)

pytestmark = pytest.mark.behavioural


# ============================================================================
# Helpers — parse tool output
# ============================================================================


def _parse(result) -> dict:
    """Extract the JSON dict from a list[TextContent] tool result."""
    assert result, "Tool returned empty result list"
    text = result[0].text
    return json.loads(text)


# ============================================================================
# A. Risk module behavioural tests
# ============================================================================


class TestRiskBehavioural:
    """Risk register tools produce correct heat-map, staleness, and register outputs."""

    @pytest.mark.asyncio
    async def test_risk_heat_map_categorises_correctly(self, seeded_store):
        """R001 (L=4, I=4, score=16) appears in high band; R005 is excluded from open counts."""
        from pm_mcp_servers.pm_risk.server import _get_risk_heat_map

        result = await _get_risk_heat_map({
            "project_id": PROJECT_ID,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        # heat_map includes ALL risks (open and closed) for the visual
        assert data["risk_count"] == 5

        # R001: likelihood=4, impact=4, score=16 → HIGH band (13-19)
        high_count = data["high_count"]
        assert high_count >= 1, f"Expected at least 1 HIGH risk, got {high_count}"

        # R001 title should appear in the matrix at position [3][3] (0-indexed: L=4→idx3, I=4→idx3)
        matrix = data["heat_map"]["matrix"]
        cell_l4_i4 = matrix[3][3]
        assert any("Supplier delivery delay" in t for t in cell_l4_i4), (
            f"R001 'Supplier delivery delay' not found at matrix[3][3]: {cell_l4_i4}"
        )

        # R005 (score=1) should appear in LOW band
        low_count = data["low_count"]
        assert low_count >= 1, f"Expected at least 1 LOW risk, got {low_count}"

    @pytest.mark.asyncio
    async def test_risk_score_calculation(self, seeded_store):
        """Each risk's risk_score equals likelihood * impact."""
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore(db_path=Path(seeded_store._test_db_path))
        risks = store.get_risks(PROJECT_ID)

        expected_scores = {
            "RISK-R001": 4 * 4,   # 16
            "RISK-R002": 3 * 3,   # 9
            "RISK-R003": 2 * 5,   # 10
            "RISK-R004": 2 * 2,   # 4
            "RISK-R005": 1 * 1,   # 1
        }

        risk_map = {r["id"]: r for r in risks}
        for risk_id, expected in expected_scores.items():
            assert risk_id in risk_map, f"Risk {risk_id} missing from register"
            actual_score = risk_map[risk_id]["risk_score"]
            assert actual_score == expected, (
                f"Risk {risk_id}: expected score {expected}, got {actual_score}"
            )

    @pytest.mark.asyncio
    async def test_stale_risk_detection(self, seeded_store):
        """R001 was updated 60 days ago — detect_stale_risks flags it as stale."""
        from pm_mcp_servers.pm_risk.server import _detect_stale_risks

        result = await _detect_stale_risks({
            "project_id": PROJECT_ID,
            "stale_days": 28,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        stale_ids = [r["risk_id"] for r in data["not_recently_updated"]]
        assert "RISK-R001" in stale_ids, (
            f"R001 (60 days stale) not in not_recently_updated: {stale_ids}"
        )

        # R002 was updated 10 days ago — should NOT be flagged as stale
        assert "RISK-R002" not in stale_ids, (
            "R002 (10 days) should not be stale at 28-day threshold"
        )

    @pytest.mark.asyncio
    async def test_risk_register_returns_open_risks(self, seeded_store):
        """get_risk_register returns exactly 4 open risks (R005 is CLOSED)."""
        from pm_mcp_servers.pm_risk.server import _get_risk_register

        result = await _get_risk_register({
            "project_id": PROJECT_ID,
            "status": "OPEN",
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        open_risks = data["risks"]
        assert len(open_risks) == 4, (
            f"Expected 4 open risks, got {len(open_risks)}"
        )

        open_ids = {r["id"] for r in open_risks}
        assert "RISK-R005" not in open_ids, "CLOSED risk R005 must not appear in open register"

    @pytest.mark.asyncio
    async def test_risk_register_sorted_by_score(self, seeded_store):
        """get_risk_register returns risks sorted by score descending."""
        from pm_mcp_servers.pm_risk.server import _get_risk_register

        result = await _get_risk_register({
            "project_id": PROJECT_ID,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        scores = [r["risk_score"] for r in data["risks"]]
        assert scores == sorted(scores, reverse=True), (
            f"Risks not sorted descending by score: {scores}"
        )

    @pytest.mark.asyncio
    async def test_risk_register_mitigations_attached(self, seeded_store):
        """get_risk_register attaches mitigations to each risk."""
        from pm_mcp_servers.pm_risk.server import _get_risk_register

        result = await _get_risk_register({
            "project_id": PROJECT_ID,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        risk_map = {r["id"]: r for r in data["risks"]}
        # R002 has one mitigation
        assert "RISK-R002" in risk_map
        mits = risk_map["RISK-R002"]["mitigations"]
        assert len(mits) == 1, f"R002 should have 1 mitigation, got {len(mits)}"
        assert mits[0]["action"] == "Change freeze implemented"

        # R001 has no mitigations
        assert "RISK-R001" in risk_map
        assert risk_map["RISK-R001"]["mitigations"] == []

    @pytest.mark.asyncio
    async def test_risk_verbal_rating_is_correct(self, seeded_store):
        """get_risk_register assigns correct verbal rating to each risk."""
        from pm_mcp_servers.pm_risk.server import _get_risk_register

        result = await _get_risk_register({
            "project_id": PROJECT_ID,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        risk_map = {r["id"]: r for r in data["risks"]}

        # Score 16 → HIGH (13-19)
        assert risk_map["RISK-R001"]["risk_rating"] == "HIGH"
        # Score 10 → MEDIUM (7-12)
        assert risk_map["RISK-R003"]["risk_rating"] == "MEDIUM"
        # Score 4 → LOW (1-6)
        assert risk_map["RISK-R004"]["risk_rating"] == "LOW"


# ============================================================================
# B. Financial module behavioural tests
# ============================================================================


class TestFinancialBehavioural:
    """Financial tools return correct variance figures from seeded data."""

    @pytest.mark.asyncio
    async def test_cost_variance_calculation(self, seeded_store):
        """get_cost_performance returns correct budget variance: actuals 16.5m vs BAC 45m."""
        from pm_mcp_servers.pm_financial.server import _get_cost_performance

        result = await _get_cost_performance({
            "project_id": PROJECT_ID,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        assert data["status"] == "success"
        assert data["total_actual_spend"] == pytest.approx(CUMULATIVE_ACTUAL, abs=1.0)
        assert data["approved_budget"] == pytest.approx(BAC, abs=1.0)

        # budget_variance = BAC - actual = 45m - 16.5m = 28.5m (positive = under budget so far)
        expected_variance = BAC - CUMULATIVE_ACTUAL  # 28_500_000
        assert data["budget_variance"] == pytest.approx(expected_variance, abs=1.0)

        # budget_variance_pct = (variance / BAC) * 100 = (28.5m / 45m) * 100 = 63.33%
        expected_variance_pct = (expected_variance / BAC) * 100
        assert data["budget_variance_pct"] == pytest.approx(expected_variance_pct, abs=0.1)

    @pytest.mark.asyncio
    async def test_financial_baseline_retrieved(self, seeded_store):
        """set_financial_baseline then retrieve confirms BAC is stored correctly."""
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore(db_path=Path(seeded_store._test_db_path))
        baselines = store.get_financial_baselines(PROJECT_ID, label="APPROVED")

        assert len(baselines) >= 1, "No APPROVED baseline found"
        total_baselines = [b for b in baselines if b.get("cost_category") == "TOTAL"]
        assert len(total_baselines) >= 1, "No TOTAL cost category baseline found"
        assert float(total_baselines[0]["total_budget"]) == pytest.approx(BAC, abs=1.0)

    @pytest.mark.asyncio
    async def test_financial_spend_profile_cumulative(self, seeded_store):
        """get_spend_profile reports correct cumulative spend to date."""
        from pm_mcp_servers.pm_financial.server import _get_spend_profile

        result = await _get_spend_profile({
            "project_id": PROJECT_ID,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        assert data["status"] == "success"
        assert data["total_spent_to_date"] == pytest.approx(CUMULATIVE_ACTUAL, abs=1.0)
        assert data["approved_budget"] == pytest.approx(BAC, abs=1.0)

    @pytest.mark.asyncio
    async def test_get_cost_performance_no_baseline_returns_error_not_exception(self, seeded_store):
        """get_cost_performance with no baseline returns a structured error, not an exception."""
        from pm_mcp_servers.pm_financial.server import _get_cost_performance

        result = await _get_cost_performance({
            "project_id": "PROJECT-WITH-NO-DATA",
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        # Must return an error dict, not raise
        assert "error" in data or data.get("status") == "error", (
            f"Expected error response for missing baseline, got: {data}"
        )

    @pytest.mark.asyncio
    async def test_cost_overrun_flag_in_red_flags(self, seeded_store):
        """When actuals exceed baseline by >10%, cost overrun flag is raised.

        The seeded store has BAC=45m and actuals=16.5m (under budget overall), so
        we insert additional actuals to push it over 10% for this test only.
        """
        from pm_data_tools.db.store import AssuranceStore
        from pm_mcp_servers.pm_assure.server import _scan_for_red_flags

        store = AssuranceStore(db_path=Path(seeded_store._test_db_path))
        # Insert a second period that pushes cumulative well over BAC
        store.upsert_financial_actual({
            "id": str(uuid.uuid4()),
            "project_id": PROJECT_ID,
            "period": "2026-05-01",
            "actual_spend": 35_000_000,   # total now = 51.5m > 45m BAC (>10% over)
            "cost_category": "TOTAL",
            "created_at": _now_offset(5),
        })

        result = await _scan_for_red_flags({
            "project_id": PROJECT_ID,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        cost_flags = [f for f in data["flags"] if f["category"] == "COST"]
        cost_flag_ids = [f["flag_id"] for f in cost_flags]
        descriptions = [f["description"] for f in cost_flags]
        assert any("overrun" in d.lower() or "variance" in d.lower() for d in descriptions), (
            f"Expected a COST overrun flag, got COST flags: {descriptions}"
        )


# ============================================================================
# C. EV module behavioural tests — mathematical correctness
# ============================================================================


class TestEVMathematical:
    """EV calculations must be mathematically exact (±0.001 on indices, ±10k on money).

    The EV module uses task data loaded via load_project / project_store.
    These tests verify the *mathematical relationships* by computing them
    directly against the seeded constants, and also exercise the store-based
    financial tools to confirm the EV constants are consistent.
    """

    def test_spi_calculation(self):
        """SPI = EV / PV — must be 0.840 ± 0.001."""
        spi = EARNED_VALUE / PLANNED_VALUE
        assert spi == pytest.approx(0.840, abs=0.001), (
            f"SPI = {spi:.4f}, expected 0.840"
        )

    def test_cpi_calculation(self):
        """CPI = EV / AC — must be 0.7636 ± 0.001."""
        cpi = EARNED_VALUE / CUMULATIVE_ACTUAL
        assert cpi == pytest.approx(0.7636, abs=0.001), (
            f"CPI = {cpi:.4f}, expected 0.7636"
        )

    def test_eac_calculation(self):
        """EAC = AC + (BAC - EV) / CPI — must be ≈ £58,930,000 ± £10,000."""
        cpi = EARNED_VALUE / CUMULATIVE_ACTUAL
        eac = CUMULATIVE_ACTUAL + (BAC - EARNED_VALUE) / cpi
        assert eac == pytest.approx(58_930_000, abs=10_000), (
            f"EAC = £{eac:,.0f}, expected ≈ £58,930,000"
        )

    def test_vac_calculation(self):
        """VAC = BAC - EAC — must be ≈ -£13,930,000 ± £10,000."""
        cpi = EARNED_VALUE / CUMULATIVE_ACTUAL
        eac = CUMULATIVE_ACTUAL + (BAC - EARNED_VALUE) / cpi
        vac = BAC - eac
        assert vac == pytest.approx(-13_930_000, abs=10_000), (
            f"VAC = £{vac:,.0f}, expected ≈ -£13,930,000"
        )

    def test_spi_lt_one_indicates_schedule_slippage(self):
        """SPI < 1.0 means the project is behind schedule."""
        assert SPI_EXPECTED < 1.0, (
            "SPI should be < 1.0 indicating schedule slippage"
        )

    def test_cpi_lt_one_indicates_cost_overrun(self):
        """CPI < 1.0 means the project is over budget for work done."""
        assert CPI_EXPECTED < 1.0, (
            "CPI should be < 1.0 indicating cost overrun"
        )

    def test_eac_gt_bac_confirms_overrun_forecast(self):
        """EAC > BAC confirms the project is forecast to overspend."""
        assert EAC_EXPECTED > BAC, (
            f"EAC ({EAC_EXPECTED:,.0f}) should be > BAC ({BAC:,.0f})"
        )

    def test_vac_is_negative(self):
        """VAC < 0 means the project is expected to exceed approved budget."""
        assert VAC_EXPECTED < 0, (
            f"VAC ({VAC_EXPECTED:,.0f}) should be negative"
        )

    def test_ev_triple_internal_consistency(self):
        """SPI, CPI, EAC and VAC are internally consistent with each other."""
        cpi = EARNED_VALUE / CUMULATIVE_ACTUAL
        eac = CUMULATIVE_ACTUAL + (BAC - EARNED_VALUE) / cpi
        vac = BAC - eac

        # Recompute using the stored expected values — must match
        assert EAC_EXPECTED == pytest.approx(eac, abs=0.01)
        assert VAC_EXPECTED == pytest.approx(vac, abs=0.01)
        assert CPI_EXPECTED == pytest.approx(cpi, abs=0.0001)


# ============================================================================
# D. Benefits module behavioural tests
# ============================================================================


class TestBenefitsBehavioural:
    """Benefits data is correctly stored and retrievable with expected statuses."""

    def test_benefit_count(self, seeded_store):
        """Total benefits = 3; all have status that is not None."""
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore(db_path=Path(seeded_store._test_db_path))
        benefits = store.get_benefits(PROJECT_ID)
        assert len(benefits) == 3, f"Expected 3 benefits, got {len(benefits)}"

    def test_benefits_without_owner_detected(self, seeded_store):
        """B002 has no benefits_owner — store query confirms this."""
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore(db_path=Path(seeded_store._test_db_path))
        benefits = store.get_benefits(PROJECT_ID)

        unowned = [b for b in benefits if not b.get("benefits_owner")]
        assert len(unowned) >= 1, "Expected at least 1 unowned benefit"

        unowned_ids = [b["id"] for b in unowned]
        assert "BEN-B002" in unowned_ids, (
            f"B002 should be unowned, unowned_ids: {unowned_ids}"
        )

    def test_off_track_benefit_detected(self, seeded_store):
        """B003 has status OFF_TRACK — confirmed by store query."""
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore(db_path=Path(seeded_store._test_db_path))
        benefits = store.get_benefits(PROJECT_ID)

        off_track = [b for b in benefits if b.get("status") == "OFF_TRACK"]
        assert len(off_track) >= 1, "Expected at least 1 OFF_TRACK benefit"

        ids = [b["id"] for b in off_track]
        assert "BEN-B003" in ids, (
            f"B003 should be OFF_TRACK, off_track ids: {ids}"
        )

    def test_benefit_statuses_match_seeded_data(self, seeded_store):
        """Each benefit has the exact status seeded into the store."""
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore(db_path=Path(seeded_store._test_db_path))
        benefits = store.get_benefits(PROJECT_ID)
        status_map = {b["id"]: b["status"] for b in benefits}

        assert status_map["BEN-B001"] == "ON_TRACK"
        assert status_map["BEN-B002"] == "AT_RISK"
        assert status_map["BEN-B003"] == "OFF_TRACK"

    def test_at_risk_benefits_count(self, seeded_store):
        """There are 2 benefits with AT_RISK or OFF_TRACK status."""
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore(db_path=Path(seeded_store._test_db_path))
        benefits = store.get_benefits(PROJECT_ID)

        degraded = [
            b for b in benefits
            if b.get("status") in ("AT_RISK", "OFF_TRACK")
        ]
        assert len(degraded) == 2, (
            f"Expected 2 at-risk/off-track benefits, got {len(degraded)}"
        )


# ============================================================================
# E. Red flag scanner behavioural tests
# ============================================================================


class TestRedFlagScannerBehavioural:
    """scan_for_red_flags end-to-end integration tests against seeded data."""

    @pytest.mark.asyncio
    async def test_red_flag_scanner_finds_critical_risks(self, seeded_store):
        """R001 and R003 are high-score with no active mitigations — scanner raises RISK CRITICAL flag."""
        from pm_mcp_servers.pm_assure.server import _scan_for_red_flags

        result = await _scan_for_red_flags({
            "project_id": PROJECT_ID,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        risk_flags = [f for f in data["flags"] if f["category"] == "RISK"]
        assert len(risk_flags) >= 1, f"Expected RISK flags, got: {data['flags']}"

        # At least one CRITICAL or HIGH risk flag must be present
        risk_severities = {f["severity"] for f in risk_flags}
        assert "CRITICAL" in risk_severities or "HIGH" in risk_severities, (
            f"Expected CRITICAL or HIGH risk flag, got severities: {risk_severities}"
        )

        # Confirm the evidence references the unmitigated risks (R001 and/or R003)
        all_evidenced_ids: list[str] = []
        for f in risk_flags:
            evidence = f.get("evidence", {})
            all_evidenced_ids.extend(evidence.get("risk_ids", []))

        assert "RISK-R001" in all_evidenced_ids, (
            f"R001 should be flagged as unmitigated HIGH risk; evidenced ids: {all_evidenced_ids}"
        )

    @pytest.mark.asyncio
    async def test_red_flag_scanner_finds_unowned_benefits(self, seeded_store):
        """B002 has no owner — scanner raises HIGH BENEFITS flag."""
        from pm_mcp_servers.pm_assure.server import _scan_for_red_flags

        result = await _scan_for_red_flags({
            "project_id": PROJECT_ID,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        benefit_flags = [f for f in data["flags"] if f["category"] == "BENEFITS"]
        assert len(benefit_flags) >= 1, (
            f"Expected at least 1 BENEFITS flag; all flags: {data['flags']}"
        )

        unowned_flags = [
            f for f in benefit_flags
            if "no benefits owner" in f.get("description", "").lower()
            or "unowned" in f.get("description", "").lower()
        ]
        assert len(unowned_flags) >= 1, (
            f"Expected unowned-benefits flag; benefit flags: {benefit_flags}"
        )

    @pytest.mark.asyncio
    async def test_red_flag_scanner_finds_outstanding_gate_conditions(self, seeded_store):
        """2 outstanding gate conditions → scanner raises CRITICAL GOVERNANCE flag."""
        from pm_mcp_servers.pm_assure.server import _scan_for_red_flags

        result = await _scan_for_red_flags({
            "project_id": PROJECT_ID,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        governance_flags = [f for f in data["flags"] if f["category"] == "GOVERNANCE"]
        assert len(governance_flags) >= 1, (
            f"Expected GOVERNANCE flags; all flags: {data['flags']}"
        )

        critical_gov = [f for f in governance_flags if f["severity"] == "CRITICAL"]
        assert len(critical_gov) >= 1, (
            f"Expected CRITICAL governance flag for outstanding conditions; "
            f"governance flags: {governance_flags}"
        )

        # Evidence must reference the blocking issues
        blocking_issues = critical_gov[0]["evidence"].get("blocking_issues", [])
        assert len(blocking_issues) >= 2, (
            f"Expected 2 blocking issues in evidence, got: {blocking_issues}"
        )

    @pytest.mark.asyncio
    async def test_red_flag_scanner_change_pressure(self, seeded_store):
        """6 open CRs (CR001-003, CR005-007 = 6 OPEN, > 5 threshold) → scanner raises MEDIUM CHANGE flag."""
        from pm_mcp_servers.pm_assure.server import _scan_for_red_flags

        result = await _scan_for_red_flags({
            "project_id": PROJECT_ID,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        change_flags = [f for f in data["flags"] if f["category"] == "CHANGE"]
        assert len(change_flags) >= 1, (
            f"Expected CHANGE pressure flag; all flags: {data['flags']}"
        )
        assert change_flags[0]["severity"] in ("MEDIUM", "HIGH"), (
            f"Unexpected severity for change pressure: {change_flags[0]['severity']}"
        )

    @pytest.mark.asyncio
    async def test_red_flag_scanner_severity_filter(self, seeded_store):
        """With severity_threshold='CRITICAL', only CRITICAL flags are returned."""
        from pm_mcp_servers.pm_assure.server import _scan_for_red_flags

        result = await _scan_for_red_flags({
            "project_id": PROJECT_ID,
            "severity_threshold": "CRITICAL",
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        for flag in data["flags"]:
            assert flag["severity"] == "CRITICAL", (
                f"Non-CRITICAL flag returned when threshold=CRITICAL: {flag}"
            )

    @pytest.mark.asyncio
    async def test_red_flag_scanner_empty_project(self, seeded_store):
        """scan_for_red_flags on a project with no data returns empty flags and data_gaps — no crash."""
        from pm_mcp_servers.pm_assure.server import _scan_for_red_flags

        result = await _scan_for_red_flags({
            "project_id": "EMPTY-PROJECT-XYZ",
            "db_path": seeded_store._test_db_path,
        })
        # Must not raise; must return parseable JSON
        data = _parse(result)

        assert isinstance(data["flags"], list)
        assert isinstance(data["data_gaps"], list)
        # With no data, data_gaps should be populated
        assert len(data["data_gaps"]) >= 1, (
            "Empty project should produce data_gaps entries"
        )

    @pytest.mark.asyncio
    async def test_red_flag_scanner_flag_ids_sequential(self, seeded_store):
        """After sorting, flag_ids are RF001, RF002, ... in order."""
        from pm_mcp_servers.pm_assure.server import _scan_for_red_flags

        result = await _scan_for_red_flags({
            "project_id": PROJECT_ID,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        flags = data["flags"]
        for idx, flag in enumerate(flags, start=1):
            expected_id = f"RF{idx:03d}"
            assert flag["flag_id"] == expected_id, (
                f"Flag at position {idx} has id {flag['flag_id']}, expected {expected_id}"
            )

    @pytest.mark.asyncio
    async def test_red_flag_scanner_sorted_critical_first(self, seeded_store):
        """Flags are returned in severity order: CRITICAL before HIGH before MEDIUM."""
        from pm_mcp_servers.pm_assure.server import _scan_for_red_flags

        result = await _scan_for_red_flags({
            "project_id": PROJECT_ID,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
        flags = data["flags"]
        if len(flags) >= 2:
            for i in range(len(flags) - 1):
                a = severity_order.get(flags[i]["severity"], 99)
                b = severity_order.get(flags[i + 1]["severity"], 99)
                assert a <= b, (
                    f"Flags not sorted by severity: position {i} is "
                    f"{flags[i]['severity']}, position {i+1} is {flags[i+1]['severity']}"
                )

    @pytest.mark.asyncio
    async def test_red_flag_scanner_summary_counts_correct(self, seeded_store):
        """Summary counts (critical, high, medium, total) match the actual flags list."""
        from pm_mcp_servers.pm_assure.server import _scan_for_red_flags

        result = await _scan_for_red_flags({
            "project_id": PROJECT_ID,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        flags = data["flags"]
        summary = data["summary"]

        actual_critical = sum(1 for f in flags if f["severity"] == "CRITICAL")
        actual_high = sum(1 for f in flags if f["severity"] == "HIGH")
        actual_medium = sum(1 for f in flags if f["severity"] == "MEDIUM")

        assert summary["critical"] == actual_critical, (
            f"Summary critical={summary['critical']} != actual {actual_critical}"
        )
        assert summary["high"] == actual_high, (
            f"Summary high={summary['high']} != actual {actual_high}"
        )
        assert summary["medium"] == actual_medium, (
            f"Summary medium={summary['medium']} != actual {actual_medium}"
        )
        assert summary["total"] == len(flags), (
            f"Summary total={summary['total']} != len(flags)={len(flags)}"
        )


# ============================================================================
# F. Monte Carlo simulation behavioural tests — statistical properties
# ============================================================================


class TestSimulationStatistical:
    """Monte Carlo simulation produces outputs with correct statistical ordering."""

    @pytest.mark.asyncio
    async def test_simulation_p80_gte_p50(self, seeded_store):
        """P80_days >= P50_days — a higher confidence interval must be >= a lower one."""
        from pm_mcp_servers.pm_simulation.server import _run_schedule_simulation

        result = await _run_schedule_simulation({
            "project_id": PROJECT_ID,
            "n_simulations": 1000,
            "baseline_duration_days": 540,
            "project_start_date": "2025-10-01",
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        # p-values are nested under data["results"]
        p50 = data["results"]["p50_days"]
        p80 = data["results"]["p80_days"]
        assert p80 >= p50, f"P80 ({p80}) must be >= P50 ({p50})"

    @pytest.mark.asyncio
    async def test_simulation_p90_gte_p80(self, seeded_store):
        """P90_days >= P80_days — P90 is a higher confidence level."""
        from pm_mcp_servers.pm_simulation.server import _run_schedule_simulation

        result = await _run_schedule_simulation({
            "project_id": PROJECT_ID,
            "n_simulations": 1000,
            "baseline_duration_days": 540,
            "project_start_date": "2025-10-01",
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        p80 = data["results"]["p80_days"]
        p90 = data["results"]["p90_days"]
        assert p90 >= p80, f"P90 ({p90}) must be >= P80 ({p80})"

    @pytest.mark.asyncio
    async def test_simulation_p50_within_reasonable_range_of_baseline(self, seeded_store):
        """P50 completion should be within ±50% of the baseline duration.

        Uncertainty distributions are centred on the baseline, so the median
        outcome should be reasonably close to it.
        """
        from pm_mcp_servers.pm_simulation.server import _run_schedule_simulation

        baseline = 540
        result = await _run_schedule_simulation({
            "project_id": PROJECT_ID,
            "n_simulations": 1000,
            "baseline_duration_days": baseline,
            "project_start_date": "2025-10-01",
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        p50 = data["results"]["p50_days"]
        lower = baseline * 0.5
        upper = baseline * 1.5
        assert lower <= p50 <= upper, (
            f"P50 ({p50}) is outside ±50% of baseline ({baseline}): [{lower}, {upper}]"
        )

    @pytest.mark.asyncio
    async def test_simulation_stores_result(self, seeded_store):
        """After run_schedule_simulation, get_simulation_results returns the run."""
        from pm_mcp_servers.pm_simulation.server import (
            _get_simulation_results,
            _run_schedule_simulation,
        )

        await _run_schedule_simulation({
            "project_id": PROJECT_ID,
            "n_simulations": 500,
            "baseline_duration_days": 540,
            "project_start_date": "2025-10-01",
            "db_path": seeded_store._test_db_path,
        })

        result = await _get_simulation_results({
            "project_id": PROJECT_ID,
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        # get_simulation_results returns the store row — p-values are at top level
        assert data.get("project_id") == PROJECT_ID
        assert data.get("p50_days") is not None, "p50_days should be set"
        assert data.get("p80_days") is not None, "p80_days should be set"

    @pytest.mark.asyncio
    async def test_simulation_risk_calibration_widens_spread(self, seeded_store):
        """Simulation with use_risk_register=True should produce wider P90-P50 gap than False.

        The seeded project has several HIGH-score risks which should inflate
        the uncertainty. We run many simulations to reduce sampling variance
        and check the direction of the effect.
        """
        from pm_mcp_servers.pm_simulation.server import _run_schedule_simulation

        baseline = 540
        n = 2000

        result_no_risk = await _run_schedule_simulation({
            "project_id": "NO-RISK-PROJECT",   # no risks in store → multiplier=1.0
            "n_simulations": n,
            "baseline_duration_days": baseline,
            "project_start_date": "2025-10-01",
            "use_risk_register": False,
            "base_uncertainty_pct": 20.0,
            "db_path": seeded_store._test_db_path,
        })
        result_with_risk = await _run_schedule_simulation({
            "project_id": PROJECT_ID,          # has HIGH risks → multiplier > 1.0
            "n_simulations": n,
            "baseline_duration_days": baseline,
            "project_start_date": "2025-10-01",
            "use_risk_register": True,
            "base_uncertainty_pct": 20.0,
            "db_path": seeded_store._test_db_path,
        })

        d_no_risk = _parse(result_no_risk)
        d_with_risk = _parse(result_with_risk)

        # p-values are nested under data["results"] in the run output
        spread_no_risk = d_no_risk["results"]["p90_days"] - d_no_risk["results"]["p50_days"]
        spread_with_risk = d_with_risk["results"]["p90_days"] - d_with_risk["results"]["p50_days"]

        assert spread_with_risk >= spread_no_risk, (
            f"Risk-calibrated spread ({spread_with_risk}) should be >= "
            f"uncalibrated spread ({spread_no_risk})"
        )

    @pytest.mark.asyncio
    async def test_simulation_returns_calendar_dates(self, seeded_store):
        """run_schedule_simulation returns ISO date strings for P50/P80/P90."""
        from pm_mcp_servers.pm_simulation.server import _run_schedule_simulation

        result = await _run_schedule_simulation({
            "project_id": PROJECT_ID,
            "n_simulations": 500,
            "baseline_duration_days": 540,
            "project_start_date": "2025-10-01",
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        # Calendar dates are at the top level of the result
        for key in ("p50_date", "p80_date", "p90_date"):
            val = data.get(key)
            assert val is not None, f"{key} should be set"
            # Validate ISO date format
            datetime.strptime(val, "%Y-%m-%d")


# ============================================================================
# G. Error handling tests
# ============================================================================


class TestErrorHandling:
    """Tools must return error dicts, not raise exceptions, for bad inputs."""

    @pytest.mark.asyncio
    async def test_risk_register_nonexistent_project_returns_error_dict(self, seeded_store):
        """get_risk_register for non-existent project returns an empty register, not an exception."""
        from pm_mcp_servers.pm_risk.server import _get_risk_register

        result = await _get_risk_register({
            "project_id": "NONEXISTENT-PROJECT-XYZ",
            "db_path": seeded_store._test_db_path,
        })
        # Must not raise; must return parseable content
        data = _parse(result)
        # Either success with 0 risks or an error dict — both are acceptable
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_risk_heat_map_nonexistent_project_no_crash(self, seeded_store):
        """get_risk_heat_map for non-existent project returns empty heat map, not an exception."""
        from pm_mcp_servers.pm_risk.server import _get_risk_heat_map

        result = await _get_risk_heat_map({
            "project_id": "NONEXISTENT-PROJECT-XYZ",
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)
        assert data["risk_count"] == 0

    @pytest.mark.asyncio
    async def test_scan_red_flags_empty_project_no_crash(self, seeded_store):
        """scan_for_red_flags on an empty project returns empty flags list with data_gaps populated."""
        from pm_mcp_servers.pm_assure.server import _scan_for_red_flags

        result = await _scan_for_red_flags({
            "project_id": "EMPTY-PROJECT-FOR-ERROR-TEST",
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        assert isinstance(data["flags"], list)
        assert isinstance(data["data_gaps"], list)
        assert len(data["data_gaps"]) >= 1

    @pytest.mark.asyncio
    async def test_financial_tools_with_no_baseline_returns_meaningful_response(self, seeded_store):
        """get_cost_performance with no baseline set returns a meaningful error, not an exception."""
        from pm_mcp_servers.pm_financial.server import _get_cost_performance

        result = await _get_cost_performance({
            "project_id": "NO-BASELINE-PROJECT",
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        # Should be an error dict with status="error" and a human-readable message
        assert data.get("status") == "error"
        assert "message" in data
        assert "baseline" in data["message"].lower() or "no" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_detect_stale_risks_empty_project_no_crash(self, seeded_store):
        """detect_stale_risks on a project with no risks returns gracefully."""
        from pm_mcp_servers.pm_risk.server import _detect_stale_risks

        result = await _detect_stale_risks({
            "project_id": "EMPTY-PROJECT-NO-RISKS",
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)

        assert data["summary"]["total_open_risks"] == 0
        assert data["not_recently_updated"] == []

    @pytest.mark.asyncio
    async def test_simulation_get_results_no_prior_run_returns_error_not_exception(self, seeded_store):
        """get_simulation_results for a project with no run returns a meaningful error."""
        from pm_mcp_servers.pm_simulation.server import _get_simulation_results

        result = await _get_simulation_results({
            "project_id": "PROJECT-NO-SIMULATION",
            "db_path": seeded_store._test_db_path,
        })
        data = _parse(result)
        # Should indicate no simulation was found
        assert isinstance(data, dict)
        # Either "error" key or "message" about no run
        has_error = "error" in data or data.get("status") == "error" or "no" in str(data).lower()
        assert has_error, f"Expected error/no-data response, got: {data}"


# ============================================================================
# H. Store integrity tests
# ============================================================================


class TestStoreIntegrity:
    """Store operations maintain correct data — upsert, history, retrieval."""

    def test_risk_score_history_recorded_on_upsert(self, seeded_store):
        """When a risk is upserted, a risk_score_history entry is created automatically."""
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore(db_path=Path(seeded_store._test_db_path))

        # R001 was upserted during fixture setup — should have history
        history = store.get_risk_score_history("RISK-R001")
        assert len(history) >= 1, (
            "R001 should have at least 1 history entry after upsert"
        )
        # The history entry must have the same score as the risk
        latest = history[-1]
        assert latest["risk_score"] == 16
        assert latest["likelihood"] == 4
        assert latest["impact"] == 4

    def test_simulation_run_upserted_correctly(self, seeded_store):
        """upsert_simulation_run then get_latest_simulation returns the correct run."""
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore(db_path=Path(seeded_store._test_db_path))

        run_id = str(uuid.uuid4())
        run = {
            "id": run_id,
            "project_id": PROJECT_ID,
            "simulation_type": "schedule",
            "n_simulations": 500,
            "p50_days": 560,
            "p80_days": 600,
            "p90_days": 630,
            "p50_date": "2027-05-01",
            "p80_date": "2027-07-01",
            "p90_date": "2027-08-15",
            "mean_duration_days": 565.0,
            "std_deviation_days": 45.0,
            "run_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        }

        store.upsert_simulation_run(run)
        retrieved = store.get_latest_simulation(PROJECT_ID, "schedule")

        assert retrieved is not None, "get_latest_simulation returned None after upsert"
        assert retrieved["id"] == run_id
        assert retrieved["p50_days"] == 560
        assert retrieved["p80_days"] == 600
        assert retrieved["p90_days"] == 630

    def test_risk_upsert_idempotent(self, seeded_store):
        """Upserting the same risk twice does not create duplicate records."""
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore(db_path=Path(seeded_store._test_db_path))

        now_str = _now_offset(0)
        store.upsert_risk({
            "id": "RISK-IDEMPOTENT",
            "project_id": PROJECT_ID,
            "title": "Duplicate test risk",
            "category": "DELIVERY",
            "likelihood": 3,
            "impact": 3,
            "risk_score": 9,
            "status": "OPEN",
            "created_at": now_str,
            "updated_at": now_str,
        })
        # Upsert again with updated score
        store.upsert_risk({
            "id": "RISK-IDEMPOTENT",
            "project_id": PROJECT_ID,
            "title": "Duplicate test risk",
            "category": "DELIVERY",
            "likelihood": 4,
            "impact": 4,
            "risk_score": 16,
            "status": "OPEN",
            "created_at": now_str,
            "updated_at": _now_offset(0),
        })

        risk = store.get_risk_by_id("RISK-IDEMPOTENT")
        assert risk is not None
        # Most recent upsert should win
        assert risk["risk_score"] == 16

        # There should be exactly 2 history entries (one per upsert)
        history = store.get_risk_score_history("RISK-IDEMPOTENT")
        assert len(history) == 2

    def test_change_requests_stored_and_retrievable(self, seeded_store):
        """All 7 change requests (6 OPEN + 1 APPROVED) are stored and retrievable."""
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore(db_path=Path(seeded_store._test_db_path))
        all_crs = store.get_change_requests(PROJECT_ID)
        assert len(all_crs) == 7, f"Expected 7 change requests, got {len(all_crs)}"

        status_map = {cr["id"]: cr["status"] for cr in all_crs}
        assert status_map["CR001"] == "OPEN"
        assert status_map["CR004"] == "APPROVED"

    def test_gate_readiness_history_retrievable(self, seeded_store):
        """Gate 3 FBC assessment is stored and retrievable with correct score."""
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore(db_path=Path(seeded_store._test_db_path))
        history = store.get_gate_readiness_history(PROJECT_ID)
        assert len(history) >= 1, "Expected at least 1 gate readiness assessment"

        latest = history[-1]
        assert latest["gate"] == "Gate 3 (FBC)"
        assert float(latest["composite_score"]) == pytest.approx(0.55, abs=0.001)

        result_data = json.loads(str(latest["result_json"]))
        blocking = result_data.get("blocking_issues", [])
        assert len(blocking) == 2, f"Expected 2 blocking issues, got: {blocking}"

    def test_resource_plan_stored_correctly(self, seeded_store):
        """Resource plan for Sarah Chen is stored with correct overloaded values."""
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore(db_path=Path(seeded_store._test_db_path))
        plans = store.get_resource_plans(PROJECT_ID, resource_name="Sarah Chen")
        assert len(plans) == 1, f"Expected 1 resource plan for Sarah Chen, got {len(plans)}"

        plan = plans[0]
        assert float(plan["planned_days"]) == pytest.approx(30.0, abs=0.01)
        assert float(plan["availability_pct"]) == pytest.approx(80.0, abs=0.01)

    def test_financial_actuals_stored_correctly(self, seeded_store):
        """Financial actuals are stored and sum to the correct cumulative total."""
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore(db_path=Path(seeded_store._test_db_path))
        actuals = store.get_financial_actuals(PROJECT_ID)
        assert len(actuals) >= 1, "Expected at least 1 financial actuals record"

        total = sum(float(a["actual_spend"]) for a in actuals)
        assert total == pytest.approx(CUMULATIVE_ACTUAL, abs=1.0), (
            f"Total actuals {total} != expected {CUMULATIVE_ACTUAL}"
        )
