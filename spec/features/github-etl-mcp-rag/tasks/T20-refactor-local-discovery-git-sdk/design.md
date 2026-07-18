# Design — T20-refactor-local-discovery-git-sdk

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T20-refactor-local-discovery-git-sdk` |
| Autor | Implementation Task Runner |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Branch | `feature/github-etl-mcp-rag-T20-refactor-local-discovery-git-sdk` |
| Base | `main` (T06 mesclado) |
| Rastreabilidade | BR-023; DEC-015; DT-001; BDD-016, BDD-018; BDD-024 |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `CHANGES_REQUIRED` | `0.1.0` | M-01 bare ambíguo; M-02 falta tabela de paridade. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | M-01/M-02/S-01/S-02 resolvidos; D-T20-006 + §3.2. |

## 1. Contexto

`T06-local-discovery` entrega `LocalRepoDiscovery` + `GitFilesystemInspector` com contrato estável para T07. A inspeção Git em produção lê `.git`, `refs/heads/main` e `packed-refs` de forma ad-hoc (`git_fs.py`), violando BR-023 / DEC-015 (**DT-001**).

T20 é refactor de conformidade: migrar somente a inspeção Git para **GitPython**, sem mudar comportamento de produto observável (BDD-016 / BDD-018).

## 2. Problema

1. Eliminar parse ad-hoc de `.git` / refs / `packed-refs` no caminho de produção da descoberta local.
2. Usar GitPython (DEC-015) para validar repositório Git e presença da branch `main`.
3. Preservar contrato público de `LocalRepoDiscovery` e modelos (`DiscoveredLocalRepo`, `LocalDiscoveryIssue`, `LocalDiscoveryResult`).
4. Manter stdlib para I/O genérico (`pathlib`, parse `file://`, glob, `os.access`) — permitido por BR-023.
5. Contribuir para BDD-024 (eliminação de DT-001) sem alterar intenção dos cenários BDD-016/018.

## 3. Solução proposta

Substituir a implementação interna de `GitFilesystemInspector.inspect_repo` (e helpers `_resolve_git_dir` / `_has_main_branch` / regex de packed-refs) por abertura via GitPython:

```text
Path candidato
  → se não é diretório → RepoInspection(not git, reason="not a directory")
  → with git.Repo(path) as repo:   # context manager (S-01); resolve .git dir / gitdir file
       InvalidGitRepositoryError / NoSuchPathError
         → reason="not a git repository"
       se repo.bare:
         → reason="not a git repository"   # paridade T06 (D-T20-006)
       "main" in repo.heads  (loose + packed via SDK)
         False → is_git_repo=True, has_main=False, reason="main branch not found"
         True  → is_valid_candidate
```

| Componente | Mudança |
|---|---|
| `discovery.py` | Nenhuma (contrato e orquestração intactos) |
| `git_fs.py` | `inspect_repo` via GitPython; remover parse ad-hoc |
| `parse_file_url` / `is_accessible` / `expand_candidates` | Permanecem stdlib |
| `pyproject.toml` | Dependência `GitPython>=3.1` |
| Testes T06 | Fixtures mínimas passam a satisfazer GitPython (ex.: dir `objects` ou `Repo.init`) — intenção BDD inalterada |

### 3.1 Decisões de design

| ID | Decisão | Motivo |
|---|---|---|
| D-T20-001 | Manter classe `GitFilesystemInspector` e assinaturas | Evita churn em mocks/injeção de T06/T07; refactor interno |
| D-T20-002 | Detectar `main` via `"main" in repo.heads` | API estável do GitPython; cobre loose + packed-refs |
| D-T20-003 | Preservar `reason` nos caminhos de produto (worktree válido, gitdir file, packed-refs, sem `main`, não-git, não-dir) | Regressão BDD-016/018; ver §3.2 para deltas justificados de stubs incompletos |
| D-T20-004 | Não mutar working tree; só leitura de metadados | BR-015 / escopo T06 preservado |
| D-T20-005 | Atualizar fixtures de teste para repos aceitos pelo SDK | Stubs sem `objects/` são rejeitados por GitPython; não é mudança de produto |
| D-T20-006 | **Bare rejeitado** (`repo.bare` → `not a git repository`) | Paridade T06: ad-hoc só reconhece `.git` dir/file em worktree; mounts `/repos/*` são worktrees. Não expandir produto para bare. |
| D-T20-007 | Runtime: pacote GitPython **e** binário `git` no PATH | Requisito do SDK (S-02); T19/imagem devem fornecê-lo; CI local idem |

