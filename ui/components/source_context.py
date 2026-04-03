"""Source transport and reference UI for a single backend-managed video asset."""

from __future__ import annotations

from html import escape

import streamlit as st

from ui.components.transport_controls import render_transport_controls
from ui.components.video_panel import render_workspace_video_panel
from ui.projection import PreviewProjection, WorkbenchProjection
from ui.state import (
    format_timecode,
    sync_source_timeline_frame_index,
    sync_source_timeline_widget_state,
)


def render_source_context_panel(
    preview_projection: PreviewProjection,
    workbench_projection: WorkbenchProjection,
) -> None:
    """Render the source reference area with preview transport and workbench linkage."""
    st.subheader("Source Context")
    st.caption("Reference playback, source metadata, transport controls, and timeline for the active backend-managed asset.")

    if not preview_projection.video_loaded or preview_projection.asset_id is None:
        render_workspace_video_panel(
            title="Source Reference",
            metadata_items=[
                ("Status", "Awaiting upload"),
                ("Role", "Reference"),
                ("Transport", "Inactive"),
            ],
            video_bytes=None,
            mime_type=None,
            asset_name=None,
            empty_title="Source reference not available",
            empty_lines=[
                "Upload a source video in the operator column to enable reference playback and frame navigation.",
                "Source Context hosts preview playback while the Mask Workbench stays focused on the selected work frame.",
            ],
            panel_note="Source Context drives preview playback and can freeze a frame into the workbench snapshot.",
            stage_height="clamp(220px, 38vh, 420px)",
        )
        return

    render_workspace_video_panel(
        title="Source Reference Video",
        metadata_items=[
            ("Asset", _short_asset_id(preview_projection.asset_id)),
            ("FPS", f"{preview_projection.video_fps:.2f}"),
            ("Frames", str(preview_projection.video_frame_count)),
            ("Resolution", f"{st.session_state.video_width} x {st.session_state.video_height}"),
        ],
        video_bytes=preview_projection.source_video_bytes,
        mime_type=preview_projection.video_mime_type,
        asset_name=preview_projection.video_name,
        empty_title="Source reference not available",
        empty_lines=[
            "The backend asset is registered, but the uploaded source video bytes are not available for playback.",
            "Re-upload the source video to restore the reference viewer.",
        ],
        panel_note="Reference role: inspect original motion while the workbench remains fixed on the active editing snapshot.",
        stage_height="clamp(240px, 42vh, 460px)",
        current_time_seconds=preview_projection.playback_timestamp_seconds,
        playback_running=preview_projection.playback_running,
        show_controls=False,
        component_height_px=560,
    )

    with st.container(border=True):
        st.markdown("**Source Navigation**")
        st.caption("Use transport and the single-video ruler to choose the preview position and freeze snapshots into the workbench.")

        if workbench_projection.workbench_frame_error_message:
            st.warning(workbench_projection.workbench_frame_error_message)

        metadata_columns = st.columns(4, gap="small")
        metadata_columns[0].write(f"Asset: {preview_projection.video_name}")
        metadata_columns[1].write(f"Duration: {format_timecode(preview_projection.video_duration_seconds)}")
        metadata_columns[2].write(f"Preview frame: {preview_projection.playback_frame_index:04d}")
        playback_label = "Running" if preview_projection.playback_running else "Paused"
        metadata_columns[3].write(f"Playback: {playback_label}")

        render_transport_controls(disabled=preview_projection.video_frame_count <= 0)
        _render_timeline_ruler(preview_projection.playback_frame_index)
        sync_source_timeline_widget_state()
        st.slider(
            "Timeline",
            min_value=0,
            max_value=max(preview_projection.video_frame_count - 1, 0),
            key="source_timeline_frame_index",
            on_change=sync_source_timeline_frame_index,
            disabled=preview_projection.video_frame_count <= 1,
        )

        context_columns = st.columns(3, gap="small")
        context_columns[0].write(f"Preview: {preview_projection.playback_frame_index:04d}")
        context_columns[1].write(f"Workbench: {workbench_projection.workbench_frame_index:04d}")
        context_columns[2].write(
            f"Workbench timecode: {format_timecode(workbench_projection.workbench_timestamp_seconds)}"
        )


def _render_timeline_ruler(current_frame_index: int) -> None:
    frame_count = max(int(st.session_state.video_frame_count), 1)
    duration_seconds = float(st.session_state.video_duration_seconds)
    playhead_percent = 0.0 if frame_count <= 1 else current_frame_index / (frame_count - 1)

    marker_positions = [0.0, 0.25, 0.5, 0.75, 1.0]
    markers_html = "".join(
        f"""
        <div class="source-timeline__marker" style="left:{position * 100:.2f}%;">
          <span class="source-timeline__tick"></span>
          <span class="source-timeline__label">{escape(format_timecode(duration_seconds * position))}</span>
        </div>
        """
        for position in marker_positions
    )

    st.html(
        f"""
        <style>
          .source-timeline {{
            padding: 0.5rem 0.1rem 0.25rem;
          }}
          .source-timeline__bar {{
            position: relative;
            height: 0.7rem;
            border-radius: 999px;
            background: linear-gradient(90deg, rgba(72, 120, 166, 0.35), rgba(72, 120, 166, 0.12));
            border: 1px solid rgba(120, 132, 145, 0.22);
            overflow: hidden;
          }}
          .source-timeline__fill {{
            position: absolute;
            inset: 0 auto 0 0;
            width: {playhead_percent * 100:.2f}%;
            background: linear-gradient(90deg, rgba(107, 170, 255, 0.75), rgba(73, 133, 230, 0.78));
          }}
          .source-timeline__playhead {{
            position: absolute;
            top: -0.18rem;
            left: {playhead_percent * 100:.2f}%;
            width: 0.14rem;
            height: 1.02rem;
            transform: translateX(-50%);
            background: #f5f7fa;
            box-shadow: 0 0 0 1px rgba(11, 13, 18, 0.85);
          }}
          .source-timeline__markers {{
            position: relative;
            height: 1.6rem;
            margin-top: 0.32rem;
          }}
          .source-timeline__marker {{
            position: absolute;
            top: 0;
            transform: translateX(-50%);
            text-align: center;
          }}
          .source-timeline__tick {{
            display: block;
            width: 1px;
            height: 0.45rem;
            margin: 0 auto 0.14rem;
            background: rgba(223, 228, 234, 0.8);
          }}
          .source-timeline__label {{
            display: block;
            font-size: 0.67rem;
            color: #cbd3dc;
            white-space: nowrap;
          }}
        </style>
        <section class="source-timeline">
          <div class="source-timeline__bar">
            <div class="source-timeline__fill"></div>
            <div class="source-timeline__playhead"></div>
          </div>
          <div class="source-timeline__markers">{markers_html}</div>
        </section>
        """,
        width="stretch",
    )


def _short_asset_id(asset_id: str) -> str:
    if len(asset_id) <= 8:
        return asset_id
    return asset_id[:8]
