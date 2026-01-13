import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.vstack([
        mo.md(r"""# Activity Metric Definition"""),
        mo.md(r"""
        This notebook validates the Monthly Active Developer (MAD) metric by comparing four different data sources:

        1. **Open Dev Data (Electric Capital)**: Pre-calculated ecosystem metrics using **rolling 28-day windows**
        2. **GitHub Archive**: Raw event data calculated from individual developer activities using **rolling 28-day windows**
        3. **Mapped Open Dev Data**: Open Dev Data filtered to only repositories with valid OSO `repo_id` mapping
        4. **Mapped GitHub Archive**: GitHub Archive filtered to only repositories with valid OSO `repo_id` mapping

        The goal is to understand any differences in methodology and ensure consistency across data sources.
        """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Data Source 1: Open Dev Data""")
    return


@app.cell(hide_code=True)
def _(client, mo):
    sql_opendevdata = """
    SELECT
        mads.day,
        mads.all_devs
    FROM stg_opendevdata__eco_mads AS mads
    JOIN stg_opendevdata__ecosystems AS e
        ON mads.ecosystem_id = e.id
    WHERE
        e.name = 'Ethereum'
        AND mads.day >= DATE('2025-01-01')
    ORDER BY 1
    """

    df_opendevdata = client.to_pandas(sql_opendevdata)

    mo.vstack([
        mo.md(f"""
        **Source**: Electric Capital Developer Report
        **Method**: Rolling 28-day window (pre-calculated)
        **Rows Retrieved**: {len(df_opendevdata):,}
        **Date Range**: {df_opendevdata['day'].min()} to {df_opendevdata['day'].max()}
        """),
        mo.ui.table(df_opendevdata, selection=None, pagination=True)
    ])
    return df_opendevdata, sql_opendevdata


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Data Source 2: GitHub Archive""")
    return


@app.cell(hide_code=True)
def _(client, mo):
    sql_gharchive = """
    WITH base AS (
        SELECT DISTINCT
            da.bucket_day,
            da.actor_id
        FROM int_gharchive__developer_activities AS da
        JOIN int_opendevdata__repositories_with_repo_id AS r
            ON da.repo_id = r.repo_id
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON r.opendevdata_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE
            da.bucket_day >= DATE('2024-12-01')
            AND e.name = 'Ethereum'
    ),

    rolling_28d AS (
        SELECT
            d.bucket_day,
            COUNT(DISTINCT w.actor_id) AS all_devs
        FROM (
            SELECT DISTINCT bucket_day FROM base
        ) d
        JOIN base w
            ON w.bucket_day BETWEEN d.bucket_day - INTERVAL '27' DAY AND d.bucket_day
        GROUP BY 1
    )

    SELECT
        bucket_day AS day,
        all_devs
    FROM rolling_28d
    WHERE bucket_day >= DATE('2025-01-01')
    ORDER BY bucket_day
    """

    df_gharchive = client.to_pandas(sql_gharchive)

    mo.vstack([
        mo.md(f"""
        **Source**: GitHub Archive (OSO Data Lake)
        **Method**: Rolling 28-day window (calculated in query)
        **Rows Retrieved**: {len(df_gharchive):,}
        **Date Range**: {df_gharchive['day'].min()} to {df_gharchive['day'].max()}
        """),
        mo.ui.table(df_gharchive, selection=None, pagination=True)
    ])
    return df_gharchive, sql_gharchive


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Data Source 3: Mapped Open Dev Data""")
    return


@app.cell(hide_code=True)
def _(client, mo):
    sql_opendevdata_mapped = """
    WITH mapped_ethereum_repos AS (
        SELECT DISTINCT
            r.opendevdata_id,
            r.repo_id
        FROM int_opendevdata__repositories_with_repo_id AS r
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON r.opendevdata_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
            AND r.repo_id IS NOT NULL
    )
    SELECT
        rda.day,
        COUNT(DISTINCT rda.canonical_developer_id) AS all_devs
    FROM stg_opendevdata__repo_developer_28d_activities AS rda
    JOIN mapped_ethereum_repos AS mer
        ON rda.repo_id = mer.opendevdata_id
    WHERE rda.day >= DATE('2025-01-01')
    GROUP BY 1
    ORDER BY 1
    """

    df_opendevdata_mapped = client.to_pandas(sql_opendevdata_mapped)

    mo.vstack([
        mo.md(f"""
- **Source**: Electric Capital Developer Report (Mapped Repos Only)
- **Method**: Rolling 28-day window from `stg_opendevdata__repo_developer_28d_activities`
- **Filter**: Only repositories with valid OSO `repo_id` mapping
- **Rows Retrieved**: {len(df_opendevdata_mapped):,}
- **Date Range**: {df_opendevdata_mapped['day'].min()} to {df_opendevdata_mapped['day'].max()}
        """),
        mo.ui.table(df_opendevdata_mapped, selection=None, pagination=True)
    ])
    return df_opendevdata_mapped, sql_opendevdata_mapped


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Data Source 4: Mapped GitHub Archive""")
    return


@app.cell(hide_code=True)
def _(client, mo):
    sql_gharchive_mapped = """
    WITH mapped_ethereum_repos AS (
        SELECT DISTINCT
            r.opendevdata_id,
            r.repo_id
        FROM int_opendevdata__repositories_with_repo_id AS r
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON r.opendevdata_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
            AND r.repo_id IS NOT NULL
    ),
    base AS (
        SELECT DISTINCT
            da.bucket_day,
            da.actor_id
        FROM int_gharchive__developer_activities AS da
        JOIN mapped_ethereum_repos AS mer
            ON da.repo_id = mer.repo_id
        WHERE da.bucket_day >= DATE('2024-12-01')
    ),
    rolling_28d AS (
        SELECT
            d.bucket_day,
            COUNT(DISTINCT w.actor_id) AS all_devs
        FROM (
            SELECT DISTINCT bucket_day FROM base
        ) d
        JOIN base w
            ON w.bucket_day BETWEEN d.bucket_day - INTERVAL '27' DAY AND d.bucket_day
        GROUP BY 1
    )
    SELECT
        bucket_day AS day,
        all_devs
    FROM rolling_28d
    WHERE bucket_day >= DATE('2025-01-01')
    ORDER BY bucket_day
    """

    df_gharchive_mapped = client.to_pandas(sql_gharchive_mapped)

    mo.vstack([
        mo.md(f"""
- **Source**: GitHub Archive (OSO Data Lake, Mapped Repos Only)
- **Method**: Rolling 28-day window (calculated in query)
- **Filter**: Only repositories with valid OSO `repo_id` mapping (same set as Data Source 3)
- **Rows Retrieved**: {len(df_gharchive_mapped):,}
- **Date Range**: {df_gharchive_mapped['day'].min()} to {df_gharchive_mapped['day'].max()}
        """),
        mo.ui.table(df_gharchive_mapped, selection=None, pagination=True)
    ])
    return df_gharchive_mapped, sql_gharchive_mapped


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Comparative Analysis""")
    return


@app.cell(hide_code=True)
def _(df_gharchive, df_gharchive_mapped, df_opendevdata, df_opendevdata_mapped, mo, pd, px):
    _df1 = df_opendevdata.copy()
    _df2 = df_gharchive.copy()
    _df3 = df_opendevdata_mapped.copy()
    _df4 = df_gharchive_mapped.copy()
    _df1['source'] = 'Open Dev Data'
    _df2['source'] = 'GitHub Archive'
    _df3['source'] = 'Mapped Open Dev Data'
    _df4['source'] = 'Mapped GitHub Archive'

    _df_combined = pd.concat([_df1, _df2, _df3, _df4], axis=0)

    _fig = px.line(
        data_frame=_df_combined,
        x='day',
        y='all_devs',
        color='source',
        color_discrete_map={
            'Open Dev Data': '#4C78A8',
            'GitHub Archive': '#E15759',
            'Mapped Open Dev Data': '#2E86AB',
            'Mapped GitHub Archive': '#A23B72'
        }
    )

    _fig.update_layout(
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text=''
        ),
        margin=dict(t=40, l=0, r=0, b=0),
        hovermode='x unified'
    )
    _fig.update_xaxes(
        title='',
        showgrid=False,
        linecolor="#000",
        linewidth=1,
        ticks="outside",
        tickformat="%b %d, %Y"
    )
    _fig.update_yaxes(
        title="Monthly Active Developers",
        showgrid=True,
        gridcolor="#DDD",
        zeroline=True,
        zerolinecolor="black",
        zerolinewidth=1,
        linecolor="#000",
        linewidth=1,
        ticks="outside"
    )
    _fig.update_traces(line=dict(width=3))

    mo.vstack([
        mo.md("### Monthly Active Developers: All Data Sources Comparison"),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(df_gharchive, df_gharchive_mapped, df_opendevdata, df_opendevdata_mapped, mo, pd):
    _merged = df_opendevdata.copy()
    _merged = pd.merge(_merged, df_gharchive, on='day', how='inner', suffixes=('_opendev', '_gharchive'))
    _merged = pd.merge(_merged, df_opendevdata_mapped[['day', 'all_devs']], on='day', how='inner')
    _merged = _merged.rename(columns={'all_devs': 'all_devs_opendev_mapped'})
    _merged = pd.merge(_merged, df_gharchive_mapped[['day', 'all_devs']], on='day', how='inner')
    _merged = _merged.rename(columns={'all_devs': 'all_devs_gharchive_mapped'})

    _merged['diff_raw'] = _merged['all_devs_gharchive'] - _merged['all_devs_opendev']
    _merged['pct_diff_raw'] = (_merged['diff_raw'] / _merged['all_devs_opendev'] * 100).round(2)
    _merged['diff_mapped'] = _merged['all_devs_gharchive_mapped'] - _merged['all_devs_opendev_mapped']
    _merged['pct_diff_mapped'] = (_merged['diff_mapped'] / _merged['all_devs_opendev_mapped'] * 100).round(2)

    _avg_opendev = _merged['all_devs_opendev'].mean()
    _avg_gharchive = _merged['all_devs_gharchive'].mean()
    _avg_opendev_mapped = _merged['all_devs_opendev_mapped'].mean()
    _avg_gharchive_mapped = _merged['all_devs_gharchive_mapped'].mean()

    mo.vstack([
        mo.md("### Statistical Summary"),
        mo.md(f"""
| Data Source | Average MAD | Min MAD | Max MAD |
|-------------|-------------|---------|---------|
| Open Dev Data | {_avg_opendev:,.0f} | {_merged['all_devs_opendev'].min():,.0f} | {_merged['all_devs_opendev'].max():,.0f} |
| GitHub Archive | {_avg_gharchive:,.0f} | {_merged['all_devs_gharchive'].min():,.0f} | {_merged['all_devs_gharchive'].max():,.0f} |
| Mapped Open Dev Data | {_avg_opendev_mapped:,.0f} | {_merged['all_devs_opendev_mapped'].min():,.0f} | {_merged['all_devs_opendev_mapped'].max():,.0f} |
| Mapped GitHub Archive | {_avg_gharchive_mapped:,.0f} | {_merged['all_devs_gharchive_mapped'].min():,.0f} | {_merged['all_devs_gharchive_mapped'].max():,.0f} |
        """),
        mo.md("**Pairwise Differences:**"),
        mo.md(f"""
| Comparison | Avg Difference |
|------------|----------------|
| GitHub Archive vs Open Dev Data | {(_avg_gharchive - _avg_opendev):+,.0f} ({((_avg_gharchive - _avg_opendev) / _avg_opendev * 100):+.2f}%) |
| Mapped GH Archive vs Mapped Open Dev Data | {(_avg_gharchive_mapped - _avg_opendev_mapped):+,.0f} ({((_avg_gharchive_mapped - _avg_opendev_mapped) / _avg_opendev_mapped * 100):+.2f}%) |
        """),
        mo.md("### Day-by-Day Comparison"),
        mo.ui.table(_merged[['day', 'all_devs_opendev', 'all_devs_gharchive', 'all_devs_opendev_mapped', 'all_devs_gharchive_mapped']],
                   selection=None,
                   pagination=True)
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Methodology Notes

    ### Open Dev Data (Electric Capital)

    Per the [Electric Capital methodology](https://www.developerreport.com/about):

    - **Time Window**: Rolling 28-day window (not calendar month)
    - **Developer Classification**:
      - **Full-Time**: ≥10 active days in the rolling 28-day window
      - **Part-Time**: <10 active days in the rolling 28-day window
      - **One-Time**: Minimal/sporadic activity (tracked via 84-day rolling window)
    - **Identity Resolution**: Developers are "fingerprinted" to deduplicate across multiple accounts/emails
    - **Code Filtering**: Commits from forks and copy-pasted code are filtered out
    - **Platform Coverage**: Primarily GitHub, but may include other code hosting platforms

    ### GitHub Archive (OSO)

    - **Time Window**: Rolling 28-day window (calculated in query using `BETWEEN d.bucket_day - INTERVAL '27' DAY AND d.bucket_day`)
    - **Platform**: GitHub only (via GitHub Archive)
    - **Activity Types**: Push events (commits) and pull request events from `int_gharchive__developer_activities`
    - **Identity**: Based on GitHub `actor_id` (no cross-email deduplication)

    ### Key Differences Explaining Variance

    | Factor | Open Dev Data | GitHub Archive |
    |--------|---------------|----------------|
    | **Identity Resolution** | Cross-email fingerprinting | Single GitHub actor_id |
    | **Code Filtering** | Excludes forks/copied code | Includes all commits |
    | **Platform Coverage** | Multi-platform possible | GitHub only |
    | **Time Window** | Rolling 28-day | Rolling 28-day |

    Both sources use **rolling 28-day windows** for MAD calculation. Differences in developer counts are primarily due to identity resolution and code filtering approaches.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Known GitHub Archive Data Limitations

    Beyond methodology differences, there are known data quality issues with GitHub Archive that contribute to undercounting:

    ### 1. Missing Events in GitHub Archive

    GitHub Archive has reported incidents of missing data:

    - [gharchive.org#245](https://github.com/igrigorik/gharchive.org/issues/245): Reports of missing events during certain time periods
    - [gharchive.org#310](https://github.com/igrigorik/gharchive.org/issues/310): Additional reports of data gaps in the archive

    These gaps mean some developer activity is simply not captured in the archive, leading to undercounting.

    ### 2. PushEvent Commit Truncation

    GitHub's Events API (which feeds GitHub Archive) **caps PushEvent payloads at 20 commits**. When a developer pushes more than 20 commits at once:

    - Only the first 20 commits are included in the event payload
    - Additional commits are silently dropped
    - The `distinct_size` field indicates the actual count, but individual commit data is lost

    **Impact**: Developers who batch large commits (common in squash-merge workflows or initial project imports) may have their activity undercounted. This primarily affects commit-based metrics rather than unique developer counts, but can still influence activity day calculations.

    ### Summary of Data Quality Factors

    | Factor | Impact on Developer Count |
    |--------|---------------------------|
    | Missing events (data gaps) | Direct undercounting of active developers |
    | PushEvent 20-commit cap | May miss activity days for batch committers |
    | Repository mapping gaps | Developers on unmapped repos not counted |
    | Identity resolution | GH Archive counts by actor_id, may overcount |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Impact Analysis: PushEvent Commit Truncation""")
    return


