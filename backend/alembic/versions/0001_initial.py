"""initial

Revision ID: 0001
Revises:
Create Date: 2026-08-08 00:00:00.000000

БЫЛО: старая миграция (id INTEGER, prediction INTEGER, probability FLOAT,
input_features STRING) описывала таблицу, не совпадающую ни с одной
реальной схемой в проекте (ни с init.sql, ни с чем-либо ORM-подобным —
модели ORM тогда вообще не существовало). Она бы создала таблицу, с
которой приложение не смогло бы работать.

СТАЛО: схема 1:1 соответствует app/database/models.py.
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "predictions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("input_payload", sa.JSON(), nullable=False),
        sa.Column("churn_probability", sa.Float(), nullable=False),
        sa.Column("churn_prediction", sa.Boolean(), nullable=False),
        sa.Column("model_version", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_predictions_created_at", "predictions", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_predictions_created_at", table_name="predictions")
    op.drop_table("predictions")
