"""MSPDI (Microsoft Project XML) schema support.

This module provides parsing and writing capabilities for Microsoft Project
XML files using the MSPDI (Microsoft Project Data Interchange) schema.
"""

from .parser import MspdiParser
from .writer import MspdiWriter

__all__ = ["MspdiParser", "MspdiWriter"]
