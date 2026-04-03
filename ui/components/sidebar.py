"""Operator controls for the backend-assisted Streamlit mask workflow UI."""

from __future__ import annotations

import streamlit as st

from ui.mock_data import get_preview_metadata, get_workspace_info
from ui.state import clear_prompts, format_timecode, refresh_preview, register_video_selection


def render_operator_panel() -> None:
    with st.container(border=True):
        st.subheader("Operator Controls")
        st.caption("Compact desktop control surface for source setup, prompt entry, and workbench tuning.")

        uploaded_file = st.file_uploader(
            "Original video",
            type=["mp4", "mov", "mkv", "avi"],
            help="Upload a source video to register a temporary backend-managed asset for transport and workbench binding.",
        )
        if register_video_selection(uploaded_file):
            st.rerun()

        action_columns = st.columns(2, gap="small")
        if action_columns[0].button("Refresh Preview", width="stretch", type="primary"):
            refresh_preview()
        if action_columns[1].button("Clear Prompts", width="stretch"):
            clear_prompts()

        st.markdown("**Current Work Frame**")
        focus_columns = st.columns(2, gap="small")
        focus_columns[0].metric("Frame", f"{st.session_state.current_frame_index:04d}")
        focus_columns[1].metric("Timecode", format_timecode(st.session_state.current_frame_timestamp_seconds))
        if st.session_state.video_loaded:
            st.caption(f"Source asset: {st.session_state.video_name}")
        else:
            st.caption("No source asset is currently registered.")

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
                get_workspace_info(
                    video_loaded=st.session_state.video_loaded,
                    video_name=st.session_state.video_name,
                    asset_id=st.session_state.asset_id,
                    frame_count=st.session_state.video_frame_count,
                ),
                width="stretch",
                hide_index=True,
            )
            st.dataframe(
                get_preview_metadata(
                    transport_ready=st.session_state.video_loaded,
                    fps=st.session_state.video_fps,
                ),
                width="stretch",
                hide_index=True,
            )


def render_sidebar() -> None:
    render_operator_panel()
