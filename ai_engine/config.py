"""
Central AI-engine configuration.

Values are read from the same .env file used by the backend so that
there is a single source of truth for thresholds and paths.
Sensitive values (database URL, JWT secret) are not needed here —
the AI engine publishes events to the backend via HTTP, not directly
to the database.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

# pyrefly: ignore [missing-import]
from pydantic import Field, field_validator
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    """Settings for the AI / Computer-Vision engine."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    # ── YOLO Model ────────────────────────────────────────────────────────────
    model_path: str = Field(
        default="yolov8n.pt",
        description=(
            "Path to YOLO weights file.  "
            "yolov8n.pt will be auto-downloaded by ultralytics on first run."
        ),
    )
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0)

    # ── Frame Processing ──────────────────────────────────────────────────────
    # Only process every Nth frame to reduce CPU/GPU load.
    frame_skip: int = Field(default=2, ge=1)
    # Resize input frame to this width before inference (height is scaled).
    # Set to 0 to keep original resolution.
    inference_width: int = Field(default=640, ge=0)

    # ── Tracking / Violation ──────────────────────────────────────────────────
    parking_overlap_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum IoU between vehicle bbox and slot polygon to count as occupied.",
    )
    violation_duration_seconds: int = Field(
        default=120,
        ge=0,
        description="Seconds a vehicle must remain in a restricted zone before a violation is raised.",
    )

    # ── Video Source ──────────────────────────────────────────────────────────
    video_source_type: Literal["file", "webcam", "rtsp"] = Field(default="file")
    video_file_path: str = Field(default="data/videos/sample.mp4")
    webcam_index: int = Field(default=0, ge=0)
    # RTSP URL is read from env; never logged or exposed to frontend.
    rtsp_url: str = Field(default="")

    # ── Evidence ──────────────────────────────────────────────────────────────
    evidence_dir: str = Field(default="evidence")

    # ── Backend Endpoint (AI engine pushes events here) ───────────────────────
    backend_base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL of the FastAPI backend. AI engine posts events here.",
    )
    ai_internal_api_key: str = Field(
        default="",
        description=(
            "Shared secret between the AI engine and the backend for internal event POSTs. "
            "Set this in .env; never hard-code it."
        ),
    )

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO")

    # ── YOLO Vehicle Classes ──────────────────────────────────────────────────
    # COCO class IDs for vehicles we care about.
    # car=2, motorcycle=3, bus=5, truck=7
    # These can be overridden via VEHICLE_CLASS_IDS env var as a CSV string.
    vehicle_class_ids: str = Field(
        default="2,3,5,7",
        description="Comma-separated COCO class IDs to treat as vehicles.",
    )

    @property
    def vehicle_class_id_list(self) -> list[int]:
        """Return vehicle class IDs as a list of integers."""
        return [int(x.strip()) for x in self.vehicle_class_ids.split(",") if x.strip()]

    @field_validator("rtsp_url")
    @classmethod
    def warn_rtsp_placeholder(cls, v: str) -> str:
        # Silently accept empty string — RTSP may not be configured for MVP.
        return v


@lru_cache(maxsize=1)
def get_ai_settings() -> AISettings:
    """Return the singleton AISettings instance."""
    return AISettings()
