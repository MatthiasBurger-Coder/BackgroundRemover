"""Runtime and debug status panel for the backend-assisted Streamlit operator UI."""

from __future__ import annotations

import streamlit as st

from ui.projection import RenderProjection
from ui.state import format_timecode


def render_status_panel(
    runtime_snapshot: list[dict[str, str]],
    runtime_handles: list[dict[str, str]],
    render_projection: RenderProjection,
) -> None:
    st.subheader("Runtime and Status")
    st.caption("Compressed operational snapshot for the current backend-assisted session.")

    metric_columns = st.columns(6)
    metric_columns[0].metric("Asset Loaded", "Yes" if render_projection.video_loaded else "No")
    metric_columns[1].metric("Frame", f"{render_projection.frame_index:04d}")
    metric_columns[2].metric("Timecode", format_timecode(render_projection.timestamp_seconds))
    metric_columns[3].metric("Prompt Count", str(render_projection.prompt_count))
    metric_columns[4].metric("Playback", "Running" if render_projection.playback_running else "Paused")
    metric_columns[5].metric("Preview Refreshes", str(render_projection.preview_generation))

    with st.expander("Runtime Snapshot", expanded=False):
        st.dataframe(runtime_snapshot, width="stretch", hide_index=True)
        st.dataframe(
            [
                {"Field": "Last Action", "Value": st.session_state.last_action},
                {"Field": "Asset ID", "Value": render_projection.asset_id[:8] if render_projection.asset_id else "Not assigned"},
                {"Field": "Source FPS", "Value": f"{render_projection.video_fps:.2f}"},
                {"Field": "Frame Count", "Value": str(render_projection.video_frame_count)},
                {"Field": "Mask Threshold", "Value": f"{st.session_state.mask_threshold:.2f}"},
                {"Field": "Mask Feather", "Value": str(st.session_state.mask_feather)},
            ],
            width="stretch",
            hide_index=True,
        )

    with st.expander("Resource Handles and Notes", expanded=False):
        st.dataframe(runtime_handles, width="stretch", hide_index=True)
        st.write("Video metadata and frame-by-index retrieval now come from the backend video asset slice.")
        st.write("Masking, segmentation, and preview rendering remain placeholder-only.")
        st.write("The layout is prepared for future adapter and service integration.")
