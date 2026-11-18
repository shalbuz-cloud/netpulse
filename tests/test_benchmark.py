"""Tests for netpulse.benchmark."""

from __future__ import annotations

import httpx
import pytest

from netpulse.benchmark import BenchmarkResult, run_benchmark
from netpulse.config import Config


class TestBenchmarkResult:
    """Tests for the BenchmarkResult dataclass and its computed properties."""

    @pytest.mark.parametrize(
        "success_count, total_time, total_bytes, expected_avg_time, expected_avg_speed",
        [
            (0, 0.0, 0, 0.0, 0.0),
            (1, 2.0, 1024, 2.0, 512.0),
            (5, 10.0, 5120, 2.0, 512.0),
            (10, 5.0, 10485760, 0.5, 2097152.0),
        ],
    )
    def test_avg_time_and_speed(
        self,
        success_count: int,
        total_time: float,
        total_bytes: int,
        expected_avg_time: float,
        expected_avg_speed: float,
    ) -> None:
        """avg_time and avg_speed compute correctly for various inputs."""
        result = BenchmarkResult(
            total_requests=10,
            success_count=success_count,
            total_time=total_time,
            total_bytes=total_bytes,
        )
        assert result.avg_time == pytest.approx(expected_avg_time)
        assert result.avg_speed == pytest.approx(expected_avg_speed)

    def test_errors_list_defaults_to_empty(self) -> None:
        """errors list is empty by default."""
        result = BenchmarkResult(
            total_requests=10,
            success_count=0,
            total_time=0.0,
            total_bytes=0,
        )
        assert result.errors == []


class TestRunBenchmark:
    """Integration-style tests for run_benchmark using httpx.MockTransport."""

    @pytest.fixture
    def config(self) -> Config:
        return Config(total_requests=3, request_timeout=10, user_agent="Test/1.0")

    @pytest.fixture
    def console(self):
        from rich.console import Console

        return Console(record=True, width=120)

    def _make_transport(self, status_code: int = 200, body: bytes = b"x" * 1024):
        """Create a mock transport that returns the given response."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=status_code,
                content=body,
                headers={"Content-Length": str(len(body))},
            )

        return httpx.MockTransport(handler)

    def test_run_benchmark_all_success(self, config: Config, console) -> None:
        """All requests succeed; metrics are accumulated correctly."""
        body = b"x" * 1024  # 1 KiB
        transport = self._make_transport(200, body)
        result = run_benchmark("https://example.com/file", config, console, transport)

        assert result.success_count == config.total_requests
        assert result.total_bytes == len(body) * config.total_requests
        assert result.total_time > 0.0
        assert result.avg_time > 0.0
        assert result.avg_speed > 0.0
        assert result.errors == []

    def test_run_benchmark_partial_failure(self, config: Config, console) -> None:
        """Some requests fail; successes are still counted."""
        # Request 1 and 3 succeed, request 2 fails with 500
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return httpx.Response(500, content=b"Internal Server Error")
            return httpx.Response(200, content=b"ok")

        transport = httpx.MockTransport(handler)
        result = run_benchmark("https://example.com/file", config, console, transport)

        assert result.success_count == 2
        assert len(result.errors) == 1
        assert "500" in result.errors[0]

    def test_run_benchmark_timeout(self, config: Config, console) -> None:
        """Timeout is recorded as an error."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("Request timed out")

        transport = httpx.MockTransport(handler)
        result = run_benchmark("https://example.com/file", config, console, transport)

        assert result.success_count == 0
        assert len(result.errors) == config.total_requests
        assert all("timed out" in e.lower() or "timeout" in e.lower() for e in result.errors)

    def test_run_benchmark_network_error(self, config: Config, console) -> None:
        """Network errors (e.g., ConnectError) are recorded."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        transport = httpx.MockTransport(handler)
        result = run_benchmark("https://example.com/file", config, console, transport)

        assert result.success_count == 0
        assert len(result.errors) == config.total_requests

    def test_run_benchmark_byte_counting(self, config: Config, console) -> None:
        """Body bytes are counted correctly even with chunked streaming."""
        chunks = [b"a" * 100, b"b" * 200, b"c" * 300]
        expected_total = sum(len(c) for c in chunks)
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(200, content=b"".join(chunks))

        transport = httpx.MockTransport(handler)
        result = run_benchmark("https://example.com/file", config, console, transport)

        assert result.total_bytes == expected_total * config.total_requests
