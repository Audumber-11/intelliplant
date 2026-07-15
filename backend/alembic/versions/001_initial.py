"""Initial migration - Industrial Safety Intelligence Platform

Revision ID: 001
Revises: 
Create Date: 2026-07-09 14:58:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    
    # Create enums
    op.execute("CREATE TYPE permittype AS ENUM ('hot_work', 'confined_space', 'working_at_height', 'excavation', 'electrical', 'line_break', 'radiation', 'chemical', 'general')")
    op.execute("CREATE TYPE permitstatus AS ENUM ('draft', 'under_review', 'approved', 'active', 'suspended', 'closed', 'rejected', 'expired')")
    op.execute("CREATE TYPE incidentseverity AS ENUM ('near_miss', 'minor', 'moderate', 'major', 'critical', 'fatality')")
    op.execute("CREATE TYPE incidentstatus AS ENUM ('reported', 'under_investigation', 'root_cause_analysis', 'corrective_actions', 'closed')")
    op.execute("CREATE TYPE risklevel AS ENUM ('low', 'medium', 'high', 'critical')")
    op.execute("CREATE TYPE assettype AS ENUM ('process_unit', 'storage_tank', 'pipeline', 'valve', 'pump', 'compressor', 'heat_exchanger', 'vessel', 'control_room', 'muster_point', 'fire_hydrant', 'safety_shower', 'gas_detector', 'other')")
    op.execute("CREATE TYPE sensortype AS ENUM ('gas_h2s', 'gas_ch4', 'gas_co', 'gas_o2', 'gas_combustible', 'temperature', 'pressure', 'flow', 'level', 'vibration', 'radiation', 'smoke', 'flame', 'weather_wind', 'weather_temp', 'weather_humidity')")
    op.execute("CREATE TYPE auditstandard AS ENUM ('iso_45001', 'osha_psm', 'api_580', 'api_581', 'seveso', 'oisd_116', 'oisd_117', 'factory_act', 'dgms')")
    op.execute("CREATE TYPE findingseverity AS ENUM ('major', 'minor', 'observation', 'good_practice')")
    op.execute("CREATE TYPE userrole AS ENUM ('operator', 'supervisor', 'safety_officer', 'plant_manager', 'emergency_coordinator', 'auditor', 'admin')")
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('full_name', sa.String(200), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('operator', 'supervisor', 'safety_officer', 'plant_manager', 'emergency_coordinator', 'auditor', 'admin', name='userrole'), nullable=False, default='operator'),
        sa.Column('employee_id', sa.String(50), unique=True),
        sa.Column('department', sa.String(100)),
        sa.Column('phone', sa.String(20)),
        sa.Column('badge_id', sa.String(50), unique=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_superuser', sa.Boolean, default=False),
        sa.Column('approved_permit_types', postgresql.ARRAY(sa.Enum('hot_work', 'confined_space', 'working_at_height', 'excavation', 'electrical', 'line_break', 'radiation', 'chemical', 'general', name='permittype')), default=[]),
        sa.Column('mfa_enabled', sa.Boolean, default=False),
        sa.Column('mfa_secret', sa.String(255)),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_login', sa.DateTime),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_badge_id', 'users', ['badge_id'])
    
    # Plant Assets table
    op.create_table(
        'plant_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tag', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('asset_type', sa.Enum('process_unit', 'storage_tank', 'pipeline', 'valve', 'pump', 'compressor', 'heat_exchanger', 'vessel', 'control_room', 'muster_point', 'fire_hydrant', 'safety_shower', 'gas_detector', 'other', name='assettype'), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('unit_area', sa.String(100)),
        sa.Column('elevation', sa.String(50)),
        sa.Column('coordinates', postgresql.GEOGRAPHY(geometry_type='POINT', srid=4326)),
        sa.Column('design_pressure', sa.Float),
        sa.Column('design_temperature', sa.Float),
        sa.Column('material', sa.String(100)),
        sa.Column('volume', sa.Float),
        sa.Column('hazardous_material', sa.Boolean, default=False),
        sa.Column('hazard_class', sa.String(50)),
        sa.Column('mawp', sa.Float),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_critical', sa.Boolean, default=False),
        sa.Column('last_inspection', sa.DateTime),
        sa.Column('next_inspection_due', sa.DateTime),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
    )
    op.create_index('ix_plant_assets_tag', 'plant_assets', ['tag'])
    op.create_index('ix_plant_assets_unit_type', 'plant_assets', ['unit_area', 'asset_type'])
    op.create_index('ix_plant_assets_critical_active', 'plant_assets', ['is_critical', 'is_active'])
    op.create_index('ix_plant_assets_coords', 'plant_assets', ['coordinates'], postgresql_using='gist')
    
    # Sensors table
    op.create_table(
        'sensors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tag', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('sensor_type', sa.Enum('gas_h2s', 'gas_ch4', 'gas_co', 'gas_o2', 'gas_combustible', 'temperature', 'pressure', 'flow', 'level', 'vibration', 'radiation', 'smoke', 'flame', 'weather_wind', 'weather_temp', 'weather_humidity', name='sensortype'), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plant_assets.id'), nullable=False),
        sa.Column('location_description', sa.String(200)),
        sa.Column('coordinates', postgresql.GEOGRAPHY(geometry_type='POINT', srid=4326)),
        sa.Column('range_min', sa.Float),
        sa.Column('range_max', sa.Float),
        sa.Column('units', sa.String(20)),
        sa.Column('alarm_low', sa.Float),
        sa.Column('alarm_high', sa.Float),
        sa.Column('alarm_critical_low', sa.Float),
        sa.Column('alarm_critical_high', sa.Float),
        sa.Column('last_calibration', sa.DateTime),
        sa.Column('next_calibration_due', sa.DateTime),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_safety_critical', sa.Boolean, default=False),
        sa.Column('communication_protocol', sa.String(50)),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_sensors_tag', 'sensors', ['tag'])
    op.create_index('ix_sensors_asset_type', 'sensors', ['asset_id', 'sensor_type'])
    op.create_index('ix_sensors_critical_active', 'sensors', ['is_safety_critical', 'is_active'])
    op.create_index('ix_sensors_coords', 'sensors', ['coordinates'], postgresql_using='gist')
    
    # Sensor Readings table
    op.create_table(
        'sensor_readings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('sensor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sensors.id'), nullable=False),
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('quality', sa.String(20)),
        sa.Column('timestamp', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('is_alarm', sa.Boolean, default=False),
        sa.Column('is_critical', sa.Boolean, default=False),
    )
    op.create_index('ix_sensor_readings_sensor_time', 'sensor_readings', ['sensor_id', 'timestamp'])
    op.create_index('ix_sensor_readings_time_alarm', 'sensor_readings', ['timestamp', 'is_alarm'])
    op.create_index('ix_sensor_readings_timestamp', 'sensor_readings', ['timestamp'])
    
    # Permits table
    op.create_table(
        'permits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('permit_number', sa.String(50), nullable=False, unique=True),
        sa.Column('permit_type', sa.Enum('hot_work', 'confined_space', 'working_at_height', 'excavation', 'electrical', 'line_break', 'radiation', 'chemical', 'general', name='permittype'), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('work_scope', sa.Text),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plant_assets.id')),
        sa.Column('location_description', sa.String(500)),
        sa.Column('coordinates', postgresql.GEOGRAPHY(geometry_type='POINT', srid=4326)),
        sa.Column('zone_classification', sa.String(50)),
        sa.Column('requested_start', sa.DateTime, nullable=False),
        sa.Column('requested_end', sa.DateTime, nullable=False),
        sa.Column('actual_start', sa.DateTime),
        sa.Column('actual_end', sa.DateTime),
        sa.Column('status', sa.Enum('draft', 'under_review', 'approved', 'active', 'suspended', 'closed', 'rejected', 'expired', name='permitstatus'), default='draft', nullable=False),
        sa.Column('risk_level', sa.Enum('low', 'medium', 'high', 'critical', name='risklevel'), default='low'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('supervisor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('standby_personnel', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column('gas_test_required', sa.Boolean, default=False),
        sa.Column('gas_test_valid_until', sa.DateTime),
        sa.Column('loto_required', sa.Boolean, default=False),
        sa.Column('loto_references', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('ppe_requirements', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('special_conditions', sa.Text),
        sa.Column('risk_assessment_id', postgresql.UUID(as_uuid=True)),
        sa.Column('method_statement_id', postgresql.UUID(as_uuid=True)),
        sa.Column('conflicting_permit_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column('is_suspended', sa.Boolean, default=False),
        sa.Column('suspension_reason', sa.Text),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('approved_at', sa.DateTime),
    )
    op.create_index('ix_permits_permit_number', 'permits', ['permit_number'])
    op.create_index('ix_permits_status_time', 'permits', ['status', 'requested_start'])
    op.create_index('ix_permits_asset_status', 'permits', ['asset_id', 'status'])
    op.create_index('ix_permits_active_time', 'permits', ['actual_start', 'actual_end'])
    op.create_index('ix_permits_coords', 'permits', ['coordinates'], postgresql_using='gist')
    
    # Gas Tests table
    op.create_table(
        'gas_tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('permit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permits.id'), nullable=False),
        sa.Column('tested_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('tested_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('valid_until', sa.DateTime, nullable=False),
        sa.Column('h2s_ppm', sa.Float),
        sa.Column('ch4_percent_lel', sa.Float),
        sa.Column('co_ppm', sa.Float),
        sa.Column('o2_percent', sa.Float),
        sa.Column('other_gases', postgresql.JSONB, default={}),
        sa.Column('is_pass', sa.Boolean, nullable=False),
        sa.Column('notes', sa.Text),
    )
    op.create_index('ix_gas_tests_permit', 'gas_tests', ['permit_id'])
    op.create_index('ix_gas_tests_tested_at', 'gas_tests', ['tested_at'])
    
    # Permit Inspections table
    op.create_table(
        'permit_inspections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('permit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permits.id'), nullable=False),
        sa.Column('inspected_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('inspected_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('checklist_items', postgresql.JSONB, default={}),
        sa.Column('overall_pass', sa.Boolean, nullable=False),
        sa.Column('findings', sa.Text),
        sa.Column('corrective_actions', sa.Text),
    )
    op.create_index('ix_permit_inspections_permit', 'permit_inspections', ['permit_id'])
    op.create_index('ix_permit_inspections_inspected_at', 'permit_inspections', ['inspected_at'])
    
    # Incidents table
    op.create_table(
        'incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('incident_number', sa.String(50), nullable=False, unique=True),
        sa.Column('severity', sa.Enum('near_miss', 'minor', 'moderate', 'major', 'critical', 'fatality', name='incidentseverity'), nullable=False),
        sa.Column('status', sa.Enum('reported', 'under_investigation', 'root_cause_analysis', 'corrective_actions', 'closed', name='incidentstatus'), default='reported'),
        sa.Column('category', sa.String(100)),
        sa.Column('subcategory', sa.String(100)),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('immediate_causes', sa.Text),
        sa.Column('root_causes', sa.Text),
        sa.Column('contributing_factors', sa.Text),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plant_assets.id')),
        sa.Column('location_description', sa.String(500)),
        sa.Column('coordinates', postgresql.GEOGRAPHY(geometry_type='POINT', srid=4326)),
        sa.Column('occurred_at', sa.DateTime, nullable=False),
        sa.Column('reported_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('injuries', sa.Integer, default=0),
        sa.Column('fatalities', sa.Integer, default=0),
        sa.Column('environmental_impact', sa.Boolean, default=False),
        sa.Column('production_loss_hours', sa.Float, default=0),
        sa.Column('estimated_cost', sa.Float),
        sa.Column('emergency_declared', sa.Boolean, default=False),
        sa.Column('emergency_level', sa.String(50)),
        sa.Column('response_actions', sa.Text),
        sa.Column('assignee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('investigator_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('investigation_deadline', sa.DateTime),
        sa.Column('rca_completed_at', sa.DateTime),
        sa.Column('corrective_actions', postgresql.JSONB, default=[]),
        sa.Column('is_reportable', sa.Boolean, default=False),
        sa.Column('regulatory_report_ref', sa.String(100)),
        sa.Column('regulatory_reported_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('closed_at', sa.DateTime),
    )
    op.create_index('ix_incidents_incident_number', 'incidents', ['incident_number'])
    op.create_index('ix_incidents_severity_status', 'incidents', ['severity', 'status'])
    op.create_index('ix_incidents_asset_time', 'incidents', ['asset_id', 'occurred_at'])
    op.create_index('ix_incidents_occurred_at', 'incidents', ['occurred_at'])
    op.create_index('ix_incidents_coords', 'incidents', ['coordinates'], postgresql_using='gist')
    
    # Incident Attachments table
    op.create_table(
        'incident_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('incidents.id'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(50)),
        sa.Column('file_size', sa.Integer),
        sa.Column('description', sa.Text),
        sa.Column('uploaded_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('uploaded_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('ix_incident_attachments_incident', 'incident_attachments', ['incident_id'])
    
    # Maintenance Records table
    op.create_table(
        'maintenance_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('work_order_number', sa.String(50), nullable=False, unique=True),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plant_assets.id'), nullable=False),
        sa.Column('maintenance_type', sa.String(50)),
        sa.Column('priority', sa.String(20)),
        sa.Column('description', sa.Text),
        sa.Column('work_performed', sa.Text),
        sa.Column('parts_replaced', postgresql.JSONB, default=[]),
        sa.Column('planned_start', sa.DateTime),
        sa.Column('planned_end', sa.DateTime),
        sa.Column('actual_start', sa.DateTime),
        sa.Column('actual_end', sa.DateTime),
        sa.Column('assigned_to_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('performed_by', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column('permit_required', sa.Boolean, default=False),
        sa.Column('permit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permits.id')),
        sa.Column('loto_applied', sa.Boolean, default=False),
        sa.Column('status', sa.String(50)),
        sa.Column('findings', sa.Text),
        sa.Column('recommendations', sa.Text),
        sa.Column('next_maintenance_due', sa.DateTime),
        sa.Column('labor_hours', sa.Float),
        sa.Column('material_cost', sa.Float),
        sa.Column('total_cost', sa.Float),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_maintenance_records_work_order', 'maintenance_records', ['work_order_number'])
    op.create_index('ix_maintenance_records_asset', 'maintenance_records', ['asset_id'])
    op.create_index('ix_maintenance_records_status', 'maintenance_records', ['status'])
    
    # Documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('document_type', sa.String(50)),
        sa.Column('category', sa.String(100)),
        sa.Column('file_path', sa.String(500)),
        sa.Column('content_hash', sa.String(64)),
        sa.Column('extracted_text', sa.Text),
        sa.Column('version', sa.String(20), default='1.0'),
        sa.Column('effective_date', sa.DateTime),
        sa.Column('expiry_date', sa.DateTime),
        sa.Column('review_frequency_days', sa.Integer),
        sa.Column('last_reviewed', sa.DateTime),
        sa.Column('reviewed_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('confidentiality', sa.String(20), default='internal'),
        sa.Column('tags', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('applicable_standards', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('applicable_assets', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column('applicable_permit_types', postgresql.ARRAY(sa.Enum('hot_work', 'confined_space', 'working_at_height', 'excavation', 'electrical', 'line_break', 'radiation', 'chemical', 'general', name='permittype')), default=[]),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('superseded_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id')),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
    )
    op.create_index('ix_documents_status', 'documents', ['status'])
    op.create_index('ix_documents_type', 'documents', ['document_type'])
    op.create_index('ix_documents_content_hash', 'documents', ['content_hash'])
    
    # Audits table
    op.create_table(
        'audits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('audit_number', sa.String(50), nullable=False, unique=True),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('standard', sa.Enum('iso_45001', 'osha_psm', 'api_580', 'api_581', 'seveso', 'oisd_116', 'oisd_117', 'factory_act', 'dgms', name='auditstandard'), nullable=False),
        sa.Column('scope', sa.Text),
        sa.Column('assets_in_scope', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column('areas_in_scope', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('planned_start', sa.DateTime),
        sa.Column('planned_end', sa.DateTime),
        sa.Column('actual_start', sa.DateTime),
        sa.Column('actual_end', sa.DateTime),
        sa.Column('auditor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('auditee_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column('lead_auditor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('status', sa.String(50), default='planned'),
        sa.Column('overall_result', sa.String(50)),
        sa.Column('major_findings', sa.Integer, default=0),
        sa.Column('minor_findings', sa.Integer, default=0),
        sa.Column('observations', sa.Integer, default=0),
        sa.Column('good_practices', sa.Integer, default=0),
        sa.Column('report_path', sa.String(500)),
        sa.Column('report_generated_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
    )
    op.create_index('ix_audits_audit_number', 'audits', ['audit_number'])
    op.create_index('ix_audits_standard', 'audits', ['standard'])
    op.create_index('ix_audits_status', 'audits', ['status'])
    
    # Audit Findings table
    op.create_table(
        'audit_findings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('audit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('audits.id'), nullable=False),
        sa.Column('finding_number', sa.String(50)),
        sa.Column('severity', sa.Enum('major', 'minor', 'observation', 'good_practice', name='findingseverity'), nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('clause_reference', sa.String(200)),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('evidence', sa.Text),
        sa.Column('requirement', sa.Text),
        sa.Column('root_cause', sa.Text),
        sa.Column('corrective_action', sa.Text),
        sa.Column('preventive_action', sa.Text),
        sa.Column('responsible_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('due_date', sa.DateTime),
        sa.Column('completion_date', sa.DateTime),
        sa.Column('status', sa.String(50), default='open'),
        sa.Column('verification_notes', sa.Text),
        sa.Column('verified_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('verified_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_audit_findings_audit', 'audit_findings', ['audit_id'])
    op.create_index('ix_audit_findings_severity', 'audit_findings', ['severity'])
    op.create_index('ix_audit_findings_status', 'audit_findings', ['status'])
    
    # Audit Checklist Items table
    op.create_table(
        'audit_checklist_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('audit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('audits.id'), nullable=False),
        sa.Column('clause', sa.String(200), nullable=False),
        sa.Column('requirement', sa.Text, nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('evidence_sources', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('evidence_collected', sa.Boolean, default=False),
        sa.Column('evidence_notes', sa.Text),
        sa.Column('result', sa.String(20)),
        sa.Column('notes', sa.Text),
        sa.Column('assessed_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('assessed_at', sa.DateTime),
        sa.Column('finding_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('audit_findings.id')),
    )
    op.create_index('ix_audit_checklist_audit', 'audit_checklist_items', ['audit_id'])
    op.create_index('ix_audit_checklist_result', 'audit_checklist_items', ['result'])
    
    # Emergency Incidents table
    op.create_table(
        'emergency_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('incident_number', sa.String(50), nullable=False, unique=True),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('incidents.id')),
        sa.Column('emergency_level', sa.String(20), nullable=False),
        sa.Column('emergency_type', sa.String(100)),
        sa.Column('incident_commander_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('safety_officer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('operations_chief_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('planning_chief_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('logistics_chief_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('liaison_officer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('declared_at', sa.DateTime, default=sa.func.now(), nullable=False),
        sa.Column('contained_at', sa.DateTime),
        sa.Column('closed_at', sa.DateTime),
        sa.Column('resources_deployed', postgresql.JSONB, default=[]),
        sa.Column('mutual_aid_activated', sa.Boolean, default=False),
        sa.Column('external_agencies_notified', postgresql.JSONB, default=[]),
        sa.Column('evacuation_zones', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('muster_points_activated', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column('personnel_accounted', sa.Integer, default=0),
    )
    op.create_index('ix_emergency_incidents_number', 'emergency_incidents', ['incident_number'])
    op.create_index('ix_emergency_incidents_status', 'emergency_incidents', ['status'])
    op.create_index('ix_emergency_incidents_declared', 'emergency_incidents', ['declared_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('emergency_incidents')
    op.drop_table('audit_checklist_items')
    op.drop_table('audit_findings')
    op.drop_table('audits')
    op.drop_table('documents')
    op.drop_table('maintenance_records')
    op.drop_table('incident_attachments')
    op.drop_table('incidents')
    op.drop_table('permit_inspections')
    op.drop_table('gas_tests')
    op.drop_table('permits')
    op.drop_table('sensor_readings')
    op.drop_table('sensors')
    op.drop_table('plant_assets')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS findingseverity')
    op.execute('DROP TYPE IF EXISTS auditstandard')
    op.execute('DROP TYPE IF EXISTS sensortype')
    op.execute('DROP TYPE IF EXISTS assettype')
    op.execute('DROP TYPE IF EXISTS risklevel')
    op.execute('DROP TYPE IF EXISTS incidentstatus')
    op.execute('DROP TYPE IF EXISTS incidentseverity')
    op.execute('DROP TYPE IF EXISTS permitstatus')
    op.execute('DROP TYPE IF EXISTS permittype')
    
    # Drop extensions (optional, might be used by other things)
    # op.execute('DROP EXTENSION IF EXISTS pg_trgm')
    # op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
    # op.execute('DROP EXTENSION IF EXISTS postgis')