import asyncio
import uuid
import random
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from collections import defaultdict, deque

from .schemas import (
    TelemetryMessage, DeviceConfig, DeviceType, ProtocolType,
    MQTTConnectionConfig, GatewayStatus, IoTMetrics
)


class SimulatedMQTTClient:
    """Simulates MQTT pub/sub for sensor data."""

    def __init__(self):
        self.connected = False
        self.topics: Dict[str, List[Callable]] = defaultdict(list)
        self.message_count = 0
        self._running = False

    async def connect(self, config: MQTTConnectionConfig):
        await asyncio.sleep(0.1)
        self.connected = True
        return True

    async def publish(self, topic: str, message: str):
        self.message_count += 1
        callbacks = self.topics.get(topic, [])
        for cb in callbacks:
            try:
                await cb(topic, message)
            except Exception:
                pass

    def subscribe(self, topic: str, callback: Callable):
        self.topics[topic].append(callback)

    async def disconnect(self):
        self.connected = False


class SimulatedOPCUAClient:
    """Simulates OPC-UA client for SCADA data."""

    def __init__(self):
        self.connected = False
        self.message_count = 0

    async def connect(self, endpoint: str):
        await asyncio.sleep(0.1)
        self.connected = True
        return True

    async def read_value(self, node_id: str) -> float:
        return round(random.uniform(0, 100), 2)

    async def disconnect(self):
        self.connected = False


class SensorSimulator:
    """Generates realistic simulated sensor data."""

    SENSOR_TYPES = {
        "pressure": {"unit": "bar", "min": 0, "max": 50, "normal": (10, 30)},
        "temperature": {"unit": "celsius", "min": -20, "max": 300, "normal": (25, 85)},
        "flow_rate": {"unit": "m3h", "min": 0, "max": 500, "normal": (50, 200)},
        "gas_h2s": {"unit": "ppm", "min": 0, "max": 100, "normal": (0, 10)},
        "gas_voc": {"unit": "ppm", "min": 0, "max": 500, "normal": (0, 50)},
        "vibration": {"unit": "mm_s", "min": 0, "max": 50, "normal": (0, 10)},
        "level": {"unit": "percent", "min": 0, "max": 100, "normal": (30, 80)},
        "humidity": {"unit": "percent", "min": 0, "max": 100, "normal": (30, 70)},
        "wind_speed": {"unit": "kmh", "min": 0, "max": 100, "normal": (0, 30)},
    }

    def __init__(self):
        self.sensor_values: Dict[str, float] = {}
        self._trends: Dict[str, float] = {}

    def generate_reading(self, device_id: str, sensor_type: str) -> TelemetryMessage:
        spec = self.SENSOR_TYPES.get(sensor_type, {"unit": "raw", "min": 0, "max": 100, "normal": (0, 50)})
        normal_min, normal_max = spec["normal"]

        if device_id not in self._trends:
            self._trends[device_id] = 0.0
        self._trends[device_id] += random.uniform(-0.5, 0.5)
        self._trends[device_id] = max(-5, min(5, self._trends[device_id]))

        drift = self._trends[device_id]
        anomaly = 0.0
        if random.random() < 0.02:
            anomaly = random.choice([-20, 20, 50, 100])

        value = normal_min + (normal_max - normal_min) * random.random()
        value += drift
        value += anomaly
        value = max(spec["min"], min(spec["max"], value))

        quality = 1.0
        if anomaly != 0:
            quality = max(0.3, 1.0 - abs(anomaly) / 100.0)

        self.sensor_values[device_id] = value

        return TelemetryMessage(
            device_id=device_id,
            device_type=DeviceType.SENSOR,
            protocol=ProtocolType.MQTT,
            sensor_type=sensor_type,
            value=round(value, 2),
            unit=spec["unit"],
            timestamp=datetime.utcnow(),
            quality=round(quality, 2),
            metadata={"anomaly": anomaly != 0, "trend": round(drift, 2)},
        )


