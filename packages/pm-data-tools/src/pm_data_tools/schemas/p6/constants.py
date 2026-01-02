"""Constants and enums for Primavera P6 schema.

This module defines P6-specific constants, enums, and field mappings used
for parsing and writing P6 data formats (XER and PMXML).
"""

from enum import Enum


class ActivityType(Enum):
    """P6 Activity Type."""

    TASK_DEPENDENT = "TT_Task"
    RESOURCE_DEPENDENT = "TT_Rsrc"
    LEVEL_OF_EFFORT = "TT_LOE"
    START_MILESTONE = "TT_Mile"
    FINISH_MILESTONE = "TT_FinMile"
    WBS_SUMMARY = "TT_WBS"


class ActivityStatus(Enum):
    """P6 Activity Status."""

    NOT_STARTED = "TK_NotStart"
    IN_PROGRESS = "TK_Active"
    COMPLETED = "TK_Complete"


class RelationshipType(Enum):
    """P6 Relationship (Dependency) Type."""

    FINISH_TO_START = "PR_FS"
    FINISH_TO_FINISH = "PR_FF"
    START_TO_START = "PR_SS"
    START_TO_FINISH = "PR_SF"


class PercentCompleteType(Enum):
    """P6 Percent Complete calculation method."""

    PHYSICAL = "CP_Phys"
    DURATION = "CP_Drtn"
    UNITS = "CP_Units"


class CalendarType(Enum):
    """P6 Calendar Type."""

    GLOBAL = "CA_Global"
    PROJECT = "CA_Project"
    RESOURCE = "CA_Rsrc"
    PERSONAL = "CA_Personal"


class ResourceType(Enum):
    """P6 Resource Type."""

    LABOR = "RT_Labor"
    NONLABOR = "RT_Mat"
    EQUIPMENT = "RT_Equip"


class DurationType(Enum):
    """P6 Duration Type."""

    FIXED_DURATION_AND_UNITS = "DT_FixedDrtn"
    FIXED_UNITS = "DT_FixedQty"
    FIXED_DURATION = "DT_FixedDUR2"
    FIXED_UNITS_TIME = "DT_FixedRate"


# XER field mappings
XER_TABLE_NAMES = {
    "PROJECT": "PROJECT",
    "TASK": "TASK",
    "TASKPRED": "TASKPRED",
    "TASKRSRC": "TASKRSRC",
    "RSRC": "RSRC",
    "CALENDAR": "CALENDAR",
    "SCHEDOPTIONS": "SCHEDOPTIONS",
    "ACCOUNT": "ACCOUNT",
    "ACTVCODE": "ACTVCODE",
    "ACTVTYPE": "ACTVTYPE",
    "TASKACTV": "TASKACTV",
}

# P6 to canonical model mappings
ACTIVITY_TYPE_TO_TASK_STATUS = {
    ActivityType.TASK_DEPENDENT: "NOT_STARTED",
    ActivityType.RESOURCE_DEPENDENT: "NOT_STARTED",
    ActivityType.LEVEL_OF_EFFORT: "NOT_STARTED",
    ActivityType.START_MILESTONE: "NOT_STARTED",
    ActivityType.FINISH_MILESTONE: "NOT_STARTED",
    ActivityType.WBS_SUMMARY: "NOT_STARTED",
}

RELATIONSHIP_TYPE_TO_DEPENDENCY_TYPE = {
    RelationshipType.FINISH_TO_START: "FINISH_TO_START",
    RelationshipType.FINISH_TO_FINISH: "FINISH_TO_FINISH",
    RelationshipType.START_TO_START: "START_TO_START",
    RelationshipType.START_TO_FINISH: "START_TO_FINISH",
}

RESOURCE_TYPE_TO_CANONICAL = {
    ResourceType.LABOR: "WORK",
    ResourceType.NONLABOR: "MATERIAL",
    ResourceType.EQUIPMENT: "EQUIPMENT",
}
