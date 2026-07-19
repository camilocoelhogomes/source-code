*** Settings ***
Documentation     ROBOT-02 — catalog / indexing BDD-001–008, 016–019, 021 (+ T24 integrais).
Resource          resources/common.resource
Resource          resources/auth.resource
Resource          resources/catalog_indexing.resource
Library           RequestsLibrary
Suite Setup       Run Keywords    Require E2e Credential Present    AND    Create UI Session
Force Tags        catalog_indexing    mvp

*** Keywords ***
List Repos Payload
    ${body}=    Get Json    ui    /api/repos
    ${as_text}=    Evaluate    str($body)
    Response Must Not Contain Token    ${as_text}
    RETURN    ${body}

Find Repo By Identifier
    [Arguments]    ${identifier}
    ${body}=    List Repos Payload
    FOR    ${repo}    IN    @{body}[repos]
        IF    '${repo}[repo_identifier]' == '${identifier}'
            RETURN    ${repo}
        END
    END
    Fail    Repository ${identifier} not found in catalog

Wait Repo State
    [Arguments]    ${repo_id}    ${wanted}    ${timeout}=${INDEXING_TIMEOUT_SECONDS}
    Wait Until Keyword Succeeds    ${timeout}s    ${INDEXING_POLL_SECONDS}s
    ...    Repo State Is    ${repo_id}    ${wanted}

Repo State Is
    [Arguments]    ${repo_id}    ${wanted}
    ${detail}=    Get Json    ui    /api/repos/${repo_id}
    Should Be Equal    ${detail}[state]    ${wanted}
    RETURN    ${detail}

*** Test Cases ***
BDD-001 Github Reference Repo Appears In Catalog
    [Tags]    bdd001    bdd019    bdd021
    Wait Until Keyword Succeeds    180s    5s
    ...    Find Repo By Identifier    ${REFERENCE_REPO}
    ${repo}=    Find Repo By Identifier    ${REFERENCE_REPO}
    Should Be Equal    ${repo}[origin]    github
    Should Not Be Empty    ${repo}[connection_name]

BDD-016 Local Fixture Repo Appears As Local
    [Tags]    bdd016    bdd021
    ${body}=    List Repos Payload
    ${found}=    Set Variable    ${False}
    FOR    ${repo}    IN    @{body}[repos]
        IF    '${repo}[origin]' == 'local'
            ${found}=    Set Variable    ${True}
        END
    END
    Should Be True    ${found}    msg=Expected at least one local origin repo (fixture volume)

BDD-002 Index Reference Repo Until Updated
    [Tags]    bdd002    bdd007
    ${repo}=    Find Repo By Identifier    ${REFERENCE_REPO}
    ${rid}=    Set Variable    ${repo}[id]
    ${ids}=    Create List    ${rid}
    ${body}=    Create Dictionary    repository_ids=${ids}
    Post Json    ui    /api/repos/index    ${body}    expected=202
    Wait Repo State    ${rid}    up_to_date
    ${detail}=    Get Json    ui    /api/repos/${rid}
    Should Be Equal    ${detail}[state]    up_to_date
    Should Be Equal    ${detail}[state_label]    atualizado
    ${as_text}=    Evaluate    str($detail)
    Response Must Not Contain Token    ${as_text}

BDD-003 Scheduler Cron Fires And Indexes Stale Local
    [Documentation]    CI-T24-003 — cron na janela + efeito do tick sem POST index pós-mutação.
    [Tags]    bdd003
    ${local_id}=    Find Local Repo Id
    Index Repo And Wait Up To Date    ${local_id}
    ${sha_b}=    Host Commit On Main
    ${cron_original}=    Capture Scheduler Cron
    ${expr}=    Put Cron Firing Soon Utc
    Wait Repo Indexed By Scheduler Tick    ${local_id}
    Mcp Assert Last Processed Equals    ${sha_b}    repo_id=${local_id}
    [Teardown]    Restore Scheduler Cron    ${cron_original}

