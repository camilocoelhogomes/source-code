# Interfaces — T22-fix-tooling-e2e-compose-zoekt

| Campo | Valor |
|---|---|
| Feature | `github-etl-mcp-rag` |
| Task | `T22-fix-tooling-e2e-compose-zoekt` |
| Autor | Tech Lead Architect |
| Data | 2026-07-19 |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |
| Design base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| BDD base | `0.1.0` (`APPROVED_BY_ARCHITECT`) |
| Branch | `feature/github-etl-mcp-rag-T22-fix-tooling-e2e-compose-zoekt` |
| Escopo desta etapa | Contratos de **manifesto** (serviço `zoekt` nos 3 composes) + contratos de **documentação** (pré-req compose provider) + reuso explícito de T21 — **sem** Protocols Python novos em `src/` |
| Aprovação Architect | `APPROVED_BY_ARCHITECT` em 2026-07-19 (modo autônomo) |

## 0. Histórico Architect

| Data | Autor | Decisão | Versão | Observações |
|---|---|---|---|---|
| 2026-07-19 | Tech Lead Architect | `APPROVED_BY_ARCHITECT` | `0.1.0` | Gate D-T22-006: interfaces = M-T22-* + docs; sem Protocols novos; T21 reusado sem mudança; helpers de parse só em testes (opcional compartilhado documentado). |

## 1. Escopo e exclusões

### Em escopo

| Superfície | Artefato | Papel |
|---|---|---|
| Manifesto compose | `docker-compose.yml`, `docker-compose.e2e.yml`, `docker-compose.dev.yml` | Shape do serviço `zoekt` (F-T04-002 / D-T22-001/002) |
| Documentação | `e2e/README.md`, `docs/runbook-local.md` | Pré-req provider Compose no PATH (F-T04-001 / D-T22-004) |
| Reuso runtime | `github_rag.e2e` (T21) | Consome compose corrigido; prova F-T04-003 pós-fix |
| Gate CI | `tests/bdd/test_e2e_compose_zoekt_fix.py` + unitários manifesto (padrão T19) | Asserts de arquivo; sem `compose up` |

### Fora de escopo

| Item | Motivo |
|---|---|
| Novos `Protocol` / classes em `src/github_rag/**` | D-T22-006 / D-T22-007 — fix é YAML + docs |
| Alterar assinaturas `E2eStackLauncher` / `RobotMvpSuite` | T21 estável; T22 só corrige input (compose) |
| Expandir `e2e/robot/**` / browser | T23+; D-T22-007/008 |
| Domínio ETL/RAG/MCP | Fora de tooling-e2e |
| Pin obrigatório de digest da imagem Zoekt | SUGGESTION residual (R-T22-01) |

## 2. Decisões de contrato

| ID | Decisão | Motivo | Design / BDD |
|---|---|---|---|
| I-T22-001 | **Não** introduzir Protocols Python nem módulos novos em `src/github_rag/` nesta task | Gate = manifesto/docs (D-T22-006); bug é ENTRYPOINT/`tini` sem filho no YAML | design §3.4; §17.2 |
| I-T22-002 | Reusar **sem mudança de Protocol** `E2eStackLauncher` (`up` / `wait_healthy` / `down`) e `RobotMvpSuite` (`run() -> int`) de T21 | F-T04-003 fecha quando o compose deixa de derrubar zoekt; launcher/suite já orquestram o fluxo | D-T22-007; EZ-04; T21 I-T21-002/009 |
| I-T22-003 | Defaults concretos T21 permanecem canônicos: `PodmanE2eStackLauncher` + `DefaultRobotMvpSuite` + `python -m github_rag.e2e` | Prova operacional pós-fix; T22 não redefine entry | T21 I-T21-003/018; design §5 |
| I-T22-004 | Falha de provider Compose ausente continua `E2eStackError` / exit tooling (`3`); mitigação T22 = **docs**, não novo tipo de erro | F-T04-001 é pré-req de host; T21 já tipa falha de stack | design §3.2; §7; T21 I-T21-008 |
| I-T22-005 | Contratos declarativos `M-T22-*` (YAML/docs) são a interface desta task; materializados pelo Developer nos arquivos de compose/docs | Mesmo padrão I-T19-017 / M-T19-* | D-T22-006; EZ-01..05 |
| I-T22-006 | Preferir `command:` argv JSON **sem** sobrescrever `entrypoint` da imagem | Preserva `tini` como init (reaping/sinais); processo efetivo `tini -- zoekt-webserver …` | D-T22-001; design §3.1 |
| I-T22-007 | Helpers de parsing de compose: **não** são API de produção. Permanecem no módulo de teste (BDD) ou, se compartilhados com unitários, em helper de teste sob `tests/` | Evita inventar parser YAML em `src/`; asserts de manifesto ≠ domínio | SUGGESTION BDD; §6 abaixo |
| I-T22-008 | Healthcheck do serviço `zoekt` é **recomendado**, não contrato bloqueante desta etapa; readiness canônica da prova permanece wait T21 + `/healthz` do `app` | R-T22-02 (probe pode falhar se imagem sem `wget`/`curl`); `command` é o fix obrigatório | design §3.1; R-T22-02 |
| I-T22-009 | Indexação continua no `app` via `zoekt-index`; serviço compose `zoekt` = **só** webserver HTTP `-rpc` | Contrato T10; volume compartilhado `/data/index` | D-T22-003 |

