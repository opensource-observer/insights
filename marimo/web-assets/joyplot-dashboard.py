import marimo

__generated_with = "0.17.4"
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
    NUM_PROJECTS = 15
    DISPLAY_MONTHS = 12

    # UI Config

    METRICS_TRANSFORMS = {}
    _fmt = lambda x: f"{x:,.0f}" if pd.notna(x) else ""
    METRICS_FORMATS = {_ml: _fmt for _ml in METRIC_LABELS}
    DEFAULT_METRIC = 'User Events'
    return (
        DEFAULT_METRIC,
        DISPLAY_MONTHS,
        METRICS_KEY,
        METRICS_TRANSFORMS,
        METRIC_LABELS,
        METRIC_NAMES,
        NUM_PROJECTS,
        START_DATE,
        STOP_DATE,
    )


@app.cell
def get_user_inputs(DEFAULT_METRIC, DISPLAY_MONTHS, METRIC_LABELS, mo):
    metric_input = mo.ui.dropdown(
        options=METRIC_LABELS,
        value=DEFAULT_METRIC,
        label='Metric:'
    )
    months_input = mo.ui.slider(3, 24, value=DISPLAY_MONTHS, show_value=True, label='Display last N months:')
    smoothing_input = mo.ui.slider(0, 12, value=0, show_value=True, label='Smoothing window (weeks):')
    return metric_input, months_input, smoothing_input


