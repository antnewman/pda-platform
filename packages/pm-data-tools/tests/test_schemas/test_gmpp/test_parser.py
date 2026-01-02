"""Tests for GMPP parser."""

from decimal import Decimal
from pathlib import Path

import pytest

from pm_data_tools.models import DeliveryConfidence, TaskStatus
from pm_data_tools.schemas.gmpp import GMPPParser


class TestGMPPParser:
    """Tests for GMPPParser class."""

    @pytest.fixture
    def parser(self) -> GMPPParser:
        """Create parser instance."""
        return GMPPParser()

    @pytest.fixture
    def fixture_path(self) -> Path:
        """Get path to test fixtures."""
        return Path(__file__).parent.parent.parent / "fixtures" / "gmpp"

    def test_parse_from_file(self, parser: GMPPParser, fixture_path: Path) -> None:
        """Test parsing from CSV file."""
        file_path = fixture_path / "projects.csv"
        projects = parser.parse_file(file_path)

        assert len(projects) == 5
        assert all(p.name for p in projects)

    def test_parse_project_names(self, parser: GMPPParser, fixture_path: Path) -> None:
        """Test project names are extracted correctly."""
        file_path = fixture_path / "projects.csv"
        projects = parser.parse_file(file_path)

        hs2 = next(p for p in projects if "High Speed 2" in p.name)
        assert hs2.name == "High Speed 2"

    def test_parse_dca_to_delivery_confidence(
        self, parser: GMPPParser, fixture_path: Path
    ) -> None:
        """Test DCA maps to DeliveryConfidence correctly."""
        file_path = fixture_path / "projects.csv"
        projects = parser.parse_file(file_path)

        # Red/Amber → RED
        hs2 = next(p for p in projects if "High Speed 2" in p.name)
        assert hs2.delivery_confidence == DeliveryConfidence.RED

        # Amber → AMBER
        smart_motorways = next(p for p in projects if "Smart Motorways" in p.name)
        assert smart_motorways.delivery_confidence == DeliveryConfidence.AMBER

        # Green → GREEN
        foundry = next(p for p in projects if "Foundry" in p.name)
        assert foundry.delivery_confidence == DeliveryConfidence.GREEN

        # Red → RED
        test_trace = next(p for p in projects if "Test and Trace" in p.name)
        assert test_trace.delivery_confidence == DeliveryConfidence.RED

    def test_parse_dates(self, parser: GMPPParser, fixture_path: Path) -> None:
        """Test date parsing from DD/MM/YYYY format."""
        file_path = fixture_path / "projects.csv"
        projects = parser.parse_file(file_path)

        hs2 = next(p for p in projects if "High Speed 2" in p.name)
        task = hs2.tasks[0]

        assert task.start_date is not None
        assert task.start_date.year == 2017
        assert task.start_date.month == 1
        assert task.start_date.day == 1

        assert task.finish_date is not None
        assert task.finish_date.year == 2033
        assert task.finish_date.month == 12
        assert task.finish_date.day == 31

    def test_parse_sro_as_resource(
        self, parser: GMPPParser, fixture_path: Path
    ) -> None:
        """Test SRO is extracted as resource."""
        file_path = fixture_path / "projects.csv"
        projects = parser.parse_file(file_path)

        hs2 = next(p for p in projects if "High Speed 2" in p.name)
        assert len(hs2.resources) == 1
        assert hs2.resources[0].name == "Sir Jon Thompson"

    def test_parse_whole_life_cost(
        self, parser: GMPPParser, fixture_path: Path
    ) -> None:
        """Test Whole Life Cost is parsed correctly."""
        file_path = fixture_path / "projects.csv"
        projects = parser.parse_file(file_path)

        hs2 = next(p for p in projects if "High Speed 2" in p.name)
        assert hs2.whole_life_cost is not None
        # Should be £72bn
        assert hs2.whole_life_cost.amount == Decimal("72000000000")
        assert hs2.whole_life_cost.currency == "GBP"

    def test_parse_department(self, parser: GMPPParser, fixture_path: Path) -> None:
        """Test department is parsed correctly."""
        file_path = fixture_path / "projects.csv"
        projects = parser.parse_file(file_path)

        hs2 = next(p for p in projects if "High Speed 2" in p.name)
        assert hs2.department == "Department for Transport"

    def test_parse_creates_summary_task(
        self, parser: GMPPParser, fixture_path: Path
    ) -> None:
        """Test each project gets one summary task."""
        file_path = fixture_path / "projects.csv"
        projects = parser.parse_file(file_path)

        for project in projects:
            assert len(project.tasks) == 1
            task = project.tasks[0]
            assert task.is_summary
            assert task.name == project.name
            assert task.status == TaskStatus.IN_PROGRESS

    def test_parse_row_without_project_name(self, parser: GMPPParser) -> None:
        """Test row without project name is skipped."""
        rows = [
            {"DCA": "Green", "SRO": "John Doe"},  # No project name
            {"Project Name": "Valid Project", "DCA": "Amber"},
        ]

        projects = parser.parse(rows)
        assert len(projects) == 1
        assert projects[0].name == "Valid Project"

    def test_parse_unknown_dca_defaults_to_amber(self, parser: GMPPParser) -> None:
        """Test unknown DCA value defaults to AMBER."""
        rows = [
            {"Project Name": "Test Project", "DCA": "Unknown Status"},
        ]

        projects = parser.parse(rows)
        assert projects[0].delivery_confidence == DeliveryConfidence.AMBER

    def test_parse_missing_dca_defaults_to_amber(self, parser: GMPPParser) -> None:
        """Test missing DCA defaults to AMBER."""
        rows = [
            {"Project Name": "Test Project"},  # No DCA field
        ]

        projects = parser.parse(rows)
        assert projects[0].delivery_confidence == DeliveryConfidence.AMBER

    def test_parse_project_without_sro(self, parser: GMPPParser) -> None:
        """Test project without SRO has no resources."""
        rows = [
            {"Project Name": "Test Project", "DCA": "Green"},  # No SRO
        ]

        projects = parser.parse(rows)
        assert len(projects[0].resources) == 0

    def test_parse_invalid_date_returns_none(self, parser: GMPPParser) -> None:
        """Test invalid date format returns None."""
        rows = [
            {
                "Project Name": "Test Project",
                "Start Date": "not-a-date",
                "End Date": "invalid",
            },
        ]

        projects = parser.parse(rows)
        task = projects[0].tasks[0]
        assert task.start_date is None
        assert task.finish_date is None

    def test_parse_money_with_m_suffix(self, parser: GMPPParser) -> None:
        """Test parsing money with 'm' suffix (millions)."""
        rows = [
            {
                "Project Name": "Test Project",
                "Whole Life Cost": "£100m",
            },
        ]

        projects = parser.parse(rows)
        assert projects[0].whole_life_cost is not None
        assert projects[0].whole_life_cost.amount == Decimal("100000000")  # 100 million

    def test_parse_money_with_b_suffix(self, parser: GMPPParser) -> None:
        """Test parsing money with 'b' suffix (billions)."""
        rows = [
            {
                "Project Name": "Test Project",
                "Whole Life Cost": "£5b",
            },
        ]

        projects = parser.parse(rows)
        assert projects[0].whole_life_cost is not None
        assert projects[0].whole_life_cost.amount == Decimal("5000000000")  # 5 billion

    def test_parse_money_plain_number(self, parser: GMPPParser) -> None:
        """Test parsing plain number as money."""
        rows = [
            {
                "Project Name": "Test Project",
                "Whole Life Cost": "1500000",
            },
        ]

        projects = parser.parse(rows)
        assert projects[0].whole_life_cost is not None
        assert projects[0].whole_life_cost.amount == Decimal("1500000")

    def test_parse_money_with_commas(self, parser: GMPPParser) -> None:
        """Test parsing money with commas."""
        rows = [
            {
                "Project Name": "Test Project",
                "Whole Life Cost": "£1,500,000",
            },
        ]

        projects = parser.parse(rows)
        assert projects[0].whole_life_cost is not None
        assert projects[0].whole_life_cost.amount == Decimal("1500000")

    def test_parse_invalid_money_returns_none(self, parser: GMPPParser) -> None:
        """Test invalid money format returns None."""
        rows = [
            {
                "Project Name": "Test Project",
                "Whole Life Cost": "not-a-number",
            },
        ]

        projects = parser.parse(rows)
        assert projects[0].whole_life_cost is None

    def test_parse_column_name_variants(self, parser: GMPPParser) -> None:
        """Test parser handles column name variants."""
        rows = [
            {
                "Project": "Test 1",  # Variant of "Project Name"
                "Confidence": "Green",  # Variant of "DCA"
                "Owner": "Alice",  # Variant of "SRO"
            },
        ]

        projects = parser.parse(rows)
        assert projects[0].name == "Test 1"
        assert projects[0].delivery_confidence == DeliveryConfidence.GREEN
        assert len(projects[0].resources) == 1
        assert projects[0].resources[0].name == "Alice"

    def test_parse_case_insensitive_dca(self, parser: GMPPParser) -> None:
        """Test DCA parsing is case-insensitive."""
        rows = [
            {"Project Name": "Test 1", "DCA": "green"},
            {"Project Name": "Test 2", "DCA": "AMBER"},
            {"Project Name": "Test 3", "DCA": "Red"},
        ]

        projects = parser.parse(rows)
        assert projects[0].delivery_confidence == DeliveryConfidence.GREEN
        assert projects[1].delivery_confidence == DeliveryConfidence.AMBER
        assert projects[2].delivery_confidence == DeliveryConfidence.RED

    def test_parse_month_year_date_format(self, parser: GMPPParser) -> None:
        """Test parsing 'Month Year' date format."""
        rows = [
            {
                "Project Name": "Test Project",
                "Start Date": "March 2020",
                "End Date": "December 2025",
            },
        ]

        projects = parser.parse(rows)
        task = projects[0].tasks[0]

        assert task.start_date is not None
        assert task.start_date.year == 2020
        assert task.start_date.month == 3

        assert task.finish_date is not None
        assert task.finish_date.year == 2025
        assert task.finish_date.month == 12
