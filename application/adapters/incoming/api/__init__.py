"""API adapters."""

from application.adapters.incoming.api.video_workspace_router import (
    VideoWorkspaceApiDependencies,
    create_video_workspace_router,
)

__all__ = ["VideoWorkspaceApiDependencies", "create_video_workspace_router"]
