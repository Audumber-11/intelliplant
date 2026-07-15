from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, ForeignKey,
    Enum as SQLEnum, Text, JSON, Index, UniqueConstraint, TypeDecorator
)
from sqlalchemy.orm import relationship, declarative_base
import uuid

Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID/UUID type. Uses String(36) for SQLite, native UUID for PostgreSQL."""
    impl = String
    cache_ok = True

    def __init__(self):
        super().__init__(length=36)

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value) if not isinstance(value, str) else value
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value) if not isinstance(value, uuid.UUID) else value
        return value

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_GUID())
        return dialect.type_descriptor(String(36))


class PermitType(str, PyEnum):
    HOT_WORK = "hot_work"
    CONFINED_SPACE = "confined_space"
    WORKING_AT_HEIGHT = "working_at_height"
    EXCAVATION = "excavation"
    ELECTRICAL = "electrical"
    LINE_BREAK = "line_break"
    RADIATION = "radiation"
    CHEMICAL = "chemical"
    GENERAL = "general"


class PermitStatus(str, PyEnum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class IncidentSeverity(str, PyEnum):
    NEAR_MISS = "near_miss"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"
    FATALITY = "fatality"


class IncidentStatus(str, PyEnum):
    REPORTED = "reported"
    UNDER_INVESTIGATION = "under_investigation"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"
    CORRECTIVE_ACTIONS = "corrective_actions"
    CLOSED = "closed"


class RiskLevel(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssetType(str, PyEnum):
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


class SensorType(str, PyEnum):
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


class AuditStandard(str, PyEnum):
    ISO_45001 = "iso_45001"
    OSHA_PSM = "osha_psm"
    API_580 = "api_580"
    API_581 = "api_581"
    SEVESO = "seveso"
    OISD_116 = "oisd_116"
    OISD_117 = "oisd_117"
    FACTORY_ACT = "factory_act"
    DGMS = "dgms"


class FindingSeverity(str, PyEnum):
    MAJOR = "major"
    MINOR = "minor"
    OBSERVATION = "observation"
    GOOD_PRACTICE = "good_practice"


class UserRole(str, PyEnum):
    OPERATOR = "operator"
    SUPERVISOR = "supervisor"
    SAFETY_OFFICER = "safety_officer"
    PLANT_MANAGER = "plant_manager"
    EMERGENCY_COORDINATOR = "emergency_coordinator"
    AUDITOR = "auditor"
    ADMIN = "admin"


class PlantAsset(Base):
    __tablename__ = "plant_assets"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tag = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    asset_type = Column(SQLEnum(AssetType), nullable=False, index=True)
    description = Column(Text)
    
    # Location
    unit_area = Column(String(100), index=True)
    elevation = Column(String(50))
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Physical properties
    design_pressure = Column(Float)
    design_temperature = Column(Float)
    material = Column(String(100))
    volume = Column(Float)
    
    # Safety
    hazardous_material = Column(Boolean, default=False)
    hazard_class = Column(String(50))
    mawp = Column(Float)  # Max Allowable Working Pressure
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_critical = Column(Boolean, default=False)
    last_inspection = Column(DateTime)
    next_inspection_due = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(GUID(), ForeignKey("users.id"))
    
    # Relationships
    sensors = relationship("Sensor", back_populates="asset", cascade="all, delete-orphan")
    permits = relationship("Permit", back_populates="asset")
    incidents = relationship("Incident", back_populates="asset")
    maintenance_records = relationship("MaintenanceRecord", back_populates="asset")
    
    __table_args__ = (
        Index('ix_plant_assets_unit_type', 'unit_area', 'asset_type'),
        Index('ix_plant_assets_critical_active', 'is_critical', 'is_active'),
    )


class Sensor(Base):
    __tablename__ = "sensors"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tag = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    sensor_type = Column(SQLEnum(SensorType), nullable=False, index=True)
    
    asset_id = Column(GUID(), ForeignKey("plant_assets.id"), nullable=False, index=True)
    
    # Location on asset
    location_description = Column(String(200))
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Calibration
    range_min = Column(Float)
    range_max = Column(Float)
    units = Column(String(20))
    alarm_low = Column(Float)
    alarm_high = Column(Float)
    alarm_critical_low = Column(Float)
    alarm_critical_high = Column(Float)
    last_calibration = Column(DateTime)
    next_calibration_due = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_safety_critical = Column(Boolean, default=False)
    communication_protocol = Column(String(50))  # Modbus, HART, WirelessHART, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    asset = relationship("PlantAsset", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_sensors_asset_type', 'asset_id', 'sensor_type'),
        Index('ix_sensors_critical_active', 'is_safety_critical', 'is_active'),
    )


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    sensor_id = Column(GUID(), ForeignKey("sensors.id"), nullable=False, index=True)
    value = Column(Float, nullable=False)
    quality = Column(String(20))  # GOOD, BAD, UNCERTAIN
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Computed
    is_alarm = Column(Boolean, default=False)
    is_critical = Column(Boolean, default=False)
    
    sensor = relationship("Sensor", back_populates="readings")
    
    __table_args__ = (
        Index('ix_sensor_readings_sensor_time', 'sensor_id', 'timestamp'),
        Index('ix_sensor_readings_time_alarm', 'timestamp', 'is_alarm'),
    )


class User(Base):
    __tablename__ = "users"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.OPERATOR, index=True)
    
    # Profile
    employee_id = Column(String(50), unique=True)
    department = Column(String(100))
    phone = Column(String(20))
    badge_id = Column(String(50), unique=True)  # For muster tracking
    
    # Permissions
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    approved_permit_types = Column(JSON, default=[])
    
    # MFA
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    created_permits = relationship("Permit", foreign_keys="Permit.created_by_id", back_populates="creator")
    approved_permits = relationship("Permit", foreign_keys="Permit.approved_by_id", back_populates="approver")
    assigned_incidents = relationship("Incident", foreign_keys="[Incident.assignee_id]", back_populates="assignee")
    audit_assignments = relationship("Audit", foreign_keys="[Audit.auditor_id]", back_populates="auditor")


class Permit(Base):
    __tablename__ = "permits"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    permit_number = Column(String(50), unique=True, nullable=False, index=True)
    permit_type = Column(SQLEnum(PermitType), nullable=False, index=True)
    
    # Description
    title = Column(String(300), nullable=False)
    description = Column(Text)
    work_scope = Column(Text)
    
    # Location
    asset_id = Column(GUID(), ForeignKey("plant_assets.id"), index=True)
    location_description = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)
    zone_classification = Column(String(50))  # Zone 0, 1, 2, Safe
    
    # Time
    requested_start = Column(DateTime, nullable=False)
    requested_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    
    # Status
    status = Column(SQLEnum(PermitStatus), default=PermitStatus.DRAFT, nullable=False, index=True)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)
    
    # People
    created_by_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    approved_by_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    supervisor_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    standby_personnel = Column(JSON, default=[])
    
    # Safety requirements
    gas_test_required = Column(Boolean, default=False)
    gas_test_valid_until = Column(DateTime)
    loto_required = Column(Boolean, default=False)
    loto_references = Column(JSON, default=[])
    ppe_requirements = Column(JSON, default=[])
    special_conditions = Column(Text)
    
    # Linked documents
    risk_assessment_id = Column(GUID(), ForeignKey("documents.id"), nullable=True)
    method_statement_id = Column(GUID(), ForeignKey("documents.id"), nullable=True)
    
    # Conflict tracking
    conflicting_permit_ids = Column(JSON, default=[])
    is_suspended = Column(Boolean, default=False)
    suspension_reason = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime)
    
    # Relationships
    asset = relationship("PlantAsset", back_populates="permits")
    creator = relationship("User", foreign_keys=[created_by_id], back_populates="created_permits")
    approver = relationship("User", foreign_keys=[approved_by_id], back_populates="approved_permits")
    gas_tests = relationship("GasTest", back_populates="permit")
    inspections = relationship("PermitInspection", back_populates="permit")
    
    __table_args__ = (
        Index('ix_permits_status_time', 'status', 'requested_start'),
        Index('ix_permits_asset_status', 'asset_id', 'status'),
        Index('ix_permits_active_time', 'actual_start', 'actual_end'),
    )


class GasTest(Base):
    __tablename__ = "gas_tests"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    permit_id = Column(GUID(), ForeignKey("permits.id"), nullable=False, index=True)
    
    # Test details
    tested_by_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    tested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    
    # Results
    h2s_ppm = Column(Float)
    ch4_percent_lel = Column(Float)
    co_ppm = Column(Float)
    o2_percent = Column(Float)
    other_gases = Column(JSON, default={})
    
    # Status
    is_pass = Column(Boolean, nullable=False)
    notes = Column(Text)
    
    permit = relationship("Permit", back_populates="gas_tests")
    tester = relationship("User")


class PermitInspection(Base):
    __tablename__ = "permit_inspections"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    permit_id = Column(GUID(), ForeignKey("permits.id"), nullable=False, index=True)
    inspected_by_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    inspected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Checklist results
    checklist_items = Column(JSON, default={})  # {item_id: {passed: bool, notes: str}}
    overall_pass = Column(Boolean, nullable=False)
    findings = Column(Text)
    corrective_actions = Column(Text)
    
    permit = relationship("Permit", back_populates="inspections")
    inspector = relationship("User")


class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    incident_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Classification
    severity = Column(SQLEnum(IncidentSeverity), nullable=False, index=True)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.REPORTED, index=True)
    category = Column(String(100))  # Fire, Explosion, Toxic Release, Fall, etc.
    subcategory = Column(String(100))
    
    # Description
    title = Column(String(300), nullable=False)
    description = Column(Text)
    immediate_causes = Column(Text)
    root_causes = Column(Text)
    contributing_factors = Column(Text)
    
    # Location & Time
    asset_id = Column(GUID(), ForeignKey("plant_assets.id"), index=True)
    location_description = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)
    occurred_at = Column(DateTime, nullable=False, index=True)
    reported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Impact
    injuries = Column(Integer, default=0)
    fatalities = Column(Integer, default=0)
    environmental_impact = Column(Boolean, default=False)
    production_loss_hours = Column(Float, default=0)
    estimated_cost = Column(Float)
    
    # Response
    emergency_declared = Column(Boolean, default=False)
    emergency_level = Column(String(50))  # Level 1, 2, 3
    response_actions = Column(Text)
    
    # Investigation
    assignee_id = Column(GUID(), ForeignKey("users.id"), index=True)
    investigator_id = Column(GUID(), ForeignKey("users.id"))
    investigation_deadline = Column(DateTime)
    rca_completed_at = Column(DateTime)
    
    # Corrective actions
    corrective_actions = Column(JSON, default=[])  # [{action, owner, due_date, status, verified}]
    
    # Regulatory
    is_reportable = Column(Boolean, default=False)
    regulatory_report_ref = Column(String(100))
    regulatory_reported_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime)
    
    # Relationships
    asset = relationship("PlantAsset", back_populates="incidents")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_incidents")
    investigator = relationship("User", foreign_keys=[investigator_id])
    attachments = relationship("IncidentAttachment", back_populates="incident", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_incidents_severity_status', 'severity', 'status'),
        Index('ix_incidents_asset_time', 'asset_id', 'occurred_at'),
    )


class IncidentAttachment(Base):
    __tablename__ = "incident_attachments"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    incident_id = Column(GUID(), ForeignKey("incidents.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    description = Column(Text)
    uploaded_by_id = Column(GUID(), ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    incident = relationship("Incident", back_populates="attachments")
    uploader = relationship("User")


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    work_order_number = Column(String(50), unique=True, nullable=False, index=True)
    
    asset_id = Column(GUID(), ForeignKey("plant_assets.id"), nullable=False, index=True)
    
    # Type
    maintenance_type = Column(String(50))  # Preventive, Corrective, Predictive, Breakdown
    priority = Column(String(20))  # Low, Medium, High, Critical
    
    # Description
    description = Column(Text)
    work_performed = Column(Text)
    parts_replaced = Column(JSON, default=[])
    
    # Schedule
    planned_start = Column(DateTime)
    planned_end = Column(DateTime)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    
    # Personnel
    assigned_to_id = Column(GUID(), ForeignKey("users.id"))
    performed_by = Column(JSON, default=[])
    
    # Safety
    permit_required = Column(Boolean, default=False)
    permit_id = Column(GUID(), ForeignKey("permits.id"))
    loto_applied = Column(Boolean, default=False)
    
    # Outcome
    status = Column(String(50))  # Planned, In Progress, Completed, Cancelled
    findings = Column(Text)
    recommendations = Column(Text)
    next_maintenance_due = Column(DateTime)
    
    # Cost
    labor_hours = Column(Float)
    material_cost = Column(Float)
    total_cost = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    asset = relationship("PlantAsset", back_populates="maintenance_records")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(300), nullable=False)
    document_type = Column(String(50))  # risk_assessment, method_statement, procedure, standard, regulation
    category = Column(String(100))
    
    # Content
    file_path = Column(String(500))
    content_hash = Column(String(64))  # SHA-256 for deduplication
    extracted_text = Column(Text)
    
    # Metadata
    version = Column(String(20), default="1.0")
    effective_date = Column(DateTime)
    expiry_date = Column(DateTime)
    review_frequency_days = Column(Integer)
    last_reviewed = Column(DateTime)
    reviewed_by_id = Column(GUID(), ForeignKey("users.id"))
    
    # Classification
    confidentiality = Column(String(20), default="internal")
    tags = Column(JSON, default=[])
    applicable_standards = Column(JSON, default=[])
    applicable_assets = Column(JSON, default=[])
    applicable_permit_types = Column(JSON, default=[])
    
    # Status
    status = Column(String(20), default="active")  # active, archived, superseded
    superseded_by_id = Column(GUID(), ForeignKey("documents.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(GUID(), ForeignKey("users.id"))
    
    reviewer = relationship("User", foreign_keys=[reviewed_by_id])
    creator = relationship("User", foreign_keys=[created_by_id])


class Audit(Base):
    __tablename__ = "audits"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    audit_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(300), nullable=False)
    standard = Column(SQLEnum(AuditStandard), nullable=False, index=True)
    
    # Scope
    scope = Column(Text)
    assets_in_scope = Column(JSON, default=[])
    areas_in_scope = Column(JSON, default=[])
    
    # Schedule
    planned_start = Column(DateTime)
    planned_end = Column(DateTime)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    
    # Team
    auditor_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    auditee_ids = Column(JSON, default=[])
    lead_auditor_id = Column(GUID(), ForeignKey("users.id"))
    
    # Status
    status = Column(String(50), default="planned")  # planned, in_progress, completed, cancelled
    overall_result = Column(String(50))  # conformance, minor_nc, major_nc
    
    # Findings summary
    major_findings = Column(Integer, default=0)
    minor_findings = Column(Integer, default=0)
    observations = Column(Integer, default=0)
    good_practices = Column(Integer, default=0)
    
    # Report
    report_path = Column(String(500))
    report_generated_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(GUID(), ForeignKey("users.id"))
    
    auditor = relationship("User", foreign_keys=[auditor_id], back_populates="audit_assignments")
    lead_auditor = relationship("User", foreign_keys=[lead_auditor_id])
    findings = relationship("AuditFinding", back_populates="audit", cascade="all, delete-orphan")
    checklist_items = relationship("AuditChecklistItem", back_populates="audit", cascade="all, delete-orphan")


class AuditFinding(Base):
    __tablename__ = "audit_findings"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    audit_id = Column(GUID(), ForeignKey("audits.id"), nullable=False, index=True)
    
    # Classification
    finding_number = Column(String(50))
    severity = Column(SQLEnum(FindingSeverity), nullable=False, index=True)
    category = Column(String(100))
    clause_reference = Column(String(200))
    
    # Description
    title = Column(String(300), nullable=False)
    description = Column(Text)
    evidence = Column(Text)
    requirement = Column(Text)
    
    # Root cause
    root_cause = Column(Text)
    
    # Corrective action
    corrective_action = Column(Text)
    preventive_action = Column(Text)
    responsible_id = Column(GUID(), ForeignKey("users.id"))
    due_date = Column(DateTime)
    completion_date = Column(DateTime)
    status = Column(String(50), default="open")  # open, in_progress, completed, verified, closed
    verification_notes = Column(Text)
    verified_by_id = Column(GUID(), ForeignKey("users.id"))
    verified_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    audit = relationship("Audit", back_populates="findings")
    responsible = relationship("User", foreign_keys=[responsible_id])
    verifier = relationship("User", foreign_keys=[verified_by_id])


class AuditChecklistItem(Base):
    __tablename__ = "audit_checklist_items"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    audit_id = Column(GUID(), ForeignKey("audits.id"), nullable=False, index=True)
    
    # Reference
    clause = Column(String(200), nullable=False)
    requirement = Column(Text, nullable=False)
    category = Column(String(100))
    
    # Evidence
    evidence_sources = Column(JSON, default=[])  # document_ids, system_reports, interviews
    evidence_collected = Column(Boolean, default=False)
    evidence_notes = Column(Text)
    
    # Assessment
    result = Column(String(20))  # conformance, minor_nc, major_nc, not_applicable, not_verified
    notes = Column(Text)
    assessed_by_id = Column(GUID(), ForeignKey("users.id"))
    assessed_at = Column(DateTime)
    
    # Finding linkage
    finding_id = Column(GUID(), ForeignKey("audit_findings.id"))
    
    audit = relationship("Audit", back_populates="checklist_items")
    assessor = relationship("User")
    finding = relationship("AuditFinding")


class EmergencyIncident(Base):
    __tablename__ = "emergency_incidents"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    incident_number = Column(String(50), unique=True, nullable=False, index=True)
    incident_id = Column(GUID(), ForeignKey("incidents.id"), nullable=True)
    
    # Classification
    emergency_level = Column(String(20), nullable=False)  # Level 1, 2, 3
    emergency_type = Column(String(100))  # Fire, Explosion, Toxic Release, etc.
    
    # ICS Structure
    incident_commander_id = Column(GUID(), ForeignKey("users.id"))
    safety_officer_id = Column(GUID(), ForeignKey("users.id"))
    operations_chief_id = Column(GUID(), ForeignKey("users.id"))
    planning_chief_id = Column(GUID(), ForeignKey("users.id"))
    logistics_chief_id = Column(GUID(), ForeignKey("users.id"))
    liaison_officer_id = Column(GUID(), ForeignKey("users.id"))
    
    # Status
    status = Column(String(20), default="active")  # active, contained, demobilizing, closed
    declared_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    contained_at = Column(DateTime)
    closed_at = Column(DateTime)
    
    # Resources
    resources_deployed = Column(JSON, default=[])
    mutual_aid_activated = Column(Boolean, default=False)
    external_agencies_notified = Column(JSON, default=[])
    
    # Evacuation
    evacuation_zones = Column(JSON, default=[])
    muster_points_activated = Column(JSON, default=[])
    personnel_accounted = Column(Integer, default=0)
    personnel_unaccounted = Column(Integer, default=0)
    
    # Documentation
    ics_201_path = Column(String(500))  # Incident Briefing
    ics_202_path = Column(String(500))  # Incident Objectives
    ics_203_path = Column(String(500))  # Organization Assignment
    ics_204_path = Column(String(500))  # Assignment List
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_emergency_status_time', 'status', 'declared_at'),
    )


class RiskZone(Base):
    __tablename__ = "risk_zones"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    zone_type = Column(String(50))  # high_risk, gas_zone, fire_zone, evacuation_route, muster_point
    
    # Geometry (stored as GeoJSON)
    geometry = Column(JSON, nullable=False)  # GeoJSON Polygon
    center_latitude = Column(Float)
    center_longitude = Column(Float)
    
    # Risk
    base_risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)
    current_risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)
    risk_factors = Column(JSON, default=[])
    
    # Active permits/assets
    active_permit_ids = Column(JSON, default=[])
    asset_ids = Column(JSON, default=[])
    
    # Status
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_risk_zones_type_active', 'zone_type', 'is_active'),
    )


class RiskEvent(Base):
    __tablename__ = "risk_events"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False, index=True)  # correlation, anomaly, threshold, prediction
    risk_level = Column(SQLEnum(RiskLevel), nullable=False, index=True)
    
    # Source
    source = Column(String(100))  # risk_engine, sensor, permit, manual
    source_id = Column(String(100))
    
    # Description
    title = Column(String(300), nullable=False)
    description = Column(Text)
    contributing_factors = Column(JSON, default=[])
    
    # Location
    asset_id = Column(GUID(), ForeignKey("plant_assets.id"), index=True)
    zone_id = Column(GUID(), ForeignKey("risk_zones.id"), index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Time
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    acknowledged_at = Column(DateTime)
    acknowledged_by_id = Column(GUID(), ForeignKey("users.id"))
    resolved_at = Column(DateTime)
    resolved_by_id = Column(GUID(), ForeignKey("users.id"))
    
    # Status
    status = Column(String(20), default="active")  # active, acknowledged, resolved, suppressed
    is_false_positive = Column(Boolean, default=False)
    
    # Actions
    recommended_actions = Column(JSON, default=[])
    taken_actions = Column(JSON, default=[])
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_risk_events_level_time', 'risk_level', 'detected_at'),
        Index('ix_risk_events_asset_time', 'asset_id', 'detected_at'),
    )