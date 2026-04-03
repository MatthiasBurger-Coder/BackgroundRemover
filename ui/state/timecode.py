"""Time and timecode helpers for the Streamlit UI adapter."""

from __future__ import annotations


def format_timecode(timestamp_seconds: float) -> str:
    """Format elapsed seconds as an HH:MM:SS.mmm timecode string."""
    total_milliseconds = max(int(round(timestamp_seconds * 1000)), 0)
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def format_time_seconds_for_frame(*, frame_index: int, fps: float) -> float:
    """Convert a frame index into seconds for the current source FPS."""
    if fps <= 0:
        return 0.0
    return max(frame_index, 0) / fps
