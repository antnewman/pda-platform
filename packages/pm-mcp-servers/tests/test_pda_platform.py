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

        assert len(TOOLS) == 7
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

        assert len(TOOLS) == 28
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
        """Unified server has exactly 124 tools (6+7+4+5+28+12+5+2+2+9+5+5+5+8+2+5+6+8)."""
        from pm_mcp_servers.pda_platform.server import ALL_TOOLS

        assert len(ALL_TOOLS) == 124

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
        "detect_narrative_divergence",
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
        "scan_for_red_flags",
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
