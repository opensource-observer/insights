import marimo

__generated_with = "0.15.2"
app = marimo.App(width="medium")


@app.cell
def setup_pyoso():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    from pyoso import Client

    # client = Client()
    # pyoso_db_conn = client.dbapi_connection()

    import os
    from dotenv import load_dotenv
    load_dotenv()
    client = Client(api_key=os.environ['OSO_API_KEY'])
    return client, mo, pd, px


@app.cell
def _(mo):
    mo.md(
        """
    # Protocol Deep Dive: Superchain TVL and Funding Events

    This notebook explores how total value locked (TVL) and funding events intersect across projects in the Optimism Superchain ecosystem. The goal is to understand how funding flows (GovGrants and RetroFunding) align with project growth and market share over time.
    """
    )
    return


@app.cell
def _(client):
    df_tvl_by_chain = client.to_pandas("""
    WITH tvl_events AS (
      SELECT 
        DATE_TRUNC('week', tvl_events.sample_date) as sample_date,
        tvl_events.chain,
        CASE
          WHEN tvl_events.chain = 'CELO' AND sample_date < DATE('2025-03-25') THEN 'Other chain(s)'
          WHEN c.chain IS NULL THEN 'Other chain(s)'
          ELSE 'Superchain'
        END AS is_superchain,
        tvl_events.amount
      FROM int_chain_metrics AS tvl_events
      LEFT JOIN int_superchain_chain_names AS c ON tvl_events.chain = c.chain
      WHERE
        tvl_events.metric_name = 'DEFILLAMA_TVL'
        AND tvl_events.amount > 0
        AND sample_date >= DATE('2021-07-01')
    )
    SELECT
      sample_date,
      chain,
      is_superchain,
      AVG(amount) AS amount
    FROM tvl_events
    GROUP BY 1, 2, 3
    ORDER BY 1, 2
    """)
    return (df_tvl_by_chain,)


@app.cell
def _(df_tvl_by_chain, mo, px):
    df_superchain = df_tvl_by_chain[df_tvl_by_chain['is_superchain'] == 'Superchain']
    df_grouped_superchain = df_superchain.groupby('sample_date')['amount'].sum().reset_index()

    fig_superchain_tvl = px.area(df_grouped_superchain, x='sample_date', y='amount',
                                 title='Superchain TVL over time',
                                 labels={'amount': 'TVL (USD)', 'sample_date': 'Date'},
                                 color_discrete_sequence=['#FF0420']

                                 )

    fig_superchain_tvl.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_family="Arial",
        title_font_family="Arial",
        title_x=0,
        xaxis_title="",
        yaxis_title="",
        legend_title="",
        autosize=True,
        margin=dict(t=50, l=0, r=0, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray',
            linecolor='black',
            linewidth=1,
            ticks='outside',
            rangemode='tozero',
            title_text="TVL (USD)"
        ),
        xaxis=dict(
            showgrid=False,
            linecolor='black',
            linewidth=1,
            ticks='outside',
            # tickformat="%b %Y",
            # dtick="M6",
            # tickangle=-45
        ),
        hovermode="x unified"
    )

    fig_superchain_tvl.update_traces(
        hovertemplate="%{y:.2f}",
        selector=dict(mode='lines')
    )
    f1 = mo.ui.plotly(fig_superchain_tvl)
    return (f1,)


