"""add new tables

Revision ID: 0002_add_new_tables
Revises: 0001_initial
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0002_add_new_tables"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ai_insights table
    op.create_table(
        "ai_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("focus_score", sa.Float(), nullable=False),
        sa.Column("distractions_per_hour", sa.Float(), nullable=False),
        sa.Column("next_prediction", sa.DateTime(timezone=True), nullable=True),
        sa.Column("avg_session_length_minutes", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ai_insights_user_id", "ai_insights", ["user_id"])

    # consents table
    op.create_table(
        "consents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("consent_given_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consent_revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.String(length=32), nullable=False, server_default="1.0"),
    )
    op.create_index("ix_consents_user_id", "consents", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_consents_user_id", table_name="consents")
    op.drop_table("consents")
    op.drop_index("ix_ai_insights_user_id", table_name="ai_insights")
    op.drop_table("ai_insights")

