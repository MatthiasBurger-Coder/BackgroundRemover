"""FastAPI application for the browser-based video workspace."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from application.adapters.incoming.api import (
    VideoWorkspaceApiDependencies,
    create_video_workspace_router,
)
from application.infrastructure.context.correlation_id_manager import CorrelationIdManager
from application.infrastructure.wiring.video_asset_backend import get_video_asset_backend
from application.infrastructure.wiring.workbench_backend import get_workbench_backend

LOGGER = logging.getLogger(__name__)


class RequestCorrelationMiddleware:
    """Assign one correlation id to one complete frontend-triggered HTTP lifecycle."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "")
        response_status_code: int | None = None

        async def send_with_status(message: Message) -> None:
            nonlocal response_status_code
            if message["type"] == "http.response.start":
                response_status_code = int(message["status"])
            await send(message)

        with CorrelationIdManager.lifecycle_scope():
            started_at = perf_counter()
            LOGGER.info("Action lifecycle started method=%s path=%s", method, path)
            try:
                await self._app(scope, receive, send_with_status)
            except BaseException:
                duration_ms = (perf_counter() - started_at) * 1000.0
                LOGGER.exception(
                    "Action lifecycle failed method=%s path=%s duration_ms=%.3f",
                    method,
                    path,
                    duration_ms,
                )
                raise

            duration_ms = (perf_counter() - started_at) * 1000.0
            LOGGER.info(
                "Action lifecycle finished method=%s path=%s status_code=%s duration_ms=%.3f",
                method,
                path,
                response_status_code if response_status_code is not None else "unknown",
                duration_ms,
            )


@asynccontextmanager
async def _application_lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Log startup through the shared application logging pipeline."""

    LOGGER.info("Background Remover API startup completed")
    yield


def create_app() -> FastAPI:
    """Create the FastAPI application with wired routes and development CORS."""

    app = FastAPI(
        title="Background Remover API",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=_application_lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestCorrelationMiddleware)

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
