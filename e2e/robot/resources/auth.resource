*** Settings ***
Documentation     Credential checks — never Log token values (BDD-027).
Library           OperatingSystem
Resource          common.resource

*** Keywords ***
Require E2e Credential Present
    [Documentation]    Fail fast if neither E2E_GITHUB_TOKEN nor GITHUB_TOKEN is set.
    ${e2e}=    Get Environment Variable    E2E_GITHUB_TOKEN    default=
    ${gh}=    Get Environment Variable    GITHUB_TOKEN    default=
    ${e2e_stripped}=    Strip String    ${e2e}
    ${gh_stripped}=    Strip String    ${gh}
    ${ok}=    Evaluate    bool("""${e2e_stripped}""".strip()) or bool("""${gh_stripped}""".strip())
    Should Be True    ${ok}    msg=Missing e2e credential (set E2E_GITHUB_TOKEN or GITHUB_TOKEN; never commit .env)
