"""Reusable viewport-aware workspace media panels for the Streamlit UI shell."""

from __future__ import annotations

import base64
from html import escape

import streamlit as st


def render_workspace_video_panel(
    title: str,
    metadata_items: list[tuple[str, str]],
    *,
    video_bytes: bytes | None,
    mime_type: str | None,
    asset_name: str | None,
    empty_title: str,
    empty_lines: list[str],
    panel_note: str | None = None,
    stage_height: str = "clamp(320px, 56vh, 680px)",
) -> None:
    """Render a viewport-aware HTML video panel for uploaded media."""
    video_source = _build_video_source(video_bytes, mime_type)
    body_html = _build_video_stage_html(
        video_source=video_source,
        mime_type=mime_type or "video/mp4",
        empty_title=empty_title,
        empty_lines=empty_lines,
        stage_height=stage_height,
    )
    footer_parts: list[str] = []
    if asset_name:
        footer_parts.append(f"Asset: {escape(asset_name)}")
    if panel_note:
        footer_parts.append(escape(panel_note))

    st.html(
        _build_panel_html(
            title=title,
            metadata_items=metadata_items,
            body_html=body_html,
            footer_text=" | ".join(footer_parts) if footer_parts else None,
        ),
        width="stretch",
    )


def render_workspace_placeholder_panel(
    title: str,
    metadata_items: list[tuple[str, str]],
    *,
    placeholder_title: str,
    placeholder_lines: list[str],
    panel_note: str | None = None,
    stage_height: str = "clamp(220px, 34vh, 360px)",
) -> None:
    """Render a reusable placeholder panel with the same workspace framing as the video view."""
    body_html = _build_placeholder_stage_html(
        placeholder_title=placeholder_title,
        placeholder_lines=placeholder_lines,
        stage_height=stage_height,
    )
    st.html(
        _build_panel_html(
            title=title,
            metadata_items=metadata_items,
            body_html=body_html,
            footer_text=panel_note,
        ),
        width="stretch",
    )


def _build_video_source(video_bytes: bytes | None, mime_type: str | None) -> str | None:
    if not video_bytes:
        return None
    encoded = base64.b64encode(video_bytes).decode("ascii")
    return f"data:{mime_type or 'video/mp4'};base64,{encoded}"


def _build_video_stage_html(
    *,
    video_source: str | None,
    mime_type: str,
    empty_title: str,
    empty_lines: list[str],
    stage_height: str,
) -> str:
    if video_source is None:
        return _build_placeholder_stage_html(
            placeholder_title=empty_title,
            placeholder_lines=empty_lines,
            stage_height=stage_height,
        )

    return f"""
    <div class="workspace-media-panel__stage" style="height: {escape(stage_height)};">
      <video class="workspace-media-panel__video" controls preload="metadata">
        <source src="{video_source}" type="{escape(mime_type)}" />
        Your browser does not support the HTML video element.
      </video>
    </div>
    """


def _build_placeholder_stage_html(
    *,
    placeholder_title: str,
    placeholder_lines: list[str],
    stage_height: str,
) -> str:
    lines_html = "".join(f"<p>{escape(line)}</p>" for line in placeholder_lines)
    return f"""
    <div class="workspace-media-panel__stage" style="height: {escape(stage_height)};">
      <div class="workspace-media-panel__placeholder">
        <div class="workspace-media-panel__placeholder-title">{escape(placeholder_title)}</div>
        {lines_html}
      </div>
    </div>
    """


def _build_panel_html(
    *,
    title: str,
    metadata_items: list[tuple[str, str]],
    body_html: str,
    footer_text: str | None,
) -> str:
    metadata_html = "".join(
        """
        <div class="workspace-media-panel__meta-item">
          <span class="workspace-media-panel__meta-label">{label}</span>
          <span class="workspace-media-panel__meta-value">{value}</span>
        </div>
        """.format(label=escape(label), value=escape(value))
        for label, value in metadata_items
    )
    footer_html = (
        f'<div class="workspace-media-panel__footer">{escape(footer_text)}</div>'
        if footer_text
        else ""
    )
    return f"""
    <style>
      .workspace-media-panel {{
        border: 1px solid rgba(120, 132, 145, 0.28);
        border-radius: 0.85rem;
        background: linear-gradient(180deg, rgba(16, 20, 26, 0.96), rgba(10, 13, 18, 0.98));
        padding: 0.7rem 0.8rem 0.8rem;
        margin-bottom: 0.6rem;
      }}
      .workspace-media-panel__header {{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 0.55rem;
        flex-wrap: wrap;
      }}
      .workspace-media-panel__title {{
        margin: 0;
        font-size: 0.98rem;
        font-weight: 600;
        color: #f1f3f5;
        white-space: nowrap;
      }}
      .workspace-media-panel__meta {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
        gap: 0.4rem;
        flex: 1 1 28rem;
      }}
      .workspace-media-panel__meta-item {{
        border: 1px solid rgba(120, 132, 145, 0.24);
        border-radius: 0.6rem;
        background: rgba(255, 255, 255, 0.03);
        padding: 0.32rem 0.48rem 0.38rem;
        min-height: 2.6rem;
      }}
      .workspace-media-panel__meta-label {{
        display: block;
        font-size: 0.64rem;
        line-height: 1.1;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #aab4bf;
        margin-bottom: 0.16rem;
      }}
      .workspace-media-panel__meta-value {{
        display: block;
        font-size: 0.82rem;
        line-height: 1.2;
        color: #f5f7fa;
      }}
      .workspace-media-panel__stage {{
        width: 100%;
        border-radius: 0.75rem;
        overflow: hidden;
        border: 1px solid rgba(120, 132, 145, 0.22);
        background: #06080b;
        display: flex;
        align-items: center;
        justify-content: center;
      }}
      .workspace-media-panel__video {{
        width: 100%;
        height: 100%;
        object-fit: contain;
        background: #06080b;
      }}
      .workspace-media-panel__placeholder {{
        width: min(42rem, 100%);
        padding: 1rem 1.1rem;
        color: #d5dbe2;
      }}
      .workspace-media-panel__placeholder-title {{
        font-size: 0.98rem;
        font-weight: 600;
        margin-bottom: 0.32rem;
        color: #eef1f4;
      }}
      .workspace-media-panel__placeholder p {{
        margin: 0.18rem 0;
        font-size: 0.82rem;
        line-height: 1.35;
      }}
      .workspace-media-panel__footer {{
        margin-top: 0.48rem;
        font-size: 0.76rem;
        line-height: 1.35;
        color: #c3cad2;
      }}
    </style>
    <section class="workspace-media-panel">
      <div class="workspace-media-panel__header">
        <h3 class="workspace-media-panel__title">{escape(title)}</h3>
        <div class="workspace-media-panel__meta">{metadata_html}</div>
      </div>
      {body_html}
      {footer_html}
    </section>
    """
