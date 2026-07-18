# Interfaces — T02-config-loader

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T02-config-loader` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.2.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T02-config-loader` |
| Escopo desta etapa | Contratos de carga/validação do JSON de conexões **somente** |
| Modo | Autonomous — aprovação Architect substitui HITL |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | candidato → `APPROVED_BY_ARCHITECT` | `0.1.0` | Auto-review sem BLOCKING/MAJOR; ver `reviews.md` |

## 1. Escopo e exclusões

### Em escopo (T02)

| Contrato | Módulo | Papel |
|---|---|---|
| `AppConfig`, `GitHubConnection`, `GitConnection`, `EnvSecretRef`, `Revisions`, `ResolvedSecret` | `src/github_rag/config/schema.py` | Modelos tipados imutáveis do JSON Sourcebot-like |
| `SecretResolver`, `SecretResolutionError` | `src/github_rag/config/secrets.py` | Resolução nome de env → valor (sem vazar valor) |
| `ConfigLoader`, `ConfigLoadError` | `src/github_rag/config/loader.py` | Ler path → validar → resolver segredos → `AppConfig` ou falha total |
| Re-exports públicos | `src/github_rag/config/__init__.py` | Superfície BDD: `AppConfig`, `ConfigLoadError`, `ConfigLoader`, `GitConnection`, `GitHubConnection` |

### Fora de escopo (não declarar em T02)

| Item | Dono |
|---|---|
| `AppSettings` / `load_settings` / reler `CONFIG_PATH` do env | T01 (fronteira consumida, não reimplementada) |
| Descoberta de repos / expansão de wildcards contra API | T05 |
| Expansão / existência de volumes `file://` | T06 |
| Política de workers | T04 |
| Persistência, UI, MCP, logs estruturados | T07+ / T17–T19 |
| Implementação real do loader (parse/validação/I/O) | Developer (pós unitários aprovados) |
| Testes unitários de contrato | QA (próximo gate) |

### Fronteira explícita com T01

```text
load_settings() → AppSettings.config_path: Path | None
                         │
                         ▼
              ConfigLoader.load(path)   ← NÃO relê CONFIG_PATH / INDEX_* / QUERY_*
```

O caller (futuro boot) passa `AppSettings.config_path`. O loader **não** chama `load_settings` e **não** lê `ENV_CONFIG_PATH`.

## 2. Decisões de contrato

| ID | Decisão | Motivo |
|---|---|---|
| I-T02-001 | Pacote `github_rag.config` com `schema` / `secrets` / `loader` | Design §3; separação de responsabilidades |
| I-T02-002 | `ConfigLoader` é classe instanciável (`ConfigLoader().load(path)`) | BDD CFG-01..14; porta única de entrada |
| I-T02-003 | `ConfigLoader.__init__(secret_resolver: SecretResolver \| None = None)` | Default lê `os.environ` via resolver interno; injeção testável sem obrigar o BDD a passar kwargs |
| I-T02-004 | `load(path: Path \| None) -> AppConfig` | Path vem do caller; `None` → `ConfigLoadError` |
| I-T02-005 | Falhas de `load` → sempre `ConfigLoadError` (nunca retorno parcial) | BR-021; BDD CFG-05..12 |
| I-T02-006 | `SecretResolver.resolve(env_name) -> str`; falhas → `SecretResolutionError` | Isola I/O de env; redaction no resolver |
| I-T02-007 | `ConfigLoader` traduz `SecretResolutionError` → `ConfigLoadError` (mensagem sem valor) | Callers/BDD só tratam `ConfigLoadError`; nome da env pode ser citado |
| I-T02-008 | Modelos imutáveis após construção; `connections` é mapa nome → união discriminada | Design §4.3; BDD isinstance + atributos |
| I-T02-009 | `ResolvedSecret` opaco: valor só via `.get_value()`; `__str__`/`__repr__` redigidos | BDD-014 / CFG-13–14; BR-008 / BR-019 |
| I-T02-010 | `GitHubConnection.token` permanece `EnvSecretRef` (só nome); segredo resolvido em `GitHubConnection.secret: ResolvedSecret` | Separar referência declarada no JSON do valor materializado |
| I-T02-011 | `file://` validação só de forma (POSIX + Windows `file:///C:/...`); sem I/O de volume | Design §4.4; CFG-04/11 |
| I-T02-012 | `revisions.branches` deve conter `"main"` (ENG-T02-001) | Fail-fast MVP; CFG-12 |
| I-T02-013 | Stdlib only; stubs Protocol/`...` nesta etapa | Alinhado ao gate T01 (I-T01-010); sem lógica real |
| I-T02-014 | Export público mínimo no `__init__` alinhado ao BDD; demais símbolos exportáveis para unitários | CFG imports; SecretResolver/ResolvedSecret disponíveis no pacote |

