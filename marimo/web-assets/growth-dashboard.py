import marimo

__generated_with = "0.16.2"
app = marimo.App(width="full")


@app.cell
def display_dashboard(
    bar_chart,
    date_input,
    events_stat,
    leaderboard,
    leaderboard_header,
    metric_input,
    mo,
    revenue_stat,
    tvl_stat,
    users_stat,
):
    mo.vstack([
        mo.hstack([
            mo.md("## **Growth Dashboard**"),
            mo.hstack([metric_input, date_input], justify='end', gap=2, align='end')
        ]),
        mo.hstack([revenue_stat, tvl_stat, users_stat, events_stat], widths="equal", gap=1),
        mo.hstack([bar_chart, 
                   mo.vstack([leaderboard_header, leaderboard], gap=1)]
                  , widths=[1,1], wrap=True)
    ])
    return


@app.cell
def build_dashboard(date_input, df, go, metric_input, mo, pd, px):
    _min_start = df[df['Metric'] == 'Revenue']['Date'].min()
    _max_stop = df[df['Metric'] == 'Revenue']['Date'].max()

    try:
        _start, _stop = map(pd.to_datetime, date_input.value)
    except:
        _start, _stop = _min_start, _max_stop
    _start = max(_start, _min_start)
    _stop = min(_stop, _max_stop)
    _prev = (_stop - pd.DateOffset(months=1)).replace(day=1)

    _dff = df[df['Date'].between(_start, _stop)]

    _dff_stop_month = _dff[_dff['Date'] == _stop]
    _piv_stop_month = _dff_stop_month.pivot_table(index='Project', columns='Metric', values='Amount', aggfunc='sum')
    _dff_prev_month = _dff[_dff['Date'] == _prev]
    _piv_prev_month = _dff_prev_month.pivot_table(index='Project', columns='Metric', values='Amount', aggfunc='sum')

    # Create 4 stats for Revenue, TVL, Users, Events
    _stop_rev = _piv_stop_month['Revenue'].sum()
    _prev_rev = _piv_prev_month['Revenue'].sum()

    _stop_tvl = _piv_stop_month['TVL'].sum()
    _prev_tvl = _piv_prev_month['TVL'].sum()

    _stop_users = _piv_stop_month['Users'].sum()
    _prev_users = _piv_prev_month['Users'].sum()

    _stop_events = _piv_stop_month['User Events'].sum()
    _prev_events = _piv_prev_month['User Events'].sum()

    revenue_stat = mo.stat(
        label="Total Revenue",
        bordered=True,
        value=f"${_stop_rev:,.0f}",
        caption=delta_caption(_stop_rev, _prev_rev) + " from last month"
    )

    tvl_stat = mo.stat(
        label="Total TVL",
        bordered=True,
        value=f"${_stop_tvl:,.0f}",
        caption=delta_caption(_stop_tvl, _prev_tvl) + " from last month"
    )

    users_stat = mo.stat(
        label="Total Users",
        bordered=True,
        value=f"{_stop_users:,.0f}",
        caption=delta_caption(_stop_users, _prev_users) + " from last month"
    )

    events_stat = mo.stat(
        label="Total Events",
        bordered=True,
        value=f"{_stop_events:,.0f}",
        caption=delta_caption(_stop_events, _prev_events) + " from last month"
    )

    # Create table with only the selected metric
    _table_data = []

    for project in _piv_stop_month.index:
        _curr = _piv_stop_month.loc[project, metric_input.value] if metric_input.value in _piv_stop_month.columns else 0
        _prev = _piv_prev_month.loc[project, metric_input.value] if project in _piv_prev_month.index and metric_input.value in _piv_prev_month.columns else 0
        _table_data.append({
            'Project': project,
            metric_input.value: _curr,
            'MoM': delta_caption(_curr, _prev)
        })

    _table_df = pd.DataFrame(_table_data)

    # Sort by the selected metric
    _table_df = _table_df.sort_values(by=metric_input.value, ascending=False)

    # Format mapping based on metric type
    if metric_input.value in ['Revenue', 'TVL']:
        _format_map = {metric_input.value: '${:,.0f}'}
    else:
        _format_map = {metric_input.value: '{:,.0f}'}

    leaderboard = mo.ui.table(
        data=_table_df.reset_index(drop=True),
        format_mapping=_format_map,
        show_column_summaries=False,
        show_data_types=False
    )

    # Create header for leaderboard
    leaderboard_header = mo.md(f"### Project Leaderboard - {_stop.strftime('%B %Y')}")

    # Create bar chart with gradient
    _chart_df = _dff[_dff['Metric'] == metric_input.value].groupby('Date')['Amount'].sum().reset_index()
    _chart_df = _chart_df.sort_values('Date')

    # Create color gradient based on date progression
    _n_bars = len(_chart_df)
    _colors = px.colors.sample_colorscale("Teal", [i/(_n_bars-1) if _n_bars > 1 else 0.5 for i in range(_n_bars)])

    _max_Y = _chart_df['Amount'].max()
    _colors = px.colors.sample_colorscale("Teal", [y/_max_Y for y in _chart_df['Amount']])

    _fig = go.Figure()
    _fig.add_trace(go.Bar(
        x=_chart_df['Date'],
        y=_chart_df['Amount'],
        marker=dict(
            color=_colors,
            line=dict(width=0)
        ),
        hovertemplate='<b>%{x|%b %Y}</b><br>%{y:,.0f}<extra></extra>'
    ))

    _fig.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(size=12, color="#111"),
        margin=dict(l=60, r=20, t=20, b=60),
        showlegend=False,
        xaxis=dict(
            title="",
            showgrid=False,
            linecolor="#ddd",
            tickformat="%b %Y"
        ),
        yaxis=dict(
            title=f"Total {metric_input.value}",
            showgrid=True,
            gridcolor="#eee",
            linecolor="#ddd"
        ),
        height=400,
    )

    bar_chart = _fig
    return (
        bar_chart,
        events_stat,
        leaderboard,
        leaderboard_header,
        revenue_stat,
        tvl_stat,
        users_stat,
    )


