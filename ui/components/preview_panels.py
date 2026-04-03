"""Workbench and workspace panels for the backend-assisted Streamlit operator UI."""

from __future__ import annotations

import streamlit as st

from ui.components.source_context import render_source_context_panel
from ui.components.video_panel import render_workspace_image_panel, render_workspace_placeholder_panel
from ui.state import format_timecode


def render_preview_panels() -> None:
    _render_mask_workbench_panel()

    detail_tab, mask_tab, preview_tab = st.tabs(["Source Context", "Mask View", "Masked Preview"])

    with detail_tab:
        render_source_context_panel()

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
                "Render path: no preview renderer attached.",
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
    render_workspace_placeholder_panel(
        title=title,
        metadata_items=[_split_summary_line(line) for line in summary_lines],
        placeholder_title="Viewport Placeholder",
        placeholder_lines=["This panel remains placeholder-only in the current prototype.", *inspection_lines],
    )


def _render_mask_workbench_panel() -> None:
    workbench_state = "backend frame bound" if st.session_state.video_loaded else "waiting for source asset"
    overlay_state = "debug overlay on" if st.session_state.show_debug_overlay else "debug overlay off"
    empty_lines = [
        "Upload a source asset and use Source Context transport controls to bind a work frame.",
        "The workbench will display the backend-selected frame here for future prompt placement and overlays.",
        "No mask generation or authoring logic is active yet in this slice.",
    ]
    if st.session_state.frame_error_message:
        empty_lines.insert(0, f"Frame loading error: {st.session_state.frame_error_message}")

    render_workspace_image_panel(
        title="Mask Workbench",
        metadata_items=[
            ("Frame", f"{st.session_state.current_frame_index:04d}"),
            ("Timecode", format_timecode(st.session_state.current_frame_timestamp_seconds)),
            ("Overlay", overlay_state),
            ("State", workbench_state),
        ],
        image_bytes=st.session_state.current_frame_image_bytes,
        mime_type=st.session_state.current_frame_image_mime_type,
        empty_title="Mask Authoring Workspace",
        empty_lines=empty_lines,
        panel_note=(
            f"Workbench frame source: {st.session_state.video_name} | "
            "Future use: prompt interaction, overlay editing, mask layer review."
            if st.session_state.video_loaded
            else "Future use: prompt interaction, overlay editing, mask layer review."
        ),
        stage_height="clamp(340px, 58vh, 760px)",
    )


def _split_summary_line(line: str) -> tuple[str, str]:
    label, value = line.split(": ", maxsplit=1)
    return label, value
