"""Parking zones router — public occupancy + citizen nearby API."""

from __future__ import annotations

import math
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import OccupancyLog, ParkingSlot, ParkingZone, Camera
from app.schemas.schemas import NearbyParkingResult, ParkingZoneOut

router = APIRouter(prefix="/api/v1/parking", tags=["parking"])


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine formula — distance in km between two WGS84 coordinates."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


@router.get("/", response_model=List[ParkingZoneOut])
async def list_parking_zones(db: AsyncSession = Depends(get_db)):
    """List all parking zones with occupancy (public endpoint)."""
    result = await db.execute(select(ParkingZone))
    return result.scalars().all()


@router.get("/nearby", response_model=List[NearbyParkingResult])
async def nearby_parking(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(default=1.0, ge=0.1, le=50.0),
    db: AsyncSession = Depends(get_db),
):
    """
    Citizen-facing: Find nearby parking with real-time availability.
    Returns parking availability only — no enforcement data.
    """
    # Get all zones with their cameras' coordinates
    stmt = select(ParkingZone, Camera).join(Camera, ParkingZone.camera_id == Camera.id)
    result = await db.execute(stmt)
    rows = result.all()

    output: List[NearbyParkingResult] = []
    for zone, camera in rows:
        if camera.latitude is None or camera.longitude is None:
            continue
        dist = _haversine_km(latitude, longitude, camera.latitude, camera.longitude)
        if dist > radius_km:
            continue

        # Get slot statuses
        slots_result = await db.execute(
            select(ParkingSlot).where(ParkingSlot.zone_id == zone.id)
        )
        slots = slots_result.scalars().all()
        total = len(slots)
        occupied = sum(1 for s in slots if s.status.value == "OCCUPIED")
        available = total - occupied
        pct = (occupied / total * 100) if total > 0 else 0.0

        output.append(NearbyParkingResult(
            parking_id=zone.id,
            name=zone.name,
            latitude=camera.latitude,
            longitude=camera.longitude,
            total_spaces=total,
            available_spaces=available,
            occupied_spaces=occupied,
            occupancy_percentage=round(pct, 1),
            distance_km=round(dist, 3),
        ))

    output.sort(key=lambda x: x.distance_km or 0)
    return output


@router.get("/{zone_id}", response_model=ParkingZoneOut)
async def get_parking_zone(zone_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific parking zone."""
    result = await db.execute(select(ParkingZone).where(ParkingZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if zone is None:
        raise HTTPException(status_code=404, detail="Parking zone not found")
    return zone
