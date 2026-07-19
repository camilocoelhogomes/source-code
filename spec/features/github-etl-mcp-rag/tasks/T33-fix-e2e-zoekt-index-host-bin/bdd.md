# BDD — T33-fix-e2e-zoekt-index-host-bin

| Campo | Valor |
|---|---|
| Task | `T33-fix-e2e-zoekt-index-host-bin` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |

## Cenários executáveis (unit + integração mock)

### BDD-T33-001 — Env host contém ZOEKT_INDEX_BIN resolvido

**Dado** launcher e2e com compose up mock ok e container zoekt mock disponível  
**Quando** `_start_host_app` monta env via `build_host_delivery_env`  
**Então** `ZOEKT_INDEX_BIN` aponta para wrapper materializado (path absoluto ≠ `zoekt-index`)

### BDD-T33-002 — Wrapper traduz -index para /data/index

**Dado** argv `["-index", "/host/.data/e2e-zoekt-index", "-name", "org/repo", "/tmp/tree"]`  
**Quando** `exec_zoekt_index_cli` executa com doubles  
**Então** `podman exec` recebe `-index /data/index` e árvore copiada via `podman cp`

### BDD-T33-003 — Container ausente fail-fast

**Dado** `podman compose ps -q zoekt` retorna vazio  
**Quando** `resolve_zoekt_index_bin` é invocado  
**Então** levanta `E2eStackError` com mensagem acionável

### BDD-T33-004 — Override explícito preservado

**Dado** env operador com `ZOEKT_INDEX_BIN=/usr/local/bin/zoekt-index`  
**Quando** `resolve_zoekt_index_bin` é invocado  
**Então** retorna path explícito sem materializar wrapper

### BDD-T33-005 — Rastreabilidade BDD-ZIH-001

**Dado** stack e2e healthy (prova manual pós-merge)  
**Quando** indexação de repo elegível dispara  
**Então** histórico **não** contém `FileNotFoundError` para `zoekt-index`  
*(Validação manual / rerun W1; Robot inalterado)*
