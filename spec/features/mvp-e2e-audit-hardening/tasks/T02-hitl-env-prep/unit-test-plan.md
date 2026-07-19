# Unit Test Plan — T02-hitl-env-prep

| Campo | Valor |
|---|---|
| Feature | `mvp-e2e-audit-hardening` |
| Task | `T02-hitl-env-prep` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design / BDD / Interfaces | `0.1.0` / `0.1.0` / `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Natureza | Documental — sem `src/`; contrato `HitlEnvPrep` |
| Suíte de aceite | `tests/bdd/test_mvp_e2e_audit_hitl_env_prep.py` (HITL-01..10) |
| Branch | `feature/mvp-e2e-audit-hardening-T02-hitl-env-prep` |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Corners cobertos pelo BDD; unitários em `src/` desnecessários (D-T02-001). |

## 1. Estratégia

| Camada | Onde | Fronteira |
|---|---|---|
| Contrato documental (aceitação) | `tests/bdd/test_mvp_e2e_audit_hitl_env_prep.py` | Path real do checklist + guards de repo |
| Runtime Python em `src/` | **não aplicável** | D-T02-001: zero módulo de produto |
| Helpers `tests/unit/` de parsing puro | **não necessários nesta task** | BDD já cobre corners sem ler `.env` real |

Decisão (I-T02-003 / D-T02-001):

- Não há implementação em `src/github_rag/**` ⇒ **não** há testes unitários de produto a escrever.
- Unitários adicionais em `src/` são **explicitamente desnecessários**.
- Helpers opcionais em `tests/unit/` (regex/parsing sintético) **não agregam valor** além do que HITL-08/`TOKEN_*_RE` e os asserts de conteúdo já exercitam; não serão criados nesta task.

## 2. Mapeamento corner cases → BDD existente

| ID | Corner case | Camada BDD | Como é coberto | Unitário `src/`? |
|---|---|---|---|---|
| C-01 | Artefato ausente | HITL-01 (+02..08 via `_read_checklist`) | `AssertionError: artefato ausente` / `is_file` False | Não |
| C-02 | Checklist sem pré-requisitos | HITL-02 | Asserts Podman / repo / `.env.example` / `e2e/README.md` | Não |
| C-03 | Passo PAT ausente ou com secret | HITL-03 + HITL-08 | Exige PAT/operador; `TOKEN_PREFIX_RE` | Não |
| C-04 | Passo `.env` incompleto | HITL-04 | Exige `cp`, ambas vars, repo | Não |
| C-05 | Proibições de commit/secret ausentes | HITL-05 | `git add`/commit + proibição token em `spec`/commits | Não |
| C-06 | Verificação incompleta / ecoa secret | HITL-06 | Comandos obrigatórios; proíbe `cat .env` / `echo $TOKEN` | Não |
| C-07 | Gate T04 incompleto (sem READY/BLOCKED ou checks) | HITL-07 | `GATE_CHECKS` + READY/BLOCKED + PASS/FAIL + evidência bool | Não |
| C-08 | Secrets no markdown (`ghp_`… / assign longo) | HITL-08 | `TOKEN_PREFIX_RE` / `TOKEN_ASSIGN_RE` | Não |
| C-09 | `.gitignore` sem `.env` | HITL-09 | `assertIn(".env", …)` | Não |
| C-10 | `.env.example` sem `E2E_GITHUB_TOKEN=` vazio / com secret | HITL-10 | regex linha vazia + prefix scan | Não |
| C-11 | Leitura de valor de `.env` real nos testes | Convenção BDD/design §8 | Testes **não** abrem `.env` real | Não |

**Pré-implementação:** C-01..C-08 em RED (artefato ausente); C-09/C-10 já verdes (guards do repo).

## 3. Decisão sobre unitários auxiliares

| Opção | Avaliação | Escolha |
|---|---|---|
| A — Só BDD HITL-01..10 | Suficiente para contrato documental; sem duplicação | **Escolhida** |
| B — `tests/unit/` parser de markdown sintético | Pouco ganho: asserts já são substring/regex no path real; sem schema tabular rígido como T01 | Descartada |
| C — Testes em `src/` | Violaria D-T02-001 | Proibida |

## 4. Comando de aceite

```bash
.venv/bin/python -m pytest tests/bdd/test_mvp_e2e_audit_hitl_env_prep.py -q
```

Estado esperado pré-checklist: **8 failed, 2 passed**.

## 5. Fora de escopo

- Qualquer teste unitário sob `src/github_rag/**`.
- Ler ou assertar valor de token em `.env` real.
- Executar Robot / `python -m github_rag.e2e` (T04).
- Validar PAT na API GitHub.
