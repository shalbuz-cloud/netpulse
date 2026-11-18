"""NetPulse — CLI benchmark tool for measuring download speed."""

import sys

import httpx
from rich.console import Console

from netpulse.benchmark import print_summary, run_benchmark
from netpulse.config import Config


def main() -> None:
    """Entry point for the ``netpulse`` command.

    Parses a single URL argument from the command line, validates it,
    runs the benchmark, and prints the summary table.
    """
    console = Console()

    if len(sys.argv) != 2:
        console.print("[bold red]Usage:[/bold red] netpulse <URL>")
        console.print("Example: netpulse https://httpbin.org/bytes/1048576")
        sys.exit(1)

    raw_url = sys.argv[1]

    try:
        parsed = httpx.URL(raw_url)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] Invalid URL: {exc}")
        sys.exit(1)

    if parsed.scheme not in ("http", "https"):
        console.print("[bold red]Error:[/bold red] URL scheme must be http:// or https://")
        sys.exit(1)
    if not parsed.host:
        console.print("[bold red]Error:[/bold red] URL is missing a host")
        sys.exit(1)

    cfg = Config()

    console.print(f"▶ Target: [bold]{raw_url}[/bold]")
    console.print(f"▶ Requests: {cfg.total_requests} | Timeout: {cfg.request_timeout}s")
    console.print("─" * 60)

    result = run_benchmark(raw_url, cfg, console)
    print_summary(result, console)


__all__ = ["main"]
