# Design — T10-zoekt-adapter

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T10-zoekt-adapter` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-18 (review design v0.1.0 → v0.1.1) |
| Branch | (a criar na implementação) `feature/github-etl-mcp-rag-T10-zoekt-adapter` |
| Base | `main` (T01 mesclado; skeleton `index/zoekt`) |
| Rastreabilidade | DEC-002, DEC-016; REQ-002; BR-023; BDD-009; BDD-024; ENG-014; ENG-012 (handoff remoção) |

## 1. Contexto

O produto indexa o tip `main` de repositórios e oferece busca **exata** e semântica (REQ-002). Por DEC-002, Zoekt é o motor de busca exata e mantém os metadados desse índice. Por DEC-016 / ENG-014 / BR-023 / BDD-024, **não existe SDK Python maduro** — a integração deve ser um **adaptador fino** sobre a API HTTP e/ou CLI **oficial** do Zoekt (`sourcegraph/zoekt`), sem reinventar formato de índice nem protocolo.

T01 já reservou o pacote `src/github_rag/index/zoekt/`. T14 (`IndexingOrchestrator`) e T16 (`QueryService`) consomem a porta `ExactCodeIndex`. T19 entrega o serviço `zoekt` no compose.

Fora de escopo desta task: chunks Tree-sitter, Qdrant, MCP/UI (consomem via T16), orquestração de restart de repo (T14), imagem/compose (T19).

## 2. Problema

1. Expor contrato de domínio estável (`ExactCodeIndex`) para indexar um conjunto de arquivos de um repo/commit e buscar correspondências exatas com metadados (repositório, caminho, commit, trecho) — base BDD-009.
2. Falar com Zoekt **somente** pelos canais oficiais (DEC-016), sem client HTTP/CLI proprietário paralelo.
3. Propagar falhas como erro tipado para T14 reiniciar o repositório inteiro (BR-005 / fluxo de erro do requirements).
4. Permitir testes unitários/BDD com double/fake injetável, sem processo Zoekt real.
5. Alinhar com ENG-012 (reindex por arquivo inteiro; paths removidos saem do índice) sem expandir escopo indevido.

## 3. Solução proposta

Pacote `github_rag.index.zoekt` com separação clara:

| Camada | Componente | Papel |
|---|---|---|
| Domínio | `ExactCodeIndex` (Protocol) | Porta: indexar / buscar / limpar índice de repo |
| Domínio | `FileToIndex`, `ExactMatch`, `ExactSearchQuery` | Modelos imutáveis de entrada/saída |
| Domínio | `ExactCodeIndexError` | Erro tipado para T14 |
| Transporte | `ZoektSearchTransport` | Cliente fino HTTP oficial `POST /api/search` |
| Transporte | `ZoektIndexRunner` | Invocador fino da CLI oficial de indexação |
| Adaptação | `ZoektExactCodeIndex` | Implementa a porta mapeando modelos ↔ transporte |
| Test double | `FakeExactCodeIndex` | Double injetável (memória) para T10/T14/T16 |

Fluxo feliz (indexação):

```text
T14 → ExactCodeIndex.index(repo, commit, files: Sequence[FileToIndex])
        → prepara árvore/workdir no escopo do adaptador (paths + conteúdo tip)
        → ZoektIndexRunner: CLI oficial (zoekt-git-index | zoekt-index)
             -index <ZOEKT_INDEX_DIR> …
        → shards no diretório compartilhado com zoekt-webserver
        → ok (T14 marca FileStage.ZOEKT)
```

Fluxo feliz (busca):

```text
T16 → ExactCodeIndex.search(ExactSearchQuery)
        → monta query language oficial Zoekt (literal + filtros repo/path se houver)
        → ZoektSearchTransport: POST {ZOEKT_URL}/api/search
             body JSON oficial {"Q":"…","Opts":{"NumContextLines":N}}
        → mapeia FileMatches → Sequence[ExactMatch]
             (repository, path, commit, snippet)
