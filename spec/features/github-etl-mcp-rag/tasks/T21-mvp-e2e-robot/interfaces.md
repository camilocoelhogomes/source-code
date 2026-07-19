# Interfaces — T21-mvp-e2e-robot

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T21-mvp-e2e-robot` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T21-mvp-e2e-robot` |
| Escopo desta etapa | Contratos Python do pacote `github_rag.e2e` (Protocols + defaults + erros + timeouts/paths) — **sem** implementação em `src/` |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-18 |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Self-review: Protocols `E2eStackLauncher`/`RobotMvpSuite`; defaults Podman/Default; resolver + erros + timeouts; superfície E2E-09; alinhado design 0.1.1 / BDD E2E-01..10. |

## 1. Escopo e exclusões

### Em escopo (Python — pacote `github_rag.e2e`)

| Contrato | Módulo | Papel | Handoff docs-cicd? |
|---|---|---|---|
| `E2eStackLauncher` | `e2e/ports.py` | Protocol lifecycle stack e2e | **Sim** |
| `RobotMvpSuite` | `e2e/ports.py` | Protocol orquestração prova MVP | **Sim** |
| `PodmanE2eStackLauncher` | `e2e/launcher.py` | Adaptador Podman + compose e2e | **Sim** (default concreto) |
| `DefaultRobotMvpSuite` | `e2e/suite.py` | Orquestração canônica | **Sim** (default concreto) |
| `E2eCredentialResolver` | `e2e/credentials.py` | Política HITL/CI + redaction | Pacote (testável; não handoff mínimo) |
| `ResolvedE2eCredential` | `e2e/credentials.py` | Valor tipado do token resolvido | Pacote |
| `E2eCredentialError` | `e2e/errors.py` | Credencial ausente/inválida | Pacote (exportado) |
| `E2eStackError` | `e2e/errors.py` | Compose/Podman/health falhou | Pacote (exportado) |
| `RobotCliRunner` | `e2e/ports.py` | Protocol callable do CLI `robot` | Pacote (injeção BDD) |
| Paths / constantes | `e2e/paths.py` | `COMPOSE_E2E`, `ROBOT_ROOT`, fixtures | Pacote (exportado) |
| Timeouts | `e2e/timeouts.py` | Defaults design §3.7 | Pacote |
| `__main__` / `run_mvp_e2e` | `e2e/__main__.py` / `e2e/suite.py` | Entry fino `python -m github_rag.e2e` | Opcional |

### Superfície Robot / fixtures (não é interface Python)

| Artefato | Papel | Como congela contrato |
|---|---|---|
| `e2e/robot/*.robot` | Asserções runtime green path | Ownership T21; invocadas por `RobotMvpSuite.run()` |
| `e2e/robot/resources/*` | Keywords HTTP/MCP/auth | Espelham timeouts; nunca logam token |
| `e2e/fixtures/config.e2e.json` | Config sem secrets; token `{ "env": "GITHUB_TOKEN" }` | E2E-08; `HOST_CONFIG` |
| `e2e/fixtures/repos/` | Fixture local versionável | E2E-05; `HOST_REPOS` |
| `e2e/results/` | Artefatos Robot (gitignored) | BDD-027 |
| `docker-compose.e2e.yml` | Compose T19 (consumo only) | D-T21-003; sem ownership T21 |

**Responsabilidade da superfície Robot/fixtures:** provar BDD-001–024 observáveis em stack real.  
**Motivo da separação:** runtime Python (`up`/`down`/`run`) ≠ keywords de asserção; ownership Robot permanece T21 (BR-030).

### Dependências consumidas (não redefinidas)

| Origem | Símbolos / artefatos |
|---|---|
| T19 | `docker-compose.e2e.yml`, alias `GITHUB_TOKEN: ${E2E_GITHUB_TOKEN:-${GITHUB_TOKEN:-}}`, imagem `app`, `/healthz` |
| SO / PATH | `podman` + `podman compose` (ou `podman-compose`) |
| Tooling | `robotframework`, `robotframework-requests` via optional-deps `e2e` |

### Fora de escopo

| Item | Dono |
|---|---|
| Alterar Dockerfile / 3 composes | T19 (proibido salvo bug bloqueante → SCOPE_CHANGE) |
| Esteira Actions / docs EN / GHCR | `docs-cicd-e2e-release` |
| Mock da API GitHub | Proibido |
| Automatizar BDD-015 | Excluído (D-T21-005) |
| Domínio de produto (catalog/index/query) | T03–T18 |
| Implementação em `src/` nesta etapa | Developer (pós unit plan) |

