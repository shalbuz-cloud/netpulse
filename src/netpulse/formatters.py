"""Unit formatting helpers for byte counts and transfer speeds."""

from typing import Final

_KIB: Final[float] = 1024.0
_MIB: Final[float] = _KIB * _KIB
_GIB: Final[float] = _MIB * _KIB


def format_size(num_bytes: int | float) -> str:
    """Format a byte count into a human-readable string using binary units.

    Args:
        num_bytes: Number of bytes to format.

    Returns:
        A string such as "1.50 MiB", "45.00 KiB", or "512 B".
    """
    if num_bytes < 0:
        return "0.00 B"
    if num_bytes < _KIB:
        return f"{num_bytes:.0f} B"
    if num_bytes < _MIB:
        return f"{num_bytes / _KIB:.2f} KiB"
    if num_bytes < _GIB:
        return f"{num_bytes / _MIB:.2f} MiB"
    return f"{num_bytes / _GIB:.2f} GiB"


def format_speed(bytes_per_second: float) -> str:
    """Format a transfer speed into a human-readable string using binary units.

    Args:
        bytes_per_second: Speed in bytes per second.

    Returns:
        A string such as "4.27 MiB/s" or "15.34 KiB/s".
    """
    if bytes_per_second < 0:
        return "0.00 B/s"
    if bytes_per_second < _KIB:
        return f"{bytes_per_second:.2f} B/s"
    return f"{format_size(bytes_per_second)}/s"
