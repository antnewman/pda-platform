"""
Tests for PM-Analyse MCP Server.

Tests server setup, tool registration, and tool calling with 15+ test cases.
"""

import json

import pytest


class TestServerInitialization:
    """Tests for PM-Analyse server initialization."""

    def test_server_creation(self):
        """Test that server can be created."""
        from pm_mcp_servers.pm_analyse.server import server
        assert server is not None
        assert server.name == "pm-analyse"

    def test_server_has_required_methods(self):
        """Test that server has required handler methods."""
        from pm_mcp_servers.pm_analyse.server import server
        assert hasattr(server, "list_tools")
        assert hasattr(server, "call_tool")


class TestToolRegistration:
    """Tests for tool registration with server."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_six_tools(self):
        """Test that server lists all 6 analysis tools."""
        from pm_mcp_servers.pm_analyse.server import list_tools
        tools = await list_tools()
        assert len(tools) == 6

    @pytest.mark.asyncio
    async def test_list_tools_includes_identify_risks(self):
        """Test that identify_risks is registered."""
        from pm_mcp_servers.pm_analyse.server import list_tools
        tools = await list_tools()
        tool_names = [t.name for t in tools]
        assert "identify_risks" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_includes_forecast_completion(self):
        """Test that forecast_completion is registered."""
        from pm_mcp_servers.pm_analyse.server import list_tools
        tools = await list_tools()
        tool_names = [t.name for t in tools]
        assert "forecast_completion" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_includes_detect_outliers(self):
        """Test that detect_outliers is registered."""
        from pm_mcp_servers.pm_analyse.server import list_tools
        tools = await list_tools()
        tool_names = [t.name for t in tools]
        assert "detect_outliers" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_includes_assess_health(self):
        """Test that assess_health is registered."""
        from pm_mcp_servers.pm_analyse.server import list_tools
        tools = await list_tools()
        tool_names = [t.name for t in tools]
        assert "assess_health" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_includes_suggest_mitigations(self):
        """Test that suggest_mitigations is registered."""
        from pm_mcp_servers.pm_analyse.server import list_tools
        tools = await list_tools()
        tool_names = [t.name for t in tools]
        assert "suggest_mitigations" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_includes_compare_baseline(self):
        """Test that compare_baseline is registered."""
        from pm_mcp_servers.pm_analyse.server import list_tools
        tools = await list_tools()
        tool_names = [t.name for t in tools]
        assert "compare_baseline" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_have_descriptions(self):
        """Test that all tools have descriptions."""
        from pm_mcp_servers.pm_analyse.server import list_tools
        tools = await list_tools()
        assert all(t.description for t in tools)

    @pytest.mark.asyncio
    async def test_list_tools_have_input_schemas(self):
        """Test that all tools have input schemas."""
        from pm_mcp_servers.pm_analyse.server import list_tools
        tools = await list_tools()
        assert all(t.inputSchema for t in tools)


class TestToolCalling:
    """Tests for calling tools through server."""

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self):
        """Test error when calling unknown tool."""
        from pm_mcp_servers.pm_analyse.server import call_tool
        result = await call_tool("unknown_tool", {})
        assert len(result) > 0
        content = result[0]
        text = content.text
        data = json.loads(text)
        assert "error" in data
        assert data["error"]["code"] == "UNKNOWN_TOOL"

    @pytest.mark.asyncio
    async def test_call_tool_identify_risks(self):
        """Test calling identify_risks through server."""
        from pm_mcp_servers.pm_analyse.server import call_tool
        result = await call_tool("identify_risks", {"project_id": "nonexistent"})
        assert len(result) > 0
        content = result[0]
        assert content.type == "text"

    @pytest.mark.asyncio
    async def test_call_tool_forecast_completion(self):
        """Test calling forecast_completion through server."""
        from pm_mcp_servers.pm_analyse.server import call_tool
        result = await call_tool("forecast_completion", {"project_id": "nonexistent"})
        assert len(result) > 0
        content = result[0]
        assert content.type == "text"

    @pytest.mark.asyncio
    async def test_call_tool_detect_outliers(self):
        """Test calling detect_outliers through server."""
        from pm_mcp_servers.pm_analyse.server import call_tool
        result = await call_tool("detect_outliers", {"project_id": "nonexistent"})
        assert len(result) > 0
        content = result[0]
        assert content.type == "text"

    @pytest.mark.asyncio
    async def test_call_tool_assess_health(self):
        """Test calling assess_health through server."""
        from pm_mcp_servers.pm_analyse.server import call_tool
        result = await call_tool("assess_health", {"project_id": "nonexistent"})
        assert len(result) > 0
        content = result[0]
        assert content.type == "text"

    @pytest.mark.asyncio
    async def test_call_tool_suggest_mitigations(self):
        """Test calling suggest_mitigations through server."""
        from pm_mcp_servers.pm_analyse.server import call_tool
        result = await call_tool("suggest_mitigations", {"project_id": "nonexistent"})
        assert len(result) > 0
        content = result[0]
        assert content.type == "text"

    @pytest.mark.asyncio
    async def test_call_tool_compare_baseline(self):
        """Test calling compare_baseline through server."""
        from pm_mcp_servers.pm_analyse.server import call_tool
        result = await call_tool("compare_baseline", {"project_id": "nonexistent"})
        assert len(result) > 0
        content = result[0]
        assert content.type == "text"

    @pytest.mark.asyncio
    async def test_call_tool_returns_text_content(self):
        """Test that tool calls return TextContent with JSON."""
        from pm_mcp_servers.pm_analyse.server import call_tool
        result = await call_tool("identify_risks", {"project_id": "nonexistent"})
        assert len(result) == 1
        content = result[0]
        assert content.type == "text"
        # Should be valid JSON
        data = json.loads(content.text)
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_call_tool_with_valid_project(self, basic_project):
        """Test calling tool with valid project."""
        from pm_mcp_servers.pm_analyse.server import call_tool
        from pm_mcp_servers.shared import project_store

        project_store.add("test-project", basic_project)
        result = await call_tool("identify_risks", {"project_id": "test-project"})
        assert len(result) > 0
        content = result[0]
        data = json.loads(content.text)
        assert "metadata" in data


class TestInputSchemaValidation:
    """Tests for tool input schema definitions."""

    @pytest.mark.asyncio
    async def test_identify_risks_schema(self):
        """Test identify_risks input schema."""
        from pm_mcp_servers.pm_analyse.server import list_tools
        tools = await list_tools()
        identify_risks = next(t for t in tools if t.name == "identify_risks")
        schema = identify_risks.inputSchema
        assert "properties" in schema
        assert "project_id" in schema["properties"]
        assert "project_id" in schema["required"]

    @pytest.mark.asyncio
    async def test_forecast_completion_schema(self):
        """Test forecast_completion input schema."""
        from pm_mcp_servers.pm_analyse.server import list_tools
        tools = await list_tools()
        forecast = next(t for t in tools if t.name == "forecast_completion")
        schema = forecast.inputSchema
        assert "properties" in schema
        assert "project_id" in schema["properties"]
        assert "method" in schema["properties"]

    @pytest.mark.asyncio
    async def test_detect_outliers_schema(self):
        """Test detect_outliers input schema."""
        from pm_mcp_servers.pm_analyse.server import list_tools
        tools = await list_tools()
        detect = next(t for t in tools if t.name == "detect_outliers")
        schema = detect.inputSchema
        assert "properties" in schema
        assert "sensitivity" in schema["properties"]

    @pytest.mark.asyncio
    async def test_assess_health_schema(self):
        """Test assess_health input schema."""
        from pm_mcp_servers.pm_analyse.server import list_tools
        tools = await list_tools()
        assess = next(t for t in tools if t.name == "assess_health")
        schema = assess.inputSchema
        assert "properties" in schema
        assert "weights" in schema["properties"]

    @pytest.mark.asyncio
    async def test_suggest_mitigations_schema(self):
        """Test suggest_mitigations input schema."""
        from pm_mcp_servers.pm_analyse.server import list_tools
        tools = await list_tools()
        suggest = next(t for t in tools if t.name == "suggest_mitigations")
        schema = suggest.inputSchema
        assert "properties" in schema
        assert "risk_ids" in schema["properties"]

    @pytest.mark.asyncio
    async def test_compare_baseline_schema(self):
        """Test compare_baseline input schema."""
        from pm_mcp_servers.pm_analyse.server import list_tools
        tools = await list_tools()
        compare = next(t for t in tools if t.name == "compare_baseline")
        schema = compare.inputSchema
        assert "properties" in schema
        assert "threshold" in schema["properties"]
