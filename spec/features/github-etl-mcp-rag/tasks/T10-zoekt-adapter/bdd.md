# BDD — T10-zoekt-adapter

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T10-zoekt-adapter` |
| Autor | QA Engineer |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-18 |
| Versão BDD | `0.1.0` |
| Design base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T10-zoekt-adapter` |
| Escopo desta etapa | Somente BDD executáveis dos critérios de aceite T10 |
| Rastreabilidade | DEC-002, DEC-016; REQ-002; BR-023; BDD-009; BDD-024; ENG-012/D-T10-006; D-T10-003..005 |

## Rastreabilidade

| Cenário | Aceite / decisão |
|---|---|
| ZOEKT-01 | BDD-009 — indexação bem-sucedida torna conteúdo buscável por match exato (porta `ExactCodeIndex` + `FakeExactCodeIndex`) |
| ZOEKT-02 | Metadados mínimos — `repository`, `path`, `commit`, `snippet` em `ExactMatch` |
| ZOEKT-03 | Falha tipada — `ExactCodeIndexError` para T14 (restart de repo) |
| ZOEKT-04 | BDD-024 / DEC-016 — double/fake injetável; sem Zoekt real; contrato da porta |
| ZOEKT-05 | `delete_repository` obrigatório (D-T10-006) remove entradas do repo |
| ZOEKT-06 | Corner — `files` vazio em `index` = no-op sucesso |
| ZOEKT-07 | Corner — `pattern` vazio em `search` = lista vazia |
| ZOEKT-08 | Corner — reindex do conjunto remove path ausente (ENG-012 / D-T10-006) |

## Artefatos executáveis

| Artefato | Caminho |
|---|---|
| Steps / asserts | `tests/bdd/test_zoekt_adapter.py` |

## Como executar

```bash
python -m pytest tests/bdd/test_zoekt_adapter.py -q
```

## Cenários

### ZOEKT-01 — Indexação torna conteúdo buscável (BDD-009)

**Dado** um `FakeExactCodeIndex` (porta `ExactCodeIndex`)  
**E** um arquivo `FileToIndex` com `repository="acme/api"`, `path="src/main.py"`, `commit="abc123"`, `content` contendo a literal `def authenticate`  
**Quando** `index("acme/api", "abc123", files)` for executado  
**E** `search(ExactSearchQuery(pattern="def authenticate"))` for executado  
**Então** o resultado deve conter ao menos um `ExactMatch` cujo conteúdo/snippet reflita o match exato da literal  
**E** o match deve referir o repositório e o path indexados.

### ZOEKT-02 — Metadados repository, path, commit, snippet

**Dado** índice populado via `FakeExactCodeIndex` com um arquivo conhecido  
**Quando** a busca por uma substring presente no conteúdo for bem-sucedida  
**Então** cada `ExactMatch` deve expor `repository`, `path`, `commit` e `snippet` não vazios  
**E** `commit` deve ser o SHA tip indexado (`abc123` no fixture)  
**E** `snippet` deve conter a substring buscada.

### ZOEKT-03 — Falha tipada ExactCodeIndexError (para T14)

**Dado** um `FakeExactCodeIndex` configurado para falhar na operação `index` (ou `search`)  
**Quando** a operação for executada  
**Então** deve levantar `ExactCodeIndexError`  
**E** a mensagem / representação não deve conter segredos (tokens).

### ZOEKT-04 — Fake/double sem Zoekt real (BDD-024 / DEC-016)

**Dado** o contrato da porta `ExactCodeIndex` (`index`, `search`, `delete_repository`)  
**Quando** os cenários BDD desta task forem exercidos  
**Então** devem usar apenas `FakeExactCodeIndex` (ou double equivalente injetável)  
**E** `FakeExactCodeIndex` deve satisfazer o Protocol `ExactCodeIndex`  
**E** nenhum processo/container Zoekt real deve ser necessário para o aceite mínimo T10.

### ZOEKT-05 — delete_repository remove índice do repositório

**Dado** dois repositórios indexados (`acme/api` e `acme/other`) com conteúdo distinto buscável  
**Quando** `delete_repository("acme/api")` for executado  
**Então** buscas no padrão de `acme/api` não devem mais retornar matches desse repo  
**E** o conteúdo de `acme/other` permanece buscável  
**E** `delete_repository` de repo sem artefatos é no-op sucesso.

### ZOEKT-06 — Corner: files vazio = no-op

**Dado** um `FakeExactCodeIndex` vazio  
**Quando** `index("acme/api", "abc123", files=[])` for executado  
**Então** a operação completa sem erro  
**E** buscas subsequentes por qualquer padrão retornam lista vazia (nada foi indexado).

### ZOEKT-07 — Corner: pattern vazio = lista vazia

**Dado** um índice com conteúdo indexado  
**Quando** `search(ExactSearchQuery(pattern=""))` for executado  
**Então** o resultado deve ser uma sequência vazia  
**E** não deve levantar `ExactCodeIndexError` (busca sem termo não é falha de infra).

### ZOEKT-08 — Corner: reindex remove path ausente do conjunto

**Dado** índice com `src/a.py` e `src/b.py` no tip `c1`  
**Quando** `index` for chamado novamente para o mesmo `repository` com tip `c2` contendo apenas `src/a.py` (conjunto elegível atual)  
**Então** busca que só existia em `src/b.py` não retorna match  
**E** o conteúdo restante em `src/a.py` permanece buscável  
**E** matches remanescentes carregam `commit="c2"`.
