"""create prospects

Revision ID: 0001_create_prospects
Revises: 
Create Date: 2026-05-10
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_create_prospects"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prospects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("rubro", sa.String(length=100), nullable=True),
        sa.Column("provincia", sa.String(length=100), nullable=True),
        sa.Column("http_code", sa.Integer(), nullable=True),
        sa.Column("load_ok", sa.Boolean(), nullable=True),
        sa.Column("response_time_ms", sa.Float(), nullable=True),
        sa.Column("ssl_enabled", sa.Boolean(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("cms", sa.String(length=100), nullable=True),
        sa.Column("ecommerce_platform", sa.String(length=100), nullable=True),
        sa.Column("frontend_stack", sa.String(length=100), nullable=True),
        sa.Column("has_chatbot", sa.Boolean(), nullable=True),
        sa.Column("chatbot_vendor", sa.String(length=100), nullable=True),
        sa.Column("has_whatsapp", sa.Boolean(), nullable=True),
        sa.Column("has_contact_form", sa.Boolean(), nullable=True),
        sa.Column("has_email", sa.Boolean(), nullable=True),
        sa.Column("has_phone", sa.Boolean(), nullable=True),
        sa.Column("has_facebook", sa.Boolean(), nullable=True),
        sa.Column("has_instagram", sa.Boolean(), nullable=True),
        sa.Column("has_contact_page", sa.Boolean(), nullable=True),
        sa.Column("has_products_or_cart", sa.Boolean(), nullable=True),
        sa.Column("looks_outdated", sa.Boolean(), nullable=True),
        sa.Column("has_clear_cta", sa.Boolean(), nullable=True),
        sa.Column("netty_fit_score", sa.Integer(), nullable=True),
        sa.Column("fit_classification", sa.String(length=20), nullable=True),
        sa.Column("score_reasons", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("domain", name="uq_prospect_domain"),
    )

    op.create_index("ix_prospects_domain", "prospects", ["domain"])
    op.create_index("ix_prospects_rubro", "prospects", ["rubro"])
    op.create_index("ix_prospects_provincia", "prospects", ["provincia"])
    op.create_index("ix_prospects_cms", "prospects", ["cms"])
    op.create_index("ix_prospects_ecommerce_platform", "prospects", ["ecommerce_platform"])
    op.create_index("ix_prospects_frontend_stack", "prospects", ["frontend_stack"])
    op.create_index("ix_prospects_has_chatbot", "prospects", ["has_chatbot"])
    op.create_index("ix_prospects_has_whatsapp", "prospects", ["has_whatsapp"])
    op.create_index("ix_prospects_netty_fit_score", "prospects", ["netty_fit_score"])
    op.create_index("ix_prospects_fit_classification", "prospects", ["fit_classification"])


def downgrade() -> None:
    op.drop_index("ix_prospects_fit_classification", table_name="prospects")
    op.drop_index("ix_prospects_netty_fit_score", table_name="prospects")
    op.drop_index("ix_prospects_has_whatsapp", table_name="prospects")
    op.drop_index("ix_prospects_has_chatbot", table_name="prospects")
    op.drop_index("ix_prospects_frontend_stack", table_name="prospects")
    op.drop_index("ix_prospects_ecommerce_platform", table_name="prospects")
    op.drop_index("ix_prospects_cms", table_name="prospects")
    op.drop_index("ix_prospects_provincia", table_name="prospects")
    op.drop_index("ix_prospects_rubro", table_name="prospects")
    op.drop_index("ix_prospects_domain", table_name="prospects")
    op.drop_table("prospects")
