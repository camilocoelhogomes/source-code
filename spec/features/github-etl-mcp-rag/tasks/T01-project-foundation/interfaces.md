# Interfaces — T01-project-foundation

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T01-project-foundation` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `CANDIDATE_FOR_HUMAN_APPROVAL` |
| Versão | `0.2.0` (revisão pós-reprovação) |
| Design base | `0.2.0` (`HUMAN_DESIGN_APPROVED`) |
| BDD base | `0.2.0` (`HUMAN_BDD_APPROVED`) |
| Branch | `feature/github-etl-mcp-rag-T01-project-foundation` |
| Commit candidato anterior | `9b945f4` (interfaces `0.1.0` — **reprovado**) |
| Escopo desta etapa | Contratos de comunicação/bootstrap de T01 **somente** |

## 0. Histórico de decisão HITL

| Data | Autor | Decisão | Versão | Observações / feedback |
|---|---|---|---|---|
| 2026-07-18 | camilocoelhogomes | **REPROVADO** | `0.1.0` / candidato `9b945f4` | Feedback explícito: “Preciso que desenvolvedores windows também consigam trabalhar, metade da minha equipe usa Windows. Até por esse o motivo de entregar via docker.” |
| 2026-07-18 | Tech Lead Architect | Revisado → novo candidato | `0.2.0` | Windows elevado a plataforma de **dev local de primeira classe** no contrato (não best-effort); venv = PowerShell/cmd/Unix; Docker/T19 = entrega padronizada **sem** montar/usar `.venv` do host — alinhado ao design `0.2.0` aprovado (D-T01-003, D-T01-007, D-T01-009). |

A reprovação reforça ENG-009 / REQ-036 / DEC-011 no **gate de interfaces**: o contrato Python de bootstrap não pode assumir Unix-only; a entrega padronizada via Docker existe precisamente para unificar runtime (inclusive para a metade da equipe em Windows), sem depender do `.venv` do host.

## 1. Escopo e exclusões

### Em escopo (T01)

| Contrato | Módulo | Papel |
|---|---|---|
| Nomes/defaults de env bootstrap | `src/github_rag/settings.py` | Constantes de contrato |
| `AppSettings` | `src/github_rag/settings.py` | Snapshot tipado somente-leitura |
| `load_settings` | `src/github_rag/settings.py` | Carga OS-agnostic a partir do ambiente do processo |
| `SettingsBootstrapError` | `src/github_rag/settings.py` | Erro de bootstrap (mensagens sem dependência de shell) |

### Fora de escopo (não declarar em T01)

| Item | Dono |
|---|---|
| `ConfigLoader`, schema Sourcebot, validação JSON | T02 |
| `SecretResolver` / `{ "env": "..." }` | T02 |
| Portas de domínio do plano §2 | T03+ |
| Validação de existência/leitura de arquivo em `CONFIG_PATH` | T02 |
| Política de máximos/limites de workers | T04 |
| Placeholders tipados PG / Qdrant / Zoekt / SLM | T03 / T10–T13 / T19 |
| `pyproject.toml`, README, layout completo, testes unitários | gates seguintes / Developer |

Nenhuma porta de domínio entra no código de T01 (design §3; handoff da task).

### Fronteira explícita: venv (dev) × Docker/T19 (entrega)

| Fluxo | Plataformas first-class | Relação com este contrato |
|---|---|---|
| **venv = desenvolvimento local** | **Windows (PowerShell + cmd)**, macOS, Linux — paridade; não best-effort | Dev usa `.venv/` no host; `load_settings` lê env do processo no host (paths nativos) |
| **Docker/T19 = entrega padronizada** | Imagem (linux/amd64 primário) | Runtime **não monta** e **não usa** o `.venv` do host (Windows, macOS ou Linux). Motivo alinhado ao feedback HITL: unificar entrega para equipe mista |

Este contrato **não** documenta comandos de shell (isso é README / BDD FND-01..04 / FND-10). Ele **obriga** que a API Python seja igualmente válida e utilizável quando o processo roda em Windows, macOS, Linux ou no container T19.

## 2. Decisões de contrato (HITL)

| ID | Decisão | Motivo | Status em `0.2.0` |
|---|---|---|---|
| I-T01-001 | Snapshot: `AppSettings` (Protocol) | Evita colisão com o módulo `settings` | Mantida |
| I-T01-002 | Carga: `load_settings` | Superfície única e testável | Mantida |
| I-T01-003 | Atributos `snake_case`; envs `INDEX_*` / `QUERY_*` / `CONFIG_PATH` | Convenção Python | Mantida |
| I-T01-004 | Defaults `2` / `4` / `CONFIG_PATH→None` | ENG-003 / design §2.5 / FND-08 | Mantida |
| I-T01-005 | `config_path: Path \| None` via `pathlib.Path`; **proibido** hardcode de `\` ou `/` | FND-09; paths nativos Windows **e** POSIX | **Reforçada** (Windows first-class) |
| I-T01-006 | Env ausente ou só whitespace → default | Bootstrap sem ambiguidade | Mantida |
| I-T01-007 | Int inválido → `SettingsBootstrapError` | Sem fallback silencioso | Mantida |
| I-T01-008 | Sem min/max de workers em T01 | Política = T04 | Mantida |
| I-T01-009 | Sem I/O / JSON / segredos / DB em `load_settings` | Aceite T01 | Mantida |
| I-T01-010 | Código = Protocol + constantes + stub `...` | Gate interfaces | Mantida |
| I-T01-011 | Pacote raiz `github_rag` | D-T01-001 | Mantida |
| I-T01-012 | **Windows = plataforma de dev local de primeira classe** no contrato (paridade com macOS/Linux; não best-effort) | Reprovação HITL `0.1.0`; metade da equipe em Windows; D-T01-009 | **Nova** |
| I-T01-013 | Contrato reconhece **venv = dev local** (inclui PowerShell/cmd) e **Docker/T19 = entrega padronizada que NÃO monta/usa `.venv` do host** | Feedback HITL + design D-T01-003 / D-T01-007 / ENG-009 | **Nova** |
| I-T01-014 | `load_settings` é **OS-agnostic**: mesma semântica em Windows, macOS, Linux e container; não assume `bin/activate`, `Scripts\`, bash ou PowerShell | Reprovação; contrato Python ≠ docs de shell | **Nova** |
| I-T01-015 | Mensagens de `SettingsBootstrapError` citam nome da env + razão tipada; **sem** dependência de shell, paths de activate ou jargão só-Unix/só-Windows | Portabilidade da DX de erro | **Nova** |
| I-T01-016 | `CONFIG_PATH` aceita strings de path **nativas** do OS do processo (`C:\...`, UNC, POSIX); tipagem só via `pathlib.Path` | Design §2.3 / §2.5; FND-09 | **Nova** (explícita) |

## 3. Mapa env → contrato

| Variável de ambiente | Atributo `AppSettings` | Tipo | Default se ausente/blank | Conversão |
|---|---|---|---|---|
| `INDEX_WORKERS` | `index_workers` | `int` | `2` | `int(str)`; falha → `SettingsBootstrapError` |
| `QUERY_WORKERS` | `query_workers` | `int` | `4` | `int(str)`; falha → `SettingsBootstrapError` |
| `CONFIG_PATH` | `config_path` | `Path \| None` | `None` | `Path(valor)` nativo; **não** valida existência; **não** normaliza separadores manualmente |

Constantes obrigatórias no módulo:

- `ENV_INDEX_WORKERS = "INDEX_WORKERS"`
- `ENV_QUERY_WORKERS = "QUERY_WORKERS"`
- `ENV_CONFIG_PATH = "CONFIG_PATH"`
- `DEFAULT_INDEX_WORKERS = 2`
- `DEFAULT_QUERY_WORKERS = 4`
- Default de path: `None` (ausência explícita)

## 4. Contratos detalhados

### 4.1 Constantes de env e defaults

**Responsabilidade:** fixar nomes canônicos e defaults aprovados.

**Motivo da separação:** nomes de processo (env) ≠ atributos tipados; defaults versionados no contrato.

**Invariantes:** literais `2` e `4`; `CONFIG_PATH` ausente = `None` tipado (não `""`).

**Erros:** nenhum nas constantes.

**Compatibilidade (Windows first-class):** nomes de env idênticos em Windows, macOS e Linux. O valor de `CONFIG_PATH` no **dev local Windows** pode ser path nativo Windows; no **container T19** será path Linux da imagem — o contrato tipa ambos via `pathlib.Path` sem preferir um OS.

### 4.2 `AppSettings` (Protocol)

**Responsabilidade:** snapshot imutável (somente leitura) dos valores de bootstrap já tipados.

**Motivo da separação:** isola configuração de processo do domínio (arquivo de conexões, catálogo, indexação, segredos).

**Propriedades:**

| Propriedade | Tipo | Responsabilidade | Invariantes |
|---|---|---|---|
| `index_workers` | `int` | Workers de indexação | `int` após carga ok; default `2` se env ausente/blank |
| `query_workers` | `int` | Workers de query | `int` após carga ok; default `4` se env ausente/blank |
| `config_path` | `Path \| None` | Path declarado, **sem** carregar arquivo | `None` se ausente/blank; senão `Path` do valor bruto nativo |

**Erros:** só via `load_settings`.

**Compatibilidade (Windows first-class):**

- `pathlib.Path` para drive letters, UNC e POSIX.
- Proibido hardcodar `\` ou `/` na implementação futura.
- Mesmo Protocol no host Windows (venv) e no container T19 (sem `.venv` do host).

### 4.3 `load_settings`

**Assinatura:**

```python
def load_settings(
    environ: Mapping[str, str] | None = None,
) -> AppSettings: ...
```

**Responsabilidade:** ler mapping (ou ambiente do processo se `None`), aplicar defaults e conversões tipadas, devolver objeto que satisfaz `AppSettings`.

**Motivo da separação:** ponto único testável (QA injeta `environ`); sem parser de config nem DI.

**Invariantes:**

- `environ is None` → ambiente do processo; não mutar.
- Ausente ou só whitespace → defaults (`2` / `4` / `None`).
- Sem I/O de arquivo, rede, DB ou parse JSON.
- Sem logging de valores de env.
- Sem validação min/max de workers (T04).
- **OS-agnostic:** não consulta shell, não assume layout `.venv\Scripts` vs `.venv/bin`, não ramifica por `os.name` para defaults ou tipagem de workers.

**Erros:**

| Condição | Tipo | Mensagem (contrato) |
|---|---|---|
| `INDEX_WORKERS` não blank e não `int` | `SettingsBootstrapError` | Nome da variável + razão da conversão; **sem** texto de shell/activate |
| `QUERY_WORKERS` não blank e não `int` | `SettingsBootstrapError` | Idem |

**Compatibilidade (Windows first-class):**

- Semântica idêntica em Windows (PowerShell/cmd/venv), macOS, Linux e processo dentro da imagem T19.
- Única variação: formato do string de `CONFIG_PATH`, sempre via `pathlib.Path`.
- Dev local com venv **e** runtime Docker coexistem; este loader não conhece `.venv` e **não** deve assumir que ele existe (T19 não o usa).

### 4.4 `SettingsBootstrapError`

**Responsabilidade:** falha de tipagem de bootstrap, distinta de erros de domínio/arquivo de conexões.

**Motivo da separação:** tratamento específico bootstrap vs T02+ sem `except Exception`.

**Invariantes:**

- Subclasse de `Exception`.
- Mensagem: nome da env + razão tipada; sem secrets.
- **Sem dependência de shell:** não mencionar `Activate.ps1`, `activate.bat`, `source`, `bin/activate`, `Scripts\`, PowerShell, cmd ou bash.

**Compatibilidade:** tipo puro Python; mesma DX de erro em Windows, macOS e Linux.

## 5. Declaração em código (sem implementação)

| Arquivo | Conteúdo permitido nesta etapa |
|---|---|
| `src/github_rag/settings.py` | Constantes, `SettingsBootstrapError`, `AppSettings(Protocol)`, stub `load_settings` com corpo `...`; docstrings Windows first-class + Docker sem `.venv` do host |
| `src/github_rag/__init__.py` | Marcador do pacote raiz; mesma posição de plataforma |

**Proibido nesta etapa:** leitura de env, conversões, snapshot concreto, `pyproject.toml`, README, árvore completa de placeholders, testes unitários.

Stub `load_settings(...): ...` permanece superfície de contrato até o Developer (pós unitários aprovados).

## 6. Fluxo de uso (conceitual)

```text
[Dev local — Windows PowerShell/cmd | macOS | Linux]
    processo no venv (.venv no host) → load_settings → AppSettings
    CONFIG_PATH pode ser path nativo do host

