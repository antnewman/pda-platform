"""Monday.com parser for project management data.

Monday.com is an API-driven work management platform. This parser
processes JSON responses from the Monday.com API to extract project data.
"""

from .parser import MondayParser

__all__ = ["MondayParser"]
