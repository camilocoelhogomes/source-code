"""Revisão inicial do catálogo: enums nativos + 3 tabelas (design §5.1/§5.3).

Cria os enums nativos ``repo_origin``, ``repo_state`` e ``execution_status`` e as
tabelas ``catalog_repository``, ``indexing_execution`` e ``file_processing`` com
constraints de integridade da origem, unicidade parcial do catálogo ativo e
índice único por ``(execution_id, file_path)``.

Revision ID: 0001_initial_catalog
Revises:
Create Date: 2026-07-18
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_catalog"
down_revision = None
branch_labels = None
depends_on = None

_repo_origin = postgresql.ENUM(
    "github", "local", name="repo_origin", create_type=False
)
_repo_state = postgresql.ENUM(
    "not_indexed",
    "queued",
    "indexing",
    "up_to_date",
    "error",
    name="repo_state",
    create_type=False,
)
_execution_status = postgresql.ENUM(
    "running", "succeeded", "failed", name="execution_status", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    _repo_origin.create(bind, checkfirst=True)
    _repo_state.create(bind, checkfirst=True)
    _execution_status.create(bind, checkfirst=True)

    op.create_table(
        "catalog_repository",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("connection_name", sa.Text(), nullable=False),
        sa.Column("origin", _repo_origin, nullable=False),
        sa.Column("github_org", sa.Text(), nullable=True),
        sa.Column("local_path", sa.Text(), nullable=True),
        sa.Column("repo_identifier", sa.Text(), nullable=False),
        sa.Column(
            "state", _repo_state, nullable=False, server_default="not_indexed"
        ),
        sa.Column("last_processed_commit", sa.Text(), nullable=True),
        sa.Column("current_main_commit", sa.Text(), nullable=True),
        sa.Column("progress_percent", sa.SmallInteger(), nullable=True),
        sa.Column("files_processed", sa.Integer(), nullable=True),
        sa.Column("files_total", sa.Integer(), nullable=True),
        sa.Column("current_stage", sa.Text(), nullable=True),
        sa.Column("current_execution_id", sa.Integer(), nullable=True),
        sa.Column(
            "active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "row_version", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "(origin <> 'github') OR (github_org IS NOT NULL)",
            name="github_requires_org",
        ),
        sa.CheckConstraint(
            "(origin <> 'local') OR (local_path IS NOT NULL)",
            name="local_requires_path",
        ),
    )
    op.create_index(
        "ux_catalog_repository_active_identity",
        "catalog_repository",
        ["connection_name", "repo_identifier"],
        unique=True,
        postgresql_where=sa.text("active"),
    )

    op.create_table(
        "indexing_execution",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "repository_id",
            sa.Integer(),
            sa.ForeignKey("catalog_repository.id"),
            nullable=False,
        ),
        sa.Column("status", _execution_status, nullable=False),
        sa.Column("commit_target", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "file_processing",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "execution_id",
            sa.Integer(),
            sa.ForeignKey("indexing_execution.id"),
            nullable=False,
        ),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("zoekt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tree_sitter_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata_persisted_at", sa.DateTime(timezone=True), nullable=True
        ),
    )
    op.create_index(
        "ux_file_processing_execution_path",
        "file_processing",
        ["execution_id", "file_path"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_file_processing_execution_path", table_name="file_processing")
    op.drop_table("file_processing")
    op.drop_table("indexing_execution")
    op.drop_index(
        "ux_catalog_repository_active_identity", table_name="catalog_repository"
    )
    op.drop_table("catalog_repository")

    bind = op.get_bind()
    _execution_status.drop(bind, checkfirst=True)
    _repo_state.drop(bind, checkfirst=True)
    _repo_origin.drop(bind, checkfirst=True)
