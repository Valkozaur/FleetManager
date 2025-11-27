"""add_truck_status_and_trailer

Revision ID: a1b2c3d4e5f6
Revises: 9456a7c14c1b
Create Date: 2025-11-27 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '9456a7c14c1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create TruckStatus Enum
    truck_status_enum = postgresql.ENUM('AVAILABLE', 'MAINTENANCE', 'OUT_OF_SERVICE', 'INACTIVE', name='truck_status_enum')
    truck_status_enum.create(op.get_bind(), checkfirst=True)

    # Add status column to trucks table
    op.add_column('trucks', sa.Column('status', postgresql.ENUM('AVAILABLE', 'MAINTENANCE', 'OUT_OF_SERVICE', 'INACTIVE', name='truck_status_enum', create_type=False), nullable=False, server_default='AVAILABLE'))
    
    # Add trailer_plate_number column to trucks table
    op.add_column('trucks', sa.Column('trailer_plate_number', sa.String(length=50), nullable=True))

    # Remove server_default after adding the column to avoid default value for future inserts if not intended
    op.alter_column('trucks', 'status', server_default=None)


def downgrade() -> None:
    # Drop trailer_plate_number column
    op.drop_column('trucks', 'trailer_plate_number')

    # Drop status column from trucks table
    op.drop_column('trucks', 'status')

    # Drop TruckStatus Enum
    postgresql.ENUM(name='truck_status_enum').drop(op.get_bind())
