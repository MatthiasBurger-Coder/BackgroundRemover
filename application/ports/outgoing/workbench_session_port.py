"""Outgoing port for persisted browser workbench state."""

from __future__ import annotations

from typing import Protocol

from application.domain.model.workbench_session import WorkbenchSession


class WorkbenchSessionPort(Protocol):
    """Port for loading and storing workbench state by asset identifier."""

    def get_workbench_session(self, asset_id: str) -> WorkbenchSession | None:
        """Return the stored workbench session for the asset if present."""

    def save_workbench_session(self, session: WorkbenchSession) -> WorkbenchSession:
        """Persist and return the provided workbench session."""

    def delete_workbench_session(self, asset_id: str) -> None:
        """Remove any stored workbench session for the asset."""