class IoTGateway:
    """IoT/SCADA Integration Gateway with multi-protocol support."""

    def __init__(self):
        self.mqtt = SimulatedMQTTClient()
        self.opcua = SimulatedOPCUAClient()
        self.simulator = SensorSimulator()
        self.devices: Dict[str, DeviceConfig] = {}
        self.message_buffer: deque = deque(maxlen=10000)
        self.message_callbacks: List[Callable] = []
        self._running = False
        self._metrics = {
            "mqtt_messages": 0,
            "opcua_messages": 0,
            "errors": 0,
            "start_time": datetime.utcnow(),
        }
        self._last_minute_counts: deque = deque(maxlen=60)

    def register_device(self, config: DeviceConfig):
        self.devices[config.device_id] = config

    def register_callback(self, callback: Callable):
        self.message_callbacks.append(callback)

    def _setup_default_devices(self):
        devices = [
            ("P-001", "Reactor Pressure", DeviceType.SENSOR, ProtocolType.MQTT, "sensors/pressure", "pressure"),
            ("T-101", "Distillation Temp", DeviceType.SENSOR, ProtocolType.WIRELESS_HART, "sensors/temperature", "temperature"),
            ("F-201", "Feed Flow Rate", DeviceType.SENSOR, ProtocolType.MODBUS, "sensors/flow", "flow_rate"),
            ("G-H2S-01", "H2S Detector A", DeviceType.SENSOR, ProtocolType.HART, "sensors/h2s", "gas_h2s"),
            ("G-VOC-01", "VOC Detector A", DeviceType.SENSOR, ProtocolType.HART, "sensors/voc", "gas_voc"),
            ("V-301", "Pump Vibration", DeviceType.SENSOR, ProtocolType.OPC_UA, None, "vibration"),
            ("L-401", "Tank Level", DeviceType.SENSOR, ProtocolType.MODBUS, "sensors/level", "level"),
            ("H-501", "Ambient Humidity", DeviceType.SENSOR, ProtocolType.MQTT, "sensors/humidity", "humidity"),
            ("W-601", "Wind Speed", DeviceType.SENSOR, ProtocolType.AMQP, "sensors/wind", "wind_speed"),
            ("PLC-01", "Unit 3 PLC", DeviceType.PLC, ProtocolType.OPC_UA, None, None),
        ]
        for dev_id, name, dtype, proto, topic, stype in devices:
            self.register_device(DeviceConfig(
                device_id=dev_id,
                device_name=name,
                device_type=dtype,
                protocol=proto,
                topic=topic,
                interval_seconds=random.choice([2, 5, 10]),
            ))

    async def start(self):
        self._setup_default_devices()
        await self.mqtt.connect(MQTTConnectionConfig())
        await self.opcua.connect("opc.tcp://localhost:4840")
        self._running = True
        return True

    async def stream_sensor_data(self) -> TelemetryMessage:
        sensor_devices = [(did, dc) for did, dc in self.devices.items()
                         if dc.device_type == DeviceType.SENSOR]
        if not sensor_devices:
            return None

        dev_id, config = random.choice(sensor_devices)
        sensor_type = None
        if config.topic:
            sensor_type = config.topic.split("/")[-1]

        reading = self.simulator.generate_reading(dev_id, sensor_type)

        if config.protocol == ProtocolType.MQTT and config.topic:
            await self.mqtt.publish(config.topic, reading.model_dump_json())
            self._metrics["mqtt_messages"] += 1
        elif config.protocol == ProtocolType.OPC_UA:
            self._metrics["opcua_messages"] += 1

        reading.metadata["device_name"] = config.device_name
        reading.metadata["protocol"] = config.protocol.value
        reading.metadata["topic"] = config.topic

        self.message_buffer.append(reading)
        self._last_minute_counts.append(1)

        for cb in self.message_callbacks:
            try:
                await cb(reading)
            except Exception:
                self._metrics["errors"] += 1

        return reading

    async def ingest_batch(self, count: int = 10) -> List[TelemetryMessage]:
        messages = []
        for _ in range(count):
            msg = await self.stream_sensor_data()
            if msg:
                messages.append(msg)
        return messages

    def get_metrics(self) -> IoTMetrics:
        protocols = defaultdict(lambda: {"connected": False, "messages": 0})
        for dev in self.devices.values():
            p = dev.protocol.value
            if p not in protocols:
                protocols[p] = {"connected": True, "messages": 0}

        return IoTMetrics(
            total_devices=len(self.devices),
            active_devices=len([d for d in self.devices.values() if d.device_type == DeviceType.SENSOR]),
            protocols=[
                GatewayStatus(
                    protocol=ProtocolType(proto),
                    connected=info["connected"],
                    messages_per_second=len(self._last_minute_counts) / max(60, 1),
                    messages_total=self._metrics["mqtt_messages"] + self._metrics["opcua_messages"],
                    devices_registered=len([d for d in self.devices.values() if d.protocol.value == proto]),
                )
                for proto, info in protocols.items()
            ],
            messages_last_hour=len(self.message_buffer),
            error_rate=self._metrics["errors"] / max(1, len(self.message_buffer)),
            avg_latency_ms=random.uniform(5, 50),
        )

    def get_recent_messages(self, n: int = 50) -> List[TelemetryMessage]:
        return list(self.message_buffer)[-n:]

    async def stop(self):
        self._running = False
        await self.mqtt.disconnect()
        await self.opcua.disconnect()
