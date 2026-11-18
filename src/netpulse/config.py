"""Application configuration."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    """Immutable configuration for the benchmark run.

    Attributes:
        total_requests: Number of sequential HTTP GET requests to perform.
        request_timeout: Per-request timeout in seconds.
        user_agent: HTTP User-Agent header sent with every request.
    """

    total_requests: int = field(default=10)
    request_timeout: float = field(default=30)
    user_agent: str = field(default="NetPulse-Benchmark/1.0")
