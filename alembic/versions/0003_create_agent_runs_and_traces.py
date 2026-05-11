"""create agent_runs and agent_traces

Revision ID: 0003_create_agent_runs_and_traces
Revises: 0002_create_pipeline_jobs
Create Date: 2026-05-11
"""

import sqlalchemy as sa
from alembic import op


revision = "0003_create_agent_runs_and_traces"
down_revision = "0002_create_pipeline_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("rubro", sa.String(length=100), nullable=True),
        sa.Column("provincia", sa.String(length=100), nullable=True),
        sa.Column("ok", sa.Boolean(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("classification", sa.String(length=20), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("analysis_json", sa.Text(), nullable=True),
        sa.Column("proposal_json", sa.Text(), nullable=True),
        sa.Column("outreach_json", sa.Text(), nullable=True),
        sa.Column("follow_up_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_agent_runs_id", "agent_runs", ["id"])
    op.create_index("ix_agent_runs_domain", "agent_runs", ["domain"])
    op.create_index("ix_agent_runs_rubro", "agent_runs", ["rubro"])
    op.create_index("ix_agent_runs_provincia", "agent_runs", ["provincia"])
    op.create_index("ix_agent_runs_ok", "agent_runs", ["ok"])
    op.create_index("ix_agent_runs_score", "agent_runs", ["score"])
    op.create_index("ix_agent_runs_classification", "agent_runs", ["classification"])

    op.create_table(
        "agent_traces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("output_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_agent_traces_id", "agent_traces", ["id"])
    op.create_index("ix_agent_traces_run_id", "agent_traces", ["run_id"])
    op.create_index("ix_agent_traces_agent_name", "agent_traces", ["agent_name"])


def downgrade() -> None:
    op.drop_index("ix_agent_traces_agent_name", table_name="agent_traces")
    op.drop_index("ix_agent_traces_run_id", table_name="agent_traces")
    op.drop_index("ix_agent_traces_id", table_name="agent_traces")
    op.drop_table("agent_traces")

    op.drop_index("ix_agent_runs_classification", table_name="agent_runs")
    op.drop_index("ix_agent_runs_score", table_name="agent_runs")
    op.drop_index("ix_agent_runs_ok", table_name="agent_runs")
    op.drop_index("ix_agent_runs_provincia", table_name="agent_runs")
    op.drop_index("ix_agent_runs_rubro", table_name="agent_runs")
    op.drop_index("ix_agent_runs_domain", table_name="agent_runs")
    op.drop_index("ix_agent_runs_id", table_name="agent_runs")
    op.drop_table("agent_runs")
