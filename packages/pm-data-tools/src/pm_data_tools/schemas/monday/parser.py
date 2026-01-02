"""Parser for Monday.com JSON API responses."""

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
from .constants import (
    COLUMN_TYPE_DATE,
    COLUMN_TYPE_NUMBERS,
    COLUMN_TYPE_PEOPLE,
    COLUMN_TYPE_PROGRESS,
    COLUMN_TYPE_STATUS,
    COLUMN_TYPE_TIMELINE,
    STATUS_LABEL_TO_TASK_STATUS,
)


class MondayParser:
    """Parser for Monday.com board JSON data.

    Monday.com boards are converted to Projects, with:
    - Groups → Summary tasks (WBS structure)
    - Items → Tasks
    - Subitems → Child tasks
    - Status columns → Task status
    - Timeline columns → Start/finish dates
    - People columns → Resources
    """

    def __init__(self, board_name: Optional[str] = None):
        """Initialize parser.

        Args:
            board_name: Override board name (uses board.name if None)
        """
        self.board_name = board_name
        self.source_tool = "monday"
        self._task_map: dict[str, UUID] = {}
        self._resource_map: dict[str, UUID] = {}

    def parse_file(self, file_path: Path) -> Project:
        """Parse Monday.com JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed Project
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return self.parse(data)

    def parse_string(self, json_string: str) -> Project:
        """Parse Monday.com JSON string.

        Args:
            json_string: JSON string

        Returns:
            Parsed Project
        """
        data = json.loads(json_string)
        return self.parse(data)

    def parse(self, data: dict[str, Any]) -> Project:
        """Parse Monday.com JSON data to canonical Project.

        Args:
            data: Monday.com board JSON data

        Returns:
            Canonical Project
        """
        # Reset mappings
        self._task_map = {}
        self._resource_map = {}

        # Extract board info
        board = data.get("data", {}).get("boards", [{}])[0] if "data" in data else data

        board_id = str(board.get("id", "1"))
        board_name = self.board_name or board.get("name", "Monday Board")

        # Generate project ID
        project_id = generate_uuid_from_source(self.source_tool, board_id)

        # Parse tasks and resources
        tasks: list[Task] = []
        resources: list[Resource] = []

        # Process groups and items
        groups = board.get("groups", [])
        for group in groups:
            # Create group as summary task
            group_task = self._parse_group(group, board_id)
            if group_task:
                tasks.append(group_task)

                # Process items in group
                items = group.get("items", [])
                for item in items:
                    item_task = self._parse_item(item, board_id, group_task.id)
                    if item_task:
                        tasks.append(item_task)

                        # Extract resources from this item
                        item_resources = self._extract_resources(item, board_id)
                        for resource in item_resources:
                            if resource.id not in [r.id for r in resources]:
                                resources.append(resource)

                        # Process subitems
                        subitems = item.get("subitems", [])
                        for subitem in subitems:
                            subitem_task = self._parse_subitem(
                                subitem, board_id, item_task.id
                            )
                            if subitem_task:
                                tasks.append(subitem_task)

        # Build project
        project = Project(
            id=project_id,
            name=board_name,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version="v2",
                original_id=board_id,
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

    def _parse_group(self, group: dict[str, Any], board_id: str) -> Optional[Task]:
        """Parse Monday.com group to summary Task.

        Args:
            group: Group data
            board_id: Board ID for UUID generation

        Returns:
            Summary task or None
        """
        group_id = group.get("id")
        if not group_id:
            return None

        group_title = group.get("title", "Untitled Group")

        task_id = generate_uuid_from_source(
            self.source_tool, f"{board_id}:group:{group_id}"
        )
        self._task_map[group_id] = task_id

        return Task(
            id=task_id,
            name=group_title,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version="v2",
                original_id=f"group:{group_id}",
            ),
            is_summary=True,
            status=TaskStatus.IN_PROGRESS,  # Groups don't have status
        )

    def _parse_item(
        self, item: dict[str, Any], board_id: str, parent_id: UUID
    ) -> Optional[Task]:
        """Parse Monday.com item to Task.

        Args:
            item: Item data
            board_id: Board ID
            parent_id: Parent group task ID

        Returns:
            Task or None
        """
        item_id = item.get("id")
        if not item_id:
            return None

        item_name = item.get("name", "Untitled Item")

        task_id = generate_uuid_from_source(
            self.source_tool, f"{board_id}:item:{item_id}"
        )
        self._task_map[item_id] = task_id

        # Extract column values
        column_values = item.get("column_values", [])

        # Get status
        status = self._extract_status(column_values)

        # Get dates
        start_date, finish_date = self._extract_dates(column_values)

        # Get percent complete
        percent_complete = self._extract_percent_complete(column_values)

        # Derive status from percent if not explicitly set
        if status == TaskStatus.IN_PROGRESS and percent_complete is not None:
            if percent_complete == 0.0:
                status = TaskStatus.NOT_STARTED
            elif percent_complete == 100.0:
                status = TaskStatus.COMPLETED

        return Task(
            id=task_id,
            name=item_name,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version="v2",
                original_id=f"item:{item_id}",
            ),
            parent_id=parent_id,
            start_date=start_date,
            finish_date=finish_date,
            percent_complete=percent_complete or 0.0,
            status=status,
        )

    def _parse_subitem(
        self, subitem: dict[str, Any], board_id: str, parent_id: UUID
    ) -> Optional[Task]:
        """Parse Monday.com subitem to Task.

        Args:
            subitem: Subitem data
            board_id: Board ID
            parent_id: Parent item task ID

        Returns:
            Task or None
        """
        subitem_id = subitem.get("id")
        if not subitem_id:
            return None

        subitem_name = subitem.get("name", "Untitled Subitem")

        task_id = generate_uuid_from_source(
            self.source_tool, f"{board_id}:subitem:{subitem_id}"
        )
        self._task_map[subitem_id] = task_id

        # Extract column values (subitems can have their own columns)
        column_values = subitem.get("column_values", [])

        status = self._extract_status(column_values)
        start_date, finish_date = self._extract_dates(column_values)
        percent_complete = self._extract_percent_complete(column_values)

        return Task(
            id=task_id,
            name=subitem_name,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version="v2",
                original_id=f"subitem:{subitem_id}",
            ),
            parent_id=parent_id,
            start_date=start_date,
            finish_date=finish_date,
            percent_complete=percent_complete or 0.0,
            status=status,
        )

    def _extract_status(self, column_values: list[dict[str, Any]]) -> TaskStatus:
        """Extract task status from column values.

        Args:
            column_values: List of column value dictionaries

        Returns:
            Task status
        """
        for col in column_values:
            if col.get("type") == COLUMN_TYPE_STATUS:
                # Get status label
                value = col.get("value")
                if value:
                    try:
                        value_data = json.loads(value) if isinstance(value, str) else value
                        label = value_data.get("label", "")
                        return STATUS_LABEL_TO_TASK_STATUS.get(
                            label, TaskStatus.IN_PROGRESS
                        )
                    except (json.JSONDecodeError, AttributeError):
                        pass

        return TaskStatus.IN_PROGRESS  # Default

    def _extract_dates(
        self, column_values: list[dict[str, Any]]
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        """Extract start and finish dates from column values.

        Args:
            column_values: List of column value dictionaries

        Returns:
            Tuple of (start_date, finish_date)
        """
        start_date: Optional[datetime] = None
        finish_date: Optional[datetime] = None

        for col in column_values:
            col_type = col.get("type")
            value = col.get("value")

            if not value or value == "null":
                continue

            try:
                if col_type == COLUMN_TYPE_TIMELINE:
                    # Timeline has from/to dates
                    value_data = json.loads(value) if isinstance(value, str) else value
                    from_date = value_data.get("from")
                    to_date = value_data.get("to")

                    if from_date:
                        start_date = self._parse_date_string(from_date)
                    if to_date:
                        finish_date = self._parse_date_string(to_date)
                    break  # Timeline takes precedence

                elif col_type == COLUMN_TYPE_DATE:
                    # Single date column
                    value_data = json.loads(value) if isinstance(value, str) else value
                    date_str = value_data.get("date") if isinstance(value_data, dict) else value_data
                    if date_str:
                        parsed_date = self._parse_date_string(date_str)
                        # Use as finish date if not already set
                        if not finish_date:
                            finish_date = parsed_date
            except (json.JSONDecodeError, AttributeError, ValueError):
                continue

        return start_date, finish_date

    def _extract_percent_complete(
        self, column_values: list[dict[str, Any]]
    ) -> Optional[float]:
        """Extract percent complete from column values.

        Args:
            column_values: List of column value dictionaries

        Returns:
            Percent complete (0-100) or None
        """
        for col in column_values:
            col_type = col.get("type")
            value = col.get("value")

            if col_type == COLUMN_TYPE_PROGRESS and value:
                try:
                    # Progress column stores percentage
                    if isinstance(value, str) and value != "null":
                        value_data = json.loads(value)
                        if isinstance(value_data, dict):
                            return float(value_data.get("value", 0))
                        return float(value_data)
                    elif isinstance(value, (int, float)):
                        return float(value)
                except (json.JSONDecodeError, ValueError, TypeError):
                    continue

            # Also check numbers column with "progress" or "complete" in title
            if col_type == COLUMN_TYPE_NUMBERS:
                title = col.get("title", "").lower()
                if "progress" in title or "complete" in title:
                    try:
                        if isinstance(value, str) and value != "null":
                            return float(value)
                        elif isinstance(value, (int, float)):
                            return float(value)
                    except (ValueError, TypeError):
                        continue

        return None

    def _extract_resources(
        self, item: dict[str, Any], board_id: str
    ) -> list[Resource]:
        """Extract resources from item people columns.

        Args:
            item: Item data
            board_id: Board ID

        Returns:
            List of resources
        """
        resources: list[Resource] = []
        column_values = item.get("column_values", [])

        for col in column_values:
            if col.get("type") == COLUMN_TYPE_PEOPLE:
                value = col.get("value")
                if not value or value == "null":
                    continue

                try:
                    value_data = json.loads(value) if isinstance(value, str) else value
                    persons_and_teams = value_data.get("personsAndTeams", [])

                    for person in persons_and_teams:
                        person_id = str(person.get("id", ""))
                        if not person_id:
                            continue

                        # Check if already tracked
                        if person_id in self._resource_map:
                            continue

                        name = person.get("name", f"User {person_id}")

                        resource_id = generate_uuid_from_source(
                            self.source_tool, f"{board_id}:person:{person_id}"
                        )
                        self._resource_map[person_id] = resource_id

                        resources.append(
                            Resource(
                                id=resource_id,
                                name=name,
                                source=SourceInfo(
                                    tool=self.source_tool,
                                    tool_version="v2",
                                    original_id=f"person:{person_id}",
                                ),
                                resource_type=ResourceType.WORK,
                            )
                        )
                except (json.JSONDecodeError, AttributeError):
                    continue

        return resources

    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime.

        Args:
            date_str: Date string (typically YYYY-MM-DD)

        Returns:
            Parsed datetime or None
        """
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
