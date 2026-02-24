# DEPRECATED

import marimo

__generated_with = "unknown"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Developer Activity [DEPRECATED]
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-02-17</span></small>

    Track monthly active developers (MAD) contributing to open source projects across crypto ecosystems.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion({
        "Definitions": mo.md("""
- **Full-Time Developers**: 10+ days of activity per month
- **Part-Time Developers**: 1-9 days of activity per month
- **Other Active Developers**: Contributors with at least one activity in the rolling 28-day window
        """),
        "Data Sources": mo.md("""
- [Open Dev Data](https://www.developerreport.com) by Electric Capital
- Ecosystem definitions from Electric Capital's taxonomy
        """),
        "Methodology": mo.md("""
- A developer is considered "active" if they made at least one commit in the given month
- Developers are deduplicated across multiple repositories and organizations
- Data includes contributions to core protocol repositories and major ecosystem projects
- Metrics are calculated on a rolling 28-day basis and aggregated monthly
- Data is refreshed monthly
        """),
    })
    return


@app.cell(hide_code=True)
def _(df, mo):
    ecosystem_list = sorted(list(df['ecosystem_name'].unique()))
    ecosystem_selector = mo.ui.dropdown(
        options=ecosystem_list,
        value='Ethereum',
        label='Select Ecosystem',
        full_width=False
    )
    ecosystem_selector
    return (ecosystem_selector,)


@app.cell(hide_code=True)
def _(df, ecosystem_selector, mo):
    _df = df[df['ecosystem_name'] == ecosystem_selector.value].copy()
    _latest = _df.iloc[-1]
    _previous = _df.iloc[-2] if len(_df) > 1 else _latest

    _current_devs = int(_latest['all_devs'])
    _change = _current_devs - int(_previous['all_devs'])
    _change_pct = (_change / int(_previous['all_devs']) * 100) if int(_previous['all_devs']) > 0 else 0
    _avg_devs = int(_df['all_devs'].mean())
    _peak_devs = int(_df['all_devs'].max())
    _ft_devs = int(_latest['full_time_devs'])

    mo.hstack([
        mo.stat(
            value=f"{_current_devs:,}",
            label="Monthly Active Devs",
            bordered=True,
            caption=f"{'+'if _change >= 0 else ''}{_change:,} ({_change_pct:+.1f}%) from prior month"
        ),
        mo.stat(
            value=f"{_ft_devs:,}",
            label="Full-Time Devs",
            bordered=True,
            caption="10+ active days/month"
        ),
        mo.stat(
            value=f"{_avg_devs:,}",
            label="Average MAD",
            bordered=True,
            caption="Across all months tracked"
        ),
        mo.stat(
            value=f"{_peak_devs:,}",
            label="Peak MAD",
            bordered=True,
            caption="All-time high"
        ),
    ], widths="equal", gap=1)
    return


@app.cell(hide_code=True)
def _(df, ecosystem_selector, mo, px):
    _df = df[df['ecosystem_name'] == ecosystem_selector.value].copy()

    _fig = px.area(
        data_frame=_df,
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
        linecolor="#1F2937",
        linewidth=1,
        ticks="outside",
        tickformat="%b %Y"
    )

    _fig.update_yaxes(
        title="Monthly Active Developers",
        showgrid=True,
        gridcolor="#E5E7EB",
        zeroline=True,
        zerolinecolor="#E5E7EB",
        zerolinewidth=1,
        linecolor="#1F2937",
        linewidth=1,
        ticks="outside",
        range=[0, _df['all_devs'].max() * 1.1] if len(_df) > 0 else None
    )

    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def _(df, ecosystem_selector, mo, pd, px):
    _raw = df[df['ecosystem_name'] == ecosystem_selector.value].copy()

    _by_type = pd.concat([
        _raw[['day']].assign(dev_count=_raw['full_time_devs'], developer_type='Full-Time Developers'),
        _raw[['day']].assign(dev_count=_raw['part_time_devs'], developer_type='Part-Time Developers'),
        _raw[['day']].assign(dev_count=_raw['all_devs'] - _raw['full_time_devs'] - _raw['part_time_devs'], developer_type='Other Active Developers'),
    ])

    _fig2 = px.area(
        data_frame=_by_type,
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
        linecolor="#1F2937",
        linewidth=1,
        ticks="outside",
        tickformat="%b %Y"
    )

    _fig2.update_yaxes(
        title="Number of Developers",
        showgrid=True,
        gridcolor="#E5E7EB",
        zeroline=True,
        zerolinecolor="#E5E7EB",
        zerolinewidth=1,
        linecolor="#1F2937",
        linewidth=1,
        ticks="outside"
    )

    mo.ui.plotly(_fig2, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def _(mo, pd, pyoso_db_conn):
    with mo.persistent_cache("eco_mads_data"):
        df = mo.sql(
            f"""
            SELECT
                e.name AS ecosystem_name,
                mads.day,
                mads.all_devs,
                mads.full_time_devs,
                mads.part_time_devs
            FROM stg_opendevdata__eco_mads AS mads
            JOIN stg_opendevdata__ecosystems AS e
                ON mads.ecosystem_id = e.id
            WHERE mads.day >= DATE('2024-01-01')
            ORDER BY 1, 2
            """,
            output=False,
            engine=pyoso_db_conn
        )
        df['day'] = pd.to_datetime(df['day'])
    return (df,)


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
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
