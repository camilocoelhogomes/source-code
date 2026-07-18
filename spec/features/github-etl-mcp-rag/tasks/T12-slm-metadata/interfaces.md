# Interfaces — T12-slm-metadata

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T12-slm-metadata` |
| Autor | QA Engineer + Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.1` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.1` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T12-slm-metadata` |

## 0. Histórico

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-18 | QA Engineer | `READY_FOR_ARCHITECT_REVIEW` | `0.1.0` | Contratos alinhados ao design APPROVED; aguarda review Architect. |
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.1` | Correções MAJOR: validação construtor settings/client; `str(erro)` com chunk_id/path. |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Módulo | Papel |
|---|---|---|
| `ChunkMetadata` | `index/metadata/types.py` | Saída imutável serializável por chunk |
| `MetadataGenerationError` (+ subclasses) | `index/metadata/errors.py` | Falhas tipadas sem fallback |
| `MetadataGenerator` | `index/metadata/ports.py` | Porta de domínio (BR-009) |
| `SlmClientSettings` | `index/metadata/config.py` | Config do adaptador OpenAI-compatible |
| `OpenAICompatibleMetadataGenerator` | `index/metadata/openai_slm.py` | Adaptador default via SDK `openai` |
| `FakeMetadataGenerator` | `index/metadata/fakes.py` | Fake determinístico para testes / aceite |

### Fora de escopo

| Item | Dono |
|---|---|
| Produção de `SemanticChunk` | T11 (contrato consumido, não redefinido) |
| Upsert Qdrant / embeddings | T13 |
| Loop orquestrador / BR-005 restart | T14 |
| Tools MCP / prosa Discovery | T17 — **não** injeta esta porta |

## 2. Decisões de contrato

| ID | Decisão | Motivo |
|---|---|---|
| I-T12-001 | Porta `MetadataGenerator.generate(chunk) -> ChunkMetadata` | Isola provedor (BR-009); loop N× no caller (D-T12-003) |
| I-T12-002 | Entrada = um `SemanticChunk` (T11); sem lista/arquivo | Impede agregação por arquivo; BR-010 / DEC-003 |
| I-T12-003 | `ChunkMetadata` frozen + `extra` imutável + `to_payload()` | Contrato estável T13 / BDD-010; sem `dict` mutável em frozen |
| I-T12-004 | Hierarquia sob `MetadataGenerationError` | Aceite T12; T14 mapeia falha da etapa (BR-005) |
| I-T12-005 | Adaptador default via SDK oficial `openai` | DEC-015 / BR-023 / BDD-024; proibido HTTP caseiro |
| I-T12-006 | Default model `qwen2.5-coder:3b` | DEC-006 / BR-009 (Qwen Coder 3B) |
| I-T12-007 | `FakeMetadataGenerator` no pacote | Aceite per-chunk + falha no meio da lista sem runtime SLM |
| I-T12-008 | Proibido inventar chunks / prosa MCP | BR-010; handoff T17 não consome a porta |

## 3. Contratos detalhados

### 3.1 Entrada: `SemanticChunk` (T11 — não redefinir)

Importar de `github_rag.index.chunk.types.SemanticChunk`.

- **Responsabilidade (T12):** única unidade de entrada da porta; campos usados: `chunk_id`, `path`, `language`, `kind`, `text`, ranges/points opcionais no prompt.
- **Motivo da separação:** T11 já estabilizou a unidade RAG; T12 só enriquece, não redefine chunking.
- **Proibido:** inventar/fundir/dividir chunks; aceitar arquivo inteiro como substituto do per-chunk.

### 3.2 `ChunkMetadata`

```python
@dataclass(frozen=True)
class ChunkMetadata:
    chunk_id: str
    summary: str
    symbols: tuple[str, ...]
    keywords: tuple[str, ...]
    intent: str
    extra: tuple[tuple[str, str | int | float | bool | None], ...]

    def to_payload(self) -> dict[str, object]: ...
