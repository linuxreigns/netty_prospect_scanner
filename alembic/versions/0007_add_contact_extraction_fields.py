"""add contact extraction fields

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_add_contact_extraction_fields"
down_revision = "0006_create_commercial_queue_audit_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("prospects") as batch_op:
        batch_op.add_column(sa.Column("phone_numbers", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("email_addresses", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("whatsapp_number", sa.String(30), nullable=True))
        batch_op.add_column(sa.Column("facebook_url", sa.String(500), nullable=True))
        batch_op.add_column(sa.Column("instagram_url", sa.String(500), nullable=True))
        batch_op.add_column(sa.Column("linkedin_url", sa.String(500), nullable=True))
        batch_op.add_column(sa.Column("twitter_url", sa.String(500), nullable=True))
        batch_op.add_column(sa.Column("youtube_url", sa.String(500), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("prospects") as batch_op:
        for col in ["phone_numbers", "email_addresses", "whatsapp_number",
                    "facebook_url", "instagram_url", "linkedin_url", "twitter_url", "youtube_url"]:
            batch_op.drop_column(col)
