import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Unified Commits Model
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Overview

    The Unified Commits Model brings together commit data from two complementary sources:

    - **Open Dev Data (ODD)**: A proprietary deduplication system that tracks commits with high fidelity, including detailed metrics like additions/deletions and resolved author identities via `canonical_developer_id`.
    
    - **GitHub Archive (GHA)**: A public event stream capturing all GitHub activity, including push events with commit payloads, identified by `actor_id` (the GitHub Database ID of the event actor).

    This unified model provides a complete view of code contributions, enabling accurate analysis across both curated high-fidelity data and universal event coverage.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## The Commit Identity Challenge

    Working with commit data presents several identity and attribution challenges:

    - **Actor vs. Author**: GHA `actor_id` represents the *pusher* (e.g., a maintainer merging a PR), not necessarily the original author of the code. In squash merges, original authors are buried within the event payload rather than being the primary actor.
    
    - **Payload Caps**: GitHub Archive `PushEvent` payloads are capped at 20 commits per event. Any commits beyond this limit in a single push are entirely missing from the GHA dataset.
    
    - **Historical Limitations (Pre-Oct 2025)**: Prior to 2025-10-07, commit payloads in GHA only contained `author_email` and `author_name`, but lacked the unique GitHub `user_id`, making reliable cross-event attribution difficult.
    
    - **Data Loss (Post-Oct 2025)**: Since 2025-10-07, GitHub Archive has stopped providing commit payload data entirely. This makes author attribution via GHA impossible for all new data, reinforcing the need for Open Dev Data's direct commit tracking.
    
    - **Coverage Limitations**: Open Dev Data tracks a curated set of repositories (high fidelity but selective), whereas GitHub Archive captures all public activity (universal but lower fidelity). This means commits may be missing from ODD if they occur in repositories outside the tracked set.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Commit Unification Architecture

    The unification follows a 3-layer approach centered on **commit SHA** as the primary key:

    1. **SHA-Based Matching**: The core unification happens by matching commits via their SHA hash. Since both ODD and GHA capture the same commit SHAs, this provides a reliable join key across sources.
    
    2. **Commit-Level Join**: ODD commits are matched to GHA events via commit SHAs where possible. When the same SHA appears in both sources, we can cross-reference metadata (e.g., linking an ODD commit's `canonical_developer_id` with a GHA event's `actor_id`).
    
    3. **Deduplication**: Merging commits from both sources and removing duplicates based on commit SHA, while preserving metadata from both systems. The result is a single record per commit with fields from both ODD and GHA where available.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## The Unified Solution

    The `int_ddp__commits_unified` model provides a single view of commits from both Open Dev Data and GitHub Archive.

    The model works by:
    
    1. Taking all commits from **Open Dev Data** with their rich metadata (additions, deletions, author info, `canonical_developer_id`).
    
    2. Unioning them with commits extracted from **GitHub Archive** push events, including the `actor_id` (the pusher) and event metadata.
    
    3. Deduplicating to create a master list of commits keyed by SHA, preserving both `canonical_developer_id` (from ODD) and `actor_id` (from GHA) for maximum flexibility.

    ### Cross-Referencing Developer Identities

    Once commits are unified by SHA, you can cross-reference developer identities between the two systems. For developers with GitHub accounts, the `node_id_map` can be used to translate between ODD's `github_graphql_id` and GHA's `user_id`. This is useful when you need to:
    
    - Link a commit author (from ODD) to their GitHub activity (from GHA)
    - Join commit data with other GitHub Archive events like issues and PRs
    - Build complete developer profiles across both data sources
    """)
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview("oso.int_ddp__commits_unified")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Best Practices

    | Goal | Recommended Source | Why? |
    |------|-------------------|------|
    | **Code Churn Analysis** | ODD commits | Includes additions/deletions metrics for measuring code change volume |
    | **Real-time Activity** | GHA commits | More current for recent events, especially post-Oct 2025 when GHA payloads stopped |
    | **Cross-Source Validation** | Unified model | Complete view with deduplication, ensures no commits are missed |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Overlap Analysis

    How many commits are tracked in both systems vs. unique to one?
    """)
    return


