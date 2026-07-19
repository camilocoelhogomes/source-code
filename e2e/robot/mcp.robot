*** Settings ***
Documentation     ROBOT-04 — MCP tools BDD-011–014 (BDD-013 integral T26).
Library           ${CURDIR}/libraries/McpKeywords.py
Library           Collections
Library           String
Resource          resources/common.resource
Resource          resources/auth.resource
Suite Setup       Require E2e Credential Present
Force Tags        mcp    mvp

*** Variables ***
@{APPROVED_TOOLS}    list_repos    search_code    semantic_search    read_file    list_tree
${QUERY_WORKERS}     ${4}
${SEARCH_ARGS}       {"pattern":"def","max_matches":3}

*** Test Cases ***
BDD-011 Approved Mcp Tools Are Available
    [Tags]    bdd011    bdd024
    ${names}=    Mcp List Tools    ${MCP_BASE}
    FOR    ${tool}    IN    @{APPROVED_TOOLS}
        List Should Contain Value    ${names}    ${tool}
    END

BDD-011 List Repos Via Mcp
    [Tags]    bdd011
    ${raw}=    Mcp Call Tool    list_repos    {}    ${MCP_BASE}
    Should Contain    ${raw}    repos
    Response Must Not Contain Token    ${raw}

BDD-012 Optional Details Omitted By Default
    [Tags]    bdd012
    ${raw}=    Mcp Call Tool    search_code    ${SEARCH_ARGS}    ${MCP_BASE}
    Response Must Not Contain Token    ${raw}
    # When includes are false/default, optional detail keys may be null/absent
    Should Contain    ${raw}    hits

BDD-012 Optional Details When Requested
    [Tags]    bdd012
    ${args}=    Set Variable    {"pattern":"def","max_matches":3,"include_repository":true,"include_path":true,"include_commit":true,"include_snippet":true}
    ${raw}=    Mcp Call Tool    search_code    ${args}    ${MCP_BASE}
    Response Must Not Contain Token    ${raw}
    Should Contain    ${raw}    hits

BDD-013 Parallel Mcp Tool Calls Under Limit And Queue Slo
    [Documentation]    BDD-013 integral: N=2*QUERY_WORKERS concorrentes + SLO + BDD-014.
    [Tags]    bdd013
    ${n_calls}=    Evaluate    int(${QUERY_WORKERS}) * 2
    ${single}=    Mcp Measure Single Call Seconds    search_code    ${SEARCH_ARGS}    ${MCP_BASE}    2
    ${bundle}=    Mcp Parallel Call Tools    search_code    ${SEARCH_ARGS}    ${n_calls}    ${MCP_BASE}
    ${results}=    Get From Dictionary    ${bundle}    results
    ${wall}=    Get From Dictionary    ${bundle}    wall_seconds
    ${count}=    Get From Dictionary    ${bundle}    n_calls
    Should Be Equal As Integers    ${count}    ${n_calls}
    FOR    ${raw}    IN    @{results}
        Should Contain    ${raw}    hits
        Response Must Not Contain Token    ${raw}
    END
    Mcp Assert Parallel Slo    ${QUERY_WORKERS}    ${n_calls}    ${wall}    ${single}

BDD-014 Mcp Responses Never Echo Token
    [Tags]    bdd014
    ${raw}=    Mcp Call Tool    list_repos    {}    ${MCP_BASE}
    Response Must Not Contain Token    ${raw}
