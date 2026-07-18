# Requisitos — ETL de repositórios com RAG e servidor MCP

## Identificação

- **Feature ID:** `github-etl-mcp-rag`
- **Versão:** 0.3.0
- **Estado:** `HUMAN_PLAN_APPROVAL`
- **Natureza:** requisitos aprovados; plano de engenharia v0.1.2 aprovado pelo PO (`PO_PLAN_APPROVED`); candidato aguardando aprovação humana do plano.
- **Aprovação humana (requisitos):** `aprovo` em 2026-07-18 por `camilocoelhogomes` (commit candidato `71ed647`).
- **Artefatos de engenharia:** `implementation-plan.md` v0.1.2 (`PO_PLAN_APPROVED` → `HUMAN_PLAN_APPROVAL`); tasks `T01`–`T19` em `tasks/`.
- **Rastreabilidade:** requisitos `REQ-*`, regras `BR-*`, decisões `DEC-*` e cenários `BDD-*`.

## Problema

Arquitetos precisam realizar Discovery sobre centenas ou milhares de microsserviços, mas o conhecimento necessário está disperso entre muitos repositórios GitHub e repositórios disponíveis localmente. Eles precisam descobrir o que alterar, como atingir um objetivo, qual repositório editar e quais repositórios ou fluxos retestar após uma implementação.

## Objetivos

- **REQ-001:** Indexar localmente o snapshot atual da branch `main` de múltiplos repositórios GitHub públicos e privados e de repositórios locais.
- **REQ-002:** Oferecer busca exata e semântica sobre os repositórios indexados.
- **REQ-003:** Expor evidências de código a agentes por um servidor MCP conectado ao Cursor.
- **REQ-004:** Permitir indexações paralelas e consultas paralelas, limitadas por variáveis de ambiente.
- **REQ-005:** Evitar o reprocessamento de commits já indexados.
- **REQ-006:** Oferecer uma UI simples para visualizar os repositórios configurados, controlar indexações, acompanhar progresso e erros e pesquisar código.
- **REQ-007:** Executar integralmente na máquina local do desenvolvedor.
- **REQ-008:** Apoiar o agente do Cursor a produzir respostas coerentes para Discovery, baseadas nas evidências recuperadas.

## Personas

- **Arquiteto:** consulta muitos microsserviços durante Discovery para localizar mudanças e impactos.
- **Desenvolvedor/operador local:** fornece acesso ao GitHub por variável de ambiente, monta repositórios locais no container, seleciona repositórios, agenda ou dispara indexações e acompanha a execução.
- **Agente MCP no Cursor:** consulta evidências; ele próprio monta a resposta narrativa ao usuário.

## Escopo funcional

### Configuração e seleção

- **REQ-009:** Configurar declarativamente todos os repositórios a indexar em um arquivo JSON externo, montado como volume no container e apontado pela variável de ambiente `CONFIG_PATH`.
- **REQ-010:** Configurar conexões GitHub por organização e incluir repositórios por wildcards de prefixo e sufixo no arquivo JSON.
- **REQ-011:** Suportar repositórios públicos e privados acessíveis por um token GitHub global do usuário, fornecido por variável de ambiente.
- **REQ-012:** Permitir selecionar por checkbox os repositórios de uma indexação sob demanda.
- **REQ-034:** Detectar e disponibilizar para indexação repositórios locais declarados no arquivo JSON e fornecidos por montagem de volume no container.
- **REQ-035:** Identificar na UI a origem de cada repositório como GitHub ou local.
- **REQ-039:** Estruturar o arquivo JSON no padrão declarativo do Sourcebot, com um objeto `connections` de conexões nomeadas.
- **REQ-040:** Referenciar repositórios locais por conexão `type: "git"` e URL absoluta `file://`, com suporte a glob de caminhos montados.
- **REQ-041:** Referenciar o segredo de uma conexão GitHub no JSON por `{ "env": "NOME_DA_VARIAVEL" }`, sem incluir o valor do token no JSON.
- **REQ-042:** Ler e validar integralmente o arquivo indicado por `CONFIG_PATH` antes de descobrir repositórios e informar configuração ausente ou inválida sem aplicar parcialmente suas conexões.

