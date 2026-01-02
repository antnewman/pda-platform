"""Parser for NISTA (Programme and Project Data Standard) format."""

import csv
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional, Union

from ...models import (
    CustomField,
    DeliveryConfidence,
    Money,
    Project,
    Resource,
    ResourceType,
    Risk,
    RiskCategory,
    RiskStatus,
    SourceInfo,
    Task,
    TaskStatus,
)
from ...utils.identifiers import generate_uuid_from_source
from .constants import (
    CATEGORY_MAPPINGS,
    CSV_COLUMN_MAPPINGS,
    DCA_MAPPINGS,
    FIELD_BENEFITS_BASELINE,
    FIELD_BENEFITS_FORECAST,
    FIELD_BENEFITS_NARRATIVE,
    FIELD_BENEFITS_NON_MONETISED,
    FIELD_BUDGET_NARRATIVE,
    FIELD_CATEGORY,
    FIELD_CUSTOM_FIELDS,
    FIELD_DCA_IPA,
    FIELD_DCA_SRO,
    FIELD_DEPARTMENT,
    FIELD_DESCRIPTION,
    FIELD_END_BASELINE,
    FIELD_END_FORECAST,
    FIELD_FY_BASELINE,
    FIELD_FY_FORECAST,
    FIELD_FY_VARIANCE,
    FIELD_IPA_COMMENTARY,
    FIELD_ISSUES,
    FIELD_METADATA,
    FIELD_MILESTONES,
    FIELD_PROJECT_ID,
    FIELD_PROJECT_NAME,
    FIELD_RISKS,
    FIELD_SCHEDULE_NARRATIVE,
    FIELD_SRO,
    FIELD_START_BASELINE,
    FIELD_START_FORECAST,
    FIELD_WLC_BASELINE,
    FIELD_WLC_FORECAST,
    FIELD_WLC_NARRATIVE,
)


