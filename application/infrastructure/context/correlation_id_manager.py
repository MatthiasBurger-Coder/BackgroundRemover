from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import uuid4


class CorrelationIdManager:
    """Manage a correlation id for the current execution context.

    This implementation uses ``contextvars`` instead of thread-local storage,
    which keeps it safe for synchronous code, multithreading, and asyncio.
    """

    MDC_KEY = "correlationId"

    _correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)
    _ownership_stack: ContextVar[tuple[bool, ...]] = ContextVar("correlation_owner_stack", default=())

    @classmethod
    def init_correlation_id(cls) -> None:
        current = cls._correlation_id.get()
        ownership_stack = cls._ownership_stack.get()

        if current is None:
            cls._correlation_id.set(str(uuid4()))
            cls._ownership_stack.set((*ownership_stack, True))
            return

        cls._ownership_stack.set((*ownership_stack, False))

    @classmethod
    def clear_if_owned(cls) -> None:
        ownership_stack = cls._ownership_stack.get()
        if not ownership_stack:
            return

        owned = ownership_stack[-1]
        remaining_stack = ownership_stack[:-1]
        cls._ownership_stack.set(remaining_stack)

        if owned:
            cls._correlation_id.set(None)

    @classmethod
    def get_correlation_id(cls) -> str | None:
        return cls._correlation_id.get()

    @classmethod
    def set_correlation_id(cls, correlation_id: str) -> None:
        cls._correlation_id.set(correlation_id)

    @classmethod
    def clear(cls) -> None:
        cls._correlation_id.set(None)
        cls._ownership_stack.set(())

    @classmethod
    @contextmanager
    def scope(cls) -> Iterator[str]:
        cls.init_correlation_id()
        try:
            yield cls.get_correlation_id() or ""
        finally:
            cls.clear_if_owned()
