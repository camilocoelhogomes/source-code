"""Filtro de inclusão por wildcard prefixo/sufixo (T05 / BR-022).

Responsabilidade deste módulo
    Avaliar se um ``full_name`` ``org/repo`` casa um padrão de inclusão
    declarado em ``GitHubConnection.repos``.

Motivo da separação
    Regra pura de domínio testável sem mock de rede ou tipos T02 completos.
"""


def matches_inclusion_pattern(full_name: str, pattern: str) -> bool:
    """Retorna True se ``full_name`` casa o padrão ``org/repo_part``.

    Semântica de ``repo_part``:
        ``*`` — qualquer repo da org;
        ``prefix*`` — nome começa com ``prefix``;
        ``*suffix`` — nome termina com ``suffix``;
        caso contrário — igualdade exata do nome do repo.

    Padrões sem ``/`` ou com org diferente retornam False.
    """
    if "/" not in pattern:
        return False

    pattern_org, repo_pattern = pattern.split("/", 1)
    if "/" not in full_name:
        return False

    repo_org, repo_name = full_name.split("/", 1)
    if pattern_org != repo_org:
        return False

    if repo_pattern == "*":
        return True

    if repo_pattern.endswith("*") and not repo_pattern.startswith("*"):
        prefix = repo_pattern[:-1]
        return repo_name.startswith(prefix)

    if repo_pattern.startswith("*") and not repo_pattern.endswith("*"):
        suffix = repo_pattern[1:]
        return repo_name.endswith(suffix)

    return repo_name == repo_pattern


def matches_any_inclusion_pattern(
    full_name: str,
    patterns: tuple[str, ...] | list[str],
) -> bool:
    """True se ``full_name`` casa ao menos um padrão de inclusão."""
    return any(matches_inclusion_pattern(full_name, p) for p in patterns)
