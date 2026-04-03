"""Runtime and debug status panel for the internal Streamlit UI shell."""

from __future__ import annotations

import streamlit as st

from ui.mock_data import FrameLabel


def render_status_panel(
    selected_frame: FrameLabel,
    runtime_snapshot: list[dict[str, str]],
    runtime_handles: list[dict[str, str]],
) -> None:
    st.subheader("Runtime, Debug, and Status")
    st.caption("This section exposes fake operational state for internal workflow validation.")

    metric_columns = st.columns(5)
    metric_columns[0].metric("Selected Frame", f"{selected_frame.index:04d}")
    metric_columns[1].metric("Prompt Count", str(len(st.session_state.prompt_entries)))
    metric_columns[2].metric("Preview Refreshes", str(st.session_state.preview_generation))
    metric_columns[3].metric("Video Loaded", "Yes" if st.session_state.video_loaded else "No")
    metric_columns[4].metric("Debug Overlay", "On" if st.session_state.show_debug_overlay else "Off")

    left_column, right_column = st.columns(2, gap="large")

    with left_column:
        st.markdown("**Runtime Snapshot**")
        st.dataframe(runtime_snapshot, use_container_width=True, hide_index=True)
        st.markdown("**UI State**")
        st.dataframe(
            [
                {"Field": "Last Action", "Value": st.session_state.last_action},
                {"Field": "Mask Threshold", "Value": f"{st.session_state.mask_threshold:.2f}"},
                {"Field": "Mask Feather", "Value": str(st.session_state.mask_feather)},
                {"Field": "Mask Invert", "Value": str(st.session_state.mask_invert)},
            ],
            use_container_width=True,
            hide_index=True,
        )

    with right_column:
        st.markdown("**Planned Resource Handles**")
        st.dataframe(runtime_handles, use_container_width=True, hide_index=True)
        st.markdown("**Extension Notes**")
        st.write("No backend services are called in this prototype.")
        st.write("All values are mock session state or static placeholder metadata.")
        st.write("The layout is prepared for future adapter and service integration.")
