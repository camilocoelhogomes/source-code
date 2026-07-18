# Design — T06-local-discovery

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T06-local-discovery` |
| Autor | Implementation Task Runner |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T06-local-discovery` |
| Base | `main` (T01+T02+T03+T04 mergeados) |
| Rastreabilidade | REQ-034, REQ-040; BR-013–015; DEC-010; BDD-016–018 |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Escopo alinhado ao task file; sem achados BLOCKING/MAJOR. |

## 1. Contexto

T02 entrega `AppConfig` com conexões `type: "git"` cujas URLs `file://` são validadas **somente na forma** (path absoluto + glob permitido). T06 materializa a descoberta: expandir glob sobre volumes montados, validar repositório Git e exigir branch `main`, produzindo candidatos com origem `local` para T07 (`CatalogSync`).

Esta task **não** persiste catálogo, **não** indexa conteúdo, **não** lê working tree/uncommitted (BR-015; snapshot = T08) e **não** trata conexões GitHub (T05).

## 2. Problema

Na inicialização (futuro bootstrap T07/T19), para cada conexão `git` válida em `AppConfig`:

1. Interpretar URL `file://` absoluta e expandir globs (`file:///repos/*`, ENG-005).
2. Para cada path expandido: verificar acessibilidade do volume/caminho.
3. Aceitar somente diretórios com repositório Git válido **e** ref `main` presente.
4. Rejeitar paths inválidos **por path**, registrando erro, sem abortar outras conexões/paths.
5. Volume ausente/inacessível: zero candidatos dessa conexão + erro explícito (BDD-018).
6. Identificar origem `local` e caminho montado para handoff T07.

## 3. Solução proposta

Módulo `github_rag.sources.local` com separação:

| Componente | Módulo | Papel |
|---|---|---|
| Modelos de descoberta | `discovery.py` | `DiscoveredLocalRepo`, `LocalDiscoveryIssue`, `LocalDiscoveryResult` |
| Porta `LocalRepoDiscovery` | `discovery.py` | Orquestra descoberta por `AppConfig` ou conexão isolada |
| Inspeção Git filesystem | `git_fs.py` | Expandir URL, validar `.git`, ref `main` — injetável para testes |
| Re-exports | `__init__.py` | Superfície pública mínima |

Fluxo feliz:

```text
AppConfig.connections
  → filtrar type=="git"
  → para cada (connection_name, GitConnection):
       parse file:// URL → (base_path, glob_pattern)
       se base_path inacessível → LocalDiscoveryIssue(connection, url, reason); continue
       expandir glob → lista de Path candidatos
       para cada candidato:
         se não é diretório Git com main → LocalDiscoveryIssue(path); continue
         senão → DiscoveredLocalRepo(connection_name, local_path, repo_identifier, origin=local)
  → LocalDiscoveryResult(repos=tuple(...), issues=tuple(...))
```

### 3.1 Escopo BDD nesta task

| Cenário | Cobertura T06 | Fora de T06 |
|---|---|---|
| BDD-016 | Descoberta de repos locais válidos com `main`; origem `local`; paths montados | UI/checkbox/indexação (T07/T14/T18) |
| BDD-018 | Volume/path inacessível → sem candidatos + erro registrado | Messaging UI (T18) |
| BDD-017 (prep) | Descoberta só retorna repos com `main`; não cataloga outras branches | Snapshot/indexação (T08/T14) |

## 4. Componentes

### 4.1 `DiscoveredLocalRepo`

Campos imutáveis:

| Campo | Tipo | Invariantes |
|---|---|---|
| `connection_name` | `str` | Nome da conexão em `AppConfig.connections` |
| `origin` | `RepoOrigin.LOCAL` | Sempre `local` |
| `local_path` | `str` | Path absoluto normalizado do repo montado |
| `repo_identifier` | `str` | Identificador estável derivado do path (basename ou relativo ao mount) |

### 4.2 `LocalDiscoveryIssue`

Erro **não fatal** por conexão ou path (não derruba outras conexões):

