"""Public state API for the Streamlit UI adapter."""

from __future__ import annotations

from ui.state import (
    generation_state,
    playback_state,
    source_state,
    video_metadata_state,
    workbench_state,
)
from ui.state.playback_state import (
    apply_playback_progress,
    clamp_current_frame_index,
    get_playback_interval_seconds,
    jump_to_first_frame,
    jump_to_last_frame,
    reset_playback_state,
    set_current_frame_index,
    step_current_frame,
    sync_current_frame_index,
    sync_playback_position,
    sync_source_timeline_frame_index,
    sync_source_timeline_widget_state,
    toggle_playback,
)
from ui.state.session_defaults import apply_session_defaults
from ui.state.source_state import (
    current_active_asset_id,
    current_active_video_name,
    current_source_fingerprint,
    get_source_upload_widget_key,
    has_active_source,
    register_video_selection,
    remove_active_video_source,
    synchronize_explicit_source_state,
)
from ui.state.timecode import format_time_seconds_for_frame, format_timecode
from ui.state.workbench_state import (
    add_prompt,
    clear_prompts,
    ensure_current_frame_loaded,
    get_prompt_rows,
    refresh_preview,
    reset_workbench_frame_state,
    set_selected_error,
)

time = playback_state.time


def initialize_state() -> None:
    """Initialize Streamlit session-state defaults and source backfills."""
    apply_session_defaults()
    synchronize_explicit_source_state()


__all__ = [
    "add_prompt",
    "apply_playback_progress",
    "clear_prompts",
    "clamp_current_frame_index",
    "current_active_asset_id",
    "current_active_video_name",
    "current_source_fingerprint",
    "ensure_current_frame_loaded",
    "format_time_seconds_for_frame",
    "format_timecode",
    "generation_state",
    "get_playback_interval_seconds",
    "get_prompt_rows",
    "get_source_upload_widget_key",
    "has_active_source",
    "initialize_state",
    "jump_to_first_frame",
    "jump_to_last_frame",
    "playback_state",
    "refresh_preview",
    "register_video_selection",
    "remove_active_video_source",
    "reset_playback_state",
    "reset_workbench_frame_state",
    "set_current_frame_index",
    "set_selected_error",
    "source_state",
    "step_current_frame",
    "sync_source_timeline_frame_index",
    "sync_source_timeline_widget_state",
    "sync_current_frame_index",
    "sync_playback_position",
    "time",
    "toggle_playback",
    "video_metadata_state",
    "workbench_state",
]