## 3. Reuso T21 — Protocols existentes (sem alteração)

Pacote: `github_rag.e2e` (já implementado em T21).

```python
# src/github_rag/e2e/ports.py — CONTRATOS CONGELADOS (não alterar em T22)

@runtime_checkable
class E2eStackLauncher(Protocol):
    """Lifecycle da stack e2e (compose up / wait healthy / down).

    Responsabilidade
        Subir e derrubar ``docker-compose.e2e.yml`` via Podman e aguardar
        readiness do app (``GET :8080/healthz``). Não conhece argv do
        serviço ``zoekt`` — apenas consome o manifesto na raiz do repo.

    Motivo da separação (T21; reafirmado em T22)
        Isola I/O de infraestrutura das asserções Robot e da política de
        credencial. T22 corrige o YAML consumido; não muda esta porta.
    """

    def up(self, env: dict[str, str]) -> None: ...
    def wait_healthy(self) -> None: ...
    def down(self) -> None: ...


@runtime_checkable
class RobotMvpSuite(Protocol):
    """Orquestra a prova canônica MVP (credencial → stack → robot → cleanup).

    Responsabilidade
        Executar o green path com exclusão ``bdd015`` e retornar exit code
        estável (``0`` = green; ``≠0`` = não entregue / falha tooling).

    Motivo da separação (T21; reafirmado em T22)
        Suite ≠ launcher: permite doubles sem Podman. T22 não altera
        ``run()``; o aceite F-T04-003 é consequência do compose saudável
        + pré-reqs documentados (EZ-04).
    """

    def run(self) -> int: ...
```

| Consumo T22 | Contrato T21 | Mudança? |
|---|---|---|
| `PodmanE2eStackLauncher.up` lê `COMPOSE_E2E` | I-T21-004/005 | Não — path fixo `docker-compose.e2e.yml` |
| Ordem `resolve → up → wait_healthy → robot → down` | I-T21-009 | Não |
| `E2eStackError` em falha compose/health | I-T21-008 | Não (docs mitigam F-T04-001) |
| Robot `--exclude bdd015` | I-T21-010 | Não |

**Responsabilidade desta seção:** congelar o boundary Python que a prova operacional usa.  
**Motivo da separação vs M-T22-*:** runtime e2e (T21) ≠ shape YAML do serviço `zoekt` (T22); ownership do fix de tooling é manifesto, não reabertura de Protocols.

## 4. Contratos de manifesto — serviço `zoekt` (M-T22-*)

### 4.1 Shape canônico (alvo pós-implementação)

Aplicar nos **três** composes (papéis REQ-043 inalterados: user / e2e / dev).

```yaml
# Bloco mínimo do serviço zoekt — contrato M-T22-001..004
zoekt:
  image: sourcegraph/zoekt:latest   # pin digest = SUGGESTION futura; não bloqueia
  # NÃO declarar entrypoint: — preserva ENTRYPOINT da imagem ["/sbin/tini","--"]
  command: ["zoekt-webserver", "-index", "/data/index", "-rpc"]
  volumes:
    - <volume_zoekt>:/data/index    # e2e_zoekt_index | zoekt_index | dev_zoekt_index
  environment:
    ZOEKT_INDEX_DIR: /data/index
  ports:
    - "6070:6070"
  # healthcheck: recomendado (I-T22-008), não bloqueante se probe indisponível
```

**Processo efetivo esperado:** `tini -- zoekt-webserver -index /data/index -rpc`  
**Prova runtime (fora do pytest manifesto):** `GET http://127.0.0.1:6070/healthz` → HTTP 200.

### 4.2 Tabela M-T22-*

