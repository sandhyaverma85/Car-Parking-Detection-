"""Pydantic schemas for all API request/response models."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field   


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="CITIZEN")


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Cameras ────────────────────────────────────────────────────────────────────

class CameraOut(BaseModel):
    id: str
    name: str
    source_type: str
    latitude: Optional[float]
    longitude: Optional[float]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Parking ────────────────────────────────────────────────────────────────────

class ParkingZoneOut(BaseModel):
    id: int
    camera_id: str
    name: str
    capacity: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SlotStatusOut(BaseModel):
    id: int
    zone_id: int
    slot_number: int
    status: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class NearbyParkingResult(BaseModel):
    parking_id: int
    name: str
    latitude: Optional[float]
    longitude: Optional[float]
    total_spaces: int
    available_spaces: int
    occupied_spaces: int
    occupancy_percentage: float
    distance_km: Optional[float]


class NearbyParkingRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_km: float = Field(default=1.0, ge=0.1, le=50.0)


# ── Violations ────────────────────────────────────────────────────────────────

class ViolationOut(BaseModel):
    id: int
    camera_id: str
    violation_type: str
    timestamp: datetime
    duration_seconds: float
    confidence: float
    status: str
    zone_name: Optional[str]
    track_id: Optional[int]
    evidence_reference: Optional[str]

    model_config = {"from_attributes": True}


class ViolationStatusUpdate(BaseModel):
    status: str = Field(pattern="^(CONFIRMED|REJECTED)$")


# ── Live / AI Events (internal) ───────────────────────────────────────────────

class OccupancyEvent(BaseModel):
    camera_id: str
    total: int
    occupied: int
    available: int
    occupancy_percentage: float
    timestamp: float


class ViolationEvent(BaseModel):
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
    evidence_path: Optional[str]
    timestamp: float


# ── Analytics ─────────────────────────────────────────────────────────────────

class OccupancyStats(BaseModel):
    zone_id: int
    zone_name: str
    average_occupancy_pct: float
    peak_occupancy_pct: float
    total_logs: int


class ViolationStats(BaseModel):
    violation_type: str
    count: int
    percentage: float


class AnalyticsSummary(BaseModel):
    total_violations_today: int
    total_violations_week: int
    violations_by_type: List[ViolationStats]
    occupancy_stats: List[OccupancyStats]


# ── WebSocket Messages ────────────────────────────────────────────────────────

class WSMessage(BaseModel):
    type: str        # "occupancy_update" | "violation_alert" | "ping"
    payload: dict
