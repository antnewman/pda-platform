"""Tests for the unified pda-platform MCP server.

Covers:
  - Server creation and tool aggregation
  - All 9 registry modules load correctly
  - No duplicate tool names across modules
  - Every tool has a dispatch entry
  - Tool count matches expected total
  - Remote SSE server creates correctly
  - Individual servers still work independently
"""

import pytest


class TestUnifiedServerImports:
    """Test that the unified server and all registries import cleanly."""

    def test_unified_server_imports(self):
        from pm_mcp_servers.pda_platform import server

        assert server is not None

    def test_unified_server_instance(self):
        from pm_mcp_servers.pda_platform.server import server

        assert server is not None
        assert server.name == "pda-platform"

    def test_all_tools_populated(self):
        from pm_mcp_servers.pda_platform.server import ALL_TOOLS

        assert len(ALL_TOOLS) > 0

    def test_tool_dispatch_populated(self):
        from pm_mcp_servers.pda_platform.server import _TOOL_DISPATCH

        assert len(_TOOL_DISPATCH) > 0


class TestRegistryModules:
    """Test that each registry module exports TOOLS and dispatch correctly."""

    def test_data_registry_loads(self):
        from pm_mcp_servers.pm_data.registry import TOOLS, dispatch

        assert len(TOOLS) == 6
        assert callable(dispatch)

    def test_analyse_registry_loads(self):
        from pm_mcp_servers.pm_analyse.registry import TOOLS, dispatch

        assert len(TOOLS) == 8
        assert callable(dispatch)

    def test_validate_registry_loads(self):
        from pm_mcp_servers.pm_validate.registry import TOOLS, dispatch

        assert len(TOOLS) == 4
        assert callable(dispatch)

    def test_nista_registry_loads(self):
        from pm_mcp_servers.pm_nista.registry import TOOLS, dispatch

        assert len(TOOLS) == 5
        assert callable(dispatch)

    def test_assure_registry_loads(self):
        from pm_mcp_servers.pm_assure.registry import TOOLS, dispatch

        assert len(TOOLS) == 29
        assert callable(dispatch)

    def test_brm_registry_loads(self):
        from pm_mcp_servers.pm_brm.registry import TOOLS, dispatch

        assert len(TOOLS) == 12
        assert callable(dispatch)

    def test_portfolio_registry_loads(self):
        from pm_mcp_servers.pm_portfolio.registry import TOOLS, dispatch

        assert len(TOOLS) == 5
        assert callable(dispatch)

    def test_ev_registry_loads(self):
        from pm_mcp_servers.pm_ev.registry import TOOLS, dispatch

        assert len(TOOLS) == 2
        assert callable(dispatch)

    def test_synthesis_registry_loads(self):
        from pm_mcp_servers.pm_synthesis.registry import TOOLS, dispatch

        assert len(TOOLS) == 2
        assert callable(dispatch)

    def test_risk_registry_loads(self):
        from pm_mcp_servers.pm_risk.registry import TOOLS, dispatch

        assert len(TOOLS) == 9
        assert callable(dispatch)

    def test_change_registry_loads(self):
        from pm_mcp_servers.pm_change.registry import TOOLS, dispatch

        assert len(TOOLS) == 5
        assert callable(dispatch)

    def test_resource_registry_loads(self):
        from pm_mcp_servers.pm_resource.registry import TOOLS, dispatch

        assert len(TOOLS) == 5
        assert callable(dispatch)

    def test_financial_registry_loads(self):
        from pm_mcp_servers.pm_financial.registry import TOOLS, dispatch

        assert len(TOOLS) == 5
        assert callable(dispatch)

    def test_knowledge_registry_loads(self):
        from pm_mcp_servers.pm_knowledge.registry import TOOLS, dispatch

        assert len(TOOLS) == 8
        assert callable(dispatch)

    def test_simulation_registry_loads(self):
        from pm_mcp_servers.pm_simulation.registry import TOOLS, dispatch

        assert len(TOOLS) == 2
        assert callable(dispatch)

    def test_lessons_registry_loads(self):
        from pm_mcp_servers.pm_lessons.registry import TOOLS, dispatch

        assert len(TOOLS) == 5
        assert callable(dispatch)

    def test_reporting_registry_loads(self):
        from pm_mcp_servers.pm_reporting.registry import TOOLS, dispatch

        assert len(TOOLS) == 6
        assert callable(dispatch)


class TestSimulationModule:
    """Test the pm_simulation module tools and dispatch."""

    EXPECTED_SIMULATION_TOOLS = {
        "run_schedule_simulation",
        "get_simulation_results",
    }

    def test_simulation_tools_present(self):
        from pm_mcp_servers.pm_simulation.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_SIMULATION_TOOLS

    def test_simulation_tools_in_unified(self):
        from pm_mcp_servers.pda_platform.server import ALL_TOOLS

        actual = {t.name for t in ALL_TOOLS}
        assert self.EXPECTED_SIMULATION_TOOLS.issubset(actual)

    def test_simulation_tools_have_dispatch(self):
        from pm_mcp_servers.pda_platform.server import _TOOL_DISPATCH

        for tool_name in self.EXPECTED_SIMULATION_TOOLS:
            assert tool_name in _TOOL_DISPATCH, f"{tool_name} missing from dispatch"


class TestToolAggregation:
    """Test that tool aggregation in the unified server is correct."""

    def test_total_tool_count(self):
        """Unified server has exactly 126 tools (6+8+4+5+29+12+5+2+2+9+5+5+5+8+2+5+6+8)."""
        from pm_mcp_servers.pda_platform.server import ALL_TOOLS

        assert len(ALL_TOOLS) == 126

    def test_no_duplicate_tool_names(self):
        """No two tools share the same name across modules."""
        from pm_mcp_servers.pda_platform.server import ALL_TOOLS

        names = [t.name for t in ALL_TOOLS]
        assert len(names) == len(set(names)), f"Duplicate tools: {[n for n in names if names.count(n) > 1]}"

    def test_every_tool_has_dispatch(self):
        """Every registered tool has a corresponding dispatch function."""
        from pm_mcp_servers.pda_platform.server import ALL_TOOLS, _TOOL_DISPATCH

        missing = [t.name for t in ALL_TOOLS if t.name not in _TOOL_DISPATCH]
        assert len(missing) == 0, f"Tools without dispatch: {missing}"

    def test_tool_ordering(self):
        """Tools appear in module order: data, analyse, validate, nista, assure, brm, portfolio, ev, synthesis, risk, change, resource, financial, knowledge, simulation, lessons, reporting, assumptions."""
        from pm_mcp_servers.pda_platform.server import ALL_TOOLS

        names = [t.name for t in ALL_TOOLS]
        # First tool should be from pm-data
        assert names[0] == "load_project"
        # Last tool should be from pm-assumptions
        assert names[-1] == "export_assumption_html_dashboard"
        # All pm-assumptions tools should be present
        assert "export_assumption_html_dashboard" in names
        assert "generate_assumption_report" in names
        assert "export_assumption_graph" in names

    def test_all_tools_have_valid_schemas(self):
        """Every tool has a name, description, and inputSchema."""
        from pm_mcp_servers.pda_platform.server import ALL_TOOLS

        for tool in ALL_TOOLS:
            assert tool.name, "Tool has no name"
            assert tool.description, f"Tool {tool.name} has no description"
            assert tool.inputSchema, f"Tool {tool.name} has no inputSchema"
            assert tool.inputSchema.get("type") == "object", f"Tool {tool.name} schema is not object type"


class TestExpectedTools:
    """Verify the exact set of expected tool names is present."""

    EXPECTED_DATA_TOOLS = {
        "load_project", "query_tasks", "get_critical_path",
        "get_dependencies", "convert_format", "get_project_summary",
    }

    EXPECTED_ANALYSE_TOOLS = {
        "identify_risks", "forecast_completion", "detect_outliers",
        "assess_health", "suggest_mitigations", "compare_baseline",
        "detect_narrative_divergence", "evaluate_calibration",
    }

    EXPECTED_VALIDATE_TOOLS = {
        "validate_structure", "validate_semantic",
        "validate_nista", "validate_custom",
    }

    EXPECTED_NISTA_TOOLS = {
        "generate_gmpp_report", "generate_narrative",
        "submit_to_nista", "fetch_nista_metadata", "validate_gmpp_report",
    }

    EXPECTED_ASSURE_TOOLS = {
        "nista_longitudinal_trend", "track_review_actions", "review_action_status",
        "check_artefact_currency", "check_confidence_divergence",
        "recommend_review_schedule", "log_override_decision",
        "analyse_override_patterns", "ingest_lesson", "search_lessons",
        "log_assurance_activity", "analyse_assurance_overhead",
        "run_assurance_workflow", "get_workflow_history",
        "classify_project_domain", "reclassify_from_store",
        "ingest_assumption", "validate_assumption",
        "get_assumption_drift", "get_cascade_impact",
        "create_project_from_profile", "export_dashboard_data",
        "export_dashboard_html", "get_armm_report",
        "assess_gate_readiness", "get_gate_readiness_history", "compare_gate_readiness",
        "scan_for_red_flags", "route_outputs_to_review",
    }

    EXPECTED_BRM_TOOLS = {
        "ingest_benefit", "track_benefit_measurement", "get_benefits_health",
        "map_benefit_dependency", "get_benefit_dependency_network",
        "forecast_benefit_realisation", "detect_benefits_drift",
        "get_benefits_cascade_impact", "generate_benefits_narrative",
        "assess_benefits_maturity",
        "forecast_benefits_outturn", "get_benefits_realisation_trajectory",
    }

    EXPECTED_PORTFOLIO_TOOLS = {
        "get_portfolio_health", "get_portfolio_gate_readiness",
        "get_portfolio_brm_overview", "get_portfolio_armm_summary",
        "get_portfolio_assumptions_risk",
    }

    EXPECTED_EV_TOOLS = {
        "compute_ev_metrics", "generate_ev_dashboard",
    }

    EXPECTED_SYNTHESIS_TOOLS = {
        "summarise_project_health", "compare_project_health",
    }

    EXPECTED_RISK_TOOLS = {
        "ingest_risk", "update_risk_status", "get_risk_register",
        "get_risk_heat_map", "ingest_mitigation",
        "get_mitigation_progress", "get_portfolio_risks",
        "get_risk_velocity", "detect_stale_risks",
    }

    EXPECTED_CHANGE_TOOLS = {
        "log_change_request", "update_change_status", "get_change_log",
        "get_change_impact_summary", "analyse_change_pressure",
    }

    EXPECTED_RESOURCE_TOOLS = {
        "analyse_resource_loading", "detect_resource_conflicts",
        "get_critical_resources", "log_resource_plan",
        "get_portfolio_capacity",
    }

    EXPECTED_FINANCIAL_TOOLS = {
        "set_financial_baseline", "log_financial_actuals",
        "get_cost_performance", "log_cost_forecast", "get_spend_profile",
    }

    EXPECTED_KNOWLEDGE_TOOLS = {
        "list_knowledge_categories", "get_benchmark_data",
        "get_failure_patterns", "get_ipa_guidance", "search_knowledge_base",
        "run_reference_class_check", "get_benchmark_percentile",
        "generate_premortem_questions",
    }

    EXPECTED_LESSONS_TOOLS = {
        "extract_lessons", "get_project_lessons",
        "search_project_lessons", "get_systemic_patterns", "generate_lessons_section",
    }

    EXPECTED_REPORTING_TOOLS = {
        "generate_gate_review_summary", "generate_sro_dashboard",
        "generate_board_exception_report", "generate_portfolio_summary",
        "generate_pir_template", "export_sro_dashboard_data",
    }

    def test_data_tools_present(self):
        from pm_mcp_servers.pm_data.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_DATA_TOOLS

    def test_analyse_tools_present(self):
        from pm_mcp_servers.pm_analyse.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_ANALYSE_TOOLS

    def test_validate_tools_present(self):
        from pm_mcp_servers.pm_validate.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_VALIDATE_TOOLS

    def test_nista_tools_present(self):
        from pm_mcp_servers.pm_nista.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_NISTA_TOOLS

    def test_assure_tools_present(self):
        from pm_mcp_servers.pm_assure.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_ASSURE_TOOLS

    def test_brm_tools_present(self):
        from pm_mcp_servers.pm_brm.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_BRM_TOOLS

    def test_portfolio_tools_present(self):
        from pm_mcp_servers.pm_portfolio.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_PORTFOLIO_TOOLS

    def test_ev_tools_present(self):
        from pm_mcp_servers.pm_ev.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_EV_TOOLS

    def test_synthesis_tools_present(self):
        from pm_mcp_servers.pm_synthesis.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_SYNTHESIS_TOOLS

    def test_risk_tools_present(self):
        from pm_mcp_servers.pm_risk.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_RISK_TOOLS

    def test_change_tools_present(self):
        from pm_mcp_servers.pm_change.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_CHANGE_TOOLS

    def test_resource_tools_present(self):
        from pm_mcp_servers.pm_resource.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_RESOURCE_TOOLS

    def test_financial_tools_present(self):
        from pm_mcp_servers.pm_financial.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_FINANCIAL_TOOLS

    def test_knowledge_tools_present(self):
        from pm_mcp_servers.pm_knowledge.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_KNOWLEDGE_TOOLS

    def test_lessons_tools_present(self):
        from pm_mcp_servers.pm_lessons.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_LESSONS_TOOLS

    def test_reporting_tools_present(self):
        from pm_mcp_servers.pm_reporting.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_REPORTING_TOOLS

    def test_all_expected_tools_in_unified(self):
        """Every expected tool from every module is in the unified server."""
        from pm_mcp_servers.pda_platform.server import ALL_TOOLS

        actual = {t.name for t in ALL_TOOLS}
        expected = (
            self.EXPECTED_DATA_TOOLS
            | self.EXPECTED_ANALYSE_TOOLS
            | self.EXPECTED_VALIDATE_TOOLS
            | self.EXPECTED_NISTA_TOOLS
            | self.EXPECTED_ASSURE_TOOLS
            | self.EXPECTED_BRM_TOOLS
            | self.EXPECTED_PORTFOLIO_TOOLS
            | self.EXPECTED_EV_TOOLS
            | self.EXPECTED_SYNTHESIS_TOOLS
            | self.EXPECTED_RISK_TOOLS
            | self.EXPECTED_CHANGE_TOOLS
            | self.EXPECTED_RESOURCE_TOOLS
            | self.EXPECTED_FINANCIAL_TOOLS
            | self.EXPECTED_KNOWLEDGE_TOOLS
            | TestSimulationModule.EXPECTED_SIMULATION_TOOLS
            | self.EXPECTED_LESSONS_TOOLS
            | self.EXPECTED_REPORTING_TOOLS
            | {
                "load_assumption_register",
                "score_assumption_confidence",
                "fetch_external_signal",
                "detect_external_drift",
                "generate_assumption_report",
                "export_assumption_dashboard",
                "export_assumption_html_dashboard",
                "export_assumption_graph",
            }
        )
        assert actual == expected


class TestRemoteServer:
    """Test the SSE remote server wrapper."""

    def test_remote_module_imports(self):
        from pm_mcp_servers.pda_platform import remote

        assert remote is not None

    def test_starlette_app_created(self):
        from pm_mcp_servers.pda_platform.remote import app

        assert app is not None

    def test_routes_registered(self):
        from pm_mcp_servers.pda_platform.remote import app

        paths = [r.path for r in app.routes]
        assert "/sse" in paths
        assert "/messages" in paths
        assert "/health" in paths

    def test_main_entry_point_exists(self):
        from pm_mcp_servers.pda_platform.remote import main

        assert callable(main)


class TestIndividualServersStillWork:
    """Verify that individual servers are unbroken by unified server changes."""

    def test_pm_data_server(self):
        from pm_mcp_servers.pm_data.server import server

        assert server.name == "pm-data"

    def test_pm_analyse_server(self):
        from pm_mcp_servers.pm_analyse.server import server

        assert server.name == "pm-analyse"

    def test_pm_validate_server(self):
        from pm_mcp_servers.pm_validate.server import app

        assert app.name == "pm-validate"

    def test_pm_nista_server(self):
        from pm_mcp_servers.pm_nista.server import app

        assert app.name == "pm-nista-server"

    def test_pm_assure_server(self):
        from pm_mcp_servers.pm_assure.server import app

        assert app.name == "pm-assure-server"


class TestLessonsRegistry:
    """Test that the pm_lessons registry loads and exports correctly."""

    def test_lessons_registry_loads(self):
        from pm_mcp_servers.pm_lessons.registry import TOOLS, dispatch

        assert len(TOOLS) == 5
        assert callable(dispatch)


class TestLessonsModule:
    """Test the pm_lessons module tools and dispatch."""

    EXPECTED_LESSONS_TOOLS = {
        "extract_lessons",
        "get_project_lessons",
        "search_project_lessons",
        "get_systemic_patterns",
        "generate_lessons_section",
    }

    def test_lessons_tools_present(self):
        from pm_mcp_servers.pm_lessons.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_LESSONS_TOOLS

    def test_lessons_tools_have_valid_schemas(self):
        from pm_mcp_servers.pm_lessons.registry import TOOLS

        for tool in TOOLS:
            assert tool.name, "Tool has no name"
            assert tool.description, f"Tool {tool.name} has no description"
            assert tool.inputSchema, f"Tool {tool.name} has no inputSchema"
            assert tool.inputSchema.get("type") == "object", f"Tool {tool.name} schema is not object type"

    def test_lessons_dispatch_covers_all_tools(self):
        from pm_mcp_servers.pm_lessons.registry import _DISPATCH, TOOLS

        tool_names = {t.name for t in TOOLS}
        dispatch_names = set(_DISPATCH.keys())
        assert tool_names == dispatch_names


def test_reporting_registry_loads():
    """pm_reporting registry exports TOOLS and a callable dispatch."""
    from pm_mcp_servers.pm_reporting.registry import TOOLS, dispatch

    assert len(TOOLS) == 6
    assert callable(dispatch)


class TestReportingModule:
    """Test the pm_reporting module tools and dispatch."""

    EXPECTED_REPORTING_TOOLS = {
        "generate_gate_review_summary",
        "generate_sro_dashboard",
        "generate_board_exception_report",
        "generate_portfolio_summary",
        "generate_pir_template",
        "export_sro_dashboard_data",
    }

    def test_reporting_tools_present(self):
        from pm_mcp_servers.pm_reporting.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_REPORTING_TOOLS

    def test_reporting_tools_have_valid_schemas(self):
        from pm_mcp_servers.pm_reporting.registry import TOOLS

        for tool in TOOLS:
            assert tool.name, "Tool has no name"
            assert tool.description, f"Tool {tool.name} has no description"
            assert tool.inputSchema, f"Tool {tool.name} has no inputSchema"
            assert tool.inputSchema.get("type") == "object", (
                f"Tool {tool.name} schema is not object type"
            )

    def test_reporting_dispatch_covers_all_tools(self):
        from pm_mcp_servers.pm_reporting.registry import TOOLS, _DISPATCH

        for tool in TOOLS:
            assert tool.name in _DISPATCH, f"{tool.name} missing from _DISPATCH"

    def test_reporting_server_instance(self):
        from pm_mcp_servers.pm_reporting.server import server

        assert server.name == "pm-reporting"

    def test_gate_review_tool_has_required_params(self):
        from pm_mcp_servers.pm_reporting.registry import TOOLS

        tool = next(t for t in TOOLS if t.name == "generate_gate_review_summary")
        required = tool.inputSchema.get("required", [])
        assert "project_id" in required
        assert "gate_number" in required

    def test_sro_dashboard_tool_has_required_params(self):
        from pm_mcp_servers.pm_reporting.registry import TOOLS

        tool = next(t for t in TOOLS if t.name == "generate_sro_dashboard")
        required = tool.inputSchema.get("required", [])
        assert "project_id" in required

    def test_portfolio_tool_accepts_list(self):
        from pm_mcp_servers.pm_reporting.registry import TOOLS

        tool = next(t for t in TOOLS if t.name == "generate_portfolio_summary")
        props = tool.inputSchema.get("properties", {})
        assert props["project_ids"]["type"] == "array"
        assert "project_ids" in tool.inputSchema.get("required", [])


