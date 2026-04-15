"""
app/config.py
─────────────
Single source of truth for every tunable value.
Load from environment variables or a .env file — never hard-code paths.

Usage
-----
    from app.config import settings
    print(settings.model_path)
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Model ──────────────────────────────────────────────────────────────
    model_path: Path = Field(
        default=Path("models/crop_disease_cnn.onnx"),
        description="Path to the ONNX model file.",
    )
    classes_path: Path = Field(
        default=Path("models/classes.json"),
        description="Path to the JSON file mapping class index → label.",
    )
    # ONNX execution providers in priority order.
    # On a GPU host set: ONNX_PROVIDERS='["CUDAExecutionProvider","CPUExecutionProvider"]'
    onnx_providers: list[str] = Field(
        default=["CPUExecutionProvider"],
        description="ONNX Runtime execution provider list.",
    )

    # ── Inference ──────────────────────────────────────────────────────────
    input_size: int = Field(
        default=256,
        description="Square side (px) the model expects. Must match training.",
    )
    # Pixel value range the model was trained on.
    # Your notebook uses transforms.ToTensor() only → [0, 1] with no mean/std.
    # If you retrain with Normalize, add norm_mean / norm_std fields here.
    pixel_scale: float = Field(
        default=1.0 / 255.0,
        description="Multiplier applied to uint8 pixel values before inference.",
    )
    top_k: int = Field(default=3, description="Number of top predictions to return.")

    # ── Server ─────────────────────────────────────────────────────────────
    allowed_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:4173"],
        description="CORS origins. Extend for your production domain.",
    )
    log_level: str = Field(default="INFO")

    # ── Validation ─────────────────────────────────────────────────────────
    @field_validator("model_path", "classes_path", mode="after")
    @classmethod
    def paths_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(
                f"Required file not found: {v}. "
                "Place the ONNX model and classes.json in the models/ directory."
            )
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton — safe to call anywhere."""
    return Settings()


# Module-level alias so callers can do `from app.config import settings`.
settings = get_settings()
