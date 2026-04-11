"""Shared SQLite persistence store for pm-data-tools assurance modules.

All tables use CREATE TABLE IF NOT EXISTS so multiple features can initialise
the store safely without conflicts.

Tables:

- ``confidence_scores``: NISTA compliance score history (P2).
- ``recommendations``: Extracted review actions (P3).
- ``divergence_snapshots``: AI confidence divergence records (P4).
- ``review_schedule_recommendations``: Adaptive review scheduling history (P5).
- ``override_decisions``: Governance override decision log (P6).
- ``lessons_learned``: Lessons learned knowledge base (P7).
- ``assurance_activities``: Assurance activity effort records (P8).
- ``overhead_analyses``: Persisted overhead analysis results (P8).
- ``workflow_executions``: Assurance workflow execution results (P9).
- ``domain_classifications``: Project domain classification results (P10).
- ``assumptions``: Project assumptions with baseline and current values (P11).
- ``assumption_validations``: Assumption validation history (P11).
- ``armm_assessments``: ARMM maturity assessment records per project (P12).
- ``armm_criterion_results``: Per-criterion assessment results (P12).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import structlog

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

DEFAULT_DB_PATH: Path = Path.home() / ".pm_data_tools" / "store.db"


class AssuranceStore:
    """Shared SQLite store for pm-data-tools assurance data.

    Manages two tables:

    - ``confidence_scores``: NISTA compliance score history per project/run.
    - ``recommendations``: Extracted assurance recommendations with status.

    All schema operations use ``CREATE TABLE IF NOT EXISTS`` so callers that
    only use one feature do not depend on the other feature's tables existing.

    Example::

        store = AssuranceStore()
        store.insert_confidence_score(
            project_id="PROJ-001",
            run_id="run-42",
            timestamp="2026-03-23T09:00:00",
            score=78.5,
            dimension_scores={"required": 85.0, "recommended": 60.0},
        )
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialise the store and create tables if absent.

        Args:
            db_path: Path to the SQLite database file.  Defaults to
                ``~/.pm_data_tools/store.db``.
        """
        self.db_path: Path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialise()
        logger.debug("assurance_store_ready", db_path=str(self.db_path))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open a connection with row-factory set.

        Returns:
            A configured :class:`sqlite3.Connection`.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _initialise(self) -> None:
        """Create all tables if they do not already exist."""
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS confidence_scores (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id       TEXT    NOT NULL,
                    run_id           TEXT    NOT NULL,
                    timestamp        TEXT    NOT NULL,
                    score            REAL    NOT NULL,
                    dimension_scores TEXT    NOT NULL,
                    UNIQUE(project_id, run_id)
                );

                CREATE TABLE IF NOT EXISTS recommendations (
                    id               TEXT PRIMARY KEY,
                    project_id       TEXT NOT NULL,
                    text             TEXT NOT NULL,
                    category         TEXT NOT NULL,
                    source_review_id TEXT NOT NULL,
                    review_date      TEXT NOT NULL,
                    status           TEXT NOT NULL,
                    owner            TEXT,
                    recurrence_of    TEXT,
                    confidence       REAL NOT NULL,
                    created_at       TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS divergence_snapshots (
                    id               TEXT PRIMARY KEY,
                    project_id       TEXT NOT NULL,
                    review_id        TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    sample_scores    TEXT NOT NULL,
                    signal_type      TEXT NOT NULL,
                    timestamp        TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS review_schedule_recommendations (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id       TEXT    NOT NULL,
                    timestamp        TEXT    NOT NULL,
                    urgency          TEXT    NOT NULL,
                    recommended_date TEXT    NOT NULL,
                    composite_score  REAL    NOT NULL,
                    signals_json     TEXT    NOT NULL,
                    rationale        TEXT    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS override_decisions (
                    id                    TEXT PRIMARY KEY,
                    project_id            TEXT NOT NULL,
                    override_type         TEXT NOT NULL,
                    decision_date         TEXT NOT NULL,
                    authoriser            TEXT NOT NULL,
                    rationale             TEXT NOT NULL,
                    overridden_finding_id TEXT,
                    overridden_value      TEXT,
                    override_value        TEXT,
                    conditions_json       TEXT NOT NULL,
                    evidence_refs_json    TEXT NOT NULL,
                    outcome               TEXT NOT NULL,
                    outcome_date          TEXT,
                    outcome_notes         TEXT,
                    created_at            TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS lessons_learned (
                    id                 TEXT PRIMARY KEY,
                    project_id         TEXT NOT NULL,
                    title              TEXT NOT NULL,
                    description        TEXT NOT NULL,
                    category           TEXT NOT NULL,
                    sentiment          TEXT NOT NULL,
                    project_type       TEXT,
                    project_phase      TEXT,
                    department         TEXT,
                    tags_json          TEXT NOT NULL,
                    date_recorded      TEXT NOT NULL,
                    recorded_by        TEXT,
                    impact_description TEXT,
                    created_at         TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS assurance_activities (
                    id                  TEXT PRIMARY KEY,
                    project_id          TEXT NOT NULL,
                    activity_type       TEXT NOT NULL,
                    description         TEXT NOT NULL,
                    date                TEXT NOT NULL,
                    effort_hours        REAL NOT NULL,
                    participants        INTEGER NOT NULL,
                    artefacts_reviewed  TEXT NOT NULL,
                    findings_count      INTEGER NOT NULL,
                    confidence_before   REAL,
                    confidence_after    REAL,
                    created_at          TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS overhead_analyses (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id      TEXT NOT NULL,
                    timestamp       TEXT NOT NULL,
                    analysis_json   TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id              TEXT PRIMARY KEY,
                    project_id      TEXT NOT NULL,
                    workflow_type   TEXT NOT NULL,
                    started_at      TEXT NOT NULL,
                    completed_at    TEXT NOT NULL,
                    duration_ms     REAL NOT NULL,
                    health          TEXT NOT NULL,
                    result_json     TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS domain_classifications (
                    id              TEXT PRIMARY KEY,
                    project_id      TEXT NOT NULL,
                    domain          TEXT NOT NULL,
                    composite_score REAL NOT NULL,
                    classified_at   TEXT NOT NULL,
                    result_json     TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS assumptions (
                    id              TEXT PRIMARY KEY,
                    project_id      TEXT NOT NULL,
                    text            TEXT NOT NULL,
                    category        TEXT NOT NULL,
                    baseline_value  REAL NOT NULL,
                    current_value   REAL,
                    unit            TEXT NOT NULL,
                    tolerance_pct   REAL NOT NULL,
                    source          TEXT NOT NULL,
                    external_ref    TEXT,
                    dependencies    TEXT NOT NULL,
                    owner           TEXT,
                    last_validated  TEXT,
                    created_date    TEXT NOT NULL,
                    notes           TEXT
                );

                CREATE TABLE IF NOT EXISTS assumption_validations (
                    id              TEXT PRIMARY KEY,
                    assumption_id   TEXT NOT NULL,
                    validated_at    TEXT NOT NULL,
                    previous_value  REAL,
                    new_value       REAL NOT NULL,
                    source          TEXT NOT NULL,
                    drift_pct       REAL NOT NULL,
                    severity        TEXT NOT NULL,
                    notes           TEXT,
                    FOREIGN KEY (assumption_id) REFERENCES assumptions(id)
                );

                CREATE TABLE IF NOT EXISTS armm_assessments (
                    id                      TEXT PRIMARY KEY,
                    project_id              TEXT NOT NULL,
                    assessed_at             TEXT NOT NULL,
                    assessed_by             TEXT NOT NULL,
                    overall_level           INTEGER NOT NULL,
                    overall_score_pct       REAL NOT NULL,
                    criteria_total          INTEGER NOT NULL,
                    criteria_met            INTEGER NOT NULL,
                    topic_scores_json       TEXT NOT NULL,
                    topic_levels_json       TEXT NOT NULL,
                    dimension_scores_json   TEXT NOT NULL,
                    dimension_levels_json   TEXT NOT NULL,
                    dimension_blocking_json TEXT NOT NULL,
                    notes                   TEXT
                );

                CREATE TABLE IF NOT EXISTS armm_criterion_results (
                    id              TEXT PRIMARY KEY,
                    assessment_id   TEXT NOT NULL,
                    project_id      TEXT NOT NULL,
                    criterion_id    TEXT NOT NULL,
                    topic_code      TEXT NOT NULL,
                    dimension_code  TEXT NOT NULL,
                    met             INTEGER NOT NULL,
                    evidence_ref    TEXT,
                    notes           TEXT,
                    FOREIGN KEY (assessment_id) REFERENCES armm_assessments(id)
                );

                CREATE TABLE IF NOT EXISTS benefits (
                    id                     TEXT PRIMARY KEY,
                    project_id             TEXT NOT NULL,
                    title                  TEXT NOT NULL,
                    description            TEXT NOT NULL,
                    is_disbenefit          INTEGER NOT NULL DEFAULT 0,
                    status                 TEXT NOT NULL DEFAULT 'IDENTIFIED',
                    financial_type         TEXT NOT NULL,
                    recipient_type         TEXT NOT NULL,
                    explicitness           TEXT NOT NULL DEFAULT 'QUANTIFIABLE',
                    baseline_value         REAL,
                    baseline_date          TEXT,
                    target_value           REAL,
                    target_date            TEXT,
                    current_actual_value   REAL,
                    interim_targets        TEXT NOT NULL DEFAULT '[]',
                    measurement_kpi        TEXT,
                    measurement_frequency  TEXT NOT NULL DEFAULT 'QUARTERLY',
                    indicator_type         TEXT NOT NULL DEFAULT 'LAGGING',
                    owner_sro              TEXT,
                    benefits_owner         TEXT,
                    business_change_owner  TEXT,
                    ipa_lifecycle_stage    TEXT NOT NULL DEFAULT 'IDENTIFY_QUANTIFY',
                    business_case_ref      TEXT,
                    gate_alignment         TEXT,
                    contributing_projects  TEXT NOT NULL DEFAULT '[]',
                    associated_risks       TEXT NOT NULL DEFAULT '[]',
                    associated_assumptions TEXT NOT NULL DEFAULT '[]',
                    confidence_score       REAL,
                    created_at             TEXT NOT NULL,
                    updated_at             TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS benefit_measurements (
                    id              TEXT PRIMARY KEY,
                    benefit_id      TEXT NOT NULL,
                    project_id      TEXT NOT NULL,
                    measured_at     TEXT NOT NULL,
                    value           REAL NOT NULL,
                    source          TEXT NOT NULL DEFAULT 'MANUAL',
                    drift_pct       REAL NOT NULL DEFAULT 0.0,
                    drift_severity  TEXT NOT NULL DEFAULT 'NONE',
                    realisation_pct REAL,
                    trend_direction TEXT,
                    notes           TEXT,
                    created_at      TEXT NOT NULL,
                    FOREIGN KEY (benefit_id) REFERENCES benefits(id)
                );

                CREATE TABLE IF NOT EXISTS benefit_dependency_nodes (
                    id          TEXT PRIMARY KEY,
                    project_id  TEXT NOT NULL,
                    node_type   TEXT NOT NULL,
                    title       TEXT NOT NULL,
                    description TEXT,
                    status      TEXT NOT NULL DEFAULT 'PLANNED',
                    owner       TEXT,
                    benefit_id  TEXT,
                    target_date TEXT,
                    created_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS benefit_dependency_edges (
                    id            TEXT PRIMARY KEY,
                    project_id    TEXT NOT NULL,
                    source_node   TEXT NOT NULL,
                    target_node   TEXT NOT NULL,
                    edge_type     TEXT NOT NULL DEFAULT 'DEPENDS_ON',
                    assumption_id TEXT,
                    risk_id       TEXT,
                    notes         TEXT,
                    created_at    TEXT NOT NULL,
                    FOREIGN KEY (source_node) REFERENCES benefit_dependency_nodes(id),
                    FOREIGN KEY (target_node) REFERENCES benefit_dependency_nodes(id),
                    UNIQUE(source_node, target_node)
                );

                CREATE TABLE IF NOT EXISTS gate_readiness_assessments (
                    id              TEXT PRIMARY KEY,
                    project_id      TEXT NOT NULL,
                    gate            TEXT NOT NULL,
                    readiness       TEXT NOT NULL,
                    composite_score REAL NOT NULL,
                    assessed_at     TEXT NOT NULL,
                    result_json     TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS risks (
                    id              TEXT PRIMARY KEY,
                    project_id      TEXT NOT NULL,
                    title           TEXT NOT NULL,
                    description     TEXT,
                    category        TEXT NOT NULL DEFAULT 'DELIVERY',
                    likelihood      INTEGER NOT NULL DEFAULT 3,
                    impact          INTEGER NOT NULL DEFAULT 3,
                    risk_score      INTEGER NOT NULL DEFAULT 9,
                    status          TEXT NOT NULL DEFAULT 'OPEN',
                    owner           TEXT,
                    target_date     TEXT,
                    proximity       TEXT,
                    notes           TEXT,
                    created_at      TEXT NOT NULL,
                    updated_at      TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS risk_mitigations (
                    id              TEXT PRIMARY KEY,
                    risk_id         TEXT NOT NULL,
                    project_id      TEXT NOT NULL,
                    action          TEXT NOT NULL,
                    owner           TEXT,
                    target_date     TEXT,
                    status          TEXT NOT NULL DEFAULT 'PLANNED',
                    effectiveness   TEXT,
                    residual_likelihood INTEGER,
                    residual_impact     INTEGER,
                    notes           TEXT,
                    created_at      TEXT NOT NULL,
                    updated_at      TEXT NOT NULL,
                    FOREIGN KEY (risk_id) REFERENCES risks(id)
                );

                CREATE TABLE IF NOT EXISTS risk_score_history (
                    id              TEXT PRIMARY KEY,
                    risk_id         TEXT NOT NULL,
                    project_id      TEXT NOT NULL,
                    likelihood      INTEGER NOT NULL,
                    impact          INTEGER NOT NULL,
                    risk_score      INTEGER NOT NULL,
                    recorded_at     TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (risk_id) REFERENCES risks(id)
                );

                CREATE TABLE IF NOT EXISTS change_requests (
                    id                  TEXT PRIMARY KEY,
                    project_id          TEXT NOT NULL,
                    title               TEXT NOT NULL,
                    description         TEXT,
                    change_type         TEXT NOT NULL DEFAULT 'SCOPE',
                    impact_cost         REAL,
                    impact_schedule_days INTEGER,
                    impact_scope        TEXT,
                    status              TEXT NOT NULL DEFAULT 'SUBMITTED',
                    raised_by           TEXT,
                    approved_by         TEXT,
                    raised_date         TEXT NOT NULL,
                    decision_date       TEXT,
                    implementation_date TEXT,
                    notes               TEXT,
                    created_at          TEXT NOT NULL,
                    updated_at          TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS resource_plans (
                    id              TEXT PRIMARY KEY,
                    project_id      TEXT NOT NULL,
                    resource_name   TEXT NOT NULL,
                    role            TEXT,
                    period_start    TEXT NOT NULL,
                    period_end      TEXT NOT NULL,
                    planned_days    REAL NOT NULL DEFAULT 0.0,
                    actual_days     REAL,
                    availability_pct REAL NOT NULL DEFAULT 100.0,
                    notes           TEXT,
                    created_at      TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS financial_baselines (
                    id              TEXT PRIMARY KEY,
                    project_id      TEXT NOT NULL,
                    label           TEXT NOT NULL DEFAULT 'APPROVED',
                    total_budget    REAL NOT NULL,
                    cost_category   TEXT NOT NULL DEFAULT 'TOTAL',
                    period_start    TEXT,
                    period_end      TEXT,
                    period_budget   REAL,
                    currency        TEXT NOT NULL DEFAULT 'GBP',
                    notes           TEXT,
                    created_at      TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS financial_actuals (
                    id              TEXT PRIMARY KEY,
                    project_id      TEXT NOT NULL,
                    period          TEXT NOT NULL,
                    actual_spend    REAL NOT NULL,
                    cost_category   TEXT NOT NULL DEFAULT 'TOTAL',
                    committed_spend REAL,
                    source          TEXT,
                    notes           TEXT,
                    created_at      TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS financial_forecasts (
                    id              TEXT PRIMARY KEY,
                    project_id      TEXT NOT NULL,
                    forecast_date   TEXT NOT NULL,
                    eac             REAL NOT NULL,
                    method          TEXT NOT NULL DEFAULT 'MANUAL',
                    confidence_pct  REAL,
                    p80_estimate    REAL,
                    notes           TEXT,
                    created_at      TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS simulation_runs (
                    id                   TEXT PRIMARY KEY,
                    project_id           TEXT NOT NULL,
                    simulation_type      TEXT NOT NULL,
                    n_simulations        INTEGER NOT NULL,
                    p50_days             INTEGER,
                    p80_days             INTEGER,
                    p90_days             INTEGER,
                    p50_date             TEXT,
                    p80_date             TEXT,
                    p90_date             TEXT,
                    mean_duration_days   REAL,
                    std_deviation_days   REAL,
                    cost_p50             REAL,
                    cost_p80             REAL,
                    cost_p90             REAL,
                    run_at               TEXT DEFAULT (datetime('now')),
                    parameters_json      TEXT
                );

                CREATE TABLE IF NOT EXISTS lessons (
                    id              TEXT PRIMARY KEY,
                    project_id      TEXT NOT NULL,
                    document_type   TEXT NOT NULL,
                    gate            TEXT,
                    phase           TEXT,
                    category        TEXT NOT NULL,
                    title           TEXT NOT NULL,
                    root_cause      TEXT,
                    recommendation  TEXT NOT NULL,
                    severity        TEXT NOT NULL DEFAULT 'MEDIUM',
                    extracted_at    TEXT DEFAULT (datetime('now')),
                    source_excerpt  TEXT
                );
                """
            )

    # ------------------------------------------------------------------
    # Confidence scores
    # ------------------------------------------------------------------

    def insert_confidence_score(
        self,
        project_id: str,
        run_id: str,
        timestamp: str,
        score: float,
        dimension_scores: dict[str, float],
    ) -> None:
        """Persist a NISTA confidence score record.

        Uses ``INSERT OR REPLACE`` so re-running the same ``run_id`` updates
        the stored values rather than raising a unique-constraint error.

        Args:
            project_id: Identifier for the project being validated.
            run_id: Unique identifier for this validation run.
            timestamp: ISO-8601 timestamp string of the run.
            score: Overall compliance score (0-100).
            dimension_scores: Per-dimension scores keyed by dimension name.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO confidence_scores
                    (project_id, run_id, timestamp, score, dimension_scores)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    run_id,
                    timestamp,
                    score,
                    json.dumps(dimension_scores),
                ),
            )
        logger.debug(
            "confidence_score_persisted",
            project_id=project_id,
            run_id=run_id,
            score=score,
        )

    def get_confidence_scores(self, project_id: str) -> list[dict[str, object]]:
        """Retrieve all confidence score records for a project, oldest first.

        Args:
            project_id: The project identifier.

        Returns:
            List of row dicts with keys: id, project_id, run_id, timestamp,
            score, dimension_scores (already deserialised from JSON).
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT id, project_id, run_id, timestamp, score, dimension_scores
                FROM confidence_scores
                WHERE project_id = ?
                ORDER BY timestamp ASC
                """,
                (project_id,),
            )
            rows = cursor.fetchall()

        result: list[dict[str, object]] = []
        for row in rows:
            record = dict(row)
            raw = record.get("dimension_scores")
            record["dimension_scores"] = json.loads(raw) if isinstance(raw, str) else {}
            result.append(record)
        return result

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    def upsert_recommendation(self, data: dict[str, object]) -> None:
        """Insert or replace a recommendation record.

        Args:
            data: Dict with keys matching the ``recommendations`` table columns.
                Must include ``id``, ``project_id``, ``text``, ``category``,
                ``source_review_id``, ``review_date``, ``status``,
                ``confidence``, ``created_at``.  ``owner`` and
                ``recurrence_of`` are optional.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO recommendations
                    (id, project_id, text, category, source_review_id,
                     review_date, status, owner, recurrence_of, confidence,
                     created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["project_id"],
                    data["text"],
                    data["category"],
                    data["source_review_id"],
                    data["review_date"],
                    data["status"],
                    data.get("owner"),
                    data.get("recurrence_of"),
                    data["confidence"],
                    data["created_at"],
                ),
            )
        logger.debug(
            "recommendation_persisted",
            id=data["id"],
            project_id=data["project_id"],
        )

    def get_recommendations(
        self,
        project_id: str,
        status_filter: str | None = None,
    ) -> list[dict[str, object]]:
        """Retrieve recommendations for a project, optionally filtered by status.

        Args:
            project_id: The project identifier.
            status_filter: Optional status value to filter by (e.g. ``"OPEN"``).

        Returns:
            List of recommendation row dicts ordered by review_date ascending.
        """
        if status_filter is not None:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM recommendations
                    WHERE project_id = ? AND status = ?
                    ORDER BY review_date ASC
                    """,
                    (project_id, status_filter),
                )
                rows = cursor.fetchall()
        else:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM recommendations
                    WHERE project_id = ?
                    ORDER BY review_date ASC
                    """,
                    (project_id,),
                )
                rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def update_recommendation_status(self, rec_id: str, status: str) -> None:
        """Update the status of a single recommendation.

        Args:
            rec_id: The recommendation ``id``.
            status: New status string (e.g. ``"CLOSED"``).
        """
        with self._connect() as conn:
            conn.execute(
                "UPDATE recommendations SET status = ? WHERE id = ?",
                (status, rec_id),
            )
        logger.debug("recommendation_status_updated", id=rec_id, status=status)

    # ------------------------------------------------------------------
    # Divergence snapshots (P4)
    # ------------------------------------------------------------------

    def insert_divergence_snapshot(
        self,
        snapshot_id: str,
        project_id: str,
        review_id: str,
        confidence_score: float,
        sample_scores: list[float],
        signal_type: str,
        timestamp: str,
    ) -> None:
        """Persist a confidence divergence snapshot.

        Uses ``INSERT OR REPLACE`` so re-submitting the same ``snapshot_id``
        updates the record rather than raising a unique-constraint error.

        Args:
            snapshot_id: UUID for this snapshot.
            project_id: The project identifier.
            review_id: The review identifier.
            confidence_score: Overall consensus confidence score (0–1).
            sample_scores: Individual per-sample confidence scores.
            signal_type: Signal classification (e.g. ``"STABLE"``).
            timestamp: ISO-8601 timestamp string of the check.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO divergence_snapshots
                    (id, project_id, review_id, confidence_score,
                     sample_scores, signal_type, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    project_id,
                    review_id,
                    confidence_score,
                    json.dumps(sample_scores),
                    signal_type,
                    timestamp,
                ),
            )
        logger.debug(
            "divergence_snapshot_persisted",
            snapshot_id=snapshot_id,
            project_id=project_id,
            signal_type=signal_type,
        )

    def get_divergence_history(self, project_id: str) -> list[dict[str, object]]:
        """Retrieve all divergence snapshots for a project, oldest first.

        Args:
            project_id: The project identifier.

        Returns:
            List of row dicts with keys: id, project_id, review_id,
            confidence_score, sample_scores (deserialised list), signal_type,
            timestamp.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT id, project_id, review_id, confidence_score,
                       sample_scores, signal_type, timestamp
                FROM divergence_snapshots
                WHERE project_id = ?
                ORDER BY timestamp ASC
                """,
                (project_id,),
            )
            rows = cursor.fetchall()

        result: list[dict[str, object]] = []
        for row in rows:
            record = dict(row)
            raw = record.get("sample_scores")
            record["sample_scores"] = json.loads(raw) if isinstance(raw, str) else []
            result.append(record)
        return result

    # ------------------------------------------------------------------
    # Review schedule recommendations (P5)
    # ------------------------------------------------------------------

    def insert_schedule_recommendation(
        self,
        project_id: str,
        timestamp: str,
        urgency: str,
        recommended_date: str,
        composite_score: float,
        signals_json: str,
        rationale: str,
    ) -> None:
        """Persist an adaptive review scheduling recommendation.

        Args:
            project_id: The project identifier.
            timestamp: ISO-8601 timestamp string of the recommendation.
            urgency: Urgency classification (e.g. ``"IMMEDIATE"``).
            recommended_date: ISO-8601 date string of the suggested review date.
            composite_score: Weighted composite severity score (0–1).
            signals_json: JSON-serialised list of contributing signals.
            rationale: Human-readable explanation of the recommendation.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO review_schedule_recommendations
                    (project_id, timestamp, urgency, recommended_date,
                     composite_score, signals_json, rationale)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    timestamp,
                    urgency,
                    recommended_date,
                    composite_score,
                    signals_json,
                    rationale,
                ),
            )
        logger.debug(
            "schedule_recommendation_persisted",
            project_id=project_id,
            urgency=urgency,
            recommended_date=recommended_date,
        )

    def get_schedule_history(self, project_id: str) -> list[dict[str, object]]:
        """Retrieve all scheduling recommendations for a project, oldest first.

        Args:
            project_id: The project identifier.

        Returns:
            List of row dicts.  ``signals_json`` is returned as a raw string.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT id, project_id, timestamp, urgency, recommended_date,
                       composite_score, signals_json, rationale
                FROM review_schedule_recommendations
                WHERE project_id = ?
                ORDER BY timestamp ASC
                """,
                (project_id,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Override decisions (P6)
    # ------------------------------------------------------------------

    def upsert_override_decision(self, data: dict[str, object]) -> None:
        """Insert or replace an override decision record.

        Args:
            data: Dict with keys matching the ``override_decisions`` table
                columns.  Must include ``id``, ``project_id``,
                ``override_type``, ``decision_date``, ``authoriser``,
                ``rationale``, ``conditions_json``, ``evidence_refs_json``,
                ``outcome``, ``created_at``.  All other fields are optional.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO override_decisions
                    (id, project_id, override_type, decision_date, authoriser,
                     rationale, overridden_finding_id, overridden_value,
                     override_value, conditions_json, evidence_refs_json,
                     outcome, outcome_date, outcome_notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["project_id"],
                    data["override_type"],
                    data["decision_date"],
                    data["authoriser"],
                    data["rationale"],
                    data.get("overridden_finding_id"),
                    data.get("overridden_value"),
                    data.get("override_value"),
                    data["conditions_json"],
                    data["evidence_refs_json"],
                    data["outcome"],
                    data.get("outcome_date"),
                    data.get("outcome_notes"),
                    data["created_at"],
                ),
            )
        logger.debug(
            "override_decision_persisted",
            id=data["id"],
            project_id=data["project_id"],
        )

    def get_override_decisions(
        self,
        project_id: str,
        override_type: str | None = None,
        outcome: str | None = None,
    ) -> list[dict[str, object]]:
        """Retrieve override decisions, optionally filtered by type and/or outcome.

        Args:
            project_id: The project identifier.
            override_type: Optional override type string to filter by.
            outcome: Optional outcome string to filter by.

        Returns:
            List of row dicts ordered by decision_date ascending.  List fields
            (``conditions_json``, ``evidence_refs_json``) are returned as raw
            JSON strings.
        """
        if override_type is not None and outcome is not None:
            sql = """
                SELECT * FROM override_decisions
                WHERE project_id = ? AND override_type = ? AND outcome = ?
                ORDER BY decision_date ASC
            """
            params: tuple[object, ...] = (project_id, override_type, outcome)
        elif override_type is not None:
            sql = """
                SELECT * FROM override_decisions
                WHERE project_id = ? AND override_type = ?
                ORDER BY decision_date ASC
            """
            params = (project_id, override_type)
        elif outcome is not None:
            sql = """
                SELECT * FROM override_decisions
                WHERE project_id = ? AND outcome = ?
                ORDER BY decision_date ASC
            """
            params = (project_id, outcome)
        else:
            sql = """
                SELECT * FROM override_decisions
                WHERE project_id = ?
                ORDER BY decision_date ASC
            """
            params = (project_id,)

        with self._connect() as conn:
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def update_override_outcome(
        self,
        override_id: str,
        outcome: str,
        outcome_date: str | None = None,
        outcome_notes: str | None = None,
    ) -> None:
        """Update the outcome of a previously logged override decision.

        Args:
            override_id: The override decision ``id``.
            outcome: New outcome string (e.g. ``"SIGNIFICANT_IMPACT"``).
            outcome_date: Optional ISO-8601 date string when the outcome
                was observed.
            outcome_notes: Optional human-readable notes about the outcome.
        """
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE override_decisions
                SET outcome = ?, outcome_date = ?, outcome_notes = ?
                WHERE id = ?
                """,
                (outcome, outcome_date, outcome_notes, override_id),
            )
        logger.debug(
            "override_outcome_updated",
            id=override_id,
            outcome=outcome,
        )

    # ------------------------------------------------------------------
    # Lessons learned (P7)
    # ------------------------------------------------------------------

    def upsert_lesson(self, data: dict[str, object]) -> None:
        """Insert or replace a lessons learned record.

        Args:
            data: Dict with keys matching the ``lessons_learned`` table
                columns.  Must include ``id``, ``project_id``, ``title``,
                ``description``, ``category``, ``sentiment``,
                ``tags_json``, ``date_recorded``, and ``created_at``.
                All other fields are optional.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO lessons_learned
                    (id, project_id, title, description, category, sentiment,
                     project_type, project_phase, department, tags_json,
                     date_recorded, recorded_by, impact_description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["project_id"],
                    data["title"],
                    data["description"],
                    data["category"],
                    data["sentiment"],
                    data.get("project_type"),
                    data.get("project_phase"),
                    data.get("department"),
                    data["tags_json"],
                    data["date_recorded"],
                    data.get("recorded_by"),
                    data.get("impact_description"),
                    data["created_at"],
                ),
            )
        logger.debug(
            "lesson_persisted",
            id=data["id"],
            project_id=data["project_id"],
        )

    def get_lessons(
        self,
        project_id: str | None = None,
        category: str | None = None,
        sentiment: str | None = None,
    ) -> list[dict[str, object]]:
        """Retrieve lessons, optionally filtered by project, category, and sentiment.

        Args:
            project_id: Optional project identifier filter.
            category: Optional category string filter.
            sentiment: Optional sentiment string filter (e.g. ``"NEGATIVE"``).

        Returns:
            List of row dicts ordered by ``date_recorded`` descending.
        """
        conditions: list[str] = []
        params: list[object] = []

        if project_id is not None:
            conditions.append("project_id = ?")
            params.append(project_id)
        if category is not None:
            conditions.append("category = ?")
            params.append(category)
        if sentiment is not None:
            conditions.append("sentiment = ?")
            params.append(sentiment)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM lessons_learned {where} ORDER BY date_recorded DESC"

        with self._connect() as conn:
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_all_lessons(self) -> list[dict[str, object]]:
        """Retrieve all lessons from the corpus, unfiltered.

        Returns:
            List of row dicts ordered by ``date_recorded`` descending.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM lessons_learned ORDER BY date_recorded DESC"
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def search_lessons_keyword(self, query: str) -> list[dict[str, object]]:
        """SQL LIKE search across title, description, and tags_json.

        Args:
            query: The search string; matched case-insensitively via
                SQLite's ``LIKE`` operator.

        Returns:
            Matching row dicts ordered by ``date_recorded`` descending.
        """
        like = f"%{query}%"
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM lessons_learned
                WHERE title LIKE ? OR description LIKE ? OR tags_json LIKE ?
                ORDER BY date_recorded DESC
                """,
                (like, like, like),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Assurance activities (P8)
    # ------------------------------------------------------------------

    def upsert_assurance_activity(self, data: dict[str, object]) -> None:
        """Insert or replace an assurance activity record.

        Args:
            data: Dict with keys matching the ``assurance_activities`` table
                columns.  Must include ``id``, ``project_id``,
                ``activity_type``, ``description``, ``date``,
                ``effort_hours``, ``participants``, ``artefacts_reviewed``,
                ``findings_count``, and ``created_at``.
                ``confidence_before`` and ``confidence_after`` are optional.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO assurance_activities
                    (id, project_id, activity_type, description, date,
                     effort_hours, participants, artefacts_reviewed,
                     findings_count, confidence_before, confidence_after,
                     created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["project_id"],
                    data["activity_type"],
                    data["description"],
                    data["date"],
                    data["effort_hours"],
                    data["participants"],
                    data["artefacts_reviewed"],
                    data["findings_count"],
                    data.get("confidence_before"),
                    data.get("confidence_after"),
                    data["created_at"],
                ),
            )
        logger.debug(
            "assurance_activity_persisted",
            id=data["id"],
            project_id=data["project_id"],
        )

    def get_assurance_activities(
        self,
        project_id: str,
        activity_type: str | None = None,
    ) -> list[dict[str, object]]:
        """Retrieve assurance activities for a project.

        Args:
            project_id: The project identifier.
            activity_type: Optional activity type string to filter by.

        Returns:
            List of row dicts ordered by date ascending.
        """
        if activity_type is not None:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM assurance_activities
                    WHERE project_id = ? AND activity_type = ?
                    ORDER BY date ASC
                    """,
                    (project_id, activity_type),
                )
                rows = cursor.fetchall()
        else:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM assurance_activities
                    WHERE project_id = ?
                    ORDER BY date ASC
                    """,
                    (project_id,),
                )
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def insert_overhead_analysis(
        self,
        project_id: str,
        timestamp: str,
        analysis_json: str,
    ) -> None:
        """Persist a complete overhead analysis result.

        Args:
            project_id: The project identifier.
            timestamp: ISO-8601 timestamp string of the analysis.
            analysis_json: Full :class:`~pm_data_tools.assurance.overhead.OverheadAnalysis`
                serialised as JSON.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO overhead_analyses
                    (project_id, timestamp, analysis_json)
                VALUES (?, ?, ?)
                """,
                (project_id, timestamp, analysis_json),
            )
        logger.debug(
            "overhead_analysis_persisted",
            project_id=project_id,
            timestamp=timestamp,
        )

    def get_overhead_history(self, project_id: str) -> list[dict[str, object]]:
        """Retrieve all overhead analysis results for a project.

        Args:
            project_id: The project identifier.

        Returns:
            List of row dicts ordered by timestamp ascending.
            ``analysis_json`` is returned as a raw JSON string.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT id, project_id, timestamp, analysis_json
                FROM overhead_analyses
                WHERE project_id = ?
                ORDER BY timestamp ASC
                """,
                (project_id,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Workflow executions (P9)
    # ------------------------------------------------------------------

    def insert_workflow_execution(
        self,
        workflow_id: str,
        project_id: str,
        workflow_type: str,
        started_at: str,
        completed_at: str,
        duration_ms: float,
        health: str,
        result_json: str,
    ) -> None:
        """Persist a workflow execution result.

        Uses ``INSERT OR REPLACE`` so replaying the same ``workflow_id``
        updates the record rather than raising a unique-constraint error.

        Args:
            workflow_id: UUID of this workflow execution.
            project_id: The project identifier.
            workflow_type: Workflow plan name (e.g. ``"FULL_ASSURANCE"``).
            started_at: ISO-8601 timestamp when execution began.
            completed_at: ISO-8601 timestamp when execution finished.
            duration_ms: Total execution duration in milliseconds.
            health: Health classification string (e.g. ``"AT_RISK"``).
            result_json: Full :class:`~pm_data_tools.assurance.workflows.WorkflowResult`
                serialised as JSON.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO workflow_executions
                    (id, project_id, workflow_type, started_at, completed_at,
                     duration_ms, health, result_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workflow_id,
                    project_id,
                    workflow_type,
                    started_at,
                    completed_at,
                    duration_ms,
                    health,
                    result_json,
                ),
            )
        logger.debug(
            "workflow_execution_persisted",
            workflow_id=workflow_id,
            project_id=project_id,
            health=health,
        )

    def get_workflow_history(self, project_id: str) -> list[dict[str, object]]:
        """Retrieve all workflow execution results for a project.

        Args:
            project_id: The project identifier.

        Returns:
            List of row dicts ordered by ``started_at`` ascending.
            ``result_json`` is returned as a raw JSON string.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT id, project_id, workflow_type, started_at, completed_at,
                       duration_ms, health, result_json
                FROM workflow_executions
                WHERE project_id = ?
                ORDER BY started_at ASC
                """,
                (project_id,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Domain classifications (P10)
    # ------------------------------------------------------------------

    def insert_domain_classification(
        self,
        classification_id: str,
        project_id: str,
        domain: str,
        composite_score: float,
        classified_at: str,
        result_json: str,
    ) -> None:
        """Persist a domain classification result.

        Uses ``INSERT OR REPLACE`` so replaying the same ``classification_id``
        updates the record rather than raising a unique-constraint error.

        Args:
            classification_id: UUID of this classification.
            project_id: The project identifier.
            domain: Complexity domain string (e.g. ``"COMPLEX"``).
            composite_score: Final weighted composite score (0–1).
            classified_at: ISO-8601 timestamp of the classification.
            result_json: Full :class:`~pm_data_tools.assurance.classifier.ClassificationResult`
                serialised as JSON.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO domain_classifications
                    (id, project_id, domain, composite_score,
                     classified_at, result_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    classification_id,
                    project_id,
                    domain,
                    composite_score,
                    classified_at,
                    result_json,
                ),
            )
        logger.debug(
            "domain_classification_persisted",
            classification_id=classification_id,
            project_id=project_id,
            domain=domain,
        )

    def get_domain_classifications(
        self, project_id: str
    ) -> list[dict[str, object]]:
        """Retrieve all domain classification results for a project.

        Args:
            project_id: The project identifier.

        Returns:
            List of row dicts ordered by ``classified_at`` ascending.
            ``result_json`` is returned as a raw JSON string.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT id, project_id, domain, composite_score,
                       classified_at, result_json
                FROM domain_classifications
                WHERE project_id = ?
                ORDER BY classified_at ASC
                """,
                (project_id,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Assumptions (P11)
    # ------------------------------------------------------------------

    def upsert_assumption(self, data: dict[str, object]) -> None:
        """Insert or replace an assumption record.

        Args:
            data: Dict with keys matching the ``assumptions`` table columns.
                Must include ``id``, ``project_id``, ``text``, ``category``,
                ``baseline_value``, ``unit``, ``tolerance_pct``, ``source``,
                ``dependencies``, ``created_date``.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO assumptions
                    (id, project_id, text, category, baseline_value,
                     current_value, unit, tolerance_pct, source,
                     external_ref, dependencies, owner, last_validated,
                     created_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["project_id"],
                    data["text"],
                    data["category"],
                    data["baseline_value"],
                    data.get("current_value"),
                    data.get("unit", ""),
                    data.get("tolerance_pct", 10.0),
                    data["source"],
                    data.get("external_ref"),
                    data.get("dependencies", "[]"),
                    data.get("owner"),
                    data.get("last_validated"),
                    data["created_date"],
                    data.get("notes"),
                ),
            )
        logger.debug(
            "assumption_persisted",
            id=data["id"],
            project_id=data["project_id"],
        )

    def get_assumptions(
        self,
        project_id: str,
        category: str | None = None,
    ) -> list[dict[str, object]]:
        """Retrieve assumptions for a project, optionally filtered by category.

        Args:
            project_id: The project identifier.
            category: Optional category string to filter by.

        Returns:
            List of row dicts ordered by ``created_date`` ascending.
        """
        if category is not None:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM assumptions
                    WHERE project_id = ? AND category = ?
                    ORDER BY created_date ASC
                    """,
                    (project_id, category),
                )
                rows = cursor.fetchall()
        else:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM assumptions
                    WHERE project_id = ?
                    ORDER BY created_date ASC
                    """,
                    (project_id,),
                )
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_assumption_by_id(
        self, assumption_id: str
    ) -> dict[str, object] | None:
        """Retrieve a single assumption by its ID.

        Args:
            assumption_id: The assumption identifier.

        Returns:
            Row dict, or ``None`` if not found.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM assumptions WHERE id = ?",
                (assumption_id,),
            )
            row = cursor.fetchone()
        return dict(row) if row else None

    def update_assumption_value(
        self,
        assumption_id: str,
        current_value: float,
        last_validated: str,
    ) -> None:
        """Update the current value and last validated date of an assumption.

        Args:
            assumption_id: The assumption identifier.
            current_value: New current value.
            last_validated: ISO-8601 date string of the validation.
        """
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE assumptions
                SET current_value = ?, last_validated = ?
                WHERE id = ?
                """,
                (current_value, last_validated, assumption_id),
            )
        logger.debug(
            "assumption_value_updated",
            assumption_id=assumption_id,
            current_value=current_value,
        )

    def insert_assumption_validation(self, data: dict[str, object]) -> None:
        """Persist an assumption validation record.

        Args:
            data: Dict with keys matching the ``assumption_validations``
                table columns.  Must include ``id``, ``assumption_id``,
                ``validated_at``, ``new_value``, ``source``, ``drift_pct``,
                ``severity``.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO assumption_validations
                    (id, assumption_id, validated_at, previous_value,
                     new_value, source, drift_pct, severity, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["assumption_id"],
                    data["validated_at"],
                    data.get("previous_value"),
                    data["new_value"],
                    data["source"],
                    data["drift_pct"],
                    data["severity"],
                    data.get("notes"),
                ),
            )
        logger.debug(
            "assumption_validation_persisted",
            id=data["id"],
            assumption_id=data["assumption_id"],
        )

    def get_assumption_validations(
        self, assumption_id: str
    ) -> list[dict[str, object]]:
        """Retrieve all validation records for an assumption, oldest first.

        Args:
            assumption_id: The assumption identifier.

        Returns:
            List of row dicts ordered by ``validated_at`` ascending.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM assumption_validations
                WHERE assumption_id = ?
                ORDER BY validated_at ASC
                """,
                (assumption_id,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # ARMM Assessment — P12
    # ------------------------------------------------------------------

    def upsert_armm_assessment(self, data: dict[str, object]) -> None:
        """Persist an ARMM assessment record (insert or replace).

        Args:
            data: Dict with keys ``id``, ``project_id``, ``assessed_at``,
                ``assessed_by``, ``overall_level``, ``overall_score_pct``,
                ``criteria_total``, ``criteria_met``, ``topic_scores_json``,
                ``topic_levels_json``, ``dimension_scores_json``,
                ``dimension_levels_json``, ``dimension_blocking_json``,
                ``notes``.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO armm_assessments (
                    id, project_id, assessed_at, assessed_by,
                    overall_level, overall_score_pct, criteria_total, criteria_met,
                    topic_scores_json, topic_levels_json,
                    dimension_scores_json, dimension_levels_json,
                    dimension_blocking_json, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["project_id"],
                    data["assessed_at"],
                    data.get("assessed_by", ""),
                    data["overall_level"],
                    data["overall_score_pct"],
                    data["criteria_total"],
                    data["criteria_met"],
                    data["topic_scores_json"],
                    data["topic_levels_json"],
                    data["dimension_scores_json"],
                    data["dimension_levels_json"],
                    data["dimension_blocking_json"],
                    data.get("notes", ""),
                ),
            )
        logger.debug("armm_assessment_upserted", id=data["id"], project_id=data["project_id"])

    def insert_armm_criterion_results(
        self, assessment_id: str, project_id: str, results: list[dict[str, object]]
    ) -> None:
        """Persist criterion-level results for an ARMM assessment.

        Args:
            assessment_id: Parent assessment ID.
            project_id: Project the assessment belongs to.
            results: List of dicts with keys ``criterion_id``, ``topic_code``,
                ``dimension_code``, ``met``, ``evidence_ref``, ``notes``.
        """
        import uuid as _uuid

        with self._connect() as conn:
            for r in results:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO armm_criterion_results (
                        id, assessment_id, project_id, criterion_id,
                        topic_code, dimension_code, met, evidence_ref, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(_uuid.uuid4()),
                        assessment_id,
                        project_id,
                        r["criterion_id"],
                        r["topic_code"],
                        r["dimension_code"],
                        int(r["met"]),
                        r.get("evidence_ref") or "",
                        r.get("notes") or "",
                    ),
                )
        logger.debug(
            "armm_criterion_results_inserted",
            assessment_id=assessment_id,
            count=len(results),
        )

    def get_armm_assessments(self, project_id: str) -> list[dict[str, object]]:
        """Return all ARMM assessments for a project, oldest first.

        Args:
            project_id: Unique project identifier.

        Returns:
            List of row dicts ordered by ``assessed_at`` ascending.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM armm_assessments
                WHERE project_id = ?
                ORDER BY assessed_at ASC
                """,
                (project_id,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_armm_project_ids(self) -> list[str]:
        """Return distinct project IDs that have ARMM assessment data.

        Returns:
            Sorted list of project ID strings.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT project_id FROM armm_assessments ORDER BY project_id"
            )
            rows = cursor.fetchall()
        return [row["project_id"] for row in rows]

    def get_armm_criterion_results(
        self,
        assessment_id: str | None = None,
        project_id: str | None = None,
        dimension_code: str | None = None,
        topic_code: str | None = None,
    ) -> list[dict[str, object]]:
        """Retrieve criterion-level results with optional filters.

        Args:
            assessment_id: Filter by assessment.
            project_id: Filter by project.
            dimension_code: Filter by dimension code (e.g. ``"TC"``).
            topic_code: Filter by topic code (e.g. ``"TC-IV"``).

        Returns:
            List of row dicts ordered by ``criterion_id`` ascending.
        """
        clauses: list[str] = []
        params: list[object] = []
        if assessment_id:
            clauses.append("assessment_id = ?")
            params.append(assessment_id)
        if project_id:
            clauses.append("project_id = ?")
            params.append(project_id)
        if dimension_code:
            clauses.append("dimension_code = ?")
            params.append(dimension_code)
        if topic_code:
            clauses.append("topic_code = ?")
            params.append(topic_code)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as conn:
            cursor = conn.execute(
                f"SELECT * FROM armm_criterion_results {where} ORDER BY criterion_id ASC",
                params,
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Benefits (P13 — Benefits Realisation Management)
    # ------------------------------------------------------------------

    def upsert_benefit(self, data: dict[str, object]) -> None:
        """Insert or replace a benefit record.

        Args:
            data: Dict with keys matching the ``benefits`` table columns.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO benefits
                    (id, project_id, title, description, is_disbenefit, status,
                     financial_type, recipient_type, explicitness,
                     baseline_value, baseline_date, target_value, target_date,
                     current_actual_value, interim_targets,
                     measurement_kpi, measurement_frequency, indicator_type,
                     owner_sro, benefits_owner, business_change_owner,
                     ipa_lifecycle_stage, business_case_ref, gate_alignment,
                     contributing_projects, associated_risks, associated_assumptions,
                     confidence_score, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["project_id"],
                    data["title"],
                    data["description"],
                    data.get("is_disbenefit", 0),
                    data.get("status", "IDENTIFIED"),
                    data["financial_type"],
                    data["recipient_type"],
                    data.get("explicitness", "QUANTIFIABLE"),
                    data.get("baseline_value"),
                    data.get("baseline_date"),
                    data.get("target_value"),
                    data.get("target_date"),
                    data.get("current_actual_value"),
                    data.get("interim_targets", "[]"),
                    data.get("measurement_kpi"),
                    data.get("measurement_frequency", "QUARTERLY"),
                    data.get("indicator_type", "LAGGING"),
                    data.get("owner_sro"),
                    data.get("benefits_owner"),
                    data.get("business_change_owner"),
                    data.get("ipa_lifecycle_stage", "IDENTIFY_QUANTIFY"),
                    data.get("business_case_ref"),
                    data.get("gate_alignment"),
                    data.get("contributing_projects", "[]"),
                    data.get("associated_risks", "[]"),
                    data.get("associated_assumptions", "[]"),
                    data.get("confidence_score"),
                    data["created_at"],
                    data["updated_at"],
                ),
            )
        logger.debug("benefit_upserted", id=data["id"], project_id=data["project_id"])

    def get_benefits(
        self,
        project_id: str,
        status_filter: str | None = None,
        financial_type_filter: str | None = None,
    ) -> list[dict[str, object]]:
        """Retrieve benefits for a project with optional filters.

        Args:
            project_id: The project identifier.
            status_filter: Optional status value to filter by.
            financial_type_filter: Optional financial type to filter by.

        Returns:
            List of row dicts ordered by ``created_at`` ascending.
        """
        clauses = ["project_id = ?"]
        params: list[object] = [project_id]
        if status_filter:
            clauses.append("status = ?")
            params.append(status_filter)
        if financial_type_filter:
            clauses.append("financial_type = ?")
            params.append(financial_type_filter)

        where = f"WHERE {' AND '.join(clauses)}"
        with self._connect() as conn:
            cursor = conn.execute(
                f"SELECT * FROM benefits {where} ORDER BY created_at ASC",
                params,
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_benefit_by_id(self, benefit_id: str) -> dict[str, object] | None:
        """Retrieve a single benefit by ID.

        Args:
            benefit_id: The benefit identifier.

        Returns:
            Row dict or ``None`` if not found.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM benefits WHERE id = ?",
                (benefit_id,),
            )
            row = cursor.fetchone()
        return dict(row) if row else None

    def update_benefit_status(self, benefit_id: str, status: str) -> None:
        """Update a benefit's status.

        Args:
            benefit_id: The benefit identifier.
            status: New status value.
        """
        with self._connect() as conn:
            conn.execute(
                "UPDATE benefits SET status = ?, updated_at = datetime('now') WHERE id = ?",
                (status, benefit_id),
            )
        logger.debug("benefit_status_updated", id=benefit_id, status=status)

    # ------------------------------------------------------------------
    # Benefit measurements
    # ------------------------------------------------------------------

    def upsert_benefit_measurement(self, data: dict[str, object]) -> None:
        """Insert or replace a benefit measurement record.

        Args:
            data: Dict with keys matching the ``benefit_measurements`` table.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO benefit_measurements
                    (id, benefit_id, project_id, measured_at, value, source,
                     drift_pct, drift_severity, realisation_pct, trend_direction,
                     notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["benefit_id"],
                    data["project_id"],
                    data["measured_at"],
                    data["value"],
                    data.get("source", "MANUAL"),
                    data.get("drift_pct", 0.0),
                    data.get("drift_severity", "NONE"),
                    data.get("realisation_pct"),
                    data.get("trend_direction"),
                    data.get("notes"),
                    data["created_at"],
                ),
            )
        logger.debug(
            "benefit_measurement_upserted",
            id=data["id"],
            benefit_id=data["benefit_id"],
        )

    def get_benefit_measurements(
        self, benefit_id: str
    ) -> list[dict[str, object]]:
        """Retrieve all measurements for a benefit, oldest first.

        Args:
            benefit_id: The benefit identifier.

        Returns:
            List of row dicts ordered by ``measured_at`` ascending.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM benefit_measurements
                WHERE benefit_id = ?
                ORDER BY measured_at ASC
                """,
                (benefit_id,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Benefit dependency nodes
    # ------------------------------------------------------------------

    def upsert_dependency_node(self, data: dict[str, object]) -> None:
        """Insert or replace a benefit dependency node.

        Args:
            data: Dict with keys matching the ``benefit_dependency_nodes`` table.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO benefit_dependency_nodes
                    (id, project_id, node_type, title, description,
                     status, owner, target_date, benefit_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["project_id"],
                    data["node_type"],
                    data["title"],
                    data.get("description"),
                    data.get("status", "PLANNED"),
                    data.get("owner"),
                    data.get("target_date"),
                    data.get("benefit_id"),
                    data["created_at"],
                ),
            )
        logger.debug(
            "dependency_node_upserted",
            id=data["id"],
            node_type=data["node_type"],
        )

    def get_dependency_nodes(
        self,
        project_id: str,
        node_type: str | None = None,
    ) -> list[dict[str, object]]:
        """Retrieve dependency nodes for a project.

        Args:
            project_id: The project identifier.
            node_type: Optional node type filter.

        Returns:
            List of row dicts ordered by ``created_at`` ascending.
        """
        clauses = ["project_id = ?"]
        params: list[object] = [project_id]
        if node_type:
            clauses.append("node_type = ?")
            params.append(node_type)

        where = f"WHERE {' AND '.join(clauses)}"
        with self._connect() as conn:
            cursor = conn.execute(
                f"SELECT * FROM benefit_dependency_nodes {where} ORDER BY created_at ASC",
                params,
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_dependency_node_by_id(
        self, node_id: str
    ) -> dict[str, object] | None:
        """Retrieve a single dependency node by ID.

        Args:
            node_id: The node identifier.

        Returns:
            Row dict or ``None`` if not found.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM benefit_dependency_nodes WHERE id = ?",
                (node_id,),
            )
            row = cursor.fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Benefit dependency edges
    # ------------------------------------------------------------------

    def upsert_dependency_edge(self, data: dict[str, object]) -> None:
        """Insert or replace a benefit dependency edge.

        Args:
            data: Dict with keys matching the ``benefit_dependency_edges`` table.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO benefit_dependency_edges
                    (id, project_id, source_node, target_node, edge_type,
                     assumption_id, risk_id, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["project_id"],
                    data["source_node"],
                    data["target_node"],
                    data.get("edge_type", "DEPENDS_ON"),
                    data.get("assumption_id"),
                    data.get("risk_id"),
                    data.get("notes"),
                    data["created_at"],
                ),
            )
        logger.debug(
            "dependency_edge_upserted",
            id=data["id"],
            source=data["source_node"],
            target=data["target_node"],
        )

    def get_dependency_edges(
        self, project_id: str
    ) -> list[dict[str, object]]:
        """Retrieve all dependency edges for a project.

        Args:
            project_id: The project identifier.

        Returns:
            List of row dicts ordered by ``created_at`` ascending.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM benefit_dependency_edges
                WHERE project_id = ?
                ORDER BY created_at ASC
                """,
                (project_id,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def delete_dependency_edge(self, edge_id: str) -> None:
        """Delete a dependency edge by ID.

        Args:
            edge_id: The edge identifier.
        """
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM benefit_dependency_edges WHERE id = ?",
                (edge_id,),
            )
        logger.debug("dependency_edge_deleted", id=edge_id)

    # ------------------------------------------------------------------
    # Gate readiness assessments (P14)
    # ------------------------------------------------------------------

    def insert_gate_readiness_assessment(self, data: dict[str, object]) -> None:
        """Insert or replace a gate readiness assessment.

        Args:
            data: Dict with keys matching the ``gate_readiness_assessments`` table.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO gate_readiness_assessments
                    (id, project_id, gate, readiness, composite_score,
                     assessed_at, result_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["project_id"],
                    data["gate"],
                    data["readiness"],
                    data["composite_score"],
                    data["assessed_at"],
                    data["result_json"],
                ),
            )
        logger.debug(
            "gate_readiness_assessment_persisted",
            id=data["id"],
            project_id=data["project_id"],
            gate=data["gate"],
        )

    def get_gate_readiness_history(
        self,
        project_id: str,
        gate: str | None = None,
    ) -> list[dict[str, object]]:
        """Retrieve gate readiness assessments for a project.

        Args:
            project_id: The project identifier.
            gate: Optional gate type filter.

        Returns:
            List of row dicts ordered by ``assessed_at`` ascending.
        """
        clauses = ["project_id = ?"]
        params: list[object] = [project_id]
        if gate:
            clauses.append("gate = ?")
            params.append(gate)

        where = f"WHERE {' AND '.join(clauses)}"
        with self._connect() as conn:
            cursor = conn.execute(
                f"SELECT * FROM gate_readiness_assessments {where} ORDER BY assessed_at ASC",
                params,
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_gate_readiness_assessment_by_id(
        self, assessment_id: str
    ) -> dict[str, object] | None:
        """Retrieve a single gate readiness assessment by ID.

        Args:
            assessment_id: The assessment identifier.

        Returns:
            Row dict or ``None`` if not found.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM gate_readiness_assessments WHERE id = ?",
                (assessment_id,),
            )
            row = cursor.fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Risk Register (P16)
    # ------------------------------------------------------------------

    def upsert_risk(self, data: dict[str, object]) -> None:
        """Insert or replace a risk record."""
        import uuid as _uuid
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO risks
                    (id, project_id, title, description, category,
                     likelihood, impact, risk_score, status, owner,
                     target_date, proximity, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"], data["project_id"], data["title"],
                    data.get("description"), data.get("category", "DELIVERY"),
                    data.get("likelihood", 3), data.get("impact", 3),
                    data.get("risk_score", 9), data.get("status", "OPEN"),
                    data.get("owner"), data.get("target_date"),
                    data.get("proximity"), data.get("notes"),
                    data["created_at"], data["updated_at"],
                ),
            )
            history_id = str(_uuid.uuid4())
            conn.execute(
                """
                INSERT INTO risk_score_history
                    (id, risk_id, project_id, likelihood, impact, risk_score, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    history_id,
                    data["id"],
                    data["project_id"],
                    data.get("likelihood", 3),
                    data.get("impact", 3),
                    data.get("risk_score", 9),
                ),
            )
        logger.debug("risk_upserted", id=data["id"], project_id=data["project_id"])

    def get_risks(
        self,
        project_id: str,
        status_filter: str | None = None,
        category_filter: str | None = None,
    ) -> list[dict[str, object]]:
        """Retrieve risks for a project with optional filters, ordered by risk_score desc."""
        clauses = ["project_id = ?"]
        params: list[object] = [project_id]
        if status_filter:
            clauses.append("status = ?")
            params.append(status_filter)
        if category_filter:
            clauses.append("category = ?")
            params.append(category_filter)
        where = f"WHERE {' AND '.join(clauses)}"
        with self._connect() as conn:
            cursor = conn.execute(
                f"SELECT * FROM risks {where} ORDER BY risk_score DESC, created_at ASC",
                params,
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_risk_by_id(self, risk_id: str) -> dict[str, object] | None:
        """Retrieve a single risk by ID."""
        with self._connect() as conn:
            cursor = conn.execute("SELECT * FROM risks WHERE id = ?", (risk_id,))
            row = cursor.fetchone()
        return dict(row) if row else None

    def update_risk_status(self, risk_id: str, status: str, notes: str | None = None) -> None:
        """Update a risk's status and optionally append notes."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE risks SET status = ?, updated_at = datetime('now')"
                + (", notes = ?" if notes else "")
                + " WHERE id = ?",
                (status, notes, risk_id) if notes else (status, risk_id),
            )
        logger.debug("risk_status_updated", id=risk_id, status=status)

    def upsert_mitigation(self, data: dict[str, object]) -> None:
        """Insert or replace a risk mitigation record."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO risk_mitigations
                    (id, risk_id, project_id, action, owner, target_date,
                     status, effectiveness, residual_likelihood, residual_impact,
                     notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"], data["risk_id"], data["project_id"],
                    data["action"], data.get("owner"), data.get("target_date"),
                    data.get("status", "PLANNED"), data.get("effectiveness"),
                    data.get("residual_likelihood"), data.get("residual_impact"),
                    data.get("notes"), data["created_at"], data["updated_at"],
                ),
            )
        logger.debug("mitigation_upserted", id=data["id"], risk_id=data["risk_id"])

    def get_mitigations(self, risk_id: str) -> list[dict[str, object]]:
        """Retrieve all mitigations for a risk, ordered by created_at."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM risk_mitigations WHERE risk_id = ? ORDER BY created_at ASC",
                (risk_id,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_mitigations_by_project(self, project_id: str) -> list[dict[str, object]]:
        """Retrieve all mitigations for a project, ordered by created_at."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM risk_mitigations WHERE project_id = ? ORDER BY created_at ASC",
                (project_id,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_risk_score_history(self, risk_id: str) -> list[dict]:
        """Return score history for a specific risk, oldest first."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM risk_score_history
                WHERE risk_id = ?
                ORDER BY recorded_at ASC
                """,
                (risk_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_project_risk_history(self, project_id: str) -> list[dict]:
        """Return score history for all risks in a project, oldest first."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT rsh.*, r.title as risk_title, r.category as risk_category
                FROM risk_score_history rsh
                JOIN risks r ON r.id = rsh.risk_id
                WHERE rsh.project_id = ?
                ORDER BY rsh.recorded_at ASC
                """,
                (project_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Change Control Log (P17)
    # ------------------------------------------------------------------

    def upsert_change_request(self, data: dict[str, object]) -> None:
        """Insert or replace a change request record."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO change_requests
                    (id, project_id, title, description, change_type,
                     impact_cost, impact_schedule_days, impact_scope,
                     status, raised_by, approved_by, raised_date,
                     decision_date, implementation_date, notes,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"], data["project_id"], data["title"],
                    data.get("description"), data.get("change_type", "SCOPE"),
                    data.get("impact_cost"), data.get("impact_schedule_days"),
                    data.get("impact_scope"), data.get("status", "SUBMITTED"),
                    data.get("raised_by"), data.get("approved_by"),
                    data["raised_date"], data.get("decision_date"),
                    data.get("implementation_date"), data.get("notes"),
                    data["created_at"], data["updated_at"],
                ),
            )
        logger.debug("change_request_upserted", id=data["id"], project_id=data["project_id"])

    def get_change_requests(
        self,
        project_id: str,
        status_filter: str | None = None,
        change_type_filter: str | None = None,
    ) -> list[dict[str, object]]:
        """Retrieve change requests for a project with optional filters."""
        clauses = ["project_id = ?"]
        params: list[object] = [project_id]
        if status_filter:
            clauses.append("status = ?")
            params.append(status_filter)
        if change_type_filter:
            clauses.append("change_type = ?")
            params.append(change_type_filter)
        where = f"WHERE {' AND '.join(clauses)}"
        with self._connect() as conn:
            cursor = conn.execute(
                f"SELECT * FROM change_requests {where} ORDER BY raised_date ASC",
                params,
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_change_request_by_id(self, change_id: str) -> dict[str, object] | None:
        """Retrieve a single change request by ID."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM change_requests WHERE id = ?", (change_id,)
            )
            row = cursor.fetchone()
        return dict(row) if row else None

    def update_change_status(
        self,
        change_id: str,
        status: str,
        approved_by: str | None = None,
        decision_date: str | None = None,
    ) -> None:
        """Update a change request's status."""
        with self._connect() as conn:
            conn.execute(
                """UPDATE change_requests
                   SET status = ?, approved_by = COALESCE(?, approved_by),
                       decision_date = COALESCE(?, decision_date),
                       updated_at = datetime('now')
                   WHERE id = ?""",
                (status, approved_by, decision_date, change_id),
            )
        logger.debug("change_status_updated", id=change_id, status=status)

    # ------------------------------------------------------------------
    # Resource Plans (P18)
    # ------------------------------------------------------------------

    def upsert_resource_plan(self, data: dict[str, object]) -> None:
        """Insert or replace a resource plan period record."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO resource_plans
                    (id, project_id, resource_name, role, period_start,
                     period_end, planned_days, actual_days, availability_pct,
                     notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"], data["project_id"], data["resource_name"],
                    data.get("role"), data["period_start"], data["period_end"],
                    data.get("planned_days", 0.0), data.get("actual_days"),
                    data.get("availability_pct", 100.0), data.get("notes"),
                    data["created_at"],
                ),
            )
        logger.debug("resource_plan_upserted", id=data["id"], project_id=data["project_id"])

    def get_resource_plans(
        self,
        project_id: str,
        resource_name: str | None = None,
    ) -> list[dict[str, object]]:
        """Retrieve resource plan records for a project."""
        clauses = ["project_id = ?"]
        params: list[object] = [project_id]
        if resource_name:
            clauses.append("resource_name = ?")
            params.append(resource_name)
        where = f"WHERE {' AND '.join(clauses)}"
        with self._connect() as conn:
            cursor = conn.execute(
                f"SELECT * FROM resource_plans {where} ORDER BY period_start ASC",
                params,
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_all_resource_plans(self) -> list[dict[str, object]]:
        """Retrieve all resource plan records across all projects."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM resource_plans ORDER BY project_id, period_start ASC"
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Financial Management (P19)
    # ------------------------------------------------------------------

    def upsert_financial_baseline(self, data: dict[str, object]) -> None:
        """Insert or replace a financial baseline record."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO financial_baselines
                    (id, project_id, label, total_budget, cost_category,
                     period_start, period_end, period_budget, currency,
                     notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"], data["project_id"],
                    data.get("label", "APPROVED"), data["total_budget"],
                    data.get("cost_category", "TOTAL"),
                    data.get("period_start"), data.get("period_end"),
                    data.get("period_budget"), data.get("currency", "GBP"),
                    data.get("notes"), data["created_at"],
                ),
            )
        logger.debug("financial_baseline_upserted", id=data["id"], project_id=data["project_id"])

    def get_financial_baselines(
        self, project_id: str, label: str | None = None
    ) -> list[dict[str, object]]:
        """Retrieve financial baselines for a project."""
        clauses = ["project_id = ?"]
        params: list[object] = [project_id]
        if label:
            clauses.append("label = ?")
            params.append(label)
        where = f"WHERE {' AND '.join(clauses)}"
        with self._connect() as conn:
            cursor = conn.execute(
                f"SELECT * FROM financial_baselines {where} ORDER BY created_at ASC",
                params,
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def upsert_financial_actual(self, data: dict[str, object]) -> None:
        """Insert or replace a financial actuals record for a period."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO financial_actuals
                    (id, project_id, period, actual_spend, cost_category,
                     committed_spend, source, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"], data["project_id"], data["period"],
                    data["actual_spend"], data.get("cost_category", "TOTAL"),
                    data.get("committed_spend"), data.get("source"),
                    data.get("notes"), data["created_at"],
                ),
            )
        logger.debug("financial_actual_upserted", id=data["id"], project_id=data["project_id"])

    def get_financial_actuals(
        self, project_id: str, cost_category: str | None = None
    ) -> list[dict[str, object]]:
        """Retrieve financial actuals for a project, ordered by period ascending."""
        clauses = ["project_id = ?"]
        params: list[object] = [project_id]
        if cost_category:
            clauses.append("cost_category = ?")
            params.append(cost_category)
        where = f"WHERE {' AND '.join(clauses)}"
        with self._connect() as conn:
            cursor = conn.execute(
                f"SELECT * FROM financial_actuals {where} ORDER BY period ASC",
                params,
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def upsert_financial_forecast(self, data: dict[str, object]) -> None:
        """Insert or replace a financial forecast (EAC) record."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO financial_forecasts
                    (id, project_id, forecast_date, eac, method,
                     confidence_pct, p80_estimate, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"], data["project_id"], data["forecast_date"],
                    data["eac"], data.get("method", "MANUAL"),
                    data.get("confidence_pct"), data.get("p80_estimate"),
                    data.get("notes"), data["created_at"],
                ),
            )
        logger.debug("financial_forecast_upserted", id=data["id"], project_id=data["project_id"])

    def get_financial_forecasts(
        self, project_id: str
    ) -> list[dict[str, object]]:
        """Retrieve financial forecasts for a project, ordered by forecast_date ascending."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM financial_forecasts WHERE project_id = ? ORDER BY forecast_date ASC",
                (project_id,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Simulation runs
    # ------------------------------------------------------------------

    def upsert_simulation_run(self, run: dict) -> None:
        """Insert or replace a Monte Carlo simulation run record.

        Args:
            run: Dict with keys matching the ``simulation_runs`` table columns.
                Must include ``id``, ``project_id``, ``simulation_type``,
                ``n_simulations``.  All other columns are optional.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO simulation_runs
                    (id, project_id, simulation_type, n_simulations,
                     p50_days, p80_days, p90_days,
                     p50_date, p80_date, p90_date,
                     mean_duration_days, std_deviation_days,
                     cost_p50, cost_p80, cost_p90,
                     run_at, parameters_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run["id"],
                    run["project_id"],
                    run["simulation_type"],
                    run["n_simulations"],
                    run.get("p50_days"),
                    run.get("p80_days"),
                    run.get("p90_days"),
                    run.get("p50_date"),
                    run.get("p80_date"),
                    run.get("p90_date"),
                    run.get("mean_duration_days"),
                    run.get("std_deviation_days"),
                    run.get("cost_p50"),
                    run.get("cost_p80"),
                    run.get("cost_p90"),
                    run.get("run_at"),
                    run.get("parameters_json"),
                ),
            )
        logger.debug(
            "simulation_run_upserted",
            id=run["id"],
            project_id=run["project_id"],
            simulation_type=run["simulation_type"],
        )

    def get_latest_simulation(
        self, project_id: str, simulation_type: str
    ) -> dict | None:
        """Retrieve the most recent simulation run for a project and type.

        Args:
            project_id: The project identifier.
            simulation_type: The simulation type (e.g. ``"schedule"``).

        Returns:
            A row dict for the latest run, or ``None`` if no run exists.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM simulation_runs
                WHERE project_id = ? AND simulation_type = ?
                ORDER BY run_at DESC
                LIMIT 1
                """,
                (project_id, simulation_type),
            )
            row = cursor.fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Lessons (pm-lessons module)
    # ------------------------------------------------------------------

    def upsert_project_lesson(self, lesson: dict) -> str:
        """Insert or replace a lesson record.

        Args:
            lesson: Dict with keys matching the ``lessons`` table columns.
                Must include ``id``, ``project_id``, ``document_type``,
                ``category``, ``title``, ``recommendation``, ``severity``.
                ``gate``, ``phase``, ``root_cause``, ``source_excerpt`` and
                ``extracted_at`` are optional.

        Returns:
            The ``id`` of the upserted lesson.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO lessons
                    (id, project_id, document_type, gate, phase, category,
                     title, root_cause, recommendation, severity,
                     extracted_at, source_excerpt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lesson["id"],
                    lesson["project_id"],
                    lesson["document_type"],
                    lesson.get("gate"),
                    lesson.get("phase"),
                    lesson["category"],
                    lesson["title"],
                    lesson.get("root_cause"),
                    lesson["recommendation"],
                    lesson.get("severity", "MEDIUM"),
                    lesson.get("extracted_at"),
                    lesson.get("source_excerpt"),
                ),
            )
        logger.debug(
            "lesson_persisted",
            id=lesson["id"],
            project_id=lesson["project_id"],
        )
        return lesson["id"]

    def get_project_lessons(
        self,
        project_id: str,
        category: str | None = None,
        gate: str | None = None,
    ) -> list[dict]:
        """Retrieve all stored lessons for a project with optional filters.

        Args:
            project_id: The project identifier.
            category: Optional category filter (e.g. ``"GOVERNANCE"``).
            gate: Optional gate filter (e.g. ``"GATE_2"``).

        Returns:
            List of lesson row dicts ordered by extracted_at ascending.
        """
        conditions = ["project_id = ?"]
        params: list = [project_id]
        if category is not None:
            conditions.append("category = ?")
            params.append(category)
        if gate is not None:
            conditions.append("gate = ?")
            params.append(gate)

        where_clause = " AND ".join(conditions)
        with self._connect() as conn:
            cursor = conn.execute(
                f"SELECT * FROM lessons WHERE {where_clause} ORDER BY extracted_at ASC",
                params,
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_all_lessons(self, category: str | None = None) -> list[dict]:
        """Retrieve all lessons across all projects with an optional category filter.

        Args:
            category: Optional category filter (e.g. ``"COMMERCIAL"``).

        Returns:
            List of lesson row dicts ordered by extracted_at ascending.
        """
        if category is not None:
            with self._connect() as conn:
                cursor = conn.execute(
                    "SELECT * FROM lessons WHERE category = ? ORDER BY extracted_at ASC",
                    (category,),
                )
                rows = cursor.fetchall()
        else:
            with self._connect() as conn:
                cursor = conn.execute(
                    "SELECT * FROM lessons ORDER BY extracted_at ASC",
                )
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def search_lessons(self, query: str) -> list[dict]:
        """Keyword search across title, root_cause, and recommendation fields.

        Args:
            query: Free-text search string.  Simple ``LIKE`` matching is used;
                no vector/semantic search is performed.

        Returns:
            List of matching lesson row dicts ordered by extracted_at ascending.
        """
        pattern = f"%{query}%"
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM lessons
                WHERE title LIKE ?
                   OR root_cause LIKE ?
                   OR recommendation LIKE ?
                ORDER BY extracted_at ASC
                """,
                (pattern, pattern, pattern),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]
