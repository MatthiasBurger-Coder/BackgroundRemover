from __future__ import annotations

import logging
from abc import ABC, abstractmethod


class LevelLogger(ABC):
    @abstractmethod
    def log_entry(
        self,
        logger: logging.Logger,
        method_name: str,
        args: tuple[object, ...],
        kwargs: dict[str, object],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def log_exit(
        self,
        logger: logging.Logger,
        method_name: str,
        duration_ms: float,
        result: object,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def log_exception(
        self,
        logger: logging.Logger,
        method_name: str,
        duration_ms: float,
        ex: BaseException,
    ) -> None:
        raise NotImplementedError
