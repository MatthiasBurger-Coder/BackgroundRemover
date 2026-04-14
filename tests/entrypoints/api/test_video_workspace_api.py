"""API regression tests for the browser-based workspace."""

from __future__ import annotations

import logging
import unittest
from pathlib import Path

from application.entrypoints.api.app import RequestCorrelationMiddleware, create_app
from application.infrastructure.context.correlation_id_manager import CorrelationIdManager
from application.infrastructure.logging.logging_setup import CorrelationIdFilter
from fastapi import FastAPI
from fastapi.testclient import TestClient

TEST_VIDEO_PATH = Path(__file__).resolve().parents[2] / "resources" / "miki.mp4"


class _RecordCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []
        self.addFilter(CorrelationIdFilter())

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)

    def clear(self) -> None:
        self.records.clear()


def _collect_application_cids(records: list[logging.LogRecord]) -> set[str]:
    return {
        record.__dict__["correlation_id"]
        for record in records
        if record.name.startswith("application.")
        and record.__dict__.get("correlation_id", "-") != "-"
    }


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
        self.assertIsNone(payload["workbench"]["state"]["maskPreview"])
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
        refresh_payload = refresh_response.json()
        self.assertEqual(refresh_payload["previewRefreshGeneration"], 1)
        self.assertIsNotNone(refresh_payload["maskPreview"])
        self.assertEqual(refresh_payload["maskPreview"]["mode"], "preview")
        self.assertTrue(
            refresh_payload["maskPreview"]["overlayImage"]["imageDataUrl"].startswith(
                "data:image/svg+xml;base64,"
            )
        )
        self.assertTrue(
            refresh_payload["maskPreview"]["maskImage"]["imageDataUrl"].startswith(
                "data:image/svg+xml;base64,"
            )
        )

        snapshot_response = self.client.get(f"/api/assets/{asset_id}/workbench")
        self.assertEqual(snapshot_response.status_code, 200)
        snapshot_payload = snapshot_response.json()
        self.assertEqual(snapshot_payload["state"]["workbenchFrameIndex"], 7)
        self.assertEqual(snapshot_payload["frame"]["frameIndex"], 7)
        self.assertEqual(len(snapshot_payload["state"]["promptEntries"]), 1)
        self.assertIsNotNone(snapshot_payload["state"]["maskPreview"])

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

    def test_asset_source_supports_byte_ranges_for_browser_seek(self) -> None:
        register_response = self.client.post(
            "/api/assets",
            files={"file": ("miki.mp4", self.video_bytes, "video/mp4")},
        )
        asset_id = register_response.json()["asset"]["assetId"]

        response = self.client.get(
            f"/api/assets/{asset_id}/source",
            headers={"Range": "bytes=0-127"},
        )

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response.headers["accept-ranges"], "bytes")
        self.assertTrue(response.headers["content-range"].startswith("bytes 0-127/"))
        self.assertEqual(len(response.content), 128)


