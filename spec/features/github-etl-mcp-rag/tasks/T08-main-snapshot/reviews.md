# Reviews — T08-main-snapshot

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T08-main-snapshot` |

## Review — Design v0.1.0

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Revisor | Tech Lead Architect |
| Artefato | `design.md` v0.1.0 |
| Resultado | `CHANGES_REQUIRED` |

### Achados

| ID | Severidade | Evidência | Correção esperada |
|---|---|---|---|
| M-01 | `MAJOR` | §4.3 (`commit_sha`); §4.6 (clone shallow tip); §5 (fetch só para diff); §1 (T16 read/tree commit indexado) | `list_tree`/`read_file` no GitHub resolvem `commit_sha` pedido ou `CommitNotFoundError` |
| S-01 | `SUGGESTION` | §3 vs §4.5 (“main remota equivalente”) | Tip local só `refs/heads/main` |
| S-02 | `SUGGESTION` | §4.6 / §7 | Auth clone sem persistir token (BR-008) |
| S-03 | `SUGGESTION` | §4.2 | Renames = deleted+added (`-M` off) |
| S-04 | `SUGGESTION` | §4.7 | Única porta pública: `DefaultMainSnapshotProvider` |

## Review — Design v0.1.1

| Campo | Valor |
|---|---|
| Data | 2026-07-18 |
| Revisor | Tech Lead Architect |
| Artefato | `design.md` v0.1.1 |
| Resultado | `APPROVED_BY_ARCHITECT` |

### Achados

| ID | Severidade | Achado | Evidência | Correção esperada | Status |
|---|---|---|---|---|---|
| — | — | Nenhum BLOCKING/MAJOR | M-01 e S-01..S-04 fechados em §3, §4.2, §4.5–4.7, §5, §7, D-T08-006..009 | — | `APPROVED_BY_ARCHITECT` |
| S-05 | `SUGGESTION` | D-T08-008 omite `diff_files`/`from_commit` já cobertos em §4.6/§5 | §11 D-T08-008 vs §4.6 | Alinhar texto da decisão na etapa de interfaces (não bloqueia) | aberto (não bloqueante) |
