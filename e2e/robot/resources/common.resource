*** Settings ***
Documentation     Shared URLs, waits and retries (T21 / design §3.7).
Library           Collections
Library           OperatingSystem
Library           RequestsLibrary
Library           String

*** Variables ***
${UI_BASE}                      http://127.0.0.1:8080
${MCP_BASE}                     http://127.0.0.1:8001
${HEALTHZ_URL}                  ${UI_BASE}/healthz
${INDEXING_TIMEOUT_SECONDS}     900
${INDEXING_POLL_SECONDS}        5
${SEARCH_TIMEOUT_SECONDS}       60
${HTTP_429_MAX_RETRIES}         3
${RATE_LIMIT_WAIT_SECONDS}      30
${REFERENCE_REPO}               camilocoelhogomes/source-code

*** Keywords ***
Create UI Session
    Create Session    ui    ${UI_BASE}    disable_warnings=True

Get Healthz
    [Documentation]    GET /healthz — never log Authorization or tokens.
    ${resp}=    GET On Session    ui    /healthz    expected_status=200
    RETURN    ${resp.json()}

Wait Until Healthz Ok
    [Arguments]    ${timeout}=60
    Create UI Session
    Wait Until Keyword Succeeds    ${timeout}s    2s    Get Healthz

Get Json
    [Arguments]    ${session}    ${path}    ${expected}=200
    FOR    ${attempt}    IN RANGE    ${HTTP_429_MAX_RETRIES}
        ${resp}=    GET On Session    ${session}    ${path}    expected_status=any
        IF    ${resp.status_code} == 429
            Sleep    ${RATE_LIMIT_WAIT_SECONDS}s
            CONTINUE
        END
        Should Be Equal As Integers    ${resp.status_code}    ${expected}
        RETURN    ${resp.json()}
    END
    Fail    GET ${path} exhausted retries (rate limit)

Post Json
    [Arguments]    ${session}    ${path}    ${body}    ${expected}=200
    FOR    ${attempt}    IN RANGE    ${HTTP_429_MAX_RETRIES}
        ${resp}=    POST On Session    ${session}    ${path}    json=${body}    expected_status=any
        IF    ${resp.status_code} == 429
            Sleep    ${RATE_LIMIT_WAIT_SECONDS}s
            CONTINUE
        END
        Should Be Equal As Integers    ${resp.status_code}    ${expected}
        RETURN    ${resp.json()}
    END
    Fail    POST ${path} exhausted retries (rate limit)

Response Must Not Contain Token
    [Documentation]    BDD-014 — body must not include env token values.
    [Arguments]    ${text}
    ${e2e}=    Get Environment Variable    E2E_GITHUB_TOKEN    default=
    ${gh}=    Get Environment Variable    GITHUB_TOKEN    default=
    Run Keyword If    '${e2e}' != ''    Should Not Contain    ${text}    ${e2e}
    Run Keyword If    '${gh}' != ''    Should Not Contain    ${text}    ${gh}