| Campo | Tipo | Descrição |
|---|---|---|
| `connection_name` | `str` | Conexão afetada |
| `path` | `str` | URL declarada ou path expandido |
| `message` | `str` | Razão legível; sem segredos |

### 4.3 `LocalDiscoveryResult`

| Campo | Tipo | Invariantes |
|---|---|---|
| `repos` | `Sequence[DiscoveredLocalRepo]` | Somente Git válido + `main` |
| `issues` | `Sequence[LocalDiscoveryIssue]` | Falhas por conexão/path; nunca aborta descoberta global |

### 4.4 `GitFilesystemInspector` (porta interna)

Responsabilidade: I/O de filesystem + heurística Git **sem** mutar working tree e **sem** exigir binário `git` no MVP.

Operações:

- `parse_file_url(url: str) -> ParsedFileUrl` — separa base + glob
- `is_accessible(path: Path) -> bool`
- `expand_candidates(base: Path, pattern: str) -> Sequence[Path]`
- `inspect_repo(path: Path) -> RepoInspection` — `valid`, `has_main`, `reason`

Validação Git (filesystem):

- Diretório contém `.git` (dir ou arquivo gitdir)
- Ref `refs/heads/main` existe **ou** `packed-refs` contém ref para `main`

### 4.5 `LocalRepoDiscovery`

```python
class LocalRepoDiscovery:
    def __init__(self, inspector: GitFilesystemInspector | None = None) -> None: ...

    def discover(self, config: AppConfig) -> LocalDiscoveryResult: ...

    def discover_connection(
        self, connection_name: str, connection: GitConnection
    ) -> LocalDiscoveryResult: ...
```

Invariantes:

- Ignora conexões `github` (não são escopo local).
- Falha de uma conexão não impede processamento das demais.
- Falha de um path expandido não impede outros paths da mesma conexão.
- Nunca indexa nem lê conteúdo de arquivos de trabalho; só metadados Git mínimos.
- `repo_identifier`: basename do diretório do repo (estável para T07 upsert).

## 5. Fluxo de dados

```text
GitConnection.url (file:///repos/*)
        │
        ▼
 parse_file_url ──► base=/repos, glob=*
        │
        ▼
 is_accessible(base)? ──no──► issue + repos=[]
        │
       yes
        │
        ▼
 expand_candidates ──► [/repos/a, /repos/b, /repos/not-git]
        │
        ▼
 inspect_repo(each) ──► valid+main → DiscoveredLocalRepo
                     └── else → LocalDiscoveryIssue
```

## 6. Erros e observabilidade

| Condição | Comportamento |
|---|---|
| Base path inacessível (volume ausente) | `issues` com mensagem; `repos` vazio para conexão |
| Path não é diretório | issue por path |
| Sem `.git` | issue por path |
| Sem branch `main` | issue por path |
| Conexão git com URL sem glob (repo único) | trata base como candidato único |

Mensagens citam conexão e path; **nunca** segredos (N/A nesta camada).

## 7. Segurança e compatibilidade

- Somente paths declarados em config (BR-013); não varre filesystem arbitrário além do glob declarado.
- Paths POSIX `file:///repos/...` e Windows `file:///C:/repos/...` (forma validada em T02).
- Desenvolvimento/testes usam `tempfile`/`Path`; convenção container `/repos` documentada (ENG-005).

## 8. Riscos e rollback

| Risco | Mitigação |
|---|---|
| Glob amplo seleciona muitos dirs | Escopo do glob vem do JSON; T07 lista antes de indexar |
| Worktree/submodule `.git` file | Parser gitdir mínimo em `git_fs.py` |
| `main` só em packed-refs | Leitura mínima de `packed-refs` |

Rollback: remover módulo `sources.local` implementado; T07 permanece bloqueada sem T06.

## 9. Handoff T07

`CatalogSync` consumirá `LocalDiscoveryResult.repos` para upsert com `RepoOrigin.LOCAL`, `connection_name`, `local_path`, `repo_identifier`. Issues alimentam log/UI via bootstrap (T18).
