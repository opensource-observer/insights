import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.vstack([
        mo.md(r"""# Activity Metric Definition"""),
        mo.md(r"""
        This notebook validates the Monthly Active Developer (MAD) metric by comparing two different data sources:
        
        1. **Open Dev Data (Electric Capital)**: Pre-calculated ecosystem metrics from the Developer Report
        2. **GitHub Archive**: Raw event data calculated from individual developer activities
        
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
        **Method**: Rolling 28-day window  
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
    # Calculate statistics
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
    - Pre-calculated metrics from the [Developer Report](https://www.developerreport.com)
    - Uses proprietary methodology for identifying and tracking developers
    - Includes commits from multiple code hosting platforms
    - Monthly aggregation with sophisticated deduplication
    
    ### GitHub Archive (OSO)
    - Raw event data from GitHub Archive
    - 28-day rolling window calculation
    - Limited to GitHub platform activities
    - Includes: commits, pull requests, issues, and code reviews
    - Uses `int_gharchive__developer_activities` which aggregates daily developer events
    
    ### Expected Differences
    - **Platform Coverage**: Open Dev Data may include non-GitHub platforms
    - **Deduplication**: Different approaches to identifying unique developers
    - **Time Windows**: Rolling 28-day vs calendar month aggregation
    - **Activity Definitions**: Different event types may be included/weighted differently
    """)
    return


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.express as px
    return pd, px


@app.cell(hide_code=True)
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    import os
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    client = pyoso.Client(os.getenv("OSO_API_KEY"))
    return client, mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
