"""Plant layout manager — generates GeoJSON for plant visualization."""
import math
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from .schemas import GeoFeature, GeoFeatureCollection, ZoneType


class PlantLayoutManager:
    """Generates plant layout GeoJSON from database models."""
    
    PLANT_CENTER = {"lat": 28.6139, "lng": 77.2090}
    
    ZONE_TEMPLATES = {
        "reactor_area": {
            "name": "Reactor Area",
            "zone_type": ZoneType.PROCESS_UNIT,
            "color": "#e74c3c",
            "risk_class": "high",
            "offset": (0.0005, 0.0003),
        },
        "tank_farm": {
            "name": "Tank Farm",
            "zone_type": ZoneType.STORAGE_TANK,
            "color": "#e67e22",
            "risk_class": "high",
            "offset": (0.0012, 0.0002),
        },
        "compressor_station": {
            "name": "Compressor Station",
            "zone_type": ZoneType.PROCESS_UNIT,
            "color": "#f39c12",
            "risk_class": "medium",
            "offset": (-0.0008, 0.0005),
        },
        "control_room": {
            "name": "Central Control Room",
            "zone_type": ZoneType.CONTROL_ROOM,
            "color": "#27ae60",
            "risk_class": "safe",
            "offset": (0.0015, 0.0008),
        },
        "muster_point": {
            "name": "Emergency Muster Point",
            "zone_type": ZoneType.MUSTER_POINT,
            "color": "#2ecc71",
            "risk_class": "safe",
            "offset": (-0.0015, 0.001),
        },
        "fire_hydrant_area": {
            "name": "Fire Hydrant Station",
            "zone_type": ZoneType.FIRE_HYDRANT,
            "color": "#e74c3c",
            "risk_class": "safe",
            "offset": (0.0008, -0.0005),
        },
        "workshop": {
            "name": "Maintenance Workshop",
            "zone_type": ZoneType.GENERAL,
            "color": "#3498db",
            "risk_class": "low",
            "offset": (-0.001, -0.0003),
        },
        "parking": {
            "name": "Vehicle Parking",
            "zone_type": ZoneType.PARKING,
            "color": "#95a5a6",
            "risk_class": "safe",
            "offset": (-0.0018, -0.0008),
        },
    }
    
    def generate_plant_layout(self, assets: list, sensors: list, zones: list) -> GeoFeatureCollection:
        features = []
        
        for zone_data in self.ZONE_TEMPLATES.values():
            center_lat = self.PLANT_CENTER["lat"] + zone_data["offset"][1]
            center_lng = self.PLANT_CENTER["lng"] + zone_data["offset"][0]
            polygon = self._make_square(center_lat, center_lng, size=0.0003)
            features.append(GeoFeature(
                geometry={"type": "Polygon", "coordinates": [polygon]},
                properties={
                    "type": "zone",
                    "name": zone_data["name"],
                    "zone_type": zone_data["zone_type"].value,
                    "color": zone_data["color"],
                    "risk_class": zone_data["risk_class"],
                }
            ))
        
        for asset in assets:
            lat = asset.latitude or self.PLANT_CENTER["lat"]
            lng = asset.longitude or self.PLANT_CENTER["lng"]
            features.append(GeoFeature(
                geometry={"type": "Point", "coordinates": [lng, lat]},
                properties={
                    "type": "asset",
                    "id": str(asset.id),
                    "tag": asset.tag,
                    "name": asset.name,
                    "asset_type": asset.asset_type,
                }
            ))
        
        for sensor in sensors:
            lat = sensor.latitude or (self.PLANT_CENTER["lat"] + hash(sensor.tag) % 100 * 0.00001)
            lng = sensor.longitude or (self.PLANT_CENTER["lng"] + hash(sensor.tag + "lng") % 100 * 0.00001)
            features.append(GeoFeature(
                geometry={"type": "Point", "coordinates": [lng, lat]},
                properties={
                    "type": "sensor",
                    "id": str(sensor.id),
                    "tag": sensor.tag,
                    "sensor_type": sensor.sensor_type,
                    "asset_id": str(sensor.asset_id) if sensor.asset_id else None,
                }
            ))
        
        return GeoFeatureCollection(features=features)
    
    def generate_risk_overlay(self, zone_risks: list) -> GeoFeatureCollection:
        features = []
        for zr in zone_risks:
            zone_data = self.ZONE_TEMPLATES.get(zr.get("zone_name", "").lower().replace(" ", "_"), {})
            offset = zone_data.get("offset", (0.0, 0.0))
            center_lat = self.PLANT_CENTER["lat"] + offset[1]
            center_lng = self.PLANT_CENTER["lng"] + offset[0]
            polygon = self._make_square(center_lat, center_lng, size=0.0003)
            
            risk_level = zr.get("risk_level", "safe")
            color_map = {
                "safe": "#2ecc71",
                "low": "#27ae60",
                "medium": "#f39c12",
                "high": "#e67e22",
                "critical": "#e74c3c",
            }
            
            features.append(GeoFeature(
                geometry={"type": "Polygon", "coordinates": [polygon]},
                properties={
                    "type": "risk_overlay",
                    "zone_name": zr.get("zone_name", "Unknown"),
                    "risk_score": zr.get("risk_score", 0.0),
                    "risk_level": risk_level,
                    "color": color_map.get(risk_level, "#95a5a6"),
                    "active_sensors": zr.get("active_sensors", 0),
                    "active_permits": zr.get("active_permits", 0),
                }
            ))
        
        return GeoFeatureCollection(features=features)
    
    def generate_muster_routes(self) -> GeoFeatureCollection:
        muster = self.PLANT_CENTER
        routes = [
            {"from": "reactor_area", "to": "muster_point", "via": [(0.0002, 0.0006), (0.0005, 0.0009), (0.0008, 0.001), (-0.0015, 0.001)]},
            {"from": "tank_farm", "to": "muster_point", "via": [(0.0012, 0.0005), (0.001, 0.0008), (0.0005, 0.001), (-0.0015, 0.001)]},
            {"from": "compressor_station", "to": "muster_point", "via": [(-0.0005, 0.0007), (-0.0008, 0.0009), (-0.0012, 0.001), (-0.0015, 0.001)]},
        ]
        
        features = []
        for route in routes:
            coordinates = []
            for via in route["via"]:
                coordinates.append([muster["lng"] + via[0], muster["lat"] + via[1]])
            
            features.append(GeoFeature(
                geometry={"type": "LineString", "coordinates": coordinates},
                properties={
                    "type": "muster_route",
                    "from_zone": route["from"],
                    "to_zone": route["to"],
                    "color": "#2ecc71",
                    "dash_array": [10, 5],
                }
            ))
        
        return GeoFeatureCollection(features=features)
    
    @staticmethod
    def _make_square(center_lat: float, center_lng: float, size: float = 0.0003) -> List[List[float]]:
        return [
            [center_lng - size, center_lat - size],
            [center_lng + size, center_lat - size],
            [center_lng + size, center_lat + size],
            [center_lng - size, center_lat + size],
            [center_lng - size, center_lat - size],
        ]
