import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # PLN Growth Trends Analysis
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">Protocol Labs</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-12</span></small>
    """)
    return


@app.cell(hide_code=True)
def _(headline_1, headline_2, headline_3, headline_4, headline_5, mo):
    _context = f"""
    - This analysis examines year-over-year growth patterns and momentum indicators for PLN
    - Data covers monthly full-time and part-time contributor activity from 2020 to present
    - Metrics exclude the most recent 2 months to ensure data completeness
    - Growth classifications help identify ecosystem momentum and forecast future activity
    """

    _insights = f"""
    1. {headline_1}.
    2. {headline_2}.
    3. {headline_3}.
    4. {headline_4}.
    5. {headline_5}.
    """

    mo.accordion({
        "Context": _context,
        "Key Insights": _insights,
        "Data Sources": """
        - [OSO API](https://docs.oso.xyz/) - GitHub metrics and developer activity data
        - [OSS Directory](https://github.com/opensource-observer/oss-directory) - Project registry
        - [GitHub Archive](https://www.gharchive.org/) - Historical GitHub events
        """
    })
    return


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_yoy_growth, mo, pd, px):
    _df = df_yoy_growth.copy()
    _df['sample_date'] = pd.to_datetime(_df['sample_date'])
    _df['year'] = _df['sample_date'].dt.year

    # Calculate YoY comparison
    _yearly = _df.groupby('year')['total_contributors'].sum().reset_index()
    if len(_yearly) >= 2:
        _current_year = _yearly.iloc[-1]['total_contributors']
        _prev_year = _yearly.iloc[-2]['total_contributors']
        _yoy_change = ((_current_year - _prev_year) / _prev_year) * 100 if _prev_year > 0 else 0
        _direction = "growth" if _yoy_change > 0 else "decline"
    else:
        _yoy_change = 0
        _direction = "stable"

    headline_1 = f"PLN shows {abs(_yoy_change):.0f}% year-over-year {_direction} in full-time and part-time contributor activity"

    # Bar chart by year
    _fig = px.bar(data_frame=_yearly, x='year', y='total_contributors', text='total_contributors')
    _fig.update_traces(textposition='outside', texttemplate='%{text:,.0f}')
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_xaxes(tickformat='d')

    mo.vstack([
        mo.md(f"### **{headline_1}**"),
        mo.md("Total full-time and part-time contributor months aggregated by year."),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return (headline_1,)


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_momentum, mo, pd, px):
    _df = df_momentum.copy()
    _df['sample_date'] = pd.to_datetime(_df['sample_date'])
    _df = _df.sort_values('sample_date')

    # Calculate 3-month rolling average
    _df['rolling_avg'] = _df['total_active'].rolling(window=3, min_periods=1).mean()

    # Calculate momentum (current vs 3-month-ago)
    _df['momentum'] = _df['rolling_avg'].pct_change(periods=3) * 100

    _latest_momentum = _df['momentum'].iloc[-1] if len(_df) > 0 else 0
    _momentum_direction = "accelerating" if _latest_momentum > 5 else ("decelerating" if _latest_momentum < -5 else "stable")

    headline_2 = f"Ecosystem momentum is {_momentum_direction} with a {abs(_latest_momentum):.0f}% change in 3-month rolling average"

    # Dual axis: rolling avg + momentum
    _fig = px.line(data_frame=_df, x='sample_date', y='rolling_avg')
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_traces(line=dict(color='#1f77b4', width=2.5))

    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_2}**

        3-month rolling average of full-time and part-time contributors. Positive momentum indicates growing engagement.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return (headline_2,)


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_seasonal, mo, pd, px):
    _df = df_seasonal.copy()
    _df['sample_date'] = pd.to_datetime(_df['sample_date'])
    _df['month'] = _df['sample_date'].dt.month
    _df['year'] = _df['sample_date'].dt.year

    # Average by month across years
    _monthly_avg = _df.groupby('month')['total_active'].mean().reset_index()
    _monthly_avg['month_name'] = pd.to_datetime(_monthly_avg['month'], format='%m').dt.strftime('%B')

    _peak_month = _monthly_avg.loc[_monthly_avg['total_active'].idxmax(), 'month_name']
    _low_month = _monthly_avg.loc[_monthly_avg['total_active'].idxmin(), 'month_name']

    headline_3 = f"Activity peaks in {_peak_month} and dips in {_low_month}, showing consistent seasonal patterns"

    # Heatmap by year/month
    _pivot = _df.pivot_table(index='year', columns='month', values='total_active', aggfunc='sum')

    _fig = px.imshow(
        _pivot,
        labels=dict(x="Month", y="Year", color="Contributors"),
        x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        color_continuous_scale='Blues',
        aspect='auto'
    )
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(margin=dict(t=20))

    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_3}**

        Heatmap showing full-time and part-time contributor activity patterns across months and years.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return (headline_3,)


@app.cell(hide_code=True)
def _(GROWTH_COLORS, PLOTLY_LAYOUT, df_velocity, mo, pd, px):
    _df = df_velocity.copy()
    _df['sample_date'] = pd.to_datetime(_df['sample_date'])

    # Calculate velocity change for projects with enough data
    _project_data = _df.groupby('project').agg({
        'sample_date': 'count',
        'velocity': ['mean', 'std']
    }).reset_index()
    _project_data.columns = ['project', 'data_points', 'mean_velocity', 'std_velocity']
    
    # Only include projects with at least 6 data points
    _valid_projects = _project_data[_project_data['data_points'] >= 6]['project'].tolist()
    _df = _df[_df['project'].isin(_valid_projects)]

    # Calculate velocity change for valid projects
    _latest = _df.groupby('project').apply(
        lambda x: x.nlargest(3, 'sample_date')['velocity'].mean()
    ).reset_index(name='recent_velocity')

    _historical = _df.groupby('project').apply(
        lambda x: x.nsmallest(3, 'sample_date')['velocity'].mean()
    ).reset_index(name='historical_velocity')

    _comparison = _latest.merge(_historical, on='project')
    
    # Calculate percentage change, handling zeros
    _comparison['velocity_change'] = _comparison.apply(
        lambda row: ((row['recent_velocity'] - row['historical_velocity']) / row['historical_velocity'] * 100) 
        if row['historical_velocity'] > 0 else 0,
        axis=1
    )
    
    # Remove extreme outliers (> 500% or < -90% change)
    _comparison = _comparison[
        (_comparison['velocity_change'] <= 500) & 
        (_comparison['velocity_change'] >= -90)
    ]
    
    # Add growth classification
    def classify_growth(pct):
        if pct >= 100:
            return 'High Growth'
        elif pct >= 25:
            return 'Moderate Growth'
        elif pct >= -25:
            return 'Stable'
        else:
            return 'Declining'
    
    _comparison['growth_class'] = _comparison['velocity_change'].apply(classify_growth)
    _comparison = _comparison.sort_values('velocity_change', ascending=False)

    # Summary stats
    _growth_summary = _comparison['growth_class'].value_counts()
    _high_growth_count = _growth_summary.get('High Growth', 0)
    _declining_count = _growth_summary.get('Declining', 0)

    headline_4 = f"{_high_growth_count} projects show high growth (>100% velocity increase), while {_declining_count} are declining"

    # Bar chart of velocity changes with color by classification
    _top_15 = _comparison.head(15)
    _fig = px.bar(
        data_frame=_top_15, 
        x='project', 
        y='velocity_change',
        color='growth_class',
        color_discrete_map=GROWTH_COLORS
    )
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(xaxis_tickangle=-45)

    # Growth classification table
    _class_table = _comparison.groupby('growth_class').agg({
        'project': 'count',
        'velocity_change': 'mean'
    }).reset_index()
    _class_table.columns = ['Classification', 'Project Count', 'Avg Growth %']
    _class_table = _class_table.sort_values('Avg Growth %', ascending=False)

    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_4}**

        Project velocity change comparing recent 3 months to historical average. Extreme outliers (>500% or <-90%) are excluded.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
        mo.md("### Growth Classification Summary"),
        mo.ui.table(
            _class_table,
            format_mapping={'Avg Growth %': '{:,.1f}%'},
            show_column_summaries=False,
            show_data_types=False
        )
    ])
    return (headline_4,)


@app.cell(hide_code=True)
def _(df_forecast, mo, np, pd, px):
    _df = df_forecast.copy()
    _df['sample_date'] = pd.to_datetime(_df['sample_date'])
    _df = _df.sort_values('sample_date')

    # Simple linear trend forecast
    _df['month_num'] = range(len(_df))

    if len(_df) >= 12:
        # Fit linear trend on last 12 months
        _recent = _df.tail(12)
        _slope = np.polyfit(_recent['month_num'], _recent['total_active'], 1)[0]
        _last_value = _df['total_active'].iloc[-1]
        _forecast_3m = _last_value + (_slope * 3)
        _forecast_6m = _last_value + (_slope * 6)
        _trend = "upward" if _slope > 0 else "downward"
    else:
        _forecast_3m = _df['total_active'].mean()
        _forecast_6m = _df['total_active'].mean()
        _trend = "flat"

    headline_5 = f"Based on current trends, PLN is projected to have {_forecast_3m:.0f} full-time/part-time contributors in 3 months ({_trend} trajectory)"

    # Line chart with trend
    _fig = px.line(data_frame=_df, x='sample_date', y='total_active')
    _fig.update_traces(line=dict(color='#1f77b4', width=2))

    # Add trend line
    if len(_df) >= 12:
        _trend_line = np.poly1d(np.polyfit(_df['month_num'], _df['total_active'], 1))
        _fig.add_scatter(
            x=_df['sample_date'], 
            y=_trend_line(_df['month_num']),
            mode='lines',
            line=dict(dash='dash', color='#e74c3c', width=1.5),
            name='Trend'
        )

    _fig.update_layout(
        title="",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=12, color="#111"),
        margin=dict(t=0, l=0, r=0, b=50),
        hovermode="x unified",
        xaxis=dict(title="", showgrid=False, linecolor="#000", linewidth=1),
        yaxis=dict(title="", showgrid=True, gridcolor="#DDD", linecolor="#000", linewidth=1)
    )

    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_5}**

        Linear trend projection based on full-time and part-time contributor data. Dashed line shows the trend direction.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
        mo.md(f"""
        | Forecast Period | Projected Contributors |
        |-----------------|----------------------:|
        | 3 months | {_forecast_3m:,.0f} |
        | 6 months | {_forecast_6m:,.0f} |
        """)
    ])
    return (headline_5,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    # Methodology Details

    ## Part 1. Year-over-Year Analysis

    YoY growth is calculated by comparing total contributor-months between consecutive years:

    \[
    \texttt{YoY Growth} = \frac{\texttt{Current Year Total} - \texttt{Previous Year Total}}{\texttt{Previous Year Total}} \times 100
    \]

    ## Part 2. Momentum Calculation

    Momentum uses a 3-month rolling average to smooth short-term fluctuations:

    \[
    \texttt{Momentum}_t = \frac{\texttt{Rolling Avg}_t - \texttt{Rolling Avg}_{t-3}}{\texttt{Rolling Avg}_{t-3}} \times 100
    \]

    ## Part 3. Growth Classification

    Projects are classified based on their velocity change percentage:

    | Classification | Velocity Change |
    |----------------|-----------------|
    | High Growth | ≥ 100% |
    | Moderate Growth | 25% to 99% |
    | Stable | -25% to 24% |
    | Declining | < -25% |

    Extreme outliers (>500% or <-90%) are excluded from the analysis.

    ## Part 4. Forecast Model

    The forecast uses a simple linear regression on the last 12 months of data:

    \[
    \texttt{Forecast}_n = \texttt{Last Value} + (n \times \texttt{Slope})
    \]

    Where slope is derived from ordinary least squares fitting.

    ## Assumptions and Limitations

    - Only full-time (10+ days/month) and part-time (1-9 days/month) contributors are included
    - The most recent 2 months are excluded to ensure data completeness
    - Forecasts assume continuation of current trends
    - Seasonal patterns may affect short-term accuracy
    - External factors (funding changes, market conditions) are not modeled
    """)
    return


@app.cell
def _(mo, pd, pyoso_db_conn):
    # Reference month: 2 months before current date
    ref_month = (pd.Timestamp.now() - pd.DateOffset(months=2)).strftime('%Y-%m-01')

    df_yoy_growth = mo.sql(
        f"""
        SELECT 
          ts.sample_date,
          SUM(ts.amount) AS total_contributors
        FROM timeseries_metrics_by_collection_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN collections_v1 c USING (collection_id)
        WHERE c.collection_name = 'protocol-labs-network'
        AND m.metric_event_source = 'GITHUB'
        AND m.metric_model IN ('active_full_time_contributor', 'active_part_time_contributor')
        AND m.metric_time_aggregation = 'monthly'
        AND ts.sample_date <= DATE('{ref_month}')
        GROUP BY ts.sample_date
        ORDER BY ts.sample_date
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_yoy_growth['sample_date'] = pd.to_datetime(df_yoy_growth['sample_date'])
    return df_yoy_growth, ref_month


@app.cell
def _(mo, pd, pyoso_db_conn, ref_month):
    df_momentum = mo.sql(
        f"""
        SELECT 
          ts.sample_date,
          SUM(ts.amount) AS total_active
        FROM timeseries_metrics_by_collection_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN collections_v1 c USING (collection_id)
        WHERE c.collection_name = 'protocol-labs-network'
        AND m.metric_event_source = 'GITHUB'
        AND m.metric_model IN ('active_full_time_contributor', 'active_part_time_contributor')
        AND m.metric_time_aggregation = 'monthly'
        AND ts.sample_date <= DATE('{ref_month}')
        GROUP BY ts.sample_date
        ORDER BY ts.sample_date
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_momentum['sample_date'] = pd.to_datetime(df_momentum['sample_date'])
    return (df_momentum,)


@app.cell
def _(mo, pd, pyoso_db_conn, ref_month):
    df_seasonal = mo.sql(
        f"""
        SELECT 
          ts.sample_date,
          SUM(ts.amount) AS total_active
        FROM timeseries_metrics_by_collection_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN collections_v1 c USING (collection_id)
        WHERE c.collection_name = 'protocol-labs-network'
        AND m.metric_event_source = 'GITHUB'
        AND m.metric_model IN ('active_full_time_contributor', 'active_part_time_contributor')
        AND m.metric_time_aggregation = 'monthly'
        AND ts.sample_date <= DATE('{ref_month}')
        GROUP BY ts.sample_date
        ORDER BY ts.sample_date
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_seasonal['sample_date'] = pd.to_datetime(df_seasonal['sample_date'])
    return (df_seasonal,)


@app.cell
def _(mo, pd, pyoso_db_conn, ref_month):
    df_velocity = mo.sql(
        f"""
        SELECT 
          p.display_name AS project,
          ts.sample_date,
          SUM(ts.amount) AS velocity
        FROM timeseries_metrics_by_project_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN projects_v1 p USING (project_id)
        JOIN projects_by_collection_v1 pbc USING (project_id)
        WHERE pbc.collection_name = 'protocol-labs-network'
        AND m.metric_model = 'commits'
        AND m.metric_time_aggregation = 'monthly'
        AND ts.sample_date <= DATE('{ref_month}')
        GROUP BY p.display_name, ts.sample_date
        ORDER BY ts.sample_date
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_velocity['sample_date'] = pd.to_datetime(df_velocity['sample_date'])
    return (df_velocity,)


@app.cell
def _(mo, pd, pyoso_db_conn, ref_month):
    df_forecast = mo.sql(
        f"""
        SELECT 
          ts.sample_date,
          SUM(ts.amount) AS total_active
        FROM timeseries_metrics_by_collection_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN collections_v1 c USING (collection_id)
        WHERE c.collection_name = 'protocol-labs-network'
        AND m.metric_event_source = 'GITHUB'
        AND m.metric_model IN ('active_full_time_contributor', 'active_part_time_contributor')
        AND m.metric_time_aggregation = 'monthly'
        AND ts.sample_date <= DATE('{ref_month}')
        GROUP BY ts.sample_date
        ORDER BY ts.sample_date
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_forecast['sample_date'] = pd.to_datetime(df_forecast['sample_date'])
    return (df_forecast,)


@app.cell(hide_code=True)
def _():
    GROWTH_COLORS = {
        'High Growth': '#2ecc71',
        'Moderate Growth': '#3498db',
        'Stable': '#95a5a6',
        'Declining': '#e74c3c'
    }
    return (GROWTH_COLORS,)


@app.cell(hide_code=True)
def _():
    PLOTLY_LAYOUT = dict(
        title="",
        barmode="relative",
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=12, color="#111"),
        margin=dict(t=0, l=0, r=0, b=50),
        legend=dict(
            orientation="v",
            yanchor="top", y=0.98,
            xanchor="left", x=0.02,
            bordercolor="black", borderwidth=1,
            bgcolor="white"
        ),
        xaxis=dict(
            title="",
            showgrid=False,
            linecolor="#000", linewidth=1,
            ticks="outside", tickformat="%b %Y"
        ),
        yaxis=dict(
            title="",
            showgrid=True, gridcolor="#DDD",
            zeroline=True, zerolinecolor="black", zerolinewidth=1,
            linecolor="#000", linewidth=1,
            ticks="outside", range=[0, None]
        )
    )
    return (PLOTLY_LAYOUT,)


@app.cell(hide_code=True)
def _():
    import numpy as np
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    return np, pd, px


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
