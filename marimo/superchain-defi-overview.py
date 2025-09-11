import marimo

__generated_with = "0.15.2"
app = marimo.App(width="medium")


@app.cell
def setup_pyoso():
    import marimo as mo
    from pyoso import Client

    client = Client()
    pyoso_db_conn = client.dbapi_connection()

    # import os
    # from dotenv import load_dotenv
    # load_dotenv()
    # client = Client(api_key=os.environ['OSO_API_KEY'])
    return mo, client, pyoso_db_conn


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
def _():
    import pandas as pd
    import plotly.express as px

    LAYOUT = dict(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_family="PT Sans, sans-serif",
        title_font_family="Lora, serif",
        title_x=0,
        legend_title="",
        autosize=True,
        margin=dict(t=50, l=0, r=0, b=0),
        legend=dict(
            orientation="h",
            yanchor="middle",
            y=1,
            xanchor="left",
            x=0
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray',
            linecolor='black',
            linewidth=1,
            ticks='outside',
            rangemode='tozero'
        ),
        xaxis=dict(
            showgrid=False,
            linecolor='black',
            linewidth=1,
            ticks='outside',
        ),
        hovermode="x"
    )
    PRIMARY_COLOR = '#FF0420'
    SECONDARY_COLOR = '#AAA'

    stringify = lambda arr: "'" + "','".join(arr) + "'"
    return pd, px,LAYOUT, PRIMARY_COLOR, SECONDARY_COLOR, stringify


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
        END AS chain_group,
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
      chain_group,
      AVG(amount) AS amount
    FROM tvl_events
    GROUP BY 1, 2, 3
    ORDER BY 1, 2
    """)
    return (df_tvl_by_chain,)


@app.cell
def _(LAYOUT, PRIMARY_COLOR, SECONDARY_COLOR, df_tvl_by_chain, mo, px):
    _df_superchain_tvl_grouped = (
        df_tvl_by_chain[df_tvl_by_chain['chain_group'] == 'Superchain']
        .groupby('sample_date')['amount']
        .sum()
        .reset_index()
    )
    _fig_superchain_tvl = px.area(
        data_frame=_df_superchain_tvl_grouped,
        x='sample_date',
        y='amount',
        title='Superchain TVL over time',
        labels={'amount': 'TVL (USD)', 'sample_date': 'Date'},
        color_discrete_sequence=[PRIMARY_COLOR, SECONDARY_COLOR]
    )
    _fig_superchain_tvl.update_layout(
        xaxis_title='',
        yaxis_title='',
        **LAYOUT
    )
    _fig_superchain_tvl.update_traces(
        hovertemplate="%{x|%d %b %Y}<br><b>%{y:$,.0f}</b>",
        selector=dict(mode='lines')
    )
    fig_superchain_tvl = mo.ui.plotly(_fig_superchain_tvl)
    return (fig_superchain_tvl,)


@app.cell
def _(LAYOUT, PRIMARY_COLOR, SECONDARY_COLOR, df_tvl_by_chain, mo, px):
    _df_superchain_market_share = (
        df_tvl_by_chain
        .groupby(['sample_date', 'chain_group'], as_index=False)
        .amount.sum()
        .assign(market_share=lambda d: d['amount']/d.groupby('sample_date')['amount'].transform('sum'))
        .query("chain_group == 'Superchain'")
    )
    _fig_market_share = px.area(
        _df_superchain_market_share,
        x='sample_date',
        y='market_share',
        title='Superchain market share of total TVL',
        labels={'market_share': 'Market Share', 'sample_date': 'Date'},
        color_discrete_sequence=[PRIMARY_COLOR, SECONDARY_COLOR]
    )
    _fig_market_share.update_layout(
         xaxis_title='',
        yaxis_title='',
        **LAYOUT
    )
    _fig_market_share.update_traces(
        hovertemplate="%{x|%d %b %Y}<br><b>%{y:.2%}</b>",
        selector=dict(mode='lines')
    )
    fig_market_share = mo.ui.plotly(_fig_market_share)
    return (fig_market_share,)


@app.cell
def _(fig_market_share, fig_superchain_tvl, mo):
    mo.vstack([
        mo.md("## Overall Trends"),
        mo.hstack(items=[fig_superchain_tvl,fig_market_share])
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
def _(client, df_funding_to_projects, stringify):
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
        AND project_id IN ({stringify(df_funding_to_projects['project_id'].unique())})
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
      END AS chain_group,
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

    _df_leaderboard = (
        df_tvl_by_project
        .query("sample_date == @most_recent_date")
        .pipe(lambda d:
            d.groupby('project_name',as_index=False)['amount'].sum().rename(columns={'amount':'Current TVL'})
            .merge(
                d.query("chain_group == 'Superchain'")
                 .groupby('project_name',as_index=False)['amount'].sum()
                 .rename(columns={'amount':'Superchain TVL'}),
                how='left',
                on='project_name'
            )
        )
        .fillna({'Superchain TVL':0})
        .assign(**{'Share of TVL on Superchain':lambda x: x['Superchain TVL']/x['Current TVL']})
        .merge(
            (
                df_funding_to_projects
                .groupby(['project_name','funding_source'],as_index=False)['amount'].sum()
                .pivot(index='project_name',columns='funding_source',values='amount')
                .reindex(columns=['OPTIMISM_GOVGRANTS','OPTIMISM_RETROFUNDING'],fill_value=0)
                .rename(columns={'OPTIMISM_GOVGRANTS':'GovGrants Funding','OPTIMISM_RETROFUNDING':'Retro Funding'})
                .reset_index()
            ) if len(df_funding_to_projects)>0
              else pd.DataFrame({'project_name':[],'GovGrants Funding':[],'Retro Funding':[]}),
            how='left', on='project_name'
        )
        .fillna(0)
        .assign(**{'Total Funding':lambda x: x['GovGrants Funding']+x['Retro Funding']})
        .rename(columns={'project_name':'Project'})
    )

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
                'Current TVL': '${:,.0f}',
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
    _project_options = sorted(df_tvl_by_project['project_name'].drop_duplicates().to_list())
    project_dropdown = mo.ui.dropdown(
        label="Select a Project",
        options=_project_options,
        value="Aave",
        searchable=True,
        full_width=True
    )
    return (project_dropdown,)


@app.cell
def _(df_tvl_by_project, mo, project_dropdown):
    df_tvl_by_project_filtered = df_tvl_by_project[df_tvl_by_project['project_name'] == project_dropdown.value]
    _chain_options = df_tvl_by_project_filtered['chain'].unique().tolist()
    chain_dropdown = mo.ui.multiselect(
        label="Select Chain(s)",
        options=_chain_options,
        value=_chain_options,
        full_width=True
    )
    return (chain_dropdown,)


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
def _(
    LAYOUT,
    chain_dropdown,
    df_funding_to_projects,
    df_tvl_by_project,
    funding_events_checkbox,
    mo,
    pd,
    project_dropdown,
    px,
):
    def project_tvl_chart(project_name, chain_list, show_funding_events):

        d = df_tvl_by_project[df_tvl_by_project['project_name'] == project_name]
        if chain_list:
            d = d[d['chain'].isin(chain_list)]

        d = (
            d.groupby(['sample_date','chain_group'],as_index=False)['amount']
             .sum()
             .sort_values('sample_date')
        )

        fig = px.area(
            d,
            x='sample_date',
            y='amount',
            color='chain_group',
            title=f'<b>{project_name} TVL</b>',
            color_discrete_map={'Other chain(s)':'#AAA','Superchain':'#ff0420'},
            category_orders={'chain_group':['Other chain(s)','Superchain']}
        )
        fig.update_layout(xaxis_title='',yaxis_title='',**LAYOUT)
        fig.update_traces(hovertemplate="%{x|%d %b %Y}<br>$%{y:,.0f}<extra></extra>")

        if show_funding_events and 'df_funding_to_projects' in globals() and len(df_funding_to_projects):
            f = (
                df_funding_to_projects
                .loc[lambda x: x['project_name']==project_name]
                .dropna(subset=['sample_date'])
            )
            if len(f):
                shapes,ann = [],[]
                for _,row in f.iterrows():
                    ts = pd.to_datetime(row['sample_date'])
                    amt = row['amount']
                    funding_type = str(row['funding_source']).replace('OPTIMISM_','')
                    label = f"{funding_type}: ${amt:,.0f}"
                    shapes.append(dict(type='line',x0=ts,x1=ts,y0=0,y1=1,yref='paper',
                                       line=dict(color='black',width=1,dash='dash')))
                    ann.append(dict(x=ts,y=0.98,xref='x',yref='paper',text=label,showarrow=False,
                                    textangle=-90,yanchor='top',bgcolor='rgba(255,255,255,0.85)'))
                fig.update_layout(shapes=shapes,annotations=ann)
            else:
                fig.update_layout(shapes=None,annotations=None)
        else:
            fig.update_layout(shapes=None,annotations=None)

        return fig


    mo.ui.plotly(
        project_tvl_chart(
            project_name=project_dropdown.value,
            chain_list=chain_dropdown.value,
            show_funding_events=bool(funding_events_checkbox.value)
        )
    )
    return


if __name__ == "__main__":
    app.run()