## 3. Mapa de módulos

| Arquivo | Responsabilidade | Motivo da separação |
|---|---|---|
| `schema.py` | Tipos de dados do config (sem I/O) | Schema tipado independente de FS/env |
| `secrets.py` | Porta e erro de resolução de segredo | Política de redaction isolada do parser |
| `loader.py` | Orquestra leitura + validação + resolução | Único ponto de falha total / sucesso completo |
| `__init__.py` | Re-exports da superfície pública | BDD e callers importam `github_rag.config` |

## 4. Contratos detalhados

### 4.1 `EnvSecretRef`

**Responsabilidade:** representar a referência `{ "env": "<NOME>" }` declarada no JSON — somente o nome da variável, nunca o valor.

**Motivo da separação:** o JSON Sourcebot-like não embute tokens (REQ-041); o modelo tipado preserva essa fronteira até a resolução.

**Propriedades:**

| Propriedade | Tipo | Invariantes |
|---|---|---|
| `env` | `str` | Não-vazio / não-blank após validação |

**Erros:** construção/validação inválida ocorre no loader → `ConfigLoadError` (conexão + token).

**Segurança:** `__str__`/`__repr__` podem citar o nome; nunca um valor de segredo.

---

### 4.2 `ResolvedSecret`

**Responsabilidade:** encapsular o valor materializado do token de forma opaca, com acesso explícito via API.

**Motivo da separação:** evita campos públicos triviais em dataclasses que vazam em `repr`/`str` (BDD-014 / CFG-14).

**API:**

```python
class ResolvedSecret(Protocol):
    def get_value(self) -> str: ...
```

**Invariantes:**

- `get_value()` devolve o valor resolvido (não-blank) após carga ok.
- `__str__` e `__repr__` **não** incluem o valor (redaction fixa, ex. `"***"` / `"<redacted>"`).
- Não serializar o valor em logs gerados por este tipo.

**Erros:** o Protocol não levanta; falha de resolução ocorre antes, em `SecretResolver` / `ConfigLoader`.

---

### 4.3 `Revisions`

**Responsabilidade:** modelar `revisions.branches` obrigatório de cada conexão.

**Motivo da separação:** regra ENG-T02-001 (`"main"` obrigatório) e validação de lista ficam no mesmo tipo reutilizado por github e git.

**Propriedades:**

| Propriedade | Tipo | Invariantes |
|---|---|---|
| `branches` | `Sequence[str]` (exposto tipicamente como lista imutável) | Lista não-vazia; cada item string não-blank; **deve conter** `"main"` |

**Erros:** ausência de `main`, lista vazia/itens blank → `ConfigLoadError` (conexão + revisions).

---

### 4.4 `GitHubConnection`

**Responsabilidade:** conexão discriminada `type="github"` tipada e imutável após carga ok.

**Motivo da separação:** campos e regras distintos de `GitConnection` (orgs/repos/token vs url `file://`); callers usam isinstance/discriminação sem dicts brutos.

**Propriedades:**

| Propriedade | Tipo | Invariantes |
|---|---|---|
| `type` | `Literal["github"]` | Sempre `"github"` |
| `orgs` | `Sequence[str]` | Lista não-vazia; itens não-blank |
| `repos` | `Sequence[str]` | Lista obrigatória; pode ser vazia; itens não-blank; `*` permitido (forma; sem expansão) |
| `token` | `EnvSecretRef` | Nome da env (não-blank) |
| `secret` | `ResolvedSecret` | Valor resolvido; redacted em str/repr |
| `revisions` | `Revisions` | Contém `"main"` |

