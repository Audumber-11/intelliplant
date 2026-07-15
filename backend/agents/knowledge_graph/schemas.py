from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class NodeType(str, Enum):
    EQUIPMENT = "equipment"
    PERMIT = "permit"
    INCIDENT = "incident"
    SENSOR = "sensor"
    PERSONNEL = "personnel"
    ZONE = "zone"
    DOCUMENT = "document"
    REGULATION = "regulation"
    HAZARD = "hazard"
    ACTION = "action"


class EdgeType(str, Enum):
    LOCATED_IN = "located_in"
    HAS_PERMIT = "has_permit"
    CAUSED_INCIDENT = "caused_incident"
    MONITORED_BY = "monitored_by"
    ASSIGNED_TO = "assigned_to"
    REQUIRES = "requires"
    TRIGGERED = "triggered"
    MITIGATED = "mitigated"
    RELATED_TO = "related_to"
    CONTAINS = "contains"
    REFERENCES = "references"
    CONNECTED_TO = "connected_to"
    PRECEDES = "precedes"
    DEPENDS_ON = "depends_on"


class GraphNode(BaseModel):
    id: str
    type: NodeType
    label: str
    properties: Dict[str, Any] = {}
    risk_score: Optional[float] = None
    zone: Optional[str] = None


class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    type: EdgeType
    weight: float = 1.0
    properties: Dict[str, Any] = {}


class KnowledgeGraph(BaseModel):
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []
    metadata: Dict[str, Any] = {}


class PathResult(BaseModel):
    path: List[GraphNode]
    edges: List[GraphEdge]
    total_risk: float = 0.0


class GraphStats(BaseModel):
    total_nodes: int = 0
    total_edges: int = 0
    node_types: Dict[str, int] = {}
    edge_types: Dict[str, int] = {}
    density: float = 0.0
    high_risk_nodes: int = 0
    zones_covered: List[str] = []


class GraphQuery(BaseModel):
    source_type: Optional[NodeType] = None
    target_type: Optional[NodeType] = None
    edge_type: Optional[EdgeType] = None
    max_depth: int = 3
    zone: Optional[str] = None
    min_risk: Optional[float] = None


class RiskPropagationResult(BaseModel):
    source_node: GraphNode
    affected_nodes: List[Dict[str, Any]]
    propagation_paths: List[PathResult]
    overall_risk_impact: float = 0.0
