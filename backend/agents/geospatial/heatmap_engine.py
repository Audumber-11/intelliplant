"""Heatmap engine — generates risk heatmaps using Inverse Distance Weighting interpolation."""
import math
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from uuid import UUID


class HeatmapEngine:
    """Generates risk heatmaps using IDW interpolation from sensor readings."""
    
    PLANT_CENTER = (28.6139, 77.2090)
    DEFAULT_GRID_SIZE = 15
    DEFAULT_RADIUS = 0.002  # ~200m in degrees
    
    RISK_THRESHOLDS = {
        "safe": 0.0,
        "low": 0.2,
        "medium": 0.4,
        "high": 0.6,
        "critical": 0.8,
    }
    
    SENSOR_WEIGHTS = {
        "gas_h2s": 1.5,
        "gas_ch4": 1.4,
        "gas_o2": 0.8,
        "temperature": 1.0,
        "pressure": 1.2,
        "vibration": 1.1,
        "flow": 0.7,
        "smoke": 1.6,
        "flame": 1.8,
        "weather": 0.6,
    }
    
    def __init__(self, grid_size: int = DEFAULT_GRID_SIZE, radius: float = DEFAULT_RADIUS):
        self.grid_size = grid_size
        self.radius = radius
    
    def generate_heatmap(
        self,
        sensor_data: List[Dict],
        existing_risks: List[Dict] = None,
        bounds: Optional[Dict[str, float]] = None,
    ) -> Dict:
        center = bounds if bounds else {
            "north": self.PLANT_CENTER[0] + self.radius,
            "south": self.PLANT_CENTER[0] - self.radius,
            "east": self.PLANT_CENTER[1] + self.radius,
            "west": self.PLANT_CENTER[1] - self.radius,
        }
        
        lat_step = (center["north"] - center["south"]) / self.grid_size
        lng_step = (center["east"] - center["west"]) / self.grid_size
        
        grid_points = []
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                lat = center["south"] + (i + 0.5) * lat_step
                lng = center["west"] + (j + 0.5) * lng_step
                grid_points.append((lat, lng))
        
        cells = []
        for lat, lng in grid_points:
            risk_score = self._idw_interpolate(lat, lng, sensor_data)
            
            risk_level = "safe"
            for level, threshold in sorted(self.RISK_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
                if risk_score >= threshold:
                    risk_level = level
                    break
            
            contributing = self._get_contributing_sensors(lat, lng, sensor_data)
            
            cells.append({
                "lat": lat,
                "lng": lng,
                "risk_score": round(risk_score, 3),
                "risk_level": risk_level,
                "contributing_sensors": contributing,
                "contributing_factors": [],
            })
        
        return {
            "bounds": center,
            "resolution": self.grid_size,
            "cells": cells,
            "timestamp": datetime.utcnow().isoformat(),
            "total_sensors": len(sensor_data),
            "avg_risk": round(sum(c["risk_score"] for c in cells) / len(cells), 3) if cells else 0.0,
            "max_risk": round(max(c["risk_score"] for c in cells), 3) if cells else 0.0,
            "critical_cells": sum(1 for c in cells if c["risk_level"] == "critical"),
            "high_risk_cells": sum(1 for c in cells if c["risk_level"] == "high"),
        }
    
    def _idw_interpolate(self, lat: float, lng: float, sensor_data: List[Dict]) -> float:
        if not sensor_data:
            return 0.0
        
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for sensor in sensor_data:
            s_lat = sensor.get("latitude", self.PLANT_CENTER[0])
            s_lng = sensor.get("longitude", self.PLANT_CENTER[1])
            risk_value = sensor.get("risk_value", 0.0)
            sensor_type = sensor.get("sensor_type", "unknown")
            
            distance = math.sqrt((lat - s_lat) ** 2 + (lng - s_lng) ** 2)
            
            type_weight = self.SENSOR_WEIGHTS.get(sensor_type, 1.0)
            
            if distance < 1e-10:
                return min(risk_value * type_weight, 1.0)
            
            w = (1.0 / (distance ** 2)) * type_weight
            weighted_sum += w * risk_value
            weight_sum += w
        
        if weight_sum == 0:
            return 0.0
        
        return min(weighted_sum / weight_sum, 1.0)
    
    def _get_contributing_sensors(self, lat: float, lng: float, sensor_data: List[Dict], max_contributors: int = 3) -> List[str]:
        distances = []
        for sensor in sensor_data:
            s_lat = sensor.get("latitude", self.PLANT_CENTER[0])
            s_lng = sensor.get("longitude", self.PLANT_CENTER[1])
            distance = math.sqrt((lat - s_lat) ** 2 + (lng - s_lng) ** 2)
            distances.append((distance, sensor.get("sensor_tag", "unknown")))
        
        distances.sort(key=lambda x: x[0])
        return [tag for _, tag in distances[:max_contributors]]
    
    def compute_zone_risk(self, zone_bounds: List[List[float]], sensor_data: List[Dict]) -> float:
        if not zone_bounds:
            return 0.0
        
        min_lng = min(p[0] for p in zone_bounds)
        max_lng = max(p[0] for p in zone_bounds)
        min_lat = min(p[1] for p in zone_bounds)
        max_lat = max(p[1] for p in zone_bounds)
        
        sample_size = 5
        total_risk = 0.0
        count = 0
        
        for i in range(sample_size):
            for j in range(sample_size):
                lat = min_lat + (i + 0.5) * (max_lat - min_lat) / sample_size
                lng = min_lng + (j + 0.5) * (max_lng - min_lng) / sample_size
                total_risk += self._idw_interpolate(lat, lng, sensor_data)
                count += 1
        
        return total_risk / count if count > 0 else 0.0
    
    def generate_sensor_risk_scores(self, readings: List[Dict], thresholds: Dict) -> List[Dict]:
        results = []
        for reading in readings:
            value = reading.get("value", 0.0)
            sensor_type = reading.get("sensor_type", "unknown")
            alarm_low = reading.get("alarm_low", 0.0)
            alarm_high = reading.get("alarm_high", 100.0)
            alarm_critical = reading.get("alarm_critical", 200.0)
            
            if alarm_critical > 0:
                risk = min(value / alarm_critical, 1.0)
            elif alarm_high > 0:
                risk = min(value / alarm_high, 0.8)
            elif alarm_low > 0 and value < alarm_low:
                risk = 0.3 if sensor_type == "gas_o2" else 0.1
            else:
                risk = 0.0
            
            results.append({
                "sensor_id": reading.get("sensor_id"),
                "sensor_tag": reading.get("sensor_tag"),
                "sensor_type": sensor_type,
                "value": value,
                "risk_value": round(risk, 3),
                "latitude": reading.get("latitude"),
                "longitude": reading.get("longitude"),
                "timestamp": reading.get("timestamp"),
            })
        
        return results
    
    def compute_heatmap_history(self, heatmap_snapshots: List[Dict]) -> List[Dict]:
        history = []
        for snapshot in heatmap_snapshots:
            cells = snapshot.get("cells", [])
            risk_scores = [c["risk_score"] for c in cells]
            
            history.append({
                "timestamp": snapshot.get("timestamp"),
                "avg_risk": round(sum(risk_scores) / len(risk_scores), 3) if risk_scores else 0.0,
                "max_risk": round(max(risk_scores), 3) if risk_scores else 0.0,
                "critical_zones": sum(1 for c in cells if c["risk_level"] == "critical"),
                "high_risk_zones": sum(1 for c in cells if c["risk_level"] == "high"),
            })
        
        return history
