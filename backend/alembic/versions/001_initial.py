"""initial

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=True),
        sa.Column('prediction', sa.Integer(), nullable=True),
        sa.Column('probability', sa.Float(), nullable=True),
        sa.Column('model_version', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('input_features', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_predictions_customer_id'), 'predictions', ['customer_id'], unique=False)
    op.create_index(op.f('ix_predictions_id'), 'predictions', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_predictions_id'), table_name='predictions')
    op.drop_index(op.f('ix_predictions_customer_id'), table_name='predictions')
    op.drop_table('predictions')