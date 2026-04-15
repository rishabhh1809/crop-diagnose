"""
app/main.py
───────────
FastAPI application factory.

Responsibilities
────────────────
• App creation and configuration.
• Lifespan: model load on startup, clean unload on shutdown.
• Middleware: CORS, request-ID injection, timing header.
• Router registration.
• Global exception handlers for unhandled errors.

Nothing else lives here — keep it a thin orchestration layer.
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from app.api.predict import router as predict_router
from app.config import settings
from app.core.model import model_session
from app.logging import configure_logging, get_logger
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

log = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Runs once at startup (before any request) and once at shutdown.
    This is the correct FastAPI 0.93+ pattern — no @app.on_event decorators.
    """
    configure_logging()
    log.info("Starting crop-diagnose backend", version=app.version)

    # Load model synchronously — it's a one-time cost and must complete
    # before we accept traffic.  For very large models consider running
    # this in asyncio.get_event_loop().run_in_executor().
    model_session.load()

    yield  # ← application runs here

    model_session.unload()
    log.info("Shutdown complete")


# ── App factory ───────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    app = FastAPI(
        title="Crop-Diagnose API",
        description=(
            "Real-time crop disease detection from leaf images. "
            "Powered by a custom CNN exported to ONNX."
        ),
        version="1.0.0",
        lifespan=lifespan,
        # Disable docs in prod by setting docs_url=None, redoc_url=None.
        docs_url="/docs",
        redoc_url="/redoc",
    )

    _add_middleware(app)
    _add_routers(app)
    _add_exception_handlers(app)

    return app


def _add_middleware(app: FastAPI) -> None:
    # ── CORS ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    # ── Request-ID + timing middleware ────────────────────────────────────
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next) -> Response:
        """
        Attach a unique request ID to every request.
        Bind it to structlog context so all log lines within the request
        carry the same ID — makes tracing trivial in log aggregators.
        """
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        t0 = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
        return response


def _add_routers(app: FastAPI) -> None:
    app.include_router(predict_router)


def _add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        log.error(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Check server logs."},
        )


# ── Entry point ───────────────────────────────────────────────────────────────

# Instantiate at module level so `uvicorn app.main:app` works.
app = create_app()
