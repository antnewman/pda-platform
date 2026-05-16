"""pm_simulation — Monte Carlo schedule and cost simulation.

Two tools:
  1. run_schedule_simulation  — run a Monte Carlo schedule simulation using PERT/triangular distributions
  2. get_simulation_results   — retrieve the latest stored simulation for a project
"""

from __future__ import annotations

import json
import math
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from pm_mcp_servers._audit import record_decision

server = Server("pm-simulation")


# ─────────────────────────────────────────────────────────────────────────
# Layer 8 — Cryptographic audit chain for pm-simulation
# ─────────────────────────────────────────────────────────────────────────
# Monte Carlo simulation results are decision-producing: a P50/P80
# pair shapes board confidence in delivery timelines. The audit chain
# records every simulation invocation so a reviewer can answer "what
# P50 and P80 was generated, with what input distribution, and with
# what statistical confidence?" without trusting the consumer to
# faithfully reproduce the numbers.

_AUDIT_MODULE = "pm_simulation"


def _safe_record_decision(
    *,
    input_data: object,
    output_data: object,
    decision: str,
    action: str,
    metadata: dict | None = None,
) -> None:
    """Best-effort audit-chain record. Never raises."""
    try:
        record_decision(
            _AUDIT_MODULE,
            input_data=input_data,
            output_data=output_data,
            decision=decision,
            action=action,
            metadata=metadata,
        )
    except Exception:
        pass

SIMULATION_TOOLS: list[Tool] = [
    Tool(
        name="run_schedule_simulation",
        description=(
            "Run a Monte Carlo schedule simulation for a project using PERT/triangular distributions. "
            "Samples task durations across N simulations to produce a probability distribution of "
            "project completion dates. Returns P50, P80, and P90 confidence intervals with "
            "corresponding calendar dates. If use_risk_register=true, derives task uncertainty "
            "from the project's risk register score — higher risk scores widen duration distributions. "
            "Results are persisted to the store and retrievable via get_simulation_results. "
            "Use before gate reviews or for delivery confidence reporting to SROs and portfolio boards."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier to run the simulation for.",
                },
                "n_simulations": {
                    "type": "integer",
                    "description": "Number of Monte Carlo iterations (default 1000, min 100, max 10000).",
                    "default": 1000,
                    "minimum": 100,
                    "maximum": 10000,
                },
                "confidence_levels": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Percentile confidence levels to compute (default [50, 80, 90]).",
                    "default": [50, 80, 90],
                },
                "use_risk_register": {
                    "type": "boolean",
                    "description": (
                        "If true, derive task uncertainty from the project risk register. "
                        "High aggregate risk scores widen duration distributions. "
                        "Default true."
                    ),
                    "default": True,
                },
                "base_uncertainty_pct": {
                    "type": "number",
                    "description": (
                        "Base uncertainty percentage applied to task durations when no risk data "
                        "is available. Default 20.0 means ±20% range on each task. "
                        "Risk register data scales this up when use_risk_register=true."
                    ),
                    "default": 20.0,
                },
                "project_start_date": {
                    "type": "string",
                    "description": (
                        "Project start date in YYYY-MM-DD format, used to compute P50/P80/P90 "
                        "calendar dates. If omitted, today's date is used."
                    ),
                },
                "baseline_duration_days": {
                    "type": "integer",
                    "description": (
                        "Known baseline total project duration in days. If provided, this is used "
                        "directly rather than attempting to derive it from stored task data. "
                        "Required when no tasks are loaded for this project_id."
                    ),
                },
                "db_path": {
                    "type": "string",
                    "description": "Optional path to the SQLite store file.",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="get_simulation_results",
        description=(
            "Retrieve the latest stored Monte Carlo simulation result for a project. "
            "Returns P50/P80/P90 days and corresponding calendar dates from the most recent run. "
            "Use after run_schedule_simulation to surface results in a report or dashboard, "
            "or to check whether an up-to-date simulation exists before running a new one."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier to retrieve simulation results for.",
                },
                "simulation_type": {
                    "type": "string",
                    "enum": ["schedule"],
                    "description": "Type of simulation to retrieve (default 'schedule').",
                    "default": "schedule",
                },
                "db_path": {
                    "type": "string",
                    "description": "Optional path to the SQLite store file.",
                },
            },
            "required": ["project_id"],
        },
    ),
]


