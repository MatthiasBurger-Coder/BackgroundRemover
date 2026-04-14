"""Regression tests for the first prompt-guided workbench mask preview slice."""

from __future__ import annotations

import unittest

from application.adapters.outgoing.rendering.svg_mask_preview_renderer_adapter import (
    SvgMaskPreviewRendererAdapter,
)
from application.adapters.outgoing.segmentation.box_blur_mask_refiner_adapter import (
    BoxBlurMaskRefinerAdapter,
)
from application.adapters.outgoing.segmentation.prompt_guided_person_segmenter_adapter import (
    PromptGuidedPersonSegmenterAdapter,
)
from application.adapters.outgoing.storage.in_memory_workbench_session_adapter import (
    InMemoryWorkbenchSessionAdapter,
)
from application.application.policies.workbench_processing_profile_policy import (
    WorkbenchProcessingProfilePolicy,
)
from application.application.use_cases.workbench_session_use_cases import (
    GetWorkbenchSessionUseCase,
    RefreshWorkbenchPreviewUseCase,
    SyncWorkbenchFrameUseCase,
    UpdateWorkbenchSettingsUseCase,
)
from application.domain.model.mask_preview import ProcessingMode
from application.domain.model.video_asset import VideoAssetContent, VideoAssetMetadata, VideoFrame
from application.domain.model.workbench_session import PromptEntry, WorkbenchSession


class _StubVideoAssetPort:
    def __init__(self) -> None:
        self._metadata = VideoAssetMetadata(
            asset_id="asset-1",
            filename="preview-test.mp4",
            fps=24.0,
            frame_count=12,
            duration_seconds=0.5,
            width=1280,
            height=720,
        )
        self._frame = VideoFrame(
            asset_id="asset-1",
            frame_index=0,
            timestamp_seconds=0.0,
            mime_type="image/png",
            width=1280,
            height=720,
            image_bytes=b"frame-bytes",
        )

    def register_video_asset(
        self,
        *,
        filename: str,
        video_bytes: bytes,
        mime_type: str | None,
    ) -> VideoAssetMetadata:
        raise NotImplementedError

    def get_video_metadata(self, asset_id: str) -> VideoAssetMetadata:
        self._assert_asset(asset_id)
        return self._metadata

    def get_video_frame(self, asset_id: str, frame_index: int) -> VideoFrame:
        self._assert_asset(asset_id)
        return VideoFrame(
            asset_id=self._frame.asset_id,
            frame_index=frame_index,
            timestamp_seconds=frame_index / self._metadata.fps,
            mime_type=self._frame.mime_type,
            width=self._frame.width,
            height=self._frame.height,
            image_bytes=self._frame.image_bytes,
        )

    def get_video_content(self, asset_id: str) -> VideoAssetContent:
        self._assert_asset(asset_id)
        return VideoAssetContent(
            asset_id=asset_id,
            filename=self._metadata.filename,
            mime_type="video/mp4",
            video_bytes=b"",
        )

    def delete_video_asset(self, asset_id: str) -> None:
        self._assert_asset(asset_id)

    def _assert_asset(self, asset_id: str) -> None:
        if asset_id != self._metadata.asset_id:
            raise AssertionError(f"Unexpected asset_id {asset_id}")


class WorkbenchMaskPreviewUseCaseTests(unittest.TestCase):
    """Protect the deterministic preview generation and invalidation flow."""

    def setUp(self) -> None:
        self.video_asset_port = _StubVideoAssetPort()
        self.workbench_session_port = InMemoryWorkbenchSessionAdapter()
        self.get_workbench_session = GetWorkbenchSessionUseCase(
            self.workbench_session_port,
            self.video_asset_port,
        )
        self.refresh_preview = RefreshWorkbenchPreviewUseCase(
            self.workbench_session_port,
            self.video_asset_port,
            self.get_workbench_session,
            PromptGuidedPersonSegmenterAdapter(),
            BoxBlurMaskRefinerAdapter(),
            SvgMaskPreviewRendererAdapter(),
            WorkbenchProcessingProfilePolicy(preview_max_dimension=192),
        )

    def test_refresh_preview_generates_svg_overlay_and_binary_mask(self) -> None:
        session = WorkbenchSession(
            asset_id="asset-1",
            prompt_entries=(
                PromptEntry(
                    identifier=1,
                    mode="foreground",
                    frame_index=0,
                    x=640,
                    y=280,
                    source="test",
                ),
            ),
        )
        self.workbench_session_port.save_workbench_session(session)

        refreshed_session = self.refresh_preview.execute("asset-1")

        self.assertEqual(refreshed_session.preview_refresh_generation, 1)
        self.assertIsNotNone(refreshed_session.mask_preview_result)
        assert refreshed_session.mask_preview_result is not None
        self.assertEqual(refreshed_session.mask_preview_result.mode, ProcessingMode.PREVIEW)
        self.assertEqual(refreshed_session.mask_preview_result.prompt_count, 1)
        self.assertGreater(refreshed_session.mask_preview_result.coverage_ratio, 0.0)
        self.assertLessEqual(refreshed_session.mask_preview_result.preview_size.width, 192)
        self.assertEqual(refreshed_session.mask_preview_result.overlay_image.mime_type, "image/svg+xml")
        self.assertIn(b"<svg", refreshed_session.mask_preview_result.overlay_image.image_bytes)
        self.assertIn(b"<svg", refreshed_session.mask_preview_result.mask_image.image_bytes)

    def test_preview_is_cleared_when_frame_or_settings_change(self) -> None:
        session = WorkbenchSession(
            asset_id="asset-1",
            prompt_entries=(
                PromptEntry(
                    identifier=1,
                    mode="foreground",
                    frame_index=0,
                    x=640,
                    y=280,
                    source="test",
                ),
            ),
        )
        self.workbench_session_port.save_workbench_session(session)
        refreshed_session = self.refresh_preview.execute("asset-1")
        self.assertIsNotNone(refreshed_session.mask_preview_result)

        sync_workbench_frame = SyncWorkbenchFrameUseCase(
            self.workbench_session_port,
            self.video_asset_port,
            self.get_workbench_session,
        )
        synced_session = sync_workbench_frame.execute(asset_id="asset-1", frame_index=3)
        self.assertIsNone(synced_session.mask_preview_result)

        self.workbench_session_port.save_workbench_session(refreshed_session)
        update_settings = UpdateWorkbenchSettingsUseCase(
            self.workbench_session_port,
            self.get_workbench_session,
        )
        updated_session = update_settings.execute(
            asset_id="asset-1",
            threshold=0.55,
            feather=14,
            invert=True,
            show_debug_overlay=False,
        )
        self.assertIsNone(updated_session.mask_preview_result)


if __name__ == "__main__":
    unittest.main()
