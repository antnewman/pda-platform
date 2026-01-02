"""Tests for MSPDI constants and helper functions."""

from pm_data_tools.schemas.mspdi.constants import parse_mspdi_bool


class TestParseMspdiBool:
    """Tests for parse_mspdi_bool function."""

    def test_parse_true_from_one(self) -> None:
        """Test parsing '1' as True."""
        assert parse_mspdi_bool("1") is True

    def test_parse_true_from_true(self) -> None:
        """Test parsing 'true' as True."""
        assert parse_mspdi_bool("true") is True

    def test_parse_true_from_TRUE(self) -> None:
        """Test parsing 'TRUE' as True (case insensitive)."""
        assert parse_mspdi_bool("TRUE") is True

    def test_parse_false_from_zero(self) -> None:
        """Test parsing '0' as False."""
        assert parse_mspdi_bool("0") is False

    def test_parse_false_from_false(self) -> None:
        """Test parsing 'false' as False."""
        assert parse_mspdi_bool("false") is False

    def test_parse_false_from_empty_string(self) -> None:
        """Test parsing empty string as False."""
        assert parse_mspdi_bool("") is False

    def test_parse_none_returns_false(self) -> None:
        """Test parsing None returns False (covers lines 102-103)."""
        assert parse_mspdi_bool(None) is False

    def test_parse_with_whitespace(self) -> None:
        """Test parsing with surrounding whitespace."""
        assert parse_mspdi_bool("  1  ") is True
        assert parse_mspdi_bool("  0  ") is False
