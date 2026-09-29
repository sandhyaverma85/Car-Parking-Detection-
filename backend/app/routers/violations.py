"""Violations router — officer/admin only."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_user, require_role
from app.database import get_db
from app.models.models import User, UserRole, Violation, ViolationStatus
from app.schemas.schemas import ViolationOut, ViolationStatusUpdate
from app.config import get_settings

router = APIRouter(prefix="/api/v1/violations", tags=["violations"])
settings = get_settings()


@router.get("/", response_model=List[ViolationOut])
async def list_violations(
    status: Optional[str] = Query(None),
    camera_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role(UserRole.OFFICER, UserRole.ADMIN)),
):
    """Officer/Admin: list violations with optional filters."""
    stmt = select(Violation).order_by(Violation.timestamp.desc()).limit(limit).offset(offset)
    if status:
        stmt = stmt.where(Violation.status == status)
    if camera_id:
        stmt = stmt.where(Violation.camera_id == camera_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{violation_id}", response_model=ViolationOut)
async def get_violation(
    violation_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role(UserRole.OFFICER, UserRole.ADMIN)),
):
    """Officer/Admin: get a specific violation."""
    result = await db.execute(select(Violation).where(Violation.id == violation_id))
    v = result.scalar_one_or_none()
    if v is None:
        raise HTTPException(status_code=404, detail="Violation not found")
    return v


@router.patch("/{violation_id}/status", response_model=ViolationOut)
async def update_violation_status(
    violation_id: int,
    body: ViolationStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.OFFICER, UserRole.ADMIN)),
):
    """Officer/Admin: confirm or reject a violation after review."""
    result = await db.execute(select(Violation).where(Violation.id == violation_id))
    v = result.scalar_one_or_none()
    if v is None:
        raise HTTPException(status_code=404, detail="Violation not found")

    v.status = ViolationStatus(body.status)
    v.reviewed_by = user.id
    v.reviewed_at = datetime.utcnow()
    await db.flush()
    await db.refresh(v)
    return v


@router.get("/{violation_id}/evidence")
async def get_evidence(
    violation_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role(UserRole.OFFICER, UserRole.ADMIN)),
):
    """
    Officer/Admin: serve the evidence image for a violation.

    Security: file path is looked up from DB (not user-supplied),
    and validated to be within the evidence directory.
    """
    result = await db.execute(select(Violation).where(Violation.id == violation_id))
    v = result.scalar_one_or_none()
    if v is None:
        raise HTTPException(status_code=404, detail="Violation not found")
    if not v.evidence_reference:
        raise HTTPException(status_code=404, detail="No evidence available")

    # Validate path stays within evidence dir
    ev_dir = Path(settings.evidence_dir).resolve()
    ev_path = Path(v.evidence_reference).resolve()
    if not str(ev_path).startswith(str(ev_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    if not ev_path.exists():
        raise HTTPException(status_code=404, detail="Evidence file not found")

    return FileResponse(str(ev_path), media_type="image/jpeg")
