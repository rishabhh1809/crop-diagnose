"""
app/core/model.py
─────────────────
ONNX model loading, lifecycle management, and inference.

Design rules
────────────
•   The InferenceSession is a singleton — loaded once at startup via the
    FastAPI lifespan, stored on app.state, never recreated per-request.
•   Inference is a pure function (run_inference) that takes a numpy array
    and returns raw logits — no HTTP concerns bleed in here.
•   Softmax and top-k extraction live here so the route handler only deals
    with domain objects (PredictResult), not raw arrays.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass  # , field
from pathlib import Path
from typing import cast

import numpy as np
import onnxruntime as ort
from app.config import settings
from app.logging import get_logger

log = get_logger(__name__)


# ── Domain objects ────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class TopPrediction:
    label: str
    confidence: float  # [0.0, 1.0]


@dataclass(frozen=True, slots=True)
class PredictResult:
    top: TopPrediction
    top_k: list[TopPrediction]
    latency_ms: float


# ── Session manager ───────────────────────────────────────────────────────────


class ModelSession:
    """
    Wraps an onnxruntime.InferenceSession with lazy-ready semantics.

    Instantiate once and call .load() inside the FastAPI lifespan.
    All inference calls are thread-safe (ORT sessions are re-entrant).
    """

    def __init__(self) -> None:
        self._session: ort.InferenceSession | None = None
        self._classes: list[str] = []
        self._input_name: str = ""

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def load(
        self,
        model_path: Path = settings.model_path,
        classes_path: Path = settings.classes_path,
        providers: list[str] = settings.onnx_providers,
    ) -> None:
        """
        Load ONNX model + class list.  Call exactly once at process start.
        """
        log.info("Loading ONNX model", path=str(model_path), providers=providers)
        t0 = time.perf_counter()

        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = (
            ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        )
        # Limit inter/intra-op threads to avoid competing with uvicorn workers.
        sess_options.intra_op_num_threads = 2
        sess_options.inter_op_num_threads = 1

        self._session = ort.InferenceSession(
            str(model_path),
            sess_options=sess_options,
            providers=providers,
        )
        self._input_name = self._session.get_inputs()[0].name

        self._classes = _load_classes(classes_path)

        elapsed = (time.perf_counter() - t0) * 1000
        log.info(
            "Model ready",
            num_classes=len(self._classes),
            load_ms=round(elapsed, 1),
            active_provider=self._session.get_providers()[0],
        )

    def unload(self) -> None:
        """Release session resources. Called in lifespan teardown."""
        self._session = None
        log.info("Model session released")

    @property
    def is_ready(self) -> bool:
        return self._session is not None

    @property
    def classes(self) -> list[str]:
        return self._classes

    # ── Inference ─────────────────────────────────────────────────────────

    def predict(self, input_array: np.ndarray) -> PredictResult:
        """
        Run inference on a preprocessed (1, 3, H, W) float32 array.

        Returns a PredictResult with the top prediction and top-k list.
        Raises RuntimeError if the session is not loaded.
        """
        if self._session is None:
            raise RuntimeError("Model session is not loaded. Call .load() first.")

        t0 = time.perf_counter()
        results = self._session.run(None, {self._input_name: input_array})
        logits: np.ndarray = cast(np.ndarray, results[0])
        latency_ms = (time.perf_counter() - t0) * 1000

        probabilities = _softmax(logits[0])  # (num_classes,)
        top_k = _top_k(probabilities, self._classes, k=settings.top_k)

        return PredictResult(
            top=top_k[0],
            top_k=top_k,
            latency_ms=round(latency_ms, 2),
        )


# ── Internal helpers ──────────────────────────────────────────────────────────


def _load_classes(path: Path) -> list[str]:
    """Load class index → label mapping from a JSON file."""
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    # Accept both list format ["class_a", "class_b"]
    # and dict format {"0": "class_a", "1": "class_b"}.
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data[str(i)] for i in range(len(data))]

    raise ValueError(f"Unrecognised classes.json format in {path}")


def _softmax(logits: np.ndarray) -> np.ndarray:
    """Numerically stable softmax."""
    exps = np.exp(logits - np.max(logits))
    return exps / exps.sum()


def _top_k(
    probabilities: np.ndarray,
    classes: list[str],
    k: int,
) -> list[TopPrediction]:
    """Return the top-k (label, confidence) pairs sorted descending."""
    k = min(k, len(classes))
    indices = np.argpartition(probabilities, -k)[-k:]
    indices = indices[np.argsort(probabilities[indices])[::-1]]
    return [
        TopPrediction(label=classes[i], confidence=float(probabilities[i]))
        for i in indices
    ]


# ── Module-level singleton ────────────────────────────────────────────────────

# Import and use this instance everywhere.
# The lifespan in main.py calls model_session.load() / .unload().
model_session = ModelSession()
