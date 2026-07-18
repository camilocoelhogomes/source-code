# BDD — T05-github-discovery

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T05-github-discovery` |
| Autor | Implementation Task Runner (QA step) |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão BDD | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T05-github-discovery` |
| Rastreabilidade | REQ-010, REQ-011, REQ-041; BR-007, BR-008, BR-019, BR-022; BDD-001, BDD-014, BDD-019 |

## Rastreabilidade

| Cenário | Aceite / requisito |
|---|---|
| GH-01 | BDD-001 — somente repos que casam wildcards |
| GH-02 | BDD-019 — token via env referenciada; não no resultado |
| GH-03 | BDD-014 — token ausente de erros desta camada |
| GH-04 | BR-022 — `repos` vazio ⇒ nenhum repo descoberto |
| GH-05 | REQ-011 — públicos e privados incluídos se acessíveis |
| GH-06 | Paginação agrega todas as páginas |
| GH-07 | Falha de auth sem vazar segredo |

## Artefatos executáveis

| Artefato | Caminho |
|---|---|
| Steps / asserts | `tests/bdd/test_github_discovery.py` |

## Como executar

```bash
python -m pytest tests/bdd/test_github_discovery.py -q
```

## Cenários

### GH-01 — Descobrir repos por wildcards (BDD-001)

**Dado** uma conexão GitHub com org `my-org` e padrões `my-org/microservice-*`, `my-org/*-api`  
**E** a API retorna repos acessíveis incluindo `my-org/microservice-auth`, `my-org/user-api`, `my-org/other-tool`, `my-org/secret-internal`  
**Quando** `GitHubRepoDiscovery.discover` for executado  
**Então** o resultado deve conter `my-org/microservice-auth` e `my-org/user-api`  
**E** não deve conter `my-org/other-tool` nem `my-org/secret-internal`.

### GH-02 — Token do ambiente, não no resultado (BDD-019)

**Dado** conexão cujo `secret` foi resolvido de variável de ambiente  
**Quando** a descoberta for bem-sucedida  
**Então** nenhum item do resultado deve conter o valor do token  
**E** `str`/`repr` de cada `DiscoveredGitHubRepo` não deve conter o token.

### GH-03 — Proteger token em erros (BDD-014)

**Dado** um token com valor conhecido  
**Quando** a descoberta falhar por erro de autenticação simulado  
**Então** `str(exc)` e `repr(exc)` não devem conter o valor do token.

### GH-04 — Lista de inclusão vazia

**Dado** conexão com `repos` vazio  
**Quando** a descoberta for executada  
**Então** o resultado deve ser vazio mesmo que a API retorne repos.

### GH-05 — Públicos e privados acessíveis (REQ-011)

**Dado** padrão `my-org/*`  
**E** API retorna repo público e privado da org  
**Quando** a descoberta for executada  
**Então** ambos devem aparecer no resultado.

### GH-06 — Paginação

**Dado** client que retorna repos em duas páginas  
**Quando** a descoberta for executada  
**Então** todos os repos de todas as páginas elegíveis devem estar no resultado.

### GH-07 — Falha de autenticação

**Dado** client que simula HTTP 401  
**Quando** a descoberta for executada  
**Então** deve levantar `GitHubDiscoveryError`  
**E** a mensagem não deve expor o token.
