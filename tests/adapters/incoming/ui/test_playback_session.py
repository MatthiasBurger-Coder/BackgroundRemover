"""Regression tests for playback synchronization in the driving UI adapter layer."""

from __future__ import annotations

import unittest

from src.application.adapters.incoming.ui.playback_session import (
    advance_playback_position,
    build_navigation_position,
    start_playback,
    step_navigation_position,
    stop_playback,
)


class PlaybackSessionTests(unittest.TestCase):
    """Protect synchronized frame/time transitions for source navigation."""

    def test_build_navigation_position_clamps_frame_and_updates_timecode(self) -> None:
        progress = build_navigation_position(frame_index=12, frame_count=10, fps=5.0)

        self.assertEqual(progress.frame_index, 9)
        self.assertAlmostEqual(progress.time_seconds, 1.8)
        self.assertFalse(progress.playback_running)

    def test_start_playback_records_anchor_without_changing_current_position(self) -> None:
        progress = start_playback(
            current_frame_index=4,
            frame_count=20,
            fps=10.0,
            now_seconds=101.25,
        )

        self.assertEqual(progress.frame_index, 4)
        self.assertAlmostEqual(progress.time_seconds, 0.4)
        self.assertTrue(progress.playback_running)
        self.assertEqual(progress.playback_anchor_frame_index, 4)
        self.assertAlmostEqual(progress.playback_started_at_seconds, 101.25)

    def test_advance_playback_position_advances_frame_and_time_from_anchor(self) -> None:
        progress = advance_playback_position(
            playback_running=True,
            current_frame_index=4,
            frame_count=20,
            fps=10.0,
            playback_started_at_seconds=100.0,
            playback_anchor_frame_index=4,
            now_seconds=100.34,
        )

        self.assertEqual(progress.frame_index, 7)
        self.assertAlmostEqual(progress.time_seconds, 0.7)
        self.assertTrue(progress.playback_running)

    def test_advance_playback_position_stops_at_last_frame(self) -> None:
        progress = advance_playback_position(
            playback_running=True,
            current_frame_index=8,
            frame_count=10,
            fps=5.0,
            playback_started_at_seconds=100.0,
            playback_anchor_frame_index=8,
            now_seconds=100.9,
        )

        self.assertEqual(progress.frame_index, 9)
        self.assertAlmostEqual(progress.time_seconds, 1.8)
        self.assertFalse(progress.playback_running)
        self.assertIsNone(progress.playback_anchor_frame_index)
        self.assertIsNone(progress.playback_started_at_seconds)

    def test_stop_playback_preserves_current_position_and_clears_anchor(self) -> None:
        progress = stop_playback(
            current_frame_index=6,
            frame_count=20,
            fps=10.0,
        )

        self.assertEqual(progress.frame_index, 6)
        self.assertAlmostEqual(progress.time_seconds, 0.6)
        self.assertFalse(progress.playback_running)
        self.assertIsNone(progress.playback_anchor_frame_index)
        self.assertIsNone(progress.playback_started_at_seconds)

    def test_step_navigation_position_updates_frame_and_time(self) -> None:
        progress = step_navigation_position(
            current_frame_index=3,
            step=2,
            frame_count=10,
            fps=4.0,
        )

        self.assertEqual(progress.frame_index, 5)
        self.assertAlmostEqual(progress.time_seconds, 1.25)
        self.assertFalse(progress.playback_running)

    def test_start_playback_at_last_frame_restarts_from_zero(self) -> None:
        progress = start_playback(
            current_frame_index=9,
            frame_count=10,
            fps=5.0,
            now_seconds=10.0,
        )

        self.assertEqual(progress.frame_index, 0)
        self.assertEqual(progress.playback_anchor_frame_index, 0)
        self.assertAlmostEqual(progress.time_seconds, 0.0)
        self.assertTrue(progress.playback_running)


if __name__ == "__main__":
    unittest.main()
