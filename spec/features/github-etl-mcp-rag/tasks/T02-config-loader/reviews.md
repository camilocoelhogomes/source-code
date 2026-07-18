# Reviews — T02-config-loader

## Review Design — Tech Lead Architect

| Campo | Valor |
|---|---|
| Revisor | Tech Lead Architect |
| Artefato | `design.md` v0.1.0 (candidato) → v0.2.0 (corrigido) |
| Data | 2026-07-18 |
| Branch | `feature/github-etl-mcp-rag-T02-config-loader` |
| Modo | Autonomous pipeline (aprovação Architect substitui HITL) |
| Resultado inicial | `CHANGES_REQUIRED` |
| Resultado final | `APPROVED_BY_ARCHITECT` |

### Checks executados

| Check | Resultado |
|---|---|
| Leitura `T02-config-loader.md`, `requirements.md` (REQ-009,039–042; BR-016–022; BDD-021/022/014), `implementation-plan.md` | OK |
| Cruzamento com T01 (`AppSettings.config_path: Path \| None`, sem I/O) | OK |
| Escopo vs fora de escopo (sem descoberta / sem I/O GitHub) | OK após correção §3.1 |
| Completude de regras de schema / erros / segredo | OK após correção §4.3–4.4 / §6 |

### Achados (sobre v0.1.0)

| ID | Severidade | Evidência | Achado | Correção esperada |
|---|---|---|---|---|
| M-01 | `MAJOR` | `design.md` v0.1.0 §13; BDD-021; plano T02↔BDD-021 e T07↔BDD-021 | Design afirmava cobrir BDD-021 integralmente, mas BDD-021 inclui descoberta/identificação de origem — fora do escopo T02. Risco de overscape no BDD ou aceite incompleto. | Explicitar cobertura parcial: T02 = carregar conexões tipadas; descoberta/origem = T05/T06/T07. |
| M-02 | `MAJOR` | `design.md` v0.1.0 §4.3; REQ-010; contrato exemplo | Regras de validação incompletas: não definia se `orgs`/`branches` vazios são inválidos, se `repos` vazio é permitido, se `connections: {}` é válido, nem tratamento de chaves extras. | Tabela de regras obrigatórias (§4.3): `orgs` não-vazio; `repos` pode ser vazio; `{}` válido; extras top-level ignorados. |
| M-03 | `MAJOR` | `design.md` v0.1.0 §4.4; T01 Windows first-class; REQ-040 | `file://` “absoluto” sem formas aceitas (POSIX vs Windows `file:///C:/...`) nem exemplos de rejeição de path relativo. | Especificar formas POSIX/Windows aceitas e rejeições (§4.4). |
| M-04 | `MAJOR` | `design.md` v0.1.0 §4.3 (“alinhado a REQ-013”) | Exigir `"main"` em `branches` atribuído a REQ-013; REQ-013 regula indexação, não o schema do JSON. | Renomear como ENG-T02-001 (decisão de engenharia do loader MVP). |
| M-05 | `MAJOR` | `design.md` v0.1.0 §3 fluxo vs §8; handoff T01 | Fluxo dizia “ler bytes”; §8 `read_text`; não deixava explícito que o path vem de `AppSettings.config_path` sem reler env. | Unificar I/O em `read_text`+`json.loads`; input = `AppSettings.config_path`. |
| S-01 | `SUGGESTION` | `design.md` v0.1.0 §10 | Fail-fast único; BR-021 só exige não aplicar parcial. | Aceitar fail-fast **ou** validação completa sem montar `AppConfig` — documentado em §6 v0.2.0. |

### O que já estava aderente (v0.1.0)

- Separação `schema` / `SecretResolver` / `ConfigLoader` alinhada ao plano §1.3 / §2.
- Fail total sem cadastro parcial (BR-021); token só via `{ "env" }` (REQ-041); wildcards só inclusão (BR-022).
- Sem descoberta GitHub/disco além do arquivo; stdlib only; rollback greenfield.
- Política de redaction em erros/`repr` para BDD-014 parcial.

### Correções aplicadas pelo Architect (v0.2.0)

| ID | Resolução |
|---|---|
| M-01 | §3.1 matriz BDD parcial; rastreabilidade `BDD-021 (parcial)`. |
| M-02 | §4.3 tabela de regras (`orgs`, `repos`, `branches`, `{}`, extras). |
| M-03 | §4.4 formas `file://` POSIX/Windows + rejeições. |
| M-04 | ENG-T02-001; REQ-013 não citato como fonte da regra de schema. |
| M-05 | Fluxo + §4.1/`§5` usam `AppSettings.config_path` + `read_text`. |
| S-01 | §6 permite fail-fast ou validação agregada sem retorno parcial. |

### Bloqueios abertos

Nenhum.

### Decisão

`APPROVED_BY_ARCHITECT` — design v0.2.0 apto para o gate BDD. Próximo artefato: `bdd.md` (sem implementação).
