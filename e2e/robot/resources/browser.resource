*** Settings ***
Documentation     Browser Library lifecycle + UI helpers (T23 / C-T23-02).
...               Separated from common.resource: HTTP session ≠ New Browser/Page.
Resource          common.resource
Library           Browser
Library           Collections
Library           OperatingSystem
Library           String

*** Variables ***
${BROWSER_HEADLESS}             ${True}
${GITHUB_INCLUSION_PATTERN}     camilocoelhogomes/source-*

*** Keywords ***
Open Ui Browser
    [Documentation]
    ...    Responsabilidade: criar browser Chromium (headless default) e abrir
    ...    página ``${UI_BASE}/``.
    ...    Motivo da separação: único ponto de New Browser/New Page; Suite Setup
    ...    não duplica argv Playwright; headed opcional via ``${BROWSER_HEADLESS}``.
    New Browser    chromium    headless=${BROWSER_HEADLESS}
    New Context
    New Page    ${UI_BASE}/

Close Ui Browser
    [Documentation]
    ...    Responsabilidade: encerrar o browser (Suite Teardown).
    ...    Motivo da separação: teardown idempotente sem acoplar a cases.
    Close Browser

Wait Repos Table Loaded
    [Documentation]
    ...    Responsabilidade: aguardar ``#repos-table`` pronta para asserts
    ...    (``tbody tr`` populada pelo loadRepos da UI).
    ...    Motivo da separação: evita race nos cases 001/016/002 sem poll
    ...    duplicado em cada case.
    Wait For Elements State    \#repos-table tbody tr    visible    timeout=60s

Repos Table Text
    [Documentation]    Texto da tabela de repositórios (DOM).
    Wait Repos Table Loaded
    ${text}=    Get Text    \#repos-table
    RETURN    ${text}

Page Body Text
    [Documentation]    Texto do body — para redaction BDD-019 (não logar token).
    ${text}=    Get Text    body
    RETURN    ${text}

Assert Reference Repo In Table
    [Documentation]    BDD-001 — ``${REFERENCE_REPO}`` aparece em ``#repos-table``.
    ${text}=    Repos Table Text
    Should Contain    ${text}    ${REFERENCE_REPO}

Assert Github Rows Match Inclusion Wildcard
    [Documentation]
    ...    BDD-001 — cada linha com origem ``github`` casa com o padrão de inclusão.
    Wait Repos Table Loaded
    ${count}=    Get Element Count    \#repos-table tbody tr
    Should Be True    ${count} > 0
    FOR    ${i}    IN RANGE    ${count}
        ${origin}=    Get Text    \#repos-table tbody tr >> nth=${i} >> td >> nth=2
        ${origin}=    Strip String    ${origin}
        IF    $origin == 'github'
            ${repo_id}=    Get Text    \#repos-table tbody tr >> nth=${i} >> td >> nth=1
            ${repo_id}=    Strip String    ${repo_id}
            ${ok}=    Evaluate    __import__('fnmatch').fnmatch($repo_id, $GITHUB_INCLUSION_PATTERN)
            Should Be True    ${ok}    msg=Repo github '${repo_id}' fora do padrão '${GITHUB_INCLUSION_PATTERN}'
        END
    END

Assert Local Origin Visible
    [Documentation]    BDD-016 — ao menos uma linha com origem ``local``.
    ${text}=    Repos Table Text
    Should Contain    ${text}    local

Assert No Token Input On Page
    [Documentation]    BDD-019 — sem ``input type=password`` / campo de token.
    ${pwd_count}=    Get Element Count    input[type="password"]
    Should Be Equal As Integers    ${pwd_count}    0
    ${token_named}=    Get Element Count    input[name*="token" i]
    Should Be Equal As Integers    ${token_named}    0
    ${token_id}=    Get Element Count    input[id*="token" i]
    Should Be Equal As Integers    ${token_id}    0

Assert Page Body Has No Env Token
    [Documentation]    BDD-019 — body não contém valor do token do ambiente.
    ${text}=    Page Body Text
    Response Must Not Contain Token    ${text}

