"""XML helper utilities for PM data tools.

This module provides safe wrappers around lxml for parsing and writing
XML data from PM tools, with error handling and namespace support.
"""

from typing import Optional, Any
from pathlib import Path

from lxml import etree


def parse_xml_file(file_path: str | Path) -> Optional[etree._Element]:
    """Parse XML file safely.

    Args:
        file_path: Path to XML file.

    Returns:
        Parsed XML element tree root, or None if parsing fails.
    """
    try:
        parser = etree.XMLParser(
            remove_blank_text=True, resolve_entities=False, no_network=True
        )
        tree = etree.parse(str(file_path), parser)
        return tree.getroot()
    except (etree.XMLSyntaxError, IOError, OSError):
        return None


def parse_xml_string(xml_string: str | bytes) -> Optional[etree._Element]:
    """Parse XML string safely.

    Args:
        xml_string: XML string or bytes.

    Returns:
        Parsed XML element tree root, or None if parsing fails.
    """
    try:
        parser = etree.XMLParser(
            remove_blank_text=True, resolve_entities=False, no_network=True
        )
        if isinstance(xml_string, str):
            xml_string = xml_string.encode("utf-8")
        return etree.fromstring(xml_string, parser)
    except etree.XMLSyntaxError:
        return None


def get_text(element: etree._Element, xpath: str, default: str = "") -> str:
    """Get text content from XML element via XPath.

    Args:
        element: XML element.
        xpath: XPath expression.
        default: Default value if element not found.

    Returns:
        Text content or default.
    """
    result = element.xpath(xpath)
    if result and isinstance(result[0], etree._Element):
        return result[0].text or default
    return default


def get_int(element: etree._Element, xpath: str, default: int = 0) -> int:
    """Get integer value from XML element via XPath.

    Args:
        element: XML element.
        xpath: XPath expression.
        default: Default value if element not found or invalid.

    Returns:
        Integer value or default.
    """
    text = get_text(element, xpath)
    if not text:
        return default

    try:
        return int(text)
    except ValueError:
        return default


def get_float(element: etree._Element, xpath: str, default: float = 0.0) -> float:
    """Get float value from XML element via XPath.

    Args:
        element: XML element.
        xpath: XPath expression.
        default: Default value if element not found or invalid.

    Returns:
        Float value or default.
    """
    text = get_text(element, xpath)
    if not text:
        return default

    try:
        return float(text)
    except ValueError:
        return default


def get_bool(element: etree._Element, xpath: str, default: bool = False) -> bool:
    """Get boolean value from XML element via XPath.

    Args:
        element: XML element.
        xpath: XPath expression.
        default: Default value if element not found.

    Returns:
        Boolean value or default.
    """
    text = get_text(element, xpath).lower()
    if text in ("1", "true", "yes"):
        return True
    elif text in ("0", "false", "no"):
        return False
    return default


def create_element(tag: str, text: Optional[str] = None, **attributes: Any) -> etree._Element:
    """Create XML element with optional text and attributes.

    Args:
        tag: Element tag name.
        text: Optional text content.
        **attributes: Element attributes.

    Returns:
        XML element.
    """
    element = etree.Element(tag, **attributes)
    if text is not None:
        element.text = str(text)
    return element


def write_xml_file(
    root: etree._Element,
    file_path: str | Path,
    encoding: str = "utf-8",
    pretty_print: bool = True,
) -> None:
    """Write XML element tree to file.

    Args:
        root: Root XML element.
        file_path: Output file path.
        encoding: Character encoding (default: utf-8).
        pretty_print: Format with indentation (default: True).
    """
    tree = etree.ElementTree(root)
    tree.write(
        str(file_path),
        encoding=encoding,
        xml_declaration=True,
        pretty_print=pretty_print,
    )


def write_xml_string(
    root: etree._Element,
    encoding: str = "utf-8",
    pretty_print: bool = True,
) -> bytes:
    """Write XML element tree to bytes.

    Args:
        root: Root XML element.
        encoding: Character encoding (default: utf-8).
        pretty_print: Format with indentation (default: True).

    Returns:
        XML as bytes.
    """
    return etree.tostring(
        root,
        encoding=encoding,
        xml_declaration=True,
        pretty_print=pretty_print,
    )


def strip_namespaces(element: etree._Element) -> etree._Element:
    """Remove all namespaces from XML element tree.

    Args:
        element: XML element.

    Returns:
        Element with namespaces removed.
    """
    for elem in element.iter():
        # Remove namespace from tag
        if isinstance(elem.tag, str) and "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

        # Remove namespace declarations
        elem.attrib.pop("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", None)

    # Remove namespace map
    etree.cleanup_namespaces(element)
    return element
