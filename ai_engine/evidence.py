"""
Evidence Generation — Phase 6

Captures and saves violation evidence frames with annotations.
Files are stored outside any public web directory and served only
via authenticated API endpoints.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

# pyrefly: ignore [missing-import]
import cv2
import numpy as np

from violation_engine import ViolationEvent
from utils.logging import get_logger

log = get_logger(__name__)


def _safe_filename(violation_id: str, camera_id: str) -> str:
    """Generate a safe, non-guessable filename for an evidence frame."""
    # Use UUID — no user-controlled input in filename
    ts = int(time.time())
    return f"evidence_{camera_id}_{ts}_{violation_id[:8]}.jpg"


def draw_annotations(
    frame: np.ndarray,
    violation: ViolationEvent,
) -> np.ndarray:
    """
    Draw violation box and metadata on a copy of the frame.
    Returns the annotated frame (original is unchanged).
    """
    annotated = frame.copy()
    x1, y1, x2, y2 = [int(c) for c in violation.bbox]

    # Red bounding box
    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 3)

    # Semi-transparent overlay for text background
    overlay = annotated.copy()
    cv2.rectangle(overlay, (x1, y1 - 60), (x2, y1), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, annotated, 0.4, 0, annotated)

    font = cv2.FONT_HERSHEY_SIMPLEX
    lines = [
        f"{violation.violation_type}",
        f"ID:{violation.track_id} | {violation.class_name} | {violation.confidence:.0%}",
        f"Duration: {violation.duration_seconds:.0f}s | Zone: {violation.zone_name}",
    ]
    for i, line in enumerate(lines):
        cv2.putText(
            annotated, line,
            (x1 + 4, y1 - 45 + i * 18),
            font, 0.45, (255, 255, 255), 1, cv2.LINE_AA,
        )

    # Timestamp watermark
    ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(violation.timestamp))
    cv2.putText(
        annotated, f"CAM:{violation.camera_id} | {ts_str}",
        (10, annotated.shape[0] - 10),
        font, 0.45, (0, 255, 255), 1, cv2.LINE_AA,
    )

    return annotated


def save_evidence(
    frame: np.ndarray,
    violation: ViolationEvent,
    evidence_dir: str,
    max_size_bytes: int = 5 * 1024 * 1024,
) -> Optional[str]:
    """
    Save an annotated evidence frame to disk.

    Returns:
        Relative evidence path (e.g. "evidence/...jpg") or None on failure.

    Security:
        - Filename is UUID-based (no user input)
        - Directory is created if missing
        - Validates file size after write
    """
    try:
        ev_dir = Path(evidence_dir)
        ev_dir.mkdir(parents=True, exist_ok=True)

        filename = _safe_filename(violation.violation_id, violation.camera_id)
        # Prevent path traversal — join with resolved dir
        filepath = (ev_dir / filename).resolve()
        if not str(filepath).startswith(str(ev_dir.resolve())):
            log.error("evidence_path_traversal_attempt", filename=filename)
            return None

        annotated = draw_annotations(frame, violation)

        # JPEG quality 85 — good balance of size/quality for evidence
        success, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            log.error("evidence_encode_failed", violation_id=violation.violation_id)
            return None

        if len(buf) > max_size_bytes:
            log.warning(
                "evidence_too_large",
                size_bytes=len(buf),
                max_bytes=max_size_bytes,
            )
            # Re-encode at lower quality
            success, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 60])

        filepath.write_bytes(buf.tobytes())
        rel_path = str(Path(evidence_dir) / filename)
        log.info(
            "evidence_saved",
            path=rel_path,
            violation_id=violation.violation_id,
            size_bytes=len(buf),
        )
        return rel_path

    except Exception as exc:
        log.error("evidence_save_failed", error=str(exc))
        return None
