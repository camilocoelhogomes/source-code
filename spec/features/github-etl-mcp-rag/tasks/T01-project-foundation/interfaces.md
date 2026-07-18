# Interfaces — T01-project-foundation

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T01-project-foundation` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `CANDIDATE_FOR_HUMAN_APPROVAL` |
| Versão | `0.1.0` |
| Design base | `0.2.0` (`HUMAN_DESIGN_APPROVED`) |
| BDD base | `0.2.0` (`HUMAN_BDD_APPROVED`) |
| Branch | `feature/github-etl-mcp-rag-T01-project-foundation` |
| Commit de referência | `db80db7` |
| Escopo desta etapa | Contratos de comunicação/bootstrap de T01 **somente** |

## 1. Escopo e exclusões

### Em escopo (T01)

| Contrato | Módulo | Papel |
|---|---|---|
| Nomes/defaults de env bootstrap | `src/github_rag/settings.py` | Constantes de contrato |
| `AppSettings` | `src/github_rag/settings.py` | Snapshot tipado somente-leitura |
| `load_settings` | `src/github_rag/settings.py` | Função de carga a partir do ambiente do processo |
| `SettingsBootstrapError` | `src/github_rag/settings.py` | Erro de bootstrap (conversão inválida) |

### Fora de escopo (não declarar em T01)

| Item | Dono |
|---|---|
| `ConfigLoader`, schema Sourcebot, validação JSON | T02 |
| `SecretResolver` / `{ "env": "..." }` | T02 |
| Portas de domínio do plano §2 (catálogo, snapshot, indexação, MCP, UI, etc.) | T03+ |
| Validação de existência/leitura de arquivo em `CONFIG_PATH` | T02 |
| Política de máximos/limites de workers em runtime de produto | T04 |
| Placeholders de conexão PostgreSQL / Qdrant / Zoekt / SLM como API tipada | T03 / T10–T13 / T19 |
| `pyproject.toml`, README, layout completo de pacotes, testes unitários | gates seguintes / Developer |

Nenhuma porta de domínio entra no código de T01 (design §3; handoff da task).

## 2. Decisões de contrato (HITL)

| ID | Decisão | Motivo |
|---|---|---|
| I-T01-001 | Nome do tipo de snapshot: `AppSettings` (Protocol) | Evita colisão com o módulo `settings`; alinhado ao design §3 |
| I-T01-002 | Função canônica de carga: `load_settings` | Superfície única e testável; sem classe loader nem DI nesta task |
| I-T01-003 | Atributos tipados em `snake_case`: `index_workers`, `query_workers`, `config_path` | Convenção Python; nomes de **env** permanecem `INDEX_WORKERS`, `QUERY_WORKERS`, `CONFIG_PATH` |
| I-T01-004 | Defaults fixos do contrato: `INDEX_WORKERS→2`, `QUERY_WORKERS→4`, `CONFIG_PATH→None` (ausente) | ENG-003 / design §2.5 / BDD FND-08 |
| I-T01-005 | `config_path: Path \| None` via `pathlib.Path` | FND-09; paths nativos Windows/macOS/Linux sem hardcode de separador |
| I-T01-006 | Env ausente **ou** string só com whitespace → default do contrato | `CONFIG_PATH` “ausente/nulo”; workers usam 2/4 |
| I-T01-007 | Valor de worker não conversível a `int` → `SettingsBootstrapError` | design §2.5 / §2.10; sem fallback silencioso |
| I-T01-008 | Sem checagem de faixa (min/max) de workers em T01 | Política de limites = T04; T01 só tipagem/bootstrap |
| I-T01-009 | Sem I/O de arquivo, rede, DB ou parse JSON em `load_settings` | Aceite T01; domínio nas tasks donas |
| I-T01-010 | Declaração em código: Protocol + constantes + exceção **sem** corpo de carga | Gate de interfaces; implementação no Developer após unitários aprovados |
| I-T01-011 | Pacote raiz `github_rag` | D-T01-001; ajustável só com mudança HITL |

## 3. Mapa env → contrato

| Variável de ambiente | Atributo `AppSettings` | Tipo | Default se ausente/blank | Conversão |
|---|---|---|---|---|
| `INDEX_WORKERS` | `index_workers` | `int` | `2` | `int(str)`; falha → `SettingsBootstrapError` |
| `QUERY_WORKERS` | `query_workers` | `int` | `4` | `int(str)`; falha → `SettingsBootstrapError` |
| `CONFIG_PATH` | `config_path` | `Path \| None` | `None` | `Path(valor)`; **não** valida existência |

Constantes de contrato obrigatórias no módulo (espelham a tabela):

- `ENV_INDEX_WORKERS = "INDEX_WORKERS"`
- `ENV_QUERY_WORKERS = "QUERY_WORKERS"`
- `ENV_CONFIG_PATH = "CONFIG_PATH"`
- `DEFAULT_INDEX_WORKERS = 2`
- `DEFAULT_QUERY_WORKERS = 4`
- Default de path: `None` (sem constante de path; ausência explícita)

## 4. Contratos detalhados

### 4.1 Constantes de env e defaults

**Responsabilidade:** fixar os nomes canônicos das variáveis e os defaults aprovados, para que implementação, testes e documentação não divergam.

**Motivo da separação:** nomes de processo (env) ficam distintos dos atributos tipados do snapshot; defaults vivem no contrato, não espalhados em tasks futuras.

**Invariantes:**

- Literais `2` e `4` e indicação de `CONFIG_PATH` ausente (`None`) permanecem no módulo (BDD FND-08).
- Não há default de string para `CONFIG_PATH` (não usar `""` como valor tipado exposto).

**Erros:** nenhum na declaração das constantes.

**Compatibilidade Windows/macOS/Linux:** nomes de env são strings OS-agnostic; o valor de `CONFIG_PATH`, quando presente, é interpretado depois como `Path` nativo do host (ou path Linux na imagem T19).

### 4.2 `AppSettings` (Protocol)

**Responsabilidade:** expor um snapshot imutável (somente leitura) dos valores de bootstrap já tipados para o processo.

**Motivo da separação:** isola configuração de processo do domínio (JSON Sourcebot, catálogo, indexação, segredos). Consumidores futuros leem o snapshot sem conhecer `os.environ`.

**Propriedades:**

| Propriedade | Tipo | Responsabilidade | Invariantes |
|---|---|---|---|
| `index_workers` | `int` | Nº de workers de indexação lido/defaultado do env | Sempre `int` após carga bem-sucedida; default `2` se env ausente/blank |
| `query_workers` | `int` | Nº de workers de query lido/defaultado do env | Sempre `int` após carga bem-sucedida; default `4` se env ausente/blank |
| `config_path` | `Path \| None` | Caminho declarado para config externa, **sem** carregar o arquivo | `None` se env ausente/blank; caso contrário `Path` construído do valor bruto |

**Erros:** o Protocol em si não levanta; erros ocorrem só em `load_settings`.

**Compatibilidade:** `Path` do `pathlib` aceita paths Windows (`C:\...`, UNC) e POSIX; proibido hardcodar `\` ou `/` na lógica do contrato/implementação.

### 4.3 `load_settings`

**Assinatura canônica:**

```python
def load_settings(
    environ: Mapping[str, str] | None = None,
) -> AppSettings: ...
```

**Responsabilidade:** ler o mapping de ambiente (ou `os.environ` quando `environ is None`), aplicar defaults e conversões tipadas simples, devolver um objeto que satisfaz `AppSettings`.

**Motivo da separação:** ponto único de entrada testável (QA injeta `environ` nos unitários) sem acoplar a parser de config ou DI framework.

**Invariantes:**

- `environ is None` → usar o ambiente do processo (`os.environ`), sem mutá-lo.
- Chave ausente ou valor só whitespace → default do contrato (workers 2/4; `config_path is None`).
- Não abre arquivo, não parseia JSON, não resolve segredos, não conecta a DB.
- Não loga valores de env (segurança design §2.11).
- Retorno satisfaz `AppSettings` (duck typing / Protocol).

**Erros:**

| Condição | Tipo | Mensagem (contrato) |
|---|---|---|
| `INDEX_WORKERS` presente e não blank, mas não conversível a `int` | `SettingsBootstrapError` | Erro claro citando o nome da variável; sem fallback para `2` |
| `QUERY_WORKERS` presente e não blank, mas não conversível a `int` | `SettingsBootstrapError` | Idem para `QUERY_WORKERS` |

**Compatibilidade:** funciona igual em Windows, macOS e Linux; diferença de OS aparece só no formato do string de `CONFIG_PATH`, tratado por `pathlib.Path`.

### 4.4 `SettingsBootstrapError`

**Responsabilidade:** sinalizar falha de bootstrap de settings (conversão tipada inválida), distinta de erros de domínio/config JSON.

**Motivo da separação:** callers podem tratar bootstrap vs T02+ sem capturar `Exception` genérica; não reutiliza exceções de I/O de arquivo.

**Invariantes:** subclasse de `Exception`; não carrega secrets na mensagem (apenas nome da variável e razão da conversão).

**Compatibilidade:** tipo puro Python; OS-agnostic.

## 5. Declaração em código (sem implementação)

| Arquivo | Conteúdo permitido nesta etapa |
|---|---|
| `src/github_rag/settings.py` | Constantes, `SettingsBootstrapError`, `AppSettings(Protocol)`, stub `load_settings` com corpo `...` |
| `src/github_rag/__init__.py` | Marcador do pacote raiz (sem API de domínio) |

**Proibido nesta etapa:** leitura de env, conversões, construção de snapshot concreto, `pyproject.toml`, README, árvore completa de placeholders, testes unitários.

Stub `load_settings(...): ...` = superfície de contrato tipada; o Developer substitui o corpo após unitários aprovados.

## 6. Fluxo de uso (conceitual)

```text
[Processo / testes]
    environ (os.environ ou mapping injetado)
         │
         ▼
   load_settings(environ?)
         │  converte INDEX_WORKERS / QUERY_WORKERS
         │  Path|None para CONFIG_PATH
         │  raise SettingsBootstrapError se int inválido
         ▼
    AppSettings { index_workers, query_workers, config_path }
         │
         ├── T01: apenas disponível para testes/harness
         ├── T02+: ConfigLoader consome config_path (não nesta task)
         └── T04+: workers consumidos pelo runtime de filas
