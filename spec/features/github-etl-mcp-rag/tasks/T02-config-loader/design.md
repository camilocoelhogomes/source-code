# Design — T02-config-loader

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T02-config-loader` |
| Autor | Implementation Task Runner (candidato); corrigido por Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.2.0` |
| Branch | `feature/github-etl-mcp-rag-T02-config-loader` |
| Base | `main` (T01 mesclado) |
| Rastreabilidade | REQ-009, REQ-039–042; BR-016–022; DEC-012, DEC-014; BDD-021 (parcial), BDD-022; BDD-014 (parcial) |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` → corrigido → `APPROVED_BY_ARCHITECT` | `0.1.0` → `0.2.0` | Ver `reviews.md` (M-01..M-05). Aprovação Architect substitui gate humano (autonomous pipeline). |

## 1. Contexto

T01 entregou bootstrap de processo (`AppSettings.config_path: Path | None`, sem I/O de arquivo). T02 carrega e valida **integralmente** o JSON Sourcebot-like apontado por esse path, produzindo um modelo tipado de conexões para T05/T06 — sem descoberta de repos, sem I/O GitHub/disco além da leitura do arquivo de config, e sem cadastro parcial.

## 2. Problema

O processo precisa, na inicialização:

1. Obter o path do arquivo a partir de `AppSettings.config_path` (T01; **não** reler `CONFIG_PATH` do ambiente no loader).
2. Ler e parsear JSON.
3. Validar o objeto `connections` (tipos `github` e `git`, campos obrigatórios, wildcards de inclusão, `file://` + glob).
4. Resolver referências `{ "env": "VAR" }` para tokens sem embutir o valor no JSON e sem vazar o segredo em erros/logs.
5. Em qualquer falha: rejeitar 100% — zero conexões aplicadas parcialmente (BR-021).

## 3. Solução proposta

Módulo `github_rag.config` com três responsabilidades separadas:

| Componente | Papel |
|---|---|
| `schema` | Modelos tipados imutáveis (`AppConfig`, `GitHubConnection`, `GitConnection`, refs de segredo) |
| `secrets` | Porta `SecretResolver`: nome de env → valor; nunca loga/retorna valor em mensagens de erro |
| `loader` | Porta `ConfigLoader`: lê path → valida schema → resolve segredos → retorna `AppConfig` ou falha total |

Fluxo feliz:

```text
AppSettings.config_path (Path) → Path.read_text(encoding="utf-8") → json.loads
  → validar raiz: "connections" presente e é objeto (dict)
  → connections vazio {} é válido → AppConfig(connections={})
  → para cada conexão nomeada: discriminar type
      github → orgs, repos (inclusão/wildcards), token.env, revisions.branches
      git    → url file:// (+ glob opcional), revisions.branches
  → SecretResolver.resolve(token.env) para cada github
  → AppConfig(connections=...) imutável
```

Fluxo de erro (qualquer etapa):

```text
falha → ConfigLoadError (mensagem sem valor de segredo) → não retorna AppConfig
```

### 3.1 Escopo BDD nesta task

| Cenário | Cobertura T02 | Fora de T02 |
|---|---|---|
| BDD-021 | Arquivo válido → todas as conexões nomeadas carregadas em modelo tipado (`AppConfig`) | Descoberta de repositórios e identificação de origem na UI/catálogo (T05/T06/T07) |
| BDD-022 | Path ausente/inexistente/JSON inválido/conexão inválida/`env` inexistente → rejeição total, sem conexões parciais, sem vazamento de segredo | Boot de container / messaging de UI (T19/T18) |
| BDD-014 (parcial) | Valor do token ausente de `str(exc)` / mensagens geradas por loader/resolver | Logs UI/MCP (T17/T18) |

## 4. Componentes

### 4.1 `ConfigLoader`

- Entrada: `Path | None`. `None` (ou caller sem path) → `ConfigLoadError` com mensagem “CONFIG_PATH ausente” (ou equivalente sem segredo).
- Saída de sucesso: somente `AppConfig` completo (todas as conexões válidas e segredos resolvidos).
- Erros: path inexistente/inacessível, JSON inválido, schema inválido, tipo desconhecido, `env` inexistente/vazio — sempre via exceção; **nunca** retorna mapa parcial.
- Não descobre repos; não chama GitHub; não varre disco além do arquivo de config.
- Não relê variáveis de workers nem reimplementa `load_settings` (T01).

