"""Video metadata state application for the Streamlit UI adapter."""

from __future__ import annotations

import logging

import streamlit as st
from application.adapters.incoming.ui.playback_session import build_navigation_position
from application.domain.model.video_asset import VideoAssetMetadata

from ui.state.playback_state import apply_playback_progress, clamp_current_frame_index
from ui.state.timecode import format_time_seconds_for_frame
from ui.state.workbench_state import reset_workbench_frame_state, set_workbench_frame_position

LOGGER = logging.getLogger(__name__)


def apply_video_metadata_state(
    *,
    metadata: VideoAssetMetadata,
    reset_prompts: bool,
) -> None:
    """Apply metadata for a newly activated source asset."""
    LOGGER.debug(
        "Applying video metadata asset_id=%s video_name=%s frame_count=%s fps=%.3f reset_prompts=%s",
        metadata.asset_id,
        metadata.filename,
        metadata.frame_count,
        metadata.fps,
        reset_prompts,
    )
    st.session_state.video_loaded = True
    st.session_state.asset_id = metadata.asset_id
    st.session_state.video_fps = metadata.fps
    st.session_state.video_frame_count = metadata.frame_count
    st.session_state.video_duration_seconds = metadata.duration_seconds
    st.session_state.video_width = metadata.width
    st.session_state.video_height = metadata.height
    progress = build_navigation_position(
        frame_index=0,
        frame_count=metadata.frame_count,
        fps=metadata.fps,
    )
    apply_playback_progress(progress)
    st.session_state.source_timeline_frame_index = progress.frame_index
    set_workbench_frame_position(
        frame_index=progress.frame_index,
        timestamp_seconds=progress.time_seconds,
        invalidate_cache=True,
    )
    st.session_state.workbench_frame_width = metadata.width
    st.session_state.workbench_frame_height = metadata.height
    if reset_prompts:
        st.session_state.prompt_entries = []


def refresh_video_metadata_state(*, metadata: VideoAssetMetadata) -> None:
    """Refresh metadata for the active source asset without resetting preview or workbench positions."""
    previous_playback_frame_index = int(st.session_state.playback_frame_index)
    previous_workbench_frame_index = int(st.session_state.workbench_frame_index)
    LOGGER.debug(
        "Refreshing metadata without reset asset_id=%s playback_frame_index=%s workbench_frame_index=%s playback_running=%s",
        metadata.asset_id,
        previous_playback_frame_index,
        previous_workbench_frame_index,
        st.session_state.playback_running,
    )
    st.session_state.video_loaded = True
    st.session_state.asset_id = metadata.asset_id
    st.session_state.video_fps = metadata.fps
    st.session_state.video_frame_count = metadata.frame_count
    st.session_state.video_duration_seconds = metadata.duration_seconds
    st.session_state.video_width = metadata.width
    st.session_state.video_height = metadata.height
    st.session_state.workbench_frame_width = metadata.width
    st.session_state.workbench_frame_height = metadata.height

    clamped_playback_frame_index = clamp_current_frame_index(previous_playback_frame_index)
    if clamped_playback_frame_index != previous_playback_frame_index:
        progress = build_navigation_position(
            frame_index=clamped_playback_frame_index,
            frame_count=metadata.frame_count,
            fps=metadata.fps,
        )
        apply_playback_progress(progress)
        st.session_state.source_timeline_frame_index = progress.frame_index
    elif not st.session_state.playback_running:
        st.session_state.playback_timestamp_seconds = format_time_seconds_for_frame(
            frame_index=clamped_playback_frame_index,
            fps=metadata.fps,
        )

    clamped_workbench_frame_index = clamp_current_frame_index(previous_workbench_frame_index)
    workbench_timestamp_seconds = format_time_seconds_for_frame(
        frame_index=clamped_workbench_frame_index,
        fps=metadata.fps,
    )
    set_workbench_frame_position(
        frame_index=clamped_workbench_frame_index,
        timestamp_seconds=workbench_timestamp_seconds,
        invalidate_cache=clamped_workbench_frame_index != previous_workbench_frame_index,
    )
    if not st.session_state.video_loaded:
        reset_workbench_frame_state(reset_position=True)


def has_complete_video_metadata() -> bool:
    """Return whether the active source metadata is complete enough for reuse."""
    return bool(
        st.session_state.video_loaded
        and (st.session_state.get("active_asset_id") or st.session_state.get("asset_id")) is not None
        and float(st.session_state.video_fps) > 0
        and int(st.session_state.video_frame_count) > 0
        and int(st.session_state.video_width) > 0
        and int(st.session_state.video_height) > 0
    )