| ID | Requisito | Arquivos | BDD |
|---|---|---|---|
| M-T22-001 | Serviço `zoekt` declara `command` cujo argv efetivo contém, nesta ordem lógica: `zoekt-webserver`, `-index`, `/data/index`, `-rpc` | 3 composes | EZ-02 |
| M-T22-002 | Serviço `zoekt` **não** sobrescreve `entrypoint` (ou, se o fizer, deve preservar `tini` como PID 1 e o mesmo filho webserver — forma preferida = só `command`) | 3 composes | EZ-02; D-T22-001 |
| M-T22-003 | Volume/mount do índice em `/data/index` permanece no bloco `zoekt` (e compartilhamento app↔zoekt herdado de T19/T10) | 3 composes | EZ-02 |
| M-T22-004 | Paridade: os três composes declaram o **mesmo argv efetivo** do webserver (tokens de M-T22-001) — nenhum compose “esquecido” | 3 composes | EZ-03; D-T22-002 |
| M-T22-005 | Porta host/container `6070` e env `ZOEKT_INDEX_DIR=/data/index` no serviço `zoekt` permanecem (compat T10/T19); T22 não remove | 3 composes | EZ-02 (indireto); T19 M-T19-002 |
| M-T22-006 | Nenhum segredo (PAT / `ghp_`) embutido nos blocos alterados dos composes | 3 composes | EZ-05 |
| M-T22-007 | Forma preferida do `command`: lista JSON inline `command: ["zoekt-webserver", "-index", "/data/index", "-rpc"]` (facilita asserts e evita ambiguidade multilinha) | 3 composes | design §3.1; SUGGESTION BDD |

**Responsabilidade dos contratos M-T22-*:** travar o shape YAML que impede `tini` sem filho (exit 1) e alinha busca HTTP `-rpc` ao volume de índice.  
**Motivo da separação em IDs distintos:**

| Separação | Por quê |
|---|---|
| M-T22-001 vs M-T22-002 | Argv do filho ≠ política de init (`tini`); ambos necessários para o processo efetivo correto |
| M-T22-003 vs M-T22-001 | Path de índice no volume pode existir sem `command` correto (status quo quebrado); travar ambos |
| M-T22-004 vs M-T22-001 | Um compose correto não basta (D-T22-002 / paridade falsa) |
| M-T22-006 | Segurança transversal (DEC-020); independente do argv |

### 4.3 Relação com M-T19-*

| M-T19 (herdado) | Delta T22 |
|---|---|
| M-T19-002 — serviço `zoekt` existe nos 3 composes | **Adiciona** `command` webserver (M-T22-001) |
| M-T19-007/008/009 — papéis e2e/dev/user | Inalterados; só bloco `zoekt` ganha `command` |
| Volumes `e2e_*` / mounts | Inalterados (M-T22-003 reforça `/data/index`) |

T22 **não** redefine M-T19-*; estende o shape do serviço `zoekt`.

## 5. Contratos de documentação — pré-req compose provider

| ID | Requisito | Arquivos | BDD |
|---|---|---|---|
| M-T22-010 | Documentar explicitamente pré-requisito de **provider Compose no PATH** (`podman-compose` e/ou `docker-compose` / plugin resolvível por `podman compose`) | `e2e/README.md`, `docs/runbook-local.md` | EZ-01 |
| M-T22-011 | Incluir comando de verificação acionável (ex.: `command -v podman-compose` e/ou `podman compose version`) | ambos | EZ-01 |
| M-T22-012 | Incluir orientação de instalação tipica (ex.: `brew install podman-compose` ou equivalente) | ambos | EZ-01 |
| M-T22-013 | Menção a arquivo `docker-compose*.yml` **não** substitui o pré-req do binário provider no PATH | ambos | EZ-01 (assert BDD) |
| M-T22-014 | Docs não embutem PAT/`ghp_`; credenciais só como nomes de variáveis (`GITHUB_TOKEN`, `E2E_GITHUB_TOKEN`) | ambos + composes | EZ-05 |

**Responsabilidade (M-T22-010..014):** superfície operacional do operador/CI para eliminar F-T04-001 sem alterar código Python.  
**Motivo da separação docs × manifesto YAML:** falha de PATH no host ≠ container zoekt exit 1; mitigações distintas (docs vs `command`).  
**Motivo da separação README e2e × runbook:** C-T22-04/05 / R-T22-05 — e2e não pode ser o único lugar documentado.

Conteúdo mínimo esperado (não é Protocol; checklist para Developer):

| Pré-req | Nota |
|---|---|
| Podman instalado e machine running (macOS) | `podman info` ok |
| Provider Compose no PATH | `podman-compose` **ou** plugin/`docker-compose` resolvível |
| Verificação | `command -v podman-compose` + `podman compose version` |
| Instalação tipica | `brew install podman-compose` (exemplo; sem pin de versão obrigatório) |

## 6. Helper de parsing de compose (opcional — só testes)

### 6.1 Decisão

| Opção | Status |
|---|---|
| Helper em `src/github_rag/**` | **Proibido** (I-T22-001 / I-T22-007) |
| Funções locais em `tests/bdd/test_e2e_compose_zoekt_fix.py` | **Permitido e atual** (`_service_block`, `_zoekt_command_blob`) |
| Helper compartilhado sob `tests/` (ex. `tests/support/compose_manifest.py`) | **Opcional** — só se unitários T22 precisarem reusar a mesma extração |

