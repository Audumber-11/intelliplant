"""Emergency Response Orchestrator — auto-generates ICS plans, manages escalation, tracks response."""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from uuid import UUID, uuid4


class EmergencyResponseEngine:
    """Orchestrates emergency response with ICS plans and auto-escalation."""
    
    EMERGENCY_LEVELS = {
        "level_1": {"name": "Minor", "response_time": 15, "teams": ["response_team"], "notify": ["safety_officer"]},
        "level_2": {"name": "Major", "response_time": 10, "teams": ["response_team", "fire_team"], "notify": ["safety_officer", "plant_manager"]},
        "level_3": {"name": "Critical", "response_time": 5, "teams": ["response_team", "fire_team", "medical_team"], "notify": ["safety_officer", "plant_manager", "external_agencies"]},
    }
    
    ICS_TEMPLATES = {
        "fire": {
            "immediate_actions": [
                "Activate fire alarm",
                "Evacuate affected area",
                "Deploy fire suppression teams",
                "Establish hot/warm/cold zones",
                "Account for all personnel at muster point",
            ],
            "investigation_steps": [
                "Photograph fire origin and spread",
                "Interview witnesses",
                "Collect physical evidence",
                "Review CCTV footage",
                "Check maintenance records for ignition sources",
            ],
            "regulatory_notifications": [
                "Factory Inspectorate within 24 hours",
                "State Pollution Control Board",
                "District Disaster Management Authority",
            ],
        },
        "toxic_release": {
            "immediate_actions": [
                "Activate emergency shutdown for affected unit",
                "Deploy SCBA-equipped response team",
                "Establish exclusion zone (500m minimum)",
                "Activate meteorological monitoring",
                "Notify neighboring facilities",
            ],
            "investigation_steps": [
                "Monitor atmospheric concentrations",
                "Map plume dispersion pattern",
                "Check process historian for abnormal readings",
                "Review instrument calibration records",
                "Interview control room operators",
            ],
            "regulatory_notifications": [
                "Factory Inspectorate immediately",
                "District Collector within 4 hours",
                "Central Pollution Control Board",
                "National Disaster Response Force if major",
            ],
        },
        "explosion": {
            "immediate_actions": [
                "Activate all emergency alarms",
                "Full plant evacuation",
                "Deploy all response teams",
                "Establish command post",
                "Request mutual aid if needed",
            ],
            "investigation_steps": [
                "Secure blast scene",
                "Document structural damage",
                "Check process upset records",
                "Review pressure relief valve history",
                "Analyze metallurgical samples",
            ],
            "regulatory_notifications": [
                "Factory Inspectorate immediately",
                "Chief Inspector of Factories",
                "State Disaster Response Force",
                "National Safety Council",
            ],
        },
        "fall": {
            "immediate_actions": [
                "Secure the fall area",
                "Administer first aid",
                "Arrange medical evacuation",
                "Preserve the scene",
                "Notify safety officer",
            ],
            "investigation_steps": [
                "Photograph fall location and equipment",
                "Check harness and fall protection equipment",
                "Review work-at-height permit",
                "Interview worker and supervisor",
                "Check training records",
            ],
            "regulatory_notifications": [
                "Factory Inspectorate within 24 hours",
                "Workers' Compensation Board",
            ],
        },
        "default": {
            "immediate_actions": [
                "Ensure scene safety",
                "Provide first aid",
                "Notify emergency response team",
                "Secure the area",
                "Preserve evidence",
            ],
            "investigation_steps": [
                "Interview witnesses",
                "Document scene",
                "Review procedures",
                "Identify root cause",
                "Develop corrective actions",
            ],
            "regulatory_notifications": [
                "Factory Inspectorate within 24 hours",
            ],
        },
    }
    
    def generate_ics_plan(self, emergency: Dict) -> Dict:
        category = emergency.get("category", "default").lower()
        level = emergency.get("emergency_level", "level_1")
        level_config = self.EMERGENCY_LEVELS.get(level, self.EMERGENCY_LEVELS["level_1"])
        
        template = self.ICS_TEMPLATES.get(category, self.ICS_TEMPLATES["default"])
        
        plan = {
            "plan_id": str(uuid4()),
            "emergency_id": emergency.get("id"),
            "category": category,
            "level": level,
            "level_name": level_config["name"],
            "incident_commander": None,
            "response_team": level_config["teams"],
            "notification_list": level_config["notify"],
            "response_time_target": level_config["response_time"],
            "immediate_actions": template["immediate_actions"],
            "investigation_steps": template["investigation_steps"],
            "regulatory_notifications": template["regulatory_notifications"],
            "muster_points": self._get_muster_points(emergency),
            "resource_requirements": self._estimate_resources(level, category),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        return plan
    
    def check_escalation(self, emergency: Dict, elapsed_minutes: float) -> Dict:
        current_level = emergency.get("emergency_level", "level_1")
        
        escalate = False
        new_level = current_level
        reason = None
        
        if current_level == "level_1" and elapsed_minutes > 15:
            escalate = True
            new_level = "level_2"
            reason = "Response time exceeded for Level 1"
        
        elif current_level == "level_2" and elapsed_minutes > 30:
            escalate = True
            new_level = "level_3"
            reason = "Response time exceeded for Level 2"
        
        severity = emergency.get("severity", "low")
        if severity == "critical" and current_level != "level_3":
            escalate = True
            new_level = "level_3"
            reason = "Critical severity requires Level 3 response"
        
        return {
            "should_escalate": escalate,
            "current_level": current_level,
            "new_level": new_level,
            "reason": reason,
            "elapsed_minutes": round(elapsed_minutes, 1),
            "checked_at": datetime.utcnow().isoformat(),
        }
    
    def track_response_metrics(self, emergencies: List[Dict]) -> Dict:
        if not emergencies:
            return {"total": 0, "metrics": {}}
        
        total = len(emergencies)
        response_times = []
        resolved = 0
        
        for em in emergencies:
            declared = em.get("declared_at")
            responded = em.get("responded_at")
            
            if declared and responded:
                if isinstance(declared, str):
                    declared = datetime.fromisoformat(declared)
                if isinstance(responded, str):
                    responded = datetime.fromisoformat(responded)
                if hasattr(declared, "timestamp") and hasattr(responded, "timestamp"):
                    rt = (responded - declared).total_seconds() / 60
                    response_times.append(rt)
            
            if em.get("status") == "resolved":
                resolved += 1
        
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total": total,
            "resolved": resolved,
            "active": total - resolved,
            "metrics": {
                "avg_response_time_minutes": round(avg_response, 1),
                "min_response_time_minutes": round(min(response_times), 1) if response_times else 0,
                "max_response_time_minutes": round(max(response_times), 1) if response_times else 0,
                "resolution_rate": round(resolved / total, 3) if total > 0 else 0.0,
            },
            "analyzed_at": datetime.utcnow().isoformat(),
        }
    
    def generate_muster_plan(self, plant_layout: Dict, emergency_type: str) -> Dict:
        muster_points = [
            {"name": "Primary Muster", "lat": 28.6149, "lng": 77.2075, "capacity": 200},
            {"name": "Secondary Muster", "lat": 28.6155, "lng": 77.211, "capacity": 150},
        ]
        
        return {
            "emergency_type": emergency_type,
            "primary_muster": muster_points[0],
            "secondary_muster": muster_points[1],
            "evacuation_routes": [
                {"from": "process_area", "to": "Primary Muster", "estimated_time": "3 minutes"},
                {"from": "tank_farm", "to": "Secondary Muster", "estimated_time": "5 minutes"},
            ],
            "accountability_method": "head count at muster points",
            "special_needs": "Check control room, offices, and maintenance workshop",
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    def _get_muster_points(self, emergency: Dict) -> List[Dict]:
        return [
            {"name": "Primary Muster Point", "location": "Main Gate Parking", "capacity": 200},
            {"name": "Secondary Muster Point", "location": "Admin Building Lawn", "capacity": 150},
        ]
    
    def _estimate_resources(self, level: str, category: str) -> Dict:
        base = {
            "level_1": {"personnel": 10, "vehicles": 2, "equipment": ["fire extinguishers", "SCBA", "first aid kits"]},
            "level_2": {"personnel": 25, "vehicles": 5, "equipment": ["fire truck", "ambulance", "SCBA", "communication equipment"]},
            "level_3": {"personnel": 50, "vehicles": 10, "equipment": ["fire truck", "ambulance", "hazmat team", "crane", "communication equipment"]},
        }
        return base.get(level, base["level_1"])
