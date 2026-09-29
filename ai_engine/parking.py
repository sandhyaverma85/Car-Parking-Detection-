"""
Parking Slot Occupancy — Phase 4

Determines which parking slots are occupied by computing the overlap
between vehicle bounding boxes and slot polygons using Shapely.
No deep learning required for the MVP.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from shapely.geometry import Polygon, box as shapely_box  # type: ignore

from tracker import TrackedVehicle
from utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class ParkingSlot:
    """Configuration for a single parking slot."""
    id: str
    slot_number: int
    polygon: Polygon
    camera_id: str


@dataclass
class SlotStatus:
    """Runtime occupancy status of a parking slot."""
    slot_id: str
    slot_number: int
    is_occupied: bool
    track_id: int | None      # which vehicle is occupying it (if any)
    camera_id: str


@dataclass
class ZoneOccupancy:
    """Summary occupancy metrics for a parking zone."""
    camera_id: str
    total: int
    occupied: int
    available: int
    occupancy_percentage: float
    slot_statuses: List[SlotStatus]


def _bbox_to_polygon(bbox: List[float]) -> Polygon:
    """Convert [x1, y1, x2, y2] bbox to a Shapely Polygon."""
    x1, y1, x2, y2 = bbox
    return shapely_box(x1, y1, x2, y2)


def _iou(poly_a: Polygon, poly_b: Polygon) -> float:
    """Compute IoU between two Shapely polygons."""
    if not poly_a.is_valid or not poly_b.is_valid:
        return 0.0
    intersection = poly_a.intersection(poly_b).area
    union = poly_a.union(poly_b).area
    return intersection / union if union > 0 else 0.0


def load_parking_slots(camera_config: dict) -> List[ParkingSlot]:
    """Parse parking slots from the camera JSON config block."""
    slots: List[ParkingSlot] = []
    cam_id = camera_config["id"]
    for s in camera_config.get("parking_slots", []):
        coords = [tuple(p) for p in s["polygon"]]
        if len(coords) < 3:
            log.warning("slot_polygon_too_small", slot_id=s["id"])
            continue
        slots.append(
            ParkingSlot(
                id=s["id"],
                slot_number=s["slot_number"],
                polygon=Polygon(coords),
                camera_id=cam_id,
            )
        )
    log.info("parking_slots_loaded", camera_id=cam_id, count=len(slots))
    return slots


class ParkingOccupancyMonitor:
    """
    Determines which parking slots are occupied each frame.

    Usage:
        monitor = ParkingOccupancyMonitor(slots, overlap_threshold=0.3)
        occupancy = monitor.evaluate(tracked_vehicles)
    """

    def __init__(self, slots: List[ParkingSlot], overlap_threshold: float = 0.3) -> None:
        self._slots = slots
        self._threshold = overlap_threshold

    def evaluate(self, tracked_vehicles: List[TrackedVehicle]) -> ZoneOccupancy:
        """
        Check each slot against current tracked vehicles.

        A slot is OCCUPIED if any vehicle bbox has IoU ≥ threshold with
        the slot polygon.
        """
        if not self._slots:
            return ZoneOccupancy(
                camera_id="", total=0, occupied=0, available=0,
                occupancy_percentage=0.0, slot_statuses=[]
            )

        camera_id = self._slots[0].camera_id
        statuses: List[SlotStatus] = []

        # Precompute vehicle polygons once
        vehicle_polys: List[Tuple[int, Polygon]] = [
            (v.track_id, _bbox_to_polygon(v.bbox))
            for v in tracked_vehicles
        ]

        for slot in self._slots:
            occupied = False
            occupying_track: int | None = None

            for track_id, v_poly in vehicle_polys:
                overlap = _iou(slot.polygon, v_poly)
                if overlap >= self._threshold:
                    occupied = True
                    occupying_track = track_id
                    break

            statuses.append(
                SlotStatus(
                    slot_id=slot.id,
                    slot_number=slot.slot_number,
                    is_occupied=occupied,
                    track_id=occupying_track,
                    camera_id=camera_id,
                )
            )

        total = len(statuses)
        occupied_count = sum(1 for s in statuses if s.is_occupied)
        available = total - occupied_count
        pct = (occupied_count / total * 100) if total > 0 else 0.0

        return ZoneOccupancy(
            camera_id=camera_id,
            total=total,
            occupied=occupied_count,
            available=available,
            occupancy_percentage=round(pct, 2),
            slot_statuses=statuses,
        )
