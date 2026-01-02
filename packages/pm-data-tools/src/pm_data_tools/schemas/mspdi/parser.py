"""MSPDI XML parser for Microsoft Project files.

This module provides parsing functionality to convert MSPDI (Microsoft Project
Data Interchange) XML files into the canonical project management data model.
"""

from pathlib import Path
from typing import Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime

from lxml import etree

from pm_data_tools.models import (
    Project,
    Task,
    Resource,
    Assignment,
    Dependency,
    Calendar,
    SourceInfo,
    Duration,
    Money,
    CustomField,
    DeliveryConfidence,
)
from pm_data_tools.utils.xml_helpers import (
    parse_xml_file,
    parse_xml_string,
    get_text,
    get_int,
    get_float,
    get_bool,
    strip_namespaces,
)
from pm_data_tools.utils.dates import parse_iso_datetime, parse_mspdi_duration
from pm_data_tools.utils.identifiers import generate_uuid_from_source

from .constants import (
    MSPDI_CONSTRAINT_TYPE_MAP,
    MSPDI_DEPENDENCY_TYPE_MAP,
    MSPDI_RESOURCE_TYPE_MAP,
    get_task_status_from_percent,
    DEFAULT_CURRENCY,
)


class MspdiParser:
    """Parser for MSPDI XML files.

    Converts Microsoft Project XML (MSPDI format) into canonical PM data model.
    Supports full project structure including tasks, resources, assignments,
    dependencies, and calendars.
    """

    def __init__(self) -> None:
        """Initialise MSPDI parser."""
        self.source_tool = "mspdi"

    def parse_file(self, file_path: str | Path) -> Optional[Project]:
        """Parse MSPDI XML file into Project model.

        Args:
            file_path: Path to MSPDI XML file

        Returns:
            Parsed Project or None if parsing fails
        """
        root = parse_xml_file(file_path)
        if root is None:
            return None

        # Strip namespaces for easier parsing
        root = strip_namespaces(root)

        return self._parse_project(root)

    def parse_string(self, xml_content: str | bytes) -> Optional[Project]:
        """Parse MSPDI XML string into Project model.

        Args:
            xml_content: MSPDI XML content as string or bytes

        Returns:
            Parsed Project or None if parsing fails
        """
        root = parse_xml_string(xml_content)
        if root is None:
            return None

        # Strip namespaces for easier parsing
        root = strip_namespaces(root)

        return self._parse_project(root)

    def _parse_project(self, root: etree._Element) -> Project:
        """Parse Project element into Project model.

        Args:
            root: Root XML element (should be Project)

        Returns:
            Parsed Project model
        """
        # Extract project metadata
        name = get_text(root, "Name", default="Untitled Project")
        title = get_text(root, "Title")
        manager = get_text(root, "Manager")
        company = get_text(root, "Company")

        # Parse dates
        start_date = parse_iso_datetime(get_text(root, "StartDate"))
        finish_date = parse_iso_datetime(get_text(root, "FinishDate"))
        status_date = parse_iso_datetime(get_text(root, "StatusDate"))
        baseline_date = parse_iso_datetime(get_text(root, "CurrentDate"))

        # Parse currency
        currency_code = get_text(root, "CurrencyCode", default=DEFAULT_CURRENCY)

        # Parse custom fields
        custom_fields_dict: dict[str, str] = {}
        author = get_text(root, "Author")
        if author:
            custom_fields_dict["author"] = author
        subject = get_text(root, "Subject")
        if subject:
            custom_fields_dict["subject"] = subject

        custom_fields_list = [
            CustomField(
                name=k,
                value=v,
                field_type="text",
                source_tool=self.source_tool,
            )
            for k, v in custom_fields_dict.items()
        ]

        # Create source info
        source = SourceInfo(
            tool=self.source_tool,
            tool_version=get_text(root, "SaveVersion", default="unknown"),
            original_id=get_text(root, "UID", default="0"),
        )

        # Generate project UUID
        project_id = generate_uuid_from_source(
            self.source_tool, source.original_id or "0"
        )

        # Parse tasks
        tasks = self._parse_tasks(root)

        # Parse resources
        resources = self._parse_resources(root)

        # Parse assignments
        assignments = self._parse_assignments(root)

        # Parse dependencies (from task predecessor links)
        dependencies = self._parse_dependencies(root)

        # Parse calendars
        calendars = self._parse_calendars(root)

        # Build Project
        return Project(
            id=project_id,
            name=name,
            source=source,
            start_date=start_date,
            finish_date=finish_date,
            status_date=status_date,
            description=title,
            project_manager=manager,
            department=company,
            tasks=tasks,
            resources=resources,
            assignments=assignments,
            dependencies=dependencies,
            calendars=calendars,
            custom_fields=custom_fields_list,
            delivery_confidence=DeliveryConfidence.EXEMPT,  # MSPDI doesn't have this
        )

    def _parse_tasks(self, root: etree._Element) -> list[Task]:
        """Parse all Task elements.

        Args:
            root: Project root element

        Returns:
            List of parsed Task models
        """
        tasks: list[Task] = []
        tasks_element = root.find("Tasks")
        if tasks_element is None:
            return tasks

        for task_elem in tasks_element.findall("Task"):
            task = self._parse_task(task_elem)
            if task is not None:
                tasks.append(task)

        return tasks

    def _parse_task(self, elem: etree._Element) -> Optional[Task]:
        """Parse single Task element.

        Args:
            elem: Task XML element

        Returns:
            Parsed Task or None if invalid
        """
        # Get task UID (required)
        uid_str = get_text(elem, "UID")
        if not uid_str:
            return None

        # Generate task UUID
        task_id = generate_uuid_from_source(self.source_tool, uid_str)

        # Basic fields
        name = get_text(elem, "Name", default="Untitled Task")
        notes = get_text(elem, "Notes")
        wbs_code = get_text(elem, "WBS")
        outline_level = get_int(elem, "OutlineLevel", default=1)

        # Parent task
        # Parent task
        parent_id: Optional[UUID] = None
        parent_uid = get_text(elem, "OutlineParent")
        if parent_uid:
            parent_id = generate_uuid_from_source(self.source_tool, parent_uid)

        # Dates
        start_date = parse_iso_datetime(get_text(elem, "Start"))
        finish_date = parse_iso_datetime(get_text(elem, "Finish"))
        actual_start = parse_iso_datetime(get_text(elem, "ActualStart"))
        actual_finish = parse_iso_datetime(get_text(elem, "ActualFinish"))
        baseline_start = parse_iso_datetime(get_text(elem, "BaselineStart"))
        baseline_finish = parse_iso_datetime(get_text(elem, "BaselineFinish"))

        # Duration
        duration_str = get_text(elem, "Duration", default="PT0H0M0S")
        duration = parse_mspdi_duration(duration_str)

        actual_duration_str = get_text(elem, "ActualDuration", default="PT0H0M0S")
        actual_duration = parse_mspdi_duration(actual_duration_str)

        # Progress
        percent_complete = get_float(elem, "PercentComplete", default=0.0)
        percent_work_complete = get_float(elem, "PercentWorkComplete", default=0.0)

        # Status from percent complete
        status = get_task_status_from_percent(percent_complete)

        # Flags
        is_milestone = get_bool(elem, "Milestone")
        is_critical = get_bool(elem, "Critical")
        is_summary = get_bool(elem, "Summary")

        # Constraint
        constraint_type_int = get_int(elem, "ConstraintType", default=0)
        constraint_type = MSPDI_CONSTRAINT_TYPE_MAP.get(constraint_type_int)
        constraint_date = parse_iso_datetime(get_text(elem, "ConstraintDate"))

        # Work (in minutes in MSPDI, convert to hours)
        work_minutes = get_float(elem, "Work", default=0.0)
        work = Duration(work_minutes / 60.0, "hours") if work_minutes > 0 else None

        actual_work_minutes = get_float(elem, "ActualWork", default=0.0)
        actual_work = (
            Duration(actual_work_minutes / 60.0, "hours")
            if actual_work_minutes > 0
            else None
        )

        # Cost
        cost_value = get_float(elem, "Cost", default=0.0)
        cost = Money(Decimal(str(cost_value)), DEFAULT_CURRENCY) if cost_value > 0 else None

        actual_cost_value = get_float(elem, "ActualCost", default=0.0)
        actual_cost = (
            Money(Decimal(str(actual_cost_value)), DEFAULT_CURRENCY)
            if actual_cost_value > 0
            else None
        )

        # Priority
        priority = get_int(elem, "Priority", default=500)

        # Source info
        source = SourceInfo(
            tool=self.source_tool,
            tool_version="",
            original_id=uid_str,
        )

        return Task(
            id=task_id,
            name=name,
            source=source,
            wbs_code=wbs_code,
            parent_id=parent_id,
            outline_level=outline_level,
            start_date=start_date,
            finish_date=finish_date,
            duration=duration,
            percent_complete=percent_complete,
            status=status,
            is_milestone=is_milestone,
            is_critical=is_critical,
            is_summary=is_summary,
            constraint_type=constraint_type,
            constraint_date=constraint_date,
            actual_start=actual_start,
            actual_finish=actual_finish,
            actual_duration=actual_duration,
            budgeted_work=work,
            actual_work=actual_work,
            budgeted_cost=cost,
            actual_cost=actual_cost,
            notes=notes,
        )

    def _parse_resources(self, root: etree._Element) -> list[Resource]:
        """Parse all Resource elements.

        Args:
            root: Project root element

        Returns:
            List of parsed Resource models
        """
        resources: list[Resource] = []
        resources_element = root.find("Resources")
        if resources_element is None:
            return resources

        for resource_elem in resources_element.findall("Resource"):
            resource = self._parse_resource(resource_elem)
            if resource is not None:
                resources.append(resource)

        return resources

    def _parse_resource(self, elem: etree._Element) -> Optional[Resource]:
        """Parse single Resource element.

        Args:
            elem: Resource XML element

        Returns:
            Parsed Resource or None if invalid
        """
        # Get resource UID (required)
        uid_str = get_text(elem, "UID")
        if not uid_str:
            return None

        # Generate resource UUID
        resource_id = generate_uuid_from_source(self.source_tool, uid_str)

        # Basic fields
        name = get_text(elem, "Name", default="Untitled Resource")
        email = get_text(elem, "EmailAddress")

        # Resource type
        type_int = get_int(elem, "Type", default=1)  # Default to Work
        resource_type = MSPDI_RESOURCE_TYPE_MAP.get(type_int)

        # Availability
        max_units = get_float(elem, "MaxUnits", default=1.0)  # 1.0 = 100%

        # Cost
        cost_per_use_value = get_float(elem, "CostPerUse", default=0.0)
        cost_per_use = (
            Money(Decimal(str(cost_per_use_value)), DEFAULT_CURRENCY)
            if cost_per_use_value > 0
            else None
        )

        standard_rate_value = get_float(elem, "StandardRate", default=0.0)
        standard_rate = (
            Money(Decimal(str(standard_rate_value)), DEFAULT_CURRENCY)
            if standard_rate_value > 0
            else None
        )

        # Source info
        source = SourceInfo(
            tool=self.source_tool,
            tool_version="",
            original_id=uid_str,
        )

        return Resource(
            id=resource_id,
            name=name,
            source=source,
            resource_type=resource_type,
            email=email,
            max_units=max_units,
            cost_per_use=cost_per_use,
            standard_rate=standard_rate,
        )

    def _parse_assignments(self, root: etree._Element) -> list[Assignment]:
        """Parse all Assignment elements.

        Args:
            root: Project root element

        Returns:
            List of parsed Assignment models
        """
        assignments: list[Assignment] = []
        assignments_element = root.find("Assignments")
        if assignments_element is None:
            return assignments

        for assignment_elem in assignments_element.findall("Assignment"):
            assignment = self._parse_assignment(assignment_elem)
            if assignment is not None:
                assignments.append(assignment)

        return assignments

    def _parse_assignment(self, elem: etree._Element) -> Optional[Assignment]:
        """Parse single Assignment element.

        Args:
            elem: Assignment XML element

        Returns:
            Parsed Assignment or None if invalid
        """
        # Get assignment UID (required)
        uid_str = get_text(elem, "UID")
        if not uid_str:
            return None

        # Get task and resource UIDs
        task_uid = get_text(elem, "TaskUID")
        resource_uid = get_text(elem, "ResourceUID")

        if not task_uid or not resource_uid:
            return None

        # Generate UUIDs
        assignment_id = generate_uuid_from_source(self.source_tool, uid_str)
        task_id = generate_uuid_from_source(self.source_tool, task_uid)
        resource_id = generate_uuid_from_source(self.source_tool, resource_uid)

        # Units (percentage, 1.0 = 100%)
        units = get_float(elem, "Units", default=1.0)

        # Work (in minutes in MSPDI)
        work_minutes = get_float(elem, "Work", default=0.0)
        work = Duration(work_minutes / 60.0, "hours") if work_minutes > 0 else None

        actual_work_minutes = get_float(elem, "ActualWork", default=0.0)
        actual_work = (
            Duration(actual_work_minutes / 60.0, "hours")
            if actual_work_minutes > 0
            else None
        )

        # Cost
        cost_value = get_float(elem, "Cost", default=0.0)
        cost = Money(Decimal(str(cost_value)), DEFAULT_CURRENCY) if cost_value > 0 else None

        actual_cost_value = get_float(elem, "ActualCost", default=0.0)
        actual_cost = (
            Money(Decimal(str(actual_cost_value)), DEFAULT_CURRENCY)
            if actual_cost_value > 0
            else None
        )

        # Source info
        source = SourceInfo(
            tool=self.source_tool,
            tool_version="",
            original_id=uid_str,
        )

        return Assignment(
            id=assignment_id,
            task_id=task_id,
            resource_id=resource_id,
            source=source,
            units=units,
            budgeted_work=work,
            actual_work=actual_work,
            budgeted_cost=cost,
            actual_cost=actual_cost,
        )

    def _parse_dependencies(self, root: etree._Element) -> list[Dependency]:
        """Parse task dependencies from PredecessorLink elements.

        Args:
            root: Project root element

        Returns:
            List of parsed Dependency models
        """
        dependencies: list[Dependency] = []
        tasks_element = root.find("Tasks")
        if tasks_element is None:
            return dependencies

        for task_elem in tasks_element.findall("Task"):
            task_uid = get_text(task_elem, "UID")
            if not task_uid:
                continue

            successor_id = generate_uuid_from_source(self.source_tool, task_uid)

            # Check for PredecessorLink elements
            for pred_elem in task_elem.findall("PredecessorLink"):
                predecessor_uid = get_text(pred_elem, "PredecessorUID")
                if not predecessor_uid:
                    continue

                predecessor_id = generate_uuid_from_source(
                    self.source_tool, predecessor_uid
                )

                # Dependency type
                type_int = get_int(pred_elem, "Type", default=1)  # Default to FS
                dependency_type = MSPDI_DEPENDENCY_TYPE_MAP.get(type_int)

                # Lag (in minutes in MSPDI, stored as PT format)
                lag_minutes = get_float(pred_elem, "LinkLag", default=0.0)
                lag = (
                    Duration(lag_minutes / 60.0, "hours") if lag_minutes != 0 else None
                )

                # Source info
                source = SourceInfo(
                    tool=self.source_tool,
                    tool_version="",
                    original_id=f"{predecessor_uid}-{task_uid}",
                )

                # Generate dependency UUID from both task UIDs
                dependency_id = generate_uuid_from_source(
                    self.source_tool,
                    f"dep-{predecessor_uid}-{task_uid}",
                )

                dependencies.append(
                    Dependency(
                        id=dependency_id,
                        predecessor_id=predecessor_id,
                        successor_id=successor_id,
                        source=source,
                        dependency_type=dependency_type,
                        lag=lag,
                    )
                )

        return dependencies

    def _parse_calendars(self, root: etree._Element) -> list[Calendar]:
        """Parse all Calendar elements.

        Args:
            root: Project root element

        Returns:
            List of parsed Calendar models
        """
        calendars: list[Calendar] = []
        calendars_element = root.find("Calendars")
        if calendars_element is None:
            return calendars

        for calendar_elem in calendars_element.findall("Calendar"):
            calendar = self._parse_calendar(calendar_elem)
            if calendar is not None:
                calendars.append(calendar)

        return calendars

    def _parse_calendar(self, elem: etree._Element) -> Optional[Calendar]:
        """Parse single Calendar element.

        Args:
            elem: Calendar XML element

        Returns:
            Parsed Calendar or None if invalid
        """
        # Get calendar UID (required)
        uid_str = get_text(elem, "UID")
        if not uid_str:
            return None

        # Generate calendar UUID
        calendar_id = generate_uuid_from_source(self.source_tool, uid_str)

        # Basic fields
        name = get_text(elem, "Name", default="Standard")

        # Source info
        source = SourceInfo(
            tool=self.source_tool,
            tool_version="",
            original_id=uid_str,
        )

        # For now, use default working days (Mon-Fri)
        # Full calendar parsing with WeekDays and Exceptions could be added later
        working_days = [0, 1, 2, 3, 4]  # Monday to Friday

        return Calendar(
            id=calendar_id,
            name=name,
            source=source,
            working_days=working_days,
        )
