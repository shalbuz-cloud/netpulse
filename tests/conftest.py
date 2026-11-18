"""Shared pytest fixtures for the netpulse test suite."""

from __future__ import annotations

import pytest
from rich.console import Console

from netpulse.config import Config


@pytest.fixture
def config() -> Config:
    """Return a Config instance with small values for fast tests."""
    return Config(total_requests=3, request_timeout=10, user_agent="Test/1.0")


@pytest.fixture
def console() -> Console:
    """Return a Console instance that records output for inspection."""
    return Console(record=True, width=120)


@pytest.fixture
def mock_transport():
    """Factory fixture for creating httpx.MockTransport instances.

    Usage:
        def test_something(mock_transport):
            transport = mock_transport(handler=lambda req: httpx.Response(200, content=b"ok"))
    """
    import httpx

    def _make(handler):
        return httpx.MockTransport(handler)

    return _make