### Indexação

- **REQ-013:** Indexar somente o snapshot atual do commit da branch `main`, considerada o código atualmente em QA, tanto para repositórios GitHub quanto locais.
- **REQ-014:** Indexar arquivos textuais relacionados ao desenvolvimento, independentemente da linguagem, incluindo Markdown e Java.
- **REQ-015:** Excluir CSV, imagens e arquivos ou diretórios normalmente ignorados pelo `.gitignore`, como `target` e `node_modules`.
- **REQ-016:** Permitir indexação sob demanda pela UI.
- **REQ-017:** Executar indexação periódica uma vez ao dia, com horário configurável pela UI e por variável de ambiente.
- **REQ-018:** Reiniciar a indexação completa do repositório quando ocorrer falha parcial.
- **REQ-019:** Não impor limite funcional explícito ao tamanho de arquivo ou repositório no MVP.

### Distribuição

- **REQ-036:** Disponibilizar preferencialmente o produto por imagens de container para uso padronizado pelos desenvolvedores da empresa.
- **REQ-037:** Permitir configurar por variáveis de ambiente o caminho do arquivo declarativo (`CONFIG_PATH`), o token GitHub e os limites de workers.
- **REQ-038:** Permitir montar no container os volumes que contêm os repositórios locais referenciados pelas conexões do JSON.

### UI de gestão e busca

- **REQ-020:** Exibir, por repositório, um dos estados: `não indexado`, `na fila`, `indexando`, `atualizado` ou `erro`.
- **REQ-021:** Durante a indexação, exibir percentual, quantidade de arquivos processados e etapa atual.
- **REQ-022:** Registrar por arquivo se ele foi enviado ao Zoekt, processado pelo Tree-sitter e salvo com metadados gerados pelo modelo local.
- **REQ-023:** Em falhas, exibir mensagem, horário e histórico de execuções.
- **REQ-024:** Considerar um repositório `atualizado` somente quando o commit atual de `main` for igual ao último commit processado registrado.
- **REQ-025:** Permitir visualizar os repositórios definidos pelo ambiente, selecionar por checkbox e iniciar indexações, sem cadastrar, editar ou remover suas definições pela UI.
- **REQ-026:** Oferecer busca exata e busca semântica na UI.
- **REQ-027:** Permitir que o modelo local interaja com a UI, inclusive apoiando a experiência de busca semântica; a recuperação semântica continua baseada em embeddings e Qdrant.

### MCP

- **REQ-028:** Disponibilizar as operações aprovadas:
  - `list_repos`: listar repositórios indexados e seus estados;
  - `search_code`: pesquisar código por correspondência exata;
  - `semantic_search`: recuperar resultados semanticamente relacionados;
  - `read_file`: recuperar conteúdo de arquivo;
  - `list_tree`: navegar pela árvore de arquivos.
- **REQ-029:** Permitir consultas paralelas, respeitando o limite de workers configurado.
- **REQ-030:** Retornar repositório, caminho, commit e trecho somente quando o agente chamador solicitar esses dados.
- **REQ-031:** O MCP deve entregar evidências pelas operações aprovadas, sem gerar resposta narrativa.
- **REQ-032:** O modelo local não deve participar da geração das respostas do MCP.
- **REQ-033:** O agente no Cursor deve montar a narrativa de Discovery a partir das evidências retornadas.

## Regras de negócio

