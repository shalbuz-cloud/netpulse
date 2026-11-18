"""Tests for netpulse CLI entry point."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from netpulse import main
from netpulse.benchmark import BenchmarkResult


class TestMain:
    """Tests for the main() CLI entry point."""

    def test_no_args_shows_usage_and_exits(self, capsys) -> None:
        """Calling main with no URL prints usage and exits with code 1."""
        with patch.object(sys, "argv", ["netpulse"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1

        captured = capsys.readouterr()
        assert "Usage:" in captured.out
        assert "Example:" in captured.out

    def test_invalid_url_scheme_exits(self, capsys) -> None:
        """Non-http/https URL scheme prints error and exits."""
        with patch.object(sys, "argv", ["netpulse", "ftp://example.com/file"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1

        captured = capsys.readouterr()
        assert "scheme must be http:// or https://" in captured.out

    def test_missing_host_exits(self, capsys) -> None:
        """URL without a host prints error and exits."""
        with patch.object(sys, "argv", ["netpulse", "https://"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1

        captured = capsys.readouterr()
        assert "missing a host" in captured.out

    def test_malformed_url_exits(self, capsys) -> None:
        """Completely malformed URL prints error and exits."""
        with patch.object(sys, "argv", ["netpulse", "not-a-url"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1

        captured = capsys.readouterr()
        assert "URL scheme must be http:// or https://" in captured.out


@pytest.mark.parametrize(
    "result",
    [
        BenchmarkResult(
            total_requests=3,
            success_count=3,
            total_time=1.5,
            total_bytes=3072,
        ),
        BenchmarkResult(
            total_requests=3,
            success_count=1,
            total_time=0.5,
            total_bytes=1024,
            errors=["Request 2/3: 500 Internal Server Error"],
        ),
    ],
)
def test_main_delegates_to_benchmark_and_summary(result: BenchmarkResult) -> None:
    """main() orchestrates run_benchmark and print_summary correctly.

    Both successful and error-containing results are passed through.
    """
    with (
        patch.object(sys, "argv", ["netpulse", "https://example.com/file"]),
        patch("netpulse.run_benchmark", return_value=result) as mock_bench,
        patch("netpulse.print_summary") as mock_print,
    ):
        main()

    mock_bench.assert_called_once()
    mock_print.assert_called_once()
    args, _ = mock_print.call_args
    assert args[0] == result
