*** Settings ***
Documentation     ROBOT-05 — BDD-022 / fail-fast observável (green path sem skip).
Resource          resources/common.resource
Resource          resources/auth.resource
Library           RequestsLibrary
Suite Setup       Run Keywords    Require E2e Credential Present    AND    Create UI Session
Force Tags        negative    mvp

*** Test Cases ***
BDD-022 Empty Index Payload Rejected
    [Tags]    bdd022
    ${r}=    POST On Session    ui    /api/repos/index
    ...    json={"repository_ids": []}    expected_status=any
    Should Be True    ${r.status_code} >= 400
    Response Must Not Contain Token    ${r.text}

BDD-022 Unknown Repository Id Rejected Without Partial Index
    [Tags]    bdd022    bdd008
    ${before}=    Get Json    ui    /api/repos
    ${r}=    POST On Session    ui    /api/repos/index
    ...    json={"repository_ids": [999999991]}    expected_status=any
    Should Be True    ${r.status_code} >= 400
    ${after}=    Get Json    ui    /api/repos
    ${before_n}=    Get Length    ${before}[repos]
    ${after_n}=    Get Length    ${after}[repos]
    Should Be Equal As Integers    ${before_n}    ${after_n}
    Response Must Not Contain Token    ${r.text}

BDD-018 Catalog Listing Remains Well Formed
    [Tags]    bdd018
    ${body}=    Get Json    ui    /api/repos
    Dictionary Should Contain Key    ${body}    repos
    ${as_text}=    Evaluate    str($body)
    Response Must Not Contain Token    ${as_text}
