"""Shared pytest fixtures for the PDA Platform test suite.

Provides a ``seeded_store`` fixture that builds an in-memory AssuranceStore
pre-loaded with a realistic synthetic UK government IT programme:

  Project: "HMRC Digital Transformation Programme"
  project_id: "TEST-PROJ-001"

The data is calibrated to exercise every red-flag check and numerical
assertion in the behavioural test suite.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

PROJECT_ID = "TEST-PROJ-001"

# ---------------------------------------------------------------------------
# EV / financial constants (used by both fixture and tests)
# ---------------------------------------------------------------------------

BAC = 45_000_000          # Budget at Completion
PLANNED_DURATION_DAYS = 540
START_DATE = "2025-10-01"

# Status date: 6 months in, 33% time elapsed
CUMULATIVE_ACTUAL = 16_500_000
PLANNED_VALUE = 15_000_000        # BCWS
EARNED_VALUE = 12_600_000         # BCWP  (28% physically complete)

# Derived:
#   SPI  = EV / PV = 12_600_000 / 15_000_000 = 0.8400
#   CPI  = EV / AC = 12_600_000 / 16_500_000 = 0.7636...
#   EAC  = AC + (BAC - EV) / CPI             ≈ 58_930_000
#   VAC  = BAC - EAC                         ≈ -13_930_000

SPI_EXPECTED = EARNED_VALUE / PLANNED_VALUE          # 0.84
CPI_EXPECTED = EARNED_VALUE / CUMULATIVE_ACTUAL      # 0.7636...
EAC_EXPECTED = CUMULATIVE_ACTUAL + (BAC - EARNED_VALUE) / CPI_EXPECTED
VAC_EXPECTED = BAC - EAC_EXPECTED


def _now_offset(days: int) -> str:
    """Return a naive ISO-8601 UTC datetime string *days* before now.

    Stored as naive (no timezone suffix) because the risk server uses
    ``datetime.now(timezone.utc).replace(tzinfo=None)`` (naive) when computing staleness thresholds, and
    comparing naive vs aware datetimes raises a TypeError in Python 3.11+.
    """
    dt = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    return dt.isoformat()


def _today() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).date().isoformat()


@pytest.fixture(scope="function")
def seeded_store(tmp_path):
    """Return an AssuranceStore pre-loaded with HMRC Digital Transformation data.

    Uses a temporary SQLite file so each test gets a fully isolated store
    without cross-test contamination.
    """
    from pm_data_tools.db.store import AssuranceStore

    db_file = tmp_path / "test_store.db"
    store = AssuranceStore(db_path=db_file)

    now = _now_offset(0)

    # ------------------------------------------------------------------
    # Financial baseline
    # ------------------------------------------------------------------
    store.upsert_financial_baseline({
        "id": str(uuid.uuid4()),
        "project_id": PROJECT_ID,
        "label": "APPROVED",
        "total_budget": BAC,
        "cost_category": "TOTAL",
        "period_start": START_DATE,
        "period_end": "2027-03-31",
        "currency": "GBP",
        "created_at": _now_offset(180),
    })

    # Financial actuals — single cumulative entry representing 6 months
    store.upsert_financial_actual({
        "id": str(uuid.uuid4()),
        "project_id": PROJECT_ID,
        "period": "2026-04-01",
        "actual_spend": CUMULATIVE_ACTUAL,
        "cost_category": "TOTAL",
        "created_at": _now_offset(10),
    })

    # ------------------------------------------------------------------
    # Risks
    # ------------------------------------------------------------------

    # R001: High score, stale (60 days), no mitigations
    r001_id = "RISK-R001"
    store.upsert_risk({
        "id": r001_id,
        "project_id": PROJECT_ID,
        "title": "Supplier delivery delay",
        "description": "Main delivery supplier at risk of late delivery of core platform components.",
        "category": "COMMERCIAL",
        "likelihood": 4,
        "impact": 4,
        "risk_score": 16,
        "status": "OPEN",
        "created_at": _now_offset(90),
        "updated_at": _now_offset(60),
    })

    # R002: Medium score, updated recently, HAS a mitigation
    r002_id = "RISK-R002"
    store.upsert_risk({
        "id": r002_id,
        "project_id": PROJECT_ID,
        "title": "Scope creep",
        "description": "Expanding user requirements threaten to inflate scope beyond approved business case.",
        "category": "DELIVERY",
        "likelihood": 3,
        "impact": 3,
        "risk_score": 9,
        "status": "OPEN",
        "created_at": _now_offset(60),
        "updated_at": _now_offset(10),
    })
    # Mitigation for R002 (marks as IN_PROGRESS — "active")
    store.upsert_mitigation({
        "id": str(uuid.uuid4()),
        "risk_id": r002_id,
        "project_id": PROJECT_ID,
        "action": "Change freeze implemented",
        "status": "IN_PROGRESS",
        "created_at": _now_offset(10),
        "updated_at": _now_offset(10),
    })

    # R003: High impact (5), medium likelihood, no mitigations, updated recently
    r003_id = "RISK-R003"
    store.upsert_risk({
        "id": r003_id,
        "project_id": PROJECT_ID,
        "title": "Legacy system integration failure",
        "description": "Integration with HMRC legacy PAYE system may fail at scale.",
        "category": "TECHNICAL",
        "likelihood": 2,
        "impact": 5,
        "risk_score": 10,
        "status": "OPEN",
        "created_at": _now_offset(30),
        "updated_at": _now_offset(5),
    })

    # R004: Low score, no mitigations needed
    r004_id = "RISK-R004"
    store.upsert_risk({
        "id": r004_id,
        "project_id": PROJECT_ID,
        "title": "Staff turnover in delivery team",
        "description": "Key team members may leave before project completion.",
        "category": "RESOURCES",
        "likelihood": 2,
        "impact": 2,
        "risk_score": 4,
        "status": "OPEN",
        "created_at": _now_offset(15),
        "updated_at": _now_offset(3),
    })

    # R005: CLOSED — must not appear in open-only views
    r005_id = "RISK-R005"
    store.upsert_risk({
        "id": r005_id,
        "project_id": PROJECT_ID,
        "title": "Data migration errors",
        "description": "Residual risk of data corruption during initial migration batch.",
        "category": "TECHNICAL",
        "likelihood": 1,
        "impact": 1,
        "risk_score": 1,
        "status": "CLOSED",
        "created_at": _now_offset(60),
        "updated_at": _now_offset(2),
    })

    # ------------------------------------------------------------------
    # Benefits
    # ------------------------------------------------------------------
    now_str = now

    # B001: ON_TRACK, has an owner
    store.upsert_benefit({
        "id": "BEN-B001",
        "project_id": PROJECT_ID,
        "title": "Efficiency savings",
        "description": "Annual efficiency savings from automation of manual tax processing workflows.",
        "financial_type": "CASH_RELEASING",
        "recipient_type": "GOVERNMENT",
        "status": "ON_TRACK",
        "target_value": 2_000_000,
        "baseline_value": 0.0,
        "current_actual_value": 0.0,
        "benefits_owner": "Jane Smith",
        "created_at": _now_offset(120),
        "updated_at": _now_offset(10),
    })

    # B002: AT_RISK, NO owner — triggers unowned benefits flag
    store.upsert_benefit({
        "id": "BEN-B002",
        "project_id": PROJECT_ID,
        "title": "User satisfaction improvement",
        "description": "Improvement in taxpayer satisfaction score following new digital service launch.",
        "financial_type": "NON_CASH_RELEASING",
        "recipient_type": "WIDER_UK_PUBLIC",
        "status": "AT_RISK",
        "target_value": 500_000,
        "baseline_value": 0.0,
        "current_actual_value": None,
        "benefits_owner": None,
        "created_at": _now_offset(120),
        "updated_at": _now_offset(5),
    })

    # B003: OFF_TRACK — behind realisation profile
    store.upsert_benefit({
        "id": "BEN-B003",
        "project_id": PROJECT_ID,
        "title": "Error rate reduction",
        "description": "Reduction in manual processing error rates following system cutover.",
        "financial_type": "CASH_RELEASING",
        "recipient_type": "GOVERNMENT",
        "status": "OFF_TRACK",
        "target_value": 800_000,
        "baseline_value": 0.0,
        "current_actual_value": 50_000,
        "benefits_owner": "Tom Jones",
        "created_at": _now_offset(120),
        "updated_at": _now_offset(5),
    })

    # ------------------------------------------------------------------
    # Gate readiness
    # ------------------------------------------------------------------
    gate_result = {
        "gate": "Gate 3 (FBC)",
        "readiness_score": 55,
        "composite_score": 0.55,
        "blocking_issues": [
            "FBC not submitted to approving authority",
            "Commercial strategy not approved",
        ],
        "recommended_actions": [
            "Submit FBC to IPA for review",
            "Obtain HMT sign-off on commercial strategy",
        ],
    }
    store.insert_gate_readiness_assessment({
        "id": str(uuid.uuid4()),
        "project_id": PROJECT_ID,
        "gate": "Gate 3 (FBC)",
        "readiness": "NOT_READY",
        "composite_score": 0.55,
        "assessed_at": "2026-03-01",
        "result_json": json.dumps(gate_result),
    })

    # ------------------------------------------------------------------
    # Change requests
    # ------------------------------------------------------------------
    cr_data = [
        ("CR001", "Additional API integration", "OPEN", None),
        ("CR002", "UI redesign for accessibility", "OPEN", None),
        ("CR003", "Extended data retention period", "OPEN", None),
        ("CR004", "Additional test environment", "APPROVED", "Change approved."),
        ("CR005", "Extended UAT period", "OPEN", None),
        ("CR006", "Additional reporting requirements", "OPEN", None),
        # CR007 is the 6th OPEN CR — needed to push pending_changes count > 5
        # so that scan_for_red_flags raises the CHANGE pressure flag
        ("CR007", "Revised security controls", "OPEN", None),
    ]
    for cr_id, title, status, notes in cr_data:
        store.upsert_change_request({
            "id": cr_id,
            "project_id": PROJECT_ID,
            "title": title,
            "status": status,
            "change_type": "SCOPE",
            "raised_date": _now_offset(30),
            "notes": notes,
            "created_at": _now_offset(30),
            "updated_at": _now_offset(1),
        })

    # ------------------------------------------------------------------
    # Resources — one resource at >100% loading
    # ------------------------------------------------------------------
    store.upsert_resource_plan({
        "id": str(uuid.uuid4()),
        "project_id": PROJECT_ID,
        "resource_name": "Sarah Chen",
        "role": "Lead Architect",
        # availability_pct=80 (part-time), but planned_days=30 for a 5-day period
        # available_days = 1 period * (80/100) * 5 = 4 days
        # planned_days=30 >> 4, so loading_pct is way above 100%
        "period_start": "2026-04-01",
        "period_end": "2026-04-30",
        "planned_days": 30.0,
        "availability_pct": 80.0,
        "created_at": _now_offset(10),
    })

    # Expose the db_path on the store so tests can pass it to tool handlers
    store._test_db_path = str(db_file)

    return store
