import marimo

__generated_with = "0.18.4"
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

    return (render_table_preview,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Developers

    We've created a **unified developer model** that bridges Open Dev Data's identity resolution with GitHub Archive's activity tracking, centered on a shared `user_id`.

    Preview:
    ```sql
    SELECT * FROM oso.int_ddp__developers LIMIT 10
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Overview

    Open Dev Data (ODD) is a proprietary deduplication system that generates its own `canonical_developer_id` by clustering commits and developer profiles. It links these profiles to GitHub accounts via `primary_github_id` (GraphQL Node ID).

    GitHub Archive (GHA) provides a raw event stream identified by `actor_id` (GitHub Database ID).

    To bridge these systems, we decode the ODD-provided GraphQL Node ID into a Database ID to match GHA records.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## The Identity Challenge

    *   **Actor vs. Author**: GHA `actor_id` represents the *pusher* (e.g., a maintainer merging a PR), not necessarily the original author of the code. In the case of squash merges, the original authors are buried within the event payload rather than being the primary actor.
    *   **Payload Caps**: GitHub Archive `PushEvent` payloads are capped at 20 commits per event. Any commits beyond this limit in a single push are entirely missing from the GHA dataset.
    *   **Historical Limitations (Pre-Oct 2025)**: Prior to 2025-10-07, commit payloads in GHA only contained `author_email` and `author_name`, but lacked the unique GitHub `user_id`, making reliable cross-event attribution difficult.
    *   **Data Loss (Post-Oct 2025)**: Since 2025-10-07, GitHub Archive has stopped providing commit payload data entirely. This makes author attribution via GHA impossible for all new data, reinforcing the need for Open Dev Data's direct commit tracking.
    *   **Coverage Limitations**: Open Dev Data tracks a curated set of repositories (high fidelity but selective), whereas GitHub Archive captures all public activity (universal but lower fidelity). This means a developer may be missing from ODD if they contribute to repositories outside the tracked set.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## The Unified Solution

    The `int_ddp__developers` model unifies these two worlds by centering on the **GitHub Database ID** (`user_id`).

    ### Identity Bridging Architecture

    The unification follows a 3-layer approach:
    1.  **ID Translation (node_id_map)**: Resolving `github_graphql_id` to `user_id`.
    2.  **Commit-Level Join (SHA-based)**: Matching ODD commits to GHA events via commit SHAs where possible.
    3.  **Developer Unification (Union + Dedupe)**: Merging the sets and deduplicating by `user_id`.

    It works by:
    1.  Taking all **Authors** from OpenDevData who have a known GitHub account (resolved by decoding `github_graphql_id` -> `user_id` via `int_github__node_id_map`).
    2.  Unioning them with all **Actors** from GitHub Archive (where `actor_id` is already the `user_id`).
    3.  Deduplicating to create a master list of users keyed by `user_id`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.mermaid("""
    graph TD
        A[stg_opendevdata__developers<br/>ODD authors with GraphQL IDs] --> B[int_github__node_id_map<br/>Decode GraphQL → Database ID]
        B --> D{Union + Deduplicate by user_id}
        C[int_gharchive__github_events<br/>GHA actors with Database IDs] --> D
        D --> E[int_ddp__developers<br/>Unified developer list]
    """)
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview("oso.int_ddp__developers")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Best Practices

    | Goal | Recommended ID | Why? |
    |:------|:----------------|:------|
    | **Commit Analysis** | `canonical_developer_id` | Handles aliasing (e.g., "Jane Doe" using 3 different emails). Most accurate for code contributions. |
    | **Platform Activity** | `user_id` / `actor_id` | Required for linking Issues, PRs, and Comments from GitHub Archive. |
    | **Cross-Domain** | `user_id` | The only bridge between the two worlds. Use `int_ddp__developers` to map `canonical_developer_id` to `user_id`. |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Overlap Analysis

    How many developers are tracked in both systems vs. unique to one?
    """)
    return


@app.cell(hide_code=True)
def _(mo, px, pyoso_db_conn):
    _query = """
    WITH odd_authors AS (
      SELECT DISTINCT author_id AS user_id
      FROM oso.int_ddp__commits_unified
      WHERE author_id IS NOT NULL AND canonical_developer_id IS NOT NULL
    ),
    gha_actors AS (
      SELECT DISTINCT actor_id AS user_id
      FROM oso.int_ddp__commits_unified
      WHERE actor_id IS NOT NULL
    ),
    categories AS (
      SELECT
        CASE
          WHEN o.user_id IS NOT NULL AND g.user_id IS NOT NULL THEN 'Both ODD + GHA'
          WHEN o.user_id IS NOT NULL AND g.user_id IS NULL THEN 'ODD Only'
          WHEN o.user_id IS NULL AND g.user_id IS NOT NULL THEN 'GHA Only'
        END AS developer_type,
        COALESCE(o.user_id, g.user_id) AS user_id
      FROM odd_authors o
      FULL OUTER JOIN gha_actors g ON o.user_id = g.user_id
    )
    SELECT developer_type, COUNT(*) AS user_count
    FROM categories
    GROUP BY developer_type
    """
    _df = mo.sql(_query, engine=pyoso_db_conn)

    _total = int(_df['user_count'].sum())
    _both = int(_df.loc[_df['developer_type'] == 'Both ODD + GHA', 'user_count'].sum())
    _odd_only = int(_df.loc[_df['developer_type'] == 'ODD Only', 'user_count'].sum())
    _gha_only = int(_df.loc[_df['developer_type'] == 'GHA Only', 'user_count'].sum())

    _fig = px.pie(
        _df,
        names='developer_type',
        values='user_count',
        title='Developer Identity Source Distribution',
        hole=0.4
    )
    _fig.update_traces(
        textinfo='label+value+percent',
        texttemplate='%{label}<br>%{value}<br>%{percent:.2%}'
    )

    mo.vstack([
        mo.hstack([
            mo.stat(label="Total Developers", value=f"{_total:,}", bordered=True, caption="All unique user_ids"),
            mo.stat(label="Both Sources", value=f"{_both:,}", bordered=True, caption="ODD + GHA overlap"),
            mo.stat(label="ODD Only", value=f"{_odd_only:,}", bordered=True, caption="Open Dev Data exclusive"),
            mo.stat(label="GHA Only", value=f"{_gha_only:,}", bordered=True, caption="GitHub Archive exclusive"),
        ], widths="equal", gap=1),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Queries

    ### 1. Full Activity Profile

    Get a developer's complete history: commits (from ODD) and issues (from GitHub Archive).

    ```sql
    WITH recent_commits AS (
        SELECT author_id, COUNT(*) as commits
        FROM oso.int_ddp__commits_deduped
        WHERE created_at >= current_date - interval '180' day
        GROUP BY 1
    ),
    recent_activity AS (
        SELECT
            actor_id,
            SUM(amount) FILTER (WHERE event_type = 'ISSUE_ACTIVITY') as issue_events,
            SUM(amount) FILTER (WHERE event_type = 'STARRED') as star_events
        FROM oso.int_ddp_github_events_daily
        WHERE bucket_day >= current_date - interval '180' day
        GROUP BY 1
    )
    SELECT
        d.user_id,
        d.canonical_developer_id,
        COALESCE(c.commits, 0) as total_commits,
        COALESCE(a.issue_events, 0) as total_issues,
        COALESCE(a.star_events, 0) as total_starred
    FROM oso.int_ddp__developers d
    LEFT JOIN recent_commits c ON d.user_id = c.author_id
    LEFT JOIN recent_activity a ON d.user_id = a.actor_id
    WHERE d.canonical_developer_id IS NOT NULL
    ORDER BY total_commits DESC
    LIMIT 10
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        WITH recent_commits AS (
            SELECT author_id, COUNT(*) as commits
            FROM oso.int_ddp__commits_deduped
            WHERE created_at >= current_date - interval '180' day
            GROUP BY 1
        ),
        recent_activity AS (
            SELECT
                actor_id,
                SUM(amount) FILTER (WHERE event_type = 'ISSUE_ACTIVITY') as issue_events,
                SUM(amount) FILTER (WHERE event_type = 'STARRED') as star_events
            FROM oso.int_ddp_github_events_daily
            WHERE bucket_day >= current_date - interval '180' day
            GROUP BY 1
        )
        SELECT
            d.user_id,
            d.canonical_developer_id,
            COALESCE(c.commits, 0) as total_commits,
            COALESCE(a.issue_events, 0) as total_issues,
            COALESCE(a.star_events, 0) as total_starred
        FROM oso.int_ddp__developers d
        LEFT JOIN recent_commits c ON d.user_id = c.author_id
        LEFT JOIN recent_activity a ON d.user_id = a.actor_id
        WHERE d.canonical_developer_id IS NOT NULL
        ORDER BY total_commits DESC
        LIMIT 10
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 2. Commits by Canonical Developer (ODD)

    ```sql
    SELECT
        created_at,
        repository_name,
        sha,
        author_name
    FROM oso.int_ddp__commits_deduped
    WHERE canonical_developer_id IN (
        SELECT canonical_developer_id
        FROM oso.int_ddp__developers
        LIMIT 1
    )
    ORDER BY created_at DESC
    LIMIT 10
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
            created_at,
            repository_name,
            sha,
            author_name
        FROM oso.int_ddp__commits_deduped
        WHERE canonical_developer_id IN (
            SELECT canonical_developer_id
            FROM oso.int_ddp__developers
            LIMIT 1
        )
        ORDER BY created_at DESC
        LIMIT 10
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 3. Events by Actor (GHA)

    ```sql
    WITH active_actor AS (
        SELECT e.actor_id
        FROM oso.int_ddp_github_events_daily e
        JOIN oso.int_ddp__developers d ON e.actor_id = d.user_id
        WHERE e.bucket_day >= current_date - interval '30' day
        LIMIT 1
    )
    SELECT
        event_time as created_at,
        event_type as type,
        repo_name
    FROM oso.int_ddp_github_events
    WHERE actor_id IN (SELECT actor_id FROM active_actor)
    AND event_time >= current_date - interval '30' day
    ORDER BY event_time DESC
    LIMIT 10
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        WITH active_actor AS (
            SELECT e.actor_id
            FROM oso.int_ddp_github_events_daily e
            JOIN oso.int_ddp__developers d ON e.actor_id = d.user_id
            WHERE e.bucket_day >= current_date - interval '30' day
            LIMIT 1
        )
        SELECT
            event_time as created_at,
            event_type as type,
            repo_name
        FROM oso.int_ddp_github_events
        WHERE actor_id IN (SELECT actor_id FROM active_actor)
        AND event_time >= current_date - interval '30' day
        ORDER BY event_time DESC
        LIMIT 10
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Related Models

    - **Commits**: commits — Unified commit data across ODD and GHA
    - **Events**: events — GitHub Archive event data and activity metrics
    - **Repositories**: repositories — Repository metadata with canonical IDs
    """)
    return


@app.cell(hide_code=True)
def imports():
    import plotly.express as px
    return (px,)


@app.cell(hide_code=True)
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
