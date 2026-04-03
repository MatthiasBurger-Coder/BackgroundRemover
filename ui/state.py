"""Session state helpers for the internal Streamlit UI shell."""

from __future__ import annotations

from typing import Any

import streamlit as st

from ui.mock_data import FrameLabel, PromptEntry, build_prompt_entry, get_default_prompt_entries


def initialize_state(frame_catalog: list[FrameLabel]) -> None:
    defaults: dict[str, Any] = {
        "selected_frame": 128,
        "prompt_mode": "foreground",
        "prompt_x": 640,
        "prompt_y": 320,
        "prompt_entries": get_default_prompt_entries(frame_catalog),
        "preview_generation": 3,
        "mask_threshold": 0.62,
        "mask_feather": 8,
        "mask_invert": False,
        "show_debug_overlay": True,
        "selected_error_index": 0,
        "video_loaded": False,
        "video_name": "No video selected",
        "last_action": "UI session initialized",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_selected_frame(frame_catalog: list[FrameLabel]) -> FrameLabel:
    selected_frame = st.session_state.selected_frame
    for frame in frame_catalog:
        if frame.index == selected_frame:
            return frame
    return frame_catalog[0]


def set_selected_frame(frame_index: int) -> None:
    st.session_state.selected_frame = frame_index
    st.session_state.last_action = f"Selected keyframe {frame_index:04d}"


def sync_selected_frame() -> None:
    set_selected_frame(int(st.session_state.selected_frame))


def register_video_selection(uploaded_file: Any | None) -> None:
    if uploaded_file is None:
        if st.session_state.video_loaded:
            st.session_state.video_loaded = False
            st.session_state.video_name = "No video selected"
            st.session_state.last_action = "Cleared video selection"
        return

    if uploaded_file.name != st.session_state.video_name or not st.session_state.video_loaded:
        st.session_state.video_loaded = True
        st.session_state.video_name = uploaded_file.name
        st.session_state.last_action = f"Loaded placeholder asset {uploaded_file.name}"


def add_prompt(frame_catalog: list[FrameLabel]) -> None:
    frame = get_selected_frame(frame_catalog)
    new_identifier = len(st.session_state.prompt_entries) + 1
    prompt = build_prompt_entry(
        identifier=new_identifier,
        mode=st.session_state.prompt_mode,
        x=int(st.session_state.prompt_x),
        y=int(st.session_state.prompt_y),
        frame=frame,
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
    st.session_state.last_action = f"Queued placeholder preview refresh #{st.session_state.preview_generation}"


def set_selected_error(index: int) -> None:
    st.session_state.selected_error_index = index
    st.session_state.last_action = f"Focused failure case #{index + 1}"


def get_prompt_rows(prompt_entries: list[PromptEntry]) -> list[dict[str, str | int]]:
    return [entry.to_row() for entry in prompt_entries]
