import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.vstack([
        mo.md("""
        # **Ethereum Developer Activity**
        """),
        mo.md("""
        Track monthly active developers contributing to open source projects in the Ethereum ecosystem.  
        Data sourced from [Open Dev Data](https://www.developerreport.com) by Electric Capital.
        """),            
    ])
    return


@app.cell(hide_code=True)
def _(df_stats, mo):
    _latest = df_stats.iloc[-1]
    _previous = df_stats.iloc[-2] if len(df_stats) > 1 else _latest
    
    _current_devs = int(_latest['all_devs'])
    _change = _current_devs - int(_previous['all_devs'])
    _change_pct = (_change / _previous['all_devs'] * 100) if _previous['all_devs'] > 0 else 0
    
    _change_color = '#2ECC71' if _change >= 0 else '#E74C3C'
    _change_symbol = '▲' if _change >= 0 else '▼'
    
    mo.vstack([
        mo.md("## Key Metrics"),
        mo.hstack([
            mo.vstack([
                mo.md(f"""
                <div style="text-align: center; padding: 20px;">
                    <div style="font-size: 48px; font-weight: bold; color: #2C3E50;">
                        {_current_devs:,}
                    </div>
                    <div style="font-size: 16px; color: #7F8C8D; margin-top: 8px;">
                        Monthly Active Developers
                    </div>
                    <div style="font-size: 14px; color: {_change_color}; margin-top: 8px;">
                        {_change_symbol} {abs(_change):,} ({abs(_change_pct):.1f}%) from previous month
                    </div>
                </div>
                """),
            ], align="center"),
        ], justify="center")
    ])
    return


@app.cell(hide_code=True)
def _(df_stats, mo):
    _total_months = len(df_stats)
    _avg_devs = int(df_stats['all_devs'].mean())
    _max_devs = int(df_stats['all_devs'].max())
    _min_devs = int(df_stats['all_devs'].min())
    
    mo.hstack([
        mo.vstack([
            mo.md(f"""
            <div style="text-align: center; padding: 16px; background: #F8F9FA; border-radius: 8px;">
                <div style="font-size: 28px; font-weight: bold; color: #4C78A8;">
                    {_avg_devs:,}
                </div>
                <div style="font-size: 14px; color: #7F8C8D; margin-top: 4px;">
                    Average MAD
                </div>
            </div>
            """),
        ]),
        mo.vstack([
            mo.md(f"""
            <div style="text-align: center; padding: 16px; background: #F8F9FA; border-radius: 8px;">
                <div style="font-size: 28px; font-weight: bold; color: #2ECC71;">
                    {_max_devs:,}
                </div>
                <div style="font-size: 14px; color: #7F8C8D; margin-top: 4px;">
                    Peak MAD
                </div>
            </div>
            """),
        ]),
        mo.vstack([
            mo.md(f"""
            <div style="text-align: center; padding: 16px; background: #F8F9FA; border-radius: 8px;">
                <div style="font-size: 28px; font-weight: bold; color: #E67E22;">
                    {_total_months}
                </div>
                <div style="font-size: 14px; color: #7F8C8D; margin-top: 4px;">
                    Months Tracked
                </div>
            </div>
            """),
        ]),
    ], justify="space-around", widths=[1, 1, 1])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("## Monthly Active Developers Over Time")
    return