```

Fluxo de erro:

```text
CLI exit ≠ 0 | HTTP 4xx/5xx | timeout | JSON inválido | binário ausente
  → ExactCodeIndexError (mensagem com repo/commit/status; sem segredos)
  → T14 marca execução em erro e reinicia o repositório inteiro
```

### 3.1 Escopo BDD nesta task

| Cenário | Cobertura T10 | Fora de T10 |
|---|---|---|
| BDD-009 | Indexação torna conteúdo buscável por match exato via porta; metadados mínimos presentes | UI que apresenta resultados (T18); QueryService (T16) |
| BDD-024 / DEC-016 | Somente adaptador fino sobre HTTP/CLI oficial; fake nos testes | Compose `zoekt` (T19) |
| Falha tipada (aceite T10) | `ExactCodeIndexError` em falhas de transporte/CLI | Política de restart (T14) |

## 4. Decisões técnicas

### D-T10-001 — Protocolo oficial: HTTP para busca + CLI para indexação

**Escolha:** híbrido oficial documentado pelo projeto `sourcegraph/zoekt`:

| Operação | Canal oficial | Referência |
|---|---|---|
| Busca | HTTP JSON `POST /api/search` no `zoekt-webserver` com flag `-rpc` | `doc/json-api.md` |
| Indexação | CLI `zoekt-git-index` (repo Git) ou `zoekt-index` (diretório) | README oficial |

**Motivo:**

- A API JSON oficial cobre **search**, não um endpoint HTTP estável de indexação ad-hoc no MVP.
- A CLI oficial escreve o formato de shard nativo; o webserver apenas lê `-index <dir>`.
- Evita reinventar formato de índice (DEC-016) e evita depender de `zoekt-indexserver`/mirror GitHub (fora do modelo do produto — nós já temos clone/snapshot via T08).

**Caminho MVP obrigatório (contrato da porta):**

1. `ExactCodeIndex.index` recebe `files` com `content` integral.
2. O adaptador materializa uma árvore temporária (`path` → bytes) e invoca **`zoekt-index -index <ZOEKT_INDEX_DIR> <tree_dir>`**, passando o nome do repositório pelas flags/opções **documentadas pelo binário oficial** (sem inventar protocolo).
3. `repository` e `commit` dos argumentos de `index(...)` são a fonte de verdade; ver invariante em D-T10-003.

**Otimização opcional (fora do Protocol, só construtor):** se `ZoektExactCodeIndex` for construído com um `workdir` Git já no tip `commit` (injetado por T14/factory), pode usar `zoekt-git-index` em vez de rematerializar `content`. T14 **não** depende disso: o contrato público permanece `files` + `content`.

**Proibido:** parser/escritor de shards `.zoekt` caseiro; HTTP inventado; gRPC como caminho default do MVP (existe no upstream, mas o contrato JSON documentado basta e é mais simples de doublear).

### D-T10-002 — Separação porta de domínio × client de transporte

| Superfície | Responsabilidade | Motivo da separação |
|---|---|---|
| `ExactCodeIndex` | Contrato de domínio estável para T14/T16 | Callers não conhecem HTTP, CLI, paths de shard nem flags |
| `ZoektSearchTransport` | `post_search(body) -> Mapping` (JSON oficial) | Isola URL, timeout, status HTTP; mockável |
| `ZoektIndexRunner` | `run(argv) -> CompletedProcess` (ou equivalente tipado) | Isola `subprocess`/PATH; mockável |
| `ZoektExactCodeIndex` | Orquestra modelos → argv/payload → modelos | Único lugar que conhece mapeamento Zoekt |

Injeção por construtor: `ZoektExactCodeIndex(search=…, indexer=…, index_dir=…, …)`.

### D-T10-003 — Modelos `FileToIndex` e `ExactMatch`

Imutáveis (`frozen=True`):

**`FileToIndex`**

| Campo | Tipo | Semântica |
|---|---|---|
| `repository` | `str` | Identificador estável do repo no produto (ex.: `org/repo` ou id de catálogo acordado com T14) |
| `path` | `str` | Caminho relativo no tip (POSIX-style no contrato; normalização no adaptador) |
| `commit` | `str` | SHA do tip sendo indexado |
| `content` | `bytes` | Conteúdo integral do arquivo no tip (ENG-012: arquivo inteiro) |

**Invariante `index(repository, commit, files)`:**

- Os argumentos `repository` e `commit` são canônicos.
- Cada `FileToIndex` deve ter `repository`/`commit` **iguais** aos argumentos; divergência → `ExactCodeIndexError` (entrada inválida, não falha de infra Zoekt — T14 não deve produzir isso).
- `workdir` **não** faz parte de `FileToIndex` nem do Protocol (ver D-T10-001 otimização de construtor).

**`ExactMatch`**

| Campo | Tipo | Semântica |
|---|---|---|
| `repository` | `str` | Repo do hit |
| `path` | `str` | Arquivo do hit |
| `commit` | `str` | Commit do tip indexado; se o shard não expuser SHA, o adaptador preenche com o `commit` da última indexação conhecida daquele `repository` (estado interno mínimo) ou, na busca filtrada, com `query`/`index` context — **nunca** string vazia em resultados de índice populado por esta porta |
| `snippet` | `str` | Trecho ao redor do match (`NumContextLines`) |

Campos auxiliares permitidos se úteis a T16 sem quebrar aceite: `line_number: int | None`. Não expor score/BM25 no contrato mínimo do MVP.

**`ExactSearchQuery`**

| Campo | Tipo | Semântica |
|---|---|---|
| `pattern` | `str` | Literal/substring a buscar (escape conforme query language Zoekt) |
| `repository` | `str \| None` | Filtro opcional `repo:` |
| `path_prefix` | `str \| None` | Filtro opcional `file:` / prefixo |
| `max_matches` | `int \| None` | Limite de resultados mapeado para `Opts` oficiais quando aplicável |
| `context_lines` | `int` | Default pequeno (ex.: 2) → `Opts.NumContextLines` |

### D-T10-004 — Erros tipados para T14

```text
ExactCodeIndexError(Exception)
  mensagem: operação + repository + commit? + razão tipada
  causa: __cause__ = exceção de transporte/subprocess quando houver
