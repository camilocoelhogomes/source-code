# Unit test plan — T36

Estado: `APPROVED_BY_ARCHITECT`

| ID | Arquivo | Cenário |
|---|---|---|
| UT-T36-01 | `test_zoekt_bin_resolver.py` | PS filter `name=_zoekt-cli_` |
| UT-T36-02 | `test_zoekt_bin_resolver.py` | argv exec com `-index /data/index -name` |
| UT-T36-03 | `test_zoekt_bin_resolver.py` | override `ZOEKT_CLI_CONTAINER_FILTER` |
| UT-T36-04 | `test_zoekt_bin_resolver.py` | shebang `sys.executable`, sem env python3 |

Regressão: suite UT-P08 + launcher T35 defer.
