"""Mock data for the internal Streamlit UI shell."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameLabel:
    index: int
    timecode: str
    label: str
    note: str

    def selector_label(self) -> str:
        return f"Frame {self.index:04d} | {self.timecode} | {self.label}"


@dataclass(frozen=True)
class PromptEntry:
    identifier: int
    mode: str
    frame_index: int
    frame_label: str
    x: int
    y: int
    source: str

    def to_row(self) -> dict[str, str | int]:
        return {
            "ID": self.identifier,
            "Mode": self.mode.title(),
            "Frame": self.frame_index,
            "Frame Label": self.frame_label,
            "X": self.x,
            "Y": self.y,
            "Source": self.source,
        }


@dataclass(frozen=True)
class FailureCase:
    code: str
    frame_index: int
    severity: str
    title: str
    summary: str
    suspected_cause: str
    recommended_check: str
    owner: str

    def selector_label(self) -> str:
        return f"{self.code} | Frame {self.frame_index:04d} | {self.title}"

    def to_row(self) -> dict[str, str | int]:
        return {
            "Code": self.code,
            "Frame": self.frame_index,
            "Severity": self.severity,
            "Title": self.title,
            "Owner": self.owner,
        }


def get_frame_catalog() -> list[FrameLabel]:
    return [
        FrameLabel(96, "00:00:03.200", "Entrance pass", "Subject enters the tracked region."),
        FrameLabel(112, "00:00:03.733", "Shoulder turn", "Background parallax increases around the silhouette."),
        FrameLabel(128, "00:00:04.267", "Primary keyframe", "Best operator reference frame for prompt placement."),
        FrameLabel(144, "00:00:04.800", "Arm extension", "Thin structures become more visible."),
        FrameLabel(160, "00:00:05.333", "Partial overlap", "Foreground touches a high-contrast background edge."),
        FrameLabel(176, "00:00:05.867", "Fast motion", "Preview mode may show temporal instability here."),
        FrameLabel(192, "00:00:06.400", "Hair detail", "Feathering decisions become easier to inspect."),
        FrameLabel(208, "00:00:06.933", "Exit transition", "Foreground leaves the center of the frame."),
    ]


def build_prompt_entry(
    identifier: int,
    mode: str,
    x: int,
    y: int,
    frame: FrameLabel,
    source: str = "Operator input",
) -> PromptEntry:
    return PromptEntry(
        identifier=identifier,
        mode=mode,
        frame_index=frame.index,
        frame_label=frame.label,
        x=x,
        y=y,
        source=source,
    )


def get_default_prompt_entries(frame_catalog: list[FrameLabel]) -> list[PromptEntry]:
    keyframe = next(frame for frame in frame_catalog if frame.index == 128)
    return [
        build_prompt_entry(1, "foreground", 642, 284, keyframe, "Seeded placeholder"),
        build_prompt_entry(2, "background", 188, 112, keyframe, "Seeded placeholder"),
    ]


def get_failure_cases() -> list[FailureCase]:
    return [
        FailureCase(
            code="FG-014",
            frame_index=160,
            severity="High",
            title="Edge leakage near right shoulder",
            summary="Placeholder case for an unstable matte edge on a high-contrast background.",
            suspected_cause="Insufficient prompt coverage around the shoulder transition.",
            recommended_check="Review prompt density and compare preview threshold values.",
            owner="Operator QA",
        ),
        FailureCase(
            code="TS-021",
            frame_index=176,
            severity="Medium",
            title="Temporal shimmer in fast motion",
            summary="Preview placeholder for frame-to-frame instability during motion bursts.",
            suspected_cause="Preview profile may underweight temporal smoothing.",
            recommended_check="Inspect neighboring frames and compare preview versus final profile assumptions.",
            owner="Workflow Review",
        ),
        FailureCase(
            code="MK-008",
            frame_index=192,
            severity="Medium",
            title="Hair region softening",
            summary="Placeholder case for over-feathered edge treatment in fine-detail regions.",
            suspected_cause="Current feather value may be too strong for inspection mode.",
            recommended_check="Reduce feather value and inspect the black and white mask panel.",
            owner="Mask Tuning",
        ),
        FailureCase(
            code="BG-003",
            frame_index=208,
            severity="Low",
            title="Background spill in exit transition",
            summary="Placeholder case for residual background fragments during subject exit.",
            suspected_cause="Prompt set may no longer cover the leaving silhouette consistently.",
            recommended_check="Choose a later keyframe and seed a new foreground prompt set.",
            owner="Operator QA",
        ),
    ]


def get_workspace_info(video_loaded: bool, video_name: str) -> list[dict[str, str]]:
    source_label = "Uploaded session asset" if video_loaded else "Mock internal session"
    active_video = video_name if video_loaded else "operator_take_07_placeholder.mp4"
    return [
        {"Field": "Workspace", "Value": "Mask Preview Lab"},
        {"Field": "Session", "Value": "UI-SHELL-042"},
        {"Field": "Operator Profile", "Value": "Internal review mode"},
        {"Field": "Video Source", "Value": source_label},
        {"Field": "Active Asset", "Value": active_video},
    ]


def get_preview_metadata() -> list[dict[str, str]]:
    return [
        {"Field": "Preview Profile", "Value": "Operator Preview"},
        {"Field": "Resolution", "Value": "1280 x 720 placeholder"},
        {"Field": "Mask Mode", "Value": "Single-subject matte"},
        {"Field": "Transport", "Value": "No backend attached"},
    ]


def get_runtime_handles() -> list[dict[str, str]]:
    return [
        {"Handle": "video_reader_port", "State": "Not connected"},
        {"Handle": "segmenter_port", "State": "Reserved for future adapter"},
        {"Handle": "preview_renderer", "State": "UI shell placeholder only"},
        {"Handle": "diagnostic_feed", "State": "Mock session data"},
    ]


def get_runtime_snapshot() -> list[dict[str, str]]:
    return [
        {"Item": "Queue State", "Value": "Idle"},
        {"Item": "Preview Ticket", "Value": "preview-shell-0007"},
        {"Item": "Mask Pipeline", "Value": "Not initialized"},
        {"Item": "Diagnostics Feed", "Value": "Mocked runtime snapshot"},
    ]
