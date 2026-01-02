"""Tests for identifier utilities."""

import pytest
from uuid import UUID

from pm_data_tools.utils.identifiers import (
    generate_uuid_from_source,
    get_namespace_for_tool,
    generate_random_uuid,
    parse_uuid,
    is_valid_uuid,
    MSPDI_NAMESPACE,
    P6_NAMESPACE,
)


class TestGenerateUuidFromSource:
    """Tests for generate_uuid_from_source function."""

    def test_generate_deterministic_uuid(self) -> None:
        """Test UUID generation is deterministic."""
        uuid1 = generate_uuid_from_source("mspdi", "123")
        uuid2 = generate_uuid_from_source("mspdi", "123")
        assert uuid1 == uuid2

    def test_different_ids_different_uuids(self) -> None:
        """Test different source IDs generate different UUIDs."""
        uuid1 = generate_uuid_from_source("mspdi", "123")
        uuid2 = generate_uuid_from_source("mspdi", "456")
        assert uuid1 != uuid2

    def test_different_tools_different_uuids(self) -> None:
        """Test different tools generate different UUIDs."""
        uuid1 = generate_uuid_from_source("mspdi", "123")
        uuid2 = generate_uuid_from_source("p6", "123")
        assert uuid1 != uuid2

    def test_with_explicit_namespace(self) -> None:
        """Test generation with explicit namespace."""
        uuid1 = generate_uuid_from_source("test", "123", MSPDI_NAMESPACE)
        assert isinstance(uuid1, UUID)


class TestGetNamespaceForTool:
    """Tests for get_namespace_for_tool function."""

    def test_mspdi_namespace(self) -> None:
        """Test getting MSPDI namespace."""
        ns = get_namespace_for_tool("mspdi")
        assert ns == MSPDI_NAMESPACE

    def test_p6_namespace(self) -> None:
        """Test getting P6 namespace."""
        ns = get_namespace_for_tool("p6")
        assert ns == P6_NAMESPACE

    def test_case_insensitive(self) -> None:
        """Test tool name is case insensitive."""
        ns1 = get_namespace_for_tool("MSPDI")
        ns2 = get_namespace_for_tool("mspdi")
        assert ns1 == ns2

    def test_unknown_tool_returns_default(self) -> None:
        """Test unknown tool returns default namespace."""
        from uuid import NAMESPACE_URL

        ns = get_namespace_for_tool("unknown")
        assert ns == NAMESPACE_URL


class TestGenerateRandomUuid:
    """Tests for generate_random_uuid function."""

    def test_generates_uuid(self) -> None:
        """Test generates valid UUID."""
        uuid = generate_random_uuid()
        assert isinstance(uuid, UUID)

    def test_generates_different_uuids(self) -> None:
        """Test generates different UUIDs each time."""
        uuid1 = generate_random_uuid()
        uuid2 = generate_random_uuid()
        assert uuid1 != uuid2


class TestParseUuid:
    """Tests for parse_uuid function."""

    def test_parse_valid_uuid_string(self) -> None:
        """Test parsing valid UUID string."""
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"
        result = parse_uuid(uuid_str)
        assert result is not None
        assert str(result) == uuid_str

    def test_parse_invalid_uuid_returns_none(self) -> None:
        """Test parsing invalid UUID returns None."""
        assert parse_uuid("not-a-uuid") is None

    def test_parse_empty_string_returns_none(self) -> None:
        """Test parsing empty string returns None."""
        assert parse_uuid("") is None


class TestIsValidUuid:
    """Tests for is_valid_uuid function."""

    def test_valid_uuid_string(self) -> None:
        """Test valid UUID string returns True."""
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"
        assert is_valid_uuid(uuid_str) is True

    def test_invalid_uuid_string(self) -> None:
        """Test invalid UUID string returns False."""
        assert is_valid_uuid("not-a-uuid") is False

    def test_empty_string(self) -> None:
        """Test empty string returns False."""
        assert is_valid_uuid("") is False
