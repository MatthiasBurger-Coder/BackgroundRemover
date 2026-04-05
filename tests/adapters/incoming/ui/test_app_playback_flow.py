"""GUI regression tests for full-app playback flow."""

from __future__ import annotations

import types
import unittest
from pathlib import Path
from unittest.mock import ANY, Mock, patch

import ui.app as ui_app
from application.infrastructure.wiring.video_asset_backend import get_video_asset_backend
from streamlit.testing.v1 import AppTest

TEST_VIDEO_PATH = Path(__file__).resolve().parents[3] / "resources" / "miki.mp4"
OPERATOR_PANEL_APP = """
from ui.components.sidebar import render_operator_panel
from ui.state import initialize_state

initialize_state()
render_operator_panel()
"""


class AppPlaybackFlowTests(unittest.TestCase):
    """Protect full-app preview playback without forcing workbench rerenders."""

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

    def test_full_app_advances_preview_while_workbench_stays_on_last_snapshot(self) -> None:
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
        self.assertGreater(app.session_state["playback_frame_index"], 0)
        self.assertEqual(app.session_state["workbench_frame_index"], 0)

    def _build_app(self) -> AppTest:
        app = AppTest.from_file("ui/app.py", default_timeout=10)
        self._seed_loaded_video_state(app)
        return app

    def _seed_loaded_video_state(self, app: AppTest) -> None:
        app.session_state["video_loaded"] = True
        app.session_state["video_name"] = self.metadata.filename
        app.session_state["active_video_name"] = self.metadata.filename
        app.session_state["video_mime_type"] = "video/mp4"
        app.session_state["source_video_bytes"] = self.video_bytes
        app.session_state["active_source_payload"] = self.video_bytes
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
        app.session_state["playback_running"] = False
        app.session_state["playback_anchor_frame_index"] = None
        app.session_state["playback_started_at_seconds"] = None
        app.session_state["source_timeline_frame_index"] = 0
        app.session_state["prompt_entries"] = []
        app.session_state["last_action"] = "Seeded full app test state"


