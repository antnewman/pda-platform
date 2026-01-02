"""PM Data Tools - Project management data interoperability library.

This library provides a canonical data model and conversion utilities for project
management data across multiple platforms and standards, targeting UK Government
NISTA compliance.
"""

__version__ = "0.2.0"

# Import public API
from .parsers import detect_format, create_parser, parse_project
from .exporters import create_exporter
from .exceptions import (
    PMDataToolsError,
    ParseError,
    UnsupportedFormatError,
    ValidationError,
    ExportError,
)

# Models are imported via pm_data_tools.models
# from .models import Project, Task, Resource, Dependency, etc.

__all__ = [
    "__version__",
    # Parser API
    "detect_format",
    "create_parser",
    "parse_project",
    # Exporter API
    "create_exporter",
    # Exceptions
    "PMDataToolsError",
    "ParseError",
    "UnsupportedFormatError",
    "ValidationError",
    "ExportError",
]
