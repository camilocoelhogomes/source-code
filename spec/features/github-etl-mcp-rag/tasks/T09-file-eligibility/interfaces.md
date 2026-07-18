# Interfaces — T09-file-eligibility

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T09-file-eligibility` |
| Autor | Tech Lead Architect |
| Data | 2026-07-18 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T09-file-eligibility` |
| Escopo desta etapa | Contratos de comunicação T09 **somente** (stubs sem comportamento completo) |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-18 |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão |
|---|---|---|---|
| 2026-07-18 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` |

## 1. Escopo e exclusões

### Em escopo

| Contrato | Módulo | Papel |
|---|---|---|
| `FileEligibilityFilter` | `eligibility/filter.py` | Porta pura de filtragem |
| `PathspecFileEligibilityFilter` | `eligibility/filter.py` | Implementação pathspec + rules (stub) |
| `EligibilityError` | `eligibility/filter.py` | Erros tipados de entrada/loader |
| `GitignoreSource` | `eligibility/gitignore.py` | DTO: dir relativo + linhas |
| `load_gitignore_sources` | `eligibility/gitignore.py` | Walk local de `.gitignore` aninhados |
| `EligibilityRules` / denylists | `eligibility/rules.py` | Denylist CSV/imagens; política sem extensão |
| Re-exports | `eligibility/__init__.py` | Superfície pública |

### Fora de escopo

| Item | Dono |
|---|---|
| Snapshot remoto / GitPython tree | T08 |
| Orquestração de indexação | T14 |
| Caps de tamanho / sniffing binário | fora (D-T09-006 / REQ-019) |
| `.git/info/exclude` / excludes globais | fora MVP |
| Allowlist de linguagens | proibida (D-T09-004) |
| Implementação completa do filter | etapa pós unit-test-plan |

## 2. Decisões de contrato

| ID | Decisão | Motivo |
|---|---|---|
| I-T09-001 | Porta `FileEligibilityFilter.filter(paths, gitignore_sources) -> list[str]` pura (sem I/O, sem `repo_root`) | D-T09-001; T14 injeta paths/sources; testes unitários em memória |
| I-T09-002 | Matching GitWildMatch exclusivamente via `pathspec` (`PathSpec.from_lines("gitwildmatch", …)` / `GitWildMatchPattern`); dep `pathspec>=0.12` | D-T09-002; DEC-015; BDD-024 / ELIG-06 |
| I-T09-003 | `GitignoreSource(relative_dir, lines)` + `load_gitignore_sources(repo_root)` separados da porta | D-T09-001/003; loader com I/O; porta testável sem disco |
| I-T09-004 | Ordem: gitignore → denylist CSV → denylist imagens → include; denylist-only (sem allowlist) | D-T09-004; REQ-014/015 |
| I-T09-005 | Sem extensão: include-by-default se não gitignored (`EligibilityRules.include_extensionless=True`) | D-T09-005 |
| I-T09-006 | Assinatura de `filter` sem parâmetros de tamanho; filtro não consulta volume | D-T09-006; REQ-019; ELIG-07 |
| I-T09-007 | Paths relativos com `/`; normalizar `\`; rejeitar absoluto/`..`/vazio com `EligibilityError`; duplicatas: ordem de entrada, colapsar mantendo a primeira | D-T09-001 §2.2/§2.5 |
| I-T09-008 | Ignored matching: fontes cujo `relative_dir` é prefixo; last-match wins; `sources=[]` = só regras de tipo | D-T09-003 |

## 3. Contratos detalhados

### 3.1 `EligibilityError`

```python
class EligibilityError(Exception):
    """Entrada inválida na porta ou falha no loader de .gitignore."""
```

- **Responsabilidade:** sinalizar fail-fast de path absoluto/escape/`..`/vazio, `repo_root` inexistente, ou `.gitignore` ilegível/não-UTF-8.
- **Motivo da separação:** distinguir erros de elegibilidade de erros de settings (T01), discovery (T05/T06) ou catalog (T03); T14 pode mapear para falha de repo (BR-005).
- **Invariantes:** mensagem cita o path/root ofensivo; sem conteúdo de arquivo nem segredos.
- **Erros:** esta classe **é** o tipo.

### 3.2 `GitignoreSource`

```python
@dataclass(frozen=True)
class GitignoreSource:
    relative_dir: str  # "" = raiz; "docs" / "a/b" = aninhado
    lines: tuple[str, ...]  # linhas do .gitignore (UTF-8)
