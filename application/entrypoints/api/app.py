"""FastAPI application for the browser-based video workspace."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

from application.adapters.incoming.api import (
    VideoWorkspaceApiDependencies,
    create_video_workspace_router,
)
from application.entrypoints.api.request_lifecycle import run_with_action_correlation
from application.infrastructure.wiring.video_asset_backend import get_video_asset_backend
from application.infrastructure.wiring.workbench_backend import get_workbench_backend

LOGGER = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create the FastAPI application with wired routes and development CORS."""

    app = FastAPI(
        title="Background Remover API",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def correlation_id_lifecycle(request: Request, call_next):  # type: ignore[no-untyped-def]
        """Bind one correlation id to one frontend-triggered API interaction."""
        return await run_with_action_correlation(request, call_next)

    video_asset_backend = get_video_asset_backend()
    workbench_backend = get_workbench_backend()
    app.include_router(
        create_video_workspace_router(
            dependencies=VideoWorkspaceApiDependencies(
                register_video_asset=video_asset_backend.register_video_asset,
                get_video_asset_metadata=video_asset_backend.get_video_asset_metadata,
                get_video_frame=video_asset_backend.get_video_frame,
                get_video_content=video_asset_backend.get_video_content,
                delete_video_asset=video_asset_backend.delete_video_asset,
                get_workbench_session=workbench_backend.get_workbench_session,
                sync_workbench_frame=workbench_backend.sync_workbench_frame,
                add_prompt=workbench_backend.add_prompt,
                clear_prompts=workbench_backend.clear_prompts,
                update_settings=workbench_backend.update_settings,
                refresh_preview=workbench_backend.refresh_preview,
                delete_workbench_session=workbench_backend.delete_session,
            )
        )
    )
    return app


app = create_app()


@app.on_event("startup")
async def log_application_startup() -> None:
    """Log startup through the shared application logging pipeline."""
    LOGGER.info("Background Remover API startup completed")