**Invariantes de superfície (BDD):** `str`/`repr` da conexão **não** contêm o valor do token.

**Erros:** validação no loader → `ConfigLoadError`.

**Fora de escopo:** chamada à API GitHub; expansão de wildcards (T05).

---

### 4.5 `GitConnection`

**Responsabilidade:** conexão discriminada `type="git"` tipada e imutável após carga ok.

**Motivo da separação:** URL `file://` e ausência de token/orgs/repos; evita misturar regras com github.

**Propriedades:**

| Propriedade | Tipo | Invariantes |
|---|---|---|
| `type` | `Literal["git"]` | Sempre `"git"` |
| `url` | `str` | Prefixo `file://` (case-sensitive); path absoluto (POSIX ou Windows `file:///C:/...`); glob `*` permitido na forma |
| `revisions` | `Revisions` | Contém `"main"` |

**Rejeições de `url` (forma):** sem `file://`; path vazio; relativo (`file://repos`, `file://./repos`); outros esquemas (`https://...`).

**Fora de escopo:** existência do volume / expansão de glob (T06).

---

### 4.6 `AppConfig`

**Responsabilidade:** snapshot imutável do arquivo de config válido — mapa completo nome → conexão discriminada.

**Motivo da separação:** único tipo de sucesso do loader; consumidores (T05/T06) não dependem de dict JSON bruto.

**Propriedades:**

| Propriedade | Tipo | Invariantes |
|---|---|---|
| `connections` | `Mapping[str, GitHubConnection \| GitConnection]` | Chaves = nomes não-blank; `{}` válido; **nunca** parcial |

**Invariantes:**

- Só existe após validação + resolução completas.
- `str`/`repr` não contêm valores de segredo (delegam redaction das conexões/`ResolvedSecret`).

**Erros:** o tipo não levanta; falhas impedem sua construção.

---

### 4.7 `SecretResolver`

**Assinatura:**

```python
class SecretResolver(Protocol):
    def resolve(self, env_name: str) -> str: ...
```

**Responsabilidade:** resolver nome de variável de ambiente → valor string presente e não-blank.

**Motivo da separação:** concentra política BR-008/BR-019 (nunca logar/retornar valor em mensagens de erro) fora do parser JSON; permite `Mapping` injetável em testes unitários sem acoplar o schema ao `os.environ`.

**Invariantes:**

- `env_name` não-blank; caso contrário → `SecretResolutionError` citando razão de nome inválido (**sem** valor).
- Variável ausente ou valor blank → `SecretResolutionError` citando **somente o nome**.
- Implementação default: lê `os.environ` ou `Mapping[str, str]` injetado no construtor concreto.
- Não muta o mapping/ambiente.

**Erros:**

| Condição | Tipo | Mensagem |
|---|---|---|
| nome blank | `SecretResolutionError` | nome inválido / blank (sem valor) |
| env ausente ou blank | `SecretResolutionError` | cita o nome da env; **nunca** o valor |

---

### 4.8 `SecretResolutionError`

**Responsabilidade:** falha tipada da resolução de segredo no nível do resolver.

**Motivo da separação:** distinguir erro de env/segredo de erro de schema/I/O; facilita testes unitários do resolver; o loader traduz para `ConfigLoadError` na API pública de `load`.

**Invariantes:**

- Subclasse de `Exception`.
- Mensagem cita nome da env / razão; **nunca** o valor do segredo.

---

### 4.9 `ConfigLoader`

**Assinatura:**

```python
class ConfigLoader:
    def __init__(
        self,
        secret_resolver: SecretResolver | None = None,
    ) -> None: ...

    def load(self, path: Path | None) -> AppConfig: ...
```

**Responsabilidade:** orquestrar leitura do arquivo (`Path.read_text(encoding="utf-8")` + `json.loads`), validar schema (design §4.3–4.4), resolver tokens github via `SecretResolver`, devolver `AppConfig` completo ou falhar total.

**Motivo da separação:** único ponto de entrada do domínio de config; isola I/O de arquivo + validação + resolução; não mistura com bootstrap T01 nem descoberta T05/T06.

**Invariantes:**

