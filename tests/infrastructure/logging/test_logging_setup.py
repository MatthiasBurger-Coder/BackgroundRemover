"""Tests for logging setup and the CorrelationIdFilter."""

from __future__ import annotations

import logging
import threading
import unittest

from application.infrastructure.context.correlation_id_manager import CorrelationIdManager
from application.infrastructure.logging.logging_setup import (
    CorrelationIdFilter,
    configure_logging,
)


def _make_record() -> logging.LogRecord:
    return logging.LogRecord(
        name="test.logger",
        level=logging.DEBUG,
        pathname="",
        lineno=0,
        msg="test message",
        args=(),
        exc_info=None,
    )


class CorrelationIdFilterTests(unittest.TestCase):
    """Verify that CorrelationIdFilter injects or auto-initializes the CID onto log records."""

    def setUp(self) -> None:
        CorrelationIdManager.clear()

    def tearDown(self) -> None:
        CorrelationIdManager.clear()

    def test_filter_injects_active_correlation_id_onto_record(self) -> None:
        CorrelationIdManager.set_correlation_id("abc-123")
        record = _make_record()

        CorrelationIdFilter().filter(record)

        self.assertEqual(record.correlation_id, "abc-123")  # type: ignore[attr-defined]

    def test_filter_auto_initializes_new_cid_when_none_is_set(self) -> None:
        # No CID initialized — filter must create one instead of writing "-".
        # This is the Streamlit thread-pool scenario: a thread started before
        # configure_logging() was called inherits a context with no CID.
        record = _make_record()

        CorrelationIdFilter().filter(record)

        self.assertNotEqual(record.correlation_id, "-")  # type: ignore[attr-defined]
        self.assertIsNotNone(record.correlation_id)  # type: ignore[attr-defined]

    def test_filter_persists_auto_initialized_cid_within_the_same_context(self) -> None:
        # Once the filter creates a CID it must reuse it for all subsequent records
        # in the same execution context — not generate a fresh UUID per record.
        record_a = _make_record()
        record_b = _make_record()
        filt = CorrelationIdFilter()

        filt.filter(record_a)
        filt.filter(record_b)

        self.assertEqual(record_a.correlation_id, record_b.correlation_id)  # type: ignore[attr-defined]
        self.assertNotEqual(record_a.correlation_id, "-")  # type: ignore[attr-defined]

    def test_filter_always_returns_true(self) -> None:
        record = _make_record()

        result = CorrelationIdFilter().filter(record)

        self.assertTrue(result)

    def test_filter_reflects_updated_cid_when_overwritten_between_calls(self) -> None:
        CorrelationIdManager.set_correlation_id("first")
        record_a = _make_record()
        CorrelationIdFilter().filter(record_a)

        CorrelationIdManager.set_correlation_id("second")
        record_b = _make_record()
        CorrelationIdFilter().filter(record_b)

        self.assertEqual(record_a.correlation_id, "first")  # type: ignore[attr-defined]
        self.assertEqual(record_b.correlation_id, "second")  # type: ignore[attr-defined]

    def test_filter_generates_independent_cid_in_context_without_cid(self) -> None:
        # Simulates a Streamlit thread-pool thread (started before configure_logging).
        # Such a thread inherits a context with no CID; the filter must give it its own.
        CorrelationIdManager.set_correlation_id("main-cid")
        thread_results: list[str] = []

        def run_in_thread() -> None:
            # Clear the inherited CID to reproduce the thread-pool scenario.
            CorrelationIdManager.clear()
            record = _make_record()
            CorrelationIdFilter().filter(record)
            thread_results.append(record.correlation_id)  # type: ignore[attr-defined]

        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()

        self.assertEqual(len(thread_results), 1)
        self.assertNotEqual(thread_results[0], "-")
        self.assertNotEqual(thread_results[0], "main-cid")

    def test_filter_does_not_leak_auto_initialized_cid_to_parent_context(self) -> None:
        # A CID created inside a thread must not bleed into the calling context.
        main_cid_before = CorrelationIdManager.get_correlation_id()  # None after setUp

        def run_in_thread() -> None:
            CorrelationIdManager.clear()
            CorrelationIdFilter().filter(_make_record())

        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()

        self.assertEqual(CorrelationIdManager.get_correlation_id(), main_cid_before)


class ConfigureLoggingInitialCidTests(unittest.TestCase):
    """Verify that configure_logging initializes a CID for the initial execution context."""

    def setUp(self) -> None:
        CorrelationIdManager.clear()
        root = logging.getLogger()
        self._saved_handlers = root.handlers[:]
        self._saved_level = root.level

    def tearDown(self) -> None:
        CorrelationIdManager.clear()
        root = logging.getLogger()
        root.handlers.clear()
        root.handlers.extend(self._saved_handlers)
        root.setLevel(self._saved_level)

    def test_configure_logging_sets_correlation_id_when_none_exists(self) -> None:
        self.assertIsNone(CorrelationIdManager.get_correlation_id())

        configure_logging()

        self.assertIsNotNone(CorrelationIdManager.get_correlation_id())

    def test_configure_logging_does_not_overwrite_preexisting_correlation_id(self) -> None:
        CorrelationIdManager.set_correlation_id("preexisting-cid")

        configure_logging()

        self.assertEqual(CorrelationIdManager.get_correlation_id(), "preexisting-cid")

    def test_configure_logging_does_not_overwrite_scope_correlation_id(self) -> None:
        with CorrelationIdManager.scope() as scope_cid:
            configure_logging()

            self.assertEqual(CorrelationIdManager.get_correlation_id(), scope_cid)

    def test_log_record_carries_real_cid_after_configure_logging(self) -> None:
        configure_logging()
        expected_cid = CorrelationIdManager.get_correlation_id()
        record = _make_record()

        handler = logging.getLogger().handlers[0]
        for f in handler.filters:
            f.filter(record)

        self.assertEqual(record.correlation_id, expected_cid)  # type: ignore[attr-defined]
        self.assertNotEqual(record.correlation_id, "-")  # type: ignore[attr-defined]

    def test_log_record_carries_auto_initialized_cid_without_configure_logging(self) -> None:
        # Even without configure_logging(), the filter must not produce "-".
        # This covers fragment reruns in thread-pool threads that never saw configure_logging.
        record = _make_record()

        CorrelationIdFilter().filter(record)

        self.assertNotEqual(record.correlation_id, "-")  # type: ignore[attr-defined]
        self.assertIsNotNone(record.correlation_id)  # type: ignore[attr-defined]

    def test_initial_cid_is_a_non_empty_string(self) -> None:
        configure_logging()

        cid = CorrelationIdManager.get_correlation_id()

        self.assertIsInstance(cid, str)
        self.assertGreater(len(cid), 0)  # type: ignore[arg-type]
