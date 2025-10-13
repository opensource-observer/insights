import marimo

__generated_with = "unknown"
app = marimo.App()


@app.cell
def _(mo):
    mo.vstack([
        mo.md("""
        # Open Source DeFi Analysis
        <small>Author: <span style="background-color:#f0f0f0;padding:2px 4px;border-radius:3px;">OSO Team</span>
        · Last Updated: <span style="background-color:#f0f0f0;padding:2px 4px;border-radius:3px;">October 2025</span></small>
        """),
        mo.md("""
        This notebook analyzes open source DeFi applications, tracking their Total Value Locked (TVL) 
        and developer activity across Ethereum Mainnet and Layer 2 networks.
        """),
        mo.accordion({
            "<b>Click to see details</b>": mo.accordion({
                "Methodology": """
                - TVL data is sourced from DefiLlama for projects in OSS Directory
                - Developer metrics use full-time contributor estimates from GitHub activity
                - Growth rates are calculated using compound monthly growth rate (CMGR)
                - Only includes projects with both TVL and developer data
                """,
                "Data Sources": """
                - OSS Directory project registry
                - DefiLlama TVL data (Mainnet and Layer 2s)
                - GitHub contributor activity
                """,
                "Further Resources": """
                - [Pyoso Docs](https://docs.opensource.observer/docs/get-started/python)
                - [Semantic Layer](https://docs.opensource.observer/docs/get-started/using-semantic-layer)
                - [Marimo Docs](https://docs.marimo.io/)
                """
            })
        })
    ])
    return


@app.cell
def _(df_devs, df_tvl_raw):
    # Get latest date for TVL
    _latest_tvl_date = df_tvl_raw['sample_date'].max()
    _df_latest_tvl = df_tvl_raw[df_tvl_raw['sample_date'] == _latest_tvl_date]

    # Number of unique DeFi applications
    num_defi_apps = len(_df_latest_tvl['project_id'].unique())

    # Current TVL on Mainnet
    current_tvl_mainnet = _df_latest_tvl[_df_latest_tvl['is_layer2'] == False]['tvl'].sum()

    # Current TVL on Layer 2s
    current_tvl_l2 = _df_latest_tvl[_df_latest_tvl['is_layer2'] == True]['tvl'].sum()

    # Current Full Time Contributors
    _latest_dev_date = df_devs['sample_date'].max()
    current_ftc = df_devs[df_devs['sample_date'] == _latest_dev_date]['full_time_contributors'].sum()
    return current_ftc, current_tvl_l2, current_tvl_mainnet, num_defi_apps


@app.cell
def _(df_devs, df_tvl_raw, pd):
    # Aggregate TVL by date
    _df_tvl_ts = df_tvl_raw.groupby('sample_date')['tvl'].sum().reset_index()
    _df_tvl_ts['sample_date'] = pd.to_datetime(_df_tvl_ts['sample_date'])
    _df_tvl_ts = _df_tvl_ts.sort_values('sample_date')
    _first_date = _df_tvl_ts['sample_date'].min()

    # Aggregate developers by date
    _df_devs_ts = df_devs.groupby('sample_date')['full_time_contributors'].sum().reset_index()
    _df_devs_ts['sample_date'] = pd.to_datetime(_df_devs_ts['sample_date'])
    _df_devs_ts = _df_devs_ts.sort_values('sample_date')

    # Merge the two datasets
    df_timeseries = pd.merge(_df_tvl_ts, _df_devs_ts, on='sample_date', how='outer')
    df_timeseries = df_timeseries.sort_values('sample_date')
    df_timeseries['full_time_contributors'] = df_timeseries['full_time_contributors'].ffill()

    df_timeseries = df_timeseries[df_timeseries['sample_date'] >= _first_date]
    return (df_timeseries,)


