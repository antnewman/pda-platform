"""Parser for Asana JSON API responses."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from ...models import (
    DeliveryConfidence,
    Project,
    Resource,
    ResourceType,
    SourceInfo,
    Task,
    TaskStatus,
)
from ...utils.identifiers import generate_uuid_from_source
from .constants import get_status_from_completed


class AsanaParser:
    """Parser for Asana project JSON data.

    Asana projects are converted to Projects, with:
    - Sections → Summary tasks (WBS structure)
    - Tasks → Tasks
    - Subtasks → Child tasks
    - completed field → Task status
    - start_on/due_on → Start/finish dates
    - assignee → Resources
    """

    def __init__(self, project_name: Optional[str] = None):
        """Initialise parser.

        Args:
            project_name: Override project name (uses project.name if None)
        """
        self.project_name = project_name
        self.source_tool = "asana"
        self._task_map: dict[str, UUID] = {}
        self._resource_map: dict[str, UUID] = {}

    def parse_file(self, file_path: Path) -> Project:
        """Parse Asana JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed Project
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return self.parse(data)

    def parse_string(self, json_string: str) -> Project:
        """Parse Asana JSON string.

        Args:
            json_string: JSON string

        Returns:
            Parsed Project
        """
        data = json.loads(json_string)
        return self.parse(data)

    def parse(self, data: dict[str, Any]) -> Project:
        """Parse Asana JSON data to canonical Project.

        Args:
            data: Asana project JSON data

        Returns:
            Canonical Project
        """
        # Reset mappings
        self._task_map = {}
        self._resource_map = {}

        # Extract project info
        project_data = data.get("data", {}) if "data" in data else data

        project_gid = str(project_data.get("gid", "1"))
        project_name = self.project_name or project_data.get("name", "Asana Project")

        # Generate project ID
        project_id = generate_uuid_from_source(self.source_tool, project_gid)

        # Parse tasks and resources
        tasks: list[Task] = []
        resources: list[Resource] = []

        # Process sections and tasks
        sections = project_data.get("sections", [])
        for section in sections:
            # Create section as summary task
            section_task = self._parse_section(section, project_gid)
            if section_task:
                tasks.append(section_task)

                # Process tasks in section
                section_tasks = section.get("tasks", [])
                for task_data in section_tasks:
                    task = self._parse_task(task_data, project_gid, section_task.id)
                    if task:
                        tasks.append(task)

                        # Extract resources from this task
                        task_resources = self._extract_resources(task_data, project_gid)
                        for resource in task_resources:
                            if resource.id not in [r.id for r in resources]:
                                resources.append(resource)

                        # Process subtasks
                        subtasks = task_data.get("subtasks", [])
                        for subtask_data in subtasks:
                            subtask = self._parse_subtask(
                                subtask_data, project_gid, task.id
                            )
                            if subtask:
                                tasks.append(subtask)

        # Build project
        project = Project(
            id=project_id,
            name=project_name,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version="v1",
                original_id=project_gid,
            ),
            delivery_confidence=DeliveryConfidence.AMBER,  # Default
            tasks=tasks,
            resources=resources,
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        return project

    def _parse_section(
        self, section: dict[str, Any], project_gid: str
    ) -> Optional[Task]:
        """Parse Asana section to summary Task.

        Args:
            section: Section data
            project_gid: Project GID for UUID generation

        Returns:
            Summary task or None
        """
        section_gid = section.get("gid")
        if not section_gid:
            return None

        section_name = section.get("name", "Untitled Section")

        task_id = generate_uuid_from_source(
            self.source_tool, f"{project_gid}:section:{section_gid}"
        )
        self._task_map[section_gid] = task_id

        return Task(
            id=task_id,
            name=section_name,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version="v1",
                original_id=f"section:{section_gid}",
            ),
            is_summary=True,
            status=TaskStatus.IN_PROGRESS,  # Sections don't have status
        )

    def _parse_task(
        self, task_data: dict[str, Any], project_gid: str, parent_id: UUID
    ) -> Optional[Task]:
        """Parse Asana task to Task.

        Args:
            task_data: Task data
            project_gid: Project GID
            parent_id: Parent section task ID

        Returns:
            Task or None
        """
        task_gid = task_data.get("gid")
        if not task_gid:
            return None

        task_name = task_data.get("name", "Untitled Task")

        task_id = generate_uuid_from_source(
            self.source_tool, f"{project_gid}:task:{task_gid}"
        )
        self._task_map[task_gid] = task_id

        # Get completed status
        completed = task_data.get("completed", False)
        status = get_status_from_completed(completed)

        # Get dates
        start_date = self._parse_date_string(task_data.get("start_on"))
        finish_date = self._parse_date_string(task_data.get("due_on"))

        # Percent complete
        percent_complete = 100.0 if completed else 0.0

        return Task(
            id=task_id,
            name=task_name,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version="v1",
                original_id=f"task:{task_gid}",
            ),
            parent_id=parent_id,
            start_date=start_date,
            finish_date=finish_date,
            percent_complete=percent_complete,
            status=status,
        )

    def _parse_subtask(
        self, subtask_data: dict[str, Any], project_gid: str, parent_id: UUID
    ) -> Optional[Task]:
        """Parse Asana subtask to Task.

        Args:
            subtask_data: Subtask data
            project_gid: Project GID
            parent_id: Parent task ID

        Returns:
            Task or None
        """
        subtask_gid = subtask_data.get("gid")
        if not subtask_gid:
            return None

        subtask_name = subtask_data.get("name", "Untitled Subtask")

        task_id = generate_uuid_from_source(
            self.source_tool, f"{project_gid}:subtask:{subtask_gid}"
        )
        self._task_map[subtask_gid] = task_id

        # Get completed status
        completed = subtask_data.get("completed", False)
        status = get_status_from_completed(completed)

        # Get dates
        start_date = self._parse_date_string(subtask_data.get("start_on"))
        finish_date = self._parse_date_string(subtask_data.get("due_on"))

        # Percent complete
        percent_complete = 100.0 if completed else 0.0

        return Task(
            id=task_id,
            name=subtask_name,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version="v1",
                original_id=f"subtask:{subtask_gid}",
            ),
            parent_id=parent_id,
            start_date=start_date,
            finish_date=finish_date,
            percent_complete=percent_complete,
            status=status,
        )

    def _extract_resources(
        self, task_data: dict[str, Any], project_gid: str
    ) -> list[Resource]:
        """Extract resources from task assignee.

        Args:
            task_data: Task data
            project_gid: Project GID

        Returns:
            List of resources
        """
        resources: list[Resource] = []

        assignee = task_data.get("assignee")
        if not assignee:
            return resources

        assignee_gid = str(assignee.get("gid", ""))
        if not assignee_gid:
            return resources

        # Check if already tracked
        if assignee_gid in self._resource_map:
            return resources

        name = assignee.get("name", f"User {assignee_gid}")

        resource_id = generate_uuid_from_source(
            self.source_tool, f"{project_gid}:user:{assignee_gid}"
        )
        self._resource_map[assignee_gid] = resource_id

        resources.append(
            Resource(
                id=resource_id,
                name=name,
                source=SourceInfo(
                    tool=self.source_tool,
                    tool_version="v1",
                    original_id=f"user:{assignee_gid}",
                ),
                resource_type=ResourceType.WORK,
            )
        )

        return resources

    def _parse_date_string(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime.

        Args:
            date_str: Date string (typically YYYY-MM-DD)

        Returns:
            Parsed datetime or None
        """
        if not date_str:
            return None

        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None
