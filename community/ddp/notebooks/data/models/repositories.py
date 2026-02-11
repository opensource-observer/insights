import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Repositories

    The **repository bridge model** maps Open Dev Data repositories to canonical GitHub IDs, enabling cross-source joins between ODD's commit tracking and GitHub Archive's event stream.

    Preview:
    ```sql
    SELECT * FROM oso.int_opendevdata__repositories_with_repo_id LIMIT 10
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Overview

    The `int_opendevdata__repositories_with_repo_id` model serves as a bridge between multiple data sources within the OSO ecosystem. It provides a unified view of software repositories by mapping external identifiers to canonical GitHub integer IDs.

    - **Normalization**: Standardizes repository names and URLs across different schemas
    - **Stability**: Provides a stable `repo_id` that can be used to join events, contributions, and project-level metrics
    - **Cross-source analysis**: Enables joining Open Dev Data commits with GitHub Archive events via a shared `repo_id`

    ### ID Source Definitions

    The `repo_id_source` column indicates how the internal `repo_id` was resolved:

    | Source | Description | Reliability |
    |:-------|:------------|:------------|
    | `ossd` | Verified match via `github_graphql_id` in the curated OSS Directory | Highest |
    | `node_id` | Decoded from `github_graphql_id` via node_id_map, but not in OSS Directory | High |
    | `gharchive` | Fallback match by `repo_name` in GitHub Archive data | Lower |
    | `opendevdata` | No match found — `repo_id` is NULL | None |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## The 3-ID System

    Repositories in the OSO ecosystem have three different identifiers that need bridging:

    | ID Type | Column Name | Description |
    |:--------|:------------|:------------|
    | OpenDevData ID | `opendevdata_id` | Primary key in ODD source data |
    | GraphQL Node ID | `github_graphql_id` | GitHub's global opaque ID (Base64 encoded) |
    | REST API ID | `repo_id` | Numeric GitHub Database ID — the primary join key |

    The `repo_id` (REST API ID) is the canonical join key used throughout the DDP models to connect repositories across Open Dev Data and GitHub Archive.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## ID Mapping Strategy

    The model employs a 3-tier priority logic to assign a `repo_id` to each record:

    1. **Primary Match (OSS Directory)**: Match using `github_graphql_id` against the curated OSS Directory. Most reliable — relies on persistent, immutable IDs from GitHub.
    2. **Decoded Match (Node ID Map)**: If not in OSS Directory, decode the `github_graphql_id` to an integer ID using `int_github__node_id_map`. Handles both legacy Base64 and next-gen MessagePack formats.
    3. **Fallback Match (GitHub Archive)**: Match by `repo_name` (e.g., `owner/repo`) against GitHub Archive data. Less reliable due to renames.
    4. **Unmatched**: `repo_id` is NULL. The repository exists in ODD but couldn't be mapped to a GitHub integer ID.

    ### Node ID Decoding

    A key challenge is bridging GitHub's two API ID systems:
    - **GraphQL API**: Opaque Node IDs (e.g., `MDEwOlJlcG9zaXRvcnkyNDI0Nzg0`)
    - **REST API**: Integer Database IDs (e.g., `2424784`)

    The `int_github__node_id_map` model pre-computes this mapping by decoding both legacy (simple Base64) and next-gen (MessagePack binary) ID formats.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.mermaid("""
    graph TD
        A[stg_opendevdata__repos<br/>ODD repositories with GraphQL IDs] --> D
        B[int_github__node_id_map<br/>Decode GraphQL → Database ID] --> D
        C[oss-directory artifacts<br/>Curated repo mappings] --> D
        E[int_gharchive__github_events<br/>GHA repos for name-based fallback] --> D
        D[int_opendevdata__repositories_with_repo_id<br/>Unified repo bridge with repo_id + source]
    """)
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview("oso.int_opendevdata__repositories_with_repo_id")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Best Practices

    | Goal | Recommended Approach | Why? |
    |:------|:---------------------|:------|
    | **Join ODD commits to GHA events** | Use `repo_id` from the bridge model | Canonical integer ID shared by both systems |
    | **Filter by match quality** | Filter on `repo_id_source` | Exclude lower-reliability fallback matches |
    | **Connect repos to ecosystems** | Join to `ecosystems_repos_recursive` via `opendevdata_id` | Maps repos to ecosystem hierarchy |
    | **Find popular repos** | Filter on `star_count > N` with `repo_id IS NOT NULL` | Only matched repos have reliable star counts |
    | **Identify coverage gaps** | Query `WHERE repo_id IS NULL` | Find ODD repos not yet mapped to GitHub IDs |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Live Data Exploration

    The following charts show actual data from the repository bridge model to demonstrate coverage and trends.
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _query = """
    SELECT
      repo_id_source,
      COUNT(*) AS count,
      COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS percentage
    FROM oso.int_opendevdata__repositories_with_repo_id
    GROUP BY repo_id_source
    ORDER BY count DESC
    """

    df_coverage = mo.sql(_query, engine=pyoso_db_conn, output=False)
    return (df_coverage,)


@app.cell(hide_code=True)
def _(df_coverage, mo, px):
    _total_repos = int(df_coverage['count'].sum())
    _matched = int(df_coverage.loc[df_coverage['repo_id_source'] != 'opendevdata', 'count'].sum())
    _match_rate = _matched / _total_repos * 100 if _total_repos > 0 else 0
    _top_source = df_coverage.iloc[0]['repo_id_source'] if len(df_coverage) > 0 else "N/A"
    _top_count = int(df_coverage.iloc[0]['count']) if len(df_coverage) > 0 else 0

    _fig = px.bar(
        df_coverage,
        x='repo_id_source',
        y='count',
        text='count',
        labels={'repo_id_source': 'ID Source', 'count': 'Repository Count'},
        color_discrete_sequence=['#4C78A8']
    )

    _fig.update_traces(
        texttemplate='%{text:,.0f}',
        textposition='outside',
        marker_color='#4C78A8'
    )

    _fig.update_layout(
        template='plotly_white',
        margin=dict(t=20, l=0, r=0, b=0),
        height=400,
        xaxis=dict(
            title='',
            showgrid=False,
            linecolor="#000",
            linewidth=1
        ),
        yaxis=dict(
            title='Repository Count',
            showgrid=True,
            gridcolor="#E5E5E5",
            linecolor="#000",
            linewidth=1
        )
    )

    mo.vstack([
        mo.hstack([
            mo.stat(label="Total Repositories", value=f"{_total_repos:,}", bordered=True, caption="In ODD source data"),
            mo.stat(label="Matched to repo_id", value=f"{_matched:,}", bordered=True, caption=f"{_match_rate:.1f}% match rate"),
            mo.stat(label="Top Source", value=_top_source, bordered=True, caption=f"{_top_count:,} repos"),
        ], widths="equal", gap=1),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("### Repository Creation Trend")
    return


@app.cell(hide_code=True)
def _(mo, pd, px, pyoso_db_conn):
    _query = """
    SELECT
      DATE_TRUNC('month', repo_created_at) AS month,
      COUNT(*) AS count
    FROM oso.int_opendevdata__repositories_with_repo_id
    WHERE repo_created_at IS NOT NULL
    GROUP BY 1
    ORDER BY 1
    """

    _df = mo.sql(_query, engine=pyoso_db_conn, output=False)
    _df['month'] = pd.to_datetime(_df['month'])

    _total = int(_df['count'].sum())
    _peak_month = _df.loc[_df['count'].idxmax(), 'month'].strftime('%b %Y') if len(_df) > 0 else "N/A"
    _peak_count = int(_df['count'].max()) if len(_df) > 0 else 0

    _fig = px.area(
        _df,
        x='month',
        y='count',
        color_discrete_sequence=['#F58518']
    )

    _fig.update_traces(
        line=dict(width=2),
        fillcolor='rgba(245, 133, 24, 0.2)',
        hovertemplate='<b>%{x|%b %Y}</b><br>Repos Created: %{y:,.0f}<extra></extra>'
    )

    _fig.update_layout(
        template='plotly_white',
        margin=dict(t=20, l=0, r=0, b=0),
        height=400,
        hovermode='x unified',
        xaxis=dict(
            title='',
            showgrid=False,
            linecolor="#000",
            linewidth=1,
            tickformat="%Y"
        ),
        yaxis=dict(
            title='Repos Created per Month',
            showgrid=True,
            gridcolor="#E5E5E5",
            linecolor="#000",
            linewidth=1
        )
    )

    mo.vstack([
        mo.hstack([
            mo.stat(label="Total with Created Date", value=f"{_total:,}", bordered=True, caption="Repos with repo_created_at"),
            mo.stat(label="Peak Month", value=_peak_month, bordered=True, caption=f"{_peak_count:,} repos created"),
        ], widths="equal", gap=1),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Queries

    ### 1. Cross-Source Join (Popular Repos with GitHub IDs)

    Find popular repositories that have been successfully mapped to a GitHub `repo_id`.

    ```sql
    SELECT
      repo_name,
      repo_id,
      opendevdata_id,
      repo_id_source,
      star_count
    FROM oso.int_opendevdata__repositories_with_repo_id
    WHERE repo_id IS NOT NULL
      AND star_count > 1000
    ORDER BY star_count DESC
    LIMIT 20
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          repo_name,
          repo_id,
          opendevdata_id,
          repo_id_source,
          star_count
        FROM oso.int_opendevdata__repositories_with_repo_id
        WHERE repo_id IS NOT NULL
          AND star_count > 1000
        ORDER BY star_count DESC
        LIMIT 20
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 2. ID Source Coverage Breakdown

    See how repositories were matched across the 3-tier priority system.

    ```sql
    SELECT
      repo_id_source,
      COUNT(*) AS count,
      COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS percentage
    FROM oso.int_opendevdata__repositories_with_repo_id
    GROUP BY repo_id_source
    ORDER BY count DESC
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          repo_id_source,
          COUNT(*) AS count,
          COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS percentage
        FROM oso.int_opendevdata__repositories_with_repo_id
        GROUP BY repo_id_source
        ORDER BY count DESC
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 3. Unmatched Repositories

    Find ODD repositories that could not be mapped to a GitHub integer ID.

    ```sql
    SELECT
      opendevdata_id,
      repo_name,
      github_graphql_id,
      repo_id_source
    FROM oso.int_opendevdata__repositories_with_repo_id
    WHERE repo_id IS NULL
    LIMIT 10
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          opendevdata_id,
          repo_name,
          github_graphql_id,
          repo_id_source
        FROM oso.int_opendevdata__repositories_with_repo_id
        WHERE repo_id IS NULL
        LIMIT 10
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 4. Bridge to Ecosystem Data

    Join repositories to ecosystems for ecosystem-level analysis.

    ```sql
    SELECT
      e.name AS ecosystem_name,
      COUNT(DISTINCT r.repo_id) AS matched_repos,
      COUNT(DISTINCT r.opendevdata_id) AS total_odd_repos
    FROM oso.stg_opendevdata__ecosystems_repos_recursive err
    JOIN oso.stg_opendevdata__ecosystems e ON err.ecosystem_id = e.id
    JOIN oso.int_opendevdata__repositories_with_repo_id r
      ON err.repo_id = r.opendevdata_id
    GROUP BY e.name
    ORDER BY matched_repos DESC
    LIMIT 15
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          e.name AS ecosystem_name,
          COUNT(DISTINCT r.repo_id) AS matched_repos,
          COUNT(DISTINCT r.opendevdata_id) AS total_odd_repos
        FROM oso.stg_opendevdata__ecosystems_repos_recursive err
        JOIN oso.stg_opendevdata__ecosystems e ON err.ecosystem_id = e.id
        JOIN oso.int_opendevdata__repositories_with_repo_id r
          ON err.repo_id = r.opendevdata_id
        GROUP BY e.name
        ORDER BY matched_repos DESC
        LIMIT 15
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Edge Cases & Unmatched Repos

    **Duplication**: Multiple ODD records may point to the same `repo_id` due to repository renames or forks tracked as distinct entries in the source data.

    **Unmatched repos** (`repo_id IS NULL`): ~1,000 out of 2.4M repos (0.04%). All unmatched repos share two traits:

    1. **No `github_graphql_id`** — ODD never captured a GraphQL Node ID, so the node_id decoder couldn't run
    2. **Deleted on GitHub** — every sampled repo returns HTTP 404, not archived or redirected

    | Category | Count | Description |
    |:---------|------:|:------------|
    | Hyphenated names, no metadata | ~430 | ODD-internal naming (e.g., `nomadic-labs-grafazos` instead of `nomadic-labs/grafazos`), never resolved to a GitHub URL |
    | `owner/repo`, 0 stars | ~270 | Valid GitHub format but deleted repos with zero community activity |
    | ODD blacklisted | ~210 | Explicitly flagged by ODD as forks, spam, or irrelevant — also all 404 |
    | `owner/repo`, no metadata | ~55 | Valid format but no stars/dates — deleted before metadata capture |
    | `owner/repo`, has stars | ~50 | Had some stars (up to ~36) but deleted due to org renames or project shutdowns |

    **Bottom line**: The unmatched set is negligible and entirely composed of dead repos. No action needed — these are expected gaps from historical ODD tracking of repositories that have since been removed from GitHub.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Related Models

    - **Ecosystems**: [ecosystems.py](./ecosystems.py) — Ecosystem definitions and hierarchy
    - **Commits**: [commits.py](./commits.py) — Unified commit data across ODD and GHA
    - **Developers**: [developers.py](./developers.py) — Unified developer identities across ODD and GHA
    - **Events**: [events.py](./events.py) — GitHub Archive event data and activity metrics
    """)
    return


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
def imports():
    import pandas as pd
    import plotly.express as px
    return (pd, px)


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
