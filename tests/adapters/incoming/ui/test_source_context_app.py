"""GUI regression tests for Source Context transport controls."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from src.application.infrastructure.wiring.video_asset_backend import get_video_asset_backend
from streamlit.testing.v1 import AppTest

TEST_VIDEO_PATH = Path(__file__).resolve().parents[3] / "resources" / "miki.mp4"
SOURCE_CONTEXT_APP = """
from ui.components.source_context import render_source_context_panel
from ui.projection import build_preview_projection, build_workbench_projection
from ui.state import initialize_state

initialize_state()
render_source_context_panel(build_preview_projection(), build_workbench_projection())
"""


class SourceContextAppTests(unittest.TestCase):
    """Protect Play/Pause behavior through the real Streamlit UI layer."""

    @classmethod
    def setUpClass(cls) -> None:
        backend = get_video_asset_backend()
        video_bytes = TEST_VIDEO_PATH.read_bytes()
        cls.source_video_bytes = video_bytes
        cls.metadata = backend.register_video_asset.execute(
            filename=TEST_VIDEO_PATH.name,
            video_bytes=video_bytes,
            mime_type="video/mp4",
        )

    def test_play_button_starts_preview_playback_without_moving_workbench(self) -> None:
        app = self._build_app()

        app.run()
        self._get_button(app, "Play").click().run()

        self.assertTrue(app.session_state["playback_running"])
        self.assertEqual(app.session_state["playback_frame_index"], 0)
        self.assertEqual(app.session_state["workbench_frame_index"], 0)
        self.assertEqual(app.session_state["playback_anchor_frame_index"], 0)
        self.assertIn("Playback running", app.session_state["last_action"])
        self.assertEqual(self._get_button(app, "Pause").label, "Pause")

    def test_pause_button_adopts_preview_frame_into_workbench_after_play(self) -> None:
        app = self._build_app()

        app.run()
        self._get_button(app, "Play").click().run()
        app.session_state["playback_frame_index"] = 7
        app.session_state["playback_timestamp_seconds"] = 7 / self.metadata.fps
        app.session_state["playback_anchor_frame_index"] = 7
        app.session_state["playback_started_at_seconds"] = 200.0
        with patch("ui.state.time.monotonic", return_value=200.0):
            self._get_button(app, "Pause").click().run()

        self.assertFalse(app.session_state["playback_running"])
        self.assertIsNone(app.session_state["playback_anchor_frame_index"])
        self.assertIsNone(app.session_state["playback_started_at_seconds"])
        self.assertEqual(app.session_state["workbench_frame_index"], 7)
        self.assertAlmostEqual(app.session_state["workbench_timestamp_seconds"], 7 / self.metadata.fps)
        self.assertIn("Playback paused", app.session_state["last_action"])
        self.assertEqual(self._get_button(app, "Play").label, "Play")

    def _build_app(self) -> AppTest:
        app = AppTest.from_string(SOURCE_CONTEXT_APP, default_timeout=10)
        self._seed_loaded_video_state(app)
        return app

    def _seed_loaded_video_state(self, app: AppTest) -> None:
        app.session_state["video_loaded"] = True
        app.session_state["video_name"] = self.metadata.filename
        app.session_state["active_video_name"] = self.metadata.filename
        app.session_state["video_mime_type"] = "video/mp4"
        app.session_state["source_video_bytes"] = self.source_video_bytes
        app.session_state["active_source_payload"] = self.source_video_bytes
        app.session_state["asset_id"] = self.metadata.asset_id
        app.session_state["active_asset_id"] = self.metadata.asset_id
        app.session_state["video_fps"] = self.metadata.fps
        app.session_state["video_frame_count"] = self.metadata.frame_count
        app.session_state["video_duration_seconds"] = self.metadata.duration_seconds
        app.session_state["video_width"] = self.metadata.width
        app.session_state["video_height"] = self.metadata.height
        app.session_state["playback_frame_index"] = 0
        app.session_state["playback_timestamp_seconds"] = 0.0
        app.session_state["workbench_frame_index"] = 0
        app.session_state["workbench_timestamp_seconds"] = 0.0
        app.session_state["workbench_frame_request_key"] = None
        app.session_state["workbench_frame_error_message"] = None
        app.session_state["source_timeline_frame_index"] = 0
        app.session_state["playback_running"] = False
        app.session_state["playback_anchor_frame_index"] = None
        app.session_state["playback_started_at_seconds"] = None
        app.session_state["last_action"] = "Seeded source context test state"

    def _get_button(self, app: AppTest, label: str):
        for button in app.button:
            if button.label == label:
                return button
        raise AssertionError(f"Button with label {label!r} was not rendered.")


if __name__ == "__main__":
    unittest.main()
