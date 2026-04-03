"""Main Streamlit entrypoint for the backend-assisted video mask operator UI."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

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
from ui.projection import RenderProjection, build_render_projection
from ui.state import (
    ensure_current_frame_loaded,
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
    initial_render_projection = build_render_projection()
    LOGGER.debug(
        "Starting UI render cycle playback_running=%s asset_id=%s frame_index=%s",
        st.session_state.playback_running,
        st.session_state.asset_id,
        st.session_state.current_frame_index,
    )
    frame_slot = render_page_shell(failure_cases, initial_render_projection)
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
    render_live_operator_workspace(
        frame_slot=frame_slot,
        playback_interval_seconds=playback_interval_seconds,
        expected_ui_generation=int(st.session_state.ui_generation),
        expected_playback_generation=int(st.session_state.playback_generation),
    )


def render_live_operator_workspace(
    *,
    frame_slot: Any,
    playback_interval_seconds: float | None,
    expected_ui_generation: int,
    expected_playback_generation: int,
) -> None:
    """Render the live workbench frame slot inside a fragment with a dynamic playback cadence."""
    LOGGER.debug(
        "Live fragment rerun interval set run_every=%s expected_ui_generation=%s expected_playback_generation=%s",
        playback_interval_seconds,
        expected_ui_generation,
        expected_playback_generation,
    )
    fragment_renderer = st.fragment(
        _render_live_operator_workspace_body,
        run_every=playback_interval_seconds,
    )
    fragment_renderer(
        frame_slot=frame_slot,
        expected_ui_generation=expected_ui_generation,
        expected_playback_generation=expected_playback_generation,
    )


def _render_live_operator_workspace_body(
    *,
    frame_slot: Any,
    expected_ui_generation: int,
    expected_playback_generation: int,
) -> None:
    """Render the dynamic workbench frame from the persistent fragment mount."""
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
    ensure_current_frame_loaded()
    render_projection = build_render_projection()
    render_workbench_frame_slot(frame_slot, render_projection)
    LOGGER.debug(
        "Fragment content render completed asset_id=%s frame_index=%s request_key=%s",
        render_projection.asset_id,
        render_projection.frame_index,
        render_projection.frame_request_key,
    )
    if playback_running_at_start and not st.session_state.playback_running:
        LOGGER.debug("Playback paused during fragment render; requesting full app rerun to disable auto-reruns")
        st.rerun()


def render_page_shell(
    failure_cases,
    render_projection: RenderProjection,
) -> Any:
    """Render the stable page shell and return the dynamic workbench frame slot."""
    LOGGER.debug(
        "Rendering stable page shell asset_id=%s frame_index=%s playback_running=%s",
        render_projection.asset_id,
        render_projection.frame_index,
        render_projection.playback_running,
    )
    render_workspace_header(render_projection)

    operator_column, workspace_column = st.columns([0.9, 2.1], gap="large")

    with operator_column:
        render_operator_panel()
        render_prompt_panel()

    with workspace_column:
        workbench_host = st.container()
        with workbench_host:
            LOGGER.debug(
                "Workbench host mounted asset_id=%s playback_running=%s",
                render_projection.asset_id,
                render_projection.playback_running,
            )
            frame_slot = st.empty()
        render_preview_panels(render_projection)
        workspace_tabs = st.tabs(["Failure Inspection", "Runtime Status"])
        with workspace_tabs[0]:
            render_failure_panel(failure_cases)
        with workspace_tabs[1]:
            render_status_panel(get_runtime_snapshot(), get_runtime_handles(), render_projection)

    LOGGER.debug("Page shell render completed")
    return frame_slot


def render_workbench_frame_slot(
    frame_slot: Any,
    render_projection: RenderProjection,
) -> None:
    """Render the dynamic workbench frame into the stable frame slot."""
    LOGGER.debug(
        "Frame slot updated asset_id=%s frame_index=%s timecode=%s playback_running=%s request_key=%s",
        render_projection.asset_id,
        render_projection.frame_index,
        render_projection.timestamp_seconds,
        render_projection.playback_running,
        render_projection.frame_request_key,
    )
    with frame_slot.container():
        render_workbench_frame_panel(render_projection)


def render_workspace_header(render_projection: RenderProjection) -> None:
    header_columns = st.columns([1.7, 0.65, 0.8, 0.9], gap="medium")
    header_columns[0].markdown("### Video Mask Creation Workspace")
    header_columns[0].caption(
        "Backend-assisted single-asset transport with a shared workbench frame binding."
    )
    header_columns[1].markdown(f"**Frame**  \n{render_projection.frame_index:04d}")
    header_columns[2].markdown(f"**Timecode**  \n{format_timecode(render_projection.timestamp_seconds)}")
    header_columns[3].markdown(f"**Prompts**  \n{render_projection.prompt_count}")


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
