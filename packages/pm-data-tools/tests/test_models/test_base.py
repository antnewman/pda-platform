"""Tests for base types and classes."""

import pytest
from datetime import datetime
from decimal import Decimal

from pm_data_tools.models.base import Duration, Money, SourceInfo, CustomField


class TestDuration:
    """Tests for Duration class."""

    def test_creation(self) -> None:
        """Test Duration creation."""
        d = Duration(8.0, "hours")
        assert d.value == 8.0
        assert d.unit == "hours"

    def test_immutable(self) -> None:
        """Test that Duration is immutable."""
        d = Duration(8.0, "hours")
        with pytest.raises(AttributeError):
            d.value = 10.0  # type: ignore

    def test_to_hours_from_hours(self) -> None:
        """Test conversion from hours to hours."""
        d = Duration(8.0, "hours")
        assert d.to_hours() == 8.0

    def test_to_hours_from_days(self) -> None:
        """Test conversion from days to hours."""
        d = Duration(2.0, "days")
        assert d.to_hours() == 16.0

    def test_to_hours_from_weeks(self) -> None:
        """Test conversion from weeks to hours."""
        d = Duration(1.0, "weeks")
        assert d.to_hours() == 40.0

    def test_to_hours_from_months(self) -> None:
        """Test conversion from months to hours."""
        d = Duration(1.0, "months")
        assert d.to_hours() == 160.0

    def test_to_days(self) -> None:
        """Test conversion to days."""
        d = Duration(16.0, "hours")
        assert d.to_days() == 2.0

    def test_to_weeks(self) -> None:
        """Test conversion to weeks."""
        d = Duration(80.0, "hours")
        assert d.to_weeks() == 2.0

    def test_to_months(self) -> None:
        """Test conversion to months."""
        d = Duration(320.0, "hours")
        assert d.to_months() == 2.0

    def test_str_representation(self) -> None:
        """Test string representation."""
        d = Duration(8.0, "hours")
        assert str(d) == "8.0 hours"


class TestMoney:
    """Tests for Money class."""

    def test_creation_with_explicit_currency(self) -> None:
        """Test Money creation with explicit currency."""
        m = Money(Decimal("100.50"), "GBP")
        assert m.amount == Decimal("100.50")
        assert m.currency == "GBP"

    def test_creation_with_default_currency(self) -> None:
        """Test Money creation with default GBP currency."""
        m = Money(Decimal("100"))
        assert m.amount == Decimal("100")
        assert m.currency == "GBP"

    def test_immutable(self) -> None:
        """Test that Money is immutable."""
        m = Money(Decimal("100"), "GBP")
        with pytest.raises(AttributeError):
            m.amount = Decimal("200")  # type: ignore

    def test_addition_same_currency(self) -> None:
        """Test adding Money with same currency."""
        m1 = Money(Decimal("100"), "GBP")
        m2 = Money(Decimal("50"), "GBP")
        result = m1 + m2

        assert result.amount == Decimal("150")
        assert result.currency == "GBP"

    def test_addition_different_currency_raises(self) -> None:
        """Test that adding different currencies raises ValueError."""
        m1 = Money(Decimal("100"), "GBP")
        m2 = Money(Decimal("50"), "USD")

        with pytest.raises(ValueError, match="Cannot add different currencies"):
            m1 + m2

    def test_subtraction_same_currency(self) -> None:
        """Test subtracting Money with same currency."""
        m1 = Money(Decimal("100"), "GBP")
        m2 = Money(Decimal("30"), "GBP")
        result = m1 - m2

        assert result.amount == Decimal("70")
        assert result.currency == "GBP"

    def test_subtraction_different_currency_raises(self) -> None:
        """Test that subtracting different currencies raises ValueError."""
        m1 = Money(Decimal("100"), "GBP")
        m2 = Money(Decimal("30"), "USD")

        with pytest.raises(ValueError, match="Cannot subtract different currencies"):
            m1 - m2

    def test_multiplication_by_scalar(self) -> None:
        """Test multiplying Money by scalar."""
        m = Money(Decimal("100"), "GBP")
        result = m * 2.5

        assert result.amount == Decimal("250")
        assert result.currency == "GBP"

    def test_str_representation_gbp(self) -> None:
        """Test string representation for GBP."""
        m = Money(Decimal("100.50"), "GBP")
        assert str(m) == "£100.50"

    def test_str_representation_other_currency(self) -> None:
        """Test string representation for non-GBP currency."""
        m = Money(Decimal("100.50"), "USD")
        assert str(m) == "USD 100.50"


