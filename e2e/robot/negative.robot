*** Settings ***
Documentation     ROBOT-05 — BDD-008/018/022 negativos integrais (T25) + regressão payload.
Resource          resources/common.resource
Resource          resources/auth.resource
Library           OperatingSystem
Library           Process
Library           RequestsLibrary
Suite Setup       Run Keywords    Require E2e Credential Present    AND    Create UI Session
Force Tags        negative    mvp

*** Keywords ***
Run Negative Probe
    [Arguments]    ${probe}
    ${repo}=    Normalize Path    ${CURDIR}/../..
    ${probe_script}=    Set Variable    ${repo}${/}e2e${/}probes${/}negative_probes.py
    ${python}=    Set Variable    ${repo}${/}.venv${/}bin${/}python
    ${result}=    Run Process    ${python}    ${probe_script}    ${probe}
    ...    cwd=${repo}
    ...    env:PYTHONPATH=${repo}${/}src:${repo}
    ...    stdout=PIPE    stderr=PIPE
    ${combined}=    Catenate    SEPARATOR=\n    ${result.stdout}    ${result.stderr}
    Response Must Not Contain Token    ${combined}
    RETURN    ${result}

*** Test Cases ***
BDD-008 Partial Failure History And Full Reindex Probe
    [Tags]    bdd008
    ${result}=    Run Negative Probe    bdd008
    Should Be Equal As Integers    ${result.rc}    0    msg=${result.stdout}\n${result.stderr}

BDD-018 Missing Volume Registers Issue On Catalog Api
    [Tags]    bdd018
    ${body}=    Get Json    ui    /api/catalog/issues
    Dictionary Should Contain Key    ${body}    issues
    ${as_text}=    Evaluate    str($body)
    Response Must Not Contain Token    ${as_text}
    ${found}=    Set Variable    ${False}
    FOR    ${issue}    IN    @{body}[issues]
        ${msg}=    Convert To Lower Case    ${issue}[message]
        IF    'inaccessible' in $msg or 'missing' in $msg or 'ausente' in $msg
            ${found}=    Set Variable    ${True}
        END
    END
    Should Be True    ${found}    msg=Expected local volume issue in /api/catalog/issues
    ${repos}=    Get Json    ui    /api/repos
    FOR    ${repo}    IN    @{repos}[repos]
        Should Not Contain    ${repo}[repo_identifier]    __missing_e2e_volume__
    END

BDD-022 Config Path Invalid Fail Fast Without Leak Probe
    [Tags]    bdd022
    ${result}=    Run Negative Probe    bdd022
    Should Be Equal As Integers    ${result.rc}    0    msg=${result.stdout}\n${result.stderr}

BDD-022 Empty Index Payload Rejected
    [Tags]    bdd022    regression
    ${r}=    POST On Session    ui    /api/repos/index
    ...    json={"repository_ids": []}    expected_status=any
    Should Be True    ${r.status_code} >= 400
    Response Must Not Contain Token    ${r.text}

BDD-022 Unknown Repository Id Rejected Without Partial Index
    [Tags]    bdd022    bdd008    regression
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
    [Tags]    bdd018    regression
    ${body}=    Get Json    ui    /api/repos
    Dictionary Should Contain Key    ${body}    repos
    ${as_text}=    Evaluate    str($body)
    Response Must Not Contain Token    ${as_text}
