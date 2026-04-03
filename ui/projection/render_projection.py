"""Render-projection model for the workbench UI."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class RenderProjection:
    """Stable render input for the workbench and related preview surfaces."""

    video_loaded: bool
    asset_id: str | None
    video_name: str
    frame_index: int
    timestamp_seconds: float
    playback_running: bool
    frame_request_key: tuple[str, int] | None
    frame_image_bytes: bytes | None
    frame_image_mime_type: str | None
    frame_error_message: str | None
    show_debug_overlay: bool
    mask_threshold: float
    mask_feather: int
    mask_invert: bool
    preview_generation: int
    prompt_count: int
    video_fps: float
    video_frame_count: int


def build_render_projection() -> RenderProjection:
    """Build a workbench render projection from session-state contexts."""
    return RenderProjection(
        video_loaded=bool(st.session_state.video_loaded),
        asset_id=st.session_state.asset_id,
        video_name=st.session_state.video_name,
        frame_index=int(st.session_state.current_frame_index),
        timestamp_seconds=float(st.session_state.current_frame_timestamp_seconds),
        playback_running=bool(st.session_state.playback_running),
        frame_request_key=st.session_state.current_frame_request_key,
        frame_image_bytes=st.session_state.current_frame_image_bytes,
        frame_image_mime_type=st.session_state.current_frame_image_mime_type,
        frame_error_message=st.session_state.frame_error_message,
        show_debug_overlay=bool(st.session_state.show_debug_overlay),
        mask_threshold=float(st.session_state.mask_threshold),
        mask_feather=int(st.session_state.mask_feather),
        mask_invert=bool(st.session_state.mask_invert),
        preview_generation=int(st.session_state.preview_generation),
        prompt_count=len(st.session_state.prompt_entries),
        video_fps=float(st.session_state.video_fps),
        video_frame_count=int(st.session_state.video_frame_count),
    )
