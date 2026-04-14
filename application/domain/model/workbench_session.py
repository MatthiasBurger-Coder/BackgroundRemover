"""Domain models for browser workbench state bound to a video asset."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from application.domain.model.mask_preview import MaskPreviewResult


@dataclass(frozen=True)
class PromptEntry:
    """A user-authored prompt bound to a fixed workbench frame."""

    identifier: int
    mode: str
    frame_index: int
    x: int
    y: int
    source: str


@dataclass(frozen=True)
class MaskSettings:
    """Mask-related settings selected for the active workbench snapshot."""

    threshold: float = 0.62
    feather: int = 8
    invert: bool = False


@dataclass(frozen=True)
class OverlayState:
    """Overlay options used while reviewing the fixed workbench frame."""

    show_debug_overlay: bool = True


@dataclass(frozen=True)
class WorkbenchSession:
    """Server-side workbench state for a single browser-managed asset session."""

    asset_id: str
    workbench_frame_index: int = 0
    workbench_timestamp_seconds: float = 0.0
    preview_refresh_generation: int = 0
    prompt_entries: tuple[PromptEntry, ...] = ()
    mask_settings: MaskSettings = field(default_factory=MaskSettings)
    overlay_state: OverlayState = field(default_factory=OverlayState)
    mask_preview_result: MaskPreviewResult | None = None

    def with_frame(self, *, frame_index: int, timestamp_seconds: float) -> WorkbenchSession:
        return replace(
            self,
            workbench_frame_index=frame_index,
            workbench_timestamp_seconds=timestamp_seconds,
        )

    def with_prompt(self, prompt_entry: PromptEntry) -> WorkbenchSession:
        return replace(self, prompt_entries=(*self.prompt_entries, prompt_entry))

    def cleared_prompts(self) -> WorkbenchSession:
        return replace(self, prompt_entries=())

    def with_mask_settings(self, mask_settings: MaskSettings) -> WorkbenchSession:
        return replace(self, mask_settings=mask_settings)

    def with_overlay_state(self, overlay_state: OverlayState) -> WorkbenchSession:
        return replace(self, overlay_state=overlay_state)

    def with_preview_refresh_generation(self, generation: int) -> WorkbenchSession:
        return replace(self, preview_refresh_generation=generation)

    def with_mask_preview_result(self, mask_preview_result: MaskPreviewResult | None) -> WorkbenchSession:
        return replace(self, mask_preview_result=mask_preview_result)

    def cleared_mask_preview_result(self) -> WorkbenchSession:
        return replace(self, mask_preview_result=None)
