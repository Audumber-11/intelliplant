"""Asset tracker — tracks personnel and equipment locations."""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from uuid import UUID


class AssetTracker:
    """Tracks asset and personnel locations on the plant layout."""
    
    PLANT_CENTER = {"lat": 28.6139, "lng": 77.2090}
    
    ZONE_CENTERS = {
        "reactor_area": {"lat": 28.6142, "lng": 77.2093},
        "tank_farm": {"lat": 28.6141, "lng": 77.2102},
        "compressor_station": {"lat": 28.6144, "lng": 77.2082},
        "control_room": {"lat": 28.6147, "lng": 77.2105},
        "muster_point": {"lat": 28.6149, "lng": 77.2075},
        "workshop": {"lat": 28.6136, "lng": 77.2087},
        "parking": {"lat": 28.6131, "lng": 77.2082},
    }
    
    PERSONNEL_NAMES = [
        "Rajesh Kumar", "Amit Singh", "Priya Sharma", "Vikram Patel",
        "Sanjay Gupta", "Anita Desai", "Mohammed Ali", "Deepa Nair",
        "Suresh Reddy", "Kavita Joshi", "Ravi Shankar", "Meena Kumari",
        "Arun Mehta", "Sunita Devi", "Manoj Tiwari", "Pooja Verma",
    ]
    
    def __init__(self):
        self._personnel_cache: Dict[str, Dict] = {}
        self._initialize_personnel()
    
    def _initialize_personnel(self):
        zones = list(self.ZONE_CENTERS.keys())
        for i, name in enumerate(self.PERSONNEL_NAMES):
            zone = zones[i % len(zones)]
            zone_center = self.ZONE_CENTERS[zone]
            self._personnel_cache[f"PER-{i+1:03d}"] = {
                "personnel_id": f"PER-{i+1:03d}",
                "name": name,
                "lat": zone_center["lat"] + random.uniform(-0.0001, 0.0001),
                "lng": zone_center["lng"] + random.uniform(-0.0001, 0.0001),
                "zone_name": zone,
                "status": "active",
                "last_update": (datetime.utcnow() - timedelta(minutes=random.randint(1, 30))).isoformat(),
            }
    
    def get_personnel_locations(self) -> List[Dict]:
        return list(self._personnel_cache.values())
    
    def get_asset_locations(self, assets: list) -> List[Dict]:
        locations = []
        for asset in assets:
            lat = asset.latitude or self.PLANT_CENTER["lat"] + random.uniform(-0.001, 0.001)
            lng = asset.longitude or self.PLANT_CENTER["lng"] + random.uniform(-0.001, 0.001)
            
            zone = self._find_zone(lat, lng)
            
            locations.append({
                "asset_id": str(asset.id),
                "tag": asset.tag,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "lat": lat,
                "lng": lng,
                "zone_name": zone,
                "risk_level": "safe",
                "last_update": datetime.utcnow().isoformat(),
            })
        
        return locations
    
    def _find_zone(self, lat: float, lng: float) -> str:
        min_dist = float("inf")
        closest_zone = "unknown"
        
        for zone_name, center in self.ZONE_CENTERS.items():
            dist = math.sqrt((lat - center["lat"]) ** 2 + (lng - center["lng"]) ** 2)
            if dist < min_dist:
                min_dist = dist
                closest_zone = zone_name
        
        return closest_zone
    
    def update_personnel_location(self, personnel_id: str, lat: float, lng: float) -> Optional[Dict]:
        if personnel_id not in self._personnel_cache:
            return None
        
        zone = self._find_zone(lat, lng)
        self._personnel_cache[personnel_id].update({
            "lat": lat,
            "lng": lng,
            "zone_name": zone,
            "last_update": datetime.utcnow().isoformat(),
        })
        
        return self._personnel_cache[personnel_id]
    
    def get_zone_occupancy(self) -> Dict[str, int]:
        occupancy: Dict[str, int] = {}
        for p in self._personnel_cache.values():
            zone = p.get("zone_name", "unknown")
            occupancy[zone] = occupancy.get(zone, 0) + 1
        return occupancy
    
    def trigger_emergency_evacuation(self) -> List[Dict]:
        evacuated = []
        for pid, p in self._personnel_cache.items():
            p["status"] = "evacuated"
            p["zone_name"] = "muster_point"
            p["lat"] = self.ZONE_CENTERS["muster_point"]["lat"] + random.uniform(-0.00005, 0.00005)
            p["lng"] = self.ZONE_CENTERS["muster_point"]["lng"] + random.uniform(-0.00005, 0.00005)
            p["last_update"] = datetime.utcnow().isoformat()
            evacuated.append(p)
        
        return evacuated


import math
