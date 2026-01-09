import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.vstack([
        mo.md(r"""# Activity Metric Definition"""),
        mo.md(r"""
        This notebook validates the Monthly Active Developer (MAD) metric by comparing two different data sources:

        1. **Open Dev Data (Electric Capital)**: Pre-calculated ecosystem metrics using **rolling 28-day windows**
        2. **GitHub Archive**: Raw event data calculated from individual developer activities using **rolling 28-day windows**

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
    mo.md(r"""## Comparative Analysis""")
    return


@app.cell(hide_code=True)
def _(df_gharchive, df_opendevdata, mo, pd, px):
    _df1 = df_opendevdata.copy()
    _df2 = df_gharchive.copy()
    _df1['source'] = 'Open Dev Data'
    _df2['source'] = 'GitHub Archive'

    _df_combined = pd.concat([_df1, _df2], axis=0)

    _fig = px.line(
        data_frame=_df_combined,
        x='day',
        y='all_devs',
        color='source',
        color_discrete_map={
            'Open Dev Data': '#4C78A8',
            'GitHub Archive': '#E15759'
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
        mo.md("### Monthly Active Developers: Data Source Comparison"),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(df_gharchive, df_opendevdata, mo, pd):
    _merged = pd.merge(
        df_opendevdata,
        df_gharchive,
        on='day',
        how='inner',
        suffixes=('_opendev', '_gharchive')
    )

    _merged['difference'] = _merged['all_devs_gharchive'] - _merged['all_devs_opendev']
    _merged['pct_difference'] = (_merged['difference'] / _merged['all_devs_opendev'] * 100).round(2)

    _avg_opendev = _merged['all_devs_opendev'].mean()
    _avg_gharchive = _merged['all_devs_gharchive'].mean()
    _avg_diff = _merged['difference'].mean()
    _avg_pct_diff = _merged['pct_difference'].mean()

    mo.vstack([
        mo.md("### Statistical Summary"),
        mo.md(f"""
        | Metric | Open Dev Data | GitHub Archive | Difference |
        |--------|---------------|----------------|------------|
        | Average MAD | {_avg_opendev:,.0f} | {_avg_gharchive:,.0f} | {_avg_diff:+,.0f} ({_avg_pct_diff:+.2f}%) |
        | Min MAD | {_merged['all_devs_opendev'].min():,.0f} | {_merged['all_devs_gharchive'].min():,.0f} | - |
        | Max MAD | {_merged['all_devs_opendev'].max():,.0f} | {_merged['all_devs_gharchive'].max():,.0f} | - |
        """),
        mo.md("### Day-by-Day Comparison"),
        mo.ui.table(_merged[['day', 'all_devs_opendev', 'all_devs_gharchive', 'difference', 'pct_difference']],
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
    - **Activity Types**: Commits, pull requests, issues, and code reviews from `int_gharchive__developer_activities`
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
    mo.md(r"""## Discrepancy Diagnostics""")
    return


@app.cell(hide_code=True)
def _(client, mo):
    sql_repo_mapping_stats = """
    WITH ethereum_repos AS (
        SELECT DISTINCT err.repo_id AS opendevdata_repo_id
        FROM stg_opendevdata__ecosystems_repos_recursive AS err
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
    ),
    mapping_status AS (
        SELECT
            r.opendevdata_id,
            r.repo_name,
            r.repo_id,
            r.repo_id_source,
            CASE
                WHEN r.repo_id IS NOT NULL THEN 'mapped'
                ELSE 'unmapped'
            END AS mapping_status
        FROM int_opendevdata__repositories_with_repo_id AS r
        JOIN ethereum_repos AS er
            ON r.opendevdata_id = er.opendevdata_repo_id
    )
    SELECT
        mapping_status,
        repo_id_source,
        COUNT(*) AS repo_count
    FROM mapping_status
    GROUP BY 1, 2
    ORDER BY 1, 2
    """

    df_repo_mapping = client.to_pandas(sql_repo_mapping_stats)

    total_repos = df_repo_mapping['repo_count'].sum()
    mapped_repos = df_repo_mapping[df_repo_mapping['mapping_status'] == 'mapped']['repo_count'].sum()
    unmapped_repos = df_repo_mapping[df_repo_mapping['mapping_status'] == 'unmapped']['repo_count'].sum()
    mapping_rate = (mapped_repos / total_repos * 100) if total_repos > 0 else 0

    mo.vstack([
        mo.md("### Diagnostic 1: Repository Mapping Coverage"),
        mo.md(f"""
        This query checks how many Ethereum ecosystem repositories from OpenDevData
        can be matched to an OSO `repo_id` (required for GitHub Archive event lookup).

        | Metric | Value |
        |--------|-------|
        | Total Ethereum Repos (OpenDevData) | {total_repos:,} |
        | Successfully Mapped to OSO repo_id | {mapped_repos:,} |
        | **Unmapped (Missing from GH Archive query)** | **{unmapped_repos:,}** |
        | Mapping Rate | {mapping_rate:.1f}% |

        **Impact**: Unmapped repositories are excluded from the GitHub Archive developer count,
        which directly causes undercounting.
        """),
        mo.ui.table(df_repo_mapping, selection=None)
    ])
    return df_repo_mapping, sql_repo_mapping_stats


@app.cell(hide_code=True)
def _(client, mo):
    sql_unmapped_repos_sample = """
    WITH ethereum_repos AS (
        SELECT DISTINCT err.repo_id AS opendevdata_repo_id
        FROM stg_opendevdata__ecosystems_repos_recursive AS err
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
    )
    SELECT
        r.opendevdata_id,
        r.repo_name,
        r.github_graphql_id,
        r.star_count,
        r.repo_id_source
    FROM int_opendevdata__repositories_with_repo_id AS r
    JOIN ethereum_repos AS er
        ON r.opendevdata_id = er.opendevdata_repo_id
    WHERE r.repo_id IS NULL
    ORDER BY r.star_count DESC NULLS LAST
    LIMIT 50
    """

    df_unmapped = client.to_pandas(sql_unmapped_repos_sample)

    mo.vstack([
        mo.md("### Diagnostic 2: Sample of Unmapped Repositories"),
        mo.md("""
        These are the top 50 unmapped repositories by star count. These repos exist in
        OpenDevData's Ethereum ecosystem but have no matching `repo_id` in OSO, meaning
        their developers are **not counted** in the GitHub Archive metric.

        Common causes:
        - Missing `github_graphql_id` in OpenDevData
        - Repository renamed (name mismatch between OpenDevData and GitHub Archive)
        - Repository not yet indexed by OSO
        """),
        mo.ui.table(df_unmapped, selection=None, pagination=True)
    ])
    return df_unmapped, sql_unmapped_repos_sample


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Controlled Comparison: Same Repository Set""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    To isolate repository mapping as a factor, we compare developer counts using **only repositories
    that exist in both data sources** (i.e., mapped repositories with valid `repo_id`).

    This controls for the repository coverage difference and reveals any remaining methodology gaps.
    """)
    return


@app.cell(hide_code=True)
def _(client, mo):
    sql_opendevdata_mapped_only = """
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

    df_opendevdata_mapped = client.to_pandas(sql_opendevdata_mapped_only)

    mo.vstack([
        mo.md("### Open Dev Data (Mapped Repos Only)"),
        mo.md(f"""
        **Source**: Electric Capital Developer Report
        **Filter**: Only repositories with valid OSO `repo_id` mapping
        **Method**: Rolling 28-day window from `stg_opendevdata__repo_developer_28d_activities`
        **Rows Retrieved**: {len(df_opendevdata_mapped):,}
        **Date Range**: {df_opendevdata_mapped['day'].min()} to {df_opendevdata_mapped['day'].max()}
        """),
        mo.ui.table(df_opendevdata_mapped, selection=None, pagination=True)
    ])
    return df_opendevdata_mapped, sql_opendevdata_mapped_only


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
        mo.md("### GitHub Archive (Mapped Repos Only)"),
        mo.md(f"""
        **Source**: GitHub Archive (OSO Data Lake)
        **Filter**: Only repositories with valid OSO `repo_id` mapping (same set as above)
        **Method**: Rolling 28-day window
        **Rows Retrieved**: {len(df_gharchive_mapped):,}
        **Date Range**: {df_gharchive_mapped['day'].min()} to {df_gharchive_mapped['day'].max()}
        """),
        mo.ui.table(df_gharchive_mapped, selection=None, pagination=True)
    ])
    return df_gharchive_mapped, sql_gharchive_mapped


@app.cell(hide_code=True)
def _(df_gharchive_mapped, df_opendevdata, df_opendevdata_mapped, mo, pd, px):
    _df1 = df_opendevdata_mapped.copy()
    _df2 = df_gharchive_mapped.copy()
    _df3 = df_opendevdata.copy()
    _df1['source'] = 'Open Dev Data (Mapped)'
    _df2['source'] = 'GitHub Archive (Mapped)'
    _df3['source'] = 'Open Dev Data (Total)'

    _df_combined = pd.concat([_df1, _df2, _df3], axis=0)

    _fig = px.line(
        data_frame=_df_combined,
        x='day',
        y='all_devs',
        color='source',
        color_discrete_map={
            'Open Dev Data (Mapped)': '#2E86AB',
            'GitHub Archive (Mapped)': '#A23B72',
            'Open Dev Data (Total)': '#4C78A8'
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
        mo.md("### Controlled Comparison: Same Repository Set"),
        mo.md("Includes **Open Dev Data (Total)** to illustrate the impact of unmapped repositories."),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(df_gharchive_mapped, df_opendevdata_mapped, mo, pd):
    _merged = pd.merge(
        df_opendevdata_mapped,
        df_gharchive_mapped,
        on='day',
        how='inner',
        suffixes=('_opendev', '_gharchive')
    )

    _merged['difference'] = _merged['all_devs_gharchive'] - _merged['all_devs_opendev']
    _merged['pct_difference'] = (_merged['difference'] / _merged['all_devs_opendev'] * 100).round(2)

    _avg_opendev = _merged['all_devs_opendev'].mean()
    _avg_gharchive = _merged['all_devs_gharchive'].mean()
    _avg_diff = _merged['difference'].mean()
    _avg_pct_diff = _merged['pct_difference'].mean()

    mo.vstack([
        mo.md("### Controlled Comparison: Statistical Summary"),
        mo.md(f"""
        **Using only mapped repositories (same set for both sources)**

        | Metric | Open Dev Data | GitHub Archive | Difference |
        |--------|---------------|----------------|------------|
        | Average MAD | {_avg_opendev:,.0f} | {_avg_gharchive:,.0f} | {_avg_diff:+,.0f} ({_avg_pct_diff:+.2f}%) |
        | Min MAD | {_merged['all_devs_opendev'].min():,.0f} | {_merged['all_devs_gharchive'].min():,.0f} | - |
        | Max MAD | {_merged['all_devs_opendev'].max():,.0f} | {_merged['all_devs_gharchive'].max():,.0f} | - |

        **Interpretation**: If the discrepancy is significantly smaller than the original comparison,
        then **repository mapping** is the primary cause. If the discrepancy remains similar,
        then **methodology differences** (identity resolution, event types) are the main factors.
        """),
        mo.md("### Day-by-Day Comparison (Mapped Repos Only)"),
        mo.ui.table(_merged[['day', 'all_devs_opendev', 'all_devs_gharchive', 'difference', 'pct_difference']],
                   selection=None,
                   pagination=True)
    ])
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
    return client, mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
