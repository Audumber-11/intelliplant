import cv2
import numpy as np
import uuid
import asyncio
import base64
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from collections import defaultdict

from .schemas import (
    CameraConfig, DetectionResult, CVAlert, CameraStatus,
    CVSummary, DetectionType, DetectionSeverity, PPEElement
)


class CVDetectionEngine:
    """Simulated computer vision detection engine."""

    DETECTION_TEMPLATES = {
        DetectionType.PPE_VIOLATION: {
            "severity": DetectionSeverity.MEDIUM,
            "template": "PPE violation detected in {zone}: missing {items}",
        },
        DetectionType.FLAME_SMOKE: {
            "severity": DetectionSeverity.CRITICAL,
            "template": "Flame/smoke detected in {zone} at {location}",
        },
        DetectionType.UNAUTHORIZED_ACCESS: {
            "severity": DetectionSeverity.HIGH,
            "template": "Unauthorized personnel in restricted zone {zone}",
        },
        DetectionType.CROWD_GATHERING: {
            "severity": DetectionSeverity.MEDIUM,
            "template": "Crowd gathering detected in {zone}: {count} persons",
        },
        DetectionType.UNSAFE_BEHAVIOR: {
            "severity": DetectionSeverity.HIGH,
            "template": "Unsafe behavior in {zone}: {description}",
        },
        DetectionType.FALL_DETECTION: {
            "severity": DetectionSeverity.CRITICAL,
            "template": "Person down detected in {zone} — immediate response needed",
        },
        DetectionType.GAS_LEAK_VISUAL: {
            "severity": DetectionSeverity.CRITICAL,
            "template": "Visual gas leak indicator in {zone} at {location}",
        },
    }

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self._mock_frame_counters = defaultdict(int)

    async def process_frame(self, camera_id: str, zone: str, frame: Optional[np.ndarray] = None) -> List[DetectionResult]:
        if self.use_mock:
            return await self._mock_detect(camera_id, zone)
        return await self._real_detect(camera_id, zone, frame)

    async def _mock_detect(self, camera_id: str, zone: str) -> List[DetectionResult]:
        self._mock_frame_counters[camera_id] += 1
        frame_num = self._mock_frame_counters[camera_id]
        results = []

        if frame_num % 30 == 0:
            missing_ppe = []
            import random
            if random.random() < 0.3:
                missing_ppe.append(random.choice(list(PPEElement)).value)
            if random.random() < 0.2:
                missing_ppe.append(random.choice(list(PPEElement)).value)
            if missing_ppe:
                results.append(DetectionResult(
                    detection_id=str(uuid.uuid4()),
                    camera_id=camera_id,
                    detection_type=DetectionType.PPE_VIOLATION,
                    severity=DetectionSeverity.MEDIUM,
                    confidence=round(random.uniform(0.75, 0.98), 2),
                    timestamp=datetime.utcnow(),
                    zone=zone,
                    description=f"PPE violation: missing {', '.join(missing_ppe)}",
                    persons_detected=random.randint(1, 5),
                    ppe_violations=missing_ppe,
                ))

        if frame_num % 100 == 0:
            results.append(DetectionResult(
                detection_id=str(uuid.uuid4()),
                camera_id=camera_id,
                detection_type=DetectionType.FLAME_SMOKE,
                severity=DetectionSeverity.CRITICAL,
                confidence=round(random.uniform(0.85, 0.99), 2),
                timestamp=datetime.utcnow(),
                zone=zone,
                description=f"Flame detected near {zone} south sector",
                persons_detected=0,
            ))

        if frame_num % 50 == 0:
            import random
            if random.random() < 0.15:
                results.append(DetectionResult(
                    detection_id=str(uuid.uuid4()),
                    camera_id=camera_id,
                    detection_type=random.choice([
                        DetectionType.UNAUTHORIZED_ACCESS,
                        DetectionType.CROWD_GATHERING,
                        DetectionType.UNSAFE_BEHAVIOR,
                        DetectionType.FALL_DETECTION,
                    ]),
                    severity=random.choice([DetectionSeverity.HIGH, DetectionSeverity.CRITICAL]),
                    confidence=round(random.uniform(0.7, 0.95), 2),
                    timestamp=datetime.utcnow(),
                    zone=zone,
                    description=f"Simulated detection event in {zone}",
                    persons_detected=random.randint(1, 8),
                ))

        return results

    async def _real_detect(self, camera_id: str, zone: str, frame: np.ndarray) -> List[DetectionResult]:
        results = []
        if frame is None:
            return results

        height, width = frame.shape[:2]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lower_red = np.array([0, 50, 50])
        upper_red = np.array([10, 255, 255])
        red_mask = cv2.inRange(hsv, lower_red, upper_red)
        red_pixels = np.sum(red_mask > 0) / (height * width)

        if red_pixels > 0.05:
            results.append(DetectionResult(
                detection_id=str(uuid.uuid4()),
                camera_id=camera_id,
                detection_type=DetectionType.FLAME_SMOKE,
                severity=DetectionSeverity.CRITICAL,
                confidence=min(red_pixels * 10, 0.95),
                timestamp=datetime.utcnow(),
                zone=zone,
                description=f"Fire/smoke indicator detected: {red_pixels:.1%} of frame shows red signature",
                persons_detected=0,
            ))

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        person_count = sum(1 for c in contours if cv2.contourArea(c) > 5000)

        if person_count > 5:
            results.append(DetectionResult(
                detection_id=str(uuid.uuid4()),
                camera_id=camera_id,
                detection_type=DetectionType.CROWD_GATHERING,
                severity=DetectionSeverity.MEDIUM,
                confidence=min(person_count * 0.1, 0.9),
                timestamp=datetime.utcnow(),
                zone=zone,
                description=f"Large group detected: {person_count} persons",
                persons_detected=person_count,
            ))

        return results


