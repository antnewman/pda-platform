"""Shared test fixtures for PM Data Tools test suite.

This module provides reusable pytest fixtures for testing models, schemas,
validators, and CLI commands.
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

# Fixtures will be added as models are built
# For now, provide basic test utilities


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def mspdi_fixtures_dir(fixtures_dir: Path) -> Path:
    """Path to MSPDI test fixtures."""
    return fixtures_dir / "mspdi"


# Example fixture structure (to be expanded):
# @pytest.fixture
# def simple_project():
#     """A simple test project with basic tasks."""
#     pass
#
# @pytest.fixture
# def complex_project():
#     """A complex test project with all entity types."""
#     pass
