"""Add seller fields

Revision ID: 002
Revises: 001
Create Date: 2024-03-14 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add new columns to sellers table
    op.add_column('sellers', sa.Column('membership_status', sa.String(), nullable=True))
    op.add_column('sellers', sa.Column('profile_url', sa.String(), nullable=True))
    op.add_column('sellers', sa.Column('total_listings', sa.String(), nullable=True))

def downgrade() -> None:
    # Remove new columns from sellers table
    op.drop_column('sellers', 'membership_status')
    op.drop_column('sellers', 'profile_url')
    op.drop_column('sellers', 'total_listings') 