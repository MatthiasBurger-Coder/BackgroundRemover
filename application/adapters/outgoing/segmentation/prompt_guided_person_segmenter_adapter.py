"""Deterministic prompt-guided baseline for person mask preview generation."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from application.domain.model.mask_preview import (
    FrameSize,
    MaskConfidenceMap,
    PointPrompt,
    ProcessingMode,
    PromptMode,
)
from application.domain.model.video_asset import VideoFrame


@dataclass(frozen=True)
class _ScaledPrompt:
    mode: PromptMode
    x: float
    y: float


class PromptGuidedPersonSegmenterAdapter:
    """Generate a soft person-shaped confidence field around foreground prompts."""

    def generate_person_confidence_map(
        self,
        *,
        frame: VideoFrame,
        prompts: Sequence[PointPrompt],
        processing_mode: ProcessingMode,
        target_size: FrameSize,
    ) -> MaskConfidenceMap:
        del processing_mode

        scaled_prompts = tuple(
            self._scale_prompt(
                prompt=prompt,
                source_width=frame.width,
                source_height=frame.height,
                target_size=target_size,
            )
            for prompt in prompts
        )
        foreground_prompts = tuple(
            prompt for prompt in scaled_prompts if prompt.mode is PromptMode.FOREGROUND
        )
        background_prompts = tuple(
            prompt for prompt in scaled_prompts if prompt.mode is PromptMode.BACKGROUND
        )

        if not foreground_prompts:
            return MaskConfidenceMap(
                width=target_size.width,
                height=target_size.height,
                rows=tuple(bytes(target_size.width) for _ in range(target_size.height)),
            )

        rows = []
        for y in range(target_size.height):
            row = bytearray(target_size.width)
            for x in range(target_size.width):
                positive_confidence = max(
                    self._foreground_confidence_at_pixel(
                        x=x,
                        y=y,
                        prompt=prompt,
                        frame_size=target_size,
                    )
                    for prompt in foreground_prompts
                )
                negative_confidence = max(
                    (
                        self._background_confidence_at_pixel(
                            x=x,
                            y=y,
                            prompt=prompt,
                            frame_size=target_size,
                        )
                        for prompt in background_prompts
                    ),
                    default=0.0,
                )
                confidence = min(max(positive_confidence - negative_confidence, 0.0), 1.0)
                row[x] = int(round(confidence * 255))
            rows.append(bytes(row))

        return MaskConfidenceMap(
            width=target_size.width,
            height=target_size.height,
            rows=tuple(rows),
        )

    def _scale_prompt(
        self,
        *,
        prompt: PointPrompt,
        source_width: int,
        source_height: int,
        target_size: FrameSize,
    ) -> _ScaledPrompt:
        source_width = max(source_width, 1)
        source_height = max(source_height, 1)
        return _ScaledPrompt(
            mode=prompt.mode,
            x=(prompt.x / source_width) * target_size.width,
            y=(prompt.y / source_height) * target_size.height,
        )

    def _foreground_confidence_at_pixel(
        self,
        *,
        x: int,
        y: int,
        prompt: _ScaledPrompt,
        frame_size: FrameSize,
    ) -> float:
        torso_rx = max(frame_size.width * 0.08, 18.0)
        torso_ry = max(frame_size.height * 0.16, 26.0)
        head_rx = torso_rx * 0.38
        head_ry = torso_ry * 0.36
        legs_rx = torso_rx * 0.72
        legs_ry = torso_ry * 1.08
        halo_rx = torso_rx * 1.45
        halo_ry = torso_ry * 1.55

        torso = self._ellipse_field(
            x=x,
            y=y,
            center_x=prompt.x,
            center_y=prompt.y,
            radius_x=torso_rx,
            radius_y=torso_ry,
        )
        head = self._ellipse_field(
            x=x,
            y=y,
            center_x=prompt.x,
            center_y=prompt.y - (torso_ry * 0.92),
            radius_x=head_rx,
            radius_y=head_ry,
        )
        legs = self._ellipse_field(
            x=x,
            y=y,
            center_x=prompt.x,
            center_y=prompt.y + (torso_ry * 1.05),
            radius_x=legs_rx,
            radius_y=legs_ry,
        )
        halo = self._ellipse_field(
            x=x,
            y=y,
            center_x=prompt.x,
            center_y=prompt.y + (torso_ry * 0.15),
            radius_x=halo_rx,
            radius_y=halo_ry,
        )

        return min(1.0, (torso * 0.95) + (head * 0.45) + (legs * 0.85) + (halo * 0.35))

    def _background_confidence_at_pixel(
        self,
        *,
        x: int,
        y: int,
        prompt: _ScaledPrompt,
        frame_size: FrameSize,
    ) -> float:
        inner_radius = max(frame_size.width * 0.04, 12.0)
        outer_radius = inner_radius * 1.8

        inner = self._ellipse_field(
            x=x,
            y=y,
            center_x=prompt.x,
            center_y=prompt.y,
            radius_x=inner_radius,
            radius_y=inner_radius,
        )
        outer = self._ellipse_field(
            x=x,
            y=y,
            center_x=prompt.x,
            center_y=prompt.y,
            radius_x=outer_radius,
            radius_y=outer_radius,
        )
        return min(1.0, (inner * 1.1) + (outer * 0.35))

    def _ellipse_field(
        self,
        *,
        x: int,
        y: int,
        center_x: float,
        center_y: float,
        radius_x: float,
        radius_y: float,
    ) -> float:
        normalized_distance = math.sqrt(
            (((x + 0.5) - center_x) / max(radius_x, 1.0)) ** 2
            + (((y + 0.5) - center_y) / max(radius_y, 1.0)) ** 2
        )
        return max(0.0, 1.0 - normalized_distance)
