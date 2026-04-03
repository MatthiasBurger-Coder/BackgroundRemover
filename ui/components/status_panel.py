"""Runtime and debug status panel for the backend-assisted Streamlit operator UI."""

from __future__ import annotations

import streamlit as st

from ui.projection import PreviewProjection, WorkbenchProjection
from ui.state import format_timecode


def render_status_panel(
    runtime_snapshot: list[dict[str, str]],
    runtime_handles: list[dict[str, str]],
    preview_projection: PreviewProjection,
    workbench_projection: WorkbenchProjection,
) -> None:
    st.subheader("Runtime and Status")
    st.caption("Compressed operational snapshot for the current backend-assisted session.")

    metric_columns = st.columns(6)
    metric_columns[0].metric("Asset Loaded", "Yes" if preview_projection.video_loaded else "No")
    metric_columns[1].metric("Preview Frame", f"{preview_projection.playback_frame_index:04d}")
    metric_columns[2].metric("Workbench Frame", f"{workbench_projection.workbench_frame_index:04d}")
    metric_columns[3].metric("Prompt Count", str(workbench_projection.prompt_count))
    metric_columns[4].metric("Playback", "Running" if preview_projection.playback_running else "Paused")
    metric_columns[5].metric("Preview Refreshes", str(workbench_projection.preview_generation))

    with st.expander("Runtime Snapshot", expanded=False):
        st.dataframe(runtime_snapshot, width="stretch", hide_index=True)
        st.dataframe(
            [
                {"Field": "Last Action", "Value": st.session_state.last_action},
                {"Field": "Asset ID", "Value": preview_projection.asset_id[:8] if preview_projection.asset_id else "Not assigned"},
                {"Field": "Preview Timecode", "Value": format_timecode(preview_projection.playback_timestamp_seconds)},
                {"Field": "Workbench Timecode", "Value": format_timecode(workbench_projection.workbench_timestamp_seconds)},
                {"Field": "Source FPS", "Value": f"{preview_projection.video_fps:.2f}"},
                {"Field": "Frame Count", "Value": str(preview_projection.video_frame_count)},
                {"Field": "Mask Threshold", "Value": f"{workbench_projection.mask_threshold:.2f}"},
                {"Field": "Mask Feather", "Value": str(workbench_projection.mask_feather)},
            ],
            width="stretch",
            hide_index=True,
        )

    with st.expander("Resource Handles and Notes", expanded=False):
        st.dataframe(runtime_handles, width="stretch", hide_index=True)
        st.write("Preview playback now advances independently from the fixed workbench snapshot.")
        st.write("Masking, segmentation, and preview rendering remain placeholder-only.")
        st.write("The layout is prepared for future adapter and service integration.")
