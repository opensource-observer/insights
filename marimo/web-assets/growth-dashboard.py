import marimo

__generated_with = "0.16.2"
app = marimo.App(width="full")


@app.cell
def _(pd):
    # Config

    COLLECTION_NAME = 'Dummy Projects'
    METRIC_EVENT_SOURCE = 'Demo'
    METRICS_KEY = {
        'user_events': 'User Events',
        'active_users': 'Active Users',
        'active_developers': 'Active Developers',
        'revenue': 'Revenue ($)',
    }
    METRIC_NAMES = [m for m in METRICS_KEY.keys()]
    METRIC_LABELS = [m for m in METRICS_KEY.values()]
    START_DATE = '2024-10-01'
    STOP_DATE  = '2025-09-30'
    NUM_PROJECTS = 30

    # UI Config

    METRICS_TRANSFORMS = {}
    _fmt = lambda x: f"{x:,.0f}" if pd.notna(x) else ""
    METRICS_FORMATS = {_ml: _fmt for _ml in METRIC_LABELS}
    DEFAULT_METRIC = 'User Events'
    return (
        COLLECTION_NAME,
        DEFAULT_METRIC,
        METRICS_FORMATS,
        METRICS_KEY,
        METRICS_TRANSFORMS,
        METRIC_EVENT_SOURCE,
        METRIC_LABELS,
        METRIC_NAMES,
        NUM_PROJECTS,
        START_DATE,
        STOP_DATE,
    )


