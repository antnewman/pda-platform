"""Tests for Dependency model."""

import pytest
from uuid import uuid4

from pm_data_tools.models import Dependency, DependencyType, Duration, SourceInfo


@pytest.fixture
def source_info() -> SourceInfo:
    """Test source info."""
    return SourceInfo(tool="test")


class TestDependencyType:
    """Tests for DependencyType enum."""

    def test_enum_values(self) -> None:
        """Test DependencyType enum values."""
        assert DependencyType.FINISH_TO_START.value == "FS"
        assert DependencyType.START_TO_START.value == "SS"
        assert DependencyType.FINISH_TO_FINISH.value == "FF"
        assert DependencyType.START_TO_FINISH.value == "SF"


class TestDependency:
    """Tests for Dependency model."""

    def test_creation_minimal(self, source_info: SourceInfo) -> None:
        """Test Dependency creation with minimal fields."""
        pred_id = uuid4()
        succ_id = uuid4()

        dep = Dependency(
            id=uuid4(),
            predecessor_id=pred_id,
            successor_id=succ_id,
            source=source_info,
        )

        assert dep.predecessor_id == pred_id
        assert dep.successor_id == succ_id
        assert dep.dependency_type == DependencyType.FINISH_TO_START

    def test_creation_with_lag(self, source_info: SourceInfo) -> None:
        """Test Dependency creation with lag."""
        dep = Dependency(
            id=uuid4(),
            predecessor_id=uuid4(),
            successor_id=uuid4(),
            source=source_info,
            dependency_type=DependencyType.START_TO_START,
            lag=Duration(2.0, "days"),
        )

        assert dep.dependency_type == DependencyType.START_TO_START
        assert dep.lag == Duration(2.0, "days")

    def test_has_lag_true(self, source_info: SourceInfo) -> None:
        """Test has_lag property returns True."""
        dep = Dependency(
            id=uuid4(),
            predecessor_id=uuid4(),
            successor_id=uuid4(),
            source=source_info,
            lag=Duration(2.0, "days"),
        )

        assert dep.has_lag is True

    def test_has_lag_false(self, source_info: SourceInfo) -> None:
        """Test has_lag property returns False."""
        dep = Dependency(
            id=uuid4(),
            predecessor_id=uuid4(),
            successor_id=uuid4(),
            source=source_info,
        )

        assert dep.has_lag is False

    def test_is_lead_true(self, source_info: SourceInfo) -> None:
        """Test is_lead property returns True for negative lag."""
        dep = Dependency(
            id=uuid4(),
            predecessor_id=uuid4(),
            successor_id=uuid4(),
            source=source_info,
            lag=Duration(-2.0, "days"),
        )

        assert dep.is_lead is True
        assert dep.is_lag is False

    def test_is_lag_true(self, source_info: SourceInfo) -> None:
        """Test is_lag property returns True for positive lag."""
        dep = Dependency(
            id=uuid4(),
            predecessor_id=uuid4(),
            successor_id=uuid4(),
            source=source_info,
            lag=Duration(2.0, "days"),
        )

        assert dep.is_lag is True
        assert dep.is_lead is False

    def test_str_representation(self, source_info: SourceInfo) -> None:
        """Test string representation."""
        pred_id = uuid4()
        succ_id = uuid4()

        dep = Dependency(
            id=uuid4(),
            predecessor_id=pred_id,
            successor_id=succ_id,
            source=source_info,
            dependency_type=DependencyType.FINISH_TO_START,
        )

        result = str(dep)
        assert "FS" in result

    def test_str_representation_with_lag(self, source_info: SourceInfo) -> None:
        """Test string representation with lag."""
        dep = Dependency(
            id=uuid4(),
            predecessor_id=uuid4(),
            successor_id=uuid4(),
            source=source_info,
            lag=Duration(2.0, "days"),
        )

        result = str(dep)
        assert "+2.0" in result