[T19 — entrega padronizada via Docker]
    processo na imagem (NÃO monta / NÃO usa .venv do host)
    → mesmo load_settings / AppSettings
    CONFIG_PATH = path Linux da imagem

                    environ
                       │
                       ▼
                 load_settings   (OS-agnostic)
                       │
                       ▼
                  AppSettings
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
        T01          T02+           T04+
     (harness)   (config_path)    (workers)
```

## 7. Matriz de compatibilidade (first-class)

| Aspecto | Posição do contrato `0.2.0` |
|---|---|
| Windows (dev) | **Primeira classe** — paths nativos; sem APIs só-Unix; erros sem jargão de shell |
| macOS / Linux (dev) | **Primeira classe** — paridade com Windows |
| Shells Windows | PowerShell + cmd são first-class no **fluxo de venv** (documentação/BDD); o contrato Python não depende deles |
| venv | Dev local em qualquer OS host acima; fora do runtime deste módulo |
| Docker / T19 | Entrega padronizada; **não** monta/usa `.venv` do host; mesmo contrato de settings |
| `pathlib.Path` | Obrigatório para `config_path`; zero hardcode de separador |
| `load_settings` | OS-agnostic (host Windows/macOS/Linux e container) |

## 8. Critérios de pronto (HITL interfaces `0.2.0`)

- [ ] Histórico da reprovação `0.1.0` / `9b945f4` preservado (autor, data, feedback)
- [ ] Windows = **primeira classe** no contrato (não best-effort), em paridade com macOS/Linux
- [ ] Explícito: venv = dev local (PowerShell/cmd inclusos); Docker/T19 = entrega **sem** montar/usar `.venv` do host
- [ ] `pathlib.Path`; sem hardcode de separadores; `CONFIG_PATH` aceita paths nativos Windows/POSIX
- [ ] `load_settings` OS-agnostic; `SettingsBootstrapError` sem dependência de shell
- [ ] Defaults `2` / `4` / `CONFIG_PATH=None` preservados
- [ ] Só bootstrap; zero portas de domínio T02+
- [ ] Stub `load_settings` sem implementação concreta; sem pyproject/README/layout completo/unitários

## 9. Pontos explícitos para nova aprovação humana

1. Elevação de Windows a **first-class** no contrato (I-T01-012) atende o feedback da reprovação `0.1.0`.
2. Distinção obrigatória venv (dev, incl. PowerShell/cmd) × Docker/T19 sem `.venv` do host (I-T01-013).
3. `load_settings` OS-agnostic + erros sem shell (I-T01-014, I-T01-015).
4. `CONFIG_PATH` / `pathlib.Path` para paths nativos Windows e POSIX (I-T01-005, I-T01-016).
5. Demais decisões `0.1.0` mantidas: `AppSettings`, `load_settings`, `snake_case`, defaults 2/4/`None`, stub `...`, pacote `github_rag`.
6. Confirmar que o gate de interfaces **não** precisa antecipar texto de README/comandos de venv (já cobertos por design/BDD aprovados).
