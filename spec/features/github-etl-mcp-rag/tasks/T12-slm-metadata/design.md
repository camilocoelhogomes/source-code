# Design — T12-slm-metadata

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T12-slm-metadata` |
| Autor | Implementation Task Runner + Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Branch | `feature/github-etl-mcp-rag-T12-slm-metadata` |
| Base | `feature/github-etl-mcp-rag-T11-treesitter-chunker` (contrato `SemanticChunk`) |
| Rastreabilidade | BR-009, BR-010, BR-023; DEC-006, DEC-015; REQ-022; BDD-007, BDD-010; BDD-024 |

## 0. Histórico de revisão Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Design inicial: porta `MetadataGenerator`, adaptador `openai`, default Qwen Coder 3B, entrada=1 `SemanticChunk`, erros tipados, proibições chunk/MCP; `ChunkMetadata.extra` imutável (sem `dict` mutável em frozen). |

## 1. Contexto

T11 entrega a unidade exclusiva de chunk RAG (`SemanticChunk`). T12 enriquece **cada** chunk com metadados contextuais gerados por SLM local (BR-010, DEC-006), para o payload Qdrant (T13) e o loop do orquestrador (T14). A troca de provedor/modelo ocorre sem alterar o orquestrador (BR-009).

Fora de escopo: tools MCP / prosa Discovery; upsert Qdrant (T13); UI chat (T16/T18 podem reutilizar a porta depois); orquestração e registro REQ-022 (T14); embeddings (porta distinta em T13).

## 2. Problema

Chunks Tree-sitter precisam de metadados contextuais serializáveis **por chunk** (não por arquivo agregado como substituto). A integração com runtime SLM local deve usar o cliente OpenAI-compatible oficial (`openai` — DEC-015 / BR-023 / BDD-024), com default Qwen Coder 3B (DEC-006). Falhas do modelo devem ser tipadas para alimentar restart total do repo em T14 (BR-005). A SLM **não** inventa chunks e **não** produz respostas MCP (BR-010).

## 3. Solução proposta

Módulo `github_rag.index.metadata` (stub T01 já reservado) com:

| Componente | Papel |
|---|---|
| `types` | `ChunkMetadata` — saída imutável serializável associada a um `chunk_id` |
| `errors` | `MetadataGenerationError` e subclasses tipadas |
| `ports` | Protocol `MetadataGenerator` |
| `openai_slm` | `OpenAICompatibleMetadataGenerator` — adaptador default via SDK `openai` |
| `config` (ou settings locais da task) | `SlmClientSettings` — `base_url`, `api_key`, `model` (default Qwen Coder 3B) |

Fluxo feliz (uma chamada = um chunk):

```text
SemanticChunk (T11)
  → MetadataGenerator.generate(chunk)
  → prompt com path/language/kind/text (+ ranges)
  → OpenAI-compatible chat.completions (SDK openai → runtime local)
  → parse JSON estruturado → ChunkMetadata
  → retorno serializável (para T13 payload / T14)
```

Fluxo N chunks (orquestrador T14 — fora desta task, contrato da porta):

```text
for chunk in SemanticChunk[]:   # N invocações
    metadata_n = generator.generate(chunk)
# falha em qualquer generate → MetadataGenerationError → T14 falha etapa / restart repo
```

### 3.1 Escopo BDD nesta task

| Cenário | Cobertura T12 | Fora de T12 |
|---|---|---|
| BDD-007 | Etapa de metadados alimentável (N chunks → N metadados); falha tipada | UI/progresso/percentual; Zoekt; `metadata_persisted` (T14/T03) |
| BDD-010 | Metadados serializáveis prontos para payload semântico | Upsert/search Qdrant (T13) |
| BDD-024 | Integração SLM via SDK `openai` (DEC-015) | Outros SDKs |
| BR-010 | Geração só de metadados de indexação; sem prosa MCP | Tools MCP (T17) |

## 4. Componentes

### 4.1 Entrada: `SemanticChunk` (contrato T11 — não redefinir)

Consumir **um** `SemanticChunk` por chamada. Campos usados no prompt / associação:

| Campo | Uso em T12 |
|---|---|
| `chunk_id` | Copiado para `ChunkMetadata.chunk_id` (associação estável) |
| `path`, `language`, `kind` | Contexto do prompt |
| `text` | Conteúdo principal enviado à SLM |
| ranges / points | Contexto opcional no prompt; não alteram a unidade |

**Proibido:** inventar, fundir, dividir ou substituir chunks; chamar Tree-sitter; aceitar “arquivo inteiro” como substituto do per-chunk na porta.

### 4.2 Saída: `ChunkMetadata`

Dataclass frozen, serializável para JSON/dict (payload Qdrant em T13):

| Campo | Tipo | Descrição |
|---|---|---|
| `chunk_id` | `str` | Igual ao `SemanticChunk.chunk_id` de entrada |
| `summary` | `str` | Resumo contextual curto do chunk (não vazio em sucesso) |
| `symbols` | `tuple[str, ...]` | Identificadores/símbolos relevantes (pode ser vazio) |
| `keywords` | `tuple[str, ...]` | Palavras-chave para busca/contexto (pode ser vazio) |
| `intent` | `str` | Intenção/papel do trecho (string; pode ser `""` se modelo omitir) |
| `extra` | `tuple[tuple[str, str \| int \| float \| bool \| None], ...]` | Pares chave/valor JSON-escalares extras do modelo (imutável; sem nested objects/lists no MVP) |

Método / helper: `to_payload() -> dict[str, object]` com tipos JSON-safe (`list` no lugar de `tuple` para `symbols`/`keywords`; `extra` → objeto plano; sem tipos não serializáveis).

Invariantes de sucesso: `chunk_id` == entrada; `summary` strip não vazio; `symbols`/`keywords` sem strings vazias; dataclass frozen sem containers mutáveis; sem mutação do `SemanticChunk`.

### 4.3 `MetadataGenerator` (Protocol)

Responsabilidade: única porta de geração de metadados contextuais SLM a partir de um chunk Tree-sitter. Separação: isola provedor/modelo (BR-009) do orquestrador (T14) e do VectorStore (T13); impede uso da SLM para inventar chunks ou prosa MCP.

```python
class MetadataGenerator(Protocol):
    def generate(self, chunk: SemanticChunk) -> ChunkMetadata: ...
