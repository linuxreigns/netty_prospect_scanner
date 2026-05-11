"""link agent_runs with prospects and pipeline_jobs

Revision ID: 0004_link_agent_runs_with_prospects_and_pipeline_jobs
Revises: 0003_create_agent_runs_and_traces
Create Date: 2026-05-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_link_agent_runs_with_prospects_and_pipeline_jobs"
down_revision = "0003_create_agent_runs_and_traces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agent_runs", sa.Column("prospect_id", sa.Integer(), nullable=True))
    op.add_column("agent_runs", sa.Column("pipeline_job_id", sa.String(length=64), nullable=True))

    op.create_index("ix_agent_runs_prospect_id", "agent_runs", ["prospect_id"])
    op.create_index("ix_agent_runs_pipeline_job_id", "agent_runs", ["pipeline_job_id"])

    op.create_foreign_key(
        "fk_agent_runs_prospect_id",
        "agent_runs",
        "prospects",
        ["prospect_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_agent_runs_pipeline_job_id",
        "agent_runs",
        "pipeline_jobs",
        ["pipeline_job_id"],
        ["job_id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_agent_runs_pipeline_job_id", "agent_runs", type_="foreignkey")
    op.drop_constraint("fk_agent_runs_prospect_id", "agent_runs", type_="foreignkey")
    op.drop_index("ix_agent_runs_pipeline_job_id", table_name="agent_runs")
    op.drop_index("ix_agent_runs_prospect_id", table_name="agent_runs")
    op.drop_column("agent_runs", "pipeline_job_id")
    op.drop_column("agent_runs", "prospect_id")
