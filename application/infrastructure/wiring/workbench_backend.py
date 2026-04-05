"""Application wiring for browser workbench session use cases."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from application.adapters.outgoing.storage.in_memory_workbench_session_adapter import (
    InMemoryWorkbenchSessionAdapter,
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
    adapter = InMemoryWorkbenchSessionAdapter()
    get_workbench_session = GetWorkbenchSessionUseCase(adapter, video_asset_backend.video_asset_port)
    return WorkbenchBackend(
        get_workbench_session=get_workbench_session,
        sync_workbench_frame=SyncWorkbenchFrameUseCase(
            adapter,
            video_asset_backend.video_asset_port,
            get_workbench_session,
        ),
        add_prompt=AddWorkbenchPromptUseCase(adapter, get_workbench_session),
        clear_prompts=ClearWorkbenchPromptsUseCase(adapter, get_workbench_session),
        update_settings=UpdateWorkbenchSettingsUseCase(adapter, get_workbench_session),
        refresh_preview=RefreshWorkbenchPreviewUseCase(adapter, get_workbench_session),
        delete_session=DeleteWorkbenchSessionUseCase(adapter),
    )