@app.cell(hide_code=True)
def _(client, mo):
    sql_commit_truncation_impact = """
    WITH push_events_stats AS (
        SELECT
            DATE_TRUNC('month', created_at) AS month,
            COUNT(*) AS total_push_events,
            SUM(CASE WHEN actual_commits_count > 20 THEN 1 ELSE 0 END) AS truncated_events,
            SUM(available_commits_count) AS available_commits,
            SUM(actual_commits_count) AS actual_commits,
            SUM(actual_commits_count - available_commits_count) AS missing_commits
        FROM stg_github__push_events
        WHERE created_at >= DATE('2025-01-01')
            AND actual_commits_count IS NOT NULL
        GROUP BY 1
    )
    SELECT
        month,
        total_push_events,
        truncated_events,
        ROUND(100.0 * truncated_events / total_push_events, 2) AS pct_truncated,
        available_commits,
        actual_commits,
        missing_commits,
        ROUND(100.0 * missing_commits / actual_commits, 2) AS pct_commits_missing
    FROM push_events_stats
    ORDER BY month
    """

    df_truncation = client.to_pandas(sql_commit_truncation_impact)

    total_events = df_truncation['total_push_events'].sum()
    total_truncated = df_truncation['truncated_events'].sum()
    total_available = df_truncation['available_commits'].sum()
    total_actual = df_truncation['actual_commits'].sum()
    total_missing = df_truncation['missing_commits'].sum()

    mo.vstack([
        mo.md(f"""
This query analyzes the impact of GitHub's 20-commit cap on PushEvent payloads using
`stg_github__push_events`, which contains both `available_commits_count` (capped at 20)
and `actual_commits_count` (the real `distinct_size` value).

**Overall Impact (since 2025-01-01):**

| Metric | Value |
|--------|-------|
| Total Push Events | {total_events:,} |
| Events with >20 commits (truncated) | {total_truncated:,} ({100.0 * total_truncated / total_events:.2f}%) |
| Commits in payload | {total_available:,} |
| Actual commits (distinct_size) | {total_actual:,} |
| **Missing commits** | **{total_missing:,}** ({100.0 * total_missing / total_actual:.2f}%) |
        """),
        mo.ui.table(df_truncation, selection=None, pagination=True)
    ])
    return df_truncation, sql_commit_truncation_impact


