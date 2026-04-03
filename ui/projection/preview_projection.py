"""Preview projection models for the Streamlit UI adapter."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class PreviewProjection:
    """Stable preview input derived from source and playback contexts."""

    asset_id: str | None
    video_loaded: bool
    video_name: str
    video_mime_type: str | None
    source_video_bytes: bytes | None
    video_fps: float
    video_frame_count: int
    video_duration_seconds: float
    playback_frame_index: int
    playback_timestamp_seconds: float
    playback_running: bool


def build_preview_projection() -> PreviewProjection:
    """Build the current preview projection from session state."""
    return PreviewProjection(
        asset_id=st.session_state.get("active_asset_id") or st.session_state.get("asset_id"),
        video_loaded=bool(st.session_state.video_loaded),
        video_name=str(st.session_state.video_name),
        video_mime_type=st.session_state.video_mime_type,
        source_video_bytes=st.session_state.source_video_bytes,
        video_fps=float(st.session_state.video_fps),
        video_frame_count=int(st.session_state.video_frame_count),
        video_duration_seconds=float(st.session_state.video_duration_seconds),
        playback_frame_index=int(st.session_state.playback_frame_index),
        playback_timestamp_seconds=float(st.session_state.playback_timestamp_seconds),
        playback_running=bool(st.session_state.playback_running),
    )
