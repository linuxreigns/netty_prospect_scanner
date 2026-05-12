"""add business_name, address, schema enrichment fields

Revision ID: 0009
Revises: 0008_add_is_parked_field
Create Date: 2026-05-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_add_enriched_fields"
down_revision = "0008_add_is_parked_field"
branch_labels = None
depends_on = None

_COLS = [
    ("business_name", sa.String(200)),
    ("address", sa.String(500)),
    ("schema_hours", sa.Text()),
    ("schema_price_range", sa.String(50)),
]


def upgrade() -> None:
    with op.batch_alter_table("prospects") as batch_op:
        for name, col_type in _COLS:
            batch_op.add_column(sa.Column(name, col_type, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("prospects") as batch_op:
        for name, _ in reversed(_COLS):
            batch_op.drop_column(name)
