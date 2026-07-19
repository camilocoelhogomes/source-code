# Reviews — T21-mvp-e2e-robot

## Review — Design `0.1.0` → `0.1.1` — Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` |
| Data | 2026-07-18 |
| Pipeline | autonomous (aprovação Architect substitui HITL intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` (após correções em `0.1.1`) |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Completude (contexto, solução, componentes, fluxo, dados, erros, segurança, compat., obs., riscos, rollback) | OK | §§1–15 |
| Rastreabilidade REQ-045–052 / BR-025–030 / DEC-017–021 / ENG-018–020 / BDD-026–028 | OK | cabeçalho; §§2–3; D-T21-* |
| Contratos plano `E2eStackLauncher` + `RobotMvpSuite` | OK | §3.3; handoff docs-cicd |
| Exclusão BDD-015 | OK | §3.5; D-T21-005; §5.2 |
| Podman + `docker-compose.e2e.yml` (T19) | OK | §3.1; D-T21-002/003; consumo sem ownership |
| Credenciais HITL/CI sem commit (REQ-048–049, BDD-027) | OK (após fix) | §3.6; D-T21-006 |
| Consumo `docs-cicd-e2e-release` sem ownership transferida | OK | §3.8; D-T21-009; fora de escopo §14 |
| Separação responsabilidades runtime × asserções | OK | §3.1; C-T21-01..05 |
| Green path vs BDD-026 / BR-026 | OK (após fix) | §3.5 política; D-T21-010 |

### Achados (v0.1.0) — corrigidos em v0.1.1

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `MAJOR` | Política de credencial permitia fallback genérico a `GITHUB_TOKEN` também em CI, contradizendo REQ-049 / task (“não usar o `GITHUB_TOKEN` default do Actions”) | design `0.1.0` §3.6; D-T21-006 | Em CI (`GITHUB_ACTIONS=true`) exigir `E2E_GITHUB_TOKEN`; HITL aceita `GITHUB_TOKEN` \| `E2E_GITHUB_TOKEN` | Corrigido §3.6 / D-T21-006 |
| `MAJOR` | Tag `manual_or_partial` “não bloqueia green path” se núcleo passar — enfraquece BDD-026 / BR-026 (“falha em qualquer fluxo observável impede MVP”) | design `0.1.0` §3.5 L129–130; skips 008/016–018/022 | `manual_or_partial` só documenta fatia; falha de cenário incluído → exit ≠ 0; fixture local + `negative.robot` no green path; só BDD-015 fora | Corrigido §3.5 / D-T21-010/012 |
| `SUGGESTION` | MCP descrito como “HTTP/SSE ou JSON-RPC” sem pin ao transporte T19 | design `0.1.0` §3.2 `mcp.resource` | Pin SSE `:8001` (`MCP_TRANSPORT=sse`) | Aceito/corrigido D-T21-011 |
| `SUGGESTION` | Notação `token.env` informal vs contrato `{ "env": "GITHUB_TOKEN" }` | design `0.1.0` §3.4 | Alinhar ao schema REQ-041 | Aceito/corrigido §3.4 |
| `SUGGESTION` | REQ-049 (DATABASE_URL/ZOEKT/…) pouco explícito vs compose T19 | design `0.1.0` §6 | Documentar injeção pelo compose; operador só token | Aceito/corrigido §3.4 / §6 |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — design.md `0.1.1` alinhado a REQ-045–052, BDD-026–028, ENG-018–020 e handoff `E2eStackLauncher` / `RobotMvpSuite`. Prosseguir para BDD.

---

## Review — BDD `0.1.0` → `0.1.1` — Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `bdd.md` + `tests/bdd/test_mvp_e2e_robot.py` |
| Data | 2026-07-18 |
| Pipeline | autonomous (aprovação Architect substitui HITL intermediário) |
| Resultado | `APPROVED_BY_ARCHITECT` (após correções em `0.1.1`) |

### Critérios avaliados

| Critério | Resultado | Evidência |
|---|---|---|
| Cobre BDD-026–028 e critérios da task | OK | bdd.md §§E2E-01..10, ROBOT-01..06; tabela aceite; mapeamento BDD-001–024 |
| Exclui BDD-015 | OK | E2E-07; ROBOT-06; mapeamento 015 = Não |
| CI exige `E2E_GITHUB_TOKEN` | OK | E2E-02; design D-T21-006 |
| Doubles; sem compose up real no pytest | OK | docstring + RecordingLauncher/RobotRunner; D-T21-008 |
| Green path não skipa BDD observáveis | OK | política Camada B; `manual_or_partial` ≠ skip; negative + fixture local no path |
| Contratos alinhados ao design 0.1.1 | OK | ordem resolve→up→healthy→robot→down; HOST_*; handoff E2E-09 |

### Achados (v0.1.0) — corrigidos em v0.1.1

| Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|
| `MAJOR` | E2E-02 podia passar se `E2eCredentialResolver.resolve` retornasse sucesso sem `E2E_GITHUB_TOKEN` (falha não obrigatória) | `test_mvp_e2e_robot.py` `test_ci_with_only_actions_github_token_fails` (v0.1.0) | Exigir falha explícita (`fail` se resolve OK; `assertTrue(failed)`) | Corrigido no teste |
| `MAJOR` | Assert de exclusão `bdd015` aceitava mera substring `bdd015` (falso positivo sem `--exclude`) | regex E2E-07 v0.1.0 | Exigir `--exclude` / `exclude=` / lista `excludes`; negar Discovery Cursor | Corrigido teste + bdd E2E-07 |
| `MAJOR` | E2E-03 usava `assertNotIn(SECRET_TOKEN, "compose failed")` (tautologia); E2E-10 podia passar só com `exit=N` sem inspecionar mensagem | E2E-03/10 v0.1.0 | Redaction via `E2eCredentialError` + `str(E2eStackError)` + argv robot | Corrigido teste + bdd E2E-10 |
| `SUGGESTION` | E2E-01 com `assertRaises` + ramo `pass` em exit ≠ 0 era inconsistente | E2E-01 v0.1.0 | Unificar: falha obrigatória + `up` não chamado | Corrigido |

### Achados abertos

| Severidade | Achado | Evidência | Correção esperada |
|---|---|---|---|
| — | Nenhum `BLOCKING` ou `MAJOR` aberto | — | — |

### Decisão

`APPROVED_BY_ARCHITECT` — BDD contratos E2E-01..10 + documentação Robot green path alinhados ao design `0.1.1`, BDD-026–028, exclusão BDD-015, CI `E2E_GITHUB_TOKEN`, doubles sem Podman real. Prosseguir para interfaces.
