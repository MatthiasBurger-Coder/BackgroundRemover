"""Domain models for prompt-guided person mask preview generation."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum


class ProcessingMode(StrEnum):
    """Explicit processing modes supported by the extraction engine."""

    PREVIEW = "preview"
    FINAL = "final"


class PromptMode(StrEnum):
    """Prompt semantics supported by the current person extraction flow."""

    FOREGROUND = "foreground"
    BACKGROUND = "background"


@dataclass(frozen=True)
class FrameSize:
    """Resolution descriptor used by preview/final processing profiles."""

    width: int
    height: int

    def scaled_to_max_dimension(self, max_dimension: int) -> FrameSize:
        """Scale the size proportionally so the longest edge stays within the target."""
        if max_dimension <= 0:
            return self
        longest_edge = max(self.width, self.height)
        if longest_edge <= max_dimension:
            return self

        scale = max_dimension / longest_edge
        return FrameSize(
            width=max(1, int(round(self.width * scale))),
            height=max(1, int(round(self.height * scale))),
        )


@dataclass(frozen=True)
class ProcessingProfile:
    """Configuration for a concrete preview or final render processing pass."""

    mode: ProcessingMode
    max_dimension: int

    def resolve_target_size(self, source_size: FrameSize) -> FrameSize:
        """Resolve the output size used for the concrete processing pass."""
        return source_size.scaled_to_max_dimension(self.max_dimension)


@dataclass(frozen=True)
class PointPrompt:
    """Prompt bound to a single workbench frame and interpreted by segmentation adapters."""

    mode: PromptMode
    frame_index: int
    x: int
    y: int


@dataclass(frozen=True)
class MaskConfidenceMap:
    """Soft confidence values in the closed range [0, 255]."""

    width: int
    height: int
    rows: tuple[bytes, ...]

    def to_binary_mask(self, *, threshold: float, invert: bool = False) -> BinaryMask:
        """Convert the soft confidence map into a binary mask."""
        threshold_byte = max(0, min(255, int(round(threshold * 255))))
        binary_rows = []
        for row in self.rows:
            binary_rows.append(
                bytes(
                    1 if ((value >= threshold_byte) != invert) else 0
                    for value in row
                )
            )
        return BinaryMask(width=self.width, height=self.height, rows=tuple(binary_rows))


@dataclass(frozen=True)
class BinaryMask:
    """Binary mask values represented as 0/1 bytes."""

    width: int
    height: int
    rows: tuple[bytes, ...]

    @property
    def active_pixel_count(self) -> int:
        """Return the number of active pixels in the mask."""
        return sum(sum(row) for row in self.rows)

    @property
    def coverage_ratio(self) -> float:
        """Return the fraction of active pixels in the mask."""
        total_pixels = self.width * self.height
        if total_pixels <= 0:
            return 0.0
        return self.active_pixel_count / total_pixels

    def iter_active_runs(self) -> Iterator[tuple[int, int, int]]:
        """Yield horizontal active pixel runs as (y, x_start, run_length)."""
        for y, row in enumerate(self.rows):
            x = 0
            while x < self.width:
                if row[x] == 0:
                    x += 1
                    continue

                run_start = x
                while x < self.width and row[x] == 1:
                    x += 1
                yield y, run_start, x - run_start


@dataclass(frozen=True)
class RenderedImage:
    """Rendered preview artifact transported through the API layer."""

    mime_type: str
    width: int
    height: int
    image_bytes: bytes


@dataclass(frozen=True)
class MaskPreviewResult:
    """Combined preview artifacts for workbench review in preview mode."""

    mode: ProcessingMode
    frame_index: int
    source_size: FrameSize
    preview_size: FrameSize
    prompt_count: int
    coverage_ratio: float
    overlay_image: RenderedImage
    mask_image: RenderedImage