Assert No Connections Crud
    [Documentation]    BDD-023 — ausência de superfície CRUD de connections.
    ${body}=    Page Body Text
    ${lower}=    Convert To Lower Case    ${body}
    Should Not Contain    ${lower}    add connection
    Should Not Contain    ${lower}    edit connection
    Should Not Contain    ${lower}    delete connection
    Should Not Contain    ${lower}    nova conexão
    ${conn_forms}=    Get Element Count    form[id*="connection" i]
    Should Be Equal As Integers    ${conn_forms}    0
    ${conn_btns}=    Get Element Count    button[id*="connection" i]
    Should Be Equal As Integers    ${conn_btns}    0

Assert Management And Search Surface Present
    [Documentation]    BDD-023 — gestão (tabela/checkbox/index) + forms de busca.
    Wait For Elements State    \#repos-table    visible
    ${cb}=    Get Element Count    \#repos-table input[type=checkbox][data-id]
    Should Be True    ${cb} > 0
    Wait For Elements State    \#btn-index    visible
    Wait For Elements State    \#exact-form    visible
    Wait For Elements State    \#exact-pattern    visible
    Wait For Elements State    \#semantic-form    visible
    Wait For Elements State    \#semantic-query    visible

Select Reference Repo Checkbox
    [Documentation]    BDD-002 — marca checkbox do ``${REFERENCE_REPO}`` via ``data-id``.
    Wait Repos Table Loaded
    ${detail}=    Get Attribute    button[data-detail]:has-text("${REFERENCE_REPO}")    data-detail
    Check Checkbox    \#repos-table input[type=checkbox][data-id="${detail}"]
    RETURN    ${detail}

Click Index Selected
    [Documentation]    BDD-002 — clica ``#btn-index``.
    Click    \#btn-index

Refresh Repos Table
    [Documentation]    Poll UI via ``#btn-refresh``.
    Click    \#btn-refresh
    Wait Repos Table Loaded

Repo Row State Text
    [Arguments]    ${repo_identifier}
    ${state}=    Get Text
    ...    \#repos-table tbody tr:has(button:has-text("${repo_identifier}")) >> td >> nth=3
    ${state}=    Strip String    ${state}
    RETURN    ${state}

Wait Reference Repo Ui State
    [Documentation]    BDD-002 — poll até estado PT desejado (ou timeout indexação).
    [Arguments]    ${wanted}    ${timeout}=${INDEXING_TIMEOUT_SECONDS}
    Wait Until Keyword Succeeds    ${timeout}s    ${INDEXING_POLL_SECONDS}s
    ...    Reference Repo Ui State Is    ${wanted}

Reference Repo Ui State Is
    [Arguments]    ${wanted}
    Refresh Repos Table
    ${state}=    Repo Row State Text    ${REFERENCE_REPO}
    Should Be Equal    ${state}    ${wanted}
    RETURN    ${state}

Open Reference Repo Detail
    [Documentation]    BDD-007 — abre detalhe via ``[data-detail]``.
    Wait Repos Table Loaded
    Click    button[data-detail]:has-text("${REFERENCE_REPO}")
    Wait For Elements State    \#repo-detail    visible

Assert Repo Detail Progress And Flags
    [Documentation]    BDD-007 — ``#repo-detail`` com progresso e flags zoekt/tree_sitter/metadata.
    ${text}=    Get Text    \#repo-detail
    Should Not Be Empty    ${text}
    Should Contain    ${text}    Detalhe
    Should Contain    ${text}    zoekt=
    Should Contain    ${text}    tree_sitter=
    Should Contain    ${text}    metadata=

Submit Exact Search
    [Documentation]    BDD-009 — fill ``#exact-pattern`` e submit ``#exact-form``.
    [Arguments]    ${pattern}
    Fill Text    \#exact-pattern    ${pattern}
    Click    \#exact-form button[type=submit]
    Wait For Elements State    \#search-results    visible

Submit Semantic Search
    [Documentation]    BDD-010 — fill ``#semantic-query`` e submit ``#semantic-form``.
    [Arguments]    ${query}
    Fill Text    \#semantic-query    ${query}
    Click    \#semantic-form button[type=submit]
    Wait For Elements State    \#search-results    visible

Assert Search Results Not Empty
    [Documentation]    BDD-009/010 — ``#search-results`` não vazio.
    ${text}=    Get Text    \#search-results
    Should Not Be Empty    ${text}
    ${stripped}=    Strip String    ${text}
    Should Not Be Equal    ${stripped}    []
    Response Must Not Contain Token    ${text}
