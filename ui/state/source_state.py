"""Source context helpers for the Streamlit UI adapter."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import streamlit as st
from application.domain.errors.video_asset_errors import VideoAssetNotFoundError
from application.infrastructure.wiring.video_asset_backend import get_video_asset_backend

from ui.state.generation_state import (
    bump_playback_generation,
    bump_source_generation,
    bump_ui_generation,
    bump_workbench_generation,
)
from ui.state.playback_state import reset_playback_state
from ui.state.video_metadata_state import (
    apply_video_metadata_state,
    has_complete_video_metadata,
    refresh_video_metadata_state,
)
from ui.state.workbench_state import reset_workbench_frame_state

LOGGER = logging.getLogger(__name__)


def synchronize_explicit_source_state() -> None:
    """Backfill explicit source fields from legacy session-state values."""
    if st.session_state.active_asset_id is None and st.session_state.asset_id is not None:
        st.session_state.active_asset_id = st.session_state.asset_id
    if st.session_state.active_video_name is None and st.session_state.video_name != "No video selected":
        st.session_state.active_video_name = st.session_state.video_name
    if st.session_state.active_source_payload is None and st.session_state.source_video_bytes is not None:
        st.session_state.active_source_payload = st.session_state.source_video_bytes
    if st.session_state.source_fingerprint is None and st.session_state.video_upload_signature is not None:
        st.session_state.source_fingerprint = st.session_state.video_upload_signature


def register_video_selection(uploaded_file: Any | None) -> bool:
    """Register, reuse, or refresh the active source selection for the operator UI."""
    if uploaded_file is None:
        if has_active_source():
            LOGGER.info(
                "Source removal skipped because uploader is empty asset_id=%s video_name=%s",
                current_active_asset_id(),
                current_active_video_name(),
            )
            st.session_state.last_action = "Kept active source while uploader was empty"
        return False

    uploaded_bytes = uploaded_file.getvalue()
    upload_signature = hashlib.sha256(uploaded_bytes).hexdigest()
    backend = get_video_asset_backend()
    if (
        upload_signature == current_source_fingerprint()
        and uploaded_file.name == current_active_video_name()
        and current_active_asset_id() is not None
    ):
        _refresh_source_binding(
            video_name=uploaded_file.name,
            mime_type=uploaded_file.type or "video/mp4",
            source_video_bytes=uploaded_bytes,
            upload_signature=upload_signature,
        )
        if has_complete_video_metadata():
            LOGGER.info(
                "Reusing active source asset_id=%s video_name=%s fingerprint=%s",
                current_active_asset_id(),
                uploaded_file.name,
                upload_signature,
            )
            st.session_state.last_action = f"Reused source asset {uploaded_file.name}"
            return False
        try:
            LOGGER.debug(
                "Refreshing existing source selection asset_id=%s video_name=%s",
                current_active_asset_id(),
                uploaded_file.name,
            )
            metadata = backend.get_video_asset_metadata.execute(current_active_asset_id())
            _activate_source_identity(metadata.asset_id)
            refresh_video_metadata_state(metadata=metadata)
            return False
        except VideoAssetNotFoundError:
            LOGGER.warning(
                "Stored asset metadata missing; re-registering uploaded file video_name=%s asset_id=%s",
                uploaded_file.name,
                current_active_asset_id(),
            )

    metadata = backend.register_video_asset.execute(
        filename=uploaded_file.name,
        video_bytes=uploaded_bytes,
        mime_type=uploaded_file.type,
    )
    _refresh_source_binding(
        video_name=metadata.filename,
        mime_type=uploaded_file.type or "video/mp4",
        source_video_bytes=uploaded_bytes,
        upload_signature=upload_signature,
    )
    _activate_source_identity(metadata.asset_id)
    apply_video_metadata_state(
        metadata=metadata,
        reset_prompts=True,
    )
    bump_ui_generation("source_registered")
    bump_source_generation("source_registered")
    bump_playback_generation("source_registered")
    bump_workbench_generation("source_registered")
    LOGGER.info(
        "Source registered asset_id=%s video_name=%s frame_count=%s fps=%.3f fingerprint=%s",
        metadata.asset_id,
        metadata.filename,
        metadata.frame_count,
        metadata.fps,
        upload_signature,
    )
    st.session_state.last_action = f"Registered backend source asset {metadata.filename}"
    return True


def remove_active_video_source() -> bool:
    """Remove the active source selection via an explicit user action."""
    if not has_active_source():
        LOGGER.info("Source removal skipped because no active source exists")
        st.session_state.last_action = "Skipped source removal"
        return False

    LOGGER.info(
        "Source removal requested asset_id=%s video_name=%s",
        current_active_asset_id(),
        current_active_video_name(),
    )
    _clear_video_asset_state()
    bump_ui_generation("source_removed")
    bump_source_generation("source_removed")
    bump_playback_generation("source_removed")
    bump_workbench_generation("source_removed")
    st.session_state.last_action = "Removed source asset"
    LOGGER.info("Source removal executed")
    return True


def get_source_upload_widget_key() -> str:
    """Return a stable uploader key that resets only on UI generation changes."""
    return f"source_video_upload_{int(st.session_state.ui_generation)}"


def has_active_source() -> bool:
    return current_active_asset_id() is not None


def current_active_asset_id() -> str | None:
    return st.session_state.get("active_asset_id") or st.session_state.get("asset_id")


def current_active_video_name() -> str | None:
    return st.session_state.get("active_video_name") or st.session_state.get("video_name")


def current_source_fingerprint() -> str | None:
    return st.session_state.get("source_fingerprint") or st.session_state.get("video_upload_signature")


def _activate_source_identity(asset_id: str) -> None:
    st.session_state.active_asset_id = asset_id
    st.session_state.asset_id = asset_id


def _refresh_source_binding(
    *,
    video_name: str,
    mime_type: str | None,
    source_video_bytes: bytes | None,
    upload_signature: str | None,
) -> None:
    st.session_state.active_video_name = video_name
    st.session_state.active_source_payload = source_video_bytes
    st.session_state.source_fingerprint = upload_signature
    st.session_state.video_name = video_name
    st.session_state.video_mime_type = mime_type
    st.session_state.source_video_bytes = source_video_bytes
    st.session_state.video_upload_signature = upload_signature


def _clear_video_asset_state() -> None:
    LOGGER.debug("Resetting video asset state")
    st.session_state.video_loaded = False
    st.session_state.video_name = "No video selected"
    st.session_state.video_mime_type = None
    st.session_state.source_video_bytes = None
    st.session_state.video_upload_signature = None
    st.session_state.active_asset_id = None
    st.session_state.active_video_name = None
    st.session_state.active_source_payload = None
    st.session_state.source_fingerprint = None
    st.session_state.asset_id = None
    st.session_state.video_fps = 0.0
    st.session_state.video_frame_count = 0
    st.session_state.video_duration_seconds = 0.0
    st.session_state.video_width = 0
    st.session_state.video_height = 0
    reset_playback_state()
    reset_workbench_frame_state(reset_position=True)
