"""Prompt definition panel for the internal Streamlit UI shell."""

from __future__ import annotations

import streamlit as st

from ui.mock_data import FrameLabel
from ui.state import add_prompt, get_prompt_rows


def render_prompt_panel(frame_catalog: list[FrameLabel], selected_frame: FrameLabel) -> None:
    st.subheader("Prompt Definition")
    st.caption("Define foreground and background prompt points for the selected keyframe.")

    control_column, table_column = st.columns([1, 1.4], gap="large")

    with control_column:
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
                max_value=4096,
                step=1,
                key="prompt_x",
            )
            coordinate_columns[1].number_input(
                "Y coordinate",
                min_value=0,
                max_value=4096,
                step=1,
                key="prompt_y",
            )
            submitted = st.form_submit_button("Add Prompt", use_container_width=True)
            if submitted:
                add_prompt(frame_catalog)

        st.write(f"Current keyframe: Frame {selected_frame.index:04d}")
        st.caption(selected_frame.label)
        st.caption(selected_frame.note)

    with table_column:
        rows = get_prompt_rows(st.session_state.prompt_entries)
        st.markdown("**Current Prompt Entries**")
        st.caption("Session-local placeholder entries only.")
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No prompt entries are currently defined in this UI session.")
