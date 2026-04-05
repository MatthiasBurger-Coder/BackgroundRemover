"""API regression tests for the browser-based workspace."""

from __future__ import annotations

import unittest
from pathlib import Path

from application.entrypoints.api.app import create_app
from fastapi.testclient import TestClient

TEST_VIDEO_PATH = Path(__file__).resolve().parents[2] / "resources" / "miki.mp4"


class VideoWorkspaceApiTests(unittest.TestCase):
    """Protect the browser-facing API for source, preview, and workbench state."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(create_app())
        cls.video_bytes = TEST_VIDEO_PATH.read_bytes()

    def test_register_asset_bootstraps_source_playback_and_workbench(self) -> None:
        response = self.client.post(
            "/api/assets",
            files={"file": ("miki.mp4", self.video_bytes, "video/mp4")},
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()

        self.assertEqual(payload["asset"]["filename"], "miki.mp4")
        self.assertGreater(payload["asset"]["fps"], 0.0)
        self.assertFalse(payload["playback"]["playbackRunning"])
        self.assertEqual(payload["playback"]["playbackFrameIndex"], 0)
        self.assertEqual(payload["workbench"]["state"]["workbenchFrameIndex"], 0)
        self.assertEqual(payload["workbench"]["frame"]["frameIndex"], 0)
        self.assertTrue(payload["workbench"]["frame"]["imageDataUrl"].startswith("data:image/png;base64,"))

    def test_workbench_frame_prompt_and_settings_flow_stays_bound_to_selected_frame(self) -> None:
        register_response = self.client.post(
            "/api/assets",
            files={"file": ("miki.mp4", self.video_bytes, "video/mp4")},
        )
        asset_id = register_response.json()["asset"]["assetId"]

        frame_response = self.client.put(
            f"/api/assets/{asset_id}/workbench/frame",
            json={"frameIndex": 7},
        )
        self.assertEqual(frame_response.status_code, 200)
        frame_payload = frame_response.json()
        self.assertEqual(frame_payload["state"]["workbenchFrameIndex"], 7)
        self.assertEqual(frame_payload["frame"]["frameIndex"], 7)

        prompt_response = self.client.post(
            f"/api/assets/{asset_id}/workbench/prompts",
            json={"mode": "foreground", "x": 123, "y": 234, "source": "API test"},
        )
        self.assertEqual(prompt_response.status_code, 200)
        prompt_payload = prompt_response.json()
        self.assertEqual(len(prompt_payload["promptEntries"]), 1)
        self.assertEqual(prompt_payload["promptEntries"][0]["frameIndex"], 7)

        settings_response = self.client.put(
            f"/api/assets/{asset_id}/workbench/settings",
            json={
                "threshold": 0.71,
                "feather": 12,
                "invert": True,
                "showDebugOverlay": False,
            },
        )
        self.assertEqual(settings_response.status_code, 200)
        settings_payload = settings_response.json()
        self.assertAlmostEqual(settings_payload["selectedMaskSettings"]["threshold"], 0.71)
        self.assertEqual(settings_payload["selectedMaskSettings"]["feather"], 12)
        self.assertTrue(settings_payload["selectedMaskSettings"]["invert"])
        self.assertFalse(settings_payload["overlayState"]["showDebugOverlay"])

        refresh_response = self.client.post(f"/api/assets/{asset_id}/workbench/preview-refresh")
        self.assertEqual(refresh_response.status_code, 200)
        self.assertEqual(refresh_response.json()["previewRefreshGeneration"], 1)

        snapshot_response = self.client.get(f"/api/assets/{asset_id}/workbench")
        self.assertEqual(snapshot_response.status_code, 200)
        snapshot_payload = snapshot_response.json()
        self.assertEqual(snapshot_payload["state"]["workbenchFrameIndex"], 7)
        self.assertEqual(snapshot_payload["frame"]["frameIndex"], 7)
        self.assertEqual(len(snapshot_payload["state"]["promptEntries"]), 1)

    def test_delete_asset_removes_source_and_workbench_state(self) -> None:
        register_response = self.client.post(
            "/api/assets",
            files={"file": ("miki.mp4", self.video_bytes, "video/mp4")},
        )
        asset_id = register_response.json()["asset"]["assetId"]

        delete_response = self.client.delete(f"/api/assets/{asset_id}")

        self.assertEqual(delete_response.status_code, 204)
        metadata_response = self.client.get(f"/api/assets/{asset_id}")
        self.assertEqual(metadata_response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
