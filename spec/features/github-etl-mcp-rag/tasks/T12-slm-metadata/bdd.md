# BDD — T12-slm-metadata

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T12-slm-metadata` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Rastreabilidade | BDD-007 (metadados); BDD-010 (payload); BDD-024; BR-009, BR-010, BR-023; DEC-006, DEC-015; REQ-022 |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | `READY_FOR_ARCHITECT_REVIEW` | `0.1.0` | MD-01..MD-10 alinhados ao design APPROVED. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | Review OK; MD-04 reforça `intent` no payload. |

## Cenários executáveis

### MD-01 — BDD-007: N chunks → N metadados via porta

**Dado** uma lista de N=`3` `SemanticChunk` distintos (chunk_ids diferentes)  
**E** um `FakeMetadataGenerator` que, para cada chunk, retorna `ChunkMetadata` com o mesmo `chunk_id` e `summary` não vazio  
**Quando** o caller invoca `generator.generate(chunk)` uma vez por chunk (loop N×)  
**Então** obtém exatamente N metadados  
**E** a sequência de `metadata.chunk_id` coincide com a de `chunk.chunk_id`  
**E** nenhum `SemanticChunk` de entrada é mutado

### MD-02 — Aceite: fake generator per-chunk

**Dado** dois `SemanticChunk` com textos/kinds distintos  
**Quando** `FakeMetadataGenerator.generate` é chamado para cada um  
**Então** cada chamada produz metadados associados **somente** àquele `chunk_id`  
**E** summaries/symbols podem diferir por chunk (geração per-chunk, não agregado por arquivo)

### MD-03 — Aceite: falha tipada no meio da lista

**Dado** N=`3` chunks e um `FakeMetadataGenerator` configurado para falhar no 2º `chunk_id`  
**Quando** o caller itera `generate` na ordem  
**Então** a 1ª chamada sucede  
**E** a 2ª levanta `MetadataGenerationError` (subclasse tipada) com `chunk_id` do chunk falho  
**E** a 3ª **não** é alcançada no fluxo que aborta na falha (caller para no erro)  
**E** não há metadados parciais silenciosos retornados no lugar do erro

### MD-04 — BDD-010: metadados serializáveis para payload

**Dado** um `ChunkMetadata` de sucesso (summary não vazio; symbols/keywords tuples; extra imutável)  
**Quando** `to_payload()` é chamado  
**Então** o retorno é `dict[str, object]` JSON-safe  
**E** `symbols`/`keywords` aparecem como `list`  
**E** `extra` aparece como objeto plano (`dict`) de escalares  
**E** `json.dumps(payload)` não levanta  
**E** o payload inclui `chunk_id`, `summary` e `intent` iguais aos do dataclass

### MD-05 — BDD-024: conformidade SDK `openai` (não client HTTP caseiro)

**Dado** a implementação default `OpenAICompatibleMetadataGenerator`  
**Quando** inspecionada a superfície de integração SLM  
**Então** o adaptador usa o pacote oficial `openai` (`OpenAI` client / `chat.completions`)  
**E** não implementa cliente HTTP ad-hoc (`httpx`/`requests`/urllib) como transporte da SLM  
**E** um client injetável fake de completions permite sucesso sem rede real

### MD-06 — Default Qwen Coder 3B (DEC-006)

**Dado** `SlmClientSettings` sem override de modelo **ou** factory/default do adaptador  
**Quando** as settings/default são inspecionados  
**Então** `model == "qwen2.5-coder:3b"` (documentado como Qwen Coder 3B)  
**E** `OpenAICompatibleMetadataGenerator` usa esse model id na chamada de completions quando não sobrescrito

### MD-07 — BR-009: troca de provedor sem alterar orquestrador

**Dado** um caller que depende apenas do Protocol `MetadataGenerator`  
**Quando** injeta `FakeMetadataGenerator` **ou** `OpenAICompatibleMetadataGenerator` (com client fake)  
**Então** ambos satisfazem `isinstance(..., MetadataGenerator)` (`runtime_checkable`)  
**E** o loop N× do caller permanece idêntico (só muda a implementação injetada)  
**E** override de `model`/`base_url` em `SlmClientSettings` não altera a assinatura da porta

### MD-08 — BR-010: sem inventar chunks / sem MCP

**Dado** um `SemanticChunk` de entrada com `chunk_id` conhecido  
**Quando** `MetadataGenerator.generate(chunk)` sucede  
**Então** `ChunkMetadata.chunk_id == chunk.chunk_id` (não inventa outro chunk)  
**E** a porta **não** expõe API de tools MCP / prosa Discovery  
**E** a assinatura de `generate` aceita **apenas** um `SemanticChunk` (não lista, não bytes de arquivo como substituto)

### MD-09 — Erros tipados sem fallback silencioso

**Dado** cenários de falha do adaptador OpenAI-compatible (client que falha / content não-JSON / summary vazio)  
**Quando** `generate` é chamado  
**Então** levanta subclasse de `MetadataGenerationError` (`MetadataModelError` ou `MetadataResponseParseError`)  
**E** nunca retorna `ChunkMetadata` com `summary` vazio em “sucesso”  
**E** `api_key` não aparece na mensagem de erro

### MD-10 — Config inválida → `MetadataConfigError`

**Dado** `SlmClientSettings` / construção do adaptador com `base_url` vazio, `model` vazio ou `timeout_seconds <= 0`  
**Quando** o adaptador é construído (ou settings validados na construção)  
**Então** levanta `MetadataConfigError` (subclasse de `MetadataGenerationError`)  
**E** não inicia chamada ao modelo

## Fora de escopo destes BDD

- UI percentual / progresso (BDD-007 perspectiva UI → T14/T18)
- Upsert/search Qdrant (T13)
- Orquestração e restart BR-005 (T14 consome os erros tipados)
- Tools MCP (T17) — apenas a proibição de uso da porta (MD-08)

## Execução

```bash
python -m pytest tests/bdd/test_slm_metadata.py -q
```
