"""Preview panels for the internal Streamlit UI shell."""

from __future__ import annotations

import streamlit as st

from ui.mock_data import FrameLabel


def render_preview_panels(selected_frame: FrameLabel) -> None:
    st.subheader("Workspace")
    st.caption("Desktop-first workspace with the uploaded source video as the primary anchor.")

    _render_original_video_panel(selected_frame)

    detail_tab, mask_tab, preview_tab = st.tabs(["Source Context", "Mask View", "Masked Preview"])

    with detail_tab:
        _render_source_context_panel(selected_frame)

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
    _render_view_placeholder_header(title=title, summary_lines=summary_lines)

    with st.container(border=True):
        st.markdown("**Viewport Placeholder**")
        st.caption("This panel remains placeholder-only in the current prototype.")
        for line in inspection_lines:
            st.write(line)


def _render_original_video_panel(selected_frame: FrameLabel) -> None:
    viewport_status = "uploaded source available" if st.session_state.video_loaded else "waiting for uploaded source"
    _render_view_placeholder_header(
        title="Original Video",
        summary_lines=[
            f"Active frame: {selected_frame.index:04d}",
            f"Timecode: {selected_frame.timecode}",
            f"Frame label: {selected_frame.label}",
            f"Viewport status: {viewport_status}",
        ],
    )

    with st.container(border=True):
        st.markdown("**Source Video Player**")
        if st.session_state.video_loaded and st.session_state.video_bytes is not None:
            st.caption(f"Uploaded asset: {st.session_state.video_name}")
            st.video(st.session_state.video_bytes, format=st.session_state.video_mime_type)
            st.caption("Use the source video as the primary reference while tuning prompts and reviewing frame context.")
        else:
            st.info("Upload an original video in the operator column to display it here.")
            st.write("No source video is currently attached to this session.")


def _render_source_context_panel(selected_frame: FrameLabel) -> None:
    with st.container(border=True):
        st.markdown("**Source Context**")
        detail_columns = st.columns(2, gap="large")
        detail_columns[0].write("Operator use: review the uploaded source video while setting prompts.")
        detail_columns[0].write("Current frame focus remains conceptual in this prototype.")
        detail_columns[1].write(f"Frame note: {selected_frame.note}")
        detail_columns[1].write("Future integration: decoded frame transport and timeline-aware inspection.")


def _render_view_placeholder_header(title: str, summary_lines: list[str]) -> None:
    st.markdown(f"**{title}**")
    metadata_columns = st.columns(len(summary_lines))
    for column, line in zip(metadata_columns, summary_lines, strict=False):
        label, value = line.split(": ", maxsplit=1)
        column.metric(label, value)
