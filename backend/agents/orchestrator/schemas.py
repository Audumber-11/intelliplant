from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    DEGRADED = "degraded"


class AgentType(str, Enum):
    RISK_ENGINE = "risk_engine"
    GEOSPATIAL = "geospatial"
    INCIDENT_INTEL = "incident_intel"
    PERMIT_INTEL = "permit_intel"
    EMERGENCY = "emergency"
    COMPLIANCE = "compliance"
    CCTV = "cctv"
    IOT_GATEWAY = "iot_gateway"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    ORCHESTRATOR = "orchestrator"


class MessagePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentMessage(BaseModel):
    message_id: str
    source_agent: AgentType
    target_agent: AgentType
    message_type: str
    priority: MessagePriority
    payload: Dict[str, Any] = {}
    timestamp: datetime
    requires_response: bool = False
    response_to: Optional[str] = None


class AgentHealth(BaseModel):
    agent_id: AgentType
    status: AgentStatus
    last_active: datetime
    task_count: int = 0
    error_count: int = 0
    avg_response_time_ms: float = 0.0
    memory_usage_mb: float = 0.0


class OrchestratorDecision(BaseModel):
    decision_id: str
    timestamp: datetime
    trigger: str
    reasoning: str
    actions: List[Dict[str, Any]] = []
    confidence: float = Field(ge=0.0, le=1.0)
    requires_human_approval: bool = False


class MonitoringConfig(BaseModel):
    interval_seconds: int = 30
    enabled_modules: List[str] = ["all"]
    alert_threshold_risk: float = 0.7
    auto_escalate: bool = True
    llm_reasoning: bool = True


class SystemStatus(BaseModel):
    overall_status: str = "healthy"
    agents: List[AgentHealth] = []
    active_decisions: int = 0
    messages_in_queue: int = 0
    uptime_hours: float = 0.0
    last_orchestration: Optional[datetime] = None
    critical_alerts_active: int = 0
    llm_enabled: bool = False
