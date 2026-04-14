"""Outgoing port for rendering workbench mask preview artifacts."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from application.domain.model.mask_preview import (
    BinaryMask,
    MaskPreviewResult,
    PointPrompt,
    ProcessingProfile,
)
from application.domain.model.video_asset import VideoFrame


class PreviewRendererPort(Protocol):
    """Port for turning source frames and masks into browser-friendly preview assets."""

    def render_mask_preview(
        self,
        *,
        source_frame: VideoFrame,
        binary_mask: BinaryMask,
        prompts: Sequence[PointPrompt],
        processing_profile: ProcessingProfile,
    ) -> MaskPreviewResult:
        """Render overlay and mask artifacts for the active workbench snapshot."""
