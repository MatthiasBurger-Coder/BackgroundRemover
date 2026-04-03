"""Application wiring for the first backend-managed video transport slice."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

from src.application.adapters.outgoing.video.ffmpeg_video_asset_adapter import (
    FfmpegVideoAssetAdapter,
)
from src.application.application.use_cases.video_asset_use_cases import (
    GetVideoAssetMetadataUseCase,
    GetVideoFrameUseCase,
    RegisterVideoAssetUseCase,
)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class VideoAssetBackend:
    """Small wiring container for the video asset use cases used by the UI."""

    register_video_asset: RegisterVideoAssetUseCase
    get_video_asset_metadata: GetVideoAssetMetadataUseCase
    get_video_frame: GetVideoFrameUseCase


@lru_cache(maxsize=1)
def get_video_asset_backend() -> VideoAssetBackend:
    LOGGER.info("Creating cached video asset backend wiring")
    adapter = FfmpegVideoAssetAdapter()
    return VideoAssetBackend(
        register_video_asset=RegisterVideoAssetUseCase(adapter),
        get_video_asset_metadata=GetVideoAssetMetadataUseCase(adapter),
        get_video_frame=GetVideoFrameUseCase(adapter),
    )
