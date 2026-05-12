"""add is_parked field to prospects

Revision ID: 0008
Revises: 0007_add_contact_extraction_fields
Create Date: 2026-05-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_add_is_parked_field"
down_revision = "0007_add_contact_extraction_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("prospects") as batch_op:
        batch_op.add_column(sa.Column("is_parked", sa.Boolean(), nullable=False, server_default="0"))
        batch_op.create_index("ix_prospects_is_parked", ["is_parked"])


def downgrade() -> None:
    with op.batch_alter_table("prospects") as batch_op:
        batch_op.drop_index("ix_prospects_is_parked")
        batch_op.drop_column("is_parked")
