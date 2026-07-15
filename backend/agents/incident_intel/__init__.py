"""Incident Pattern Intelligence — analyzes incident patterns, finds root causes, predicts recurrence."""
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from uuid import UUID


class IncidentPatternEngine:
    """Analyzes incident patterns for root cause analysis and prediction."""
    
    SEVERITY_WEIGHTS = {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.5,
        "low": 0.2,
    }
    
    CATEGORY_KEYWORDS = {
        "fire": ["fire", "flame", "smoke", "combustion", "ignition", "arson"],
        "explosion": ["explosion", "blast", "overpressure", "rupture"],
        "toxic_release": ["toxic", "gas leak", "h2s", "hcn", "nh3", "chlorine", "release"],
        "fall": ["fall", "slip", "trip", "height", "scaffold"],
        "mechanical": ["crush", "entangle", "rotate", "pinch", "machinery"],
        "electrical": ["shock", "electrocution", "arc flash", "short circuit"],
        "chemical": ["chemical", "spill", "corrosion", "reactive"],
        "structural": ["collapse", "structural", "foundation", "corrosion"],
    }
    
    ROOT_CAUSE_CATEGORIES = [
        "inadequate_procedures",
        "training_gap",
        "equipment_failure",
        "human_error",
        "design_deficiency",
        "maintenance_lapse",
        "communication_failure",
        "management_system",
        "environmental",
        "contractor_related",
    ]
    
    def analyze_incident_patterns(self, incidents: List[Dict]) -> Dict:
        if not incidents:
            return {"patterns": [], "recommendations": [], "risk_summary": {}}
        
        category_counts = {}
        severity_counts = {}
        temporal_patterns = []
        location_clusters = {}
        repeat_assets = {}
        
        for inc in incidents:
            cat = inc.get("category", "unknown")
            sev = inc.get("severity", "low")
            asset_id = inc.get("asset_id")
            
            category_counts[cat] = category_counts.get(cat, 0) + 1
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            if asset_id:
                repeat_assets[str(asset_id)] = repeat_assets.get(str(asset_id), 0) + 1
            
            occurred = inc.get("occurred_at")
            if occurred:
                if isinstance(occurred, str):
                    try:
                        occurred = datetime.fromisoformat(occurred.replace("Z", "+00:00"))
                    except:
                        continue
                temporal_patterns.append({
                    "month": occurred.month if hasattr(occurred, "month") else 0,
                    "hour": occurred.hour if hasattr(occurred, "hour") else 0,
                    "weekday": occurred.weekday() if hasattr(occurred, "weekday") else 0,
                })
        
        patterns = []
        
        top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        for cat, count in top_categories:
            if count >= 2:
                patterns.append({
                    "type": "category_cluster",
                    "category": cat,
                    "count": count,
                    "description": f"{count} incidents in '{cat}' category — investigate systemic issues",
                    "severity": "high" if count >= 3 else "medium",
                })
        
        repeat = {k: v for k, v in repeat_assets.items() if v >= 2}
        for asset_id, count in repeat.items():
            patterns.append({
                "type": "repeat_location",
                "asset_id": asset_id,
                "count": count,
                "description": f"Asset has {count} incidents — potential chronic hazard",
                "severity": "high",
            })
        
        if temporal_patterns:
            month_counts = {}
            for tp in temporal_patterns:
                m = tp["month"]
                month_counts[m] = month_counts.get(m, 0) + 1
            peak_month = max(month_counts.items(), key=lambda x: x[1], default=(0, 0))
            if peak_month[1] >= 2:
                patterns.append({
                    "type": "temporal_cluster",
                    "month": peak_month[0],
                    "count": peak_month[1],
                    "description": f"Peak incident month: {peak_month[0]} — consider seasonal factors",
                    "severity": "medium",
                })
        
        recommendations = self._generate_recommendations(patterns, incidents)
        
        return {
            "patterns": patterns,
            "recommendations": recommendations,
            "risk_summary": {
                "total_incidents": len(incidents),
                "category_distribution": category_counts,
                "severity_distribution": severity_counts,
                "repeat_assets": repeat,
                "pattern_count": len(patterns),
            },
            "analyzed_at": datetime.utcnow().isoformat(),
        }
    
    def find_similar_incidents(self, incident: Dict, historical: List[Dict], top_k: int = 5) -> List[Dict]:
        if not historical:
            return []
        
        scored = []
        for hist in historical:
            score = 0.0
            
            if hist.get("category") == incident.get("category"):
                score += 0.3
            
            if hist.get("severity") == incident.get("severity"):
                score += 0.2
            
            if hist.get("asset_id") == incident.get("asset_id"):
                score += 0.3
            
            inc_title = set(incident.get("title", "").lower().split())
            hist_title = set(hist.get("title", "").lower().split())
            overlap = len(inc_title & hist_title) / max(len(inc_title | hist_title), 1)
            score += 0.2 * overlap
            
            scored.append({"incident": hist, "similarity_score": round(score, 3)})
        
        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:top_k]
    
    def predict_recurrence_risk(self, asset_incidents: List[Dict], asset_info: Dict = None) -> Dict:
        if not asset_incidents:
            return {"risk_score": 0.0, "risk_level": "low", "factors": []}
        
        total = len(asset_incidents)
        recent_cutoff = datetime.utcnow() - timedelta(days=365)
        recent = 0
        for inc in asset_incidents:
            occurred = inc.get("occurred_at")
            if occurred and hasattr(occurred, "timestamp"):
                if occurred > recent_cutoff:
                    recent += 1
        
        frequency_score = min(total / 5.0, 1.0)
        recency_score = min(recent / 3.0, 1.0)
        
        severity_score = 0.0
        for inc in asset_incidents:
            sev = inc.get("severity", "low")
            severity_score += self.SEVERITY_WEIGHTS.get(sev, 0.1)
        severity_score = min(severity_score / len(asset_incidents), 1.0)
        
        risk_score = (frequency_score * 0.4 + recency_score * 0.35 + severity_score * 0.25)
        
        factors = []
        if total >= 3:
            factors.append(f"High incident frequency: {total} incidents")
        if recent >= 2:
            factors.append(f"Recent incidents: {recent} in last 12 months")
        if severity_score > 0.6:
            factors.append("Prevalence of high-severity incidents")
        
        risk_level = "low"
        if risk_score >= 0.7:
            risk_level = "critical"
        elif risk_score >= 0.5:
            risk_level = "high"
        elif risk_score >= 0.3:
            risk_level = "medium"
        
        return {
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "factors": factors,
            "total_incidents": total,
            "recent_incidents": recent,
            "analyzed_at": datetime.utcnow().isoformat(),
        }
    
    def classify_root_cause(self, incident: Dict) -> Dict:
        text = f"{incident.get('title', '')} {incident.get('description', '')} {incident.get('immediate_causes', '')}".lower()
        
        cause_scores = {}
        cause_indicators = {
            "inadequate_procedures": ["procedure", "procedure not followed", "no procedure", "standard operating"],
            "training_gap": ["training", "untrained", "inexperienced", "knowledge gap", "not aware"],
            "equipment_failure": ["equipment fail", "mechanical fail", "broken", "malfunction", "wear"],
            "human_error": ["human error", "mistake", "forgot", "negligence", "careless", "improper"],
            "design_deficiency": ["design flaw", "inadequate design", "poor design", "not designed"],
            "maintenance_lapse": ["maintenance", "not maintained", "overdue", "deferred", "lack of maintenance"],
            "communication_failure": ["communication", "not informed", "misunderstanding", "handover"],
            "management_system": ["management", "supervision", "leadership", "safety culture"],
            "environmental": ["weather", "environmental", "natural", "temperature", "humidity"],
            "contractor_related": ["contractor", "subcontract", "vendor", "third party"],
        }
        
        for cause, indicators in cause_indicators.items():
            score = 0
            for indicator in indicators:
                if indicator in text:
                    score += 1
            if score > 0:
                cause_scores[cause] = score / len(indicators)
        
        if cause_scores:
            top_causes = sorted(cause_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            return {
                "primary_cause": top_causes[0][0],
                "contributing_causes": [c[0] for c in top_causes[1:]],
                "confidence": round(top_causes[0][1], 3),
                "all_scores": {k: round(v, 3) for k, v in cause_scores.items()},
            }
        
        return {
            "primary_cause": "unknown",
            "contributing_causes": [],
            "confidence": 0.0,
            "all_scores": {},
        }
    
    def _generate_recommendations(self, patterns: List[Dict], incidents: List[Dict]) -> List[Dict]:
        recommendations = []
        
        for pattern in patterns:
            if pattern["type"] == "category_cluster":
                recommendations.append({
                    "action": f"Conduct root cause analysis for '{pattern['category']}' incidents",
                    "priority": "high" if pattern["count"] >= 3 else "medium",
                    "category": pattern["category"],
                    "rationale": f"{pattern['count']} incidents in same category suggests systemic issue",
                })
            
            elif pattern["type"] == "repeat_location":
                recommendations.append({
                    "action": "Implement enhanced monitoring and engineering controls at repeat-incident asset",
                    "priority": "high",
                    "asset_id": pattern.get("asset_id"),
                    "rationale": f"Asset has {pattern['count']} incidents — chronic hazard",
                })
            
            elif pattern["type"] == "temporal_cluster":
                recommendations.append({
                    "action": "Review seasonal safety measures and adjust staffing",
                    "priority": "medium",
                    "rationale": f"Peak incident period identified in month {pattern['month']}",
                })
        
        critical_count = sum(1 for i in incidents if i.get("severity") == "critical")
        if critical_count > 0:
            recommendations.append({
                "action": "Review all critical incidents for systemic barriers",
                "priority": "critical",
                "rationale": f"{critical_count} critical incidents require management attention",
            })
        
        return recommendations