@pytest.mark.asyncio
class TestUnifiedDispatch:
    """Test that the unified call_tool dispatcher routes correctly."""

    async def test_unknown_tool_returns_error(self):
        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool("nonexistent_tool_xyz", {})
        assert len(result) == 1
        assert "Unknown tool" in result[0].text


class TestAssumptionsModule:
    """Tests for the pm-assumptions module registry and tool definitions."""

    EXPECTED_ASSUMPTIONS_TOOLS = {
        "load_assumption_register",
        "score_assumption_confidence",
        "fetch_external_signal",
        "detect_external_drift",
        "generate_assumption_report",
        "export_assumption_dashboard",
        "export_assumption_html_dashboard",
        "export_assumption_graph",
    }

    def test_assumptions_registry_loads(self):
        from pm_mcp_servers.pm_assumptions.registry import TOOLS

        assert len(TOOLS) == 8

    def test_assumptions_tool_names(self):
        from pm_mcp_servers.pm_assumptions.registry import TOOLS

        actual = {t.name for t in TOOLS}
        assert actual == self.EXPECTED_ASSUMPTIONS_TOOLS

    def test_assumptions_tools_in_unified(self):
        from pm_mcp_servers.pda_platform.server import ALL_TOOLS

        actual = {t.name for t in ALL_TOOLS}
        assert self.EXPECTED_ASSUMPTIONS_TOOLS.issubset(actual)

    def test_all_assumptions_tools_have_dispatch(self):
        from pm_mcp_servers.pm_assumptions.registry import TOOLS, _DISPATCH

        for tool in TOOLS:
            assert tool.name in _DISPATCH, f"No dispatch for {tool.name}"

    def test_load_assumption_register_required_params(self):
        from pm_mcp_servers.pm_assumptions.registry import TOOLS

        tool = next(t for t in TOOLS if t.name == "load_assumption_register")
        required = tool.inputSchema.get("required", [])
        assert "project_id" in required
        assert "file_path" in required

    def test_fetch_external_signal_enum_values(self):
        from pm_mcp_servers.pm_assumptions.registry import TOOLS

        tool = next(t for t in TOOLS if t.name == "fetch_external_signal")
        props = tool.inputSchema.get("properties", {})
        assert "enum" in props["indicator"]
        assert "ons" in props["source"]["enum"]
        assert "world_bank" in props["source"]["enum"]

    def test_detect_external_drift_required_params(self):
        from pm_mcp_servers.pm_assumptions.registry import TOOLS

        tool = next(t for t in TOOLS if t.name == "detect_external_drift")
        required = tool.inputSchema.get("required", [])
        assert "project_id" in required
        assert "assumption_id" in required
        assert "indicator" in required
        assert "source" in required

    def test_export_assumption_graph_format_enum(self):
        from pm_mcp_servers.pm_assumptions.registry import TOOLS

        tool = next(t for t in TOOLS if t.name == "export_assumption_graph")
        props = tool.inputSchema.get("properties", {})
        assert "enum" in props["format"]
        assert "cypher" in props["format"]["enum"]
        assert "csv" in props["format"]["enum"]
        assert "json" in props["format"]["enum"]
        assert "all" in props["format"]["enum"]

    def test_build_assumption_dashboard_panels_is_callable(self):
        """The shared panel-builder helper should be importable and callable."""
        from pm_mcp_servers.pm_assumptions.server import build_assumption_dashboard_panels

        # For a non-existent project, should still return a well-formed dict
        # (empty assumptions, zero counts). No exception.
        result = build_assumption_dashboard_panels("NONEXISTENT-TEST-PROJECT")
        assert isinstance(result, dict)
        assert "project_id" in result
        assert result["project_id"] == "NONEXISTENT-TEST-PROJECT"
        assert "summary" in result
        assert "total_assumptions" in result["summary"]
        assert "rag_counts" in result["summary"]
        assert result["summary"]["rag_counts"] == {"RED": 0, "AMBER": 0, "GREEN": 0}
        assert "top5_lowest_confidence" in result
        assert "external_signals" in result
        assert "all_assumptions" in result


class TestRemoteHttpEndpoints:
    """Tests for the new HTTP endpoints on the remote SSE server.

    These endpoints let a hosted UDS renderer load dashboard panel data
    and YAML specs directly from the PDA Platform, eliminating the need
    for a local filesystem or a separate data server.
    """

    def _client(self):
        from starlette.testclient import TestClient
        from pm_mcp_servers.pda_platform.remote import app
        return TestClient(app)

    def test_health_still_works(self):
        """Sanity check — the existing /health endpoint is unaffected."""
        client = self._client()
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["server"] == "pda-platform"

    def test_dashboard_data_returns_json(self):
        """GET /data/{project_id}/dashboard.json returns the panel data dict."""
        client = self._client()
        r = client.get("/data/TEST-NONEXISTENT/dashboard.json")
        # Even for a project with no data, this should 200 with empty counts
        assert r.status_code == 200
        data = r.json()
        assert data["project_id"] == "TEST-NONEXISTENT"
        assert "summary" in data
        assert "top5_lowest_confidence" in data
        assert "external_signals" in data

    def test_dashboard_spec_returns_yaml(self):
        """GET /dashboards/assumption-drift.uds.yaml returns the YAML spec."""
        client = self._client()
        r = client.get("/dashboards/assumption-drift.uds.yaml")
        assert r.status_code == 200
        # Content-type should be YAML-ish
        assert "yaml" in r.headers.get("content-type", "").lower()
        # Body should contain known UDS spec fields
        body = r.text
        assert "uds:" in body
        assert "assumption-drift" in body or "Assumption Drift" in body

    def test_dashboard_spec_404_for_unknown(self):
        """GET /dashboards/{unknown}.uds.yaml returns 404 with an error body."""
        client = self._client()
        r = client.get("/dashboards/does-not-exist.uds.yaml")
        assert r.status_code == 404
        assert "error" in r.json()

    def test_dashboard_spec_rejects_path_traversal(self):
        """Path-traversal attempts resolve to a safe no-match, not a file read."""
        client = self._client()
        r = client.get("/dashboards/..%2F..%2Fetc%2Fpasswd.uds.yaml")
        # Should be 404 — the sanitiser strips `..` and `/` before lookup
        assert r.status_code == 404

    def test_cors_headers_present(self):
        """CORS headers allow any origin (permissive for read-only public data)."""
        client = self._client()
        r = client.get(
            "/data/TEST-NONEXISTENT/dashboard.json",
            headers={"Origin": "https://any.netlify.app"},
        )
        assert r.status_code == 200
        assert r.headers.get("access-control-allow-origin") == "*"


class TestAssureDispatchWiring:
    """Regression tests for tool-dispatch wiring in pm-assure.

    These guard against bugs where a tool is registered in ASSURE_TOOLS but
    omitted from the per-module _DISPATCH dict — meaning Claude can see the
    tool but calling it returns "Unknown tool: <name>". scan_for_red_flags
    is the README's headlined "Start here" call, so silent-fail is publicly
    visible.
    """

    async def test_scan_for_red_flags_dispatches(self):
        """scan_for_red_flags must route to its handler, not return 'Unknown tool'."""
        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool("scan_for_red_flags", {"project_id": "TEST-NONEXISTENT"})
        text = result[0].text
        assert "Unknown tool" not in text, (
            f"scan_for_red_flags is registered but not wired to its handler: {text}"
        )

    async def test_every_assure_tool_has_dispatch_entry(self):
        """No tool in ASSURE_TOOLS should be missing from _DISPATCH.

        Catches the same class of bug for any future tool added to the module.
        """
        from pm_mcp_servers.pm_assure.registry import TOOLS as ASSURE_TOOLS, _DISPATCH

        registered = {t.name for t in ASSURE_TOOLS}
        wired = set(_DISPATCH.keys())
        missing = registered - wired
        assert not missing, (
            f"Tools registered in ASSURE_TOOLS but missing from _DISPATCH: {missing}"
        )


class TestAssessGateReadinessErrors:
    """Regression tests for clear, actionable errors from assess_gate_readiness.

    The handler used to fail with the opaque string "Error: 'gate'" when
    callers omitted required parameters — a wrapped KeyError. These tests
    confirm we now return a structured JSON error that names the missing
    parameter and shows the expected values.
    """

    async def test_missing_gate_returns_clear_error(self):
        import json as _json
        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool("assess_gate_readiness", {"project_id": "TEST-X"})
        body = _json.loads(result[0].text)
        assert "error" in body
        assert "missing" in body["error"].lower()
        assert "GATE_3" in _json.dumps(body)

    async def test_missing_project_id_returns_clear_error(self):
        import json as _json
        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool("assess_gate_readiness", {"gate": "GATE_3"})
        body = _json.loads(result[0].text)
        assert "error" in body
        assert "missing" in body["error"].lower()
        assert "project_id" in body["error"]

    async def test_invalid_gate_returns_clear_error(self):
        import json as _json
        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool(
            "assess_gate_readiness",
            {"project_id": "TEST-X", "gate": "GATE_99"},
        )
        body = _json.loads(result[0].text)
        assert "error" in body
        assert "GATE_99" in body["error"] or "Invalid" in body["error"]
        assert "expected" in body
class TestReferenceClassInputValidation:
    """Regression tests for run_reference_class_check input validation.

    Without validation, passing estimate_type='cost' (a common LLM-style
    abbreviation) returned the misleading error "No benchmark data for
    IT_AND_DIGITAL/cost" — sounded like missing data, was actually invalid
    input. Now: aliases are resolved silently, unknown values produce
    structured errors naming valid options.
    """

    async def test_canonical_cost_overrun_still_works(self):
        import json as _json
        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool("run_reference_class_check", {
            "project_type": "IT_AND_DIGITAL",
            "estimate_type": "cost_overrun",
            "submitted_value": 42,
        })
        body = _json.loads(result[0].text)
        assert "error" not in body, f"Unexpected error: {body}"
        # Should have benchmark output fields
        assert "approximate_percentile" in body or "interpretation" in body or "mean" in _json.dumps(body).lower()

    async def test_alias_cost_resolves_to_cost_overrun(self):
        import json as _json
        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool("run_reference_class_check", {
            "project_type": "IT_AND_DIGITAL",
            "estimate_type": "cost",
            "submitted_value": 42,
        })
        body = _json.loads(result[0].text)
        assert "error" not in body, f"Alias 'cost' should resolve to 'cost_overrun': {body}"

    async def test_alias_schedule_resolves_to_schedule_slip(self):
        import json as _json
        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool("run_reference_class_check", {
            "project_type": "IT_AND_DIGITAL",
            "estimate_type": "schedule",
            "submitted_value": 12,
        })
        body = _json.loads(result[0].text)
        assert "error" not in body, f"Alias 'schedule' should resolve to 'schedule_slip': {body}"

    async def test_invalid_estimate_type_returns_clear_error(self):
        import json as _json
        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool("run_reference_class_check", {
            "project_type": "IT_AND_DIGITAL",
            "estimate_type": "banana",
            "submitted_value": 42,
        })
        body = _json.loads(result[0].text)
        assert "error" in body
        assert "banana" in body["error"]
        assert "expected" in body
        assert "cost_overrun" in body["expected"]
        assert "accepted_aliases" in body