class NISTAParser:
    """Parser for NISTA Programme and Project Data Standard.

    Supports multiple input formats:
    - JSON (native NISTA format)
    - CSV (GMPP legacy format with column mapping)
    - Excel (via openpyxl, treated as CSV)

    Mapping Strategy:
    - Each NISTA project → One Project in canonical model
    - Project gets single summary task
    - DCA field → DeliveryConfidence enum
    - SRO → Resource (if structured) or string (if simple)
    - Whole Life Cost → Project.whole_life_cost
    - Benefits → Project.monetised_benefits
    - Milestones → Tasks with is_milestone=True
    - Risks → Risk objects
    """

    def __init__(self, source_tool: str = "nista", source_version: str = "v1.0"):
        """Initialize NISTA parser.

        Args:
            source_tool: Source tool identifier (default: "nista")
            source_version: Source version (default: "v1.0")
        """
        self.source_tool = source_tool
        self.source_version = source_version

    def parse_file(self, file_path: Union[str, Path]) -> Union[Project, list[Project]]:
        """Parse NISTA data file (auto-detects format).

        Args:
            file_path: Path to file (.json, .csv, or .xlsx)

        Returns:
            Single Project (for JSON) or list of Projects (for CSV/Excel)

        Raises:
            ValueError: If file format is not supported
        """
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()

        if suffix == ".json":
            return self.parse_json_file(file_path)
        elif suffix == ".csv":
            return self.parse_csv_file(file_path)
        elif suffix in [".xlsx", ".xls"]:
            return self.parse_excel_file(file_path)
        else:
            raise ValueError(
                f"Unsupported file format: {suffix}. "
                f"Supported formats: .json, .csv, .xlsx, .xls"
            )

    def parse_json_file(self, file_path: Path) -> Project:
        """Parse NISTA JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed Project
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return self.parse_json(data)

    def parse_csv_file(self, file_path: Path) -> list[Project]:
        """Parse NISTA/GMPP CSV file.

        Args:
            file_path: Path to CSV file

        Returns:
            List of parsed Projects (one per row)
        """
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return self.parse_csv(list(reader))

    def parse_excel_file(self, file_path: Path) -> list[Project]:
        """Parse NISTA/GMPP Excel file.

        Args:
            file_path: Path to Excel file

        Returns:
            List of parsed Projects

        Raises:
            ImportError: If openpyxl is not installed
        """
        try:
            import openpyxl
        except ImportError:
            raise ImportError(
                "openpyxl is required for Excel support. "
                "Install with: pip install openpyxl"
            )

        workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet = workbook.active

        # Extract rows as dictionaries
        rows = []
        headers = None
        for row in sheet.iter_rows(values_only=True):
            if headers is None:
                headers = [str(cell) if cell is not None else "" for cell in row]
            else:
                row_dict = {
                    headers[i]: (cell if cell is not None else "")
                    for i, cell in enumerate(row)
                    if i < len(headers)
                }
                rows.append(row_dict)

        workbook.close()
        return self.parse_csv(rows)  # Reuse CSV parser

    def parse_json(self, data: dict[str, Any]) -> Project:
        """Parse NISTA JSON data to canonical Project.

        Args:
            data: NISTA JSON data dictionary

        Returns:
            Canonical Project
        """
        # Extract core fields
        project_id_str = data.get(FIELD_PROJECT_ID, "")
        project_name = data.get(FIELD_PROJECT_NAME, "Unnamed Project")

        # Generate UUID
        project_id = generate_uuid_from_source(
            self.source_tool, project_id_str or project_name
        )

        # Parse dates
        start_date = self._parse_date(data.get(FIELD_START_BASELINE))
        end_date = self._parse_date(data.get(FIELD_END_BASELINE))
        start_forecast = self._parse_date(data.get(FIELD_START_FORECAST))
        end_forecast = self._parse_date(data.get(FIELD_END_FORECAST))

        # Use forecast if available, otherwise baseline
        final_start = start_forecast or start_date
        final_end = end_forecast or end_date

        # Parse DCA
        dca_ipa_str = data.get(FIELD_DCA_IPA, "")
        dca_sro_str = data.get(FIELD_DCA_SRO, "")
        delivery_confidence = self._parse_dca(dca_ipa_str or dca_sro_str)

        # Parse financials
        wlc = self._parse_money_millions(
            data.get(FIELD_WLC_FORECAST) or data.get(FIELD_WLC_BASELINE)
        )
        benefits = self._parse_money_millions(
            data.get(FIELD_BENEFITS_FORECAST) or data.get(FIELD_BENEFITS_BASELINE)
        )

        # Parse SRO
        sro_data = data.get(FIELD_SRO)
        sro_name = None
        resources = []

        if isinstance(sro_data, dict):
            # Structured SRO object
            sro_name = sro_data.get("name")
            if sro_name:
                resource_id = generate_uuid_from_source(
                    self.source_tool, f"{project_id_str}:sro:{sro_name}"
                )
                resources.append(
                    Resource(
                        id=resource_id,
                        name=sro_name,
                        source=SourceInfo(
                            tool=self.source_tool,
                            tool_version=self.source_version,
                            original_id=f"sro:{sro_name}",
                        ),
                        resource_type=ResourceType.WORK,
                        email_address=sro_data.get("email"),
                        notes=sro_data.get("title"),
                    )
                )
        elif isinstance(sro_data, str):
            # Simple string SRO name
            sro_name = sro_data

        # Parse category
        category = self._normalize_category(data.get(FIELD_CATEGORY))

        # Create summary task
        task_id = generate_uuid_from_source(self.source_tool, f"{project_name}:task")
        summary_task = Task(
            id=task_id,
            name=project_name,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version=self.source_version,
                original_id=project_id_str,
            ),
            is_summary=True,
            start_date=final_start,
            finish_date=final_end,
            status=TaskStatus.IN_PROGRESS,
            notes=data.get(FIELD_DESCRIPTION),
        )
        tasks = [summary_task]

        # Parse milestones
        milestones_data = data.get(FIELD_MILESTONES, [])
        for i, milestone in enumerate(milestones_data):
            milestone_task = self._parse_milestone(milestone, i, project_id_str)
            if milestone_task:
                tasks.append(milestone_task)

        # Parse risks
        risks_data = data.get(FIELD_RISKS, {})
        risks = self._parse_risks(risks_data, project_id_str)

        # Parse custom fields
        custom_fields = []
        custom_data = data.get(FIELD_CUSTOM_FIELDS, {})
        for key, value in custom_data.items():
            custom_fields.append(
                CustomField(name=key, value=str(value), value_type=type(value).__name__)
            )

        # Build project
        project = Project(
            id=project_id,
            name=project_name,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version=self.source_version,
                original_id=project_id_str,
            ),
            description=data.get(FIELD_DESCRIPTION),
            category=category,
            department=data.get(FIELD_DEPARTMENT),
            start_date=final_start,
            finish_date=final_end,
            delivery_confidence=delivery_confidence,
            whole_life_cost=wlc,
            monetised_benefits=benefits,
            senior_responsible_owner=sro_name,
            tasks=tasks,
            resources=resources,
            assignments=[],
            dependencies=[],
            calendars=[],
            risks=risks,
            custom_fields=custom_fields,
        )

        return project

    def parse_csv(self, rows: list[dict[str, Any]]) -> list[Project]:
        """Parse NISTA/GMPP CSV data to canonical Projects.

        Args:
            rows: List of CSV row dictionaries

        Returns:
            List of canonical Projects (one per row)
        """
        projects = []

        for row in rows:
            # Normalize column names using CSV_COLUMN_MAPPINGS
            normalized_row = self._normalize_csv_row(row)

            # Parse as JSON (reuse JSON parser logic)
            try:
                project = self.parse_json(normalized_row)
                if project:
                    projects.append(project)
            except Exception:
                # Skip invalid rows
                continue

        return projects

    def _normalize_csv_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """Normalize CSV row column names to NISTA field names.

        Args:
            row: CSV row dictionary with original column names

        Returns:
            Dictionary with normalized NISTA field names
        """
        normalized = {}

        for col_name, value in row.items():
            # Clean up column name
            col_name_clean = col_name.strip()

            # Check if we have a mapping
            if col_name_clean in CSV_COLUMN_MAPPINGS:
                nista_field = CSV_COLUMN_MAPPINGS[col_name_clean]
                normalized[nista_field] = value
            else:
                # Keep unmapped fields as custom fields
                if "custom_fields" not in normalized:
                    normalized["custom_fields"] = {}
                normalized["custom_fields"][col_name_clean] = value

        return normalized

    def _parse_milestone(
        self, milestone_data: dict[str, Any], index: int, project_id: str
    ) -> Optional[Task]:
        """Parse milestone data to Task.

        Args:
            milestone_data: Milestone dictionary
            index: Milestone index
            project_id: Parent project ID

        Returns:
            Task object or None
        """
        name = milestone_data.get("name")
        if not name:
            return None

        baseline_date = self._parse_date(milestone_data.get("baseline_date"))
        forecast_date = self._parse_date(milestone_data.get("forecast_date"))
        actual_date = self._parse_date(milestone_data.get("actual_date"))

        # Determine task status
        status_str = milestone_data.get("status", "")
        status = TaskStatus.NOT_STARTED
        if status_str == "Completed" or actual_date:
            status = TaskStatus.COMPLETED
        elif status_str == "In Progress":
            status = TaskStatus.IN_PROGRESS

        # Use actual > forecast > baseline for dates
        final_date = actual_date or forecast_date or baseline_date

        task_id = generate_uuid_from_source(
            self.source_tool, f"{project_id}:milestone:{index}:{name}"
        )

        return Task(
            id=task_id,
            name=name,
            source=SourceInfo(
                tool=self.source_tool,
                tool_version=self.source_version,
                original_id=f"milestone:{index}",
            ),
            is_milestone=True,
            start_date=final_date,
            finish_date=final_date,
            status=status,
        )

    def _parse_risks(
        self, risks_data: dict[str, Any], project_id: str
    ) -> list[Risk]:
        """Parse risks summary to Risk objects.

        Args:
            risks_data: Risks summary dictionary
            project_id: Parent project ID

        Returns:
            List of Risk objects
        """
        risks = []
        top_risks = risks_data.get("top_risks", [])

        for i, risk_data in enumerate(top_risks):
            description = risk_data.get("description")
            if not description:
                continue

            # Map severity string to probability/impact scores (1-5 scale)
            severity_str = risk_data.get("severity", "Medium")
            probability, impact = 3, 3  # Default to medium (3 out of 5)
            if severity_str == "High":
                probability, impact = 4, 4  # High = 16/25 score
            elif severity_str == "Low":
                probability, impact = 2, 2  # Low = 4/25 score

            risk_id = generate_uuid_from_source(
                self.source_tool, f"{project_id}:risk:{i}:{description[:50]}"
            )

            risks.append(
                Risk(
                    id=risk_id,
                    name=description[:100],  # Name instead of title
                    description=description,
                    source=SourceInfo(
                        tool=self.source_tool,
                        tool_version=self.source_version,
                        original_id=f"risk:{i}",
                    ),
                    category=RiskCategory.TECHNICAL,  # Default category
                    status=RiskStatus.IDENTIFIED,
                    probability=probability,
                    impact=impact,
                    mitigation=risk_data.get("mitigation"),
                )
            )

        return risks

    def _parse_date(self, date_str: Optional[Union[str, datetime]]) -> Optional[datetime]:
        """Parse date string to datetime.

        Args:
            date_str: Date string or datetime object

        Returns:
            Parsed datetime or None
        """
        if not date_str:
            return None

        if isinstance(date_str, datetime):
            return date_str

        # Try ISO 8601 first (NISTA standard)
        formats = [
            "%Y-%m-%d",  # ISO 8601
            "%d/%m/%Y",  # UK format
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d %B %Y",  # e.g. "1 January 2025"
            "%B %Y",  # e.g. "January 2025" (day defaults to 1st)
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str).strip(), fmt)
            except ValueError:
                continue

        return None

    def _parse_money_millions(
        self, amount: Optional[Union[str, int, float, Decimal]]
    ) -> Optional[Money]:
        """Parse money amount in millions to Money object.

        Args:
            amount: Amount in £ millions (can be string, int, float, or Decimal)

        Returns:
            Money object or None
        """
        if amount is None or amount == "":
            return None

        try:
            if isinstance(amount, str):
                # Clean up string
                clean_str = amount.strip().replace(",", "").replace(" ", "")
                clean_str = clean_str.replace("£", "").replace("GBP", "")

                # Handle 'm' or 'million' suffix
                if "m" in clean_str.lower() or "million" in clean_str.lower():
                    clean_str = clean_str.lower().replace("m", "").replace("illion", "")

                value = Decimal(clean_str)
            else:
                value = Decimal(str(amount))

            # Convert millions to pounds
            amount_gbp = value * Decimal(1_000_000)
            return Money(amount=amount_gbp, currency="GBP")

        except (ValueError, ArithmeticError):
            return None

    def _parse_dca(self, dca_str: Optional[str]) -> Optional[DeliveryConfidence]:
        """Parse DCA string to DeliveryConfidence enum.

        Args:
            dca_str: DCA string (Green/Amber/Red/Exempt)

        Returns:
            DeliveryConfidence enum or None
        """
        if not dca_str:
            return None

        normalized = DCA_MAPPINGS.get(dca_str.strip(), "")

        if normalized == "Green":
            return DeliveryConfidence.GREEN
        elif normalized == "Amber":
            return DeliveryConfidence.AMBER
        elif normalized == "Red":
            return DeliveryConfidence.RED
        elif normalized == "Exempt":
            return DeliveryConfidence.EXEMPT

        return None

    def _normalize_category(self, category_str: Optional[str]) -> Optional[str]:
        """Normalize project category string.

        Args:
            category_str: Category string

        Returns:
            Normalized category or None
        """
        if not category_str:
            return None

        return CATEGORY_MAPPINGS.get(category_str.strip(), category_str.strip())