```

- **Responsabilidade:** materializar um `.gitignore` já lido (dir relativo ao root + linhas) para a porta pura.
- **Motivo da separação:** desacopla I/O de disco do matching; fixtures BDD/unit injetam fontes sem filesystem.
- **Invariantes:** `relative_dir` usa `/` (sem leading/trailing `/` exceto `""`); `lines` imutável após construção.
- **Erros:** construção inválida pode ser rejeitada pelo filter/loader com `EligibilityError` (não nesta dataclass por si só nesta etapa).

### 3.3 `load_gitignore_sources`

```python
def load_gitignore_sources(repo_root: Path) -> list[GitignoreSource]: ...
```

- **Responsabilidade:** percorrer `repo_root` (sem seguir symlinks para fora; sem descer em `.git/`), coletar arquivos nomeados exatamente `.gitignore`, devolver fontes `(relative_dir, lines)`.
- **Motivo da separação:** I/O local permitido (BR-023) fica fora da porta; T14 pode preferir materializar de snapshot sem este helper.
- **Invariantes:** raiz → `relative_dir=""`; decode UTF-8; ordem estável (walk determinístico).
- **Erros:** `EligibilityError` se root inexistente/ilegível ou `.gitignore` não-UTF-8.

### 3.4 `EligibilityRules` / denylists

```python
CSV_DENYLIST: frozenset[str]   # {".csv"}
IMAGE_DENYLIST: frozenset[str] # png/jpg/jpeg/gif/bmp/webp/ico/tif/tiff/heic/avif/svg

@dataclass(frozen=True)
class EligibilityRules:
    csv_extensions: frozenset[str]
    image_extensions: frozenset[str]
    include_extensionless: bool  # True = D-T09-005
```

- **Responsabilidade:** centralizar denylists case-insensitive e a política de arquivos sem extensão.
- **Motivo da separação:** regras de tipo evoluem sem alterar a porta nem o motor pathspec; evita allowlist acidental espalhada no filter.
- **Invariantes:** extensões com ponto leading (`.csv`); matching case-insensitive na implementação; `DEFAULT_ELIGIBILITY_RULES` = lista fechada D-T09-004 + `include_extensionless=True`.
- **Erros:** nenhum nas constantes; o filter aplica as regras.

### 3.5 `FileEligibilityFilter` (Protocol)

```python
@runtime_checkable
class FileEligibilityFilter(Protocol):
    def filter(
        self,
        paths: Sequence[str],
        gitignore_sources: Sequence[GitignoreSource],
    ) -> list[str]: ...
```

- **Responsabilidade:** devolver subset elegível de `paths` (ordem estável; duplicatas colapsadas na primeira ocorrência), aplicando ignore + denylist.
- **Motivo da separação:** contrato estável para T14 sem acoplar a pathspec, disco ou constantes de extensão.
- **Invariantes:** sem I/O; sem params de tamanho; `gitignore_sources=[]` válido.
- **Erros:** `EligibilityError` em path inválido (absoluto/`..`/vazio).

### 3.6 `PathspecFileEligibilityFilter`

```python
class PathspecFileEligibilityFilter:
    def __init__(self, rules: EligibilityRules | None = None) -> None: ...

    def filter(
        self,
        paths: Sequence[str],
        gitignore_sources: Sequence[GitignoreSource],
    ) -> list[str]: ...
```

- **Responsabilidade:** implementação concreta com `pathspec` GitWildMatch + `EligibilityRules` (defaults do módulo `rules`).
- **Motivo da separação:** isola SDK OSS e política de tipo da porta; permite mock da porta em T14 e inspeção ELIG-06 do uso de pathspec.
- **Invariantes:** importa/usa `pathspec`; last-match wins entre fontes aplicáveis (I-T09-008); denylist após ignore.
- **Erros:** `EligibilityError` conforme §2.5 do design; stub nesta etapa → `NotImplementedError` até implementação.

## 4. Fluxo de avaliação (contrato)

```text
path normalizado
  → ignorado por pathspec aninhado? → excluir
  → extensão ∈ CSV_DENYLIST? → excluir
  → extensão ∈ IMAGE_DENYLIST? → excluir
  → sem extensão e include_extensionless? → incluir
  → demais → incluir
```

## 5. Código nesta etapa

| Arquivo | Conteúdo |
|---|---|
| `src/github_rag/eligibility/__init__.py` | Reexports públicos |
| `src/github_rag/eligibility/filter.py` | Protocol + erro + stub pathspec |
| `src/github_rag/eligibility/rules.py` | Denylists + `EligibilityRules` |
| `src/github_rag/eligibility/gitignore.py` | `GitignoreSource` + stub loader |
| `pyproject.toml` | `pathspec>=0.12` em dependencies |

Gate interfaces: contratos e comentários de responsabilidade/separação presentes; comportamento completo fica para TDD após unit-test-plan aprovado. BDD de comportamento permanece red (`NotImplementedError`).

## 6. Compatibilidade

Python 3.12+; OS-agnostic (paths lógicos `/`; `\` normalizado na entrada); Windows/macOS/Linux first-class; dep pathspec no venv ENG-009 e imagem T19.
