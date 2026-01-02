"""Constants for NISTA schema parsing."""

# NISTA JSON field names (from JSON schema)
FIELD_PROJECT_ID = "project_id"
FIELD_PROJECT_NAME = "project_name"
FIELD_DEPARTMENT = "department"
FIELD_CATEGORY = "category"
FIELD_DESCRIPTION = "description"
FIELD_DCA_IPA = "delivery_confidence_assessment_ipa"
FIELD_DCA_SRO = "delivery_confidence_assessment_sro"
FIELD_IPA_COMMENTARY = "ipa_rating_commentary"
FIELD_SRO = "senior_responsible_owner"
FIELD_START_BASELINE = "start_date_baseline"
FIELD_END_BASELINE = "end_date_baseline"
FIELD_START_FORECAST = "start_date_forecast"
FIELD_END_FORECAST = "end_date_forecast"
FIELD_SCHEDULE_NARRATIVE = "schedule_narrative"
FIELD_FY_BASELINE = "financial_year_baseline"
FIELD_FY_FORECAST = "financial_year_forecast"
FIELD_FY_VARIANCE = "financial_year_variance_percent"
FIELD_BUDGET_NARRATIVE = "budget_variance_narrative"
FIELD_WLC_BASELINE = "whole_life_cost_baseline"
FIELD_WLC_FORECAST = "whole_life_cost_forecast"
FIELD_WLC_NARRATIVE = "whole_life_cost_narrative"
FIELD_BENEFITS_BASELINE = "benefits_baseline"
FIELD_BENEFITS_FORECAST = "benefits_forecast"
FIELD_BENEFITS_NON_MONETISED = "benefits_non_monetised"
FIELD_BENEFITS_NARRATIVE = "benefits_narrative"
FIELD_MILESTONES = "milestones"
FIELD_RISKS = "risks_summary"
FIELD_ISSUES = "issues_summary"
FIELD_CUSTOM_FIELDS = "custom_fields"
FIELD_METADATA = "metadata"

# CSV column name mappings (GMPP legacy support)
# Maps from GMPP CSV column names to NISTA field names
CSV_COLUMN_MAPPINGS = {
    # Project ID
    "GMPP ID Number": FIELD_PROJECT_ID,
    "Project ID": FIELD_PROJECT_ID,

    # Project name
    "Project Name": FIELD_PROJECT_NAME,
    "Project": FIELD_PROJECT_NAME,

    # Department
    "Department": FIELD_DEPARTMENT,
    "Dept": FIELD_DEPARTMENT,

    # Category
    "Annual Report Category": FIELD_CATEGORY,
    "Category": FIELD_CATEGORY,
    "Project Category": FIELD_CATEGORY,

    # Description
    "Description / Aims": FIELD_DESCRIPTION,
    "Description": FIELD_DESCRIPTION,
    "Project Description": FIELD_DESCRIPTION,

    # Delivery Confidence Assessment
    "IPA Delivery Confidence Assessment": FIELD_DCA_IPA,
    "IPA DCA": FIELD_DCA_IPA,
    "Delivery Confidence Assessment": FIELD_DCA_IPA,

    "SRO Delivery Confidence Assessment": FIELD_DCA_SRO,
    "SRO DCA": FIELD_DCA_SRO,

    # Commentaries
    "Departmental commentary on actions planned or taken on the IPA RAG rating.": FIELD_IPA_COMMENTARY,
    "IPA Rating Commentary": FIELD_IPA_COMMENTARY,

    # Dates
    "Project - Start Date (Latest Approved Start Date)": FIELD_START_BASELINE,
    "Start Date": FIELD_START_BASELINE,
    "Baseline Start Date": FIELD_START_BASELINE,

    "Project - End Date (Latest Approved End Date)": FIELD_END_BASELINE,
    "End Date": FIELD_END_BASELINE,
    "Baseline End Date": FIELD_END_BASELINE,

    "Forecast Start Date": FIELD_START_FORECAST,
    "Forecast End Date": FIELD_END_FORECAST,

    # Schedule narrative
    "Departmental narrative on schedule, including any deviation from planned schedule (if necessary)": FIELD_SCHEDULE_NARRATIVE,
    "Schedule Narrative": FIELD_SCHEDULE_NARRATIVE,

    # Financials
    "Financial Year Baseline (£m) (including Non-Government Costs)": FIELD_FY_BASELINE,
    "FY Baseline": FIELD_FY_BASELINE,

    "Financial Year Forecast (£m) (including Non-Government Costs)": FIELD_FY_FORECAST,
    "FY Forecast": FIELD_FY_FORECAST,

    "Financial Year Variance (%)": FIELD_FY_VARIANCE,
    "FY Variance %": FIELD_FY_VARIANCE,

    "Departmental narrative on budget/forecast variance for 2023/24 (if variance is more than 5%)": FIELD_BUDGET_NARRATIVE,
    "Budget Variance Narrative": FIELD_BUDGET_NARRATIVE,

    # Whole Life Cost
    "TOTAL Baseline Whole Life Costs (£m) (including Non-Government Costs)": FIELD_WLC_BASELINE,
    "Whole Life Cost": FIELD_WLC_BASELINE,
    "WLC": FIELD_WLC_BASELINE,

    "TOTAL Forecast Whole Life Costs (£m)": FIELD_WLC_FORECAST,
    "WLC Forecast": FIELD_WLC_FORECAST,

    "Departmental Narrative on Budgeted Whole Life Costs": FIELD_WLC_NARRATIVE,
    "WLC Narrative": FIELD_WLC_NARRATIVE,

    # Benefits
    "TOTAL Baseline Benefits (£m)": FIELD_BENEFITS_BASELINE,
    "Benefits": FIELD_BENEFITS_BASELINE,
    "Monetised Benefits": FIELD_BENEFITS_BASELINE,

    "TOTAL Forecast Benefits (£m)": FIELD_BENEFITS_FORECAST,
    "Benefits Forecast": FIELD_BENEFITS_FORECAST,

    "Departmental Narrative on Budgeted Benefits": FIELD_BENEFITS_NARRATIVE,
    "Benefits Narrative": FIELD_BENEFITS_NARRATIVE,
}

# Delivery Confidence Assessment mappings
DCA_MAPPINGS = {
    "Green": "Green",
    "green": "Green",
    "GREEN": "Green",
    "Amber": "Amber",
    "amber": "Amber",
    "AMBER": "Amber",
    "Red": "Red",
    "red": "Red",
    "RED": "Red",
    "Exempt": "Exempt",
    "exempt": "Exempt",
    "EXEMPT": "Exempt",
    "": "",
    None: "",
}

# Category mappings (normalize variations)
CATEGORY_MAPPINGS = {
    "Infrastructure and Construction": "Infrastructure and Construction",
    "Infrastructure & Construction": "Infrastructure and Construction",
    "Infrastructure": "Infrastructure and Construction",
    "Government Transformation and Service Delivery": "Government Transformation and Service Delivery",
    "Transformation and Service Delivery": "Government Transformation and Service Delivery",
    "Transformation": "Government Transformation and Service Delivery",
    "Service Delivery": "Government Transformation and Service Delivery",
    "Military Capability": "Military Capability",
    "Military": "Military Capability",
    "Defence": "Military Capability",
    "ICT": "ICT",
    "IT": "ICT",
    "Technology": "ICT",
}
