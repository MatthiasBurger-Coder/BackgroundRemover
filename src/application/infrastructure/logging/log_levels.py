from __future__ import annotations

import logging
from enum import Enum
from typing import Any, cast

TRACE_NUMERIC_LEVEL = 5


class LogLevel(Enum):
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"

    @property
    def numeric_value(self) -> int:
        return {
            LogLevel.TRACE: TRACE_NUMERIC_LEVEL,
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARN: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
        }[self]


_TRACE_INSTALLED = False


def install_trace_level() -> None:
    global _TRACE_INSTALLED
    if _TRACE_INSTALLED:
        return

    logging.addLevelName(TRACE_NUMERIC_LEVEL, "TRACE")

    def trace(
        self: logging.Logger,
        message: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if self.isEnabledFor(TRACE_NUMERIC_LEVEL):
            self._log(TRACE_NUMERIC_LEVEL, message, args, **kwargs)

    cast(Any, logging.Logger).trace = trace
    _TRACE_INSTALLED = True
