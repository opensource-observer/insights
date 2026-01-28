import marimo

__generated_with = "0.19.2"
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
    ## Data Quality and Coverage Challenges

    Working with commit data presents several quality and coverage challenges:

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
    ## The Unified Solution

    We provide two models for working with unified commits:

    ### `int_ddp__commits_unified`

    Combines commits from both Open Dev Data and GitHub Archive by **joining on commit SHA**. This model LEFT JOINs ODD data to GHA commits, enriching GHA commits with ODD metadata where available.

    **Key characteristics:**
    - Grain is `(sha, repository_id)` - the same commit can appear in multiple repositories (forks)
    - May contain duplicates if the same commit appears multiple times in the source data
    - Best for: Analysis where you want all commit occurrences, including across forks

    ### `int_ddp__commits_deduped`

    A deduplicated version of the unified commits, keeping only the first occurrence of each `(sha, repository_id)` pair by `created_at`.

    **Key characteristics:**
    - Grain is `(sha, repository_id)` with deduplication applied
    - Each commit appears only once per repository
    - Best for: Analysis requiring unique commits per repository (e.g., counting commits per repo)

    ### How the Unification Works

    1. **Start with GHA commits**: All commits from GitHub Archive push events (`stg_github__commits`)
    2. **Enrich with ODD data**: LEFT JOIN ODD commits on SHA to add rich metadata (additions, deletions, `canonical_developer_id`)
    3. **Resolve author IDs**: Use `node_id_map` to decode ODD's GraphQL IDs to GitHub Database IDs

    The result is GHA commits enriched with ODD metadata where available, providing both `actor_id` (who pushed) and `author_id` (commit author) when possible.

    ### Data Lineage

    **Source Models:**
    - `stg_github__commits`: Extracts commits from GitHub Archive push events (pre-Oct 2025)
    - `stg_github__commits_since_20251007`: Extracts commits from GitHub Archive push events (post-Oct 2025)
    - `stg_opendevdata__commits`: Raw commits from Open Dev Data with identity resolution
    - `int_github__commits_all`: Consolidated GHA commits (UNION of both pre and post-Oct 2025)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.mermaid("""
    graph TD
        A[stg_github__commits<br/>Pre-Oct 2025] --> B[int_github__commits_all<br/>Consolidated GHA]
        A2[stg_github__commits_since_20251007<br/>Post-Oct 2025] --> B
        C[stg_opendevdata__commits<br/>ODD commits] --> D
        B --> D{LEFT JOIN on SHA}
        D --> E[int_ddp__commits_unified<br/>Unified, not deduped]
        E --> F[int_ddp__commits_deduped<br/>Deduplicated]
    """)
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview("oso.int_ddp__commits_unified")
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview("oso.int_ddp__commits_deduped")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Best Practices

    | Goal | Recommended Model | Why? |
    |------|-------------------|------|
    | **Count commits per repository** | `int_ddp__commits_deduped` | Ensures each commit counted only once per repo |
    | **Code churn analysis** | `int_ddp__commits_unified` | Includes additions/deletions from ODD enrichment |
    | **Cross-fork analysis** | `int_ddp__commits_unified` | See all occurrences of a commit across forks |
    | **Real-time activity** | `int_github__commits_all` | Most current GHA data (underlying source) |
    | **ODD-only analysis** | `stg_opendevdata__commits` | Query ODD data directly without GHA enrichment |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Overlap Analysis

    The `source` column in `int_ddp__commits_unified` tells us where each commit originated:

    - **gharchive**: Commits from GitHub Archive (may also exist in ODD if enriched)
    - **opendevdata**: Commits that exist ONLY in Open Dev Data (not in GHA)

    Commits with `source = 'gharchive'` that have non-null `canonical_developer_id` exist in both systems.
    """)
    return


@app.cell(hide_code=True)
def _(mo, px, pyoso_db_conn):
    _query = """
    SELECT
      CASE
        WHEN source = 'opendevdata' THEN 'ODD Only'
        WHEN source = 'gharchive' AND canonical_developer_id IS NOT NULL THEN 'Both ODD + GHA'
        WHEN source = 'gharchive' AND canonical_developer_id IS NULL THEN 'GHA Only'
      END AS commit_source,
      COUNT(*) AS commit_count
    FROM oso.int_ddp__commits_unified
    WHERE created_at >= DATE '2025-01-01'
    GROUP BY
      CASE
        WHEN source = 'opendevdata' THEN 'ODD Only'
        WHEN source = 'gharchive' AND canonical_developer_id IS NOT NULL THEN 'Both ODD + GHA'
        WHEN source = 'gharchive' AND canonical_developer_id IS NULL THEN 'GHA Only'
      END
    """
    _df = mo.sql(_query, engine=pyoso_db_conn)

    _fig = px.pie(
        _df,
        names='commit_source',
        values='commit_count',
        title='Commit Source Distribution (2025+)',
        hole=0.4
    )
    _fig.update_traces(
        textinfo='label+value+percent',
        texttemplate='%{label}<br>%{value}<br>%{percent:.2%}'
    )
    mo.ui.plotly(_fig)
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

    return (render_table_preview,)


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
