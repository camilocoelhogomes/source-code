"""Bootstrap de settings do processo — contratos T01 (sem domínio).

Responsabilidade deste módulo
    Declarar nomes/defaults de variáveis de ambiente de bootstrap e a superfície
    tipada (`AppSettings`, `load_settings`, `SettingsBootstrapError`) usada pelo
    processo. Em T01 não há parser de config, segredos, DB nem portas de domínio.

Motivo da separação
    Isolar configuração de processo (env) do domínio (arquivo JSON de conexões,
    catálogo, indexação). Tasks T02+ consomem estes valores; não antecipam APIs aqui.

Compatibilidade — Windows / macOS / Linux = primeira classe (não best-effort)
    Metade da equipe desenvolve em Windows; o contrato trata Windows com a mesma
    obrigatoriedade que macOS e Linux. Nomes de env são OS-agnostic. Paths usam
    ``pathlib.Path`` sem hardcode de separadores. ``CONFIG_PATH`` aceita
    paths nativos Windows (drive/UNC) e POSIX.

venv (dev local) × Docker/T19 (entrega)
    Dev local: processo pode rodar no venv do host (Windows PowerShell/cmd,
    macOS ou Linux). Entrega padronizada (T19): imagem **não monta** e **não
    usa** o ``.venv`` do host — motivo alinhado à entrega via Docker para equipe
    mista. Este módulo não depende do layout do ambiente virtual.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

_NativePath = type(Path())

# ---------------------------------------------------------------------------
# Constantes de contrato (nomes de env + defaults aprovados)
# ---------------------------------------------------------------------------

ENV_INDEX_WORKERS = "INDEX_WORKERS"
"""Nome canônico da env de workers de indexação.

Responsabilidade: único identificador de processo para esse limite.
Motivo da separação: evita acoplar atributos Python aos nomes de env.
Invariantes: string estável; não traduzida por OS.
Erros: nenhum.
Compatibilidade: idêntica em Windows, macOS e Linux (first-class).
"""

ENV_QUERY_WORKERS = "QUERY_WORKERS"
"""Nome canônico da env de workers de query.

Responsabilidade: único identificador de processo para esse limite.
Motivo da separação: mesmo motivo de ``ENV_INDEX_WORKERS``.
Invariantes: string estável; não traduzida por OS.
Erros: nenhum.
Compatibilidade: idêntica em Windows, macOS e Linux (first-class).
"""

ENV_CONFIG_PATH = "CONFIG_PATH"
"""Nome canônico da env que declara o caminho do arquivo de config externo.

Responsabilidade: apontar (só declarar) o path; **não** carregar nem validar JSON.
Motivo da separação: carga/validação do JSON de conexões pertencem a T02, não a T01.
Invariantes: string estável; valor tipado exposto como ``Path | None``.
Erros: nenhum nesta constante.
Compatibilidade (Windows first-class): no host Windows o valor pode ser path
nativo Windows; em macOS/Linux, POSIX; na imagem T19, path Linux do container.
Tipagem sempre via ``pathlib.Path`` — sem hardcode de separador. T19 não usa
``.venv`` do host.
"""

ENV_INDEX_CRON = "INDEX_CRON"
"""Nome canônico da env de expressão cron default de indexação (T15 / ENG-004).

Responsabilidade: único identificador de processo para o default de agenda.
Motivo da separação: schedule consome ``AppSettings.index_cron``; não relê env.
Invariantes: string estável; valor tipado exposto como ``str``.
Erros: nenhum nesta constante.
Compatibilidade: OS-agnostic (não é path).
"""

DEFAULT_INDEX_WORKERS = 2
"""Default de ``INDEX_WORKERS`` quando a env está ausente ou em branco (ENG-003).

Responsabilidade: valor de bootstrap aprovado (não política de máximos — T04).
Motivo da separação: default versionado no contrato, não espalhado em callers.
Invariantes: literal ``2``; usado só se env ausente/blank.
Erros: nenhum.
Compatibilidade: OS-agnostic (Windows, macOS, Linux, container T19).
"""

DEFAULT_QUERY_WORKERS = 4
"""Default de ``QUERY_WORKERS`` quando a env está ausente ou em branco (ENG-003).