@app.cell
def generate_dummy_data(
    METRIC_NAMES,
    NUM_PROJECTS,
    START_DATE,
    STOP_DATE,
    np,
    pd,
):
    # Generate project names
    project_names = [
        "Señor Bear","Signal Layer","Axiom Labs","Kernel Compute","TensorPath",
        "Modular Stack","StreamForge","NexusAI","Epoch Systems","SignalMesh",
        "Relay Labs","ComputeCore","InsightStream","PrimeLayer","OpenCascade",
        "VectorBase","Pioneer Protocol","BlockMetric","DeltaMesh","Origin Systems",
        "Helix Compute","Frontier Analytics","LayerSense","Protocol Works","IndexFlow",
        "AtlasStack","ClearCompute","CodeMesh","DataRelay","VectorChain"
    ]

    # Generate date range (daily for higher granularity)
    dates = pd.date_range(start=START_DATE, end=STOP_DATE, freq='D')
    T = len(dates)

    data = []
    rng = np.random.default_rng(42)

    # Create 3–5 global shock days that affect everyone
    n_shocks = int(rng.integers(3, 6))
    shock_idx = sorted(rng.choice(np.arange(7, max(8, T-7)), size=n_shocks, replace=False)) if T > 14 else []
    shock_series = np.ones(T, dtype=float)
    for d in shock_idx:
        shock_series[d] = float(rng.uniform(0.8, 1.2))

    # Bucket assignment probabilities
    buckets = [
        ("hyper",     0.20, (2.0, 9.0)),
        ("fast",      0.20, (1.5, 3.0)),
        ("strong",    0.20, (1.1, 2.0)),
        ("mature",    0.20, (1.0, 1.2)),
        ("declining", 0.20, (0.8, 1.0)),
    ]
    bucket_names = [b[0] for b in buckets]
    bucket_probs = np.array([b[1] for b in buckets])
    bucket_probs = bucket_probs / bucket_probs.sum()

    for project in project_names[:NUM_PROJECTS]:
        base_mult = (abs(hash(project)) % 100) / 50 + 0.5
        bucket = rng.choice(bucket_names, p=bucket_probs)
        growth_min, growth_max = next(r for n,p,r in buckets if n == bucket)
        annual_growth = float(rng.uniform(growth_min, growth_max))
        daily_rate = np.log(annual_growth) / 365.0  # exponential trend per day

        # Optional project-level weekend effect (persistent)
        weekend_effect = 1.0
        if rng.random() < 0.5:
            weekend_effect = float(rng.uniform(0.80, 1.20))

        # Starting levels per metric
        starting_values = {}
        first_date = dates[0]
        for metric in METRIC_NAMES:
            if metric == 'active_developers':
                start_val = int(8 + base_mult * 22)
            elif metric == 'revenue':
                start_val = int(9000 + base_mult * 22000)
            elif metric == 'active_users':
                start_val = int(120 + base_mult * 480)
            elif metric == 'user_events':
                start_val = int(1500 + base_mult * 11000)
            else:
                start_val = int(100 * base_mult)
            starting_values[metric] = max(1, start_val)
            data.append({'Date': first_date,'Project': project,'Metric': metric,'Amount': starting_values[metric]})
        prev = starting_values.copy()

        # Mean-reverting noise parameters around the exponential trend
        rho = 0.85  # mean reversion of deviation
        sigma = 0.06  # daily noise
        deviation = {m: 0.0 for m in METRIC_NAMES}

        for i, date in enumerate(dates[1:], start=1):
            # Exponential trend factor relative to start
            trend_factor = float(np.exp(daily_rate * i))
            shock = float(shock_series[i])
            is_weekend = date.weekday() >= 5

            for metric in METRIC_NAMES:
                # Update deviation with mean reversion
                deviation[metric] = rho * deviation[metric] + rng.normal(0.0, sigma)
                # Clip deviation to +/-20%
                deviation[metric] = float(np.clip(deviation[metric], -0.20, 0.20))

                weekend_factor = weekend_effect if is_weekend else 1.0
                base = starting_values[metric]
                value = base * trend_factor * (1.0 + deviation[metric]) * weekend_factor * shock
                value = max(1.0, value)

                # Hard overall cap at 6× initial value
                value = min(value, base * 6.0)

                new_value = int(round(value))
                prev[metric] = new_value
                data.append({'Date': date,'Project': project,'Metric': metric,'Amount': new_value})

    # Final DataFrame
    df_raw = pd.DataFrame(data)
    return (df_raw,)


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
def generate_teal_joyplot(go, np, pd, px):
    def rgba_from_rgb(rgb, alpha):
        return rgb.replace("rgb", "rgba").replace(")", f",{alpha})")

    def make_teal_joyplot(df, project_col='Project', date_col='Date', amount_col='Amount', smoothing=7, display_months=None):
        # Build wide table (date x project)
        wide = df.pivot_table(index=date_col, columns=project_col, values=amount_col, aggfunc='sum').sort_index()

        # Convert smoothing (weeks) to rolling window size based on data frequency
        if len(wide.index) > 1:
            idx = pd.to_datetime(wide.index)
            # Convert median datetime step to numeric days
            diffs_days = np.diff(idx.values).astype('timedelta64[D]').astype(float)
            step_days = max(1, int(round(np.median(diffs_days))))
        else:
            step_days = 1
        window = int(round(smoothing * 7 / step_days))
        if window and window > 1:
            wide = wide.rolling(window=window, min_periods=1, center=True).mean()

        if display_months is not None and display_months > 0:
            last_date = pd.to_datetime(wide.index.max())
            cutoff = last_date - pd.DateOffset(months=display_months)
            wide_display = wide[wide.index >= cutoff]
        else:
            wide_display = wide

        # Compute growth score per project on the smoothed, unnormalized series within display window
        growth_score = {}
        win = max(7, int(round(30 / step_days)))
        for col in wide_display.columns:
            s = wide_display[col].astype(float)
            if s.dropna().empty:
                growth_score[col] = -np.inf
                continue
            first_avg = s.iloc[:win].mean(skipna=True)
            last_avg = s.iloc[-win:].mean(skipna=True)
            if pd.notna(first_avg) and first_avg > 0 and pd.notna(last_avg):
                growth_score[col] = (last_avg - first_avg) / first_avg
            else:
                growth_score[col] = -np.inf

        # Normalize per project with soft clipping of outliers
        wide_norm = wide_display.copy()
        for col in wide_display.columns:
            non_zero_count = (wide_display[col] > 0).sum()
            if non_zero_count > 24:
                threshold = float(wide_display[col].quantile(0.95))
                wide_norm[col] = wide_norm[col].clip(upper=threshold)
            denom = wide_norm[col].max(skipna=True)
            wide_norm[col] = wide_norm[col] / (denom if pd.notna(denom) and denom != 0 else 1.0)

        # Order projects by growth score (fastest growing at bottom for right-side labels to stand out)
        cols = sorted(list(wide_norm.columns), key=lambda c: growth_score.get(c, -np.inf))
        cmap = px.colors.sequential.Teal
        cmap_subset = cmap[len(cmap)//2:][::-1]

        n = len(cols)
        proj_colors = {}
        for rank, col in enumerate(cols):
            idx = int(round(rank * (len(cmap_subset) - 1) / max(1, n - 1)))
            proj_colors[col] = cmap_subset[idx]

        fig = go.Figure()
        gap = 1.10
        fill_alpha = 0.40
        tickvals, ticktext = [], []

        last_date = wide_norm.index.max()

        for i, col in enumerate(cols):
            y_offset = i * gap
            y_vals = wide_norm[col].fillna(0).values
            x_vals = wide_norm.index

            color = proj_colors[col]
            fill_color = rgba_from_rgb(color, fill_alpha)

            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=np.full(y_vals.shape, y_offset, dtype=float),
                    mode="lines",
                    line=dict(width=0),
                    hoverinfo="skip",
                    showlegend=False
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals + y_offset,
                    mode="lines",
                    fill="tonexty",
                    line=dict(color=color, width=1.0),
                    line_shape="spline",
                    fillcolor=fill_color,
                    name=col,
                    customdata=np.c_[wide_norm[col].reindex(x_vals).fillna(0).values * 100],
                    hovertemplate="<b>%{fullData.name}</b><br>Month: %{x|%b %Y}<br>Scaled: %{customdata[0]:,.0f}%<extra></extra>",
                    showlegend=False
                )
            )

            tickvals.append(y_offset)
            # Show cumulative change over display window (last vs first window)
            series_display = wide_display[col]
            first_avg = series_display.iloc[:win].mean(skipna=True)
            last_avg = series_display.iloc[-win:].mean(skipna=True)
            if pd.notna(first_avg) and first_avg != 0 and pd.notna(last_avg):
                change = (last_avg - first_avg) / first_avg * 100
                label = f"{change:+.0f}%"
            else:
                label = "--"
            ticktext.append(f"<b>{col}</b>: {label}")

        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(size=12, color="#111"),
            margin=dict(l=0, r=80, t=0, b=0),
            showlegend=False,
            title=dict(text="", x=0, xanchor="left", font=dict(size=14, color="#111"))
        )
        fig.update_xaxes(title="", showgrid=False, visible=False, linecolor="#000", linewidth=1)
        fig.update_yaxes(
            title="",
            side="right",
            showgrid=False,
            tickmode="array",
            ticklabelposition="outside top",
            ticklabelstandoff=5,
            tickvals=tickvals,
            ticktext=ticktext,
            zeroline=False,
            tickcolor="#000",
            showline=False
        )
        return fig
    return (make_teal_joyplot,)


@app.cell
def build_dashboard(
    df,
    make_teal_joyplot,
    metric_input,
    mo,
    months_input,
    smoothing_input,
):
    _sel = metric_input.value

    # Teal Joyplot for selected metric across projects
    _df_sel = df[df['Metric']==_sel].copy()
    joyplot_header = mo.md(f"### {_sel} — Teal Joyplot Over Time")
    joyplot = mo.ui.plotly(
        make_teal_joyplot(
            df=_df_sel.rename(columns={'Project':'Project','Date':'Date','Amount':'Amount'}),
            smoothing=int(smoothing_input.value),
            display_months=int(months_input.value)
        ),
        config={'displayModeBar': False}
    )
    return joyplot, joyplot_header


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
def show_dashboard(
    joyplot,
    joyplot_header,
    metric_input,
    mo,
    months_input,
    smoothing_input,
):
    mo.vstack([
        mo.hstack([
            mo.md(f"## **Growth Dashboard — Joyplot**"),
            mo.hstack([metric_input, months_input, smoothing_input], justify='end', gap=2, align='end')
        ]),
        mo.vstack([joyplot_header, joyplot], gap=1),
    ])
    return


if __name__ == "__main__":
    app.run()
