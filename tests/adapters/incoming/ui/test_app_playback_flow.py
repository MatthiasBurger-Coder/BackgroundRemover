"""GUI regression tests for full-app playback flow."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from src.application.infrastructure.wiring.video_asset_backend import get_video_asset_backend
from streamlit.testing.v1 import AppTest

TEST_VIDEO_PATH = Path(__file__).resolve().parents[3] / "resources" / "miki.mp4"


class AppPlaybackFlowTests(unittest.TestCase):
    """Protect full-app playback behavior against unstable rerun loops."""

    @classmethod
    def setUpClass(cls) -> None:
        backend = get_video_asset_backend()
        video_bytes = TEST_VIDEO_PATH.read_bytes()
        cls.video_bytes = video_bytes
        cls.metadata = backend.register_video_asset.execute(
            filename=TEST_VIDEO_PATH.name,
            video_bytes=video_bytes,
            mime_type="video/mp4",
        )

    def test_full_app_stays_stable_and_advances_frame_while_playback_is_running(self) -> None:
        app = self._build_app()
        app.session_state["playback_running"] = True
        app.session_state["playback_anchor_frame_index"] = 0
        app.session_state["playback_started_at_seconds"] = 100.0

        with patch("ui.state.time.monotonic", return_value=100.6), patch(
            "ui.components.sidebar.register_video_selection",
            return_value=False,
        ):
            app.run(timeout=10)

        self.assertTrue(app.session_state["playback_running"])
        self.assertGreater(app.session_state["current_frame_index"], 0)

    def _build_app(self) -> AppTest:
        app = AppTest.from_file("ui/app.py", default_timeout=10)
        self._seed_loaded_video_state(app)
        return app

    def _seed_loaded_video_state(self, app: AppTest) -> None:
        app.session_state["video_loaded"] = True
        app.session_state["video_name"] = self.metadata.filename
        app.session_state["video_mime_type"] = "video/mp4"
        app.session_state["source_video_bytes"] = self.video_bytes
        app.session_state["asset_id"] = self.metadata.asset_id
        app.session_state["video_fps"] = self.metadata.fps
        app.session_state["video_frame_count"] = self.metadata.frame_count
        app.session_state["video_duration_seconds"] = self.metadata.duration_seconds
        app.session_state["video_width"] = self.metadata.width
        app.session_state["video_height"] = self.metadata.height
        app.session_state["current_frame_index"] = 0
        app.session_state["current_frame_timestamp_seconds"] = 0.0
        app.session_state["current_frame_request_key"] = None
        app.session_state["frame_error_message"] = None
        app.session_state["playback_running"] = False
        app.session_state["playback_anchor_frame_index"] = None
        app.session_state["playback_started_at_seconds"] = None
        app.session_state["prompt_entries"] = []
        app.session_state["last_action"] = "Seeded full app test state"

if __name__ == "__main__":
    unittest.main()
