"""Use cases for browser-facing workbench state and prompt editing."""

from __future__ import annotations

from dataclasses import dataclass

from application.domain.model.workbench_session import (
    MaskSettings,
    OverlayState,
    PromptEntry,
    WorkbenchSession,
)
from application.ports.outgoing.video_asset_port import VideoAssetPort
from application.ports.outgoing.workbench_session_port import WorkbenchSessionPort


@dataclass(frozen=True)
class GetWorkbenchSessionUseCase:
    """Load the current workbench session, creating a default state when missing."""

    workbench_session_port: WorkbenchSessionPort
    video_asset_port: VideoAssetPort

    def execute(self, asset_id: str) -> WorkbenchSession:
        existing_session = self.workbench_session_port.get_workbench_session(asset_id)
        if existing_session is not None:
            return existing_session
        metadata = self.video_asset_port.get_video_metadata(asset_id)
        session = WorkbenchSession(
            asset_id=asset_id,
            workbench_frame_index=0,
            workbench_timestamp_seconds=0.0 if metadata.fps <= 0 else 0 / metadata.fps,
        )
        return self.workbench_session_port.save_workbench_session(session)


@dataclass(frozen=True)
class SyncWorkbenchFrameUseCase:
    """Bind the workbench session to a specific frame index for the active asset."""

    workbench_session_port: WorkbenchSessionPort
    video_asset_port: VideoAssetPort
    get_workbench_session: GetWorkbenchSessionUseCase

    def execute(self, *, asset_id: str, frame_index: int) -> WorkbenchSession:
        metadata = self.video_asset_port.get_video_metadata(asset_id)
        clamped_frame_index = metadata.clamped_frame_index(frame_index)
        timestamp_seconds = clamped_frame_index / metadata.fps if metadata.fps > 0 else 0.0
        session = self.get_workbench_session.execute(asset_id)
        return self.workbench_session_port.save_workbench_session(
            session.with_frame(
                frame_index=clamped_frame_index,
                timestamp_seconds=timestamp_seconds,
            )
        )


@dataclass(frozen=True)
class AddWorkbenchPromptUseCase:
    """Append a prompt entry to the current workbench session."""

    workbench_session_port: WorkbenchSessionPort
    get_workbench_session: GetWorkbenchSessionUseCase

    def execute(
        self,
        *,
        asset_id: str,
        mode: str,
        x: int,
        y: int,
        source: str,
    ) -> WorkbenchSession:
        session = self.get_workbench_session.execute(asset_id)
        prompt_entry = PromptEntry(
            identifier=len(session.prompt_entries) + 1,
            mode=mode,
            frame_index=session.workbench_frame_index,
            x=x,
            y=y,
            source=source,
        )
        return self.workbench_session_port.save_workbench_session(session.with_prompt(prompt_entry))


@dataclass(frozen=True)
class ClearWorkbenchPromptsUseCase:
    """Remove all prompt entries from the current workbench session."""

    workbench_session_port: WorkbenchSessionPort
    get_workbench_session: GetWorkbenchSessionUseCase

    def execute(self, asset_id: str) -> WorkbenchSession:
        session = self.get_workbench_session.execute(asset_id)
        return self.workbench_session_port.save_workbench_session(session.cleared_prompts())


@dataclass(frozen=True)
class UpdateWorkbenchSettingsUseCase:
    """Update mask and overlay options for the active workbench session."""

    workbench_session_port: WorkbenchSessionPort
    get_workbench_session: GetWorkbenchSessionUseCase

    def execute(
        self,
        *,
        asset_id: str,
        threshold: float,
        feather: int,
        invert: bool,
        show_debug_overlay: bool,
    ) -> WorkbenchSession:
        session = self.get_workbench_session.execute(asset_id)
        updated_session = session.with_mask_settings(
            MaskSettings(
                threshold=max(0.0, min(threshold, 1.0)),
                feather=max(feather, 0),
                invert=invert,
            )
        ).with_overlay_state(
            OverlayState(show_debug_overlay=show_debug_overlay)
        )
        return self.workbench_session_port.save_workbench_session(updated_session)


@dataclass(frozen=True)
class RefreshWorkbenchPreviewUseCase:
    """Increment the preview refresh generation for the active workbench session."""

    workbench_session_port: WorkbenchSessionPort
    get_workbench_session: GetWorkbenchSessionUseCase

    def execute(self, asset_id: str) -> WorkbenchSession:
        session = self.get_workbench_session.execute(asset_id)
        next_generation = session.preview_refresh_generation + 1
        return self.workbench_session_port.save_workbench_session(
            session.with_preview_refresh_generation(next_generation)
        )


@dataclass(frozen=True)
class DeleteWorkbenchSessionUseCase:
    """Remove the stored workbench session for an asset."""

    workbench_session_port: WorkbenchSessionPort

    def execute(self, asset_id: str) -> None:
        self.workbench_session_port.delete_workbench_session(asset_id)