@app.cell
def get_user_inputs(mo):
    date_input = mo.ui.date_range(
        start='2024-10-01',
        stop='2025-09-01',
        label='Date Range:'
    )
    metric_input = mo.ui.dropdown(
        options=['Revenue', 'TVL', 'Users', 'User Events'],
        value='Revenue',
        label='Metric:'
    )
    return date_input, metric_input


@app.cell
def process_data(df_raw, pd):
    df = df_raw.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df['Metric'] = df['Metric'].map({
        'contract_invocations': 'User Events',
        'farcaster_users': 'Users',
        'layer2_gas_fees_amortized': 'Revenue',
        'defillama_tvl': 'TVL'
    })
    df.loc[df['Metric'] == 'Revenue', 'Amount'] /= 1e18
    df.loc[df['Metric'] == 'Revenue', 'Amount'] *= 4000
    return (df,)


@app.cell
def get_data(mo, pyoso_db_conn):
    df_raw = mo.sql(
        f"""
        SELECT
          sample_date AS "Date",
          project_display_name AS "Project",
          metric_model AS "Metric",
          amount AS "Amount",
          rank AS "Rank"
        FROM int_ranked_projects_by_collection
        WHERE
          collection_name = 'optimism'
          AND metric_event_source = 'BASE'
          AND metric_model IN (
            'defillama_tvl',
            'contract_invocations',
            'layer2_gas_fees_amortized',
            'farcaster_users'
          )
        ORDER BY 1,2,3
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_raw,)


@app.function
def delta_caption(curr, prev):
    if not prev:
        return "--"
    v = (curr - prev) / prev * 100
    c = f"{v:,.1f}%"
    if v > 0:
        c = "+" + c
    return c


@app.cell
def import_libraries():
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    return go, pd, px


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
