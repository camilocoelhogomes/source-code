# Unit test plan — T35

| ID | Cenário | Esperado |
|---|---|---|
| UT-T35-01 | exec_zoekt_index_cli | mkdir podman exec antes de cp |
| UT-T35-02 | cp subprocess timeout | E2eStackError |
| UT-T35-03 | mkdir falha | E2eStackError, cp não executado |
| UT-T35-04 | enqueue repo INDEXING | id na fila; run_until_idle completa |
| UT-T35-05 | reconcile defer_enqueue | tip atualizado; estado não queued |
| UT-T35-06 | launcher e2e compose | host env contém E2E_DEFER_STARTUP_INDEX=1 |
