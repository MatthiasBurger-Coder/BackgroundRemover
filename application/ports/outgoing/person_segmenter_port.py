"""Outgoing port for prompt-guided person mask generation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from application.domain.model.mask_preview import (
    FrameSize,
    MaskConfidenceMap,
    PointPrompt,
    ProcessingMode,
)
from application.domain.model.video_asset import VideoFrame


class PersonSegmenterPort(Protocol):
    """Port for generating a person-focused confidence map from prompts."""

    def generate_person_confidence_map(
        self,
        *,
        frame: VideoFrame,
        prompts: Sequence[PointPrompt],
        processing_mode: ProcessingMode,
        target_size: FrameSize,
    ) -> MaskConfidenceMap:
        """Return a soft person confidence map for the requested frame."""
