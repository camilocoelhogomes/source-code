# Reviews — T27-gap-sdk-dec015-conformity

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T27-gap-sdk-dec015-conformity` |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | QA Engineer | `TESTS_READY_FOR_REVIEW` | `0.1.0` | Unitários prontos para gate Architect. Ver `unit-test-plan.md` 0.1.0. Suíte nova `tests/bdd/test_dec015_conformity.py` + `tests/bdd/support/dec015_pins.py` (I-T27-001) + promoção `tests/unit/ui/helpers.py` (I-T27-002) + refactors comportamentalmente neutros de `TestCD05SdkManifest`/`TestUiImports`. RED nomeado e íntegro em `TestDEC01PinsVersionMatrix::test_all_dec015_packages_declare_a_version_range` (`alembic`, `psycopg[binary]` sem faixa de versão no `pyproject.toml` — gap real, fora de `src/github_rag/**`). Restante da suíte nova já verde nesta etapa porque a produção (T05/T08/T10/T15/T17/T18/T20) já usa os SDKs oficiais — consolidação de evidência, não implementação nova (design §2/§8). Full suite: 1 falhado (o RED nomeado) / 1253 passados / 2 pulados (pré-existentes, sem Docker); cobertura global 96.53% (gate ≥95%). Corner case observado e não corrigido (fora de escopo QA): `tests/bdd/test_local_discovery_git_sdk.py`/`test_dec015_conformity.py::TestDEC03GitPythonReference` falha por `ImportError` de import circular pré-existente (`github_rag.catalog.sync` ↔ `github_rag.sources.local.discovery`) **somente quando executado de forma isolada**; passa na suíte completa (ordem de import diferente). Não é regressão desta task — reportar ao Architect para avaliar se abre task de hardening separada. Aguardando review do Architect antes de qualquer implementação "verde" (fechar o RED de `pyproject.toml`) pelo Developer. |
