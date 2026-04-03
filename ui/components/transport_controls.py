"""Transport controls for the single-asset source timeline."""

from __future__ import annotations

import streamlit as st

from ui.state import (
    jump_to_first_frame,
    jump_to_last_frame,
    step_current_frame,
    toggle_playback,
)


def render_transport_controls(*, disabled: bool) -> None:
    """Render first/previous/play-next-last controls for the active source asset."""
    buttons = st.columns([0.95, 0.95, 1.15, 0.95, 0.95], gap="small")
    if buttons[0].button("First", width="stretch", disabled=disabled):
        jump_to_first_frame()
        st.rerun()
    if buttons[1].button("Previous", width="stretch", disabled=disabled):
        step_current_frame(-1)
        st.rerun()
    play_label = "Pause" if st.session_state.playback_running else "Play"
    if buttons[2].button(play_label, width="stretch", disabled=disabled, type="primary"):
        toggle_playback()
        st.rerun()
    if buttons[3].button("Next", width="stretch", disabled=disabled):
        step_current_frame(1)
        st.rerun()
    if buttons[4].button("Last", width="stretch", disabled=disabled):
        jump_to_last_frame()
        st.rerun()
