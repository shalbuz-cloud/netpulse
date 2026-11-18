"""Tests for netpulse.config."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from netpulse.config import Config


class TestConfigDefaults:
    """Verify default values of the frozen Config dataclass."""

    def test_defaults(self) -> None:
        """Config() returns expected default values."""
        cfg = Config()
        assert cfg.total_requests == 10
        assert cfg.request_timeout == 30
        assert cfg.user_agent == "NetPulse-Benchmark/1.0"


class TestConfigFrozen:
    """Verify that Config is immutable."""

    def test_frozen_blocks_mutation(self) -> None:
        """Attempting to mutate a Config field raises FrozenInstanceError."""
        cfg = Config()
        with pytest.raises(FrozenInstanceError):
            cfg.total_requests = 5  # type: ignore[misc]

    def test_frozen_blocks_all_fields(self) -> None:
        """All fields are protected from mutation."""
        cfg = Config()
        with pytest.raises(FrozenInstanceError):
            cfg.request_timeout = 60  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            cfg.user_agent = "Other"  # type: ignore[misc]


class TestConfigCustom:
    """Verify that custom values can be supplied at construction time."""

    def test_custom_values(self) -> None:
        """Config accepts non-default values."""
        cfg = Config(total_requests=5, request_timeout=10, user_agent="Test/1.0")
        assert cfg.total_requests == 5
        assert cfg.request_timeout == 10
        assert cfg.user_agent == "Test/1.0"