@app.cell
def build_dashboard(
    METRICS_FORMATS,
    METRIC_LABELS,
    df,
    go,
    metric_input,
    mo,
    np,
    pd,
    px,
):
    _sel = metric_input.value

    # Get stop month and previous month
    _per_metric_max = df.groupby('Metric')['Date'].max()
    _stop = _per_metric_max.min()
    _prev = (_stop - pd.offsets.MonthBegin(1))

    # Pivot and lookup the stop month vs previous month
    _wide = df.pivot_table(index=['Date','Project'],columns='Metric',values='Amount',aggfunc='sum').sort_index()
    _piv_stop = _wide.xs(_stop,level='Date', drop_level=True)
    _piv_prev = _wide.xs(_prev,level='Date', drop_level=True)
    _all_projects = _piv_stop.index.union(_piv_prev.index)
    _piv_stop = _piv_stop.reindex(_all_projects).fillna(0)
    _piv_prev = _piv_prev.reindex(_all_projects).fillna(0)

    # 1) Stats widgets
    stats = []
    _tot_stop = _piv_stop.sum(axis=0)  # Series indexed by Metric
    _tot_prev = _piv_prev.sum(axis=0)

    _ordered_metrics = [_sel] + [_m for _m in METRIC_LABELS if _m != _sel]
    for _metric in _ordered_metrics:
        _label = f"Total {_metric}" if _metric != _sel else f"⭐️ Total {_metric}"
        _format = METRICS_FORMATS.get(_metric)
        stop_val = float(_tot_stop.get(_metric,0))
        prev_val = float(_tot_prev.get(_metric,0))
        stats.append(
            mo.stat(
                label=_label,
                value=_format(stop_val),
                caption=delta_caption(stop_val,prev_val)+" from last month",
                bordered=True,
            )
        )

    # 2) Leaderboard table for selected metric (vectorized; no per-row .loc in a loop)
    leaderboard_header = mo.md(f"### Project Leaderboard - {_stop.strftime('%B %Y')}")

    _curr = _piv_stop[_sel] if _sel in _piv_stop.columns else pd.Series(0,index=_piv_stop.index)
    _prev_series = _piv_prev[_sel] if _sel in _piv_prev.columns else pd.Series(0,index=_piv_prev.index)
    _table_df = pd.DataFrame({'Project':_all_projects,_sel:_curr.reindex(_all_projects).to_numpy()})
    _prev_vals = _prev_series.reindex(_all_projects).to_numpy()

    _table_df['MoM'] = [delta_caption(c,p) for c,p in zip(_table_df[_sel].to_numpy(),_prev_vals)]
    _table_df['Rank'] = _table_df[_sel].rank(ascending=False, method='min')
    _table_df.sort_values(by=_sel,ascending=False,inplace=True)
    _table_df = _table_df[['Rank', 'Project', _sel, 'MoM']].reset_index(drop=True)
    leaderboard = mo.ui.table(
        data=_table_df,
        format_mapping={_sel:METRICS_FORMATS.get(_sel,lambda x: f"{x:,.0f}")},
        show_column_summaries=False,
        show_data_types=False
    )

    # 3) Bar chart
    _series = _wide[_sel].groupby(level='Date').sum().sort_index()
    _chart_df = _series.rename('Amount').reset_index()

    _n = len(_chart_df)
    if _n <= 1:
        _colors = ["#cccccc"]*_n
    else:
        _ys = _chart_df['Amount'].to_numpy()
        _y_norm = _ys / _ys.max()
        _colors = px.colors.sample_colorscale("Teal", _y_norm.tolist())

    _fig = go.Figure()
    _fig.add_trace(go.Bar(
        x=_chart_df['Date'],
        y=_chart_df['Amount'],
        marker=dict(color=_colors,line=dict(width=0)),
        hovertemplate='<b>%{x|%b %Y}</b><br>%{y:,.0f}<extra></extra>'
    ))
    _fig.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(size=12,color="#111"),
        margin=dict(l=60,r=20,t=20,b=60),
        showlegend=False,
        xaxis=dict(title="",showgrid=False,linecolor="#ddd",tickformat="%b %Y"),
        yaxis=dict(title="",showgrid=True,gridcolor="#eee",linecolor="#ddd"),
        height=360
    )

    chart_header = mo.md(f"### Total {_sel} Over Time")
    bar_chart = mo.ui.plotly(_fig)    

    # 4) Ranking over time with annotations + full monthly axis
    _df_sel = df[df['Metric']==_sel].copy()
    _df_sel['Rank'] = (
        _df_sel
        .sort_values(['Date','Amount'], ascending=[True,False])
        .groupby('Date')['Amount']
        .rank(method='min', ascending=False)
    )

    _rank_piv = _df_sel.pivot_table(
        index='Project',
        columns='Date',
        values='Rank',
        aggfunc='mean'
    )

    # Order columns by time, and projects by rank at the stop month if present, else by row mean
    _rank_piv = _rank_piv.reindex(sorted(_rank_piv.columns), axis=1)
    if _stop in _rank_piv.columns:
        row_order = _rank_piv[_stop].sort_values(na_position='last').index
    else:
        row_order = _rank_piv.mean(axis=1, skipna=True).sort_values(na_position='last').index
    _rank_piv = _rank_piv.loc[row_order]

    # Ensure every month is displayed on X (MS = month start)
    _full_months = pd.date_range(_rank_piv.columns.min(), _rank_piv.columns.max(), freq='MS')
    _rank_piv = _rank_piv.reindex(_full_months, axis=1)

    # Prepare Z and text (annotate ranks; blank where NaN)
    _z = _rank_piv.to_numpy(dtype=float)
    _text = np.where(np.isnan(_z), "", np.char.mod('%d', np.nan_to_num(_z, nan=0)))

    _colorscale = list(reversed(px.colors.sequential.Teal))
    _zmin = 1.0
    _zmax = float(np.nanmax(_z)) if np.isfinite(np.nanmax(_z)) else 1.0

    _heat = go.Figure(
        data=go.Heatmap(
            x=_rank_piv.columns,       # monthly dates
            y=_rank_piv.index,         # projects
            z=_z,
            zmin=_zmin,
            zmax=_zmax,
            colorscale=_colorscale,
            showscale=False,           # remove colorbar
            text=_text,                # annotations
            texttemplate="%{text}",    # show rank integers
            #textfont=dict(size=10, color="#111"),
            xgap=1,
            ygap=1,
            hovertemplate="<b>%{y}</b><br>%{x|%b %Y}<br>Rank: %{z:.0f}<extra></extra>"
        )
    )

    _est_height = max(360, 18*len(_rank_piv.index) + 120)
    _heat.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(size=12, color="#111"),
        margin=dict(l=20, r=20, t=20, b=60),
        height=_est_height,
        showlegend=False,
        xaxis=dict(
            title="",
            type="date",
            tickmode="linear",
            dtick="M1",           # show every month
            tickformat="%b %Y",
            showgrid=False,
            linecolor="#ddd",
            side="top"            # months on top
        ),
        yaxis=dict(
            title="",
            showgrid=False,
            linecolor="#ddd",
            automargin=True,
            autorange="reversed"  # rank 1 at top
        )
    )

    heatmap_header = mo.md(f"### Project Rank by Month — {_sel}")
    heatmap = mo.ui.plotly(_heat)
    return (
        bar_chart,
        chart_header,
        heatmap,
        heatmap_header,
        leaderboard,
        leaderboard_header,
        stats,
    )


@app.cell
def get_user_inputs(DEFAULT_METRIC, METRIC_LABELS, mo):
    metric_input = mo.ui.dropdown(
        options=METRIC_LABELS,
        value=DEFAULT_METRIC,
        label='Metric:'
    )
    return (metric_input,)