@app.cell
def _(df_tvl_by_chain, mo, pd, px):
    df_grouped_market_share = df_tvl_by_chain.groupby(['sample_date', 'is_superchain'])['amount'].sum().reset_index()

    # Calculate total TVL for each date
    _df_total_tvl = df_grouped_market_share.groupby('sample_date')['amount'].sum().reset_index()
    _df_total_tvl.rename(columns={'amount': 'total_tvl'}, inplace=True)

    # Merge total TVL back into the grouped dataframe
    df_grouped_market_share = pd.merge(df_grouped_market_share, _df_total_tvl, on='sample_date')

    # Calculate market share
    df_grouped_market_share['market_share'] = df_grouped_market_share['amount'] / df_grouped_market_share['total_tvl']

    # Filter for superchain only
    df_superchain_market_share = df_grouped_market_share[df_grouped_market_share['is_superchain'] == 'Superchain']

    _fig_market_share = px.area(df_superchain_market_share, x='sample_date', y='market_share',
                  title='Superchain market share of total TVL',
                  labels={'market_share': 'Market Share', 'sample_date': 'Date'},
                  color_discrete_sequence=['#ff0420'],)

    _fig_market_share.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_family="Arial",
        title_font_family="Arial",
        title_x=0,
        xaxis_title="",
        yaxis_title="",
        legend_title="",
        autosize=True,
        margin=dict(t=50, l=0, r=0, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray',
            linecolor='black',
            linewidth=1,
            ticks='outside',
            rangemode='tozero',
            tickformat=".1%",
            title_text="Market Share"
        ),
        xaxis=dict(
            showgrid=False,
            linecolor='black',
            linewidth=1,
            ticks='outside',
        ),
        hovermode="x unified"
    )

    _fig_market_share.update_traces(
        hovertemplate="%{y:.2%}",
        selector=dict(mode='lines')
    )

    f2 = mo.ui.plotly(_fig_market_share)
    return (f2,)


@app.cell
def _(f1, f2, mo):
    mo.vstack([
        mo.md("## Overall Trends"),
        mo.hstack(items=[f1,f2])
    ])

    return


@app.cell
def _(client, pd):
    df_funding_to_projects = client.to_pandas("""
    WITH funding_events AS (
      SELECT
        sample_date,
        project_id,
        regexp_extract(metric_name, '^(.*)_funding_awarded_daily', 1) AS funding_source,
        SUM(amount) AS amount
      FROM timeseries_metrics_by_project_v0
      JOIN metrics_v0 USING metric_id
      WHERE metric_name IN (
        'OPTIMISM_GOVGRANTS_funding_awarded_daily',
        'OPTIMISM_RETROFUNDING_funding_awarded_daily'
      )
      GROUP BY 1,2,3
    )
    SELECT
      sample_date,
      funding_source,
      display_name AS project_name,
      amount,
      project_id  
    FROM funding_events
    JOIN projects_v1 USING project_id
    WHERE project_source = 'OSS_DIRECTORY'
    ORDER BY 1,2
    """)

    df_funding_to_projects['sample_date'] = pd.to_datetime(df_funding_to_projects['sample_date'], errors='coerce')
    return (df_funding_to_projects,)


@app.cell
def _(df_funding_to_projects):
    stringify = lambda arr: "'" + "','".join(arr) + "'"
    funded_projects_str = stringify(df_funding_to_projects['project_id'].unique())
    return (funded_projects_str,)


@app.cell
def _(client, funded_projects_str):
    df_tvl_by_project = client.to_pandas(f"""
    WITH tvl_events AS (
      SELECT
        sample_date,
        project_id,
        regexp_extract(metric_name, '^(.*)_defillama_tvl_weekly', 1) AS chain,
        amount
      FROM timeseries_metrics_by_project_v0
      JOIN metrics_v0 USING metric_id
      WHERE
        metric_name LIKE '%_defillama_tvl_weekly'
        AND project_id IN ({funded_projects_str})
        AND sample_date >= DATE('2021-07-01')
    ),
    max_tvl AS (
      SELECT
        project_id,
        MAX(amount) AS max_tvl
      FROM tvl_events
      GROUP BY 1
    )
    SELECT
      sample_date,
      tvl_events.chain,
      CASE
        WHEN tvl_events.chain = 'CELO' AND sample_date < DATE('2025-03-25') THEN 'Other chain(s)'
        WHEN c.chain IS NULL THEN 'Other chain(s)'
        ELSE 'Superchain'
      END AS is_superchain,
      display_name AS project_name,
      amount,
      project_id
    FROM tvl_events
    JOIN projects_v1 USING (project_id)
    JOIN max_tvl USING (project_id)
    LEFT JOIN int_superchain_chain_names AS c ON tvl_events.chain = c.chain
    WHERE
      tvl_events.chain NOT IN ('VESTING')
      AND max_tvl > 1000000
    ORDER BY 1,2
    """)
    return (df_tvl_by_project,)


