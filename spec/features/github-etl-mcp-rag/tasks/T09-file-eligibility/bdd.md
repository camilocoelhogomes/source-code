# BDD — T09-file-eligibility

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T09-file-eligibility` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-18 |
| Versão BDD | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T09-file-eligibility` |
| Escopo desta etapa | Somente BDD executáveis dos critérios de aceite T09 |
| Rastreabilidade | REQ-014, REQ-015, REQ-019; BR-023; DEC-015; BDD-006; BDD-024; D-T09-001..006 |

## Rastreabilidade

| Cenário | Aceite / decisão |
|---|---|
| ELIG-01 | BDD-006 — incluir textuais/MD/Java; excluir CSV, imagens, gitignore |
| ELIG-02 | Corner — repositório sem `.gitignore` (D-T09-003 item 5) |
| ELIG-03 | Corner — `.gitignore` aninhado (D-T09-003) |
| ELIG-04 | Corner — extensões mistas no mesmo snapshot (D-T09-004) |
| ELIG-05 | Corner — sem extensão: Makefile/Dockerfile incluídos; sob dir gitignored excluídos (D-T09-005) |
| ELIG-06 | BDD-024 / D-T09-002 — matching via `pathspec` GitWildMatch (não parser caseiro) |
| ELIG-07 | REQ-019 / D-T09-006 — sem caps de tamanho no filtro |

## Artefatos executáveis

| Artefato | Caminho |
|---|---|
| Steps / asserts | `tests/bdd/test_file_eligibility.py` |

## Como executar

```bash
python -m pytest tests/bdd/test_file_eligibility.py -q
```

## Cenários

### ELIG-01 — BDD-006: filtrar arquivos elegíveis

**Dado** um snapshot com paths relativos:
`src/App.java`, `docs/readme.md`, `src/main.py`, `data/report.csv`, `assets/logo.png`, `target/Foo.class`  
**E** `gitignore_sources` com raiz ignorando `target/`  
**Quando** `PathspecFileEligibilityFilter().filter(paths, gitignore_sources)` for executado  
**Então** o resultado deve conter `src/App.java`, `docs/readme.md` e `src/main.py`  
**E** não deve conter `data/report.csv`, `assets/logo.png` nem `target/Foo.class`  
**E** a ordem dos elegíveis deve seguir a ordem de entrada.

### ELIG-02 — Corner: repositório sem `.gitignore`

**Dado** `gitignore_sources == []` (nenhum `.gitignore`)  
**E** paths `src/App.java`, `notes.md`, `data.csv`, `img/photo.jpg`  
**Quando** o filtro for executado  
**Então** `src/App.java` e `notes.md` devem ser incluídos  
**E** `data.csv` e `img/photo.jpg` devem ser excluídos somente por regra de tipo  
**E** nenhum path textual deve ser excluído por ignore.

### ELIG-03 — Corner: `.gitignore` aninhado

**Dado** fontes:
- raiz `""` com `node_modules/`
- aninhado `"docs"` com `*.tmp`  
**E** paths `src/Service.java`, `docs/guide.md`, `docs/scratch.tmp`, `node_modules/pkg/index.js`  
**Quando** o filtro for executado  
**Então** `src/Service.java` e `docs/guide.md` devem ser incluídos  
**E** `docs/scratch.tmp` e `node_modules/pkg/index.js` devem ser excluídos  
**E** (variante loader) `load_gitignore_sources(repo_root)` sobre árvore com os mesmos `.gitignore` deve produzir fontes equivalentes e o mesmo resultado de filtro.

### ELIG-04 — Corner: extensões mistas no mesmo snapshot

**Dado** um único snapshot com paths mistos:
`.md`, `.java`, `.py`, `.ts`, `.yml`, `.csv`, `.png`, `.svg`, `.jpg`, `.JPEG` (case misto)  
**E** `gitignore_sources` vazio  
**Quando** o filtro for executado  
**Então** textuais (md/java/py/ts/yml) devem ser incluídos  
**E** csv e imagens (png/svg/jpg/JPEG) devem ser excluídos  
**E** matching de extensão denylist deve ser case-insensitive (`report.CSV`, `Logo.PNG`).

### ELIG-05 — Corner: arquivos sem extensão

**Dado** fontes com `node_modules/` na raiz  
**E** paths `Makefile`, `Dockerfile`, `LICENSE`, `node_modules/pkg`  
**Quando** o filtro for executado  
**Então** `Makefile`, `Dockerfile` e `LICENSE` devem ser incluídos (D-T09-005 include-by-default)  
**E** `node_modules/pkg` deve ser excluído via gitignore.

### ELIG-06 — BDD-024: matching via pathspec (não parser caseiro)

**Dado** `gitignore_sources` com padrões GitWildMatch: comentário `#`, negação `!` e glob  
**Quando** o filtro for executado sobre paths que exercitam esses padrões  
**Então** o comportamento deve seguir GitWildMatch (comentário ignorado; negação re-inclui; glob casa)  
**E** o módulo de implementação deve importar/usar a biblioteca `pathspec` (inspeção de import/código)  
**E** não deve implementar parser caseiro de GitWildMatch.

### ELIG-07 — Sem caps de tamanho (REQ-019 / D-T09-006)

**Dado** paths textuais elegíveis (ex.: `src/HugeService.java`, `docs/big.md`)  
**E** `gitignore_sources` vazio  
**Quando** `filter` for invocado  
**Então** ambos devem ser incluídos  
**E** a assinatura de `filter` não deve aceitar parâmetros de tamanho (`size`, `max_bytes`, `max_size` ou equivalentes)  
**E** o filtro não deve rejeitar paths por volume/tamanho.

## Fora de escopo destes BDD

- Caps futuros de tamanho / sniffing de binário por conteúdo
- `.git/info/exclude` e excludes globais
- Indexação, UI, orquestração T14
- Testes unitários de contrato (etapa pós-interfaces)

## Estado red esperado (pré-implementação)

Os testes em `tests/bdd/test_file_eligibility.py` devem falhar com `ImportError` (módulos/símbolos `github_rag.eligibility.filter` / `gitignore` ainda inexistentes) ou `NotImplementedError` se houver stub sem implementação.
