"""Shared utilities and stores for pm-mcp-servers.

This module provides shared project storage that can be used across
different MCP server modules (pm-data, pm-analyse, pm-validate).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ProjectStore:
    """Thread-safe in-memory project storage shared across MCP servers."""
    _projects: dict[str, Any] = field(default_factory=dict)

    def add(self, project_id: str, project: Any) -> None:
        """Store a project."""
        self._projects[project_id] = project

    def get(self, project_id: str) -> Optional[Any]:
        """Retrieve a project by ID."""
        return self._projects.get(project_id)

    def exists(self, project_id: str) -> bool:
        """Check if project exists."""
        return project_id in self._projects

    def list_all(self) -> list[str]:
        """List all project IDs."""
        return list(self._projects.keys())

    def remove(self, project_id: str) -> bool:
        """Remove a project."""
        if project_id in self._projects:
            del self._projects[project_id]
            return True
        return False


# Global project store instance that can be imported by all MCP servers
project_store = ProjectStore()