### 4.2 `SecretResolver`

- Entrada: nome da variável (`str` não-vazio / não-blank).
- Saída: valor (`str`) se presente e não-blank no ambiente (ou `Mapping` injetável).
- Erros: nome blank, variável ausente ou valor blank → erro tipado **citando só o nome**, nunca o valor.
- Implementação default: lê `os.environ` (ou `Mapping` injetável para testes).

### 4.3 Schema / modelos

- `AppConfig`: mapa nome → conexão discriminada (`github` | `git`). Imutável após construção.
- `GitHubConnection`: `type="github"`, `orgs: list[str]`, `repos: list[str]`, `token: EnvSecretRef` (+ acesso ao segredo resolvido via `ResolvedSecret` opaco), `revisions: Revisions`.
- `GitConnection`: `type="git"`, `url: str`, `revisions: Revisions`.
- `EnvSecretRef`: `{ env: str }` — só o nome (não-blank).
- `Revisions`: `branches: list[str]`.
- Nomes de conexão: únicos (chave do objeto JSON); não-vazios / não-blank.

#### Regras de validação de campos (obrigatórias em T02)

| Campo | Regra |
|---|---|
| `connections` | Obrigatório; tipo objeto. `{}` válido. |
| Nome da conexão | String não-vazia / não-blank. |
| `type` | Obrigatório; somente `"github"` ou `"git"`. Outro valor → erro. |
| `orgs` (github) | Lista obrigatória; **não-vazia**; cada item string não-blank. |
| `repos` (github) | Lista obrigatória; pode ser vazia (nenhuma inclusão). Cada item string não-blank; `*` permitido (inclusão — BR-022 / DEC-014). Expansão = T05. |
| `token` (github) | Objeto obrigatório na forma `{ "env": "<NOME>" }` com NOME não-blank. String literal ou outros formatos → erro. |
| `url` (git) | String obrigatória; ver §4.4. |
| `revisions` | Objeto obrigatório em github e git. |
| `revisions.branches` | Lista obrigatória, não-vazia; cada item string não-blank. **Deve conter `"main"`** (decisão de engenharia T02 / ENG-T02-001: fail-fast alinhado ao MVP que só indexa `main`; extras aceitos e ignorados até T08+). Ausência de `main` → `ConfigLoadError`. |
| Chaves top-level além de `connections` | Ignoradas (compatibilidade Sourcebot-like; não são fonte de conexões). |
| Campos desconhecidos dentro de uma conexão | Ignorados na v0 (não quebram parse); campos obrigatórios acima continuam exigidos. |

**ENG-T02-001:** Exigir `"main"` em `branches` não deriva de REQ-013 (REQ-013 regula o que o pipeline indexa). É validação antecipada do contrato MVP neste loader.

### 4.4 Wildcards e `file://`

- **GitHub `repos`:** exclusivamente inclusão (BR-022). Validação T02: forma de string; pode conter `*`. Expansão contra API GitHub = T05.
- **Git `url`:**
  - Deve usar esquema `file://` (case-sensitive prefix `file://`).
  - Path após o esquema deve ser **absoluto** (não relativo).
  - Formas absolutas aceitas (string; sem I/O de existência):
    - POSIX: `file:///repos`, `file:///repos/*`, `file:///repos/my-org/*`
    - Windows (dev local first-class, alinhado T01): `file:///C:/repos`, `file:///C:/repos/*`, `file:///C:/repos/my-org/*` (drive letter após `file:///`)
  - Glob `*` no path permitido. Expansão / existência de volume = T06.
  - Rejeitar: ausência de `file://`, path vazio, path relativo (ex.: `file://repos`, `file://./repos`).

## 5. Fluxo de dados

| Etapa | Dados | Persistência |
|---|---|---|
| Input | `Path` de `AppSettings.config_path` | FS (somente leitura do arquivo de config) |
| Parse | `dict` bruto | memória |
| Validação | modelos tipados (token ainda como `EnvSecretRef`) | memória |
| Resolução | token materializado como `ResolvedSecret` opaco (não serializado para logs/repr) | memória |
| Output | `AppConfig` | retornado ao caller; sem escrita |

**Segurança de segredo:**