- `secret_resolver is None` → usa implementação default baseada em `os.environ`.
- `path is None` → `ConfigLoadError` (CONFIG_PATH ausente / path ausente).
- Sucesso ⇒ `AppConfig` com **todas** as conexões válidas e segredos resolvidos.
- Qualquer falha ⇒ `ConfigLoadError`; **nunca** retorna mapa/lista parcial (BR-021).
- Não relê `CONFIG_PATH` / workers; não chama GitHub; não varre disco além do arquivo de config.
- Chaves top-level além de `connections`: ignoradas.
- Campos desconhecidos dentro de uma conexão: ignorados na v0; obrigatórios continuam exigidos.
- `SecretResolutionError` capturada/traduzida → `ConfigLoadError` (mensagem pode citar conexão + nome da env; sem valor).

**Erros (sempre `ConfigLoadError`):** ver design §6 (path, I/O, JSON, schema, type, orgs/repos/token/revisions/url, env ausente/blank).

**Segurança:** mensagens sem valor de segredo; sem dump completo do arquivo como se fosse segredo.

---

### 4.10 `ConfigLoadError`

**Responsabilidade:** falha total de carga/validação/resolução do arquivo de conexões.

**Motivo da separação:** distinta de `SettingsBootstrapError` (T01) e de `SecretResolutionError` (nível resolver); callers tratam um único tipo na borda do loader.

**Invariantes:**

- Subclasse de `Exception`.
- Mensagem: path/conexão/campo/nome de env + razão; **nunca** valor de token; sem dump integral do arquivo como segredo.
- Pode encapsular (`from`) `SecretResolutionError` ou erros de I/O/JSON sem expor segredos.

## 5. Declaração em código (sem implementação)

| Arquivo | Conteúdo permitido nesta etapa |
|---|---|
| `schema.py` | Protocols/`...` + docstrings de responsabilidade/motivo; tipos de dados sem parse |
| `secrets.py` | `SecretResolutionError`, `SecretResolver` (Protocol), stub concreto default com corpo `...` |
| `loader.py` | `ConfigLoadError`, `ConfigLoader` com `__init__`/`load` em `...` |
| `__init__.py` | Re-exports públicos alinhados ao BDD (+ símbolos auxiliares do contrato) |

**Proibido nesta etapa:** `json.loads` real, validação de schema, leitura de arquivo, resolução real de env, testes unitários, descoberta de repos.

Stubs permanecem superfície de contrato até o Developer (pós unitários aprovados). Imports do BDD deixam de falhar por `ImportError`; comportamento de carga permanece red (`load` não implementado).

## 6. Fluxo de uso (conceitual)

```text
AppSettings.config_path ──► ConfigLoader.load(path)
                                 │
                    path is None ─┴─► ConfigLoadError
                                 │
                          read_text + json.loads
                                 │
                          validar connections
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
         GitHubConnection   GitConnection      erro schema
              │                  │                  │
     SecretResolver.resolve      │                  ▼
              │                  │           ConfigLoadError
              ▼                  │
       ResolvedSecret            │
              │                  │
              └────────┬─────────┘
                       ▼
                  AppConfig  (imutável, completo)
```

## 7. Superfície pública vs BDD

| Símbolo | Export em `github_rag.config` | Usado pelo BDD |
|---|---|---|
| `ConfigLoader` | sim | sim |
| `ConfigLoadError` | sim | sim |
| `AppConfig` | sim | sim |
| `GitHubConnection` | sim | sim |
| `GitConnection` | sim | sim |
| `SecretResolver` | sim | não (indireto via env) |
| `SecretResolutionError` | sim | não |
| `EnvSecretRef` | sim | não (atributos via conexão) |
| `Revisions` | sim | indireto (`revisions.branches`) |
| `ResolvedSecret` | sim | indireto (redaction str/repr) |

## 8. Critérios de pronto (interfaces)

- [x] Contratos com responsabilidade + motivo da separação em cada tipo
- [x] Alinhado a design 0.2.0 e BDD 0.1.0 (CFG-01..14)
- [x] Fronteira T01 explícita (não relê env de bootstrap)
- [x] `ConfigLoadError` + `SecretResolutionError` com política de redaction
- [x] Stubs mínimos exportados; sem lógica real do loader
- [x] Auto-review Architect → `APPROVED_BY_ARCHITECT`
