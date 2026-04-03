"""Regression tests for workbench frame binding in the UI adapter state layer."""

from __future__ import annotations

import hashlib
import types
import unittest
from unittest.mock import Mock, patch

import ui.state as ui_state
from src.application.domain.errors.video_asset_errors import VideoFrameExtractionError
from src.application.domain.model.video_asset import VideoAssetMetadata


class _SessionState(dict):
    """Dictionary with attribute access compatible with Streamlit session state usage."""

    def __getattr__(self, item: str):
        try:
            return self[item]
        except KeyError as error:
            raise AttributeError(item) from error

    def __setattr__(self, key: str, value) -> None:
        self[key] = value


class _UploadedFile:
    """Minimal uploaded file double compatible with the Streamlit state adapter."""

    def __init__(self, *, name: str, mime_type: str, payload: bytes) -> None:
        self.name = name
        self.type = mime_type
        self._payload = payload

    def getvalue(self) -> bytes:
        return self._payload


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

    def test_register_video_selection_preserves_loaded_frame_on_same_upload_rerun(self) -> None:
        uploaded_bytes = b"same-video"
        upload_signature = hashlib.sha256(uploaded_bytes).hexdigest()
        uploaded_file = _UploadedFile(
            name="clip.mp4",
            mime_type="video/mp4",
            payload=uploaded_bytes,
        )
        metadata = VideoAssetMetadata(
            asset_id="asset-1",
            filename="clip.mp4",
            fps=24.0,
            frame_count=120,
            duration_seconds=5.0,
            width=640,
            height=360,
        )
        session_state = _SessionState(
            video_loaded=True,
            video_name="clip.mp4",
            video_mime_type="video/mp4",
            source_video_bytes=uploaded_bytes,
            video_upload_signature=upload_signature,
            asset_id="asset-1",
            video_fps=24.0,
            video_frame_count=120,
            video_duration_seconds=5.0,
            video_width=640,
            video_height=360,
            current_frame_index=12,
            current_frame_timestamp_seconds=0.5,
            current_frame_image_bytes=b"frame-bytes",
            current_frame_image_mime_type="image/png",
            current_frame_width=640,
            current_frame_height=360,
            current_frame_request_key=("asset-1", 12),
            frame_error_message=None,
            playback_running=False,
            playback_anchor_frame_index=None,
            playback_started_at_seconds=None,
            prompt_entries=[],
            last_action="Seeded state",
        )
        fake_backend = types.SimpleNamespace(
            get_video_asset_metadata=types.SimpleNamespace(execute=Mock(return_value=metadata))
        )

        with patch.object(ui_state, "st", types.SimpleNamespace(session_state=session_state)), patch.object(
            ui_state,
            "get_video_asset_backend",
            return_value=fake_backend,
        ):
            changed = ui_state.register_video_selection(uploaded_file)

        self.assertFalse(changed)
        self.assertEqual(session_state.current_frame_index, 12)
        self.assertAlmostEqual(session_state.current_frame_timestamp_seconds, 0.5)
        self.assertEqual(session_state.current_frame_image_bytes, b"frame-bytes")
        self.assertEqual(session_state.current_frame_request_key, ("asset-1", 12))
        self.assertFalse(session_state.playback_running)

    def test_register_video_selection_preserves_playback_state_on_same_upload_rerun(self) -> None:
        uploaded_bytes = b"same-video"
        upload_signature = hashlib.sha256(uploaded_bytes).hexdigest()
        uploaded_file = _UploadedFile(
            name="clip.mp4",
            mime_type="video/mp4",
            payload=uploaded_bytes,
        )
        metadata = VideoAssetMetadata(
            asset_id="asset-1",
            filename="clip.mp4",
            fps=24.0,
            frame_count=120,
            duration_seconds=5.0,
            width=640,
            height=360,
        )
        session_state = _SessionState(
            video_loaded=True,
            video_name="clip.mp4",
            video_mime_type="video/mp4",
            source_video_bytes=uploaded_bytes,
            video_upload_signature=upload_signature,
            asset_id="asset-1",
            video_fps=24.0,
            video_frame_count=120,
            video_duration_seconds=5.0,
            video_width=640,
            video_height=360,
            current_frame_index=12,
            current_frame_timestamp_seconds=0.5,
            current_frame_image_bytes=b"frame-bytes",
            current_frame_image_mime_type="image/png",
            current_frame_width=640,
            current_frame_height=360,
            current_frame_request_key=("asset-1", 12),
            frame_error_message=None,
            playback_running=True,
            playback_anchor_frame_index=10,
            playback_started_at_seconds=123.0,
            prompt_entries=[],
            last_action="Seeded state",
        )
        fake_backend = types.SimpleNamespace(
            get_video_asset_metadata=types.SimpleNamespace(execute=Mock(return_value=metadata))
        )

        with patch.object(ui_state, "st", types.SimpleNamespace(session_state=session_state)), patch.object(
            ui_state,
            "get_video_asset_backend",
            return_value=fake_backend,
        ):
            changed = ui_state.register_video_selection(uploaded_file)

        self.assertFalse(changed)
        self.assertTrue(session_state.playback_running)
        self.assertEqual(session_state.playback_anchor_frame_index, 10)
        self.assertEqual(session_state.playback_started_at_seconds, 123.0)
        self.assertEqual(session_state.current_frame_request_key, ("asset-1", 12))


if __name__ == "__main__":
    unittest.main()
