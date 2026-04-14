"""Application wiring for browser workbench session use cases."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from application.adapters.outgoing.rendering.svg_mask_preview_renderer_adapter import (
    SvgMaskPreviewRendererAdapter,
)
from application.adapters.outgoing.segmentation.box_blur_mask_refiner_adapter import (
    BoxBlurMaskRefinerAdapter,
)
from application.adapters.outgoing.segmentation.prompt_guided_person_segmenter_adapter import (
    PromptGuidedPersonSegmenterAdapter,
)
from application.adapters.outgoing.storage.in_memory_workbench_session_adapter import (
    InMemoryWorkbenchSessionAdapter,
)
from application.application.policies.workbench_processing_profile_policy import (
    WorkbenchProcessingProfilePolicy,
)
from application.application.use_cases.workbench_session_use_cases import (
    AddWorkbenchPromptUseCase,
    ClearWorkbenchPromptsUseCase,
    DeleteWorkbenchSessionUseCase,
    GetWorkbenchSessionUseCase,
    RefreshWorkbenchPreviewUseCase,
    SyncWorkbenchFrameUseCase,
    UpdateWorkbenchSettingsUseCase,
)
from application.infrastructure.wiring.video_asset_backend import get_video_asset_backend


@dataclass(frozen=True)
class WorkbenchBackend:
    """Wiring container for GUI-facing workbench session use cases."""

    get_workbench_session: GetWorkbenchSessionUseCase
    sync_workbench_frame: SyncWorkbenchFrameUseCase
    add_prompt: AddWorkbenchPromptUseCase
    clear_prompts: ClearWorkbenchPromptsUseCase
    update_settings: UpdateWorkbenchSettingsUseCase
    refresh_preview: RefreshWorkbenchPreviewUseCase
    delete_session: DeleteWorkbenchSessionUseCase


@lru_cache(maxsize=1)
def get_workbench_backend() -> WorkbenchBackend:
    video_asset_backend = get_video_asset_backend()
    workbench_session_adapter = InMemoryWorkbenchSessionAdapter()
    person_segmenter_adapter = PromptGuidedPersonSegmenterAdapter()
    mask_refiner_adapter = BoxBlurMaskRefinerAdapter()
    preview_renderer_adapter = SvgMaskPreviewRendererAdapter()
    processing_profile_policy = WorkbenchProcessingProfilePolicy()
    get_workbench_session = GetWorkbenchSessionUseCase(
        workbench_session_adapter,
        video_asset_backend.video_asset_port,
    )
    return WorkbenchBackend(
        get_workbench_session=get_workbench_session,
        sync_workbench_frame=SyncWorkbenchFrameUseCase(
            workbench_session_adapter,
            video_asset_backend.video_asset_port,
            get_workbench_session,
        ),
        add_prompt=AddWorkbenchPromptUseCase(workbench_session_adapter, get_workbench_session),
        clear_prompts=ClearWorkbenchPromptsUseCase(workbench_session_adapter, get_workbench_session),
        update_settings=UpdateWorkbenchSettingsUseCase(workbench_session_adapter, get_workbench_session),
        refresh_preview=RefreshWorkbenchPreviewUseCase(
            workbench_session_adapter,
            video_asset_backend.video_asset_port,
            get_workbench_session,
            person_segmenter_adapter,
            mask_refiner_adapter,
            preview_renderer_adapter,
            processing_profile_policy,
        ),
        delete_session=DeleteWorkbenchSessionUseCase(workbench_session_adapter),
    )