```

- **Responsabilidade:** transportar metadados contextuais imutáveis associados a um `chunk_id` e serializá-los para payload Qdrant (T13).
- **Motivo da separação:** desacopla o formato de saída SLM do adaptador OpenAI e do VectorStore; evita mutação pós-geração.
- **Invariantes de sucesso:** `chunk_id` == entrada; `summary.strip()` não vazio; `symbols`/`keywords` sem strings vazias; containers imutáveis; sem nested objects/lists em `extra` (MVP).
- **`to_payload()`:** `symbols`/`keywords` → `list`; `extra` → `dict` plano de escalares JSON-safe; demais campos escalares/`str`.

### 3.3 Erros (`MetadataGenerationError`)

```python
class MetadataGenerationError(Exception):
    def __init__(
        self,
        message: str = "",
        *,
        chunk_id: str | None = None,
        path: str | None = None,
    ) -> None: ...

    chunk_id: str | None
    path: str | None

class MetadataConfigError(MetadataGenerationError): ...
class MetadataModelError(MetadataGenerationError): ...
class MetadataResponseParseError(MetadataGenerationError): ...
```

- **Responsabilidade:** sinalizar falhas de geração sem engolir erro nem retornar metadados “vazios” genéricos.
- **Motivo da separação:** distinto de `ChunkingError` (T11) e de erros de VectorStore (T13); T14 trata qualquer `MetadataGenerationError` como falha da etapa de metadados.
- **Quando (design §6):**
  - `MetadataConfigError` — `base_url`/model/timeout inválidos na construção
  - `MetadataModelError` — rede/SDK/runtime/timeout/HTTP/API/resposta vazia/contexto estourado
  - `MetadataResponseParseError` — content não-JSON, schema inválido, `summary` vazio
- **Invariantes:** mensagens sem valor de `api_key`/secrets; MVP sem retry na porta; classe **não** armazena atributo `api_key`.
- **Representação (`str`/`repr`):** quando `chunk_id` e/ou `path` forem não-`None`, devem aparecer na representação textual do erro (observabilidade para T14 / UT-E02).

### 3.4 `MetadataGenerator` (Protocol)

```python
@runtime_checkable
class MetadataGenerator(Protocol):
    def generate(self, chunk: SemanticChunk) -> ChunkMetadata:
        """Gera metadados contextuais SLM para um chunk Tree-sitter.

        Responsabilidade
            Única porta de geração de metadados de indexação a partir de
            um SemanticChunk.

        Motivo da separação
            Isola provedor/modelo (BR-009) do orquestrador (T14) e do
            VectorStore (T13); impede uso da SLM para inventar chunks
            ou prosa/tools MCP (BR-010).
        """
        ...
```

- **Sucesso:** um `ChunkMetadata` para aquele chunk.
- **Falha:** `MetadataGenerationError` (subclasse); nunca metadados parciais silenciosos.
- **Proibido na assinatura:** lista de chunks, `bytes` de arquivo, parâmetros MCP.

### 3.5 `SlmClientSettings`

```python
@dataclass(frozen=True)
class SlmClientSettings:
    base_url: str
    api_key: str = "local"
    model: str = "qwen2.5-coder:3b"  # Qwen Coder 3B (DEC-006)
    timeout_seconds: float = 60.0
```

- **Responsabilidade:** carregar parâmetros do runtime OpenAI-compatible local (URL, auth placeholder, modelo, timeout).
- **Motivo da separação:** permite BR-009 (troca de modelo/provedor via settings) sem alterar a porta nem o orquestrador.
- **Defaults:** `model=qwen2.5-coder:3b`; `api_key="local"`; `timeout_seconds=60.0` (positivo).
- **Validação:** valores inválidos → `MetadataConfigError` na construção do adaptador (ou helper de validação chamado por ele).

### 3.6 `OpenAICompatibleMetadataGenerator`

```python
class OpenAICompatibleMetadataGenerator:
    def __init__(
        self,
        client: Any | None = None,  # openai.OpenAI | None
        *,
        settings: SlmClientSettings | None = None,
        model: str | None = None,
    ) -> None: ...

    def generate(self, chunk: SemanticChunk) -> ChunkMetadata: ...
