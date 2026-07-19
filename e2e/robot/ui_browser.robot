*** Settings ***
Documentation     Evidência browser (Browser Library) — lacuna UI T23; não substitui ui.robot / catalog_indexing.robot
Resource          resources/browser.resource
Library           Browser
Force Tags        ui    browser    mvp
Suite Setup       Open Ui Browser
Suite Teardown    Close Ui Browser

*** Test Cases ***
BDD-001 Listagem UI Com Wildcard De Inclusao
    [Tags]    bdd001
    Wait Repos Table Loaded
    Assert Reference Repo In Table
    Assert Github Rows Match Inclusion Wildcard
    ${text}=    Get Text    \#repos-table
    Should Contain    ${text}    ${REFERENCE_REPO}

BDD-016 Origem Local Visivel Na Tabela
    [Tags]    bdd016
    Wait Repos Table Loaded
    Assert Local Origin Visible
    ${text}=    Get Text    \#repos-table
    Should Contain    ${text}    local

BDD-019 Pagina Sem Input De Token
    [Tags]    bdd019
    Assert No Token Input On Page
    Assert Page Body Has No Env Token

BDD-023 Sem Crud Connections Gestao E Pesquisa Presentes
    [Tags]    bdd023
    Assert No Connections Crud
    Assert Management And Search Surface Present
    Wait For Elements State    \#repos-table    visible
    Wait For Elements State    \#btn-index    visible
    Wait For Elements State    \#exact-form    visible
    Wait For Elements State    \#semantic-form    visible

BDD-002 Checkbox Indexar E Estados Na UI
    [Tags]    bdd002
    Wait Repos Table Loaded
    Select Reference Repo Checkbox
    Click Index Selected
    Wait Until Keyword Succeeds    ${INDEXING_TIMEOUT_SECONDS}s    ${INDEXING_POLL_SECONDS}s
    ...    Reference Repo Reached Terminal Or Progress Ui
    ${state}=    Repo Row State Text    ${REFERENCE_REPO}
    Should Be True
    ...    '${state}' in ['na fila', 'indexando', 'atualizado']
    ...    msg=Estado UI inesperado: ${state}
    Wait Reference Repo Ui State    atualizado
    Click    \#btn-refresh
    ${final}=    Repo Row State Text    ${REFERENCE_REPO}
    Should Be Equal    ${final}    atualizado

BDD-007 Detalhe Progresso E Flags Zoekt Tree Sitter Metadata
    [Tags]    bdd007
    Wait Repos Table Loaded
    Open Reference Repo Detail
    Assert Repo Detail Progress And Flags
    ${detail}=    Get Text    \#repo-detail
    Should Not Be Empty    ${detail}

BDD-009 Busca Exata Form E Search Results
    [Tags]    bdd009
    Submit Exact Search    github_rag
    Assert Search Results Not Empty
    Fill Text    \#exact-pattern    def
    Click    \#exact-form button[type=submit]
    ${hits2}=    Get Text    \#search-results
    Should Not Be Empty    ${hits2}

BDD-010 Busca Semantica Form E Search Results
    [Tags]    bdd010
    Submit Semantic Search    container delivery compose
    Assert Search Results Not Empty
    Wait For Elements State    \#semantic-query    visible
    Wait For Elements State    \#search-results    visible

*** Keywords ***
Reference Repo Reached Terminal Or Progress Ui
    [Documentation]    Poll intermediário — estado na fila / indexando / atualizado.
    Refresh Repos Table
    ${state}=    Repo Row State Text    ${REFERENCE_REPO}
    Should Be True
    ...    '${state}' in ['na fila', 'indexando', 'atualizado']
    ...    msg=Aguardando progressão UI; estado=${state}