@app.cell(hide_code=True)
def _(df_stats, mo, px):
    _fig = px.area(
        data_frame=df_stats,
        x='day',
        y='all_devs',
        color_discrete_sequence=['#4C78A8']
    )
    
    _fig.update_traces(
        line=dict(width=2),
        fillcolor='rgba(76, 120, 168, 0.2)',
        hovertemplate='<b>%{x|%b %Y}</b><br>Active Developers: %{y:,.0f}<extra></extra>'
    )
    
    _fig.update_layout(
        template='plotly_white',
        margin=dict(t=20, l=0, r=0, b=0),
        hovermode='x unified',
        showlegend=False,
        height=400
    )
    
    _fig.update_xaxes(
        title='',
        showgrid=False,
        linecolor="#000",
        linewidth=1,
        ticks="outside",
        tickformat="%b %Y"
    )
    
    _fig.update_yaxes(
        title="Monthly Active Developers",
        showgrid=True,
        gridcolor="#E5E5E5",
        zeroline=True,
        zerolinecolor="#CCCCCC",
        zerolinewidth=1,
        linecolor="#000",
        linewidth=1,
        ticks="outside",
        range=[0, df_stats['all_devs'].max() * 1.1]
    )
    
    mo.vstack([
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("## Developer Activity by Type")
    return


@app.cell(hide_code=True)
def _(df_by_type, mo, px):
    _fig2 = px.area(
        data_frame=df_by_type,
        x='day',
        y='dev_count',
        color='developer_type',
        color_discrete_map={
            'Full-Time Developers': '#7A4D9B',
            'Part-Time Developers': '#41AB5D',
            'Other Active Developers': '#F39C12'
        }
    )
    
    _fig2.update_traces(
        line=dict(width=1.5),
        hovertemplate='%{fullData.name}<br><b>%{x|%b %Y}</b><br>Developers: %{y:,.0f}<extra></extra>'
    )
    
    _fig2.update_layout(
        template='plotly_white',
        margin=dict(t=20, l=0, r=0, b=0),
        hovermode='x unified',
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text=''
        )
    )
    
    _fig2.update_xaxes(
        title='',
        showgrid=False,
        linecolor="#000",
        linewidth=1,
        ticks="outside",
        tickformat="%b %Y"
    )
    
    _fig2.update_yaxes(
        title="Number of Developers",
        showgrid=True,
        gridcolor="#E5E5E5",
        zeroline=True,
        zerolinecolor="#CCCCCC",
        zerolinewidth=1,
        linecolor="#000",
        linewidth=1,
        ticks="outside"
    )
    
    mo.vstack([
        mo.ui.plotly(_fig2, config={'displayModeBar': False}),
        mo.md("""
        #### Activity Level Definitions
        - **Full-Time Developers**: 10+ days of activity per month
        - **Part-Time Developers**: 1-9 days of activity per month  
        - **Other Active Developers**: Contributors with at least one activity in the rolling 28-day window
        """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("## Data Table")
    return


@app.cell(hide_code=True)
def _(df_stats, mo):
    _display_df = df_stats.copy()
    _display_df['day'] = _display_df['day'].dt.strftime('%Y-%m-%d')
    _display_df = _display_df.rename(columns={
        'day': 'Date',
        'all_devs': 'Monthly Active Developers'
    })
    mo.ui.table(_display_df, selection=None, pagination=True)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ### About This Data
    
    **Data Source**: [Open Dev Data](https://www.developerreport.com) by Electric Capital
    
    **Methodology**:
    - A developer is considered "active" if they made at least one commit in the given month
    - Developers are deduplicated across multiple repositories and organizations
    - Data includes contributions to core protocol repositories and major ecosystem projects
    - Metrics are calculated on a rolling 28-day basis and aggregated monthly
    
    **Updates**: Data is refreshed monthly
    
    **Coverage**: This dashboard focuses on the Ethereum ecosystem as defined by Open Dev Data
    """)
    return


@app.cell
def _(mo, pd, pyoso_db_conn):
    df_stats = mo.sql(
        f"""
        SELECT
            mads.day,
            mads.all_devs
        FROM stg_opendevdata__eco_mads AS mads
        JOIN stg_opendevdata__ecosystems AS e
            ON mads.ecosystem_id = e.id
        WHERE
            e.name = 'Ethereum'
            AND mads.day >= DATE('2024-01-01')
        ORDER BY 1
        """,
        output=False,
        engine=pyoso_db_conn
    )
    df_stats['day'] = pd.to_datetime(df_stats['day'])
    return (df_stats,)


@app.cell
def _(mo, pd, pyoso_db_conn):
    # Query for developer activity by type
    df_by_type = mo.sql(
        f"""
        SELECT
            mads.day,
            mads.full_time_devs AS dev_count,
            'Full-Time Developers' AS developer_type
        FROM stg_opendevdata__eco_mads AS mads
        JOIN stg_opendevdata__ecosystems AS e
            ON mads.ecosystem_id = e.id
        WHERE
            e.name = 'Ethereum'
            AND mads.day >= DATE('2024-01-01')
        
        UNION ALL
        
        SELECT
            mads.day,
            mads.part_time_devs AS dev_count,
            'Part-Time Developers' AS developer_type
        FROM stg_opendevdata__eco_mads AS mads
        JOIN stg_opendevdata__ecosystems AS e
            ON mads.ecosystem_id = e.id
        WHERE
            e.name = 'Ethereum'
            AND mads.day >= DATE('2024-01-01')
            
        UNION ALL
        
        SELECT
            mads.day,
            (mads.all_devs - mads.full_time_devs - mads.part_time_devs) AS dev_count,
            'Other Active Developers' AS developer_type
        FROM stg_opendevdata__eco_mads AS mads
        JOIN stg_opendevdata__ecosystems AS e
            ON mads.ecosystem_id = e.id
        WHERE
            e.name = 'Ethereum'
            AND mads.day >= DATE('2024-01-01')
        
        ORDER BY 1, 3
        """,
        output=False,
        engine=pyoso_db_conn
    )
    df_by_type['day'] = pd.to_datetime(df_by_type['day'])
    return (df_by_type,)


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    return pd, px


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
