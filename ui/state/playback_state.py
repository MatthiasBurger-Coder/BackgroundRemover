"""Playback context helpers for the Streamlit UI adapter."""

from __future__ import annotations

import logging
import time

import streamlit as st
from src.application.adapters.incoming.ui.playback_session import (
    PlaybackProgress,
    advance_playback_position,
    build_navigation_position,
    start_playback,
    step_navigation_position,
    stop_playback,
)

from ui.state.generation_state import bump_playback_generation

LOGGER = logging.getLogger(__name__)


def sync_playback_position(now_seconds: float | None = None) -> None:
    """Advance the preview playback context using wall-clock time while playback is running."""
    if not st.session_state.playback_running:
        return

    previous_frame_index = int(st.session_state.playback_frame_index)
    was_running = bool(st.session_state.playback_running)
    progress = advance_playback_position(
        playback_running=st.session_state.playback_running,
        current_frame_index=st.session_state.playback_frame_index,
        frame_count=st.session_state.video_frame_count,
        fps=st.session_state.video_fps,
        playback_started_at_seconds=st.session_state.playback_started_at_seconds,
        playback_anchor_frame_index=st.session_state.playback_anchor_frame_index,
        now_seconds=time.monotonic() if now_seconds is None else now_seconds,
    )
    apply_playback_progress(progress)
    if progress.playback_running:
        LOGGER.debug(
            "Preview updated frame_index=%s previous_frame_index=%s playback_running=%s",
            progress.frame_index,
            previous_frame_index,
            progress.playback_running,
        )
        LOGGER.debug(
            "Workbench unchanged during playback frame_index=%s timecode=%.3f",
            st.session_state.workbench_frame_index,
            st.session_state.workbench_timestamp_seconds,
        )
        st.session_state.last_action = f"Playback running at frame {progress.frame_index:04d}"
        return

    if was_running:
        _adopt_preview_frame_into_workbench(reason="playback_stopped")
        bump_playback_generation("playback_stopped")
    LOGGER.info(
        "Playback stopped frame_index=%s previous_frame_index=%s",
        progress.frame_index,
        previous_frame_index,
    )
    st.session_state.last_action = f"Playback paused at frame {progress.frame_index:04d}"


def clamp_current_frame_index(frame_index: int) -> int:
    """Clamp a frame index into the valid range for the active source asset."""
    frame_count = int(st.session_state.video_frame_count)
    if frame_count <= 0:
        return 0
    return max(0, min(int(frame_index), frame_count - 1))


def sync_current_frame_index() -> None:
    set_current_frame_index(st.session_state.playback_frame_index)


def sync_source_timeline_frame_index() -> None:
    """Seek the preview playback context from the dedicated source-timeline widget state."""
    set_current_frame_index(int(st.session_state.source_timeline_frame_index))


def sync_source_timeline_widget_state() -> None:
    """Mirror the preview frame into the source-timeline widget state during full reruns."""
    st.session_state.source_timeline_frame_index = int(st.session_state.playback_frame_index)


def set_current_frame_index(frame_index: int) -> None:
    """Seek preview playback to a specific frame and adopt it into the workbench snapshot."""
    was_running = bool(st.session_state.playback_running)
    progress = build_navigation_position(
        frame_index=frame_index,
        frame_count=st.session_state.video_frame_count,
        fps=st.session_state.video_fps,
    )
    apply_playback_progress(progress)
    if was_running and not progress.playback_running:
        bump_playback_generation("playback_stopped")
    _adopt_preview_frame_into_workbench(reason="frame_selected")
    LOGGER.info("Selected frame frame_index=%s time_seconds=%.3f", progress.frame_index, progress.time_seconds)
    st.session_state.last_action = f"Selected frame {progress.frame_index:04d}"


def jump_to_first_frame() -> None:
    set_current_frame_index(0)


def jump_to_last_frame() -> None:
    if st.session_state.video_frame_count <= 0:
        return
    set_current_frame_index(st.session_state.video_frame_count - 1)


def step_current_frame(step: int) -> None:
    """Step preview playback by a signed number of frames and adopt the new workbench snapshot."""
    was_running = bool(st.session_state.playback_running)
    progress = step_navigation_position(
        current_frame_index=st.session_state.playback_frame_index,
        step=step,
        frame_count=st.session_state.video_frame_count,
        fps=st.session_state.video_fps,
    )
    apply_playback_progress(progress)
    if was_running and not progress.playback_running:
        bump_playback_generation("playback_stopped")
    _adopt_preview_frame_into_workbench(reason="frame_stepped")
    st.session_state.last_action = f"Selected frame {progress.frame_index:04d}"


def toggle_playback() -> None:
    """Toggle the preview playback context between running and paused states."""
    if not st.session_state.video_loaded or st.session_state.video_frame_count <= 0:
        LOGGER.warning("Ignoring playback toggle without active video")
        return

    now_seconds = time.monotonic()
    was_running = bool(st.session_state.playback_running)
    if st.session_state.playback_running:
        sync_playback_position(now_seconds=now_seconds)
        progress = stop_playback(
            current_frame_index=st.session_state.playback_frame_index,
            frame_count=st.session_state.video_frame_count,
            fps=st.session_state.video_fps,
        )
    else:
        progress = start_playback(
            current_frame_index=st.session_state.playback_frame_index,
            frame_count=st.session_state.video_frame_count,
            fps=st.session_state.video_fps,
            now_seconds=now_seconds,
        )

    apply_playback_progress(progress)
    if not was_running and progress.playback_running:
        bump_playback_generation("playback_started")
        LOGGER.info(
            "Playback started frame_index=%s anchor=%s started_at=%s",
            progress.frame_index,
            progress.playback_anchor_frame_index,
            progress.playback_started_at_seconds,
        )
    elif was_running and not progress.playback_running:
        _adopt_preview_frame_into_workbench(reason="playback_stopped")
        bump_playback_generation("playback_stopped")
        LOGGER.info(
            "Playback stopped frame_index=%s anchor=%s started_at=%s",
            progress.frame_index,
            progress.playback_anchor_frame_index,
            progress.playback_started_at_seconds,
        )
    state_label = "Running" if progress.playback_running else "Paused"
    st.session_state.last_action = f"Playback {state_label.lower()} at frame {progress.frame_index:04d}"


def get_playback_interval_seconds() -> float:
    """Resolve the fragment auto-rerun interval from the active source FPS."""
    fps = float(st.session_state.video_fps)
    if fps <= 0:
        return 0.25
    preview_fps = min(fps, 4.0)
    return max(1.0 / preview_fps, 0.15)


def reset_playback_state() -> None:
    """Reset the preview playback context to a paused state."""
    st.session_state.playback_running = False
    st.session_state.playback_anchor_frame_index = None
    st.session_state.playback_started_at_seconds = None
    st.session_state.playback_frame_index = 0
    st.session_state.playback_timestamp_seconds = 0.0
    st.session_state.source_timeline_frame_index = 0


def apply_playback_progress(progress: PlaybackProgress) -> None:
    """Write normalized preview playback progress into session state."""
    st.session_state.playback_frame_index = progress.frame_index
    st.session_state.playback_timestamp_seconds = progress.time_seconds
    st.session_state.playback_running = progress.playback_running
    st.session_state.playback_anchor_frame_index = progress.playback_anchor_frame_index
    st.session_state.playback_started_at_seconds = progress.playback_started_at_seconds


def _adopt_preview_frame_into_workbench(*, reason: str) -> None:
    from ui.state.workbench_state import adopt_playback_frame_to_workbench

    adopt_playback_frame_to_workbench(reason=reason)
