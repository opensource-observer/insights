import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Filecoin Developer Data Tour
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">Protocol Labs</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-12</span></small>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Overview

    This notebook provides an interactive tour of the Filecoin and Protocol Labs Network (PLN) developer data available through OSO.
    It walks through the key data models, shows how to query them, and demonstrates practical examples.

    **What you'll learn:**
    1. How to find Filecoin-related collections using keyword search
    2. The hierarchy: Collections → Projects → Artifacts (repositories)
    3. How to query developer lifecycle metrics over time
    4. How to analyze contributor engagement across the ecosystem

    > **Note:** The companion dashboards and analysis notebooks focus on three main collections:
    > `protocol-labs-network`, `filecoin-core`, and `filecoin-builders`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Step 1: Finding Filecoin Collections

    Collections group related projects together. We can find Filecoin-related collections by searching for keywords like "Protocol Labs", "PLN", or "Filecoin" in the display name.
    """)
    return


@app.cell
def _(mo, pyoso_db_conn):
    df_filecoin_collections = mo.sql(
        f"""
        SELECT 
          collection_name,
          display_name,
          description
        FROM collections_v1
        WHERE collection_source = 'OSS_DIRECTORY'
        AND (
          LOWER(display_name) LIKE '%protocol labs%'
          OR LOWER(display_name) LIKE '%pln%'
          OR LOWER(display_name) LIKE '%filecoin%'
          OR LOWER(collection_name) LIKE '%filecoin%'
          OR LOWER(collection_name) LIKE '%protocol-labs%'
        )
        ORDER BY display_name
        """,
        engine=pyoso_db_conn
    )
    return (df_filecoin_collections,)


@app.cell(hide_code=True)
def _(df_filecoin_collections, mo):
    _count = len(df_filecoin_collections) if not df_filecoin_collections.empty else 0
    mo.md(f"""
    Found **{_count}** collections matching our keywords. The main ones we'll focus on are:
    - `protocol-labs-network` - The umbrella collection covering all PLN projects
    - `filecoin-core` - Core Filecoin protocol projects  
    - `filecoin-builders` - Projects building on Filecoin
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Step 2: Exploring Projects

    Each collection contains multiple projects. Let's see what projects are in the Protocol Labs Network:
    """)
    return


@app.cell
def _(mo, pyoso_db_conn):
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
        LIMIT 25
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Step 3: Understanding Repositories (Artifacts)

    Projects contain artifacts - typically GitHub repositories. Here's how to find repositories for PLN projects:
    """)
    return


@app.cell
def _(mo, pyoso_db_conn):
    df_sample_artifacts = mo.sql(
        f"""
        SELECT 
          a.artifact_namespace || '/' || a.artifact_name AS repository,
          p.display_name AS project,
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
    ---
    ## Step 4: Developer Lifecycle Metrics

    OSO tracks how developers move through different engagement states. Before querying these metrics, let's understand what they mean:

    | Lifecycle State | Description |
    |-----------------|-------------|
    | `first_time_contributor` | Making their first contribution |
    | `new_full_time_contributor` | Just became full-time (10+ days/month) |
    | `new_part_time_contributor` | Just became part-time (1-9 days/month) |
    | `active_full_time_contributor` | Continuing full-time engagement |
    | `active_part_time_contributor` | Continuing part-time engagement |
    | `reactivated_full_time_contributor` | Returned after gap, now full-time |
    | `reactivated_part_time_contributor` | Returned after gap, now part-time |
    | `churned_after_*` | No longer active after reaching that state |

    These metrics are stored in `timeseries_metrics_by_collection_v0` and can be filtered using the `metrics_v0` table.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Available Lifecycle Metrics

    Let's query the `metrics_v0` table to see all available contributor lifecycle metrics:
    """)
    return


@app.cell
def _(mo, pyoso_db_conn):
    df_lifecycle_metrics = mo.sql(
        f"""
        SELECT 
          metric_model,
          display_name,
          metric_time_aggregation
        FROM metrics_v0
        WHERE metric_event_source = 'GITHUB'
        AND metric_model LIKE '%contributor%'
        AND metric_model NOT LIKE 'change_in%'
        AND metric_time_aggregation = 'monthly'
        ORDER BY metric_model
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Querying Lifecycle Metrics Over Time

    Now let's see how these metrics change over time for the Protocol Labs Network. We join `timeseries_metrics_by_collection_v0` with `metrics_v0` and `collections_v1`:
    """)
    return


@app.cell
def _(mo, pyoso_db_conn):
    df_lifecycle_timeseries = mo.sql(
        f"""
        SELECT 
          c.display_name AS collection,
          m.metric_model AS lifecycle_state,
          ts.sample_date,
          ts.amount AS developer_count
        FROM timeseries_metrics_by_collection_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN collections_v1 c USING (collection_id)
        WHERE c.collection_name = 'protocol-labs-network'
        AND m.metric_event_source = 'GITHUB'
        AND m.metric_model IN (
          'active_full_time_contributor',
          'active_part_time_contributor', 
          'first_time_contributor'
        )
        AND m.metric_time_aggregation = 'monthly'
        AND ts.sample_date >= DATE('2023-01-01')
        ORDER BY ts.sample_date DESC, m.metric_model
        LIMIT 36
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Step 5: Project-Level Analysis

    You can also get metrics at the project level using `timeseries_metrics_by_project_v0`. Here are the top projects by average monthly full-time contributors:
    """)
    return


@app.cell
def _(mo, pyoso_db_conn):
    df_top_projects = mo.sql(
        f"""
        SELECT 
          p.display_name AS project,
          AVG(ts.amount) AS avg_monthly_contributors
        FROM timeseries_metrics_by_project_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN projects_v1 p USING (project_id)
        JOIN projects_by_collection_v1 pbc USING (project_id)
        WHERE pbc.collection_name = 'protocol-labs-network'
        AND m.metric_model = 'active_full_time_contributor'
        AND m.metric_time_aggregation = 'monthly'
        AND ts.sample_date >= DATE('2024-01-01')
        AND ts.sample_date < DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1' MONTH
        GROUP BY p.display_name
        HAVING AVG(ts.amount) > 0
        ORDER BY avg_monthly_contributors DESC
        LIMIT 15
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Key Tables Reference

    | Table | Description | Key Columns |
    |-------|-------------|-------------|
    | `collections_v1` | Collection definitions | `collection_id`, `collection_name`, `display_name` |
    | `projects_v1` | Project metadata | `project_id`, `project_name`, `display_name` |
    | `projects_by_collection_v1` | Links projects to collections | `project_id`, `collection_id` |
    | `artifacts_by_project_v1` | Links artifacts to projects | `artifact_id`, `project_id`, `artifact_source` |
    | `metrics_v0` | Metric definitions | `metric_id`, `metric_model`, `metric_event_source` |
    | `timeseries_metrics_by_collection_v0` | Time-series metrics by collection | `metric_id`, `collection_id`, `sample_date`, `amount` |
    | `timeseries_metrics_by_project_v0` | Time-series metrics by project | `metric_id`, `project_id`, `sample_date`, `amount` |
    | `repositories_v0` | Repository metadata | `artifact_id`, `star_count`, `fork_count`, `language` |

    ---
    ## Related Resources

    - **[OSO Documentation](https://docs.oso.xyz/)** - Full API and data documentation
    - **[OSS Directory](https://github.com/opensource-observer/oss-directory)** - Project registry source
    - **[Getting Started with Pyoso](https://docs.oso.xyz/docs/get-started/python)** - Python client guide
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
