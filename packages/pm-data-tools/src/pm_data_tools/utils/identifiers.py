"""Identifier utilities for PM data tools.

This module provides utilities for generating and managing UUIDs from
source system identifiers, ensuring consistent ID mapping across conversions.
"""

from uuid import UUID, uuid4, uuid5, NAMESPACE_URL
from typing import Optional


# Namespaces for different source tools
MSPDI_NAMESPACE = uuid5(NAMESPACE_URL, "https://schemas.microsoft.com/project/mspdi")
P6_NAMESPACE = uuid5(NAMESPACE_URL, "https://primavera.oracle.com/p6")
JIRA_NAMESPACE = uuid5(NAMESPACE_URL, "https://atlassian.com/jira")
PLANNER_NAMESPACE = uuid5(NAMESPACE_URL, "https://microsoft.com/planner")
ASANA_NAMESPACE = uuid5(NAMESPACE_URL, "https://asana.com")
MONDAY_NAMESPACE = uuid5(NAMESPACE_URL, "https://monday.com")


def generate_uuid_from_source(
    source_tool: str, source_id: str, namespace: Optional[UUID] = None
) -> UUID:
    """Generate deterministic UUID from source tool and ID.

    This ensures the same source ID always generates the same UUID,
    enabling consistent roundtrip conversions.

    Args:
        source_tool: Source tool name ("mspdi", "p6", "jira", etc.).
        source_id: ID from source system.
        namespace: Optional UUID namespace (auto-selected if not provided).

    Returns:
        Deterministic UUID based on source tool and ID.
    """
    if namespace is None:
        namespace = get_namespace_for_tool(source_tool)

    # Combine source_tool and source_id for uniqueness across tools
    name = f"{source_tool}:{source_id}"
    return uuid5(namespace, name)


def get_namespace_for_tool(tool: str) -> UUID:
    """Get UUID namespace for a specific tool.

    Args:
        tool: Tool name ("mspdi", "p6", "jira", etc.).

    Returns:
        UUID namespace for the tool.
    """
    namespaces = {
        "mspdi": MSPDI_NAMESPACE,
        "p6": P6_NAMESPACE,
        "jira": JIRA_NAMESPACE,
        "planner": PLANNER_NAMESPACE,
        "asana": ASANA_NAMESPACE,
        "monday": MONDAY_NAMESPACE,
    }

    return namespaces.get(tool.lower(), NAMESPACE_URL)


def generate_random_uuid() -> UUID:
    """Generate random UUID.

    Returns:
        Random UUID (UUID4).
    """
    return uuid4()


def parse_uuid(uuid_str: str) -> Optional[UUID]:
    """Parse UUID string.

    Args:
        uuid_str: UUID string.

    Returns:
        Parsed UUID, or None if invalid.
    """
    try:
        return UUID(uuid_str)
    except (ValueError, AttributeError):
        return None


def is_valid_uuid(uuid_str: str) -> bool:
    """Check if string is a valid UUID.

    Args:
        uuid_str: String to check.

    Returns:
        True if valid UUID format.
    """
    return parse_uuid(uuid_str) is not None
