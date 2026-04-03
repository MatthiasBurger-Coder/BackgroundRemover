"""Sidebar controls for the internal Streamlit UI shell."""

from __future__ import annotations

import streamlit as st

from ui.mock_data import FrameLabel, get_preview_metadata, get_workspace_info
from ui.state import clear_prompts, refresh_preview, register_video_selection


def render_sidebar(selected_frame: FrameLabel) -> None:
    with st.sidebar:
        st.title("Operator Controls")
        st.caption("Internal UI shell for mask workflow planning and review.")

        uploaded_file = st.file_uploader(
            "Original video",
            type=["mp4", "mov", "mkv", "avi"],
            help="Upload a source video for session-local playback in the Original Video tab.",
        )
        register_video_selection(uploaded_file)

        st.subheader("Session")
        st.dataframe(
            get_workspace_info(st.session_state.video_loaded, st.session_state.video_name),
            width="stretch",
            hide_index=True,
        )

        st.subheader("Preview Parameters")
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
        st.checkbox("Invert mask", key="mask_invert")
        st.checkbox("Debug overlay", key="show_debug_overlay")

        st.subheader("Actions")
        if st.button("Refresh Preview", width="stretch", type="primary"):
            refresh_preview()
        if st.button("Clear Prompts", width="stretch"):
            clear_prompts()

        st.subheader("Current Focus")
        st.write(f"Frame {selected_frame.index:04d}")
        st.caption(selected_frame.label)
        st.caption(selected_frame.note)

        st.subheader("Preview Profile")
        st.dataframe(get_preview_metadata(), width="stretch", hide_index=True)