@app.cell(hide_code=True)
def _(client, mo):
    sql_truncation_by_size = """
    SELECT
        CASE
            WHEN actual_commits_count <= 20 THEN '1-20 (no truncation)'
            WHEN actual_commits_count <= 50 THEN '21-50'
            WHEN actual_commits_count <= 100 THEN '51-100'
            WHEN actual_commits_count <= 500 THEN '101-500'
            ELSE '500+'
        END AS commit_range,
        COUNT(*) AS push_event_count,
        SUM(available_commits_count) AS available_commits,
        SUM(actual_commits_count) AS actual_commits,
        SUM(actual_commits_count - available_commits_count) AS missing_commits
    FROM stg_github__push_events
    WHERE created_at >= DATE('2025-01-01')
        AND actual_commits_count IS NOT NULL
    GROUP BY 1
    ORDER BY
        CASE
            WHEN actual_commits_count <= 20 THEN 1
            WHEN actual_commits_count <= 50 THEN 2
            WHEN actual_commits_count <= 100 THEN 3
            WHEN actual_commits_count <= 500 THEN 4
            ELSE 5
        END
    """

    df_by_size = client.to_pandas(sql_truncation_by_size)

    mo.vstack([
        mo.md("""
**Distribution by Push Size:**

This shows how many push events fall into each size bucket and the corresponding commit loss.
        """),
        mo.ui.table(df_by_size, selection=None)
    ])
    return df_by_size, sql_truncation_by_size


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
    return client, mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
