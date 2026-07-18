# BDD — T06-local-discovery

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T06-local-discovery` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Rastreabilidade | BDD-016, BDD-018; REQ-034, REQ-040; BR-013–015; DEC-010 |

## Cenários executáveis

### LOC-01 — BDD-016: descobrir repositórios locais montados com `main`

**Dado** um `AppConfig` com conexão `local-microservices` (`type: git`, `url: file://<mount>/*`)  
**E** um volume montado em `<mount>` com diretórios Git válidos contendo branch `main`  
**Quando** `LocalRepoDiscovery().discover(config)` é executado  
**Então** cada repo válido aparece em `result.repos` com `origin == RepoOrigin.LOCAL`  
**E** `connection_name == "local-microservices"`  
**E** `local_path` aponta para o diretório montado absoluto  
**E** `repo_identifier` identifica o repositório de forma estável  

### LOC-02 — BDD-016: ignorar paths sem Git ou sem `main`

**Dado** o mesmo mount com subpastas: repo válido com `main`, pasta comum, repo Git sem `main`  
**Quando** a descoberta é executada  
**Então** somente o repo com Git válido e `main` entra em `result.repos`  
**E** os paths inválidos geram entradas em `result.issues`  

### LOC-03 — BDD-018: volume local ausente ou inacessível

**Dado** conexão `git` apontando para `file:///repos/missing/*`  
**E** o path base `/repos/missing` não existe ou não é legível  
**Quando** a descoberta é executada  
**Então** `result.repos` não contém candidatos dessa conexão  
**E** `result.issues` registra erro citando conexão e path  

### LOC-04 — Falha isolada por conexão (BR-021 descoberta)

**Dado** `AppConfig` com duas conexões `git`: uma inacessível e outra com repos válidos  
**Quando** a descoberta é executada  
**Então** repos da conexão válida aparecem em `result.repos`  
**E** a conexão inacessível contribui apenas com `issues`, sem abortar a outra  

### LOC-05 — URL sem glob (repo único)

**Dado** conexão `git` com `url: file://<mount>/single-repo` (sem `*`)  
**E** `<mount>/single-repo` é Git válido com `main`  
**Quando** a descoberta é executada  
**Então** um único `DiscoveredLocalRepo` é retornado  

### LOC-06 — Conexões GitHub ignoradas

**Dado** `AppConfig` misto (`github` + `git`)  
**Quando** `LocalRepoDiscovery().discover(config)`  
**Então** somente conexões `git` são processadas  

## Fora de escopo destes BDD

- UI/checkbox/indexação (BDD-016 perspectiva UI → T07/T18)
- Snapshot de `main`/uncommitted (BDD-017 → T08/T14)
- Persistência catálogo (T07)

## Execução

```bash
python -m pytest tests/bdd/test_local_discovery.py -q
```
