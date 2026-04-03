"""Regression tests for workbench frame binding in the UI adapter state layer."""

from __future__ import annotations

import hashlib
import types
import unittest
from contextlib import ExitStack
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

    def _patch_state_modules(self, session_state: _SessionState) -> ExitStack:
        session_proxy = types.SimpleNamespace(session_state=session_state)
        stack = ExitStack()
        stack.enter_context(patch.object(ui_state.generation_state, "st", session_proxy))
        stack.enter_context(patch.object(ui_state.playback_state, "st", session_proxy))
        stack.enter_context(patch.object(ui_state.source_state, "st", session_proxy))
        stack.enter_context(patch.object(ui_state.video_metadata_state, "st", session_proxy))
        stack.enter_context(patch.object(ui_state.workbench_state, "st", session_proxy))
        return stack

    def test_ensure_workbench_frame_loaded_updates_bound_workbench_frame(self) -> None:
        session_state = _SessionState(
            video_loaded=True,
            asset_id="asset-1",
            video_frame_count=12,
            playback_frame_index=5,
            playback_timestamp_seconds=0.0,
            workbench_frame_index=5,
            workbench_timestamp_seconds=0.0,
            workbench_frame_image_bytes=None,
            workbench_frame_image_mime_type=None,
            workbench_frame_width=0,
            workbench_frame_height=0,
            workbench_frame_request_key=None,
            workbench_frame_error_message=None,
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

        with self._patch_state_modules(session_state), patch.object(
            ui_state.workbench_state,
            "get_video_asset_backend",
            return_value=fake_backend,
        ):
            ui_state.ensure_workbench_frame_loaded()

        self.assertEqual(session_state.workbench_frame_index, 5)
        self.assertAlmostEqual(session_state.workbench_timestamp_seconds, 0.5)
        self.assertEqual(session_state.workbench_frame_image_bytes, b"frame-bytes")
        self.assertEqual(session_state.workbench_frame_image_mime_type, "image/png")
        self.assertEqual(session_state.workbench_frame_width, 1280)
        self.assertEqual(session_state.workbench_frame_height, 720)
        self.assertIsNone(session_state.workbench_frame_error_message)

    def test_ensure_workbench_frame_loaded_stops_playback_on_frame_error(self) -> None:
        session_state = _SessionState(
            video_loaded=True,
            asset_id="asset-1",
            video_frame_count=12,
            playback_frame_index=5,
            playback_timestamp_seconds=0.5,
            workbench_frame_index=5,
            workbench_timestamp_seconds=0.5,
            workbench_frame_image_bytes=b"stale",
            workbench_frame_image_mime_type="image/png",
            workbench_frame_width=1280,
            workbench_frame_height=720,
            workbench_frame_request_key=None,
            workbench_frame_error_message=None,
            playback_running=True,
            playback_anchor_frame_index=5,
            playback_started_at_seconds=10.0,
        )
        fake_backend = types.SimpleNamespace(
            get_video_frame=types.SimpleNamespace(
                execute=Mock(side_effect=VideoFrameExtractionError("frame decode failed"))
            )
        )

        with self._patch_state_modules(session_state), patch.object(
            ui_state.workbench_state,
            "get_video_asset_backend",
            return_value=fake_backend,
        ):
            ui_state.ensure_workbench_frame_loaded()

        self.assertFalse(session_state.playback_running)
        self.assertIsNone(session_state.workbench_frame_image_bytes)
        self.assertIsNone(session_state.workbench_frame_image_mime_type)
        self.assertEqual(session_state.workbench_frame_error_message, "frame decode failed")
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
            playback_frame_index=12,
            playback_timestamp_seconds=0.5,
            workbench_frame_index=12,
            workbench_timestamp_seconds=0.5,
            workbench_frame_image_bytes=b"frame-bytes",
            workbench_frame_image_mime_type="image/png",
            workbench_frame_width=640,
            workbench_frame_height=360,
            workbench_frame_request_key=("asset-1", 12),
            workbench_frame_error_message=None,
            playback_running=False,
            playback_anchor_frame_index=None,
            playback_started_at_seconds=None,
            prompt_entries=[],
            last_action="Seeded state",
        )
        metadata_execute = Mock(return_value=metadata)
        fake_backend = types.SimpleNamespace(
            get_video_asset_metadata=types.SimpleNamespace(execute=metadata_execute)
        )

        with self._patch_state_modules(session_state), patch.object(
            ui_state.source_state,
            "get_video_asset_backend",
            return_value=fake_backend,
        ):
            changed = ui_state.register_video_selection(uploaded_file)

        self.assertFalse(changed)
        self.assertEqual(session_state.playback_frame_index, 12)
        self.assertAlmostEqual(session_state.playback_timestamp_seconds, 0.5)
        self.assertEqual(session_state.workbench_frame_image_bytes, b"frame-bytes")
        self.assertEqual(session_state.workbench_frame_request_key, ("asset-1", 12))
        self.assertFalse(session_state.playback_running)
        metadata_execute.assert_not_called()

    def test_register_video_selection_ignores_empty_uploader_when_source_is_active(self) -> None:
        session_state = _SessionState(
            video_loaded=True,
            video_name="clip.mp4",
            video_mime_type="video/mp4",
            source_video_bytes=b"same-video",
            video_upload_signature="fingerprint-1",
            source_fingerprint="fingerprint-1",
            asset_id="asset-1",
            active_asset_id="asset-1",
            active_video_name="clip.mp4",
            active_source_payload=b"same-video",
            video_fps=24.0,
            video_frame_count=120,
            video_duration_seconds=5.0,
            video_width=640,
            video_height=360,
            playback_frame_index=12,
            playback_timestamp_seconds=0.5,
            workbench_frame_index=12,
            workbench_timestamp_seconds=0.5,
            workbench_frame_image_bytes=b"frame-bytes",
            workbench_frame_image_mime_type="image/png",
            workbench_frame_width=640,
            workbench_frame_height=360,
            workbench_frame_request_key=("asset-1", 12),
            workbench_frame_error_message=None,
            playback_running=True,
            playback_anchor_frame_index=10,
            playback_started_at_seconds=123.0,
            ui_generation=4,
            playback_generation=9,
            prompt_entries=[],
            last_action="Seeded state",
        )
        fake_backend = types.SimpleNamespace(
            register_video_asset=types.SimpleNamespace(execute=Mock()),
            get_video_asset_metadata=types.SimpleNamespace(execute=Mock()),
        )

        with self._patch_state_modules(session_state), patch.object(
            ui_state.source_state,
            "get_video_asset_backend",
            return_value=fake_backend,
        ):
            changed = ui_state.register_video_selection(None)

        self.assertFalse(changed)
        self.assertTrue(session_state.video_loaded)
        self.assertEqual(session_state.asset_id, "asset-1")
        self.assertEqual(session_state.active_asset_id, "asset-1")
        self.assertTrue(session_state.playback_running)
        self.assertEqual(session_state.ui_generation, 4)
        self.assertEqual(session_state.playback_generation, 9)
        fake_backend.register_video_asset.execute.assert_not_called()
        fake_backend.get_video_asset_metadata.execute.assert_not_called()

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
            playback_frame_index=12,
            playback_timestamp_seconds=0.5,
            workbench_frame_index=12,
            workbench_timestamp_seconds=0.5,
            workbench_frame_image_bytes=b"frame-bytes",
            workbench_frame_image_mime_type="image/png",
            workbench_frame_width=640,
            workbench_frame_height=360,
            workbench_frame_request_key=("asset-1", 12),
            workbench_frame_error_message=None,
            playback_running=True,
            playback_anchor_frame_index=10,
            playback_started_at_seconds=123.0,
            prompt_entries=[],
            last_action="Seeded state",
        )
        metadata_execute = Mock(return_value=metadata)
        fake_backend = types.SimpleNamespace(
            get_video_asset_metadata=types.SimpleNamespace(execute=metadata_execute)
        )

        with self._patch_state_modules(session_state), patch.object(
            ui_state.source_state,
            "get_video_asset_backend",
            return_value=fake_backend,
        ):
            changed = ui_state.register_video_selection(uploaded_file)

        self.assertFalse(changed)
        self.assertTrue(session_state.playback_running)
        self.assertEqual(session_state.playback_anchor_frame_index, 10)
        self.assertEqual(session_state.playback_started_at_seconds, 123.0)
        self.assertEqual(session_state.workbench_frame_request_key, ("asset-1", 12))
        metadata_execute.assert_not_called()

    def test_register_video_selection_refreshes_metadata_for_same_upload_when_cached_state_is_incomplete(self) -> None:
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
            video_fps=0.0,
            video_frame_count=0,
            video_duration_seconds=0.0,
            video_width=0,
            video_height=0,
            playback_frame_index=12,
            playback_timestamp_seconds=0.5,
            workbench_frame_index=12,
            workbench_timestamp_seconds=0.5,
            workbench_frame_image_bytes=b"frame-bytes",
            workbench_frame_image_mime_type="image/png",
            workbench_frame_width=0,
            workbench_frame_height=0,
            workbench_frame_request_key=("asset-1", 12),
            workbench_frame_error_message=None,
            playback_running=False,
            playback_anchor_frame_index=None,
            playback_started_at_seconds=None,
            prompt_entries=[],
            last_action="Seeded state",
        )
        metadata_execute = Mock(return_value=metadata)
        fake_backend = types.SimpleNamespace(
            get_video_asset_metadata=types.SimpleNamespace(execute=metadata_execute)
        )

        with self._patch_state_modules(session_state), patch.object(
            ui_state.source_state,
            "get_video_asset_backend",
            return_value=fake_backend,
        ):
            changed = ui_state.register_video_selection(uploaded_file)

        self.assertFalse(changed)
        metadata_execute.assert_called_once_with("asset-1")
        self.assertEqual(session_state.video_fps, 24.0)
        self.assertEqual(session_state.video_frame_count, 120)
        self.assertEqual(session_state.video_width, 640)
        self.assertEqual(session_state.video_height, 360)

    def test_remove_active_video_source_clears_source_and_bumps_generations(self) -> None:
        session_state = _SessionState(
            video_loaded=True,
            video_name="clip.mp4",
            video_mime_type="video/mp4",
            source_video_bytes=b"same-video",
            video_upload_signature="fingerprint-1",
            source_fingerprint="fingerprint-1",
            asset_id="asset-1",
            active_asset_id="asset-1",
            active_video_name="clip.mp4",
            active_source_payload=b"same-video",
            video_fps=24.0,
            video_frame_count=120,
            video_duration_seconds=5.0,
            video_width=640,
            video_height=360,
            playback_frame_index=12,
            playback_timestamp_seconds=0.5,
            workbench_frame_index=12,
            workbench_timestamp_seconds=0.5,
            workbench_frame_image_bytes=b"frame-bytes",
            workbench_frame_image_mime_type="image/png",
            workbench_frame_width=640,
            workbench_frame_height=360,
            workbench_frame_request_key=("asset-1", 12),
            workbench_frame_error_message=None,
            playback_running=True,
            playback_anchor_frame_index=10,
            playback_started_at_seconds=123.0,
            ui_generation=4,
            playback_generation=9,
            prompt_entries=[],
            last_action="Seeded state",
        )

        with self._patch_state_modules(session_state):
            changed = ui_state.remove_active_video_source()

        self.assertTrue(changed)
        self.assertFalse(session_state.video_loaded)
        self.assertIsNone(session_state.asset_id)
        self.assertIsNone(session_state.active_asset_id)
        self.assertIsNone(session_state.source_fingerprint)
        self.assertFalse(session_state.playback_running)
        self.assertEqual(session_state.ui_generation, 5)
        self.assertEqual(session_state.playback_generation, 10)
        self.assertEqual(session_state.last_action, "Removed source asset")

    def test_sync_playback_position_advances_preview_without_moving_workbench_frame(self) -> None:
        session_state = _SessionState(
            video_loaded=True,
            asset_id="asset-1",
            active_asset_id="asset-1",
            video_fps=24.0,
            video_frame_count=120,
            playback_frame_index=4,
            playback_timestamp_seconds=4 / 24.0,
            workbench_frame_index=2,
            workbench_timestamp_seconds=2 / 24.0,
            workbench_frame_request_key=("asset-1", 2),
            playback_running=True,
            playback_anchor_frame_index=4,
            playback_started_at_seconds=100.0,
            workbench_frame_error_message=None,
            playback_generation=3,
            last_action="Seeded state",
        )

        with self._patch_state_modules(session_state):
            ui_state.sync_playback_position(now_seconds=100.5)

        self.assertGreater(session_state.playback_frame_index, 4)
        self.assertGreater(session_state.playback_timestamp_seconds, 4 / 24.0)
        self.assertEqual(session_state.workbench_frame_index, 2)
        self.assertAlmostEqual(session_state.workbench_timestamp_seconds, 2 / 24.0)
        self.assertEqual(session_state.workbench_frame_request_key, ("asset-1", 2))

    def test_toggle_playback_adopts_preview_frame_into_workbench_when_stopping(self) -> None:
        session_state = _SessionState(
            video_loaded=True,
            asset_id="asset-1",
            active_asset_id="asset-1",
            video_fps=24.0,
            video_frame_count=120,
            playback_frame_index=6,
            playback_timestamp_seconds=6 / 24.0,
            workbench_frame_index=2,
            workbench_timestamp_seconds=2 / 24.0,
            workbench_frame_request_key=("asset-1", 2),
            playback_running=True,
            playback_anchor_frame_index=6,
            playback_started_at_seconds=100.0,
            workbench_frame_error_message=None,
            playback_generation=3,
            last_action="Seeded state",
        )

        with self._patch_state_modules(session_state):
            ui_state.toggle_playback()

        self.assertFalse(session_state.playback_running)
        self.assertEqual(session_state.workbench_frame_index, session_state.playback_frame_index)
        self.assertAlmostEqual(session_state.workbench_timestamp_seconds, session_state.playback_timestamp_seconds)
        self.assertIsNone(session_state.workbench_frame_request_key)
        self.assertIn("Playback paused", session_state.last_action)


if __name__ == "__main__":
    unittest.main()