class TestSourceInfo:
    """Tests for SourceInfo class."""

    def test_creation_minimal(self) -> None:
        """Test SourceInfo creation with minimal data."""
        source = SourceInfo(tool="mspdi")
        assert source.tool == "mspdi"
        assert source.tool_version is None
        assert source.file_path is None
        assert source.extracted_at is None
        assert source.original_id is None

    def test_creation_complete(self) -> None:
        """Test SourceInfo creation with complete data."""
        now = datetime(2025, 1, 1, 12, 0, 0)
        source = SourceInfo(
            tool="mspdi",
            tool_version="1.0",
            file_path="/path/to/file.xml",
            extracted_at=now,
            original_id="123",
        )

        assert source.tool == "mspdi"
        assert source.tool_version == "1.0"
        assert source.file_path == "/path/to/file.xml"
        assert source.extracted_at == now
        assert source.original_id == "123"

    def test_immutable(self) -> None:
        """Test that SourceInfo is immutable."""
        source = SourceInfo(tool="mspdi")
        with pytest.raises(AttributeError):
            source.tool = "p6"  # type: ignore

    def test_str_representation_minimal(self) -> None:
        """Test string representation with minimal data."""
        source = SourceInfo(tool="mspdi")
        assert "tool=mspdi" in str(source)

    def test_str_representation_with_version(self) -> None:
        """Test string representation with version."""
        source = SourceInfo(tool="mspdi", tool_version="1.0")
        result = str(source)
        assert "tool=mspdi" in result
        assert "version=1.0" in result

    def test_str_representation_with_file(self) -> None:
        """Test string representation with file path."""
        source = SourceInfo(tool="mspdi", file_path="/path/to/file.xml")
        result = str(source)
        assert "tool=mspdi" in result
        assert "file=/path/to/file.xml" in result


class TestCustomField:
    """Tests for CustomField class."""

    def test_creation_with_string_value(self) -> None:
        """Test CustomField creation with string value."""
        field = CustomField(
            name="custom_text",
            value="some text",
            field_type="text",
            source_tool="mspdi",
        )

        assert field.name == "custom_text"
        assert field.value == "some text"
        assert field.field_type == "text"
        assert field.source_tool == "mspdi"
        assert field.source_field_id is None

    def test_creation_with_number_value(self) -> None:
        """Test CustomField creation with number value."""
        field = CustomField(
            name="custom_number",
            value=42,
            field_type="number",
            source_tool="jira",
            source_field_id="customfield_10001",
        )

        assert field.name == "custom_number"
        assert field.value == 42
        assert field.field_type == "number"
        assert field.source_tool == "jira"
        assert field.source_field_id == "customfield_10001"

    def test_creation_with_boolean_value(self) -> None:
        """Test CustomField creation with boolean value."""
        field = CustomField(
            name="is_flagged",
            value=True,
            field_type="boolean",
            source_tool="p6",
        )

        assert field.value is True

    def test_creation_with_date_value(self) -> None:
        """Test CustomField creation with datetime value."""
        dt = datetime(2025, 1, 1, 12, 0, 0)
        field = CustomField(
            name="custom_date",
            value=dt,
            field_type="date",
            source_tool="mspdi",
        )

        assert field.value == dt

    def test_creation_with_none_value(self) -> None:
        """Test CustomField creation with None value."""
        field = CustomField(
            name="optional_field",
            value=None,
            field_type="text",
            source_tool="mspdi",
        )

        assert field.value is None

    def test_immutable(self) -> None:
        """Test that CustomField is immutable."""
        field = CustomField(
            name="test",
            value="value",
            field_type="text",
            source_tool="mspdi",
        )

        with pytest.raises(AttributeError):
            field.value = "new value"  # type: ignore

    def test_str_representation(self) -> None:
        """Test string representation."""
        field = CustomField(
            name="priority",
            value="High",
            field_type="choice",
            source_tool="jira",
        )

        result = str(field)
        assert "priority" in result
        assert "High" in result
        assert "choice" in result
