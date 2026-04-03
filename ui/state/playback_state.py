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
    """Advance the playback context using wall-clock time while playback is running."""
    if not st.session_state.playback_running:
        return

    previous_frame_index = int(st.session_state.current_frame_index)
    was_running = bool(st.session_state.playback_running)
    progress = advance_playback_position(
        playback_running=st.session_state.playback_running,
        current_frame_index=st.session_state.current_frame_index,
        frame_count=st.session_state.video_frame_count,
        fps=st.session_state.video_fps,
        playback_started_at_seconds=st.session_state.playback_started_at_seconds,
        playback_anchor_frame_index=st.session_state.playback_anchor_frame_index,
        now_seconds=time.monotonic() if now_seconds is None else now_seconds,
    )
    apply_playback_progress(progress)
    st.session_state.current_frame_request_key = None
    st.session_state.frame_error_message = None
    if was_running and not progress.playback_running:
        bump_playback_generation("playback_stopped")
    LOGGER.debug(
        "Synchronized playback frame_index=%s previous_frame_index=%s playback_running=%s",
        progress.frame_index,
        previous_frame_index,
        progress.playback_running,
    )
    if progress.playback_running:
        st.session_state.last_action = f"Playback running at frame {progress.frame_index:04d}"
    else:
        st.session_state.last_action = f"Playback paused at frame {progress.frame_index:04d}"


def clamp_current_frame_index(frame_index: int) -> int:
    """Clamp a frame index into the valid range for the active source asset."""
    frame_count = int(st.session_state.video_frame_count)
    if frame_count <= 0:
        return 0
    return max(0, min(int(frame_index), frame_count - 1))


def sync_current_frame_index() -> None:
    set_current_frame_index(st.session_state.current_frame_index)


def sync_source_timeline_frame_index() -> None:
    """Seek the playback context from the dedicated source-timeline widget state."""
    set_current_frame_index(int(st.session_state.source_timeline_frame_index))


def sync_source_timeline_widget_state() -> None:
    """Mirror the current playback frame into the source-timeline widget state."""
    st.session_state.source_timeline_frame_index = int(st.session_state.current_frame_index)


def set_current_frame_index(frame_index: int) -> None:
    """Seek the playback context to a specific frame and pause playback."""
    was_running = bool(st.session_state.playback_running)
    progress = build_navigation_position(
        frame_index=frame_index,
        frame_count=st.session_state.video_frame_count,
        fps=st.session_state.video_fps,
    )
    apply_playback_progress(progress)
    st.session_state.current_frame_request_key = None
    st.session_state.frame_error_message = None
    if was_running and not progress.playback_running:
        bump_playback_generation("playback_stopped")
    LOGGER.info("Selected frame frame_index=%s time_seconds=%.3f", progress.frame_index, progress.time_seconds)
    st.session_state.last_action = f"Selected frame {progress.frame_index:04d}"


def jump_to_first_frame() -> None:
    set_current_frame_index(0)


def jump_to_last_frame() -> None:
    if st.session_state.video_frame_count <= 0:
        return
    set_current_frame_index(st.session_state.video_frame_count - 1)


def step_current_frame(step: int) -> None:
    """Step the playback context by a signed number of frames and pause playback."""
    was_running = bool(st.session_state.playback_running)
    progress = step_navigation_position(
        current_frame_index=st.session_state.current_frame_index,
        step=step,
        frame_count=st.session_state.video_frame_count,
        fps=st.session_state.video_fps,
    )
    apply_playback_progress(progress)
    st.session_state.current_frame_request_key = None
    st.session_state.frame_error_message = None
    if was_running and not progress.playback_running:
        bump_playback_generation("playback_stopped")
    st.session_state.last_action = f"Selected frame {progress.frame_index:04d}"


def toggle_playback() -> None:
    """Toggle the playback context between running and paused states."""
    if not st.session_state.video_loaded or st.session_state.video_frame_count <= 0:
        LOGGER.warning("Ignoring playback toggle without active video")
        return

    now_seconds = time.monotonic()
    was_running = bool(st.session_state.playback_running)
    if st.session_state.playback_running:
        sync_playback_position(now_seconds=now_seconds)
        progress = stop_playback(
            current_frame_index=st.session_state.current_frame_index,
            frame_count=st.session_state.video_frame_count,
            fps=st.session_state.video_fps,
        )
    else:
        progress = start_playback(
            current_frame_index=st.session_state.current_frame_index,
            frame_count=st.session_state.video_frame_count,
            fps=st.session_state.video_fps,
            now_seconds=now_seconds,
        )

    apply_playback_progress(progress)
    st.session_state.current_frame_request_key = None
    st.session_state.frame_error_message = None
    if not was_running and progress.playback_running:
        bump_playback_generation("playback_started")
    elif was_running and not progress.playback_running:
        bump_playback_generation("playback_stopped")
    state_label = "Running" if progress.playback_running else "Paused"
    LOGGER.info(
        "Playback toggled new_state=%s frame_index=%s anchor=%s started_at=%s",
        state_label.lower(),
        progress.frame_index,
        progress.playback_anchor_frame_index,
        progress.playback_started_at_seconds,
    )
    st.session_state.last_action = f"Playback {state_label.lower()} at frame {progress.frame_index:04d}"


def get_playback_interval_seconds() -> float:
    """Resolve the fragment auto-rerun interval from the active source FPS."""
    fps = float(st.session_state.video_fps)
    if fps <= 0:
        return 0.25
    preview_fps = min(fps, 4.0)
    return max(1.0 / preview_fps, 0.15)


def reset_playback_state() -> None:
    """Reset the playback context to a paused state."""
    st.session_state.playback_running = False
    st.session_state.playback_anchor_frame_index = None
    st.session_state.playback_started_at_seconds = None


def apply_playback_progress(progress: PlaybackProgress) -> None:
    """Write normalized playback progress into session state."""
    st.session_state.current_frame_index = progress.frame_index
    st.session_state.current_frame_timestamp_seconds = progress.time_seconds
    st.session_state.playback_running = progress.playback_running
    st.session_state.playback_anchor_frame_index = progress.playback_anchor_frame_index
    st.session_state.playback_started_at_seconds = progress.playback_started_at_seconds
