import marimo

__generated_with = "0.17.5"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Filecoin Developer Data Tour
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">Protocol Labs</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-11</span></small>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Overview

    This notebook provides an interactive tour of the Filecoin and Protocol Labs Network (PLN) developer data available through OSO.
    The data covers GitHub activity metrics, contributor lifecycle states, and project-level analytics for the PLN ecosystem.

    **Collections in scope:**
    - **Protocol Labs Network (PLN)** - The umbrella collection covering all PLN projects
    - **Filecoin Core** - Core Filecoin protocol projects
    - **Filecoin Builders** - Projects building on Filecoin

    **Primary use cases:**
    - Tracking developer engagement and retention across the ecosystem
    - Analyzing contributor lifecycle states (first-time, part-time, full-time, churned)
    - Comparing activity across projects and collections
    - Monitoring ecosystem health via GitHub metrics
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

    def render_table_preview(model_name, description=""):
        df = get_model_preview(model_name)
        sql_snippet = generate_sql_snippet(model_name, df, limit=5)
        fmt = {c: '{:.0f}' for c in df.columns if df[c].dtype == 'int64' and ('_id' in c or c == 'id')}
        table = mo.ui.table(df, format_mapping=fmt, show_column_summaries=False, show_data_types=False)
        row_count = get_row_count(model_name)
        col_count = len(df.columns)
        title = f"{model_name} | {row_count:,.0f} rows, {col_count} cols"
        content = mo.vstack([mo.md(description) if description else None, sql_snippet, table])
        return mo.accordion({title: content})

    def render_table_accordion(model_configs):
        """Render multiple tables in a single accordion.
        model_configs: list of (model_name, description) tuples
        """
        accordion = {}
        for model_name, description in model_configs:
            df = get_model_preview(model_name)
            sql_snippet = generate_sql_snippet(model_name, df, limit=5)
            fmt = {c: '{:.0f}' for c in df.columns if df[c].dtype == 'int64' and ('_id' in c or c == 'id')}
            table = mo.ui.table(df, format_mapping=fmt, show_column_summaries=False, show_data_types=False)
            row_count = get_row_count(model_name)
            col_count = len(df.columns)
            title = f"{model_name} | {row_count:,.0f} rows, {col_count} cols"
            content = mo.vstack([mo.md(description) if description else None, sql_snippet, table])
            accordion[title] = content
        return mo.accordion(accordion)
    return (render_table_preview,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Primary Tables

    ### Collections

    Collections group related projects together. The Filecoin ecosystem has three main collections:
    - `protocol-labs-network` - All PLN projects
    - `filecoin-core` - Core protocol projects
    - `filecoin-builders` - Builder ecosystem projects
    """)
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview(
        "collections_v1",
        "The `collection_id` is used to join with other tables. Filter by `collection_source = 'OSS_DIRECTORY'` for curated collections."
    )
    return


@app.cell
def _(collections_v1, mo, pyoso_db_conn):
    df_filecoin_collections = mo.sql(
        f"""
        SELECT 
          collection_name,
          display_name,
          description
        FROM collections_v1
        WHERE collection_source = 'OSS_DIRECTORY'
        AND collection_name IN ('protocol-labs-network', 'filecoin-core', 'filecoin-builders')
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Projects

    Projects represent individual open source projects (e.g., IPFS, libp2p, Filecoin).
    Use `projects_by_collection_v1` to find projects in a specific collection.
    """)
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview(
        "projects_v1",
        "Each project has a unique `project_id`. The `project_source` indicates where the project is registered (e.g., `OSS_DIRECTORY`)."
    )
    return


@app.cell
def _(mo, projects_by_collection_v1, projects_v1, pyoso_db_conn):
    df_pln_projects = mo.sql(
        f"""
        SELECT 
          p.project_name,
          p.display_name,
          pbc.collection_name
        FROM projects_by_collection_v1 pbc
        JOIN projects_v1 p USING (project_id)
        WHERE pbc.collection_name = 'protocol-labs-network'
        ORDER BY p.display_name
        LIMIT 20
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Artifacts (Repositories)

    Artifacts are the lowest-level entities - typically GitHub repositories.
    Each artifact is linked to a project via `artifacts_by_project_v1`.
    """)
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview(
        "artifacts_by_project_v1",
        "Filter by `artifact_source = 'GITHUB'` for GitHub repositories. The `artifact_namespace` is the GitHub org/user, and `artifact_name` is the repo name."
    )
    return


@app.cell
def _(
    artifacts_by_project_v1,
    mo,
    projects_by_collection_v1,
    projects_v1,
    pyoso_db_conn,
):
    df_sample_artifacts = mo.sql(
        f"""
        SELECT 
          a.artifact_namespace,
          a.artifact_name,
          p.display_name AS project_display_name,
          pbc.collection_name
        FROM artifacts_by_project_v1 a
        JOIN projects_v1 p USING (project_id)
        JOIN projects_by_collection_v1 pbc USING (project_id)
        WHERE a.artifact_source = 'GITHUB'
        AND pbc.collection_name = 'protocol-labs-network'
        ORDER BY a.artifact_namespace, a.artifact_name
        LIMIT 20
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Metrics

    The `metrics_v0` table contains metadata about all available metrics. Key fields:
    - `metric_name` - Full metric identifier (e.g., `GITHUB_active_full_time_contributor_monthly`)
    - `metric_model` - The metric type (e.g., `active_full_time_contributor`)
    - `metric_event_source` - The data source (e.g., `GITHUB`)
    - `metric_time_aggregation` - Time granularity (e.g., `monthly`, `weekly`, `daily`)
    """)
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview(
        "metrics_v0",
        "Use `metric_id` to join with timeseries metrics tables. Search by `metric_model` to find specific metric types."
    )
    return


@app.cell
def _(metrics_v0, mo, pyoso_db_conn):
    df_lifecycle_metrics = mo.sql(
        f"""
        SELECT 
          metric_name,
          metric_model,
          metric_event_source,
          metric_time_aggregation,
          display_name
        FROM metrics_v0
        WHERE metric_event_source = 'GITHUB'
        AND metric_model LIKE '%contributor%'
        AND metric_time_aggregation = 'monthly'
        ORDER BY metric_model
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Time-Series Metrics

    Time-series metrics are available at three levels:
    - **Collection level** - `timeseries_metrics_by_collection_v0`
    - **Project level** - `timeseries_metrics_by_project_v0`
    - **Artifact level** - `timeseries_metrics_by_artifact_v0` (less common)

    Always join with `metrics_v0` to get metric metadata.
    """)
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview(
        "timeseries_metrics_by_collection_v0",
        "Join on `metric_id` with `metrics_v0` and on `collection_id` with `collections_v1`."
    )
    return


@app.cell
def _(
    collections_v1,
    metrics_v0,
    mo,
    pyoso_db_conn,
    timeseries_metrics_by_collection_v0,
):
    df_collection_metrics_sample = mo.sql(
        f"""
        SELECT 
          c.collection_name,
          m.metric_model,
          ts.sample_date,
          ts.amount
        FROM timeseries_metrics_by_collection_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN collections_v1 c USING (collection_id)
        WHERE c.collection_name = 'protocol-labs-network'
        AND m.metric_model = 'active_full_time_contributor'
        AND m.metric_time_aggregation = 'monthly'
        ORDER BY ts.sample_date DESC
        LIMIT 12
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Key Metrics (Snapshots)

    For current-state metrics (like total stars, forks), use the `key_metrics_by_*` tables:
    - `key_metrics_by_artifact_v0` - Per-repository snapshots
    - `key_metrics_by_project_v0` - Per-project snapshots
    - `key_metrics_by_collection_v0` - Per-collection snapshots
    """)
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview(
        "key_metrics_by_artifact_v0",
        "Contains the most recent snapshot of key metrics for each artifact. Useful for stars, forks, and contributor counts."
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Example Queries

    ### Get lifecycle metrics for PLN collections
    """)
    return


