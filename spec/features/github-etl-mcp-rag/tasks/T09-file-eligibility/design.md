# Design — T09-file-eligibility

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T09-file-eligibility` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão do design | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T09-file-eligibility` |
| Base | `main` (T01 já mesclado) |
| Rastreabilidade | REQ-014, REQ-015, REQ-019; BR-023; DEC-015; BDD-006; BDD-024 |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-18 |

## 1. Contexto

T01 reservou o pacote `github_rag.eligibility` como fronteira vazia. O plano (§1.3 / §2)
define a porta `FileEligibilityFilter`: incluir arquivos textuais de desenvolvimento
(qualquer linguagem, incluindo Markdown e Java), excluir CSV, imagens e paths
cobertos por `.gitignore`, com matching via **pathspec** (GitWildMatch) — DEC-015 /
BR-023 / BDD-024. Sem caps de tamanho no MVP (REQ-019).

Consumidor futuro: `T14-indexing-orchestrator` (após snapshot `T08`). Esta task
não lê Git remoto, não indexa e não toca UI.

Corner cases obrigatórios (task + BDD-006): repositório sem `.gitignore`,
`.gitignore` aninhados, extensões mistas no mesmo snapshot, arquivos sem
extensão com política documentada.

## 2. Solução técnica

### 2.1 Estratégia geral

1. Expor a porta `FileEligibilityFilter` **pura**: recebe paths relativos do
   snapshot e fontes de `.gitignore` já materializadas; devolve paths elegíveis.
   Sem I/O na porta.
2. Separar **carregamento** de `.gitignore` (stdlib `pathlib`, permitido por
   BR-023) em helper dedicada, injetável/testável com fixtures de diretório.
3. Aplicar matching GitWildMatch exclusivamente via biblioteca **`pathspec`**
   (proibido reimplementar; alternativa GitPython `check-ignore` descartada —
   ver D-T09-002).
4. Aplicar regras de tipo (CSV / imagens / textuais) por extensão (e política
   de sem-extensão), **após** a decisão de ignore — path ignorado nunca entra.
5. Não inspecionar tamanho de arquivo nem conteúdo binário no MVP (REQ-019).

### 2.2 Componentes

| Componente | Módulo | Responsabilidade |
|---|---|---|
| `FileEligibilityFilter` | `eligibility/filter.py` | Porta: filtrar paths elegíveis |
| `PathspecFileEligibilityFilter` | `eligibility/filter.py` | Implementação com pathspec + rules |
| `GitignoreSource` | `eligibility/gitignore.py` | DTO: diretório relativo + linhas do `.gitignore` |
| `load_gitignore_sources` | `eligibility/gitignore.py` | Walk local: coleta `.gitignore` aninhados |
| `EligibilityRules` / constantes | `eligibility/rules.py` | Denylist CSV/imagens; política sem extensão |
| `EligibilityError` | `eligibility/filter.py` | Erros tipados de entrada inválida |

Decisão **D-T09-001** — API da porta (puro, sem leitura de root na porta):

```text
FileEligibilityFilter.filter(
    paths: Sequence[str],
    gitignore_sources: Sequence[GitignoreSource],
) -> list[str]
```

