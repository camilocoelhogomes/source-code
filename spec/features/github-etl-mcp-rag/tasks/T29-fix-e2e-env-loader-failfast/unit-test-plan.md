# Unit test plan — T29

| ID | Alvo | Cenário | Esperado |
|---|---|---|---|
| UT-T29-01 | `parse_dotenv_text` | `INDEX_CRON=0 2 * * *` | valor com espaços |
| UT-T29-02 | `parse_dotenv_text` | `KEY="quoted value"` | aspas removidas |
| UT-T29-03 | `parse_dotenv_text` | `# comment` e linha vazia | ignoradas |
| UT-T29-04 | `parse_dotenv_text` | linha sem `=` | ignorada |
| UT-T29-05 | `load_dotenv_file` | arquivo inexistente | `{}`, environ intacto |
| UT-T29-06 | `load_dotenv_file` | arquivo válido, override=False | só chaves ausentes |
| UT-T29-07 | `load_dotenv_file` | override=True | sobrescreve |
| UT-T29-08 | `wait_healthy` | host exit antes do loop | `E2eStackError` imediato |
| UT-T29-09 | `wait_healthy` | host exit durante poll | `E2eStackError`, sem timeout |
| UT-T29-10 | `wait_healthy` fail-fast | stderr com token | redacted |

Arquivo: `tests/unit/e2e/test_env_loader.py`, `tests/unit/e2e/test_launcher.py` (UT-T29-08..10).

Estado: `APPROVED_BY_ARCHITECT` — 2026-07-19