```

Subtipos **opcionais** (úteis, não obrigatórios se um tipo único + atributo `operation` bastar):

| Tipo / tag | Quando |
|---|---|
| `operation="index"` | CLI falhou, workdir inválido, binário ausente |
| `operation="search"` | HTTP/timeout/JSON |
| `operation="delete"` | limpeza de índice de repo (se exposta) |

Invariantes: mensagens **sem** tokens/segredos; podem citar URL host (sem query string sensível), exit code, status HTTP.

T14 trata qualquer `ExactCodeIndexError` como falha de etapa Zoekt → estado `erro` → restart do repositório inteiro.

### D-T10-005 — Fake/double injetável

`FakeExactCodeIndex` (mesmo Protocol):

- Armazena `dict[(repository, commit, path)] -> content` em memória.
- `index` upserta conteúdos; busca faz substring exata sobre `content`.
- `delete_repository` remove todas as entradas daquele `repository`.
- Pode ser configurado para levantar `ExactCodeIndexError` sob demanda (simular falha para T14).
- **Não** fala HTTP/CLI.

Testes unitários T10 usam fakes dos transportes **e** o fake da porta; BDD da task valida contrato da porta com fake (sem container Zoekt). Integração real Zoekt fica para T19/smoke opcional — fora do aceite mínimo T10.

### D-T10-006 — Remoção de paths (ENG-012) — handoff

Zoekt indexa por **repositório/shard**, não oferece API oficial de “delete path X” estável no fluxo JSON documentado.

**Decisão de escopo T10:**

- **Não** implementar `remove_paths` como operação de protocolo inventada sobre arquivos de shard.
- Contrato da porta inclui **reindexação do conjunto atual** como mecanismo de verdade: T14, após calcular diff (ENG-012), chama `index(repository, commit, files=eligible_files_at_tip)` de forma que o índice do repo passe a refletir só os arquivos elegíveis presentes. Paths removidos **deixam de existir** no novo índice porque o shard é regenerado a partir do conjunto/tip atual.
- **`delete_repository(repository: str) -> None` é obrigatório no Protocol** (restart BR-005 / T14): remove do `ZOEKT_INDEX_DIR` apenas os artefatos de índice cujo nome/associação ao `repository` foi definido na indexação por esta porta (ex.: shards gerados para aquele repo name). É limpeza de arquivos no diretório de índice — **sem** parse do formato binário interno dos shards. Ausência de artefatos = no-op sucesso. Falha de I/O → `ExactCodeIndexError`.

**Handoff explícito a T14:** orquestrador é dono de (1) lista de paths removidos no diff, (2) decisão de reindexar arquivo inteiro vs restart, (3) chamar `index` com o conjunto restante e/ou `delete_repository` + reindex full. T10 só garante que reindex/delete deixam o índice consistente.

## 5. Componentes

### 5.1 `ExactCodeIndex` (Protocol)

```text
index(repository: str, commit: str, files: Sequence[FileToIndex]) -> None
search(query: ExactSearchQuery) -> Sequence[ExactMatch]
delete_repository(repository: str) -> None
```

Comentários de responsabilidade (obrigatórios nas interfaces da task):

- **Responsabilidade:** abstrair indexação e busca exata de código para o produto.
- **Motivo da separação:** T14/T16 não devem acoplar a Zoekt; permite `FakeExactCodeIndex` e troca de backend oficial sem mudar orquestração/UI/MCP.

### 5.2 `ZoektSearchTransport`

- `post_search(body: Mapping[str, Any]) -> Mapping[str, Any]`
- Base URL: settings/config injetada (ver §5.5).
- Timeout configurável; erros de rede/HTTP → envelopados pela porta.

### 5.3 `ZoektIndexRunner`

- Executa argv da CLI oficial (`zoekt-git-index` / `zoekt-index`).
- Captura stdout/stderr para anexar razão tipada (truncada) em `ExactCodeIndexError`.
- Não interpreta formato de shard.

### 5.4 `ZoektExactCodeIndex`

- Implementação default da porta.
- Escape de `pattern` na query language Zoekt para busca literal (evitar que metacaracteres virem regex acidental — documentar estratégia na interface: preferir sintaxe literal oficial / quoting documentado).
- Mapeamento da resposta JSON oficial (`FileMatches` / lines / fragments) → `ExactMatch`.

### 5.5 Configuração / envs

`settings.py` (T01) **não** declara Zoekt hoje. T10 **não** precisa alterar a política de workers; documenta envs de infraestrutura para o adaptador e T19:

| Env | Obrigatória | Default sugerido | Uso |
|---|---|---|---|
| `ZOEKT_URL` | para busca real | `http://127.0.0.1:6070` | Base do `zoekt-webserver` (`/api/search`) |
| `ZOEKT_INDEX_DIR` | para indexação real | `/data/index` (container) ou path local de dev | Flag `-index` da CLI e volume do webserver |
| `ZOEKT_GIT_INDEX_BIN` | não | `zoekt-git-index` (PATH) | Override de binário |
| `ZOEKT_INDEX_BIN` | não | `zoekt-index` (PATH) | Override de binário |