- `__repr__` / `__str__` de `ResolvedSecret` e de objetos de conexão **não** incluem o valor do token.
- Mensagens de `ConfigLoadError` citam conexão, campo e nome da env — **nunca** o valor.
- Preferir manter o valor acessível só via API explícita do `ResolvedSecret` (ex.: `.get_value()`), não em campos públicos triviais de dataclass sem redaction.
- Testes BDD-014 parciais cobrem ausência do valor em `str(exc)` / mensagens.

## 6. Erros

| Condição | Código/tipo sugerido | Mensagem (sem segredo) | Parcial? |
|---|---|---|---|
| `CONFIG_PATH` ausente (`None`) | `ConfigLoadError` | path ausente | não |
| Arquivo inexistente / sem permissão | `ConfigLoadError` | path + razão I/O | não |
| JSON malformado | `ConfigLoadError` | parse error (sem dump do arquivo) | não |
| Raiz sem `connections` ou tipo errado | `ConfigLoadError` | schema | não |
| Nome de conexão vazio/blank | `ConfigLoadError` | schema | não |
| `type` ausente/desconhecido | `ConfigLoadError` | conexão + type | não |
| `orgs` ausente/vazio/item inválido | `ConfigLoadError` | conexão + orgs | não |
| `repos` ausente ou item inválido | `ConfigLoadError` | conexão + repos | não |
| `revisions` / `branches` inválidos ou sem `main` | `ConfigLoadError` | conexão + revisions | não |
| `token` não é `{ "env": "..." }` / env blank | `ConfigLoadError` | conexão + token | não |
| `env` ausente/blank no ambiente | `ConfigLoadError` | conexão + nome da env | não |
| URL `git` sem `file://` absoluto válido | `ConfigLoadError` | conexão + url | não |

Invariante: **nenhum** caminho de erro retorna lista/mapa parcial de conexões válidas. Estratégia: fail-fast na primeira falha **ou** validar tudo e falhar sem montar `AppConfig` — desde que o retorno de erro nunca exponha subset aplicável.

## 7. Segurança

- BR-008 / BR-019 / BDD-014 (parcial T02): valor do token nunca em exceções/logs gerados pelo loader/resolver.
- JSON nunca contém o valor do token (REQ-041) — apenas `{ "env": "..." }`.
- Sem telemetria externa nesta task.

## 8. Compatibilidade

- Paths do arquivo de config via `pathlib.Path` (Windows / macOS / Linux first-class, herdado de T01).
- Leitura: `Path.read_text(encoding="utf-8")` + `json.loads`.
- URLs `file://` com formas POSIX e Windows (§4.4); validação só de forma, sem resolver FS.
- Sem dependência de shell; OS-agnostic.
- Dependência de runtime: stdlib apenas (`json`, `os`, `pathlib`, `dataclasses`/`typing`). Sem novas deps de produção em T02.

## 9. Observabilidade

- Erros estruturados via exceção tipada (mensagem humana).
- Sem logger obrigatório em T02; se houver logger futuro, deve reutilizar a mesma política de redaction (fora de escopo agora).

## 10. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Schema instável quebra T05/T06 | Contratos em `interfaces.md` versionados; modelos imutáveis |
| Vazamento de token em `repr` | Testes explícitos; `ResolvedSecret` opaco / redaction em `__repr__`/`__str__` |
| Validação excessiva (descoberta) | T02 só valida forma; expansão wildcard/`file://` em T05/T06 |
| Aceitar config parcial por “best effort” | Sem montagem de `AppConfig` em erro; sem retorno parcial |
| Overscape de BDD-021 | §3.1 limita T02 ao carregamento tipado |

## 11. Rollback

Greenfield: reverter o merge do PR desta branch. Sem migração de dados.

## 12. Fora de escopo (explícito)

- Chamadas GitHub; varredura de disco; persistência PostgreSQL; UI.
- Política de workers (T04); sync de catálogo (T07).
- Validação de existência de volumes montados (T06).
- Identificação de origem na UI / descoberta de repos (BDD-021 restante).

## 13. Definição de pronto (design)

- Architect aprova este design (`APPROVED_BY_ARCHITECT`) — **cumprido** em v0.2.0.
- Próximo gate: `bdd.md` cobrindo BDD-021 (parcial §3.1), BDD-022 e proteção de token no loader (BDD-014 parcial).