@app.cell(hide_code=True)
def _(mo, px, pyoso_db_conn):
    query = """
    WITH odd_commits AS (
      SELECT DISTINCT sha
      FROM oso.int_ddp__commits_unified
      WHERE source = 'opendevdata'
    ),
    gha_commits AS (
      SELECT DISTINCT sha
      FROM oso.int_ddp__commits_unified
      WHERE source = 'gharchive'
    ),
    categories AS (
      SELECT
        CASE
          WHEN o.sha IS NOT NULL AND g.sha IS NOT NULL THEN 'Both ODD + GHA'
          WHEN o.sha IS NOT NULL AND g.sha IS NULL THEN 'ODD Only'
          WHEN o.sha IS NULL AND g.sha IS NOT NULL THEN 'GHA Only'
        END AS commit_source,
        COALESCE(o.sha, g.sha) AS sha
      FROM odd_commits o
      FULL OUTER JOIN gha_commits g ON o.sha = g.sha
    )
    SELECT commit_source, COUNT(*) AS commit_count
    FROM categories
    WHERE commit_source IS NOT NULL
    GROUP BY commit_source
    """
    df = mo.sql(query, engine=pyoso_db_conn)

    fig = px.pie(
        df,
        names='commit_source',
        values='commit_count',
        title='Commit Source Distribution',
        hole=0.4
    )
    fig.update_traces(
        textinfo='label+value+percent',
        texttemplate='%{label}<br>%{value}<br>%{percent:.2%}'
    )
    mo.ui.plotly(fig)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Queries

    ### 1. Commits by Repository (Unified Model)

    Get commit counts by repository using the unified commits model.
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
            repository_name,
            source,
            COUNT(*) AS commit_count
        FROM oso.int_ddp__commits_unified
        WHERE created_at >= current_date - interval '30' day
        GROUP BY repository_name, source
        ORDER BY commit_count DESC
        LIMIT 15
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 2. Cross-Source Comparison

    Compare commit counts from ODD vs GHA for recent activity.
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
            DATE(created_at) AS commit_date,
            SUM(CASE WHEN source = 'opendevdata' THEN 1 ELSE 0 END) AS odd_commits,
            SUM(CASE WHEN source = 'gharchive' THEN 1 ELSE 0 END) AS gha_commits,
            COUNT(*) AS total_commits
        FROM oso.int_ddp__commits_unified
        WHERE created_at >= current_date - interval '14' day
        GROUP BY DATE(created_at)
        ORDER BY commit_date DESC
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 3. Recent Commits with Author Info

    Get recent commits enriched with author information from both sources.
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
            author_name,
            canonical_developer_id,
            actor_id,
            source
        FROM oso.int_ddp__commits_unified
        WHERE created_at >= current_date - interval '7' day
        ORDER BY created_at DESC
        LIMIT 10
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Related Models

    - **Developers**: [developers.py](./developers.py) — Unified developer identities across ODD and GHA
    - **Repositories**: [repositories.py](./repositories.py) — Repository metadata with canonical IDs
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
    
    def get_format_mapping(df, include_percentage=False):
        """Generate format mapping for table display"""
        fmt = {}
        for c in df.columns:
            if df[c].dtype in ['int64', 'float64']:
                if include_percentage and 'percentage' in c.lower():
                    fmt[c] = '{:.2f}'
                elif '_id' in c or c == 'id' or 'count' in c.lower():
                    fmt[c] = '{:.0f}'
                elif include_percentage:
                    fmt[c] = '{:.0f}'
        return fmt
    
    return (render_table_preview, pd, get_format_mapping)


@app.cell(hide_code=True)
def imports():
    import plotly.express as px
    import pandas as pd
    return pd, px


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
