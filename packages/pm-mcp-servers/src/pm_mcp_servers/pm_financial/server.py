"""PM-Financial MCP server — Financial Management tools (P19).

Tools:
  1. set_financial_baseline   — Set the approved budget envelope (BAC/WLC) for a project
  2. log_financial_actuals    — Record actual spend for a period with variance analysis
  3. get_cost_performance     — Core financial health: variance, EAC, VAC, RAG status, S-curve
  4. log_cost_forecast        — Record a point-in-time EAC forecast with VAC assessment
  5. get_spend_profile        — Full spend S-curve with run rate and projected outturn
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

FINANCIAL_TOOLS: list[Tool] = [
    Tool(
        name="set_financial_baseline",
        description=(
            "Set the approved budget envelope (Budget at Completion / Whole Life Cost) "
            "for a project. A project may hold multiple baseline records — for example "
            "one TOTAL and several by cost category (CAPEX, OPEX, PEOPLE), or an "
            "INITIAL and a REVISED baseline following a scope change. Conforms to "
            "IPA/Green Book financial management requirements."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "total_budget": {
                    "type": "number",
                    "description": "Approved whole life cost (WLC) in the specified currency.",
                },
                "label": {
                    "type": "string",
                    "enum": ["APPROVED", "REVISED", "INITIAL"],
                    "description": "Baseline label. Defaults to APPROVED.",
                    "default": "APPROVED",
                },
                "cost_category": {
                    "type": "string",
                    "enum": ["TOTAL", "CAPEX", "OPEX", "PEOPLE", "CONTINGENCY"],
                    "description": "Cost category this baseline applies to. Defaults to TOTAL.",
                    "default": "TOTAL",
                },
                "period_start": {
                    "type": "string",
                    "description": "ISO date — start of the baseline period (optional).",
                },
                "period_end": {
                    "type": "string",
                    "description": "ISO date — end of the baseline period (optional).",
                },
                "period_budget": {
                    "type": "number",
                    "description": "Budget allocated to this specific period (optional).",
                },
                "currency": {
                    "type": "string",
                    "description": "ISO 4217 currency code. Defaults to GBP.",
                    "default": "GBP",
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes on this baseline (e.g. change control reference).",
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": ["project_id", "total_budget"],
        },
    ),
    Tool(
        name="log_financial_actuals",
        description=(
            "Record actual spend for a reporting period. Computes variance against "
            "the approved baseline and returns a budget status (UNDER_BUDGET, "
            "ON_BUDGET, OVER_BUDGET). Also captures committed spend — amounts "
            "contractually committed but not yet invoiced."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "period": {
                    "type": "string",
                    "description": (
                        "ISO date — the period end date "
                        "(e.g. '2026-03-31' for Q4 FY25/26)."
                    ),
                },
                "actual_spend": {
                    "type": "number",
                    "description": "Actual spend recorded for this period.",
                },
                "cost_category": {
                    "type": "string",
                    "enum": ["TOTAL", "CAPEX", "OPEX", "PEOPLE", "CONTINGENCY"],
                    "description": "Cost category. Defaults to TOTAL.",
                    "default": "TOTAL",
                },
                "committed_spend": {
                    "type": "number",
                    "description": (
                        "Spend committed but not yet invoiced — "
                        "included in total exposure calculation."
                    ),
                },
                "source": {
                    "type": "string",
                    "description": (
                        "Data source for this return "
                        "(e.g. 'Oracle Financials', 'Manual return')."
                    ),
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes on this actuals entry.",
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": ["project_id", "period", "actual_spend"],
        },
    ),
    Tool(
        name="get_cost_performance",
        description=(
            "Core financial health assessment for a project. Returns approved budget "
            "(BAC), cumulative actual spend, committed spend, total exposure, "
            "budget variance, Estimate at Completion (EAC), Variance at Completion "
            "(VAC), cost RAG status, spend profile (S-curve data), and forecast trend. "
            "Requires set_financial_baseline to be called first."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "cost_category": {
                    "type": "string",
                    "description": (
                        "Filter to a specific cost category. Defaults to TOTAL."
                    ),
                    "default": "TOTAL",
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="log_cost_forecast",
        description=(
            "Record a point-in-time Estimate at Completion (EAC). Computes "
            "Variance at Completion (VAC) against the approved budget and returns "
            "a plain-English assessment. Supports multiple forecasting methods: "
            "MANUAL, CPI_BASED (earned value), REGRESSION, and STATISTICAL."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "eac": {
                    "type": "number",
                    "description": "Estimate at Completion — forecast whole life cost.",
                },
                "method": {
                    "type": "string",
                    "enum": ["MANUAL", "CPI_BASED", "REGRESSION", "STATISTICAL"],
                    "description": "Forecasting method used. Defaults to MANUAL.",
                    "default": "MANUAL",
                },
                "confidence_pct": {
                    "type": "number",
                    "description": (
                        "Confidence percentile for this estimate "
                        "(e.g. 70.0 for a P70 estimate)."
                    ),
                },
                "p80_estimate": {
                    "type": "number",
                    "description": (
                        "Separate P80 cost estimate if available "
                        "(80th percentile outturn cost)."
                    ),
                },
                "forecast_date": {
                    "type": "string",
                    "description": "ISO date — defaults to today.",
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes on this forecast.",
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": ["project_id", "eac"],
        },
    ),
    Tool(
        name="get_spend_profile",
        description=(
            "Produce a complete spend S-curve for a project. Returns all reported "
            "actuals as a time series with cumulative spend, the approved budget "
            "(BAC), latest EAC, run rate, months remaining at run rate, and "
            "projected outturn classification (WITHIN_BUDGET / AT_RISK / OVER_BUDGET)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "include_forecast": {
                    "type": "boolean",
                    "description": (
                        "Whether to project forward using the latest EAC. "
                        "Defaults to true."
                    ),
                    "default": True,
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": ["project_id"],
        },
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_store(arguments: dict[str, Any]) -> Any:
    """Create an AssuranceStore from optional db_path argument."""
    from pm_data_tools.db.store import AssuranceStore

    raw_db_path = arguments.get("db_path")
    db_path = Path(raw_db_path) if raw_db_path else None
    return AssuranceStore(db_path=db_path)


def _today_iso() -> str:
    return date.today().isoformat()


def _round2(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 2)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def _set_financial_baseline(arguments: dict[str, Any]) -> list[TextContent]:
    """Set the approved budget envelope for a project."""
    try:
        store = _get_store(arguments)

        project_id = arguments["project_id"]
        total_budget = float(arguments["total_budget"])
        label = arguments.get("label", "APPROVED")
        cost_category = arguments.get("cost_category", "TOTAL")
        currency = arguments.get("currency", "GBP")

        data = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "label": label,
            "total_budget": total_budget,
            "cost_category": cost_category,
            "period_start": arguments.get("period_start"),
            "period_end": arguments.get("period_end"),
            "period_budget": arguments.get("period_budget"),
            "currency": currency,
            "notes": arguments.get("notes"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        store.upsert_financial_baseline(data)

        output = {
            "status": "success",
            "baseline_id": data["id"],
            "project_id": project_id,
            "label": label,
            "cost_category": cost_category,
            "total_budget": round(total_budget, 2),
            "currency": currency,
            "period_start": data["period_start"],
            "period_end": data["period_end"],
            "period_budget": _round2(data["period_budget"]),
            "notes": data["notes"],
            "created_at": data["created_at"],
            "message": (
                f"Approved budget of \u00a3{total_budget:,.0f} ({currency}) "
                f"set for project {project_id}."
            ),
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _log_financial_actuals(arguments: dict[str, Any]) -> list[TextContent]:
    """Record actual spend for a period with variance analysis."""
    try:
        store = _get_store(arguments)

        project_id = arguments["project_id"]
        period = arguments["period"]
        actual_spend = float(arguments["actual_spend"])
        cost_category = arguments.get("cost_category", "TOTAL")
        committed_spend = (
            float(arguments["committed_spend"])
            if arguments.get("committed_spend") is not None
            else None
        )

        data = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "period": period,
            "actual_spend": actual_spend,
            "cost_category": cost_category,
            "committed_spend": committed_spend,
            "source": arguments.get("source"),
            "notes": arguments.get("notes"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        store.upsert_financial_actual(data)

        output: dict[str, Any] = {
            "status": "success",
            "actual_id": data["id"],
            "project_id": project_id,
            "period": period,
            "actual_spend": round(actual_spend, 2),
            "cost_category": cost_category,
            "committed_spend": _round2(committed_spend),
            "source": data["source"],
            "notes": data["notes"],
            "created_at": data["created_at"],
        }

        # Variance analysis against approved baseline
        baselines = store.get_financial_baselines(
            project_id, label="APPROVED"
        )
        # Filter to matching cost category
        matching = [
            b for b in baselines if b.get("cost_category") == cost_category
        ]

        if matching:
            baseline = matching[0]
            bac = float(baseline["total_budget"])
            if bac != 0:
                variance = bac - actual_spend
                variance_pct = (variance / bac) * 100
            else:
                variance = 0.0
                variance_pct = 0.0

            if bac != 0 and abs(variance_pct) <= 1.0:
                status = "ON_BUDGET"
            elif variance > 0:
                status = "UNDER_BUDGET"
            else:
                status = "OVER_BUDGET"

            output["variance_analysis"] = {
                "approved_budget": round(bac, 2),
                "variance": round(variance, 2),
                "variance_pct": round(variance_pct, 2),
                "status": status,
            }
            output["message"] = (
                f"Actuals of \u00a3{actual_spend:,.0f} recorded for period {period}. "
                f"Budget variance: \u00a3{variance:,.0f} ({variance_pct:.1f}%) — {status}."
            )
        else:
            output["variance_analysis"] = None
            output["message"] = (
                f"Actuals of \u00a3{actual_spend:,.0f} recorded for period {period}. "
                f"No APPROVED baseline found for category {cost_category} — "
                f"call set_financial_baseline to enable variance analysis."
            )

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _get_cost_performance(arguments: dict[str, Any]) -> list[TextContent]:
    """Core financial health assessment."""
    try:
        store = _get_store(arguments)

        project_id = arguments["project_id"]
        cost_category = arguments.get("cost_category", "TOTAL")

        # --- Baseline ---
        baselines = store.get_financial_baselines(project_id, label="APPROVED")
        matching_baselines = [
            b for b in baselines if b.get("cost_category") == cost_category
        ]

        if not matching_baselines:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": "error",
                            "project_id": project_id,
                            "message": (
                                f"No APPROVED baseline found for project {project_id} "
                                f"(category: {cost_category}). "
                                f"Call set_financial_baseline first."
                            ),
                        },
                        indent=2,
                    ),
                )
            ]

        baseline = matching_baselines[0]
        bac = float(baseline["total_budget"])

        # --- Actuals ---
        actuals = store.get_financial_actuals(
            project_id, cost_category=cost_category
        )
        actuals_sorted = sorted(actuals, key=lambda r: r.get("period", ""))

        total_actual_spend = sum(float(r["actual_spend"]) for r in actuals_sorted)
        total_committed = sum(
            float(r["committed_spend"])
            for r in actuals_sorted
            if r.get("committed_spend") is not None
        )
        total_exposure = total_actual_spend + total_committed

        # Budget variance
        if bac != 0:
            budget_variance = bac - total_actual_spend
            budget_variance_pct = (budget_variance / bac) * 100
        else:
            budget_variance = 0.0
            budget_variance_pct = 0.0

        # --- Forecasts ---
        forecasts = store.get_financial_forecasts(project_id)
        forecasts_sorted = sorted(
            forecasts, key=lambda r: r.get("forecast_date", "")
        )

        latest_eac: float | None = None
        vac: float | None = None
        if forecasts_sorted:
            latest_eac = float(forecasts_sorted[-1]["eac"])
            vac = bac - latest_eac if bac != 0 else None

        # --- RAG status ---
        if bac != 0:
            if latest_eac is not None:
                # EAC-based RAG
                if latest_eac > bac:
                    cost_status = "RED"
                elif budget_variance_pct < -5.0:
                    cost_status = "RED"
                elif abs(budget_variance_pct) <= 5.0:
                    cost_status = "AMBER"
                else:
                    cost_status = "GREEN"
            else:
                if budget_variance_pct < -5.0:
                    cost_status = "RED"
                elif abs(budget_variance_pct) <= 5.0:
                    cost_status = "AMBER"
                else:
                    cost_status = "GREEN"
        else:
            cost_status = "AMBER"

        # --- Spend profile (S-curve) ---
        cumulative = 0.0
        spend_profile = []
        for r in actuals_sorted:
            spend = float(r["actual_spend"])
            cumulative += spend
            spend_profile.append(
                {
                    "period": r.get("period"),
                    "actual_spend": round(spend, 2),
                    "cumulative_spend": round(cumulative, 2),
                }
            )

        # --- Forecast trend ---
        forecast_trend: str | None = None
        if len(forecasts_sorted) >= 2:
            first_eac = float(forecasts_sorted[0]["eac"])
            last_eac = float(forecasts_sorted[-1]["eac"])
            diff_pct = (
                ((last_eac - first_eac) / first_eac * 100) if first_eac != 0 else 0.0
            )
            if diff_pct > 2.0:
                forecast_trend = "INCREASING"
            elif diff_pct < -2.0:
                forecast_trend = "DECREASING"
            else:
                forecast_trend = "STABLE"

        periods_reported = len({r.get("period") for r in actuals_sorted if r.get("period")})

        output = {
            "status": "success",
            "project_id": project_id,
            "cost_category": cost_category,
            "approved_budget": round(bac, 2),
            "total_actual_spend": round(total_actual_spend, 2),
            "total_committed": round(total_committed, 2),
            "total_exposure": round(total_exposure, 2),
            "budget_variance": round(budget_variance, 2),
            "budget_variance_pct": round(budget_variance_pct, 2),
            "latest_eac": _round2(latest_eac),
            "vac": _round2(vac),
            "cost_status": cost_status,
            "spend_profile": spend_profile,
            "forecast_trend": forecast_trend,
            "periods_reported": periods_reported,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _log_cost_forecast(arguments: dict[str, Any]) -> list[TextContent]:
    """Record a point-in-time EAC forecast."""
    try:
        store = _get_store(arguments)

        project_id = arguments["project_id"]
        eac = float(arguments["eac"])
        method = arguments.get("method", "MANUAL")
        forecast_date = arguments.get("forecast_date") or _today_iso()
        confidence_pct = (
            float(arguments["confidence_pct"])
            if arguments.get("confidence_pct") is not None
            else None
        )
        p80_estimate = (
            float(arguments["p80_estimate"])
            if arguments.get("p80_estimate") is not None
            else None
        )

        data = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "forecast_date": forecast_date,
            "eac": eac,
            "method": method,
            "confidence_pct": confidence_pct,
            "p80_estimate": p80_estimate,
            "notes": arguments.get("notes"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        store.upsert_financial_forecast(data)

        output: dict[str, Any] = {
            "status": "success",
            "forecast_id": data["id"],
            "project_id": project_id,
            "forecast_date": forecast_date,
            "eac": round(eac, 2),
            "method": method,
            "confidence_pct": _round2(confidence_pct),
            "p80_estimate": _round2(p80_estimate),
            "notes": data["notes"],
            "created_at": data["created_at"],
        }

        # VAC assessment against APPROVED TOTAL baseline
        baselines = store.get_financial_baselines(project_id, label="APPROVED")
        total_baselines = [
            b for b in baselines if b.get("cost_category") == "TOTAL"
        ]

        if total_baselines:
            bac = float(total_baselines[0]["total_budget"])
            if bac != 0:
                vac = bac - eac
                vac_pct = (vac / bac) * 100
            else:
                vac = 0.0
                vac_pct = 0.0

            direction = "under" if vac >= 0 else "over"
            direction_pct = "under" if vac_pct >= 0 else "over"

            output["vac"] = round(vac, 2)
            output["vac_pct"] = round(vac_pct, 2)
            output["approved_budget"] = round(bac, 2)
            output["assessment"] = (
                f"EAC of \u00a3{eac:,.0f} is \u00a3{abs(vac):,.0f} {direction} "
                f"the approved budget of \u00a3{bac:,.0f} "
                f"({abs(vac_pct):.1f}% {direction_pct})."
            )
        else:
            output["vac"] = None
            output["vac_pct"] = None
            output["assessment"] = (
                f"EAC of \u00a3{eac:,.0f} recorded. "
                f"No APPROVED TOTAL baseline found — call set_financial_baseline "
                f"to enable VAC analysis."
            )

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _get_spend_profile(arguments: dict[str, Any]) -> list[TextContent]:
    """Produce a complete spend S-curve."""
    try:
        store = _get_store(arguments)

        project_id = arguments["project_id"]
        include_forecast = arguments.get("include_forecast", True)

        # --- Baseline ---
        baselines = store.get_financial_baselines(project_id, label="APPROVED")
        total_baselines = [
            b for b in baselines if b.get("cost_category") == "TOTAL"
        ]
        approved_budget: float | None = None
        if total_baselines:
            approved_budget = float(total_baselines[0]["total_budget"])

        # --- Actuals ---
        actuals = store.get_financial_actuals(project_id)
        actuals_sorted = sorted(actuals, key=lambda r: r.get("period", ""))

        cumulative = 0.0
        periods = []
        for r in actuals_sorted:
            spend = float(r["actual_spend"])
            cumulative += spend
            vs_budget_pct: float | None = None
            if approved_budget and approved_budget != 0:
                vs_budget_pct = round((cumulative / approved_budget) * 100, 2)
            periods.append(
                {
                    "period": r.get("period"),
                    "actual_spend": round(spend, 2),
                    "cumulative_spend": round(cumulative, 2),
                    "vs_budget_pct": vs_budget_pct,
                }
            )

        total_spent_to_date = cumulative

        remaining_budget: float | None = None
        pct_spent: float | None = None
        if approved_budget is not None and approved_budget != 0:
            remaining_budget = approved_budget - total_spent_to_date
            pct_spent = (total_spent_to_date / approved_budget) * 100

        # --- Latest EAC ---
        latest_eac: float | None = None
        remaining_eac: float | None = None
        if include_forecast:
            forecasts = store.get_financial_forecasts(project_id)
            if forecasts:
                forecasts_sorted = sorted(
                    forecasts, key=lambda r: r.get("forecast_date", "")
                )
                latest_eac = float(forecasts_sorted[-1]["eac"])
                remaining_eac = latest_eac - total_spent_to_date

        # --- Projected outturn ---
        projected_outturn: str = "UNKNOWN"
        if latest_eac is not None and approved_budget is not None and approved_budget != 0:
            eac_vs_bac_pct = ((latest_eac - approved_budget) / approved_budget) * 100
            if latest_eac > approved_budget:
                projected_outturn = "OVER_BUDGET"
            elif eac_vs_bac_pct > -5.0:
                projected_outturn = "AT_RISK"
            else:
                projected_outturn = "WITHIN_BUDGET"
        elif approved_budget is not None and approved_budget != 0 and periods:
            # No EAC — use run rate vs remaining budget heuristic
            n_periods = len(periods)
            run_rate = total_spent_to_date / n_periods if n_periods > 0 else 0.0
            if remaining_budget is not None and run_rate > 0:
                months_remaining = remaining_budget / run_rate
                # If projected outturn > 120% of BAC, flag as OVER_BUDGET
                estimated_final = total_spent_to_date + (run_rate * months_remaining)
                if estimated_final > approved_budget * 1.05:
                    projected_outturn = "AT_RISK"
                else:
                    projected_outturn = "WITHIN_BUDGET"
        elif not periods:
            projected_outturn = "UNKNOWN"

        # --- Run rate ---
        n_months = len(periods)
        run_rate_monthly: float | None = None
        months_remaining_at_run_rate: float | None = None
        if n_months > 0:
            run_rate_monthly = total_spent_to_date / n_months
            if (
                remaining_budget is not None
                and run_rate_monthly > 0
            ):
                months_remaining_at_run_rate = remaining_budget / run_rate_monthly

        output = {
            "status": "success",
            "project_id": project_id,
            "approved_budget": _round2(approved_budget),
            "latest_eac": _round2(latest_eac),
            "total_spent_to_date": round(total_spent_to_date, 2),
            "remaining_budget": _round2(remaining_budget),
            "remaining_eac": _round2(remaining_eac),
            "pct_spent": round(pct_spent, 2) if pct_spent is not None else None,
            "projected_outturn": projected_outturn,
            "run_rate_monthly": _round2(run_rate_monthly),
            "months_remaining_at_run_rate": (
                round(months_remaining_at_run_rate, 1)
                if months_remaining_at_run_rate is not None
                else None
            ),
            "periods": periods,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]
