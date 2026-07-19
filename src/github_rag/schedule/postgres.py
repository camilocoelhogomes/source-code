"""Adaptador SQLAlchemy da preferência de cron (T15 / BR-024).

Responsabilidade deste módulo
    Persistir a expressão cron em ``scheduler_preference`` via ORM.

Motivo da separação
    SQLAlchemy fica só aqui (ENG-013); sem APScheduler neste módulo.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime, timezone

from sqlalchemy import DateTime, MetaData, SmallInteger, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from github_rag.schedule.cron_expr import validate_cron_expression

_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

_SINGLETON_ID = 1


class Base(DeclarativeBase):
    """Base ORM do schedule (naming alinhado ao catálogo T03)."""

    metadata = MetaData(naming_convention=_NAMING_CONVENTION)


class SchedulerPreferenceRow(Base):
    """Linha singleton da preferência de cron (design §4.1)."""

    __tablename__ = "scheduler_preference"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    cron_expression: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class SqlAlchemyCronPreferenceStore:
    """``CronPreferenceStore`` via SQLAlchemy 2.x."""

    def __init__(
        self,
        session_factory: Callable[[], AbstractContextManager[Session]]
        | sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def get(self) -> str | None:
        with self._session_factory() as session:
            row = session.get(SchedulerPreferenceRow, _SINGLETON_ID)
            if row is None:
                return None
            return row.cron_expression

    def set(self, cron_expression: str) -> str:
        normalized = validate_cron_expression(cron_expression)
        now = datetime.now(timezone.utc)
        with self._session_factory() as session:
            row = session.get(SchedulerPreferenceRow, _SINGLETON_ID)
            if row is None:
                row = SchedulerPreferenceRow(
                    id=_SINGLETON_ID,
                    cron_expression=normalized,
                    updated_at=now,
                )
                session.add(row)
            else:
                row.cron_expression = normalized
                row.updated_at = now
            session.commit()
        return normalized

    def clear(self) -> None:
        with self._session_factory() as session:
            row = session.get(SchedulerPreferenceRow, _SINGLETON_ID)
            if row is not None:
                session.delete(row)
                session.commit()
