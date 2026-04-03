"""Regression tests for workbench frame binding in the UI adapter state layer."""

from __future__ import annotations

import types
import unittest
from unittest.mock import Mock, patch

from src.application.domain.errors.video_asset_errors import VideoFrameExtractionError
import ui.state as ui_state


class _SessionState(dict):
    """Dictionary with attribute access compatible with Streamlit session state usage."""

    def __getattr__(self, item: str):
        try:
            return self[item]
        except KeyError as error:
            raise AttributeError(item) from error

    def __setattr__(self, key: str, value) -> None:
        self[key] = value


class StateBindingTests(unittest.TestCase):
    """Protect current-frame loading and workbench binding behavior."""

    def test_ensure_current_frame_loaded_updates_bound_workbench_frame(self) -> None:
        session_state = _SessionState(
            video_loaded=True,
            asset_id="asset-1",
            video_frame_count=12,
            current_frame_index=5,
            current_frame_timestamp_seconds=0.0,
            current_frame_image_bytes=None,
            current_frame_image_mime_type=None,
            current_frame_width=0,
            current_frame_height=0,
            current_frame_request_key=None,
            frame_error_message=None,
            playback_running=False,
            playback_anchor_frame_index=None,
            playback_started_at_seconds=None,
        )
        fake_frame = types.SimpleNamespace(
            frame_index=5,
            timestamp_seconds=0.5,
            image_bytes=b"frame-bytes",
            mime_type="image/png",
            width=1280,
            height=720,
        )
        fake_backend = types.SimpleNamespace(
            get_video_frame=types.SimpleNamespace(execute=Mock(return_value=fake_frame))
        )

        with patch.object(ui_state, "st", types.SimpleNamespace(session_state=session_state)), patch.object(
            ui_state,
            "get_video_asset_backend",
            return_value=fake_backend,
        ):
            ui_state.ensure_current_frame_loaded()

        self.assertEqual(session_state.current_frame_index, 5)
        self.assertAlmostEqual(session_state.current_frame_timestamp_seconds, 0.5)
        self.assertEqual(session_state.current_frame_image_bytes, b"frame-bytes")
        self.assertEqual(session_state.current_frame_image_mime_type, "image/png")
        self.assertEqual(session_state.current_frame_width, 1280)
        self.assertEqual(session_state.current_frame_height, 720)
        self.assertIsNone(session_state.frame_error_message)

    def test_ensure_current_frame_loaded_stops_playback_on_frame_error(self) -> None:
        session_state = _SessionState(
            video_loaded=True,
            asset_id="asset-1",
            video_frame_count=12,
            current_frame_index=5,
            current_frame_timestamp_seconds=0.5,
            current_frame_image_bytes=b"stale",
            current_frame_image_mime_type="image/png",
            current_frame_width=1280,
            current_frame_height=720,
            current_frame_request_key=None,
            frame_error_message=None,
            playback_running=True,
            playback_anchor_frame_index=5,
            playback_started_at_seconds=10.0,
        )
        fake_backend = types.SimpleNamespace(
            get_video_frame=types.SimpleNamespace(
                execute=Mock(side_effect=VideoFrameExtractionError("frame decode failed"))
            )
        )

        with patch.object(ui_state, "st", types.SimpleNamespace(session_state=session_state)), patch.object(
            ui_state,
            "get_video_asset_backend",
            return_value=fake_backend,
        ):
            ui_state.ensure_current_frame_loaded()

        self.assertFalse(session_state.playback_running)
        self.assertIsNone(session_state.current_frame_image_bytes)
        self.assertIsNone(session_state.current_frame_image_mime_type)
        self.assertEqual(session_state.frame_error_message, "frame decode failed")
        self.assertEqual(session_state.last_action, "Frame loading failed")


if __name__ == "__main__":
    unittest.main()
