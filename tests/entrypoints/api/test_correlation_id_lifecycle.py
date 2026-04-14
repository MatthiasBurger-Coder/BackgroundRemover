"""Tests for request-scoped correlation id lifecycle behavior."""

from __future__ import annotations

import asyncio
import logging
import unittest

from application.entrypoints.api.request_lifecycle import run_with_action_correlation
from application.infrastructure.context.correlation_id_manager import CorrelationIdManager
from fastapi import Request


class _CaptureHandler(logging.Handler):
    """Collect emitted records for targeted assertions."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class _CorrelationIdFilter(logging.Filter):
    """Attach the active correlation id to test log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = CorrelationIdManager.get_correlation_id() or "-"  # type: ignore[attr-defined]
        return True


class CorrelationIdLifecycleTests(unittest.TestCase):
    """Ensure each frontend-triggered API interaction receives a fresh CID."""

    def setUp(self) -> None:
        CorrelationIdManager.clear()
        self.logger = logging.getLogger("application.entrypoints.api.request_lifecycle")
        self.capture_handler = _CaptureHandler()
        self.capture_handler.addFilter(_CorrelationIdFilter())
        self.logger.addHandler(self.capture_handler)
        self.logger.setLevel(logging.INFO)
        self._original_propagate = self.logger.propagate
        self.logger.propagate = False

    def tearDown(self) -> None:
        self.logger.removeHandler(self.capture_handler)
        self.logger.propagate = self._original_propagate
        CorrelationIdManager.clear()

    def test_each_request_gets_fresh_correlation_id_and_keeps_it_during_request(self) -> None:
        observed_cids: list[str] = []

        async def _run_once(path: str) -> None:
            request = Request(
                {
                    "type": "http",
                    "method": "GET",
                    "path": path,
                    "headers": [],
                    "query_string": b"",
                    "client": ("testclient", 123),
                    "server": ("testserver", 80),
                    "scheme": "http",
                    "http_version": "1.1",
                }
            )

            async def _fake_call_next(_: Request) -> object:
                active_cid = CorrelationIdManager.get_correlation_id()
                if active_cid is not None:
                    observed_cids.append(active_cid)
                return type("Response", (), {"status_code": 200})()

            await run_with_action_correlation(request, _fake_call_next)

        asyncio.run(_run_once("/api/health"))
        asyncio.run(_run_once("/api/health"))

        lifecycle_records = [
            record
            for record in self.capture_handler.records
            if record.getMessage().startswith("Action lifecycle")
        ]

        self.assertEqual(len(lifecycle_records), 4)

        first_start = lifecycle_records[0]
        first_finish = lifecycle_records[1]
        second_start = lifecycle_records[2]
        second_finish = lifecycle_records[3]

        self.assertEqual(first_start.correlation_id, first_finish.correlation_id)  # type: ignore[attr-defined]
        self.assertEqual(second_start.correlation_id, second_finish.correlation_id)  # type: ignore[attr-defined]
        self.assertNotEqual(first_start.correlation_id, second_start.correlation_id)  # type: ignore[attr-defined]
        self.assertEqual(len(observed_cids), 2)
        self.assertEqual(first_start.correlation_id, observed_cids[0])  # type: ignore[attr-defined]
        self.assertEqual(second_start.correlation_id, observed_cids[1])  # type: ignore[attr-defined]
        self.assertIsNone(CorrelationIdManager.get_correlation_id())