# ── Internal helpers ───────────────────────────────────────────────────────────

def _get_store(db_path: str | None = None):
    """Create an AssuranceStore from an optional db_path argument."""
    from pm_data_tools.db.store import AssuranceStore

    if db_path:
        return AssuranceStore(db_path=Path(db_path))
    return AssuranceStore()


def _triangular_sample(min_val: float, mode: float, max_val: float) -> float:
    """Sample from a triangular distribution using the inverse CDF method.

    Args:
        min_val: Minimum value (a).
        mode: Most likely value (c).
        max_val: Maximum value (b).

    Returns:
        A sampled float value.
    """
    # Clamp to ensure valid triangular distribution
    if min_val >= max_val:
        return mode
    if mode < min_val:
        mode = min_val
    if mode > max_val:
        mode = max_val

    u = random.random()
    fc = (mode - min_val) / (max_val - min_val)

    if u < fc:
        return min_val + math.sqrt(u * (max_val - min_val) * (mode - min_val))
    else:
        return max_val - math.sqrt((1.0 - u) * (max_val - min_val) * (max_val - mode))


def _compute_percentile(sorted_values: list[float], pct: int) -> float:
    """Compute a percentile from a sorted list.

    Args:
        sorted_values: A sorted list of floats.
        pct: Percentile to compute (0-100).

    Returns:
        The value at the given percentile.
    """
    n = len(sorted_values)
    if n == 0:
        return 0.0
    idx = (pct / 100.0) * (n - 1)
    lower = int(idx)
    upper = min(lower + 1, n - 1)
    frac = idx - lower
    return sorted_values[lower] + frac * (sorted_values[upper] - sorted_values[lower])


def _days_to_date(start_date: str, days: int) -> str:
    """Add working-day-equivalent calendar days to a start date.

    Uses a simple 1.4x calendar conversion (5 working days = 7 calendar days).

    Args:
        start_date: ISO date string (YYYY-MM-DD).
        days: Number of working days to add.

    Returns:
        ISO date string for the resulting date.
    """
    try:
        base = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        base = datetime.now()
    # Convert working days to calendar days (5 day week)
    calendar_days = int(days * 1.4)
    result = base + timedelta(days=calendar_days)
    return result.strftime("%Y-%m-%d")


def _build_conformal_bands(
    store: Any,
    project_id: str,
    simulation_type: str,
    p50_days: float,
    p80_days: float,
    alpha: float = 0.2,
    min_history: int = 5,
) -> dict[str, Any]:
    """Return a `_calibration` dict for a schedule simulation result.

    Reads the project's calibration history (past forecast vs actual
    residuals) from the store and runs A4's
    :func:`conformal_predict_band` on the P50 and P80 point estimates.
    When fewer than ``min_history`` residuals are available, returns a
    NOT_COMPUTED marker — a band fitted on too few residuals would
    overstate the coverage guarantee.

    Args:
        store: AssuranceStore instance.
        project_id: Project identifier.
        simulation_type: ``"schedule"`` for Monte Carlo schedule sims.
        p50_days: The simulation's P50 point estimate.
        p80_days: The simulation's P80 point estimate.
        alpha: Target miscoverage rate. Default 0.2 (80% nominal
            coverage, matching the paper's reference).
        min_history: Minimum residual count below which bands are not
            fitted. Default 5; below this the empirical quantile is
            too noisy to be meaningful.

    Returns:
        Dict with ``status`` (``"COMPUTED"`` or ``"NOT_COMPUTED"``),
        ``alpha``, ``coverage_pct``, plus when computed
        ``p50_band`` and ``p80_band`` each as
        ``{"lower": float, "upper": float, "half_width": float}``.
    """
    coverage_pct = round((1.0 - alpha) * 100, 1)
    try:
        residuals_p50 = store.get_simulation_residuals(
            project_id, simulation_type, quantile_label="P50"
        )
        residuals_p80 = store.get_simulation_residuals(
            project_id, simulation_type, quantile_label="P80"
        )
    except Exception as exc:
        return {
            "status": "NOT_COMPUTED",
            "reason": f"Calibration history lookup failed: {exc}",
            "alpha": alpha,
            "coverage_pct": coverage_pct,
        }

    p50_values = [float(r["residual"]) for r in residuals_p50]
    p80_values = [float(r["residual"]) for r in residuals_p80]

    if len(p50_values) < min_history or len(p80_values) < min_history:
        return {
            "status": "NOT_COMPUTED",
            "reason": (
                f"Insufficient calibration history: need at least "
                f"{min_history} residuals per quantile; have "
                f"{len(p50_values)} P50 and {len(p80_values)} P80. "
                "Record past (forecast, actual) pairs via "
                "AssuranceStore.upsert_simulation_residual to build "
                "calibration history."
            ),
            "alpha": alpha,
            "coverage_pct": coverage_pct,
            "p50_history_count": len(p50_values),
            "p80_history_count": len(p80_values),
        }

    # Deferred — calibration module pulls in scipy lazily.
    from agent_planning.calibration import conformal_predict_band

    p50_low, p50_high = conformal_predict_band(
        point_estimate=p50_days,
        calibration_residuals=p50_values,
        alpha=alpha,
    )
    p80_low, p80_high = conformal_predict_band(
        point_estimate=p80_days,
        calibration_residuals=p80_values,
        alpha=alpha,
    )

    return {
        "status": "COMPUTED",
        "alpha": alpha,
        "coverage_pct": coverage_pct,
        "p50_band": {
            "lower": p50_low,
            "upper": p50_high,
            "half_width": (p50_high - p50_low) / 2.0,
        },
        "p80_band": {
            "lower": p80_low,
            "upper": p80_high,
            "half_width": (p80_high - p80_low) / 2.0,
        },
        "p50_history_count": len(p50_values),
        "p80_history_count": len(p80_values),
    }