## 2. Decisões de contrato

| ID | Decisão | Motivo | Design / BDD |
|---|---|---|---|
| I-T21-001 | Pacote Python `github_rag.e2e` separado de `github_rag.delivery` | Runtime e2e ≠ composition root do container | D-T21-001; design §3.3 |
| I-T21-002 | Portas `@runtime_checkable`: `E2eStackLauncher` (`up`/`wait_healthy`/`down`) e `RobotMvpSuite` (`run() -> int`) | Handoff plano; doubles BDD sem Podman | design §3.3; E2E-03..09 |
| I-T21-003 | Defaults concretos: `PodmanE2eStackLauncher`, `DefaultRobotMvpSuite` | Consumo estável docs-cicd | design §3.8; E2E-09 |
| I-T21-004 | Compose file **fixo**: `docker-compose.e2e.yml` na raiz do repo (`COMPOSE_E2E`); Podman obrigatório (não Docker CLI primário) | REQ-051; D-T21-002/003 | E2E-05 |
| I-T21-005 | `up(env)` injeta `HOST_CONFIG` → `e2e/fixtures/config.e2e.json` e `HOST_REPOS` → `e2e/fixtures/repos` (paths absolutos resolvidos a partir de `repo_root`) | Green path local + GitHub | D-T21-012; E2E-05 |
| I-T21-006 | `E2eCredentialResolver.resolve(environ=…)`: HITL aceita `E2E_GITHUB_TOKEN` **ou** `GITHUB_TOKEN` (preferir `E2E_GITHUB_TOKEN` se ambos); CI (`GITHUB_ACTIONS=true` **ou** `E2E_REQUIRE_E2E_TOKEN=1`) exige **somente** `E2E_GITHUB_TOKEN` não vazio | REQ-049; DEC-020; D-T21-006 | E2E-01/02 |
| I-T21-007 | Credencial ausente/inválida → `E2eCredentialError` **antes** de `launcher.up`; mensagem sem valor de token | BDD-027 | E2E-01/10 |
| I-T21-008 | Falha compose/Podman/health → `E2eStackError`; factory `E2eStackError.from_stderr(raw: str)` redige substrings de token conhecidas / padrões `ghp_` | Não vazar secret em stderr | design §7; E2E-03/10 |
| I-T21-009 | Ordem congelada em `DefaultRobotMvpSuite.run()`: resolve → `up` → `wait_healthy` → `robot` → `down` (`down` no `finally`, inclusive em falha) | BDD-026 | E2E-03..06 |
| I-T21-010 | Invocação Robot **deve** excluir tag `bdd015` de forma explícita (`--exclude bdd015` / `exclude=` / lista `excludes`); mera substring não basta | D-T21-005 | E2E-07 |
| I-T21-011 | Green path inclui suites/markers: `health`, `catalog_indexing`, `ui`, `mcp`, `negative` sob `ROBOT_ROOT` (`e2e/robot/`) | D-T21-010; negative obrigatório | E2E-07 |
| I-T21-012 | `run() -> int`: `0` = MVP proof green; ≠0 = MVP não entregue; **não** propaga exceção de stack/credencial para o consumidor estável — captura, loga seguro, retorna ≠0 (exceções tipadas permanecem para uso direto do resolver/launcher em unit) | Exit codes estáveis CI | design §5; E2E-01..06 |
| I-T21-013 | `DefaultRobotMvpSuite` keyword-only; deps injetáveis: `launcher`, `robot_runner`, `credential_resolver`, `environ`, `repo_root` | Doubles sem Podman/robot real | D-T21-008; E2E-05 |
| I-T21-014 | Nome canônico do callable Robot: `robot_runner` (alias de construtor `run_robot=` **não** é contrato público; BDD aceita fallback só até implementação) | Congelar superfície | E2E-05 helper |
| I-T21-015 | Token **nunca** em argv/kwargs do `robot_runner`; só via env do processo compose (já alias T19) | BDD-014/027 | E2E-10 |
| I-T21-016 | Timeouts defaults em `github_rag.e2e.timeouts` (compose+healthy 600s; index 900s poll 5s; search 60s; 429 ≤3× wait 30–60s) | Flakiness GitHub | design §3.7 |
| I-T21-017 | Exports públicos mínimos handoff: `E2eStackLauncher`, `RobotMvpSuite`, `PodmanE2eStackLauncher`, `DefaultRobotMvpSuite`; também exportar erros, resolver, paths/timeouts para testes | E2E-09 + gate pytest | design §3.3/§3.8 |
| I-T21-018 | `python -m github_rag.e2e` → `SystemExit(DefaultRobotMvpSuite(launcher=PodmanE2eStackLauncher()).run())` | Entry fino operador/CI | design §3.8 |
| I-T21-019 | Health canônico: `GET http://127.0.0.1:8080/healthz` → 200 com UI+MCP ready (payload T19); MCP prova Robot = SSE `:8001` | D-T21-011; BDD-020 | design §5.1 |
| I-T21-020 | Stubs desta etapa: contratos em markdown; **proibido** criar `src/github_rag/e2e/` até unit plan + aprovação | Gate interfaces ≠ código produção | pipeline |

