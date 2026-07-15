"""
Multi-Sensor Correlation Engine — detects compound risk patterns
by correlating readings across multiple sensors on the same asset or zone.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class SensorReading:
    sensor_id: str
    sensor_type: str
    value: float
    timestamp: datetime
    asset_id: str
    alarm_low: Optional[float] = None
    alarm_high: Optional[float] = None
    alarm_critical_low: Optional[float] = None
    alarm_critical_high: Optional[float] = None


@dataclass
class CorrelatedRisk:
    risk_type: str
    severity: str  # low, medium, high, critical
    confidence: float
    contributing_sensors: List[str]
    asset_id: str
    description: str
    recommended_actions: List[str]
    detected_at: datetime = field(default_factory=datetime.utcnow)


class CorrelationEngine:
    """
    Correlates multi-sensor readings to detect compound risks that single-sensor
    analysis would miss. Implements temporal and spatial correlation patterns.
    """

    # Time window for correlation (seconds)
    CORRELATION_WINDOW_SECONDS = 300  # 5 minutes

    # Compound risk patterns
    PATTERNS = {
        "gas_leak_with_ignition_source": {
            "sensors": ["gas_h2s", "gas_ch4", "gas_combustible", "flame", "smoke"],
            "min_active": 2,
            "description": "Potential gas leak with ignition source detected",
            "severity_boost": 2,
            "actions": [
                "Evacuate immediate area",
                "Activate fire suppression",
                "Notify emergency response team",
                "Isolate fuel sources",
            ],
        },
        "pressure_temperature_excursion": {
            "sensors": ["pressure", "temperature"],
            "min_active": 2,
            "description": "Simultaneous pressure and temperature excursion",
            "severity_boost": 1,
            "actions": [
                "Reduce process throughput",
                "Verify relief system status",
                "Notify operations supervisor",
            ],
        },
        "toxic_gas_accumulation": {
            "sensors": ["gas_h2s", "gas_co", "gas_o2"],
            "min_active": 2,
            "description": "Toxic gas accumulation with oxygen displacement",
            "severity_boost": 2,
            "actions": [
                "Activate forced ventilation",
                "Deploy gas monitoring team",
                "Restrict area access",
                "Prepare SCBA team",
            ],
        },
        "equipment_degradation": {
            "sensors": ["vibration", "temperature", "pressure"],
            "min_active": 2,
            "description": "Multiple indicators suggest equipment degradation",
            "severity_boost": 1,
            "actions": [
                "Schedule inspection",
                "Reduce operating parameters",
                "Prepare backup equipment",
            ],
        },
        "fire_explosion_risk": {
            "sensors": [
                "gas_ch4",
                "gas_combustible",
                "flame",
                "smoke",
                "temperature",
            ],
            "min_active": 3,
            "description": "Elevated fire/explosion risk from multiple indicators",
            "severity_boost": 3,
            "actions": [
                "Activate fire watch",
                "Clear hot work permits in zone",
                "Deploy fire brigade standby",
                "Activate emergency shutdown",
            ],
        },
        "weather_compounded_risk": {
            "sensors": [
                "weather_wind",
                "weather_temp",
                "gas_h2s",
                "gas_combustible",
            ],
            "min_active": 2,
            "description": "Weather conditions amplifying process risks",
            "severity_boost": 1,
            "actions": [
                "Adjust ventilation rates",
                "Increase monitoring frequency",
                "Brief field crews on conditions",
            ],
        },
    }

    def __init__(self):
        self.readings_buffer: Dict[str, List[SensorReading]] = {}
        self._window = timedelta(seconds=self.CORRELATION_WINDOW_SECONDS)

    def ingest_reading(self, reading: SensorReading) -> List[CorrelatedRisk]:
        """
        Ingest a new sensor reading and check for compound risk patterns.
        Returns list of detected correlated risks.
        """
        asset_id = reading.asset_id
        if asset_id not in self.readings_buffer:
            self.readings_buffer[asset_id] = []

        self.readings_buffer[asset_id].append(reading)
        self._prune_old_readings(asset_id)

        return self._evaluate_patterns(asset_id)

    def ingest_batch(self, readings: List[SensorReading]) -> List[CorrelatedRisk]:
        """Ingest a batch of readings and return all detected risks."""
        all_risks = []
        for reading in readings:
            risks = self.ingest_reading(reading)
            all_risks.extend(risks)
        return self._deduplicate_risks(all_risks)

    def _prune_old_readings(self, asset_id: str):
        """Remove readings outside the correlation window."""
        now = datetime.utcnow()
        self.readings_buffer[asset_id] = [
            r
            for r in self.readings_buffer[asset_id]
            if (now - r.timestamp) <= self._window
        ]

    def _evaluate_patterns(self, asset_id: str) -> List[CorrelatedRisk]:
        """Evaluate all patterns against current readings for an asset."""
        readings = self.readings_buffer.get(asset_id, [])
        if not readings:
            return []

        # Get active sensor types (those in alarm or critical state)
        active_sensors = set()
        sensor_map: Dict[str, SensorReading] = {}
        for r in readings:
            sensor_map[r.sensor_type] = r
            if self._is_in_alarm(r):
                active_sensors.add(r.sensor_type)

        detected_risks = []
        for pattern_name, pattern in self.PATTERNS.items():
            pattern_sensors = set(pattern["sensors"])
            matching_active = active_sensors & pattern_sensors

            if len(matching_active) >= pattern["min_active"]:
                severity = self._calculate_severity(
                    matching_active, sensor_map, pattern
                )
                confidence = min(
                    1.0, len(matching_active) / len(pattern_sensors)
                )

                risk = CorrelatedRisk(
                    risk_type=pattern_name,
                    severity=severity,
                    confidence=confidence,
                    contributing_sensors=list(matching_active),
                    asset_id=asset_id,
                    description=pattern["description"],
                    recommended_actions=pattern["actions"],
                )
                detected_risks.append(risk)

        return detected_risks

    def _is_in_alarm(self, reading: SensorReading) -> bool:
        """Check if a sensor reading is in alarm state."""
        if reading.alarm_critical_high and reading.value >= reading.alarm_critical_high:
            return True
        if reading.alarm_critical_low and reading.value <= reading.alarm_critical_low:
            return True
        if reading.alarm_high and reading.value >= reading.alarm_high:
            return True
        if reading.alarm_low and reading.value <= reading.alarm_low:
            return True
        return False

    def _calculate_severity(
        self,
        active_sensors: set,
        sensor_map: Dict[str, SensorReading],
        pattern: dict,
    ) -> str:
        """Calculate overall severity based on active sensors and pattern config."""
        critical_count = 0
        high_count = 0

        for sensor_type in active_sensors:
            reading = sensor_map.get(sensor_type)
            if not reading:
                continue
            if reading.alarm_critical_high and reading.value >= reading.alarm_critical_high:
                critical_count += 1
            elif reading.alarm_critical_low and reading.value <= reading.alarm_critical_low:
                critical_count += 1
            elif reading.alarm_high and reading.value >= reading.alarm_high:
                high_count += 1
            elif reading.alarm_low and reading.value <= reading.alarm_low:
                high_count += 1

        base_score = critical_count * 4 + high_count * 2
        boosted_score = base_score + pattern.get("severity_boost", 0)

        if boosted_score >= 8:
            return "critical"
        elif boosted_score >= 5:
            return "high"
        elif boosted_score >= 3:
            return "medium"
        return "low"

    def _deduplicate_risks(self, risks: List[CorrelatedRisk]) -> List[CorrelatedRisk]:
        """Remove duplicate risk events (same type + same asset)."""
        seen = set()
        unique = []
        for risk in risks:
            key = (risk.risk_type, risk.asset_id)
            if key not in seen:
                seen.add(key)
                unique.append(risk)
        return unique

    def get_asset_risk_summary(self, asset_id: str) -> Dict:
        """Get current risk summary for an asset."""
        readings = self.readings_buffer.get(asset_id, [])
        now = datetime.utcnow()
        recent = [r for r in readings if (now - r.timestamp) <= self._window]

        alarm_count = sum(1 for r in recent if self._is_in_alarm(r))
        total = len(recent)

        return {
            "asset_id": asset_id,
            "total_readings": total,
            "alarms_active": alarm_count,
            "sensor_types": list(set(r.sensor_type for r in recent)),
            "last_updated": max((r.timestamp for r in recent), default=None),
        }
