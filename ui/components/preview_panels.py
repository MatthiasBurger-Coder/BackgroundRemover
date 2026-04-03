"""Preview panels for the internal Streamlit UI shell."""

from __future__ import annotations

import streamlit as st

from ui.mock_data import FrameLabel


def render_preview_panels(selected_frame: FrameLabel) -> None:
    st.subheader("View Workspace")
    st.caption("All views below are placeholder-only and simulate the future operator workspace.")

    original_tab, mask_tab, preview_tab = st.tabs(["Original Video", "Mask View", "Masked Preview"])

    with original_tab:
        _render_view_placeholder(
            title="Original Video View",
            summary_lines=[
                f"Active frame: {selected_frame.index:04d}",
                f"Timecode: {selected_frame.timecode}",
                f"Frame label: {selected_frame.label}",
                "Viewport status: source media not connected in UI shell.",
            ],
            inspection_lines=[
                "Intended use: operator verifies subject position and framing before prompting.",
                "Expected future integration: decoded frame transport from the video reader adapter.",
            ],
        )

    with mask_tab:
        _render_view_placeholder(
            title="Mask View",
            summary_lines=[
                "Display mode: black and white matte placeholder.",
                f"Threshold mirror: {st.session_state.mask_threshold:.2f}",
                f"Feather mirror: {st.session_state.mask_feather}",
                f"Invert mask: {'On' if st.session_state.mask_invert else 'Off'}",
            ],
            inspection_lines=[
                "Intended use: inspect matte shape, edge solidity, and missing regions.",
                "Expected future integration: segmentation and temporal stabilization outputs.",
            ],
        )

    with preview_tab:
        debug_label = "enabled" if st.session_state.show_debug_overlay else "disabled"
        _render_view_placeholder(
            title="Masked Preview",
            summary_lines=[
                "Display mode: composited preview placeholder.",
                f"Preview generation counter: {st.session_state.preview_generation}",
                f"Debug overlay: {debug_label}",
                "Render path: no rendering backend attached.",
            ],
            inspection_lines=[
                "Intended use: review how the masked subject would look in preview mode.",
                "Expected future integration: preview renderer and quality diagnostics.",
            ],
        )


def _render_view_placeholder(
    title: str,
    summary_lines: list[str],
    inspection_lines: list[str],
) -> None:
    st.markdown(f"**{title}**")
    metadata_columns = st.columns(len(summary_lines))
    for column, line in zip(metadata_columns, summary_lines, strict=False):
        label, value = line.split(": ", maxsplit=1)
        column.metric(label, value)

    with st.container(border=True):
        st.markdown("**Viewport Placeholder**")
        st.write("No real media is rendered in this prototype.")
        for line in inspection_lines:
            st.write(line)
