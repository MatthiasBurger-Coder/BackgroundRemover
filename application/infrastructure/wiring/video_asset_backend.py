"""Application wiring for the first backend-managed video transport slice."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

from application.adapters.outgoing.video.ffmpeg_video_asset_adapter import (
    FfmpegVideoAssetAdapter,
)
from application.application.use_cases.video_asset_use_cases import (
    DeleteVideoAssetUseCase,
    GetVideoAssetMetadataUseCase,
    GetVideoContentUseCase,
    GetVideoFrameUseCase,
    RegisterVideoAssetUseCase,
)
from application.ports.outgoing.video_asset_port import VideoAssetPort

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class VideoAssetBackend:
    """Small wiring container for the video asset use cases used by the UI."""

    video_asset_port: VideoAssetPort
    register_video_asset: RegisterVideoAssetUseCase
    get_video_asset_metadata: GetVideoAssetMetadataUseCase
    get_video_frame: GetVideoFrameUseCase
    get_video_content: GetVideoContentUseCase
    delete_video_asset: DeleteVideoAssetUseCase


@lru_cache(maxsize=1)
def get_video_asset_backend() -> VideoAssetBackend:
    LOGGER.info("Creating cached video asset backend wiring")
    adapter = FfmpegVideoAssetAdapter()
    return VideoAssetBackend(
        video_asset_port=adapter,
        register_video_asset=RegisterVideoAssetUseCase(adapter),
        get_video_asset_metadata=GetVideoAssetMetadataUseCase(adapter),
        get_video_frame=GetVideoFrameUseCase(adapter),
        get_video_content=GetVideoContentUseCase(adapter),
        delete_video_asset=DeleteVideoAssetUseCase(adapter),
    )
