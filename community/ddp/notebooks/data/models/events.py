import marimo

__generated_with = "0.19.9"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    def get_model_preview(model_name, limit=5):
        return mo.sql(f"SELECT * FROM {model_name} LIMIT {limit}",
                      engine=pyoso_db_conn, output=False)

    def get_row_count(model_name):
        result = mo.sql(f"SHOW STATS FOR {model_name}",
                        engine=pyoso_db_conn, output=False)
        return result['row_count'].sum()

    def generate_sql_snippet(model_name, df_results, limit=5):
        column_names = df_results.columns.tolist()
        # Format columns with one per line, indented
        columns_formatted = ',\n  '.join(column_names)
        sql_snippet = f"""```sql
    SELECT 
      {columns_formatted}
    FROM {model_name}
    LIMIT {limit}
    ```
    """
        return mo.md(sql_snippet)

    def render_table_preview(model_name):
        df = get_model_preview(model_name)
        if df.empty:
            return mo.md(f"**{model_name}**\n\nUnable to retrieve preview (table might be empty or inaccessible).")

        sql_snippet = generate_sql_snippet(model_name, df, limit=5)
        fmt = {c: '{:.0f}' for c in df.columns if df[c].dtype == 'int64' and ('_id' in c or c == 'id')}
        table = mo.ui.table(df, format_mapping=fmt, show_column_summaries=False, show_data_types=False)
        row_count = get_row_count(model_name)
        col_count = len(df.columns)
        title = f"{model_name} | {row_count:,.0f} rows, {col_count} cols"
        return mo.accordion({title: mo.vstack([sql_snippet, table])})

    import pandas as pd

    return pd, render_table_preview


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # GitHub Events Model

    This notebook documents GitHub event data in OSO, explaining where it comes from, how it's
    transformed, and how to use it for developer activity analysis.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Overview

    OSO tracks developer activity from two complementary sources:
    [GitHub Archive](https://www.gharchive.org/) (GHA) and
    [Open Dev Data](https://opendevdata.org/) (ODD). Both are linked through a shared
    `repo_id` (GitHub REST API repository ID), enabling cross-source joins and
    ecosystem-level analysis.

    | Source | Coverage | Strengths |
    |--------|----------|-----------|
    | **GitHub Archive** | All event types | Broad activity coverage (PRs, issues, reviews, stars, forks), real-time public timeline |
    | **Open Dev Data** | Commits only | Identity resolution, code churn metrics (additions/deletions), Git history analysis |

    This notebook defines the **unified event model** — a complete view of developer
    activity that combines data from both sources. GHA alone has known gaps:
    - `PushEvent` payloads are capped at **20 commits** per event
    - Since **2025-10-07**, GHA stopped providing commit payload data entirely

    The unified event model addresses these gaps by enriching GHA events with ODD data
    where available. For commit events specifically, the unified commit model
    (`int_ddp__commits_unified`) provides identity-resolved authorship and code churn
    metrics — see [commits.py](/data/models/commits) for details.

    Downstream metrics (MAD, activity rollups, ecosystem comparisons) depend on accurate
    event data, so the unified models are the correct foundation for all developer
    activity analysis.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Data Freshness & Completeness

    - **Freshness**: GitHub Archive data is up to **3 days behind** real-time. The staging model
      (`stg_github__events`) shifts the query window back by 3 days to avoid querying BigQuery
      tables that don't yet exist
      ([source](../../../../../../oso/warehouse/oso_sqlmesh/models/staging/github/stg_github__events.py#L114-L117)).
    - **Completeness**: GitHub Archive captures the public GitHub timeline only. Private
      repositories and deleted events are not included.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Data Lineage
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.mermaid("""
    graph TD
        subgraph sources["Sources"]
            GHA["stg_github__events<br/><i>raw, nested</i>"]
            ODD["stg_opendevdata__commits<br/><i>identity-resolved</i>"]
        end

        subgraph staging["GHA Staging"]
            REL["stg_github__releases"]
            COM["stg_github__comments"]
            ISS["stg_github__issues"]
            PR["stg_github__pull_requests"]
            SF["stg_github__stars_and_forks"]
        end

        BRIDGE["int_opendevdata__repositories_with_repo_id<br/><i>maps ODD repo IDs → GitHub repo_id</i>"]
        DEDUP["int_ddp__commits_deduped<br/><i>GHA + ODD merged, 1 row per sha + repo_id</i>"]

        subgraph unified["Unified Pipeline"]
            EVENTS["int_events__github_unified<br/><i>COMMIT_CODE + all other event types</i>"]
            DAILY["int_events_daily__github_unified"]
        end

        METRICS["oso_metrics/code/*<br/><i>18 metric definitions</i>"]

        GHA --> staging
        ODD --> BRIDGE
        BRIDGE --> DEDUP
        GHA --> DEDUP
        DEDUP --> EVENTS
        REL --> EVENTS
        COM --> EVENTS
        ISS --> EVENTS
        PR --> EVENTS
        SF --> EVENTS
        EVENTS --> DAILY
        DAILY --> METRICS

        style EVENTS fill:#4C78A8,color:#fff
        style DAILY fill:#4C78A8,color:#fff
        style DEDUP fill:#F58518,color:#fff
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Existing Models

    **DDP Pipeline:**
    - **`oso.stg_github__events`**: Raw GitHub Archive events with nested `repo` and `actor` fields,
      plus JSON `payload`.
    - **`oso.int_gharchive__github_events`**: Standardized projection with flat columns. Contains
      all event types but at PushEvent grain (not commit grain).
    - **`oso.int_ddp_github_events`**: Filtered to `PushEvent` and `WatchEvent`.
    - **`oso.int_ddp_github_events_daily`**: Daily aggregation with normalized event type buckets.
    - **`oso.int_gharchive__developer_activities`**: MAD rollup (PushEvent + PullRequestEvent).

    **Cross-source models:**
    - **`oso.int_opendevdata__repositories_with_repo_id`**: Bridge model mapping ODD repository IDs
      to GitHub `repo_id`, enabling cross-source joins.

    **Unified commit models:**
    - **`oso.int_ddp__commits_unified`**: GHA commits enriched with ODD metadata where available,
      plus ODD-only commits not in GHA. Provides `author_id`, `canonical_developer_id`, additions,
      and deletions.
    - **`oso.int_ddp__commits_deduped`**: Deduplicated — one row per `(sha, repository_id)`.

    ### `int_events__github_unified`

    UNION ALL of unified commits with all other GHA event types:

    | Event Source | Model | Grain |
    |-------------|-------|-------|
    | **Commits** | `int_ddp__commits_deduped` | One row per commit (GHA + ODD merged, deduped) |
    | **Releases** | `stg_github__releases` | One row per release |
    | **Comments** | `stg_github__comments` | One row per comment |
    | **Issues** | `stg_github__issues` | One row per issue event |
    | **Pull Requests** | `stg_github__pull_requests` | One row per PR event |
    | **Stars & Forks** | `stg_github__stars_and_forks` | One row per star/fork |

    The commit source (`int_ddp__commits_deduped`) provides columns compatible with the
    other staging models: `created_at`, `repository_id`, `repository_name`, `actor_login`,
    `actor_id`, `author_email`. Uses `sha` as `event_source_id`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Canonical Entry Point: `int_events__github_unified`

    **Model**: `oso.int_events__github_unified`

    This is the unified events model combining GHA events with ODD-enriched commits.
    It UNION ALLs commits from `int_ddp__commits_deduped` with other event types
    (releases, comments, issues, PRs, stars, forks) into a single table. Commits are
    at commit grain (one row per commit, not per PushEvent).

    ### Key Fields
    - **`time`**: Timestamp when the event occurred
    - **`event_type`**: Uppercased event type (e.g., `COMMIT_CODE`, `PULL_REQUEST_OPENED`, `STARRED`)
    - **`event_source`**: Always `GITHUB`
    - **`event_source_id`**: Source identifier (e.g., `sha` for commits, `id` for other events)
    - **`to_artifact_id`**: Target artifact (repository) hashed ID
    - **`to_artifact_name`**: Repository name
    - **`to_artifact_namespace`**: Repository owner
    - **`from_artifact_id`**: Source artifact (developer) hashed ID
    - **`from_artifact_name`**: Developer login
    - **`amount`**: Event count (always 1.0)
    """)
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview("oso.int_events__github_unified")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Event Types

    The unified model includes all major GitHub event types, standardized and uppercased:

    | Event Type | Source | Description |
    |------------|--------|-------------|
    | `COMMIT_CODE` | `int_ddp__commits_deduped` | Individual commits (GHA + ODD merged, deduped by SHA) |
    | `PULL_REQUEST_OPENED` | `stg_github__pull_requests` | Pull request opened |
    | `PULL_REQUEST_MERGED` | `stg_github__pull_requests` | Pull request merged |
    | `PULL_REQUEST_CLOSED` | `stg_github__pull_requests` | Pull request closed |
    | `PULL_REQUEST_REOPENED` | `stg_github__pull_requests` | Pull request reopened |
    | `ISSUE_OPENED` | `stg_github__issues` | Issue opened |
    | `ISSUE_CLOSED` | `stg_github__issues` | Issue closed |
    | `ISSUE_REOPENED` | `stg_github__issues` | Issue reopened |
    | `STARRED` | `stg_github__stars_and_forks` | Repository starred |
    | `FORKED` | `stg_github__stars_and_forks` | Repository forked |
    | `RELEASE_PUBLISHED` | `stg_github__releases` | Release published |

    `COMMIT_CODE` events are at **commit grain** (one row per commit, not per PushEvent).
    For commit-level analysis with additional fields like `additions`, `deletions`,
    and `canonical_developer_id`, see [commits.py](/data/models/commits).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Daily Aggregation: `int_events_daily__github_unified`

    **Model**: `oso.int_events_daily__github_unified`

    This model aggregates events from `int_events__github_unified` by day, grouping by
    `from_artifact_id`, `to_artifact_id`, `event_source`, and `event_type`. The `amount`
    column is summed to give daily totals.

    ### Key Fields
    - **`bucket_day`**: `DATE_TRUNC('DAY', time)`
    - **`event_type`**: Same event types as the base model
    - **`from_artifact_id`**: Developer (hashed ID)
    - **`to_artifact_id`**: Repository (hashed ID)
    - **`event_source`**: Always `GITHUB`
    - **`amount`**: Sum of events for that day/developer/repo/type combination

    This is the primary model for time-series analysis and metric computation. All 18 metric
    definitions in `oso_metrics/code/` source from this daily aggregation.
    """)
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview("oso.int_events_daily__github_unified")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Deriving Developer Metrics

    The daily aggregation model `int_events_daily__github_unified` is the building block for
    developer metrics like Monthly Active Developers (MAD). Filter by `event_type` to define
    what counts as "developer activity."

    ### Common Activity Definitions

    | Definition | Event Types Included |
    |------------|---------------------|
    | Code contributors | `COMMIT_CODE` |
    | Code + review contributors | `COMMIT_CODE`, `PULL_REQUEST_OPENED`, `PULL_REQUEST_MERGED` |
    | All active developers | All event types |

    ### Key Fields for Activity Queries
    - **`bucket_day`**: Date of activity
    - **`from_artifact_id`**: Developer (hashed ID)
    - **`to_artifact_id`**: Repository (hashed ID)
    - **`event_type`**: Filter to define your activity scope
    - **`amount`**: Count of events
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    See the **Sample Queries** section below for ready-to-use SQL for daily active developers,
    custom activity rollups, and ecosystem-level filtering.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Cross-Source Enrichment

    The unified model already merges GHA and ODD data at the commit level through
    `int_ddp__commits_deduped`. For `COMMIT_CODE` events, the underlying commits include:

    - **Identity resolution**: `canonical_developer_id` linking across Git emails and GitHub logins
    - **Code churn**: `additions` and `deletions` per commit
    - **Bot detection**: `is_bot` flag
    - **Source tracking**: `source` field indicating GHA, ODD, or both

    These enriched fields are available in [commits.py](/data/models/commits). The event model
    itself carries the standardized schema (`time`, `event_type`, `from_artifact_*`, `to_artifact_*`,
    `amount`) for consistent querying across all event types.

    To filter events by ecosystem, join through the repository and ecosystem mapping tables.
    See [repositories.py](/data/models/repositories) and [ecosystems.py](/data/models/ecosystems)
    for the bridge models.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## How Events Are Unified

    The key difference between `int_events__github_unified` and a GHA-only events model is
    the **commit source**. Commits come from `int_ddp__commits_deduped` which merges GitHub
    Archive and Open Dev Data, deduped on `(sha, repository_id)`. All other event types
    (releases, comments, issues, PRs, stars, forks) source from their standard GHA staging models.

    ### What the Unified Commits Solve

    | Problem | GHA-only | Unified |
    |---------|----------|---------|
    | 20-commit cap per PushEvent | Under-counts commits in large pushes | ODD fills in the missing commits |
    | No commit payloads post Oct 2025 | Only `head` SHA, no commit array | ODD provides full commit history |
    | Actor ≠ Author | `actor_id` is the pusher, not the code author | ODD resolves the actual commit author |
    | No code churn data | No additions/deletions | ODD provides per-commit additions and deletions |

    ### Architecture

    The model UNION ALLs commits from `int_ddp__commits_deduped` with other event types
    into a single table. Each source CTE maps its columns into the standard schema:

    - **`time`** ← `created_at` (commits), `created_at` (other events)
    - **`event_source_id`** ← `sha` (commits), `id` (other events)
    - **`from_artifact_name`** ← `actor_login` (the developer)
    - **`to_artifact_name`** ← repository name
    - **`amount`** ← always `1.0`

    Because `int_ddp__commits_deduped` covers the full date range (no gap post Oct 2025),
    the unified model does not need a pre/post date split.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Live Data Exploration

    The following charts show actual data from the event tables, filtered to a recent date range
    to demonstrate the data structure and typical patterns.
    """)
    return


@app.cell(hide_code=True)
def _():
    import plotly.express as px

    return (px,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Event Type Distribution (Last 14 Days)
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    # Query event type distribution from unified events (limited date range)
    _event_type_query = """
    SELECT
      event_type,
      COUNT(*) AS event_count
    FROM oso.int_events__github_unified
    WHERE time >= CURRENT_DATE - INTERVAL '14' DAY
    GROUP BY event_type
    ORDER BY event_count DESC
    """

    with mo.persistent_cache("event_types"):
        df_event_types = mo.sql(_event_type_query, engine=pyoso_db_conn, output=False)
    return (df_event_types,)


@app.cell(hide_code=True)
def _(df_event_types, mo, px):
    _fig = px.bar(
        df_event_types,
        x='event_type',
        y='event_count',
        text='event_count',
        labels={'event_type': 'Event Type', 'event_count': 'Event Count'},
        color_discrete_sequence=['#4C78A8']
    )

    _fig.update_traces(
        texttemplate='%{text:,.0f}',
        textposition='outside'
    )

    _fig.update_layout(
        template='plotly_white',
        margin=dict(t=20, l=0, r=0, b=0),
        height=400,
        xaxis=dict(
            title='',
            tickangle=-45,
            showgrid=False,
            linecolor="#000",
            linewidth=1
        ),
        yaxis=dict(
            title='Event Count',
            showgrid=True,
            gridcolor="#E5E5E5",
            linecolor="#000",
            linewidth=1
        )
    )

    _total_events = df_event_types['event_count'].sum()
    _top_event = df_event_types.iloc[0]['event_type'] if len(df_event_types) > 0 else "N/A"
    _top_count = df_event_types.iloc[0]['event_count'] if len(df_event_types) > 0 else 0
    _num_types = len(df_event_types)

    mo.vstack([
        mo.hstack([
            mo.stat(label="Total Events", value=f"{_total_events:,.0f}", bordered=True, caption="Last 14 days"),
            mo.stat(label="Top Event Type", value=_top_event, bordered=True, caption=f"{_top_count:,.0f} events"),
            mo.stat(label="Event Types", value=f"{_num_types}", bordered=True, caption="Distinct types"),
        ], widths="equal", gap=1),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Daily Active Developers (Last 30 Days)
    """)
    return


@app.cell(hide_code=True)
def _(mo, pd, pyoso_db_conn):
    # Query daily active developers from the daily aggregation (limited date range)
    _daily_devs_query = """
    SELECT
      bucket_day,
      COUNT(DISTINCT from_artifact_id) AS daily_active_developers
    FROM oso.int_events_daily__github_unified
    WHERE
      bucket_day >= CURRENT_DATE - INTERVAL '30' DAY
      AND event_type = 'COMMIT_CODE'
    GROUP BY bucket_day
    ORDER BY bucket_day
    """

    with mo.persistent_cache("daily_developers"):
        df_daily_devs = mo.sql(_daily_devs_query, engine=pyoso_db_conn, output=False)
        df_daily_devs['bucket_day'] = pd.to_datetime(df_daily_devs['bucket_day'])
    return (df_daily_devs,)


@app.cell(hide_code=True)
def _(df_daily_devs, mo, px):
    _fig2 = px.area(
        df_daily_devs,
        x='bucket_day',
        y='daily_active_developers',
        color_discrete_sequence=['#4C78A8']
    )

    _fig2.update_traces(
        line=dict(width=2),
        fillcolor='rgba(76, 120, 168, 0.2)',
        hovertemplate='<b>%{x|%b %d, %Y}</b><br>Active Developers: %{y:,.0f}<extra></extra>'
    )

    _fig2.update_layout(
        template='plotly_white',
        margin=dict(t=20, l=0, r=0, b=0),
        height=400,
        hovermode='x unified',
        xaxis=dict(
            title='',
            showgrid=False,
            linecolor="#000",
            linewidth=1,
            tickformat="%b %d"
        ),
        yaxis=dict(
            title='Daily Active Developers',
            showgrid=True,
            gridcolor="#E5E5E5",
            linecolor="#000",
            linewidth=1
        )
    )

    _avg_devs = int(df_daily_devs['daily_active_developers'].mean())
    _max_devs = int(df_daily_devs['daily_active_developers'].max())
    _min_devs = int(df_daily_devs['daily_active_developers'].min())
    _latest_devs = int(df_daily_devs['daily_active_developers'].iloc[-1]) if len(df_daily_devs) > 0 else 0

    mo.vstack([
        mo.hstack([
            mo.stat(label="Latest Day", value=f"{_latest_devs:,}", bordered=True, caption="Most recent count"),
            mo.stat(label="30-Day Average", value=f"{_avg_devs:,}", bordered=True, caption="Mean daily developers"),
            mo.stat(label="Peak", value=f"{_max_devs:,}", bordered=True, caption="Maximum in period"),
            mo.stat(label="Minimum", value=f"{_min_devs:,}", bordered=True, caption="Lowest in period"),
        ], widths="equal", gap=1),
        mo.ui.plotly(_fig2, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Daily Events by Type (Last 14 Days)
    """)
    return


@app.cell(hide_code=True)
def _(mo, pd, pyoso_db_conn):
    # Query daily events by type from the daily aggregation
    _daily_by_type_query = """
    SELECT
      bucket_day,
      event_type,
      SUM(amount) AS total_events
    FROM oso.int_events_daily__github_unified
    WHERE bucket_day >= CURRENT_DATE - INTERVAL '14' DAY
    GROUP BY bucket_day, event_type
    ORDER BY bucket_day, event_type
    """

    with mo.persistent_cache("daily_events_by_type"):
        df_daily_by_type = mo.sql(_daily_by_type_query, engine=pyoso_db_conn, output=False)
        df_daily_by_type['bucket_day'] = pd.to_datetime(df_daily_by_type['bucket_day'])
    return (df_daily_by_type,)


@app.cell(hide_code=True)
def _(df_daily_by_type, mo, px):
    # Group into top 5 event types + OTHER for a clean stacked area
    _type_totals = df_daily_by_type.groupby('event_type')['total_events'].sum()
    _top5 = _type_totals.nlargest(5).index.tolist()
    _df = df_daily_by_type.copy()
    _df['event_type_grouped'] = _df['event_type'].where(_df['event_type'].isin(_top5), 'OTHER')
    _df_grouped = _df.groupby(['bucket_day', 'event_type_grouped'])['total_events'].sum().reset_index()
    _df_grouped = _df_grouped.rename(columns={'event_type_grouped': 'event_type'})

    _fig3 = px.area(
        _df_grouped,
        x='bucket_day',
        y='total_events',
        color='event_type'
    )

    _fig3.update_traces(
        line=dict(width=1.5),
        hovertemplate='%{fullData.name}<br><b>%{x|%b %d}</b><br>Events: %{y:,.0f}<extra></extra>'
    )

    _fig3.update_layout(
        template='plotly_white',
        margin=dict(t=20, l=0, r=0, b=0),
        height=400,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text=''
        ),
        xaxis=dict(
            title='',
            showgrid=False,
            linecolor="#000",
            linewidth=1,
            tickformat="%b %d"
        ),
        yaxis=dict(
            title='Total Events',
            showgrid=True,
            gridcolor="#E5E5E5",
            linecolor="#000",
            linewidth=1
        )
    )

    # Calculate stats
    _commit_total = int(_type_totals.get('COMMIT_CODE', 0))
    _starred_total = int(_type_totals.get('STARRED', 0))
    _grand_total = int(_type_totals.sum())
    _num_types = len(_type_totals)

    mo.vstack([
        mo.hstack([
            mo.stat(label="Commits", value=f"{_commit_total:,}", bordered=True, caption="COMMIT_CODE"),
            mo.stat(label="Stars", value=f"{_starred_total:,}", bordered=True, caption="STARRED"),
            mo.stat(label="Event Types", value=f"{_num_types}", bordered=True, caption="Distinct types (top 5 + OTHER shown)"),
            mo.stat(label="Total", value=f"{_grand_total:,}", bordered=True, caption="All events (14 days)"),
        ], widths="equal", gap=1),
        mo.ui.plotly(_fig3, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Commit Source Breakdown (Last 14 Days)
    """)
    return


@app.cell(hide_code=True)
def _(mo, pd, pyoso_db_conn):
    # Compare commit volumes by source using the deduped commits model
    # ~20s estimated query time
    _source_comparison_query = """
    SELECT
      source,
      COUNT(DISTINCT repository_id) AS repos_with_data,
      COUNT(*) AS total_commits
    FROM oso.int_ddp__commits_deduped
    WHERE
      created_at >= CURRENT_DATE - INTERVAL '14' DAY
    GROUP BY source
    ORDER BY total_commits DESC
    """

    with mo.persistent_cache("source_comparison"):
        df_source_comparison = mo.sql(_source_comparison_query, engine=pyoso_db_conn, output=False)
        # Ensure numeric types
        df_source_comparison['repos_with_data'] = pd.to_numeric(df_source_comparison['repos_with_data'])
        df_source_comparison['total_commits'] = pd.to_numeric(df_source_comparison['total_commits'])
    return (df_source_comparison,)


@app.cell(hide_code=True)
def _(df_source_comparison, mo, px):
    _fig5 = px.bar(
        df_source_comparison,
        x='source',
        y='total_commits',
        text='total_commits',
        labels={'source': 'Commit Source', 'total_commits': 'Total Commits'},
        color='source',
        color_discrete_map={
            'gharchive': '#4C78A8',
            'opendevdata': '#F58518'
        }
    )

    _fig5.update_traces(
        texttemplate='%{text:,.0f}',
        textposition='outside'
    )

    _fig5.update_layout(
        template='plotly_white',
        margin=dict(t=20, l=0, r=0, b=0),
        height=400,
        showlegend=False,
        xaxis=dict(
            title='',
            showgrid=False,
            linecolor="#000",
            linewidth=1
        ),
        yaxis=dict(
            title='Total Commits',
            showgrid=True,
            gridcolor="#E5E5E5",
            linecolor="#000",
            linewidth=1
        )
    )

    _total_commits = int(df_source_comparison['total_commits'].sum())
    _total_repos = int(df_source_comparison['repos_with_data'].sum())
    _num_sources = len(df_source_comparison)

    mo.vstack([
        mo.hstack([
            mo.stat(label="Total Commits", value=f"{_total_commits:,}", bordered=True, caption="Last 14 days (deduped)"),
            mo.stat(label="Repos", value=f"{_total_repos:,}", bordered=True, caption="With commit data"),
            mo.stat(label="Sources", value=f"{_num_sources}", bordered=True, caption="GHA, ODD, or both"),
        ], widths="equal", gap=1),
        mo.ui.plotly(_fig5, config={'displayModeBar': False}),
    ])
    return



@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Queries

    ### 1. Event Type Distribution (Last 14 Days)

    See what event types are most common across all unified GitHub events.

    ```sql
    SELECT
      event_type,
      COUNT(*) AS event_count
    FROM oso.int_events__github_unified
    WHERE time >= CURRENT_DATE - INTERVAL '14' DAY
    GROUP BY event_type
    ORDER BY event_count DESC
    LIMIT 20
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql("""
    SELECT
      event_type,
      COUNT(*) AS event_count
    FROM oso.int_events__github_unified
    WHERE time >= CURRENT_DATE - INTERVAL '14' DAY
    GROUP BY event_type
    ORDER BY event_count DESC
    LIMIT 20
    """, engine=pyoso_db_conn)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 2. Daily Active Developers (Last 14 Days)

    Count unique developers committing each day using the daily aggregation.

    ```sql
    SELECT
      bucket_day,
      COUNT(DISTINCT from_artifact_id) AS daily_active_developers
    FROM oso.int_events_daily__github_unified
    WHERE
      bucket_day >= CURRENT_DATE - INTERVAL '14' DAY
      AND event_type = 'COMMIT_CODE'
    GROUP BY bucket_day
    ORDER BY bucket_day
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql("""
    SELECT
      bucket_day,
      COUNT(DISTINCT from_artifact_id) AS daily_active_developers
    FROM oso.int_events_daily__github_unified
    WHERE
      bucket_day >= CURRENT_DATE - INTERVAL '14' DAY
      AND event_type = 'COMMIT_CODE'
    GROUP BY bucket_day
    ORDER BY bucket_day
    """, engine=pyoso_db_conn)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 3. Events for a Specific Repository (Last 14 Days)

    Query all event types for a repository by owner and name.

    ```sql
    SELECT
      DATE_TRUNC('DAY', time) AS event_day,
      event_type,
      COUNT(*) AS event_count
    FROM oso.int_events__github_unified
    WHERE
      to_artifact_namespace = 'ethereum'
      AND to_artifact_name = 'go-ethereum'
      AND time >= CURRENT_DATE - INTERVAL '14' DAY
    GROUP BY 1, 2
    ORDER BY event_day, event_type
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql("""
    SELECT
      DATE_TRUNC('DAY', time) AS event_day,
      event_type,
      COUNT(*) AS event_count
    FROM oso.int_events__github_unified
    WHERE
      to_artifact_namespace = 'ethereum'
      AND to_artifact_name = 'go-ethereum'
      AND time >= CURRENT_DATE - INTERVAL '14' DAY
    GROUP BY 1, 2
    ORDER BY event_day, event_type
    """, engine=pyoso_db_conn)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 4. Filter Events by Ecosystem (Last 14 Days)

    Find developer activity for a specific ecosystem by joining through the ecosystem mapping tables.

    ```sql
    SELECT
      eco.name AS ecosystem_name,
      COUNT(DISTINCT ev.from_artifact_name) AS unique_developers,
      SUM(ev.amount) AS total_events
    FROM oso.int_events__github_unified ev
    JOIN oso.int_opendevdata__repositories_with_repo_id r
      ON ev.to_artifact_namespace || '/' || ev.to_artifact_name = r.repo_name
    JOIN oso.stg_opendevdata__ecosystems_repos_recursive err
      ON r.opendevdata_id = err.repo_id
    JOIN oso.stg_opendevdata__ecosystems eco
      ON err.ecosystem_id = eco.id
    WHERE
      ev.time >= CURRENT_DATE - INTERVAL '14' DAY
      AND eco.name = 'Ethereum'
    GROUP BY eco.name
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql("""
    SELECT
      eco.name AS ecosystem_name,
      COUNT(DISTINCT ev.from_artifact_name) AS unique_developers,
      SUM(ev.amount) AS total_events
    FROM oso.int_events__github_unified ev
    JOIN oso.int_opendevdata__repositories_with_repo_id r
      ON ev.to_artifact_namespace || '/' || ev.to_artifact_name = r.repo_name
    JOIN oso.stg_opendevdata__ecosystems_repos_recursive err
      ON r.opendevdata_id = err.repo_id
    JOIN oso.stg_opendevdata__ecosystems eco
      ON err.ecosystem_id = eco.id
    WHERE
      ev.time >= CURRENT_DATE - INTERVAL '14' DAY
      AND eco.name = 'Ethereum'
    GROUP BY eco.name
    """, engine=pyoso_db_conn)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 5. Custom Activity Rollup (Last 14 Days)

    Build your own activity definition by combining multiple event types.

    ```sql
    SELECT
      DATE_TRUNC('DAY', time) AS bucket_day,
      from_artifact_name AS developer_login,
      to_artifact_namespace || '/' || to_artifact_name AS repo_name,
      SUM(amount) AS num_events
    FROM oso.int_events__github_unified
    WHERE
      time >= CURRENT_DATE - INTERVAL '14' DAY
      AND event_type IN (
        'COMMIT_CODE',
        'PULL_REQUEST_OPENED',
        'PULL_REQUEST_MERGED',
        'ISSUE_OPENED'
      )
    GROUP BY 1, 2, 3
    ORDER BY bucket_day DESC, num_events DESC
    LIMIT 100
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql("""
    SELECT
      DATE_TRUNC('DAY', time) AS bucket_day,
      from_artifact_name AS developer_login,
      to_artifact_namespace || '/' || to_artifact_name AS repo_name,
      SUM(amount) AS num_events
    FROM oso.int_events__github_unified
    WHERE
      time >= CURRENT_DATE - INTERVAL '14' DAY
      AND event_type IN (
        'COMMIT_CODE',
        'PULL_REQUEST_OPENED',
        'PULL_REQUEST_MERGED',
        'ISSUE_OPENED'
      )
    GROUP BY 1, 2, 3
    ORDER BY bucket_day DESC, num_events DESC
    LIMIT 100
    """, engine=pyoso_db_conn)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Related Models

    - **Commits**: [commits.py](/data/models/commits) — Commit-level activity from Open Dev Data with identity resolution and code churn metrics
    - **Repositories**: [repositories.py](/data/models/repositories) — Repository mappings, identifiers, and the bridge model for cross-source joins
    - **Developers**: [developers.py](/data/models/developers) — Unified developer identities across GitHub and Open Dev Data
    - **Ecosystems**: [ecosystems.py](/data/models/ecosystems) — Ecosystem hierarchies and repository-to-ecosystem mappings
    - **Activity Metrics**: [activity.py](/data/metric-definitions/activity) — Monthly Active Developer (MAD) metric definitions built on event data
    """)
    return


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
