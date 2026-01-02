"""Parser for Smartsheet JSON API responses."""

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
)
from ...utils.identifiers import generate_uuid_from_source
from .constants import get_status_from_percent_complete


class SmartsheetParser:
    """Parser for Smartsheet JSON data.

    Smartsheet sheets are converted to Projects, with:
    - Rows → Tasks (hierarchical via parentId)
    - Rows with children → Summary tasks
    - Columns mapped to task attributes
    - percentComplete → Task status
    - start/end → Start/finish dates
    - assignedTo → Resources
    """

    def __init__(self, sheet_name: Optional[str] = None):
        """Initialise parser.

        Args:
            sheet_name: Override sheet name (uses sheet.name if None)
        """
        self.sheet_name = sheet_name
        self.source_tool = "smartsheet"
        self._task_map: dict[str, UUID] = {}
        self._resource_map: dict[str, UUID] = {}
        self._row_children: dict[str, list[dict[str, Any]]] = {}

    def parse_file(self, file_path: Path) -> Project:
        """Parse Smartsheet JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed Project
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return self.parse(data)

    def parse_string(self, json_string: str) -> Project:
        """Parse Smartsheet JSON string.

        Args:
            json_string: JSON string

        Returns:
            Parsed Project
        """
        data = json.loads(json_string)
        return self.parse(data)

    def parse(self, data: dict[str, Any]) -> Project:
        """Parse Smartsheet JSON data to canonical Project.

        Args:
            data: Smartsheet JSON data

        Returns:
            Canonical Project
        """
        # Reset mappings
        self._task_map = {}
        self._resource_map = {}
        self._row_children = {}

        # Extract sheet info
        sheet_data = data.get("data", {}) if "data" in data else data

        sheet_id = str(sheet_data.get("id", "1"))
        sheet_name = self.sheet_name or sheet_data.get("name", "Smartsheet")

        # Generate project ID
        project_id = generate_uuid_from_source(self.source_tool, sheet_id)

        # Build parent-child relationships
        rows = sheet_data.get("rows", [])
        self._build_hierarchy(rows)

        # Parse tasks and resources
        tasks: list[Task] = []
        resources: list[Resource] = []

        # Process all rows
        for row in rows:
            # Parse row as task
            task = self._parse_row(row, sheet_id)
            if task:
                tasks.append(task)

                # Extract resources
                row_resources = self._extract_resources(row, sheet_id)
                for resource in row_resources:
                    if resource.id not in [r.id for r in resources]:
                        resources.append(resource)

        # Build project
        project = Project(
            id=project_id,
            name=sheet_name,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version="v2",
                original_id=sheet_id,
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

    def _build_hierarchy(self, rows: list[dict[str, Any]]) -> None:
        """Build parent-child relationships from rows.

        Args:
            rows: List of row dictionaries
        """
        for row in rows:
            parent_id = str(row.get("parentId", ""))
            if parent_id:
                if parent_id not in self._row_children:
                    self._row_children[parent_id] = []
                self._row_children[parent_id].append(row)

    def _parse_row(self, row: dict[str, Any], sheet_id: str) -> Optional[Task]:
        """Parse Smartsheet row to Task.

        Args:
            row: Row data
            sheet_id: Sheet ID

        Returns:
            Task or None
        """
        row_id = row.get("id")
        if not row_id:
            return None

        row_id_str = str(row_id)

        # Determine if this is a summary task (has children)
        is_summary = row_id_str in self._row_children

        # Extract column values
        columns = {cell.get("columnId"): cell for cell in row.get("cells", [])}

        # Get task name (first column or from specific column)
        task_name = self._extract_value(row, "name") or "Untitled Row"

        # Get parent ID if exists
        parent_id: Optional[UUID] = None
        parent_row_id = row.get("parentId")
        if parent_row_id:
            parent_row_id_str = str(parent_row_id)
            if parent_row_id_str in self._task_map:
                parent_id = self._task_map[parent_row_id_str]

        # Generate task ID
        task_id = generate_uuid_from_source(
            self.source_tool, f"{sheet_id}:row:{row_id_str}"
        )
        self._task_map[row_id_str] = task_id

        # Get percent complete
        percent_complete = self._extract_percent_complete(row)

        # Get status
        status = get_status_from_percent_complete(percent_complete)

        # Get dates
        start_date = self._extract_date(row, "start")
        finish_date = self._extract_date(row, "end")

        return Task(
            id=task_id,
            name=task_name,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version="v2",
                original_id=f"row:{row_id_str}",
            ),
            parent_id=parent_id,
            is_summary=is_summary,
            start_date=start_date,
            finish_date=finish_date,
            percent_complete=percent_complete,
            status=status,
        )

    def _extract_value(self, row: dict[str, Any], field_name: str) -> Optional[str]:
        """Extract value from row by field name.

        Args:
            row: Row data
            field_name: Field name to extract

        Returns:
            Field value or None
        """
        # Try direct field access first
        if field_name in row:
            return str(row[field_name])

        # Try cells
        for cell in row.get("cells", []):
            value = cell.get("value")
            if value is not None:
                # Use first non-empty cell as name if no specific mapping
                return str(value)

        return None

    def _extract_percent_complete(self, row: dict[str, Any]) -> float:
        """Extract percent complete from row.

        Args:
            row: Row data

        Returns:
            Percent complete (0-100)
        """
        # Try direct field
        if "percentComplete" in row:
            try:
                return float(row["percentComplete"])
            except (ValueError, TypeError):
                pass

        # Try cells
        for cell in row.get("cells", []):
            # Look for percent complete column
            if cell.get("columnType") == "PERCENT_COMPLETE":
                value = cell.get("value")
                if value is not None:
                    try:
                        return float(value) * 100  # Smartsheet stores as 0-1
                    except (ValueError, TypeError):
                        pass

        return 0.0

    def _extract_date(
        self, row: dict[str, Any], field_name: str
    ) -> Optional[datetime]:
        """Extract date from row.

        Args:
            row: Row data
            field_name: Field name (start or end)

        Returns:
            Parsed datetime or None
        """
        # Try direct field
        if field_name in row:
            return self._parse_date_string(row[field_name])

        # Try cells with specific column types
        for cell in row.get("cells", []):
            col_type = cell.get("columnType", "")
            if (field_name == "start" and col_type == "DATE") or (
                field_name == "end" and col_type == "DATE"
            ):
                value = cell.get("value")
                if value:
                    return self._parse_date_string(value)

        return None

    def _extract_resources(
        self, row: dict[str, Any], sheet_id: str
    ) -> list[Resource]:
        """Extract resources from row assignedTo field.

        Args:
            row: Row data
            sheet_id: Sheet ID

        Returns:
            List of resources
        """
        resources: list[Resource] = []

        # Try direct assignedTo field
        assigned_to = row.get("assignedTo")
        if not assigned_to:
            # Try cells
            for cell in row.get("cells", []):
                if cell.get("columnType") == "CONTACT_LIST":
                    assigned_to = cell.get("value")
                    if assigned_to:
                        break

        if not assigned_to:
            return resources

        # Parse assigned users (can be string or object)
        if isinstance(assigned_to, str):
            # Single user as string
            user_id = assigned_to
            user_name = assigned_to
        elif isinstance(assigned_to, dict):
            # User object
            user_id = str(assigned_to.get("id", assigned_to.get("email", "")))
            user_name = assigned_to.get("name", assigned_to.get("email", user_id))
        else:
            return resources

        if not user_id:
            return resources

        # Check if already tracked
        if user_id in self._resource_map:
            return resources

        resource_id = generate_uuid_from_source(
            self.source_tool, f"{sheet_id}:user:{user_id}"
        )
        self._resource_map[user_id] = resource_id

        resources.append(
            Resource(
                id=resource_id,
                name=user_name,
                source=SourceInfo(
                    tool=self.source_tool,
                    tool_version="v2",
                    original_id=f"user:{user_id}",
                ),
                resource_type=ResourceType.WORK,
            )
        )

        return resources

    def _parse_date_string(self, date_str: Any) -> Optional[datetime]:
        """Parse date string to datetime.

        Args:
            date_str: Date string (typically YYYY-MM-DD)

        Returns:
            Parsed datetime or None
        """
        if not date_str:
            return None

        if not isinstance(date_str, str):
            return None

        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None
