from __future__ import annotations

import logging

from application.infrastructure.logging.level_logger import LevelLogger


class ErrorLevelLogger(LevelLogger):
    def log_entry(
        self,
        logger: logging.Logger,
        method_name: str,
        args: tuple[object, ...],
        kwargs: dict[str, object],
    ) -> None:
        return None

    def log_exit(
        self,
        logger: logging.Logger,
        method_name: str,
        duration_ms: float,
        result: object,
    ) -> None:
        return None

    def log_exception(
        self,
        logger: logging.Logger,
        method_name: str,
        duration_ms: float,
        ex: BaseException,
    ) -> None:
        if logger.isEnabledFor(logging.ERROR):
            logger.error("✖ Exception in %s (%.3f ms)", method_name, duration_ms, exc_info=ex)