- **BR-001:** PostgreSQL é a fonte de verdade para repositórios GitHub e locais, suas origens, estado de indexação e último commit processado.
- **BR-002:** Antes de indexar, o último commit processado deve ser comparado ao commit atual da `main`.
- **BR-003:** Um commit já registrado como processado não deve ser reprocessado.
- **BR-004:** O estado `atualizado` exige igualdade entre o commit atual da `main` e o último commit processado.
- **BR-005:** Falha em qualquer etapa invalida a execução corrente do repositório; uma nova tentativa recomeça o repositório inteiro.
- **BR-006:** O paralelismo de indexação e consulta deve respeitar os limites definidos por variáveis de ambiente.
- **BR-007:** O token GitHub é global por usuário, deve ser fornecido por variável de ambiente e deve conceder acesso aos repositórios privados desejados.
- **BR-008:** O token é segredo: não pode aparecer em respostas MCP, resultados de busca, logs nem mensagens da UI.
- **BR-009:** O modelo local padrão é Qwen Coder 3B, atrás de abstração que permita trocar provedor ou modelo.
- **BR-010:** O modelo local é usado para gerar metadados contextuais na indexação e para interação com a UI, nunca para produzir respostas MCP.
- **BR-011:** A busca semântica MCP recupera evidências por embeddings/Qdrant e não gera prosa com o SLM.
- **BR-012:** A UI não deve persistir nem ser a fonte principal de configuração do token GitHub.
- **BR-013:** Repositórios locais somente entram no catálogo quando declarados no arquivo apontado por `CONFIG_PATH` e disponibilizados ao container por montagem de volume.
- **BR-014:** Repositórios GitHub e locais seguem o mesmo pipeline, estados, critérios de elegibilidade de arquivos e política de falha.
- **BR-015:** Para preservar o escopo da `main`, alterações locais não confirmadas em commit e conteúdo de outras branches não entram na indexação.
- **BR-016:** O arquivo JSON externo apontado por `CONFIG_PATH` é a única fonte de verdade para definir quais conexões e repositórios podem ser indexados.
- **BR-017:** A UI não pode criar, editar nem excluir conexões ou definições de repositórios.
- **BR-018:** Cada entrada de `connections` deve ter nome único e tipo compatível com sua origem: `github` para GitHub ou `git` para caminho local.
- **BR-019:** O token GitHub deve permanecer em variável de ambiente separada e ser apenas referenciado pela conexão declarativa.
- **BR-020:** O arquivo apontado por `CONFIG_PATH` deve ser carregado e validado na inicialização do container; alterações exigem reinicialização para serem aplicadas.
- **BR-021:** Configuração ausente, JSON malformado, conexão inválida ou referência de segredo inexistente não pode produzir cadastro parcial silencioso.
- **BR-022:** Wildcards de repositório em conexões GitHub são filtros exclusivamente de inclusão; somente repositórios correspondentes podem entrar no catálogo.

## Contrato declarativo da configuração

`CONFIG_PATH` deve apontar para um arquivo JSON válido montado no container. O arquivo não pode conter o valor de nenhum segredo e deve seguir a estrutura de `connections` do Sourcebot. Neste produto, o campo `repos` da conexão GitHub é exclusivamente de inclusão e aceita wildcards. Exemplo representativo:

```json
{
  "connections": {
    "github-microservices": {
      "type": "github",
      "token": {
        "env": "GITHUB_TOKEN"
      },
      "orgs": [
        "my-org"
      ],
      "repos": [
        "my-org/microservice-*",
        "my-org/*-api"
      ],
      "revisions": {
        "branches": [
          "main"
        ]
      }
    },
    "local-microservices": {
      "type": "git",
      "url": "file:///repos/*",
      "revisions": {
        "branches": [
          "main"
        ]
      }
    }
  }
}
```

O contrato mantém o padrão Sourcebot de arquivo externo, `CONFIG_PATH`, `connections`, referência de token por variável de ambiente e conexões locais `type: "git"` com URLs `file:///...`. A inclusão por wildcard no campo `repos` é requisito específico deste produto.

## Dados e rastreabilidade operacional

- Nome da conexão declarativa, repositório, tipo de origem (`GitHub` ou `local`) e, quando aplicável, organização GitHub ou caminho montado.
- Commit atual da `main` e último commit processado.
- Estado atual da indexação.
- Percentual, arquivos processados e etapa atual.
- Registro por arquivo das etapas Zoekt, Tree-sitter e persistência dos metadados.
- Mensagem e horário de erro.
- Histórico de execuções.
- Chunks por contexto e metadados contextuais.
- Vetores usados na recuperação semântica.

## Integrações e decisões fechadas