class LiveOperatorWorkspaceFragmentTests(unittest.TestCase):
    """Protect the preview fragment body against stale reruns and workbench coupling."""

    def _build_preview_projection(self, *, playback_running: bool) -> types.SimpleNamespace:
        return types.SimpleNamespace(
            asset_id="asset-1",
            playback_frame_index=3,
            playback_running=playback_running,
        )

    def _build_workbench_projection(self) -> types.SimpleNamespace:
        return types.SimpleNamespace(
            asset_id="asset-1",
            workbench_frame_index=2,
            workbench_timestamp_seconds=0.125,
            prompt_count=1,
        )

    def test_main_renders_stable_page_shell_before_mounting_paused_fragment(self) -> None:
        session_state = types.SimpleNamespace(
            playback_running=False,
            asset_id="asset-1",
            playback_frame_index=0,
            workbench_frame_index=0,
            ui_generation=3,
            playback_generation=8,
        )
        fake_st = types.SimpleNamespace(session_state=session_state, set_page_config=Mock())

        with (
            patch.object(ui_app, "st", fake_st),
            patch.object(ui_app, "configure_logging"),
            patch.object(ui_app, "initialize_state"),
            patch.object(ui_app, "ensure_workbench_frame_loaded"),
            patch.object(ui_app, "get_failure_cases", return_value=["failure"]),
            patch.object(ui_app, "build_preview_projection", return_value=self._build_preview_projection(playback_running=False)),
            patch.object(ui_app, "build_workbench_projection", return_value=self._build_workbench_projection()),
            patch.object(ui_app, "render_page_shell") as render_page_shell,
            patch.object(ui_app, "render_live_preview_fragment") as render_fragment,
        ):
            ui_app.main()

        render_page_shell.assert_called_once_with(["failure"], ANY, ANY)
        render_fragment.assert_called_once_with(
            playback_interval_seconds=None,
            expected_ui_generation=3,
            expected_playback_generation=8,
        )

    def test_live_fragment_uses_playback_interval_when_playback_is_running(self) -> None:
        session_state = types.SimpleNamespace(
            playback_running=True,
            asset_id="asset-1",
            playback_frame_index=0,
            workbench_frame_index=0,
            ui_generation=3,
            playback_generation=8,
        )
        fake_st = types.SimpleNamespace(session_state=session_state, set_page_config=Mock())

        with (
            patch.object(ui_app, "st", fake_st),
            patch.object(ui_app, "configure_logging"),
            patch.object(ui_app, "initialize_state"),
            patch.object(ui_app, "ensure_workbench_frame_loaded"),
            patch.object(ui_app, "get_failure_cases", return_value=["failure"]),
            patch.object(ui_app, "get_playback_interval_seconds", return_value=0.25),
            patch.object(ui_app, "build_preview_projection", return_value=self._build_preview_projection(playback_running=True)),
            patch.object(ui_app, "build_workbench_projection", return_value=self._build_workbench_projection()),
            patch.object(ui_app, "render_page_shell"),
            patch.object(ui_app, "render_live_preview_fragment") as render_fragment,
        ):
            ui_app.main()

        render_fragment.assert_called_once_with(
            playback_interval_seconds=0.25,
            expected_ui_generation=3,
            expected_playback_generation=8,
        )

    def test_live_fragment_body_skips_playback_sync_when_paused(self) -> None:
        session_state = types.SimpleNamespace(
            playback_running=False,
            ui_generation=3,
            playback_generation=8,
        )
        fake_st = types.SimpleNamespace(session_state=session_state, rerun=Mock())

        with (
            patch.object(ui_app, "st", fake_st),
            patch.object(ui_app, "sync_playback_position") as sync_playback,
            patch.object(ui_app, "build_preview_projection", return_value=self._build_preview_projection(playback_running=False)),
        ):
            ui_app._render_live_preview_fragment_body(
                expected_ui_generation=3,
                expected_playback_generation=8,
            )

        sync_playback.assert_not_called()
        fake_st.rerun.assert_not_called()

    def test_live_fragment_body_syncs_playback_when_running_without_workbench_render(self) -> None:
        session_state = types.SimpleNamespace(
            playback_running=True,
            ui_generation=3,
            playback_generation=8,
        )
        fake_st = types.SimpleNamespace(session_state=session_state, rerun=Mock())

        with (
            patch.object(ui_app, "st", fake_st),
            patch.object(ui_app, "sync_playback_position") as sync_playback,
            patch.object(ui_app, "build_preview_projection", return_value=self._build_preview_projection(playback_running=True)),
            patch.object(ui_app, "render_workbench_frame_panel") as render_workbench,
        ):
            ui_app._render_live_preview_fragment_body(
                expected_ui_generation=3,
                expected_playback_generation=8,
            )

        sync_playback.assert_called_once_with()
        render_workbench.assert_not_called()
        fake_st.rerun.assert_not_called()

    def test_live_fragment_configures_dynamic_run_every(self) -> None:
        session_state = types.SimpleNamespace(
            playback_running=True,
            ui_generation=3,
            playback_generation=8,
        )
        run_every_values: list[float | None] = []

        def fake_fragment(func=None, *, run_every=None):
            run_every_values.append(run_every)

            def wrapped(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapped

        fake_st = types.SimpleNamespace(session_state=session_state, fragment=fake_fragment, rerun=Mock())

        with patch.object(ui_app, "st", fake_st), patch.object(ui_app, "_render_live_preview_fragment_body") as body:
            ui_app.render_live_preview_fragment(
                playback_interval_seconds=0.25,
                expected_ui_generation=3,
                expected_playback_generation=8,
            )

        self.assertEqual(run_every_values, [0.25])
        body.assert_called_once_with(
            expected_ui_generation=3,
            expected_playback_generation=8,
        )

    def test_live_fragment_body_ignores_stale_generation_without_rerun(self) -> None:
        session_state = types.SimpleNamespace(
            playback_running=True,
            ui_generation=7,
            playback_generation=12,
        )
        rerun = Mock()
        fake_st = types.SimpleNamespace(session_state=session_state, rerun=rerun)

        with patch.object(ui_app, "st", fake_st), patch.object(
            ui_app,
            "build_preview_projection",
        ) as build_preview_projection:
            ui_app._render_live_preview_fragment_body(
                expected_ui_generation=6,
                expected_playback_generation=11,
            )

        rerun.assert_not_called()
        build_preview_projection.assert_not_called()

    def test_live_fragment_body_requests_app_rerun_when_playback_stops_during_sync(self) -> None:
        session_state = types.SimpleNamespace(
            playback_running=True,
            ui_generation=3,
            playback_generation=8,
        )
        rerun = Mock()
        fake_st = types.SimpleNamespace(session_state=session_state, rerun=rerun)

        def stop_playback() -> None:
            session_state.playback_running = False

        with (
            patch.object(ui_app, "st", fake_st),
            patch.object(ui_app, "sync_playback_position", side_effect=stop_playback) as sync_playback,
            patch.object(ui_app, "build_preview_projection", return_value=self._build_preview_projection(playback_running=False)),
        ):
            ui_app._render_live_preview_fragment_body(
                expected_ui_generation=3,
                expected_playback_generation=8,
            )

        rerun.assert_called_once_with()
        sync_playback.assert_called_once_with()


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
        app.session_state["playback_frame_index"] = 0
        app.session_state["playback_timestamp_seconds"] = 0.0
        app.session_state["workbench_frame_index"] = 0
        app.session_state["workbench_timestamp_seconds"] = 0.0
        app.session_state["workbench_frame_request_key"] = None
        app.session_state["workbench_frame_error_message"] = None
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
