"""Workbench context helpers for the Streamlit UI adapter."""

from __future__ import annotations

import logging

import streamlit as st
from src.application.domain.errors.video_asset_errors import VideoFrameExtractionError
from src.application.infrastructure.wiring.video_asset_backend import get_video_asset_backend

from ui.mock_data import PromptEntry
from ui.state.generation_state import bump_playback_generation, bump_workbench_generation
from ui.state.playback_state import clamp_current_frame_index, reset_playback_state
from ui.state.timecode import format_timecode

LOGGER = logging.getLogger(__name__)


def ensure_current_frame_loaded() -> None:
    """Load or reuse the workbench frame for the current render projection."""
    active_asset_id = _resolve_active_asset_id()
    if not st.session_state.video_loaded or active_asset_id is None:
        reset_workbench_frame_state(reset_position=False)
        return

    frame_index = clamp_current_frame_index(st.session_state.current_frame_index)
    request_key = (active_asset_id, frame_index)
    if request_key == st.session_state.current_frame_request_key and st.session_state.current_frame_image_bytes:
        LOGGER.debug("Skipping frame reload for cached request asset_id=%s frame_index=%s", active_asset_id, frame_index)
        return

    backend = get_video_asset_backend()
    try:
        LOGGER.debug("Loading frame asset_id=%s frame_index=%s", active_asset_id, frame_index)
        frame = backend.get_video_frame.execute(
            asset_id=active_asset_id,
            frame_index=frame_index,
        )
    except VideoFrameExtractionError as error:
        reset_playback_state()
        reset_workbench_frame_state(reset_position=False)
        st.session_state.frame_error_message = str(error)
        st.session_state.last_action = "Frame loading failed"
        bump_playback_generation("frame_load_failed")
        bump_workbench_generation("frame_load_failed")
        LOGGER.exception("Frame loading failed asset_id=%s frame_index=%s", active_asset_id, frame_index)
        return

    st.session_state.current_frame_index = frame.frame_index
    st.session_state.current_frame_timestamp_seconds = frame.timestamp_seconds
    st.session_state.current_frame_image_bytes = frame.image_bytes
    st.session_state.current_frame_image_mime_type = frame.mime_type
    st.session_state.current_frame_width = frame.width
    st.session_state.current_frame_height = frame.height
    st.session_state.current_frame_request_key = request_key
    st.session_state.frame_error_message = None
    LOGGER.debug(
        "Loaded frame asset_id=%s resolved_frame_index=%s timestamp=%.3f size=%sx%s",
        active_asset_id,
        frame.frame_index,
        frame.timestamp_seconds,
        frame.width,
        frame.height,
    )


def reset_workbench_frame_state(*, reset_position: bool) -> None:
    """Reset cached frame data while optionally rewinding the current position."""
    if reset_position:
        st.session_state.current_frame_index = 0
        st.session_state.current_frame_timestamp_seconds = 0.0
    st.session_state.current_frame_image_bytes = None
    st.session_state.current_frame_image_mime_type = None
    st.session_state.current_frame_width = 0
    st.session_state.current_frame_height = 0
    st.session_state.current_frame_request_key = None
    st.session_state.frame_error_message = None


def add_prompt() -> None:
    """Append a prompt entry bound to the current workbench frame."""
    new_identifier = len(st.session_state.prompt_entries) + 1
    frame_index = int(st.session_state.current_frame_index)
    timecode = format_timecode(st.session_state.current_frame_timestamp_seconds)
    prompt = PromptEntry(
        identifier=new_identifier,
        mode=st.session_state.prompt_mode,
        frame_index=frame_index,
        frame_label=f"Frame {frame_index:04d} | {timecode}",
        x=int(st.session_state.prompt_x),
        y=int(st.session_state.prompt_y),
        source="Operator input",
    )
    st.session_state.prompt_entries = [*st.session_state.prompt_entries, prompt]
    st.session_state.last_action = (
        f"Added {prompt.mode} prompt at ({prompt.x}, {prompt.y}) on frame {prompt.frame_index:04d}"
    )


def clear_prompts() -> None:
    st.session_state.prompt_entries = []
    st.session_state.last_action = "Cleared all prompt entries"


def refresh_preview() -> None:
    st.session_state.preview_generation += 1
    LOGGER.info("Queued preview refresh generation=%s", st.session_state.preview_generation)
    st.session_state.last_action = f"Queued placeholder preview refresh #{st.session_state.preview_generation}"


def set_selected_error(index: int) -> None:
    st.session_state.selected_error_index = index
    st.session_state.last_action = f"Focused failure case #{index + 1}"


def get_prompt_rows(prompt_entries: list[PromptEntry]) -> list[dict[str, str | int]]:
    return [entry.to_row() for entry in prompt_entries]


def _resolve_active_asset_id() -> str | None:
    return st.session_state.get("active_asset_id") or st.session_state.get("asset_id")