- **DEC-001:** GitHub e volumes locais montados no container são origens de repositórios.
- **DEC-009:** A autenticação GitHub usa token de usuário com permissão de repositórios, fornecido por variável de ambiente.
- **DEC-002:** Zoekt executa buscas exatas e mantém os metadados necessários a esse índice.
- **DEC-003:** Tree-sitter cria chunks contextuais antes da persistência no RAG.
- **DEC-004:** Qdrant é o banco vetorial.
- **DEC-005:** PostgreSQL é o banco relacional e a fonte de verdade dos estados; SQLite foi descartado.
- **DEC-006:** Uma SLM com provedor/modelo abstrato gera metadados contextuais; Qwen Coder 3B é o padrão.
- **DEC-007:** Todo processamento ocorre localmente.
- **DEC-008:** O MCP expõe somente evidências; a narrativa é responsabilidade do agente chamador no Cursor.
- **DEC-010:** Repositórios locais são informados exclusivamente por montagem de volume no container.
- **DEC-011:** Imagens de container são a forma preferencial de distribuição para os desenvolvedores da empresa.
- **DEC-012:** A configuração dos repositórios segue o padrão Sourcebot de arquivo JSON externo montado por volume e caminho informado em `CONFIG_PATH`, usando `connections`.
- **DEC-013:** Definições de repositórios não são mantidas pela UI; a UI opera sobre o catálogo derivado da configuração de ambiente.
- **DEC-014:** Wildcards de repositórios GitHub são usados somente para inclusão.

## Fluxo principal

1. O desenvolvedor obtém a imagem de container, cria o arquivo JSON externo com as conexões GitHub e locais e o monta no container.
2. O desenvolvedor define `CONFIG_PATH` com o caminho interno desse arquivo, fornece o token GitHub em variável separada referenciada pelo JSON e monta os volumes declarados pelas URLs `file://`.
3. Na inicialização, o sistema lê por `CONFIG_PATH` e valida integralmente o arquivo JSON.
4. O sistema descobre os repositórios GitHub conforme organização e filtros declarados e os repositórios Git válidos encontrados nos caminhos locais.
5. A UI apresenta os repositórios GitHub e locais, suas conexões, origens e estados, sem permitir alterar a configuração.
6. O usuário seleciona repositórios por checkbox e inicia a indexação, ou o agendamento diário a dispara.
7. Para cada repositório, o sistema consulta o snapshot atual da `main` e compara seu commit ao último processado.
8. Repositórios já atualizados não são reprocessados.
9. Os demais entram na fila e são processados em paralelo até o limite configurado.
10. Arquivos elegíveis passam pelas etapas de Zoekt, Tree-sitter, geração local de metadados e persistência relacional/vetorial.
11. A UI atualiza progresso, etapa e rastreabilidade por arquivo.
12. Ao concluir, o último commit processado é registrado e o repositório passa a `atualizado`.
13. Usuários pesquisam na UI ou agentes recuperam evidências pelas tools MCP.

## Fluxos alternativos e erros

- Variável de ambiente do token ausente, token inválido ou sem acesso: os repositórios GitHub afetados não são descobertos ou indexados, e a execução registra erro sem expor o token.
- `CONFIG_PATH` ausente, arquivo inexistente/inacessível ou JSON inválido: nenhuma conexão é aplicada parcialmente e o erro de configuração é informado.
- Conexão sem tipo, com tipo desconhecido ou com referência de segredo inexistente: a configuração é rejeitada e o erro identifica a conexão, sem expor segredos.
- Nenhum repositório corresponde aos filtros declarados: a UI apresenta lista vazia sem iniciar indexação.
- Volume local ausente ou inacessível: nenhum repositório desse volume é disponibilizado, e a execução registra erro.
- Caminho montado sem repositório Git válido ou sem branch `main`: o caminho não é indexado, e a execução registra erro.
- Commit já processado: o repositório permanece `atualizado` e não é reprocessado.
- Novo commit em `main`: o repositório deixa de estar atualizado e pode ser indexado no ciclo diário ou sob demanda.
- Falha de rede, Zoekt, parser, modelo local, PostgreSQL ou Qdrant: a execução fica em `erro`; uma nova tentativa reinicia o repositório inteiro.
- Arquivo excluído ou ignorado: não entra no pipeline de indexação.
- Limite de workers atingido: os repositórios ou consultas excedentes aguardam capacidade.

