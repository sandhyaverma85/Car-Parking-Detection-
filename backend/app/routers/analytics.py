"""Analytics router — admin only, uses real stored data."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import require_role
from app.database import get_db
from app.models.models import (
    OccupancyLog, ParkingZone, UserRole, Violation, ViolationType
)
from app.schemas.schemas import AnalyticsSummary, OccupancyStats, ViolationStats

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/occupancy", response_model=List[OccupancyStats])
async def occupancy_analytics(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(UserRole.ADMIN)),
):
    """Admin: average and peak occupancy per zone from real logged data."""
    stmt = (
        select(
            OccupancyLog.zone_id,
            ParkingZone.name,
            func.avg(OccupancyLog.occupancy_percentage).label("avg_pct"),
            func.max(OccupancyLog.occupancy_percentage).label("peak_pct"),
            func.count(OccupancyLog.id).label("total_logs"),
        )
        .join(ParkingZone, OccupancyLog.zone_id == ParkingZone.id)
        .group_by(OccupancyLog.zone_id, ParkingZone.name)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        OccupancyStats(
            zone_id=r.zone_id,
            zone_name=r.name,
            average_occupancy_pct=round(float(r.avg_pct or 0), 1),
            peak_occupancy_pct=round(float(r.peak_pct or 0), 1),
            total_logs=r.total_logs,
        )
        for r in rows
    ]


@router.get("/violations", response_model=AnalyticsSummary)
async def violation_analytics(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(UserRole.OFFICER, UserRole.ADMIN)),
):
    """Officer/Admin: violation counts by type, today vs week."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    # Today's total
    today_count = await db.scalar(
        select(func.count(Violation.id)).where(Violation.timestamp >= today_start)
    )
    # Week total
    week_count = await db.scalar(
        select(func.count(Violation.id)).where(Violation.timestamp >= week_start)
    )

    # By type
    type_stmt = (
        select(Violation.violation_type, func.count(Violation.id).label("cnt"))
        .group_by(Violation.violation_type)
    )
    type_result = await db.execute(type_stmt)
    type_rows = type_result.all()
    total_all = sum(r.cnt for r in type_rows) or 1

    by_type = [
        ViolationStats(
            violation_type=r.violation_type.value if hasattr(r.violation_type, "value") else str(r.violation_type),
            count=r.cnt,
            percentage=round(r.cnt / total_all * 100, 1),
        )
        for r in type_rows
    ]

    # Occupancy stats
    occ_stmt = (
        select(
            OccupancyLog.zone_id,
            ParkingZone.name,
            func.avg(OccupancyLog.occupancy_percentage).label("avg_pct"),
            func.max(OccupancyLog.occupancy_percentage).label("peak_pct"),
            func.count(OccupancyLog.id).label("total_logs"),
        )
        .join(ParkingZone, OccupancyLog.zone_id == ParkingZone.id)
        .group_by(OccupancyLog.zone_id, ParkingZone.name)
    )
    occ_result = await db.execute(occ_stmt)
    occ_rows = occ_result.all()
    occ_stats = [
        OccupancyStats(
            zone_id=r.zone_id,
            zone_name=r.name,
            average_occupancy_pct=round(float(r.avg_pct or 0), 1),
            peak_occupancy_pct=round(float(r.peak_pct or 0), 1),
            total_logs=r.total_logs,
        )
        for r in occ_rows
    ]

    return AnalyticsSummary(
        total_violations_today=today_count or 0,
        total_violations_week=week_count or 0,
        violations_by_type=by_type,
        occupancy_stats=occ_stats,
    )
