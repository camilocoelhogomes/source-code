*** Settings ***
Documentation     Keywords T24 — cron tick, MCP commits, fixture host, elegibilidade.
Resource          common.resource
Library           Collections
Library           RequestsLibrary
Library           ${CURDIR}/../libraries/McpKeywords.py
Library           ${CURDIR}/../libraries/CatalogIndexingKeywords.py

*** Variables ***
${SCHEDULER_TICK_TIMEOUT_SECONDS}    120
${SCHEDULER_TICK_POLL_SECONDS}       ${INDEXING_POLL_SECONDS}
${MARKER_INCLUDE_JAVA}               T24_INCLUDE_JAVA_A1B2
${MARKER_INCLUDE_PY}                 T24_INCLUDE_PY_C3D4
${MARKER_INCLUDE_MD}                 T24_INCLUDE_MD_E5F6
${MARKER_EXCLUDE_CSV}                T24_EXCLUDE_CSV_G7H8
${MARKER_EXCLUDE_GITIGNORE}          T24_EXCLUDE_GITIGNORE_I9J0
${MARKER_MAIN_ONLY}                  MAIN_ONLY_MARKER
${MARKER_OTHER_BRANCH}               OTHER_BRANCH_MARKER
${MARKER_UNCOMMITTED}                UNCOMMITTED_MARKER

*** Keywords ***
Capture Scheduler Cron
    ${current}=    Get Json    ui    /api/scheduler/cron
    Should Not Be Empty    ${current}[cron]
    ${as_text}=    Evaluate    str($current)
    Response Must Not Contain Token    ${as_text}
    RETURN    ${current}

Put Cron Firing Soon Utc
    ${expr}=    Cron Expression Firing Soon Utc
    ${put}=    Create Dictionary    cron=${expr}
    ${r}=    PUT On Session    ui    /api/scheduler/cron    json=${put}    expected_status=200
    Should Be Equal    ${r.json()}[cron]    ${expr}
    ${as_text}=    Evaluate    str($r.json())
    Response Must Not Contain Token    ${as_text}
    RETURN    ${expr}

Restore Scheduler Cron
    [Arguments]    ${cron_original}
    ${payload}=    Set Variable    ${cron_original}
    ${is_str}=    Evaluate    isinstance($cron_original, str)
    IF    ${is_str}
        ${payload}=    Create Dictionary    cron=${cron_original}
    END
    ${r}=    PUT On Session    ui    /api/scheduler/cron    json=${payload}    expected_status=200
    ${as_text}=    Evaluate    str($r.json())
    Response Must Not Contain Token    ${as_text}

Wait Repo Indexed By Scheduler Tick
    [Documentation]    Poll até up_to_date sem POST /api/repos/index (BDD-003).
    [Arguments]    ${repo_id}    ${timeout}=${SCHEDULER_TICK_TIMEOUT_SECONDS}
    Wait Until Keyword Succeeds    ${timeout}s    ${SCHEDULER_TICK_POLL_SECONDS}s
    ...    Repo State Up To Date Labeled    ${repo_id}

Repo State Up To Date Labeled
    [Arguments]    ${repo_id}
    ${detail}=    Get Json    ui    /api/repos/${repo_id}
    Should Be Equal    ${detail}[state]    up_to_date
    Should Be Equal    ${detail}[state_label]    atualizado
    ${as_text}=    Evaluate    str($detail)
    Response Must Not Contain Token    ${as_text}
    RETURN    ${detail}

Mcp Repo Commits
    [Arguments]    ${repo_id}=${None}    ${repo_identifier}=${None}
    ${raw}=    Mcp Call Tool    list_repos    {}    ${MCP_BASE}
    Response Must Not Contain Token    ${raw}
    IF    $repo_id != ${None}
        ${commits}=    Parse Mcp List Repos Commits    ${raw}    repo_id=${repo_id}
    ELSE IF    $repo_identifier != ${None}
        ${commits}=    Parse Mcp List Repos Commits    ${raw}    repo_identifier=${repo_identifier}
    ELSE
        Fail    Mcp Repo Commits requer repo_id ou repo_identifier
    END
    RETURN    ${commits}

Mcp Capture Last Processed Commit
    [Arguments]    ${repo_id}=${None}    ${repo_identifier}=${None}
    ${commits}=    Mcp Repo Commits    repo_id=${repo_id}    repo_identifier=${repo_identifier}
    Should Not Be Empty    ${commits}[last_processed_commit]
    RETURN    ${commits}[last_processed_commit]

