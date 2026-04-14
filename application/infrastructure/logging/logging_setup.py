from __future__ import annotations

import logging
from collections.abc import Iterable

from application.infrastructure.context.correlation_id_manager import CorrelationIdManager
from application.infrastructure.logging.log_levels import LogLevel, install_trace_level


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = CorrelationIdManager.get_correlation_id() or "-"
        return True


DEFAULT_FORMAT = (
    "%(asctime)s %(levelname)-8s [cid=%(correlation_id)s] %(name)s - %(message)s"
)


def configure_logging(
    level: LogLevel = LogLevel.DEBUG,
    logger_names: Iterable[str] | None = None,
) -> None:
    install_trace_level()

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(DEFAULT_FORMAT))
    handler.addFilter(CorrelationIdFilter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level.numeric_value)

    if logger_names:
        for logger_name in logger_names:
            named_logger = logging.getLogger(logger_name)
            named_logger.setLevel(level.numeric_value)
