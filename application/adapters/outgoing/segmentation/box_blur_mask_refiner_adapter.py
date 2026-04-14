"""Simple box-blur refiner for preview confidence maps."""

from __future__ import annotations

from application.domain.model.mask_preview import MaskConfidenceMap


class BoxBlurMaskRefinerAdapter:
    """Apply a separable box blur to soften prompt-guided preview masks."""

    def refine_confidence_map(
        self,
        *,
        confidence_map: MaskConfidenceMap,
        feather_radius: int,
    ) -> MaskConfidenceMap:
        if feather_radius <= 0:
            return confidence_map

        horizontal_rows = tuple(
            self._blur_row(row=row, radius=feather_radius)
            for row in confidence_map.rows
        )
        vertical_rows = self._blur_columns(rows=horizontal_rows, radius=feather_radius)
        return MaskConfidenceMap(
            width=confidence_map.width,
            height=confidence_map.height,
            rows=vertical_rows,
        )

    def _blur_row(self, *, row: bytes, radius: int) -> bytes:
        prefix_sums = [0]
        for value in row:
            prefix_sums.append(prefix_sums[-1] + value)

        blurred = bytearray(len(row))
        for x in range(len(row)):
            start_index = max(0, x - radius)
            end_index = min(len(row) - 1, x + radius)
            sample_count = end_index - start_index + 1
            sample_sum = prefix_sums[end_index + 1] - prefix_sums[start_index]
            blurred[x] = int(round(sample_sum / sample_count))
        return bytes(blurred)

    def _blur_columns(self, *, rows: tuple[bytes, ...], radius: int) -> tuple[bytes, ...]:
        if not rows:
            return ()

        width = len(rows[0])
        height = len(rows)
        blurred_rows = [bytearray(width) for _ in range(height)]

        for x in range(width):
            prefix_sums = [0]
            for y in range(height):
                prefix_sums.append(prefix_sums[-1] + rows[y][x])

            for y in range(height):
                start_index = max(0, y - radius)
                end_index = min(height - 1, y + radius)
                sample_count = end_index - start_index + 1
                sample_sum = prefix_sums[end_index + 1] - prefix_sums[start_index]
                blurred_rows[y][x] = int(round(sample_sum / sample_count))

        return tuple(bytes(row) for row in blurred_rows)
