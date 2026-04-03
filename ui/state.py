"""Session state helpers for the backend-assisted Streamlit operator UI."""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

import streamlit as st
from src.application.adapters.incoming.ui.playback_session import (
    PlaybackProgress,
    advance_playback_position,
    build_navigation_position,
    start_playback,
    step_navigation_position,
    stop_playback,
)
from src.application.domain.errors.video_asset_errors import (
    VideoAssetNotFoundError,
    VideoFrameExtractionError,
)
from src.application.domain.model.video_asset import VideoAssetMetadata
from src.application.infrastructure.wiring.video_asset_backend import get_video_asset_backend

from ui.mock_data import PromptEntry

LOGGER = logging.getLogger(__name__)


def initialize_state() -> None:
    defaults: dict[str, Any] = {
        "prompt_mode": "foreground",
        "prompt_x": 640,
        "prompt_y": 320,
        "prompt_entries": [],
        "preview_generation": 3,
        "mask_threshold": 0.62,
        "mask_feather": 8,
        "mask_invert": False,
        "show_debug_overlay": True,
        "selected_error_index": 0,
        "video_loaded": False,
        "video_name": "No video selected",
        "video_mime_type": None,
        "source_video_bytes": None,
        "video_upload_signature": None,
        "active_asset_id": None,
        "active_video_name": None,
        "active_source_payload": None,
        "source_fingerprint": None,
        "asset_id": None,
        "video_fps": 0.0,
        "video_frame_count": 0,
        "video_duration_seconds": 0.0,
        "video_width": 0,
        "video_height": 0,
        "current_frame_index": 0,
        "current_frame_timestamp_seconds": 0.0,
        "current_frame_image_bytes": None,
        "current_frame_image_mime_type": None,
        "current_frame_width": 0,
        "current_frame_height": 0,
        "current_frame_request_key": None,
        "frame_error_message": None,
        "playback_running": False,
        "playback_anchor_frame_index": None,
        "playback_started_at_seconds": None,
        "ui_generation": 0,
        "playback_generation": 0,
        "last_action": "UI session initialized",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    _synchronize_explicit_source_state()
    LOGGER.debug("Session state initialized video_loaded=%s asset_id=%s", st.session_state.video_loaded, st.session_state.asset_id)


def register_video_selection(uploaded_file: Any | None) -> bool:
    if uploaded_file is None:
        if _has_active_source():
            LOGGER.info(
                "Source removal skipped because uploader is empty asset_id=%s video_name=%s",
                _current_active_asset_id(),
                _current_active_video_name(),
            )
            st.session_state.last_action = "Kept active source while uploader was empty"
        return False

    uploaded_bytes = uploaded_file.getvalue()
    upload_signature = hashlib.sha256(uploaded_bytes).hexdigest()
    backend = get_video_asset_backend()
    if (
        upload_signature == _current_source_fingerprint()
        and uploaded_file.name == _current_active_video_name()
        and _current_active_asset_id() is not None
    ):
        _refresh_source_binding(
            video_name=uploaded_file.name,
            mime_type=uploaded_file.type or "video/mp4",
            source_video_bytes=uploaded_bytes,
            upload_signature=upload_signature,
        )
        if _has_complete_video_metadata():
            LOGGER.info(
                "Reusing active source asset_id=%s video_name=%s fingerprint=%s",
                _current_active_asset_id(),
                uploaded_file.name,
                upload_signature,
            )
            st.session_state.last_action = f"Reused source asset {uploaded_file.name}"
            return False
        try:
            LOGGER.debug(
                "Refreshing existing source selection asset_id=%s video_name=%s",
                _current_active_asset_id(),
                uploaded_file.name,
            )
            metadata = backend.get_video_asset_metadata.execute(_current_active_asset_id())
            _refresh_video_metadata(
                metadata=metadata,
                mime_type=uploaded_file.type or "video/mp4",
                source_video_bytes=uploaded_bytes,
                upload_signature=upload_signature,
            )
            return False
        except VideoAssetNotFoundError:
            LOGGER.warning(
                "Stored asset metadata missing; re-registering uploaded file video_name=%s asset_id=%s",
                uploaded_file.name,
                _current_active_asset_id(),
            )
            pass

    metadata = backend.register_video_asset.execute(
        filename=uploaded_file.name,
        video_bytes=uploaded_bytes,
        mime_type=uploaded_file.type,
    )
    _apply_video_metadata(
        metadata=metadata,
        mime_type=uploaded_file.type or "video/mp4",
        source_video_bytes=uploaded_bytes,
        upload_signature=upload_signature,
        reset_prompts=True,
    )
    _bump_ui_generation("source_registered")
    _bump_playback_generation("source_registered")
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
    if not _has_active_source():
        LOGGER.info("Source removal skipped because no active source exists")
        st.session_state.last_action = "Skipped source removal"
        return False

    LOGGER.info(
        "Source removal requested asset_id=%s video_name=%s",
        _current_active_asset_id(),
        _current_active_video_name(),
    )
    _clear_video_asset_state()
    _bump_ui_generation("source_removed")
    _bump_playback_generation("source_removed")
    st.session_state.last_action = "Removed source asset"
    LOGGER.info("Source removal executed")
    return True


def sync_playback_position(now_seconds: float | None = None) -> None:
    if not st.session_state.playback_running:
        return

    previous_frame_index = int(st.session_state.current_frame_index)
    was_running = bool(st.session_state.playback_running)
    progress = advance_playback_position(
        playback_running=st.session_state.playback_running,
        current_frame_index=st.session_state.current_frame_index,
        frame_count=st.session_state.video_frame_count,
        fps=st.session_state.video_fps,
        playback_started_at_seconds=st.session_state.playback_started_at_seconds,
        playback_anchor_frame_index=st.session_state.playback_anchor_frame_index,
        now_seconds=time.monotonic() if now_seconds is None else now_seconds,
    )
    _apply_playback_progress(progress)
    st.session_state.current_frame_request_key = None
    st.session_state.frame_error_message = None
    if was_running and not progress.playback_running:
        _bump_playback_generation("playback_stopped")
    LOGGER.debug(
        "Synchronized playback frame_index=%s previous_frame_index=%s playback_running=%s",
        progress.frame_index,
        previous_frame_index,
        progress.playback_running,
    )
    if progress.playback_running:
        st.session_state.last_action = f"Playback running at frame {progress.frame_index:04d}"
    else:
        st.session_state.last_action = f"Playback paused at frame {progress.frame_index:04d}"


def ensure_current_frame_loaded() -> None:
    active_asset_id = _current_active_asset_id()
    if not st.session_state.video_loaded or active_asset_id is None:
        st.session_state.current_frame_image_bytes = None
        st.session_state.current_frame_image_mime_type = None
        st.session_state.current_frame_request_key = None
        st.session_state.frame_error_message = None
        return

    frame_index = clamp_current_frame_index(st.session_state.current_frame_index)
    request_key = (active_asset_id, frame_index)
    if request_key == st.session_state.current_frame_request_key and st.session_state.current_frame_image_bytes:
        LOGGER.debug("Skipping frame reload for cached request asset_id=%s frame_index=%s", active_asset_id, frame_index)
        return

    backend = get_video_asset_backend()
    try:
        LOGGER.debug("Loading frame asset_id=%s frame_index=%s", active_asset_id, frame_index)
        frame = backend.get_video_frame.execute(
            asset_id=active_asset_id,
            frame_index=frame_index,
        )
    except VideoFrameExtractionError as error:
        st.session_state.current_frame_image_bytes = None
        st.session_state.current_frame_image_mime_type = None
        st.session_state.current_frame_request_key = None
        st.session_state.playback_running = False
        st.session_state.playback_anchor_frame_index = None
        st.session_state.playback_started_at_seconds = None
        st.session_state.frame_error_message = str(error)
        st.session_state.last_action = "Frame loading failed"
        _bump_playback_generation("frame_load_failed")
        LOGGER.exception("Frame loading failed asset_id=%s frame_index=%s", active_asset_id, frame_index)
        return

    st.session_state.current_frame_index = frame.frame_index
    st.session_state.current_frame_timestamp_seconds = frame.timestamp_seconds
    st.session_state.current_frame_image_bytes = frame.image_bytes
    st.session_state.current_frame_image_mime_type = frame.mime_type
    st.session_state.current_frame_width = frame.width
    st.session_state.current_frame_height = frame.height
    st.session_state.current_frame_request_key = request_key
    st.session_state.frame_error_message = None
    LOGGER.debug(
        "Loaded frame asset_id=%s resolved_frame_index=%s timestamp=%.3f size=%sx%s",
        active_asset_id,
        frame.frame_index,
        frame.timestamp_seconds,
        frame.width,
        frame.height,
    )


def clamp_current_frame_index(frame_index: int) -> int:
    frame_count = int(st.session_state.video_frame_count)
    if frame_count <= 0:
        return 0
    return max(0, min(int(frame_index), frame_count - 1))


def sync_current_frame_index() -> None:
    set_current_frame_index(st.session_state.current_frame_index)


def set_current_frame_index(frame_index: int) -> None:
    progress = build_navigation_position(
        frame_index=frame_index,
        frame_count=st.session_state.video_frame_count,
        fps=st.session_state.video_fps,
    )
    _apply_playback_progress(progress)
    st.session_state.current_frame_request_key = None
    st.session_state.frame_error_message = None
    LOGGER.info("Selected frame frame_index=%s time_seconds=%.3f", progress.frame_index, progress.time_seconds)
    st.session_state.last_action = f"Selected frame {progress.frame_index:04d}"


def jump_to_first_frame() -> None:
    set_current_frame_index(0)


def jump_to_last_frame() -> None:
    if st.session_state.video_frame_count <= 0:
        return
    set_current_frame_index(st.session_state.video_frame_count - 1)


def step_current_frame(step: int) -> None:
    progress = step_navigation_position(
        current_frame_index=st.session_state.current_frame_index,
        step=step,
        frame_count=st.session_state.video_frame_count,
        fps=st.session_state.video_fps,
    )
    _apply_playback_progress(progress)
    st.session_state.current_frame_request_key = None
    st.session_state.frame_error_message = None
    st.session_state.last_action = f"Selected frame {progress.frame_index:04d}"


def toggle_playback() -> None:
    if not st.session_state.video_loaded or st.session_state.video_frame_count <= 0:
        LOGGER.warning("Ignoring playback toggle without active video")
        return

    now_seconds = time.monotonic()
    was_running = bool(st.session_state.playback_running)
    if st.session_state.playback_running:
        sync_playback_position(now_seconds=now_seconds)
        progress = stop_playback(
            current_frame_index=st.session_state.current_frame_index,
            frame_count=st.session_state.video_frame_count,
            fps=st.session_state.video_fps,
        )
    else:
        progress = start_playback(
            current_frame_index=st.session_state.current_frame_index,
            frame_count=st.session_state.video_frame_count,
            fps=st.session_state.video_fps,
            now_seconds=now_seconds,
        )

    _apply_playback_progress(progress)
    st.session_state.current_frame_request_key = None
    st.session_state.frame_error_message = None
    if not was_running and progress.playback_running:
        _bump_playback_generation("playback_started")
    elif was_running and not progress.playback_running:
        _bump_playback_generation("playback_stopped")
    state_label = "Running" if progress.playback_running else "Paused"
    LOGGER.info(
        "Playback toggled new_state=%s frame_index=%s anchor=%s started_at=%s",
        state_label.lower(),
        progress.frame_index,
        progress.playback_anchor_frame_index,
        progress.playback_started_at_seconds,
    )
    st.session_state.last_action = f"Playback {state_label.lower()} at frame {progress.frame_index:04d}"


def get_playback_interval_seconds() -> float:
    fps = float(st.session_state.video_fps)
    if fps <= 0:
        return 0.25
    preview_fps = min(fps, 4.0)
    return max(1.0 / preview_fps, 0.15)


def get_source_upload_widget_key() -> str:
    return f"source_video_upload_{int(st.session_state.ui_generation)}"


def add_prompt() -> None:
    new_identifier = len(st.session_state.prompt_entries) + 1
    frame_index = int(st.session_state.current_frame_index)
    timecode = format_timecode(st.session_state.current_frame_timestamp_seconds)
    prompt = PromptEntry(
        identifier=new_identifier,
        mode=st.session_state.prompt_mode,
        frame_index=frame_index,
        frame_label=f"Frame {frame_index:04d} | {timecode}",
        x=int(st.session_state.prompt_x),
        y=int(st.session_state.prompt_y),
        source="Operator input",
    )
    st.session_state.prompt_entries = [*st.session_state.prompt_entries, prompt]
    st.session_state.last_action = (
        f"Added {prompt.mode} prompt at ({prompt.x}, {prompt.y}) on frame {prompt.frame_index:04d}"
    )


def clear_prompts() -> None:
    st.session_state.prompt_entries = []
    st.session_state.last_action = "Cleared all prompt entries"


def refresh_preview() -> None:
    st.session_state.preview_generation += 1
    LOGGER.info("Queued preview refresh generation=%s", st.session_state.preview_generation)
    st.session_state.last_action = f"Queued placeholder preview refresh #{st.session_state.preview_generation}"


def set_selected_error(index: int) -> None:
    st.session_state.selected_error_index = index
    st.session_state.last_action = f"Focused failure case #{index + 1}"


def get_prompt_rows(prompt_entries: list[PromptEntry]) -> list[dict[str, str | int]]:
    return [entry.to_row() for entry in prompt_entries]


def format_timecode(timestamp_seconds: float) -> str:
    total_milliseconds = max(int(round(timestamp_seconds * 1000)), 0)
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def _apply_video_metadata(
    *,
    metadata: VideoAssetMetadata,
    mime_type: str,
    source_video_bytes: bytes | None,
    upload_signature: str,
    reset_prompts: bool,
) -> None:
    LOGGER.debug(
        "Applying video metadata asset_id=%s video_name=%s frame_count=%s fps=%.3f reset_prompts=%s",
        metadata.asset_id,
        metadata.filename,
        metadata.frame_count,
        metadata.fps,
        reset_prompts,
    )
    st.session_state.video_loaded = True
    _refresh_source_binding(
        video_name=metadata.filename,
        mime_type=mime_type,
        source_video_bytes=source_video_bytes,
        upload_signature=upload_signature,
    )
    st.session_state.active_asset_id = metadata.asset_id
    st.session_state.asset_id = metadata.asset_id
    st.session_state.video_fps = metadata.fps
    st.session_state.video_frame_count = metadata.frame_count
    st.session_state.video_duration_seconds = metadata.duration_seconds
    st.session_state.video_width = metadata.width
    st.session_state.video_height = metadata.height
    if reset_prompts:
        progress = build_navigation_position(
            frame_index=0,
            frame_count=metadata.frame_count,
            fps=metadata.fps,
        )
        st.session_state.prompt_entries = []
    else:
        progress = build_navigation_position(
            frame_index=st.session_state.current_frame_index,
            frame_count=metadata.frame_count,
            fps=metadata.fps,
        )
    _apply_playback_progress(progress)
    st.session_state.current_frame_image_bytes = None
    st.session_state.current_frame_image_mime_type = None
    st.session_state.current_frame_width = metadata.width
    st.session_state.current_frame_height = metadata.height
    st.session_state.current_frame_request_key = None
    st.session_state.frame_error_message = None


def _refresh_video_metadata(
    *,
    metadata: VideoAssetMetadata,
    mime_type: str,
    source_video_bytes: bytes | None,
    upload_signature: str,
) -> None:
    previous_frame_index = int(st.session_state.current_frame_index)
    LOGGER.debug(
        "Refreshing metadata without reset asset_id=%s frame_index=%s playback_running=%s",
        metadata.asset_id,
        previous_frame_index,
        st.session_state.playback_running,
    )
    st.session_state.video_loaded = True
    _refresh_source_binding(
        video_name=metadata.filename,
        mime_type=mime_type,
        source_video_bytes=source_video_bytes,
        upload_signature=upload_signature,
    )
    st.session_state.active_asset_id = metadata.asset_id
    st.session_state.asset_id = metadata.asset_id
    st.session_state.video_fps = metadata.fps
    st.session_state.video_frame_count = metadata.frame_count
    st.session_state.video_duration_seconds = metadata.duration_seconds
    st.session_state.video_width = metadata.width
    st.session_state.video_height = metadata.height
    st.session_state.current_frame_width = metadata.width
    st.session_state.current_frame_height = metadata.height
    clamped_frame_index = clamp_current_frame_index(previous_frame_index)
    if clamped_frame_index != previous_frame_index:
        progress = build_navigation_position(
            frame_index=clamped_frame_index,
            frame_count=metadata.frame_count,
            fps=metadata.fps,
        )
        _apply_playback_progress(progress)
        st.session_state.current_frame_image_bytes = None
        st.session_state.current_frame_image_mime_type = None
        st.session_state.current_frame_request_key = None
    elif not st.session_state.playback_running:
        st.session_state.current_frame_timestamp_seconds = format_time_seconds_for_frame(
            frame_index=clamped_frame_index,
            fps=metadata.fps,
        )
    st.session_state.frame_error_message = None


def _apply_playback_progress(progress: PlaybackProgress) -> None:
    st.session_state.current_frame_index = progress.frame_index
    st.session_state.current_frame_timestamp_seconds = progress.time_seconds
    st.session_state.playback_running = progress.playback_running
    st.session_state.playback_anchor_frame_index = progress.playback_anchor_frame_index
    st.session_state.playback_started_at_seconds = progress.playback_started_at_seconds


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


def _has_complete_video_metadata() -> bool:
    return bool(
        st.session_state.video_loaded
        and _current_active_asset_id() is not None
        and float(st.session_state.video_fps) > 0
        and int(st.session_state.video_frame_count) > 0
        and int(st.session_state.video_width) > 0
        and int(st.session_state.video_height) > 0
    )


def _has_active_source() -> bool:
    return _current_active_asset_id() is not None


def _current_active_asset_id() -> str | None:
    return st.session_state.get("active_asset_id") or st.session_state.get("asset_id")


def _current_active_video_name() -> str | None:
    return st.session_state.get("active_video_name") or st.session_state.get("video_name")


def _current_source_fingerprint() -> str | None:
    return st.session_state.get("source_fingerprint") or st.session_state.get("video_upload_signature")


def _synchronize_explicit_source_state() -> None:
    if st.session_state.active_asset_id is None and st.session_state.asset_id is not None:
        st.session_state.active_asset_id = st.session_state.asset_id
    if st.session_state.active_video_name is None and st.session_state.video_name != "No video selected":
        st.session_state.active_video_name = st.session_state.video_name
    if st.session_state.active_source_payload is None and st.session_state.source_video_bytes is not None:
        st.session_state.active_source_payload = st.session_state.source_video_bytes
    if st.session_state.source_fingerprint is None and st.session_state.video_upload_signature is not None:
        st.session_state.source_fingerprint = st.session_state.video_upload_signature


def _bump_ui_generation(reason: str) -> int:
    return _bump_generation("ui_generation", reason)


def _bump_playback_generation(reason: str) -> int:
    return _bump_generation("playback_generation", reason)


def _bump_generation(field_name: str, reason: str) -> int:
    next_value = int(st.session_state.get(field_name, 0)) + 1
    st.session_state[field_name] = next_value
    LOGGER.info("Generation bumped field=%s new_value=%s reason=%s", field_name, next_value, reason)
    return next_value


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
    st.session_state.current_frame_index = 0
    st.session_state.current_frame_timestamp_seconds = 0.0
    st.session_state.current_frame_image_bytes = None
    st.session_state.current_frame_image_mime_type = None
    st.session_state.current_frame_width = 0
    st.session_state.current_frame_height = 0
    st.session_state.current_frame_request_key = None
    st.session_state.frame_error_message = None
    st.session_state.playback_running = False
    st.session_state.playback_anchor_frame_index = None
    st.session_state.playback_started_at_seconds = None


def format_time_seconds_for_frame(*, frame_index: int, fps: float) -> float:
    if fps <= 0:
        return 0.0
    return max(frame_index, 0) / fps
