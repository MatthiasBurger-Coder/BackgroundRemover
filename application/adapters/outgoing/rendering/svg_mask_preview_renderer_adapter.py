"""SVG-based preview renderer for prompt-guided mask previews."""

from __future__ import annotations

import base64
from collections.abc import Sequence
from html import escape

from application.domain.model.mask_preview import (
    BinaryMask,
    FrameSize,
    MaskPreviewResult,
    PointPrompt,
    ProcessingProfile,
    PromptMode,
    RenderedImage,
)
from application.domain.model.video_asset import VideoFrame


class SvgMaskPreviewRendererAdapter:
    """Render overlay and monochrome mask previews as SVG assets."""

    def render_mask_preview(
        self,
        *,
        source_frame: VideoFrame,
        binary_mask: BinaryMask,
        prompts: Sequence[PointPrompt],
        processing_profile: ProcessingProfile,
    ) -> MaskPreviewResult:
        preview_size = FrameSize(width=binary_mask.width, height=binary_mask.height)
        source_size = FrameSize(width=source_frame.width, height=source_frame.height)
        source_image_url = self._build_data_url(
            mime_type=source_frame.mime_type,
            image_bytes=source_frame.image_bytes,
        )
        mask_rectangles = self._build_mask_rectangles(binary_mask)
        prompt_markers = self._build_prompt_markers(
            prompts=prompts,
            source_size=source_size,
            preview_size=preview_size,
        )

        overlay_svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {preview_size.width} {preview_size.height}" '
            f'width="{preview_size.width}" height="{preview_size.height}" shape-rendering="crispEdges">'
            f'<image href="{escape(source_image_url, quote=True)}" '
            f'width="{preview_size.width}" height="{preview_size.height}" preserveAspectRatio="none" />'
            f'<rect width="{preview_size.width}" height="{preview_size.height}" fill="#06111c" opacity="0.18" />'
            f'<g fill="#14f195" fill-opacity="0.44">{mask_rectangles}</g>'
            f'<g>{prompt_markers}</g>'
            "</svg>"
        )
        mask_svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {preview_size.width} {preview_size.height}" '
            f'width="{preview_size.width}" height="{preview_size.height}" shape-rendering="crispEdges">'
            f'<rect width="{preview_size.width}" height="{preview_size.height}" fill="#05070d" />'
            f'<g fill="#f4f7fb">{mask_rectangles}</g>'
            "</svg>"
        )

        return MaskPreviewResult(
            mode=processing_profile.mode,
            frame_index=source_frame.frame_index,
            source_size=source_size,
            preview_size=preview_size,
            prompt_count=len(prompts),
            coverage_ratio=binary_mask.coverage_ratio,
            overlay_image=RenderedImage(
                mime_type="image/svg+xml",
                width=preview_size.width,
                height=preview_size.height,
                image_bytes=overlay_svg.encode("utf-8"),
            ),
            mask_image=RenderedImage(
                mime_type="image/svg+xml",
                width=preview_size.width,
                height=preview_size.height,
                image_bytes=mask_svg.encode("utf-8"),
            ),
        )

    def _build_data_url(self, *, mime_type: str, image_bytes: bytes) -> str:
        payload = base64.b64encode(image_bytes).decode("ascii")
        return f"data:{mime_type};base64,{payload}"

    def _build_mask_rectangles(self, binary_mask: BinaryMask) -> str:
        rectangles = []
        for y, x_start, run_length in binary_mask.iter_active_runs():
            rectangles.append(
                f'<rect x="{x_start}" y="{y}" width="{run_length}" height="1" />'
            )
        return "".join(rectangles)

    def _build_prompt_markers(
        self,
        *,
        prompts: Sequence[PointPrompt],
        source_size: FrameSize,
        preview_size: FrameSize,
    ) -> str:
        if source_size.width <= 0 or source_size.height <= 0:
            return ""

        markers = []
        for prompt in prompts:
            x = (prompt.x / source_size.width) * preview_size.width
            y = (prompt.y / source_size.height) * preview_size.height
            stroke_color = "#14f195" if prompt.mode is PromptMode.FOREGROUND else "#ff5d73"
            markers.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.5" fill="none" '
                f'stroke="{stroke_color}" stroke-width="1.5" />'
            )
            markers.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.5" fill="{stroke_color}" />'
            )
        return "".join(markers)
