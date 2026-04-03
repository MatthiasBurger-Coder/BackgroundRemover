"""Source transport and timeline UI for a single backend-managed video asset."""

from __future__ import annotations

from html import escape

import streamlit as st

from ui.components.transport_controls import render_transport_controls
from ui.state import format_timecode, sync_current_frame_index


def render_source_context_panel() -> None:
    """Render the single-asset source navigation area."""
    st.subheader("Source Context")
    st.caption("Single-video transport and ruler for backend-managed source navigation.")

    if not st.session_state.video_loaded or st.session_state.asset_id is None:
        st.info("Upload a source video in the operator column to enable transport and timeline navigation.")
        st.write("The workbench will bind to the selected frame after the asset is registered.")
        return

    summary_columns = st.columns(5, gap="small")
    summary_columns[0].metric("Asset", _short_asset_id(st.session_state.asset_id))
    summary_columns[1].metric("FPS", f"{st.session_state.video_fps:.2f}")
    summary_columns[2].metric("Frames", str(st.session_state.video_frame_count))
    summary_columns[3].metric("Duration", format_timecode(st.session_state.video_duration_seconds))
    summary_columns[4].metric("Resolution", f"{st.session_state.video_width} x {st.session_state.video_height}")

    with st.container(border=True):
        st.markdown(f"**Source Asset**  \n{st.session_state.video_name}")
        render_transport_controls(disabled=st.session_state.video_frame_count <= 0)
        _render_timeline_ruler()
        st.slider(
            "Timeline",
            min_value=0,
            max_value=max(st.session_state.video_frame_count - 1, 0),
            key="current_frame_index",
            on_change=sync_current_frame_index,
            disabled=st.session_state.video_frame_count <= 1,
        )

        context_columns = st.columns(3, gap="small")
        context_columns[0].write(f"Frame: {st.session_state.current_frame_index:04d}")
        context_columns[1].write(f"Timecode: {format_timecode(st.session_state.current_frame_timestamp_seconds)}")
        playback_label = "Running" if st.session_state.playback_running else "Paused"
        context_columns[2].write(f"Playback: {playback_label}")
        st.caption("Source Context drives the shared current frame used by the Mask Workbench.")


def _render_timeline_ruler() -> None:
    current_frame_index = int(st.session_state.current_frame_index)
    frame_count = max(int(st.session_state.video_frame_count), 1)
    duration_seconds = float(st.session_state.video_duration_seconds)
    playhead_percent = 0.0 if frame_count <= 1 else current_frame_index / (frame_count - 1)

    marker_positions = [0.0, 0.25, 0.5, 0.75, 1.0]
    markers_html = "".join(
        """
        <div class="source-timeline__marker" style="left:{left:.2f}%;">
          <span class="source-timeline__tick"></span>
          <span class="source-timeline__label">{label}</span>
        </div>
        """.format(
            left=position * 100,
            label=escape(format_timecode(duration_seconds * position)),
        )
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