class CCTVAgent:
    """CCTV Analytics agent that processes video feeds with computer vision."""

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.detection_engine = CVDetectionEngine(use_mock=use_mock)
        self.cameras: Dict[str, CameraConfig] = {}
        self.alerts: List[CVAlert] = []
        self.detection_history: List[DetectionResult] = []
        self._alert_callbacks: List[Callable] = []
        self._active_captures: Dict[str, Any] = {}

    def register_camera(self, config: CameraConfig):
        self.cameras[config.camera_id] = config

    def register_alert_callback(self, callback: Callable):
        self._alert_callbacks.append(callback)

    def _setup_default_cameras(self):
        for i, (zone, name) in enumerate([
            ("unit_3", "Unit 3 - Distillation Column"),
            ("storage_a", "Storage Tank A - North"),
            ("flare_area", "Flare Area"),
            ("control_room", "Control Room Entry"),
            ("loading_bay", "Loading Bay"),
        ]):
            self.register_camera(CameraConfig(
                camera_id=f"cam_{zone}",
                camera_name=name,
                zone=zone,
                use_webcam=i == 0,
                camera_index=i if i < 2 else i
            ))

    async def start_monitoring(self, use_webcam: bool = False):
        self._setup_default_cameras()
        if use_webcam:
            for cam_id, config in self.cameras.items():
                if config.use_webcam:
                    try:
                        cap = cv2.VideoCapture(config.camera_index)
                        if cap.isOpened():
                            self._active_captures[cam_id] = cap
                    except Exception:
                        pass

    async def process_camera(self, camera_id: str, frame: Optional[np.ndarray] = None) -> List[DetectionResult]:
        if camera_id not in self.cameras:
            return []
        config = self.cameras[camera_id]
        results = await self.detection_engine.process_frame(camera_id, config.zone, frame)
        self.detection_history.extend(results)
        for result in results:
            alert = self._create_alert(result)
            self.alerts.append(alert)
            for cb in self._alert_callbacks:
                try:
                    await cb(alert)
                except Exception:
                    pass
        return results

    async def process_all_cameras(self) -> Dict[str, List[DetectionResult]]:
        frame = None
        for cam_id in self._active_captures:
            try:
                cap = self._active_captures[cam_id]
                if cap and cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        continue
            except Exception:
                pass
            break

        results = {}
        for cam_id in self.cameras:
            results[cam_id] = await self.process_camera(cam_id, frame)
        return results

    def _create_alert(self, detection: DetectionResult) -> CVAlert:
        escalated = detection.severity in (DetectionSeverity.CRITICAL, DetectionSeverity.HIGH)
        return CVAlert(
            alert_id=str(uuid.uuid4()),
            detection_id=detection.detection_id,
            alert_type=detection.detection_type,
            severity=detection.severity,
            camera_id=detection.camera_id,
            zone=detection.zone,
            message=detection.description,
            timestamp=detection.timestamp,
            escalated_to_emergency=escalated,
        )

    def get_summary(self) -> CVSummary:
        cameras_status = []
        for cam_id, config in self.cameras.items():
            recent = [d for d in self.detection_history[-200:]
                      if d.camera_id == cam_id]
            cameras_status.append(CameraStatus(
                camera_id=cam_id,
                camera_name=config.camera_name,
                online=cam_id in self._active_captures or self.use_mock,
                fps_current=15.0,
                detections_last_hour=len(recent),
                alerts_generated=len([a for a in self.alerts if a.camera_id == cam_id]),
            ))

        active = [a for a in self.alerts[-100:] if not a.acknowledged]
        ppe_today = len([d for d in self.detection_history[-500:]
                        if d.detection_type == DetectionType.PPE_VIOLATION])
        critical_today = len([d for d in self.detection_history[-500:]
                             if d.severity in (DetectionSeverity.CRITICAL, DetectionSeverity.HIGH)])

        violation_types = defaultdict(int)
        for d in self.detection_history[-500:]:
            violation_types[d.detection_type.value] += 1
        most_common = max(violation_types, key=violation_types.get) if violation_types else None

        return CVSummary(
            total_cameras=len(self.cameras),
            online_cameras=len(cameras_status),
            active_alerts=len(active),
            detections_last_hour=len(self.detection_history[-200:]),
            ppe_violations_today=ppe_today,
            critical_events_today=critical_today,
            most_common_violation=most_common,
            cameras=cameras_status,
        )

    def get_active_alerts(self, severity: Optional[DetectionSeverity] = None) -> List[CVAlert]:
        alerts = [a for a in self.alerts if not a.acknowledged]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts[-50:]

    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = user
                return True
        return False

    def get_heatmap_data(self) -> Dict[str, float]:
        zone_scores = defaultdict(float)
        for alert in self.alerts[-200:]:
            sev_weight = {"low": 1, "medium": 2, "high": 4, "critical": 8}
            zone_scores[alert.zone] += sev_weight.get(alert.severity.value, 1)
        max_score = max(zone_scores.values()) if zone_scores else 1
        return {z: round(s / max_score, 2) for z, s in zone_scores.items()}

    def stop(self):
        for cap in self._active_captures.values():
            try:
                cap.release()
            except Exception:
                pass
        self._active_captures.clear()
