"""Playback synchronization helpers for the driving Streamlit UI adapter."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlaybackProgress:
    """Normalized playback/navigation state for the current source asset."""

    frame_index: int
    time_seconds: float
    playback_running: bool
    playback_anchor_frame_index: int | None = None
    playback_started_at_seconds: float | None = None


def build_navigation_position(*, frame_index: int, frame_count: int, fps: float) -> PlaybackProgress:
    """Build a paused navigation position with synchronized frame/time values."""
    clamped_frame_index = clamp_frame_index(frame_index, frame_count)
    return PlaybackProgress(
        frame_index=clamped_frame_index,
        time_seconds=frame_index_to_time_seconds(clamped_frame_index, fps),
        playback_running=False,
    )


def step_navigation_position(
    *,
    current_frame_index: int,
    step: int,
    frame_count: int,
    fps: float,
) -> PlaybackProgress:
    """Move the current navigation position by a signed frame step."""
    return build_navigation_position(
        frame_index=current_frame_index + step,
        frame_count=frame_count,
        fps=fps,
    )


def start_playback(
    *,
    current_frame_index: int,
    frame_count: int,
    fps: float,
    now_seconds: float,
) -> PlaybackProgress:
    """Start playback from the current synchronized frame position."""
    if frame_count <= 0:
        return build_navigation_position(frame_index=0, frame_count=0, fps=fps)

    start_frame_index = clamp_frame_index(current_frame_index, frame_count)
    if start_frame_index >= frame_count - 1:
        start_frame_index = 0

    return PlaybackProgress(
        frame_index=start_frame_index,
        time_seconds=frame_index_to_time_seconds(start_frame_index, fps),
        playback_running=True,
        playback_anchor_frame_index=start_frame_index,
        playback_started_at_seconds=now_seconds,
    )


def stop_playback(*, current_frame_index: int, frame_count: int, fps: float) -> PlaybackProgress:
    """Stop playback and preserve the synchronized frame position."""
    return build_navigation_position(
        frame_index=current_frame_index,
        frame_count=frame_count,
        fps=fps,
    )


def advance_playback_position(
    *,
    playback_running: bool,
    current_frame_index: int,
    frame_count: int,
    fps: float,
    playback_started_at_seconds: float | None,
    playback_anchor_frame_index: int | None,
    now_seconds: float,
) -> PlaybackProgress:
    """Advance synchronized playback based on elapsed wall-clock time."""
    if not playback_running:
        return build_navigation_position(
            frame_index=current_frame_index,
            frame_count=frame_count,
            fps=fps,
        )

    if frame_count <= 0 or fps <= 0 or playback_started_at_seconds is None or playback_anchor_frame_index is None:
        return stop_playback(
            current_frame_index=current_frame_index,
            frame_count=frame_count,
            fps=fps,
        )

    elapsed_seconds = max(now_seconds - playback_started_at_seconds, 0.0)
    advanced_frames = int(elapsed_seconds * fps)
    next_frame_index = clamp_frame_index(playback_anchor_frame_index + advanced_frames, frame_count)

    if next_frame_index >= frame_count - 1:
        return PlaybackProgress(
            frame_index=frame_count - 1,
            time_seconds=frame_index_to_time_seconds(frame_count - 1, fps),
            playback_running=False,
        )

    return PlaybackProgress(
        frame_index=next_frame_index,
        time_seconds=frame_index_to_time_seconds(next_frame_index, fps),
        playback_running=True,
        playback_anchor_frame_index=playback_anchor_frame_index,
        playback_started_at_seconds=playback_started_at_seconds,
    )


def clamp_frame_index(frame_index: int, frame_count: int) -> int:
    """Clamp a frame index into the valid range for the current asset."""
    if frame_count <= 0:
        return 0
    return max(0, min(int(frame_index), frame_count - 1))


def frame_index_to_time_seconds(frame_index: int, fps: float) -> float:
    """Convert a synchronized frame index into a playback timestamp."""
    if fps <= 0:
        return 0.0
    return max(frame_index, 0) / fps
