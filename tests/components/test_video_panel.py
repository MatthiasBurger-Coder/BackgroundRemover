"""Regression tests for synchronized source video rendering."""

from __future__ import annotations

import types
import unittest
from unittest.mock import Mock, patch

import ui.components.video_panel as video_panel
from ui.components.video_panel import build_workspace_video_stage_html


class VideoPanelTests(unittest.TestCase):
    """Protect the source video binding to synchronized playback state."""

    def test_build_workspace_video_stage_html_embeds_current_time_and_autoplay_state(self) -> None:
        rendered_html = build_workspace_video_stage_html(
            video_source="data:video/mp4;base64,ZmFrZQ==",
            mime_type="video/mp4",
            empty_title="Unavailable",
            empty_lines=["No source"],
            stage_height="320px",
            current_time_seconds=1.25,
            playback_running=True,
            show_controls=False,
        )

        self.assertIn("workspace-media-panel__video", rendered_html)
        self.assertIn("data-video-current-time=\"1.250\"", rendered_html)
        self.assertIn("data-video-autoplay=\"true\"", rendered_html)
        self.assertIn("autoplay muted playsinline", rendered_html)
        self.assertNotIn(" controls", rendered_html)

    def test_render_workspace_video_panel_uses_streamlit_iframe(self) -> None:
        iframe_mock = Mock()
        fake_streamlit = types.SimpleNamespace(iframe=iframe_mock)

        with patch.object(video_panel, "st", fake_streamlit):
            video_panel.render_workspace_video_panel(
                title="Source Reference",
                metadata_items=[("FPS", "24.00")],
                video_bytes=b"fake-video",
                mime_type="video/mp4",
                asset_name="clip.mp4",
                empty_title="Unavailable",
                empty_lines=["No source"],
                current_time_seconds=1.25,
                playback_running=True,
                show_controls=False,
                component_height_px=560,
            )

        iframe_mock.assert_called_once()
        iframe_source = iframe_mock.call_args.kwargs["src"]
        self.assertIn("workspace-media-panel__video", iframe_source)
        self.assertIn("<section class=\"workspace-media-panel\">", iframe_source)
        self.assertFalse(iframe_source.startswith("data:"))
        self.assertEqual(iframe_mock.call_args.kwargs["height"], 560)
        self.assertEqual(iframe_mock.call_args.kwargs["width"], "stretch")


if __name__ == "__main__":
    unittest.main()
