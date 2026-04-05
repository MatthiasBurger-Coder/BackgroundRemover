"""Use cases for the first backend-backed video asset workflow slice."""

from __future__ import annotations

from dataclasses import dataclass

from application.domain.model.video_asset import VideoAssetMetadata, VideoFrame
from application.ports.outgoing.video_asset_port import VideoAssetPort


@dataclass(frozen=True)
class RegisterVideoAssetUseCase:
    """Register an uploaded video as a backend-managed temporary asset."""

    video_asset_port: VideoAssetPort

    def execute(self, *, filename: str, video_bytes: bytes, mime_type: str | None) -> VideoAssetMetadata:
        return self.video_asset_port.register_video_asset(
            filename=filename,
            video_bytes=video_bytes,
            mime_type=mime_type,
        )


@dataclass(frozen=True)
class GetVideoAssetMetadataUseCase:
    """Load metadata for an existing backend-managed video asset."""

    video_asset_port: VideoAssetPort

    def execute(self, asset_id: str) -> VideoAssetMetadata:
        return self.video_asset_port.get_video_metadata(asset_id)


@dataclass(frozen=True)
class GetVideoFrameUseCase:
    """Load a single decoded frame by asset identifier and frame index."""

    video_asset_port: VideoAssetPort

    def execute(self, *, asset_id: str, frame_index: int) -> VideoFrame:
        return self.video_asset_port.get_video_frame(asset_id, frame_index)
