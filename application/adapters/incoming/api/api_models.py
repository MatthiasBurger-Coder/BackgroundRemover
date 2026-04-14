"""Pydantic models for the browser-facing video workspace API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AssetMetadataResponse(BaseModel):
    """Serializable metadata for the active source asset."""

    asset_id: str = Field(alias="assetId")
    filename: str
    fps: float
    frame_count: int = Field(alias="frameCount")
    duration_seconds: float = Field(alias="durationSeconds")
    width: int
    height: int

    model_config = ConfigDict(populate_by_name=True)


class PlaybackStateResponse(BaseModel):
    """Initial playback state delivered to the browser client."""

    playback_running: bool = Field(alias="playbackRunning")
    playback_frame_index: int = Field(alias="playbackFrameIndex")
    playback_timestamp_seconds: float = Field(alias="playbackTimestampSeconds")
    playback_fps: float = Field(alias="playbackFps")
    preview_status: str = Field(alias="previewStatus")

    model_config = ConfigDict(populate_by_name=True)


class PromptEntryResponse(BaseModel):
    """Serializable prompt entry for the fixed workbench snapshot."""

    identifier: int
    mode: str
    frame_index: int = Field(alias="frameIndex")
    x: int
    y: int
    source: str

    model_config = ConfigDict(populate_by_name=True)


class OverlayStateResponse(BaseModel):
    """Serializable overlay state for the fixed workbench snapshot."""

    show_debug_overlay: bool = Field(alias="showDebugOverlay")

    model_config = ConfigDict(populate_by_name=True)


class MaskSettingsResponse(BaseModel):
    """Serializable mask settings for the workbench editor."""

    threshold: float
    feather: int
    invert: bool


class RenderedImageResponse(BaseModel):
    """Serializable preview artifact transported as a browser-ready data URL."""

    mime_type: str = Field(alias="mimeType")
    width: int
    height: int
    image_data_url: str = Field(alias="imageDataUrl")

    model_config = ConfigDict(populate_by_name=True)


class MaskPreviewResponse(BaseModel):
    """Serializable result for a generated workbench mask preview."""

    mode: str
    frame_index: int = Field(alias="frameIndex")
    source_width: int = Field(alias="sourceWidth")
    source_height: int = Field(alias="sourceHeight")
    preview_width: int = Field(alias="previewWidth")
    preview_height: int = Field(alias="previewHeight")
    prompt_count: int = Field(alias="promptCount")
    coverage_ratio: float = Field(alias="coverageRatio")
    overlay_image: RenderedImageResponse = Field(alias="overlayImage")
    mask_image: RenderedImageResponse = Field(alias="maskImage")

    model_config = ConfigDict(populate_by_name=True)


class WorkbenchStateResponse(BaseModel):
    """Serializable workbench state used by the browser editor."""

    workbench_frame_index: int = Field(alias="workbenchFrameIndex")
    workbench_timestamp_seconds: float = Field(alias="workbenchTimestampSeconds")
    workbench_frame_request_key: str = Field(alias="workbenchFrameRequestKey")
    preview_refresh_generation: int = Field(alias="previewRefreshGeneration")
    prompt_entries: list[PromptEntryResponse] = Field(alias="promptEntries")
    overlay_state: OverlayStateResponse = Field(alias="overlayState")
    selected_mask_settings: MaskSettingsResponse = Field(alias="selectedMaskSettings")
    mask_preview: MaskPreviewResponse | None = Field(alias="maskPreview")
    workbench_status: str = Field(alias="workbenchStatus")

    model_config = ConfigDict(populate_by_name=True)


class VideoFrameResponse(BaseModel):
    """Serializable frame payload for the workbench snapshot."""

    asset_id: str = Field(alias="assetId")
    frame_index: int = Field(alias="frameIndex")
    timestamp_seconds: float = Field(alias="timestampSeconds")
    mime_type: str = Field(alias="mimeType")
    width: int
    height: int
    image_data_url: str = Field(alias="imageDataUrl")

    model_config = ConfigDict(populate_by_name=True)


class WorkbenchSnapshotResponse(BaseModel):
    """Combined workbench state and decoded frame snapshot."""

    state: WorkbenchStateResponse
    frame: VideoFrameResponse


class AssetRegistrationResponse(BaseModel):
    """Bootstrap payload returned after registering a new source asset."""

    asset: AssetMetadataResponse
    playback: PlaybackStateResponse
    workbench: WorkbenchSnapshotResponse


class SyncWorkbenchFrameRequest(BaseModel):
    """Request body for binding the workbench to a specific frame."""

    frame_index: int = Field(alias="frameIndex")

    model_config = ConfigDict(populate_by_name=True)


class CreatePromptRequest(BaseModel):
    """Request body for adding a prompt entry to the workbench."""

    mode: str
    x: int
    y: int
    source: str = "Operator input"


class UpdateWorkbenchSettingsRequest(BaseModel):
    """Request body for updating mask and overlay settings."""

    threshold: float
    feather: int
    invert: bool
    show_debug_overlay: bool = Field(alias="showDebugOverlay")

    model_config = ConfigDict(populate_by_name=True)
