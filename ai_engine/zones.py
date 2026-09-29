"""
Restricted Zone Management — Phase 5

Loads and manages restricted zones (NO_PARKING, FIRE_HYDRANT, etc.)
and checks which vehicles are currently inside each zone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from shapely.geometry import Polygon  # type: ignore

from tracker import TrackedVehicle
from utils.logging import get_logger

log = get_logger(__name__)

ZONE_TYPES = {
    "NO_PARKING",
    "FIRE_HYDRANT",
    "BUS_STOP",
    "EMERGENCY_ACCESS",
    "COMMERCIAL_CURB",
    "RESTRICTED_CURB",
}


@dataclass
class RestrictedZone:
    """A configured restricted zone for a camera."""
    id: str
    name: str
    zone_type: str
    polygon: Polygon
    camera_id: str
    allowed_vehicle_types: List[str]   # empty = none allowed
    max_duration_seconds: int          # 0 = no parking at all


@dataclass
class ZonePresence:
    """A vehicle currently inside a restricted zone."""
    track_id: int
    zone: RestrictedZone
    vehicle_category: str
    class_name: str
    confidence: float
    duration_seconds: float
    bbox: List[float]


def _point_in_polygon(bbox: List[float], zone_polygon: Polygon) -> bool:
    """
    Check if a vehicle bbox centroid is inside the zone polygon.
    Uses centroid rather than full IoU to handle partial overlaps cleanly.
    """
    x1, y1, x2, y2 = bbox
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    from shapely.geometry import Point
    return zone_polygon.contains(Point(cx, cy))


def load_zones(camera_config: dict) -> List[RestrictedZone]:
    """Parse restricted zones from the camera JSON config block.

    Supports both 'zones' and legacy 'restricted_zones' keys.
    Supports both 'zone_type' and legacy 'type' fields.
    """
    zones: List[RestrictedZone] = []
    cam_id = camera_config["id"]
    # Support both key names for backwards compatibility
    raw_zones = camera_config.get("zones", camera_config.get("restricted_zones", []))
    for z in raw_zones:
        # Support both field names
        zone_type = z.get("zone_type", z.get("type", ""))
        if zone_type not in ZONE_TYPES:
            log.warning("unknown_zone_type", zone_id=z["id"], type=zone_type)
            continue
        coords = [tuple(p) for p in z["polygon"]]
        if len(coords) < 3:
            log.warning("zone_polygon_too_small", zone_id=z["id"])
            continue
        zones.append(
            RestrictedZone(
                id=z["id"],
                name=z["name"],
                zone_type=zone_type,
                polygon=Polygon(coords),
                camera_id=cam_id,
                allowed_vehicle_types=z.get("allowed_vehicle_types", []),
                max_duration_seconds=z.get("max_duration_seconds", 120),
            )
        )
    log.info("zones_loaded", camera_id=cam_id, count=len(zones))
    return zones


class ZoneMonitor:
    """
    Checks which vehicles are inside restricted zones each frame.
    """

    def __init__(self, zones: List[RestrictedZone]) -> None:
        self._zones = zones

    def check(
        self,
        tracked_vehicles: List[TrackedVehicle],
        get_duration_fn,   # Callable[[int], float] — from tracker
    ) -> List[ZonePresence]:
        """
        Return a list of ZonePresence for all vehicles inside restricted zones.
        """
        presences: List[ZonePresence] = []

        for vehicle in tracked_vehicles:
            for zone in self._zones:
                if _point_in_polygon(vehicle.bbox, zone.polygon):
                    duration = get_duration_fn(vehicle.track_id)
                    presences.append(
                        ZonePresence(
                            track_id=vehicle.track_id,
                            zone=zone,
                            vehicle_category=vehicle.vehicle_category,
                            class_name=vehicle.class_name,
                            confidence=vehicle.confidence,
                            duration_seconds=duration,
                            bbox=vehicle.bbox,
                        )
                    )

        return presences
