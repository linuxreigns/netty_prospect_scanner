"""create pipeline_jobs

Revision ID: 0002_create_pipeline_jobs
Revises: 0001_create_prospects
Create Date: 2026-05-10
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_create_pipeline_jobs"
down_revision = "0001_create_prospects"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pipeline_jobs",
        sa.Column("job_id", sa.String(length=64), primary_key=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=True),
        sa.Column("max_attempts", sa.Integer(), nullable=True),
        sa.Column("discovered_count", sa.Integer(), nullable=True),
        sa.Column("scanned_count", sa.Integer(), nullable=True),
        sa.Column("saved_count", sa.Integer(), nullable=True),
        sa.Column("hot_count", sa.Integer(), nullable=True),
        sa.Column("phase", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("ix_pipeline_jobs_job_id", "pipeline_jobs", ["job_id"])
    op.create_index("ix_pipeline_jobs_status", "pipeline_jobs", ["status"])
    op.create_index("ix_pipeline_jobs_created_at", "pipeline_jobs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_pipeline_jobs_created_at", table_name="pipeline_jobs")
    op.drop_index("ix_pipeline_jobs_status", table_name="pipeline_jobs")
    op.drop_index("ix_pipeline_jobs_job_id", table_name="pipeline_jobs")
    op.drop_table("pipeline_jobs")
