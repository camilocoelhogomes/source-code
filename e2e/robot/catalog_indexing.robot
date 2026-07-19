*** Settings ***
Documentation     ROBOT-02 — catalog / indexing BDD-001–008, 016–019, 021.
Resource          resources/common.resource
Resource          resources/auth.resource
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
    [Tags]    bdd002    bdd005    bdd007
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

BDD-003 Scheduler Cron Get And Put
    [Tags]    bdd003
    ${current}=    Get Json    ui    /api/scheduler/cron
    Should Not Be Empty    ${current}[cron]
    ${put}=    Create Dictionary    cron=0 3 * * *
    ${r}=    PUT On Session    ui    /api/scheduler/cron    json=${put}    expected_status=200
    Should Be Equal    ${r.json()}[cron]    0 3 * * *
    PUT On Session    ui    /api/scheduler/cron    json=${current}    expected_status=200

BDD-004 Reindex When Already Updated Stays Updated
    [Tags]    bdd004
    ${repo}=    Find Repo By Identifier    ${REFERENCE_REPO}
    ${rid}=    Set Variable    ${repo}[id]
    Wait Repo State    ${rid}    up_to_date    timeout=60
    ${ids}=    Create List    ${rid}
    ${body}=    Create Dictionary    repository_ids=${ids}
    Post Json    ui    /api/repos/index    ${body}    expected=202
    Wait Repo State    ${rid}    up_to_date    timeout=300

BDD-006 Exact Search Finds Python Or Markdown
    [Tags]    bdd006    bdd009
    ${repo}=    Find Repo By Identifier    ${REFERENCE_REPO}
    ${body}=    Create Dictionary    pattern=def    repository_id=${repo}[id]
    ${hits}=    Post Json    ui    /api/search/exact    ${body}
    Should Not Be Empty    ${hits}[hits]
    ${as_text}=    Evaluate    str($hits)
    Response Must Not Contain Token    ${as_text}

BDD-017 Local Repo Can Be Indexed
    [Tags]    bdd017
    ${body}=    List Repos Payload
    ${local_id}=    Set Variable    ${None}
    FOR    ${repo}    IN    @{body}[repos]
        IF    '${repo}[origin]' == 'local'
            ${local_id}=    Set Variable    ${repo}[id]
            BREAK
        END
    END
    Should Not Be Equal    ${local_id}    ${None}
    ${ids}=    Create List    ${local_id}
    ${payload}=    Create Dictionary    repository_ids=${ids}
    Post Json    ui    /api/repos/index    ${payload}    expected=202
    Wait Repo State    ${local_id}    up_to_date    timeout=300

BDD-008 Invalid Index Request Is Explicit Error
    [Tags]    bdd008
    ${r}=    POST On Session    ui    /api/repos/index
    ...    json={"repository_ids": [999999991]}    expected_status=any
    Should Be True    ${r.status_code} >= 400
    Response Must Not Contain Token    ${r.text}