## 3. Layout do pacote (alvo pós-implementação)

```text
src/github_rag/e2e/
  __init__.py          # re-exports I-T21-017
  ports.py             # E2eStackLauncher, RobotMvpSuite, RobotCliRunner
  credentials.py       # E2eCredentialResolver, ResolvedE2eCredential
  errors.py            # E2eCredentialError, E2eStackError
  launcher.py          # PodmanE2eStackLauncher
  suite.py             # DefaultRobotMvpSuite, run_mvp_e2e
  paths.py             # COMPOSE_E2E, ROBOT_ROOT, fixtures
  timeouts.py          # constantes §3.7
  __main__.py          # python -m github_rag.e2e
```

**Responsabilidade do pacote:** orquestrar prova e2e (credencial → stack Podman → Robot → cleanup) sem domínio de produto.  
**Motivo da separação:** handoff consumível por `docs-cicd-e2e-release` sem ownership dos composes T19 nem das keywords Robot misturadas ao runtime Python.

## 4. Paths e constantes

Módulo: `github_rag.e2e.paths`

```python
from pathlib import Path

# Nomes/arquivos canônicos (relativos à raiz do repositório)
COMPOSE_E2E_NAME: str = "docker-compose.e2e.yml"
ROBOT_SUITE_DIRNAME: str = "e2e/robot"
E2E_CONFIG_FIXTURE_REL: str = "e2e/fixtures/config.e2e.json"
E2E_REPOS_FIXTURE_REL: str = "e2e/fixtures/repos"
E2E_RESULTS_DIRNAME: str = "e2e/results"

# Paths absolutos default (resolvidos em runtime a partir de repo_root;
# o pacote exporta Path apontando para a raiz detectada / injetada).
COMPOSE_E2E: Path
ROBOT_ROOT: Path
E2E_CONFIG_FIXTURE: Path
E2E_REPOS_FIXTURE: Path
E2E_RESULTS_DIR: Path

def resolve_repo_root(start: Path | None = None) -> Path:
    """Localiza a raiz do repo (presença de docker-compose.e2e.yml + pyproject).

    Responsabilidade
        Fornecer âncora única para COMPOSE_E2E / fixtures / ROBOT_ROOT.

    Motivo da separação
        Evita hardcode de cwd do processo CI vs operador local.
    """
    ...
```

- **Responsabilidade:** paths canônicos testáveis sem I/O de stack.  
- **Motivo da separação:** constantes ≠ launcher; E2E-05/09 leem `COMPOSE_E2E` / `ROBOT_ROOT` na superfície do pacote.  
- **Alias exportado:** `COMPOSE_E2E` é o nome canônico (BDD também aceita `COMPOSE_E2E_PATH` só como compat transitória — **não** contrato público).

## 5. Timeouts

Módulo: `github_rag.e2e.timeouts`

```python
COMPOSE_UP_HEALTHY_TIMEOUT_SECONDS: float = 600.0
INDEXING_TIMEOUT_SECONDS: float = 900.0
INDEXING_POLL_INTERVAL_SECONDS: float = 5.0
SEARCH_TIMEOUT_SECONDS: float = 60.0
SEARCH_HTTP_429_MAX_RETRIES: int = 3
GITHUB_RATE_LIMIT_MAX_RETRIES: int = 3
GITHUB_RATE_LIMIT_WAIT_MIN_SECONDS: float = 30.0
GITHUB_RATE_LIMIT_WAIT_MAX_SECONDS: float = 60.0
```

