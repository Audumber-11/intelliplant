"""
Rules-based Risk Evaluation Engine — applies configurable safety rules
against fused data to generate risk assessments and compliance checks.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RuleCategory(str, Enum):
    SENSOR_THRESHOLD = "sensor_threshold"
    PERMIT_COMPLIANCE = "permit_compliance"
    MAINTENANCE_COMPLIANCE = "maintenance_compliance"
    TEMPORAL_RISK = "temporal_risk"
    SPATIAL_RISK = "spatial_risk"
    COMPOUND_CONDITION = "compound_condition"
    REGULATORY = "regulatory"


class RuleSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Rule:
    rule_id: str
    name: str
    category: RuleCategory
    severity: RuleSeverity
    description: str
    condition: str  # Human-readable condition
    actions: List[str] = field(default_factory=list)
    enabled: bool = True
    applicable_asset_types: List[str] = field(default_factory=list)
    applicable_zones: List[str] = field(default_factory=list)


@dataclass
class RuleResult:
    rule_id: str
    rule_name: str
    triggered: bool
    severity: RuleSeverity
    category: RuleCategory
    evidence: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class RulesEngine:
    """
    Evaluates safety rules against plant data. Rules are configurable and
    cover sensor thresholds, permit compliance, maintenance schedules,
    temporal patterns, and compound conditions.
    """

    def __init__(self):
        self.rules: Dict[str, Rule] = {}
        self._load_default_rules()

    def _load_default_rules(self):
        """Load default safety rules."""
        defaults = [
            # Sensor threshold rules
            Rule(
                rule_id="SR-001",
                name="H2S Critical Level",
                category=RuleCategory.SENSOR_THRESHOLD,
                severity=RuleSeverity.CRITICAL,
                description="H2S concentration exceeds 10 ppm (IDLH threshold)",
                condition="h2s_ppm >= 10",
                actions=[
                    "Immediate area evacuation",
                    "Deploy SCBA rescue team",
                    "Activate emergency response Level 3",
                ],
                applicable_asset_types=["process_unit", "pipeline", "vessel"],
            ),
            Rule(
                rule_id="SR-002",
                name="H2S Warning Level",
                category=RuleCategory.SENSOR_THRESHOLD,
                severity=RuleSeverity.HIGH,
                description="H2S concentration exceeds 5 ppm (TWA limit)",
                condition="h2s_ppm >= 5",
                actions=[
                    "Restrict area access",
                    "Increase ventilation",
                    "Deploy gas monitoring team",
                ],
            ),
            Rule(
                rule_id="SR-003",
                name="LEL Critical Level",
                category=RuleCategory.SENSOR_THRESHOLD,
                severity=RuleSeverity.CRITICAL,
                description="Combustible gas exceeds 20% LEL (explosion risk)",
                condition="ch4_percent_lel >= 20",
                actions=[
                    "Eliminate ignition sources",
                    "Activate emergency ventilation",
                    "Prepare for potential evacuation",
                ],
            ),
            Rule(
                rule_id="SR-004",
                name="LEL Warning Level",
                category=RuleCategory.SENSOR_THRESHOLD,
                severity=RuleSeverity.HIGH,
                description="Combustible gas exceeds 10% LEL",
                condition="ch4_percent_lel >= 10",
                actions=[
                    "Restrict hot work in area",
                    "Increase gas monitoring frequency",
                    "Notify operations supervisor",
                ],
            ),
            Rule(
                rule_id="SR-005",
                name="Oxygen Deficiency",
                category=RuleCategory.SENSOR_THRESHOLD,
                severity=RuleSeverity.CRITICAL,
                description="Oxygen level below 19.5% (confined space risk)",
                condition="o2_percent < 19.5",
                actions=[
                    "Restrict confined space entry",
                    "Activate forced ventilation",
                    "Deploy gas testing team",
                ],
            ),
            Rule(
                rule_id="SR-006",
                name="High Temperature",
                category=RuleCategory.SENSOR_THRESHOLD,
                severity=RuleSeverity.HIGH,
                description="Temperature exceeds design limit",
                condition="temperature > design_temperature * 0.9",
                actions=[
                    "Reduce process throughput",
                    "Verify cooling systems",
                    "Notify operations",
                ],
            ),
            Rule(
                rule_id="SR-007",
                name="High Pressure",
                category=RuleCategory.SENSOR_THRESHOLD,
                severity=RuleSeverity.HIGH,
                description="Pressure exceeds 90% of MAWP",
                condition="pressure > mawp * 0.9",
                actions=[
                    "Reduce throughput",
                    "Verify relief systems",
                    "Prepare for potential shutdown",
                ],
            ),
            # Permit compliance rules
            Rule(
                rule_id="PR-001",
                name="Hot Work Without Gas Test",
                category=RuleCategory.PERMIT_COMPLIANCE,
                severity=RuleSeverity.CRITICAL,
                description="Hot work permit active without valid gas test",
                condition="permit_type == hot_work AND gas_test_invalid",
                actions=[
                    "Suspend hot work immediately",
                    "Conduct gas test",
                    "Verify atmosphere is safe",
                ],
            ),
            Rule(
                rule_id="PR-002",
                name="Expired Permit",
                category=RuleCategory.PERMIT_COMPLIANCE,
                severity=RuleSeverity.HIGH,
                description="Work permit has expired but work continues",
                condition="permit_status == active AND now > requested_end",
                actions=[
                    "Stop work immediately",
                    "Re-evaluate safety conditions",
                    "Issue new permit if required",
                ],
            ),
            Rule(
                rule_id="PR-003",
                name="Conflicting Permits",
                category=RuleCategory.PERMIT_COMPLIANCE,
                severity=RuleSeverity.HIGH,
                description="Multiple conflicting permits active in same zone",
                condition="active_permits_in_zone > 1 AND conflicting_types",
                actions=[
                    "Review permit compatibility",
                    "Coordinate with permit holders",
                    "Consider suspending lower-priority permits",
                ],
            ),
            Rule(
                rule_id="PR-004",
                name="LOTO Not Applied",
                category=RuleCategory.PERMIT_COMPLIANCE,
                severity=RuleSeverity.CRITICAL,
                description="Energy isolation required but LOTO not confirmed",
                condition="loto_required AND NOT loto_applied",
                actions=[
                    "Stop work immediately",
                    "Apply energy isolation",
                    "Verify zero energy state",
                ],
            ),
            # Maintenance compliance rules
            Rule(
                rule_id="MR-001",
                name="Overdue Inspection",
                category=RuleCategory.MAINTENANCE_COMPLIANCE,
                severity=RuleSeverity.MEDIUM,
                description="Asset inspection is overdue",
                condition="next_inspection_due < now AND inspection_status != completed",
                actions=[
                    "Schedule inspection urgently",
                    "Review asset condition",
                    "Consider reducing operating parameters",
                ],
            ),
            Rule(
                rule_id="MR-002",
                name="Calibration Overdue",
                category=RuleCategory.MAINTENANCE_COMPLIANCE,
                severity=RuleSeverity.HIGH,
                description="Safety sensor calibration is overdue",
                condition="sensor.is_safety_critical AND next_calibration_due < now",
                actions=[
                    "Remove sensor from service",
                    "Deploy portable monitoring",
                    "Schedule calibration",
                ],
            ),
            Rule(
                rule_id="MR-003",
                name="Excessive Vibration",
                category=RuleCategory.MAINTENANCE_COMPLIANCE,
                severity=RuleSeverity.HIGH,
                description="Rotating equipment vibration exceeds threshold",
                condition="vibration > alarm_high AND asset_type in [pump, compressor]",
                actions=[
                    "Reduce speed/load",
                    "Schedule bearing inspection",
                    "Prepare backup equipment",
                ],
            ),
            # Temporal risk rules
            Rule(
                rule_id="TR-001",
                name="Night Shift Risk Escalation",
                category=RuleCategory.TEMPORAL_RISK,
                severity=RuleSeverity.MEDIUM,
                description="Higher risk during night shift (reduced staffing)",
                condition="hour NOT IN [7,8,9,10,11,12,13,14,15,16,17,18]",
                actions=[
                    "Increase supervisor presence",
                    "Enhance monitoring coverage",
                    "Verify communication channels",
                ],
            ),
            Rule(
                rule_id="TR-002",
                name="Weekend Risk Escalation",
                category=RuleCategory.TEMPORAL_RISK,
                severity=RuleSeverity.MEDIUM,
                description="Elevated risk during weekend/holiday operations",
                condition="day_of_week IN [Saturday, Sunday] OR is_holiday",
                actions=[
                    "Verify emergency response readiness",
                    "Confirm on-call personnel availability",
                    "Review weekend work permits",
                ],
            ),
            # Compound condition rules
            Rule(
                rule_id="CC-001",
                name="Simultaneous Hot Work and Gas Release",
                category=RuleCategory.COMPOUND_CONDITION,
                severity=RuleSeverity.CRITICAL,
                description="Hot work active while gas detector shows elevated readings",
                condition="hot_work_permit_active AND gas_detector_alarm",
                actions=[
                    "Stop hot work immediately",
                    "Evacuate hot work area",
                    "Investigate gas source",
                    "Re-assess safety conditions",
                ],
            ),
            Rule(
                rule_id="CC-002",
                name="Maintenance During Process Upset",
                category=RuleCategory.COMPOUND_CONDITION,
                severity=RuleSeverity.HIGH,
                description="Maintenance activity during process upset condition",
                condition="maintenance_active AND process_upset_detected",
                actions=[
                    "Review maintenance safety assumptions",
                    "Consider postponing maintenance",
                    "Enhance safety monitoring",
                ],
            ),
            # Regulatory rules (OISD, Factory Act, DGMS)
            Rule(
                rule_id="RG-001",
                name="OISD-116 Compliance Check",
                category=RuleCategory.REGULATORY,
                severity=RuleSeverity.HIGH,
                description="OISD-116 periodic safety audit compliance",
                condition="days_since_last_oisd_audit > 365",
                actions=[
                    "Schedule OISD-116 audit",
                    "Review previous findings",
                    "Prepare compliance documentation",
                ],
            ),
            Rule(
                rule_id="RG-002",
                name="Factory Act Safety Training",
                category=RuleCategory.REGULATORY,
                severity=RuleSeverity.MEDIUM,
                description="Annual safety training compliance per Factory Act",
                condition="training_due_date < now",
                actions=[
                    "Schedule safety training",
                    "Verify personnel training records",
                    "Update training matrix",
                ],
            ),
        ]

        for rule in defaults:
            self.rules[rule.rule_id] = rule

    def evaluate(
        self,
        context: Dict[str, Any],
        asset_types: Optional[List[str]] = None,
        categories: Optional[List[RuleCategory]] = None,
    ) -> List[RuleResult]:
        """
        Evaluate all applicable rules against the given context.
        Context should contain sensor values, permit status, etc.
        """
        results = []

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            if categories and rule.category not in categories:
                continue

            if (
                asset_types
                and rule.applicable_asset_types
                and not any(at in rule.applicable_asset_types for at in asset_types)
            ):
                continue

            triggered = self._evaluate_condition(rule, context)
            evidence = self._collect_evidence(rule, context, triggered)

            results.append(
                RuleResult(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    triggered=triggered,
                    severity=rule.severity,
                    category=rule.category,
                    evidence=evidence,
                )
            )

        return results

    def _evaluate_condition(self, rule: Rule, context: Dict[str, Any]) -> bool:
        """Evaluate a rule condition against context. Simplified evaluation."""
        condition = rule.condition.lower()

        try:
            # Sensor threshold checks
            if "h2s_ppm >=" in condition:
                threshold = float(condition.split(">=")[1].strip())
                return context.get("h2s_ppm", 0) >= threshold

            if "ch4_percent_lel >=" in condition:
                threshold = float(condition.split(">=")[1].strip())
                return context.get("ch4_percent_lel", 0) >= threshold

            if "o2_percent <" in condition:
                threshold = float(condition.split("<")[1].strip())
                return context.get("o2_percent", 21) < threshold

            if "vibration >" in condition:
                return context.get("vibration_alarm", False)

            if "temperature >" in condition:
                return context.get("temperature_alarm", False)

            if "pressure >" in condition:
                return context.get("pressure_alarm", False)

            # Permit checks
            if "hot_work" in condition and "gas_test_invalid" in condition:
                return (
                    context.get("permit_type") == "hot_work"
                    and context.get("gas_test_valid", True) is False
                )

            if "permit_status == active" in condition and "now > requested_end" in condition:
                return (
                    context.get("permit_status") == "active"
                    and context.get("permit_expired", False)
                )

            if "loto_required" in condition and "not loto_applied" in condition:
                return (
                    context.get("loto_required", False)
                    and not context.get("loto_applied", False)
                )

            # Compound conditions
            if "hot_work_permit_active" in condition and "gas_detector_alarm" in condition:
                return (
                    context.get("hot_work_permit_active", False)
                    and context.get("gas_detector_alarm", False)
                )

            # Temporal checks
            if "hour not in" in condition:
                safe_hours = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
                current_hour = context.get("current_hour", datetime.utcnow().hour)
                return current_hour not in safe_hours

            if "day_of_week in" in condition:
                current_day = context.get("current_day", datetime.utcnow().strftime("%A"))
                return current_day in ["Saturday", "Sunday"]

            # Maintenance checks
            if "next_inspection_due < now" in condition:
                due = context.get("next_inspection_due")
                if due and isinstance(due, datetime):
                    return due < datetime.utcnow()
                return False

            # Default: not triggered
            return False

        except Exception as e:
            logger.warning(f"Error evaluating rule {rule.rule_id}: {e}")
            return False

    def _collect_evidence(
        self, rule: Rule, context: Dict[str, Any], triggered: bool
    ) -> Dict[str, Any]:
        """Collect evidence for a rule evaluation."""
        evidence = {
            "rule_id": rule.rule_id,
            "triggered": triggered,
            "context_keys": list(context.keys()),
        }

        # Add relevant context values
        if "h2s_ppm" in context:
            evidence["h2s_ppm"] = context["h2s_ppm"]
        if "ch4_percent_lel" in context:
            evidence["ch4_percent_lel"] = context["ch4_percent_lel"]
        if "o2_percent" in context:
            evidence["o2_percent"] = context["o2_percent"]
        if "permit_status" in context:
            evidence["permit_status"] = context["permit_status"]

        return evidence

    def get_applicable_rules(
        self, asset_type: Optional[str] = None, category: Optional[RuleCategory] = None
    ) -> List[Rule]:
        """Get rules applicable to a given asset type and/or category."""
        results = []
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            if category and rule.category != category:
                continue
            if (
                asset_type
                and rule.applicable_asset_types
                and asset_type not in rule.applicable_asset_types
            ):
                continue
            results.append(rule)
        return results