```

- Sucesso: um `ChunkMetadata` para aquele chunk.
- Falha: `MetadataGenerationError` (subclasse); nunca retorna metadados parciais silenciosos nem cria chunks.
- Assinatura **não** aceita lista de chunks nem arquivo-fonte — o loop N× é do caller (T14).

### 4.4 Adaptador default: `OpenAICompatibleMetadataGenerator`

| Aspecto | Decisão |
|---|---|
| SDK | Pacote oficial **`openai`** (`OpenAI` client) — DEC-015 / BR-023 / BDD-024 |
| Transporte | `base_url` apontando a runtime local OpenAI-compatible (Ollama, vLLM, etc. — escolha de runtime fora do contrato da porta) |
| API | `chat.completions.create` (mensagens system+user; `response_format` JSON quando suportado, senão parse estrito do content) |
| Modelo default | **Qwen Coder 3B** — id configurável; default documentado `qwen2.5-coder:3b` (DEC-006 / BR-009); override por settings/env sem mudar a porta |
| Auth | `api_key` configurável (runtimes locais frequentemente aceitam placeholder); nunca hardcodar secret no código |
| Proibido | `httpx`/`requests`/urllib ad-hoc como cliente da SLM; reinventar wire protocol OpenAI |

Construtor injetável: `(client: OpenAI | None, *, model: str, ...)` — testes usam fake client **ou** `FakeMetadataGenerator` implementando a porta sem rede.

### 4.5 Prompt e parse

- System: instruir JSON estrito com chaves `summary`, `symbols`, `keywords`, `intent` (+ extras opcionais); proibir markdown/prosa fora do JSON; idioma do summary alinhado ao código/comentários quando possível.
- User: incluir `path`, `language`, `kind`, ranges, e o `text` do chunk.
- Parse: JSON object; validar `summary` não vazio; normalizar listas → tuples; rejeitar não-objeto / JSON inválido → `MetadataResponseParseError`.
- Truncamento: se runtime/SDK limitar contexto, erro tipado (`MetadataModelError`) — **não** fragmentar o chunk em pedaços menores.

### 4.6 Configuração (`SlmClientSettings`)

| Campo | Default | Notas |
|---|---|---|
| `base_url` | obrigatório em runtime real (ex. `http://127.0.0.1:11434/v1`) | Injetável; testes com fake não precisam |
| `api_key` | `"local"` ou env | Sem secret no repo |
| `model` | `qwen2.5-coder:3b` | Documentado como **Qwen Coder 3B** (DEC-006) |
| `timeout_seconds` | valor positivo documentado no design/impl | Falha → `MetadataModelError` |

Leitura de env/settings concretos pode reutilizar T01/T02 se já houver chaves; caso contrário, defaults locais da factory T12 sem expandir escopo de T02.

## 5. Fluxo de dados

```text
T11 ContextualChunker.chunk → SemanticChunk[]
T14 (por chunk):
  MetadataGenerator.generate(SemanticChunk)
    → ChunkMetadata
T13 VectorStore.upsert(..., chunk + metadata.to_payload() + embedding)
T17 MCP: NÃO chama MetadataGenerator / SLM
```

## 6. Erros tipados

Hierarquia sob `MetadataGenerationError`:

| Tipo | Quando | Fallback? |
|---|---|---|
| `MetadataConfigError` | `base_url`/model/timeout inválidos na construção | Não |
| `MetadataModelError` | falha de rede/SDK/runtime, timeout, HTTP/API error, resposta vazia do modelo | Não |
| `MetadataResponseParseError` | content não-JSON, schema inválido, `summary` vazio | Não |

