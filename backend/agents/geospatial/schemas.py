from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from enum import Enum


class GeoType(str, Enum):
    POINT = "Point"
    POLYGON = "Polygon"
    MULTI_POLYGON = "MultiPolygon"
    LINE_STRING = "LineString"


class ZoneType(str, Enum):
    PROCESS_UNIT = "process_unit"
    STORAGE_TANK = "storage_tank"
    CONTROL_ROOM = "control_room"
    MUSTER_POINT = "muster_point"
    FIRE_HYDRANT = "fire_hydrant"
    PARKING = "parking"
    RESIDENTIAL = "residential"
    GREEN_BELT = "green_belt"
    HAZARDOUS = "hazardous"
    GENERAL = "general"


class RiskLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GeoPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float] = Field(description="[longitude, latitude]")


class GeoPolygon(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[List[float]]]


class GeoFeature(BaseModel):
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]


class GeoFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoFeature]


class HeatmapCell(BaseModel):
    lat: float
    lng: float
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    contributing_sensors: List[str] = []
    contributing_factors: List[str] = []


class HeatmapGrid(BaseModel):
    bounds: Dict[str, float]  # {north, south, east, west}
    resolution: int = Field(description="Grid size (e.g. 20 = 20x20)")
    cells: List[HeatmapCell]
    timestamp: str


class AssetLocation(BaseModel):
    asset_id: UUID
    tag: str
    lat: float
    lng: float
    heading: Optional[float] = None
    speed: Optional[float] = None
    zone_id: Optional[UUID] = None
    zone_name: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.SAFE
    last_update: str


class PersonnelLocation(BaseModel):
    personnel_id: str
    name: str
    lat: float
    lng: float
    zone_id: Optional[UUID] = None
    zone_name: Optional[str] = None
    status: str = "active"  # active, emergency, evacuated
    last_update: str


class ZoneRisk(BaseModel):
    zone_id: UUID
    zone_name: str
    zone_type: ZoneType
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    active_sensors: int = 0
    active_permits: int = 0
    active_incidents: int = 0
    bounds: Optional[GeoPolygon] = None


class HeatmapHistoryPoint(BaseModel):
    timestamp: str
    avg_risk: float
    max_risk: float
    critical_zones: int
    high_risk_zones: int
