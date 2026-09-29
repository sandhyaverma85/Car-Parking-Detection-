"""
Sync video metadata, cameras, slots, and violations with database.
"""

import sqlite3
import os
import shutil

def sync():
    os.makedirs('frontend/public/data', exist_ok=True)
    os.makedirs('backend/data', exist_ok=True)

    if os.path.exists('data/video_telemetry.json'):
        shutil.copy2('data/video_telemetry.json', 'frontend/public/data/video_telemetry.json')
        shutil.copy2('data/video_telemetry.json', 'backend/data/video_telemetry.json')
    if os.path.exists('data/training_metrics.json'):
        shutil.copy2('data/training_metrics.json', 'frontend/public/data/training_metrics.json')
        shutil.copy2('data/training_metrics.json', 'backend/data/training_metrics.json')

    for db_path in ['backend/parking_dev.db', 'parking_dev.db']:
        if not os.path.exists(db_path):
            continue
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # 1. Update CAM-001 (car_video_02.mp4)
        cur.execute(
            "UPDATE cameras SET name = ?, status = 'ACTIVE' WHERE id = ?",
            ('MallPark CCTV-01 · Floor B1 (Pillars A01–A12)', 'CAM-001')
        )
        
        # 2. Insert or replace CAM-002 (car_video_01.mp4)
        cur.execute("""
            INSERT OR REPLACE INTO cameras (id, name, source_type, secure_source_reference, latitude, longitude, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('CAM-002', 'MallPark CCTV-02 · Floor L2 Curb (Pillars C01–C08)', 'FILE', 'VIDEO_FILE_PATH', 12.9720, 77.5950, 'ACTIVE'))
        
        # 3. Update zone for CAM-001
        cur.execute(
            "UPDATE parking_zones SET name = ?, capacity = ? WHERE camera_id = ?",
            ('Nexus Grand Mall · Floor B1 (Pillars A01–A12)', 16, 'CAM-001')
        )
        
        # 4. Check if CAM-002 zone exists
        cur.execute("SELECT id FROM parking_zones WHERE camera_id = 'CAM-002'")
        z2 = cur.fetchone()
        if not z2:
            cur.execute("""
                INSERT INTO parking_zones (camera_id, name, capacity)
                VALUES (?, ?, ?)
            """, ('CAM-002', 'Nexus Grand Mall · Floor L2 Curb Zone', 8))
            z2_id = cur.lastrowid
        else:
            z2_id = z2[0]

        # 5. Populate parking slots with pillars
        cur.execute("SELECT id FROM parking_zones WHERE camera_id = 'CAM-001'")
        z1 = cur.fetchone()
        if z1:
            z1_id = z1[0]
            for slot_num in range(1, 17):
                cur.execute("SELECT id FROM parking_slots WHERE zone_id = ? AND slot_number = ?", (z1_id, slot_num))
                if not cur.fetchone():
                    status = 'OCCUPIED' if slot_num in [1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 14, 15] else 'EMPTY'
                    cur.execute("""
                        INSERT INTO parking_slots (zone_id, slot_number, status, updated_at)
                        VALUES (?, ?, ?, datetime('now'))
                    """, (z1_id, slot_num, status))

        # 6. Add real video-linked violations
        violations = [
            ("CAM-001", "DOUBLE_PARKING", 240, 0.98, "DOUBLE PARKING · Pillar A-05", "INC-C12355-6890", "PENDING_REVIEW"),
            ("CAM-001", "UNAUTHORIZED_PARKING", 185, 0.965, "UNAUTHORIZED CURB OBSTRUCTION · Pillar A-08", "INC-U2E55-8758", "PENDING_REVIEW"),
            ("CAM-001", "OVERSTAY", 420, 0.948, "COMMERCIAL OVERSTAY · Pillar B-02", "INC-E90211-3419", "CITATION_ISSUED"),
        ]

        for cam_id, vtype, dur, conf, zname, trk, vstat in violations:
            cur.execute("SELECT id FROM violations WHERE track_id = ?", (trk,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO violations (
                        camera_id, violation_type, timestamp, duration_seconds, confidence,
                        evidence_reference, status, zone_name, track_id
                    ) VALUES (?, ?, datetime('now'), ?, ?, ?, ?, ?, ?)
                """, (cam_id, vtype, dur, conf, "evidence/sample.jpg", vstat, zname, trk))

        conn.commit()
        conn.close()
        print(f"[+] Successfully synced video and camera data with {db_path}")

if __name__ == "__main__":
    sync()
