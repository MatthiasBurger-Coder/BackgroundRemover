from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from uuid import uuid4


class CorrelationIdManager:
    """Manage a correlation id for the current execution context.

    This implementation uses ``contextvars`` instead of thread-local storage,
    which keeps it safe for synchronous code, multithreading, and asyncio.
    """

    MDC_KEY = "correlationId"

    _correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)

    @classmethod
    def _generate_correlation_id(cls) -> str:
        return str(uuid4())

    @classmethod
    def init_correlation_id(cls) -> None:
        """Backwards-compatible helper for legacy callers.

        The request lifecycle should prefer ``lifecycle_scope()`` so one
        frontend action owns exactly one cid from start to finish.
        """

        if cls._correlation_id.get() is None:
            cls._correlation_id.set(cls._generate_correlation_id())

    @classmethod
    def begin_lifecycle(cls, correlation_id: str | None = None) -> Token[str | None]:
        """Bind a fresh correlation id for one explicit action lifecycle."""

        return cls._correlation_id.set(correlation_id or cls._generate_correlation_id())

    @classmethod
    def end_lifecycle(cls, token: Token[str | None]) -> None:
        cls._correlation_id.reset(token)

    @classmethod
    def get_correlation_id(cls) -> str | None:
        return cls._correlation_id.get()

    @classmethod
    def set_correlation_id(cls, correlation_id: str) -> None:
        cls._correlation_id.set(correlation_id)

    @classmethod
    def clear(cls) -> None:
        cls._correlation_id.set(None)

    @classmethod
    @contextmanager
    def lifecycle_scope(cls, correlation_id: str | None = None) -> Iterator[str]:
        """Create and own a correlation id for one complete action lifecycle."""

        token = cls.begin_lifecycle(correlation_id)
        try:
            yield cls.get_correlation_id() or ""
        finally:
            cls.end_lifecycle(token)

    @classmethod
    @contextmanager
    def scope(cls) -> Iterator[str]:
        """Reuse the active lifecycle id or create a temporary nested one."""

        current = cls.get_correlation_id()
        if current is not None:
            yield current
            return

        with cls.lifecycle_scope() as correlation_id:
            yield correlation_id
