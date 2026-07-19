# BDD — T34-fix-host-local-repos-path-resolution

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T34-fix-host-local-repos-path-resolution` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Rastreabilidade | BDD-016; F-W1-008 |

## Cenários executáveis

Arquivo: `tests/bdd/test_local_discovery.py` (LOC-T34-01..02)

### LOC-T34-01 — BDD-016: `file:///repos/*` + `HOST_REPOS` descobre repos no host

**Dado** config com conexão git `url: file:///repos/*`
**E** variável `HOST_REPOS` aponta para diretório montável com repo Git válido + `main`
**Quando** `LocalRepoDiscovery(host_repos=HOST_REPOS).discover(config)`
**Então** ≥1 repo com `origin=local`
**E** `issues` vazio para conexão acessível

### LOC-T34-02 — BDD-018: subpath `/repos/x` remapeado; volume ausente → issue

**Dado** config `file:///repos/__missing__/*`
**E** `HOST_REPOS` aponta para diretório existente sem `__missing__`
**Quando** discovery executa
**Então** 0 repos
**E** issue contém `inaccessible` ou `no matching` (path pós-remap)
