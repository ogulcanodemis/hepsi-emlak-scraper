"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-03-14 10:00:00.000000

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
    # Create sellers table
    op.create_table(
        'sellers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('company', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create properties table
    op.create_table(
        'properties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('property_type', sa.String(), nullable=True),
        sa.Column('size', sa.Float(), nullable=True),
        sa.Column('room_count', sa.String(), nullable=True),
        sa.Column('floor', sa.String(), nullable=True),
        sa.Column('building_age', sa.String(), nullable=True),
        sa.Column('heating_type', sa.String(), nullable=True),
        sa.Column('bathroom_count', sa.String(), nullable=True),
        sa.Column('balcony', sa.String(), nullable=True),
        sa.Column('furnished', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(), nullable=True),
        sa.Column('seller_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['seller_id'], ['sellers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id'),
        sa.UniqueConstraint('url')
    )
    op.create_index(op.f('ix_properties_external_id'), 'properties', ['external_id'], unique=True)

    # Create features table
    op.create_table(
        'features',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create property_features association table
    op.create_table(
        'property_features',
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('feature_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['feature_id'], ['features.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('property_id', 'feature_id')
    )

    # Create property_images table
    op.create_table(
        'property_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('is_primary', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create search_history table
    op.create_table(
        'search_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('search_url', sa.String(), nullable=True),
        sa.Column('search_params', postgresql.JSONB(), nullable=True),
        sa.Column('results_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('search_history')
    op.drop_table('property_images')
    op.drop_table('property_features')
    op.drop_table('features')
    op.drop_index(op.f('ix_properties_external_id'), table_name='properties')
    op.drop_table('properties')
    op.drop_table('sellers') 