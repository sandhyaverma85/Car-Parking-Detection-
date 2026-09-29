"""
Full system unit and integration tests:
- AI Pipeline rules & parking occupancy calculation
- Evidence generation
- Auth, password hashing, and RBAC permissions
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import Polygon

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ai_engine"))

from app.auth.auth import hash_password, verify_password, create_access_token, _decode_token
from app.models.models import UserRole
# pyrefly: ignore [missing-import]
from parking import ParkingSlot, ParkingOccupancyMonitor
# pyrefly: ignore [missing-import]
from zones import RestrictedZone, ZoneMonitor
# pyrefly: ignore [missing-import]
from tracker import TrackedVehicle
# pyrefly: ignore [missing-import]
from violation_engine import ViolationRuleEngine, ViolationEvent
# pyrefly: ignore [missing-import]
from evidence import draw_annotations, save_evidence


class TestAuthAndRBAC:
    def test_argon2_password_hashing(self):
        pw = "SecretP@ssw0rd123"
        hashed = hash_password(pw)
        assert hashed != pw
        assert verify_password(pw, hashed) is True
        assert verify_password("WrongPassword", hashed) is False

    def test_jwt_token_creation_and_payload(self):
        token, expires_in = create_access_token(user_id=1, role=UserRole.ADMIN.value)
        assert isinstance(token, str)
        assert expires_in > 0
        payload = _decode_token(token)
        assert payload["sub"] == "1"
        assert payload["role"] == "ADMIN"


class TestAIEngineComponents:
    def test_parking_slot_occupancy(self):
        # Create 2 slots: P01 and P02
        slots = [
            ParkingSlot(id="P01", slot_number=1, polygon=Polygon([(0, 0), (100, 0), (100, 100), (0, 100)]), camera_id="CAM-001"),
            ParkingSlot(id="P02", slot_number=2, polygon=Polygon([(150, 0), (250, 0), (250, 100), (150, 100)]), camera_id="CAM-001"),
        ]
        monitor = ParkingOccupancyMonitor(slots, overlap_threshold=0.3)

        # Vehicle occupying P01 only
        vehicle1 = TrackedVehicle(
            track_id=1,
            bbox=[10, 10, 90, 90],
            confidence=0.9,
            class_id=2,
            class_name="car",
            vehicle_category="PRIVATE",
        )

        res = monitor.evaluate([vehicle1])
        assert res.total == 2
        assert res.occupied == 1
        assert res.available == 1
        assert res.occupancy_percentage == 50.0

    def test_violation_rule_engine_duration(self):
        zone = RestrictedZone(
            id="Z01",
            name="No Parking Zone",
            zone_type="NO_PARKING",
            polygon=Polygon([(0, 0), (200, 0), (200, 200), (0, 200)]),
            camera_id="CAM-001",
            allowed_vehicle_types=[],
            max_duration_seconds=2,
        )
        monitor = ZoneMonitor([zone])
        rule_engine = ViolationRuleEngine(cooldown_seconds=10.0)

        vehicle = TrackedVehicle(
            track_id=42,
            bbox=[50, 50, 120, 120],
            confidence=0.88,
            class_id=2,
            class_name="car",
            vehicle_category="PRIVATE",
        )

        # 1. Below duration threshold (1.0s < 2s) -> No violation
        presences_short = monitor.check([vehicle], get_duration_fn=lambda tid: 1.0)
        violations_short = rule_engine.evaluate(presences_short)
        assert len(violations_short) == 0

        # 2. Exceeding duration threshold (3.0s > 2s) -> Violation created!
        presences_long = monitor.check([vehicle], get_duration_fn=lambda tid: 3.0)
        violations_long = rule_engine.evaluate(presences_long)
        assert len(violations_long) == 1
        assert violations_long[0].violation_type == "NO_PARKING"
        assert violations_long[0].track_id == 42

    def test_evidence_frame_generation(self, tmp_path):
        frame = np.zeros((432, 768, 3), dtype=np.uint8)
        violation = ViolationEvent(
            violation_id="test-violation-uuid",
            camera_id="CAM-001",
            track_id=15,
            violation_type="NO_PARKING",
            zone_id="Z01",
            zone_name="MG Road Zone",
            vehicle_category="PRIVATE",
            class_name="car",
            confidence=0.92,
            duration_seconds=4.5,
            bbox=[100, 100, 250, 250],
            timestamp=time.time(),
        )

        annotated = draw_annotations(frame, violation)
        assert annotated.shape == frame.shape

        ev_dir = str(tmp_path / "evidence")
        path = save_evidence(frame, violation, ev_dir)
        assert path is not None
        assert Path(path).exists()
        assert Path(path).stat().st_size > 0