- `paths`: paths relativos ao root do repositório, com `/` como separador
  lógico (normalizar `\` → `/` na entrada; rejeitar paths absolutos ou com
  `..` que escapem o root — ver §2.5).
- `gitignore_sources`: lista de `(relative_dir, lines)` onde `relative_dir=""`
  é o `.gitignore` da raiz; `"subdir"` / `"a/b"` são aninhados.
- Retorno: subset de `paths` elegíveis, **ordem estável** (mesma ordem de
  entrada; sem dedupe obrigatório além de preservar primeira ocorrência se
  houver duplicata — documentar: duplicatas são preservadas como na entrada
  ou colapsadas? **Preservar ordem de entrada e colapsar duplicatas
  mantendo a primeira** — previsível para T14).

Motivo da separação porta × loader: T14 pode obter a árvore do snapshot via
GitPython (T08) e, se preferir, materializar conteúdos de `.gitignore` sem
acoplar o filtro a disco; testes unitários injetam fontes em memória. O helper
`load_gitignore_sources(repo_root: Path) -> list[GitignoreSource]` cobre o
caso local comum e os corners de aninhamento.

Decisão **D-T09-002** — SDK de matching: **`pathspec`** com
`GitWildMatchPattern` (DEC-015). Não usar GitPython `check-ignore` nesta task
(evita dependência de working tree Git real e alinha ENG-013: pathspec fica no
adaptador/módulo de elegibilidade). Proibido parser caseiro de GitWildMatch.

Dependência: adicionar `pathspec` em `[project].dependencies` do
`pyproject.toml` (versão mínima compatível com Python 3.12; pin flexível
`pathspec>=0.12`).

Decisão **D-T09-003** — carregamento de `.gitignore` aninhados:

1. `load_gitignore_sources(repo_root)` percorre o diretório (não segue
   symlinks para fora do root), encontra todos os arquivos nomeados exatamente
   `.gitignore`.
2. Ignora `.git/` (não descer em metadados Git).
3. Para cada arquivo: `relative_dir` = diretório pai relativo ao root (`""` na
   raiz); `lines` = linhas de texto UTF-8 (falha de decode → §2.5).
4. Matching (semântica Git aproximada para MVP):
   - Para cada path candidato, considerar as fontes cuja `relative_dir` é
     prefixo do diretório do path (raiz → mais profundo).
   - Em cada fonte, casar o path **relativo àquela fonte** com um
     `PathSpec.from_lines("gitwildmatch", lines)` (pathspec trata comentários
     `#`, negação `!` e `**` dentro daquele arquivo).
   - **Last match wins** entre padrões que efetivamente casam ao longo das
     fontes aplicáveis (equivalente prático ao Git para ignore/unignore
     aninhado). Se o resultado final for “ignored”, o path é excluído.
5. Repositório **sem** nenhum `.gitignore`: `gitignore_sources=[]` → nenhum
   path é excluído por ignore; só regras de tipo (CSV/imagens) aplicam.
6. Fora de escopo MVP: `.git/info/exclude`, `core.excludesFile` global,
   atributos `export-ignore` — não mencionados em REQ-015/BDD-006.

Decisão **D-T09-004** — inclusão textual vs exclusão CSV/imagens
(**denylist**, não allowlist de linguagens):

Ordem de avaliação por path (após normalização):

1. Se ignorado por `.gitignore` → **excluir**.
2. Se extensão (case-insensitive) ∈ denylist CSV → **excluir**.
3. Se extensão ∈ denylist imagens → **excluir**.
4. Caso contrário → **incluir** (cobre Markdown, Java, Python, TS, YAML,
   Dockerfiles com extensão, etc., e “qualquer linguagem” de REQ-014).

Denylist CSV (mínimo fechado nesta task):

- `.csv`

Denylist imagens (mínimo fechado nesta task):

- Raster / ícones: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.webp`, `.ico`,
  `.tif`, `.tiff`, `.heic`, `.avif`
- Vetorial tratado como imagem (REQ-015 “imagens”): `.svg`

Extensões **não** na denylist (exemplos inclusos): `.md`, `.java`, `.py`,
`.ts`, `.tsx`, `.js`, `.json`, `.yml`, `.yaml`, `.xml`, `.html`, `.css`,
`.properties`, `.gradle`, `.kt`, `.go`, `.rs`, `.c`, `.h`, `.cpp`, `.sql`,
`.sh`, `.toml`, `.ini`, `.txt`, etc. Allowlist explícita de linguagens é
**proibida** (quebraria “independentemente da linguagem”).

Arquivos cujo nome termina com extensão denylist composta (ex.:
`report.CSV`, `Logo.PNG`) usam matching **case-insensitive**.

Decisão **D-T09-005** — arquivos **sem extensão**:

Política: **incluir por padrão**, desde que não cobertos por `.gitignore`.

Motivo: artefatos textuais de desenvolvimento frequentes não têm extensão
(`Makefile`, `Dockerfile`, `LICENSE`, `Jenkinsfile`, `Procfile`). Excluir por
padrão removeria evidências úteis ao Discovery. Binários sem extensão
eventuais não são filtrados por sniffing no MVP (REQ-019 / sem análise de
conteúdo); espera-se que build outputs estejam em paths gitignored
(`target/`, `node_modules/`, `dist/`, etc.).

Documentar e cobrir em testes: `Makefile` e `Dockerfile` incluídos;
`node_modules/pkg` (sem extensão sob dir ignorado) excluído via gitignore.

Decisão **D-T09-006** — sem limites de tamanho (REQ-019):

O filtro **não** recebe nem consulta tamanho de arquivo, não aplica
max-bytes, não corta paths por volume. Qualquer cap futuro seria task nova /
mudança de requisito — fora de T09.

### 2.3 Fluxo

```text
T08 (futuro) / teste:
  paths = ["src/App.java", "docs/a.md", "data.csv", "logo.png",
           "target/x.class", "Makefile"]

load_gitignore_sources(repo_root)  # opcional; ou fixtures
  → [GitignoreSource("", ["target/", "node_modules/"]),
     GitignoreSource("docs", ["*.tmp"])]   # exemplo aninhado

FileEligibilityFilter.filter(paths, sources)
  │
  ├─ normalizar separadores / validar path relativo
  ├─ para cada path:
  │    ├─ match pathspec aninhado? → drop
  │    ├─ ext ∈ {csv}? → drop
  │    ├─ ext ∈ imagens? → drop
  │    └─ else → keep (incl. sem extensão)
  └─ retorna ["src/App.java", "docs/a.md", "Makefile"]
```

Sem `.gitignore`: apenas CSV/imagens saem; textuais e sem extensão permanecem.

### 2.4 Dados

| Dado | Origem | Persistência |
|---|---|---|
| Lista de paths | Snapshot / caller (T14) | Nenhuma |
| Conteúdo `.gitignore` | Disco via helper ou injeção | Ephemeral em memória |
| Denylists | Constantes em `rules.py` | Código versionado |
| Resultado elegível | Retorno da porta | Sem persistência |

Sem schema PostgreSQL, sem rede, sem token.

### 2.5 Erros

| Situação | Tipo | Comportamento |
|---|---|---|
| Path absoluto ou com escape `..` | `EligibilityError` | Rejeitar a chamada (fail-fast); mensagem cita o path ofensivo |
| Path vazio / só `"."` inválido como arquivo | `EligibilityError` ou drop documentado | Preferir rejeitar path vazio; `"."` / `"./"` não são arquivos elegíveis |
| `repo_root` inexistente em `load_gitignore_sources` | `EligibilityError` | Rejeitar loader; porta não é chamada |
| `.gitignore` ilegível / não-UTF-8 | `EligibilityError` | Falha explícita no loader (não silenciar); porta pura não lê disco |
| Linhas inválidas dentro do gitignore | — | pathspec ignora/comentários conforme GitWildMatch; não abortar o filter |
| `gitignore_sources` vazio | — | Válido: só regras de tipo |

Falha no loader durante indexação real será tratada por T14 (falha do repo /
BR-005); T09 só tipa o erro.

### 2.6 Segurança

- Não lê tokens nem `CONFIG_PATH`.
- Não segue symlinks para fora de `repo_root` no loader (evitar path traversal).
- Rejeitar paths absolutos / `..` na porta.
- Logs (se houver): apenas contagens e paths relativos; sem conteúdo de arquivo.

### 2.7 Compatibilidade

- Python 3.12+; OS-agnostic (paths lógicos com `/`).
- Dependência nova: `pathspec` no `pyproject.toml` (venv ENG-009 e imagem T19).
- Windows: normalizar `\` na entrada; matching sempre com `/`.

### 2.8 Observabilidade

- Sem métricas obrigatórias no MVP.
- Comportamento observável via testes: inclusão MD/Java, exclusão CSV/imagens,
  ignore raiz/aninhado, ausência de gitignore, sem extensão, case de extensão.
- Opcional futuro (não T09): contadores included/excluded por razão.

### 2.9 Riscos e rollback

| Risco | Mitigação |
|---|---|
| Semântica Git completa (exclude global, order edge cases) | Escopo MVP: só `.gitignore` em árvore; last-match entre fontes aplicáveis; testes aninhados |
| Denylist incompleta de imagens | Lista mínima fechada + extensível em `rules.py`; CSV explícito |
| Binários sem extensão incluídos | Aceito no MVP; gitignore cobre artefatos típicos; REQ-019 sem sniffing |
| Allowlist acidental de linguagens | D-T09-004 denylist-only; revisão de testes |
| Performance em árvores enormes | pathspec maduro; sem caps; risco de escala já no requirements |

Rollback: remover implementação/`pathspec` do `pyproject.toml` e restaurar
placeholder `eligibility/`; T14 ainda não mesclado nesta porta.

## 3. Critérios de aceite mapeados

| Aceite | Design |
|---|---|
| BDD-006: textuais + MD + Java incluídos | D-T09-004 denylist; exemplos MD/Java nos testes |
| BDD-006: CSV, imagens, gitignore excluídos | D-T09-003 + D-T09-004 |
| Sem `.gitignore` | D-T09-003 item 5 |
| Gitignore aninhado | D-T09-003 + helper |
| Extensões mistas | Mesmo snapshot; regras por path |
| Sem extensão documentado | D-T09-005 include-by-default |
| Sem caps de tamanho | D-T09-006 |
| pathspec / BDD-024 | D-T09-002 + dep em `pyproject.toml` |
| Porta pura e testável | D-T09-001 |

## 4. Arquivos previstos

- `src/github_rag/eligibility/__init__.py` (reexports)
- `src/github_rag/eligibility/filter.py`
- `src/github_rag/eligibility/rules.py`
- `src/github_rag/eligibility/gitignore.py`
- `pyproject.toml` (`pathspec` em dependencies)
- `tests/bdd/` (cenários BDD-006 + corners)
- `tests/unit/eligibility/`
- Artefatos em `spec/.../tasks/T09-file-eligibility/`

## 5. Fora de escopo (confirmação)

- Leitura remota GitHub; indexação Zoekt/RAG; UI; orquestração T14.
- Caps de tamanho / detecção de binário por conteúdo.
- `.git/info/exclude` e excludes globais do usuário.
- Allowlist fechada de linguagens.
- GitPython `check-ignore` como motor de matching.

## 6. Decisões (índice)

| ID | Decisão |
|---|---|
| D-T09-001 | Porta pura `filter(paths, gitignore_sources)`; loader separado |
| D-T09-002 | Matching via `pathspec` GitWildMatch; dep no `pyproject.toml` |
| D-T09-003 | `.gitignore` aninhados: fontes por dir + last-match; vazio = só tipo |
| D-T09-004 | Denylist CSV + imagens; demais textuais incluídos (sem allowlist) |
| D-T09-005 | Sem extensão: incluir por padrão (se não gitignored) |
| D-T09-006 | Sem limites de tamanho no filtro (REQ-019) |