- **Responsabilidade:** defaults de espera/retry (design §3.7), espelhados em `e2e/robot/resources/common.resource`.  
- **Motivo da separação:** timeouts testáveis sem Podman; Robot e launcher compartilham a mesma fonte de verdade.

## 6. Erros

Módulo: `github_rag.e2e.errors`

```python
class E2eCredentialError(Exception):
    """Credencial e2e ausente ou inválida para o ambiente (HITL/CI).

    Responsabilidade
        Sinalizar falha explícita de política DEC-020 / REQ-049 antes de subir stack.
        ``str(self)`` NUNCA contém o valor do token.

    Motivo da separação
        Distingue falha de auth/política de falha de runtime Podman/compose (E2eStackError).
    """


class E2eStackError(Exception):
    """Falha ao subir, aguardar healthy ou derrubar a stack e2e.

    Responsabilidade
        Expor erro de runtime (compose/Podman/health) com mensagem segura
        (stderr truncado, sem token).

    Motivo da separação
        Isola I/O de infraestrutura das asserções Robot e da política de credencial.

    Classmethods
        from_stderr(raw: str, *, secrets: Sequence[str] | None = None) -> E2eStackError
            Constrói instância redigindo ``secrets`` conhecidos e padrões ``ghp_…``
            em ``raw`` antes de armazenar a mensagem (E2E-10).
    """

    @classmethod
    def from_stderr(
        cls,
        raw: str,
        *,
        secrets: Sequence[str] | None = None,
    ) -> E2eStackError: ...
```

## 7. Credenciais

Módulo: `github_rag.e2e.credentials`

```python
from dataclasses import dataclass
from collections.abc import Mapping
from typing import Literal

CredentialSource = Literal["E2E_GITHUB_TOKEN", "GITHUB_TOKEN"]


@dataclass(frozen=True, slots=True)
class ResolvedE2eCredential:
    """Token resolvido para o green path e2e.

    Responsabilidade
        Carregar o valor do token e a fonte escolhida, sem serializar em logs.

    Motivo da separação
        Evita ``str`` opaco; testes BDD leem ``.token`` de forma estável (E2E-02).
    """

    token: str
    source: CredentialSource


class E2eCredentialResolver:
    """Política de resolução de credencial HITL vs CI.

    Responsabilidade
        - HITL (``GITHUB_ACTIONS`` ausente/false e sem ``E2E_REQUIRE_E2E_TOKEN=1``):
          aceitar ``E2E_GITHUB_TOKEN`` ou ``GITHUB_TOKEN`` (não vazios);
          se ambos, preferir ``E2E_GITHUB_TOKEN``.
        - CI (``GITHUB_ACTIONS=true`` ou ``E2E_REQUIRE_E2E_TOKEN=1``):
          exigir ``E2E_GITHUB_TOKEN`` não vazio; **rejeitar** fallback ao
          ``GITHUB_TOKEN`` default do Actions.
        - Em falha: ``E2eCredentialError`` com mensagem genérica (sem secret).

    Motivo da separação
        Isola DEC-020 / REQ-049 / D-T21-006 do launcher e da suíte Robot;
        não faz parte do handoff mínimo docs-cicd, mas é contrato interno estável
        e testável (E2E-01/02/10).
    """

    def resolve(
        self,
        *,
        environ: Mapping[str, str] | None = None,
    ) -> ResolvedE2eCredential:
        """Resolve o token a partir de ``environ`` (default: ``os.environ``).

        Raises
            E2eCredentialError: ausente/vazio ou CI sem E2E_GITHUB_TOKEN.
        """
        ...
```

## 8. Portas

Módulo: `github_rag.e2e.ports`

### 8.1 `E2eStackLauncher`

