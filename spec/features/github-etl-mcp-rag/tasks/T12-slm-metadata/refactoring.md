# Refatoração Blue — T12-slm-metadata

| Campo | Valor |
|---|---|
| Task | `T12-slm-metadata` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Resultado | `BLUE_APPROVED_BY_ARCHITECT` |

## Baseline (antes do Blue)

| Item | Valor |
|---|---|
| Testes T12 | `59 passed, 3 subtests` (`tests/unit/index/metadata` + `tests/bdd/test_slm_metadata.py`) |
| Cobertura `openai_slm.py` | 100% (stmts/branches) após testes de branches críticas |
| Pacote `index/metadata` | ~100% (exceto branches triviais de `errors.__str__` cobertas na mesma etapa) |
| Contratos | design/interfaces APPROVED; implementação `APPROVED_BY_ARCHITECT` |
| Escopo Blue | Simplificação estrutural; otimização só com gargalo medido |

## Avaliação

| Candidato | Evidência de gargalo? | Ação |
|---|---|---|
| Chamada `chat.completions.create` / latência SLM | Não — I/O externo; sem benchmark local reproduzível | Nenhuma |
| Parse JSON / normalização de listas | Não — custo desprezível vs rede/modelo | Nenhuma |
| Condicional densa em `_extract_content` | Complexidade local (legibilidade), não perf | Simplificar normalização `content`→`text` |
| Separação types/errors/ports/config/fakes/adapter | Já alinhada a interfaces | Manter |

## Mudanças aplicadas

1. `_extract_content`: separar `None` / coerção `str` / strip vazio — mesmo contrato de erro (`MetadataModelError` “resposta vazia”), fluxo mais linear.

## Resultados (depois)

| Item | Valor |
|---|---|
| Comportamento / contratos | Inalterados (mesmos testes verdes) |
| Suite T12 | deve permanecer verde pós-Blue |
| Otimização de performance | Nenhuma alegada (sem baseline de tempo) |

## Decisão

`BLUE_APPROVED_BY_ARCHITECT` — simplificação mínima de legibilidade; sem otimização especulativa. Qualquer ganho de latência futuro exige medição before/after com runtime SLM real.