### 6.2 Contrato do helper de teste (se extraído / compartilhado)

```python
# tests/support/compose_manifest.py  — OPCIONAL; não é API de produção

from pathlib import Path

def service_block(compose_text: str, service: str) -> str:
    """Extrai o bloco YAML textual de um serviço sob ``services:``.

    Responsabilidade
        Isolar a fatia do manifesto correspondente a ``service`` para
        asserts de regressão (existência de chaves/tokens) sem subir stack
        e sem depender de ``compose config`` / daemon.

    Motivo da separação
        Parser de texto de teste ≠ launcher T21 ≠ domínio Zoekt (T10).
        Mantém REQ-044 / DEC-017 (gate manifesto-only).
    """
    ...


def zoekt_command_blob(compose_text: str) -> str:
    """Retorna o texto do ``command`` do serviço ``zoekt``.

    Responsabilidade
        Localizar ``command`` (forma preferida: lista JSON inline) e
        expor o blob para checagem dos tokens M-T22-001
        (``zoekt-webserver``, ``-index``, ``/data/index``, ``-rpc``).
        Ausência de ``command`` deve falhar com mensagem acionável
        (F-T04-002: tini sem filho).

    Motivo da separação
        Extração do argv ≠ asserção de paridade entre composes (EZ-03)
        ≠ asserts de docs (EZ-01). Facilita unitários sem duplicar regex.
    """
    ...


def assert_zoekt_webserver_command(compose_text: str, *, compose_name: str) -> str:
    """Valida M-T22-001/003 no texto de um compose.

    Responsabilidade
        Gate único reutilizável: tokens do webserver + presença de
        ``/data/index`` no bloco ``zoekt``.

    Motivo da separação
        Cenários EZ-02 (por arquivo) e EZ-03 (paridade) compartilham a
        mesma regra; evita drift entre BDD e unitários.
    """
    ...
```

**Forma YAML suportada pelo helper (contrato de teste):**  
prioridade à lista JSON inline (M-T22-007). Forma multilinha YAML (`command:` + itens `-`) **não** é obrigatória; se a implementação desviar da forma JSON, o Developer deve alinhar ao design §3.1 **ou** o QA endurece o parser nos unitários (SUGGESTION BDD residual).

**Não** usar `yaml.safe_load` completo como dependência de produção; se unitários optarem por parser YAML completo, fica restrito a `tests/` e deps de teste.

## 7. Aceite tooling F-T04-003 (contrato operacional, não Protocol)

| Fase T21 | Critério T22 | Gate |
|---|---|---|
| `compose` | Completa sem zoekt `Exited (1)` por `tini` sem filho | Pré-condição M-T22-001..004 no CI; runtime = `python -m github_rag.e2e` |
| `healthy` | `wait_healthy` alcança `/healthz` do app | Runtime T21 (I-T22-002) |
| `robot` | Green path **é iniciado** (não skip por tooling) | Runtime; pass/fail de cenário de produto **não** bloqueia T22 (D-T22-008) |

**Responsabilidade:** amarrar EZ-04 ao reuso T21 sem criar porta nova.  
**Motivo da separação:** prova operacional ≠ asserts pytest de manifesto (D-T22-006).

## 8. Mapeamento BDD → contratos

| Cenário | Contratos |
|---|---|
| EZ-01 | M-T22-010..013; I-T22-004 |
| EZ-02 | M-T22-001/002/003/005/007; I-T22-006/009 |
| EZ-03 | M-T22-004; I-T22-005 |
| EZ-04 | I-T22-002/003; §7; pré-condições EZ-01..03 |
| EZ-05 | M-T22-006; M-T22-014 |

## 9. Handoff

| Consumidor | Uso |
|---|---|
| Developer | Materializar `command` zoekt nos 3 YAML + docs M-T22-010..014; **não** alterar `src/github_rag/e2e/ports.py` |
| QA (unit plan) | Asserts manifesto/docs contra M-T22-*; extremos: `command` ausente, tokens faltando, compose sem paridade, docs só com menção a `.yml` |
| Operador / CI | Pré-reqs docs → `python -m github_rag.e2e` (T21) |
| T10 / T19 | Contratos HTTP/volume e papéis compose permanecem |

Mudança de Protocol T21, expansão Robot, ou domínio Zoekt além do argv compose ⇒ `SCOPE_CHANGE_REQUIRED`.

## 10. Estado

`APPROVED_BY_ARCHITECT` — interfaces `0.1.0` completas: I-T22-001..009 + M-T22-001..007 + M-T22-010..014; sem Protocols novos; sem BLOCKING/MAJOR abertos. Prosseguir para unit-test-plan (QA).