```python
from typing import Any, Protocol, runtime_checkable
from collections.abc import Mapping


@runtime_checkable
class E2eStackLauncher(Protocol):
    """Lifecycle da stack e2e (Podman + docker-compose.e2e.yml).

    Responsabilidade
        Subir, aguardar healthy e derrubar a stack isolada T19, aplicando
        ``HOST_CONFIG`` / ``HOST_REPOS`` e env necessário ao compose.
        Falha explícita via ``E2eStackError`` se stack não sobe ou health timeout.

    Motivo da separação
        Runtime ≠ asserções Robot; reutilizável pela esteira docs-cicd sem
        ownership dos composes (C-T21-01; handoff plano).
    """

    def up(self, env: Mapping[str, str] | None = None, **kwargs: Any) -> None:
        """Sobe a stack (``podman compose -f docker-compose.e2e.yml up -d --build``).

        Responsabilidade
            Executar compose com env mesclado (incl. HOST_* e token já no environ
            do processo). Não invoca Robot.

        Motivo da separação
            Permite doubles que só registram ``env`` (E2E-05) sem Podman real.

        Raises
            E2eStackError: Podman/compose falhou.
        """
        ...

    def wait_healthy(self, *, timeout_seconds: float | None = None) -> None:
        """Aguarda ``GET /healthz`` = 200 com UI+MCP ready.

        Responsabilidade
            Bloquear até healthy ou timeout (default: timeouts.COMPOSE_UP_HEALTHY_*).

        Motivo da separação
            Health é pré-condição da suíte; falha aqui não deve invocar ``robot``
            (E2E-04).

        Raises
            E2eStackError: timeout ou health não-ok.
        """
        ...

    def down(self) -> None:
        """Derruba a stack (melhor esforço; idempotente o suficiente para ``finally``).

        Responsabilidade
            Cleanup após prova (sucesso ou falha). Erros de down não mascaram o
            exit code da suíte, mas não devem vazar secrets.

        Motivo da separação
            Garante cleanup observável nos doubles (E2E-03/04/06).
        """
        ...
```

### 8.2 `RobotCliRunner`

```python
@runtime_checkable
class RobotCliRunner(Protocol):
    """Invocação testável do CLI Robot Framework.

    Responsabilidade
        Executar as suites green path e retornar exit code do ``robot``.
        Deve aceitar exclusão explícita da tag ``bdd015`` e paths/markers das
        suites ``health``, ``catalog_indexing``, ``ui``, ``mcp``, ``negative``.

    Motivo da separação
        Isola subprocess ``robot`` do orquestrador; doubles BDD registram
        argv/kwargs sem stack real (E2E-05..07/10).
    """

    def __call__(self, *args: Any, **kwargs: Any) -> int:
        """Retorna exit code do Robot (0 = green).

        Contrato observável mínimo nos kwargs/args (qualquer encoding OK desde
        que E2E-07 passe):
        - exclusão explícita ``bdd015``;
        - presença dos markers/suites do green path;
        - sem valor de token (I-T21-015).
        """
        ...
```

### 8.3 `RobotMvpSuite`

```python
@runtime_checkable
class RobotMvpSuite(Protocol):
    """Orquestração canônica da prova MVP (BDD-026).

    Responsabilidade
        Coordenar credenciais → launcher → wait healthy → robot → down;
        retornar exit code estável (0 = MVP proof green).
        Declarar exclusão BDD-015 na invocação Robot.

    Motivo da separação
        Suíte consumível por docs-cicd sem transferir ownership Robot/composes
        (C-T21-03; BR-030; BDD-028).
    """

    def run(self) -> int:
        """Executa a prova MVP; 0 = green; ≠0 = MVP não entregue."""
        ...
```

## 9. Adaptador `PodmanE2eStackLauncher`

Módulo: `github_rag.e2e.launcher`

```python
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Callable


class PodmanE2eStackLauncher:
    """Adaptador Podman + docker-compose.e2e.yml (I-T21-003/004).

    Responsabilidade
        Implementar ``E2eStackLauncher`` invocando Podman compose no compose
        canônico T19; mesclar ``HOST_CONFIG``/``HOST_REPOS`` defaults dos fixtures;
        poll ``/healthz``; redigir stderr em ``E2eStackError``.

    Motivo da separação
        Mantém a porta estável enquanto o detalhe Podman/compose permanece
        substituível por doubles nos testes (D-T21-008).
    """

    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        compose_file: Path | None = None,
        health_url: str = "http://127.0.0.1:8080/healthz",
        healthy_timeout_seconds: float | None = None,
        run_command: Callable[[Sequence[str], Mapping[str, str]], tuple[int, str, str]]
        | None = None,
    ) -> None:
        """Keyword-only; ``run_command`` injetável para unit (sem Podman real)."""
        ...

    def up(self, env: Mapping[str, str] | None = None, **kwargs: Any) -> None: ...
    def wait_healthy(self, *, timeout_seconds: float | None = None) -> None: ...
    def down(self) -> None: ...
```

