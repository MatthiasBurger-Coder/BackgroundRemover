"""Tests for correlation lifecycle ownership and logging setup."""

from __future__ import annotations

import logging
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


class CorrelationIdManagerScopeTests(unittest.TestCase):
    """Protect explicit action lifecycle correlation semantics."""

    def setUp(self) -> None:
        CorrelationIdManager.clear()

    def tearDown(self) -> None:
        CorrelationIdManager.clear()

    def test_scope_creates_temporary_cid_when_none_is_bound(self) -> None:
        self.assertIsNone(CorrelationIdManager.get_correlation_id())

        with CorrelationIdManager.scope() as correlation_id:
            self.assertEqual(CorrelationIdManager.get_correlation_id(), correlation_id)
            self.assertIsInstance(correlation_id, str)
            self.assertGreater(len(correlation_id), 0)

        self.assertIsNone(CorrelationIdManager.get_correlation_id())

    def test_scope_reuses_existing_lifecycle_cid(self) -> None:
        with CorrelationIdManager.lifecycle_scope() as lifecycle_cid:
            with CorrelationIdManager.scope() as nested_cid:
                self.assertEqual(nested_cid, lifecycle_cid)
                self.assertEqual(CorrelationIdManager.get_correlation_id(), lifecycle_cid)

            self.assertEqual(CorrelationIdManager.get_correlation_id(), lifecycle_cid)

        self.assertIsNone(CorrelationIdManager.get_correlation_id())

    def test_lifecycle_scope_creates_fresh_cid_and_restores_previous_context(self) -> None:
        CorrelationIdManager.set_correlation_id("outer-cid")

        with CorrelationIdManager.lifecycle_scope() as lifecycle_cid:
            self.assertNotEqual(lifecycle_cid, "outer-cid")
            self.assertEqual(CorrelationIdManager.get_correlation_id(), lifecycle_cid)

        self.assertEqual(CorrelationIdManager.get_correlation_id(), "outer-cid")


class CorrelationIdFilterTests(unittest.TestCase):
    """Verify that log records reflect the active lifecycle instead of creating one implicitly."""

    def setUp(self) -> None:
        CorrelationIdManager.clear()

    def tearDown(self) -> None:
        CorrelationIdManager.clear()

    def test_filter_injects_active_correlation_id_onto_record(self) -> None:
        CorrelationIdManager.set_correlation_id("abc-123")
        record = _make_record()

        CorrelationIdFilter().filter(record)

        self.assertEqual(record.correlation_id, "abc-123")  # type: ignore[attr-defined]

    def test_filter_writes_placeholder_when_no_lifecycle_is_bound(self) -> None:
        record = _make_record()

        CorrelationIdFilter().filter(record)

        self.assertEqual(record.correlation_id, "-")  # type: ignore[attr-defined]
        self.assertIsNone(CorrelationIdManager.get_correlation_id())

    def test_filter_always_returns_true(self) -> None:
        record = _make_record()

        result = CorrelationIdFilter().filter(record)

        self.assertTrue(result)


class ConfigureLoggingTests(unittest.TestCase):
    """Verify that logging setup stays correlation-neutral until a lifecycle is explicitly started."""

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

    def test_configure_logging_does_not_initialize_correlation_context(self) -> None:
        self.assertIsNone(CorrelationIdManager.get_correlation_id())

        configure_logging()

        self.assertIsNone(CorrelationIdManager.get_correlation_id())

    def test_configure_logging_preserves_existing_correlation_id(self) -> None:
        CorrelationIdManager.set_correlation_id("preexisting-cid")

        configure_logging()

        self.assertEqual(CorrelationIdManager.get_correlation_id(), "preexisting-cid")

    def test_configured_handler_uses_active_lifecycle_cid(self) -> None:
        configure_logging()
        handler = logging.getLogger().handlers[0]
        record = _make_record()

        with CorrelationIdManager.lifecycle_scope() as expected_cid:
            for installed_filter in handler.filters:
                installed_filter.filter(record)

        self.assertEqual(record.correlation_id, expected_cid)  # type: ignore[attr-defined]

    def test_configured_handler_uses_placeholder_without_lifecycle(self) -> None:
        configure_logging()
        handler = logging.getLogger().handlers[0]
        record = _make_record()

        for installed_filter in handler.filters:
            installed_filter.filter(record)

        self.assertEqual(record.correlation_id, "-")  # type: ignore[attr-defined]
