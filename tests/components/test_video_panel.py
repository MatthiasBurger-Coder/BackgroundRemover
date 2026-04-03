"""Regression tests for synchronized source video rendering."""

from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
