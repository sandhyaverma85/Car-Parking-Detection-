"""
Generates rich dynamic telemetry for both surveillance videos using YOLOv8n.
Extracts real vehicle detections, assigns realistic parking bays, vacant spots,
and dynamic violations for each keyframe.
"""

import json
from pathlib import Path
import cv2
# pyrefly: ignore [missing-import]
from ultralytics import YOLO

def process_video(video_path: str, feed_id: str, floor: str, total_bays: int, vacant_slots_def: list, violation_rules: list):
    path = Path(video_path)
    if not path.exists():
        print(f"Error: {video_path} does not exist")
        return None

    cap = cv2.VideoCapture(str(path))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    model = YOLO("yolov8n.pt")
    keyframes = []
    
    # Sample every 15 frames (~0.5s intervals)
    step = 15
    frame_idx = 0

    print(f"Processing {video_path} ({width}x{height}, {total_frames} frames)...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % step == 0:
            timestamp_sec = round(frame_idx / fps, 2)
            results = model(frame, conf=0.35, classes=[2, 3, 5, 7], verbose=False)[0]

            detections = []
            cars_count = 0
            trucks_count = 0
            motorcycles_count = 0

            for i, box in enumerate(results.boxes):
                cls_id = int(box.cls[0])
                cls_name = model.names[cls_id]
                conf = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                if cls_name in ["car", "van"]:
                    cars_count += 1
                elif cls_name in ["truck", "bus"]:
                    trucks_count += 1
                elif cls_name == "motorcycle":
                    motorcycles_count += 1

                left_pct = f"{(x1 / width) * 100:.1f}%"
                top_pct = f"{(y1 / height) * 100:.1f}%"
                w_pct = f"{((x2 - x1) / width) * 100:.1f}%"
                h_pct = f"{((y2 - y1) / height) * 100:.1f}%"

                detections.append({
                    "id": f"det-{frame_idx}-{i}",
                    "track_id": 4000 + i,
                    "class": cls_name,
                    "confidence": round(conf, 3),
                    "xyxy": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                    "css_rect": {
                        "left": left_pct,
                        "top": top_pct,
                        "width": w_pct,
                        "height": h_pct,
                    }
                })

            total_vehicles = len(detections)

            # Determine vacant slots for this feed
            vacant_slots = []
            for vs in vacant_slots_def:
                vacant_slots.append({
                    "slot_id": vs["slot_id"],
                    "pillar": vs["pillar"],
                    "css_rect": vs["css_rect"],
                    "type": "VACANT"
                })

            # Determine violations dynamically from detections
            violations = []
            for vr in violation_rules:
                # Find matching detection or trigger
                v_box = None
                matched_det = None
                for d in detections:
                    cx = (d["xyxy"][0] + d["xyxy"][2]) / 2 / width
                    cy = (d["xyxy"][1] + d["xyxy"][3]) / 2 / height
                    if vr["min_cx"] <= cx <= vr["max_cx"] and vr["min_cy"] <= cy <= vr["max_cy"]:
                        v_box = d["css_rect"]
                        matched_det = d
                        break

                if v_box or vr.get("always", False):
                    box_to_use = v_box or vr["fallback_css"]
                    violations.append({
                        "id": vr["id"],
                        "code": vr["code"],
                        "type": vr["type"],
                        "title": vr["title"],
                        "pillar": vr["pillar"],
                        "confidence": matched_det["confidence"] if matched_det else vr["default_conf"],
                        "track_id": matched_det["track_id"] if matched_det else vr.get("track_id", 4092),
                        "vehicle_type": matched_det["class"] if matched_det else "car",
                        "css_rect": box_to_use,
                        "time_ago": vr.get("time_ago", "Just now"),
                        "severity": vr.get("severity", "CRITICAL"),
                        "description": vr.get("description", "Vehicle violating parking protocol")
                    })

            occupied_bays = min(total_bays, total_vehicles)
            available_bays = max(0, total_bays - occupied_bays)
            occupancy_pct = round((occupied_bays / total_bays) * 100, 1)

            keyframes.append({
                "frame_index": frame_idx,
                "timestamp_sec": timestamp_sec,
                "total_vehicles": total_vehicles,
                "cars": cars_count,
                "trucks": trucks_count,
                "motorcycles": motorcycles_count,
                "total_bays": total_bays,
                "occupied_bays": occupied_bays,
                "available_bays": available_bays,
                "occupancy_percentage": occupancy_pct,
                "violations_count": len(violations),
                "detections": detections,
                "vacant_slots": vacant_slots,
                "violations": violations,
            })

        frame_idx += 1

    cap.release()

    peak_vehicles = max((k["total_vehicles"] for k in keyframes), default=0)

    telemetry = {
        "feed_id": feed_id,
        "floor": floor,
        "video_file": video_path,
        "resolution": f"{width}x{height}",
        "fps": fps,
        "total_frames": total_frames,
        "total_bays": total_bays,
        "peak_vehicles": peak_vehicles,
        "keyframes": keyframes,
    }

    return telemetry

def main():
    # ── Feed 1: car_video_02.mp4 (Floor B1 Basement) ────────
    # 12 Bays total in this monitored bay sector
    feed1_vacant = [
        {
            "slot_id": "BAY-B1-03",
            "pillar": "PILLAR A-03",
            "css_rect": { "left": "19.5%", "top": "50.5%", "width": "9.5%", "height": "16.0%" }
        },
        {
            "slot_id": "BAY-B1-07",
            "pillar": "PILLAR A-07",
            "css_rect": { "left": "44.5%", "top": "50.5%", "width": "8.5%", "height": "14.5%" }
        },
        {
            "slot_id": "BAY-B1-11",
            "pillar": "PILLAR A-11",
            "css_rect": { "left": "12.0%", "top": "51.0%", "width": "8.0%", "height": "14.0%" }
        }
    ]

    feed1_violations = [
        {
            "id": "viol-1",
            "code": "C12355-6890",
            "type": "DOUBLE_PARKING",
            "title": "Double Parking",
            "pillar": "PILLAR A-05",
            "min_cx": 0.65, "max_cx": 0.90,
            "min_cy": 0.60, "max_cy": 0.90,
            "fallback_css": { "left": "66.0%", "top": "66.0%", "width": "22.0%", "height": "24.0%" },
            "default_conf": 0.98,
            "track_id": 4092,
            "time_ago": "2m ago",
            "severity": "CRITICAL",
            "description": "Vehicle double parked obstructing stall egress"
        },
        {
            "id": "viol-2",
            "code": "U2E55-8758",
            "type": "UNAUTHORIZED_STOPPAGE",
            "title": "Unauthorized Aisle Stoppage",
            "pillar": "PILLAR A-08",
            "min_cx": 0.35, "max_cx": 0.65,
            "min_cy": 0.50, "max_cy": 0.85,
            "fallback_css": { "left": "38.0%", "top": "56.0%", "width": "26.0%", "height": "28.0%" },
            "default_conf": 0.965,
            "track_id": 4110,
            "time_ago": "4m ago",
            "severity": "HIGH",
            "description": "Commercial SUV halted in main circulation thoroughfare"
        }
    ]

    t1 = process_video("data/videos/car_video_02.mp4", "CAM-001", "B1", 12, feed1_vacant, feed1_violations)
    if t1:
        for out_path in ["data/video_telemetry.json", "frontend/public/data/video_telemetry.json", "frontend/public/data/video_telemetry_feed1.json"]:
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w") as f:
                json.dump(t1, f, indent=2)
        print("Wrote Feed 1 telemetry successfully.")

    # ── Feed 2: car_video_01.mp4 (Floor L2 Deck) ───────────
    # 8 Bays total
    feed2_vacant = [
        {
            "slot_id": "BAY-L2-02",
            "pillar": "PILLAR C-02",
            "css_rect": { "left": "15.0%", "top": "45.0%", "width": "16.0%", "height": "22.0%" }
        },
        {
            "slot_id": "BAY-L2-05",
            "pillar": "PILLAR C-05",
            "css_rect": { "left": "68.0%", "top": "45.0%", "width": "18.0%", "height": "22.0%" }
        },
        {
            "slot_id": "BAY-L2-07",
            "pillar": "PILLAR C-07",
            "css_rect": { "left": "42.0%", "top": "38.0%", "width": "14.0%", "height": "20.0%" }
        }
    ]

    feed2_violations = [
        {
            "id": "viol-3",
            "code": "E98211-3419",
            "type": "RESTRICTED_CURB_VIOLATION",
            "title": "Commercial Loading Overstay",
            "pillar": "PILLAR C-04",
            "min_cx": 0.20, "max_cx": 0.60,
            "min_cy": 0.40, "max_cy": 0.85,
            "fallback_css": { "left": "35.0%", "top": "50.0%", "width": "22.0%", "height": "25.0%" },
            "default_conf": 0.948,
            "track_id": 3108,
            "time_ago": "8m ago",
            "severity": "WARNING",
            "description": "Loading bay stay duration exceeded 15 minute limit"
        }
    ]

    t2 = process_video("data/videos/car_video_01.mp4", "CAM-002", "L2", 8, feed2_vacant, feed2_violations)
    if t2:
        for out_path in ["data/video_telemetry_feed2.json", "frontend/public/data/video_telemetry_feed2.json"]:
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w") as f:
                json.dump(t2, f, indent=2)
        print("Wrote Feed 2 telemetry successfully.")

if __name__ == "__main__":
    main()
