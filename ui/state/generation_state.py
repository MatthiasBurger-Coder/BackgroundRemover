"""Generation counters for UI adapter lifecycle guards."""

from __future__ import annotations

import logging

import streamlit as st

LOGGER = logging.getLogger(__name__)


def bump_generation(field_name: str, reason: str) -> int:
    """Increment a named generation counter and log the reason."""
    next_value = int(st.session_state.get(field_name, 0)) + 1
    st.session_state[field_name] = next_value
    LOGGER.info("Generation bumped field=%s new_value=%s reason=%s", field_name, next_value, reason)
    return next_value


def bump_ui_generation(reason: str) -> int:
    return bump_generation("ui_generation", reason)


def bump_source_generation(reason: str) -> int:
    return bump_generation("source_generation", reason)


def bump_playback_generation(reason: str) -> int:
    return bump_generation("playback_generation", reason)


def bump_workbench_generation(reason: str) -> int:
    return bump_generation("workbench_generation", reason)
