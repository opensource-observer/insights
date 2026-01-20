import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.vstack([
        mo.md(r"""# Time Series Metrics Model"""),
        mo.md(r"""
        This notebook explains how to derive and query time series metrics from event data
        across different aggregation periods.

        **Time series metrics** enable temporal analysis of developer activity, ecosystem growth,
        and contribution patterns. They are aggregated from raw event data at various time granularities
        to support trend analysis, comparisons, and forecasting.
        """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Aggregation Periods""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Available Time Periods

    | Period | Duration | Use Case |
    |--------|----------|----------|
    | **Daily** | 1 day | Fine-grained analysis, anomaly detection |
    | **7-day (Weekly)** | 7 days | Smooth daily noise, weekly patterns |
    | **28-day** | 28 days | Monthly comparisons (consistent window) |
    | **30-day** | 30 days | Approximate calendar month |

    ### When to Use Each Period

    **Daily Metrics**
    - Debugging data quality issues
    - Detecting sudden changes or anomalies
    - Understanding day-of-week patterns
    - Real-time monitoring dashboards

    **7-day (Weekly) Metrics**
    - Smoothing daily volatility
    - Week-over-week comparisons
    - Sprint-level analysis
    - Weekly reports

    **28-day Metrics**
    - Monthly Active Developer (MAD) calculations
    - Consistent month-to-month comparisons
    - Avoids calendar month length variations
    - Standard for Electric Capital methodology

    **30-day Metrics**
    - Calendar month approximations
    - Financial reporting periods
    - Quarterly rollups

    ### Rolling vs. Point-in-Time

    **Rolling Window**: Each day's value includes activity from the previous N days
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
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Entity-Level Metrics""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Aggregation by Entity Type

    Time series metrics can be aggregated at different entity levels:

    | Entity | Granularity | Example Metrics |
    |--------|-------------|-----------------|
    | **Developer** | Individual | Commits/day, Active days/month, Repos contributed |
    | **Repository** | Single repo | Commits/day, Contributors/month, PR velocity |
    | **Project** | Multi-repo group | Total activity, Team size, Growth rate |
    | **Ecosystem** | Cross-project | MAD count, New developers, Retention rate |

    ### Developer → Time Series Metrics

    ```sql
    SELECT
        canonical_developer_id,
        DATE_TRUNC('month', day) AS month,
        COUNT(DISTINCT day) AS active_days,
        SUM(commits) AS total_commits
    FROM stg_opendevdata__repo_developer_28d_activities
    GROUP BY 1, 2
    ```

    ### Repository → Time Series Metrics

    ```sql
    SELECT
        repo_id,
        DATE_TRUNC('month', day) AS month,
        COUNT(DISTINCT canonical_developer_id) AS contributors,
        SUM(commits) AS total_commits
    FROM stg_opendevdata__repo_developer_28d_activities
    GROUP BY 1, 2
    ```

    ### Ecosystem → Time Series Metrics

    ```sql
    SELECT
        e.name AS ecosystem,
        DATE_TRUNC('month', rda.day) AS month,
        COUNT(DISTINCT rda.canonical_developer_id) AS monthly_active_devs
    FROM stg_opendevdata__repo_developer_28d_activities rda
    JOIN stg_opendevdata__ecosystems_repos_recursive err
        ON rda.repo_id = err.repo_id
    JOIN stg_opendevdata__ecosystems e
        ON err.ecosystem_id = e.id
    GROUP BY 1, 2
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Data Models""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Source Event Tables

    | Table | Description | Key Fields |
    |-------|-------------|------------|
    | `stg_opendevdata__repo_developer_28d_activities` | Pre-aggregated 28-day rolling activity | `day`, `repo_id`, `canonical_developer_id`, `commits` |
    | `stg_opendevdata__eco_mads` | Pre-calculated ecosystem MAD counts | `day`, `ecosystem_id`, `all_devs`, `full_time_devs` |
    | `int_gharchive__developer_activities` | Raw GitHub Archive events | `bucket_day`, `repo_id`, `actor_id`, activity counts |

    ### Aggregation Logic

    **From Events to Daily Metrics:**
    ```sql
    -- Count distinct developers active each day
    SELECT
        bucket_day,
        COUNT(DISTINCT actor_id) AS daily_active_developers
    FROM int_gharchive__developer_activities
    GROUP BY bucket_day
    ```

    **From Daily to Rolling 28-day:**
    ```sql
    -- Rolling window aggregation
    SELECT
        d.bucket_day,
        COUNT(DISTINCT e.actor_id) AS mad_28d
    FROM (SELECT DISTINCT bucket_day FROM events) d
    JOIN events e
        ON e.bucket_day BETWEEN d.bucket_day - INTERVAL '27 days' AND d.bucket_day
    GROUP BY d.bucket_day
    ```

    ### Key Fields

    - **day / bucket_day**: The date of the observation
    - **repo_id**: Repository identifier
    - **canonical_developer_id**: Developer fingerprint (Electric Capital)
    - **actor_id**: GitHub user ID (GitHub Archive)
    - **ecosystem_id**: Ecosystem identifier
    - **commits**: Count of commits in the period
    - **all_devs**: Count of all active developers
    - **full_time_devs**: Count of developers with ≥10 active days
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Sample Queries""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Query 1: 28-day Commit Patterns - Ethereum vs Solana""")
    return


@app.cell(hide_code=True)
def _(client, mo, px):
    sql_28d_commits = """
    WITH ecosystem_daily_commits AS (
        SELECT
            e.name AS ecosystem,
            rda.day,
            SUM(rda.commits) AS daily_commits
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
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

    df_commits = client.to_pandas(sql_28d_commits)

    _fig = px.line(
        df_commits,
        x='day',
        y='commits_28d_avg',
        color='ecosystem',
        title='28-day Average Commits: Ethereum vs Solana',
        labels={'day': 'Date', 'commits_28d_avg': 'Commits (28-day avg)', 'ecosystem': 'Ecosystem'},
        color_discrete_map={'Ethereum': '#627EEA', 'Solana': '#9945FF'}
    )
    _fig.update_layout(
        template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    mo.vstack([
        mo.md("""
        **28-day rolling average commits for Ethereum and Solana**

        This smooths daily volatility to show underlying trends in commit activity.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return df_commits, sql_28d_commits


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Query 2: Daily, Weekly, and Monthly Aggregations Compared""")
    return


@app.cell(hide_code=True)
def _(client, mo, pd, px):
    sql_aggregation_comparison = """
    WITH daily AS (
        SELECT
            rda.day,
            COUNT(DISTINCT rda.canonical_developer_id) AS developers
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
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

    df_agg = client.to_pandas(sql_aggregation_comparison)

    # Melt for visualization
    df_melted = df_agg.melt(
        id_vars=['day'],
        value_vars=['daily_devs', 'weekly_avg', 'monthly_avg'],
        var_name='aggregation',
        value_name='developers'
    )

    _fig = px.line(
        df_melted,
        x='day',
        y='developers',
        color='aggregation',
        title='Ethereum Developers: Daily vs Weekly vs Monthly Aggregation',
        labels={'day': 'Date', 'developers': 'Developer Count', 'aggregation': 'Period'},
        color_discrete_map={
            'daily_devs': '#E15759',
            'weekly_avg': '#4C78A8',
            'monthly_avg': '#2E86AB'
        }
    )
    _fig.update_layout(
        template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    mo.vstack([
        mo.md("""
        **Comparison of aggregation periods**

        Shows how different rolling windows smooth the underlying daily data:
        - **Daily**: Raw daily counts (most volatile)
        - **7-day Average**: Smooths weekly patterns
        - **28-day Average**: Shows monthly trend
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return df_agg, df_melted, sql_aggregation_comparison


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Query 3: Pull Request Patterns""")
    return


@app.cell(hide_code=True)
def _(client, mo, px):
    sql_pr_patterns = """
    SELECT
        e.name AS ecosystem,
        DATE_TRUNC('week', da.bucket_day) AS week,
        SUM(da.pull_request_opened_count) AS prs_opened,
        SUM(da.pull_request_merged_count) AS prs_merged
    FROM int_gharchive__developer_activities AS da
    JOIN int_opendevdata__repositories_with_repo_id AS r
        ON da.repo_id = r.repo_id
    JOIN stg_opendevdata__ecosystems_repos_recursive AS err
        ON r.opendevdata_id = err.repo_id
    JOIN stg_opendevdata__ecosystems AS e
        ON err.ecosystem_id = e.id
    WHERE e.name IN ('Ethereum', 'Solana')
        AND da.bucket_day >= DATE('2024-07-01')
    GROUP BY 1, 2
    ORDER BY ecosystem, week
    """

    df_prs = client.to_pandas(sql_pr_patterns)

    _fig = px.line(
        df_prs,
        x='week',
        y='prs_merged',
        color='ecosystem',
        title='Weekly Merged Pull Requests: Ethereum vs Solana',
        labels={'week': 'Week', 'prs_merged': 'PRs Merged', 'ecosystem': 'Ecosystem'},
        color_discrete_map={'Ethereum': '#627EEA', 'Solana': '#9945FF'}
    )
    _fig.update_layout(
        template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    mo.vstack([
        mo.md("""
        **Weekly pull request activity**

        Aggregated at weekly granularity to show PR workflow patterns.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return df_prs, sql_pr_patterns


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Query 4: Ecosystem Selector with Time Period""")
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
def _(client, ecosystem_picker, mo, period_picker, px):
    window_size = {"Daily": 0, "7-day Rolling": 6, "28-day Rolling": 27}[period_picker.value]

    sql_custom = f"""
    WITH daily AS (
        SELECT
            rda.day,
            COUNT(DISTINCT rda.canonical_developer_id) AS developers,
            SUM(rda.commits) AS commits
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{ecosystem_picker.value}'
            AND rda.day >= DATE('2024-06-01')
        GROUP BY 1
    )

    SELECT
        day,
        developers,
        commits,
        AVG(developers) OVER (ORDER BY day ROWS BETWEEN {window_size} PRECEDING AND CURRENT ROW) AS developers_smoothed,
        AVG(commits) OVER (ORDER BY day ROWS BETWEEN {window_size} PRECEDING AND CURRENT ROW) AS commits_smoothed
    FROM daily
    WHERE day >= DATE('2024-07-01')
    ORDER BY day
    """

    df_custom = client.to_pandas(sql_custom)

    _fig = px.line(
        df_custom,
        x='day',
        y='developers_smoothed',
        title=f'{ecosystem_picker.value} Developers ({period_picker.value})',
        labels={'day': 'Date', 'developers_smoothed': 'Developer Count'}
    )
    _fig.update_layout(template='plotly_white')
    _fig.update_traces(line=dict(color='#2E86AB', width=2))

    mo.vstack([
        mo.md(f"""
        **{ecosystem_picker.value} developer activity with {period_picker.value} aggregation**
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
        mo.ui.table(df_custom.tail(14), selection=None)
    ])
    return df_custom, sql_custom, window_size


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Example Use Cases""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Use Case 1: Monthly Report Generation

    Generate consistent monthly metrics using 28-day rolling windows:

    ```sql
    -- Monthly MAD report (sample last day of each month)
    SELECT
        DATE_TRUNC('month', day) AS report_month,
        MAX(CASE WHEN DAY(day) = 28 THEN all_devs END) AS mad_count
    FROM stg_opendevdata__eco_mads
    WHERE ecosystem_id = 'ethereum'
    GROUP BY 1
    ORDER BY 1
    ```

    ### Use Case 2: Week-over-Week Growth

    Calculate weekly growth rates:

    ```sql
    WITH weekly AS (
        SELECT
            DATE_TRUNC('week', day) AS week,
            AVG(all_devs) AS avg_mad
        FROM stg_opendevdata__eco_mads
        WHERE ecosystem_id = 'ethereum'
        GROUP BY 1
    )
    SELECT
        week,
        avg_mad,
        LAG(avg_mad) OVER (ORDER BY week) AS prev_week,
        ROUND(100.0 * (avg_mad - LAG(avg_mad) OVER (ORDER BY week)) /
              LAG(avg_mad) OVER (ORDER BY week), 2) AS wow_growth_pct
    FROM weekly
    ORDER BY week DESC
    LIMIT 12
    ```

    ### Use Case 3: Anomaly Detection

    Identify days with unusual activity:

    ```sql
    WITH stats AS (
        SELECT
            AVG(all_devs) AS mean_mad,
            STDDEV(all_devs) AS std_mad
        FROM stg_opendevdata__eco_mads
        WHERE ecosystem_id = 'ethereum'
            AND day >= CURRENT_DATE - INTERVAL '90 days'
    )
    SELECT day, all_devs
    FROM stg_opendevdata__eco_mads, stats
    WHERE ecosystem_id = 'ethereum'
        AND ABS(all_devs - mean_mad) > 2 * std_mad
    ORDER BY day DESC
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Methodology Notes""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Time Zone Considerations

    - All timestamps are stored in UTC
    - Day boundaries are at midnight UTC
    - For timezone-specific analysis, convert at query time

    ### Aggregation Best Practices

    | Scenario | Recommended Aggregation |
    |----------|------------------------|
    | Executive dashboards | 28-day or 30-day |
    | Operational monitoring | Daily with 7-day overlay |
    | Trend analysis | 28-day rolling |
    | Anomaly detection | Daily |
    | Year-over-year comparison | Calendar month or 30-day |

    ### Known Limitations

    1. **Rolling windows overlap**: 28-day rolling metrics for consecutive days share 27 days of data
    2. **Edge effects**: First N-1 days of a rolling window have incomplete data
    3. **Calendar effects**: Weekends and holidays affect daily counts
    4. **Data freshness**: GitHub Archive has ~24-48 hour lag

    ### Comparison: Rolling vs Calendar Periods

    | Aspect | Rolling Window | Calendar Period |
    |--------|----------------|-----------------|
    | Consistency | Same length always | Varies (28-31 days) |
    | Comparability | Any day can compare to any day | Month-to-month only |
    | Smoothness | Continuous | Step changes |
    | Interpretation | "Past N days" | "This month" |
    """)
    return


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.express as px
    return pd, px


@app.cell(hide_code=True)
def setup_pyoso():
    import pyoso
    import marimo as mo
    import os
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    client = pyoso.Client(os.getenv("OSO_API_KEY"))
    return client, mo, os, pyoso_db_conn


if __name__ == "__main__":
    app.run()