```

- **Responsabilidade:** implementar `MetadataGenerator` via SDK oficial `openai` (`chat.completions.create`) apontando a runtime local OpenAI-compatible.
- **Motivo da separação:** concentra DEC-015/BDD-024 atrás da porta; testes injetam client fake sem rede.
- **Default model:** `settings.model` ou `qwen2.5-coder:3b` quando settings omitido; override explícito por `model=` (ganha de `settings.model`) ou settings.
- **Construção / validação (obrigatório):**
  1. Se `settings is not None`: validar `base_url.strip()` não vazio, `model.strip()` não vazio (após aplicar override `model=` se houver), `timeout_seconds > 0` → senão `MetadataConfigError` **antes** de qualquer chamada.
  2. Se `settings is None` e `client` injetado: **não** exige `base_url`; model efetivo = `model` kwarg ou `"qwen2.5-coder:3b"` (permite UT-P01 / testes sem settings).
  3. Se `settings is None` e `client is None`: `MetadataConfigError` (impossível criar `OpenAI` real sem `base_url`).
  4. Se `client is None` e settings válidos: criar `openai.OpenAI(base_url=..., api_key=..., timeout=...)`.
- **Fluxo `generate`:** montar prompt (path/language/kind/ranges/text) → `chat.completions.create` → parse JSON estrito → `ChunkMetadata` com `chunk_id` da entrada; falhas SDK → `MetadataModelError`; parse/schema/`summary` vazio → `MetadataResponseParseError`; nunca incluir valor de `api_key` em mensagens.
- **Proibido:** `httpx`/`requests`/urllib ad-hoc como cliente SLM; fragmentar chunk em pedaços; inventar chunk_id.

### 3.7 `FakeMetadataGenerator`

```python
class FakeMetadataGenerator:
    def __init__(
        self,
        *,
        by_chunk_id: Mapping[str, ChunkMetadata] | None = None,
        fail_chunk_ids: AbstractSet[str] | None = None,
        fail_error: type[MetadataGenerationError] = MetadataModelError,
        default_summary_prefix: str = "summary:",
    ) -> None: ...

    def generate(self, chunk: SemanticChunk) -> ChunkMetadata: ...
```

- **Responsabilidade:** implementação determinística da porta para testes (sucesso per-chunk e falha tipada no meio da lista) sem runtime SLM.
- **Motivo da separação:** satisfaz aceite da task e permite T14 testar o loop N× independentemente do adaptador OpenAI.
- **Comportamento:**
  - se `chunk.chunk_id` ∈ `fail_chunk_ids` → levanta `fail_error` com `chunk_id`/`path`
  - senão se há entrada em `by_chunk_id` → retorna essa metadata (deve preservar `chunk_id`)
  - senão → retorna `ChunkMetadata` sintético com `chunk_id=chunk.chunk_id`, `summary=f"{default_summary_prefix}{chunk.chunk_id}"`, tuples vazias, `intent=""`

## 4. Reexports (`index/metadata/__init__.py`)

```python
from github_rag.index.metadata.config import SlmClientSettings
from github_rag.index.metadata.errors import (
    MetadataConfigError,
    MetadataGenerationError,
    MetadataModelError,
    MetadataResponseParseError,
)
from github_rag.index.metadata.fakes import FakeMetadataGenerator
from github_rag.index.metadata.openai_slm import OpenAICompatibleMetadataGenerator
from github_rag.index.metadata.ports import MetadataGenerator
from github_rag.index.metadata.types import ChunkMetadata
```

## 5. Handoff

| Consumidor | Usa |
|---|---|
| T13 `VectorStore` | `ChunkMetadata.to_payload()` + campos do `SemanticChunk` |
| T14 orquestrador | `MetadataGenerator.generate` N vezes; captura `MetadataGenerationError` |
| T16/T18 (opcional) | Mesma porta — **não** MCP |
| T17 MCP | **Não** consome esta porta |
