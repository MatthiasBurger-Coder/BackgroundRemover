"""Request lifecycle helpers for API correlation-aware logging."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request

from application.infrastructure.context.correlation_id_manager import CorrelationIdManager

LOGGER = logging.getLogger(__name__)


async def run_with_action_correlation(
    request: Request,
    call_next: Callable[[Request], Awaitable[object]],
) -> object:
    """Execute one request lifecycle under one dedicated correlation id."""

    with CorrelationIdManager.scope() as correlation_id:
        start = perf_counter()
        LOGGER.info(
            "Action lifecycle started method=%s path=%s cid=%s",
            request.method,
            request.url.path,
            correlation_id,
        )
        try:
            response = await call_next(request)
        except BaseException:
            duration_ms = (perf_counter() - start) * 1000.0
            LOGGER.exception(
                "Action lifecycle failed method=%s path=%s durationMs=%.2f cid=%s",
                request.method,
                request.url.path,
                duration_ms,
                correlation_id,
            )
            raise

        duration_ms = (perf_counter() - start) * 1000.0
        LOGGER.info(
            "Action lifecycle finished method=%s path=%s status=%s durationMs=%.2f cid=%s",
            request.method,
            request.url.path,
            getattr(response, "status_code", "-"),
            duration_ms,
            correlation_id,
        )
        return response
