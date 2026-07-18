"""Mapeamento ORM do catálogo (SQLAlchemy 2.x; design §5.1).

Responsabilidade deste módulo
    Declarar o schema físico do catálogo — enums nativos PostgreSQL
    (``repo_origin``, ``repo_state``, ``execution_status``) e as três tabelas
    (`catalog_repository`, `indexing_execution`, `file_processing`) — como
    modelos declarativos tipados, com a ``MetaData`` de convenção de nomes que
    a revisão inicial do Alembic materializa.

Motivo da separação
    Manter o schema num único ponto (consumido pelo adaptador e pelo
    ``env.py`` do Alembic via ``Base.metadata``) evita divergência entre código e
    migração. Os enums nativos preservam a semântica PostgreSQL exigida pelo
    design (D-T03-003: sem SQLite).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    SmallInteger,
    Text,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..models import ExecutionStatus, RepoOrigin, RepoState

_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base declarativa com convenção de nomes determinística (design §5.3)."""

    metadata = MetaData(naming_convention=_NAMING_CONVENTION)


_repo_origin_enum = SAEnum(
    RepoOrigin, name="repo_origin", native_enum=True, values_callable=lambda e: [m.value for m in e]
)
_repo_state_enum = SAEnum(
    RepoState, name="repo_state", native_enum=True, values_callable=lambda e: [m.value for m in e]
)
_execution_status_enum = SAEnum(
    ExecutionStatus,
    name="execution_status",
    native_enum=True,
    values_callable=lambda e: [m.value for m in e],
)


class CatalogRepositoryRow(Base):
    """Linha do catálogo (SoT; design §5.1)."""

    __tablename__ = "catalog_repository"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    connection_name: Mapped[str] = mapped_column(Text, nullable=False)
    origin: Mapped[RepoOrigin] = mapped_column(_repo_origin_enum, nullable=False)
    github_org: Mapped[str | None] = mapped_column(Text, nullable=True)
    local_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    repo_identifier: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[RepoState] = mapped_column(
        _repo_state_enum, nullable=False, server_default=RepoState.NOT_INDEXED.value
    )
    last_processed_commit: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_main_commit: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_percent: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    files_processed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    files_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_stage: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_execution_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    row_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        CheckConstraint(
            "(origin <> 'github') OR (github_org IS NOT NULL)",
            name="github_requires_org",
        ),
        CheckConstraint(
            "(origin <> 'local') OR (local_path IS NOT NULL)",
            name="local_requires_path",
        ),
        Index(
            "ux_catalog_repository_active_identity",
            "connection_name",
            "repo_identifier",
            unique=True,
            postgresql_where=text("active"),
        ),
    )


class IndexingExecutionRow(Base):
    """Histórico de execuções (REQ-023; design §5.1)."""

    __tablename__ = "indexing_execution"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_repository.id"), nullable=False
    )
    status: Mapped[ExecutionStatus] = mapped_column(
        _execution_status_enum, nullable=False
    )
    commit_target: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class FileProcessingRow(Base):
    """Etapas por arquivo (REQ-022; design §5.1)."""

    __tablename__ = "file_processing"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[int] = mapped_column(
        ForeignKey("indexing_execution.id"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    zoekt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tree_sitter_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_persisted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index(
            "ux_file_processing_execution_path",
            "execution_id",
            "file_path",
            unique=True,
        ),
    )
