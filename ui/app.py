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
    render_parameter_panel,
    render_preview_panels,
    render_prompt_panel,
    render_sidebar,
    render_status_panel,
)
from ui.mock_data import get_failure_cases, get_frame_catalog, get_runtime_handles, get_runtime_snapshot
from ui.state import get_selected_frame, initialize_state, sync_selected_frame


def main() -> None:
    st.set_page_config(
        page_title="Video Mask Workflow Shell",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    frame_catalog = get_frame_catalog()
    failure_cases = get_failure_cases()
    initialize_state(frame_catalog)
    selected_frame = get_selected_frame(frame_catalog)

    render_sidebar(selected_frame)
    render_workspace_header(selected_frame)
    render_keyframe_section(frame_catalog)

    selected_frame = get_selected_frame(frame_catalog)
    render_prompt_panel(frame_catalog, selected_frame)
    render_preview_panels(selected_frame)

    parameter_column, failure_column = st.columns([1, 1.3], gap="large")
    with parameter_column:
        render_parameter_panel()
    with failure_column:
        render_failure_panel(failure_cases)

    render_status_panel(selected_frame, get_runtime_snapshot(), get_runtime_handles())


def render_workspace_header(selected_frame) -> None:
    st.title("Video Mask Creation Workspace")
    st.caption(
        "Internal Streamlit operator shell for prompt-driven video mask review. "
        "This prototype exposes UI structure only and does not execute processing."
    )

    metric_columns = st.columns(4)
    metric_columns[0].metric("Selected Frame", f"{selected_frame.index:04d}")
    metric_columns[1].metric("Frame Label", selected_frame.label)
    metric_columns[2].metric("Prompt Count", str(len(st.session_state.prompt_entries)))
    metric_columns[3].metric("Preview Counter", str(st.session_state.preview_generation))


def render_keyframe_section(frame_catalog) -> None:
    st.subheader("Keyframe Selection")
    st.caption("Choose the current operator focus frame from the placeholder timeline.")

    options = [frame.index for frame in frame_catalog]
    st.select_slider(
        "Keyframe",
        options=options,
        key="selected_frame",
        on_change=sync_selected_frame,
        format_func=lambda value: next(
            frame.selector_label() for frame in frame_catalog if frame.index == value
        ),
    )

    selected_frame = get_selected_frame(frame_catalog)
    detail_columns = st.columns(3)
    detail_columns[0].metric("Current Keyframe", f"{selected_frame.index:04d}")
    detail_columns[1].metric("Timecode", selected_frame.timecode)
    detail_columns[2].metric("Frame Label", selected_frame.label)
    st.caption(selected_frame.note)


if __name__ == "__main__":
    if get_script_run_ctx(suppress_warning=True) is None:
        print("Start this UI with: streamlit run ui/app.py")
        raise SystemExit(1)
    main()
