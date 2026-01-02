"""Parser for GMPP (Government Major Projects Portfolio) CSV data."""

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from ...models import (
    DeliveryConfidence,
    Money,
    Project,
    Resource,
    ResourceType,
    SourceInfo,
    Task,
    TaskStatus,
)
from ...utils.identifiers import generate_uuid_from_source
from .constants import (
    COLUMN_DCA,
    COLUMN_DEPARTMENT,
    COLUMN_END_DATE,
    COLUMN_PROJECT_NAME,
    COLUMN_SRO,
    COLUMN_START_DATE,
    COLUMN_WHOLE_LIFE_COST,
    DCA_TO_DELIVERY_CONFIDENCE,
)


class GMPPParser:
    """Parser for GMPP CSV data.

    GMPP (Government Major Projects Portfolio) data represents UK government
    major projects. Each row in the CSV represents a project.

    Mapping:
    - Each CSV row → One Project
    - Project gets single summary task
    - DCA field → DeliveryConfidence
    - SRO → Resource
    - Whole Life Cost → Project budget
    """

    def __init__(self):
        """Initialise parser."""
        self.source_tool = "gmpp"

    def parse_file(self, file_path: Path) -> list[Project]:
        """Parse GMPP CSV file.

        Args:
            file_path: Path to CSV file

        Returns:
            List of parsed Projects (one per row)
        """
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return self.parse(list(reader))

    def parse(self, rows: list[dict[str, Any]]) -> list[Project]:
        """Parse GMPP CSV data to canonical Projects.

        Args:
            rows: List of CSV row dictionaries

        Returns:
            List of canonical Projects
        """
        projects: list[Project] = []

        for row in rows:
            project = self._parse_row(row)
            if project:
                projects.append(project)

        return projects

    def _parse_row(self, row: dict[str, Any]) -> Optional[Project]:
        """Parse single GMPP CSV row to Project.

        Args:
            row: CSV row dictionary

        Returns:
            Project or None
        """
        # Extract project name
        project_name = self._find_value(row, COLUMN_PROJECT_NAME)
        if not project_name:
            return None

        # Generate project ID from name
        project_id = generate_uuid_from_source(self.source_tool, project_name)

        # Extract DCA
        dca_str = self._find_value(row, COLUMN_DCA)
        delivery_confidence = DCA_TO_DELIVERY_CONFIDENCE.get(
            dca_str or "", DeliveryConfidence.AMBER
        )

        # Extract dates
        start_date = self._parse_date(self._find_value(row, COLUMN_START_DATE))
        end_date = self._parse_date(self._find_value(row, COLUMN_END_DATE))

        # Extract department
        department = self._find_value(row, COLUMN_DEPARTMENT)

        # Extract Whole Life Cost
        wlc_str = self._find_value(row, COLUMN_WHOLE_LIFE_COST)
        whole_life_cost = self._parse_money(wlc_str)

        # Create single summary task for the project
        task_id = generate_uuid_from_source(self.source_tool, f"{project_name}:task")
        task = Task(
            id=task_id,
            name=project_name,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version="v1",
                original_id=project_name,
            ),
            is_summary=True,
            start_date=start_date,
            finish_date=end_date,
            status=TaskStatus.IN_PROGRESS,
        )

        # Extract SRO as resource
        resources: list[Resource] = []
        sro_name = self._find_value(row, COLUMN_SRO)
        if sro_name:
            resource_id = generate_uuid_from_source(
                self.source_tool, f"{project_name}:sro:{sro_name}"
            )
            resources.append(
                Resource(
                    id=resource_id,
                    name=sro_name,
                    source=SourceInfo(
                        tool=self.source_tool,
                        tool_version="v1",
                        original_id=f"sro:{sro_name}",
                    ),
                    resource_type=ResourceType.WORK,
                )
            )

        # Build project
        project = Project(
            id=project_id,
            name=project_name,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version="v1",
                original_id=project_name,
            ),
            delivery_confidence=delivery_confidence,
            department=department,
            whole_life_cost=whole_life_cost,
            senior_responsible_owner=sro_name,
            tasks=[task],
            resources=resources,
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        return project

    def _find_value(self, row: dict[str, Any], column_names: list[str]) -> Optional[str]:
        """Find value in row by trying multiple column name variants.

        Args:
            row: CSV row dictionary
            column_names: List of possible column names to try

        Returns:
            Value or None
        """
        for col_name in column_names:
            if col_name in row and row[col_name]:
                value = str(row[col_name]).strip()
                if value:
                    return value
        return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime.

        Args:
            date_str: Date string

        Returns:
            Parsed datetime or None
        """
        if not date_str:
            return None

        # UK government typically uses DD/MM/YYYY
        formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d %B %Y",  # e.g. "1 January 2025"
            "%B %Y",  # e.g. "January 2025" (day defaults to 1st)
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _parse_money(self, amount_str: Optional[str]) -> Optional[Money]:
        """Parse money string to Money object.

        Args:
            amount_str: Amount string (e.g., "£1.5m", "1500000", "1.5 million")

        Returns:
            Money object or None
        """
        if not amount_str:
            return None

        # Clean up string
        clean_str = amount_str.strip().replace(",", "").replace(" ", "")

        # Remove currency symbols
        clean_str = clean_str.replace("£", "").replace("GBP", "")

        # Handle millions/billions notation
        multiplier = Decimal(1)
        if "m" in clean_str.lower() or "million" in amount_str.lower():
            multiplier = Decimal(1_000_000)
            clean_str = clean_str.lower().replace("m", "").replace("illion", "")
        elif "b" in clean_str.lower() or "billion" in amount_str.lower():
            multiplier = Decimal(1_000_000_000)
            clean_str = clean_str.lower().replace("b", "").replace("illion", "")

        try:
            value = Decimal(clean_str) * multiplier
            return Money(amount=value, currency="GBP")
        except (ValueError, ArithmeticError):
            return None
