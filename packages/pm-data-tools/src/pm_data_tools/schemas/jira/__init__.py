"""Jira schema support.

This module provides integration with Jira for converting issues
to the canonical project data model.
"""

from .parser import JiraParser

__all__ = ["JiraParser"]
