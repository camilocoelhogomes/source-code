"""Modelos tipados do arquivo de config Sourcebot-like (T02) — sem I/O.

Responsabilidade deste módulo
    Declarar os tipos imutáveis que representam conexões validadas
    (``AppConfig``, ``GitHubConnection``, ``GitConnection``, refs e revisions).
    Não lê arquivo, não resolve env e não descobre repositórios.

Motivo da separação
    Isolar o schema tipado do loader (I/O + orquestração) e do resolver de
    segredos (política de redaction / env). T05/T06 consomem estes modelos;
    não dependem de dict JSON bruto.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, Protocol, runtime_checkable


@runtime_checkable
class EnvSecretRef(Protocol):
    """Referência ``{ "env": "<NOME>" }`` declarada no JSON.

    Responsabilidade
        Expor somente o nome da variável de ambiente referenciada pelo token.

    Motivo da separação
        O JSON não embute o valor do token (REQ-041); este tipo preserva a
        fronteira declaração vs materialização (``ResolvedSecret``).
    """

    @property
    def env(self) -> str:
        """Nome da variável de ambiente (não-blank após validação)."""
        ...


@runtime_checkable
class ResolvedSecret(Protocol):
    """Valor de segredo materializado de forma opaca.

    Responsabilidade
        Entregar o valor resolvido apenas via ``get_value()``, com
        ``__str__``/``__repr__`` redigidos (BDD-014 / BR-008 / BR-019).

    Motivo da separação
        Evita vazamento acidental em logs/repr de conexões ou ``AppConfig``.
    """

    def get_value(self) -> str:
        """Retorna o valor resolvido (não-blank). Não usar em str/repr."""
        ...


@runtime_checkable
class Revisions(Protocol):
    """Bloco ``revisions`` de uma conexão.

    Responsabilidade
        Expor ``branches`` já validado (não-vazio, itens não-blank, contém
        ``"main"`` — ENG-T02-001).

    Motivo da separação
        Regra compartilhada entre github e git, sem duplicar validação.
    """

    @property
    def branches(self) -> Sequence[str]:
        """Branches configuradas; deve incluir ``main``."""
        ...


@runtime_checkable
class GitHubConnection(Protocol):
    """Conexão discriminada ``type="github"``.

    Responsabilidade
        Expor orgs, repos (forma com wildcards de inclusão), referência de
        token, segredo resolvido e revisions — imutável após carga ok.

    Motivo da separação
        Campos/regras distintos de ``GitConnection``; callers discriminam sem
        dicts brutos. Expansão de wildcards = T05 (fora deste tipo).
    """

    @property
    def type(self) -> Literal["github"]:
        """Discriminante literal ``github``."""
        ...

    @property
    def orgs(self) -> Sequence[str]:
        """Organizações (lista não-vazia, itens não-blank)."""
        ...

    @property
    def repos(self) -> Sequence[str]:
        """Padrões de inclusão; pode ser vazia; ``*`` permitido na forma."""
        ...

    @property
    def token(self) -> EnvSecretRef:
        """Referência ``env`` do token (somente o nome)."""
        ...

    @property
    def secret(self) -> ResolvedSecret:
        """Token materializado (opaco; redacted em str/repr)."""
        ...

    @property
    def revisions(self) -> Revisions:
        """Revisões; ``branches`` contém ``main``."""
        ...


@runtime_checkable
class GitConnection(Protocol):
    """Conexão discriminada ``type="git"``.

    Responsabilidade
        Expor URL ``file://`` absoluta (forma POSIX/Windows) e revisions —
        imutável após carga ok.

    Motivo da separação
        Sem token/orgs/repos; validação de URL isolada. Existência de volume =
        T06 (fora deste tipo).
    """

    @property
    def type(self) -> Literal["git"]:
        """Discriminante literal ``git``."""
        ...

    @property
    def url(self) -> str:
        """URL ``file://`` absoluta (forma); glob ``*`` permitido."""
        ...

    @property
    def revisions(self) -> Revisions:
        """Revisões; ``branches`` contém ``main``."""
        ...


@runtime_checkable
class AppConfig(Protocol):
    """Snapshot imutável do arquivo de config válido.

    Responsabilidade
        Expor o mapa completo ``connections`` nome → conexão discriminada
        após validação e resolução bem-sucedidas.

    Motivo da separação
        Único tipo de sucesso do ``ConfigLoader``; nunca representa subset
        parcial (BR-021). Consumidores T05/T06 não dependem de JSON bruto.
    """

    @property
    def connections(self) -> Mapping[str, GitHubConnection | GitConnection]:
        """Mapa nome → conexão; ``{}`` é válido."""
        ...


@dataclass(frozen=True)
class _EnvSecretRef:
    """Implementação imutável da referência declarada no JSON."""

    env: str


@dataclass(frozen=True)
class _ResolvedSecret:
    """Implementação opaca cujo valor não participa de str/repr."""

    _value: str = field(repr=False)

    def get_value(self) -> str:
        """Retorna o valor somente por acesso explícito."""
        return self._value

    def __str__(self) -> str:
        return "<redacted>"

    def __repr__(self) -> str:
        return "_ResolvedSecret(<redacted>)"


@dataclass(frozen=True)
class _Revisions:
    """Implementação imutável de revisions."""

    branches: tuple[str, ...]


@dataclass(frozen=True)
class _GitHubConnection:
    """Implementação imutável da conexão GitHub validada."""

    orgs: tuple[str, ...]
    repos: tuple[str, ...]
    token: _EnvSecretRef
    secret: _ResolvedSecret
    revisions: _Revisions
    type: Literal["github"] = field(default="github", init=False)


@dataclass(frozen=True)
class _GitConnection:
    """Implementação imutável da conexão Git validada."""

    url: str
    revisions: _Revisions
    type: Literal["git"] = field(default="git", init=False)


@dataclass(frozen=True)
class _AppConfig:
    """Implementação imutável do snapshot completo."""

    connections: Mapping[str, GitHubConnection | GitConnection]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "connections",
            MappingProxyType(dict(self.connections)),
        )
