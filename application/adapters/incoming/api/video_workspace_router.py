"""FastAPI router for the browser-based video workspace."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Protocol

from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status

from application.adapters.incoming.api.api_models import (
    AssetMetadataResponse,
    AssetRegistrationResponse,
    CreatePromptRequest,
    MaskSettingsResponse,
    OverlayStateResponse,
    PlaybackStateResponse,
    PromptEntryResponse,
    SyncWorkbenchFrameRequest,
    UpdateWorkbenchSettingsRequest,
    VideoFrameResponse,
    WorkbenchSnapshotResponse,
    WorkbenchStateResponse,
)
from application.domain.errors.video_asset_errors import (
    VideoAssetNotFoundError,
    VideoFrameExtractionError,
    VideoProbeError,
)
from application.domain.model.video_asset import VideoAssetContent, VideoAssetMetadata, VideoFrame
from application.domain.model.workbench_session import WorkbenchSession


class _GetVideoAssetMetadataExecutable(Protocol):
    def execute(self, asset_id: str) -> VideoAssetMetadata: ...


class _GetVideoContentExecutable(Protocol):
    def execute(self, asset_id: str) -> VideoAssetContent: ...


class _GetWorkbenchSessionExecutable(Protocol):
    def execute(self, asset_id: str) -> WorkbenchSession: ...


class _GetVideoFrameExecutable(Protocol):
    def execute(self, *, asset_id: str, frame_index: int) -> VideoFrame: ...


class _SyncWorkbenchFrameExecutable(Protocol):
    def execute(self, *, asset_id: str, frame_index: int) -> WorkbenchSession: ...


class _ExecutablePrompt(Protocol):
    def execute(self, *, asset_id: str, mode: str, x: int, y: int, source: str) -> WorkbenchSession: ...


class _ExecutableSettings(Protocol):
    def execute(
        self,
        *,
        asset_id: str,
        threshold: float,
        feather: int,
        invert: bool,
        show_debug_overlay: bool,
    ) -> WorkbenchSession: ...


class _ExecutableRegister(Protocol):
    def execute(self, *, filename: str, video_bytes: bytes, mime_type: str | None) -> VideoAssetMetadata: ...


class _ExecutableDelete(Protocol):
    def execute(self, asset_id: str) -> None: ...


@dataclass(frozen=True)
class VideoWorkspaceApiDependencies:
    """Dependency bundle consumed by the API router without reaching into infrastructure."""

    register_video_asset: _ExecutableRegister
    get_video_asset_metadata: _GetVideoAssetMetadataExecutable
    get_video_frame: _GetVideoFrameExecutable
    get_video_content: _GetVideoContentExecutable
    delete_video_asset: _ExecutableDelete
    get_workbench_session: _GetWorkbenchSessionExecutable
    sync_workbench_frame: _SyncWorkbenchFrameExecutable
    add_prompt: _ExecutablePrompt
    clear_prompts: _GetWorkbenchSessionExecutable
    update_settings: _ExecutableSettings
    refresh_preview: _GetWorkbenchSessionExecutable
    delete_workbench_session: _ExecutableDelete


UPLOAD_FILE = File(...)


def create_video_workspace_router(
    *,
    dependencies: VideoWorkspaceApiDependencies,
) -> APIRouter:
    """Build the browser-facing API router from already wired use cases."""

    router = APIRouter(prefix="/api", tags=["video-workspace"])

    @router.get("/health")
    def get_health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post(
        "/assets",
        response_model=AssetRegistrationResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def register_asset(file: UploadFile = UPLOAD_FILE) -> AssetRegistrationResponse:
        try:
            payload = await file.read()
            metadata = dependencies.register_video_asset.execute(
                filename=file.filename or "uploaded-video.mp4",
                video_bytes=payload,
                mime_type=file.content_type,
            )
            workbench_session = dependencies.get_workbench_session.execute(metadata.asset_id)
            frame = dependencies.get_video_frame.execute(asset_id=metadata.asset_id, frame_index=0)
        except VideoProbeError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error

        return AssetRegistrationResponse(
            asset=_build_asset_metadata_response(metadata),
            playback=_build_playback_state_response(metadata),
            workbench=_build_workbench_snapshot_response(workbench_session, frame),
        )

    @router.get("/assets/{asset_id}", response_model=AssetMetadataResponse)
    def get_asset_metadata(asset_id: str) -> AssetMetadataResponse:
        try:
            metadata = dependencies.get_video_asset_metadata.execute(asset_id)
        except VideoAssetNotFoundError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        return _build_asset_metadata_response(metadata)

    @router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_asset(asset_id: str) -> Response:
        try:
            dependencies.delete_workbench_session.execute(asset_id)
            dependencies.delete_video_asset.execute(asset_id)
        except VideoAssetNotFoundError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.get("/assets/{asset_id}/source")
    def get_asset_source(asset_id: str) -> Response:
        try:
            content = dependencies.get_video_content.execute(asset_id)
        except VideoAssetNotFoundError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        return Response(
            content=content.video_bytes,
            media_type=content.mime_type,
            headers={
                "Content-Disposition": f'inline; filename="{content.filename}"',
                "Cache-Control": "no-store",
            },
        )

    @router.get("/assets/{asset_id}/frames/{frame_index}", response_model=VideoFrameResponse)
    def get_frame(asset_id: str, frame_index: int) -> VideoFrameResponse:
        try:
            frame = dependencies.get_video_frame.execute(asset_id=asset_id, frame_index=frame_index)
        except VideoAssetNotFoundError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        except VideoFrameExtractionError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
        return _build_frame_response(frame)

    @router.get("/assets/{asset_id}/workbench", response_model=WorkbenchSnapshotResponse)
    def get_workbench_snapshot(asset_id: str) -> WorkbenchSnapshotResponse:
        try:
            session = dependencies.get_workbench_session.execute(asset_id)
            frame = dependencies.get_video_frame.execute(
                asset_id=asset_id,
                frame_index=session.workbench_frame_index,
            )
        except VideoAssetNotFoundError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        except VideoFrameExtractionError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
        return _build_workbench_snapshot_response(session, frame)

    @router.put("/assets/{asset_id}/workbench/frame", response_model=WorkbenchSnapshotResponse)
    def sync_workbench_frame(
        asset_id: str,
        request: SyncWorkbenchFrameRequest,
    ) -> WorkbenchSnapshotResponse:
        try:
            session = dependencies.sync_workbench_frame.execute(
                asset_id=asset_id,
                frame_index=request.frame_index,
            )
            frame = dependencies.get_video_frame.execute(
                asset_id=asset_id,
                frame_index=session.workbench_frame_index,
            )
        except VideoAssetNotFoundError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        except VideoFrameExtractionError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
        return _build_workbench_snapshot_response(session, frame)

    @router.post("/assets/{asset_id}/workbench/prompts", response_model=WorkbenchStateResponse)
    def add_prompt(asset_id: str, request: CreatePromptRequest) -> WorkbenchStateResponse:
        try:
            session = dependencies.add_prompt.execute(
                asset_id=asset_id,
                mode=request.mode,
                x=request.x,
                y=request.y,
                source=request.source,
            )
        except VideoAssetNotFoundError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        return _build_workbench_state_response(session)

    @router.delete("/assets/{asset_id}/workbench/prompts", response_model=WorkbenchStateResponse)
    def clear_prompts(asset_id: str) -> WorkbenchStateResponse:
        try:
            session = dependencies.clear_prompts.execute(asset_id)
        except VideoAssetNotFoundError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        return _build_workbench_state_response(session)

    @router.put("/assets/{asset_id}/workbench/settings", response_model=WorkbenchStateResponse)
    def update_workbench_settings(
        asset_id: str,
        request: UpdateWorkbenchSettingsRequest,
    ) -> WorkbenchStateResponse:
        try:
            session = dependencies.update_settings.execute(
                asset_id=asset_id,
                threshold=request.threshold,
                feather=request.feather,
                invert=request.invert,
                show_debug_overlay=request.show_debug_overlay,
            )
        except VideoAssetNotFoundError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        return _build_workbench_state_response(session)

    @router.post("/assets/{asset_id}/workbench/preview-refresh", response_model=WorkbenchStateResponse)
    def refresh_preview(asset_id: str) -> WorkbenchStateResponse:
        try:
            session = dependencies.refresh_preview.execute(asset_id)
        except VideoAssetNotFoundError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        return _build_workbench_state_response(session)

    return router


def _build_asset_metadata_response(metadata: VideoAssetMetadata) -> AssetMetadataResponse:
    return AssetMetadataResponse(
        assetId=metadata.asset_id,
        filename=metadata.filename,
        fps=metadata.fps,
        frameCount=metadata.frame_count,
        durationSeconds=metadata.duration_seconds,
        width=metadata.width,
        height=metadata.height,
    )


def _build_playback_state_response(metadata: VideoAssetMetadata) -> PlaybackStateResponse:
    return PlaybackStateResponse(
        playbackRunning=False,
        playbackFrameIndex=0,
        playbackTimestampSeconds=0.0,
        playbackFps=metadata.fps,
        previewStatus="ready",
    )


def _build_frame_response(frame: VideoFrame) -> VideoFrameResponse:
    encoded_image = base64.b64encode(frame.image_bytes).decode("ascii")
    return VideoFrameResponse(
        assetId=frame.asset_id,
        frameIndex=frame.frame_index,
        timestampSeconds=frame.timestamp_seconds,
        mimeType=frame.mime_type,
        width=frame.width,
        height=frame.height,
        imageDataUrl=f"data:{frame.mime_type};base64,{encoded_image}",
    )


def _build_workbench_snapshot_response(
    session: WorkbenchSession,
    frame: VideoFrame,
) -> WorkbenchSnapshotResponse:
    return WorkbenchSnapshotResponse(
        state=_build_workbench_state_response(session),
        frame=_build_frame_response(frame),
    )


def _build_workbench_state_response(session: WorkbenchSession) -> WorkbenchStateResponse:
    return WorkbenchStateResponse(
        workbenchFrameIndex=session.workbench_frame_index,
        workbenchTimestampSeconds=session.workbench_timestamp_seconds,
        workbenchFrameRequestKey=f"{session.asset_id}:{session.workbench_frame_index}",
        previewRefreshGeneration=session.preview_refresh_generation,
        promptEntries=[
            PromptEntryResponse(
                identifier=entry.identifier,
                mode=entry.mode,
                frameIndex=entry.frame_index,
                x=entry.x,
                y=entry.y,
                source=entry.source,
            )
            for entry in session.prompt_entries
        ],
        overlayState=OverlayStateResponse(
            showDebugOverlay=session.overlay_state.show_debug_overlay,
        ),
        selectedMaskSettings=MaskSettingsResponse(
            threshold=session.mask_settings.threshold,
            feather=session.mask_settings.feather,
            invert=session.mask_settings.invert,
        ),
        workbenchStatus="ready",
    )
