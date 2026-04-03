"""Workbench projection models for the Streamlit UI adapter."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class WorkbenchProjection:
    """Stable workbench input derived from source and editing contexts."""

    asset_id: str | None
    video_loaded: bool
    video_name: str
    video_fps: float
    video_frame_count: int
    workbench_frame_index: int
    workbench_timestamp_seconds: float
    playback_running: bool
    workbench_frame_request_key: tuple[str, int] | None
    workbench_frame_image_bytes: bytes | None
    workbench_frame_image_mime_type: str | None
    workbench_frame_error_message: str | None
    preview_generation: int
    prompt_count: int
    mask_threshold: float
    mask_feather: int
    mask_invert: bool
    show_debug_overlay: bool


def build_workbench_projection() -> WorkbenchProjection:
    """Build the current workbench projection from session state."""
    return WorkbenchProjection(
        asset_id=st.session_state.get("active_asset_id") or st.session_state.get("asset_id"),
        video_loaded=bool(st.session_state.video_loaded),
        video_name=str(st.session_state.video_name),
        video_fps=float(st.session_state.video_fps),
        video_frame_count=int(st.session_state.video_frame_count),
        workbench_frame_index=int(st.session_state.workbench_frame_index),
        workbench_timestamp_seconds=float(st.session_state.workbench_timestamp_seconds),
        playback_running=bool(st.session_state.playback_running),
        workbench_frame_request_key=st.session_state.workbench_frame_request_key,
        workbench_frame_image_bytes=st.session_state.workbench_frame_image_bytes,
        workbench_frame_image_mime_type=st.session_state.workbench_frame_image_mime_type,
        workbench_frame_error_message=st.session_state.workbench_frame_error_message,
        preview_generation=int(st.session_state.preview_generation),
        prompt_count=len(st.session_state.prompt_entries),
        mask_threshold=float(st.session_state.mask_threshold),
        mask_feather=int(st.session_state.mask_feather),
        mask_invert=bool(st.session_state.mask_invert),
        show_debug_overlay=bool(st.session_state.show_debug_overlay),
    )
