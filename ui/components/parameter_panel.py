"""Parameter summary panel for the internal Streamlit UI shell."""

from __future__ import annotations

import streamlit as st


def render_parameter_panel() -> None:
    st.subheader("Parameter Adjustment")
    st.caption("Controls live in the sidebar. This section mirrors the active placeholder state.")

    metric_columns = st.columns(4)
    metric_columns[0].metric("Threshold", f"{st.session_state.mask_threshold:.2f}")
    metric_columns[1].metric("Feather", str(st.session_state.mask_feather))
    metric_columns[2].metric("Invert Mask", "On" if st.session_state.mask_invert else "Off")
    metric_columns[3].metric("Debug Overlay", "On" if st.session_state.show_debug_overlay else "Off")

    st.dataframe(
        [
            {
                "Parameter": "Threshold",
                "Current Value": f"{st.session_state.mask_threshold:.2f}",
                "Prototype Note": "Placeholder control for future mask cutoff tuning.",
            },
            {
                "Parameter": "Feather",
                "Current Value": str(st.session_state.mask_feather),
                "Prototype Note": "Placeholder control for future edge softening behavior.",
            },
            {
                "Parameter": "Invert Mask",
                "Current Value": str(st.session_state.mask_invert),
                "Prototype Note": "Placeholder toggle for alternate matte inspection.",
            },
            {
                "Parameter": "Debug Overlay",
                "Current Value": str(st.session_state.show_debug_overlay),
                "Prototype Note": "Placeholder toggle for future review overlays.",
            },
        ],
        use_container_width=True,
        hide_index=True,
    )
