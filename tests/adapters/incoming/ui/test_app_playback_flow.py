"""GUI regression tests for full-app playback flow."""

from __future__ import annotations

import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import ui.app as ui_app
from src.application.infrastructure.wiring.video_asset_backend import get_video_asset_backend
from streamlit.testing.v1 import AppTest

TEST_VIDEO_PATH = Path(__file__).resolve().parents[3] / "resources" / "miki.mp4"
OPERATOR_PANEL_APP = """
from ui.components.sidebar import render_operator_panel
from ui.state import initialize_state

initialize_state()
render_operator_panel()
"""


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


class LiveOperatorWorkspaceFragmentTests(unittest.TestCase):
    """Protect the live fragment body against paused-state hot-loop reruns."""

    def test_live_fragment_requests_full_app_rerun_when_playback_is_paused(self) -> None:
        session_state = types.SimpleNamespace(
            playback_running=False,
            ui_generation=3,
            playback_generation=8,
        )

        class _StopFragment(Exception):
            pass

        rerun = Mock(side_effect=_StopFragment)
        fake_st = types.SimpleNamespace(session_state=session_state, rerun=rerun)

        with (
            patch.object(ui_app, "st", fake_st),
            patch.object(ui_app, "render_operator_workspace") as render_workspace,
            self.assertRaises(_StopFragment),
        ):
            ui_app.render_live_operator_workspace.__wrapped__(
                [],
                expected_ui_generation=3,
                expected_playback_generation=8,
            )

        rerun.assert_called_once_with(scope="app")
        render_workspace.assert_not_called()

    def test_live_fragment_renders_workspace_while_playback_is_running(self) -> None:
        session_state = types.SimpleNamespace(
            playback_running=True,
            ui_generation=3,
            playback_generation=8,
        )
        fake_st = types.SimpleNamespace(session_state=session_state, rerun=Mock())

        with patch.object(ui_app, "st", fake_st), patch.object(ui_app, "render_operator_workspace") as render_workspace:
            ui_app.render_live_operator_workspace.__wrapped__(
                ["failure"],
                expected_ui_generation=3,
                expected_playback_generation=8,
            )

        fake_st.rerun.assert_not_called()
        render_workspace.assert_called_once_with(["failure"])

    def test_live_fragment_requests_full_app_rerun_when_generation_is_stale(self) -> None:
        session_state = types.SimpleNamespace(
            playback_running=True,
            ui_generation=7,
            playback_generation=12,
        )

        class _StopFragment(Exception):
            pass

        rerun = Mock(side_effect=_StopFragment)
        fake_st = types.SimpleNamespace(session_state=session_state, rerun=rerun)

        with (
            patch.object(ui_app, "st", fake_st),
            patch.object(ui_app, "render_operator_workspace") as render_workspace,
            self.assertRaises(_StopFragment),
        ):
            ui_app.render_live_operator_workspace.__wrapped__(
                [],
                expected_ui_generation=6,
                expected_playback_generation=11,
            )

        rerun.assert_called_once_with(scope="app")
        render_workspace.assert_not_called()


class OperatorPanelSourceLifecycleTests(unittest.TestCase):
    """Protect explicit source removal from the real operator panel UI."""

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

    def test_remove_video_button_clears_active_source(self) -> None:
        app = AppTest.from_string(OPERATOR_PANEL_APP, default_timeout=10)
        self._seed_loaded_video_state(app)

        app.run()
        self._get_button(app, "Remove Video").click().run()

        self.assertFalse(app.session_state["video_loaded"])
        self.assertIsNone(app.session_state["asset_id"])
        self.assertIsNone(app.session_state["active_asset_id"])
        self.assertFalse(app.session_state["playback_running"])

    def _seed_loaded_video_state(self, app: AppTest) -> None:
        app.session_state["video_loaded"] = True
        app.session_state["video_name"] = self.metadata.filename
        app.session_state["active_video_name"] = self.metadata.filename
        app.session_state["video_mime_type"] = "video/mp4"
        app.session_state["source_video_bytes"] = self.video_bytes
        app.session_state["active_source_payload"] = self.video_bytes
        app.session_state["asset_id"] = self.metadata.asset_id
        app.session_state["active_asset_id"] = self.metadata.asset_id
        app.session_state["source_fingerprint"] = "fingerprint-1"
        app.session_state["video_upload_signature"] = "fingerprint-1"
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
        app.session_state["ui_generation"] = 2
        app.session_state["playback_generation"] = 4
        app.session_state["prompt_entries"] = []
        app.session_state["last_action"] = "Seeded operator panel test state"

    def _get_button(self, app: AppTest, label: str):
        for button in app.button:
            if button.label == label:
                return button
        raise AssertionError(f"Button with label {label!r} was not rendered.")


if __name__ == "__main__":
    unittest.main()
