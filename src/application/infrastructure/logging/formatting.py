from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

BOUND_SELF_NAMES = {"self", "cls"}


def prepare_arguments_for_logging(
    qualname: str,
    arg_names: tuple[str, ...],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    if not args or not arg_names:
        return (
            tuple(summarize_value_for_logging(argument) for argument in args),
            {key: summarize_value_for_logging(value) for key, value in kwargs.items()},
        )

    first_name = arg_names[0]
    prepared_args = args
    if first_name in BOUND_SELF_NAMES and qualname.count(".") >= 1:
        prepared_args = args[1:]

    return (
        tuple(summarize_value_for_logging(argument) for argument in prepared_args),
        {key: summarize_value_for_logging(value) for key, value in kwargs.items()},
    )


def summarize_value_for_logging(value: Any) -> Any:
    if isinstance(value, bytes):
        return f"<bytes len={len(value)}>"

    if is_dataclass(value) and not isinstance(value, type):
        summary: dict[str, Any] = {}
        for field in fields(value):
            summary[field.name] = summarize_value_for_logging(getattr(value, field.name))
        return {value.__class__.__name__: summary}

    if isinstance(value, tuple):
        return tuple(summarize_value_for_logging(item) for item in value)

    if isinstance(value, list):
        return [summarize_value_for_logging(item) for item in value]

    if isinstance(value, dict):
        return {
            key: summarize_value_for_logging(item)
            for key, item in value.items()
        }

    return value
