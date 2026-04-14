"""Use cases for browser-facing workbench state and prompt editing."""

from __future__ import annotations

from dataclasses import dataclass

from application.application.policies.workbench_processing_profile_policy import (
    WorkbenchProcessingProfilePolicy,
)
from application.domain.model.mask_preview import FrameSize, PointPrompt, PromptMode
from application.domain.model.workbench_session import (
    MaskSettings,
    OverlayState,
    PromptEntry,
    WorkbenchSession,
)
from application.ports.outgoing.mask_refiner_port import MaskRefinerPort
from application.ports.outgoing.person_segmenter_port import PersonSegmenterPort
from application.ports.outgoing.preview_renderer_port import PreviewRendererPort
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
            ).cleared_mask_preview_result()
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
        return self.workbench_session_port.save_workbench_session(
            session.with_prompt(prompt_entry).cleared_mask_preview_result()
        )


@dataclass(frozen=True)
class ClearWorkbenchPromptsUseCase:
    """Remove all prompt entries from the current workbench session."""

    workbench_session_port: WorkbenchSessionPort
    get_workbench_session: GetWorkbenchSessionUseCase

    def execute(self, asset_id: str) -> WorkbenchSession:
        session = self.get_workbench_session.execute(asset_id)
        return self.workbench_session_port.save_workbench_session(
            session.cleared_prompts().cleared_mask_preview_result()
        )


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
        ).cleared_mask_preview_result()
        return self.workbench_session_port.save_workbench_session(updated_session)


@dataclass(frozen=True)
class RefreshWorkbenchPreviewUseCase:
    """Generate and store a fresh prompt-guided preview for the active workbench frame."""

    workbench_session_port: WorkbenchSessionPort
    video_asset_port: VideoAssetPort
    get_workbench_session: GetWorkbenchSessionUseCase
    person_segmenter_port: PersonSegmenterPort
    mask_refiner_port: MaskRefinerPort
    preview_renderer_port: PreviewRendererPort
    processing_profile_policy: WorkbenchProcessingProfilePolicy

    def execute(self, asset_id: str) -> WorkbenchSession:
        session = self.get_workbench_session.execute(asset_id)
        frame = self.video_asset_port.get_video_frame(asset_id, session.workbench_frame_index)
        source_size = FrameSize(width=frame.width, height=frame.height)
        processing_profile = self.processing_profile_policy.preview_profile()
        target_size = processing_profile.resolve_target_size(source_size)
        active_prompts = tuple(
            _to_point_prompt(prompt_entry)
            for prompt_entry in session.prompt_entries
            if prompt_entry.frame_index == session.workbench_frame_index
        )
        confidence_map = self.person_segmenter_port.generate_person_confidence_map(
            frame=frame,
            prompts=active_prompts,
            processing_mode=processing_profile.mode,
            target_size=target_size,
        )
        refined_confidence_map = self.mask_refiner_port.refine_confidence_map(
            confidence_map=confidence_map,
            feather_radius=_scaled_feather_radius(
                feather=session.mask_settings.feather,
                source_size=source_size,
                target_size=target_size,
            ),
        )
        binary_mask = refined_confidence_map.to_binary_mask(
            threshold=session.mask_settings.threshold,
            invert=session.mask_settings.invert,
        )
        mask_preview_result = self.preview_renderer_port.render_mask_preview(
            source_frame=frame,
            binary_mask=binary_mask,
            prompts=active_prompts,
            processing_profile=processing_profile,
        )
        next_generation = session.preview_refresh_generation + 1
        return self.workbench_session_port.save_workbench_session(
            session.with_mask_preview_result(mask_preview_result).with_preview_refresh_generation(
                next_generation
            )
        )


@dataclass(frozen=True)
class DeleteWorkbenchSessionUseCase:
    """Remove the stored workbench session for an asset."""

    workbench_session_port: WorkbenchSessionPort

    def execute(self, asset_id: str) -> None:
        self.workbench_session_port.delete_workbench_session(asset_id)


def _to_point_prompt(prompt_entry: PromptEntry) -> PointPrompt:
    return PointPrompt(
        mode=PromptMode(prompt_entry.mode),
        frame_index=prompt_entry.frame_index,
        x=prompt_entry.x,
        y=prompt_entry.y,
    )


def _scaled_feather_radius(*, feather: int, source_size: FrameSize, target_size: FrameSize) -> int:
    if feather <= 0 or source_size.width <= 0:
        return 0
    scaled_radius = round(feather * (target_size.width / source_size.width))
    return max(scaled_radius, 0)
