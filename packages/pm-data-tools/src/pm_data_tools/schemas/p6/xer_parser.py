"""XER format parser for Primavera P6.

XER (Project Export/Exchange) is a tab-delimited text format used by
Primavera P6 to export project data. This parser converts XER files
to the canonical data model.
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
from uuid import UUID

from pm_data_tools.models import (
    DeliveryConfidence,
    Dependency,
    DependencyType,
    Money,
    Project,
    Resource,
    ResourceType,
    SourceInfo,
    Task,
    TaskStatus,
)
from pm_data_tools.utils.identifiers import generate_uuid_from_source

from .constants import (
    RELATIONSHIP_TYPE_TO_DEPENDENCY_TYPE,
    RESOURCE_TYPE_TO_CANONICAL,
    RelationshipType,
)


class XERParser:
    """Parser for P6 XER format files.

    The XER format is a tab-delimited text format where:
    - %T lines define table structures (column names)
    - %R lines contain data records
    - %F lines mark end of tables
    """

    def __init__(self, file_path: Path):
        """Initialize parser.

        Args:
            file_path: Path to XER file
        """
        self.file_path = file_path
        self.source_tool = "primavera-p6"
        self.tables: dict[str, list[dict[str, str]]] = {}

    def parse(self) -> Project:
        """Parse XER file to canonical Project model.

        Returns:
            Parsed Project
        """
        # Read and parse XER file structure
        self._read_xer_file()

        # Extract project metadata
        project_data = self._parse_project()

        # Parse tasks
        tasks = self._parse_tasks()

        # Parse resources
        resources = self._parse_resources()

        # Parse dependencies
        dependencies = self._parse_dependencies()

        # Parse assignments
        assignments = self._parse_assignments()

        # Build project
        project = Project(
            id=project_data["id"],
            name=project_data["name"],
            source=project_data["source"],
            delivery_confidence=DeliveryConfidence.AMBER,  # Default
            start_date=project_data.get("start_date"),
            finish_date=project_data.get("finish_date"),
            tasks=tasks,
            resources=resources,
            assignments=assignments,
            dependencies=dependencies,
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        return project

    def _read_xer_file(self) -> None:
        """Read and parse XER file structure into tables."""
        with open(self.file_path, "r", encoding="utf-8") as f:
            current_table: Optional[str] = None
            current_columns: list[str] = []

            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Table definition
                if line.startswith("%T"):
                    parts = line.split("\t")
                    current_table = parts[1] if len(parts) > 1 else None
                    if current_table:
                        self.tables[current_table] = []

                # Column definitions
                elif line.startswith("%F"):
                    parts = line.split("\t")
                    current_columns = parts[1:] if len(parts) > 1 else []

                # Data record
                elif line.startswith("%R") and current_table and current_columns:
                    parts = line.split("\t")
                    values = parts[1:] if len(parts) > 1 else []

                    # Create record dict
                    record = {}
                    for i, col in enumerate(current_columns):
                        record[col] = values[i] if i < len(values) else ""

                    self.tables[current_table].append(record)

    def _parse_project(self) -> dict:
        """Parse project metadata from PROJECT table.

        Returns:
            Dict with project data
        """
        if "PROJECT" not in self.tables or not self.tables["PROJECT"]:
            raise ValueError("No PROJECT table found in XER file")

        proj_record = self.tables["PROJECT"][0]

        project_id = generate_uuid_from_source(
            self.source_tool, proj_record.get("proj_id", "1")
        )

        # Parse dates
        start_date = self._parse_date(proj_record.get("plan_start_date"))
        finish_date = self._parse_date(proj_record.get("plan_end_date"))

        return {
            "id": project_id,
            "name": proj_record.get("proj_short_name", "Unnamed Project"),
            "source": SourceInfo(
                tool=self.source_tool,
                tool_version="p6",
                original_id=proj_record.get("proj_id", "1"),
            ),
            "start_date": start_date,
            "finish_date": finish_date,
        }

    def _parse_tasks(self) -> list[Task]:
        """Parse tasks from TASK table.

        Returns:
            List of Task models
        """
        tasks: list[Task] = []

        if "TASK" not in self.tables:
            return tasks

        for task_record in self.tables["TASK"]:
            task_id = generate_uuid_from_source(
                self.source_tool, task_record.get("task_id", "")
            )

            # Parse parent WBS
            parent_id: Optional[UUID] = None
            wbs_id = task_record.get("wbs_id")
            if wbs_id:
                # Note: In real implementation, would need to track WBS hierarchy
                pass

            # Parse dates
            start_date = self._parse_date(task_record.get("act_start_date"))
            finish_date = self._parse_date(task_record.get("act_end_date"))

            # Parse progress
            percent_complete = float(task_record.get("phys_complete_pct", "0.0"))

            # Parse status
            status_code = task_record.get("status_code", "TK_NotStart")
            status = (
                TaskStatus.COMPLETED
                if status_code == "TK_Complete"
                else TaskStatus.IN_PROGRESS
                if status_code == "TK_Active"
                else TaskStatus.NOT_STARTED
            )

            task = Task(
                id=task_id,
                name=task_record.get("task_name", "Unnamed Task"),
                source=SourceInfo(
                    tool=self.source_tool,
                    tool_version="p6",
                    original_id=task_record.get("task_id", ""),
                ),
                parent_id=parent_id,
                start_date=start_date,
                finish_date=finish_date,
                percent_complete=percent_complete,
                status=status,
            )

            tasks.append(task)

        return tasks

    def _parse_resources(self) -> list[Resource]:
        """Parse resources from RSRC table.

        Returns:
            List of Resource models
        """
        resources: list[Resource] = []

        if "RSRC" not in self.tables:
            return resources

        for rsrc_record in self.tables["RSRC"]:
            resource_id = generate_uuid_from_source(
                self.source_tool, rsrc_record.get("rsrc_id", "")
            )

            # Map P6 resource type to canonical
            p6_type = rsrc_record.get("rsrc_type", "RT_Labor")
            resource_type = ResourceType.WORK  # Default

            if p6_type == "RT_Labor":
                resource_type = ResourceType.WORK
            elif p6_type == "RT_Mat":
                resource_type = ResourceType.MATERIAL
            elif p6_type == "RT_Equip":
                resource_type = ResourceType.EQUIPMENT

            resource = Resource(
                id=resource_id,
                name=rsrc_record.get("rsrc_name", "Unnamed Resource"),
                source=SourceInfo(
                    tool=self.source_tool,
                    tool_version="p6",
                    original_id=rsrc_record.get("rsrc_id", ""),
                ),
                resource_type=resource_type,
            )

            resources.append(resource)

        return resources

    def _parse_dependencies(self) -> list[Dependency]:
        """Parse dependencies from TASKPRED table.

        Returns:
            List of Dependency models
        """
        dependencies: list[Dependency] = []

        if "TASKPRED" not in self.tables:
            return dependencies

        for pred_record in self.tables["TASKPRED"]:
            dep_id = generate_uuid_from_source(
                self.source_tool, pred_record.get("task_pred_id", "")
            )

            predecessor_id = generate_uuid_from_source(
                self.source_tool, pred_record.get("pred_task_id", "")
            )

            successor_id = generate_uuid_from_source(
                self.source_tool, pred_record.get("task_id", "")
            )

            # Map relationship type
            p6_type = pred_record.get("pred_type", "PR_FS")
            dep_type = DependencyType.FINISH_TO_START  # Default

            if p6_type == "PR_FS":
                dep_type = DependencyType.FINISH_TO_START
            elif p6_type == "PR_FF":
                dep_type = DependencyType.FINISH_TO_FINISH
            elif p6_type == "PR_SS":
                dep_type = DependencyType.START_TO_START
            elif p6_type == "PR_SF":
                dep_type = DependencyType.START_TO_FINISH

            dependency = Dependency(
                id=dep_id,
                predecessor_id=predecessor_id,
                successor_id=successor_id,
                source=SourceInfo(
                    tool=self.source_tool,
                    tool_version="p6",
                    original_id=pred_record.get("task_pred_id", ""),
                ),
                dependency_type=dep_type,
            )

            dependencies.append(dependency)

        return dependencies

    def _parse_assignments(self) -> list:
        """Parse assignments from TASKRSRC table.

        Returns:
            List of Assignment models
        """
        # Simplified for now - full implementation would parse TASKRSRC table
        return []

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse P6 date string.

        P6 dates are typically in format: YYYY-MM-DD HH:MM

        Args:
            date_str: Date string

        Returns:
            Parsed datetime or None
        """
        if not date_str or date_str.strip() == "":
            return None

        try:
            # Try common P6 formats
            formats = [
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
                "%d-%b-%y %H:%M",
                "%d-%b-%y",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue

            return None
        except Exception:  # pragma: no cover
            return None  # pragma: no cover
