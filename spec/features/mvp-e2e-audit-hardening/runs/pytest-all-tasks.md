# ParentPytestRun — pytest all tasks (T03)

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T03-run-pytest-all-tasks` |
| Contrato | `ParentPytestRun` |
| Data/hora (UTC) | `2026-07-19T02:30:35Z` |
| Branch | `feature/mvp-e2e-audit-hardening-T03-run-pytest-all-tasks` |
| Commit SHA | `cb5e5c576add44402e84543f7419e518351f8c46` |
| Python | `Python 3.14.6` |
| OS | `Darwin 24.6.0 arm64` |
| Comando canônico | `python -m pytest tests/ -q --tb=line` |

## Escopo (D-T03-001)

Declaração: sem mudança de produto nesta task. Não altera `src/github_rag/**`, não altera `e2e/robot/**` e não corrige falhas de domínio do pai — apenas executa e registra evidência run-first.

## Soft-dep T01

Inventário T01 **disponível** neste tip da branch (pós-merge): `spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md`. Soft-dep: o run **não depende** do artefato T01; superfícies abaixo usam heurística do design §3.3 (independente do inventário).

## Resultado agregado

| Métrica | Valor |
|---|---|
| exit code | `0` |
| passed | `1145` |
| failed | `0` |
| skipped | `2` |
| errors | `0` |
| total | `1147` |
| duração | `10.17s` |
| subtests passed | `240` |
| warnings | `142` |

### Cobertura

| Campo | Valor |
|---|---|
| coverage | `96.44%` (TOTAL term report; `Required test coverage of 95.0% reached`) |
| coverage_gate | `false` |

`coverage_gate: false` — o gate `fail_under=95` foi **atingido**; exit code `0`.

### Nota de ordem de implementação (D-T03-002)

Primeiro run (pré-artefato) falhou só nos 9 testes de contrato da feature filha (`mvp_e2e_audit_*`) por artefato ausente; essas falhas **não** alimentam T05. Após materializar este resumo, a suíte canônica acima ficou verde (exit `0`).

## Mapa de superfícies candidatas (ENG-006)

Heurística estável por path/nodeid (design §3.3):

| Superfície | Heurística |
|---|---|
| `health` | `delivery`, `health`, `runtime_boot`, `wiring`, `manifest` |
| `catalog_indexing` | `catalog`, `indexing`, `index/`, `snapshot`, `eligibility`, `schedule`, `sources`, `concurrency` |
| `ui` | `ui/`, `management_ui` |
| `mcp` | `mcp/` |
| `negative` | cenários negativos explícitos / markers; N/A neste run |
| `tooling-e2e` | `e2e/`, `config`, `settings`, infra de teste, coleta/import errors |

## Lista de falhas do pai

Lista vazia — **nenhuma** falha/erro de domínio do pai neste run (sem entradas de falha).

Regra **D-T03-002**: testes de contrato da feature filha (`mvp_e2e_audit_*`) ficam fora desta lista e não alimentam T05. Neste run não há entradas do pai a mapear para superfície.

## Proibições / sanitização

- Nenhum PAT, conteúdo de `.env`, header Authorization ou dump de env neste artefato.
- Sem prefixos `ghp_` / `gho_` / `ghu_` / `ghs_` / `ghr_`.
- Log bruto local em `/tmp` (não versionado); este resumo é a evidência versionável (ENG-002).

## Handoff T05

- Achados de produto do pai neste run: **nenhum**.
- T05 ainda deve considerar falhas futuras de pytest + resultados T04; ausência de falha pytest não encerra lacunas (BDD-008 / T01+T06).
