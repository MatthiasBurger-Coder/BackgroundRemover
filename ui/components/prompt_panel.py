"""Prompt definition panel for the backend-assisted Streamlit operator UI."""

from __future__ import annotations

import streamlit as st

from ui.state import add_prompt, format_timecode, get_prompt_rows


def render_prompt_panel() -> None:
    with st.container(border=True):
        st.subheader("Prompt Definition")
        st.caption("Add foreground and background points for the current work frame.")

        with st.form("prompt_entry_form", border=True):
            st.radio(
                "Prompt mode",
                options=["foreground", "background"],
                key="prompt_mode",
                horizontal=True,
            )
            coordinate_columns = st.columns(2)
            coordinate_columns[0].number_input(
                "X coordinate",
                min_value=0,
                max_value=max(st.session_state.video_width, 4096),
                step=1,
                key="prompt_x",
            )
            coordinate_columns[1].number_input(
                "Y coordinate",
                min_value=0,
                max_value=max(st.session_state.video_height, 4096),
                step=1,
                key="prompt_y",
            )
            submitted = st.form_submit_button(
                "Add Prompt",
                width="stretch",
                disabled=not st.session_state.video_loaded,
            )
            if submitted:
                add_prompt()

        st.caption(
            f"Current work frame: Frame {st.session_state.current_frame_index:04d} | "
            f"{format_timecode(st.session_state.current_frame_timestamp_seconds)}"
        )

        rows = get_prompt_rows(st.session_state.prompt_entries)
        with st.expander(f"Prompt Log ({len(rows)})", expanded=False):
            if rows:
                st.dataframe(rows, width="stretch", hide_index=True)
            else:
                st.info("No prompt entries are currently defined in this session.")
