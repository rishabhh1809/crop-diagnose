"""
tests/test_preprocessing.py
────────────────────────────
Unit tests for the preprocessing pipeline.

These tests are fast (<1s total) and require no ONNX model — they test
only the pure functions in app/core/preprocessing.py.

Run with:  pytest tests/test_preprocessing.py -v
"""

from __future__ import annotations

import io

import numpy as np
import pytest
from app.core.preprocessing import (
    PreprocessingError,
    _centre_crop_square,
    _decode_image_bytes,
    _resize,
    _to_chw_float32,
    preprocess_frame,
)
from PIL import Image

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_jpeg_bytes(
    width: int = 640, height: int = 480, colour: tuple = (120, 200, 80)
) -> bytes:
    """Create a solid-colour JPEG encoded as raw bytes."""
    img = Image.new("RGB", (width, height), colour)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


# ── _decode_image_bytes ──────────────────────────────────────────────────────


class TestDecodeImageBytes:
    def test_decodes_valid_jpeg(self):
        b = _make_jpeg_bytes()
        img = _decode_image_bytes(b)
        assert img.mode == "RGB"

    def test_raises_on_invalid_bytes(self):
        garbage = b"this is not an image"
        with pytest.raises(PreprocessingError, match="Cannot decode image bytes"):
            _decode_image_bytes(garbage)


# ── _centre_crop_square ───────────────────────────────────────────────────────


class TestCentreCropSquare:
    def test_landscape_becomes_square(self):
        img = Image.new("RGB", (640, 480))
        cropped = _centre_crop_square(img)
        assert cropped.size == (480, 480)

    def test_portrait_becomes_square(self):
        img = Image.new("RGB", (480, 640))
        cropped = _centre_crop_square(img)
        assert cropped.size == (480, 480)

    def test_square_unchanged(self):
        img = Image.new("RGB", (512, 512))
        cropped = _centre_crop_square(img)
        assert cropped.size == (512, 512)

    def test_crop_is_centred(self):
        # Build a 300×100 image where only the centre 100×100 is red.
        img = Image.new("RGB", (300, 100), (0, 0, 0))
        centre_region = Image.new("RGB", (100, 100), (255, 0, 0))
        img.paste(centre_region, (100, 0))
        cropped = _centre_crop_square(img)
        # All pixels in the 100×100 crop should be red.
        pixels = np.array(cropped)
        assert np.all(pixels == [255, 0, 0])


# ── _resize ───────────────────────────────────────────────────────────────────


class TestResize:
    def test_resizes_to_target(self):
        img = Image.new("RGB", (512, 512))
        resized = _resize(img, 256)
        assert resized.size == (256, 256)


# ── _to_chw_float32 ───────────────────────────────────────────────────────────


class TestToChwFloat32:
    def test_shape_is_chw(self):
        img = Image.new("RGB", (256, 256))
        arr = _to_chw_float32(img)
        assert arr.shape == (3, 256, 256)

    def test_dtype_is_float32(self):
        img = Image.new("RGB", (256, 256))
        arr = _to_chw_float32(img)
        assert arr.dtype == np.float32

    def test_values_in_zero_one(self):
        # White image → all channels = 255 / 255 = 1.0
        img = Image.new("RGB", (4, 4), (255, 255, 255))
        arr = _to_chw_float32(img)
        assert arr.max() <= 1.0
        assert arr.min() >= 0.0
        np.testing.assert_allclose(arr, 1.0, atol=1e-6)

    def test_black_image_is_zero(self):
        img = Image.new("RGB", (4, 4), (0, 0, 0))
        arr = _to_chw_float32(img)
        np.testing.assert_allclose(arr, 0.0, atol=1e-6)


# ── preprocess_frame (integration) ───────────────────────────────────────────


class TestPreprocessFrame:
    def test_output_shape(self):
        b = _make_jpeg_bytes(640, 480)
        tensor = preprocess_frame(b)
        assert tensor.shape == (1, 3, 256, 256)

    def test_output_dtype(self):
        b = _make_jpeg_bytes()
        tensor = preprocess_frame(b)
        assert tensor.dtype == np.float32

    def test_output_range(self):
        b = _make_jpeg_bytes()
        tensor = preprocess_frame(b)
        assert tensor.min() >= 0.0
        assert tensor.max() <= 1.0

    def test_bad_payload_raises_preprocessing_error(self):
        with pytest.raises(PreprocessingError):
            preprocess_frame(b"totally_not_an_image")