## Restrições

- Execução local e leve para máquinas de desenvolvedores.
- Distribuição preferencial por imagens de container.
- Repositórios locais fornecidos ao container por montagem de volume.
- Definições de conexões e repositórios fornecidas exclusivamente pelo arquivo JSON externo apontado por `CONFIG_PATH`, sem cadastro persistido pela UI.
- Token GitHub fornecido ao container por variável de ambiente separada e referenciado pelo JSON, sem configuração persistida pela UI.
- Empacotamento e limites de CPU, memória e disco serão definidos no Dockerfile e na configuração da imagem.
- Sem requisito de latência no MVP.
- Cobertura mínima de testes do projeto: 95%.
- O produto deve operar com centenas ou milhares de repositórios, sujeito aos recursos locais configurados.

## Fora de escopo do MVP

- Branches diferentes de `main`.
- Alterações locais não confirmadas em commit.
- Histórico completo de commits; indexa-se o snapshot atual.
- Pull requests, issues, GitHub Actions e webhooks.
- Geração de narrativa ou operação `ask_codebase` no MCP.
- Busca baseada no conteúdo de CSV e imagens.
- Definições/referências de símbolos, diffs e demais operações MCP não aprovadas.
- SLA ou meta numérica de latência.

## Métrica de sucesso

- O servidor MCP conecta-se ao Cursor.
- Em validação humana com perguntas representativas de Discovery, o agente do Cursor consegue usar as evidências recuperadas para indicar:
  1. o que deve ser alterado;
  2. como atingir o objetivo;
  3. qual repositório deve ser editado;
  4. quais repositórios ou fluxos devem ser retestados.
- Repositórios cujo commit da `main` já foi processado não são reindexados.

## Critérios de aceite BDD

### BDD-001 — Descobrir repositórios de uma organização

**Dado** um token GitHub válido fornecido por variável de ambiente com acesso a repositórios públicos e privados  
**E** uma conexão GitHub com organização e wildcards de inclusão declarados no arquivo apontado por `CONFIG_PATH`  
**Quando** o container carregar a configuração  
**Então** a UI deve listar somente os repositórios acessíveis que correspondam aos wildcards de inclusão.

### BDD-002 — Indexar repositórios selecionados

**Dado** que existem repositórios configurados como `não indexado`  
**Quando** o usuário selecionar repositórios por checkbox e iniciar a indexação  
**Então** eles devem passar por `na fila`, `indexando` e `atualizado`  
**E** o paralelismo deve respeitar o limite de workers configurado.

### BDD-003 — Executar o agendamento diário

**Dado** um horário diário configurado pela UI ou variável de ambiente  
**Quando** o horário configurado chegar  
**Então** o sistema deve verificar os repositórios configurados e indexar os que não estiverem atualizados.

### BDD-004 — Evitar reprocessamento

**Dado** que o PostgreSQL registra um commit como último commit processado  
**E** esse commit é o commit atual da `main`  
**Quando** uma indexação periódica ou sob demanda verificar o repositório  
**Então** o conteúdo não deve ser reprocessado  
**E** o repositório deve permanecer `atualizado`.

### BDD-005 — Indexar um novo snapshot

**Dado** que o commit atual da `main` difere do último commit processado  
**Quando** a indexação for executada  
**Então** o snapshot atual deve ser processado  
**E** o novo commit deve tornar-se o último commit processado após conclusão bem-sucedida.

### BDD-006 — Filtrar arquivos elegíveis

**Dado** um snapshot com arquivos textuais de desenvolvimento, Markdown, Java, CSV, imagens e caminhos ignorados pelo `.gitignore`  
**Quando** o snapshot for preparado para indexação  
**Então** os arquivos textuais de desenvolvimento, incluindo Markdown e Java, devem ser incluídos  
**E** CSV, imagens e caminhos ignorados devem ser excluídos.

### BDD-007 — Acompanhar progresso detalhado

