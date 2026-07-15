from datetime import datetime
from typing import Optional, List, Dict, Any, Literal, Generic, TypeVar
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from enum import Enum

T = TypeVar('T')


# Enums
class PermitType(str, Enum):
    HOT_WORK = "hot_work"
    CONFINED_SPACE = "confined_space"
    WORKING_AT_HEIGHT = "working_at_height"
    EXCAVATION = "excavation"
    ELECTRICAL = "electrical"
    LINE_BREAK = "line_break"
    RADIATION = "radiation"
    CHEMICAL = "chemical"
    GENERAL = "general"


class PermitStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class IncidentSeverity(str, Enum):
    NEAR_MISS = "near_miss"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"
    FATALITY = "fatality"


class IncidentStatus(str, Enum):
    REPORTED = "reported"
    UNDER_INVESTIGATION = "under_investigation"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"
    CORRECTIVE_ACTIONS = "corrective_actions"
    CLOSED = "closed"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssetType(str, Enum):
    PROCESS_UNIT = "process_unit"
    STORAGE_TANK = "storage_tank"
    PIPELINE = "pipeline"
    VALVE = "valve"
    PUMP = "pump"
    COMPRESSOR = "compressor"
    HEAT_EXCHANGER = "heat_exchanger"
    VESSEL = "vessel"
    CONTROL_ROOM = "control_room"
    MUSTER_POINT = "muster_point"
    FIRE_HYDRANT = "fire_hydrant"
    SAFETY_SHOWER = "safety_shower"
    GAS_DETECTOR = "gas_detector"
    OTHER = "other"


class SensorType(str, Enum):
    GAS_H2S = "gas_h2s"
    GAS_CH4 = "gas_ch4"
    GAS_CO = "gas_co"
    GAS_O2 = "gas_o2"
    GAS_COMBUSTIBLE = "gas_combustible"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    FLOW = "flow"
    LEVEL = "level"
    VIBRATION = "vibration"
    RADIATION = "radiation"
    SMOKE = "smoke"
    FLAME = "flame"
    WEATHER_WIND = "weather_wind"
    WEATHER_TEMP = "weather_temp"
    WEATHER_HUMIDITY = "weather_humidity"


class UserRole(str, Enum):
    OPERATOR = "operator"
    SUPERVISOR = "supervisor"
    SAFETY_OFFICER = "safety_officer"
    PLANT_MANAGER = "plant_manager"
    EMERGENCY_COORDINATOR = "emergency_coordinator"
    AUDITOR = "auditor"
    ADMIN = "admin"


# Base schemas
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# User schemas
class UserBase(BaseSchema):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    full_name: str = Field(min_length=1, max_length=200)
    employee_id: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = UserRole.OPERATOR


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseSchema):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    approved_permit_types: Optional[List[PermitType]] = None


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    is_superuser: bool
    mfa_enabled: bool
    badge_id: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None


class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseSchema):
    username: Optional[str] = None
    user_id: Optional[UUID] = None


# Asset schemas
class AssetBase(BaseSchema):
    tag: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    asset_type: AssetType
    description: Optional[str] = None
    unit_area: Optional[str] = None
    elevation: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    design_pressure: Optional[float] = None
    design_temperature: Optional[float] = None
    material: Optional[str] = None
    volume: Optional[float] = None
    hazardous_material: bool = False
    hazard_class: Optional[str] = None
    mawp: Optional[float] = None
    is_critical: bool = False


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    unit_area: Optional[str] = None
    is_active: Optional[bool] = None
    is_critical: Optional[bool] = None
    last_inspection: Optional[datetime] = None
    next_inspection_due: Optional[datetime] = None


