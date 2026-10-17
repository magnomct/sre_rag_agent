"""0001_initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. query_history
    op.create_table(
        'query_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=True, default=0.0),
        sa.Column('top_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('from_cache', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_query_history_created_at'), 'query_history', ['created_at'], unique=False)

    # 2. incident_simulations
    op.create_table(
        'incident_simulations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scenario_id', sa.String(length=100), nullable=False),
        sa.Column('scenario_title', sa.String(length=255), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True, default='completed'),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('mttd_seconds', sa.Float(), nullable=True, default=0.0),
        sa.Column('mttr_seconds', sa.Float(), nullable=True, default=0.0),
        sa.Column('score', sa.Integer(), nullable=True, default=0),
        sa.Column('hints_used', sa.Integer(), nullable=True, default=0),
        sa.Column('commands_executed', sa.Integer(), nullable=True, default=0),
        sa.Column('operator_solution', sa.Text(), nullable=True, default=''),
        sa.Column('is_correct', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_incident_simulations_scenario_id'), 'incident_simulations', ['scenario_id'], unique=False)
    op.create_index(op.f('ix_incident_simulations_difficulty'), 'incident_simulations', ['difficulty'], unique=False)
    op.create_index(op.f('ix_incident_simulations_created_at'), 'incident_simulations', ['created_at'], unique=False)
    op.create_index('idx_incident_perf', 'incident_simulations', ['scenario_id', 'difficulty'], unique=False)

    # 3. chaos_sessions
    op.create_table(
        'chaos_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('fault_type', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True, default=0.0),
        sa.Column('injected_count', sa.Integer(), nullable=True, default=0),
        sa.Column('active', sa.Boolean(), nullable=True, default=True),
        sa.Column('source', sa.String(length=50), nullable=True, default='operator'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chaos_sessions_session_id'), 'chaos_sessions', ['session_id'], unique=True)

    # 4. chaos_events
    op.create_table(
        'chaos_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=True, default='operator'),
        sa.Column('endpoint', sa.String(length=255), nullable=True, default=''),
        sa.Column('client_ip', sa.String(length=50), nullable=True, default=''),
        sa.Column('payload', sa.Text(), nullable=True, default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chaos_events_session_id'), 'chaos_events', ['session_id'], unique=False)
    op.create_index(op.f('ix_chaos_events_event_type'), 'chaos_events', ['event_type'], unique=False)
    op.create_index('idx_chaos_audit', 'chaos_events', ['event_type', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('chaos_events')
    op.drop_table('chaos_sessions')
    op.drop_table('incident_simulations')
    op.drop_table('query_history')
