"""Constants for GMPP schema mapping."""

from ...models import DeliveryConfidence

# GMPP Delivery Confidence Assessment (DCA) to canonical mapping
DCA_TO_DELIVERY_CONFIDENCE: dict[str, DeliveryConfidence] = {
    "Green": DeliveryConfidence.GREEN,
    "Amber": DeliveryConfidence.AMBER,
    "Amber/Red": DeliveryConfidence.RED,
    "Red": DeliveryConfidence.RED,
    # Case-insensitive variants
    "green": DeliveryConfidence.GREEN,
    "amber": DeliveryConfidence.AMBER,
    "amber/red": DeliveryConfidence.RED,
    "red": DeliveryConfidence.RED,
}

# GMPP CSV column name mappings (flexible to handle variations)
COLUMN_PROJECT_NAME = ["Project Name", "Project", "Name", "Title"]
COLUMN_DCA = ["DCA", "Delivery Confidence Assessment", "Confidence", "RAG"]
COLUMN_WHOLE_LIFE_COST = ["Whole Life Cost", "WLC", "Total Cost", "Budget"]
COLUMN_SRO = ["SRO", "Senior Responsible Owner", "Responsible Owner", "Owner"]
COLUMN_DEPARTMENT = ["Department", "Dept", "Organisation", "Organization"]
COLUMN_START_DATE = ["Start Date", "Planned Start", "Start", "Commenced"]
COLUMN_END_DATE = ["End Date", "Planned End", "End", "Completion Date", "ISD"]