@app.cell
def _(df_funding_to_projects, df_tvl_by_project, mo, pd):
    most_recent_date = (
        df_tvl_by_project
        .groupby('sample_date')['project_id']
        .nunique()
        .sort_index()
        .tail(5)
        .sort_index(ascending=False)
        .sort_values(ascending=False)
        .index[0]
    )

    df_snapshot = df_tvl_by_project[df_tvl_by_project['sample_date'] == most_recent_date]

    _df_total_tvl = (
        df_snapshot
        .groupby('project_name')['amount']
        .sum()
        .rename('Total TVL')
    )
    _df_superchain_tvl = (
        df_snapshot
        .query("is_superchain == 'Superchain'")
        .groupby('project_name')['amount']
        .sum()
        .rename('Superchain TVL')
    )
    _df_leaderboard = pd.concat([_df_total_tvl, _df_superchain_tvl], axis=1, join='outer').fillna(0).reset_index()

    _df_leaderboard['Share of TVL on Superchain'] = _df_leaderboard['Superchain TVL'] / _df_leaderboard['Total TVL']


    if len(df_funding_to_projects) > 0:
        df_funding_grouped = (
            df_funding_to_projects
            .groupby(['project_name','funding_source'], as_index=False)['amount']
            .sum()
            .pivot(index='project_name', columns='funding_source', values='amount')
            .fillna(0)
            .reset_index()
        )
    else:
        df_funding_grouped = pd.DataFrame({'project_name': []})

    for col in ['OPTIMISM_GOVGRANTS','OPTIMISM_RETROFUNDING']:
        if col not in df_funding_grouped.columns:
            df_funding_grouped[col] = 0

    df_funding_grouped = df_funding_grouped.rename(columns={
        'OPTIMISM_GOVGRANTS':'GovGrants Funding',
        'OPTIMISM_RETROFUNDING':'Retro Funding'
    })

    _df_leaderboard = (
        _df_leaderboard
        .merge(df_funding_grouped, how='left', left_on='project_name', right_on='project_name')
        .fillna(0)
    )
    _df_leaderboard['Total Funding'] = (
        _df_leaderboard['GovGrants Funding'] + _df_leaderboard['Retro Funding']
    )
    _df_leaderboard.rename(columns={
        'project_name': 'Project',
    }, inplace=True)

    mo.vstack([
        mo.md(f"""

        <h2>Superchain DeFi Leaderboard</h2>

        This table includes projects with at least $1M in TVL at some point in their history (on any chain). Current TVL is captured from the week beginning {most_recent_date}, according to DefiLlama. Funding data comes from the Optimism Foundation's public data, and linked to project names [here](https://github.com/opensource-observer/oss-funding).
    .
        """
        ),
        mo.ui.table(
            _df_leaderboard.sort_values('Superchain TVL', ascending=False).reset_index(drop=True),
            format_mapping={
                'Total TVL': '${:,.0f}',
                'Superchain TVL': '${:,.0f}',
                'Share of TVL on Superchain': '{:.1%}',
                'GovGrants Funding': '${:,.0f}',
                'Retro Funding': '${:,.0f}',
                'Total Funding': '${:,.0f}',
            },
            show_data_types=False,
            show_column_summaries=False,
            page_size=50
        )  
    ])

    return


@app.cell
def _(df_tvl_by_project, mo):
    PROJECT_OPTIONS = sorted(df_tvl_by_project['project_name'].drop_duplicates().to_list())
    project_dropdown = mo.ui.dropdown(
        label="Select a Project",
        options=PROJECT_OPTIONS,
        value="Aave",
        searchable=True,
        full_width=True
    )
    return (project_dropdown,)


@app.cell
def _(df_tvl_by_project, mo, project_dropdown):
    df_tvl_by_project_filtered = df_tvl_by_project[df_tvl_by_project['project_name'] == project_dropdown.value]
    CHAIN_OPTIONS = df_tvl_by_project_filtered['chain'].unique().tolist()
    chain_dropdown = mo.ui.multiselect(
        label="Select Chain(s)",
        options=CHAIN_OPTIONS,
        value=CHAIN_OPTIONS,
        full_width=True
    )
    return chain_dropdown, df_tvl_by_project_filtered


