"""FFmpeg-backed adapter for temporary source asset registration and frame retrieval."""

from __future__ import annotations

import atexit
import json
import logging
import math
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

from application.domain.errors.video_asset_errors import (
    VideoAssetNotFoundError,
    VideoFrameExtractionError,
    VideoProbeError,
)
from application.domain.model.video_asset import VideoAssetContent, VideoAssetMetadata, VideoFrame

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class _RegisteredVideoAsset:
    metadata: VideoAssetMetadata
    mime_type: str | None
    file_path: Path


class FfmpegVideoAssetAdapter:
    """Store uploaded videos in a temp directory and decode frames with FFmpeg tools."""

    def __init__(self) -> None:
        ffmpeg_path = shutil.which("ffmpeg")
        ffprobe_path = shutil.which("ffprobe")
        if ffmpeg_path is None or ffprobe_path is None:
            raise RuntimeError("ffmpeg and ffprobe must be available on PATH for video transport support.")
        self._ffmpeg_path = ffmpeg_path
        self._ffprobe_path = ffprobe_path

        self._storage_root = Path(tempfile.mkdtemp(prefix="background-remover-assets-"))
        self._assets: dict[str, _RegisteredVideoAsset] = {}
        atexit.register(self._cleanup_storage)
        LOGGER.info("Initialized FFmpeg video asset adapter storage_root=%s", self._storage_root)

    def register_video_asset(
        self,
        *,
        filename: str,
        video_bytes: bytes,
        mime_type: str | None,
    ) -> VideoAssetMetadata:
        asset_id = uuid.uuid4().hex
        file_path = self._storage_root / f"{asset_id}{Path(filename).suffix or '.mp4'}"
        file_path.write_bytes(video_bytes)
        LOGGER.info("Registering video asset asset_id=%s filename=%s bytes=%s", asset_id, filename, len(video_bytes))
        metadata = self._probe_metadata(asset_id=asset_id, filename=filename, file_path=file_path)
        self._assets[asset_id] = _RegisteredVideoAsset(
            metadata=metadata,
            mime_type=mime_type,
            file_path=file_path,
        )
        LOGGER.debug(
            "Registered video asset asset_id=%s frame_count=%s fps=%.3f resolution=%sx%s",
            asset_id,
            metadata.frame_count,
            metadata.fps,
            metadata.width,
            metadata.height,
        )
        return metadata

    def get_video_metadata(self, asset_id: str) -> VideoAssetMetadata:
        LOGGER.debug("Fetching video metadata asset_id=%s", asset_id)
        return self._get_registered_asset(asset_id).metadata

    def get_video_frame(self, asset_id: str, frame_index: int) -> VideoFrame:
        asset = self._get_registered_asset(asset_id)
        metadata = asset.metadata
        clamped_frame_index = metadata.clamped_frame_index(frame_index)
        LOGGER.debug(
            "Fetching video frame asset_id=%s requested_frame_index=%s clamped_frame_index=%s",
            asset_id,
            frame_index,
            clamped_frame_index,
        )
        image_bytes, resolved_frame_index = self._extract_frame_png(
            file_path=asset.file_path,
            requested_frame_index=clamped_frame_index,
            asset_id=asset_id,
        )

        frame = VideoFrame(
            asset_id=asset_id,
            frame_index=resolved_frame_index,
            timestamp_seconds=resolved_frame_index / metadata.fps if metadata.fps > 0 else 0.0,
            mime_type="image/png",
            width=metadata.width,
            height=metadata.height,
            image_bytes=image_bytes,
        )
        LOGGER.debug(
            "Resolved video frame asset_id=%s frame_index=%s timestamp=%.3f bytes=%s",
            asset_id,
            resolved_frame_index,
            resolved_frame_index / metadata.fps if metadata.fps > 0 else 0.0,
            len(image_bytes),
        )
        return frame

    def get_video_content(self, asset_id: str) -> VideoAssetContent:
        asset = self._get_registered_asset(asset_id)
        mime_type = asset.mime_type or "video/mp4"
        return VideoAssetContent(
            asset_id=asset_id,
            filename=asset.metadata.filename,
            mime_type=mime_type,
            video_bytes=asset.file_path.read_bytes(),
        )

    def delete_video_asset(self, asset_id: str) -> None:
        asset = self._get_registered_asset(asset_id)
        self._assets.pop(asset_id, None)
        asset.file_path.unlink(missing_ok=True)

    def _probe_metadata(self, *, asset_id: str, filename: str, file_path: Path) -> VideoAssetMetadata:
        command = [
            self._ffprobe_path,
            "-v",
            "error",
            "-count_frames",
            "-select_streams",
            "v:0",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(file_path),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            LOGGER.error("ffprobe failed asset_id=%s filename=%s stderr=%s", asset_id, filename, completed.stderr.strip())
            raise VideoProbeError(
                f"ffprobe failed for uploaded asset {filename}: {completed.stderr.strip()}"
            )

        try:
            payload = cast(dict[str, Any], json.loads(completed.stdout))
        except json.JSONDecodeError as error:
            raise VideoProbeError(f"Invalid ffprobe output for uploaded asset {filename}.") from error

        streams = cast(list[dict[str, Any]], payload.get("streams", []))
        video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
        if video_stream is None:
            raise VideoProbeError(f"No video stream found in uploaded asset {filename}.")

        fps = self._parse_fps(video_stream)
        width = int(video_stream.get("width") or 0)
        height = int(video_stream.get("height") or 0)
        duration_seconds = self._parse_duration_seconds(payload, video_stream)
        frame_count = self._parse_frame_count(video_stream, duration_seconds, fps)

        if width <= 0 or height <= 0 or fps <= 0 or frame_count <= 0:
            raise VideoProbeError(
                f"Incomplete metadata for uploaded asset {filename}: "
                f"fps={fps}, frame_count={frame_count}, size={width}x{height}"
            )

        LOGGER.debug(
            "Probed metadata asset_id=%s filename=%s fps=%.3f frame_count=%s duration=%.3f resolution=%sx%s",
            asset_id,
            filename,
            fps,
            frame_count,
            duration_seconds,
            width,
            height,
        )
        return VideoAssetMetadata(
            asset_id=asset_id,
            filename=filename,
            fps=fps,
            frame_count=frame_count,
            duration_seconds=duration_seconds,
            width=width,
            height=height,
        )

    def _parse_fps(self, video_stream: dict[str, Any]) -> float:
        rate_value = str(video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate") or "0/1")
        try:
            fps = float(Fraction(rate_value))
        except (ValueError, ZeroDivisionError):
            fps = 0.0
        return fps

    def _parse_duration_seconds(self, payload: dict[str, Any], video_stream: dict[str, Any]) -> float:
        format_section = cast(dict[str, Any], payload.get("format", {}))
        raw_duration = (
            video_stream.get("duration")
            or format_section.get("duration")
            or 0.0
        )
        try:
            duration_seconds = float(raw_duration)
        except (TypeError, ValueError):
            duration_seconds = 0.0
        return max(duration_seconds, 0.0)

    def _parse_frame_count(self, video_stream: dict[str, Any], duration_seconds: float, fps: float) -> int:
        raw_frame_count = video_stream.get("nb_frames") or video_stream.get("nb_read_frames")
        try:
            if raw_frame_count not in {None, "N/A"}:
                return max(int(cast(str, raw_frame_count)), 0)
        except (TypeError, ValueError):
            pass

        if duration_seconds <= 0 or fps <= 0:
            return 0
        return max(int(math.floor((duration_seconds * fps) + 0.5)), 1)

    def _get_registered_asset(self, asset_id: str) -> _RegisteredVideoAsset:
        asset = self._assets.get(asset_id)
        if asset is None:
            LOGGER.error("Unknown video asset requested asset_id=%s", asset_id)
            raise VideoAssetNotFoundError(f"Unknown video asset: {asset_id}")
        return asset

    def _extract_frame_png(
        self,
        *,
        file_path: Path,
        requested_frame_index: int,
        asset_id: str,
    ) -> tuple[bytes, int]:
        frame_candidates = [requested_frame_index]
        if requested_frame_index > 0:
            frame_candidates.extend(
                candidate
                for candidate in range(requested_frame_index - 1, max(requested_frame_index - 5, -1), -1)
            )

        for candidate_frame_index in frame_candidates:
            LOGGER.debug(
                "Attempting frame extraction asset_id=%s requested_frame_index=%s candidate_frame_index=%s",
                asset_id,
                requested_frame_index,
                candidate_frame_index,
            )
            command = [
                self._ffmpeg_path,
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(file_path),
                "-vf",
                f"select=eq(n\\,{candidate_frame_index})",
                "-frames:v",
                "1",
                "-fps_mode",
                "vfr",
                "-f",
                "image2pipe",
                "-vcodec",
                "png",
                "-",
            ]
            completed = subprocess.run(command, capture_output=True, check=False)
            if completed.returncode == 0 and completed.stdout:
                LOGGER.debug(
                    "Extracted frame asset_id=%s candidate_frame_index=%s bytes=%s",
                    asset_id,
                    candidate_frame_index,
                    len(completed.stdout),
                )
                return completed.stdout, candidate_frame_index

        LOGGER.error(
            "Frame extraction failed asset_id=%s requested_frame_index=%s candidate_window=%s",
            asset_id,
            requested_frame_index,
            frame_candidates,
        )
        raise VideoFrameExtractionError(
            f"Failed to extract frame {requested_frame_index} from asset {asset_id}: "
            "ffmpeg returned no image output for the requested frame window."
        )

    def _cleanup_storage(self) -> None:
        shutil.rmtree(self._storage_root, ignore_errors=True)
