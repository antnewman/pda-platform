"""Custom exceptions for pm-data-tools."""


class PMDataToolsError(Exception):
    """Base exception for all pm-data-tools errors."""
    pass


class ParseError(PMDataToolsError):
    """Raised when parsing a project file fails."""
    pass


class UnsupportedFormatError(PMDataToolsError):
    """Raised when file format is not supported."""
    pass


class ValidationError(PMDataToolsError):
    """Raised when project data fails validation."""
    pass


class ExportError(PMDataToolsError):
    """Raised when exporting project data fails."""
    pass


__all__ = [
    'PMDataToolsError',
    'ParseError',
    'UnsupportedFormatError',
    'ValidationError',
    'ExportError',
]
