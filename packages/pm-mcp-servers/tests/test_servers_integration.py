"""Integration tests for MCP server implementations."""

import pytest


class TestPMDataServer:
    """Tests for pm-data MCP server."""

    @pytest.mark.asyncio
    async def test_server_imports(self):
        """Server module imports without errors."""
        from pm_mcp_servers.pm_data import server
        assert server is not None

    @pytest.mark.asyncio
    async def test_server_exists(self):
        """Server instance is created."""
        from pm_mcp_servers.pm_data.server import server
        assert server is not None
        assert server.name == "pm-data"


class TestPMValidateServer:
    """Tests for pm-validate MCP server."""

    @pytest.mark.asyncio
    async def test_server_imports(self):
        """Server module imports without errors."""
        from pm_mcp_servers.pm_validate import server
        assert server is not None

    @pytest.mark.asyncio
    async def test_server_exists(self):
        """Server instance is created."""
        from pm_mcp_servers.pm_validate.server import app
        assert app is not None
        assert app.name == "pm-validate"
