"""High-level exporter API and factory functions.

Provides convenience functions for creating exporters to convert canonical
Project models to various target formats.
"""

from typing import Protocol
from .models import Project


class Exporter(Protocol):
    """Protocol for exporters."""

    def export(self, project: Project, output_path: str) -> None:
        """Export project to file."""
        ...

    def export_to_string(self, project: Project) -> str:
        """Export project to string."""
        ...


def create_exporter(format_name: str) -> Exporter:
    """Create exporter instance for specified format.

    Args:
        format_name: Target format name ('nista', 'json', 'mspdi', etc.)

    Returns:
        Exporter instance with export() and export_to_string() methods

    Raises:
        ValueError: If format is not supported
    """
    format_name = format_name.lower()

    if format_name in ['nista', 'json']:
        from .schemas.nista.exporter import NistaExporter
        return NistaExporter()

    elif format_name == 'mspdi':
        # MSPDI exporter might not be implemented yet
        try:
            from .schemas.mspdi.exporter import MspdiExporter
            return MspdiExporter()
        except ImportError:
            raise ValueError(f"MSPDI exporter not yet implemented")

    elif format_name == 'gmpp':
        try:
            from .schemas.gmpp.exporter import GmppExporter
            return GmppExporter()
        except ImportError:
            raise ValueError(f"GMPP exporter not yet implemented")

    else:
        raise ValueError(
            f"Unsupported export format: {format_name}. "
            f"Supported: nista, json"
        )


__all__ = [
    'Exporter',
    'create_exporter',
]
