"""
ByteTrack Object Tracker — Phase 3

Uses Ultralytics' built-in ByteTrack integration so we don't need a
separate ByteTrack installation.  Produces TrackedVehicle objects that
combine detection + a stable track_id.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time

import numpy as np

from detector import Detection
from utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class TrackedVehicle:
    """A vehicle detection enriched with a stable ByteTrack ID."""
    track_id: int
    bbox: List[float]          # [x1, y1, x2, y2]
    confidence: float
    class_id: int
    class_name: str
    vehicle_category: str
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)


class VehicleTracker:
    """
    Wraps Ultralytics ByteTrack to assign stable IDs across frames.

    Ultralytics YOLO has ByteTrack built-in via model.track().
    We use that instead of installing a separate bytetrack package.
    """

    def __init__(self, model) -> None:
        """
        Args:
            model: The loaded Ultralytics YOLO model instance.
        """
        self._model = model
        # Cache: track_id → TrackedVehicle (for duration tracking)
        self._track_cache: Dict[int, TrackedVehicle] = {}

    def track(
        self,
        frame: np.ndarray,
        conf: float,
        iou: float,
        class_ids: List[int],
        inference_width: int,
    ) -> List[TrackedVehicle]:
        """
        Run detection + ByteTrack on a frame.

        Returns:
            List of TrackedVehicle with stable track_ids.
        """
        # Resize if configured
        if inference_width > 0:
            # pyrefly: ignore [missing-import]
            import cv2
            h, w = frame.shape[:2]
            scale = inference_width / w
            frame = cv2.resize(frame, (inference_width, int(h * scale)))

        results = self._model.track(
            frame,
            conf=conf,
            iou=iou,
            classes=class_ids,
            tracker="bytetrack.yaml",
            persist=True,
            verbose=False,
        )

        tracked: List[TrackedVehicle] = []
        now = time.time()

        for result in results:
            if result.boxes is None or result.boxes.id is None:
                continue

            boxes = result.boxes
            for i in range(len(boxes)):
                tid = int(boxes.id[i].item())
                cls_id = int(boxes.cls[i].item())
                conf_val = float(boxes.conf[i].item())
                xyxy = boxes.xyxy[i].tolist()

                from detector import _COCO_NAMES, _CATEGORY_MAP as CAT_MAP
                cls_name = _COCO_NAMES.get(cls_id, f"class_{cls_id}")
                category = CAT_MAP.get(cls_name, "UNKNOWN")

                if tid in self._track_cache:
                    vehicle = self._track_cache[tid]
                    vehicle.bbox = xyxy
                    vehicle.confidence = conf_val
                    vehicle.last_seen = now
                else:
                    vehicle = TrackedVehicle(
                        track_id=tid,
                        bbox=xyxy,
                        confidence=conf_val,
                        class_id=cls_id,
                        class_name=cls_name,
                        vehicle_category=category,
                        first_seen=now,
                        last_seen=now,
                    )
                    self._track_cache[tid] = vehicle
                    log.info("new_track", track_id=tid, class_name=cls_name)

                tracked.append(vehicle)

        # Remove stale tracks (not seen for > 5 seconds)
        stale = [tid for tid, v in self._track_cache.items()
                 if now - v.last_seen > 5.0]
        for tid in stale:
            del self._track_cache[tid]

        return tracked

    def get_duration(self, track_id: int) -> float:
        """Return how long (seconds) a track has been active."""
        v = self._track_cache.get(track_id)
        if v is None:
            return 0.0
        return time.time() - v.first_seen
