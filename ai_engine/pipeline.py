"""
Full AI Processing Pipeline — Phase 6

Orchestrates: Video → YOLO → ByteTrack → Parking → Zones → Violations → Evidence → Backend POST

This is the main entry point for the AI engine.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
import httpx

from config import get_ai_settings
from parking import ParkingOccupancyMonitor, load_parking_slots
from violation_engine import ViolationRuleEngine, ViolationEvent
from zones import ZoneMonitor, load_zones
from evidence import save_evidence
from utils.logging import get_logger, setup_logging

log = get_logger(__name__)


def _open_source(settings) -> cv2.VideoCapture:
    """Open the configured video source."""
    src_type = settings.video_source_type
    if src_type == "file":
        path = settings.video_file_path
        if not Path(path).exists():
            log.error("video_file_not_found", path=path)
            sys.exit(1)
        cap = cv2.VideoCapture(path)
    elif src_type == "webcam":
        cap = cv2.VideoCapture(settings.webcam_index)
    elif src_type == "rtsp":
        # RTSP URL contains credentials — never log it
        cap = cv2.VideoCapture(settings.rtsp_url)
        log.info("rtsp_source_opened")  # intentionally no URL in log
    else:
        log.error("unknown_source_type", type=src_type)
        sys.exit(1)

    if not cap.isOpened():
        log.error("video_source_failed_to_open", type=src_type)
        sys.exit(1)

    log.info("video_source_opened", type=src_type)
    return cap


def _post_occupancy(client: httpx.Client, settings, occupancy) -> None:
    """POST parking occupancy update to the backend."""
    try:
        payload = {
            "camera_id": occupancy.camera_id,
            "total": occupancy.total,
            "occupied": occupancy.occupied,
            "available": occupancy.available,
            "occupancy_percentage": occupancy.occupancy_percentage,
            "timestamp": time.time(),
        }
        client.post(
            f"{settings.backend_base_url}/api/v1/live/occupancy",
            json=payload,
            headers={"X-AI-Key": settings.ai_internal_api_key},
            timeout=2.0,
        )
    except Exception:
        pass  # Non-fatal: backend may be starting up


def _post_violation(client: httpx.Client, settings, violation: ViolationEvent) -> None:
    """POST a new violation to the backend."""
    try:
        payload = {
            "violation_id": violation.violation_id,
            "camera_id": violation.camera_id,
            "track_id": violation.track_id,
            "violation_type": violation.violation_type,
            "zone_id": violation.zone_id,
            "zone_name": violation.zone_name,
            "vehicle_category": violation.vehicle_category,
            "class_name": violation.class_name,
            "confidence": violation.confidence,
            "duration_seconds": violation.duration_seconds,
            "evidence_path": violation.evidence_path,
            "timestamp": violation.timestamp,
        }
        client.post(
            f"{settings.backend_base_url}/api/v1/live/violation",
            json=payload,
            headers={"X-AI-Key": settings.ai_internal_api_key},
            timeout=2.0,
        )
    except Exception:
        pass 


def run_pipeline(camera_config: dict, settings) -> None:
    """Run the full AI pipeline for one camera."""
    cam_id = camera_config["id"]
    log.info("pipeline_start", camera_id=cam_id)

    # Load model + tracker (imported here to allow unit testing without GPU)
    from ultralytics import YOLO  # type: ignore
    model = YOLO(settings.model_path)
    from tracker import VehicleTracker
    tracker = VehicleTracker(model)

    # Load zone/slot configuration
    slots = load_parking_slots(camera_config)
    zones = load_zones(camera_config)
    occupancy_monitor = ParkingOccupancyMonitor(slots, settings.parking_overlap_threshold)
    zone_monitor = ZoneMonitor(zones)
    rule_engine = ViolationRuleEngine()

    cap = _open_source(settings)
    frame_idx = 0

    with httpx.Client() as http_client:
        while True:
            ret, frame = cap.read()
            if not ret:
                log.info("video_stream_ended", camera_id=cam_id)
                break

            frame_idx += 1
            # Skip frames to reduce CPU/GPU load
            if frame_idx % settings.frame_skip != 0:
                continue

            # ── Detection + Tracking ──────────────────────────────────────
            tracked = tracker.track(
                frame,
                conf=settings.confidence_threshold,
                iou=settings.iou_threshold,
                class_ids=settings.vehicle_class_id_list,
                inference_width=settings.inference_width,
            )

            # ── Parking Occupancy ─────────────────────────────────────────
            occupancy = occupancy_monitor.evaluate(tracked)
            _post_occupancy(http_client, settings, occupancy)

            # ── Zone / Violation Check ────────────────────────────────────
            presences = zone_monitor.check(tracked, tracker.get_duration)
            violations = rule_engine.evaluate(presences)

            for violation in violations:
                ev_path = save_evidence(
                    frame, violation,
                    settings.evidence_dir,
                    settings.evidence_max_size_bytes
                    if hasattr(settings, "evidence_max_size_bytes") else 5 * 1024 * 1024,
                )
                violation.evidence_path = ev_path
                _post_violation(http_client, settings, violation)

    cap.release()
    log.info("pipeline_done", camera_id=cam_id)


def main() -> None:
    settings = get_ai_settings()
    setup_logging(settings.log_level)

    config_path = Path("data/configs/cameras.json")
    with config_path.open() as f:
        cam_config = json.load(f)

    cameras = cam_config.get("cameras", [])
    if not cameras:
        log.error("no_cameras_configured")
        sys.exit(1)

    # MVP: process first configured camera
    # Multi-camera: run each in a separate thread/process
    run_pipeline(cameras[0], settings)


if __name__ == "__main__":
    main()
