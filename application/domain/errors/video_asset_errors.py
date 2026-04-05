"""Domain errors for video asset handling."""

from __future__ import annotations


class VideoAssetError(RuntimeError):
    """Base error for backend video asset failures."""


class VideoAssetNotFoundError(VideoAssetError):
    """Raised when a requested asset identifier is unknown."""


class VideoProbeError(VideoAssetError):
    """Raised when metadata extraction fails for an uploaded video."""


class VideoFrameExtractionError(VideoAssetError):
    """Raised when frame extraction fails for a requested frame."""
