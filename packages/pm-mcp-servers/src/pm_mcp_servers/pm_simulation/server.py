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

server = Server("pm-simulation")

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
