"""Adaptador PostgreSQL da porta ``CatalogRepository`` (design §3.1/§5).

Responsabilidade deste pacote
    Concentrar o I/O do catálogo contra PostgreSQL: mapeamento ORM (SQLAlchemy
    2.x), o repositório concreto ``PostgresCatalogRepository`` e a fábrica que lê
    ``DATABASE_URL`` na fronteira do catálogo (sem reabrir o contrato T01 —
    D-T03-006).

Motivo da separação
    Isolar toda a dependência de SQLAlchemy/psycopg aqui mantém o domínio
    (`catalog.memory`, `catalog.transitions`) 100% testável sem PG/Docker. Este
    pacote é importado sob demanda; o run de domínio nunca exige o driver.

Nota de cobertura
    O I/O real só é exercível contra PostgreSQL (testes ``integration``); por isso
    o pacote é omitido do gate de cobertura do run padrão (ver `pyproject.toml`).
"""

from __future__ import annotations

from .factory import create_postgres_catalog_repository
from .repository import PostgresCatalogRepository

__all__ = [
    "PostgresCatalogRepository",
    "create_postgres_catalog_repository",
]
