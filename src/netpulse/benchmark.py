"""Core benchmark logic for sequential HTTP GET requests."""

import time
from dataclasses import dataclass, field

import httpx
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from netpulse.config import Config
from netpulse.formatters import format_size, format_speed


@dataclass
class BenchmarkResult:
    """Holds aggregated metrics from a benchmark run.

    Attributes:
        total_requests: Total number of requests attempted.
        success_count: Number of successful requests.
        total_time: Sum of all successful request durations, in seconds.
        total_bytes: Total bytes downloaded across all successful requests.
        errors: Human-readable error messages for failed requests.
    """

    total_requests: int
    success_count: int
    total_time: float
    total_bytes: int
    errors: list[str] = field(default_factory=list)

    @property
    def avg_time(self) -> float:
        """Average duration of a single successful request, in seconds."""
        if self.success_count == 0:
            return 0.0
        return self.total_time / self.success_count

    @property
    def avg_speed(self) -> float:
        """Average download speed in bytes per second."""
        if self.total_time <= 0:
            return 0.0
        return self.total_bytes / self.total_time


def run_benchmark(
    url: str,
    config: Config,
    console: Console,
) -> BenchmarkResult:
    """Execute sequential HTTP GET requests and collect performance metrics.

    Sends exactly ``config.TOTAL_REQUESTS`` requests, each starting only
    after the previous response body has been fully read. Uses a single
    connection with keep-alive disabled to avoid any caching.

    Args:
        url: The target URL to benchmark.
        config: Application configuration values.
        console: Rich console used to render the progress bar.

    Returns:
        BenchmarkResult with aggregated metrics and any errors encountered.
    """
    result = BenchmarkResult(
        total_requests=config.total_requests,
        success_count=0,
        total_time=0,
        total_bytes=0,
    )

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    )
    task_id = progress.add_task("Benchmarking", total=config.total_requests)

    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "User-Agent": config.user_agent,
    }

    with (
        progress,
        httpx.Client(
            limits=httpx.Limits(max_connections=1, max_keepalive_connections=1),
            timeout=httpx.Timeout(config.request_timeout),
            follow_redirects=True,
        ) as client,
    ):
        for i in range(1, config.total_requests + 1):
            start = time.perf_counter()
            try:
                size = 0
                with client.stream("GET", url, headers=headers) as response:
                    response.raise_for_status()
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                elapsed = time.perf_counter() - start

                result.success_count += 1
                result.total_time += elapsed
                result.total_bytes += size

                speed = size / elapsed if elapsed > 0 else 0.0
                progress.update(
                    task_id,
                    description=(
                        f"Request {i}/{config.total_requests}: "
                        f"{elapsed:.3f}s | {format_size(size)} | "
                        f"{format_speed(speed)}"
                    ),
                    advance=1,
                )
            except httpx.HTTPError as exc:
                elapsed = time.perf_counter() - start
                msg = f"Request {i}/{config.total_requests}: {exc}"
                result.errors.append(msg)
                progress.update(
                    task_id,
                    description=(f"Request {i}/{config.total_requests}: ERROR ({elapsed:.3f}s)"),
                    advance=1,
                )
    return result


def print_summary(result: BenchmarkResult, console: Console) -> None:
    """Render the final summary table to the console.

    Args:
        result: The benchmark result to display.
        console: Rich console to render through.
    """
    if result.errors:
        console.print("\n[bold red] Completed with errors:[/bold red]")
        for err in result.errors:
            console.print(f"  [red]• {err}[/red]")

    if result.success_count == 0:
        console.print("\n[bold red] All requests failed.[/bold red]")
        return

    table = Table(title="Benchmark Summary", box=None)
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", style="bold green")
    table.add_row("Successful requests", f"{result.success_count}/{result.total_requests}")
    table.add_row("Total time", f"{result.total_time:.3f} s")
    table.add_row("Average request time", f"{result.avg_time:.3f} s")
    table.add_row("Total bytes downloaded", format_size(result.total_bytes))
    table.add_row("Average downloaded speed", format_speed(result.avg_speed))
    console.print(table)
