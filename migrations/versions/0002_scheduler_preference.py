"""Preferência de cron do scheduler (T15 / ENG-004).

Cria a tabela singleton ``scheduler_preference`` para override de expressão
cron persistida pela UI (sem CRUD de conexões — BR-017).

Revision ID: 0002_scheduler_preference
Revises: 0001_initial_catalog
Create Date: 2026-07-18
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_scheduler_preference"
down_revision = "0001_initial_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheduler_preference",
        sa.Column("id", sa.SmallInteger(), primary_key=True),
        sa.Column("cron_expression", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("scheduler_preference")