**Decisão D-T10-007:** carregar essas envs via construtor/factory do adaptador (`ZoektExactCodeIndex.from_environ` ou parâmetros explícitos), **sem** expandir `AppSettings` de T01 nesta task, salvo se a review humana pedir unificação. Motivo: T01 é bootstrap de processo genérico; Zoekt é infra de domínio/indexação. T19 garante serviço + volume + `-rpc`.

Stdlib `urllib` ou client HTTP mínimo da stdlib/`http.client` para o POST JSON oficial é aceitável como **adaptador fino** (não é reinventar protocolo — o contrato é o JSON documentado). Alternativa: `httpx`/`requests` se já existirem no projeto; **não** adicionar dependência só por preferência sem necessidade. Preferência do design: **stdlib** para o POST, alinhado a “adaptador fino”.

## 6. Fluxo detalhado

### 6.1 Indexação (T14 → T10)

```text
1. T14 resolve tip main + arquivos elegíveis (T08/T09) com conteúdo integral.
2. T14 chama ExactCodeIndex.index(repository, commit, files).
3. Adaptador materializa tree (temp dir por repo/commit ou usa workdir Git).
4. Runner invoca CLI oficial → shards em ZOEKT_INDEX_DIR.
5. Sucesso: retorno void; T14 registra FileStage.ZOEKT por arquivo.
6. Falha: ExactCodeIndexError → T14 aborta repo.
```

