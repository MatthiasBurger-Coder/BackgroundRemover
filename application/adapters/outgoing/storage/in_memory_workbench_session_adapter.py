"""In-memory storage adapter for browser workbench sessions."""

from __future__ import annotations

from application.domain.model.workbench_session import WorkbenchSession


class InMemoryWorkbenchSessionAdapter:
    """Persist workbench state in process memory for the active backend runtime."""

    def __init__(self) -> None:
        self._sessions: dict[str, WorkbenchSession] = {}

    def get_workbench_session(self, asset_id: str) -> WorkbenchSession | None:
        return self._sessions.get(asset_id)

    def save_workbench_session(self, session: WorkbenchSession) -> WorkbenchSession:
        self._sessions[session.asset_id] = session
        return session

    def delete_workbench_session(self, asset_id: str) -> None:
        self._sessions.pop(asset_id, None)
