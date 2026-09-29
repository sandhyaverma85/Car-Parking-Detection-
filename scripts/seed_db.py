"""
Database seed script — creates initial admin user and sample camera data.
Run once after database initialization.

Usage:
    cd backend
    .venv\\Scripts\\activate
    python scripts/seed_db.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

# pyrefly: ignore [missing-import]
from app.database import AsyncSessionLocal, engine
# pyrefly: ignore [missing-import]
from app.models.models import (
    Base, Camera, CameraSourceType, CameraStatus,
    ParkingZone, ParkingSlot, SlotStatus, User, UserRole
)
# pyrefly: ignore [missing-import]
from app.auth.auth import hash_password


async def seed() -> None:
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if officer already exists
        # pyrefly: ignore [missing-import]
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == "officer@smartparking.com"))
        if result.scalar_one_or_none():
            print("Officer user already exists. Skipping user seed.")
        else:
            # Create Parking Enforcement Officer user ONLY
            officer = User(
                name="Enforcement Officer",
                email="officer@smartparking.com",
                password_hash=hash_password("officer@smartparking.com"),
                role=UserRole.OFFICER,
            )
            db.add(officer)
            print("Created Parking Officer: " " / Officer@1234")

        # Check if CAM-001 exists
        cam_result = await db.execute(select(Camera).where(Camera.id == "CAM-001"))
        if not cam_result.scalar_one_or_none():
            # Create mall/building CCTV camera
            camera = Camera(
                id="CAM-001",
                name="Nexus Grand Mall — Floor B1 (Pillars C01–C15)",
                source_type=CameraSourceType.FILE,
                secure_source_reference="VIDEO_FILE_PATH",
                latitude=12.9716,
                longitude=77.5946,
                status=CameraStatus.ACTIVE,
            )
            db.add(camera)
            await db.flush()

            # Create mall parking zones with floor and pillar references
            zone1 = ParkingZone(
                camera_id="CAM-001",
                name="Nexus Mall · Floor B1 (Pillars A01–A05)",
                capacity=5,
            )
            db.add(zone1)
            await db.flush()

            # Create parking slots with pillar assignments
            pillars = ["Pillar A-01", "Pillar A-02", "Pillar A-03", "Pillar A-04", "Pillar A-05"]
            for i in range(1, 6):
                slot = ParkingSlot(
                    zone_id=zone1.id,
                    slot_number=i,
                    status=SlotStatus.EMPTY,
                )
                db.add(slot)

            await db.commit()

        print("[OK] Seed complete! Dedicated Parking Officer system active.")
        print("   Parking Officer: officer@smartparking.com / Officer@1234")


if __name__ == "__main__":
    asyncio.run(seed())
