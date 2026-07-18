"""Fronteira de elegibilidade de arquivos (T09).

Responsabilidade
    Reexportar a porta ``FileEligibilityFilter``, implementação pathspec,
    DTO/loader de ``.gitignore`` e regras de denylist.

Motivo da separação
    Superfície pública estável para T14 e testes sem acoplar ao layout
    interno dos submódulos ``filter`` / ``gitignore`` / ``rules``.
"""

from github_rag.eligibility.filter import (
    EligibilityError,
    FileEligibilityFilter,
    PathspecFileEligibilityFilter,
)
from github_rag.eligibility.gitignore import GitignoreSource, load_gitignore_sources
from github_rag.eligibility.rules import (
    CSV_DENYLIST,
    DEFAULT_ELIGIBILITY_RULES,
    IMAGE_DENYLIST,
    EligibilityRules,
)

__all__ = [
    "CSV_DENYLIST",
    "DEFAULT_ELIGIBILITY_RULES",
    "EligibilityError",
    "EligibilityRules",
    "FileEligibilityFilter",
    "GitignoreSource",
    "IMAGE_DENYLIST",
    "PathspecFileEligibilityFilter",
    "load_gitignore_sources",
]
