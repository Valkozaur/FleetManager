"""add_route_management_tables

Revision ID: 9456a7c14c1b
Revises: 0684cc85fbca
Create Date: 2025-11-26 07:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9456a7c14c1b'
down_revision: Union[str, Sequence[str], None] = '0684cc85fbca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Enums
    route_status_enum = postgresql.ENUM('PLANNED', 'ACTIVE', 'COMPLETED', name='route_status_enum')
    route_status_enum.create(op.get_bind(), checkfirst=True)

    driver_status_enum = postgresql.ENUM('AVAILABLE', 'ON_ROUTE', name='driver_status_enum')
    driver_status_enum.create(op.get_bind(), checkfirst=True)

    stop_activity_type_enum = postgresql.ENUM('PICKUP', 'DROP', name='stop_activity_type_enum')
    stop_activity_type_enum.create(op.get_bind(), checkfirst=True)

    stop_status_enum = postgresql.ENUM('PENDING', 'ARRIVED', 'COMPLETED', name='stop_status_enum')
    stop_status_enum.create(op.get_bind(), checkfirst=True)

    # Create Tables
    op.create_table('trucks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('plate_number', sa.String(length=50), nullable=False),
        sa.Column('capacity_weight', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plate_number')
    )

    op.create_table('drivers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=False),
        sa.Column('status', postgresql.ENUM('AVAILABLE', 'ON_ROUTE', name='driver_status_enum', create_type=False), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('routes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('driver_id', sa.UUID(), nullable=False),
        sa.Column('truck_id', sa.UUID(), nullable=False),
        sa.Column('status', postgresql.ENUM('PLANNED', 'ACTIVE', 'COMPLETED', name='route_status_enum', create_type=False), nullable=False),
        sa.Column('scheduled_start_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ),
        sa.ForeignKeyConstraint(['truck_id'], ['trucks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('route_stops',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('route_id', sa.UUID(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('activity_type', postgresql.ENUM('PICKUP', 'DROP', name='stop_activity_type_enum', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'ARRIVED', 'COMPLETED', name='stop_status_enum', create_type=False), nullable=False),
        sa.Column('location', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('route_stops')
    op.drop_table('routes')
    op.drop_table('drivers')
    op.drop_table('trucks')

    # Drop Enums
    postgresql.ENUM(name='stop_status_enum').drop(op.get_bind())
    postgresql.ENUM(name='stop_activity_type_enum').drop(op.get_bind())
    postgresql.ENUM(name='driver_status_enum').drop(op.get_bind())
    postgresql.ENUM(name='route_status_enum').drop(op.get_bind())
