"""
app/api/predict.py
───────────────────
FastAPI route handlers for prediction, health, and class-list endpoints.

Rules
─────
• Route handlers contain zero business logic — they validate, delegate,
  and translate. All real work happens in app/core/.
• Every error surface is typed and returns a structured JSON body.
• Logging uses structlog bound context so every log line carries
  request-level metadata without threading.local hacks.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Request, status, File, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.core.model import PredictResult, model_session
from app.core.preprocessing import PreprocessingError, preprocess_frame
from app.logging import get_logger
from app.schemas.predict import (
    ClassProbability,
    ClassesResponse,
    HealthResponse,
    PredictResponse,
)
from app.config import settings

log = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["inference"])


# ── POST /api/predict ─────────────────────────────────────────────────────────

@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Predict crop disease from an uploaded image",
    responses={
        422: {"description": "Invalid or undecodable uploaded file"},
        503: {"description": "Model not loaded yet"},
    },
)
async def predict(request: Request, file: UploadFile = File(...)) -> PredictResponse:
    """
    Accept an image file upload from the frontend, run it through
    the ONNX model, and return the top prediction with confidence scores.
    """
    bound_log = log.bind(client=request.client.host if request.client else "unknown")

    if not model_session.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is still loading. Retry in a moment.",
        )

    t_total = time.perf_counter()

    # ── Preprocessing ──────────────────────────────────────────────────────
    try:
        image_bytes = await file.read()
        input_array = preprocess_frame(image_bytes)
    except PreprocessingError as exc:
        bound_log.warning("Frame preprocessing failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot process frame: {exc}",
        ) from exc

    # ── Inference ──────────────────────────────────────────────────────────
    try:
        result: PredictResult = await run_in_threadpool(model_session.predict, input_array)
    except Exception as exc:
        bound_log.error("Inference failed", error=str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inference failed. Check server logs.",
        ) from exc

    total_ms = round((time.perf_counter() - t_total) * 1000, 2)
    bound_log.info(
        "Prediction complete",
        label=result.top.label,
        confidence=round(result.top.confidence, 4),
        inference_ms=result.latency_ms,
        total_ms=total_ms,
    )

    return PredictResponse(
        label=result.top.label,
        confidence=round(result.top.confidence, 6),
        top_k=[
            ClassProbability(label=p.label, confidence=round(p.confidence, 6))
            for p in result.top_k
        ],
        latency_ms=result.latency_ms,
    )


# ── GET /api/health ───────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness + readiness probe",
)
async def health() -> HealthResponse:
    """
    Returns 200 with model_loaded=true when the ONNX session is ready.
    The frontend polls this before enabling the camera.
    Also suitable as a Kubernetes readiness probe.
    """
    return HealthResponse(
        status="ok" if model_session.is_ready else "loading",
        model_loaded=model_session.is_ready,
        num_classes=len(model_session.classes),
        input_size=settings.input_size,
        onnx_providers=settings.onnx_providers,
    )


# ── GET /api/classes ──────────────────────────────────────────────────────────

@router.get(
    "/classes",
    response_model=ClassesResponse,
    summary="List all disease class labels",
)
async def classes() -> ClassesResponse:
    """
    Returns all class labels in index order.
    The frontend uses this to build the disease legend / legend panel.
    """
    return ClassesResponse(
        classes=model_session.classes,
        num_classes=len(model_session.classes),
    )