"""Development entrypoint for the FastAPI backend serving the browser GUI."""

from __future__ import annotations

import os

import uvicorn
from application.infrastructure.logging import LogLevel, configure_logging


def _resolve_log_level() -> LogLevel:
    configured_level = os.getenv("BACKGROUND_REMOVER_LOG_LEVEL", "DEBUG").upper()
    try:
        return LogLevel[configured_level]
    except KeyError:
        return LogLevel.DEBUG

if __name__ == "__main__":
    configure_logging(level=_resolve_log_level())
    port = int(os.getenv("BACKGROUND_REMOVER_API_PORT", "8010"))
    uvicorn.run(
        "application.entrypoints.api.app:app",
        host="127.0.0.1",
        port=port,
        reload=False,
        log_config=None,
    )
