"""
Data Fusion Engine — combines sensor data, permit status, weather,
maintenance records, and historical incidents into a unified risk context.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class RiskContext:
    """Unified risk context combining all data sources."""
    asset_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Sensor data
    sensor_readings: Dict[str, float] = field(default_factory=dict)
    sensor_alarms: List[str] = field(default_factory=list)
    sensor_critical: List[str] = field(default_factory=list)

    # Permit data
    active_permits: List[Dict] = field(default_factory=list)
    permit_conflicts: List[Dict] = field(default_factory=list)
    expired_permits: List[Dict] = field(default_factory=list)

    # Weather
    wind_speed: Optional[float] = None
    wind_direction: Optional[str] = None
    temperature_ambient: Optional[float] = None
    humidity: Optional[float] = None
    rainfall: Optional[float] = None

    # Maintenance
    overdue_inspections: bool = False
    overdue_calibrations: bool = False
    pending_maintenance: List[Dict] = field(default_factory=list)

    # Historical
    recent_incidents: List[Dict] = field(default_factory=list)
    near_miss_count_30d: int = 0
    incident_count_90d: int = 0

    # Zone data
    zone_risk_level: str = "low"
    zone_permit_count: int = 0
    zone_personnel_count: int = 0

    # Computed risk
    overall_risk_score: float = 0.0
    risk_factors: List[str] = field(default_factory=list)
    compound_risks: List[Dict] = field(default_factory=list)


class DataFusionEngine:
    """
    Fuses data from multiple sources into a unified RiskContext for each asset.
    Handles data quality, staleness, and missing data gracefully.
    """

    # Data freshness thresholds
    STALE_READING_SECONDS = 600  # 10 minutes
    STALE_WEATHER_SECONDS = 1800  # 30 minutes

    # Risk weights for scoring
    WEIGHTS = {
        "sensor_alarms": 0.30,
        "sensor_critical": 0.25,
        "permit_risk": 0.15,
        "weather_risk": 0.10,
        "maintenance_risk": 0.10,
        "historical_risk": 0.10,
    }

    # Risk score thresholds
    THRESHOLDS = {
        "critical": 0.8,
        "high": 0.6,
        "medium": 0.4,
        "low": 0.0,
    }

    def __init__(self):
        self.context_cache: Dict[str, RiskContext] = {}

    def fuse_asset_data(
        self,
        asset_id: str,
        sensor_data: Optional[Dict] = None,
        permit_data: Optional[List[Dict]] = None,
        weather_data: Optional[Dict] = None,
        maintenance_data: Optional[Dict] = None,
        historical_data: Optional[Dict] = None,
        zone_data: Optional[Dict] = None,
    ) -> RiskContext:
        """
        Create a fused RiskContext from all available data sources.
        Missing data sources are handled gracefully with defaults.
        """
        context = RiskContext(asset_id=asset_id)

        # Fuse sensor data
        if sensor_data:
            self._fuse_sensor_data(context, sensor_data)

        # Fuse permit data
        if permit_data:
            self._fuse_permit_data(context, permit_data)

        # Fuse weather data
        if weather_data:
            self._fuse_weather_data(context, weather_data)

        # Fuse maintenance data
        if maintenance_data:
            self._fuse_maintenance_data(context, maintenance_data)

        # Fuse historical data
        if historical_data:
            self._fuse_historical_data(context, historical_data)

        # Fuse zone data
        if zone_data:
            self._fuse_zone_data(context, zone_data)

        # Calculate overall risk score
        self._calculate_risk_score(context)

        # Cache the context
        self.context_cache[asset_id] = context

        return context

    def _fuse_sensor_data(self, context: RiskContext, data: Dict):
        """Process and fuse sensor data into context."""
        readings = data.get("readings", {})
        context.sensor_readings = readings

        # Identify alarms
        for sensor_type, value in readings.items():
            alarm_config = data.get("alarm_config", {}).get(sensor_type, {})
            if alarm_config.get("critical_high") and value >= alarm_config["critical_high"]:
                context.sensor_critical.append(sensor_type)
            elif alarm_config.get("critical_low") and value <= alarm_config["critical_low"]:
                context.sensor_critical.append(sensor_type)
            elif alarm_config.get("alarm_high") and value >= alarm_config["alarm_high"]:
                context.sensor_alarms.append(sensor_type)
            elif alarm_config.get("alarm_low") and value <= alarm_config["alarm_low"]:
                context.sensor_alarms.append(sensor_type)

        # Check for stale readings
        last_update = data.get("last_update")
        if last_update:
            age = (datetime.utcnow() - last_update).total_seconds()
            if age > self.STALE_READING_SECONDS:
                context.risk_factors.append(f"Sensor data stale ({int(age)}s old)")

    def _fuse_permit_data(self, context: RiskContext, permits: List[Dict]):
        """Process and fuse permit data into context."""
        now = datetime.utcnow()

        for permit in permits:
            status = permit.get("status", "")

            if status in ("approved", "active"):
                context.active_permits.append(permit)

                # Check for expired permits
                end_time = permit.get("requested_end")
                if end_time and isinstance(end_time, datetime) and end_time < now:
                    context.expired_permits.append(permit)
                    context.risk_factors.append(
                        f"Expired permit: {permit.get('permit_number', 'unknown')}"
                    )

            # Check for permit conflicts (simplified)
            if permit.get("is_suspended"):
                context.permit_conflicts.append(
                    {
                        "permit_id": permit.get("id"),
                        "reason": permit.get("suspension_reason", "Unknown"),
                    }
                )

        # Check for conflicting permit types at same location
        hot_work = [p for p in context.active_permits if p.get("permit_type") == "hot_work"]
        confined = [
            p
            for p in context.active_permits
            if p.get("permit_type") == "confined_space"
        ]
        if hot_work and confined:
            context.permit_conflicts.append(
                {
                    "type": "hot_work_confined_conflict",
                    "description": "Hot work and confined space permits active simultaneously",
                }
            )

    def _fuse_weather_data(self, context: RiskContext, data: Dict):
        """Process and fuse weather data into context."""
        context.wind_speed = data.get("wind_speed")
        context.wind_direction = data.get("wind_direction")
        context.temperature_ambient = data.get("temperature")
        context.humidity = data.get("humidity")
        context.rainfall = data.get("rainfall")

        # High wind risk
        if context.wind_speed and context.wind_speed > 40:  # km/h
            context.risk_factors.append(f"High wind: {context.wind_speed} km/h")

        # Extreme temperature
        if context.temperature_ambient:
            if context.temperature_ambient > 45:
                context.risk_factors.append(
                    f"Extreme heat: {context.temperature_ambient}°C"
                )
            elif context.temperature_ambient < 0:
                context.risk_factors.append(
                    f"Extreme cold: {context.temperature_ambient}°C"
                )

    def _fuse_maintenance_data(self, context: RiskContext, data: Dict):
        """Process and fuse maintenance data into context."""
        context.overdue_inspections = data.get("overdue_inspections", False)
        context.overdue_calibrations = data.get("overdue_calibrations", False)
        context.pending_maintenance = data.get("pending_maintenance", [])

        if context.overdue_inspections:
            context.risk_factors.append("Overdue asset inspection")
        if context.overdue_calibrations:
            context.risk_factors.append("Overdue sensor calibration")

    def _fuse_historical_data(self, context: RiskContext, data: Dict):
        """Process and fuse historical incident data into context."""
        context.recent_incidents = data.get("recent_incidents", [])
        context.near_miss_count_30d = data.get("near_miss_count_30d", 0)
        context.incident_count_90d = data.get("incident_count_90d", 0)

        if context.near_miss_count_30d > 3:
            context.risk_factors.append(
                f"High near-miss rate: {context.near_miss_count_30d} in 30 days"
            )
        if context.incident_count_90d > 2:
            context.risk_factors.append(
                f"Frequent incidents: {context.incident_count_90d} in 90 days"
            )

    def _fuse_zone_data(self, context: RiskContext, data: Dict):
        """Process and fuse zone data into context."""
        context.zone_risk_level = data.get("risk_level", "low")
        context.zone_permit_count = data.get("permit_count", 0)
        context.zone_personnel_count = data.get("personnel_count", 0)

        if context.zone_permit_count > 5:
            context.risk_factors.append(
                f"High permit density: {context.zone_permit_count} active permits in zone"
            )

    def _calculate_risk_score(self, context: RiskContext):
        """
        Calculate overall risk score (0.0 to 1.0) using weighted factors.
        """
        scores = {}

        # Sensor alarm score
        alarm_count = len(context.sensor_alarms)
        critical_count = len(context.sensor_critical)
        scores["sensor_alarms"] = min(1.0, (alarm_count * 0.15) + (critical_count * 0.3))

        # Sensor critical score
        scores["sensor_critical"] = min(1.0, critical_count * 0.35)

        # Permit risk score
        permit_risk = 0.0
        if context.expired_permits:
            permit_risk += 0.3 * len(context.expired_permits)
        if context.permit_conflicts:
            permit_risk += 0.4 * len(context.permit_conflicts)
        if len(context.active_permits) > 3:
            permit_risk += 0.2
        scores["permit_risk"] = min(1.0, permit_risk)

        # Weather risk score
        weather_risk = 0.0
        if context.wind_speed and context.wind_speed > 40:
            weather_risk += 0.3
        if context.temperature_ambient and (
            context.temperature_ambient > 45 or context.temperature_ambient < 0
        ):
            weather_risk += 0.3
        if context.rainfall and context.rainfall > 50:
            weather_risk += 0.2
        scores["weather_risk"] = min(1.0, weather_risk)

        # Maintenance risk score
        maintenance_risk = 0.0
        if context.overdue_inspections:
            maintenance_risk += 0.4
        if context.overdue_calibrations:
            maintenance_risk += 0.3
        if context.pending_maintenance:
            maintenance_risk += 0.1 * min(len(context.pending_maintenance), 3)
        scores["maintenance_risk"] = min(1.0, maintenance_risk)

        # Historical risk score
        historical_risk = 0.0
        if context.near_miss_count_30d > 0:
            historical_risk += min(0.5, context.near_miss_count_30d * 0.1)
        if context.incident_count_90d > 0:
            historical_risk += min(0.5, context.incident_count_90d * 0.15)
        scores["historical_risk"] = min(1.0, historical_risk)

        # Weighted sum
        total_score = sum(
            scores.get(factor, 0) * weight
            for factor, weight in self.WEIGHTS.items()
        )

        context.overall_risk_score = min(1.0, total_score)

    def get_risk_level(self, score: float) -> str:
        """Convert numeric risk score to level string."""
        for level, threshold in sorted(
            self.THRESHOLDS.items(), key=lambda x: x[1], reverse=True
        ):
            if score >= threshold:
                return level
        return "low"

    def get_cached_context(self, asset_id: str) -> Optional[RiskContext]:
        """Get cached risk context for an asset."""
        return self.context_cache.get(asset_id)

    def get_fusion_summary(self) -> Dict:
        """Get summary of all fused contexts."""
        return {
            "total_assets": len(self.context_cache),
            "risk_distribution": {
                level: sum(
                    1
                    for c in self.context_cache.values()
                    if self.get_risk_level(c.overall_risk_score) == level
                )
                for level in ["low", "medium", "high", "critical"]
            },
            "assets_with_alarms": sum(
                1
                for c in self.context_cache.values()
                if c.sensor_alarms or c.sensor_critical
            ),
            "assets_with_permit_conflicts": sum(
                1
                for c in self.context_cache.values()
                if c.permit_conflicts
            ),
        }