**Dado** um repositório em indexação  
**Quando** arquivos avançarem pelo pipeline  
**Então** a UI deve mostrar percentual, quantidade processada e etapa atual  
**E** registrar, por arquivo, a passagem por Zoekt, Tree-sitter e persistência dos metadados gerados.

### BDD-008 — Tratar falha parcial

**Dado** que uma etapa falhou após parte dos arquivos ter sido processada  
**Quando** a execução terminar com erro  
**Então** a UI deve mostrar estado `erro`, mensagem, horário e histórico  
**E** uma nova tentativa deve reiniciar a indexação do repositório inteiro.

### BDD-009 — Buscar código exato pela UI

**Dado** que existem repositórios atualizados  
**Quando** o usuário realizar uma busca exata na UI  
**Então** a UI deve apresentar as correspondências encontradas no índice de código.

### BDD-010 — Buscar semanticamente pela UI

**Dado** que existem chunks e metadados indexados no Qdrant  
**Quando** o usuário realizar uma busca semântica na UI  
**Então** a UI deve apresentar resultados semanticamente relacionados  
**E** o modelo local pode apoiar a interação da UI.

### BDD-011 — Consultar evidências pelo MCP

**Dado** que o servidor MCP está conectado ao Cursor  
**Quando** o agente chamar `list_repos`, `search_code`, `semantic_search`, `read_file` ou `list_tree`  
**Então** o MCP deve retornar evidências correspondentes à operação  
**E** não deve usar o modelo local para gerar uma resposta narrativa.

### BDD-012 — Retornar detalhes somente quando solicitados

**Dado** uma consulta MCP com resultados  
**Quando** o agente não solicitar repositório, caminho, commit ou trecho  
**Então** esses detalhes opcionais não devem ser incluídos  
**Quando** o agente os solicitar  
**Então** os detalhes solicitados devem ser retornados quando aplicáveis.

### BDD-013 — Executar consultas paralelas

**Dado** múltiplas consultas MCP simultâneas  
**Quando** elas forem recebidas  
**Então** devem ser processadas em paralelo até o limite configurado  
**E** as excedentes devem aguardar capacidade.

### BDD-014 — Proteger o token

**Dado** um token GitHub configurado  
**Quando** ocorrer indexação, busca, consulta MCP ou erro  
**Então** o token não deve aparecer em logs, mensagens da UI nem respostas MCP.

### BDD-015 — Apoiar Discovery no Cursor

**Dado** repositórios representativos indexados e o MCP conectado ao Cursor  
**Quando** um arquiteto perguntar o que alterar, como atingir um objetivo, qual repositório editar ou o que retestar  
**Então** o agente do Cursor deve conseguir consultar as tools aprovadas  
**E** compor uma resposta coerente baseada nas evidências recuperadas.

### BDD-016 — Descobrir repositórios locais montados

**Dado** uma imagem do produto em execução  
**E** uma conexão local `type: "git"` com URL `file://` declarada no arquivo apontado por `CONFIG_PATH`  
**E** um volume correspondente montado contendo repositórios Git válidos com branch `main`  
**Quando** o sistema carregar a configuração e descobrir as origens disponíveis  
**Então** os repositórios locais devem aparecer na UI identificados como `local`  
**E** devem estar disponíveis para seleção e indexação.

### BDD-017 — Indexar somente a `main` de repositório local

**Dado** um repositório local montado com uma branch `main`, outras branches e alterações não confirmadas  
**Quando** o repositório for indexado  
**Então** somente o snapshot do commit atual da `main` deve entrar no pipeline  
**E** outras branches e alterações não confirmadas não devem ser indexadas.

### BDD-018 — Tratar volume local indisponível

**Dado** um volume local configurado que esteja ausente ou inacessível  
**Quando** o sistema tentar descobrir ou indexar seus repositórios  
**Então** os repositórios desse volume não devem ser indexados  
**E** a UI deve registrar o erro correspondente.

### BDD-019 — Obter token GitHub do ambiente

