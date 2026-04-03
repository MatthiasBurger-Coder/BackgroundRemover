"""Runtime and debug status panel for the backend-assisted Streamlit operator UI."""

from __future__ import annotations

import streamlit as st

from ui.state import format_timecode


def render_status_panel(
    runtime_snapshot: list[dict[str, str]],
    runtime_handles: list[dict[str, str]],
) -> None:
    st.subheader("Runtime and Status")
    st.caption("Compressed operational snapshot for the current backend-assisted session.")

    metric_columns = st.columns(6)
    metric_columns[0].metric("Asset Loaded", "Yes" if st.session_state.video_loaded else "No")
    metric_columns[1].metric("Frame", f"{st.session_state.current_frame_index:04d}")
    metric_columns[2].metric("Timecode", format_timecode(st.session_state.current_frame_timestamp_seconds))
    metric_columns[3].metric("Prompt Count", str(len(st.session_state.prompt_entries)))
    metric_columns[4].metric("Playback", "Running" if st.session_state.playback_running else "Paused")
    metric_columns[5].metric("Preview Refreshes", str(st.session_state.preview_generation))

    with st.expander("Runtime Snapshot", expanded=False):
        st.dataframe(runtime_snapshot, width="stretch", hide_index=True)
        st.dataframe(
            [
                {"Field": "Last Action", "Value": st.session_state.last_action},
                {"Field": "Asset ID", "Value": st.session_state.asset_id[:8] if st.session_state.asset_id else "Not assigned"},
                {"Field": "Source FPS", "Value": f"{st.session_state.video_fps:.2f}"},
                {"Field": "Frame Count", "Value": str(st.session_state.video_frame_count)},
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