@app.cell
def _(
    collections_v1,
    metrics_v0,
    mo,
    pyoso_db_conn,
    timeseries_metrics_by_collection_v0,
):
    df_lifecycle_by_collection = mo.sql(
        f"""
        SELECT 
          c.display_name AS collection,
          m.metric_model AS lifecycle_state,
          ts.sample_date,
          ts.amount AS developer_count
        FROM timeseries_metrics_by_collection_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN collections_v1 c USING (collection_id)
        WHERE c.collection_name IN ('protocol-labs-network', 'filecoin-core', 'filecoin-builders')
        AND m.metric_event_source = 'GITHUB'
        AND m.metric_model LIKE '%contributor%'
        AND m.metric_model NOT LIKE 'change_in%'
        AND m.metric_time_aggregation = 'monthly'
        AND ts.sample_date >= DATE('2024-01-01')
        ORDER BY ts.sample_date DESC, c.collection_name, m.metric_model
        LIMIT 50
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Get top projects by active contributors
    """)
    return


@app.cell
def _(
    metrics_v0,
    mo,
    projects_by_collection_v1,
    projects_v1,
    pyoso_db_conn,
    timeseries_metrics_by_project_v0,
):
    df_top_projects = mo.sql(
        f"""
        SELECT 
          p.display_name AS project,
          pbc.collection_name,
          m.metric_model,
          AVG(ts.amount) AS avg_monthly_contributors
        FROM timeseries_metrics_by_project_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN projects_v1 p USING (project_id)
        JOIN projects_by_collection_v1 pbc USING (project_id)
        WHERE pbc.collection_name = 'protocol-labs-network'
        AND m.metric_model = 'active_full_time_contributor'
        AND m.metric_time_aggregation = 'monthly'
        AND ts.sample_date >= DATE('2024-01-01')
        GROUP BY 1, 2, 3
        ORDER BY avg_monthly_contributors DESC
        LIMIT 15
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Get repository metrics for a specific project
    """)
    return


