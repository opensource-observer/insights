import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Timeseries Metrics

    Pre-aggregated **time series models** for developer activity, commit patterns, and ecosystem growth — built from Open Dev Data's 28-day rolling windows and GitHub Archive's event stream.

    Preview:
    ```sql
    SELECT * FROM oso.stg_opendevdata__eco_mads LIMIT 10
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Overview

    Time series metrics enable temporal analysis of developer activity, ecosystem growth, and contribution patterns. They are pre-aggregated from raw event data at various granularities to support trend analysis, comparisons, and reporting.

    - **Open Dev Data** provides curated 28-day rolling activity metrics with identity resolution (`canonical_developer_id`) and pre-calculated ecosystem MAD (Monthly Active Developer) counts
    - **GitHub Archive** provides raw event-based daily rollups identified by `actor_id`
    - Together they enable both high-fidelity (ODD) and broad-coverage (GHA) temporal analysis

    ### Key Models

    | Model | Source | Grain | Key Metrics |
    |:------|:-------|:------|:------------|
    | `stg_opendevdata__repo_developer_28d_activities` | ODD | day × repo × developer | `num_commits`, `l28_days`, rolling 28-day activity |
    | `stg_opendevdata__eco_mads` | ODD | day × ecosystem | `all_devs`, `full_time_devs` |
    | `int_gharchive__developer_activities` | GHA | day × repo × actor | `num_events` (PushEvent + PullRequestEvent) |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Aggregation Periods

    | Period | Duration | Use Case |
    |:-------|:---------|:---------|
    | **Daily** | 1 day | Anomaly detection, debugging data quality, day-of-week patterns |
    | **7-day (Weekly)** | 7 days | Smooth daily noise, week-over-week comparisons, sprint-level analysis |
    | **28-day** | 28 days | Monthly Active Developers (MAD), consistent month-to-month comparison, Electric Capital methodology |
    | **30-day** | 30 days | Calendar month approximations, financial reporting |

    ### Rolling vs. Point-in-Time

    **Rolling Window**: Each day's value includes activity from the previous N days (overlapping)
    ```
    Day 28: Activity from Day 1-28
    Day 29: Activity from Day 2-29
    Day 30: Activity from Day 3-30
    ```

    **Point-in-Time**: Each period is discrete (non-overlapping)
    ```
    Week 1: Activity from Day 1-7
    Week 2: Activity from Day 8-14
    Week 3: Activity from Day 15-21
    ```

    The ODD models (`repo_developer_28d_activities`, `eco_mads`) use **rolling windows**. For point-in-time, use `DATE_TRUNC` on the raw data.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.mermaid("""
    graph TD
        A[stg_opendevdata__commits<br/>ODD commits with identity resolution] --> B[stg_opendevdata__repo_developer_28d_activities<br/>28-day rolling: day × repo × developer]
        B --> C[stg_opendevdata__eco_mads<br/>Ecosystem MAD counts: day × ecosystem]
        D[int_gharchive__github_events<br/>All GHA events] --> E[int_gharchive__developer_activities<br/>Daily rollup: day × repo × actor]
        E --> F[int_ddp_github_events_daily<br/>Daily aggregated events]
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Key Fields

    ### `stg_opendevdata__repo_developer_28d_activities`

    The primary model for developer-level time series analysis. Each row represents one developer's activity in one repo on one day, within a 28-day rolling window.

    - **`day`**: Date of the observation
    - **`repo_id`**: ODD repository ID
    - **`canonical_developer_id`**: Deduplicated developer identity (handles email aliasing)
    - **`num_commits`**: Commit count in the rolling 28-day window
    - **`l28_days`**: Number of active days in the 28-day window
    - **`original_day`**: The original observation date before windowing

    ### `stg_opendevdata__eco_mads`

    Pre-calculated ecosystem-level MAD counts from ODD.

    - **`day`**: Date of the observation
    - **`ecosystem_id`**: ODD ecosystem ID
    - **`all_devs`**: Count of all active developers in the 28-day window
    - **`full_time_devs`**: Count of developers with >= 10 active days

    ### `int_gharchive__developer_activities`

    Daily developer activity rollup from GitHub Archive (PushEvent + PullRequestEvent).

    - **`bucket_day`**: Date of activity
    - **`actor_id`**: GitHub user ID
    - **`repo_id`**: GitHub repository ID
    - **`num_events`**: Event count for that day/actor/repo
    """)
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview("oso.stg_opendevdata__repo_developer_28d_activities")
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview("oso.stg_opendevdata__eco_mads")
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview("oso.int_gharchive__developer_activities")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Best Practices

    | Goal | Recommended Model | Why? |
    |:------|:-------------------|:------|
    | **Monthly Active Developers (MAD)** | `stg_opendevdata__eco_mads` | Pre-calculated with full-time vs. all-dev breakdown |
    | **Developer-level activity** | `stg_opendevdata__repo_developer_28d_activities` | Identity-resolved, 28-day rolling window |
    | **Custom activity definitions** | `int_gharchive__developer_activities` | Raw daily counts, define your own aggregation |
    | **Trend analysis / dashboards** | `eco_mads` or 28-day rolling | Smooths daily noise, consistent window length |
    | **Anomaly detection** | `int_gharchive__developer_activities` | Daily granularity shows sudden changes |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Live Data Exploration

    The following charts show actual time series data to demonstrate aggregation patterns and ecosystem trends.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("### 28-Day Commit Trends: Ethereum vs Solana")
    return


@app.cell(hide_code=True)
def _(mo, pd, pyoso_db_conn):
    _query = """
    WITH ecosystem_daily_commits AS (
        SELECT
            e.name AS ecosystem,
            rda.day,
            SUM(rda.num_commits) AS daily_commits
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name IN ('Ethereum', 'Solana')
            AND rda.day >= DATE('2024-06-01')
        GROUP BY 1, 2
    )
    SELECT
        ecosystem,
        day,
        daily_commits,
        AVG(daily_commits) OVER (
            PARTITION BY ecosystem
            ORDER BY day
            ROWS BETWEEN 27 PRECEDING AND CURRENT ROW
        ) AS commits_28d_avg
    FROM ecosystem_daily_commits
    WHERE day >= DATE('2024-07-01')
    ORDER BY ecosystem, day
    """

    df_commits = mo.sql(_query, engine=pyoso_db_conn, output=False)
    df_commits['day'] = pd.to_datetime(df_commits['day'])
    return (df_commits,)


@app.cell(hide_code=True)
def _(df_commits, mo, px):
    _eth = df_commits[df_commits['ecosystem'] == 'Ethereum']
    _sol = df_commits[df_commits['ecosystem'] == 'Solana']
    _eth_latest = int(_eth['commits_28d_avg'].iloc[-1]) if len(_eth) > 0 else 0
    _sol_latest = int(_sol['commits_28d_avg'].iloc[-1]) if len(_sol) > 0 else 0
    _eth_peak = int(_eth['commits_28d_avg'].max()) if len(_eth) > 0 else 0

    _fig = px.line(
        df_commits,
        x='day',
        y='commits_28d_avg',
        color='ecosystem',
        labels={'day': '', 'commits_28d_avg': 'Commits (28-day avg)', 'ecosystem': 'Ecosystem'},
        color_discrete_map={'Ethereum': '#4C78A8', 'Solana': '#F58518'}
    )

    _fig.update_traces(line=dict(width=2))

    _fig.update_layout(
        template='plotly_white',
        margin=dict(t=20, l=0, r=0, b=0),
        height=400,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text=''),
        xaxis=dict(
            title='',
            showgrid=False,
            linecolor="#000",
            linewidth=1,
            tickformat="%b %Y"
        ),
        yaxis=dict(
            title='Commits (28-day avg)',
            showgrid=True,
            gridcolor="#E5E5E5",
            linecolor="#000",
            linewidth=1
        )
    )

    mo.vstack([
        mo.hstack([
            mo.stat(label="Ethereum (latest)", value=f"{_eth_latest:,}", bordered=True, caption="28-day avg commits"),
            mo.stat(label="Solana (latest)", value=f"{_sol_latest:,}", bordered=True, caption="28-day avg commits"),
            mo.stat(label="Ethereum Peak", value=f"{_eth_peak:,}", bordered=True, caption="Max 28-day avg"),
        ], widths="equal", gap=1),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("### Aggregation Comparison: Daily vs Weekly vs Monthly (Ethereum)")
    return


@app.cell(hide_code=True)
def _(mo, pd, px, pyoso_db_conn):
    _query = """
    WITH daily AS (
        SELECT
            rda.day,
            COUNT(DISTINCT rda.canonical_developer_id) AS developers
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
            AND rda.day >= DATE('2024-10-01')
            AND rda.day <= DATE('2025-01-15')
        GROUP BY 1
    )
    SELECT
        day,
        developers AS daily_devs,
        AVG(developers) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS weekly_avg,
        AVG(developers) OVER (ORDER BY day ROWS BETWEEN 27 PRECEDING AND CURRENT ROW) AS monthly_avg
    FROM daily
    ORDER BY day
    """

    _df = mo.sql(_query, engine=pyoso_db_conn, output=False)
    _df['day'] = pd.to_datetime(_df['day'])

    _df_melted = _df.melt(
        id_vars=['day'],
        value_vars=['daily_devs', 'weekly_avg', 'monthly_avg'],
        var_name='aggregation',
        value_name='developers'
    )

    _latest_daily = int(_df['daily_devs'].iloc[-1]) if len(_df) > 0 else 0
    _latest_weekly = int(_df['weekly_avg'].iloc[-1]) if len(_df) > 0 else 0
    _latest_monthly = int(_df['monthly_avg'].iloc[-1]) if len(_df) > 0 else 0

    _fig = px.line(
        _df_melted,
        x='day',
        y='developers',
        color='aggregation',
        labels={'day': '', 'developers': 'Developer Count', 'aggregation': 'Period'},
        color_discrete_map={
            'daily_devs': '#72B7B2',
            'weekly_avg': '#F58518',
            'monthly_avg': '#4C78A8'
        }
    )

    _fig.update_traces(line=dict(width=2))

    _fig.update_layout(
        template='plotly_white',
        margin=dict(t=20, l=0, r=0, b=0),
        height=400,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text=''),
        xaxis=dict(
            title='',
            showgrid=False,
            linecolor="#000",
            linewidth=1,
            tickformat="%b %d"
        ),
        yaxis=dict(
            title='Developer Count',
            showgrid=True,
            gridcolor="#E5E5E5",
            linecolor="#000",
            linewidth=1
        )
    )

    mo.vstack([
        mo.hstack([
            mo.stat(label="Daily (latest)", value=f"{_latest_daily:,}", bordered=True, caption="Raw count"),
            mo.stat(label="7-Day Avg", value=f"{_latest_weekly:,}", bordered=True, caption="Smoothed weekly"),
            mo.stat(label="28-Day Avg", value=f"{_latest_monthly:,}", bordered=True, caption="Smoothed monthly"),
        ], widths="equal", gap=1),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("### Interactive Explorer")
    return


@app.cell(hide_code=True)
def _(mo):
    ecosystem_picker = mo.ui.dropdown(
        options=["Ethereum", "Solana", "Optimism", "Arbitrum", "Base", "AI"],
        value="Ethereum",
        label="Ecosystem"
    )
    period_picker = mo.ui.dropdown(
        options=["Daily", "7-day Rolling", "28-day Rolling"],
        value="28-day Rolling",
        label="Aggregation"
    )
    mo.hstack([ecosystem_picker, period_picker], justify="start", gap=2)
    return ecosystem_picker, period_picker


@app.cell(hide_code=True)
def _(ecosystem_picker, mo, pd, period_picker, px, pyoso_db_conn):
    _window = {"Daily": 0, "7-day Rolling": 6, "28-day Rolling": 27}[period_picker.value]

    _query = f"""
    WITH daily AS (
        SELECT
            rda.day,
            COUNT(DISTINCT rda.canonical_developer_id) AS developers,
            SUM(rda.num_commits) AS commits
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{ecosystem_picker.value}'
            AND rda.day >= DATE('2024-06-01')
        GROUP BY 1
    )
    SELECT
        day,
        developers,
        commits,
        AVG(developers) OVER (ORDER BY day ROWS BETWEEN {_window} PRECEDING AND CURRENT ROW) AS developers_smoothed,
        AVG(commits) OVER (ORDER BY day ROWS BETWEEN {_window} PRECEDING AND CURRENT ROW) AS commits_smoothed
    FROM daily
    WHERE day >= DATE('2024-07-01')
    ORDER BY day
    """

    _df = mo.sql(_query, engine=pyoso_db_conn, output=False)
    _df['day'] = pd.to_datetime(_df['day'])

    _latest_devs = int(_df['developers_smoothed'].iloc[-1]) if len(_df) > 0 else 0
    _latest_commits = int(_df['commits_smoothed'].iloc[-1]) if len(_df) > 0 else 0
    _peak_devs = int(_df['developers_smoothed'].max()) if len(_df) > 0 else 0

    _fig = px.line(
        _df,
        x='day',
        y='developers_smoothed',
        labels={'day': '', 'developers_smoothed': 'Developer Count'},
        color_discrete_sequence=['#4C78A8']
    )

    _fig.update_traces(line=dict(width=2))

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
            tickformat="%b %Y"
        ),
        yaxis=dict(
            title='Developer Count',
            showgrid=True,
            gridcolor="#E5E5E5",
            linecolor="#000",
            linewidth=1
        )
    )

    mo.vstack([
        mo.hstack([
            mo.stat(label="Developers (latest)", value=f"{_latest_devs:,}", bordered=True, caption=f"{period_picker.value}"),
            mo.stat(label="Commits (latest)", value=f"{_latest_commits:,}", bordered=True, caption=f"{period_picker.value}"),
            mo.stat(label="Peak Developers", value=f"{_peak_devs:,}", bordered=True, caption="Max in period"),
        ], widths="equal", gap=1),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Queries

    ### 1. Ecosystem MAD Report

    Sample the 28-day MAD count on the last day of each month for trend reporting.

    ```sql
    SELECT
      DATE_TRUNC('month', day) AS report_month,
      MAX(CASE WHEN DAY(day) = 28 THEN all_devs END) AS mad_count,
      MAX(CASE WHEN DAY(day) = 28 THEN full_time_devs END) AS full_time_mad
    FROM oso.stg_opendevdata__eco_mads
    WHERE ecosystem_id IN (
      SELECT id FROM oso.stg_opendevdata__ecosystems WHERE name = 'Ethereum'
    )
    AND day >= DATE('2024-01-01')
    GROUP BY 1
    ORDER BY 1
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          DATE_TRUNC('month', day) AS report_month,
          MAX(CASE WHEN DAY(day) = 28 THEN all_devs END) AS mad_count,
          MAX(CASE WHEN DAY(day) = 28 THEN full_time_devs END) AS full_time_mad
        FROM oso.stg_opendevdata__eco_mads
        WHERE ecosystem_id IN (
          SELECT id FROM oso.stg_opendevdata__ecosystems WHERE name = 'Ethereum'
        )
        AND day >= DATE('2024-01-01')
        GROUP BY 1
        ORDER BY 1
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 2. Week-over-Week Growth

    Calculate weekly growth rates for ecosystem developer counts.

    ```sql
    WITH weekly AS (
        SELECT
            DATE_TRUNC('week', day) AS week,
            AVG(all_devs) AS avg_mad
        FROM oso.stg_opendevdata__eco_mads
        WHERE ecosystem_id IN (
          SELECT id FROM oso.stg_opendevdata__ecosystems WHERE name = 'Ethereum'
        )
        AND day >= DATE('2024-10-01')
        GROUP BY 1
    )
    SELECT
        week,
        CAST(avg_mad AS INTEGER) AS avg_mad,
        CAST(LAG(avg_mad) OVER (ORDER BY week) AS INTEGER) AS prev_week,
        ROUND(100.0 * (avg_mad - LAG(avg_mad) OVER (ORDER BY week)) /
              LAG(avg_mad) OVER (ORDER BY week), 2) AS wow_growth_pct
    FROM weekly
    ORDER BY week DESC
    LIMIT 12
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        WITH weekly AS (
            SELECT
                DATE_TRUNC('week', day) AS week,
                AVG(all_devs) AS avg_mad
            FROM oso.stg_opendevdata__eco_mads
            WHERE ecosystem_id IN (
              SELECT id FROM oso.stg_opendevdata__ecosystems WHERE name = 'Ethereum'
            )
            AND day >= DATE('2024-10-01')
            GROUP BY 1
        )
        SELECT
            week,
            CAST(avg_mad AS INTEGER) AS avg_mad,
            CAST(LAG(avg_mad) OVER (ORDER BY week) AS INTEGER) AS prev_week,
            ROUND(100.0 * (avg_mad - LAG(avg_mad) OVER (ORDER BY week)) /
                  LAG(avg_mad) OVER (ORDER BY week), 2) AS wow_growth_pct
        FROM weekly
        ORDER BY week DESC
        LIMIT 12
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 3. Developer-Level Activity

    Get individual developer activity within an ecosystem over a rolling 28-day window.

    ```sql
    SELECT
      rda.canonical_developer_id,
      rda.day,
      COUNT(DISTINCT rda.repo_id) AS repos_active,
      SUM(rda.num_commits) AS total_commits
    FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
    JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
      ON rda.repo_id = err.repo_id
    JOIN oso.stg_opendevdata__ecosystems AS e
      ON err.ecosystem_id = e.id
    WHERE e.name = 'Ethereum'
      AND rda.day = DATE('2025-01-01')
    GROUP BY 1, 2
    ORDER BY total_commits DESC
    LIMIT 15
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          rda.canonical_developer_id,
          rda.day,
          COUNT(DISTINCT rda.repo_id) AS repos_active,
          SUM(rda.num_commits) AS total_commits
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
          ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON err.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
          AND rda.day = DATE('2025-01-01')
        GROUP BY 1, 2
        ORDER BY total_commits DESC
        LIMIT 15
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 4. Cross-Ecosystem Comparison (GHA)

    Compare daily active developers across ecosystems using GitHub Archive data.

    ```sql
    SELECT
      e.name AS ecosystem_name,
      da.bucket_day,
      COUNT(DISTINCT da.actor_id) AS daily_active_devs,
      SUM(da.num_events) AS total_events
    FROM oso.int_gharchive__developer_activities da
    JOIN oso.int_opendevdata__repositories_with_repo_id r
      ON da.repo_id = r.repo_id
    JOIN oso.stg_opendevdata__ecosystems_repos_recursive err
      ON r.opendevdata_id = err.repo_id
    JOIN oso.stg_opendevdata__ecosystems e
      ON err.ecosystem_id = e.id
    WHERE e.name IN ('Ethereum', 'Solana')
      AND da.bucket_day >= CURRENT_DATE - INTERVAL '7' DAY
    GROUP BY 1, 2
    ORDER BY ecosystem_name, bucket_day
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          e.name AS ecosystem_name,
          da.bucket_day,
          COUNT(DISTINCT da.actor_id) AS daily_active_devs,
          SUM(da.num_events) AS total_events
        FROM oso.int_gharchive__developer_activities da
        JOIN oso.int_opendevdata__repositories_with_repo_id r
          ON da.repo_id = r.repo_id
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive err
          ON r.opendevdata_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems e
          ON err.ecosystem_id = e.id
        WHERE e.name IN ('Ethereum', 'Solana')
          AND da.bucket_day >= CURRENT_DATE - INTERVAL '7' DAY
        GROUP BY 1, 2
        ORDER BY ecosystem_name, bucket_day
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Methodology Notes

    ### Timezone & Calendar
    - All timestamps are UTC; day boundaries at midnight UTC
    - 28-day windows avoid calendar month length variations (28 vs 30 vs 31)
    - Rolling windows overlap: consecutive days share N-1 days of data

    ### Known Limitations
    - **Edge effects**: First N-1 days of a rolling window have incomplete data
    - **Calendar effects**: Weekends and holidays affect daily counts
    - **Data freshness**: GitHub Archive has ~24-48 hour lag; ODD data depends on ingestion schedule
    - **Full-time threshold**: `full_time_devs` uses >= 10 active days in the 28-day window

    ### Rolling vs Calendar Periods

    | Aspect | Rolling Window | Calendar Period |
    |:-------|:---------------|:----------------|
    | Consistency | Same length always | Varies (28-31 days) |
    | Comparability | Any day to any day | Month-to-month only |
    | Smoothness | Continuous | Step changes at period boundaries |
    | Interpretation | "Past N days" | "This month" |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Related Models

    - **Ecosystems**: [ecosystems.py](./ecosystems.py) — Ecosystem definitions and hierarchy
    - **Developers**: [developers.py](./developers.py) — Unified developer identities across ODD and GHA
    - **Commits**: [commits.py](./commits.py) — Unified commit data with ODD enrichment
    - **Events**: [events.py](./events.py) — GitHub Archive event data and daily aggregations
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
