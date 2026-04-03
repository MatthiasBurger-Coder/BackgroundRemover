"""Main Streamlit entrypoint for the internal video mask UI shell."""

from __future__ import annotations

import sys
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
from ui.mock_data import get_failure_cases, get_frame_catalog, get_runtime_handles, get_runtime_snapshot
from ui.state import get_selected_frame, initialize_state


def main() -> None:
    st.set_page_config(
        page_title="Video Mask Workflow Shell",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    frame_catalog = get_frame_catalog()
    failure_cases = get_failure_cases()
    initialize_state(frame_catalog)
    selected_frame = get_selected_frame(frame_catalog)

    render_workspace_header(selected_frame)

    operator_column, workspace_column = st.columns([0.9, 2.1], gap="large")

    with operator_column:
        render_operator_panel(frame_catalog, selected_frame)
        selected_frame = get_selected_frame(frame_catalog)
        render_prompt_panel(frame_catalog, selected_frame)

    with workspace_column:
        selected_frame = get_selected_frame(frame_catalog)
        render_preview_panels(selected_frame)
        workspace_tabs = st.tabs(["Failure Inspection", "Runtime Status"])
        with workspace_tabs[0]:
            render_failure_panel(failure_cases)
        with workspace_tabs[1]:
            render_status_panel(selected_frame, get_runtime_snapshot(), get_runtime_handles())


def render_workspace_header(selected_frame) -> None:
    header_columns = st.columns([1.6, 0.7, 0.7, 0.7], gap="medium")
    header_columns[0].markdown("### Video Mask Creation Workspace")
    header_columns[0].caption("Desktop-first operator shell for prompt-driven video mask review.")
    header_columns[1].markdown(f"**Frame**  \n{selected_frame.index:04d}")
    header_columns[2].markdown(f"**Prompts**  \n{len(st.session_state.prompt_entries)}")
    header_columns[3].markdown(f"**Preview**  \n{st.session_state.preview_generation}")


if __name__ == "__main__":
    if get_script_run_ctx(suppress_warning=True) is None:
        print("Start this UI with: streamlit run ui/app.py")
        raise SystemExit(1)
    main()
