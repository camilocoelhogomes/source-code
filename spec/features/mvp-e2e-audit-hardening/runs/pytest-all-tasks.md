# ParentPytestRun — pytest all tasks (T03)

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T03-run-pytest-all-tasks` |
| Contrato | `ParentPytestRun` |
| Data/hora (UTC) | `2026-07-19T02:28:23Z` |
| Branch | `feature/mvp-e2e-audit-hardening-T03-run-pytest-all-tasks` |
| Commit SHA | `2c5f250425907f242d422bc57c3c0531631e7868` |
| Python | `Python 3.14.6` |
| OS | `Darwin 24.6.0 arm64` |
| Comando canônico | `python -m pytest tests/ -q --tb=line` |

## Escopo (D-T03-001)

Declaração: sem mudança de produto nesta task. Não altera `src/github_rag/**`, não altera `e2e/robot/**` e não corrige falhas de domínio do pai — apenas executa e registra evidência run-first.

## Soft-dep T01

Inventário T01 (`audit/` / coverage inventory) **não** estava disponível neste commit base (`main` @ `086f3b3` / tip da branch sem merge de T01). Soft-dep: o run **não depende** do artefato T01; superfícies abaixo usam heurística do design §3.3 (independente do inventário).

## Resultado agregado

| Métrica | Valor |
|---|---|
| exit code | `1` |
| passed | `1096` |
| failed | `9` |
| skipped | `2` |
| errors | `0` |
| total | `1107` |
| duração | `11.67s` |
| subtests passed | `240` |
| warnings | `142` |

### Cobertura

| Campo | Valor |
|---|---|
| coverage | `96.44%` (TOTAL term report; `Required test coverage of 95.0% reached`) |
| coverage_gate | `false` |

`coverage_gate: false` — o gate `fail_under=95` foi **atingido**; o exit code ≠ 0 **não** se deve ao coverage gate.

### Interpretação do exit code

Exit `1` decorre exclusivamente de **9 falhas de contrato da feature filha** (`tests/bdd/test_mvp_e2e_audit_pytest_run.py`, nodeids `mvp_e2e_audit_*`) — artefato ainda ausente no momento do run (ordem D-T03-002: run → escrever artefato → asserts de contrato).  
Essas falhas **não** entram na lista de falhas do pai para T05.

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

Lista vazia — **nenhuma** falha/erro de domínio do pai neste run.

Regra **D-T03-002**: excluir nodeids da feature filha (`mvp_e2e_audit_*` / contrato T03) desta lista. Os 9 `failed` agregados acima são só contrato da filha e foram excluídos.

| nodeid | tipo | mensagem sanitizada | superfície candidata |
|---|---|---|---|
| — | — | (nenhuma falha do pai) | — |

Regra **D-T03-002**: nodeids `mvp_e2e_audit_*` da feature filha são excluídos desta lista (ver seção seguinte).

## Falhas excluídas (feature filha — não T05)

Excluídas por D-T03-002 (`mvp_e2e_audit_*` / contrato T03). Mensagens sanitizadas: `artefato ausente: …/runs/pytest-all-tasks.md` — sem secrets.

| nodeid | tipo | motivo exclusão |
|---|---|---|
| `tests/bdd/test_mvp_e2e_audit_pytest_run.py::TestPYTEST01ArtifactExists::test_artifact_file_exists` | failed | D-T03-002 / feature filha |
| `tests/bdd/test_mvp_e2e_audit_pytest_run.py::TestPYTEST02Metadata::test_run_metadata_present` | failed | D-T03-002 / feature filha |
| `tests/bdd/test_mvp_e2e_audit_pytest_run.py::TestPYTEST03AggregatedResult::test_aggregated_counts_present` | failed | D-T03-002 / feature filha |
| `tests/bdd/test_mvp_e2e_audit_pytest_run.py::TestPYTEST04Coverage::test_coverage_or_na_and_gate_field` | failed | D-T03-002 / feature filha |
| `tests/bdd/test_mvp_e2e_audit_pytest_run.py::TestPYTEST05ParentFailures::test_failure_list_contract` | failed | D-T03-002 / feature filha |
| `tests/bdd/test_mvp_e2e_audit_pytest_run.py::TestPYTEST06SoftDepT01::test_t01_soft_dep_note` | failed | D-T03-002 / feature filha |
| `tests/bdd/test_mvp_e2e_audit_pytest_run.py::TestPYTEST07NoSecrets::test_artifact_has_no_token_patterns` | failed | D-T03-002 / feature filha |
| `tests/bdd/test_mvp_e2e_audit_pytest_run.py::TestPYTEST08ExcludesChildNodeids::test_parent_failure_list_excludes_child_contract_nodeids` | failed | D-T03-002 / feature filha |
| `tests/bdd/test_mvp_e2e_audit_pytest_run.py::TestPYTEST09NoProductChange::test_no_product_change_declared` | failed | D-T03-002 / feature filha |

## Proibições / sanitização

- Nenhum PAT, conteúdo de `.env`, header Authorization ou dump de env neste artefato.
- Sem prefixos `ghp_` / `gho_` / `ghu_` / `ghs_` / `ghr_`.
- Log bruto local em `/tmp` (não versionado); este resumo é a evidência versionável (ENG-002).

## Handoff T05

- Achados de produto do pai neste run: **nenhum**.
- T05 ainda deve considerar falhas futuras de pytest + resultados T04; ausência de falha pytest não encerra lacunas (BDD-008 / T01+T06).
