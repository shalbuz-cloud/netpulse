"""Tests for netpulse.formatters."""

from __future__ import annotations

import pytest

from netpulse.formatters import format_size, format_speed


class TestFormatSize:
    """Positive and negative cases for format_size."""

    @pytest.mark.parametrize(
        "num_bytes, expected",
        [
            (0, "0 B"),
            (1, "1 B"),
            (512, "512 B"),
            (1023, "1023 B"),
            (1024, "1.00 KiB"),
            (1536, "1.50 KiB"),
            (1048576, "1.00 MiB"),
            (1572864, "1.50 MiB"),
            (1073741824, "1.00 GiB"),
            (1610612736, "1.50 GiB"),
        ],
    )
    def test_format_size_positive(self, num_bytes: int | float, expected: str) -> None:
        """format_size returns correct binary-unit strings for valid inputs."""
        assert format_size(num_bytes) == expected

    @pytest.mark.parametrize("num_bytes", [-1, -1024, -1048576])
    def test_format_size_negative(self, num_bytes: int | float) -> None:
        """Negative inputs are clamped to '0.00 B'."""
        assert format_size(num_bytes) == "0.00 B"


class TestFormatSpeed:
    """Positive and negative cases for format_speed."""

    @pytest.mark.parametrize(
        "bps, expected",
        [
            (0, "0.00 B/s"),
            (1, "1.00 B/s"),
            (512, "512.00 B/s"),
            (1024, "1.00 KiB/s"),
            (1536, "1.50 KiB/s"),
            (1048576, "1.00 MiB/s"),
            (1572864, "1.50 MiB/s"),
            (1073741824, "1.00 GiB/s"),
        ],
    )
    def test_format_speed_positive(self, bps: float, expected: str) -> None:
        """format_speed returns correct binary-unit strings for valid inputs."""
        assert format_speed(bps) == expected

    @pytest.mark.parametrize("bps", [-1.0, -1024.0, -1048576.0])
    def test_format_speed_negative(self, bps: float) -> None:
        """Negative speeds are clamped to '0.00 B/s'."""
        assert format_speed(bps) == "0.00 B/s"