**Comportamento congelado de `up`:**

1. Resolve `compose_file` default = `{repo_root}/docker-compose.e2e.yml`.
2. Monta env efetivo = `environ` do processo ∪ `env` arg ∪ defaults:
   - `HOST_CONFIG` = abs path `e2e/fixtures/config.e2e.json` (se ausente no env)
   - `HOST_REPOS` = abs path `e2e/fixtures/repos` (se ausente no env)
3. Executa equivalente a: `podman compose -f <compose> up -d --build`.
4. Em exit ≠ 0 → `E2eStackError.from_stderr(...)`.

**Não faz:** asserções BDD de produto; ownership/edição do compose T19; mock GitHub.

## 10. `DefaultRobotMvpSuite`

Módulo: `github_rag.e2e.suite`

```python
from collections.abc import Mapping, MutableMapping
from pathlib import Path


class DefaultRobotMvpSuite:
    """Implementação canônica de ``RobotMvpSuite`` (I-T21-003/009/013).

    Responsabilidade
        Orquestrar resolve → up → wait_healthy → robot (green path, exclude bdd015)
        → down (finally); mapear falhas para exit ≠ 0 sem vazar secrets.

    Motivo da separação
        Único entry estável para operador/CI/docs-cicd; launcher e robot_runner
        permanecem substituíveis.
    """

    def __init__(
        self,
        *,
        launcher: E2eStackLauncher,
        robot_runner: RobotCliRunner | None = None,
        credential_resolver: E2eCredentialResolver | None = None,
        environ: Mapping[str, str] | MutableMapping[str, str] | None = None,
        repo_root: Path | None = None,
        output_dir: Path | None = None,
    ) -> None:
        """Todos os parâmetros keyword-only.

        Defaults de produção:
        - ``robot_runner``: subprocess ``robot`` apontando ``ROBOT_ROOT`` +
          ``--exclude bdd015`` + suites green path + ``outputdir=e2e/results``.
        - ``credential_resolver``: ``E2eCredentialResolver()``.
        - ``environ``: ``os.environ``.
        """
        ...

    def run(self) -> int:
        """Executa a prova; nunca omite ``launcher.down()`` após ``up`` bem-sucedido
        ou tentativa de up que exigiu cleanup (E2E-03/04/06).

        Política de exceção (I-T21-012):
        - ``E2eCredentialError`` / ``E2eStackError`` capturadas → return ≠ 0
          (mensagem segura em log/stderr do processo).
        - Exit code do ``robot_runner`` propagado (0 ou ≠0).
        """
        ...


def run_mvp_e2e(
    *,
    launcher: E2eStackLauncher | None = None,
    environ: Mapping[str, str] | None = None,
) -> int:
    """Helper de módulo / entrypoint.

    Responsabilidade
        Atalho equivalente a
        ``DefaultRobotMvpSuite(launcher=launcher or PodmanE2eStackLauncher(), …).run()``.

    Motivo da separação
        ``__main__`` e scripts CI não duplicam wiring.
    """
    ...
```

### 10.1 Pseudocontrato da invocação Robot (produção)

O `robot_runner` default **deve** tornar observáveis (E2E-07):

| Requisito | Encoding aceito |
|---|---|
| Exclude BDD-015 | `--exclude bdd015` **ou** `exclude="bdd015"` / `excludes=["bdd015"]` |
| Suites green path | paths ou args contendo `health`, `catalog_indexing`, `ui`, `mcp`, `negative` |
| Output | sob `e2e/results/` (gitignored) |
| Sem token | argv/kwargs sem valor do token |

## 11. Superfície pública `github_rag.e2e`

Módulo: `github_rag.e2e.__init__`

