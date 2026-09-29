"""
Violation Rule Engine — Phase 5

Evaluates zone presence data and generates violations based on
duration/persistence rules.  Does NOT contain any detection or
tracking code.

Rules:
  R1: Vehicle in NO_PARKING zone > max_duration_seconds → NO_PARKING violation
  R2: Vehicle in FIRE_HYDRANT zone > max_duration_seconds → FIRE_HYDRANT_BLOCKED
  R3: Vehicle in EMERGENCY_ACCESS zone > 0 seconds → EMERGENCY_ACCESS_BLOCKED
  R4: Non-allowed vehicle in BUS_STOP > max_duration_seconds → BUS_STOP_VIOLATION
  R5: Vehicle in COMMERCIAL_CURB / RESTRICTED_CURB > duration → RESTRICTED_CURB_VIOLATION
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from zones import ZonePresence
from utils.logging import get_logger

log = get_logger(__name__)


# Violation type strings (kept consistent with DB enum)
class ViolationType:
    NO_PARKING = "NO_PARKING"
    FIRE_HYDRANT_BLOCKED = "FIRE_HYDRANT_BLOCKED"
    EMERGENCY_ACCESS_BLOCKED = "EMERGENCY_ACCESS_BLOCKED"
    BUS_STOP_VIOLATION = "BUS_STOP_VIOLATION"
    RESTRICTED_CURB_VIOLATION = "RESTRICTED_CURB_VIOLATION"


@dataclass
class ViolationEvent:
    """A violation detected by the rule engine."""
    violation_id: str
    camera_id: str
    track_id: int
    violation_type: str
    zone_id: str
    zone_name: str
    vehicle_category: str
    class_name: str
    confidence: float
    duration_seconds: float
    bbox: List[float]
    timestamp: float = field(default_factory=time.time)
    # Evidence path will be filled by evidence.py
    evidence_path: Optional[str] = None


# Map zone type → violation type
_ZONE_TO_VIOLATION: Dict[str, str] = {
    "NO_PARKING":       ViolationType.NO_PARKING,
    "FIRE_HYDRANT":     ViolationType.FIRE_HYDRANT_BLOCKED,
    "EMERGENCY_ACCESS": ViolationType.EMERGENCY_ACCESS_BLOCKED,
    "BUS_STOP":         ViolationType.BUS_STOP_VIOLATION,
    "COMMERCIAL_CURB":  ViolationType.RESTRICTED_CURB_VIOLATION,
    "RESTRICTED_CURB":  ViolationType.RESTRICTED_CURB_VIOLATION,
}


class ViolationRuleEngine:
    """
    Applies duration-based rules to zone presence data.

    Maintains state to avoid re-firing violations for the same
    (track_id, zone_id) pair within a cooldown window.
    """

    def __init__(self, cooldown_seconds: float = 300.0) -> None:
        """
        Args:
            cooldown_seconds: After a violation is raised for a
                (track_id, zone_id) pair, don't raise another one for
                this many seconds (prevents alert flooding).
        """
        self._cooldown = cooldown_seconds
        # Key: (track_id, zone_id) → timestamp of last violation
        self._last_violation: Dict[Tuple[int, str], float] = {}

    def evaluate(self, presences: List[ZonePresence]) -> List[ViolationEvent]:
        """
        Apply rules to zone presence data.  Returns new violations only.
        """
        violations: List[ViolationEvent] = []
        now = time.time()

        for presence in presences:
            zone = presence.zone
            vtype = _ZONE_TO_VIOLATION.get(zone.zone_type)
            if vtype is None:
                continue

            # Check if vehicle type is allowed
            if zone.allowed_vehicle_types:
                if presence.class_name in zone.allowed_vehicle_types:
                    continue  # allowed — no violation

            # Duration check
            threshold = zone.max_duration_seconds
            if presence.duration_seconds < threshold:
                continue  # not long enough yet

            # Cooldown check — don't re-fire for same track+zone
            key = (presence.track_id, zone.id)
            last = self._last_violation.get(key, 0.0)
            if now - last < self._cooldown:
                continue

            # Generate violation
            self._last_violation[key] = now
            v = ViolationEvent(
                violation_id=str(uuid.uuid4()),
                camera_id=zone.camera_id,
                track_id=presence.track_id,
                violation_type=vtype,
                zone_id=zone.id,
                zone_name=zone.name,
                vehicle_category=presence.vehicle_category,
                class_name=presence.class_name,
                confidence=presence.confidence,
                duration_seconds=presence.duration_seconds,
                bbox=presence.bbox,
                timestamp=now,
            )
            violations.append(v)
            log.info(
                "violation_detected",
                violation_id=v.violation_id,
                type=vtype,
                track_id=presence.track_id,
                zone=zone.name,
                duration=f"{presence.duration_seconds:.1f}s",
            )

        return violations