Responsabilidade: valor de bootstrap aprovado (não política de máximos — T04).
Motivo da separação: default versionado no contrato, não espalhado em callers.
Invariantes: literal ``4``; usado só se env ausente/blank.
Erros: nenhum.
Compatibilidade: OS-agnostic (Windows, macOS, Linux, container T19).
"""

DEFAULT_INDEX_CRON = "0 2 * * *"
"""Default de ``INDEX_CRON`` quando a env está ausente ou em branco (ENG-004).

Responsabilidade: expressão cron diária (02:00 UTC) — caso especial de REQ-017.
Motivo da separação: default versionado no contrato T01; validação sintática em T15.
Invariantes: literal ``0 2 * * *``; usado só se env ausente/blank.
Erros: nenhum.
Compatibilidade: OS-agnostic.
"""

# CONFIG_PATH ausente/nulo no bootstrap: default tipado é None (sem path default).


class SettingsBootstrapError(Exception):
    """Falha de bootstrap ao tipar variáveis de ambiente.

    Responsabilidade
        Sinalizar conversão inválida (ex.: worker não numérico) sem política de
        domínio e sem I/O de arquivo.

    Motivo da separação
        Distinguir erros de bootstrap de erros de arquivo de conexões / segredos
        (T02+) e de falhas de infraestrutura.

    Invariantes
        Mensagem cita o nome da variável e a razão tipada da falha; não inclui
        segredos. **Sem dependência de shell:** não mencionar Activate.ps1,
        activate.bat, source, bin/activate, Scripts, PowerShell, cmd ou bash.

    Erros
        Esta classe **é** o tipo de erro; não envolve outras exceções de OS.

    Compatibilidade Windows / macOS / Linux (first-class)
        Tipo puro Python; mesma DX de erro no host (venv) e no container T19
        (entrega sem ``.venv`` do host).
    """


@runtime_checkable
class AppSettings(Protocol):
    """Snapshot somente-leitura dos settings de bootstrap do processo.

    Responsabilidade
        Expor ``index_workers``, ``query_workers``, ``config_path`` e
        ``index_cron`` já tipados após ``load_settings``, sem reconsultar o
        ambiente.

    Motivo da separação
        Isola o contrato de configuração de processo do domínio (parser do arquivo
        de conexões, catálogo, indexação, MCP). Consumidores dependem do snapshot,
        não de ``os.environ``.

    Invariantes
        - ``index_workers`` e ``query_workers`` são ``int`` após carga ok.
        - ``config_path`` é ``None`` se ``CONFIG_PATH`` ausente/blank; senão ``Path``.
        - ``index_cron`` é ``str`` não-vazia (env ou ``DEFAULT_INDEX_CRON``); sem
          validação de sintaxe cron (T15 / ``validate_cron_expression``).
        - Não implica que o arquivo em ``config_path`` exista ou seja válido (T02).

    Erros
        O Protocol não levanta; falhas ocorrem em ``load_settings``.

    Compatibilidade Windows / macOS / Linux (first-class)
        ``config_path`` usa ``pathlib.Path`` para paths nativos Windows (drive/UNC)
        e POSIX; sem separadores hardcoded. Válido no venv do host e no runtime
        T19 (que não monta/usa ``.venv`` do host).
    """

    @property
    def index_workers(self) -> int:
        """Workers de indexação efetivos (env ou default ``2``).

        Responsabilidade: expor o inteiro já resolvido para o runtime futuro (T04).
        Motivo da separação: atributo tipado distinto do nome de env ``INDEX_WORKERS``.
        Invariantes: sempre ``int`` em instância válida; default conceitual ``2``.
        Erros: nenhum na propriedade; conversão inválida falha na carga.
        Compatibilidade: OS-agnostic (Windows, macOS, Linux, T19).
        """
        ...

    @property
    def query_workers(self) -> int:
        """Workers de query efetivos (env ou default ``4``).

        Responsabilidade: expor o inteiro já resolvido para o runtime futuro (T04).
        Motivo da separação: atributo tipado distinto do nome de env ``QUERY_WORKERS``.
        Invariantes: sempre ``int`` em instância válida; default conceitual ``4``.
        Erros: nenhum na propriedade; conversão inválida falha na carga.
        Compatibilidade: OS-agnostic (Windows, macOS, Linux, T19).
        """
        ...

    @property
    def config_path(self) -> Path | None:
        """Path declarado em ``CONFIG_PATH``, ou ``None`` se ausente.

        Responsabilidade: carregar apenas o path tipado; não abrir/validar arquivo.
        Motivo da separação: parsing do arquivo de conexões e segredos ficam em T02.
        Invariantes: ``None`` ⇔ env ausente ou só whitespace; senão ``Path(valor)``.
        Erros: nenhum na propriedade.
        Compatibilidade (Windows first-class): aceita paths nativos Windows e
        POSIX via ``pathlib.Path``; T19 usa path Linux da imagem (sem ``.venv``
        do host). Proibido hardcodar separadores.
        """
        ...

    @property
    def index_cron(self) -> str:
        """Expressão cron default de boot (env ``INDEX_CRON`` ou default).

        Responsabilidade: expor a string já resolvida para o ``DailyScheduler``.
        Motivo da separação: atributo tipado distinto do nome de env ``INDEX_CRON``;
        o pacote ``schedule`` não relê ``os.environ`` (D-T15-001).
        Invariantes: sempre ``str`` não-vazia após strip; sem validação de sintaxe.
        Erros: nenhum na propriedade; sintaxe inválida falha em T15.
        Compatibilidade: OS-agnostic (não é path).
        """
        ...


@dataclass(frozen=True)
class _AppSettingsSnapshot:
    """Snapshot concreto e imutável do contrato ``AppSettings``."""

    index_workers: int
    query_workers: int
    config_path: Path | None
    index_cron: str


def _load_worker(
    environ: Mapping[str, str],
    name: str,
    default: int,
) -> int:
    """Converte uma env de worker ou aplica seu default quando blank."""
    raw_value = environ.get(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        return int(raw_value)
    except ValueError as error:
        raise SettingsBootstrapError(
            f"{name}: value must be a valid integer"
        ) from error


def load_settings(
    environ: Mapping[str, str] | None = None,
) -> AppSettings:
    """Carrega ``AppSettings`` a partir do ambiente do processo.

    Responsabilidade
        Ler ``environ`` (ou o ambiente do processo se ``None``), aplicar defaults
        ``2`` / ``4`` / ``None`` e conversões tipadas simples, devolver snapshot
        compatível com ``AppSettings``.

    Motivo da separação
        Único ponto de entrada testável (mapping injetável) sem DI nem loader de
        domínio. Não resolve segredos nem valida o arquivo de conexões (T02).

    Invariantes
        - ``environ is None`` → ambiente do processo; não mutar o mapping.
        - Chave ausente ou valor só whitespace → defaults do contrato.
        - Sem I/O de arquivo, rede, DB ou parse JSON.
        - Sem logging de valores de env.
        - Sem validação min/max de workers (T04).
        - OS-agnostic: não assume shell ou layout do ambiente virtual, nem
          ramifica defaults por sistema operacional.

    Erros
        ``SettingsBootstrapError`` se ``INDEX_WORKERS`` ou ``QUERY_WORKERS``
        estiverem presentes (não blank) e não forem conversíveis a ``int``.
        Mensagem: nome da env + razão tipada; **sem** jargão de shell.
        Não usa fallback silencioso para o default nesses casos.

    Compatibilidade Windows / macOS / Linux (first-class)
        Mesma semântica no venv do host (Windows PowerShell/cmd, macOS, Linux)
        e no processo da imagem T19. T19 = entrega padronizada e **não** monta
        nem usa o ``.venv`` do host. Diferença de OS só no formato do string de
        ``CONFIG_PATH``, sempre via ``pathlib.Path``.

    Implementação
        A carga produz um snapshot imutável que satisfaz ``AppSettings``.
    """
    source = os.environ if environ is None else environ
    raw_config_path = source.get(ENV_CONFIG_PATH)
    config_path = (
        None
        if raw_config_path is None or not raw_config_path.strip()
        else _NativePath(raw_config_path)
    )
    raw_index_cron = source.get(ENV_INDEX_CRON)
    index_cron = (
        DEFAULT_INDEX_CRON
        if raw_index_cron is None or not raw_index_cron.strip()
        else raw_index_cron.strip()
    )
    return _AppSettingsSnapshot(
        index_workers=_load_worker(
            source,
            ENV_INDEX_WORKERS,
            DEFAULT_INDEX_WORKERS,
        ),
        query_workers=_load_worker(
            source,
            ENV_QUERY_WORKERS,
            DEFAULT_QUERY_WORKERS,
        ),
        config_path=config_path,
        index_cron=index_cron,
    )
