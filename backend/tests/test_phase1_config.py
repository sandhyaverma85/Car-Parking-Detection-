"""
Phase 1 — Configuration and structure tests.

These tests verify:
  1. Settings are correctly read from environment.
  2. Missing/insecure JWT_SECRET raises a clear error.
  3. Placeholder DATABASE_URL is rejected.
  4. CORS origins list is parsed correctly.
  5. Evidence and data directories exist.
  6. Camera config JSON is valid.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# pyright: ignore [reportMissingImports]
import pytest   


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clear_settings_cache() -> None:
    """Clear the lru_cache so each test gets a fresh Settings instance."""
    from app.config import get_settings
    get_settings.cache_clear()


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestSettings:
    def setup_method(self) -> None:
        _clear_settings_cache()

    def teardown_method(self) -> None:
        _clear_settings_cache()

    def test_valid_settings_load(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Settings load correctly when all required env vars are present."""
        monkeypatch.setenv("JWT_SECRET", "a" * 64)
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        from app.config import get_settings
        s = get_settings()
        assert s.jwt_algorithm == "HS256"
        assert s.jwt_access_token_expire_minutes == 30
        assert s.confidence_threshold == 0.5

    def test_missing_jwt_secret_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Application refuses to start if JWT_SECRET is the placeholder."""
        monkeypatch.setenv("JWT_SECRET", "CHANGE_ME")
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        from pydantic import ValidationError
        from app.config import Settings
        with pytest.raises(ValidationError, match="JWT_SECRET"):
            Settings()

    def test_short_jwt_secret_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """JWT_SECRET shorter than 32 characters is rejected."""
        monkeypatch.setenv("JWT_SECRET", "short")
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        from pydantic import ValidationError
        from app.config import Settings
        with pytest.raises(ValidationError):
            Settings()

    def test_placeholder_database_url_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """DATABASE_URL containing CHANGE_ME is rejected."""
        monkeypatch.setenv("JWT_SECRET", "a" * 64)
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:CHANGE_ME@localhost/db")
        from pydantic import ValidationError
        from app.config import Settings
        with pytest.raises(ValidationError, match="DATABASE_URL"):
            Settings()

    def test_database_url_driver_rewrite(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """postgresql:// is rewritten to postgresql+asyncpg:// for async driver."""
        monkeypatch.setenv("JWT_SECRET", "a" * 64)
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        from app.config import Settings
        s = Settings()
        assert s.database_url.startswith("postgresql+asyncpg://")

    def test_cors_origins_parsed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """CORS_ORIGINS env var is split into a list correctly."""
        monkeypatch.setenv("JWT_SECRET", "a" * 64)
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv(
            "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
        )
        from app.config import Settings
        s = Settings()
        assert "http://localhost:5173" in s.cors_origins_list
        assert "http://localhost:3000" in s.cors_origins_list
        assert len(s.cors_origins_list) == 2


class TestDirectoryStructure:
    """Verify that required project directories exist."""

    BASE = Path(__file__).resolve().parents[2]  # project root

    def test_backend_dir(self) -> None:
        assert (self.BASE / "backend" / "app").is_dir()

    def test_ai_engine_dir(self) -> None:
        assert (self.BASE / "ai_engine").is_dir()

    def test_data_configs_dir(self) -> None:
        assert (self.BASE / "data" / "configs").is_dir()

    def test_evidence_dir(self) -> None:
        assert (self.BASE / "evidence").is_dir()

    def test_logs_dir(self) -> None:
        assert (self.BASE / "logs").is_dir()


class TestCameraConfig:
    """Validate cameras.json schema."""

    CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "configs" / "cameras.json"

    def test_config_file_exists(self) -> None:
        assert self.CONFIG_PATH.exists(), "data/configs/cameras.json is missing."

    def test_config_is_valid_json(self) -> None:
        data = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))
        assert "cameras" in data

    def test_at_least_one_camera(self) -> None:
        data = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))
        assert len(data["cameras"]) >= 1

    def test_camera_has_required_fields(self) -> None:
        data = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))
        for cam in data["cameras"]:
            assert "id" in cam
            assert "name" in cam
            assert "parking_slots" in cam
            # Accept both 'zones' (current) and 'restricted_zones' (legacy) key names
            assert "zones" in cam or "restricted_zones" in cam, (
                "Camera must have 'zones' or 'restricted_zones' key"
            )

    def test_parking_slot_polygons(self) -> None:
        data = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))
        for cam in data["cameras"]:
            for slot in cam["parking_slots"]:
                assert "id" in slot
                poly = slot["polygon"]
                # A polygon must have at least 3 vertices.
                assert len(poly) >= 3
                for point in poly:
                    assert len(point) == 2

    def test_restricted_zone_types(self) -> None:
        valid_types = {
            "NO_PARKING",
            "FIRE_HYDRANT",
            "BUS_STOP",
            "EMERGENCY_ACCESS",
            "COMMERCIAL_CURB",
            "RESTRICTED_CURB",
        }
        data = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))
        for cam in data["cameras"]:
            # Support both 'zones' (current) and 'restricted_zones' (legacy)
            zone_list = cam.get("zones", cam.get("restricted_zones", []))
            for zone in zone_list:
                # Support both 'zone_type' (current) and 'type' (legacy)
                zone_type = zone.get("zone_type", zone.get("type", ""))
                assert zone_type in valid_types, (
                    f"Unknown zone type: {zone_type}"
                )
