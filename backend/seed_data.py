"""
Seed database with realistic demo data for hackathon presentation.
Creates plants, assets, sensors, permits, incidents, and risk events.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from uuid import uuid4
import random

from database import init_db, init_chroma, AsyncSessionLocal
from models import (
    PlantAsset, Sensor, SensorReading, User, Permit, Incident,
    RiskEvent, RiskZone, Audit, EmergencyIncident, AssetType, SensorType,
    PermitType, PermitStatus, IncidentSeverity, IncidentStatus, RiskLevel,
    UserRole, AuditStandard, FindingSeverity
)


async def seed():
    await init_db()
    await init_chroma()

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        from sqlalchemy import select, func
        result = await db.execute(select(func.count(PlantAsset.id)))
        if result.scalar() > 0:
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # === USERS ===
        users = []
        user_data = [
            ("admin@intelliplant.com", "admin", "System Admin", UserRole.ADMIN, "EMP-001"),
            ("rajesh.kumar@intelliplant.com", "rajesh.kumar", "Rajesh Kumar", UserRole.PLANT_MANAGER, "EMP-002"),
            ("priya.sharma@intelliplant.com", "priya.sharma", "Priya Sharma", UserRole.SAFETY_OFFICER, "EMP-003"),
            ("amit.patel@intelliplant.com", "amit.patel", "Amit Patel", UserRole.SUPERVISOR, "EMP-004"),
            ("sunita.reddy@intelliplant.com", "sunita.reddy", "Sunita Reddy", UserRole.OPERATOR, "EMP-005"),
            ("vikram.singh@intelliplant.com", "vikram.singh", "Vikram Singh", UserRole.EMERGENCY_COORDINATOR, "EMP-006"),
            ("meena.iyer@intelliplant.com", "meena.iyer", "Meena Iyer", UserRole.AUDITOR, "EMP-007"),
        ]
        for email, username, full_name, role, emp_id in user_data:
            user = User(
                email=email, username=username, full_name=full_name,
                hashed_password="demo_hash", role=role, employee_id=emp_id,
                department="Operations", is_active=True,
            )
            db.add(user)
            users.append(user)
        await db.flush()

        # === PLANT ASSETS ===
        assets = []
        asset_data = [
            ("V-101", "Primary Reactor Vessel", AssetType.VESSEL, "Reactor Area", 28.6139, 77.2090, True, True),
            ("V-102", "Flash Separator", AssetType.VESSEL, "Separation Unit", 28.6140, 77.2091, True, False),
            ("T-201", "Crude Oil Storage Tank", AssetType.STORAGE_TANK, "Tank Farm", 28.6145, 77.2085, True, True),
            ("T-202", "Diesel Storage Tank", AssetType.STORAGE_TANK, "Tank Farm", 28.6146, 77.2086, True, False),
            ("P-301", "Main Feed Pump", AssetType.PUMP, "Pump House", 28.6141, 77.2092, True, False),
            ("P-302", "Cooling Water Pump", AssetType.PUMP, "Cooling Tower", 28.6142, 77.2093, True, False),
            ("C-401", "Main Compressor", AssetType.COMPRESSOR, "Compressor Hall", 28.6143, 77.2094, True, True),
            ("HX-501", "Feed-Effluent Exchanger", AssetType.HEAT_EXCHANGER, "Reactor Area", 28.6138, 77.2089, True, False),
            ("PL-601", "Reactor Feed Pipeline", AssetType.PIPELINE, "Reactor Area", 28.6137, 77.2088, True, False),
            ("V-103", "High Pressure Separator", AssetType.VESSEL, "Separation Unit", 28.6144, 77.2095, True, True),
            ("FDH-01", "Fire Hydrant Station 1", AssetType.FIRE_HYDRANT, "Tank Farm", 28.6147, 77.2084, True, False),
            ("SS-01", "Safety Shower Unit 1", AssetType.SAFETY_SHOWER, "Reactor Area", 28.6136, 77.2087, True, False),
            ("GD-01", "Gas Detector Unit - Reactor", AssetType.GAS_DETECTOR, "Reactor Area", 28.6135, 77.2086, True, True),
            ("GD-02", "Gas Detector Unit - Tank Farm", AssetType.GAS_DETECTOR, "Tank Farm", 28.6148, 77.2083, True, True),
            ("CR-01", "Central Control Room", AssetType.CONTROL_ROOM, "Admin Block", 28.6150, 77.2090, True, False),
            ("MP-01", "Primary Muster Point", AssetType.MUSTER_POINT, "Main Gate", 28.6155, 77.2100, True, False),
            ("MP-02", "Secondary Muster Point", AssetType.MUSTER_POINT, "Parking Area", 28.6160, 77.2105, True, False),
        ]
        for tag, name, atype, area, lat, lon, active, critical in asset_data:
            asset = PlantAsset(
                tag=tag, name=name, asset_type=atype, unit_area=area,
                latitude=lat, longitude=lon, is_active=active, is_critical=critical,
                hazardous_material=critical,
                design_pressure=random.uniform(10, 100),
                design_temperature=random.uniform(50, 400),
                last_inspection=datetime.utcnow() - timedelta(days=random.randint(10, 300)),
                next_inspection_due=datetime.utcnow() + timedelta(days=random.randint(-30, 180)),
            )
            db.add(asset)
            assets.append(asset)
        await db.flush()

        # === SENSORS ===
        sensors = []
        sensor_configs = [
            # H2S sensors
            ("GD-01-H2S", "H2S Detector - Reactor", SensorType.GAS_H2S, 0, 50, "ppm", 0.5, 10, 0.3, 15, True),
            ("GD-02-H2S", "H2S Detector - Tank Farm", SensorType.GAS_H2S, 1, 50, "ppm", 0.5, 10, 0.3, 15, True),
            # CH4 sensors
            ("GD-01-CH4", "Methane Detector - Reactor", SensorType.GAS_CH4, 0, 100, "%LEL", 10, 20, 5, 40, True),
            ("GD-02-CH4", "Methane Detector - Tank Farm", SensorType.GAS_CH4, 1, 100, "%LEL", 10, 20, 5, 40, True),
            # O2 sensors
            ("GD-01-O2", "Oxygen Detector - Reactor", SensorType.GAS_O2, 0, 25, "%", 19.5, 23.5, 18, 25, True),
            # Temperature sensors
            ("V-101-TMP", "Reactor Temperature", SensorType.TEMPERATURE, 0, 500, "°C", None, 350, None, 400, True),
            ("V-102-TMP", "Separator Temperature", SensorType.TEMPERATURE, 1, 300, "°C", None, 250, None, 280, False),
            ("T-201-TMP", "Tank Temperature", SensorType.TEMPERATURE, 2, 100, "°C", None, 60, None, 80, False),
            # Pressure sensors
            ("V-101-PRM", "Reactor Pressure", SensorType.PRESSURE, 0, 200, "bar", None, 150, None, 180, True),
            ("C-401-PRM", "Compressor Discharge Pressure", SensorType.PRESSURE, 6, 100, "bar", None, 85, None, 95, True),
            # Vibration sensors
            ("C-401-VIB", "Compressor Vibration", SensorType.VIBRATION, 6, 50, "mm/s", None, 10, None, 15, True),
            ("P-301-VIB", "Feed Pump Vibration", SensorType.VIBRATION, 4, 50, "mm/s", None, 8, None, 12, False),
            # Flow sensors
            ("PL-601-FLW", "Reactor Feed Flow", SensorType.FLOW, 8, 1000, "m3/h", 100, 800, 50, 900, False),
            # Smoke/Flame
            ("GD-01-SMK", "Smoke Detector - Reactor", SensorType.SMOKE, 0, 100, "%obs/m", None, 50, None, 80, True),
            ("GD-01-FLM", "Flame Detector - Reactor", SensorType.FLAME, 0, 100, "%", None, 50, None, 80, True),
            # Weather
            ("WX-001-WND", "Wind Speed", SensorType.WEATHER_WIND, 12, 200, "km/h", None, 40, None, 60, False),
            ("WX-001-TMP", "Ambient Temperature", SensorType.WEATHER_TEMP, 12, 60, "°C", None, 45, -5, 50, False),
            ("WX-001-HUM", "Ambient Humidity", SensorType.WEATHER_HUMIDITY, 12, 100, "%", None, 85, 15, 95, False),
        ]
        for tag, name, stype, asset_idx, rng_max, units, alarm_lo, alarm_hi, crit_lo, crit_hi, safety_crit in sensor_configs:
            sensor = Sensor(
                tag=tag, name=name, sensor_type=stype,
                asset_id=assets[asset_idx].id,
                range_min=0, range_max=rng_max, units=units,
                alarm_low=alarm_lo, alarm_high=alarm_hi,
                alarm_critical_low=crit_lo, alarm_critical_high=crit_hi,
                is_active=True, is_safety_critical=safety_crit,
                communication_protocol="WirelessHART",
                last_calibration=datetime.utcnow() - timedelta(days=random.randint(5, 90)),
                next_calibration_due=datetime.utcnow() + timedelta(days=random.randint(-20, 180)),
            )
            db.add(sensor)
            sensors.append(sensor)
        await db.flush()

        # === SENSOR READINGS (last 24 hours) ===
        now = datetime.utcnow()
        reading_count = 0
        for sensor in sensors:
            # Generate readings with some variation
            base_value = random.uniform(
                sensor.range_min or 0,
                (sensor.range_max or 100) * 0.6
            )
            for i in range(48):  # Every 30 min for 24 hours
                ts = now - timedelta(minutes=i * 30)
                # Occasionally trigger alarms
                if random.random() < 0.05:
                    value = sensor.alarm_high or (sensor.range_max or 100) * 0.9
                elif random.random() < 0.02:
                    value = sensor.alarm_critical_high or (sensor.range_max or 100) * 0.95
                else:
                    value = base_value + random.uniform(-base_value * 0.1, base_value * 0.1)

                is_alarm = (sensor.alarm_high and value >= sensor.alarm_high) or \
                           (sensor.alarm_low and value <= sensor.alarm_low)
                is_critical = (sensor.alarm_critical_high and value >= sensor.alarm_critical_high) or \
                              (sensor.alarm_critical_low and value <= sensor.alarm_critical_low)

                reading = SensorReading(
                    sensor_id=sensor.id,
                    value=round(value, 2),
                    quality="GOOD" if random.random() > 0.01 else "UNCERTAIN",
                    timestamp=ts,
                    is_alarm=is_alarm,
                    is_critical=is_critical,
                )
                db.add(reading)
                reading_count += 1
        await db.flush()

        # === PERMITS ===
        permits = []
        permit_data = [
            ("hot_work", "Welding on V-101 Nozzle", 0, "approved", True),
            ("confined_space", "Inspection inside T-201", 2, "active", True),
            ("working_at_height", "Scaffold Erection on C-401", 6, "approved", False),
            ("line_break", "Flange Breaking on PL-601", 8, "under_review", False),
            ("excavation", "Foundation Repair Near T-202", 3, "draft", False),
            ("hot_work", "Pipeline Repair on PL-601", 8, "active", True),
            ("electrical", "MCC Panel Maintenance", 14, "approved", False),
        ]
        for ptype, title, asset_idx, status, gas_req in permit_data:
            start = now - timedelta(hours=random.randint(0, 12))
            end = now + timedelta(hours=random.randint(4, 48))
            permit = Permit(
                permit_number=f"PMT-{now.strftime('%Y%m%d')}-{random.randint(1000,9999)}",
                permit_type=PermitType(ptype),
                title=title,
                description=f"Planned {ptype.replace('_', ' ')} work on {assets[asset_idx].name}",
                asset_id=assets[asset_idx].id,
                location_description=f"{assets[asset_idx].unit_area} - {assets[asset_idx].name}",
                latitude=assets[asset_idx].latitude,
                longitude=assets[asset_idx].longitude,
                requested_start=start,
                requested_end=end,
                status=PermitStatus(status),
                created_by_id=users[random.randint(2, 5)].id,
                approved_by_id=users[2].id if status in ("approved", "active") else None,
                approved_at=now - timedelta(hours=1) if status in ("approved", "active") else None,
                gas_test_required=gas_req,
                gas_test_valid_until=now + timedelta(hours=8) if gas_req else None,
                loto_required=ptype in ("line_break", "electrical"),
                ppe_requirements=["Hard Hat", "Safety Glasses", "Hi-Vis Vest", "Safety Boots"],
            )
            db.add(permit)
            permits.append(permit)
        await db.flush()

        # === INCIDENTS ===
        incidents = []
        incident_data = [
            ("near_miss", "Near miss - Gas detector alarm at Reactor", 0, "closed", now - timedelta(days=15)),
            ("minor", "Minor slip near Tank Farm access road", 2, "closed", now - timedelta(days=10)),
            ("moderate", "H2S alarm activation at Reactor area", 0, "closed", now - timedelta(days=7)),
            ("near_miss", "Scaffold tag missing on C-401", 6, "closed", now - timedelta(days=5)),
            ("major", "Small leak detected on PL-601 flange", 8, "under_investigation", now - timedelta(days=3)),
            ("minor", "PPE non-compliance observation", 4, "closed", now - timedelta(days=2)),
            ("near_miss", "Hot work sparks near combustible area", 0, "reported", now - timedelta(hours=6)),
        ]
        for severity, title, asset_idx, status, occurred in incident_data:
            incident = Incident(
                incident_number=f"INC-{occurred.strftime('%Y%m%d')}-{random.randint(1000,9999)}",
                severity=IncidentSeverity(severity),
                status=IncidentStatus(status),
                title=title,
                description=f"Detailed description of: {title}",
                asset_id=assets[asset_idx].id,
                location_description=f"{assets[asset_idx].unit_area}",
                latitude=assets[asset_idx].latitude,
                longitude=assets[asset_idx].longitude,
                occurred_at=occurred,
                reported_at=occurred + timedelta(minutes=random.randint(5, 60)),
                assignee_id=users[random.randint(2, 5)].id,
                is_reportable=(severity in ("major", "critical")),
            )
            db.add(incident)
            incidents.append(incident)
        await db.flush()

        # === RISK EVENTS ===
        risk_events = [
            ("correlated_risk", RiskLevel.HIGH, "H2S and Combustible Gas Co-detection",
             "Multiple gas detectors showing elevated readings in Reactor area", 0),
            ("anomaly", RiskLevel.MEDIUM, "Vibration Trend - Compressor C-401",
             "Vibration levels trending upward over last 7 days", 6),
            ("threshold", RiskLevel.HIGH, "High Pressure Warning - V-101",
             "Reactor pressure at 92% of MAWP", 0),
            ("prediction", RiskLevel.LOW, "Calibration Due - Gas Detector GD-02",
             "Tank farm gas detector calibration overdue by 15 days", 1),
            ("correlated_risk", RiskLevel.CRITICAL, "Fire Risk - Hot Work + Gas Alarm",
             "Hot work permit active while gas detector shows elevated CH4", 0),
        ]
        for etype, level, title, desc, asset_idx in risk_events:
            event = RiskEvent(
                event_type=etype,
                risk_level=level,
                source="risk_engine",
                title=title,
                description=desc,
                asset_id=assets[asset_idx].id,
                latitude=assets[asset_idx].latitude,
                longitude=assets[asset_idx].longitude,
                detected_at=now - timedelta(hours=random.randint(1, 12)),
                status="active",
                recommended_actions=[
                    {"action": "Investigate source", "status": "pending"},
                    {"action": "Deploy monitoring team", "status": "pending"},
                ],
            )
            db.add(event)
        await db.flush()

        # === RISK ZONES ===
        zones = [
            ("Reactor High Risk Zone", "high_risk", 28.6139, 77.2090, RiskLevel.HIGH),
            ("Tank Farm Zone", "gas_zone", 28.6146, 77.2085, RiskLevel.MEDIUM),
            ("Pump House Zone", "fire_zone", 28.6141, 77.2092, RiskLevel.LOW),
            ("Main Gate Evacuation", "evacuation_route", 28.6155, 77.2100, RiskLevel.LOW),
        ]
        for name, ztype, lat, lon, base_risk in zones:
            zone = RiskZone(
                name=name, zone_type=ztype,
                geometry={"type": "Polygon", "coordinates": [[[lon-0.001, lat-0.001], [lon+0.001, lat-0.001], [lon+0.001, lat+0.001], [lon-0.001, lat+0.001], [lon-0.001, lat-0.001]]]},
                center_latitude=lat, center_longitude=lon,
                base_risk_level=base_risk, current_risk_level=base_risk,
                is_active=True,
            )
            db.add(zone)

        # === AUDITS ===
        audit = Audit(
            audit_number=f"AUD-{now.strftime('%Y%m%d')}-0001",
            title="Annual Safety Compliance Audit",
            standard=AuditStandard.OISD_116,
            scope="Process safety management compliance for Reactor Unit",
            auditor_id=users[6].id,
            planned_start=now - timedelta(days=5),
            planned_end=now + timedelta(days=5),
            status="in_progress",
            major_findings=1,
            minor_findings=3,
            observations=5,
        )
        db.add(audit)

        await db.commit()
        print(f"Seeded:")
        print(f"  - {len(users)} users")
        print(f"  - {len(assets)} assets")
        print(f"  - {len(sensors)} sensors")
        print(f"  - {reading_count} sensor readings")
        print(f"  - {len(permits)} permits")
        print(f"  - {len(incidents)} incidents")
        print(f"  - 5 risk events")
        print(f"  - 4 risk zones")
        print(f"  - 1 audit")


if __name__ == "__main__":
    asyncio.run(seed())
