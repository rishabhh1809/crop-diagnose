"""
app/core/preprocessing.py
──────────────────────────
Pure, stateless functions that transform raw image bytes into a
numpy array ready for ONNX inference.

Design rules
────────────
• No side effects, no I/O, no model references — easily unit-testable.
• Mirrors training transforms exactly:
    torchvision.transforms.ToTensor()  →  divide uint8 by 255 → float32
    If you add Normalize() at training time, add norm_mean/norm_std params here.
• Centre-crop before resize so non-square camera feeds don't distort the leaf.
"""

from __future__ import annotations

import io

import numpy as np
from app.config import settings
from app.logging import get_logger
from PIL import Image

log = get_logger(__name__)


# ── Exceptions ────────────────────────────────────────────────────────────────


class PreprocessingError(ValueError):
    """Raised when a frame cannot be decoded or preprocessed."""


# ── Public API ────────────────────────────────────────────────────────────────


def preprocess_frame(image_bytes: bytes) -> np.ndarray:
    """
    Full pipeline: raw image bytes → ONNX-ready float32 numpy array.

    Parameters
    ----------
    image_bytes:
        Raw bytes file contents uploaded to the API.

    Returns
    -------
    np.ndarray of shape (1, 3, H, W) and dtype float32, values in [0, 1].

    Raises
    ------
    PreprocessingError on any decoding or conversion failure.
    """
    image = _decode_image_bytes(image_bytes)
    image = _centre_crop_square(image)
    image = _resize(image, settings.input_size)
    tensor = _to_chw_float32(image)  # (3, H, W)
    return tensor[np.newaxis, ...]  # (1, 3, H, W)


# ── Internal helpers ──────────────────────────────────────────────────────────


def _decode_image_bytes(image_bytes: bytes) -> Image.Image:
    """Decode raw image bytes to a PIL RGB image."""
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        raise PreprocessingError(f"Cannot decode image bytes: {exc}") from exc

    return image


def _centre_crop_square(image: Image.Image) -> Image.Image:
    """
    Crop the largest possible square from the centre of the image.

    This avoids letterboxing / stretching artefacts when the camera feed
    is non-square (e.g. 4:3 or 16:9 mobile camera).
    """
    w, h = image.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return image.crop((left, top, left + side, top + side))


def _resize(image: Image.Image, size: int) -> Image.Image:
    """Resize to (size × size) using high-quality Lanczos resampling."""
    return image.resize((size, size), Image.Resampling.LANCZOS)


def _to_chw_float32(image: Image.Image) -> np.ndarray:
    """
    Convert PIL image → float32 numpy array in CHW layout, values in [0, 1].

    Mirrors torchvision.transforms.ToTensor():
        HWC uint8 [0, 255]  →  CHW float32 [0.0, 1.0]
    """
    array = np.array(image, dtype=np.float32)  # HWC, [0, 255]
    array *= settings.pixel_scale  # scale to [0, 1]
    array = np.transpose(array, (2, 0, 1))  # HWC → CHW
    return array  # (3, H, W)