Mcp Assert Last Processed Equals
    [Arguments]    ${expected_sha}    ${repo_id}=${None}    ${repo_identifier}=${None}
    ${commits}=    Mcp Repo Commits    repo_id=${repo_id}    repo_identifier=${repo_identifier}
    Should Be Equal    ${commits}[last_processed_commit]    ${expected_sha}
    Should Be Equal    ${commits}[current_main_commit]    ${expected_sha}

Host Commit On Main
    [Arguments]    ${fixture_dir}=${None}    ${relative_path}=t24_bump.txt    ${content}=${None}    ${message}=${None}
    IF    $fixture_dir == ${None}
        ${fixture_dir}=    Resolve Sample Local Dir
    END
    ${sha}=    CatalogIndexingKeywords.Host Commit On Main
    ...    ${fixture_dir}
    ...    relative_path=${relative_path}
    ...    content=${content}
    ...    message=${message}
    RETURN    ${sha}

Index Repo And Wait Up To Date
    [Arguments]    ${repo_id}    ${timeout}=${INDEXING_TIMEOUT_SECONDS}
    ${ids}=    Create List    ${repo_id}
    ${body}=    Create Dictionary    repository_ids=${ids}
    Post Json    ui    /api/repos/index    ${body}    expected=202
    Wait Until Keyword Succeeds    ${timeout}s    ${INDEXING_POLL_SECONDS}s
    ...    Repo State Up To Date Labeled    ${repo_id}

Prepare Eligibility Fixture Tree
    ${fixture_dir}=    Resolve Sample Local Dir
    ${markers}=    Prepare Eligibility Tree    ${fixture_dir}
    RETURN    ${markers}

Prepare MainOnly Fixture Branches
    ${fixture_dir}=    Resolve Sample Local Dir
    ${markers}=    Prepare Main Only Branches    ${fixture_dir}
    RETURN    ${markers}

Assert Exact Search Hits
    [Arguments]    ${pattern}    ${repository_id}    ${expected_path}=${None}
    ${body}=    Create Dictionary    pattern=${pattern}    repository_id=${repository_id}
    ${hits}=    Post Json    ui    /api/search/exact    ${body}
    ${as_text}=    Evaluate    str($hits)
    Response Must Not Contain Token    ${as_text}
    Should Not Be Empty    ${hits}[hits]
    IF    $expected_path != ${None}
        ${paths}=    Evaluate    [h.get('path','') for h in $hits['hits']]
        List Should Contain Value    ${paths}    ${expected_path}
    END
    RETURN    ${hits}

Assert Exact Search Empty
    [Arguments]    ${pattern}    ${repository_id}
    ${body}=    Create Dictionary    pattern=${pattern}    repository_id=${repository_id}
    ${hits}=    Post Json    ui    /api/search/exact    ${body}
    ${as_text}=    Evaluate    str($hits)
    Response Must Not Contain Token    ${as_text}
    ${count}=    Get Length    ${hits}[hits]
    Should Be Equal As Integers    ${count}    0
    RETURN    ${hits}

Assert Repo Files Paths Eligible
    [Arguments]    ${repo_id}    ${includes}    ${excludes}
    ${detail}=    Get Json    ui    /api/repos/${repo_id}
    ${as_text}=    Evaluate    str($detail)
    Response Must Not Contain Token    ${as_text}
    ${paths}=    Evaluate    [f.get('path','') for f in ($detail.get('files') or [])]
    FOR    ${inc}    IN    @{includes}
        List Should Contain Value    ${paths}    ${inc}
    END
    FOR    ${exc}    IN    @{excludes}
        List Should Not Contain Value    ${paths}    ${exc}
    END

Assert Main Marker Indexed
    [Arguments]    ${repository_id}    ${tip_sha}
    ${hits}=    Assert Exact Search Hits    ${MARKER_MAIN_ONLY}    ${repository_id}
    ${commits}=    Evaluate    [h.get('commit','') for h in $hits['hits']]
    List Should Contain Value    ${commits}    ${tip_sha}

Assert Marker Absent From Exact Search
    [Arguments]    ${pattern}    ${repository_id}
    Assert Exact Search Empty    ${pattern}    ${repository_id}

Find Local Repo Id
    ${body}=    Get Json    ui    /api/repos
    ${as_text}=    Evaluate    str($body)
    Response Must Not Contain Token    ${as_text}
    FOR    ${repo}    IN    @{body}[repos]
        IF    '${repo}[origin]' == 'local'
            RETURN    ${repo}[id]
        END
    END
    Fail    Expected at least one local origin repo
