"""
app/schemas/predict.py
───────────────────────
Pydantic v2 request and response schemas for the prediction API.

All serialisation, validation, and OpenAPI documentation lives here —
the route handler and model code stay free of HTTP-layer concerns.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# ── Response ──────────────────────────────────────────────────────────────────

class ClassProbability(BaseModel):
    """A single class label with its softmax confidence score."""

    label: str = Field(..., description="Disease class label.")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Softmax probability in [0.0, 1.0].",
    )


class PredictResponse(BaseModel):
    """Full prediction response returned to the frontend."""

    label: str = Field(..., description="Top-1 predicted class label.")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Top-1 softmax confidence in [0.0, 1.0].",
    )
    top_k: list[ClassProbability] = Field(
        ...,
        description="Top-k predictions sorted by confidence descending.",
    )
    latency_ms: float = Field(
        ...,
        description="ONNX inference time in milliseconds (excludes preprocessing).",
    )

    model_config = {"json_schema_extra": {
        "example": {
            "label": "Tomato___Late_blight",
            "confidence": 0.9421,
            "top_k": [
                {"label": "Tomato___Late_blight", "confidence": 0.9421},
                {"label": "Tomato___Early_blight", "confidence": 0.0412},
                {"label": "Tomato___healthy", "confidence": 0.0167},
            ],
            "latency_ms": 23.4,
        }
    }}


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = Field(..., description="'ok' when the model is loaded and ready.")
    model_loaded: bool
    num_classes: int
    input_size: int
    onnx_providers: list[str]


# ── Classes ───────────────────────────────────────────────────────────────────

class ClassesResponse(BaseModel):
    classes: list[str] = Field(
        ...,
        description="All disease class labels in index order.",
    )
    num_classes: int