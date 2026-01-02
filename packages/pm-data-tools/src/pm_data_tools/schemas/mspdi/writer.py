"""MSPDI XML writer for Microsoft Project files.

This module provides writing functionality to convert canonical project
management data models into MSPDI (Microsoft Project Data Interchange) XML files.
"""

from pathlib import Path
from typing import Optional

from lxml import etree

from pm_data_tools.models import (
    Project,
    Task,
    Resource,
    Assignment,
    Dependency,
    Calendar,
)
from pm_data_tools.utils.xml_helpers import write_xml_string
from pm_data_tools.utils.dates import format_iso_datetime, format_mspdi_duration

from .constants import (
    MSPDI_NAMESPACE,
    CONSTRAINT_TYPE_TO_MSPDI,
    DEPENDENCY_TYPE_TO_MSPDI,
    RESOURCE_TYPE_TO_MSPDI,
    mspdi_bool,
)


class MspdiWriter:
    """Writer for MSPDI XML files.

    Converts canonical PM data model into Microsoft Project XML (MSPDI format).
    Supports full project structure including tasks, resources, assignments,
    dependencies, and calendars.
    """

    def __init__(self) -> None:
        """Initialise MSPDI writer."""
        self.namespace = f"{{{MSPDI_NAMESPACE}}}"

    def write_file(self, project: Project, file_path: str | Path) -> None:
        """Write Project model to MSPDI XML file.

        Args:
            project: Project model to write
            file_path: Output file path
        """
        xml_bytes = self.write_string(project)
        output_path = Path(file_path)
        output_path.write_bytes(xml_bytes)

    def write_string(self, project: Project) -> bytes:
        """Write Project model to MSPDI XML string.

        Args:
            project: Project model to write

        Returns:
            MSPDI XML as bytes
        """
        root = self._build_project(project)
        return write_xml_string(root)

    def _build_project(self, project: Project) -> etree._Element:
        """Build Project XML element from Project model.

        Args:
            project: Project model

        Returns:
            Project XML element
        """
        project_elem = etree.Element(
            f"{self.namespace}Project",
            nsmap={None: MSPDI_NAMESPACE},
        )

        # Basic metadata
        self._add_element(project_elem, "Name", project.name)
        self._add_element(project_elem, "Title", project.description or "")
        self._add_element(project_elem, "Manager", project.project_manager or "")
        self._add_element(project_elem, "Company", project.department or "")

        # Dates
        if project.start_date:
            self._add_element(
                project_elem, "StartDate", format_iso_datetime(project.start_date)
            )
        if project.finish_date:
            self._add_element(
                project_elem, "FinishDate", format_iso_datetime(project.finish_date)
            )
        if project.status_date:
            self._add_element(
                project_elem, "StatusDate", format_iso_datetime(project.status_date)
            )

        # Currency
        self._add_element(project_elem, "CurrencyCode", "GBP")

        # Source info
        self._add_element(project_elem, "UID", project.source.original_id)
        self._add_element(project_elem, "SaveVersion", project.source.tool_version)

        # Custom fields
        for custom_field in project.custom_fields:
            if custom_field.name == "author":
                self._add_element(project_elem, "Author", str(custom_field.value))
            elif custom_field.name == "subject":
                self._add_element(project_elem, "Subject", str(custom_field.value))

        # Tasks
        if project.tasks:
            tasks_elem = etree.SubElement(project_elem, "Tasks")
            for task in project.tasks:
                self._build_task(tasks_elem, task, project)

        # Resources
        if project.resources:
            resources_elem = etree.SubElement(project_elem, "Resources")
            for resource in project.resources:
                self._build_resource(resources_elem, resource)

        # Assignments
        if project.assignments:
            assignments_elem = etree.SubElement(project_elem, "Assignments")
            for assignment in project.assignments:
                self._build_assignment(assignments_elem, assignment, project)

        # Calendars
        if project.calendars:
            calendars_elem = etree.SubElement(project_elem, "Calendars")
            for calendar in project.calendars:
                self._build_calendar(calendars_elem, calendar)

        return project_elem

    def _build_task(
        self, parent: etree._Element, task: Task, project: Project
    ) -> None:
        """Build Task XML element.

        Args:
            parent: Parent Tasks element
            task: Task model
            project: Parent project for dependency lookup
        """
        task_elem = etree.SubElement(parent, "Task")

        # Identity
        self._add_element(task_elem, "UID", task.source.original_id)
        self._add_element(task_elem, "Name", task.name)

        # WBS and hierarchy
        if task.wbs_code:
            self._add_element(task_elem, "WBS", task.wbs_code)
        self._add_element(task_elem, "OutlineLevel", str(task.outline_level))

        # Parent task
        if task.parent_id:
            parent_task = next(
                (t for t in project.tasks if t.id == task.parent_id), None
            )
            if parent_task:
                self._add_element(
                    task_elem, "OutlineParent", parent_task.source.original_id
                )

        # Dates
        if task.start_date:
            self._add_element(task_elem, "Start", format_iso_datetime(task.start_date))
        if task.finish_date:
            self._add_element(
                task_elem, "Finish", format_iso_datetime(task.finish_date)
            )
        if task.actual_start:
            self._add_element(
                task_elem, "ActualStart", format_iso_datetime(task.actual_start)
            )
        if task.actual_finish:
            self._add_element(
                task_elem, "ActualFinish", format_iso_datetime(task.actual_finish)
            )

        # Duration
        if task.duration:
            self._add_element(
                task_elem, "Duration", format_mspdi_duration(task.duration)
            )
        if task.actual_duration:
            self._add_element(
                task_elem, "ActualDuration", format_mspdi_duration(task.actual_duration)
            )

        # Progress
        self._add_element(task_elem, "PercentComplete", str(int(task.percent_complete)))

        # Flags
        self._add_element(task_elem, "Milestone", mspdi_bool(task.is_milestone))
        self._add_element(task_elem, "Critical", mspdi_bool(task.is_critical))
        self._add_element(task_elem, "Summary", mspdi_bool(task.is_summary))

        # Constraint
        if task.constraint_type:
            constraint_int = CONSTRAINT_TYPE_TO_MSPDI.get(task.constraint_type, 0)
            self._add_element(task_elem, "ConstraintType", str(constraint_int))
        if task.constraint_date:
            self._add_element(
                task_elem, "ConstraintDate", format_iso_datetime(task.constraint_date)
            )

        # Work (convert hours to minutes for MSPDI)
        if task.budgeted_work:
            work_minutes = task.budgeted_work.to_hours() * 60.0
            self._add_element(task_elem, "Work", str(int(work_minutes)))
        if task.actual_work:
            actual_work_minutes = task.actual_work.to_hours() * 60.0
            self._add_element(task_elem, "ActualWork", str(int(actual_work_minutes)))

        # Cost
        if task.budgeted_cost:
            self._add_element(task_elem, "Cost", str(float(task.budgeted_cost.amount)))
        if task.actual_cost:
            self._add_element(task_elem, "ActualCost", str(float(task.actual_cost.amount)))

        # Notes
        if task.notes:
            self._add_element(task_elem, "Notes", task.notes)

        # Predecessor links
        predecessors = [
            dep for dep in project.dependencies if dep.successor_id == task.id
        ]
        for dep in predecessors:
            pred_task = next(
                (t for t in project.tasks if t.id == dep.predecessor_id), None
            )
            if pred_task:
                pred_link_elem = etree.SubElement(task_elem, "PredecessorLink")
                self._add_element(
                    pred_link_elem, "PredecessorUID", pred_task.source.original_id
                )
                if dep.dependency_type:
                    type_int = DEPENDENCY_TYPE_TO_MSPDI.get(dep.dependency_type, 1)
                    self._add_element(pred_link_elem, "Type", str(type_int))
                if dep.lag:
                    lag_minutes = dep.lag.to_hours() * 60.0
                    self._add_element(pred_link_elem, "LinkLag", str(int(lag_minutes)))

    def _build_resource(self, parent: etree._Element, resource: Resource) -> None:
        """Build Resource XML element.

        Args:
            parent: Parent Resources element
            resource: Resource model
        """
        resource_elem = etree.SubElement(parent, "Resource")

        # Identity
        self._add_element(resource_elem, "UID", resource.source.original_id)
        self._add_element(resource_elem, "Name", resource.name)

        # Email
        if resource.email:
            self._add_element(resource_elem, "EmailAddress", resource.email)

        # Resource type
        if resource.resource_type:
            type_int = RESOURCE_TYPE_TO_MSPDI.get(resource.resource_type, 1)
            self._add_element(resource_elem, "Type", str(type_int))

        # Availability
        self._add_element(resource_elem, "MaxUnits", str(resource.max_units))

        # Cost
        if resource.cost_per_use:
            self._add_element(
                resource_elem, "CostPerUse", str(float(resource.cost_per_use.amount))
            )
        if resource.standard_rate:
            self._add_element(
                resource_elem, "StandardRate", str(float(resource.standard_rate.amount))
            )

    def _build_assignment(
        self, parent: etree._Element, assignment: Assignment, project: Project
    ) -> None:
        """Build Assignment XML element.

        Args:
            parent: Parent Assignments element
            assignment: Assignment model
            project: Parent project for task/resource lookup
        """
        assignment_elem = etree.SubElement(parent, "Assignment")

        # Identity
        self._add_element(assignment_elem, "UID", assignment.source.original_id)


        # Task and Resource references
        task = next((t for t in project.tasks if t.id == assignment.task_id), None)
        if task:
            self._add_element(assignment_elem, "TaskUID", task.source.original_id)

        resource = next((r for r in project.resources if r.id == assignment.resource_id), None)
        if resource:
            self._add_element(assignment_elem, "ResourceUID", resource.source.original_id)
        # Units
        self._add_element(assignment_elem, "Units", str(assignment.units))

        # Work (convert hours to minutes for MSPDI)
        if assignment.budgeted_work:
            work_minutes = assignment.budgeted_work.to_hours() * 60.0
            self._add_element(assignment_elem, "Work", str(int(work_minutes)))
        if assignment.actual_work:
            actual_work_minutes = assignment.actual_work.to_hours() * 60.0
            self._add_element(
                assignment_elem, "ActualWork", str(int(actual_work_minutes))
            )

        # Cost
        if assignment.budgeted_cost:
            self._add_element(
                assignment_elem, "Cost", str(float(assignment.budgeted_cost.amount))
            )
        if assignment.actual_cost:
            self._add_element(
                assignment_elem, "ActualCost", str(float(assignment.actual_cost.amount))
            )

    def _build_calendar(self, parent: etree._Element, calendar: Calendar) -> None:
        """Build Calendar XML element.

        Args:
            parent: Parent Calendars element
            calendar: Calendar model
        """
        calendar_elem = etree.SubElement(parent, "Calendar")

        # Identity
        self._add_element(calendar_elem, "UID", calendar.source.original_id)
        self._add_element(calendar_elem, "Name", calendar.name)

        # Base calendar flag
        is_base = "1" if calendar.base_calendar_id is None else "0"
        self._add_element(calendar_elem, "IsBaseCalendar", is_base)

    def _add_element(
        self, parent: etree._Element, tag: str, text: Optional[str]
    ) -> None:
        """Add a child element with text content.

        Args:
            parent: Parent element
            tag: Element tag name
            text: Text content (None values are skipped)
        """
        if text is not None:
            elem = etree.SubElement(parent, tag)
            elem.text = text
