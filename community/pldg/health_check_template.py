import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Data Pipeline Health Check: [DATA_SOURCE_NAME]

    **Author:** Your Name
    **Date:** YYYY-MM-DD
    **Data Source:** `oso.stg_[source]__[table]` → `oso.int_[model]` → `oso.[model]_v0`

    ## ⚠️ Template Instructions

    This template uses **working example queries** with real OSO tables so you can run it immediately.

    **To customize for your data source:**
    1. Search for `TODO:` comments in each cell
    2. Replace example tables with your actual data pipeline tables
    3. Replace example fields with your actual column names
    4. Update this header with your data source details

    ## Understanding OSO Table Naming

    OSO uses a consistent naming convention to indicate the pipeline stage:

    - **Staging tables**: `oso.stg_[source]__[table]`
      - Prefix: `stg_` indicates staging layer
      - Example: `oso.stg_github__events` (raw GitHub events from staging)

    - **Intermediate tables**: `oso.int_[model_name]`
      - Prefix: `int_` indicates intermediate/transformation layer
      - Example: `oso.int_events_daily__github` (daily aggregated events)

    - **Mart tables**: `oso.[model_name]_v0` or `oso.[model_name]_v1`
      - Suffix: `_v0` or `_v1` indicates mart model version
      - Example: `oso.timeseries_metrics_by_project_v0` (final metrics mart)

    ## Overview
    This notebook performs 3 essential data quality checks:
    1. **Presence Check** - Verify data exists at each pipeline stage
    2. **Date Coverage** - Validate time-series data ranges and gaps
    3. **Duplicate Detection** - Identify duplicate records on key fields

    ## Pipeline Flow
    ```
    oso.stg_github__events (staging)
           ↓
    oso.int_events_daily__github (intermediate)
           ↓
    oso.timeseries_metrics_by_project_v0 (mart)
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Check 1: Presence - Row Counts at Each Pipeline Stage

    Verify data exists at each stage of the pipeline.
    This helps identify data loss or unexpected growth between stages.
    """)
    return


@app.cell
def _(mo, pyoso_db_conn):
    # TODO: Replace oso.stg_github__events with your staging table
    staging_count = mo.sql(
        f"""
        SELECT COUNT(*) as count
        FROM oso.stg_github__events
        WHERE DATE_TRUNC('DAY', created_at) = DATE('2025-01-01')
        """,
        engine=pyoso_db_conn
    )
    return (staging_count,)


@app.cell
def _(mo, pyoso_db_conn):
    # TODO: Replace oso.int_events_daily__github with your intermediate table
    intermediate_count = mo.sql(
        f"""
        SELECT COUNT(*) as count
        FROM oso.int_events_daily__github
        WHERE bucket_day = DATE('2025-01-01')
        """,
        engine=pyoso_db_conn
    )
    return (intermediate_count,)


@app.cell
def _(mo, pyoso_db_conn):
    # TODO: Replace oso.timeseries_metrics_by_project_v0 with your mart table
    mart_count = mo.sql(
        f"""
        SELECT COUNT(*) as count
        FROM oso.timeseries_metrics_by_project_v0
        JOIN oso.metrics_v0 USING (metric_id)
        WHERE
          sample_date = DATE('2025-01-01')
          AND metric_event_source = 'GITHUB'
        """,
        engine=pyoso_db_conn
    )
    return (mart_count,)


@app.cell
def _(intermediate_count, mart_count, pd, staging_count):
    # Create summary dataframe
    counts_df = pd.DataFrame(
        {
            "Stage": ["Staging (stg_)", "Intermediate (int_)", "Mart (_v0)"],
            "Row Count": [
                staging_count["count"].iloc[0],
                intermediate_count['count'].iloc[0],
                mart_count["count"].iloc[0],
            ],
        }
    )
    return (counts_df,)


@app.cell
def _(counts_df, px):
    # Create and display bar chart
    px.bar(
        counts_df,
        x="Stage",
        y="Row Count",
        title="Pipeline Row Counts by Stage (2025-01-01)",
        text="Row Count",
    ).update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    ).update_layout(
        yaxis_title="Row Count",
        showlegend=False
    )
    return


@app.cell
def _(intermediate_count, mart_count, mo, staging_count):
    mo.md(f"""
    **Results:**
    - Staging rows (stg_): {staging_count['count'].iloc[0]:,.0f}
    - Intermediate rows (int_): {intermediate_count['count'].iloc[0]:,.0f}
    - Mart rows (_v0): {mart_count['count'].iloc[0]:,.0f}

    **Analysis:** [Explain whether these counts make sense. Is data being filtered? Combined? Expanded?]
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Check 2: Date Coverage - Time-Series Data Analysis

    Analyze date range coverage in your time-series data.
    Gaps in date coverage can indicate pipeline failures or incomplete data.
    """)
    return


@app.cell
def _(mo, pyoso_db_conn):
    # TODO: Replace table and date field with your actual values
    coverage = mo.sql(
        f"""
        SELECT
            DATE(MIN(sample_date)) as earliest_date,
            DATE(MAX(sample_date)) as latest_date,
            COUNT(DISTINCT DATE(sample_date)) as unique_dates,
            DATE_DIFF('day', MIN(sample_date), MAX(sample_date)) as days_span
        FROM oso.timeseries_metrics_by_project_v0
        WHERE sample_date IS NOT NULL
        """,
        engine=pyoso_db_conn
    )
    return (coverage,)


@app.cell
def _(mo, pyoso_db_conn):
    # TODO: Replace table and date field with your actual values
    daily_counts = mo.sql(
        f"""
        SELECT
            DATE(sample_date) as date,
            COUNT(*) as record_count
        FROM oso.timeseries_metrics_by_project_v0
        WHERE sample_date IS NOT NULL
        GROUP BY DATE(sample_date)
        ORDER BY date DESC
        LIMIT 365
        """,
        engine=pyoso_db_conn
    )
    return (daily_counts,)


@app.cell
def _(daily_counts, px):
    # Create and display time series chart
    px.line(
        daily_counts,
        x="date",
        y="record_count",
        title="Daily Record Count Over Time (Last 365 Days)",
        labels={"record_count": "Record Count", "date": "Date"},
    )
    return


@app.cell
def _(coverage, mo):
    mo.md(f"""
    **Coverage Summary:**
    - Earliest date: {coverage['earliest_date'].iloc[0]}
    - Latest date: {coverage['latest_date'].iloc[0]}
    - Unique dates: {coverage['unique_dates'].iloc[0]:,.0f}
    - Total span: {coverage['days_span'].iloc[0]:,.0f} days

    **Analysis:** [Explain the date coverage. Are there expected gaps? Is the data current?
    Are there any suspicious patterns in the time series?]
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Check 3: Duplicates - Detect Duplicate Records

    Detect duplicate records based on key fields.
    Duplicates can indicate issues with joins or data ingestion.
    """)
    return


@app.cell
def _(mo, pyoso_db_conn):
    # TODO: Replace project_id with your key field
    duplicates = mo.sql(
        f"""
        SELECT
            project_id,
            COUNT(*) as duplicate_count
        FROM oso.projects_v1
        GROUP BY project_id
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC
        LIMIT 20
        """,
        engine=pyoso_db_conn
    )
    return (duplicates,)


@app.cell
def _(duplicates, mo):
    # Create conditional message
    if len(duplicates) > 0:
        duplicates_message = mo.md(f"""
        ⚠️ **Warning:** Found {len(duplicates)} duplicate key values (showing top 20)

        **Analysis:** [Explain why these duplicates might exist. Are they expected?
        Do they indicate a data quality issue?]
        """)
    else:
        duplicates_message = mo.md("✅ **No duplicates found** - All key values are unique")

    duplicates_message    
    return


@app.cell
def _(duplicates, mo):
    # Conditionally display duplicates table
    if len(duplicates) > 0:
        _duplicates_table = mo.ui.table(duplicates)
    else:
        _duplicates_table = None
    _duplicates_table
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Imports
    """)
    return


@app.cell
def _():
    import pandas as pd
    import plotly.express as px
    return pd, px


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import marimo as mo
    from pyoso import Client
    client = Client()
    pyoso_db_conn = client.dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
