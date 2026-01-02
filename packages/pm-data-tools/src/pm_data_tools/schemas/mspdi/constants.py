"""MSPDI schema constants and field mappings.

This module defines mappings between MSPDI XML field values and canonical
model enums, based on the official Microsoft Project Data Interchange schema.

Schema reference: https://schemas.microsoft.com/project/2007/mspdi_pj12.xsd
"""

from pm_data_tools.models.task import ConstraintType, TaskStatus
from pm_data_tools.models.dependency import DependencyType
from pm_data_tools.models.resource import ResourceType

# MSPDI namespace
MSPDI_NAMESPACE = "http://schemas.microsoft.com/project"

# MSPDI Constraint Type mappings (integer to ConstraintType)
MSPDI_CONSTRAINT_TYPE_MAP = {
    0: ConstraintType.ASAP,  # As Soon As Possible
    1: ConstraintType.ALAP,  # As Late As Possible
    2: ConstraintType.MSO,   # Must Start On
    3: ConstraintType.MFO,   # Must Finish On
    4: ConstraintType.SNET,  # Start No Earlier Than
    5: ConstraintType.SNLT,  # Start No Later Than
    6: ConstraintType.FNET,  # Finish No Earlier Than
    7: ConstraintType.FNLT,  # Finish No Later Than
}

# Reverse mapping for writing
CONSTRAINT_TYPE_TO_MSPDI = {v: k for k, v in MSPDI_CONSTRAINT_TYPE_MAP.items()}

# MSPDI Dependency Type mappings (integer to DependencyType)
MSPDI_DEPENDENCY_TYPE_MAP = {
    0: DependencyType.FINISH_TO_FINISH,   # FF
    1: DependencyType.FINISH_TO_START,    # FS (default)
    2: DependencyType.START_TO_FINISH,    # SF
    3: DependencyType.START_TO_START,     # SS
}

# Reverse mapping for writing
DEPENDENCY_TYPE_TO_MSPDI = {v: k for k, v in MSPDI_DEPENDENCY_TYPE_MAP.items()}

# MSPDI Resource Type mappings (integer to ResourceType)
MSPDI_RESOURCE_TYPE_MAP = {
    0: ResourceType.MATERIAL,   # Material resource
    1: ResourceType.WORK,       # Work resource (default)
    2: ResourceType.COST,       # Cost resource
}

# Reverse mapping for writing
RESOURCE_TYPE_TO_MSPDI = {v: k for k, v in MSPDI_RESOURCE_TYPE_MAP.items()}

# Task status is derived from % Complete in MSPDI
def get_task_status_from_percent(percent_complete: float) -> TaskStatus:
    """Derive task status from percent complete.

    Args:
        percent_complete: Percentage complete (0-100)

    Returns:
        Corresponding task status
    """
    if percent_complete == 0.0:
        return TaskStatus.NOT_STARTED
    elif percent_complete >= 100.0:
        return TaskStatus.COMPLETED
    else:
        return TaskStatus.IN_PROGRESS


# Default values for MSPDI fields
DEFAULT_HOURS_PER_DAY = 8.0
DEFAULT_HOURS_PER_WEEK = 40.0
DEFAULT_DAYS_PER_MONTH = 20.0
DEFAULT_CURRENCY = "GBP"

# MSPDI boolean representations
MSPDI_TRUE = "1"
MSPDI_FALSE = "0"


def mspdi_bool(value: bool) -> str:
    """Convert Python bool to MSPDI boolean string.

    Args:
        value: Python boolean

    Returns:
        MSPDI boolean string ("1" or "0")
    """
    return MSPDI_TRUE if value else MSPDI_FALSE


def parse_mspdi_bool(value: str | None) -> bool:
    """Parse MSPDI boolean string to Python bool.

    Args:
        value: MSPDI boolean string ("1", "0", "true", "false", or None)

    Returns:
        Python boolean (defaults to False if None)
    """
    if value is None:
        return False
    return value.strip().lower() in (MSPDI_TRUE, "true")
