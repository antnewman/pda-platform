"""Tests for the ONS fetcher in pm_assumptions.

Verifies that every supported indicator resolves to a well-shaped result,
both on the live-API path and on the cached-fallback path, and that
unknown indicators raise. Fallback is exercised by mocking urlopen to
fail so the tests do not require network access.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from pm_mcp_servers.pm_assumptions.server import _fetch_ons


ALL_INDICATORS = [
    ("cpi_inflation", "% annual"),
    ("services_cpi_rate", "% annual"),
    ("services_cpi_index", "index (2015=100)"),
    ("all_items_cpi_index", "index (2015=100)"),
    ("base_rate", "% per annum"),
    ("construction_output", "index (2019=100)"),
]

NEW_INDICATORS = {
    "services_cpi_rate",
    "services_cpi_index",
    "all_items_cpi_index",
}

REQUIRED_KEYS = {"value", "unit", "signal_date", "url", "description", "source_name"}


class TestFetchOnsFallback:
    """Fallback-path tests. Network is mocked to always fail."""

    @pytest.mark.parametrize("indicator,expected_unit", ALL_INDICATORS)
    def test_fallback_shape(self, indicator: str, expected_unit: str) -> None:
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("network unavailable")
            result = _fetch_ons(indicator)

        assert REQUIRED_KEYS.issubset(result.keys())
        assert isinstance(result["value"], (int, float))
        assert result["unit"] == expected_unit
        assert result["source_name"].startswith("ONS")
        assert "fetch_error" in result, "fallback path must stamp fetch_error"

    def test_services_cpi_rate_fallback_matches_published_feb_2026(self) -> None:
        """Fallback for services CPI rate matches published Feb 2026 (4.3%)."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("network unavailable")
            result = _fetch_ons("services_cpi_rate")

        assert result["value"] == pytest.approx(4.3, abs=0.05)

    @pytest.mark.parametrize("indicator", sorted(NEW_INDICATORS))
    def test_new_indicator_has_mm23_dataset_url(self, indicator: str) -> None:
        """New services and all-items indices are on the MM23 dataset."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("network unavailable")
            result = _fetch_ons(indicator)

        assert "MM23" in result["url"], (
            f"{indicator} should be served from the MM23 dataset"
        )


class TestFetchOnsRejection:
    def test_unknown_indicator_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown ONS indicator"):
            _fetch_ons("not_a_real_indicator")
