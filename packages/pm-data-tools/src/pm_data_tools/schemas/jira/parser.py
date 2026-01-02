"""Jira issue parser.

This module parses Jira issues (from API or JSON export) into the
canonical project data model.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from pm_data_tools.models import (
    DeliveryConfidence,
    Dependency,
    DependencyType,
    Project,
    SourceInfo,
    Task,
    TaskStatus,
)
from pm_data_tools.utils.identifiers import generate_uuid_from_source

from .constants import (
    STATUS_CATEGORY_TO_TASK_STATUS,
    STATUS_NAME_TO_TASK_STATUS,
)


class JiraParser:
    """Parser for Jira issues to canonical project model.

    Converts Jira issues into tasks, mapping:
    - Issue summary → Task name
    - Issue status → Task status
    - Issue hierarchy → Task parent relationships
    - Issue links → Dependencies (where applicable)
    """

    def __init__(self, project_key: str, project_name: Optional[str] = None):
        """Initialize parser.

        Args:
            project_key: Jira project key (e.g., "PROJ")
            project_name: Optional project name (defaults to project_key)
        """
        self.project_key = project_key
        self.project_name = project_name or project_key
        self.source_tool = "jira"

    def parse_from_file(self, file_path: Path) -> Project:
        """Parse Jira issues from JSON file.

        Args:
            file_path: Path to JSON file containing Jira issues

        Returns:
            Parsed Project
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        issues = data.get("issues", [])
        return self.parse_issues(issues)

    def parse_issues(self, issues: list[dict[str, Any]]) -> Project:
        """Parse Jira issues to Project model.

        Args:
            issues: List of Jira issue dicts

        Returns:
            Parsed Project
        """
        # Generate project ID
        project_id = generate_uuid_from_source(self.source_tool, self.project_key)

        # Parse tasks from issues
        tasks = self._parse_tasks(issues)

        # Parse dependencies from issue links
        dependencies = self._parse_dependencies(issues)

        # Create project
        project = Project(
            id=project_id,
            name=self.project_name,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version="cloud",
                original_id=self.project_key,
            ),
            delivery_confidence=DeliveryConfidence.AMBER,
            tasks=tasks,
            resources=[],  # Jira doesn't have resource management
            assignments=[],  # Jira assignees would need separate handling
            dependencies=dependencies,
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        return project

    def _parse_tasks(self, issues: list[dict[str, Any]]) -> list[Task]:
        """Parse Jira issues to Task models.

        Args:
            issues: List of Jira issue dicts

        Returns:
            List of Task models
        """
        tasks: list[Task] = []

        for issue in issues:
            fields = issue.get("fields", {})

            # Generate task ID from issue key
            task_id = generate_uuid_from_source(
                self.source_tool, issue.get("key", "")
            )

            # Parse parent relationship
            parent_id: Optional[UUID] = None
            parent = fields.get("parent")
            if parent:
                parent_key = parent.get("key")
                if parent_key:
                    parent_id = generate_uuid_from_source(self.source_tool, parent_key)

            # Parse status
            status_field = fields.get("status", {})
            status = self._map_status(status_field)

            # Parse dates
            created_date = self._parse_jira_date(fields.get("created"))
            updated_date = self._parse_jira_date(fields.get("updated"))
            due_date = self._parse_jira_date(fields.get("duedate"))

            # Parse progress (Jira doesn't have built-in % complete)
            # If status is "Done", consider it 100%, otherwise estimate based on status
            if status == TaskStatus.COMPLETED:
                percent_complete = 100.0
            elif status == TaskStatus.IN_PROGRESS:
                percent_complete = 50.0  # Estimate
            else:
                percent_complete = 0.0

            # Create task
            task = Task(
                id=task_id,
                name=fields.get("summary", "Unnamed Issue"),
                source=SourceInfo(
                    tool=self.source_tool,
                    tool_version="cloud",
                    original_id=issue.get("key", ""),
                ),
                parent_id=parent_id,
                start_date=created_date,  # Use created as start
                finish_date=due_date,  # Use due date as finish
                percent_complete=percent_complete,
                status=status,
            )

            tasks.append(task)

        return tasks

    def _parse_dependencies(
        self, issues: list[dict[str, Any]]
    ) -> list[Dependency]:
        """Parse dependencies from Jira issue links.

        Note: Jira issue links are not true dependencies, but we map
        "blocks/blocked by" relationships to dependencies.

        Args:
            issues: List of Jira issue dicts

        Returns:
            List of Dependency models
        """
        dependencies: list[Dependency] = []

        for issue in issues:
            fields = issue.get("fields", {})
            issue_links = fields.get("issuelinks", [])

            for link in issue_links:
                link_type = link.get("type", {})
                link_name = link_type.get("name", "").lower()

                # Only map "blocks" relationships to dependencies
                if "block" not in link_name:
                    continue

                # Determine predecessor and successor
                inward_issue = link.get("inwardIssue")
                outward_issue = link.get("outwardIssue")

                if inward_issue:  # This issue is blocked by inward issue
                    predecessor_key = inward_issue.get("key")
                    successor_key = issue.get("key")
                elif outward_issue:  # This issue blocks outward issue
                    predecessor_key = issue.get("key")
                    successor_key = outward_issue.get("key")
                else:
                    continue

                if not predecessor_key or not successor_key:
                    continue

                # Generate IDs
                dep_id = generate_uuid_from_source(
                    self.source_tool, f"{predecessor_key}-{successor_key}"
                )
                predecessor_id = generate_uuid_from_source(
                    self.source_tool, predecessor_key
                )
                successor_id = generate_uuid_from_source(
                    self.source_tool, successor_key
                )

                # Create dependency (Jira links are always finish-to-start)
                dependency = Dependency(
                    id=dep_id,
                    predecessor_id=predecessor_id,
                    successor_id=successor_id,
                    source=SourceInfo(
                        tool=self.source_tool,
                        tool_version="cloud",
                        original_id=f"{predecessor_key}-{successor_key}",
                    ),
                    dependency_type=DependencyType.FINISH_TO_START,
                )

                dependencies.append(dependency)

        return dependencies

    def _map_status(self, status_field: dict[str, Any]) -> TaskStatus:
        """Map Jira status to canonical task status.

        Args:
            status_field: Jira status field dict

        Returns:
            Canonical TaskStatus
        """
        # Try status category first (more reliable)
        status_category = status_field.get("statusCategory", {})
        category_key = status_category.get("key", "").lower()

        if category_key in STATUS_CATEGORY_TO_TASK_STATUS:
            return STATUS_CATEGORY_TO_TASK_STATUS[category_key]

        # Fall back to status name
        status_name = status_field.get("name", "").lower()
        if status_name in STATUS_NAME_TO_TASK_STATUS:
            return STATUS_NAME_TO_TASK_STATUS[status_name]

        # Default to in progress
        return TaskStatus.IN_PROGRESS

    def _parse_jira_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Jira date string.

        Jira dates can be in formats:
        - ISO 8601 with time: 2025-01-01T12:00:00.000+0000
        - Date only: 2025-01-15

        Args:
            date_str: Date string

        Returns:
            Parsed datetime or None
        """
        if not date_str:
            return None

        try:
            # Try date-only format first (duedate format)
            if "T" not in date_str:
                return datetime.fromisoformat(date_str)

            # Handle full ISO format with timezone
            # Remove milliseconds and timezone
            clean_str = date_str.split(".")[0]  # Remove .000+0000
            clean_str = clean_str.split("+")[0]  # Remove +0000
            clean_str = clean_str.split("-")[0:3]  # Keep YYYY-MM-DDTHH:MM:SS parts
            clean_str = "-".join(clean_str)

            return datetime.fromisoformat(clean_str)
        except (ValueError, AttributeError, IndexError):
            return None