### 6.2 Busca (T16 → T10)

```text
1. T16 monta ExactSearchQuery a partir da UI/MCP.
2. Adaptador compõe Q na query language oficial (+ repo:/file: se filtros).
3. Transport POST /api/search com Opts.NumContextLines.
4. Map → Sequence[ExactMatch] (determinístico: ordenar por repository, path, line).
5. T16/UI/MCP apresentam evidências (BDD-009 na ponta UI em T18).
```

### 6.3 Restart de repo (T14)

```text
ExactCodeIndexError ou política BR-005
  → delete_repository(repository)  # obrigatório no Protocol
  → reindex full do tip
```

## 7. Dados

| Dado | Onde vive | Persistência |
|---|---|---|
| Shards Zoekt | `ZOEKT_INDEX_DIR` (volume) | Disco do serviço Zoekt; descartável no MVP (plano rollback) |
| Metadados repo/path/commit/snippet | Dentro do índice Zoekt + mapeados em `ExactMatch` | Sem tabela PostgreSQL em T10 |
| Progresso etapa `zoekt` | Catálogo T03 (`FileStage.ZOEKT`) | T14 grava; T10 não toca catálogo |

Sem schema Alembic nesta task.

## 8. Erros

| Situação | Tipo | Comportamento |
|---|---|---|
| CLI exit ≠ 0 / timeout | `ExactCodeIndexError` | T14 restart repo |
| Binário não encontrado | `ExactCodeIndexError` | Idem; mensagem cita nome do bin |
| HTTP connection error / 5xx / 4xx | `ExactCodeIndexError` | Idem |
| Corpo JSON inesperado | `ExactCodeIndexError` | Idem |
| `files` vazio em `index` | no-op sucesso **ou** erro explícito — preferir **no-op sucesso** se T14 só chama com elegíveis; documentar na interface | — |
| `pattern` vazio em `search` | `ExactCodeIndexError` ou lista vazia — preferir **lista vazia** (busca sem termo não é falha de infra) | — |

## 9. Segurança

- Sem tokens GitHub nesta camada.
- Não logar conteúdo integral de arquivos em nível INFO; erros podem citar path/repo/commit.
- `ZOEKT_URL` é infra local (DEC-007); sem credenciais no MVP.
- Temp dirs de indexação com permissões de usuário do processo; limpeza best-effort após CLI ok.

## 10. Compatibilidade

- Windows / macOS / Linux first-class: paths via `pathlib`; subprocess com lista de args (nunca shell string).
- Dev local: binários no PATH **ou** só `FakeExactCodeIndex` nos testes.
- Container T19: imagem `ghcr.io/sourcegraph/zoekt` (ou pin documentado), `zoekt-webserver -rpc -index /data/index`, app aponta `ZOEKT_URL` / `ZOEKT_INDEX_DIR`.
- Não altera contratos T01–T09.
- Handoff: `ExactCodeIndex` → T14, T16.

## 11. Observabilidade

- Erros tipados com `operation`, `repository`, `commit` (quando houver).
- Sem métricas obrigatórias no MVP.
- Opcional: log DEBUG de argv da CLI (sem conteúdo de arquivo) e status HTTP.