@app.cell
def process_data(METRICS_KEY, METRICS_TRANSFORMS, METRIC_NAMES, df_raw, pd):
    df = df_raw.copy()

    df['Date'] = pd.to_datetime(df['Date'])

    _last_date = df['Date'].max()
    _project_metrics = df[df['Date'] == _last_date].groupby('Project')['Metric'].count()
    _projects = _project_metrics[_project_metrics == len(METRIC_NAMES)].index
    df = df[df['Project'].isin(_projects)]

    df['Metric'] = df['Metric'].map(METRICS_KEY)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    for _metric, _transform in METRICS_TRANSFORMS.items():
        df.loc[df['Metric'] == _metric, 'Amount'] = df.loc[df['Metric'] == _metric, 'Amount'].apply(_transform)
    return (df,)


@app.cell
def generate_dummy_data(
    METRIC_NAMES,
    NUM_PROJECTS,
    pd,
    np,
    START_DATE,
    STOP_DATE,
):
    # Generate project names
    project_names = [
        "BlockForge", "CryptoNexus", "DefiCentral", "TokenFlow", "ChainSync",
        "Web3Hub", "DeFiBridge", "SmartChain", "TokenVault", "CryptoNet",
        "BlockLift", "ChainCore", "DeFiPulse", "TokenStream", "Web3Core",
        "BlockChainz", "CryptoBase", "DeFiLink", "TokenStack", "Web3Mesh",
        "ChainForge", "DeFiZone", "TokenWave", "Web3Grid", "BlockNet",
        "CryptoMesh", "DeFiEdge", "TokenFire", "Web3Flow", "ChainBase"
    ]
    
    # Generate date range
    dates = pd.date_range(start=START_DATE, end=STOP_DATE, freq='MS')
    
    # Initialize data list
    data = []
    
    # Generate data for each project, metric combination
    # Store starting values to ensure month-over-month growth on average
    for project in project_names[:NUM_PROJECTS]:
        # Each project has a base multiplier to create variation
        base_mult = hash(project) % 100 / 50 + 0.5  # 0.5 to 1.5
        
        # Determine if this project will have declining trends (some will)
        project_declining = hash(project) % 10 < 2  # 20% of projects declining
        
        # Store starting values for each metric
        starting_values = {}
        
        # Generate first month values
        first_date = dates[0]
        for metric in METRIC_NAMES:
            if metric == 'active_developers':
                start_val = int(10 + base_mult * 20)
            elif metric == 'revenue':
                start_val = int(10000 + base_mult * 20000)
            elif metric == 'active_users':
                start_val = int(100 + base_mult * 500)
            elif metric == 'user_events':
                start_val = int(1000 + base_mult * 12000)
            else:
                start_val = int(100 * base_mult)
            
            starting_values[metric] = start_val
            
            data.append({
                'Date': first_date,
                'Project': project,
                'Metric': metric,
                'Amount': start_val
            })
        
        # Generate remaining months with consistent growth/decline
        previous_values = starting_values.copy()
        
        for date_idx, date in enumerate(dates[1:], 1):
            for metric in METRIC_NAMES:
                # Calculate growth trend (positive for most, negative for declining projects)
                if project_declining:
                    # Declining projects decrease by 1-3% per month
                    growth_rate = np.random.uniform(0.97, 0.99)
                else:
                    # Growing projects increase by 10-20% per month on average (targeting ~15%)
                    growth_rate = np.random.uniform(1.10, 1.20)
                
                # Apply growth with some noise
                noise = np.random.normal(1.0, 0.08)  # Reduced noise for smoother trends
                new_value = int(previous_values[metric] * growth_rate * noise)
                
                # Ensure no negative values
                new_value = max(1, new_value)  # At least 1 for all metrics
                
                # Update previous value for next iteration
                previous_values[metric] = new_value
                
                data.append({
                    'Date': date,
                    'Project': project,
                    'Metric': metric,
                    'Amount': new_value
                })
    
    df_raw = pd.DataFrame(data)
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
    import numpy as np
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    return go, np, pd, px


@app.cell
def setup_marimo():
    import marimo as mo
    return (mo,)


@app.cell
def show_dashboard(bar_chart, chart_header, heatmap, heatmap_header, leaderboard, leaderboard_header, metric_input, mo, stats):
    mo.vstack([
        mo.hstack([
            mo.md(f"## **Growth Dashboard**"),
            mo.hstack([metric_input], justify='end', gap=2, align='end')
        ]),
        mo.hstack(stats, widths="equal", gap=1),
        mo.hstack([
            mo.vstack([chart_header, bar_chart], gap=1),
            mo.vstack([leaderboard_header, leaderboard], gap=1)
        ], widths=[1,1], wrap=True),
        mo.vstack([
            heatmap_header, heatmap
        ])
    ])
    return


if __name__ == "__main__":
    app.run()
