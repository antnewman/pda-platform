"""GMPP (Government Major Projects Portfolio) quarterly reporting module.

This module provides data models and utilities for UK Government GMPP quarterly
reporting, including:
- Enhanced data models with AI-generated narratives and confidence scoring
- Data aggregation from multiple project management sources
- Integration with the agent-task-planning framework for narrative generation

Example:
    >>> from pm_data_tools.gmpp import QuarterlyReport, GMPPDataAggregator
    >>> aggregator = GMPPDataAggregator()
    >>> report = await aggregator.aggregate_quarterly_report(
    ...     project=project,
    ...     quarter="Q2",
    ...     financial_year="2025-26"
    ... )
"""

from pm_data_tools.gmpp.models import (
    QuarterPeriod,
    DCANarrative,
    FinancialPerformance,
    SchedulePerformance,
    BenefitsPerformance,
    QuarterlyReport,
    ReviewLevel,
)
from pm_data_tools.gmpp.aggregator import GMPPDataAggregator
from pm_data_tools.gmpp.narratives import NarrativeGenerator

__all__ = [
    "QuarterPeriod",
    "DCANarrative",
    "FinancialPerformance",
    "SchedulePerformance",
    "BenefitsPerformance",
    "QuarterlyReport",
    "ReviewLevel",
    "GMPPDataAggregator",
    "NarrativeGenerator",
]
