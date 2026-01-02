"""High-level parser API and factory functions.

Provides convenience functions for detecting file formats and creating
appropriate parsers without needing to know internal schema structure.
"""

from pathlib import Path
from typing import Optional
import mimetypes

from .models import Project


def detect_format(file_path: str | Path) -> Optional[str]:
    """Auto-detect project file format.

    Args:
        file_path: Path to project file

    Returns:
        Format name ('mspdi', 'p6_xer', 'nista', etc.) or None if unknown
    """
    path = Path(file_path)

    if not path.exists():
        return None

    # Check extension first
    ext = path.suffix.lower()
    if ext in ['.xml', '.mpp']:
        # Check if MSPDI by reading first few lines
        try:
            with open(path, 'r', encoding='utf-8') as f:
                header = f.read(500)
                if 'schemas.microsoft.com/project' in header or 'MSPDI' in header:
                    return 'mspdi'
                if 'NISTA' in header or '"department"' in header:
                    return 'nista'
        except:
            pass
        return 'mspdi'  # Default for .xml

    elif ext == '.xer':
        return 'p6_xer'

    elif ext in ['.json']:
        # Try to determine if it's NISTA, Jira, Monday, etc.
        try:
            import json
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Check for NISTA-specific fields
                if isinstance(data, dict):
                    if 'delivery_confidence_assessment' in data or 'department' in str(data):
                        return 'nista'
                    if 'issues' in data or 'jira' in str(data).lower():
                        return 'jira'
                    if 'boards' in data or 'monday' in str(data).lower():
                        return 'monday'
                    if 'tasks' in data and 'gid' in str(data):
                        return 'asana'
                    if 'sheets' in data:
                        return 'smartsheet'
        except:
            pass
        return 'nista'  # Default for .json

    elif ext in ['.csv']:
        # Could be GMPP or generic CSV
        try:
            with open(path, 'r', encoding='utf-8') as f:
                header = f.readline()
                if 'GMPP' in header or 'Delivery Confidence' in header:
                    return 'gmpp'
        except:
            pass
        return 'gmpp'

    return None


def create_parser(format_name: str):
    """Create parser instance for specified format.

    Args:
        format_name: Format name ('mspdi', 'p6_xer', 'nista', 'jira',
                     'monday', 'asana', 'smartsheet', 'gmpp')

    Returns:
        Parser instance with parse_file() and parse_string() methods

    Raises:
        ValueError: If format is not supported
    """
    format_name = format_name.lower()

    if format_name == 'mspdi':
        from .schemas.mspdi.parser import MspdiParser
        return MspdiParser()

    elif format_name == 'p6_xer' or format_name == 'p6':
        from .schemas.p6.xer_parser import XERParser
        from pathlib import Path

        # XERParser has non-standard interface - needs file_path in __init__
        # Create wrapper to match standard interface
        class XERParserWrapper:
            def __init__(self):
                self.source_tool = "primavera-p6"

            def parse_file(self, file_path: str | Path) -> Optional[Project]:
                parser = XERParser(Path(file_path))
                return parser.parse()

            def parse_string(self, content: str) -> Optional[Project]:
                # XER parser doesn't support string parsing
                raise NotImplementedError("XER parser requires file path")

        return XERParserWrapper()

    elif format_name == 'nista':
        from .schemas.nista.parser import NISTAParser
        return NISTAParser()

    elif format_name == 'jira':
        from .schemas.jira.parser import JiraParser
        # JiraParser requires project_key, use generic placeholder
        return JiraParser(project_key="PROJ")

    elif format_name == 'monday':
        from .schemas.monday.parser import MondayParser
        return MondayParser()

    elif format_name == 'asana':
        from .schemas.asana.parser import AsanaParser
        return AsanaParser()

    elif format_name == 'smartsheet':
        from .schemas.smartsheet.parser import SmartsheetParser
        return SmartsheetParser()

    elif format_name == 'gmpp':
        from .schemas.gmpp.parser import GMPPParser
        return GMPPParser()

    else:
        raise ValueError(
            f"Unsupported format: {format_name}. "
            f"Supported: mspdi, p6_xer, nista, jira, monday, asana, smartsheet, gmpp"
        )


def parse_project(file_path: str | Path, format: Optional[str] = None) -> Optional[Project]:
    """Convenience function to parse a project file.

    Auto-detects format if not specified, creates appropriate parser,
    and returns parsed Project.

    Args:
        file_path: Path to project file
        format: Optional format hint. If None, will auto-detect.

    Returns:
        Parsed Project or None if parsing fails

    Raises:
        ValueError: If format is unsupported
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Detect format if not provided
    if format is None:
        format = detect_format(path)
        if format is None:
            raise ValueError(f"Could not detect format for: {file_path}")

    # Create parser and parse
    parser = create_parser(format)
    return parser.parse_file(path)


__all__ = [
    'detect_format',
    'create_parser',
    'parse_project',
]
