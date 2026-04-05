from __future__ import annotations

from application.infrastructure.logging.level_logger import LevelLogger
from application.infrastructure.logging.log_levels import LogLevel
from application.infrastructure.logging.strategies.debug_level_logger import DebugLevelLogger
from application.infrastructure.logging.strategies.error_level_logger import ErrorLevelLogger
from application.infrastructure.logging.strategies.info_level_logger import InfoLevelLogger
from application.infrastructure.logging.strategies.trace_level_logger import TraceLevelLogger
from application.infrastructure.logging.strategies.warn_level_logger import WarnLevelLogger


class LevelLoggerRegistry:
    def __init__(self) -> None:
        self._registry: dict[LogLevel, LevelLogger] = {
            LogLevel.TRACE: TraceLevelLogger(),
            LogLevel.DEBUG: DebugLevelLogger(),
            LogLevel.INFO: InfoLevelLogger(),
            LogLevel.WARN: WarnLevelLogger(),
            LogLevel.ERROR: ErrorLevelLogger(),
        }

    def get(self, level: LogLevel) -> LevelLogger:
        return self._registry.get(level, self._registry[LogLevel.DEBUG])
