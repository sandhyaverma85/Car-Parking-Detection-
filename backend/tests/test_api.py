"""
Comprehensive integration tests for the Smart Parking & Curb Management API.
Tests cover:
- Health check
- Authentication (login, signup, admin registration, edge cases)
- Role-Based Access Control (Public vs Citizen vs Officer vs Admin)
- Parking & Nearby Geo-search endpoints
- Violations management & status updates
- Internal AI engine live event ingestion (occupancy & violations)
- Analytics endpoints
- User profile & management
"""

from __future__ import annotations

import os
from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth.auth import create_access_token, hash_password
from app.database import Base, get_db
from app.main import app
from app.models.models import (
    Camera,
    CameraSourceType,
    CameraStatus,
    OccupancyLog,
    ParkingSlot,
    ParkingZone,
    SlotStatus,
    User,
    UserRole,
    Vehicle,
    VehicleCategory,
    Violation,
    ViolationStatus,
    ViolationType,
)


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
def disable_rate_limiting():
    """Disable slowapi rate limiter during automated testing."""
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = False
    yield
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = True


@pytest.fixture(autouse=True)
async def setup_test_db():
    """Create fresh tables and seed baseline fixtures before each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed baseline users, camera, zone, and slots
    async with TestingSessionLocal() as session:
        admin = User(
            id=1,
            name="Admin User",
            email="admin@test.com",
            password_hash=hash_password("Admin@1234"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        officer = User(
            id=2,
            name="Traffic Officer",
            email="officer@test.com",
            password_hash=hash_password("Officer@1234"),
            role=UserRole.OFFICER,
            is_active=True,
        )
        citizen = User(
            id=3,
            name="Citizen Driver",
            email="citizen@test.com",
            password_hash=hash_password("Citizen@1234"),
            role=UserRole.CITIZEN,
            is_active=True,
        )
        session.add_all([admin, officer, citizen])

        camera = Camera(
            id="CAM-001",
            name="MG Road Junction",
            source_type=CameraSourceType.FILE,
            secure_source_reference="VIDEO_FILE_PATH",
            latitude=12.9716,
            longitude=77.5946,
            status=CameraStatus.ACTIVE,
        )
        session.add(camera)
        await session.flush()

        zone = ParkingZone(
            id=1,
            camera_id="CAM-001",
            name="MG Road Zone A",
            capacity=5,
        )
        session.add(zone)
        await session.flush()

        for i in range(1, 6):
            slot = ParkingSlot(
                id=i,
                zone_id=1,
                slot_number=i,
                status=SlotStatus.OCCUPIED if i <= 2 else SlotStatus.EMPTY,
            )
            session.add(slot)

        await session.commit()

    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def admin_headers():
    token, _ = create_access_token(user_id=1, role=UserRole.ADMIN.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def officer_headers():
    token, _ = create_access_token(user_id=2, role=UserRole.OFFICER.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def citizen_headers():
    token, _ = create_access_token(user_id=3, role=UserRole.CITIZEN.value)
    return {"Authorization": f"Bearer {token}"}


# ── Health Check ─────────────────────────────────────────────────────────────

class TestHealth:
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


# ── Authentication ───────────────────────────────────────────────────────────

class TestAuth:
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@test.com", "password": "Admin@1234"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@test.com", "password": "WrongPassword"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unknown_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@test.com", "password": "SomePassword"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_public_signup_creates_citizen(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "name": "New Citizen",
                "email": "newcitizen@test.com",
                "password": "Password@1234",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newcitizen@test.com"
        assert data["role"] == "CITIZEN"

    @pytest.mark.asyncio
    async def test_public_signup_duplicate_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "name": "Duplicate Admin",
                "email": "admin@test.com",
                "password": "Password@1234",
            },
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_admin_can_register_officer(self, client: AsyncClient, admin_headers: dict):
        response = await client.post(
            "/api/v1/auth/register",
            headers=admin_headers,
            json={
                "name": "Officer Two",
                "email": "officer2@test.com",
                "password": "Password@1234",
                "role": "OFFICER",
            },
        )
        assert response.status_code == 201
        assert response.json()["role"] == "OFFICER"

    @pytest.mark.asyncio
    async def test_officer_cannot_register_user(self, client: AsyncClient, officer_headers: dict):
        response = await client.post(
            "/api/v1/auth/register",
            headers=officer_headers,
            json={
                "name": "Officer Three",
                "email": "officer3@test.com",
                "password": "Password@1234",
                "role": "OFFICER",
            },
        )
        assert response.status_code == 403


# ── Role-Based Access Control (RBAC) ─────────────────────────────────────────

class TestRBAC:
    @pytest.mark.asyncio
    async def test_public_can_view_parking(self, client: AsyncClient):
        response = await client.get("/api/v1/parking/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_citizen_cannot_view_cameras(self, client: AsyncClient, citizen_headers: dict):
        response = await client.get("/api/v1/cameras/", headers=citizen_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_citizen_cannot_view_violations(self, client: AsyncClient, citizen_headers: dict):
        response = await client.get("/api/v1/violations/", headers=citizen_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_citizen_cannot_view_users(self, client: AsyncClient, citizen_headers: dict):
        response = await client.get("/api/v1/users/", headers=citizen_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_officer_can_view_cameras_and_violations(self, client: AsyncClient, officer_headers: dict):
        cam_res = await client.get("/api/v1/cameras/", headers=officer_headers)
        assert cam_res.status_code == 200
        viol_res = await client.get("/api/v1/violations/", headers=officer_headers)
        assert viol_res.status_code == 200

    @pytest.mark.asyncio
    async def test_officer_can_access_camera_footage(self, client: AsyncClient, officer_headers: dict):
        response = await client.get("/api/v1/cameras/CAM-001/footage", headers=officer_headers)
        assert response.status_code == 200
        assert response.headers.get("content-type") == "video/mp4"

    @pytest.mark.asyncio
    async def test_citizen_cannot_access_camera_footage(self, client: AsyncClient, citizen_headers: dict):
        response = await client.get("/api/v1/cameras/CAM-001/footage", headers=citizen_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access_camera_footage(self, client: AsyncClient):
        response = await client.get("/api/v1/cameras/CAM-001/footage")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_officer_cannot_view_users(self, client: AsyncClient, officer_headers: dict):
        response = await client.get("/api/v1/users/", headers=officer_headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_view_users(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/api/v1/users/", headers=admin_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 3

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, client: AsyncClient):
        response = await client.get("/api/v1/cameras/", headers={"Authorization": "Bearer badtoken"})
        assert response.status_code == 401


# ── Parking & Nearby Search ──────────────────────────────────────────────────

class TestParking:
    @pytest.mark.asyncio
    async def test_list_parking_zones(self, client: AsyncClient):
        response = await client.get("/api/v1/parking/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "MG Road Zone A"

    @pytest.mark.asyncio
    async def test_get_parking_zone_by_id(self, client: AsyncClient):
        response = await client.get("/api/v1/parking/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1

    @pytest.mark.asyncio
    async def test_get_nonexistent_parking_zone(self, client: AsyncClient):
        response = await client.get("/api/v1/parking/9999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_nearby_parking_matches_close_coordinates(self, client: AsyncClient):
        # Coordinates near Bangalore MG Road (12.9716, 77.5946)
        response = await client.get(
            "/api/v1/parking/nearby",
            params={"latitude": 12.9716, "longitude": 77.5946, "radius_km": 1.0},
        )
        assert response.status_code == 200
        results = response.json()
        assert len(results) >= 1
        assert results[0]["name"] == "MG Road Zone A"
        assert "distance_km" in results[0]
        assert results[0]["total_spaces"] == 5

    @pytest.mark.asyncio
    async def test_nearby_parking_empty_for_far_away(self, client: AsyncClient):
        # Coordinates in Delhi (~1700km away)
        response = await client.get(
            "/api/v1/parking/nearby",
            params={"latitude": 28.6139, "longitude": 77.2090, "radius_km": 5.0},
        )
        assert response.status_code == 200
        assert len(response.json()) == 0


# ── Violations Management ────────────────────────────────────────────────────

class TestViolations:
    @pytest.mark.asyncio
    async def test_list_and_update_violation(self, client: AsyncClient, officer_headers: dict):
        # Create a test violation directly in DB
        async with TestingSessionLocal() as session:
            veh = Vehicle(
                camera_id="CAM-001",
                track_id=10,
                vehicle_type=VehicleCategory.PRIVATE,
                class_name="car",
            )
            session.add(veh)
            await session.flush()

            v = Violation(
                camera_id="CAM-001",
                vehicle_id=veh.id,
                violation_type=ViolationType.NO_PARKING,
                duration_seconds=45.0,
                confidence=0.91,
                status=ViolationStatus.PENDING_REVIEW,
                zone_id="Z01",
                zone_name="No Parking Zone",
                track_id=10,
            )
            session.add(v)
            await session.commit()
            violation_id = v.id

        # List violations
        list_res = await client.get("/api/v1/violations/", headers=officer_headers)
        assert list_res.status_code == 200
        assert any(x["id"] == violation_id for x in list_res.json())

        # Update status to CONFIRMED
        patch_res = await client.patch(
            f"/api/v1/violations/{violation_id}/status",
            headers=officer_headers,
            json={"status": "CONFIRMED"},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "CONFIRMED"

    @pytest.mark.asyncio
    async def test_get_violation_not_found(self, client: AsyncClient, officer_headers: dict):
        response = await client.get("/api/v1/violations/9999", headers=officer_headers)
        assert response.status_code == 404


# ── Live Event Ingestion (AI Engine -> Backend) ──────────────────────────────

class TestLiveEventIngestion:
    @pytest.mark.asyncio
    async def test_receive_occupancy_event(self, client: AsyncClient):
        payload = {
            "camera_id": "CAM-001",
            "timestamp": 1727517600.0,
            "occupied": 4,
            "available": 1,
            "total": 5,
            "occupancy_percentage": 80.0,
        }
        response = await client.post(
            "/api/v1/live/occupancy",
            headers={"X-AI-Key": "dev-ai-key-local"},
            json=payload,
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_receive_occupancy_invalid_key_forbidden(self, client: AsyncClient):
        payload = {
            "camera_id": "CAM-001",
            "timestamp": 1727517600.0,
            "occupied": 3,
            "available": 2,
            "total": 5,
            "occupancy_percentage": 60.0,
        }
        response = await client.post(
            "/api/v1/live/occupancy",
            headers={"X-AI-Key": "wrong-key"},
            json=payload,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_receive_violation_event(self, client: AsyncClient, officer_headers: dict):
        payload = {
            "violation_id": "test-viol-001",
            "camera_id": "CAM-001",
            "track_id": 99,
            "violation_type": "FIRE_HYDRANT_BLOCKED",
            "zone_id": "Z02",
            "zone_name": "Hydrant Buffer",
            "vehicle_category": "PRIVATE",
            "class_name": "car",
            "confidence": 0.95,
            "duration_seconds": 12.5,
            "evidence_path": "evidence/CAM-001/test.jpg",
            "timestamp": 1727517600.0,
        }
        response = await client.post(
            "/api/v1/live/violation",
            headers={"X-AI-Key": "dev-ai-key-local"},
            json=payload,
        )
        assert response.status_code == 204

        # Verify it was persisted to DB
        viol_res = await client.get("/api/v1/violations/", headers=officer_headers)
        assert viol_res.status_code == 200
        records = [v for v in viol_res.json() if v["track_id"] == 99]
        assert len(records) == 1
        assert records[0]["violation_type"] == "FIRE_HYDRANT_BLOCKED"
        assert records[0]["status"] == "PENDING_REVIEW"


# ── Analytics Endpoints ──────────────────────────────────────────────────────

class TestAnalytics:
    @pytest.mark.asyncio
    async def test_violation_analytics_structure(self, client: AsyncClient, officer_headers: dict):
        response = await client.get("/api/v1/analytics/violations", headers=officer_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_violations_today" in data
        assert "total_violations_week" in data
        assert "violations_by_type" in data
        assert "occupancy_stats" in data

    @pytest.mark.asyncio
    async def test_occupancy_analytics_admin(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/api/v1/analytics/occupancy", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_occupancy_analytics_forbidden_for_officer(self, client: AsyncClient, officer_headers: dict):
        # /api/v1/analytics/occupancy requires ADMIN role
        response = await client.get("/api/v1/analytics/occupancy", headers=officer_headers)
        assert response.status_code == 403


# ── User Profile & Management ────────────────────────────────────────────────

class TestUsers:
    @pytest.mark.asyncio
    async def test_get_current_user_profile(self, client: AsyncClient, citizen_headers: dict):
        response = await client.get("/api/v1/users/me", headers=citizen_headers)
        assert response.status_code == 200
        assert response.json()["email"] == "citizen@test.com"

    @pytest.mark.asyncio
    async def test_admin_deactivate_user(self, client: AsyncClient, admin_headers: dict):
        # Deactivate citizen (id=3)
        response = await client.delete("/api/v1/users/3", headers=admin_headers)
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_admin_cannot_deactivate_self(self, client: AsyncClient, admin_headers: dict):
        # Admin is id=1
        response = await client.delete("/api/v1/users/1", headers=admin_headers)
        assert response.status_code == 400
