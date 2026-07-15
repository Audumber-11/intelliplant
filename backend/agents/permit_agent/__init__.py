"""Permit Intelligence Agent — conflict detection, risk scoring, compliance verification."""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from uuid import UUID


class PermitIntelligenceEngine:
    """Analyzes permits for conflicts, risk, and compliance."""
    
    CONFLICT_RULES = [
        {"name": "same_asset_overlap", "description": "Permits on same asset with overlapping times", "severity": "high"},
        {"name": "hot_work_near_gas", "description": "Hot work permit near active gas leak risk", "severity": "critical"},
        {"name": "concurrent_excavation", "description": "Multiple excavation permits in same zone", "severity": "medium"},
        {"name": "loto_conflict", "description": "LOTO and maintenance on same equipment", "severity": "high"},
        {"name": "expired_gas_test", "description": "Gas test validity expired for active permit", "severity": "critical"},
    ]
    
    RISK_FACTORS = {
        "hot_work": {"weight": 0.3, "keywords": ["hot work", "welding", "cutting", "grinding", "fire"]},
        "confined_space": {"weight": 0.25, "keywords": ["confined space", "entry", "vessel", "tank"]},
        "excavation": {"weight": 0.2, "keywords": ["excavation", "digging", "trench", "buried"]},
        "working_at_height": {"weight": 0.2, "keywords": ["height", "scaffold", "elevated", "ladder"]},
        "electrical": {"weight": 0.25, "keywords": ["electrical", "live", "power", "energized"]},
        "chemical": {"weight": 0.3, "keywords": ["chemical", "hazardous", "toxic", "corrosive"]},
    }
    
    def detect_conflicts(self, permits: List[Dict]) -> List[Dict]:
        conflicts = []
        
        active_permits = [p for p in permits if p.get("status") in ("approved", "active")]
        
        for i, p1 in enumerate(active_permits):
            for p2 in active_permits[i + 1:]:
                if self._times_overlap(p1, p2):
                    if p1.get("asset_id") == p2.get("asset_id"):
                        conflicts.append({
                            "conflict_type": "same_asset_overlap",
                            "severity": "high",
                            "description": f"Permits {p1.get('permit_number', 'N/A')} and {p2.get('permit_number', 'N/A')} overlap on same asset",
                            "conflicting_permit_id": str(p2.get("id")),
                            "conflicting_permit_number": p2.get("permit_number", "N/A"),
                            "recommendation": "Coordinate timing or separate work areas",
                            "permit_ids": [str(p1.get("id")), str(p2.get("id"))],
                        })
                    
                    if self._is_hot_work(p1) and self._has_gas_risk(p2):
                        conflicts.append({
                            "conflict_type": "hot_work_near_gas",
                            "severity": "critical",
                            "description": f"Hot work permit {p1.get('permit_number')} near active gas risk ({p2.get('permit_number')})",
                            "conflicting_permit_id": str(p2.get("id")),
                            "conflicting_permit_number": p2.get("permit_number", "N/A"),
                            "recommendation": "Suspend hot work until gas risk is resolved",
                            "permit_ids": [str(p1.get("id")), str(p2.get("id"))],
                        })
                    
                    if self._is_excavation(p1) and self._is_excavation(p2):
                        if p1.get("zone_id") == p2.get("zone_id"):
                            conflicts.append({
                                "conflict_type": "concurrent_excavation",
                                "severity": "medium",
                                "description": f"Multiple excavation permits in same zone",
                                "conflicting_permit_id": str(p2.get("id")),
                                "conflicting_permit_number": p2.get("permit_number", "N/A"),
                                "recommendation": "Consolidate excavation work or stagger schedules",
                                "permit_ids": [str(p1.get("id")), str(p2.get("id"))],
                            })
        
        return conflicts
    
    def score_permit_risk(self, permit: Dict, active_permits: List[Dict] = None) -> Dict:
        risk_score = 0.0
        risk_factors = []
        
        title = f"{permit.get('title', '')} {permit.get('work_scope', '')}".lower()
        
        for factor_name, factor_info in self.RISK_FACTORS.items():
            for keyword in factor_info["keywords"]:
                if keyword in title:
                    risk_score += factor_info["weight"]
                    risk_factors.append(factor_name)
                    break
        
        if permit.get("gas_test_required") and not permit.get("gas_test_valid_until"):
            risk_score += 0.2
            risk_factors.append("gas_test_pending")
        
        if permit.get("loto_required"):
            risk_score += 0.1
            risk_factors.append("loto_required")
        
        if active_permits:
            conflicts = self.detect_conflicts([permit] + active_permits)
            if conflicts:
                risk_score += 0.3 * len(conflicts)
                risk_factors.append(f"{len(conflicts)}_conflicts_detected")
        
        risk_score = min(risk_score, 1.0)
        
        risk_level = "low"
        if risk_score >= 0.7:
            risk_level = "critical"
        elif risk_score >= 0.5:
            risk_level = "high"
        elif risk_score >= 0.3:
            risk_level = "medium"
        
        conditions = []
        if "hot_work" in risk_factors:
            conditions.append("Fire watch required during and 30 min after work")
        if "confined_space" in risk_factors:
            conditions.append("Continuous atmospheric monitoring required")
        if "gas_test_pending" in risk_factors:
            conditions.append("Gas test must be completed before work starts")
        if "loto_required" in risk_factors:
            conditions.append("Verify all energy sources isolated before work")
        
        return {
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommended_conditions": conditions,
            "requires_supervision": risk_score >= 0.5,
            "requires_gas_test": "hot_work" in risk_factors or "confined_space" in risk_factors,
            "calculated_at": datetime.utcnow().isoformat(),
        }
    
    def validate_permit(self, permit: Dict) -> Dict:
        issues = []
        warnings = []
        
        if not permit.get("title"):
            issues.append({"field": "title", "message": "Title is required"})
        if not permit.get("requested_start") or not permit.get("requested_end"):
            issues.append({"field": "time", "message": "Start and end times are required"})
        elif permit.get("requested_start") and permit.get("requested_end"):
            start = permit["requested_start"]
            end = permit["requested_end"]
            if hasattr(start, "timestamp") and hasattr(end, "timestamp"):
                if end <= start:
                    issues.append({"field": "time", "message": "End time must be after start time"})
                duration = (end - start).total_seconds() / 3600
                if duration > 12:
                    warnings.append(f"Long permit duration: {duration:.1f} hours")
        
        if not permit.get("created_by_id"):
            issues.append({"field": "creator", "message": "Creator is required"})
        
        title = f"{permit.get('title', '')} {permit.get('work_scope', '')}".lower()
        if "hot work" in title and not permit.get("gas_test_required"):
            warnings.append("Hot work typically requires gas test")
        if "confined space" in title and not permit.get("loto_required"):
            warnings.append("Confined space entry may require LOTO")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "validated_at": datetime.utcnow().isoformat(),
        }
    
    def get_permit_analytics(self, permits: List[Dict]) -> Dict:
        if not permits:
            return {"total": 0, "by_status": {}, "by_type": {}, "avg_risk": 0.0}
        
        by_status = {}
        by_type = {}
        risk_scores = []
        
        for p in permits:
            status = p.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
            
            ptype = p.get("permit_type", "unknown")
            by_type[ptype] = by_type.get(ptype, 0) + 1
            
            risk = self.score_permit_risk(p)
            risk_scores.append(risk["risk_score"])
        
        return {
            "total": len(permits),
            "by_status": by_status,
            "by_type": by_type,
            "avg_risk": round(sum(risk_scores) / len(risk_scores), 3) if risk_scores else 0.0,
            "high_risk_permits": sum(1 for r in risk_scores if r >= 0.5),
            "analyzed_at": datetime.utcnow().isoformat(),
        }
    
    @staticmethod
    def _times_overlap(p1: Dict, p2: Dict) -> bool:
        start1 = p1.get("requested_start")
        end1 = p1.get("requested_end")
        start2 = p2.get("requested_start")
        end2 = p2.get("requested_end")
        
        if not all([start1, end1, start2, end2]):
            return False
        
        try:
            if isinstance(start1, str):
                start1 = datetime.fromisoformat(start1)
            if isinstance(end1, str):
                end1 = datetime.fromisoformat(end1)
            if isinstance(start2, str):
                start2 = datetime.fromisoformat(start2)
            if isinstance(end2, str):
                end2 = datetime.fromisoformat(end2)
            
            return start1 < end2 and start2 < end1
        except:
            return False
    
    @staticmethod
    def _is_hot_work(permit: Dict) -> bool:
        title = f"{permit.get('title', '')} {permit.get('work_scope', '')}".lower()
        return any(kw in title for kw in ["hot work", "welding", "cutting", "grinding", "fire"])
    
    @staticmethod
    def _has_gas_risk(permit: Dict) -> bool:
        title = f"{permit.get('title', '')} {permit.get('work_scope', '')}".lower()
        return any(kw in title for kw in ["gas", "h2s", "leak", "hydrocarbon"])
    
    @staticmethod
    def _is_excavation(permit: Dict) -> bool:
        title = f"{permit.get('title', '')} {permit.get('work_scope', '')}".lower()
        return any(kw in title for kw in ["excavation", "digging", "trench", "earthwork"])
