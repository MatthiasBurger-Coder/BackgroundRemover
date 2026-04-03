"""Main Streamlit entrypoint for the backend-assisted video mask operator UI."""

from __future__ import annotations

import sys
import time
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from ui.components import (
    render_failure_panel,
    render_operator_panel,
    render_preview_panels,
    render_prompt_panel,
    render_status_panel,
)
from ui.mock_data import get_failure_cases, get_runtime_handles, get_runtime_snapshot
from ui.state import (
    ensure_current_frame_loaded,
    format_timecode,
    get_playback_interval_seconds,
    initialize_state,
    sync_playback_position,
)


def main() -> None:
    st.set_page_config(
        page_title="Video Mask Workflow Shell",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    failure_cases = get_failure_cases()
    initialize_state()
    sync_playback_position()
    ensure_current_frame_loaded()

    render_workspace_header()

    operator_column, workspace_column = st.columns([0.9, 2.1], gap="large")

    with operator_column:
        render_operator_panel()
        render_prompt_panel()

    with workspace_column:
        render_preview_panels()
        workspace_tabs = st.tabs(["Failure Inspection", "Runtime Status"])
        with workspace_tabs[0]:
            render_failure_panel(failure_cases)
        with workspace_tabs[1]:
            render_status_panel(get_runtime_snapshot(), get_runtime_handles())

    if st.session_state.playback_running:
        time.sleep(get_playback_interval_seconds())
        st.rerun()


def render_workspace_header() -> None:
    header_columns = st.columns([1.7, 0.65, 0.8, 0.9], gap="medium")
    header_columns[0].markdown("### Video Mask Creation Workspace")
    header_columns[0].caption(
        "Backend-assisted single-asset transport with a shared workbench frame binding."
    )
    header_columns[1].markdown(f"**Frame**  \n{st.session_state.current_frame_index:04d}")
    header_columns[2].markdown(f"**Timecode**  \n{format_timecode(st.session_state.current_frame_timestamp_seconds)}")
    header_columns[3].markdown(f"**Prompts**  \n{len(st.session_state.prompt_entries)}")


if __name__ == "__main__":
    if get_script_run_ctx(suppress_warning=True) is None:
        print("Start this UI with: streamlit run ui/app.py")
        raise SystemExit(1)
    main()
