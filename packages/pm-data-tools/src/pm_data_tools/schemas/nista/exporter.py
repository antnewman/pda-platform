"""Exporter for NISTA Programme and Project Data Standard format."""

import csv
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional, Union

from ...models import DeliveryConfidence, Project


class NISTAExporter:
    """Exporter for NISTA Programme and Project Data Standard.

    Exports canonical Project models to NISTA-compliant formats:
    - JSON (native NISTA format)
    - CSV (GMPP legacy format)
    - Excel (via openpyxl)

    Usage:
        exporter = NISTAExporter(version="1.0")
        nista_data = exporter.export(project)
        exporter.to_file(project, "output.json")
        exporter.to_csv(project, "output.csv")
    """

    def __init__(self, version: str = "1.0"):
        """Initialize NISTA exporter.

        Args:
            version: NISTA schema version (default: "1.0")
        """
        self.version = version

    def export(self, project: Project) -> dict[str, Any]:
        """Export Project to NISTA data dictionary.

        Args:
            project: Canonical Project model

        Returns:
            NISTA-compliant data dictionary
        """
        # Build NISTA data structure
        data: dict[str, Any] = {
            "project_id": str(project.id) if project.id else "",
            "project_name": project.name,
        }

        # Optional fields - only include if present
        if project.department:
            data["department"] = project.department

        if project.category:
            data["category"] = project.category

        if project.description:
            data["description"] = project.description

        # Delivery Confidence Assessment
        if project.delivery_confidence:
            dca_value = self._format_dca(project.delivery_confidence)
            data["delivery_confidence_assessment_ipa"] = dca_value
            # Assume IPA and SRO same if only one provided
            data["delivery_confidence_assessment_sro"] = dca_value

        # Senior Responsible Owner
        if project.senior_responsible_owner:
            data["senior_responsible_owner"] = {
                "name": project.senior_responsible_owner
            }

        # Dates
        if project.start_date:
            data["start_date_baseline"] = project.start_date.strftime("%Y-%m-%d")

        if project.finish_date:
            data["end_date_baseline"] = project.finish_date.strftime("%Y-%m-%d")

        # Financials (convert to £ millions)
        if project.whole_life_cost:
            wlc_millions = float(project.whole_life_cost.amount) / 1_000_000
            data["whole_life_cost_baseline"] = round(wlc_millions, 2)

        if project.monetised_benefits:
            benefits_millions = float(project.monetised_benefits.amount) / 1_000_000
            data["benefits_baseline"] = round(benefits_millions, 2)

        # Milestones
        milestones = []
        for task in project.tasks:
            if task.is_milestone:
                milestone = {
                    "name": task.name,
                }
                if task.start_date:
                    milestone["baseline_date"] = task.start_date.strftime("%Y-%m-%d")
                if task.finish_date and task.finish_date != task.start_date:
                    milestone["forecast_date"] = task.finish_date.strftime("%Y-%m-%d")

                # Status mapping
                status = "Not Started"
                if task.is_complete:
                    status = "Completed"
                elif task.percent_complete and task.percent_complete > 0:
                    status = "In Progress"

                milestone["status"] = status
                milestones.append(milestone)

        if milestones:
            data["milestones"] = milestones

        # Risks
        if project.risks:
            top_risks = []
            for risk in project.risks[:5]:  # Top 5 risks
                risk_data = {
                    "description": risk.description or risk.name,
                }

                # Map probability/impact to severity
                if risk.is_high_risk:
                    risk_data["severity"] = "High"
                elif risk.is_low_risk:
                    risk_data["severity"] = "Low"
                else:
                    risk_data["severity"] = "Medium"

                if risk.mitigation:
                    risk_data["mitigation"] = risk.mitigation

                top_risks.append(risk_data)

            data["risks_summary"] = {
                "total_count": len(project.risks),
                "high_count": len([r for r in project.risks if r.is_high_risk]),
                "medium_count": len([r for r in project.risks if r.is_medium_risk]),
                "low_count": len([r for r in project.risks if r.is_low_risk]),
                "top_risks": top_risks,
            }

        # Metadata
        data["metadata"] = {
            "schema_version": self.version,
            "last_updated": datetime.now().isoformat(),
        }

        return data

    def to_file(self, project: Project, file_path: Union[str, Path]) -> None:
        """Export Project to NISTA JSON file.

        Args:
            project: Canonical Project model
            file_path: Output file path (.json)
        """
        file_path = Path(file_path)
        data = self.export(project)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def to_csv(
        self, projects: Union[Project, list[Project]], file_path: Union[str, Path]
    ) -> None:
        """Export Project(s) to NISTA/GMPP CSV file.

        Args:
            projects: Single Project or list of Projects
            file_path: Output file path (.csv)
        """
        file_path = Path(file_path)

        # Normalize to list
        if isinstance(projects, Project):
            projects = [projects]

        # Define CSV columns (GMPP legacy format)
        columns = [
            "GMPP ID Number",
            "Project Name",
            "Department",
            "Annual Report Category",
            "Description / Aims",
            "IPA Delivery Confidence Assessment",
            "SRO Delivery Confidence Assessment",
            "Departmental commentary on actions planned or taken on the IPA RAG rating.",
            "Project - Start Date (Latest Approved Start Date)",
            "Project - End Date (Latest Approved End Date)",
            "Departmental narrative on schedule, including any deviation from planned schedule (if necessary)",
            "Financial Year Baseline (£m) (including Non-Government Costs)",
            "Financial Year Forecast (£m) (including Non-Government Costs)",
            "Financial Year Variance (%)",
            "Departmental narrative on budget/forecast variance for 2023/24 (if variance is more than 5%)",
            "TOTAL Baseline Whole Life Costs (£m) (including Non-Government Costs)",
            "Departmental Narrative on Budgeted Whole Life Costs",
            "TOTAL Baseline Benefits (£m)",
            "Departmental Narrative on Budgeted Benefits",
        ]

        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()

            for project in projects:
                data = self.export(project)
                row = self._nista_to_csv_row(data)
                writer.writerow(row)

    def to_excel(
        self, projects: Union[Project, list[Project]], file_path: Union[str, Path]
    ) -> None:
        """Export Project(s) to NISTA/GMPP Excel file.

        Args:
            projects: Single Project or list of Projects
            file_path: Output file path (.xlsx)

        Raises:
            ImportError: If openpyxl is not installed
        """
        try:
            import openpyxl
        except ImportError:
            raise ImportError(
                "openpyxl is required for Excel export. "
                "Install with: pip install openpyxl"
            )

        file_path = Path(file_path)

        # Normalize to list
        if isinstance(projects, Project):
            projects = [projects]

        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "GMPP Data"

        # Define columns (same as CSV)
        columns = [
            "GMPP ID Number",
            "Project Name",
            "Department",
            "Annual Report Category",
            "Description / Aims",
            "IPA Delivery Confidence Assessment",
            "SRO Delivery Confidence Assessment",
            "Departmental commentary on actions planned or taken on the IPA RAG rating.",
            "Project - Start Date (Latest Approved Start Date)",
            "Project - End Date (Latest Approved End Date)",
            "Departmental narrative on schedule, including any deviation from planned schedule (if necessary)",
            "Financial Year Baseline (£m) (including Non-Government Costs)",
            "Financial Year Forecast (£m) (including Non-Government Costs)",
            "Financial Year Variance (%)",
            "Departmental narrative on budget/forecast variance for 2023/24 (if variance is more than 5%)",
            "TOTAL Baseline Whole Life Costs (£m) (including Non-Government Costs)",
            "Departmental Narrative on Budgeted Whole Life Costs",
            "TOTAL Baseline Benefits (£m)",
            "Departmental Narrative on Budgeted Benefits",
        ]

        # Write header
        ws.append(columns)

        # Write data rows
        for project in projects:
            data = self.export(project)
            row_dict = self._nista_to_csv_row(data)
            row_values = [row_dict.get(col, "") for col in columns]
            ws.append(row_values)

        # Save workbook
        wb.save(file_path)

    def _nista_to_csv_row(self, nista_data: dict[str, Any]) -> dict[str, str]:
        """Convert NISTA data dictionary to CSV row.

        Args:
            nista_data: NISTA data dictionary

        Returns:
            Dictionary mapping CSV column names to values
        """
        row: dict[str, str] = {}

        # Map NISTA fields to GMPP CSV columns
        row["GMPP ID Number"] = nista_data.get("project_id", "")
        row["Project Name"] = nista_data.get("project_name", "")
        row["Department"] = nista_data.get("department", "")
        row["Annual Report Category"] = nista_data.get("category", "")
        row["Description / Aims"] = nista_data.get("description", "")

        row["IPA Delivery Confidence Assessment"] = nista_data.get(
            "delivery_confidence_assessment_ipa", ""
        )
        row["SRO Delivery Confidence Assessment"] = nista_data.get(
            "delivery_confidence_assessment_sro", ""
        )

        row[
            "Departmental commentary on actions planned or taken on the IPA RAG rating."
        ] = nista_data.get("ipa_rating_commentary", "")

        row["Project - Start Date (Latest Approved Start Date)"] = nista_data.get(
            "start_date_baseline", ""
        )
        row["Project - End Date (Latest Approved End Date)"] = nista_data.get(
            "end_date_baseline", ""
        )

        row[
            "Departmental narrative on schedule, including any deviation from planned schedule (if necessary)"
        ] = nista_data.get("schedule_narrative", "")

        row["Financial Year Baseline (£m) (including Non-Government Costs)"] = str(
            nista_data.get("financial_year_baseline", "")
        )
        row["Financial Year Forecast (£m) (including Non-Government Costs)"] = str(
            nista_data.get("financial_year_forecast", "")
        )
        row["Financial Year Variance (%)"] = str(
            nista_data.get("financial_year_variance_percent", "")
        )

        row[
            "Departmental narrative on budget/forecast variance for 2023/24 (if variance is more than 5%)"
        ] = nista_data.get("budget_variance_narrative", "")

        row[
            "TOTAL Baseline Whole Life Costs (£m) (including Non-Government Costs)"
        ] = str(nista_data.get("whole_life_cost_baseline", ""))
        row["Departmental Narrative on Budgeted Whole Life Costs"] = nista_data.get(
            "whole_life_cost_narrative", ""
        )

        row["TOTAL Baseline Benefits (£m)"] = str(
            nista_data.get("benefits_baseline", "")
        )
        row["Departmental Narrative on Budgeted Benefits"] = nista_data.get(
            "benefits_narrative", ""
        )

        return row

    def _format_dca(self, dca: DeliveryConfidence) -> str:
        """Format DeliveryConfidence enum to NISTA string.

        Args:
            dca: DeliveryConfidence enum

        Returns:
            NISTA DCA string (Green/Amber/Red/Exempt)
        """
        if dca == DeliveryConfidence.GREEN:
            return "Green"
        elif dca == DeliveryConfidence.AMBER:
            return "Amber"
        elif dca == DeliveryConfidence.RED:
            return "Red"
        elif dca == DeliveryConfidence.EXEMPT:
            return "Exempt"
        return ""