@app.cell
def _(
    artifacts_by_project_v1,
    key_metrics_by_artifact_v0,
    metrics_v0,
    mo,
    projects_v1,
    pyoso_db_conn,
):
    df_repo_metrics = mo.sql(
        f"""
        SELECT 
          a.artifact_namespace || '/' || a.artifact_name AS repository,
          m.display_name AS metric,
          km.amount,
          km.sample_date
        FROM key_metrics_by_artifact_v0 km
        JOIN artifacts_by_project_v1 a USING (artifact_id)
        JOIN metrics_v0 m USING (metric_id)
        JOIN projects_v1 p USING (project_id)
        WHERE p.project_name = 'ipfs'
        AND a.artifact_source = 'GITHUB'
        AND m.metric_model IN ('stars', 'forks', 'contributors')
        ORDER BY km.amount DESC
        LIMIT 20
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Lifecycle Metrics Reference

    The contributor lifecycle metrics track how developers move through different engagement states:

    | Metric Model | Description |
    |-------------|-------------|
    | `first_time_contributor` | First contribution in this period |
    | `new_part_time_contributor` | Was first-time last period, now part-time |
    | `new_full_time_contributor` | Was first-time last period, now full-time |
    | `active_part_time_contributor` | Continued part-time engagement |
    | `active_full_time_contributor` | Continued full-time engagement |
    | `part_time_to_full_time_contributor` | Increased from part-time to full-time |
    | `full_time_to_part_time_contributor` | Decreased from full-time to part-time |
    | `reactivated_part_time_contributor` | Returned after gap, now part-time |
    | `reactivated_full_time_contributor` | Returned after gap, now full-time |
    | `churned_after_first_time_contributor` | Left after first contribution |
    | `churned_after_part_time_contributor` | Left after part-time engagement |
    | `churned_after_full_time_contributor` | Left after full-time engagement |

    **Activity Classification:**
    - **Full-time**: 10+ days of activity per month
    - **Part-time**: 1-9 days of activity per month
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Related Resources

    - **[OSO Documentation](https://docs.opensource.observer/)** - Full API and data documentation
    - **[OSS Directory](https://github.com/opensource-observer/oss-directory)** - Project registry source
    - **[Getting Started with Pyoso](https://docs.opensource.observer/docs/get-started/python)** - Python client guide
    - **[Marimo Documentation](https://docs.marimo.io/)** - Notebook framework docs
    """)
    return


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.express as px
    return


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
