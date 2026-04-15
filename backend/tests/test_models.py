"""
tests/test_api.py
──────────────────
Integration tests for the FastAPI route layer.

The ONNX model session is mocked — these tests run without any .onnx file
and verify that the API contract (status codes, response shapes, error
handling) is correct.

Run with:  pytest tests/test_api.py -v
"""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from app.core.model import PredictResult, TopPrediction
from httpx import ASGITransport, AsyncClient
from PIL import Image

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _solid_jpeg_bytes(colour: tuple = (100, 180, 60)) -> bytes:
    img = Image.new("RGB", (640, 480), colour)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


FAKE_CLASSES = [
    "Apple___Apple_scab",
    "Apple___healthy",
    "Tomato___Late_blight",
]

FAKE_RESULT = PredictResult(
    top=TopPrediction(label="Tomato___Late_blight", confidence=0.9421),
    top_k=[
        TopPrediction(label="Tomato___Late_blight", confidence=0.9421),
        TopPrediction(label="Apple___Apple_scab", confidence=0.0412),
        TopPrediction(label="Apple___healthy", confidence=0.0167),
    ],
    latency_ms=22.4,
)


@pytest.fixture()
def mock_model_session():
    """Return a mock ModelSession that looks ready and returns FAKE_RESULT."""
    mock = MagicMock()
    mock.is_ready = True
    mock.classes = FAKE_CLASSES
    mock.predict.return_value = FAKE_RESULT
    return mock


@pytest_asyncio.fixture()
async def client(mock_model_session):
    """
    AsyncClient pointed at the FastAPI app with the model session patched.
    We patch at the router import site so the route handlers see the mock.
    """
    with patch("app.api.predict.model_session", mock_model_session):
        # Also patch the lifespan model load so startup doesn't fail.
        with patch("app.main.model_session", mock_model_session):
            from app.main import app

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                yield ac


# ── POST /api/predict ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestPredictEndpoint:
    async def test_returns_200_on_valid_frame(self, client):
        resp = await client.post(
            "/api/predict",
            files={"file": ("image.jpg", _solid_jpeg_bytes(), "image/jpeg")},
        )
        assert resp.status_code == 200

    async def test_response_shape(self, client):
        resp = await client.post(
            "/api/predict",
            files={"file": ("image.jpg", _solid_jpeg_bytes(), "image/jpeg")},
        )
        data = resp.json()
        assert "label" in data
        assert "confidence" in data
        assert "top_k" in data
        assert "latency_ms" in data

    async def test_label_is_string(self, client):
        resp = await client.post(
            "/api/predict",
            files={"file": ("image.jpg", _solid_jpeg_bytes(), "image/jpeg")},
        )
        assert isinstance(resp.json()["label"], str)

    async def test_confidence_in_range(self, client):
        resp = await client.post(
            "/api/predict",
            files={"file": ("image.jpg", _solid_jpeg_bytes(), "image/jpeg")},
        )
        conf = resp.json()["confidence"]
        assert 0.0 <= conf <= 1.0

    async def test_top_k_length(self, client):
        resp = await client.post(
            "/api/predict",
            files={"file": ("image.jpg", _solid_jpeg_bytes(), "image/jpeg")},
        )
        assert len(resp.json()["top_k"]) == len(FAKE_RESULT.top_k)

    async def test_returns_422_on_empty_frame(self, client):
        # Even with UploadFile, an empty file might be a 422 if it fails to decode as image
        resp = await client.post(
            "/api/predict", files={"file": ("image.jpg", b"", "image/jpeg")}
        )
        assert resp.status_code == 422

    async def test_returns_415_on_unsupported_media_type(self, client):
        resp = await client.post(
            "/api/predict",
            files={"file": ("image.txt", b"!!!notbase64!!!", "text/plain")},
        )
        assert resp.status_code == 415

    async def test_returns_422_on_missing_file_field(self, client):
        resp = await client.post("/api/predict")
        assert resp.status_code == 422

    async def test_503_when_model_not_ready(self, client, mock_model_session):
        mock_model_session.is_ready = False
        resp = await client.post(
            "/api/predict",
            files={"file": ("image.jpg", _solid_jpeg_bytes(), "image/jpeg")},
        )
        assert resp.status_code == 503


# ── GET /api/health ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_returns_200(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200

    async def test_model_loaded_true(self, client):
        resp = await client.get("/api/health")
        assert resp.json()["model_loaded"] is True

    async def test_status_ok(self, client):
        resp = await client.get("/api/health")
        assert resp.json()["status"] == "ok"


# ── GET /api/classes ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestClassesEndpoint:
    async def test_returns_200(self, client):
        resp = await client.get("/api/classes")
        assert resp.status_code == 200

    async def test_classes_list(self, client):
        resp = await client.get("/api/classes")
        assert resp.json()["classes"] == FAKE_CLASSES

    async def test_num_classes(self, client):
        resp = await client.get("/api/classes")
        assert resp.json()["num_classes"] == len(FAKE_CLASSES)
