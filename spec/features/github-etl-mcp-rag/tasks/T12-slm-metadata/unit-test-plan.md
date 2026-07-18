# Plano de testes unitários — T12-slm-metadata

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T12-slm-metadata` |
| Autor | QA Engineer + Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Interfaces base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | `READY_FOR_ARCHITECT_REVIEW` | `0.1.0` | Matriz UT-T/E/P/C/F/O/X + RED esperado. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | RED confirmado (7× ModuleNotFoundError); UT-E03 reforçado. |

## Artefatos

| Artefato | Caminho |
|---|---|
| Helpers / fixtures | `tests/unit/index/metadata/helpers.py` |
| Types / payload | `tests/unit/index/metadata/test_types.py` |
| Errors | `tests/unit/index/metadata/test_errors.py` |
| Ports / Protocol | `tests/unit/index/metadata/test_ports.py` |
| Config / settings | `tests/unit/index/metadata/test_config.py` |
| Fake generator | `tests/unit/index/metadata/test_fakes.py` |
| OpenAI adaptador | `tests/unit/index/metadata/test_openai_slm.py` |
| BDD | `tests/bdd/test_slm_metadata.py` |

## Matriz

| ID | Foco | Entrada | Esperado | Rastreabilidade | Arquivo |
|---|---|---|---|---|---|
| UT-T01 | `ChunkMetadata` frozen | mutate attr | `FrozenInstanceError` | I-T12-003 | `test_types.py` |
| UT-T02 | `to_payload` JSON-safe | metadata completa | lists + extra dict; `json.dumps` ok | BDD-010 / MD-04 | `test_types.py` |
| UT-T03 | `to_payload` symbols/keywords vazios | tuples `()` | lists `[]` | corner vazio | `test_types.py` |
| UT-T04 | `to_payload` extra escalares | bool/int/float/None/str | valores preservados | schema MVP | `test_types.py` |
| UT-T05 | `extra` imutável | tentar mutar via payload only | dataclass frozen; extra é tuple | I-T12-003 | `test_types.py` |
| UT-E01 | hierarquia erros | subclasses | `issubclass(..., MetadataGenerationError)` | D-T12-006 | `test_errors.py` |
| UT-E02 | attrs chunk_id/path | `MetadataModelError(chunk_id=..., path=...)` | attrs + str contém ids | observabilidade | `test_errors.py` |
| UT-E03 | mensagem sem secret | message com hint do campo api_key; sem atributo `api_key` | str/repr sem valor secret; `hasattr(err,"api_key")` é False | segurança §7 | `test_errors.py` |
| UT-P01 | Protocol runtime | Fake / OpenAI adapter | `isinstance(..., MetadataGenerator)` | BR-009 / MD-07 | `test_ports.py` |
| UT-P02 | assinatura `generate` | inspect | exatamente 1 param posicional `chunk` (além self) | D-T12-003 / MD-08 | `test_ports.py` |
| UT-C01 | default model | `SlmClientSettings(base_url=...)` | `model == "qwen2.5-coder:3b"` | DEC-006 / MD-06 | `test_config.py` |
| UT-C02 | default api_key/timeout | settings mínimos | `api_key=="local"`, `timeout_seconds==60.0` | I-T12-006 | `test_config.py` |
| UT-C03 | settings frozen | mutate | `FrozenInstanceError` | imutabilidade | `test_config.py` |
| UT-C04 | override model | `model="other"` | valor aplicado | BR-009 | `test_config.py` |
| UT-F01 | fake per-chunk | 2 chunks | 2 metadados com chunk_ids corretos | aceite / MD-02 | `test_fakes.py` |
| UT-F02 | fake fail mid-list | fail 2º id | 1 ok + `MetadataGenerationError` | aceite / MD-03 | `test_fakes.py` |
| UT-F03 | fake by_chunk_id | mapa explícito | retorna metadata mapeada | contrato fake | `test_fakes.py` |
| UT-F04 | fake não inventa chunk_id | chunk A | metadata.chunk_id == A | BR-010 | `test_fakes.py` |
| UT-F05 | fake idempotente | 2× mesmo chunk | mesmos campos essenciais | idempotência | `test_fakes.py` |
| UT-O01 | sucesso com client fake | JSON válido | `ChunkMetadata` summary/symbols | fluxo feliz | `test_openai_slm.py` |
| UT-O02 | content não-JSON | prosa markdown | `MetadataResponseParseError` | MD-09 | `test_openai_slm.py` |
| UT-O03 | summary vazio | JSON `summary:""` | `MetadataResponseParseError` | D-T12 / proibições | `test_openai_slm.py` |
| UT-O04 | falha SDK/rede | client raises | `MetadataModelError` | MD-09 | `test_openai_slm.py` |
| UT-O05 | resposta vazia | content `None`/vazio | `MetadataModelError` ou parse tipado | corner | `test_openai_slm.py` |
| UT-O06 | default model na chamada | settings default | create chamado com `qwen2.5-coder:3b` | MD-06 | `test_openai_slm.py` |
| UT-O07 | config inválida | base_url `""` / timeout `0` | `MetadataConfigError` | MD-10 | `test_openai_slm.py` |
| UT-O08 | chunk_id preservado | entrada conhecida | output.chunk_id == input | BR-010 | `test_openai_slm.py` |
| UT-O09 | SDK openai | inspect módulo/adapter | importa/`OpenAI` usado; sem httpx client SLM | BDD-024 / MD-05 | `test_openai_slm.py` |
| UT-O10 | symbols/keywords normalizados | listas no JSON | tuples sem strings vazias | parse | `test_openai_slm.py` |
| UT-O11 | não muta SemanticChunk | generate sucesso | chunk inalterado | invariante | `test_openai_slm.py` |
| UT-O12 | intent omitido | JSON sem intent | `intent == ""` | design §4.2 | `test_openai_slm.py` |

## Extremos / inválidos / vazios

| ID | Caso | Esperado | Arquivo |
|---|---|---|---|
| UT-X01 | N=0 loop caller | zero chamadas; sem erro da porta | `test_fakes.py` (documentado) / BDD |
| UT-X02 | symbols com string vazia no JSON | rejeita parse **ou** filtra — contrato: sem strings vazias no sucesso | `test_openai_slm.py` |
| UT-X03 | JSON array root | `MetadataResponseParseError` | `test_openai_slm.py` |
| UT-X04 | extra nested object no JSON | parse error (MVP sem nested) | `test_openai_slm.py` |
| UT-X05 | model override no construtor | completions usa model override | `test_openai_slm.py` |
| UT-X06 | duas gerações sequenciais independentes | sem estado cruzado no fake/adapter | `test_fakes.py` / `test_openai_slm.py` |

## Red esperado

Antes da implementação, imports de `github_rag.index.metadata.types|errors|ports|config|fakes|openai_slm` falham (`ImportError` / `ModuleNotFoundError`) ou atributos ausentes (`AttributeError`). Demonstrar com:

```bash
python -m pytest tests/unit/index/metadata tests/bdd/test_slm_metadata.py -q
```
