from __future__ import annotations

import logging

from src.application.infrastructure.logging.formatting import summarize_value_for_logging
from src.application.infrastructure.logging.level_logger import LevelLogger


class TraceLevelLogger(LevelLogger):
    def log_entry(
        self,
        logger: logging.Logger,
        method_name: str,
        args: tuple[object, ...],
        kwargs: dict[str, object],
    ) -> None:
        if logger.isEnabledFor(5):
            trace_logger = getattr(logger, "trace", None)
            if callable(trace_logger):
                trace_logger("→ Enter %s", method_name)
                trace_logger("  args=%s kwargs=%s", args, kwargs)

    def log_exit(
        self,
        logger: logging.Logger,
        method_name: str,
        duration_ms: float,
        result: object,
    ) -> None:
        if logger.isEnabledFor(5):
            trace_logger = getattr(logger, "trace", None)
            if callable(trace_logger):
                trace_logger("← Exit %s (%.3f ms)", method_name, duration_ms)
                trace_logger("  result=%r", summarize_value_for_logging(result))

    def log_exception(
        self,
        logger: logging.Logger,
        method_name: str,
        duration_ms: float,
        ex: BaseException,
    ) -> None:
        if logger.isEnabledFor(5):
            trace_logger = getattr(logger, "trace", None)
            if callable(trace_logger):
                trace_logger("✖ Exception in %s (%.3f ms)", method_name, duration_ms, exc_info=ex)
