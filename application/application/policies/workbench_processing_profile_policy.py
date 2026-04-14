"""Policies for explicit preview/final processing profile selection."""

from __future__ import annotations

from dataclasses import dataclass

from application.domain.model.mask_preview import ProcessingMode, ProcessingProfile


@dataclass(frozen=True)
class WorkbenchProcessingProfilePolicy:
    """Resolve explicit profiles for workbench preview and future final render modes."""

    preview_max_dimension: int = 384
    final_max_dimension: int = 1080

    def preview_profile(self) -> ProcessingProfile:
        """Return the profile used for fast, interactive workbench previews."""
        return ProcessingProfile(
            mode=ProcessingMode.PREVIEW,
            max_dimension=self.preview_max_dimension,
        )

    def final_profile(self) -> ProcessingProfile:
        """Return the placeholder profile reserved for higher quality final rendering."""
        return ProcessingProfile(
            mode=ProcessingMode.FINAL,
            max_dimension=self.final_max_dimension,
        )
