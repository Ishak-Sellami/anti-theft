"""initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-08-22 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.db.models.user import GUID

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='OWNER'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'recovery_policies',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('policy_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'used_nonces',
        sa.Column('nonce', sa.String(length=64), nullable=False),
        sa.Column('device_id', sa.String(length=64), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('nonce')
    )
    op.create_index('ix_used_nonces_expires_at', 'used_nonces', ['expires_at'])

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('actor_type', sa.String(length=20), nullable=False),
        sa.Column('actor_id', sa.String(length=64), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=64), nullable=False),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('prev_hash', sa.String(length=64), nullable=False),
        sa.Column('entry_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_actor_id', 'audit_logs', ['actor_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])

    op.create_table(
        'devices',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('owner_id', GUID(), nullable=False),
        sa.Column('device_name', sa.String(length=100), nullable=False),
        sa.Column('device_model', sa.String(length=100), nullable=True),
        sa.Column('os_version', sa.String(length=50), nullable=True),
        sa.Column('agent_version', sa.String(length=50), nullable=True),
        sa.Column('security_state', sa.String(length=20), nullable=False, server_default='NORMAL'),
        sa.Column('connectivity_state', sa.String(length=20), nullable=False, server_default='OFFLINE'),
        sa.Column('power_state', sa.String(length=20), nullable=False, server_default='NORMAL'),
        sa.Column('public_key_pem', sa.Text(), nullable=False),
        sa.Column('public_key_fingerprint', sa.String(length=64), nullable=False),
        sa.Column('enrollment_status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('active_policy_id', sa.String(length=64), nullable=False, server_default='pol_stolen_default_v1'),
        sa.Column('battery_level', sa.Integer(), nullable=True),
        sa.Column('is_charging', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('last_heartbeat_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_known_lat', sa.Float(), nullable=True),
        sa.Column('last_known_lng', sa.Float(), nullable=True),
        sa.Column('last_known_accuracy', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_key_fingerprint')
    )
    op.create_index('ix_devices_owner_id', 'devices', ['owner_id'])
    op.create_index('ix_devices_security_state', 'devices', ['security_state'])
    op.create_index('ix_devices_connectivity_state', 'devices', ['connectivity_state'])
    op.create_index('ix_devices_public_key_fingerprint', 'devices', ['public_key_fingerprint'])

    op.create_table(
        'location_telemetry',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('device_id', GUID(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('altitude', sa.Float(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('bearing', sa.Float(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('battery_level', sa.Integer(), nullable=True),
        sa.Column('power_state', sa.String(length=20), nullable=False),
        sa.Column('security_state', sa.String(length=20), nullable=False),
        sa.Column('connectivity_state', sa.String(length=20), nullable=False),
        sa.Column('network_metadata', sa.JSON(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_location_telemetry_device_id', 'location_telemetry', ['device_id'])
    op.create_index('ix_location_telemetry_recorded_at', 'location_telemetry', ['recorded_at'])

    op.create_table(
        'security_events',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('device_id', GUID(), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('security_state_before', sa.String(length=20), nullable=False),
        sa.Column('security_state_after', sa.String(length=20), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('device_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('signature', sa.String(length=512), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_security_events_device_id', 'security_events', ['device_id'])
    op.create_index('ix_security_events_event_type', 'security_events', ['event_type'])

    op.create_table(
        'device_commands',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('device_id', GUID(), nullable=False),
        sa.Column('issued_by', GUID(), nullable=False),
        sa.Column('command_type', sa.String(length=64), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('nonce', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('signature', sa.String(length=512), nullable=False),
        sa.Column('dispatched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result_payload', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['issued_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nonce')
    )
    op.create_index('ix_device_commands_device_id', 'device_commands', ['device_id'])
    op.create_index('ix_device_commands_status', 'device_commands', ['status'])

    op.create_table(
        'evidence_metadata',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('device_id', GUID(), nullable=False),
        sa.Column('event_id', GUID(), nullable=True),
        sa.Column('capture_type', sa.String(length=50), nullable=False),
        sa.Column('integrity_hash', sa.String(length=64), nullable=False),
        sa.Column('storage_ref', sa.String(length=512), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False, server_default='application/octet-stream'),
        sa.Column('file_size_bytes', sa.String(length=50), nullable=True),
        sa.Column('chain_of_custody_notes', sa.Text(), nullable=True),
        sa.Column('device_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['event_id'], ['security_events.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_evidence_metadata_device_id', 'evidence_metadata', ['device_id'])


def downgrade() -> None:
    op.drop_table('evidence_metadata')
    op.drop_table('device_commands')
    op.drop_table('security_events')
    op.drop_table('location_telemetry')
    op.drop_table('devices')
    op.drop_table('audit_logs')
    op.drop_table('used_nonces')
    op.drop_table('recovery_policies')
    op.drop_table('users')
