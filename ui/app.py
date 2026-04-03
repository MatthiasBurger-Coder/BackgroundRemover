"""Main Streamlit entrypoint for the backend-assisted video mask operator UI."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from src.application.infrastructure.logging import LogLevel, configure_logging
from streamlit.runtime.scriptrunner import get_script_run_ctx

from ui.components import (
    render_failure_panel,
    render_operator_panel,
    render_preview_panels,
    render_prompt_panel,
    render_status_panel,
    render_workbench_frame_panel,
)
from ui.mock_data import get_failure_cases, get_runtime_handles, get_runtime_snapshot
from ui.projection import (
    PreviewProjection,
    WorkbenchProjection,
    build_preview_projection,
    build_workbench_projection,
)
from ui.state import (
    ensure_workbench_frame_loaded,
    format_timecode,
    get_playback_interval_seconds,
    initialize_state,
    sync_playback_position,
)

LOGGER = logging.getLogger(__name__)


def main() -> None:
    configure_logging(level=LogLevel.DEBUG)
    st.set_page_config(
        page_title="Video Mask Workflow Shell",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    failure_cases = get_failure_cases()
    initialize_state()
    ensure_workbench_frame_loaded()
    preview_projection = build_preview_projection()
    workbench_projection = build_workbench_projection()
    LOGGER.debug(
        "Starting UI render cycle playback_running=%s asset_id=%s playback_frame_index=%s workbench_frame_index=%s",
        st.session_state.playback_running,
        preview_projection.asset_id,
        preview_projection.playback_frame_index,
        workbench_projection.workbench_frame_index,
    )
    render_page_shell(failure_cases, preview_projection, workbench_projection)
    playback_interval_seconds = (
        get_playback_interval_seconds() if st.session_state.playback_running else None
    )
    LOGGER.debug(
        "Live fragment mounted playback_running=%s ui_generation=%s playback_generation=%s run_every=%s",
        st.session_state.playback_running,
        int(st.session_state.ui_generation),
        int(st.session_state.playback_generation),
        playback_interval_seconds,
    )
    render_live_preview_fragment(
        playback_interval_seconds=playback_interval_seconds,
        expected_ui_generation=int(st.session_state.ui_generation),
        expected_playback_generation=int(st.session_state.playback_generation),
    )


def render_live_preview_fragment(
    *,
    playback_interval_seconds: float | None,
    expected_ui_generation: int,
    expected_playback_generation: int,
) -> None:
    """Run preview playback timing in a stable fragment without remounting the page shell."""
    LOGGER.debug(
        "Live fragment rerun interval set run_every=%s expected_ui_generation=%s expected_playback_generation=%s",
        playback_interval_seconds,
        expected_ui_generation,
        expected_playback_generation,
    )
    fragment_renderer = st.fragment(
        _render_live_preview_fragment_body,
        run_every=playback_interval_seconds,
    )
    fragment_renderer(
        expected_ui_generation=expected_ui_generation,
        expected_playback_generation=expected_playback_generation,
    )


def _render_live_preview_fragment_body(
    *,
    expected_ui_generation: int,
    expected_playback_generation: int,
) -> None:
    """Advance preview playback state without re-rendering the workbench shell."""
    if _fragment_generation_is_stale(
        expected_ui_generation=expected_ui_generation,
        expected_playback_generation=expected_playback_generation,
    ):
        LOGGER.info(
            "Stale fragment ignored expected_ui_generation=%s current_ui_generation=%s expected_playback_generation=%s current_playback_generation=%s",
            expected_ui_generation,
            int(st.session_state.ui_generation),
            expected_playback_generation,
            int(st.session_state.playback_generation),
        )
        return

    playback_running_at_start = bool(st.session_state.playback_running)
    LOGGER.debug(
        "Fragment content render started ui_generation=%s playback_generation=%s playback_running=%s",
        int(st.session_state.ui_generation),
        int(st.session_state.playback_generation),
        playback_running_at_start,
    )
    if playback_running_at_start:
        LOGGER.debug(
            "Playback sync executed ui_generation=%s playback_generation=%s",
            int(st.session_state.ui_generation),
            int(st.session_state.playback_generation),
        )
        sync_playback_position()
    else:
        LOGGER.debug(
            "Playback rerun paused ui_generation=%s playback_generation=%s",
            int(st.session_state.ui_generation),
            int(st.session_state.playback_generation),
        )
    preview_projection = build_preview_projection()
    LOGGER.debug(
        "Fragment content render completed asset_id=%s playback_frame_index=%s playback_running=%s",
        preview_projection.asset_id,
        preview_projection.playback_frame_index,
        preview_projection.playback_running,
    )
    if playback_running_at_start and not st.session_state.playback_running:
        LOGGER.debug("Playback paused during fragment render; requesting full app rerun to refresh workbench snapshot")
        st.rerun()


def render_page_shell(
    failure_cases,
    preview_projection: PreviewProjection,
    workbench_projection: WorkbenchProjection,
) -> None:
    """Render the stable operator page shell outside the preview fragment."""
    LOGGER.debug(
        "Rendering stable page shell asset_id=%s playback_frame_index=%s workbench_frame_index=%s playback_running=%s",
        preview_projection.asset_id,
        preview_projection.playback_frame_index,
        workbench_projection.workbench_frame_index,
        preview_projection.playback_running,
    )
    render_workspace_header(workbench_projection)

    operator_column, workspace_column = st.columns([0.9, 2.1], gap="large")

    with operator_column:
        render_operator_panel()
        render_prompt_panel()

    with workspace_column:
        with st.container():
            LOGGER.debug(
                "Workbench host mounted asset_id=%s workbench_frame_index=%s",
                workbench_projection.asset_id,
                workbench_projection.workbench_frame_index,
            )
            render_workbench_frame_panel(workbench_projection)
        render_preview_panels(preview_projection, workbench_projection)
        workspace_tabs = st.tabs(["Failure Inspection", "Runtime Status"])
        with workspace_tabs[0]:
            render_failure_panel(failure_cases)
        with workspace_tabs[1]:
            render_status_panel(
                get_runtime_snapshot(),
                get_runtime_handles(),
                preview_projection,
                workbench_projection,
            )

    LOGGER.debug("Page shell render completed")


def render_workspace_header(workbench_projection: WorkbenchProjection) -> None:
    header_columns = st.columns([1.7, 0.65, 0.8, 0.9], gap="medium")
    header_columns[0].markdown("### Video Mask Creation Workspace")
    header_columns[0].caption(
        "Backend-assisted single-asset transport with a preview player and a fixed workbench snapshot."
    )
    header_columns[1].markdown(f"**Workbench Frame**  \n{workbench_projection.workbench_frame_index:04d}")
    header_columns[2].markdown(
        f"**Workbench Timecode**  \n{format_timecode(workbench_projection.workbench_timestamp_seconds)}"
    )
    header_columns[3].markdown(f"**Prompts**  \n{workbench_projection.prompt_count}")


def _fragment_generation_is_stale(
    *,
    expected_ui_generation: int,
    expected_playback_generation: int,
) -> bool:
    return bool(
        int(st.session_state.ui_generation) != expected_ui_generation
        or int(st.session_state.playback_generation) != expected_playback_generation
    )


if __name__ == "__main__":
    if get_script_run_ctx(suppress_warning=True) is None:
        print("Start this UI with: streamlit run ui/app.py")
        raise SystemExit(1)
    main()