## 12. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Zoekt só reindexa bem em unidade repo/shard | D-T10-006: reindex do conjunto tip; T14 orquestra ENG-012 |
| Commit ausente em metadados de `zoekt-index` | Adaptador mantém mapa mínimo `repository → commit` da última `index` bem-sucedida para preencher `ExactMatch.commit` (D-T10-003) |
| Webserver sem `-rpc` | T19 deve ligar `-rpc`; erro tipado se `/api/search` indisponível |
| Diferença de query language (regex vs literal) | Documentar escape/quoting na interface; testes de canto com metacaracteres |
| Dependência de binário no host de dev | Fake default nos testes; CLI só em integração/T19 |
| Ambiguidade de `repository` string vs UUID catálogo | Contrato: string estável acordada com T14 (full_name ou id); um único formato por instalação |

## 13. Rollback

- Remover implementação sob `index/zoekt/` exceto placeholder; manter Protocol/fake se já consumidos — em greenfield T10, reverter a branch da task.
- Volumes Zoekt descartáveis; sem migração PostgreSQL.
- Sem force-push; merge só após gates do pipeline.

## 14. Critérios de aceite mapeados

| Aceite da task | Design |
|---|---|
| Indexação bem-sucedida torna conteúdo pesquisável (BDD-009) | `index` + `search` via CLI/HTTP oficiais; fake cobre contrato nos testes |
| Falhas propagam erro tipado para T14 | `ExactCodeIndexError` (D-T10-004) |
| Testes com double/fake | `FakeExactCodeIndex` + transports fake (D-T10-005) |
| Adaptador fino oficial (DEC-016 / BDD-024) | D-T10-001 — sem formato/protocolo proprietário |
| Metadados repo/path/commit/snippet | `ExactMatch` (D-T10-003) |

## 15. Arquivos previstos

- `src/github_rag/index/zoekt/__init__.py` — reexports públicos
- `src/github_rag/index/zoekt/models.py` — `FileToIndex`, `ExactMatch`, `ExactSearchQuery`
- `src/github_rag/index/zoekt/errors.py` — `ExactCodeIndexError`
- `src/github_rag/index/zoekt/port.py` — Protocol `ExactCodeIndex`
- `src/github_rag/index/zoekt/client.py` — `ZoektSearchTransport` (HTTP oficial)
- `src/github_rag/index/zoekt/runner.py` — `ZoektIndexRunner` (CLI oficial)
- `src/github_rag/index/zoekt/index.py` — `ZoektExactCodeIndex`
- `src/github_rag/index/zoekt/fake.py` — `FakeExactCodeIndex`
- `tests/unit/index/zoekt/...`
- `tests/bdd/...` (cenários da task)
- Artefatos em `spec/.../tasks/T10-zoekt-adapter/`

## 16. Fora de escopo (confirmação)

- Tree-sitter / Qdrant / SLM.
- MCP tools e UI de busca (T16/T17/T18).
- `docker-compose` serviço `zoekt` (T19) — apenas contrato de envs/flags.
- Orquestração ENG-012 / restart (T14), além do handoff D-T10-006.
- gRPC Zoekt como API default.
- Alteração de `AppSettings` T01 (salvo pedido HITL).

## 17. Ambiguidade / SCOPE_CHANGE

Nenhuma ambiguidade que **exija** `SCOPE_CHANGE` para produzir interfaces/BDD desta task. Pontos de alinhamento (não bloqueantes do design):

1. Formato canônico de `repository` (full_name vs UUID do catálogo) — fechar com T14 na interface; default sugerido: o mesmo identificador que T14 já usa no orquestrador.
2. Unificar `ZOEKT_*` em `AppSettings` vs factory local — D-T10-007 escolhe factory local; mudar isso não é mudança de requisito de produto.
3. Se a review humana exigir `remove_paths` na porta apesar de D-T10-006, isso seria **expansão de contrato** (ainda implementável como reindex filtrado), não mudança de REQ/BDD aprovados.
