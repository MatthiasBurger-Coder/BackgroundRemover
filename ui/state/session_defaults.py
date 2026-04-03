"""Session-state bootstrap values for the Streamlit UI adapter."""

from __future__ import annotations

from typing import Any

import streamlit as st

SESSION_STATE_DEFAULTS: dict[str, Any] = {
    "prompt_mode": "foreground",
    "prompt_x": 640,
    "prompt_y": 320,
    "prompt_entries": [],
    "preview_generation": 3,
    "mask_threshold": 0.62,
    "mask_feather": 8,
    "mask_invert": False,
    "show_debug_overlay": True,
    "selected_error_index": 0,
    "video_loaded": False,
    "video_name": "No video selected",
    "video_mime_type": None,
    "source_video_bytes": None,
    "video_upload_signature": None,
    "active_asset_id": None,
    "active_video_name": None,
    "active_source_payload": None,
    "source_fingerprint": None,
    "asset_id": None,
    "video_fps": 0.0,
    "video_frame_count": 0,
    "video_duration_seconds": 0.0,
    "video_width": 0,
    "video_height": 0,
    "current_frame_index": 0,
    "current_frame_timestamp_seconds": 0.0,
    "current_frame_image_bytes": None,
    "current_frame_image_mime_type": None,
    "current_frame_width": 0,
    "current_frame_height": 0,
    "current_frame_request_key": None,
    "frame_error_message": None,
    "source_timeline_frame_index": 0,
    "playback_running": False,
    "playback_anchor_frame_index": None,
    "playback_started_at_seconds": None,
    "ui_generation": 0,
    "source_generation": 0,
    "playback_generation": 0,
    "workbench_generation": 0,
    "last_action": "UI session initialized",
}


def apply_session_defaults() -> None:
    """Populate missing session-state fields without applying workflow logic."""
    for key, value in SESSION_STATE_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value
