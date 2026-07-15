from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime


class DetectionType(str, Enum):
    PPE_VIOLATION = "ppe_violation"
    FLAME_SMOKE = "flame_smoke"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    CROWD_GATHERING = "crowd_gathering"
    UNSAFE_BEHAVIOR = "unsafe_behavior"
    FALL_DETECTION = "fall_detection"
    GAS_LEAK_VISUAL = "gas_leak_visual"


class PPEElement(str, Enum):
    HARD_HAT = "hard_hat"
    SAFETY_VEST = "safety_vest"
    SAFETY_GOGGLES = "safety_goggles"
    EAR_PROTECTION = "ear_protection"
    FACE_SHIELD = "face_shield"
    SAFETY_GLOVES = "safety_gloves"
    SAFETY_BOOTS = "safety_boots"
    HARNESS = "harness"


class DetectionSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CameraConfig(BaseModel):
    camera_id: str
    camera_name: str
    zone: str
    rtsp_url: Optional[str] = None
    use_webcam: bool = False
    camera_index: int = 0
    resolution: str = "640x480"
    fps: int = 15


class DetectionResult(BaseModel):
    detection_id: str
    camera_id: str
    detection_type: DetectionType
    severity: DetectionSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime
    zone: str
    description: str
    persons_detected: int = 0
    ppe_violations: List[str] = []
    bounding_box: Optional[str] = None
    snapshot_path: Optional[str] = None


class CVAlert(BaseModel):
    alert_id: str
    detection_id: str
    alert_type: DetectionType
    severity: DetectionSeverity
    camera_id: str
    zone: str
    message: str
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    escalated_to_emergency: bool = False


class CameraStatus(BaseModel):
    camera_id: str
    camera_name: str
    online: bool
    fps_current: float
    last_frame_at: Optional[datetime] = None
    detections_last_hour: int = 0
    alerts_generated: int = 0


class CVSummary(BaseModel):
    total_cameras: int = 0
    online_cameras: int = 0
    active_alerts: int = 0
    detections_last_hour: int = 0
    ppe_violations_today: int = 0
    critical_events_today: int = 0
    most_common_violation: Optional[str] = None
    cameras: List[CameraStatus] = []


class CCTVFeedFrame(BaseModel):
    camera_id: str
    timestamp: datetime
    frame_data: str
    detections: List[DetectionResult] = []
