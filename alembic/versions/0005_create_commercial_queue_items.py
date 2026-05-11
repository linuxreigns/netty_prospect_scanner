"""create commercial_queue_items

Revision ID: 0005_create_commercial_queue_items
Revises: 0004_link_agent_runs_with_prospects_and_pipeline_jobs
Create Date: 2026-05-11
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0005_create_commercial_queue_items"
down_revision = "0004_link_agent_runs_with_prospects_and_pipeline_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commercial_queue_items",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("prospect_id", sa.Integer(), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["prospect_id"], ["prospects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_commercial_queue_items_id"), "commercial_queue_items", ["id"], unique=False)
    op.create_index(op.f("ix_commercial_queue_items_channel"), "commercial_queue_items", ["channel"], unique=False)
    op.create_index(op.f("ix_commercial_queue_items_prospect_id"), "commercial_queue_items", ["prospect_id"], unique=False)
    op.create_index(op.f("ix_commercial_queue_items_domain"), "commercial_queue_items", ["domain"], unique=False)
    op.create_index(op.f("ix_commercial_queue_items_status"), "commercial_queue_items", ["status"], unique=False)
    op.create_index(op.f("ix_commercial_queue_items_created_at"), "commercial_queue_items", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_commercial_queue_items_created_at"), table_name="commercial_queue_items")
    op.drop_index(op.f("ix_commercial_queue_items_status"), table_name="commercial_queue_items")
    op.drop_index(op.f("ix_commercial_queue_items_domain"), table_name="commercial_queue_items")
    op.drop_index(op.f("ix_commercial_queue_items_prospect_id"), table_name="commercial_queue_items")
    op.drop_index(op.f("ix_commercial_queue_items_channel"), table_name="commercial_queue_items")
    op.drop_index(op.f("ix_commercial_queue_items_id"), table_name="commercial_queue_items")
    op.drop_table("commercial_queue_items")
