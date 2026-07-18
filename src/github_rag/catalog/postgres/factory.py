"""Fábrica do adaptador PostgreSQL — leitura de ``DATABASE_URL`` (design §3.2/§8).

Responsabilidade deste módulo
    Construir um ``PostgresCatalogRepository`` a partir de ``DATABASE_URL`` lida
    de um ``Mapping`` injetável (por padrão ``os.environ``), criando o engine e o
    ``sessionmaker`` SQLAlchemy.

Motivo da separação
    Mantém a leitura de ``DATABASE_URL`` na fronteira do catálogo (D-T03-006), sem
    reabrir o contrato T01. O ``Mapping`` injetável preserva o padrão OS-agnostic
    de T01 e permite testar sem variáveis reais de ambiente.

Segurança (design §8)
    Nenhuma mensagem de erro inclui a ``DATABASE_URL`` ou credenciais.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..errors import CatalogPersistenceError
from .repository import PostgresCatalogRepository

_DATABASE_URL_KEY = "DATABASE_URL"


def create_postgres_catalog_repository(
    env: Mapping[str, str] | None = None,
) -> PostgresCatalogRepository:
    """Cria o adaptador PG a partir de ``DATABASE_URL`` (formato SQLAlchemy).

    Levanta ``CatalogPersistenceError`` se a variável estiver ausente/vazia, sem
    jamais vazar o valor da URL (design §8).
    """
    source: Mapping[str, str] = os.environ if env is None else env
    database_url = source.get(_DATABASE_URL_KEY, "").strip()
    if not database_url:
        raise CatalogPersistenceError(
            f"{_DATABASE_URL_KEY} ausente ou vazia — configure a conexão PostgreSQL"
        )
    try:
        engine = create_engine(database_url, future=True)
    except Exception as exc:  # noqa: BLE001 - normaliza falha de infra sem vazar URL
        raise CatalogPersistenceError(
            "falha ao inicializar o engine PostgreSQL do catálogo"
        ) from exc
    session_factory = sessionmaker(bind=engine, future=True, expire_on_commit=False)
    return PostgresCatalogRepository(session_factory)
