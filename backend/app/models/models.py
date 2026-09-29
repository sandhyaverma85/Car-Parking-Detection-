"""
ORM models — all database tables.

Uses SQLAlchemy 2.x declarative style with type annotations.
PostGIS geometry columns use GeoAlchemy2.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geometry  # type: ignore
from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text, func, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.config import get_settings

try:
    _is_sqlite = get_settings().database_url.startswith("sqlite")
except Exception:
    _is_sqlite = False

_PolygonType = Text if _is_sqlite else Geometry("POLYGON", srid=4326)
_PointType = Text if _is_sqlite else Geometry("POINT", srid=4326)


# ── Enums ──────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    CITIZEN = "CITIZEN"
    OFFICER = "OFFICER"
    ADMIN = "ADMIN"


class CameraStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"


class CameraSourceType(str, enum.Enum):
    FILE = "file"
    WEBCAM = "webcam"
    RTSP = "rtsp"


class SlotStatus(str, enum.Enum):
    EMPTY = "EMPTY"
    OCCUPIED = "OCCUPIED"


class VehicleCategory(str, enum.Enum):
    PRIVATE = "PRIVATE"
    COMMERCIAL = "COMMERCIAL"
    EMERGENCY = "EMERGENCY"
    UNKNOWN = "UNKNOWN"


class ViolationStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class ViolationType(str, enum.Enum):
    NO_PARKING = "NO_PARKING"
    FIRE_HYDRANT_BLOCKED = "FIRE_HYDRANT_BLOCKED"
    EMERGENCY_ACCESS_BLOCKED = "EMERGENCY_ACCESS_BLOCKED"
    BUS_STOP_VIOLATION = "BUS_STOP_VIOLATION"
    RESTRICTED_CURB_VIOLATION = "RESTRICTED_CURB_VIOLATION"


# ── Tables ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.CITIZEN)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[CameraSourceType] = mapped_column(Enum(CameraSourceType), nullable=False)
    # Store a reference key to the secret (e.g. env var name), NOT the RTSP URL
    secure_source_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[CameraStatus] = mapped_column(Enum(CameraStatus), default=CameraStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parking_zones: Mapped[list["ParkingZone"]] = relationship("ParkingZone", back_populates="camera")
    vehicles: Mapped[list["Vehicle"]] = relationship("Vehicle", back_populates="camera")
    violations: Mapped[list["Violation"]] = relationship("Violation", back_populates="camera")


class ParkingZone(Base):
    __tablename__ = "parking_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    camera_id: Mapped[str] = mapped_column(String(64), ForeignKey("cameras.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # PostGIS polygon (WGS84 for geographic queries)
    polygon: Mapped[str | None] = mapped_column(_PolygonType, nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    camera: Mapped["Camera"] = relationship("Camera", back_populates="parking_zones")
    slots: Mapped[list["ParkingSlot"]] = relationship("ParkingSlot", back_populates="zone")
    occupancy_logs: Mapped[list["OccupancyLog"]] = relationship("OccupancyLog", back_populates="zone")


class ParkingSlot(Base):
    __tablename__ = "parking_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    zone_id: Mapped[int] = mapped_column(Integer, ForeignKey("parking_zones.id"), nullable=False, index=True)
    slot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    polygon: Mapped[str | None] = mapped_column(_PolygonType, nullable=True)
    status: Mapped[SlotStatus] = mapped_column(Enum(SlotStatus), default=SlotStatus.EMPTY)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    zone: Mapped["ParkingZone"] = relationship("ParkingZone", back_populates="slots")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    camera_id: Mapped[str] = mapped_column(String(64), ForeignKey("cameras.id"), nullable=False, index=True)
    track_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    vehicle_type: Mapped[VehicleCategory] = mapped_column(Enum(VehicleCategory), default=VehicleCategory.UNKNOWN)
    class_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    camera: Mapped["Camera"] = relationship("Camera", back_populates="vehicles")
    violations: Mapped[list["Violation"]] = relationship("Violation", back_populates="vehicle")

    __table_args__ = (
        Index("ix_vehicles_camera_track", "camera_id", "track_id"),
    )


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    camera_id: Mapped[str] = mapped_column(String(64), ForeignKey("cameras.id"), nullable=False, index=True)
    vehicle_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=True)
    violation_type: Mapped[ViolationType] = mapped_column(Enum(ViolationType), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    # PostGIS point for map display
    location: Mapped[str | None] = mapped_column(_PointType, nullable=True)
    # Relative path to evidence file — NOT the full filesystem path
    evidence_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ViolationStatus] = mapped_column(
        Enum(ViolationStatus), default=ViolationStatus.PENDING_REVIEW, index=True
    )
    zone_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    zone_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    track_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Officer who reviewed (if any)
    reviewed_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    camera: Mapped["Camera"] = relationship("Camera", back_populates="violations")
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="violations")

    __table_args__ = (
        Index("ix_violations_timestamp_status", "timestamp", "status"),
    )


class OccupancyLog(Base):
    __tablename__ = "occupancy_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    zone_id: Mapped[int] = mapped_column(Integer, ForeignKey("parking_zones.id"), nullable=False, index=True)
    occupied: Mapped[int] = mapped_column(Integer, nullable=False)
    available: Mapped[int] = mapped_column(Integer, nullable=False)
    occupancy_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    zone: Mapped["ParkingZone"] = relationship("ParkingZone", back_populates="occupancy_logs")

    __table_args__ = (
        Index("ix_occupancy_logs_zone_timestamp", "zone_id", "timestamp"),
    )
