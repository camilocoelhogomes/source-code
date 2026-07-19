*** Settings ***
Documentation     ROBOT-03 — UI search / BDD-009–010, 023 (+ smoke 014).
Resource          resources/common.resource
Resource          resources/auth.resource
Library           RequestsLibrary
Suite Setup       Run Keywords    Require E2e Credential Present    AND    Create UI Session
Force Tags        ui    mvp

*** Test Cases ***
BDD-009 Exact Search Via Ui
    [Tags]    bdd009
    ${body}=    Create Dictionary    pattern=github_rag
    ${hits}=    Post Json    ui    /api/search/exact    ${body}
    Dictionary Should Contain Key    ${hits}    hits
    ${as_text}=    Evaluate    str($hits)
    Response Must Not Contain Token    ${as_text}

BDD-010 Semantic Search Via Ui
    [Tags]    bdd010
    ${body}=    Create Dictionary    query=container delivery compose    limit=${5}
    ${hits}=    Post Json    ui    /api/search/semantic    ${body}
    Dictionary Should Contain Key    ${hits}    hits
    ${as_text}=    Evaluate    str($hits)
    Response Must Not Contain Token    ${as_text}

BDD-023 Connections Crud Not Available
    [Tags]    bdd023
    ${r}=    POST On Session    ui    /api/connections
    ...    json={"name":"x"}    expected_status=any
    Should Be Equal As Integers    ${r.status_code}    404
    ${r2}=    PUT On Session    ui    /api/connections/1
    ...    json={"name":"x"}    expected_status=any
    Should Be Equal As Integers    ${r2.status_code}    404
    Response Must Not Contain Token    ${r.text}
