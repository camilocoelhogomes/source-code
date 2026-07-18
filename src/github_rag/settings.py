"""Bootstrap de settings do processo — contratos T01 (sem domínio).

Responsabilidade deste módulo
    Declarar nomes/defaults de variáveis de ambiente de bootstrap e a superfície
    tipada (`AppSettings`, `load_settings`, `SettingsBootstrapError`) usada pelo
    processo. Em T01 não há parser de config, segredos, DB nem portas de domínio.

Motivo da separação
    Isolar configuração de processo (env) do domínio (arquivo JSON de conexões,
    catálogo, indexação). Tasks T02+ consomem estes valores; não antecipam APIs aqui.

Compatibilidade Windows / macOS / Linux
    Nomes de env são OS-agnostic. Paths usam ``pathlib.Path`` (sem hardcode de
    ``\\`` ou ``/``). O mesmo contrato vale no host de desenvolvimento e na
    imagem T19 (paths Linux da imagem; sem uso de ``.venv`` do host).
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol, runtime_checkable

# ---------------------------------------------------------------------------
# Constantes de contrato (nomes de env + defaults aprovados)
# ---------------------------------------------------------------------------

ENV_INDEX_WORKERS = "INDEX_WORKERS"
"""Nome canônico da env de workers de indexação.

Responsabilidade: único identificador de processo para esse limite.
Motivo da separação: evita acoplar atributos Python aos nomes de env.
Invariantes: string estável; não traduzida por OS.
Erros: nenhum.
Compatibilidade: idêntica em Windows, macOS e Linux.
"""

ENV_QUERY_WORKERS = "QUERY_WORKERS"
"""Nome canônico da env de workers de query.

Responsabilidade: único identificador de processo para esse limite.
Motivo da separação: mesmo motivo de ``ENV_INDEX_WORKERS``.
Invariantes: string estável; não traduzida por OS.
Erros: nenhum.
Compatibilidade: idêntica em Windows, macOS e Linux.
"""

ENV_CONFIG_PATH = "CONFIG_PATH"
"""Nome canônico da env que declara o caminho do arquivo de config externo.

Responsabilidade: apontar (só declarar) o path; **não** carregar nem validar JSON.
Motivo da separação: carga/validação do JSON de conexões pertencem a T02, não a T01.
Invariantes: string estável; valor tipado exposto como ``Path | None``.
Erros: nenhum nesta constante.
Compatibilidade: valor nativo do OS do host; na imagem T19, path Linux do container.
"""

DEFAULT_INDEX_WORKERS = 2
"""Default de ``INDEX_WORKERS`` quando a env está ausente ou em branco (ENG-003).

Responsabilidade: valor de bootstrap aprovado (não política de máximos — T04).
Motivo da separação: default versionado no contrato, não espalhado em callers.
Invariantes: literal ``2``; usado só se env ausente/blank.
Erros: nenhum.
Compatibilidade: OS-agnostic.
"""

DEFAULT_QUERY_WORKERS = 4
"""Default de ``QUERY_WORKERS`` quando a env está ausente ou em branco (ENG-003).

Responsabilidade: valor de bootstrap aprovado (não política de máximos — T04).
Motivo da separação: default versionado no contrato, não espalhado em callers.
Invariantes: literal ``4``; usado só se env ausente/blank.
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
        Mensagem cita o nome da variável e a razão da falha; não inclui segredos.

    Erros
        Esta classe **é** o tipo de erro; não envolve outras exceções de OS.

    Compatibilidade Windows / macOS / Linux
        Tipo puro Python; comportamento idêntico em todos os OS.
    """


@runtime_checkable
class AppSettings(Protocol):
    """Snapshot somente-leitura dos settings de bootstrap do processo.

    Responsabilidade
        Expor ``index_workers``, ``query_workers`` e ``config_path`` já tipados
        após ``load_settings``, sem reconsultar o ambiente.

    Motivo da separação
        Isola o contrato de configuração de processo do domínio (parser do arquivo
        de conexões, catálogo, indexação, MCP). Consumidores dependem do snapshot,
        não de ``os.environ``.

    Invariantes
        - ``index_workers`` e ``query_workers`` são ``int`` após carga ok.
        - ``config_path`` é ``None`` se ``CONFIG_PATH`` ausente/blank; senão ``Path``.
        - Não implica que o arquivo em ``config_path`` exista ou seja válido (T02).

    Erros
        O Protocol não levanta; falhas ocorrem em ``load_settings``.

    Compatibilidade Windows / macOS / Linux
        ``config_path`` usa ``pathlib.Path`` (paths nativos); sem separadores
        hardcoded na implementação futura.
    """

    @property
    def index_workers(self) -> int:
        """Workers de indexação efetivos (env ou default ``2``).

        Responsabilidade: expor o inteiro já resolvido para o runtime futuro (T04).
        Motivo da separação: atributo tipado distinto do nome de env ``INDEX_WORKERS``.
        Invariantes: sempre ``int`` em instância válida; default conceitual ``2``.
        Erros: nenhum na propriedade; conversão inválida falha na carga.
        Compatibilidade: OS-agnostic.
        """
        ...

    @property
    def query_workers(self) -> int:
        """Workers de query efetivos (env ou default ``4``).

        Responsabilidade: expor o inteiro já resolvido para o runtime futuro (T04).
        Motivo da separação: atributo tipado distinto do nome de env ``QUERY_WORKERS``.
        Invariantes: sempre ``int`` em instância válida; default conceitual ``4``.
        Erros: nenhum na propriedade; conversão inválida falha na carga.
        Compatibilidade: OS-agnostic.
        """
        ...

    @property
    def config_path(self) -> Path | None:
        """Path declarado em ``CONFIG_PATH``, ou ``None`` se ausente.

        Responsabilidade: carregar apenas o path tipado; não abrir/validar arquivo.
        Motivo da separação: parsing do arquivo de conexões e segredos ficam em T02.
        Invariantes: ``None`` ⇔ env ausente ou só whitespace; senão ``Path(valor)``.
        Erros: nenhum na propriedade.
        Compatibilidade: ``Path`` aceita paths Windows e POSIX; T19 usa paths Linux.
        """
        ...


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

    Erros
        ``SettingsBootstrapError`` se ``INDEX_WORKERS`` ou ``QUERY_WORKERS``
        estiverem presentes (não blank) e não forem conversíveis a ``int``.
        Não usa fallback silencioso para o default nesses casos.

    Compatibilidade Windows / macOS / Linux
        Mesma semântica em todos os OS; diferença apenas no formato do string
        de ``CONFIG_PATH``, interpretado via ``pathlib.Path``.

    Nota de pipeline (T01 — gate de interfaces)
        Esta assinatura é a superfície de contrato. O corpo concreto (leitura,
        conversão, construção do snapshot) é implementado pelo Developer após
        aprovação dos testes unitários — não nesta etapa.
    """
    ...