**Dado** um container iniciado com o token GitHub em variável de ambiente  
**E** uma conexão GitHub cujo campo `token.env` referencia essa variável  
**Quando** o sistema acessar a organização GitHub  
**Então** deve usar o token fornecido pelo ambiente  
**E** a UI não deve solicitar nem persistir esse token.

### BDD-020 — Executar a imagem de container distribuída

**Dado** uma imagem de container disponibilizada para os desenvolvedores  
**E** `CONFIG_PATH`, o arquivo JSON externo, as variáveis de segredo e as montagens de volume necessárias  
**Quando** um desenvolvedor iniciar o produto  
**Então** a UI e o servidor MCP devem ficar disponíveis para uso local.

### BDD-021 — Carregar configuração declarativa

**Dado** um arquivo JSON válido com conexões GitHub e locais nomeadas  
**E** `CONFIG_PATH` apontando para esse arquivo montado  
**Quando** o container iniciar  
**Então** todas as conexões devem ser carregadas  
**E** os repositórios descobertos devem ser identificados pela conexão e origem correspondentes.

### BDD-022 — Rejeitar configuração inválida

**Dado** `CONFIG_PATH` ausente ou apontando para arquivo inexistente, malformado ou com conexão inválida  
**Quando** o container iniciar  
**Então** nenhuma conexão da configuração deve ser aplicada parcialmente  
**E** o erro deve ser informado sem expor segredos.

### BDD-023 — Manter configuração fora da UI

**Dado** os repositórios carregados do arquivo apontado por `CONFIG_PATH`  
**Quando** o usuário acessar a UI  
**Então** deve conseguir visualizar estados, selecionar repositórios, disparar indexações e pesquisar  
**E** não deve conseguir cadastrar, editar ou remover conexões ou definições de repositórios.

## Riscos

- Centenas ou milhares de repositórios, arquivos sem limite explícito e SLM local podem exceder CPU, memória, disco ou tempo aceitável.
- Reiniciar um repositório inteiro após falha pode elevar custo e duração de indexação.
- A qualidade dos chunks, metadados e embeddings pode reduzir a coerência das respostas de Discovery.
- Wildcards de inclusão amplos podem selecionar um volume inesperado de repositórios.
- Arquivo de configuração ausente, montado no caminho incorreto ou sem permissão de leitura impede a descoberta dos repositórios.
- Permissões excessivas ou tratamento inadequado do token GitHub podem expor código privado.
- Montagens de volume incorretas podem expor diretórios locais indevidos ao container.
- Diferenças de arquitetura e capacidade entre máquinas dos desenvolvedores podem afetar compatibilidade e desempenho das imagens.
- Ausência de meta objetiva de latência e de um conjunto fechado de perguntas de avaliação limita a mensuração quantitativa do MVP.

## Dúvidas não bloqueantes para refinamento técnico

- Valores padrão e máximos de CPU, memória, disco e workers no Dockerfile.
- Precedência quando o horário diário estiver definido simultaneamente pela UI e por variável de ambiente.
- Convenção de nomes e caminhos internos dos volumes que conterão repositórios locais.
- Registro corporativo, arquiteturas de CPU e plataformas suportadas pelas imagens de container.
- Conjunto representativo de perguntas e repositórios para a validação humana da coerência.

## Matriz resumida de rastreabilidade

| Objetivo | Requisitos/regras | Cenários |
|---|---|---|
| Configurar, descobrir e selecionar repositórios | REQ-009–012, REQ-034–035, REQ-039–042, BR-007, BR-012–022 | BDD-001–002, BDD-016–023 |
| Indexar snapshots sem repetição | REQ-013–019, BR-001–006, BR-014–015 | BDD-003–008, BDD-017–018 |
| Gerir e pesquisar pela UI | REQ-020–027, BR-009–011 | BDD-007, BDD-009–010 |
| Recuperar evidências via MCP | REQ-028–033, DEC-008 | BDD-011–013, BDD-015 |
| Distribuir por containers | REQ-036–038, DEC-011–012 | BDD-020–022 |
| Proteger credenciais | REQ-011, REQ-041, BR-008, BR-012, BR-019, DEC-009 | BDD-014, BDD-019, BDD-022 |