class RequestCorrelationLoggingTests(unittest.TestCase):
    """Verify that one frontend request maps to one complete correlation lifecycle."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.video_bytes = TEST_VIDEO_PATH.read_bytes()

    def setUp(self) -> None:
        CorrelationIdManager.clear()
        self._root_logger = logging.getLogger()
        self._saved_handlers = self._root_logger.handlers[:]
        self._saved_level = self._root_logger.level
        self._collector = _RecordCollector()
        self._root_logger.handlers.clear()
        self._root_logger.addHandler(self._collector)
        self._root_logger.setLevel(logging.DEBUG)

    def tearDown(self) -> None:
        CorrelationIdManager.clear()
        self._root_logger.handlers.clear()
        self._root_logger.handlers.extend(self._saved_handlers)
        self._root_logger.setLevel(self._saved_level)

    def test_each_frontend_request_gets_a_fresh_cid_and_keeps_it_for_the_full_request(self) -> None:
        with TestClient(create_app()) as client:
            self._collector.clear()

            first_response = client.post(
                "/api/assets",
                files={"file": ("miki.mp4", self.video_bytes, "video/mp4")},
            )

            self.assertEqual(first_response.status_code, 201)
            first_request_cids = _collect_application_cids(self._collector.records)
            self.assertEqual(len(first_request_cids), 1)
            first_cid = next(iter(first_request_cids))
            self.assertTrue(
                any(
                    record.getMessage().startswith("Action lifecycle started")
                    for record in self._collector.records
                    if record.name == "application.entrypoints.api.app"
                )
            )
            self.assertTrue(
                any(
                    record.getMessage().startswith("Action lifecycle finished")
                    for record in self._collector.records
                    if record.name == "application.entrypoints.api.app"
                )
            )
            self.assertIsNone(CorrelationIdManager.get_correlation_id())

            self._collector.clear()

            second_response = client.post(
                "/api/assets",
                files={"file": ("miki.mp4", self.video_bytes, "video/mp4")},
            )

            self.assertEqual(second_response.status_code, 201)
            second_request_cids = _collect_application_cids(self._collector.records)
            self.assertEqual(len(second_request_cids), 1)
            second_cid = next(iter(second_request_cids))
            self.assertNotEqual(first_cid, second_cid)
            self.assertIsNone(CorrelationIdManager.get_correlation_id())

    def test_request_lifecycle_overrides_stale_context_without_reusing_it(self) -> None:
        CorrelationIdManager.set_correlation_id("stale-cid")

        with TestClient(create_app()) as client:
            self._collector.clear()

            response = client.post(
                "/api/assets",
                files={"file": ("miki.mp4", self.video_bytes, "video/mp4")},
            )

        self.assertEqual(response.status_code, 201)
        request_cids = _collect_application_cids(self._collector.records)
        self.assertEqual(len(request_cids), 1)
        request_cid = next(iter(request_cids))
        self.assertNotEqual(request_cid, "stale-cid")
        self.assertEqual(CorrelationIdManager.get_correlation_id(), "stale-cid")

    def test_failed_frontend_request_keeps_one_cid_for_start_failure_and_nested_logs(self) -> None:
        failing_app = FastAPI()
        failing_logger = logging.getLogger("application.entrypoints.api.failure_probe")

        @failing_app.get("/boom")
        async def boom() -> None:
            failing_logger.info("Failing lifecycle work started")
            raise RuntimeError("boom")

        failing_app.add_middleware(RequestCorrelationMiddleware)

        with TestClient(failing_app, raise_server_exceptions=False) as client:
            self._collector.clear()

            response = client.get("/boom")

        self.assertEqual(response.status_code, 500)
        failure_request_cids = _collect_application_cids(self._collector.records)
        self.assertEqual(len(failure_request_cids), 1)
        failure_cid = next(iter(failure_request_cids))

        started_records = [
            record
            for record in self._collector.records
            if record.name == "application.entrypoints.api.app"
            and record.getMessage().startswith("Action lifecycle started")
        ]
        failed_records = [
            record
            for record in self._collector.records
            if record.name == "application.entrypoints.api.app"
            and record.getMessage().startswith("Action lifecycle failed")
        ]
        nested_failure_records = [
            record
            for record in self._collector.records
            if record.name == "application.entrypoints.api.failure_probe"
        ]

        self.assertEqual(len(started_records), 1)
        self.assertEqual(len(failed_records), 1)
        self.assertEqual(len(nested_failure_records), 1)
        self.assertEqual(started_records[0].correlation_id, failure_cid)  # type: ignore[attr-defined]
        self.assertEqual(failed_records[0].correlation_id, failure_cid)  # type: ignore[attr-defined]
        self.assertEqual(nested_failure_records[0].correlation_id, failure_cid)  # type: ignore[attr-defined]
        self.assertIsNone(CorrelationIdManager.get_correlation_id())


if __name__ == "__main__":
    unittest.main()