```

## 7. Matriz de compatibilidade

| Aspecto | Contrato |
|---|---|
| Windows | `CONFIG_PATH` com path nativo; `Path` não assume `/` |
| macOS / Linux | Idem com paths POSIX |
| Container T19 | Mesmo contrato; paths Linux da imagem; **não** lê `.venv` do host |
| Shell PowerShell / cmd / bash | Fora do contrato Python; documentados no README (BDD FND-01..03) |

## 8. Critérios de pronto (HITL interfaces)

- [ ] Somente contratos de bootstrap; zero portas de domínio T02+
- [ ] Defaults `2` / `4` / `CONFIG_PATH=None` preservados
- [ ] `AppSettings` + `load_settings` + `SettingsBootstrapError` aprovados
- [ ] Paths via `pathlib`; sem hardcode de separador
- [ ] Código candidato = Protocol/tipos/constantes/stub de assinatura; sem implementação concreta nem layout completo
- [ ] Sem `ConfigLoader` / `SecretResolver` / validação de arquivo

## 9. Pontos explícitos para aprovação humana

1. Nome `AppSettings` + função `load_settings` (vs. classe `SettingsLoader`).
2. Atributos `snake_case` vs. espelhar literalmente os nomes das envs nos atributos.
3. Whitespace-only em env = ausente (default), não erro.
4. Sem validação min/max de workers em T01 (adiado a T04).
5. Stub `load_settings(...): ...` permitido nesta etapa como superfície de contrato até o Developer implementar.
6. Pacote raiz permanece `github_rag`.
