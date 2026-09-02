"""interval rule fields

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-31

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("schedule_rules") as batch:
        batch.add_column(sa.Column("start_time", sa.Time(), nullable=True))
        batch.add_column(sa.Column("end_time", sa.Time(), nullable=True))
        batch.add_column(sa.Column("interval_minutes", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("schedule_rules") as batch:
        batch.drop_column("interval_minutes")
        batch.drop_column("end_time")
        batch.drop_column("start_time")
