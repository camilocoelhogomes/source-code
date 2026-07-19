# BDD — T29 fix-e2e-env-loader-failfast

| Campo | Valor |
|---|---|
| Estado | `APPROVED_BY_ARCHITECT` |

## BDD-T29-01 — INDEX_CRON seguro no .env.example

**Dado** `.env.example` versionado  
**Quando** operador copia para `.env` e usa loader Python  
**Então** `INDEX_CRON` é `"0 2 * * *"` com aspas no example  
**E** loader parseia valor com espaços sem erro de shell

## BDD-T29-02 — Loader Python no entrypoint e2e

**Dado** `.env` local com `INDEX_CRON=0 2 * * *` (sem aspas) e `E2E_GITHUB_TOKEN=ghp_test`  
**Quando** `parse_dotenv_text` processa o conteúdo  
**Então** retorna `{"INDEX_CRON": "0 2 * * *", "E2E_GITHUB_TOKEN": "ghp_test"}`  
**E** `load_dotenv_file` aplica em `os.environ` sem invocar shell

## BDD-T29-03 — README documenta env seguro

**Dado** operador segue `e2e/README.md`  
**Então** instruções recomendam `python -m github_rag.e2e` (loader automático)  
**E** desaconselham `source .env` para valores com espaços

## BDD-T29-04 — Fail-fast host app exit antes do healthy

**Dado** `PodmanE2eStackLauncher` com `host_app=True` e processo filho que exitou com code=1  
**Quando** `wait_healthy()` é invocado  
**Então** levanta `E2eStackError` imediatamente (<1s)  
**E** mensagem contém `exit`/`code=1`  
**E** stderr sanitizado (sem token)

## BDD-T29-05 — Fail-fast host app exit durante poll

**Dado** launcher com host app rodando e healthz indisponível  
**Quando** processo filho exita durante o loop de poll  
**Então** `wait_healthy` levanta `E2eStackError` na próxima iteração  
**E** não aguarda timeout de 600s

## Aprovação

| Gate | Decisão | Autor | Data |
|---|---|---|---|
| Architect BDD review | `APPROVED_BY_ARCHITECT` | tech-lead-architect | 2026-07-19 |
