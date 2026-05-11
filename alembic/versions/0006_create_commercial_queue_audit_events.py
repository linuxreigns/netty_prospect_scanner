"""create commercial_queue_audit_events

Revision ID: 0006_create_commercial_queue_audit_events
Revises: 0005_create_commercial_queue_items
Create Date: 2026-05-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_create_commercial_queue_audit_events"
down_revision = "0005_create_commercial_queue_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commercial_queue_audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("queue_item_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("actor", sa.String(length=120), nullable=False),
        sa.Column("previous_status", sa.String(length=20), nullable=True),
        sa.Column("new_status", sa.String(length=20), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["queue_item_id"], ["commercial_queue_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_commercial_queue_audit_events_id"), "commercial_queue_audit_events", ["id"], unique=False)
    op.create_index(
        op.f("ix_commercial_queue_audit_events_queue_item_id"),
        "commercial_queue_audit_events",
        ["queue_item_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_commercial_queue_audit_events_action"), "commercial_queue_audit_events", ["action"], unique=False
    )
    op.create_index(
        op.f("ix_commercial_queue_audit_events_created_at"),
        "commercial_queue_audit_events",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_commercial_queue_audit_events_created_at"), table_name="commercial_queue_audit_events")
    op.drop_index(op.f("ix_commercial_queue_audit_events_action"), table_name="commercial_queue_audit_events")
    op.drop_index(op.f("ix_commercial_queue_audit_events_queue_item_id"), table_name="commercial_queue_audit_events")
    op.drop_index(op.f("ix_commercial_queue_audit_events_id"), table_name="commercial_queue_audit_events")
    op.drop_table("commercial_queue_audit_events")
