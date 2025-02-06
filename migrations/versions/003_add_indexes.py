"""Add indexes for better performance

Revision ID: 003
Revises: 002
Create Date: 2024-03-14 12:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add indexes
    op.create_index('ix_properties_title', 'properties', ['title'])
    op.create_index('ix_properties_price', 'properties', ['price'])
    op.create_index('ix_properties_location', 'properties', ['location'])
    op.create_index('ix_properties_created_at', 'properties', ['created_at'])

def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_properties_title', 'properties')
    op.drop_index('ix_properties_price', 'properties')
    op.drop_index('ix_properties_location', 'properties')
    op.drop_index('ix_properties_created_at', 'properties') 