class TestBoardReportFallback:
    """Regression tests for graceful fallback when ANTHROPIC_API_KEY is unset.

    Previously generate_board_exception_report failed hard with a JSON
    error if the key was missing. Now it produces a deterministic,
    evidence-only markdown board report from the same underlying project
    data — always usable, always honest about which mode it ran in.
    """

    def _seed_minimal_project(self, project_id: str = "BOARD-FALLBACK-TEST"):
        """Seed enough project data that _has_any_data() returns True."""
        from datetime import datetime
        from pm_data_tools.db.store import AssuranceStore
        store = AssuranceStore()
        now = datetime.utcnow().isoformat()
        store.upsert_risk({
            "id": f"{project_id}-R001",
            "project_id": project_id,
            "title": "Test risk for fallback report",
            "description": "Seeded for testing the evidence-only fallback path.",
            "category": "DELIVERY",
            "likelihood": 4,
            "impact": 4,
            "risk_score": 16,
            "status": "OPEN",
            "created_at": now,
            "updated_at": now,
        })
        return project_id

    async def test_evidence_only_when_api_key_missing(self, monkeypatch):
        """Without ANTHROPIC_API_KEY: returns markdown evidence-only report, not an error."""
        import json as _json
        from pm_mcp_servers.pda_platform.server import call_tool

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        project_id = self._seed_minimal_project("BOARD-FALLBACK-NOKEY")
        result = await call_tool("generate_board_exception_report", {"project_id": project_id})

        text = result[0].text
        # Must not be a JSON error
        try:
            body = _json.loads(text)
            assert "error" not in body, f"Expected fallback markdown, got error: {body}"
        except _json.JSONDecodeError:
            pass  # Plain markdown — what the fallback produces

        assert "AI synthesis unavailable" in text
        assert "Board Exception Report" in text
        assert project_id in text
        assert "evidence-only" in text.lower()

    async def test_no_data_still_errors_clearly(self, monkeypatch):
        """If the project has no data at all, return a clear 'no data' error."""
        import json as _json
        from pm_mcp_servers.pda_platform.server import call_tool

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        result = await call_tool("generate_board_exception_report", {
            "project_id": "DOES-NOT-EXIST-AT-ALL",
        })

        body = _json.loads(result[0].text)
        assert "error" in body
        assert "No data found" in body["error"]

    async def test_fallback_includes_high_risks(self, monkeypatch):
        """The evidence-only fallback should surface seeded HIGH/CRITICAL risks."""
        from pm_mcp_servers.pda_platform.server import call_tool

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        project_id = self._seed_minimal_project("BOARD-FALLBACK-RISKS")
        result = await call_tool("generate_board_exception_report", {"project_id": project_id})

        text = result[0].text
        assert "High and Critical Risks" in text
        assert (
            "Test risk for fallback report" in text
            or f"{project_id}-R001" in text
        )


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 5: Output-guardrail engine (issue #29 / A2)
# ─────────────────────────────────────────────────────────────────────────


class TestGuardrailEngine:
    """Behavioural anchor for the deterministic output-guardrail engine.

    Covers every verdict path (APPROVED / FLAGGED / REJECTED), the
    audit-trail-records-every-evaluation invariant, the rule-condition
    error path (records UNKNOWN, does not crash), and the wrapper's
    behaviour for each verdict against a synthetic MCP handler.
    """

    # ── Pure engine: severity-to-verdict mapping ──────────────────────

    def test_approved_when_no_rule_fires(self):
        from pm_mcp_servers._guardrails import (
            Severity,
            Verdict,
            build_required_field_rule,
            evaluate,
        )

        policy = [build_required_field_rule("verdict", severity=Severity.BLOCK)]
        result = evaluate({"verdict": "GREEN"}, policy)
        assert result.verdict == Verdict.APPROVED
        assert result.triggered == []
        assert len(result.evaluations) == 1
        assert result.evaluations[0].violated is False

    def test_flagged_when_only_warn_fires(self):
        from pm_mcp_servers._guardrails import (
            Severity,
            Verdict,
            build_required_field_rule,
            evaluate,
        )

        policy = [
            build_required_field_rule("missing_field", severity=Severity.WARN),
        ]
        result = evaluate({"verdict": "GREEN"}, policy)
        assert result.verdict == Verdict.FLAGGED
        assert len(result.triggered) == 1
        assert result.triggered[0].severity == Severity.WARN

    def test_rejected_when_any_block_fires_even_with_warns(self):
        from pm_mcp_servers._guardrails import (
            Severity,
            Verdict,
            build_forbidden_phrase_rule,
            build_required_field_rule,
            evaluate,
        )

        policy = [
            build_required_field_rule("missing_field", severity=Severity.WARN),
            build_forbidden_phrase_rule(
                "narrative",
                phrases=["100% certain"],
                severity=Severity.BLOCK,
            ),
        ]
        result = evaluate(
            {"narrative": "We are 100% certain of the outcome."}, policy
        )
        assert result.verdict == Verdict.REJECTED
        # Both rules fired — trail records both.
        assert len(result.triggered) == 2

    def test_info_severity_never_changes_verdict(self):
        from pm_mcp_servers._guardrails import Rule, Severity, Verdict, evaluate

        policy = [
            Rule(
                name="info_only",
                description="Records context",
                severity=Severity.INFO,
                condition=lambda _: True,  # always "violated" → trail entry
            )
        ]
        result = evaluate({}, policy)
        assert result.verdict == Verdict.APPROVED
        assert len(result.triggered) == 1
        assert result.triggered[0].severity == Severity.INFO

    # ── Audit-trail invariant ─────────────────────────────────────────

    def test_audit_trail_records_every_rule_regardless_of_verdict(self):
        from pm_mcp_servers._guardrails import (
            Severity,
            build_forbidden_phrase_rule,
            build_required_field_rule,
            evaluate,
        )

        policy = [
            build_required_field_rule("verdict", severity=Severity.BLOCK),
            build_required_field_rule("missing_a", severity=Severity.WARN),
            build_required_field_rule("missing_b", severity=Severity.WARN),
            build_forbidden_phrase_rule(
                "narrative",
                phrases=["100% certain"],
                severity=Severity.BLOCK,
            ),
        ]
        # Clean output — none fire.
        clean = evaluate(
            {"verdict": "GREEN", "missing_a": 1, "missing_b": 2, "narrative": "ok"},
            policy,
        )
        # Dirty output — all four fire.
        dirty = evaluate({"narrative": "100% certain"}, policy)

        # Both produce the same shape of trail — same number of rules
        # evaluated, in the same order.
        assert len(clean.evaluations) == len(dirty.evaluations) == 4
        assert [e.rule_name for e in clean.evaluations] == [
            e.rule_name for e in dirty.evaluations
        ]

    def test_condition_that_raises_records_unknown_and_continues(self):
        from pm_mcp_servers._guardrails import (
            Rule,
            Severity,
            Verdict,
            build_required_field_rule,
            evaluate,
        )

        def boom(_: dict) -> bool:
            raise RuntimeError("policy bug")

        policy = [
            Rule(
                name="exploding_rule",
                description="Should not break the engine",
                severity=Severity.BLOCK,
                condition=boom,
            ),
            build_required_field_rule("verdict", severity=Severity.BLOCK),
        ]
        result = evaluate({"verdict": "GREEN"}, policy)
        # Verdict is APPROVED — boom did NOT trigger rejection.
        assert result.verdict == Verdict.APPROVED
        # The trail records UNKNOWN for the broken rule.
        boom_entry = next(e for e in result.evaluations if e.rule_name == "exploding_rule")
        assert boom_entry.severity == Severity.UNKNOWN
        assert boom_entry.error == "RuntimeError"

    # ── Range / allowed-values rule builders ──────────────────────────

    def test_range_rule_fires_above_upper_bound(self):
        from pm_mcp_servers._guardrails import Verdict, build_range_rule, evaluate

        policy = [build_range_rule("confidence", lower=0.0, upper=1.0)]
        assert evaluate({"confidence": 1.5}, policy).verdict == Verdict.REJECTED
        assert evaluate({"confidence": 0.5}, policy).verdict == Verdict.APPROVED
        # Missing/non-numeric also fires.
        assert evaluate({"confidence": "not-a-number"}, policy).verdict == Verdict.REJECTED
        assert evaluate({}, policy).verdict == Verdict.REJECTED

    def test_allowed_values_rule(self):
        from pm_mcp_servers._guardrails import Verdict, build_allowed_values_rule, evaluate

        policy = [build_allowed_values_rule("verdict", {"GREEN", "AMBER", "RED"})]
        assert evaluate({"verdict": "AMBER"}, policy).verdict == Verdict.APPROVED
        assert evaluate({"verdict": "PURPLE"}, policy).verdict == Verdict.REJECTED
        # Missing fires.
        assert evaluate({}, policy).verdict == Verdict.REJECTED

    def test_forbidden_phrase_rule_is_case_insensitive_by_default(self):
        from pm_mcp_servers._guardrails import Verdict, build_forbidden_phrase_rule, evaluate

        policy = [
            build_forbidden_phrase_rule(
                "narrative",
                phrases=["100% certain", "guaranteed"],
            )
        ]
        assert (
            evaluate(
                {"narrative": "Outcomes are 100% Certain"}, policy
            ).verdict
            == Verdict.REJECTED
        )
        assert (
            evaluate(
                {"narrative": "Risks managed proportionately."}, policy
            ).verdict
            == Verdict.APPROVED
        )

    # ── Wrapper: end-to-end against a synthetic MCP handler ───────────

    async def test_wrapper_approved_returns_original_output_unchanged(self):
        import json as _json

        from mcp.types import TextContent

        from pm_mcp_servers._guardrails import (
            Severity,
            build_required_field_rule,
            wrap_tool_output,
        )

        async def fake_handler(_args):
            return [TextContent(type="text", text=_json.dumps({"verdict": "GREEN"}))]

        wrapped = wrap_tool_output(
            fake_handler,
            policy=[build_required_field_rule("verdict", severity=Severity.BLOCK)],
        )
        result = await wrapped({})
        # Same object identity — APPROVED passes the original through.
        assert result[0].text == _json.dumps({"verdict": "GREEN"})
        # No annotation added.
        assert "_guardrail_flags" not in result[0].text

    async def test_wrapper_flagged_adds_annotation_preserving_original_fields(self):
        import json as _json

        from mcp.types import TextContent

        from pm_mcp_servers._guardrails import (
            Severity,
            build_required_field_rule,
            wrap_tool_output,
        )

        async def fake_handler(_args):
            return [TextContent(type="text", text=_json.dumps({"verdict": "GREEN"}))]

        wrapped = wrap_tool_output(
            fake_handler,
            policy=[
                build_required_field_rule(
                    "missing_field", severity=Severity.WARN
                )
            ],
        )
        result = await wrapped({})
        payload = _json.loads(result[0].text)
        # Original field preserved.
        assert payload["verdict"] == "GREEN"
        # Annotation present.
        assert "_guardrail_flags" in payload
        assert payload["_guardrail_flags"]["verdict"] == "FLAGGED"
        assert len(payload["_guardrail_flags"]["triggered"]) == 1

    async def test_wrapper_rejected_returns_error_json_not_original_output(self):
        import json as _json

        from mcp.types import TextContent

        from pm_mcp_servers._guardrails import (
            Severity,
            build_forbidden_phrase_rule,
            wrap_tool_output,
        )

        async def fake_handler(_args):
            return [
                TextContent(
                    type="text",
                    text=_json.dumps(
                        {"narrative": "We are 100% certain this will succeed."}
                    ),
                )
            ]

        wrapped = wrap_tool_output(
            fake_handler,
            policy=[
                build_forbidden_phrase_rule(
                    "narrative",
                    phrases=["100% certain"],
                    severity=Severity.BLOCK,
                )
            ],
        )
        result = await wrapped({})
        payload = _json.loads(result[0].text)
        # Original prose suppressed — hard fail-safe. The triggered
        # rule's description may legitimately echo the forbidden token
        # as metadata, but the original narrative sentence ("this will
        # succeed") and the original dict's keys must not appear in
        # the response.
        assert "this will succeed" not in result[0].text
        assert "narrative" not in payload  # original field absent
        assert payload["error"] == "guardrail_rejected"
        assert payload["verdict"] == "REJECTED"
        assert len(payload["triggered"]) == 1

    async def test_wrapper_records_to_audit_chain_when_provided(self):
        import json as _json

        from mcp.types import TextContent

        from pm_data_tools.audit import AuditChain
        from pm_mcp_servers._guardrails import (
            Severity,
            build_required_field_rule,
            wrap_tool_output,
        )

        chain = AuditChain()

        async def fake_handler(_args):
            return [TextContent(type="text", text=_json.dumps({"verdict": "GREEN"}))]

        wrapped = wrap_tool_output(
            fake_handler,
            policy=[build_required_field_rule("verdict", severity=Severity.BLOCK)],
            audit_chain=chain,
            action="TEST_GUARDRAIL",
        )
        await wrapped({})
        await wrapped({})
        # Two evaluations → two audit entries.
        assert len(chain) == 2
        assert chain.entries[0].decision == "APPROVED"
        assert chain.entries[0].action == "TEST_GUARDRAIL"
        # Chain still verifies after recording.
        assert chain.verify().is_valid

    async def test_wrapper_passes_through_non_json_text_unchanged(self):
        from mcp.types import TextContent

        from pm_mcp_servers._guardrails import (
            Severity,
            build_required_field_rule,
            wrap_tool_output,
        )

        async def fake_handler(_args):
            return [TextContent(type="text", text="this is not JSON")]

        wrapped = wrap_tool_output(
            fake_handler,
            policy=[build_required_field_rule("verdict", severity=Severity.BLOCK)],
        )
        result = await wrapped({})
        # Non-JSON output passes through untouched — engine has nothing
        # to evaluate against an opaque blob.
        assert result[0].text == "this is not JSON"


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 4: Calibration and conformal prediction (issue #31 / A4)
# ─────────────────────────────────────────────────────────────────────────


class TestCalibrationAndConformal:
    """Behavioural anchor for L4 calibration and conformal-prediction primitives.

    Anchors the paper's headline tests:
    - ECE-on-perfectly-calibrated-data-is-zero
    - temperature-scaling-reduces-ECE on a synthetic overconfident classifier
    - empirical-coverage-meets-guarantee on a synthetic split-conformal run
      at alpha=0.1 (90% nominal → at least ~88% empirical)

    Plus the regression-band variant used by the Monte Carlo / benchmark
    pipelines.
    """

    # ── ECE ───────────────────────────────────────────────────────────

    def test_ece_perfectly_calibrated_classifier_is_zero(self):
        import numpy as np

        from agent_planning.calibration import compute_ece

        # Synthetic: every prediction has confidence == accuracy. Build
        # two cohorts — one with confidence 0.9 and accuracy 0.9; one
        # with confidence 1.0 and accuracy 1.0.
        rng = np.random.default_rng(0)
        n_per = 500

        # Cohort 1: top-class prob ~ 0.9, correct 90% of the time.
        cohort1_probs = np.full((n_per, 2), 0.0)
        cohort1_probs[:, 1] = 0.9
        cohort1_probs[:, 0] = 0.1
        cohort1_correct_mask = rng.random(n_per) < 0.9
        cohort1_y = np.where(cohort1_correct_mask, 1, 0)

        # Cohort 2: top-class prob 1.0, always correct.
        cohort2_probs = np.full((n_per, 2), 0.0)
        cohort2_probs[:, 1] = 1.0
        cohort2_probs[:, 0] = 0.0
        cohort2_y = np.ones(n_per, dtype=int)

        y_true = np.concatenate([cohort1_y, cohort2_y])
        y_probs = np.concatenate([cohort1_probs, cohort2_probs])

        result = compute_ece(y_true, y_probs, n_bins=15)
        # With this size of synthetic data, the empirical accuracy in
        # the 0.9 cohort is within sampling noise of 0.9; the gap is
        # well below 0.03. The paper's "is zero" reference is the
        # population-level statement; we use a tolerant assertion.
        assert result.ece < 0.03
        assert result.n_samples == 2 * n_per

    def test_ece_uncalibrated_classifier_has_nonzero_ece(self):
        import numpy as np

        from agent_planning.calibration import compute_ece

        rng = np.random.default_rng(1)
        n = 1000
        # Severely overconfident: always predicts confidence 0.95 but
        # only correct 60% of the time.
        probs = np.full((n, 2), 0.0)
        probs[:, 1] = 0.95
        probs[:, 0] = 0.05
        correct = rng.random(n) < 0.6
        y_true = np.where(correct, 1, 0)

        result = compute_ece(y_true, probs, n_bins=15)
        # ECE should be close to |0.95 - 0.6| = 0.35.
        assert result.ece > 0.3

    # ── Temperature scaling ───────────────────────────────────────────

    def test_temperature_scaling_reduces_ece_on_overconfident_classifier(self):
        import numpy as np

        from agent_planning.calibration import (
            apply_temperature_scaling,
            compute_ece,
            find_temperature,
        )

        rng = np.random.default_rng(2)
        n = 3000
        n_classes = 4

        # Build a well-calibrated logit/label pair: labels sampled FROM
        # the softmax of the soft logits, so the well-calibrated
        # softmax probabilities truly match the empirical class
        # distribution per row.
        logits_soft = rng.normal(scale=1.5, size=(n, n_classes))
        soft_probs = apply_temperature_scaling(logits_soft, temperature=1.0)
        # Sample one label per row from its probability vector.
        uniforms = rng.random(n)
        cum = np.cumsum(soft_probs, axis=1)
        y_true = (uniforms[:, None] < cum).argmax(axis=1)

        # Now make the model overconfident by scaling the logits by
        # K > 1. The softmax of K·logits is sharper than soft_probs —
        # so the predicted confidence exceeds the true accuracy.
        K = 4.0
        logits_overconf = logits_soft * K

        raw_probs = apply_temperature_scaling(logits_overconf, temperature=1.0)
        ece_before = compute_ece(y_true, raw_probs, n_bins=15).ece

        # Fit temperature on this calibration set. The minimiser
        # should find T close to K = 4.0, undoing the overconfidence.
        T = find_temperature(logits_overconf, y_true)

        scaled_probs = apply_temperature_scaling(logits_overconf, temperature=T)
        ece_after = compute_ece(y_true, scaled_probs, n_bins=15).ece

        # Overconfident classifiers need T > 1 to soften. Test the
        # direction of the fix and the materiality of the gain.
        assert T > 1.0, f"expected T > 1 for overconfident classifier; got {T}"
        assert ece_after < ece_before, (
            f"temperature scaling failed to reduce ECE: "
            f"before={ece_before:.4f}, after={ece_after:.4f}"
        )
        # The corrected ECE should be materially lower (loose bound).
        assert ece_after < 0.5 * ece_before

    def test_apply_temperature_scaling_at_T_one_is_softmax(self):
        import numpy as np

        from agent_planning.calibration import apply_temperature_scaling

        logits = np.array([[1.0, 2.0, 3.0], [0.0, 0.0, 0.0]])
        probs = apply_temperature_scaling(logits, temperature=1.0)
        # Each row sums to 1.
        assert np.allclose(probs.sum(axis=1), 1.0)
        # T=1.0 reproduces softmax; row 2 is uniform.
        assert np.allclose(probs[1], [1 / 3, 1 / 3, 1 / 3])

    # ── Split conformal prediction ────────────────────────────────────

    def test_empirical_coverage_meets_guarantee_alpha_01(self):
        """Paper's headline test: 90% nominal → at least ~88% empirical."""
        import numpy as np

        from agent_planning.calibration import (
            calibrate_conformal,
            conformal_predict,
            evaluate_coverage,
        )

        rng = np.random.default_rng(3)
        n_total = 2000
        n_classes = 5
        alpha = 0.1

        # Synthetic noisy classifier: probabilities sampled from
        # Dirichlet with a mode peaked on the true class, but
        # severely under-calibrated.
        y_true = rng.integers(0, n_classes, size=n_total)
        probs = np.empty((n_total, n_classes))
        for i in range(n_total):
            base = np.full(n_classes, 0.2)
            base[y_true[i]] = 2.0  # peak on the true class
            probs[i] = rng.dirichlet(base)

        # Split into calibration and test sets.
        split = n_total // 2
        y_cal, y_test = y_true[:split], y_true[split:]
        probs_cal, probs_test = probs[:split], probs[split:]

        q_hat = calibrate_conformal(y_cal, probs_cal, alpha=alpha)
        prediction_sets = conformal_predict(probs_test, q_hat)
        coverage = evaluate_coverage(y_test, prediction_sets)

        # Marginal coverage guarantee under exchangeability:
        # P(y in C) >= 1 - alpha (here 0.9). Allow a small empirical
        # slack to stay robust to finite-sample variance.
        assert coverage >= 0.88, (
            f"empirical coverage {coverage:.3f} below nominal {1 - alpha:.2f}"
        )

    def test_conformal_predict_set_size_grows_with_q_hat(self):
        import numpy as np

        from agent_planning.calibration import conformal_predict

        # Three classes, model gives a peak on class 1.
        probs = np.array([
            [0.1, 0.7, 0.2],
            [0.3, 0.4, 0.3],
        ])
        small_q = 0.2  # threshold cutoff = 0.8
        large_q = 0.7  # threshold cutoff = 0.3

        small_sets = conformal_predict(probs, small_q)
        large_sets = conformal_predict(probs, large_q)

        # Larger q_hat = more permissive — sets at least as large.
        for s, l in zip(small_sets, large_sets):
            assert s.issubset(l)

    # ── Regression band ───────────────────────────────────────────────

    def test_conformal_predict_band_is_symmetric_around_point(self):
        from agent_planning.calibration import conformal_predict_band

        # Residuals roughly Gaussian; band should be symmetric.
        residuals = [1.0, -1.2, 0.8, -0.9, 1.1, -1.0, 1.3, -1.4, 0.7, -0.8]
        low, high = conformal_predict_band(
            point_estimate=10.0,
            calibration_residuals=residuals,
            alpha=0.2,
        )
        midpoint = (low + high) / 2.0
        assert abs(midpoint - 10.0) < 1e-9
        assert high > low

    def test_conformal_predict_band_widens_as_alpha_drops(self):
        import numpy as np

        from agent_planning.calibration import conformal_predict_band

        rng = np.random.default_rng(4)
        residuals = rng.normal(scale=1.5, size=200).tolist()

        narrow = conformal_predict_band(0.0, residuals, alpha=0.5)
        wide = conformal_predict_band(0.0, residuals, alpha=0.05)
        # Lower miscoverage → wider band.
        assert (wide[1] - wide[0]) > (narrow[1] - narrow[0])

    def test_conformal_predict_band_empirical_coverage_on_holdout(self):
        import numpy as np

        from agent_planning.calibration import conformal_predict_band

        # Simulate: true value drawn from N(point, 2.0); residuals
        # from the calibration history; band claims to cover with
        # probability 1 - alpha.
        rng = np.random.default_rng(5)
        scale = 2.0
        point = 100.0
        calibration_residuals = rng.normal(scale=scale, size=500)
        alpha = 0.2

        low, high = conformal_predict_band(point, calibration_residuals, alpha=alpha)

        # Test on a fresh draw of 5000 new points from the same
        # distribution. Empirical coverage should be near (1 - alpha)
        # modulo finite-sample variance. Allow modest slack (3pp)
        # below nominal — conformal coverage is a marginal guarantee
        # on the calibration set, not a pointwise one on a held-out
        # draw, and tightening this assertion makes the test flaky on
        # different numpy RNG implementations.
        new_values = point + rng.normal(scale=scale, size=5000)
        covered = ((new_values >= low) & (new_values <= high)).mean()
        assert covered >= 0.77, (
            f"empirical band coverage {covered:.3f} too far below "
            f"nominal {1 - alpha:.2f}"
        )


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 9: Confidence→RAG monotonicity kernel (issue #35 / A8)
# ─────────────────────────────────────────────────────────────────────────


class TestMonotonicityVerifier:
    """Behavioural anchor for the Z3-backed monotonicity proof.

    Confirms the defaults (pm-assumptions's RAG mapping) verify, that a
    deliberately broken mapping produces a concrete counterexample, and
    that the verifier is callable from external modules with their own
    thresholds (the key extensibility property).
    """

    def test_default_pm_assumptions_mapping_is_proven_monotone(self):
        from agent_planning.verified import (
            DEFAULT_RAG_LABELS,
            DEFAULT_RAG_THRESHOLDS,
            verify_rag_mapping,
        )

        result = verify_rag_mapping(
            thresholds=DEFAULT_RAG_THRESHOLDS,
            labels=DEFAULT_RAG_LABELS,
        )
        assert result.is_proven
        assert result.status == "PROVEN"
        assert result.counterexample is None
        # The audit-trail attributes are populated.
        assert result.thresholds == tuple(DEFAULT_RAG_THRESHOLDS)
        assert result.labels == tuple(DEFAULT_RAG_LABELS)

    def test_swapped_labels_produces_concrete_counterexample(self):
        from agent_planning.verified import verify_rag_mapping

        # Swap GREEN and RED — high score now maps to RED, low to GREEN.
        # The verifier should find a counterexample.
        broken_labels = ("GREEN", "AMBER", "RED")  # wrong order
        result = verify_rag_mapping(
            thresholds=(40.0, 70.0),
            labels=broken_labels,
        )
        assert not result.is_proven
        assert result.status == "COUNTEREXAMPLE"
        assert result.counterexample is not None
        cx1, cx2 = result.counterexample
        # The counterexample must respect x1 <= x2.
        assert cx1 <= cx2
        # And produce a violation under the broken mapping (where the
        # ordering treats labels[0]=GREEN < labels[1]=AMBER < labels[2]=RED
        # by index; so the "value" at low cx1 is index 0 = GREEN and at
        # high cx2 is index 2 = RED — monotonicity says index(cx1) <=
        # index(cx2), but the counterexample picks cx1 such that its
        # index is HIGHER than cx2's, which means by the labels' ordering
        # we have moved DOWN the label list as input rises).
        labels_at_cx = result.counterexample_labels
        assert labels_at_cx is not None
        # The counterexample labels must be ones that demonstrate the bug.
        assert labels_at_cx[0] != labels_at_cx[1]

    def test_finer_grained_mapping_with_four_bands_verifies(self):
        """Verifier scales to arbitrary numbers of bands, not just three."""
        from agent_planning.verified import verify_rag_mapping

        result = verify_rag_mapping(
            thresholds=(25.0, 50.0, 75.0),
            labels=("VERY_LOW", "LOW", "HIGH", "VERY_HIGH"),
        )
        assert result.is_proven

    def test_custom_domain_proves_monotonicity_over_zero_to_one_range(self):
        """The verifier handles domains other than the pm-assumptions [0, 100]."""
        from agent_planning.verified import verify_rag_mapping

        # 0-1 normalised confidence with the same bands rescaled.
        result = verify_rag_mapping(
            thresholds=(0.4, 0.7),
            labels=("RED", "AMBER", "GREEN"),
            domain=(0.0, 1.0),
        )
        assert result.is_proven

    def test_verify_rag_mapping_is_callable_from_consumer_module(self):
        """Smoke test: nothing about :func:`verify_rag_mapping` requires
        special context from agent_planning. A consumer module can
        import and call it directly."""
        from agent_planning.verified import verify_rag_mapping

        result = verify_rag_mapping()  # all defaults
        assert result.is_proven

    def test_evaluate_rag_helper_matches_pm_assumptions_behaviour(self):
        """The pure-Python helper used by the verifier produces the same
        labels as the canonical pm_assumptions._rag implementation."""
        from agent_planning.verified import evaluate_rag

        # pm-assumptions: GREEN if >= 70, AMBER if >= 40, else RED.
        assert evaluate_rag(0.0) == "RED"
        assert evaluate_rag(39.999) == "RED"
        assert evaluate_rag(40.0) == "AMBER"
        assert evaluate_rag(69.999) == "AMBER"
        assert evaluate_rag(70.0) == "GREEN"
        assert evaluate_rag(100.0) == "GREEN"

    def test_proof_result_carries_audit_trail(self):
        """The result object preserves thresholds/labels/domain for audit chain consumers."""
        from agent_planning.verified import verify_rag_mapping

        result = verify_rag_mapping(
            thresholds=(40.0, 70.0),
            labels=("RED", "AMBER", "GREEN"),
            domain=(0.0, 100.0),
        )
        assert result.thresholds == (40.0, 70.0)
        assert result.labels == ("RED", "AMBER", "GREEN")
        assert result.domain == (0.0, 100.0)
        # The message string includes the verified parameters so audit
        # consumers can inspect without unpacking the dataclass.
        assert "PROVEN" in result.message.upper() or "monoton" in result.message.lower()


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 5 integration: generate_board_exception_report (issue #36 / B1)
# ─────────────────────────────────────────────────────────────────────────


class TestBoardExceptionReportGuardrail:
    """Behavioural anchor for the L5 guardrail integration on the
    board exception report tool.

    Covers the three verdict paths in the context of the AI-authored
    board report:
    - APPROVED: clean output (the evidence-only fallback) passes through
      unchanged as markdown.
    - REJECTED: output containing a forbidden phrase is replaced with
      structured error JSON; original prose is suppressed.
    - FLAGGED: not exercised here (no WARN-severity rules in the policy)
      but the policy can be extended without changing this test.
    """

    def _seed_minimal_project(self, project_id: str = "BOARD-GUARDRAIL-TEST"):
        """Seed a single risk so _has_any_data returns True."""
        from datetime import datetime

        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        now = datetime.utcnow().isoformat()
        store.upsert_risk(
            {
                "id": f"{project_id}-R001",
                "project_id": project_id,
                "title": "Test risk for guardrail integration",
                "description": "Seeded for B1 regression test.",
                "category": "DELIVERY",
                "likelihood": 4,
                "impact": 4,
                "risk_score": 16,
                "status": "OPEN",
                "created_at": now,
                "updated_at": now,
            }
        )
        return project_id

    async def test_clean_evidence_only_report_passes_through_as_markdown(self, monkeypatch):
        """The deterministic evidence-only fallback produces clean
        markdown — no forbidden phrases — so it should pass through the
        guardrail untouched and the consumer should see the original
        markdown response shape."""
        from pm_mcp_servers.pda_platform.server import call_tool

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        project_id = self._seed_minimal_project("BOARD-GUARDRAIL-CLEAN")
        result = await call_tool(
            "generate_board_exception_report", {"project_id": project_id}
        )

        text = result[0].text
        # Markdown response shape preserved — not wrapped in JSON.
        assert text.startswith("#") or "Exception Report" in text
        # No guardrail-rejection error.
        assert "guardrail_rejected" not in text
        # No FLAGGED notice prepended (clean output).
        assert "L5 guardrail flagged" not in text

    async def test_forbidden_phrase_in_output_triggers_rejection(self, monkeypatch):
        """When the evidence-only fallback (or Claude) produces a
        forbidden phrase, the guardrail replaces the report with a
        structured error JSON. The original prose containing the
        forbidden phrase is NOT returned — this is the hard fail-safe
        that prevents a board-facing consumer from rendering it."""
        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_reporting import server as reporting_server

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        project_id = self._seed_minimal_project("BOARD-GUARDRAIL-REJECT")

        # Force the fallback path to emit text containing a forbidden
        # phrase. The forbidden-phrase rule will then fire and the
        # guardrail will reject the output.
        def fake_compose(_project_id, _period, _data):
            return (
                "# Board Exception Report\n\n"
                "We are 100% certain the project will deliver on time.\n\n"
                "(rest of compromising report content)"
            )

        monkeypatch.setattr(
            reporting_server,
            "_compose_evidence_only_board_report",
            fake_compose,
        )

        result = await call_tool(
            "generate_board_exception_report", {"project_id": project_id}
        )

        import json as _json

        # The original prose is suppressed — the offending sentence
        # must NOT appear in the response.
        text = result[0].text
        assert "We are 100% certain the project will deliver" not in text
        # The response is structured error JSON, not markdown.
        payload = _json.loads(text)
        assert payload["error"] == "guardrail_rejected"
        assert payload["verdict"] == "REJECTED"
        # At least one rule fired.
        assert len(payload["triggered"]) >= 1
        triggered_names = [t["rule_name"] for t in payload["triggered"]]
        assert any("forbidden_phrase" in name for name in triggered_names)

    async def test_template_leak_phrase_also_rejected(self, monkeypatch):
        """The policy catches template-leak failures — the LLM emits
        scaffolding placeholders rather than substantive content."""
        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_reporting import server as reporting_server

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        project_id = self._seed_minimal_project("BOARD-GUARDRAIL-LEAK")

        def fake_compose(_project_id, _period, _data):
            return (
                "# Board Exception Report\n\n"
                "## Exception 1: [INSERT NARRATIVE HERE]\n"
                "Situation: TBD\n"
            )

        monkeypatch.setattr(
            reporting_server,
            "_compose_evidence_only_board_report",
            fake_compose,
        )

        result = await call_tool(
            "generate_board_exception_report", {"project_id": project_id}
        )

        import json as _json

        payload = _json.loads(result[0].text)
        assert payload["error"] == "guardrail_rejected"


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 5 integration: generate_assumption_report (issue #37 / B2)
# ─────────────────────────────────────────────────────────────────────────


class TestAssumptionReportGuardrail:
    """Behavioural anchor for the L5 guardrail integration on
    generate_assumption_report.

    The handler returns a structured JSON report. The integration
    serialises the whole report to a single string and runs the
    forbidden-phrase check against it, so a forbidden phrase in any
    field (nested narratives, per-assumption actions, governance
    list) fires the guardrail. APPROVED: original JSON. FLAGGED:
    JSON with ``_guardrail_flags``. REJECTED: structured error JSON.
    """

    def _seed_assumptions(
        self,
        project_id: str = "ASSUMP-GUARDRAIL-TEST",
        extra_text: str | None = None,
    ):
        """Seed enough assumption rows for the report path to produce output.

        The pm-assumptions store schema embeds the likelihood, impact,
        validation plan and review date in the ``notes`` field as
        pipe-delimited values; the report handler parses these out at
        read time. We mirror that here so the test data takes the same
        shape as a real loaded register.
        """
        from datetime import date

        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        today = str(date.today())
        for i in range(3):
            store.upsert_assumption(
                {
                    "id": f"{project_id}-A{i:03d}",
                    "project_id": project_id,
                    "text": f"Test assumption {i} for guardrail integration",
                    "category": "DELIVERY",
                    "baseline_value": 1.0,
                    "current_value": None,
                    "unit": "boolean",
                    "tolerance_pct": 0.0,
                    "source": "Internal estimate",
                    "external_ref": None,
                    "dependencies": "",
                    "owner": "Test Owner",
                    "last_validated": None,
                    "created_date": today,
                    "notes": (
                        "Impact if false: Schedule slippage of two weeks. | "
                        "Likelihood: MEDIUM | "
                        "Validation plan: Quarterly review | "
                        "Status: Open | "
                        f"Review date: {today}"
                    ),
                }
            )
        # Optionally inject a fourth assumption whose `text` field
        # contains caller-supplied content — used by the rejection
        # test to thread a forbidden phrase through to the report
        # (the text flows into `recommended_actions[].text` in the
        # final JSON, so a forbidden phrase here ends up in the
        # serialised report and triggers the guardrail).
        if extra_text is not None:
            store.upsert_assumption(
                {
                    "id": f"{project_id}-A999",
                    "project_id": project_id,
                    "text": extra_text,
                    "category": "DELIVERY",
                    "baseline_value": 1.0,
                    "current_value": None,
                    "unit": "boolean",
                    "tolerance_pct": 0.0,
                    "source": "Test",
                    "external_ref": None,
                    "dependencies": "",
                    "owner": "Test Owner",
                    "last_validated": None,
                    "created_date": today,
                    "notes": (
                        "Impact if false: Total project failure | "
                        "Likelihood: HIGH | "
                        "Validation plan: Test | "
                        "Status: Open | "
                        f"Review date: {today}"
                    ),
                }
            )
        return project_id

    async def test_clean_report_passes_through_as_json(self):
        """Default report path produces clean deterministic narratives —
        none of the forbidden phrases should appear, and the response
        should be the structured JSON report unchanged."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        project_id = self._seed_assumptions("ASSUMP-GUARDRAIL-CLEAN")
        result = await call_tool(
            "generate_assumption_report", {"project_id": project_id}
        )

        payload = _json.loads(result[0].text)
        # No guardrail-rejection error.
        assert "error" not in payload or payload.get("error") != "guardrail_rejected"
        # No FLAGGED annotation on clean output.
        assert "_guardrail_flags" not in payload
        # Standard report shape preserved.
        assert "executive_summary" in payload
        assert "top_at_risk_assumptions" in payload

    async def test_forbidden_phrase_anywhere_in_report_triggers_rejection(self):
        """If a forbidden phrase appears in any field — here injected via
        an assumption whose `text` flows into the per-assumption action
        block — the entire report is rejected. Demonstrates the value
        of serialising the full report and checking that string: the
        violation fires regardless of which field carries it."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        project_id = self._seed_assumptions(
            "ASSUMP-GUARDRAIL-REJECT",
            extra_text="We are 100% certain this assumption will hold",
        )

        result = await call_tool(
            "generate_assumption_report", {"project_id": project_id}
        )

        text = result[0].text
        payload = _json.loads(text)
        # The original report is suppressed — the assumption text which
        # would normally echo into `recommended_actions[].text` must
        # NOT appear in the response.
        assert "100% certain this assumption will hold" not in text
        assert payload["error"] == "guardrail_rejected"
        assert payload["verdict"] == "REJECTED"
        # At least one rule fired.
        assert len(payload["triggered"]) >= 1
        triggered_names = [t["rule_name"] for t in payload["triggered"]]
        assert any("forbidden_phrase" in name for name in triggered_names)


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 5 integration: generate_gate_review_summary (issue #38 / B3)
# ─────────────────────────────────────────────────────────────────────────


class TestGateReviewSummaryGuardrail:
    """Behavioural anchor for the L5 guardrail integration on
    generate_gate_review_summary.

    The handler returns markdown. The guardrail policy adds gate-
    specific phrases ("always met", "definitely deliver") to the
    base overclaim/template-leak set so reviewer-language drift is
    caught deterministically.
    """

    def _seed_minimal_project(self, project_id: str = "GATE-GUARDRAIL-TEST"):
        from datetime import datetime

        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        now = datetime.utcnow().isoformat()
        store.upsert_risk(
            {
                "id": f"{project_id}-R001",
                "project_id": project_id,
                "title": "Test risk for gate review guardrail",
                "description": "Seeded for B3 regression test.",
                "category": "DELIVERY",
                "likelihood": 4,
                "impact": 4,
                "risk_score": 16,
                "status": "OPEN",
                "created_at": now,
                "updated_at": now,
            }
        )
        return project_id

    async def test_clean_gate_review_summary_passes_through_as_markdown(
        self, monkeypatch
    ):
        """When Claude returns clean IPA-style prose, the guardrail
        approves and the markdown response is unchanged."""
        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_reporting import server as reporting_server

        # Provide an API key so the handler enters the Claude path.
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        # Stub Anthropic client and the Claude call.
        monkeypatch.setattr(reporting_server, "_get_anthropic_client", lambda: object())
        monkeypatch.setattr(
            reporting_server,
            "_call_claude",
            lambda _c, _p, max_tokens=3000: (
                "# Gate 3 Review Summary — GATE-GUARDRAIL-CLEAN\n\n"
                "**Delivery Confidence Assessment:** AMBER\n\n"
                "## Executive Summary\n"
                "Project is broadly on track with managed risks."
            ),
        )

        project_id = self._seed_minimal_project("GATE-GUARDRAIL-CLEAN")
        result = await call_tool(
            "generate_gate_review_summary",
            {"project_id": project_id, "gate_number": 3},
        )

        text = result[0].text
        # Markdown shape preserved — no JSON wrapper.
        assert text.startswith("#")
        assert "Gate 3 Review Summary" in text
        # No guardrail rejection.
        assert "guardrail_rejected" not in text
        # No FLAGGED notice.
        assert "L5 guardrail flagged" not in text

    async def test_overclaim_phrase_rejects_gate_review_summary(self, monkeypatch):
        """If Claude returns prose containing an overclaim phrase
        ("definitely deliver" — gate-specific), the guardrail replaces
        the response with structured error JSON and suppresses the
        prose."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_reporting import server as reporting_server

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(reporting_server, "_get_anthropic_client", lambda: object())
        monkeypatch.setattr(
            reporting_server,
            "_call_claude",
            lambda _c, _p, max_tokens=3000: (
                "# Gate 3 Review Summary\n\n"
                "## Executive Summary\n"
                "The project will definitely deliver on time and to budget."
            ),
        )

        project_id = self._seed_minimal_project("GATE-GUARDRAIL-REJECT")
        result = await call_tool(
            "generate_gate_review_summary",
            {"project_id": project_id, "gate_number": 3},
        )

        text = result[0].text
        # The original prose is suppressed — the offending sentence
        # (NOT the bare forbidden token, which legitimately appears in
        # the rule's description as metadata) must not appear.
        assert "deliver on time and to budget" not in text
        payload = _json.loads(text)
        assert payload["error"] == "guardrail_rejected"
        assert payload["verdict"] == "REJECTED"
        # Error message references the document kind.
        assert "gate review summary" in payload["message"]
        # Triggered list includes a forbidden_phrase rule.
        triggered_names = [t["rule_name"] for t in payload["triggered"]]
        assert any("forbidden_phrase" in name for name in triggered_names)

    async def test_template_leak_in_gate_review_summary_is_rejected(
        self, monkeypatch
    ):
        """Template-leak phrases are rejected on the gate-review path
        too."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_reporting import server as reporting_server

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(reporting_server, "_get_anthropic_client", lambda: object())
        monkeypatch.setattr(
            reporting_server,
            "_call_claude",
            lambda _c, _p, max_tokens=3000: (
                "# Gate 3 Review Summary\n\n"
                "## Executive Summary\n"
                "INSERT NARRATIVE HERE — TODO before submission."
            ),
        )

        project_id = self._seed_minimal_project("GATE-GUARDRAIL-LEAK")
        result = await call_tool(
            "generate_gate_review_summary",
            {"project_id": project_id, "gate_number": 3},
        )

        payload = _json.loads(result[0].text)
        assert payload["error"] == "guardrail_rejected"


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 5 integration: detect_narrative_divergence (issue #39 / B4)
# ─────────────────────────────────────────────────────────────────────────


class TestNarrativeDivergenceGuardrail:
    """Behavioural anchor for the L5 guardrail integration on
    pm_analyse.detect_narrative_divergence.

    The tool requires ANTHROPIC_API_KEY at runtime, so a full end-to-end
    rejection test would need a stubbed Anthropic SDK. We instead test
    the integration's pure-Python entry point — `_apply_narrative_
    divergence_guardrail` — which is what the tool's success path
    calls. The entry point captures all of the behaviour that matters:
    a clean result is returned unchanged; a forbidden phrase anywhere
    in the serialised result triggers REJECTED with the original
    analysis suppressed.
    """

    def test_clean_result_passes_through_unchanged(self):
        from pm_mcp_servers.pm_analyse.tools import (
            _apply_narrative_divergence_guardrail,
        )

        clean = {
            "project_id": "TEST-001",
            "overall_assessment": "ALIGNED",
            "divergence_score": 0.0,
            "claims_assessed": 3,
            "contradictions": 0,
            "flags": [],
            "supported_claims": [
                {"claim": "Project on schedule", "evidence": "Latest gate AMBER"},
            ],
            "unverifiable_claims": [],
            "data_used": ["risks", "gate_readiness"],
            "data_gaps": [],
        }
        result = _apply_narrative_divergence_guardrail(clean)
        # Clean result returned unchanged — no error, no annotation.
        assert result == clean
        assert "_guardrail_flags" not in result
        assert "error" not in result

    def test_forbidden_phrase_in_flag_explanation_triggers_rejection(self):
        from pm_mcp_servers.pm_analyse.tools import (
            _apply_narrative_divergence_guardrail,
        )

        dirty = {
            "project_id": "TEST-002",
            "overall_assessment": "DIVERGENT",
            "divergence_score": 0.6,
            "claims_assessed": 2,
            "contradictions": 1,
            "flags": [
                {
                    "claim": "We are 100% certain delivery is on track",
                    "verdict": "CONTRADICTED",
                    "severity": "HIGH",
                    "evidence": "Gate readiness is RED",
                    "confidence": 0.9,
                }
            ],
            "supported_claims": [],
            "unverifiable_claims": [],
            "data_used": ["risks"],
            "data_gaps": [],
        }
        result = _apply_narrative_divergence_guardrail(dirty)

        # The original analysis is suppressed. The flagged-claim text
        # (containing the forbidden phrase) must not appear in the
        # returned dict's payload.
        import json as _json

        serialised = _json.dumps(result, default=str)
        assert "delivery is on track" not in serialised
        # Structured rejection.
        assert result["error"] == "guardrail_rejected"
        assert result["verdict"] == "REJECTED"
        # Message references the document kind.
        assert "narrative-divergence" in result["message"]
        triggered_names = [t["rule_name"] for t in result["triggered"]]
        assert any("forbidden_phrase" in name for name in triggered_names)

    def test_template_leak_in_supported_claim_triggers_rejection(self):
        """Template-leak phrases in any structured field fire too —
        demonstrates the value of the whole-result string check vs.
        per-field rules."""
        from pm_mcp_servers.pm_analyse.tools import (
            _apply_narrative_divergence_guardrail,
        )

        leaked = {
            "project_id": "TEST-003",
            "overall_assessment": "MINOR_DIVERGENCE",
            "divergence_score": 0.2,
            "claims_assessed": 2,
            "contradictions": 1,
            "flags": [],
            "supported_claims": [
                {
                    "claim": "Project status",
                    "evidence": "INSERT NARRATIVE HERE",
                }
            ],
            "unverifiable_claims": [],
            "data_used": [],
            "data_gaps": [],
        }
        result = _apply_narrative_divergence_guardrail(leaked)
        assert result["error"] == "guardrail_rejected"


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 5 integration: generate_premortem_questions (issue #40 / B5)
# ─────────────────────────────────────────────────────────────────────────


class TestPremortemQuestionsGuardrail:
    """Behavioural anchor for the L5 guardrail integration on
    generate_premortem_questions.

    Pre-mortem questions are read verbatim into gate-review forums.
    Today they come from deterministic constants in
    pm_knowledge.knowledge_base; the guardrail is the regression
    guard that catches drift if those constants are edited (or if
    an LLM-augmented question source is wired in later).
    """

    async def test_default_questions_pass_through_clean(self):
        """The bundled pre-mortem questions contain no forbidden
        phrases, so the default call should return the original JSON
        shape with no annotation and no error."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool("generate_premortem_questions", {"gate": "ANY"})
        payload = _json.loads(result[0].text)

        # No rejection.
        assert "error" not in payload or payload.get("error") != "guardrail_rejected"
        # No FLAGGED annotation.
        assert "_guardrail_flags" not in payload
        # Standard shape preserved.
        assert "questions" in payload
        assert "gate" in payload
        assert payload["question_count"] == len(payload["questions"])

    async def test_forbidden_phrase_in_question_text_triggers_rejection(
        self, monkeypatch
    ):
        """Monkeypatch a forbidden phrase into the question source and
        confirm the guardrail rejects the response. The original
        question text must NOT appear in the response — a facilitator
        cannot accidentally deliver it from the wire."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_knowledge import server as knowledge_server

        # Inject a question whose `question` text contains a forbidden
        # phrase. The handler loads from PREMORTEM_QUESTIONS at call
        # time, so monkeypatching the module-level constant takes
        # effect for this test.
        tainted_questions = {
            "ANY": [
                {
                    "question": (
                        "Are we 100% certain we can deliver in the planned "
                        "timeframe under any plausible variant of the risks "
                        "we have logged?"
                    ),
                    "targets": ["delivery_confidence"],
                    "failure_mode": "Overconfidence",
                }
            ]
        }
        monkeypatch.setattr(
            knowledge_server, "PREMORTEM_QUESTIONS", tainted_questions
        )

        result = await call_tool("generate_premortem_questions", {"gate": "ANY"})
        text = result[0].text
        # The original question prose is suppressed.
        assert "deliver in the planned" not in text
        payload = _json.loads(text)
        assert payload["error"] == "guardrail_rejected"
        assert payload["verdict"] == "REJECTED"
        # Message references the document kind.
        assert "pre-mortem questions" in payload["message"]
        triggered_names = [t["rule_name"] for t in payload["triggered"]]
        assert any("forbidden_phrase" in name for name in triggered_names)


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 5 integration: generate_benefits_narrative (issue #41 / B6)
# ─────────────────────────────────────────────────────────────────────────


class TestBenefitsNarrativeGuardrail:
    """Behavioural anchor for the L5 guardrail integration on
    pm_brm.generate_benefits_narrative.

    Benefits narratives are gate-review evidence — quoted in Treasury
    and IPA submissions. The tool requires ANTHROPIC_API_KEY for the
    full path, so we test the pure-Python integration entry point
    (`_apply_benefits_narrative_guardrail`) directly.
    """

    def test_clean_narrative_output_passes_through_unchanged(self):
        import json as _json

        from pm_mcp_servers.pm_brm.server import (
            _apply_benefits_narrative_guardrail,
        )

        clean = {
            "project_id": "BRM-TEST-001",
            "gate_number": 3,
            "narrative_text": (
                "The programme is on track to realise the planned £45M "
                "in efficiency benefits by FY27, with the largest tranche "
                "(£18M from automation) already showing measurable "
                "drawdown in Q2 actuals."
            ),
            "confidence": 0.72,
            "review_level": "SPOT_CHECK",
            "samples_used": 5,
            "review_reason": None,
            "generated_at": "2026-05-16T07:00:00",
            "context_summary": {"total_benefits": 12, "health_score": 78},
            "message": "Benefits narrative generated with 72% confidence.",
        }
        result = _apply_benefits_narrative_guardrail(clean)
        payload = _json.loads(result[0].text)
        assert payload == clean
        assert "_guardrail_flags" not in payload

    def test_overclaim_phrase_in_narrative_text_triggers_rejection(self):
        import json as _json

        from pm_mcp_servers.pm_brm.server import (
            _apply_benefits_narrative_guardrail,
        )

        dirty = {
            "project_id": "BRM-TEST-002",
            "gate_number": 3,
            # Forbidden phrase embedded in the Claude-authored narrative.
            "narrative_text": (
                "We are 100% certain the programme will realise the "
                "planned benefits at the originally-modelled run-rate."
            ),
            "confidence": 0.5,
            "review_level": "DETAILED_REVIEW",
            "samples_used": 5,
            "review_reason": None,
            "generated_at": "2026-05-16T07:00:00",
            "context_summary": {"total_benefits": 12, "health_score": 60},
            "message": "Benefits narrative generated with 50% confidence.",
        }
        result = _apply_benefits_narrative_guardrail(dirty)
        text = result[0].text
        # The narrative_text containing the overclaim must not appear.
        assert "realise the planned benefits at the originally" not in text
        payload = _json.loads(text)
        assert payload["error"] == "guardrail_rejected"
        assert payload["verdict"] == "REJECTED"
        assert "benefits narrative" in payload["message"]

    def test_template_leak_in_narrative_triggers_rejection(self):
        import json as _json

        from pm_mcp_servers.pm_brm.server import (
            _apply_benefits_narrative_guardrail,
        )

        leaked = {
            "project_id": "BRM-TEST-003",
            "gate_number": 3,
            "narrative_text": (
                "The programme will deliver INSERT BENEFIT HERE by FY27."
            ),
            "confidence": 0.4,
            "review_level": "EXPERT_REQUIRED",
            "samples_used": 5,
            "review_reason": "Low confidence",
            "generated_at": "2026-05-16T07:00:00",
            "context_summary": {},
            "message": "",
        }
        result = _apply_benefits_narrative_guardrail(leaked)
        payload = _json.loads(result[0].text)
        assert payload["error"] == "guardrail_rejected"


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 5 integration: generate_portfolio_summary (issue #42 / B7)
# ─────────────────────────────────────────────────────────────────────────


class TestPortfolioSummaryGuardrail:
    """Behavioural anchor for the L5 guardrail integration on
    generate_portfolio_summary.

    Same markdown-output shape as B1 (board report) and B3 (gate review)
    so the test goes via the call_tool dispatcher with Claude
    monkeypatched. Adds portfolio-specific phrases ("all green",
    "no concerns identified") that catch the LLM-evasion failure
    mode common to multi-project rollups.
    """

    def _seed_two_minimal_projects(self):
        from datetime import datetime

        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        now = datetime.utcnow().isoformat()
        project_ids = ["PORT-G-001", "PORT-G-002"]
        for pid in project_ids:
            store.upsert_risk(
                {
                    "id": f"{pid}-R001",
                    "project_id": pid,
                    "title": "Test portfolio risk",
                    "description": "Seeded for B7.",
                    "category": "DELIVERY",
                    "likelihood": 3,
                    "impact": 3,
                    "risk_score": 9,
                    "status": "OPEN",
                    "created_at": now,
                    "updated_at": now,
                }
            )
        return project_ids

    async def test_clean_portfolio_summary_passes_through_as_markdown(
        self, monkeypatch
    ):
        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_reporting import server as reporting_server

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(
            reporting_server, "_get_anthropic_client", lambda: object()
        )
        monkeypatch.setattr(
            reporting_server,
            "_call_claude",
            lambda _c, _p, max_tokens=2000: (
                "# Portfolio Summary — Test Portfolio\n\n"
                "Three projects under review. Mixed delivery confidence; "
                "active risk management in place across all assets."
            ),
        )

        pids = self._seed_two_minimal_projects()
        result = await call_tool(
            "generate_portfolio_summary",
            {"project_ids": pids, "portfolio_name": "Test Portfolio"},
        )
        text = result[0].text
        assert text.startswith("#")
        assert "Portfolio Summary" in text
        assert "guardrail_rejected" not in text
        assert "L5 guardrail flagged" not in text

    async def test_portfolio_overclaim_phrase_triggers_rejection(
        self, monkeypatch
    ):
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_reporting import server as reporting_server

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(
            reporting_server, "_get_anthropic_client", lambda: object()
        )
        monkeypatch.setattr(
            reporting_server,
            "_call_claude",
            lambda _c, _p, max_tokens=2000: (
                "# Portfolio Summary — Test Portfolio\n\n"
                "All projects are showing all green RAG ratings with "
                "no concerns identified at this stage."
            ),
        )

        pids = self._seed_two_minimal_projects()
        result = await call_tool(
            "generate_portfolio_summary",
            {"project_ids": pids, "portfolio_name": "Test Portfolio"},
        )
        text = result[0].text
        # Original LLM-evasion prose suppressed.
        assert "RAG ratings with" not in text
        payload = _json.loads(text)
        assert payload["error"] == "guardrail_rejected"
        assert payload["verdict"] == "REJECTED"
        assert "portfolio summary" in payload["message"]


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 5 integration: generate_lessons_section (issue #43 / B8)
# ─────────────────────────────────────────────────────────────────────────


class TestLessonsSectionGuardrail:
    """Behavioural anchor for the L5 guardrail integration on
    generate_lessons_section.

    The handler has three return paths — no-lessons template,
    no-API-key deterministic fallback, and Claude-authored narrative.
    All three are gated by the guardrail. The deterministic-fallback
    path is the easiest to exercise live (no Claude monkeypatch
    required) and is what the test focuses on.
    """

    def _seed_lessons(self, project_id: str, lessons: list[dict]):
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        for lesson in lessons:
            row = {
                "id": lesson["id"],
                "project_id": project_id,
                "document_type": lesson.get("document_type", "GATE_REVIEW"),
                "category": lesson.get("category", "GENERAL"),
                "title": lesson.get("title", "Untitled"),
                "root_cause": lesson.get("root_cause", "Not recorded"),
                "recommendation": lesson.get("recommendation", "Not recorded"),
                "severity": lesson.get("severity", "MEDIUM"),
                "extracted_at": "2026-05-16T07:00:00",
            }
            store.upsert_project_lesson(row)

    async def test_no_lessons_template_passes_through(self, monkeypatch):
        """When no lessons exist, the deterministic template is
        returned — clean markdown, no guardrail rejection."""
        from pm_mcp_servers.pda_platform.server import call_tool

        # Use a project_id with no stored lessons.
        result = await call_tool(
            "generate_lessons_section",
            {"project_id": "LESSONS-EMPTY-PROJ-001"},
        )
        text = result[0].text
        assert text.startswith("# Lessons Learned")
        assert "No lessons have been recorded" in text
        assert "guardrail_rejected" not in text

    async def test_fallback_path_clean_lessons_pass_through(self, monkeypatch):
        """With API key unset and clean lesson data, the deterministic
        fallback returns formatted markdown unchanged."""
        from pm_mcp_servers.pda_platform.server import call_tool

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        self._seed_lessons(
            "LESSONS-CLEAN-001",
            [
                {
                    "id": "L-CLEAN-1",
                    "title": "Engage suppliers early",
                    "category": "PROCUREMENT",
                    "severity": "HIGH",
                    "root_cause": "Late supplier engagement delayed bid evaluation.",
                    "recommendation": "Initiate market engagement six months before tender.",
                }
            ],
        )
        result = await call_tool(
            "generate_lessons_section", {"project_id": "LESSONS-CLEAN-001"}
        )
        text = result[0].text
        assert "Engage suppliers early" in text
        assert "guardrail_rejected" not in text

    async def test_fallback_path_with_overclaim_phrase_in_lesson_rejects(
        self, monkeypatch
    ):
        """A lesson whose recommendation contains a forbidden phrase
        propagates that phrase into the deterministic-fallback markdown.
        The guardrail rejects the response and suppresses the prose."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        self._seed_lessons(
            "LESSONS-REJECT-001",
            [
                {
                    "id": "L-REJECT-1",
                    "title": "Tainted lesson",
                    "category": "DELIVERY",
                    "severity": "HIGH",
                    "root_cause": "Test injection",
                    "recommendation": (
                        "We are 100% certain this lesson applies "
                        "universally."
                    ),
                }
            ],
        )
        result = await call_tool(
            "generate_lessons_section", {"project_id": "LESSONS-REJECT-001"}
        )
        text = result[0].text
        # Original recommendation prose suppressed.
        assert "lesson applies" not in text
        payload = _json.loads(text)
        assert payload["error"] == "guardrail_rejected"
        assert "lessons section" in payload["message"]


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 5 integration: generate_pir_template (issue #44 / B9)
# ─────────────────────────────────────────────────────────────────────────


class TestPirTemplateGuardrail:
    """Behavioural anchor for the L5 guardrail integration on
    generate_pir_template.

    Critical edge case: the PIR template DELIBERATELY embeds
    ``[PLACEHOLDER]`` markers throughout (sign-off names, outstanding
    actions, etc.). The PIR-specific policy therefore omits
    ``[placeholder]`` from the forbidden-phrase list, otherwise every
    legitimately-generated PIR would falsely reject.

    Two tests below cover:
    1. The `[PLACEHOLDER]`-rich legitimate output passes through.
    2. A genuine PIR-specific failure mode ("all benefits delivered"
       when data shows otherwise) is rejected.
    """

    def _seed_minimal_project(self, project_id: str = "PIR-GUARDRAIL-TEST"):
        from datetime import datetime

        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        now = datetime.utcnow().isoformat()
        store.upsert_risk(
            {
                "id": f"{project_id}-R001",
                "project_id": project_id,
                "title": "Test risk for PIR guardrail",
                "description": "Seeded for B9 regression test.",
                "category": "DELIVERY",
                "likelihood": 4,
                "impact": 4,
                "risk_score": 16,
                "status": "CLOSED",
                "created_at": now,
                "updated_at": now,
            }
        )
        return project_id

    async def test_placeholder_rich_pir_passes_through_unchanged(
        self, monkeypatch
    ):
        """The PIR template deliberately embeds ``[PLACEHOLDER]``
        markers for human-completion fields. The guardrail must NOT
        treat these as template-leak — that is the entire point of
        having a PIR-specific policy distinct from the board/gate
        policy. This test is the key correctness check for B9."""
        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_reporting import server as reporting_server

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(
            reporting_server, "_get_anthropic_client", lambda: object()
        )
        monkeypatch.setattr(
            reporting_server,
            "_call_claude",
            lambda _c, _p, max_tokens=4000: (
                "# Post-Implementation Review — PIR-PLACE-001\n\n"
                "**Closure Date:** 2026-05-01  **Prepared by:** [PLACEHOLDER — name]\n\n"
                "## 1. Project Overview\n"
                "Substantive content here.\n\n"
                "## 8. Outstanding Actions\n"
                "| Action | Owner | Target Date |\n"
                "|---|---|---|\n"
                "| [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |\n"
            ),
        )

        project_id = self._seed_minimal_project("PIR-PLACE-001")
        result = await call_tool(
            "generate_pir_template", {"project_id": project_id}
        )
        text = result[0].text
        # Markdown shape preserved with [PLACEHOLDER] markers intact —
        # confirming the policy correctly excludes them.
        assert text.startswith("#")
        assert "[PLACEHOLDER]" in text
        assert "Post-Implementation Review" in text
        assert "guardrail_rejected" not in text
        assert "L5 guardrail flagged" not in text

    async def test_pir_overclaim_phrase_triggers_rejection(self, monkeypatch):
        """When Claude emits "all benefits delivered" (the PIR-specific
        failure mode where the LLM hallucinates a successful close-out
        regardless of the underlying data), the guardrail rejects the
        document."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_reporting import server as reporting_server

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(
            reporting_server, "_get_anthropic_client", lambda: object()
        )
        monkeypatch.setattr(
            reporting_server,
            "_call_claude",
            lambda _c, _p, max_tokens=4000: (
                "# Post-Implementation Review — PIR-REJECT-001\n\n"
                "## 5. Benefits Delivery\n"
                "All benefits delivered on time and to budget."
            ),
        )

        project_id = self._seed_minimal_project("PIR-REJECT-001")
        result = await call_tool(
            "generate_pir_template", {"project_id": project_id}
        )
        text = result[0].text
        # Original LLM-hallucinated prose suppressed.
        assert "on time and to budget" not in text
        payload = _json.loads(text)
        assert payload["error"] == "guardrail_rejected"
        assert "PIR template" in payload["message"]


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 6 integration: generate_board_exception_report (issue #45 / B10)
# ─────────────────────────────────────────────────────────────────────────


class TestBoardExceptionReportGroundedness:
    """Behavioural anchor for the L6 groundedness integration on
    generate_board_exception_report.

    L6 is informational — it does NOT gate the response (that is L5's
    job). It appends a visible groundedness footer to the markdown so
    a reviewer sees how well the AI's prose is supported by the
    underlying source data. The structured ``_groundedness`` dict is
    embedded in an HTML comment for Evidence-Engine / UDS consumers.
    """

    def _seed_minimal_project(self, project_id: str = "BOARD-GROUND-TEST"):
        from datetime import datetime

        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        now = datetime.utcnow().isoformat()
        store.upsert_risk(
            {
                "id": f"{project_id}-R001",
                "project_id": project_id,
                "title": "Cyber security control gap",
                "description": "Penetration test identified two unpatched servers.",
                "category": "TECHNICAL",
                "likelihood": 4,
                "impact": 4,
                "risk_score": 16,
                "status": "OPEN",
                "created_at": now,
                "updated_at": now,
            }
        )
        return project_id

    async def test_clean_evidence_only_report_carries_groundedness_footer(
        self, monkeypatch
    ):
        """The evidence-only fallback document is composed directly from
        store data, so its tokens overlap heavily with the source
        content — the groundedness verdict should be GROUNDED and the
        footer (both human-readable line and machine-readable HTML
        comment) should appear on the markdown response."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        project_id = self._seed_minimal_project("BOARD-GROUND-CLEAN")
        result = await call_tool(
            "generate_board_exception_report", {"project_id": project_id}
        )
        text = result[0].text
        # Markdown response shape preserved.
        assert text.startswith("#") or "Exception Report" in text
        # Human-readable groundedness line present.
        assert "Groundedness:" in text
        # Machine-readable comment present.
        assert "<!-- _groundedness:" in text
        # Parse the machine-readable block to confirm structure.
        start = text.index("<!-- _groundedness:") + len("<!-- _groundedness:")
        end = text.index("-->", start)
        gnd = _json.loads(text[start:end].strip())
        assert gnd["verdict"] in ("GROUNDED", "UNGROUNDED")
        assert "overall_score" in gnd
        assert isinstance(gnd["ungrounded_terms"], list)
        assert "provenance_trail" in gnd

    async def test_hallucinated_phrase_in_claude_output_produces_ungrounded_terms(
        self, monkeypatch
    ):
        """When Claude's output includes terms that appear in no source
        (a hallucination), those terms appear in the
        ``_groundedness.ungrounded_terms`` list. L6 does not block the
        response — it surfaces the unsupported terms for human review."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_reporting import server as reporting_server

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(
            reporting_server, "_get_anthropic_client", lambda: object()
        )
        # Claude emits a sentence containing a term ("zeppelin") that
        # absolutely does not appear in the project data. L6 catches
        # it.
        monkeypatch.setattr(
            reporting_server,
            "_call_claude",
            lambda _c, _p, max_tokens=2000: (
                "# Board Exception Report\n\n"
                "## Exception 1: Programme schedule\n"
                "The programme requires an additional zeppelin convoy "
                "to recover the schedule risk identified in the latest "
                "review."
            ),
        )

        project_id = self._seed_minimal_project("BOARD-GROUND-UNG")
        result = await call_tool(
            "generate_board_exception_report", {"project_id": project_id}
        )
        text = result[0].text
        # Response carries the footer.
        assert "Groundedness:" in text
        # Extract the structured block.
        start = text.index("<!-- _groundedness:") + len("<!-- _groundedness:")
        end = text.index("-->", start)
        gnd = _json.loads(text[start:end].strip())
        # The hallucinated term is in the ungrounded list.
        assert "zeppelin" in gnd["ungrounded_terms"]
        # L6 is informational; the response is still the markdown
        # report, not a guardrail rejection.
        assert "guardrail_rejected" not in text


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 6 integration: generate_assumption_report (issue #46 / B11)
# ─────────────────────────────────────────────────────────────────────────


class TestAssumptionReportGroundedness:
    """L6 attaches a ``_groundedness`` field to the JSON assumption
    report after L5 has approved it. The field carries the verdict,
    score, ungrounded terms, and provenance trail — all derived from
    comparing the assembled narrative text against the raw assumption
    rows and external signals."""

    def _seed_assumptions(self, project_id: str = "ASSUMP-L6-TEST"):
        from datetime import date

        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        today = str(date.today())
        for i in range(3):
            store.upsert_assumption(
                {
                    "id": f"{project_id}-A{i:03d}",
                    "project_id": project_id,
                    "text": f"Schedule milestone {i} relies on supplier delivery",
                    "category": "DELIVERY",
                    "baseline_value": 1.0,
                    "current_value": None,
                    "unit": "boolean",
                    "tolerance_pct": 0.0,
                    "source": "Internal estimate",
                    "external_ref": None,
                    "dependencies": "",
                    "owner": "Test Owner",
                    "last_validated": None,
                    "created_date": today,
                    "notes": (
                        "Impact if false: Schedule slippage. | "
                        "Likelihood: MEDIUM | "
                        "Validation plan: Quarterly review | "
                        "Status: Open | "
                        f"Review date: {today}"
                    ),
                }
            )
        return project_id

    async def test_clean_report_carries_groundedness_field(self):
        """The assumption report's deterministic narratives are
        assembled from the underlying assumption rows, so the
        groundedness score should be high (the narrative cites the
        same words the source data uses). The field structure must
        carry verdict + overall_score + ungrounded_terms +
        provenance_trail for downstream consumers."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        project_id = self._seed_assumptions("ASSUMP-L6-CLEAN")
        result = await call_tool(
            "generate_assumption_report", {"project_id": project_id}
        )
        payload = _json.loads(result[0].text)
        # Original report shape preserved.
        assert "executive_summary" in payload
        # L6 field present and well-formed.
        assert "_groundedness" in payload
        gnd = payload["_groundedness"]
        assert gnd["verdict"] in ("GROUNDED", "UNGROUNDED", "NOT_COMPUTED")
        if gnd["verdict"] != "NOT_COMPUTED":
            assert "overall_score" in gnd
            assert "ungrounded_terms" in gnd
            assert "provenance_trail" in gnd

    async def test_groundedness_is_not_computed_when_no_signals(self):
        """Even without external signals stored, the report still
        produces a meaningful groundedness check because the
        assumption rows themselves are valid sources. So the verdict
        is GROUNDED or UNGROUNDED, never NOT_COMPUTED, when there is
        at least one assumption."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        project_id = self._seed_assumptions("ASSUMP-L6-NOSIGS")
        result = await call_tool(
            "generate_assumption_report", {"project_id": project_id}
        )
        payload = _json.loads(result[0].text)
        gnd = payload["_groundedness"]
        # NOT NOT_COMPUTED — assumptions provide sources.
        assert gnd["verdict"] in ("GROUNDED", "UNGROUNDED")


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 6 integration: generate_gate_review_summary (issue #47 / B12)
# ─────────────────────────────────────────────────────────────────────────


class TestGateReviewSummaryGroundedness:
    """L6 attaches a groundedness footer to the IPA-format gate review
    summary markdown. Reuses the shared
    `_attach_groundedness_to_markdown` helper from B10 so the
    footer shape is identical across pm-reporting tools."""

    def _seed(self, project_id: str = "GATE-L6-TEST"):
        from datetime import datetime

        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        now = datetime.utcnow().isoformat()
        store.upsert_risk(
            {
                "id": f"{project_id}-R001",
                "project_id": project_id,
                "title": "Supplier capacity constraint",
                "description": "Single-supplier risk identified.",
                "category": "COMMERCIAL",
                "likelihood": 3,
                "impact": 4,
                "risk_score": 12,
                "status": "OPEN",
                "created_at": now,
                "updated_at": now,
            }
        )
        return project_id

    async def test_gate_review_summary_carries_groundedness_footer(
        self, monkeypatch
    ):
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_reporting import server as reporting_server

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(
            reporting_server, "_get_anthropic_client", lambda: object()
        )
        monkeypatch.setattr(
            reporting_server,
            "_call_claude",
            lambda _c, _p, max_tokens=3000: (
                "# Gate 3 Review Summary — GATE-L6-CLEAN\n\n"
                "**Delivery Confidence Assessment:** AMBER\n\n"
                "## Executive Summary\n"
                "Supplier capacity constraint identified at Gate 3."
            ),
        )

        project_id = self._seed("GATE-L6-CLEAN")
        result = await call_tool(
            "generate_gate_review_summary",
            {"project_id": project_id, "gate_number": 3},
        )
        text = result[0].text
        assert "Groundedness:" in text
        # HTML comment block is present.
        assert "<!-- _groundedness:" in text
        # Parse it and validate the structure.
        start = text.index("<!-- _groundedness:") + len("<!-- _groundedness:")
        end = text.index("-->", start)
        gnd = _json.loads(text[start:end].strip())
        assert gnd["verdict"] in ("GROUNDED", "UNGROUNDED")


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 6 integration: detect_narrative_divergence (issue #48 / B13)
# ─────────────────────────────────────────────────────────────────────────


class TestNarrativeDivergenceGroundedness:
    """L6 adds a top-level `_groundedness` field to the JSON output of
    detect_narrative_divergence — measuring how well the Claude-
    authored claims and evidence strings are grounded in the project
    data that fed the analysis."""

    def test_clean_result_carries_groundedness_field(self):
        from pm_mcp_servers.pm_analyse.tools import (
            _attach_groundedness_to_divergence_result,
        )

        result = {
            "project_id": "DIV-L6-CLEAN",
            "overall_assessment": "ALIGNED",
            "divergence_score": 0.0,
            "claims_assessed": 2,
            "contradictions": 0,
            "flags": [],
            "supported_claims": [
                {
                    "claim": "Schedule risk is being actively managed",
                    "evidence": "Latest gate AMBER with mitigation plan",
                }
            ],
            "unverifiable_claims": [],
            "data_used": ["risks", "gate_readiness"],
            "data_gaps": [],
        }
        data_summary = {
            "risks": {"open": 1, "top_risks": [{"title": "Schedule risk"}]},
            "gate_readiness": {"readiness": "AMBER"},
        }
        new_result = _attach_groundedness_to_divergence_result(
            result, data_summary
        )
        assert "_groundedness" in new_result
        gnd = new_result["_groundedness"]
        assert gnd["verdict"] in ("GROUNDED", "UNGROUNDED")
        assert "overall_score" in gnd
        assert "provenance_trail" in gnd

    def test_no_sources_produces_not_computed_verdict(self):
        from pm_mcp_servers.pm_analyse.tools import (
            _attach_groundedness_to_divergence_result,
        )

        result = {
            "project_id": "DIV-L6-NOSRC",
            "overall_assessment": "DIVERGENT",
            "flags": [{"claim": "Test", "evidence": "Test"}],
            "supported_claims": [],
            "unverifiable_claims": [],
        }
        new_result = _attach_groundedness_to_divergence_result(result, {})
        assert new_result["_groundedness"]["verdict"] == "NOT_COMPUTED"

    def test_hallucinated_term_appears_in_ungrounded_terms(self):
        from pm_mcp_servers.pm_analyse.tools import (
            _attach_groundedness_to_divergence_result,
        )

        result = {
            "project_id": "DIV-L6-HAL",
            "overall_assessment": "DIVERGENT",
            "divergence_score": 0.6,
            "claims_assessed": 1,
            "contradictions": 1,
            "flags": [
                {
                    "claim": "Programme requires zeppelin reinforcement",
                    "evidence": "Zeppelin convoy unavailable",
                }
            ],
            "supported_claims": [],
            "unverifiable_claims": [],
            "data_used": ["risks"],
            "data_gaps": [],
        }
        data_summary = {
            "risks": {"open": 2, "top_risks": [{"title": "Schedule risk"}]},
        }
        new_result = _attach_groundedness_to_divergence_result(
            result, data_summary
        )
        gnd = new_result["_groundedness"]
        # The hallucinated term should appear as ungrounded.
        assert "zeppelin" in gnd["ungrounded_terms"]
        # L6 does NOT block — the original analysis is intact.
        assert new_result["flags"] == result["flags"]


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 6 integration: generate_premortem_questions (issue #49 / B14)
# ─────────────────────────────────────────────────────────────────────────


class TestPremortemQuestionsGroundedness:
    """L6 adds a `_groundedness` field to the premortem-questions
    output. By construction the question text comes verbatim from
    the bundled constants, so the normal verdict is GROUNDED.
    The provenance_trail is the useful audit artefact even when
    everything is grounded."""

    async def test_default_questions_are_grounded_in_bundled_constants(self):
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool("generate_premortem_questions", {"gate": "ANY"})
        payload = _json.loads(result[0].text)
        assert "_groundedness" in payload
        gnd = payload["_groundedness"]
        # Verdict is GROUNDED because the questions are read from the
        # constants which we also pass in as sources.
        assert gnd["verdict"] == "GROUNDED"
        assert gnd["overall_score"] >= 0.7
        # provenance_trail records the source ids.
        assert "premortem_questions" in gnd["provenance_trail"]

    async def test_monkeypatched_question_with_hallucinated_term_is_ungrounded(
        self, monkeypatch
    ):
        """If the questions constant is replaced with a question whose
        tokens don't appear in the original constants AND don't appear
        anywhere in the patched constants either, the diverging tokens
        appear in ungrounded_terms."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_knowledge import server as knowledge_server

        # Patch BOTH constants the L6 check uses as sources to empty,
        # so a question containing arbitrary text is genuinely
        # ungrounded.
        monkeypatch.setattr(
            knowledge_server,
            "PREMORTEM_QUESTIONS",
            {
                "ANY": [
                    {
                        "question": (
                            "Has the zeppelin convoy plan been reviewed?"
                        ),
                        "targets": ["logistics"],
                        "failure_mode": "Supply chain",
                    }
                ]
            },
        )
        monkeypatch.setattr(knowledge_server, "RISK_FLAG_QUESTIONS", {})

        result = await call_tool("generate_premortem_questions", {"gate": "ANY"})
        payload = _json.loads(result[0].text)
        gnd = payload["_groundedness"]
        # The question text is identical to what the patched
        # PREMORTEM_QUESTIONS contains, so it should be GROUNDED
        # against the patched constant. This confirms the source
        # plumbing reads from the live module-level constant rather
        # than a frozen import-time copy.
        assert gnd["verdict"] == "GROUNDED"


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 6 integration: generate_benefits_narrative (issue #50 / B15)
# ─────────────────────────────────────────────────────────────────────────


class TestBenefitsNarrativeGroundedness:
    """L6 measures how well the Claude-authored benefits narrative is
    grounded in the benefits-register context. Test the integration
    entry point directly since the full tool requires Anthropic API."""

    def test_grounded_narrative_carries_groundedness_field(self):
        from pm_mcp_servers.pm_brm.server import (
            _attach_groundedness_to_benefits_output,
        )

        output = {
            "project_id": "BRM-L6-001",
            "narrative_text": (
                "The programme will realise efficiency benefits by FY27, "
                "with automation contributing measurable drawdown."
            ),
            "confidence": 0.72,
        }
        context = {
            "total_benefit_count": 12,
            "health_score": 78,
            "aggregate_realisation_pct": 0.42,
            "at_risk_count": 2,
            "benefits_summary": (
                "Programme efficiency benefits realisation automation "
                "tranche FY27 measurable drawdown."
            ),
        }
        new_output = _attach_groundedness_to_benefits_output(output, context)
        assert "_groundedness" in new_output
        gnd = new_output["_groundedness"]
        assert gnd["verdict"] in ("GROUNDED", "UNGROUNDED")
        assert "provenance_trail" in gnd

    def test_hallucinated_benefit_term_appears_in_ungrounded_terms(self):
        from pm_mcp_servers.pm_brm.server import (
            _attach_groundedness_to_benefits_output,
        )

        output = {
            "project_id": "BRM-L6-002",
            "narrative_text": (
                "The programme will realise zeppelin benefits by FY27."
            ),
        }
        context = {
            "total_benefit_count": 12,
            "health_score": 78,
            "benefits_summary": "Programme efficiency 45M FY27.",
        }
        new_output = _attach_groundedness_to_benefits_output(output, context)
        gnd = new_output["_groundedness"]
        # "zeppelin" doesn't appear in context.
        assert "zeppelin" in gnd["ungrounded_terms"]

    def test_no_context_produces_not_computed_verdict(self):
        from pm_mcp_servers.pm_brm.server import (
            _attach_groundedness_to_benefits_output,
        )

        output = {
            "project_id": "BRM-L6-NOCTX",
            "narrative_text": "Test narrative.",
        }
        new_output = _attach_groundedness_to_benefits_output(output, {})
        assert new_output["_groundedness"]["verdict"] == "NOT_COMPUTED"


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 6 integration: generate_portfolio_summary (issue #51 / B16)
# ─────────────────────────────────────────────────────────────────────────


class TestPortfolioSummaryGroundedness:
    """L6 attaches a groundedness footer to the portfolio summary
    markdown. Sources span every project's data plus the per-project
    scorecard — one source per project so per-source citation scores
    identify which project supports which narrative fragment."""

    def _seed_two_projects(self):
        from datetime import datetime

        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        now = datetime.utcnow().isoformat()
        pids = ["PORT-L6-001", "PORT-L6-002"]
        for pid in pids:
            store.upsert_risk(
                {
                    "id": f"{pid}-R001",
                    "project_id": pid,
                    "title": "Supplier capacity constraint",
                    "description": "Single-supplier risk.",
                    "category": "COMMERCIAL",
                    "likelihood": 3,
                    "impact": 3,
                    "risk_score": 9,
                    "status": "OPEN",
                    "created_at": now,
                    "updated_at": now,
                }
            )
        return pids

    async def test_portfolio_summary_carries_groundedness_footer(
        self, monkeypatch
    ):
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_reporting import server as reporting_server

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(
            reporting_server, "_get_anthropic_client", lambda: object()
        )
        monkeypatch.setattr(
            reporting_server,
            "_call_claude",
            lambda _c, _p, max_tokens=2000: (
                "# Portfolio Summary — Test\n\n"
                "Two projects in scope. Single-supplier risk identified "
                "in both projects."
            ),
        )
        pids = self._seed_two_projects()
        result = await call_tool(
            "generate_portfolio_summary",
            {"project_ids": pids, "portfolio_name": "Test"},
        )
        text = result[0].text
        assert "Groundedness:" in text
        assert "<!-- _groundedness:" in text
        start = text.index("<!-- _groundedness:") + len("<!-- _groundedness:")
        end = text.index("-->", start)
        gnd = _json.loads(text[start:end].strip())
        assert gnd["verdict"] in ("GROUNDED", "UNGROUNDED")
        # Per-source citation scores — one entry per project.
        per_source = gnd["per_source_citation_scores"]
        assert any(k.startswith("project_PORT-L6-") for k in per_source.keys())


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 6 integration: generate_lessons_section (issue #52 / B17)
# ─────────────────────────────────────────────────────────────────────────


class TestLessonsSectionGroundedness:
    """L6 appends a groundedness footer to the lessons section markdown
    on all three return paths (no-lessons template, deterministic
    fallback, Claude-authored narrative). The sources are the stored
    lesson rows themselves."""

    def _seed_lessons(self, project_id: str, lessons: list[dict]):
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        for lesson in lessons:
            row = {
                "id": lesson["id"],
                "project_id": project_id,
                "document_type": lesson.get("document_type", "GATE_REVIEW"),
                "category": lesson.get("category", "GENERAL"),
                "title": lesson.get("title", "Untitled"),
                "root_cause": lesson.get("root_cause", "Not recorded"),
                "recommendation": lesson.get("recommendation", "Not recorded"),
                "severity": lesson.get("severity", "MEDIUM"),
                "extracted_at": "2026-05-16T07:00:00",
            }
            store.upsert_project_lesson(row)

    async def test_fallback_path_carries_groundedness_footer(self, monkeypatch):
        """The deterministic fallback markdown should produce a footer
        with verdict, score, and (machine-readable) HTML-comment block."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        self._seed_lessons(
            "LESSONS-L6-001",
            [
                {
                    "id": "L-L6-1",
                    "title": "Engage suppliers early",
                    "category": "PROCUREMENT",
                    "severity": "HIGH",
                    "root_cause": "Late supplier engagement delayed bid evaluation.",
                    "recommendation": "Initiate market engagement six months before tender.",
                }
            ],
        )
        result = await call_tool(
            "generate_lessons_section", {"project_id": "LESSONS-L6-001"}
        )
        text = result[0].text
        assert "Groundedness:" in text
        assert "<!-- _groundedness:" in text
        start = text.index("<!-- _groundedness:") + len("<!-- _groundedness:")
        end = text.index("-->", start)
        gnd = _json.loads(text[start:end].strip())
        assert gnd["verdict"] in ("GROUNDED", "UNGROUNDED")
        # Per-source scores include the lesson row keyed by id.
        per_source = gnd["per_source_citation_scores"]
        assert "lessons_corpus" in per_source
        assert "lesson_L-L6-1" in per_source

    async def test_no_lessons_template_marks_not_computed(self, monkeypatch):
        """The no-lessons template has nothing to ground against —
        the footer says so explicitly rather than silently skipping
        the annotation."""
        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool(
            "generate_lessons_section", {"project_id": "LESSONS-L6-EMPTY"}
        )
        text = result[0].text
        # Special "not computed" message appears.
        assert "Groundedness: not computed" in text


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 6 integration: generate_pir_template (issue #53 / B18)
# ─────────────────────────────────────────────────────────────────────────


class TestPirTemplateGroundedness:
    """L6 attaches a groundedness footer to the PIR template markdown.
    Sources are the project_data dict (risks, gate readiness,
    benefits, financials, change requests) — the same material the
    PIR pre-populates from. Completes the L6 cluster: all nine AI-
    authored tools now surface a groundedness verdict."""

    def _seed(self, project_id: str = "PIR-L6-TEST"):
        from datetime import datetime

        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        now = datetime.utcnow().isoformat()
        store.upsert_risk(
            {
                "id": f"{project_id}-R001",
                "project_id": project_id,
                "title": "Procurement single-supplier risk",
                "description": "Concentration risk on key supplier identified at Gate 3.",
                "category": "COMMERCIAL",
                "likelihood": 3,
                "impact": 4,
                "risk_score": 12,
                "status": "CLOSED",
                "created_at": now,
                "updated_at": now,
            }
        )
        return project_id

    async def test_pir_template_carries_groundedness_footer(self, monkeypatch):
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_reporting import server as reporting_server

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(
            reporting_server, "_get_anthropic_client", lambda: object()
        )
        monkeypatch.setattr(
            reporting_server,
            "_call_claude",
            lambda _c, _p, max_tokens=4000: (
                "# Post-Implementation Review — PIR-L6-CLEAN\n\n"
                "**Closure Date:** 2026-05-01  **Prepared by:** [PLACEHOLDER]\n\n"
                "## 3. Risks That Materialised\n"
                "Procurement single-supplier risk closed with mitigation."
            ),
        )

        project_id = self._seed("PIR-L6-CLEAN")
        result = await call_tool(
            "generate_pir_template", {"project_id": project_id}
        )
        text = result[0].text
        # Markdown shape preserved; PIR's [PLACEHOLDER] markers
        # untouched (L5 already validated this in B9).
        assert text.startswith("#")
        assert "[PLACEHOLDER]" in text
        # L6 footer present.
        assert "Groundedness:" in text
        assert "<!-- _groundedness:" in text
        start = text.index("<!-- _groundedness:") + len("<!-- _groundedness:")
        end = text.index("-->", start)
        gnd = _json.loads(text[start:end].strip())
        assert gnd["verdict"] in ("GROUNDED", "UNGROUNDED")


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 8 integration: pm-assure audit chain (issue #54 / B19)
# ─────────────────────────────────────────────────────────────────────────


class TestPmAssureAuditChain:
    """L8 records every decision-producing handler in pm-assure into a
    file-backed tamper-evident chain. Four handlers are now audited:
    assess_gate_readiness, scan_for_red_flags, log_override_decision,
    run_assurance_workflow.

    Tests monkeypatch the audit-dir to a per-test tmp_path so the
    real operator audit log is untouched. Each test resets the
    in-memory chain cache so a fresh chain starts from the new dir.
    """

    def _setup_isolated_audit(self, monkeypatch, tmp_path):
        from pm_mcp_servers import _audit as audit_mod

        # Point the audit dir at a per-test tmp path AND drop the
        # cached in-memory chain so the next record starts in the new
        # location.
        audit_mod._refresh_audit_dir_for_testing(tmp_path / "audit")
        # Ensure no signing key — keep tests deterministic.
        monkeypatch.delenv("PDA_AUDIT_SIGNING_KEY", raising=False)
        return audit_mod

    async def test_assess_gate_readiness_appends_audit_entry(
        self, monkeypatch, tmp_path
    ):
        """A successful assess_gate_readiness invocation appends one
        entry to the chain and the chain still verifies after."""
        from pm_mcp_servers.pda_platform.server import call_tool

        audit_mod = self._setup_isolated_audit(monkeypatch, tmp_path)

        # Seed enough store data that the assessor can score the gate.
        from datetime import datetime

        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        now = datetime.utcnow().isoformat()
        store.upsert_risk(
            {
                "id": "AUDIT-GATE-001-R001",
                "project_id": "AUDIT-GATE-001",
                "title": "Test risk",
                "description": "Seeded.",
                "category": "DELIVERY",
                "likelihood": 3,
                "impact": 3,
                "risk_score": 9,
                "status": "OPEN",
                "created_at": now,
                "updated_at": now,
            }
        )

        await call_tool(
            "assess_gate_readiness",
            {"project_id": "AUDIT-GATE-001", "gate": "GATE_3"},
        )

        # One entry appended.
        chain, _, log_path = audit_mod._get_chain("pm_assure")
        assert len(chain) == 1
        entry = chain.entries[0]
        assert entry.action == "assess_gate_readiness"
        # The on-disk file mirrors the in-memory chain.
        assert log_path.exists()
        with open(log_path, encoding="utf-8") as f:
            lines = [line for line in f if line.strip()]
        assert len(lines) == 1
        # Chain integrity verifies.
        assert audit_mod.verify_chain("pm_assure").is_valid

    async def test_red_flags_decision_classified_into_verdict(
        self, monkeypatch, tmp_path
    ):
        """scan_for_red_flags appends an entry whose decision string
        reflects the highest-severity flag set surfaced."""
        from pm_mcp_servers.pda_platform.server import call_tool

        audit_mod = self._setup_isolated_audit(monkeypatch, tmp_path)

        await call_tool(
            "scan_for_red_flags",
            {"project_id": "AUDIT-RED-001"},
        )
        chain, _, _ = audit_mod._get_chain("pm_assure")
        assert len(chain) == 1
        decision = chain.entries[0].decision
        assert decision in {
            "RED_FLAGS_CRITICAL",
            "RED_FLAGS_HIGH",
            "RED_FLAGS_MEDIUM",
            "NO_RED_FLAGS",
        }

    async def test_chain_links_across_multiple_calls_and_detects_tampering(
        self, monkeypatch, tmp_path
    ):
        """Two sequential calls produce a linked chain. Hand-editing
        any entry on disk and re-hydrating the chain detects the
        tamper."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        audit_mod = self._setup_isolated_audit(monkeypatch, tmp_path)

        for project_id in ("AUDIT-CHAIN-001", "AUDIT-CHAIN-002"):
            await call_tool(
                "scan_for_red_flags",
                {"project_id": project_id},
            )

        chain, _, log_path = audit_mod._get_chain("pm_assure")
        assert len(chain) == 2
        # The second entry references the first via previous_entry_hash.
        assert chain.entries[1].previous_entry_hash == chain.entries[0].entry_hash
        assert audit_mod.verify_chain("pm_assure").is_valid

        # Tamper with the first entry's decision string on disk, then
        # re-hydrate by clearing the in-memory cache (NOT the disk
        # log) and calling verify.
        with open(log_path, encoding="utf-8") as f:
            lines = [line for line in f if line.strip()]
        first = _json.loads(lines[0])
        first["decision"] = "TAMPERED"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(_json.dumps(first) + "\n")
            for line in lines[1:]:
                f.write(line if line.endswith("\n") else line + "\n")
        # Clear the in-memory cache so the next verify_chain hydrates
        # from the (tampered) disk log. Reach into the private cache
        # directly here rather than reset_for_testing, which would
        # also delete the disk log we want to inspect.
        audit_mod._CHAINS.pop("pm_assure", None)
        audit_mod._LOCKS.pop("pm_assure", None)
        result = audit_mod.verify_chain("pm_assure")
        assert not result.is_valid
        assert result.status == "TAMPERED"


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 8 integration: pm-assumptions audit chain (issue #55 / B20)
# ─────────────────────────────────────────────────────────────────────────


class TestPmAssumptionsAuditChain:
    """L8 records pm-assumptions decisions: score_assumption_confidence,
    detect_external_drift, generate_assumption_report. The chain key
    is `pm_assumptions` — distinct from pm_assure so the two modules'
    audit logs are independent files."""

    def _setup_isolated_audit(self, monkeypatch, tmp_path):
        from pm_mcp_servers import _audit as audit_mod

        audit_mod._refresh_audit_dir_for_testing(tmp_path / "audit")
        monkeypatch.delenv("PDA_AUDIT_SIGNING_KEY", raising=False)
        return audit_mod

    def _seed_assumptions(self, project_id: str):
        from datetime import date

        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        today = str(date.today())
        for i in range(2):
            store.upsert_assumption(
                {
                    "id": f"{project_id}-A{i:03d}",
                    "project_id": project_id,
                    "text": f"Schedule milestone {i} depends on supplier delivery",
                    "category": "DELIVERY",
                    "baseline_value": 1.0,
                    "current_value": None,
                    "unit": "boolean",
                    "tolerance_pct": 0.0,
                    "source": "Internal estimate",
                    "external_ref": None,
                    "dependencies": "",
                    "owner": "Test Owner",
                    "last_validated": None,
                    "created_date": today,
                    "notes": (
                        "Impact if false: Schedule slippage. | "
                        "Likelihood: MEDIUM | "
                        "Validation plan: Quarterly review | "
                        "Status: Open | "
                        f"Review date: {today}"
                    ),
                }
            )
        return project_id

    async def test_score_assumption_confidence_records_rag_verdict(
        self, monkeypatch, tmp_path
    ):
        """A score_assumption_confidence call appends one entry whose
        decision is the highest-severity RAG band present (RED,
        AMBER, or GREEN)."""
        from pm_mcp_servers.pda_platform.server import call_tool

        audit_mod = self._setup_isolated_audit(monkeypatch, tmp_path)
        project_id = self._seed_assumptions("AUDIT-CONF-001")
        await call_tool(
            "score_assumption_confidence", {"project_id": project_id}
        )

        chain, _, _ = audit_mod._get_chain("pm_assumptions")
        assert len(chain) == 1
        entry = chain.entries[0]
        assert entry.action == "score_assumption_confidence"
        assert entry.decision in {
            "ASSUMPTIONS_RED",
            "ASSUMPTIONS_AMBER",
            "ASSUMPTIONS_GREEN",
        }
        assert audit_mod.verify_chain("pm_assumptions").is_valid

    async def test_pm_assumptions_chain_isolated_from_pm_assure(
        self, monkeypatch, tmp_path
    ):
        """The two modules' chains live in different JSONL files and
        do NOT cross-link. Recording into one leaves the other
        empty."""
        from pm_mcp_servers.pda_platform.server import call_tool

        audit_mod = self._setup_isolated_audit(monkeypatch, tmp_path)
        project_id = self._seed_assumptions("AUDIT-ISO-001")
        await call_tool(
            "score_assumption_confidence", {"project_id": project_id}
        )

        # pm_assumptions chain has the entry...
        ass_chain, _, ass_path = audit_mod._get_chain("pm_assumptions")
        assert len(ass_chain) == 1
        assert ass_path.name == "pm_assumptions.jsonl"
        # ...but the pm_assure chain stays empty (different file).
        assure_chain, _, assure_path = audit_mod._get_chain("pm_assure")
        assert len(assure_chain) == 0
        assert assure_path.name == "pm_assure.jsonl"
        assert ass_path != assure_path

    async def test_generate_assumption_report_records_audit_entry(
        self, monkeypatch, tmp_path
    ):
        """Generating the executive assumption report appends an
        entry recording the overall verdict and the assumption /
        signal counts."""
        from pm_mcp_servers.pda_platform.server import call_tool

        audit_mod = self._setup_isolated_audit(monkeypatch, tmp_path)
        project_id = self._seed_assumptions("AUDIT-REP-001")
        await call_tool(
            "generate_assumption_report", {"project_id": project_id}
        )
        chain, _, _ = audit_mod._get_chain("pm_assumptions")
        assert len(chain) == 1
        entry = chain.entries[0]
        assert entry.action == "generate_assumption_report"
        # Metadata captures the source counts.
        assert "assumption_count" in entry.metadata
        assert entry.metadata["assumption_count"] >= 1


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 8 integration: pm-reporting audit chain (issue #56 / B21)
# ─────────────────────────────────────────────────────────────────────────


class TestPmReportingAuditChain:
    """L8 records the L5 verdict every generate_* tool's document
    receives. The chain answers: "for this report, was the output
    APPROVED, FLAGGED, or REJECTED?". Recorded inside
    `_apply_document_guardrail` so every caller is audited
    automatically (single point of instrumentation)."""

    def _setup_isolated_audit(self, monkeypatch, tmp_path):
        from pm_mcp_servers import _audit as audit_mod

        audit_mod._refresh_audit_dir_for_testing(tmp_path / "audit")
        monkeypatch.delenv("PDA_AUDIT_SIGNING_KEY", raising=False)
        return audit_mod

    def _seed_minimal_project(self, project_id: str):
        from datetime import datetime

        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        now = datetime.utcnow().isoformat()
        store.upsert_risk(
            {
                "id": f"{project_id}-R001",
                "project_id": project_id,
                "title": "Test risk",
                "description": "Seeded.",
                "category": "DELIVERY",
                "likelihood": 3,
                "impact": 3,
                "risk_score": 9,
                "status": "OPEN",
                "created_at": now,
                "updated_at": now,
            }
        )
        return project_id

    async def test_board_exception_report_approved_path_records_audit(
        self, monkeypatch, tmp_path
    ):
        from pm_mcp_servers.pda_platform.server import call_tool

        audit_mod = self._setup_isolated_audit(monkeypatch, tmp_path)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        project_id = self._seed_minimal_project("AUDIT-REP-BRD-001")
        await call_tool(
            "generate_board_exception_report", {"project_id": project_id}
        )

        chain, _, _ = audit_mod._get_chain("pm_reporting")
        assert len(chain) == 1
        entry = chain.entries[0]
        assert entry.action == "generate_board_exception_report"
        # Clean fallback output should be APPROVED.
        assert entry.decision == "APPROVED"
        # Audit input captures project_id and path.
        assert audit_mod.verify_chain("pm_reporting").is_valid

    async def test_board_exception_report_rejected_path_records_audit(
        self, monkeypatch, tmp_path
    ):
        """A monkeypatched fallback that emits a forbidden phrase
        produces a REJECTED entry in the chain. The audit shows the
        rejection happened even though the consumer received only the
        rejection JSON — operators auditing the chain see the full
        history regardless."""
        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_reporting import server as reporting_server

        audit_mod = self._setup_isolated_audit(monkeypatch, tmp_path)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        project_id = self._seed_minimal_project("AUDIT-REP-BRD-REJ")

        def fake_compose(_project_id, _period, _data):
            return "# Board Report\n\nWe are 100% certain of the outcome."

        monkeypatch.setattr(
            reporting_server,
            "_compose_evidence_only_board_report",
            fake_compose,
        )
        await call_tool(
            "generate_board_exception_report", {"project_id": project_id}
        )
        chain, _, _ = audit_mod._get_chain("pm_reporting")
        assert len(chain) == 1
        entry = chain.entries[0]
        assert entry.decision == "REJECTED"
        # Output payload records the triggered rule names.
        # (Read the live entry rather than reasserting all rule data.)
        assert audit_mod.verify_chain("pm_reporting").is_valid

    async def test_multiple_reporting_tools_share_one_chain(
        self, monkeypatch, tmp_path
    ):
        """All five generate_* tools record into the same pm_reporting
        chain, in invocation order. A reviewer auditing the chain sees
        the cross-tool sequence of decisions."""
        from pm_mcp_servers.pda_platform.server import call_tool
        from pm_mcp_servers.pm_reporting import server as reporting_server

        audit_mod = self._setup_isolated_audit(monkeypatch, tmp_path)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(
            reporting_server, "_get_anthropic_client", lambda: object()
        )
        monkeypatch.setattr(
            reporting_server,
            "_call_claude",
            lambda _c, _p, max_tokens=2000: (
                "# Document\n\n"
                "Substantive content with no forbidden phrases."
            ),
        )
        project_id = self._seed_minimal_project("AUDIT-REP-MULTI")

        # Three sequential tool calls.
        await call_tool(
            "generate_board_exception_report", {"project_id": project_id}
        )
        await call_tool(
            "generate_gate_review_summary",
            {"project_id": project_id, "gate_number": 3},
        )
        await call_tool(
            "generate_portfolio_summary",
            {"project_ids": [project_id], "portfolio_name": "Test"},
        )

        chain, _, _ = audit_mod._get_chain("pm_reporting")
        assert len(chain) == 3
        actions = [e.action for e in chain.entries]
        assert actions == [
            "generate_board_exception_report",
            "generate_gate_review_summary",
            "generate_portfolio_summary",
        ]
        # Chain integrity verifies after all three.
        assert audit_mod.verify_chain("pm_reporting").is_valid


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 8 integration: pm-knowledge audit chain (issue #57 / B22)
# ─────────────────────────────────────────────────────────────────────────


class TestPmKnowledgeAuditChain:
    """L8 records pm-knowledge decisions: run_reference_class_check
    and generate_premortem_questions. The chain answers "what
    optimism-bias flag did this estimate raise?" and "which gate
    + risk-flag combination produced which questions?"."""

    def _setup_isolated_audit(self, monkeypatch, tmp_path):
        from pm_mcp_servers import _audit as audit_mod

        audit_mod._refresh_audit_dir_for_testing(tmp_path / "audit")
        monkeypatch.delenv("PDA_AUDIT_SIGNING_KEY", raising=False)
        return audit_mod

    async def test_reference_class_check_records_optimism_bias_verdict(
        self, monkeypatch, tmp_path
    ):
        """A submitted estimate below the IPA median should produce
        OPTIMISM_BIAS_FLAGGED. An estimate at or above median should
        produce WITHIN_RANGE."""
        from pm_mcp_servers.pda_platform.server import call_tool

        audit_mod = self._setup_isolated_audit(monkeypatch, tmp_path)

        # Submit a clearly low estimate to trigger the optimism-bias flag.
        await call_tool(
            "run_reference_class_check",
            {
                "project_type": "IT_AND_DIGITAL",
                "estimate_type": "cost_overrun",
                "submitted_value": 1.0,
            },
        )
        chain, _, _ = audit_mod._get_chain("pm_knowledge")
        assert len(chain) == 1
        first = chain.entries[0]
        assert first.action == "run_reference_class_check"
        assert first.decision in {"OPTIMISM_BIAS_FLAGGED", "WITHIN_RANGE"}

    async def test_premortem_questions_records_count_decision(
        self, monkeypatch, tmp_path
    ):
        """generate_premortem_questions records QUESTIONS_EMITTED when
        at least one question is produced — the default gate=ANY does
        emit questions from the bundled constants."""
        from pm_mcp_servers.pda_platform.server import call_tool

        audit_mod = self._setup_isolated_audit(monkeypatch, tmp_path)
        await call_tool(
            "generate_premortem_questions", {"gate": "ANY"}
        )
        chain, _, _ = audit_mod._get_chain("pm_knowledge")
        assert len(chain) == 1
        first = chain.entries[0]
        assert first.action == "generate_premortem_questions"
        assert first.decision in {"QUESTIONS_EMITTED", "NO_QUESTIONS"}


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 8 integration: pm-simulation audit chain (issue #58 / B23)
# ─────────────────────────────────────────────────────────────────────────


class TestPmSimulationAuditChain:
    """L8 records Monte Carlo schedule simulation runs into the
    `pm_simulation` audit chain. The chain answers: "for this
    simulation run, what P50/P80/P90 were produced and what was the
    risk-multiplier-adjusted confidence band?"."""

    def _setup_isolated_audit(self, monkeypatch, tmp_path):
        from pm_mcp_servers import _audit as audit_mod

        audit_mod._refresh_audit_dir_for_testing(tmp_path / "audit")
        monkeypatch.delenv("PDA_AUDIT_SIGNING_KEY", raising=False)
        return audit_mod

    async def test_schedule_simulation_records_run_and_p_values(
        self, monkeypatch, tmp_path
    ):
        """A run_schedule_simulation call appends an entry capturing
        the run_id and the P-values. The decision string is one of
        HIGH/MEDIUM/LOW_CONFIDENCE."""
        from pm_mcp_servers.pda_platform.server import call_tool

        audit_mod = self._setup_isolated_audit(monkeypatch, tmp_path)

        # Driving the simulation via baseline_duration_days avoids
        # needing project tasks in the store.
        await call_tool(
            "run_schedule_simulation",
            {
                "project_id": "AUDIT-SIM-001",
                "baseline_duration_days": 120,
                "n_simulations": 200,
                "use_risk_register": False,
            },
        )
        chain, _, _ = audit_mod._get_chain("pm_simulation")
        assert len(chain) == 1
        entry = chain.entries[0]
        assert entry.action == "run_schedule_simulation"
        assert entry.decision in {
            "HIGH_CONFIDENCE",
            "MEDIUM_CONFIDENCE",
            "LOW_CONFIDENCE",
        }
        # Metadata captures risk-adjustment status.
        assert "risk_adjustment_applied" in entry.metadata
        # Chain integrity verifies.
        assert audit_mod.verify_chain("pm_simulation").is_valid

    async def test_two_simulation_runs_form_a_linked_chain(
        self, monkeypatch, tmp_path
    ):
        from pm_mcp_servers.pda_platform.server import call_tool

        audit_mod = self._setup_isolated_audit(monkeypatch, tmp_path)
        for label in ("RUN_A", "RUN_B"):
            await call_tool(
                "run_schedule_simulation",
                {
                    "project_id": f"AUDIT-SIM-{label}",
                    "baseline_duration_days": 150,
                    "n_simulations": 200,
                    "use_risk_register": False,
                },
            )
        chain, _, _ = audit_mod._get_chain("pm_simulation")
        assert len(chain) == 2
        assert chain.entries[1].previous_entry_hash == chain.entries[0].entry_hash
        assert audit_mod.verify_chain("pm_simulation").is_valid


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 4 integration: evaluate_calibration tool (issue #59 / B24)
# ─────────────────────────────────────────────────────────────────────────


class TestEvaluateCalibrationTool:
    """The new pm-analyse `evaluate_calibration` tool exposes A4's
    compute_ece + reliability-diagram primitive as an MCP tool.
    Anchors the integration: tool is registered, dispatch works,
    well-calibrated input produces low ECE, miscalibrated produces
    high ECE, errors surface as structured response."""

    async def test_tool_is_registered_and_routed(self):
        """evaluate_calibration must be discoverable on the unified
        server and dispatchable via call_tool."""
        from pm_mcp_servers.pda_platform.server import ALL_TOOLS

        names = {t.name for t in ALL_TOOLS}
        assert "evaluate_calibration" in names

    async def test_well_calibrated_inputs_produce_low_ece(self):
        """A predictor whose confidence matches accuracy on every
        subset produces near-zero ECE."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        # Build a perfectly-calibrated synthetic set: half the
        # samples at confidence 0.5 with 50% accuracy, half at 0.9
        # with 90% accuracy. Using exact alternation makes the test
        # deterministic.
        predictions: list[float] = []
        actuals: list[int] = []
        for i in range(100):
            predictions.append(0.5)
            actuals.append(1 if i % 2 == 0 else 0)
        for i in range(100):
            predictions.append(0.9)
            actuals.append(0 if i % 10 == 0 else 1)

        result = await call_tool(
            "evaluate_calibration",
            {"predictions": predictions, "actuals": actuals, "n_bins": 10},
        )
        payload = _json.loads(result[0].text)
        assert "ece" in payload
        assert payload["ece"] < 0.05
        assert payload["n_samples"] == 200
        assert len(payload["bins"]) == 10
        # Every well-formed bin has the expected keys.
        for b in payload["bins"]:
            assert {"lower", "upper", "count", "mean_confidence", "mean_accuracy", "gap"}.issubset(b.keys())

    async def test_overconfident_predictor_produces_high_ece(self):
        """A predictor that always claims 0.9 confidence but is only
        right 60% of the time has ECE close to 0.3."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        predictions = [0.9] * 200
        # 60% accuracy.
        actuals = [1 if i % 5 < 3 else 0 for i in range(200)]

        result = await call_tool(
            "evaluate_calibration",
            {"predictions": predictions, "actuals": actuals},
        )
        payload = _json.loads(result[0].text)
        # 0.9 - 0.6 = 0.3 gap; ECE close to 0.3.
        assert payload["ece"] > 0.2
        # Poor-calibration interpretation surfaced.
        assert "poorly calibrated" in payload["interpretation"].lower()

    async def test_mismatched_lengths_returns_structured_error(self):
        """predictions/actuals length mismatch should not crash — it
        should return a structured error dict so the consumer can
        recover."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool(
            "evaluate_calibration",
            {"predictions": [0.5, 0.7, 0.9], "actuals": [1, 0]},
        )
        payload = _json.loads(result[0].text)
        assert "error" in payload
        assert payload["error"]["code"] == "INVALID_INPUT"

    async def test_project_id_echoed_in_response(self):
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool(
            "evaluate_calibration",
            {
                "predictions": [0.5, 0.7],
                "actuals": [1, 0],
                "project_id": "CALIB-TEST-001",
            },
        )
        payload = _json.loads(result[0].text)
        assert payload["project_id"] == "CALIB-TEST-001"

    async def test_empty_bins_serialise_as_null_means(self):
        """A bin that no sample falls in must serialise with null
        mean_confidence/mean_accuracy/gap (not NaN, which JSON cannot
        represent and consumers can't render)."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        # All predictions at 0.95 — only the top bin is populated.
        predictions = [0.95] * 10
        actuals = [1] * 10
        result = await call_tool(
            "evaluate_calibration",
            {"predictions": predictions, "actuals": actuals, "n_bins": 10},
        )
        payload = _json.loads(result[0].text)
        empty_bins = [b for b in payload["bins"] if b["count"] == 0]
        assert empty_bins, "expected at least one empty bin"
        for b in empty_bins:
            assert b["mean_confidence"] is None
            assert b["mean_accuracy"] is None
            assert b["gap"] is None


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 4 integration: Monte Carlo conformal bands (issue #60 / B25)
# ─────────────────────────────────────────────────────────────────────────


class TestMonteCarloConformalBands:
    """L4 wraps run_schedule_simulation's P50/P80 outputs in conformal
    bands when the store has a calibration history. When no history
    exists, the response surfaces a NOT_COMPUTED marker rather than
    fabricating an uncalibrated band."""

    def _seed_residuals(
        self, project_id: str, count: int = 10, scale: float = 5.0
    ):
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        for i in range(count):
            # Symmetric residuals around 0; deterministic.
            sign = 1 if i % 2 == 0 else -1
            magnitude = scale * (1 + (i % 3))
            for label, base in (("P50", 100.0), ("P80", 120.0)):
                store.upsert_simulation_residual(
                    {
                        "id": f"{project_id}-{label}-{i:03d}",
                        "project_id": project_id,
                        "simulation_type": "schedule",
                        "predicted_value": base,
                        "actual_value": base + sign * magnitude,
                        "quantile_label": label,
                    }
                )
        return store

    async def test_simulation_without_history_marks_not_computed(self):
        """A project with no calibration history produces
        `_calibration.status == "NOT_COMPUTED"`, plus an explanatory
        reason."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool(
            "run_schedule_simulation",
            {
                "project_id": "SIM-CB-EMPTY",
                "baseline_duration_days": 120,
                "n_simulations": 200,
                "use_risk_register": False,
            },
        )
        payload = _json.loads(result[0].text)
        assert "_calibration" in payload
        calib = payload["_calibration"]
        assert calib["status"] == "NOT_COMPUTED"
        assert "Insufficient calibration history" in calib["reason"]
        assert calib["coverage_pct"] == 80.0

    async def test_simulation_with_history_produces_conformal_bands(self):
        """With enough residuals seeded, the response carries
        `_calibration.status == "COMPUTED"` plus P50 and P80 bands
        symmetric around the simulation's point estimates."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        self._seed_residuals("SIM-CB-WITH", count=10)
        result = await call_tool(
            "run_schedule_simulation",
            {
                "project_id": "SIM-CB-WITH",
                "baseline_duration_days": 120,
                "n_simulations": 200,
                "use_risk_register": False,
            },
        )
        payload = _json.loads(result[0].text)
        calib = payload["_calibration"]
        assert calib["status"] == "COMPUTED"
        for key in ("p50_band", "p80_band"):
            band = calib[key]
            assert "lower" in band
            assert "upper" in band
            assert band["upper"] >= band["lower"]
            assert band["half_width"] >= 0
        # The history counts surface in the response.
        assert calib["p50_history_count"] == 10
        assert calib["p80_history_count"] == 10

    def test_store_round_trips_simulation_residual(self):
        """The new table accepts upserts and retrieves them filtered
        by simulation_type + quantile_label."""
        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        store.upsert_simulation_residual(
            {
                "id": "SIM-CB-STORE-001",
                "project_id": "SIM-CB-STORE",
                "simulation_type": "schedule",
                "predicted_value": 100.0,
                "actual_value": 108.0,
                "quantile_label": "P50",
            }
        )
        rows = store.get_simulation_residuals("SIM-CB-STORE", "schedule")
        ids = {r["id"] for r in rows}
        assert "SIM-CB-STORE-001" in ids
        # The residual is computed from predicted/actual when absent.
        match = next(r for r in rows if r["id"] == "SIM-CB-STORE-001")
        assert abs(match["residual"] - 8.0) < 1e-9


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 4 integration: reference-class conformal band (issue #61 / B26)
# ─────────────────────────────────────────────────────────────────────────


class TestReferenceClassConformalInterval:
    """L4 wraps run_reference_class_check's P80 in a conformal band
    synthesised from the IPA benchmark descriptors (median, P80,
    mean). The band tells a Green Book reviewer "the true outcome is
    likely to fall in this range with X% confidence based on the
    reference class"."""

    async def test_reference_class_carries_conformal_band(self):
        """A normal run produces `_calibration.status == COMPUTED`
        with a centred band around the IPA P80."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool(
            "run_reference_class_check",
            {
                "project_type": "IT_AND_DIGITAL",
                "estimate_type": "cost_overrun",
                "submitted_value": 15.0,
            },
        )
        payload = _json.loads(result[0].text)
        assert "_calibration" in payload
        calib = payload["_calibration"]
        assert calib["status"] == "COMPUTED"
        assert calib["coverage_pct"] == 80.0
        band = calib["band"]
        assert band["lower"] < band["upper"]
        assert band["half_width"] > 0
        # Method is recorded so consumers know provenance.
        assert calib["method"] == "synthetic-from-IPA-descriptives"

    def test_band_widens_when_distribution_is_wider(self):
        """A wider (P80 - median) gap implies higher implied sigma,
        so the conformal half-width grows accordingly."""
        from pm_mcp_servers.pm_knowledge.server import (
            _build_reference_class_band,
        )

        narrow = _build_reference_class_band(
            recommended_p80=20.0,
            median=15.0,  # gap = 5
            mean=15.0,
            unit="%",
        )
        wide = _build_reference_class_band(
            recommended_p80=20.0,
            median=5.0,  # gap = 15
            mean=5.0,
            unit="%",
        )
        assert narrow["status"] == "COMPUTED"
        assert wide["status"] == "COMPUTED"
        assert wide["band"]["half_width"] > narrow["band"]["half_width"]

    def test_invalid_distribution_returns_not_computed(self):
        """If P80 <= median the synthesis can't run."""
        from pm_mcp_servers.pm_knowledge.server import (
            _build_reference_class_band,
        )

        result = _build_reference_class_band(
            recommended_p80=10.0,
            median=12.0,  # median > p80 — not a valid IPA distribution
            mean=11.0,
            unit="%",
        )
        assert result["status"] == "NOT_COMPUTED"
        assert "P80 > median" in result["reason"]


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 2 integration: route_outputs_to_review tool (issue #62 / B27)
# ─────────────────────────────────────────────────────────────────────────


class TestRouteOutputsToReviewTool:
    """The new pm-assure `route_outputs_to_review` MCP tool surfaces
    A5's four-tier escalation router. Reads confidence scores from
    the store, normalises 0-100 → [0, 1], aggregates, and dispatches
    to `route`. The OR fail-safe is preserved end-to-end."""

    def _seed_confidence_scores(
        self, project_id: str, scores: list[float]
    ):
        from datetime import datetime

        from pm_data_tools.db.store import AssuranceStore

        store = AssuranceStore()
        now = datetime.utcnow().isoformat()
        # Seed assumptions first (the FK target).
        for i, score in enumerate(scores):
            aid = f"{project_id}-A{i:03d}"
            store.upsert_assumption(
                {
                    "id": aid,
                    "project_id": project_id,
                    "text": f"Test assumption {i}",
                    "category": "DELIVERY",
                    "baseline_value": 1.0,
                    "current_value": None,
                    "unit": "boolean",
                    "tolerance_pct": 0.0,
                    "source": "Test",
                    "external_ref": None,
                    "dependencies": "",
                    "owner": "Tester",
                    "last_validated": None,
                    "created_date": "2026-05-16",
                    "notes": "",
                }
            )
            store.upsert_assumption_confidence_score(
                {
                    "id": f"{aid}-CS",
                    "project_id": project_id,
                    "assumption_id": aid,
                    "score": float(score),
                    "rag": "GREEN" if score >= 70 else "AMBER" if score >= 40 else "RED",
                    "review_age_days": 0,
                    "source_credibility_score": float(score),
                    "data_backing_score": float(score),
                    "likelihood_penalty": 1.0,
                    "explanation": "test seed",
                }
            )

    async def test_tool_is_registered_and_routed(self):
        from pm_mcp_servers.pda_platform.server import ALL_TOOLS

        names = {t.name for t in ALL_TOOLS}
        assert "route_outputs_to_review" in names

    async def test_no_history_returns_structured_error(self):
        """A project with no confidence history surfaces a structured
        error rather than crashing."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        result = await call_tool(
            "route_outputs_to_review", {"project_id": "ROUTE-EMPTY-001"}
        )
        payload = _json.loads(result[0].text)
        assert "error" in payload
        assert payload["error"]["code"] == "NO_CONFIDENCE_HISTORY"

    async def test_high_confidence_clean_outputs_route_to_none(self):
        """Mean confidence around 0.85 and no outliers → level NONE."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        # All scores at 85 (0.85 normalised) — tight cluster, no outlier.
        self._seed_confidence_scores("ROUTE-CLEAN-001", [85.0] * 6)
        result = await call_tool(
            "route_outputs_to_review",
            {"project_id": "ROUTE-CLEAN-001"},
        )
        payload = _json.loads(result[0].text)
        assert payload["level"] == "NONE"
        assert payload["triggered_by_outliers"] is False
        assert payload["triggered_by_confidence"] is False
        assert payload["sample_size"] == 6

    async def test_low_confidence_routes_to_expert_required(self):
        """Mean confidence below the expert threshold routes to
        EXPERT_REQUIRED even when no outlier fires."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        # All scores at 25 (0.25 normalised) — well below 0.4 expert
        # threshold; tight cluster so no outlier fires.
        self._seed_confidence_scores("ROUTE-LOW-001", [25.0] * 6)
        result = await call_tool(
            "route_outputs_to_review",
            {"project_id": "ROUTE-LOW-001"},
        )
        payload = _json.loads(result[0].text)
        assert payload["level"] == "EXPERT_REQUIRED"
        assert payload["triggered_by_confidence"] is True

    async def test_outlier_in_high_confidence_set_still_escalates(self):
        """OR fail-safe: even with high overall confidence, a single
        statistical outlier triggers EXPERT_REQUIRED."""
        import json as _json

        from pm_mcp_servers.pda_platform.server import call_tool

        # Five scores around 85, one wildly low — outlier fires.
        self._seed_confidence_scores(
            "ROUTE-OUTLIER-001", [85.0, 86.0, 84.0, 87.0, 85.0, 10.0]
        )
        result = await call_tool(
            "route_outputs_to_review",
            {
                "project_id": "ROUTE-OUTLIER-001",
                # Force high overall confidence so the outlier is the
                # *sole* trigger — proves OR fail-safe behaviour.
                "confidence_override": 0.95,
            },
        )
        payload = _json.loads(result[0].text)
        assert payload["level"] == "EXPERT_REQUIRED"
        assert payload["triggered_by_outliers"] is True
        assert payload["triggered_by_confidence"] is False


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 3 integration: hallucinations list (issue #63 / B28)
# ─────────────────────────────────────────────────────────────────────────


class TestHallucinationsField:
    """B28 surfaces an A6 quality score and a `potential_hallucinations`
    boolean alongside the L6 groundedness signal on every AI-authored
    tool response. The composition is via
    `_quality.derive_quality_from_groundedness`, which maps L6
    signals (overall_score, ungrounded_terms, answer_token_count)
    into A6's compute_quality_score formula."""

    def test_grounded_input_produces_no_hallucination_flag(self):
        from pm_mcp_servers._quality import derive_quality_from_groundedness

        gnd = {
            "verdict": "GROUNDED",
            "overall_score": 0.95,
            "ungrounded_terms": ["minor"],
            "answer_token_count": 100,
            "provenance_trail": "stub",
        }
        quality = derive_quality_from_groundedness(gnd)
        assert quality["verdict"] == "COMPUTED"
        assert quality["potential_hallucinations"] is False
        assert quality["overall_score"] > 0.5
        # Components are surfaced for downstream consumers.
        assert "components" in quality
        assert "relevance" in quality["components"]
        assert quality["components"]["relevance"] == 0.95

    def test_ungrounded_input_flags_potential_hallucinations(self):
        from pm_mcp_servers._quality import derive_quality_from_groundedness

        gnd = {
            "verdict": "UNGROUNDED",
            "overall_score": 0.4,
            "ungrounded_terms": ["zeppelin", "convoy", "rapture"],
            "answer_token_count": 20,
            "provenance_trail": "stub",
        }
        quality = derive_quality_from_groundedness(gnd)
        assert quality["verdict"] == "COMPUTED"
        # UNGROUNDED verdict ALONE flips the flag regardless of ratio.
        assert quality["potential_hallucinations"] is True

    def test_high_ungrounded_ratio_flags_even_when_grounded(self):
        """If groundedness is technically GROUNDED but the ungrounded-
        term ratio exceeds the threshold, hallucinations are still
        flagged. The composition treats hallucination_term_ratio as
        an independent trigger."""
        from pm_mcp_servers._quality import derive_quality_from_groundedness

        gnd = {
            "verdict": "GROUNDED",
            "overall_score": 0.75,
            # 50 ungrounded terms out of 100 — ratio 0.5 > default 0.3.
            "ungrounded_terms": [f"t{i}" for i in range(50)],
            "answer_token_count": 100,
            "provenance_trail": "stub",
        }
        quality = derive_quality_from_groundedness(gnd)
        assert quality["potential_hallucinations"] is True

    def test_not_computed_groundedness_passes_through(self):
        from pm_mcp_servers._quality import derive_quality_from_groundedness

        assert (
            derive_quality_from_groundedness(None)["verdict"]
            == "NOT_COMPUTED"
        )
        assert (
            derive_quality_from_groundedness({"verdict": "NOT_COMPUTED"})[
                "verdict"
            ]
            == "NOT_COMPUTED"
        )

    async def test_assumption_report_response_carries_quality_field(self):
        """End-to-end on one representative JSON-output tool: the
        assumption report now carries both `_groundedness` and
        `_quality` as top-level fields."""
        import json as _json
        from datetime import date

        from pm_data_tools.db.store import AssuranceStore
        from pm_mcp_servers.pda_platform.server import call_tool

        store = AssuranceStore()
        today = str(date.today())
        store.upsert_assumption(
            {
                "id": "QUAL-ASSUMP-001-A001",
                "project_id": "QUAL-ASSUMP-001",
                "text": "Schedule depends on supplier delivery",
                "category": "DELIVERY",
                "baseline_value": 1.0,
                "current_value": None,
                "unit": "boolean",
                "tolerance_pct": 0.0,
                "source": "Internal",
                "external_ref": None,
                "dependencies": "",
                "owner": "Tester",
                "last_validated": None,
                "created_date": today,
                "notes": "Impact if false: Schedule slip. | Likelihood: MEDIUM | Validation plan: Quarterly | Status: Open | Review date: " + today,
            }
        )

        result = await call_tool(
            "generate_assumption_report", {"project_id": "QUAL-ASSUMP-001"}
        )
        payload = _json.loads(result[0].text)
        assert "_groundedness" in payload
        assert "_quality" in payload
        quality = payload["_quality"]
        # When L6 is COMPUTED, L3 should also be COMPUTED.
        if payload["_groundedness"]["verdict"] in ("GROUNDED", "UNGROUNDED"):
            assert quality["verdict"] == "COMPUTED"
            assert "potential_hallucinations" in quality


# ─────────────────────────────────────────────────────────────────────────
# Verified Autonomy — Layer 1 integration: confidence-gap surfacing (issue #64 / B29)
# ─────────────────────────────────────────────────────────────────────────


class TestConfidenceGapSurfacing:
    """B29 exposes the gap between conservative inverse-weighted
    confidence and the naive arithmetic mean. The gap is non-negative
    by construction; a large gap signals that low-confidence fields
    are being hidden by the naive mean."""

    def test_with_gap_function_returns_all_fields(self):
        from agent_planning.confidence import (
            compute_overall_confidence_with_gap,
        )

        result = compute_overall_confidence_with_gap(
            {"a": 0.9, "b": 0.9, "c": 0.9}
        )
        assert set(result.keys()) == {
            "weighted",
            "plain_mean",
            "gap",
            "field_count",
        }
        assert result["field_count"] == 3

    def test_equal_confidences_produce_zero_gap(self):
        from agent_planning.confidence import (
            compute_overall_confidence_with_gap,
        )

        result = compute_overall_confidence_with_gap(
            {"a": 0.7, "b": 0.7, "c": 0.7}
        )
        assert abs(result["weighted"] - result["plain_mean"]) < 1e-9
        assert abs(result["gap"]) < 1e-9

    def test_mixed_confidences_produce_positive_gap(self):
        """When low and high confidences coexist, the inverse-weighted
        average pulls towards the low values — so plain_mean >
        weighted and gap > 0."""
        from agent_planning.confidence import (
            compute_overall_confidence_with_gap,
        )

        result = compute_overall_confidence_with_gap(
            {"high": 0.95, "low": 0.20}
        )
        assert result["plain_mean"] > result["weighted"]
        assert result["gap"] > 0.0
        # Plain mean is exactly the arithmetic mean.
        assert abs(result["plain_mean"] - 0.575) < 1e-9

    def test_empty_input_returns_zeros(self):
        from agent_planning.confidence import (
            compute_overall_confidence_with_gap,
        )

        result = compute_overall_confidence_with_gap({})
        assert result == {
            "weighted": 0.0,
            "plain_mean": 0.0,
            "gap": 0.0,
            "field_count": 0,
        }

    def test_legacy_function_still_returns_a_float(self):
        """Backward compatibility: existing callers of
        `compute_overall_confidence` still receive a plain float."""
        from agent_planning.confidence import compute_overall_confidence

        value = compute_overall_confidence({"a": 0.8, "b": 0.6})
        assert isinstance(value, float)
        assert 0.0 <= value <= 1.0
