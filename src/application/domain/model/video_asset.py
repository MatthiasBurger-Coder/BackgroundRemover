"""Domain models for the first backend-managed video asset workflow slice."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VideoAssetMetadata:
    """Backend metadata required for source transport and frame navigation."""

    asset_id: str
    filename: str
    fps: float
    frame_count: int
    duration_seconds: float
    width: int
    height: int

    def clamped_frame_index(self, frame_index: int) -> int:
        """Clamp a requested frame index into the available frame range."""
        if self.frame_count <= 0:
            return 0
        return max(0, min(frame_index, self.frame_count - 1))


@dataclass(frozen=True)
class VideoFrame:
    """A decoded frame payload returned by the backend for workbench display."""

    asset_id: str
    frame_index: int
    timestamp_seconds: float
    mime_type: str
    width: int
    height: int
    image_bytes: bytes
