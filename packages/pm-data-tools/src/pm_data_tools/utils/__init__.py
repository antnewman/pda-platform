"""Utility functions and helpers."""

from .dates import (
    parse_iso_datetime,
    parse_datetime,
    parse_mspdi_duration,
    format_mspdi_duration,
    duration_to_timedelta,
    timedelta_to_duration,
    calculate_working_days,
    add_working_days,
    format_iso_datetime,
)
from .identifiers import (
    generate_uuid_from_source,
    get_namespace_for_tool,
    generate_random_uuid,
    parse_uuid,
    is_valid_uuid,
)
from .xml_helpers import (
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

__all__ = [
    # Date utilities
    "parse_iso_datetime",
    "parse_datetime",
    "parse_mspdi_duration",
    "format_mspdi_duration",
    "duration_to_timedelta",
    "timedelta_to_duration",
    "calculate_working_days",
    "add_working_days",
    "format_iso_datetime",
    # Identifier utilities
    "generate_uuid_from_source",
    "get_namespace_for_tool",
    "generate_random_uuid",
    "parse_uuid",
    "is_valid_uuid",
    # XML utilities
    "parse_xml_file",
    "parse_xml_string",
    "get_text",
    "get_int",
    "get_float",
    "get_bool",
    "create_element",
    "write_xml_file",
    "write_xml_string",
    "strip_namespaces",
]