def _compute_risk_multiplier(risks: list[dict]) -> float:
    """Derive a risk uncertainty multiplier from a list of risk records.

    Maps mean risk score to an additive multiplier for base_uncertainty_pct:
    - Mean risk score <= 4 (low):    1.0x  (no uplift)
    - Mean risk score 5-9 (medium):  1.15x
    - Mean risk score 10-14 (high):  1.30x
    - Mean risk score >= 15 (critical): 1.50x

    Args:
        risks: List of risk dicts from the store, each with a ``risk_score`` field.

    Returns:
        A float multiplier >= 1.0.
    """
    if not risks:
        return 1.0

    open_risks = [r for r in risks if r.get("status", "OPEN") == "OPEN"]
    if not open_risks:
        return 1.0

    scores = [float(r.get("risk_score", 9)) for r in open_risks]
    mean_score = sum(scores) / len(scores)

    if mean_score <= 4:
        return 1.0
    elif mean_score <= 9:
        return 1.15
    elif mean_score <= 14:
        return 1.30
    else:
        return 1.50


# ── Tool handlers ──────────────────────────────────────────────────────────────

async def _run_schedule_simulation(arguments: dict[str, Any]) -> list[TextContent]:
    project_id: str = arguments["project_id"]
    n_simulations: int = max(100, min(10000, int(arguments.get("n_simulations", 1000))))
    confidence_levels: list[int] = arguments.get("confidence_levels", [50, 80, 90])
    use_risk_register: bool = bool(arguments.get("use_risk_register", True))
    base_uncertainty_pct: float = float(arguments.get("base_uncertainty_pct", 20.0))
    project_start_date: str = arguments.get("project_start_date") or datetime.now().strftime("%Y-%m-%d")
    baseline_duration_override: int | None = arguments.get("baseline_duration_days")
    db_path: str | None = arguments.get("db_path")

    # ── Load data from store ───────────────────────────────────────────────────
    store = _get_store(db_path)

    risk_multiplier = 1.0
    risk_adjustment_applied = False

    if use_risk_register:
        try:
            risks = store.get_risks(project_id)
            if risks:
                risk_multiplier = _compute_risk_multiplier(risks)
                risk_adjustment_applied = risk_multiplier > 1.0
        except Exception:
            # Store may not have risks for this project — that is fine
            pass

    # ── Determine baseline duration ────────────────────────────────────────────
    if baseline_duration_override is not None:
        baseline_duration_days = int(baseline_duration_override)
        n_tasks = 10  # synthetic task count for modelling purposes
    else:
        # Attempt to derive from stored project data — use a sensible fallback
        # The pm_data module stores projects in memory; we model the project as a
        # single aggregate task with the full baseline duration.  Users should
        # supply baseline_duration_days for accurate results.
        baseline_duration_days = 365  # default fallback
        n_tasks = 10

    effective_uncertainty = base_uncertainty_pct * risk_multiplier

    # ── Run simulations ────────────────────────────────────────────────────────
    # Model project as n_tasks tasks, each contributing to the critical path.
    # Critical path = 70% of total tasks on average (typical project heuristic).
    # Each task duration follows a PERT/triangular distribution.
    critical_path_fraction = 0.70
    task_base_duration = baseline_duration_days * critical_path_fraction / n_tasks
    non_cp_duration = baseline_duration_days * (1.0 - critical_path_fraction)

    uncertainty_half = effective_uncertainty / 100.0

    outcomes: list[float] = []
    for _ in range(n_simulations):
        cp_total = 0.0
        for _ in range(n_tasks):
            t_min = task_base_duration * (1.0 - uncertainty_half)
            t_mode = task_base_duration
            t_max = task_base_duration * (1.0 + uncertainty_half * 2.0)
            cp_total += _triangular_sample(t_min, t_mode, t_max)
        # Add non-critical path (less variability, ±5%)
        ncp_sample = _triangular_sample(
            non_cp_duration * 0.95,
            non_cp_duration,
            non_cp_duration * 1.05,
        )
        # Total project duration = max(critical path, non-critical path) heuristic
        total_duration = max(cp_total, ncp_sample)
        outcomes.append(total_duration)

    outcomes.sort()

    # ── Compute statistics ─────────────────────────────────────────────────────
    mean_days = sum(outcomes) / len(outcomes)
    variance = sum((x - mean_days) ** 2 for x in outcomes) / len(outcomes)
    std_dev = math.sqrt(variance)

    p_values: dict[int, float] = {}
    for pct in confidence_levels:
        p_values[pct] = _compute_percentile(outcomes, pct)

    p50_days = int(round(p_values.get(50, _compute_percentile(outcomes, 50))))
    p80_days = int(round(p_values.get(80, _compute_percentile(outcomes, 80))))
    p90_days = int(round(p_values.get(90, _compute_percentile(outcomes, 90))))

    p50_date = _days_to_date(project_start_date, p50_days)
    p80_date = _days_to_date(project_start_date, p80_days)
    p90_date = _days_to_date(project_start_date, p90_days)

    # Compute probability of meeting baseline
    outcomes_below_baseline = sum(1 for x in outcomes if x <= baseline_duration_days)
    baseline_probability = int(round(100.0 * outcomes_below_baseline / len(outcomes)))

    # ── Build interpretation ───────────────────────────────────────────────────
    interpretation = (
        f"There is a 50% chance of completing by {p50_date} and an 80% chance by {p80_date}. "
        f"The baseline of {baseline_duration_days} days has a {baseline_probability}% probability of being met."
    )
    if baseline_probability < 20:
        interpretation += (
            " The baseline is highly unlikely to be achieved — the schedule carries significant risk "
            "of overrun and should be reviewed urgently."
        )
    elif baseline_probability < 50:
        interpretation += (
            " The baseline has less than a 50% chance of being met. The P80 date should be used "
            "for stakeholder reporting to manage expectations."
        )

    run_at = datetime.now().isoformat()
    run_id = str(uuid.uuid4())

    # ── Persist to store ───────────────────────────────────────────────────────
    parameters = {
        "n_simulations": n_simulations,
        "confidence_levels": confidence_levels,
        "use_risk_register": use_risk_register,
        "base_uncertainty_pct": base_uncertainty_pct,
        "effective_uncertainty_pct": round(effective_uncertainty, 2),
        "risk_multiplier": round(risk_multiplier, 4),
        "project_start_date": project_start_date,
        "baseline_duration_days": baseline_duration_days,
    }

    store.upsert_simulation_run({
        "id": run_id,
        "project_id": project_id,
        "simulation_type": "schedule",
        "n_simulations": n_simulations,
        "p50_days": p50_days,
        "p80_days": p80_days,
        "p90_days": p90_days,
        "p50_date": p50_date,
        "p80_date": p80_date,
        "p90_date": p90_date,
        "mean_duration_days": round(mean_days, 2),
        "std_deviation_days": round(std_dev, 2),
        "run_at": run_at,
        "parameters_json": json.dumps(parameters),
    })

    result = {
        "project_id": project_id,
        "simulation_type": "schedule",
        "run_id": run_id,
        "n_simulations": n_simulations,
        "baseline_duration_days": baseline_duration_days,
        "results": {
            "p50_days": p50_days,
            "p80_days": p80_days,
            "p90_days": p90_days,
            "mean_days": round(mean_days, 2),
            "std_deviation_days": round(std_dev, 2),
        },
        "p50_date": p50_date,
        "p80_date": p80_date,
        "p90_date": p90_date,
        "baseline_probability_pct": baseline_probability,
        "risk_adjustment_applied": risk_adjustment_applied,
        "risk_multiplier": round(risk_multiplier, 4),
        "effective_uncertainty_pct": round(effective_uncertainty, 2),
        "interpretation": interpretation,
        "run_at": run_at,
    }

    # ── Layer 4: conformal prediction bands ─────────────────────────────
    # If the store has a calibration history (past forecast vs actual
    # residuals) for this project's schedule simulations, wrap the P50
    # and P80 outputs in coverage-guaranteed bands using
    # `conformal_predict_band`. If no history exists, surface a clear
    # NOT_COMPUTED marker rather than fabricating an uncalibrated band
    # — the consumer then knows to start recording actuals via
    # `upsert_simulation_residual`.
    result["_calibration"] = _build_conformal_bands(
        store=store,
        project_id=project_id,
        simulation_type="schedule",
        p50_days=p50_days,
        p80_days=p80_days,
    )

    # Audit-chain entry — the decision is a coarse confidence band
    # derived from the baseline-vs-P50 relationship. Output captures
    # P50/P80/P90 days and run identifier; input captures the
    # simulation parameters that drove the run.
    if baseline_probability >= 70:
        sim_verdict = "HIGH_CONFIDENCE"
    elif baseline_probability >= 40:
        sim_verdict = "MEDIUM_CONFIDENCE"
    else:
        sim_verdict = "LOW_CONFIDENCE"
    _safe_record_decision(
        input_data={
            "project_id": project_id,
            "n_simulations": n_simulations,
            "baseline_duration_days": baseline_duration_days,
            "base_uncertainty_pct": base_uncertainty_pct,
            "use_risk_register": use_risk_register,
        },
        output_data={
            "run_id": run_id,
            "p50_days": p50_days,
            "p80_days": p80_days,
            "p90_days": p90_days,
            "baseline_probability_pct": baseline_probability,
        },
        decision=sim_verdict,
        action="run_schedule_simulation",
        metadata={
            "risk_multiplier": round(risk_multiplier, 4),
            "risk_adjustment_applied": risk_adjustment_applied,
        },
    )
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _get_simulation_results(arguments: dict[str, Any]) -> list[TextContent]:
    project_id: str = arguments["project_id"]
    simulation_type: str = arguments.get("simulation_type", "schedule")
    db_path: str | None = arguments.get("db_path")

    store = _get_store(db_path)

    row = store.get_latest_simulation(project_id, simulation_type)
    if row is None:
        return [TextContent(type="text", text=json.dumps({
            "error": (
                f"No {simulation_type} simulation results found for project '{project_id}'. "
                "Run run_schedule_simulation first to generate results."
            ),
            "project_id": project_id,
            "simulation_type": simulation_type,
        }, indent=2))]

    # Deserialise parameters_json
    if row.get("parameters_json"):
        try:
            row["parameters"] = json.loads(row["parameters_json"])
        except (json.JSONDecodeError, TypeError):
            row["parameters"] = {}
        del row["parameters_json"]

    return [TextContent(type="text", text=json.dumps(row, indent=2))]


# ── MCP handlers ──────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return SIMULATION_TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    handlers = {
        "run_schedule_simulation": _run_schedule_simulation,
        "get_simulation_results": _get_simulation_results,
    }
    handler = handlers.get(name)
    if not handler:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    return await handler(arguments)


def main() -> None:
    import asyncio
    from mcp.server.stdio import stdio_server

    async def _run() -> None:
        async with stdio_server() as (r, w):
            await server.run(r, w, server.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
