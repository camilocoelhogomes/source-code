*** Settings ***
Documentation     ROBOT-01 — health / BDD-020 (UI + MCP ready).
Resource          resources/common.resource
Resource          resources/auth.resource
Suite Setup       Require E2e Credential Present
Force Tags        health    mvp

*** Test Cases ***
BDD-020 Healthz Reports Ui And Mcp Ready
    [Tags]    bdd020
    Wait Until Healthz Ok    timeout=120
    ${body}=    Get Healthz
    Should Be Equal    ${body}[status]    ok
    Should Be Equal    ${body}[ui]    ready
    Should Be Equal    ${body}[mcp]    ready
    ${as_text}=    Evaluate    str(${body})
    Response Must Not Contain Token    ${as_text}
