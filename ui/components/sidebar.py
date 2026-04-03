"""Sidebar controls for the internal Streamlit UI shell."""

from __future__ import annotations

import streamlit as st

from ui.mock_data import FrameLabel, get_preview_metadata, get_workspace_info
from ui.state import clear_prompts, refresh_preview, register_video_selection, sync_selected_frame


def render_operator_panel(frame_catalog: list[FrameLabel], selected_frame: FrameLabel) -> None:
    with st.container(border=True):
        st.subheader("Operator Controls")
        st.caption("Compact desktop control surface for source setup, keyframe focus, and preview tuning.")

        uploaded_file = st.file_uploader(
            "Original video",
            type=["mp4", "mov", "mkv", "avi"],
            help="Upload a source video for session-local playback in the Original Video tab.",
        )
        register_video_selection(uploaded_file)

        action_columns = st.columns(2, gap="small")
        if action_columns[0].button("Refresh Preview", width="stretch", type="primary"):
            refresh_preview()
        if action_columns[1].button("Clear Prompts", width="stretch"):
            clear_prompts()

        st.markdown("**Keyframe Focus**")
        st.select_slider(
            "Keyframe",
            options=[frame.index for frame in frame_catalog],
            key="selected_frame",
            on_change=sync_selected_frame,
            format_func=lambda value: next(
                frame.selector_label() for frame in frame_catalog if frame.index == value
            ),
        )

        focus_columns = st.columns(2, gap="small")
        focus_columns[0].metric("Frame", f"{selected_frame.index:04d}")
        focus_columns[1].metric("Timecode", selected_frame.timecode)
        st.caption(selected_frame.label)

        with st.expander("Preview Parameters", expanded=True):
            st.slider(
                "Threshold",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                key="mask_threshold",
                help="Placeholder control for future mask threshold tuning.",
            )
            st.slider(
                "Feather",
                min_value=0,
                max_value=32,
                step=1,
                key="mask_feather",
                help="Placeholder control for future edge softening.",
            )
            toggle_columns = st.columns(2, gap="small")
            toggle_columns[0].checkbox("Invert mask", key="mask_invert")
            toggle_columns[1].checkbox("Debug overlay", key="show_debug_overlay")

        with st.expander("Session Context", expanded=False):
            st.dataframe(
                get_workspace_info(st.session_state.video_loaded, st.session_state.video_name),
                width="stretch",
                hide_index=True,
            )
            st.dataframe(get_preview_metadata(), width="stretch", hide_index=True)
            st.caption(selected_frame.note)


def render_sidebar(frame_catalog: list[FrameLabel], selected_frame: FrameLabel) -> None:
    render_operator_panel(frame_catalog, selected_frame)
