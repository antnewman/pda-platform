"""Tests for Resource model."""

import pytest
from decimal import Decimal
from uuid import uuid4

from pm_data_tools.models import Resource, ResourceType, Money, SourceInfo


@pytest.fixture
def source_info() -> SourceInfo:
    """Test source info."""
    return SourceInfo(tool="test")


class TestResourceType:
    """Tests for ResourceType enum."""

    def test_enum_values(self) -> None:
        """Test ResourceType enum values."""
        assert ResourceType.WORK.value == "work"
        assert ResourceType.MATERIAL.value == "material"
        assert ResourceType.COST.value == "cost"
        assert ResourceType.EQUIPMENT.value == "equipment"


class TestResource:
    """Tests for Resource model."""

    def test_creation_minimal(self, source_info: SourceInfo) -> None:
        """Test Resource creation with minimal fields."""
        resource = Resource(
            id=uuid4(),
            name="Test Resource",
            source=source_info,
        )

        assert resource.name == "Test Resource"
        assert resource.resource_type == ResourceType.WORK
        assert resource.max_units == 1.0

    def test_creation_complete(self, source_info: SourceInfo) -> None:
        """Test Resource creation with all fields."""
        resource = Resource(
            id=uuid4(),
            name="Senior Engineer",
            source=source_info,
            resource_type=ResourceType.WORK,
            max_units=1.0,
            standard_rate=Money(Decimal("500"), "GBP"),
            overtime_rate=Money(Decimal("750"), "GBP"),
            cost_per_use=Money(Decimal("100"), "GBP"),
            email="engineer@example.com",
            group="Engineering",
        )

        assert resource.name == "Senior Engineer"
        assert resource.standard_rate == Money(Decimal("500"), "GBP")
        assert resource.email == "engineer@example.com"
        assert resource.group == "Engineering"

    def test_immutable(self, source_info: SourceInfo) -> None:
        """Test that Resource is immutable."""
        resource = Resource(id=uuid4(), name="Test", source=source_info)

        with pytest.raises(AttributeError):
            resource.name = "Modified"  # type: ignore

    def test_is_overallocated_true(self, source_info: SourceInfo) -> None:
        """Test is_overallocated property returns True."""
        resource = Resource(
            id=uuid4(),
            name="Test",
            source=source_info,
            max_units=1.5,
        )

        assert resource.is_overallocated is True

    def test_is_overallocated_false(self, source_info: SourceInfo) -> None:
        """Test is_overallocated property returns False."""
        resource = Resource(
            id=uuid4(),
            name="Test",
            source=source_info,
            max_units=1.0,
        )

        assert resource.is_overallocated is False

    def test_availability_percent(self, source_info: SourceInfo) -> None:
        """Test availability_percent property."""
        resource = Resource(
            id=uuid4(),
            name="Test",
            source=source_info,
            max_units=0.5,
        )

        assert resource.availability_percent == 50.0

    def test_str_representation(self, source_info: SourceInfo) -> None:
        """Test string representation."""
        resource = Resource(
            id=uuid4(),
            name="Engineer",
            source=source_info,
            resource_type=ResourceType.WORK,
            max_units=1.0,
        )

        result = str(resource)
        assert "Engineer" in result
        assert "work" in result
        assert "100.0%" in result