@app.cell
def _(mo):
    funding_events_checkbox = mo.ui.checkbox(label="Show funding events", value=True)
    return (funding_events_checkbox,)


@app.cell
def _(chain_dropdown, funding_events_checkbox, mo, project_dropdown):
    mo.vstack([
        mo.md("## Protocol Deep Dive"),
        mo.hstack(
            [project_dropdown, chain_dropdown, funding_events_checkbox],
            align="stretch",
            justify="start",
            gap=2,
            widths=[2,2,1]
        ),
    ])
    return


@app.cell
def _(funding_events_checkbox):
    show_funding_events = bool(funding_events_checkbox.value)
    return (show_funding_events,)


@app.cell
def _(
    chain_dropdown,
    df_funding_to_projects,
    df_tvl_by_project_filtered,
    project_dropdown,
):
    df_funding_to_projects_filtered = df_funding_to_projects[
        df_funding_to_projects['project_name'] == project_dropdown.value
    ]
    df_tvl_by_project_filtered_by_chain = df_tvl_by_project_filtered[
        df_tvl_by_project_filtered['chain'].isin(chain_dropdown.value)
    ]
    return df_funding_to_projects_filtered, df_tvl_by_project_filtered_by_chain


@app.cell
def _(
    df_funding_to_projects_filtered,
    df_tvl_by_project_filtered_by_chain,
    mo,
    pd,
    project_dropdown,
    px,
    show_funding_events,
):
    # Group by date and is_superchain to create stacked data
    df_grouped = df_tvl_by_project_filtered_by_chain.groupby(['sample_date', 'is_superchain'])['amount'].sum().reset_index()

    # Sort by date
    df_grouped = df_grouped.sort_values(by=['sample_date'])

    # Create stacked area chart with custom color mapping
    fig_tvl_by_project = px.area(
        df_grouped, 
        x="sample_date", 
        y="amount", 
        color='is_superchain',
        title=f'<b>{project_dropdown.value} TVL</b>',
        color_discrete_map={'Other chain(s)': '#AAA', 'Superchain': '#ff0420'}  
    )

    # Apply consistent styling like your other charts
    fig_tvl_by_project.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_family="Arial",
        title_font_family="Arial",
        title_x=0,
        xaxis_title="",
        yaxis_title="",
        legend_title="",
        autosize=True,
        margin=dict(t=50, l=0, r=0, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray',
            linecolor='black',
            linewidth=1,
            ticks='outside',
            rangemode='tozero',
            title_text="TVL (USD)"
        ),
        xaxis=dict(
            showgrid=False,
            linecolor='black',
            linewidth=1,
            ticks='outside',
        ),
        hovermode="x unified"
    )

    # Update hover template
    fig_tvl_by_project.update_traces(
        hovertemplate="%{y:.2f}",
        selector=dict(mode='lines')
    )

    if show_funding_events:
        annotations = []
        shapes = []
        for _, row in df_funding_to_projects_filtered.dropna(subset=['sample_date']).iterrows():
            ts = pd.Timestamp(row['sample_date']).to_pydatetime()
            amt = row['amount']
            funding_type = row['funding_source'].replace('OPTIMISM_','')
            label = f"{funding_type}: ${amt:,.0f}"

            shapes.append(dict(
                type='line',x0=ts,x1=ts,y0=0,y1=1,yref='paper',
                line=dict(color='black',width=1,dash='dash')
            ))
            annotations.append(dict(
                x=ts,y=0.98,xref='x',yref='paper',text=label,showarrow=False,
                textangle=-90,yanchor='top',bgcolor='rgba(255,255,255,0.8)'
            ))

        fig_tvl_by_project.update_layout(annotations=annotations,shapes=shapes)
    else:
        fig_tvl_by_project.update_layout(annotations=None,shapes=None)


    mo.ui.plotly(fig_tvl_by_project)
    return


if __name__ == "__main__":
    app.run()
