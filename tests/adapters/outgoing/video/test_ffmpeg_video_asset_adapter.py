"""Integration-style regression tests for the FFmpeg video asset adapter."""

from __future__ import annotations

import unittest
from pathlib import Path

from src.application.adapters.outgoing.video.ffmpeg_video_asset_adapter import (
    FfmpegVideoAssetAdapter,
)

TEST_VIDEO_PATH = Path(__file__).resolve().parents[3] / "resources" / "miki.mp4"


class FfmpegVideoAssetAdapterTests(unittest.TestCase):
    """Protect the real-video metadata and frame extraction workflow."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.adapter = FfmpegVideoAssetAdapter()
        cls.video_bytes = TEST_VIDEO_PATH.read_bytes()

    def test_register_video_asset_and_extract_boundary_frames_from_real_video(self) -> None:
        metadata = self.adapter.register_video_asset(
            filename=TEST_VIDEO_PATH.name,
            video_bytes=self.video_bytes,
            mime_type="video/mp4",
        )

        self.assertEqual(metadata.filename, "miki.mp4")
        self.assertGreater(metadata.fps, 0.0)
        self.assertGreater(metadata.frame_count, 0)
        self.assertGreater(metadata.duration_seconds, 0.0)
        self.assertGreater(metadata.width, 0)
        self.assertGreater(metadata.height, 0)

        requested_indices = [0, metadata.frame_count // 2, metadata.frame_count - 1]
        extracted_frames = [
            self.adapter.get_video_frame(metadata.asset_id, frame_index)
            for frame_index in requested_indices
        ]

        self.assertEqual(extracted_frames[0].frame_index, 0)
        self.assertEqual(extracted_frames[-1].frame_index, metadata.frame_count - 1)

        for frame in extracted_frames:
            self.assertEqual(frame.asset_id, metadata.asset_id)
            self.assertEqual(frame.mime_type, "image/png")
            self.assertEqual(frame.width, metadata.width)
            self.assertEqual(frame.height, metadata.height)
            self.assertGreater(len(frame.image_bytes), 0)

        self.assertLess(extracted_frames[0].timestamp_seconds, extracted_frames[1].timestamp_seconds)
        self.assertLess(extracted_frames[1].timestamp_seconds, extracted_frames[2].timestamp_seconds)

    def test_get_video_frame_clamps_out_of_range_request_to_last_real_frame(self) -> None:
        metadata = self.adapter.register_video_asset(
            filename=TEST_VIDEO_PATH.name,
            video_bytes=self.video_bytes,
            mime_type="video/mp4",
        )

        frame = self.adapter.get_video_frame(metadata.asset_id, metadata.frame_count + 25)

        self.assertEqual(frame.frame_index, metadata.frame_count - 1)
        self.assertEqual(frame.width, metadata.width)
        self.assertEqual(frame.height, metadata.height)
        self.assertGreater(len(frame.image_bytes), 0)


if __name__ == "__main__":
    unittest.main()
