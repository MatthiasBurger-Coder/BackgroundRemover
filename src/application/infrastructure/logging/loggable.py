from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from time import perf_counter
from typing import Any, TypeVar, cast

from src.application.infrastructure.context.correlation_id_manager import CorrelationIdManager
from src.application.infrastructure.logging.formatting import prepare_arguments_for_logging
from src.application.infrastructure.logging.level_logger_registry import LevelLoggerRegistry
from src.application.infrastructure.logging.log_levels import LogLevel, install_trace_level

F = TypeVar("F", bound=Callable[..., Any])
_LOGGABLE_MARKER = "__loggable_level__"


def loggable(level: LogLevel = LogLevel.DEBUG) -> Callable[[type[Any] | F], type[Any] | F]:
    install_trace_level()
    registry = LevelLoggerRegistry()

    def decorator(target: type[Any] | F) -> type[Any] | F:
        if inspect.isclass(target):
            return _decorate_class(target, level, registry)

        return _decorate_callable(target, level, registry)

    return decorator


def _decorate_class(target_class: type[Any], level: LogLevel, registry: LevelLoggerRegistry) -> type[Any]:
    for attribute_name, attribute_value in vars(target_class).items():
        if attribute_name.startswith("_"):
            continue
        if not callable(attribute_value):
            continue
        if getattr(attribute_value, _LOGGABLE_MARKER, None) is not None:
            continue

        decorated_callable = _decorate_callable(attribute_value, level, registry)
        setattr(target_class, attribute_name, decorated_callable)

    setattr(target_class, _LOGGABLE_MARKER, level)
    return target_class


def _decorate_callable[CallableT: Callable[..., Any]](
    target: CallableT,
    level: LogLevel,
    registry: LevelLoggerRegistry,
) -> CallableT:
    signature = inspect.signature(target)
    arg_names = tuple(signature.parameters.keys())
    level_logger = registry.get(level)

    if inspect.iscoroutinefunction(target):
        @wraps(target)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return await _invoke_async(target, level, level_logger, arg_names, args, kwargs)

        setattr(async_wrapper, _LOGGABLE_MARKER, level)
        return cast(CallableT, async_wrapper)

    @wraps(target)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        return _invoke_sync(target, level, level_logger, arg_names, args, kwargs)

    setattr(sync_wrapper, _LOGGABLE_MARKER, level)
    return cast(CallableT, sync_wrapper)


def _invoke_sync(
    target: Callable[..., Any],
    level: LogLevel,
    level_logger: Any,
    arg_names: tuple[str, ...],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    with CorrelationIdManager.scope():
        logger, method_name, prepared_args, prepared_kwargs = _prepare_invocation_context(target, arg_names, args, kwargs)
        start = perf_counter()
        try:
            level_logger.log_entry(logger, method_name, prepared_args, prepared_kwargs)
            result = target(*args, **kwargs)
            duration_ms = (perf_counter() - start) * 1000.0
            level_logger.log_exit(logger, method_name, duration_ms, result)
            return result
        except BaseException as ex:
            duration_ms = (perf_counter() - start) * 1000.0
            level_logger.log_exception(logger, method_name, duration_ms, ex)
            raise


async def _invoke_async(
    target: Callable[..., Awaitable[Any]],
    level: LogLevel,
    level_logger: Any,
    arg_names: tuple[str, ...],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    with CorrelationIdManager.scope():
        logger, method_name, prepared_args, prepared_kwargs = _prepare_invocation_context(target, arg_names, args, kwargs)
        start = perf_counter()
        try:
            level_logger.log_entry(logger, method_name, prepared_args, prepared_kwargs)
            result = await target(*args, **kwargs)
            duration_ms = (perf_counter() - start) * 1000.0
            level_logger.log_exit(logger, method_name, duration_ms, result)
            return result
        except BaseException as ex:
            duration_ms = (perf_counter() - start) * 1000.0
            level_logger.log_exception(logger, method_name, duration_ms, ex)
            raise


def _prepare_invocation_context(
    target: Callable[..., Any],
    arg_names: tuple[str, ...],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> tuple[logging.Logger, str, tuple[Any, ...], dict[str, Any]]:
    logger_name = _resolve_logger_name(target, args)
    method_name = _resolve_method_name(target, args)
    prepared_args, prepared_kwargs = prepare_arguments_for_logging(target.__qualname__, arg_names, args, kwargs)
    logger = logging.getLogger(logger_name)
    return logger, method_name, prepared_args, prepared_kwargs


def _resolve_logger_name(target: Callable[..., Any], args: tuple[Any, ...]) -> str:
    if args:
        first = args[0]
        if target.__qualname__.startswith(f"{first.__class__.__name__}."):
            return f"{first.__class__.__module__}.{first.__class__.__name__}"

    return target.__module__


def _resolve_method_name(target: Callable[..., Any], args: tuple[Any, ...]) -> str:
    qualname = target.__qualname__

    if args:
        first = args[0]
        class_name = first.__class__.__name__
        if class_name in qualname.split("."):
            return f"{class_name}.{target.__name__}"

    return target.__name__