class AssetResponse(AssetBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None


class AssetWithRelations(AssetResponse):
    sensors: List["SensorResponse"] = []
    active_permits: int = 0
    open_incidents: int = 0
    current_risk_level: RiskLevel = RiskLevel.LOW


# Sensor schemas
class SensorBase(BaseSchema):
    tag: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    sensor_type: SensorType
    asset_id: UUID
    location_description: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    units: Optional[str] = None
    alarm_low: Optional[float] = None
    alarm_high: Optional[float] = None
    alarm_critical_low: Optional[float] = None
    alarm_critical_high: Optional[float] = None
    communication_protocol: Optional[str] = None
    is_safety_critical: bool = False


class SensorCreate(SensorBase):
    pass


class SensorUpdate(BaseSchema):
    name: Optional[str] = None
    location_description: Optional[str] = None
    alarm_low: Optional[float] = None
    alarm_high: Optional[float] = None
    alarm_critical_low: Optional[float] = None
    alarm_critical_high: Optional[float] = None
    is_active: Optional[bool] = None
    is_safety_critical: Optional[bool] = None
    last_calibration: Optional[datetime] = None
    next_calibration_due: Optional[datetime] = None


class SensorResponse(SensorBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SensorReadingBase(BaseSchema):
    sensor_id: UUID
    value: float
    quality: str = "GOOD"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SensorReadingCreate(SensorReadingBase):
    pass


class SensorReadingResponse(SensorReadingBase):
    id: UUID
    is_alarm: bool
    is_critical: bool


class SensorReadingBulk(BaseSchema):
    readings: List[SensorReadingCreate]


# Permit schemas
class PermitCondition(BaseSchema):
    id: str
    description: str
    is_met: bool = False
    verified_by: Optional[UUID] = None
    verified_at: Optional[datetime] = None


class PermitBase(BaseSchema):
    permit_type: PermitType
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    work_scope: Optional[str] = None
    asset_id: Optional[UUID] = None
    location_description: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    zone_classification: Optional[str] = None
    requested_start: datetime
    requested_end: datetime
    gas_test_required: bool = False
    loto_required: bool = False
    ppe_requirements: List[str] = []
    special_conditions: Optional[str] = None


class PermitCreate(PermitBase):
    pass


class PermitUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    work_scope: Optional[str] = None
    requested_start: Optional[datetime] = None
    requested_end: Optional[datetime] = None
    status: Optional[PermitStatus] = None


class PermitApproval(BaseSchema):
    approved_by_id: UUID
    approved_at: datetime
    comments: Optional[str] = None
    conditions: Optional[List[PermitCondition]] = None


class PermitResponse(BaseSchema):
    id: UUID
    permit_number: str
    permit_type: PermitType
    title: str
    description: Optional[str] = None
    work_scope: Optional[str] = None
    asset_id: Optional[UUID] = None
    location_description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zone_classification: Optional[str] = None
    requested_start: datetime
    requested_end: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    status: PermitStatus
    risk_level: Optional[RiskLevel] = None
    created_by_id: UUID
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    gas_test_required: bool = False
    loto_required: bool = False
    ppe_requirements: List = []
    special_conditions: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PermitWithDetails(PermitResponse):
    asset: Optional[AssetResponse] = None
    creator: Optional[UserResponse] = None
    approver: Optional[UserResponse] = None
    conflicts: List["PermitConflict"] = []
    risk_assessment: Optional["RiskAssessment"] = None


class PermitConflict(BaseSchema):
    conflict_type: str
    severity: RiskLevel
    description: str
    conflicting_permit_id: UUID
    conflicting_permit_number: str
    recommendation: str


class RiskAssessment(BaseSchema):
    permit_id: UUID
    overall_risk: RiskLevel
    factors: Dict[str, Any]
    mitigation_measures: List[str]
    assessed_by: UUID
    assessed_at: datetime
    valid_until: datetime


# Incident schemas
class IncidentBase(BaseSchema):
    title: str = Field(min_length=1, max_length=300)
    description: str
    severity: IncidentSeverity
    category: Optional[str] = None
    asset_id: Optional[UUID] = None
    location_description: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    occurred_at: datetime
    injuries: int = 0
    fatalities: int = 0
    environmental_impact: bool = False


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    root_cause: Optional[str] = None
    contributing_factors: Optional[List[str]] = None
    corrective_actions: Optional[List[str]] = None


class IncidentResponse(IncidentBase):
    id: UUID
    incident_number: str
    status: IncidentStatus
    assignee_id: Optional[UUID] = None
    root_cause: Optional[str] = None
    contributing_factors: Optional[str] = None
    corrective_actions: List = []
    created_at: datetime
    updated_at: datetime


class IncidentWithDetails(IncidentResponse):
    asset: Optional[AssetResponse] = None
    reporter: Optional[UserResponse] = None
    assignee: Optional[UserResponse] = None
    similar_incidents: List[IncidentResponse] = []


# Risk Event schemas
class RiskEventBase(BaseSchema):
    event_type: str
    risk_level: RiskLevel
    source: str
    source_id: Optional[str] = None
    title: str
    description: str
    contributing_factors: List[str] = []
    asset_id: Optional[UUID] = None
    zone_id: Optional[UUID] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    recommended_actions: List = []


class RiskEventCreate(RiskEventBase):
    pass


class RiskEventResponse(RiskEventBase):
    id: UUID
    detected_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by_id: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[UUID] = None
    status: str
    is_false_positive: bool
    taken_actions: List[str] = []


class RiskEventAcknowledge(BaseSchema):
    acknowledged_by_id: UUID
    comments: Optional[str] = None


class RiskEventResolve(BaseSchema):
    resolved_by_id: UUID
    resolution: str
    actions_taken: List[str]


# Geospatial schemas
class GeoPoint(BaseSchema):
    type: Literal["Point"] = "Point"
    coordinates: List[float]  # [lon, lat]


class GeoPolygon(BaseSchema):
    type: Literal["Polygon"] = "Polygon"
    coordinates: List[List[List[float]]]


class GeoFeature(BaseSchema):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: GeoPoint | GeoPolygon
    properties: Dict[str, Any]


class GeoFeatureCollection(BaseSchema):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[GeoFeature]


class HeatmapPoint(BaseSchema):
    latitude: float
    longitude: float
    intensity: float
    risk_level: RiskLevel
    factors: List[str] = []


class HeatmapGrid(BaseSchema):
    bounds: List[List[float]]  # [[min_lon, min_lat], [max_lon, max_lat]]
    resolution: int  # meters per cell
    cells: List[List[float]]  # 2D array of intensity values
    risk_levels: List[List[str]]  # 2D array of risk level strings


class AssetLocation(BaseSchema):
    asset_id: UUID
    tag: str
    name: str
    asset_type: AssetType
    latitude: float
    longitude: float
    current_risk: RiskLevel
    active_permits: int
    active_alerts: int


# Query/Filter schemas
class PaginationParams(BaseSchema):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseSchema, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class AssetFilter(BaseSchema):
    asset_type: Optional[AssetType] = None
    unit_area: Optional[str] = None
    is_active: Optional[bool] = None
    is_critical: Optional[bool] = None
    search: Optional[str] = None


class PermitFilter(BaseSchema):
    permit_type: Optional[PermitType] = None
    status: Optional[PermitStatus] = None
    asset_id: Optional[UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None


class IncidentFilter(BaseSchema):
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    asset_id: Optional[UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None


class RiskEventFilter(BaseSchema):
    risk_level: Optional[RiskLevel] = None
    event_type: Optional[str] = None
    asset_id: Optional[UUID] = None
    zone_id: Optional[UUID] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# Dashboard schemas
class DashboardKPIs(BaseSchema):
    active_permits: int
    active_risk_events: Dict[str, int]  # by risk level
    open_incidents: int
    overdue_inspections: int
    personnel_on_site: int
    muster_points_ready: int


class RiskTrendPoint(BaseSchema):
    timestamp: datetime
    low: int
    medium: int
    high: int
    critical: int


class PermitTrendPoint(BaseSchema):
    date: str
    created: int
    approved: int
    active: int
    closed: int


# WebSocket schemas
class WSMessage(BaseSchema):
    type: str
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSRiskUpdate(WSMessage):
    type: Literal["risk_update"] = "risk_update"
    payload: RiskEventResponse


class WSPermitUpdate(WSMessage):
    type: Literal["permit_update"] = "permit_update"
    payload: PermitResponse


class WSHeatmapUpdate(WSMessage):
    type: Literal["heatmap_update"] = "heatmap_update"
    payload: HeatmapGrid


class WSAssetUpdate(WSMessage):
    type: Literal["asset_update"] = "asset_update"
    payload: AssetLocation


class WSEmergencyAlert(WSMessage):
    type: Literal["emergency_alert"] = "emergency_alert"
    payload: "EmergencyIncidentResponse"


# Emergency schemas
class EmergencyIncidentBase(BaseSchema):
    title: str
    description: str
    incident_type: str
    severity: IncidentSeverity
    latitude: float
    longitude: float
    reported_by_id: UUID


class EmergencyIncidentCreate(EmergencyIncidentBase):
    pass


class EmergencyIncidentResponse(EmergencyIncidentBase):
    id: UUID
    incident_number: str
    status: str
    ics_roles: Dict[str, UUID] = {}
    muster_status: Dict[str, int] = {}
    created_at: datetime
    updated_at: datetime


# Audit schemas
class AuditStandardType(str, Enum):
    ISO_45001 = "iso_45001"
    OSHA_PSM = "osha_psm"
    API_580 = "api_580"
    API_581 = "api_581"
    SEVESO = "seveso"
    OISD_116 = "oisd_116"
    OISD_117 = "oisd_117"
    FACTORY_ACT = "factory_act"
    DGMS = "dgms"


class FindingSeverity(str, Enum):
    MAJOR = "major"
    MINOR = "minor"
    OBSERVATION = "observation"
    GOOD_PRACTICE = "good_practice"


class AuditChecklistItem(BaseSchema):
    clause: str
    requirement: str
    evidence_required: List[str]
    status: str = "pending"  # pending, compliant, non_compliant, na
    findings: List[str] = []


class AuditBase(BaseSchema):
    title: str
    standard: AuditStandardType
    scope: str
    planned_start: datetime
    planned_end: datetime
    auditor_id: UUID


class AuditCreate(AuditBase):
    pass


class AuditResponse(BaseSchema):
    id: UUID
    audit_number: str
    title: str
    standard: AuditStandardType
    scope: Optional[str] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    auditor_id: UUID
    status: str
    overall_result: Optional[str] = None
    major_findings: int = 0
    minor_findings: int = 0
    observations: int = 0
    good_practices: int = 0
    created_at: datetime


class AuditFindingBase(BaseSchema):
    clause: str
    severity: FindingSeverity
    description: str
    evidence: List[str] = []


class AuditFindingCreate(AuditFindingBase):
    pass


class AuditFindingResponse(AuditFindingBase):
    id: UUID
    audit_id: UUID
    status: str = "open"
    assigned_to: Optional[UUID] = None
    due_date: Optional[datetime] = None
    corrective_action: Optional[str] = None
    verified: bool = False
    created_at: datetime


# Search/Query schemas
class KnowledgeQuery(BaseSchema):
    question: str = Field(min_length=3, max_length=500)
    collection: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeQueryResponse(BaseSchema):
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    query_time_ms: float
    chunks_searched: int


# Health/Status
class HealthResponse(BaseSchema):
    status: str
    version: str
    database: str
    chromadb: str
    redis: str
    timestamp: datetime


# Bulk operations
class BulkDeleteRequest(BaseSchema):
    ids: List[UUID]


class BulkOperationResponse(BaseSchema):
    success_count: int
    failed_count: int
    errors: List[Dict[str, Any]] = []


# File upload
class FileUploadResponse(BaseSchema):
    filename: str
    size: int
    content_type: str
    document_id: Optional[str] = None


# Report generation
class ReportRequest(BaseSchema):
    report_type: str
    filters: Dict[str, Any]
    format: str = "pdf"  # pdf, excel, csv
    include_evidence: bool = True


class ReportResponse(BaseSchema):
    report_id: str
    status: str
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None


# Update forward references
AssetWithRelations.model_rebuild()
PermitWithDetails.model_rebuild()
IncidentWithDetails.model_rebuild()
EmergencyIncidentResponse.model_rebuild()
AuditResponse.model_rebuild()
AuditFindingResponse.model_rebuild()