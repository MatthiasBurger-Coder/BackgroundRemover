"""Preview panels for the internal Streamlit UI shell."""

from __future__ import annotations

import streamlit as st

from ui.mock_data import FrameLabel
from ui.components.video_panel import render_workspace_placeholder_panel, render_workspace_video_panel


def render_preview_panels(selected_frame: FrameLabel) -> None:
    _render_mask_workbench_panel(selected_frame)

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
    render_workspace_placeholder_panel(
        title=title,
        metadata_items=[_split_summary_line(line) for line in summary_lines],
        placeholder_title="Viewport Placeholder",
        placeholder_lines=["This panel remains placeholder-only in the current prototype.", *inspection_lines],
    )


def _render_mask_workbench_panel(selected_frame: FrameLabel) -> None:
    workbench_state = "ready for authoring" if st.session_state.video_loaded else "waiting for source context"
    overlay_state = "debug overlay on" if st.session_state.show_debug_overlay else "debug overlay off"
    render_workspace_placeholder_panel(
        title="Mask Workbench",
        metadata_items=[
            ("Frame", f"{selected_frame.index:04d}"),
            ("Mode", "Authoring"),
            ("Overlay", overlay_state),
            ("State", workbench_state),
        ],
        placeholder_title="Mask Authoring Workspace",
        placeholder_lines=[
            "Primary operator surface for future prompt-driven mask creation and refinement.",
            "This viewport is reserved for the editing canvas, overlay interactions, and mask layer inspection.",
            "No live mask authoring logic is active yet in this prototype.",
        ],
        panel_note=(
            f"Active frame {selected_frame.index:04d} | "
            "Future use: prompt interaction, overlay editing, mask review."
        ),
        stage_height="clamp(320px, 52vh, 640px)",
    )


def _render_source_context_panel(selected_frame: FrameLabel) -> None:
    source_status = "uploaded source available" if st.session_state.video_loaded else "waiting for uploaded source"
    render_workspace_video_panel(
        title="Source Context",
        metadata_items=[
            ("Frame", f"{selected_frame.index:04d}"),
            ("Timecode", selected_frame.timecode),
            ("Status", source_status),
        ],
        video_bytes=st.session_state.video_bytes,
        mime_type=st.session_state.video_mime_type,
        asset_name=st.session_state.video_name if st.session_state.video_loaded else None,
        empty_title="Source reference not available",
        empty_lines=[
            "Upload an original video in the operator column to inspect it here.",
            "Use this reference view for source comparison while authoring masks in the workbench.",
        ],
        panel_note=(
            f"Reference role: source comparison and operator inspection | "
            f"Frame note: {selected_frame.note}"
        ),
        stage_height="clamp(280px, 44vh, 540px)",
    )


def _split_summary_line(line: str) -> tuple[str, str]:
    label, value = line.split(": ", maxsplit=1)
    return label, value
