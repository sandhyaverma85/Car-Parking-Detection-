"""
YOLO Vehicle Detector — Phase 2

Wraps Ultralytics YOLO for vehicle detection.
Returns structured Detection objects; does NOT contain tracking or rule logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np

from config import get_ai_settings
from utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class Detection:
    """Single vehicle detection result from one frame."""
    bbox: List[float]          # [x1, y1, x2, y2] in pixel coords
    confidence: float
    class_id: int
    class_name: str
    vehicle_category: str      # PRIVATE / COMMERCIAL / EMERGENCY / UNKNOWN


# COCO class ID → display name mapping (subset we care about)
_COCO_NAMES: dict[int, str] = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

# Vehicle category mapping
_CATEGORY_MAP: dict[str, str] = {
    "car":        "PRIVATE",
    "motorcycle": "PRIVATE",
    "bus":        "COMMERCIAL",
    "truck":      "COMMERCIAL",
    # Future custom classes can be added here
    "ambulance":  "EMERGENCY",
    "fire_truck": "EMERGENCY",
}


class VehicleDetector:
    """
    YOLO-based vehicle detector.

    Usage:
        detector = VehicleDetector()
        detections = detector.detect(frame)
    """

    def __init__(self) -> None:
        settings = get_ai_settings()
        self._conf = settings.confidence_threshold
        self._iou = settings.iou_threshold
        self._class_ids = settings.vehicle_class_id_list
        self._inference_width = settings.inference_width
        self._model = self._load_model(settings.model_path)

    def _load_model(self, model_path: str):
        """Load YOLO model. Downloads weights automatically if not present."""
        try:
            from ultralytics import YOLO  # type: ignore
            path = Path(model_path)
            model = YOLO(str(path))
            log.info("yolo_model_loaded", model=model_path)
            return model
        except Exception as exc:
            log.error("yolo_model_load_failed", error=str(exc))
            raise

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Run inference on a single frame.

        Args:
            frame: BGR frame from OpenCV (H × W × 3).

        Returns:
            List of Detection objects for vehicle classes only.
        """
        if self._model is None:
            return []

        # Resize width if configured (keeps aspect ratio)
        if self._inference_width > 0:
            h, w = frame.shape[:2]
            scale = self._inference_width / w
            # pyrefly: ignore [missing-import]
            import cv2
            frame = cv2.resize(frame, (self._inference_width, int(h * scale)))

        results = self._model(
            frame,
            conf=self._conf,
            iou=self._iou,
            classes=self._class_ids,
            verbose=False,
        )

        detections: List[Detection] = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                cls_name = _COCO_NAMES.get(cls_id, f"class_{cls_id}")
                category = _CATEGORY_MAP.get(cls_name, "UNKNOWN")

                detections.append(
                    Detection(
                        bbox=xyxy,
                        confidence=conf,
                        class_id=cls_id,
                        class_name=cls_name,
                        vehicle_category=category,
                    )
                )

        return detections
