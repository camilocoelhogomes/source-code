# BDD — T36-fix-zoekt-index-cli-binary-e2e

| ID | Cenário | Verificação |
|---|---|---|
| BDD-T36-001 | Sidecar zoekt-cli no compose dev+e2e | `docker-compose.*.yml` serviço `zoekt-cli` |
| BDD-T36-002 | Wrapper shebang venv | `materialize_zoekt_index_wrapper` → `#!{sys.executable}` |
| BDD-T36-003 | Exec no container zoekt-cli | `find_zoekt_container_id` filtro `name=_zoekt-cli_` |
| BDD-T36-004 | Contrato T10 argv | `exec_zoekt_index_cli` → `-index /data/index -name <repo> <tree>` |
| BDD-T36-005 | Indexação sample-local sem erro CLI | e2e run (Robot BDD-002) |

Estado: `APPROVED_BY_ARCHITECT`