### 3.2 Paridade T06 → GitPython (M-02)

| Cenário | T06 ad-hoc | T20 GitPython | Paridade |
|---|---|---|---|
| Worktree `.git/` + `refs/heads/main` (+ `objects/`) | válido | válido | idêntica |
| Worktree com `.git` file (`gitdir:`) + `main` | válido | válido | idêntica |
| `main` só em `packed-refs` (repo SDK-válido) | válido | válido (`repo.heads`) | idêntica |
| Diretório sem Git | `not a git repository` | idem (InvalidGitRepositoryError) | idêntica |
| Path não-diretório | `not a directory` | idem (check pré-SDK) | idêntica |
| Git válido sem branch `main` | `main branch not found` | idem | idêntica |
| Bare com `main` | `not a git repository` (sem `.git` filho) | abrir OK no SDK, **rejeitar via D-T20-006** com mesma `reason` | idêntica (política explícita) |
| `.git/` incompleto (ex.: sem `objects/`) | pode classificar `is_git_repo=True` | `InvalidGitRepositoryError` → `not a git repository` | **delta justificado**: stub não é repo Git real; fora do caminho de produto (volumes com `git clone`/`init` reais) |
| `.git/` vazio | `is_git_repo=True`, sem `main` | `not a git repository` | **delta justificado** (mesmo motivo) |

Deltas da tabela **não** alteram BDD-016/018 nem candidatos em mounts reais; apenas rejeitam stubs incompletos que o ad-hoc aceitava por acaso.

## 4. Componentes

Sem novos módulos. Fronteira de SDK confinada a `git_fs.py` (ENG-013 / adaptador).

## 5. Fluxo

Inalterado em relação a T06 design §3 (filtro `git` → parse URL → acessibilidade → glob → inspect → repos/issues). Somente a implementação de `inspect` muda.

## 6. Dados

Contratos de saída imutáveis de T06 permanecem. Nenhum schema/persistência.

## 7. Erros

| Condição | Resultado observável |
|---|---|
| Path não é diretório | issue / `reason="not a directory"` |
| Não é repo Git (SDK) | `reason="not a git repository"` |
| Repo sem branch `main` | `reason="main branch not found"` |
| Volume inacessível | issue de conexão (lógica discovery inalterada) |
| URL inválida | issue de parse (stdlib, inalterado) |

Exceções GitPython de abertura são traduzidas para `RepoInspection` — nunca propagam para abortar outras conexões.

## 8. Segurança

- Somente leitura de metadados Git via SDK (context manager; sem mutação).
- Sem parse manual de refs; GitPython pode invocar o binário `git` do PATH (D-T20-007).
- Sem exposição de segredos (conexões `git` locais não têm token).

## 9. Compatibilidade

| Consumidor | Impacto |
|---|---|
| T07 / bootstrap | Nenhum (mesma porta) |
| BDD-016 / BDD-018 | Regressão obrigatória verde |
| Unitários T06 de discovery com mock | Intactos (autospec da interface) |
| Unitários de `inspect_repo` / BDD fixtures | Ajuste de fixture para repos válidos ao SDK |

## 10. Observabilidade

Sem mudança de logging além do já implícito em `LocalDiscoveryIssue.message`.

## 11. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Fixtures antigas falham com GitPython | Atualizar helpers de teste; provar BDD-016/018 |
| Diff de edge case (repo vazio pós-`git init` sem commit) | Sem ref em `heads` → `main branch not found` (alinhado) |
| Bare aceito pelo SDK | D-T20-006 rejeita explicitamente |
| Binário `git` ausente no PATH | D-T20-007; falha de abertura → `not a git repository` / issue; documentar em changelog e T19 |

## 12. Rollback

Reverter o PR da T20; comportamento de produto volta ao de T06 (com DT-001 reaberta).

## 13. Fora de escopo

- Snapshot/diff (T08); sync catálogo (T07); UI; mudanças de wildcards além do adaptador; BDD-024 completo (outras integrações/T19).

## 14. Critérios de aceite (DoD técnico)

- Zero leitura ad-hoc de `.git`/refs/`packed-refs` em código de produção de `sources.local`.
- `GitPython` declarado em dependências e usado em `inspect_repo` (com context manager).
- Bare rejeitado com paridade T06 (D-T20-006).
- Runtime documentado: GitPython + `git` no PATH (D-T20-007).
- BDD LOC-01..06 (BDD-016/018) verdes.
- Cobertura global ≥ 95%.
- Contrato `LocalRepoDiscovery` inalterado.
