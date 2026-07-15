"""Quality & Compliance Audit Agent — checklist evaluation, finding analysis, compliance scoring."""
from datetime import datetime
from typing import List, Dict, Optional
from uuid import UUID


class ComplianceAuditEngine:
    """Evaluates audit checklists, scores compliance, and generates findings."""
    
    OISD_116_CHECKLIST = [
        {"id": "OISD-01", "category": "Process Safety", "item": "Process Hazard Analysis (PHA) completed and current", "weight": 3},
        {"id": "OISD-02", "category": "Process Safety", "item": "Management of Change (MOC) procedure implemented", "weight": 3},
        {"id": "OISD-03", "category": "Process Safety", "item": "Operating procedures available and followed", "weight": 2},
        {"id": "OISD-04", "category": "Process Safety", "item": "Safety Critical Equipment inventory maintained", "weight": 3},
        {"id": "OISD-05", "category": "Process Safety", "item": "Process safety information up to date", "weight": 2},
        {"id": "OISD-06", "category": "Mechanical Integrity", "item": "Pressure equipment inspection program active", "weight": 3},
        {"id": "OISD-07", "category": "Mechanical Integrity", "item": "Corrosion monitoring program implemented", "weight": 2},
        {"id": "OISD-08", "category": "Mechanical Integrity", "item": "Safety instrumented systems tested regularly", "weight": 3},
        {"id": "OISD-09", "category": "Emergency Planning", "item": "Emergency response plan current and tested", "weight": 3},
        {"id": "OISD-10", "category": "Emergency Planning", "item": "Fire and gas detection systems functional", "weight": 3},
        {"id": "OISD-11", "category": "Human Factors", "item": "Operator training program documented", "weight": 2},
        {"id": "OISD-12", "category": "Human Factors", "item": "Fatigue risk management in place", "weight": 2},
        {"id": "OISD-13", "category": "Contractor Safety", "item": "Contractor safety pre-qualification completed", "weight": 2},
        {"id": "OISD-14", "category": "Contractor Safety", "item": "Contractor work permits issued correctly", "weight": 2},
        {"id": "OISD-15", "category": "Incident Investigation", "item": "Incident investigation procedure followed", "weight": 3},
        {"id": "OISD-16", "category": "Incident Investigation", "item": "Corrective actions tracked to closure", "weight": 2},
    ]
    
    FACTORY_ACT_CHECKLIST = [
        {"id": "FA-01", "category": "General Safety", "item": "Adequate lighting in all work areas", "weight": 1},
        {"id": "FA-02", "category": "General Safety", "item": "Ventilation systems operational", "weight": 2},
        {"id": "FA-03", "category": "General Safety", "item": "Clean and orderly workplace", "weight": 1},
        {"id": "FA-04", "category": "Safety Equipment", "item": "PPE provided and used", "weight": 3},
        {"id": "FA-05", "category": "Safety Equipment", "item": "Safety signage and warnings displayed", "weight": 2},
        {"id": "FA-06", "category": "Safety Equipment", "item": "Fire extinguishers available and charged", "weight": 3},
        {"id": "FA-07", "category": "Building Safety", "item": "Adequate exits and escape routes", "weight": 3},
        {"id": "FA-08", "category": "Building Safety", "item": "Emergency exits unblocked", "weight": 3},
        {"id": "FA-09", "category": "Electrical Safety", "item": "Electrical installations up to code", "weight": 2},
        {"id": "FA-10", "category": "Machinery Safety", "item": "Machine guards in place and functional", "weight": 3},
        {"id": "FA-11", "category": "Machinery Safety", "item": "LOTO procedures followed", "weight": 3},
        {"id": "FA-12", "category": "Welfare", "item": "Adequate drinking water available", "weight": 1},
        {"id": "FA-13", "category": "Welfare", "item": "First aid facilities provided", "weight": 2},
        {"id": "FA-14", "category": "Welfare", "item": "Rest rooms and washrooms adequate", "weight": 1},
    ]
    
    def get_checklist(self, standard: str) -> List[Dict]:
        if standard.lower() == "oisd_116":
            return self.OISD_116_CHECKLIST
        elif standard.lower() == "factory_act":
            return self.FACTORY_ACT_CHECKLIST
        return self.OISD_116_CHECKLIST
    
    def evaluate_checklist(self, standard: str, responses: List[Dict]) -> Dict:
        checklist = self.get_checklist(standard)
        
        checklist_map = {item["id"]: item for item in checklist}
        
        total_weight = sum(item["weight"] for item in checklist)
        achieved_weight = 0
        findings = []
        
        for response in responses:
            item_id = response.get("item_id")
            status = response.get("status", "pending")
            evidence = response.get("evidence", "")
            notes = response.get("notes", "")
            
            item = checklist_map.get(item_id)
            if not item:
                continue
            
            if status == "compliant":
                achieved_weight += item["weight"]
            elif status == "non_compliant":
                findings.append({
                    "finding_number": f"NC-{item_id}",
                    "severity": "major" if item["weight"] >= 3 else "minor",
                    "category": item["category"],
                    "clause_reference": item_id,
                    "title": item["item"],
                    "description": f"Non-compliance with: {item['item']}",
                    "evidence": evidence,
                    "requirement": item["item"],
                    "status": "open",
                })
            elif status == "observation":
                findings.append({
                    "finding_number": f"OB-{item_id}",
                    "severity": "observation",
                    "category": item["category"],
                    "clause_reference": item_id,
                    "title": item["item"],
                    "description": notes or f"Observation for: {item['item']}",
                    "evidence": evidence,
                    "requirement": item["item"],
                    "status": "open",
                })
        
        compliance_score = (achieved_weight / total_weight * 100) if total_weight > 0 else 0
        
        major_findings = sum(1 for f in findings if f["severity"] == "major")
        minor_findings = sum(1 for f in findings if f["severity"] == "minor")
        observations = sum(1 for f in findings if f["severity"] == "observation")
        
        if compliance_score >= 90 and major_findings == 0:
            overall_result = "conformance"
        elif major_findings > 0:
            overall_result = "major_nc"
        else:
            overall_result = "minor_nc"
        
        return {
            "standard": standard,
            "total_items": len(checklist),
            "evaluated_items": len(responses),
            "compliance_score": round(compliance_score, 1),
            "overall_result": overall_result,
            "findings_summary": {
                "major": major_findings,
                "minor": minor_findings,
                "observations": observations,
                "total": len(findings),
            },
            "findings": findings,
            "evaluated_at": datetime.utcnow().isoformat(),
        }
    
    def analyze_findings(self, findings: List[Dict]) -> Dict:
        if not findings:
            return {"categories": [], "trends": [], "recommendations": []}
        
        category_counts = {}
        for f in findings:
            cat = f.get("category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for cat, count in categories[:3]:
            recommendations.append({
                "category": cat,
                "finding_count": count,
                "recommendation": f"Focus improvement efforts on '{cat}' — {count} finding(s) identified",
                "priority": "high" if count >= 3 else "medium",
            })
        
        return {
            "categories": [{"name": cat, "count": count} for cat, count in categories],
            "total_findings": len(findings),
            "recommendations": recommendations,
            "analyzed_at": datetime.utcnow().isoformat(),
        }
    
    def generate_audit_report(self, audit: Dict, findings: List[Dict], checklist_results: List[Dict]) -> Dict:
        compliance_score = 0
        if checklist_results:
            scores = [r.get("compliance_score", 0) for r in checklist_results]
            compliance_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "audit_id": str(audit.get("id")),
            "audit_number": audit.get("audit_number"),
            "title": audit.get("title"),
            "standard": audit.get("standard"),
            "compliance_score": round(compliance_score, 1),
            "overall_result": audit.get("overall_result", "pending"),
            "summary": {
                "major_findings": audit.get("major_findings", 0),
                "minor_findings": audit.get("minor_findings", 0),
                "observations": audit.get("observations", 0),
                "good_practices": audit.get("good_practices", 0),
            },
            "top_risk_areas": self.analyze_findings(findings).get("categories", [])[:5],
            "generated_at": datetime.utcnow().isoformat(),
        }