Base carrega `chunk_id: str | None` e `path: str | None` quando souber. Mensagens sem secrets (`api_key`). Qualquer `MetadataGenerationError` é falha da etapa de metadados para T14 (alimenta BR-005 / restart do repo).

**Proibido:** engolir erro e retornar metadados “vazios” genéricos; inventar chunk alternativo; retry infinito sem política explícita (MVP: sem retry na porta; caller decide).

## 7. Segurança

- Tráfego apenas para `base_url` configurado (runtime local esperado); sem telemetria de terceiros.
- Não logar `api_key` nem prompt completo com secrets de código além do necessário a debug opt-in.
- Conteúdo do chunk pode ser grande (REQ-019) — risco de contexto/memória; sem split do chunk.
- Esta porta **não** é caminho MCP (BR-010).

## 8. Compatibilidade

- Dep nova: `openai` (pin no `pyproject`).
- Python 3.12+.
- Depende do contrato T11 `SemanticChunk` (import de `github_rag.index.chunk.types`); **não** altera T11.
- Não redefine unidade de chunk; T13 consome `ChunkMetadata` serializado.

## 9. Observabilidade

- Sem logger obrigatório; erros tipados bastam para T14 marcar falha da etapa de metadados.
- Fake generator nos testes: sucesso per-chunk e falha no meio da lista (critério de aceite da task).

## 10. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Modelo retorna prosa/markdown | Parse estrito + `MetadataResponseParseError` |
| Id do modelo Qwen varia por runtime | Default documentado + override por config; porta indiferente ao id |
| Chunk enorme estoura contexto | Erro tipado; sem fragmentar chunk |
| Tentação de batch “por arquivo” | Assinatura só aceita um `SemanticChunk` (D-T12-003) |
| Uso acidental em MCP | Proibição BR-010 no design/interfaces; T17 não injeta esta porta |
| Cliente HTTP caseiro | Proibido; só SDK `openai` (D-T12-002) |

## 11. Rollback

Remover implementação em `index/metadata/` (manter stub T01 se necessário), dep `openai` do pyproject e testes T12. Sem migration de dados. T13/T14 passam a não ter gerador real até reintrodução.

## 12. Decisões de design

| ID | Decisão | Motivo |
|---|---|---|
| D-T12-001 | Porta `MetadataGenerator.generate(chunk) -> ChunkMetadata` | BR-009; orquestrador injeta fake/real sem conhecer provedor |
| D-T12-002 | Adaptador default via SDK oficial `openai` (OpenAI-compatible) | DEC-015, BR-023, BDD-024; proibido client HTTP inventado |
| D-T12-003 | Entrada = **um** `SemanticChunk` por chamada; loop N× no caller | BR-010/DEC-006 per-chunk; impede substituto “por arquivo” |
| D-T12-004 | Default de modelo = Qwen Coder 3B (`qwen2.5-coder:3b`) | DEC-006, BR-009 |
| D-T12-005 | Saída `ChunkMetadata` frozen + `to_payload()` JSON-safe | Contrato estável para T13 payload / BDD-010 |
| D-T12-006 | Erros tipados sob `MetadataGenerationError` sem fallback silencioso | Aceite T12; T14 / BR-005 |
| D-T12-007 | Proibido inventar/alterar chunks e produzir prosa MCP | BR-010; DEC-003 (unidade = T11) |
| D-T12-008 | `FakeMetadataGenerator` / client injetável para testes | Aceite: per-chunk + falha no meio da lista sem runtime SLM |
| D-T12-009 | Runtime local concreto (Ollama/vLLM/…) fora do contrato da porta | requirements: escolha de runtime não altera abstração BR-009 |
| D-T12-010 | Embeddings **fora** de T12 (porta distinta em T13) | Separação metadados SLM × vetores; mesmo SDK `openai` pode ser reutilizado depois |

## 13. Proibições (checklist)

- [ ] Não inventar chunks nem substituir Tree-sitter.
- [ ] Não aceitar agregação por arquivo como API da porta.
- [ ] Não usar SLM para respostas/tools MCP.
- [ ] Não implementar cliente HTTP/CLI OpenAI caseiro.
- [ ] Não retornar sucesso com `summary` vazio ou engolir falha do modelo.

## 14. Arquivos previstos

```text
src/github_rag/index/metadata/
  __init__.py
  types.py
  errors.py
  ports.py
  openai_slm.py
  config.py          # opcional se settings caberem na factory
tests/unit/index/metadata/
tests/bdd/test_slm_metadata.py
spec/.../tasks/T12-slm-metadata/*
```

## 15. Handoff

| Consumidor | Usa |
|---|---|
| T13 `VectorStore` | `ChunkMetadata.to_payload()` + campos do `SemanticChunk` |
| T14 orquestrador | `MetadataGenerator.generate` N vezes; captura `MetadataGenerationError` |
| T16/T18 (opcional) | Mesma porta para apoio a busca/UI — **não** MCP |
| T17 MCP | **Não** consome esta porta |
