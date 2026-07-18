# Unit test plan — T06-local-discovery

| Campo | Valor |
|---|---|
| Task | `T06-local-discovery` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Cobertura alvo | ≥95% global; 100% módulos novos |

## git_fs.py

| ID | Cenário | Tipo |
|---|---|---|
| UT-GFS-01 | `parse_file_url` POSIX com glob `file:///repos/*` | happy |
| UT-GFS-02 | `parse_file_url` POSIX sem glob | happy |
| UT-GFS-03 | `parse_file_url` Windows `file:///C:/repos/*` | happy |
| UT-GFS-04 | `is_accessible` path existente vs ausente | corner |
| UT-GFS-05 | `expand_candidates` glob retorna só diretórios | happy |
| UT-GFS-06 | `expand_candidates` pattern None → base única | corner |
| UT-GFS-07 | `inspect_repo` `.git` dir + ref main | happy |
| UT-GFS-08 | `inspect_repo` `.git` file (gitdir) | corner |
| UT-GFS-09 | `inspect_repo` main só em packed-refs | corner |
| UT-GFS-10 | `inspect_repo` sem `.git` | invalid |
| UT-GFS-11 | `inspect_repo` Git sem main | invalid |
| UT-GFS-12 | `inspect_repo` path não diretório | invalid |

## discovery.py

| ID | Cenário | Tipo |
|---|---|---|
| UT-DIS-01 | `discover_connection` feliz com glob | happy |
| UT-DIS-02 | base inacessível → issue, repos vazio | error |
| UT-DIS-03 | path inválido gera issue, válidos permanecem | partial |
| UT-DIS-04 | `discover` múltiplas conexões git isoladas | concurrency |
| UT-DIS-05 | `discover` ignora github | boundary |
| UT-DIS-06 | `repo_identifier` = basename | contract |
| UT-DIS-07 | inspector injetado usado | DI |

## Execução

```bash
python -m pytest tests/unit/sources/local/ tests/bdd/test_local_discovery.py -q
```

Os testes devem falhar (NotImplementedError) até a implementação TDD.
