from __future__ import annotations

import logging

from application.infrastructure.logging.formatting import summarize_value_for_logging
from application.infrastructure.logging.level_logger import LevelLogger


class DebugLevelLogger(LevelLogger):
    def log_entry(
        self,
        logger: logging.Logger,
        method_name: str,
        args: tuple[object, ...],
        kwargs: dict[str, object],
    ) -> None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("→ Enter %s", method_name)
            logger.debug("  args=%s kwargs=%s", args, kwargs)

    def log_exit(
        self,
        logger: logging.Logger,
        method_name: str,
        duration_ms: float,
        result: object,
    ) -> None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("← Exit %s (%.3f ms)", method_name, duration_ms)
            logger.debug("  result=%r", summarize_value_for_logging(result))

    def log_exception(
        self,
        logger: logging.Logger,
        method_name: str,
        duration_ms: float,
        ex: BaseException,
    ) -> None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("✖ Exception in %s (%.3f ms)", method_name, duration_ms, exc_info=ex)