BDD-004 Reindex When Already Updated Stays Updated
    [Tags]    bdd004
    ${repo}=    Find Repo By Identifier    ${REFERENCE_REPO}
    ${rid}=    Set Variable    ${repo}[id]
    Wait Repo State    ${rid}    up_to_date    timeout=60
    ${ids}=    Create List    ${rid}
    ${body}=    Create Dictionary    repository_ids=${ids}
    Post Json    ui    /api/repos/index    ${body}    expected=202
    Wait Repo State    ${rid}    up_to_date    timeout=300

BDD-005 Tip Change Updates Last Processed Commit
    [Documentation]    CI-T24-005 — tip main muda → last_processed_commit (MCP).
    [Tags]    bdd005
    ${local_id}=    Find Local Repo Id
    Index Repo And Wait Up To Date    ${local_id}
    ${sha_a}=    Mcp Capture Last Processed Commit    repo_id=${local_id}
    ${sha_b}=    Host Commit On Main
    Should Not Be Equal    ${sha_a}    ${sha_b}
    Index Repo And Wait Up To Date    ${local_id}
    Mcp Assert Last Processed Equals    ${sha_b}    repo_id=${local_id}
    Should Not Be Equal    ${sha_a}    ${sha_b}

BDD-006 Eligibility Include And Exclude Paths
    [Documentation]    CI-T24-006 — include code/MD + exclude CSV/imagem/gitignore.
    [Tags]    bdd006
    Prepare Eligibility Fixture Tree
    ${local_id}=    Find Local Repo Id
    Index Repo And Wait Up To Date    ${local_id}
    Assert Exact Search Hits    ${MARKER_INCLUDE_MD}    ${local_id}    docs/notes.md
    Assert Exact Search Hits    ${MARKER_INCLUDE_JAVA}    ${local_id}    src/Hello.java
    Assert Exact Search Empty    ${MARKER_EXCLUDE_CSV}    ${local_id}
    Assert Exact Search Empty    ${MARKER_EXCLUDE_GITIGNORE}    ${local_id}
    @{includes}=    Create List    docs/notes.md    src/Hello.java
    @{excludes}=    Create List    data/report.csv    img/photo.png    ignored_dir/secret_marker.txt
    Assert Repo Files Paths Eligible    ${local_id}    ${includes}    ${excludes}

BDD-006 Exact Search Finds Python Or Markdown Smoke
    [Documentation]    Complemento T21 — smoke MD/Python no repo GitHub (não substitui CI-T24-006).
    [Tags]    bdd006    bdd009
    ${repo}=    Find Repo By Identifier    ${REFERENCE_REPO}
    ${body}=    Create Dictionary    pattern=def    repository_id=${repo}[id]
    ${hits}=    Post Json    ui    /api/search/exact    ${body}
    Should Not Be Empty    ${hits}[hits]
    ${as_text}=    Evaluate    str($hits)
    Response Must Not Contain Token    ${as_text}

BDD-017 Main Only Other Branch And Uncommitted Absent
    [Documentation]    CI-T24-017 — somente main; other + uncommitted ausentes na busca.
    [Tags]    bdd017
    Prepare MainOnly Fixture Branches
    ${local_id}=    Find Local Repo Id
    Index Repo And Wait Up To Date    ${local_id}
    ${commits}=    Mcp Repo Commits    repo_id=${local_id}
    Should Be Equal    ${commits}[last_processed_commit]    ${commits}[current_main_commit]
    Assert Main Marker Indexed    ${local_id}    ${commits}[last_processed_commit]
    Assert Marker Absent From Exact Search    ${MARKER_OTHER_BRANCH}    ${local_id}
    Assert Marker Absent From Exact Search    ${MARKER_UNCOMMITTED}    ${local_id}

BDD-008 Invalid Index Request Is Explicit Error
    [Tags]    bdd008
    ${r}=    POST On Session    ui    /api/repos/index
    ...    json={"repository_ids": [999999991]}    expected_status=any
    Should Be True    ${r.status_code} >= 400
    Response Must Not Contain Token    ${r.text}
