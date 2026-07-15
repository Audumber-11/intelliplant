from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class ProtocolType(str, Enum):
    MQTT = "mqtt"
    OPC_UA = "opc_ua"
    MODBUS = "modbus"
    HART = "hart"
    WIRELESS_HART = "wireless_hart"
    AMQP = "amqp"
    KAFKA = "kafka"


class DeviceType(str, Enum):
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    PLC = "plc"
    RTU = "rtu"
    GATEWAY = "gateway"
    CONTROLLER = "controller"


class TelemetryMessage(BaseModel):
    device_id: str
    device_type: DeviceType
    protocol: ProtocolType
    sensor_type: Optional[str] = None
    value: float
    unit: str
    timestamp: datetime
    quality: float = Field(ge=0.0, le=1.0, default=1.0)
    metadata: Dict[str, Any] = {}


class DeviceConfig(BaseModel):
    device_id: str
    device_name: str
    device_type: DeviceType
    protocol: ProtocolType
    endpoint: Optional[str] = None
    topic: Optional[str] = None
    interval_seconds: int = 10
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class MQTTConnectionConfig(BaseModel):
    broker: str = "localhost"
    port: int = 1883
    client_id: str = "intelliplant_gateway"
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = False
    topics: List[str] = ["sensors/#", "actuators/#", "alerts/#"]


class OPCUAConfig(BaseModel):
    endpoint: str = "opc.tcp://localhost:4840"
    application_name: str = "IntelliPlant"
    security_mode: str = "None"
    root_node: str = "Objects"


class GatewayStatus(BaseModel):
    protocol: ProtocolType
    connected: bool
    messages_per_second: float = 0.0
    messages_total: int = 0
    last_message_at: Optional[datetime] = None
    error_count: int = 0
    devices_registered: int = 0


class IoTMetrics(BaseModel):
    total_devices: int = 0
    active_devices: int = 0
    protocols: List[GatewayStatus] = []
    throughput_per_second: float = 0.0
    messages_last_hour: int = 0
    error_rate: float = 0.0
    avg_latency_ms: float = 0.0