```python
from github_rag.e2e.ports import E2eStackLauncher, RobotMvpSuite, RobotCliRunner
from github_rag.e2e.launcher import PodmanE2eStackLauncher
from github_rag.e2e.suite import DefaultRobotMvpSuite, run_mvp_e2e
from github_rag.e2e.credentials import E2eCredentialResolver, ResolvedE2eCredential
from github_rag.e2e.errors import E2eCredentialError, E2eStackError
from github_rag.e2e.paths import COMPOSE_E2E, ROBOT_ROOT, E2E_CONFIG_FIXTURE, E2E_REPOS_FIXTURE
from github_rag.e2e import timeouts as timeouts

__all__ = [
    # Handoff docs-cicd (obrigatório E2E-09)
    "E2eStackLauncher",
    "RobotMvpSuite",
    "PodmanE2eStackLauncher",
    "DefaultRobotMvpSuite",
    # Pacote / testes
    "RobotCliRunner",
    "E2eCredentialResolver",
    "ResolvedE2eCredential",
    "E2eCredentialError",
    "E2eStackError",
    "run_mvp_e2e",
    "COMPOSE_E2E",
    "ROBOT_ROOT",
    "E2E_CONFIG_FIXTURE",
    "E2E_REPOS_FIXTURE",
    "timeouts",
]
```

Uso estável (congelado):

```python
from github_rag.e2e import DefaultRobotMvpSuite, PodmanE2eStackLauncher

suite = DefaultRobotMvpSuite(launcher=PodmanE2eStackLauncher())
raise SystemExit(suite.run())  # 0 = MVP proof green
```

## 12. `__main__`

Módulo: `github_rag.e2e.__main__`

```python
def main() -> None:
    """Entrypoint ``python -m github_rag.e2e`` → ``SystemExit(run_mvp_e2e())``."""
    raise SystemExit(run_mvp_e2e())


if __name__ == "__main__":
    main()
```

## 13. Mapeamento contratos × BDD

| Cenário | Contratos exercitados |
|---|---|
| E2E-01 | `E2eCredentialResolver` / `DefaultRobotMvpSuite.run`; `E2eCredentialError`; `up` não chamado |
| E2E-02 | CI exige `E2E_GITHUB_TOKEN`; `ResolvedE2eCredential.token` |
| E2E-03 | `E2eStackError` em `up`; robot não roda; `down` no finally |
| E2E-04 | `wait_healthy` → `E2eStackError`; robot não roda; `down` |
| E2E-05 | ordem + `HOST_CONFIG`/`HOST_REPOS` + `COMPOSE_E2E` |
| E2E-06 | `robot_runner` exit 1 → suite ≠ 0; `down` |
| E2E-07 | exclude `bdd015` + markers green path |
| E2E-08 | manifesto/fixtures (não Protocol) |
| E2E-09 | exports `__all__` handoff |
| E2E-10 | redaction `E2eCredentialError` / `E2eStackError.from_stderr` / argv robot |
| ROBOT-01..06 | ownership `e2e/robot/` via `ROBOT_ROOT` (fora do gate pytest) |

## 14. Compatibilidade e restrições

| Regra | Detalhe |
|---|---|
| Python | ≥ 3.12 |
| Sem domínio | Pacote `e2e` não importa catalog/index/query adapters de produto |
| Sem secrets | Fixtures JSON só `{ "token": { "env": "GITHUB_TOKEN" } }`; sem PAT literal |
| T19 intacto | Não editar compose/Dockerfile nesta task |
| optional-deps | Extra `e2e` em `pyproject.toml` + espelho `requirements-e2e.txt` (D-T21-007) — declarado na implementação |

## 15. Self-review Architect (gate)

| Critério | Resultado |
|---|---|
| Protocols obrigatórios do plano presentes | OK — `E2eStackLauncher`, `RobotMvpSuite` |
| Defaults concretos + resolver/erros/timeouts do design | OK — §§5–10 |
| Comentários RESPONSABILIDADE + MOTIVO DA SEPARAÇÃO em cada contrato | OK |
| Assinaturas alinhadas a `tests/bdd/test_mvp_e2e_robot.py` | OK — `environ`, `robot_runner`, `.token`, `from_stderr`, exports E2E-09 |
| CI vs HITL credencial (D-T21-006) | OK — I-T21-006 |
| Exclude bdd015 explícito + green path completo | OK — I-T21-010/011 |
| Sem implementação `src/` nesta etapa | OK — I-T21-020 |
| Achados BLOCKING/MAJOR abertos | Nenhum |

### Decisão

`APPROVED_BY_ARCHITECT` — interfaces.md `0.1.0` congelam a superfície `github_rag.e2e` para unit-test-plan e implementação subsequente.
