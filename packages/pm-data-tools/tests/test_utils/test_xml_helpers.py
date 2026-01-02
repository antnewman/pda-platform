"""Tests for XML helper utilities."""

import pytest
from pathlib import Path
from lxml import etree

from pm_data_tools.utils.xml_helpers import (
    parse_xml_file,
    parse_xml_string,
    get_text,
    get_int,
    get_float,
    get_bool,
    create_element,
    write_xml_file,
    write_xml_string,
    strip_namespaces,
)


@pytest.fixture
def sample_xml() -> str:
    """Sample XML for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<Project>
    <Name>Test Project</Name>
    <ID>123</ID>
    <Cost>1000.50</Cost>
    <Active>1</Active>
</Project>"""


@pytest.fixture
def sample_element(sample_xml: str) -> etree._Element:
    """Parsed XML element for testing."""
    result = parse_xml_string(sample_xml)
    assert result is not None
    return result


class TestParseXmlString:
    """Tests for parse_xml_string function."""

    def test_parse_valid_xml_string(self, sample_xml: str) -> None:
        """Test parsing valid XML string."""
        result = parse_xml_string(sample_xml)
        assert result is not None
        assert result.tag == "Project"

    def test_parse_bytes(self) -> None:
        """Test parsing XML bytes."""
        xml_bytes = b"<root><child>text</child></root>"
        result = parse_xml_string(xml_bytes)
        assert result is not None
        assert result.tag == "root"

    def test_parse_invalid_xml_returns_none(self) -> None:
        """Test parsing invalid XML returns None."""
        result = parse_xml_string("<invalid>")
        assert result is None


class TestGetText:
    """Tests for get_text function."""

    def test_get_existing_text(self, sample_element: etree._Element) -> None:
        """Test getting text from existing element."""
        result = get_text(sample_element, "Name")
        assert result == "Test Project"

    def test_get_nonexistent_returns_default(self, sample_element: etree._Element) -> None:
        """Test getting nonexistent element returns default."""
        result = get_text(sample_element, "Missing", default="N/A")
        assert result == "N/A"

    def test_get_empty_returns_default(self, sample_element: etree._Element) -> None:
        """Test getting element without text returns default."""
        xml = parse_xml_string("<root><empty></empty></root>")
        assert xml is not None
        result = get_text(xml, "empty", default="N/A")
        assert result == "N/A"


class TestGetInt:
    """Tests for get_int function."""

    def test_get_valid_int(self, sample_element: etree._Element) -> None:
        """Test getting valid integer."""
        result = get_int(sample_element, "ID")
        assert result == 123

    def test_get_nonexistent_returns_default(self, sample_element: etree._Element) -> None:
        """Test getting nonexistent element returns default."""
        result = get_int(sample_element, "Missing", default=0)
        assert result == 0

    def test_get_invalid_int_returns_default(self) -> None:
        """Test getting invalid integer returns default."""
        xml = parse_xml_string("<root><value>not-an-int</value></root>")
        assert xml is not None
        result = get_int(xml, "value", default=-1)
        assert result == -1


class TestGetFloat:
    """Tests for get_float function."""

    def test_get_valid_float(self, sample_element: etree._Element) -> None:
        """Test getting valid float."""
        result = get_float(sample_element, "Cost")
        assert result == 1000.50

    def test_get_nonexistent_returns_default(self, sample_element: etree._Element) -> None:
        """Test getting nonexistent element returns default."""
        result = get_float(sample_element, "Missing", default=0.0)
        assert result == 0.0

    def test_get_invalid_float_returns_default(self) -> None:
        """Test getting invalid float returns default."""
        xml = parse_xml_string("<root><value>not-a-float</value></root>")
        assert xml is not None
        result = get_float(xml, "value", default=-1.0)
        assert result == -1.0


class TestGetBool:
    """Tests for get_bool function."""

    def test_get_true_from_one(self, sample_element: etree._Element) -> None:
        """Test getting True from '1'."""
        result = get_bool(sample_element, "Active")
        assert result is True

    def test_get_true_from_true(self) -> None:
        """Test getting True from 'true'."""
        xml = parse_xml_string("<root><flag>true</flag></root>")
        assert xml is not None
        result = get_bool(xml, "flag")
        assert result is True

    def test_get_false_from_zero(self) -> None:
        """Test getting False from '0'."""
        xml = parse_xml_string("<root><flag>0</flag></root>")
        assert xml is not None
        result = get_bool(xml, "flag")
        assert result is False

    def test_get_false_from_false(self) -> None:
        """Test getting False from 'false'."""
        xml = parse_xml_string("<root><flag>false</flag></root>")
        assert xml is not None
        result = get_bool(xml, "flag")
        assert result is False

    def test_get_nonexistent_returns_default(self) -> None:
        """Test getting nonexistent element returns default."""
        xml = parse_xml_string("<root></root>")
        assert xml is not None
        result = get_bool(xml, "missing", default=True)
        assert result is True


class TestCreateElement:
    """Tests for create_element function."""

    def test_create_simple_element(self) -> None:
        """Test creating simple element."""
        elem = create_element("Task")
        assert elem.tag == "Task"
        assert elem.text is None

    def test_create_element_with_text(self) -> None:
        """Test creating element with text."""
        elem = create_element("Name", text="Test")
        assert elem.tag == "Name"
        assert elem.text == "Test"

    def test_create_element_with_attributes(self) -> None:
        """Test creating element with attributes."""
        elem = create_element("Task", id="123", name="Test")
        assert elem.get("id") == "123"
        assert elem.get("name") == "Test"


class TestWriteXmlString:
    """Tests for write_xml_string function."""

    def test_write_simple_element(self) -> None:
        """Test writing simple element to string."""
        elem = create_element("root")
        result = write_xml_string(elem)
        assert b"<root/>" in result

    def test_write_with_text(self) -> None:
        """Test writing element with text."""
        elem = create_element("name", text="Test")
        result = write_xml_string(elem)
        assert b"<name>Test</name>" in result

    def test_write_includes_declaration(self) -> None:
        """Test output includes XML declaration."""
        elem = create_element("root")
        result = write_xml_string(elem)
        assert b"<?xml" in result


class TestWriteXmlFile:
    """Tests for write_xml_file function."""

    def test_write_file(self, tmp_path: Path) -> None:
        """Test writing XML to file."""
        elem = create_element("Project")
        name_elem = create_element("Name", text="Test Project")
        elem.append(name_elem)

        output_file = tmp_path / "test.xml"
        write_xml_file(elem, output_file)

        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "<?xml" in content
        assert "<Project>" in content
        assert "Test Project" in content


class TestStripNamespaces:
    """Tests for strip_namespaces function."""

    def test_strip_namespace_from_tag(self) -> None:
        """Test stripping namespace from element tags."""
        xml_str = """<root xmlns="http://example.com">
            <child>text</child>
        </root>"""
        elem = parse_xml_string(xml_str)
        assert elem is not None

        result = strip_namespaces(elem)
        assert result.tag == "root"
        assert "}" not in result.tag
