"""Outgoing port for confidence-map refinement."""

from __future__ import annotations

from typing import Protocol

from application.domain.model.mask_preview import MaskConfidenceMap


class MaskRefinerPort(Protocol):
    """Port for deterministic mask refinement strategies."""

    def refine_confidence_map(
        self,
        *,
        confidence_map: MaskConfidenceMap,
        feather_radius: int,
    ) -> MaskConfidenceMap:
        """Return a refined confidence map suitable for thresholding."""