@app.cell
def _(df_devs, df_tvl_raw, pd):
    # Get latest TVL for each project
    _latest_tvl_date = df_tvl_raw['sample_date'].max()
    _df_current_tvl = df_tvl_raw[df_tvl_raw['sample_date'] == _latest_tvl_date].groupby(['project_id', 'display_name'])['tvl'].sum().reset_index()
    _df_current_tvl.columns = ['project_id', 'display_name', 'current_tvl']

    # Get first year with TVL data for each project
    _df_first_year = df_tvl_raw.groupby('project_id')['sample_date'].min().reset_index()
    _df_first_year['first_year'] = pd.to_datetime(_df_first_year['sample_date']).dt.year
    _df_first_year = _df_first_year[['project_id', 'first_year']]

    # Calculate monthly TVL for CMGR calculation
    _df_tvl_monthly = df_tvl_raw.copy()
    _df_tvl_monthly['year_month'] = pd.to_datetime(_df_tvl_monthly['sample_date']).dt.to_period('M')
    _df_tvl_monthly = _df_tvl_monthly.groupby(['project_id', 'year_month'])['tvl'].sum().reset_index()

    # Calculate CMGR for each project
    def _calculate_cmgr(project_df):
        if len(project_df) < 2:
            return None
        project_df = project_df.sort_values('year_month')
        first_value = project_df.iloc[0]['tvl']
        last_value = project_df.iloc[-1]['tvl']
        num_months = len(project_df) - 1
        if first_value <= 0 or num_months <= 0:
            return None
        cmgr = ((last_value / first_value) ** (1 / num_months)) - 1
        return cmgr * 100  # Convert to percentage

    _df_cmgr = _df_tvl_monthly.groupby('project_id').apply(_calculate_cmgr).reset_index()
    _df_cmgr.columns = ['project_id', 'tvl_cmgr']

    # Calculate average FTC for past 6 months
    _latest_dev_date = df_devs['sample_date'].max()
    _six_months_ago = pd.to_datetime(_latest_dev_date) - pd.DateOffset(months=6)
    _df_recent_devs = df_devs[pd.to_datetime(df_devs['sample_date']) >= _six_months_ago]
    _df_avg_ftc = _df_recent_devs.groupby('project_id')['full_time_contributors'].mean().reset_index()
    _df_avg_ftc.columns = ['project_id', 'avg_ftc_6mo']

    # Merge all leaderboard data
    df_leaderboard = _df_current_tvl.merge(_df_first_year, on='project_id', how='left')
    df_leaderboard = df_leaderboard.merge(_df_cmgr, on='project_id', how='left')
    df_leaderboard = df_leaderboard.merge(_df_avg_ftc, on='project_id', how='left')

    # Sort by current TVL descending
    df_leaderboard = df_leaderboard.sort_values('current_tvl', ascending=False)

    # Format columns
    df_leaderboard['current_tvl'] = df_leaderboard['current_tvl'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "-")
    df_leaderboard['tvl_cmgr'] = df_leaderboard['tvl_cmgr'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
    df_leaderboard['avg_ftc_6mo'] = df_leaderboard['avg_ftc_6mo'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
    df_leaderboard['first_year'] = df_leaderboard['first_year'].apply(lambda x: str(int(x)) if pd.notna(x) else "-")

    # Rename columns for display
    df_leaderboard = df_leaderboard[['display_name', 'current_tvl', 'first_year', 'tvl_cmgr', 'avg_ftc_6mo']]
    df_leaderboard.columns = ['Project', 'Current TVL', 'First Year', 'TVL CMGR', 'Avg FTC (6mo)']
    return (df_leaderboard,)


@app.cell
def _(current_ftc, current_tvl_l2, current_tvl_mainnet, mo, num_defi_apps):
    mo.vstack([
        mo.md("## Key Metrics"),
        mo.hstack([
            mo.stat(label="Tracked DeFi Applications", value=f"{num_defi_apps:,}", bordered=True),
            mo.stat(label="TVL on Mainnet", value=f"${current_tvl_mainnet:,.0f}", bordered=True),
            mo.stat(label="TVL on Layer 2s", value=f"${current_tvl_l2:,.0f}", bordered=True),
            mo.stat(label="Full Time Contributors", value=f"{current_ftc:,.0f}", bordered=True),
        ], widths="equal", gap=1)
    ])
    return


@app.cell
def _(df_timeseries, go, make_subplots, mo):
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add TVL trace
    fig.add_trace(
        go.Scatter(
            x=df_timeseries['sample_date'],
            y=df_timeseries['tvl'],
            name="Total TVL",
            line=dict(color="#3B82F6", width=2),
            mode='lines'
        ),
        secondary_y=False,
    )

    # Add FTC trace
    fig.add_trace(
        go.Scatter(
            x=df_timeseries['sample_date'],
            y=df_timeseries['full_time_contributors'],
            name="Full Time Contributors",
            line=dict(color="#10B981", width=2),
            mode='lines'
        ),
        secondary_y=True,
    )

    # Update layout
    fig.update_layout(
        title="",
        font=dict(size=12, color="#111"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(t=60, l=20, r=20, b=40),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        )
    )

    # Update axes
    fig.update_xaxes(title_text="Date", showgrid=True, gridcolor="#f0f0f0")
    fig.update_yaxes(title_text="Total TVL ($)", secondary_y=False, showgrid=True, gridcolor="#f0f0f0")
    fig.update_yaxes(title_text="Full Time Contributors", secondary_y=True, showgrid=False)


    mo.vstack([
        mo.md("## Open Source DeFi: TVL and Developer Activity"),
        mo.ui.plotly(fig)
    ])

    return


@app.cell
def _(df_leaderboard, mo):
    mo.vstack([
        mo.md("## Tracked DeFi Applications"),
        mo.ui.table(
            data=df_leaderboard.reset_index(drop=True),
            selection=None, 
            page_size=25,
            show_data_types=False,
            show_column_summaries=False
        )
    ])
    return


@app.cell
def _(mo, pyoso_db_conn):
    df_tvl_raw = mo.sql(
        f"""
        SELECT
          tm.sample_date,
          project_id,
          p.display_name,
          c.chain,
          c.is_layer2,
          SUM(tm.amount) AS tvl
        FROM timeseries_metrics_by_project_v0 tm
        JOIN projects_v1 p USING (project_id)
        JOIN metrics_v0 m USING (metric_id)
        JOIN int_chains c
          ON m.metric_event_source = c.chain    
        WHERE
          (c.is_layer2 OR c.chain = 'MAINNET')
          AND m.metric_model = 'defillama_tvl'
          AND m.metric_time_aggregation = 'daily'
          AND p.project_source = 'OSS_DIRECTORY'
        GROUP BY 1,2,3,4,5
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_tvl_raw,)


@app.cell
def _(df_tvl_raw):
    project_ids = df_tvl_raw['project_id'].unique()
    return (project_ids,)


@app.cell
def _(mo, project_ids, pyoso_db_conn, stringify):
    df_devs = mo.sql(
        f"""
        SELECT
          tm.sample_date,
          project_id,
          p.display_name,
          SUM(tm.amount) AS full_time_contributors
        FROM timeseries_metrics_by_project_v0 tm
        JOIN projects_v1 p USING project_id
        JOIN metrics_v0 m USING metric_id
        WHERE
          m.metric_model = 'full_time_contributors'
          AND m.metric_time_aggregation = 'monthly'
          AND m.metric_event_source = 'GITHUB'
          AND project_id IN ({stringify(project_ids)})
        GROUP BY 1,2,3
        """,
        engine=pyoso_db_conn,
        output=False
    )
    return (df_devs,)


@app.cell
def _():
    stringify = lambda arr: "'" + "','".join(arr) + "'"
    return (stringify,)


@app.cell
def _():
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    return go, make_subplots, pd


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
