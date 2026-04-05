"""Outgoing port for backend-managed video assets."""

from __future__ import annotations

from typing import Protocol

from application.domain.model.video_asset import VideoAssetContent, VideoAssetMetadata, VideoFrame


class VideoAssetPort(Protocol):
    """Port for registering source videos and retrieving frame data."""

    def register_video_asset(
        self,
        *,
        filename: str,
        video_bytes: bytes,
        mime_type: str | None,
    ) -> VideoAssetMetadata:
        """Store an uploaded video as a temporary backend-managed asset."""

    def get_video_metadata(self, asset_id: str) -> VideoAssetMetadata:
        """Return metadata for a previously registered asset."""

    def get_video_frame(self, asset_id: str, frame_index: int) -> VideoFrame:
        """Decode and return a single frame by index."""

    def get_video_content(self, asset_id: str) -> VideoAssetContent:
        """Return the original stored video bytes for browser playback."""

    def delete_video_asset(self, asset_id: str) -> None:
        """Remove a previously registered asset and its stored file."""
