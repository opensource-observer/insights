import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Protocol Labs Network Ecosystem Health
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">Protocol Labs</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-12</span></small>
    """)
    return


@app.cell(hide_code=True)
def _(headline_1, headline_2, headline_3, headline_4, headline_5, mo):
    _context = f"""
    - This analysis covers Protocol Labs Network (PLN) developer activity from 2020 to present
    - Collections in scope: protocol-labs-network, filecoin-core, filecoin-builders
    - Lifecycle metrics are based on GitHub activity (commits, issues, PRs, code reviews)
    - Full-time contributors have 10+ days of activity per month; part-time have 1-9 days
    - Data is lagged by 2 months to ensure completeness
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
def _(PLOTLY_LAYOUT, df_active_contributors, mo, pd, px, ref_month):
    _df = df_active_contributors.copy()
    _df['sample_date'] = pd.to_datetime(_df['sample_date'])

    # Calculate metrics for headline using 2-month lagged data
    _ref_date = pd.to_datetime(ref_month)
    _latest_data = _df[_df['sample_date'] == _ref_date]
    _latest_active = _latest_data['total_active'].sum() if not _latest_data.empty else 0
    _historical_avg = _df['total_active'].mean()
    _pct_vs_avg = ((_latest_active - _historical_avg) / _historical_avg) * 100 if _historical_avg > 0 else 0

    headline_1 = f"PLN has {_latest_active:,.0f} active contributors as of {ref_month}, {'above' if _pct_vs_avg > 0 else 'below'} the historical average by {abs(_pct_vs_avg):.0f}%"

    # Create visualization
    _fig = px.area(data_frame=_df, x='sample_date', y='total_active')
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_traces(line=dict(color='#1f77b4', width=2), fillcolor='rgba(31, 119, 180, 0.3)')

    mo.vstack([
        mo.md(f"### **{headline_1}**"),
        mo.md("Total active contributors (full-time + part-time) across all PLN projects over time."),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return (headline_1,)


@app.cell(hide_code=True)
def _(
    LIFECYCLE_COLORS,
    LIFECYCLE_LABELS,
    LIFECYCLE_ORDER,
    PLOTLY_LAYOUT,
    df_lifecycle_breakdown,
    mo,
    pd,
    px,
    ref_month,
):
    _df = df_lifecycle_breakdown.copy()
    _df['sample_date'] = pd.to_datetime(_df['sample_date'])

    # Map to human-readable labels
    _df['lifecycle_label'] = _df['lifecycle_state'].map(LIFECYCLE_LABELS)

    # Get reference month breakdown
    _ref_date = pd.to_datetime(ref_month)
    _latest = _df[_df['sample_date'] == _ref_date]

    _full_time = _latest[_latest['lifecycle_state'].str.contains('full_time', na=False)]['developer_count'].sum()
    _part_time = _latest[_latest['lifecycle_state'].str.contains('part_time', na=False) & ~_latest['lifecycle_state'].str.contains('full_time', na=False)]['developer_count'].sum()
    _first_time = _latest[_latest['lifecycle_state'] == 'first_time_contributor']['developer_count'].sum()
    _total = _full_time + _part_time + _first_time

    _full_time_pct = (_full_time / _total * 100) if _total > 0 else 0

    headline_2 = f"Full-time contributors make up {_full_time_pct:.0f}% of active developers ({_full_time:,.0f} full-time, {_part_time:,.0f} part-time, {_first_time:,.0f} first-time)"

    # Stacked area chart with labels ordered logically
    _df_pivot = _df.pivot_table(
        index='sample_date', 
        columns='lifecycle_label', 
        values='developer_count', 
        aggfunc='sum'
    ).fillna(0).reset_index()

    _df_melted = _df_pivot.melt(id_vars='sample_date', var_name='State', value_name='Count')

    # Order states logically
    _df_melted['State'] = pd.Categorical(
        _df_melted['State'],
        categories=[s for s in LIFECYCLE_ORDER if s in _df_melted['State'].unique()],
        ordered=True
    )
    _df_melted = _df_melted.sort_values(['sample_date', 'State'])

    _fig = px.area(
        data_frame=_df_melted, 
        x='sample_date', 
        y='Count', 
        color='State',
        color_discrete_map=LIFECYCLE_COLORS,
        category_orders={'State': LIFECYCLE_ORDER},
        labels={'State': 'Lifecycle State', 'Count': 'Contributors', 'sample_date': ''}
    )
    _fig.update_layout(**PLOTLY_LAYOUT)

    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_2}**

        Breakdown of contributor lifecycle states over time. Full-time contributors (10+ active days/month) drive sustained development.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return (headline_2,)


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_collection_comparison, mo, pd, px, ref_month):
    _df = df_collection_comparison.copy()
    _df['sample_date'] = pd.to_datetime(_df['sample_date'])

    # Get reference month totals by collection
    _ref_date = pd.to_datetime(ref_month)
    _latest = _df[_df['sample_date'] == _ref_date].groupby('collection')['developer_count'].sum().reset_index()
    
    if not _latest.empty:
        _top_collection = _latest.loc[_latest['developer_count'].idxmax(), 'collection']
        _top_count = _latest['developer_count'].max()
    else:
        _top_collection = 'N/A'
        _top_count = 0

    headline_3 = f"{_top_collection} leads with {_top_count:,.0f} active contributors, showing the distribution of developer activity across PLN collections"

    # Line chart by collection
    _df_agg = _df.groupby(['sample_date', 'collection'], as_index=False)['developer_count'].sum()

    _fig = px.line(data_frame=_df_agg, x='sample_date', y='developer_count', color='collection')
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_traces(line=dict(width=2.5))

    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_3}**

        Comparing developer activity across the three main PLN collections.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return (headline_3,)


@app.cell(hide_code=True)
def _(df_top_projects, mo):
    _df = df_top_projects.copy()

    _top_project = _df.iloc[0]['project'] if len(_df) > 0 else 'N/A'
    _top_contributors = _df.iloc[0]['avg_monthly_contributors'] if len(_df) > 0 else 0
    _top_10_total = _df.head(10)['avg_monthly_contributors'].sum()

    headline_4 = f"{_top_project} leads with {_top_contributors:.0f} avg monthly full-time contributors; top 10 projects account for {_top_10_total:.0f} contributors"

    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_4}**

        Projects ranked by average monthly full-time contributors over the past year.
        """),
        mo.ui.table(
            _df.head(15).reset_index(drop=True),
            format_mapping={'avg_monthly_contributors': '{:,.1f}'},
            show_column_summaries=False,
            show_data_types=False,
            page_size=15
        )
    ])
    return (headline_4,)


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_cohort_retention, mo, pd, px):
    _df = df_cohort_retention.copy()

    if not _df.empty:
        _df['cohort_month'] = pd.to_datetime(_df['cohort_month'])
        _df['cohort_label'] = _df['cohort_month'].dt.strftime('%Y-%m')

        # Calculate retention percentage relative to month 0
        _month_0 = _df[_df['months_since_entry'] == 0].set_index('cohort_label')['cohort_size'].to_dict()
        _df['initial_size'] = _df['cohort_label'].map(_month_0)
        _df['retention_pct'] = (_df['active_count'] / _df['initial_size'] * 100).round(1)

        # Get average retention at each month
        _avg_retention = _df.groupby('months_since_entry')['retention_pct'].mean()
        _avg_3mo = _avg_retention.get(3, 0)
        _avg_6mo = _avg_retention.get(6, 0)

        headline_5 = f"Average contributor retention is {_avg_3mo:.0f}% after 3 months and {_avg_6mo:.0f}% after 6 months from becoming a regular contributor"

        # Create cohort retention heatmap
        _pivot = _df.pivot_table(
            index='cohort_label',
            columns='months_since_entry',
            values='retention_pct'
        ).fillna(0)

        _fig = px.imshow(
            _pivot,
            labels=dict(x="Months Since Entry", y="Cohort", color="Retention %"),
            aspect="auto",
            color_continuous_scale="Blues"
        )
        _fig.update_layout(**PLOTLY_LAYOUT)
        _fig.update_layout(
            margin=dict(t=20, l=80, r=20, b=50),
            coloraxis_colorbar=dict(title="Retention %")
        )

        _chart = mo.ui.plotly(_fig, config={'displayModeBar': False})
    else:
        headline_5 = "Cohort retention data is being calculated"
        _chart = mo.md("*Cohort data unavailable*")

    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_5}**

        Cohort retention analysis: tracking how many contributors remain active N months after becoming a New Full-Time or New Part-Time contributor.
        """),
        _chart
    ])
    return (headline_5,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Project Comparison

    Select a project to compare its contributor activity against the PLN ecosystem average.
    """)
    return


@app.cell(hide_code=True)
def _(df_project_list, mo):
    project_selector = mo.ui.dropdown(
        options=df_project_list['project'].tolist() if not df_project_list.empty else [],
        value=df_project_list['project'].iloc[0] if not df_project_list.empty else None,
        label="Select Project:"
    )
    project_selector
    return (project_selector,)


@app.cell(hide_code=True)
def _(
    PLOTLY_LAYOUT,
    df_pln_avg,
    df_project_timeseries,
    mo,
    pd,
    project_selector,
    px,
):
    if project_selector.value and not df_project_timeseries.empty:
        _df_proj = df_project_timeseries[df_project_timeseries['project'] == project_selector.value].copy()
        _df_proj['sample_date'] = pd.to_datetime(_df_proj['sample_date'])

        _df_avg = df_pln_avg.copy()
        _df_avg['sample_date'] = pd.to_datetime(_df_avg['sample_date'])
        _df_avg['project'] = 'PLN Average'

        # Combine for comparison
        _df_combined = pd.concat([
            _df_proj[['sample_date', 'project', 'total_active']],
            _df_avg[['sample_date', 'project', 'total_active']]
        ])

        _fig = px.line(
            data_frame=_df_combined,
            x='sample_date',
            y='total_active',
            color='project'
        )
        _fig.update_layout(**PLOTLY_LAYOUT)
        _fig.update_traces(line=dict(width=2.5))

        _chart = mo.ui.plotly(_fig, config={'displayModeBar': False})
    else:
        _chart = mo.md("*Select a project to see comparison*")

    mo.vstack([
        mo.md(f"### {project_selector.value or 'Project'} vs PLN Average"),
        _chart
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    # Methodology Details

    ## Part 1. Data Collection

    Developer activity data is sourced from GitHub Archive via OSO's data pipeline. Events tracked include:
    - Commits (`COMMIT_CODE`)
    - Issues (`ISSUE_OPENED`, `ISSUE_CLOSED`, `ISSUE_COMMENT`, `ISSUE_REOPENED`)
    - Pull Requests (`PULL_REQUEST_OPENED`, `PULL_REQUEST_MERGED`, `PULL_REQUEST_CLOSED`, `PULL_REQUEST_REOPENED`)
    - Code Reviews (`PULL_REQUEST_REVIEW_COMMENT`)

    ## Part 2. Lifecycle Classification

    Contributors are classified based on their monthly activity level:

    \[
    \texttt{Activity Level} = \begin{cases}
    \text{Full-time} & \text{if days active} \geq 10 \\
    \text{Part-time} & \text{if } 1 \leq \text{days active} < 10 \\
    \text{Inactive} & \text{if days active} = 0
    \end{cases}
    \]

    Lifecycle transitions are tracked month-over-month to identify:
    - **First-time contributors**: First contribution in the current period
    - **New full/part-time**: Transitioned from first-time to engaged
    - **Active full/part-time**: Continued engagement at same level
    - **Reactivated**: Returned after a gap in activity
    - **Churned**: No activity in current period after being active

    ## Part 3. Assumptions and Limitations

    - Only public GitHub activity is tracked; private repositories are excluded
    - Bot accounts are filtered out where identifiable
    - Data is refreshed monthly with backfill
    - Contributions made while repos were private or under different orgs are not captured
    """)
    return


@app.cell
def _(mo, pd, pyoso_db_conn):
    # Reference month: 2 months before current date
    ref_month = (pd.Timestamp.now() - pd.DateOffset(months=2)).strftime('%Y-%m-01')

    df_active_contributors = mo.sql(
        f"""
        SELECT 
          ts.sample_date,
          SUM(ts.amount) AS total_active
        FROM timeseries_metrics_by_collection_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN collections_v1 c USING (collection_id)
        WHERE c.collection_name = 'protocol-labs-network'
        AND m.metric_event_source = 'GITHUB'
        AND m.metric_model IN ('active_full_time_contributor', 'active_part_time_contributor', 'first_time_contributor')
        AND m.metric_time_aggregation = 'monthly'
        AND ts.sample_date <= DATE('{ref_month}')
        GROUP BY ts.sample_date
        ORDER BY ts.sample_date
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_active_contributors['sample_date'] = pd.to_datetime(df_active_contributors['sample_date'])
    return df_active_contributors, ref_month


@app.cell
def _(mo, pd, pyoso_db_conn, ref_month):
    df_lifecycle_breakdown = mo.sql(
        f"""
        SELECT 
          ts.sample_date,
          m.metric_model AS lifecycle_state,
          SUM(ts.amount) AS developer_count
        FROM timeseries_metrics_by_collection_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN collections_v1 c USING (collection_id)
        WHERE c.collection_name = 'protocol-labs-network'
        AND m.metric_event_source = 'GITHUB'
        AND m.metric_model LIKE '%contributor%'
        AND m.metric_model NOT LIKE 'change_in%'
        AND m.metric_time_aggregation = 'monthly'
        AND ts.sample_date <= DATE('{ref_month}')
        GROUP BY ts.sample_date, m.metric_model
        ORDER BY ts.sample_date, m.metric_model
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_lifecycle_breakdown['sample_date'] = pd.to_datetime(df_lifecycle_breakdown['sample_date'])
    return (df_lifecycle_breakdown,)


@app.cell
def _(mo, pd, pyoso_db_conn, ref_month):
    df_collection_comparison = mo.sql(
        f"""
        SELECT 
          c.display_name AS collection,
          ts.sample_date,
          m.metric_model AS lifecycle_state,
          SUM(ts.amount) AS developer_count
        FROM timeseries_metrics_by_collection_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN collections_v1 c USING (collection_id)
        WHERE c.collection_name IN ('protocol-labs-network', 'filecoin-core', 'filecoin-builders')
        AND m.metric_event_source = 'GITHUB'
        AND m.metric_model IN ('active_full_time_contributor', 'active_part_time_contributor')
        AND m.metric_time_aggregation = 'monthly'
        AND ts.sample_date <= DATE('{ref_month}')
        GROUP BY c.display_name, ts.sample_date, m.metric_model
        ORDER BY ts.sample_date
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_collection_comparison['sample_date'] = pd.to_datetime(df_collection_comparison['sample_date'])
    return (df_collection_comparison,)


@app.cell
def _(mo, pyoso_db_conn, ref_month):
    df_top_projects = mo.sql(
        f"""
        SELECT 
          p.display_name AS project,
          pbc.collection_name,
          AVG(ts.amount) AS avg_monthly_contributors
        FROM timeseries_metrics_by_project_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN projects_v1 p USING (project_id)
        JOIN projects_by_collection_v1 pbc USING (project_id)
        WHERE pbc.collection_name = 'protocol-labs-network'
        AND m.metric_model = 'active_full_time_contributor'
        AND m.metric_time_aggregation = 'monthly'
        AND ts.sample_date >= DATE_ADD('year', -1, DATE('{ref_month}'))
        AND ts.sample_date <= DATE('{ref_month}')
        GROUP BY p.display_name, pbc.collection_name
        HAVING AVG(ts.amount) > 0
        ORDER BY avg_monthly_contributors DESC
        LIMIT 20
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_top_projects,)


@app.cell
def _(mo, pd, pyoso_db_conn, ref_month):
    # Cohort retention: track contributors who became new_full_time or new_part_time
    # and see how many are still active N months later
    df_cohort_retention = mo.sql(
        f"""
        WITH entry_cohorts AS (
          SELECT 
            ts.sample_date AS cohort_month,
            SUM(ts.amount) AS cohort_size
          FROM timeseries_metrics_by_collection_v0 ts
          JOIN metrics_v0 m USING (metric_id)
          JOIN collections_v1 c USING (collection_id)
          WHERE c.collection_name = 'protocol-labs-network'
          AND m.metric_event_source = 'GITHUB'
          AND m.metric_model IN ('new_full_time_contributor', 'new_part_time_contributor')
          AND m.metric_time_aggregation = 'monthly'
          AND ts.sample_date <= DATE('{ref_month}')
          AND ts.sample_date >= DATE_ADD('year', -2, DATE('{ref_month}'))
          GROUP BY ts.sample_date
        ),
        active_counts AS (
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
        )
        SELECT 
          e.cohort_month,
          e.cohort_size,
          DATE_DIFF('month', e.cohort_month, a.sample_date) AS months_since_entry,
          a.total_active AS active_count
        FROM entry_cohorts e
        JOIN active_counts a ON a.sample_date >= e.cohort_month
        WHERE DATE_DIFF('month', e.cohort_month, a.sample_date) BETWEEN 0 AND 12
        ORDER BY e.cohort_month, months_since_entry
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_cohort_retention['cohort_month'] = pd.to_datetime(df_cohort_retention['cohort_month'])
    return (df_cohort_retention,)


@app.cell
def _(mo, pyoso_db_conn):
    df_project_list = mo.sql(
        """
        SELECT DISTINCT p.display_name AS project
        FROM projects_v1 p
        JOIN projects_by_collection_v1 pbc USING (project_id)
        WHERE pbc.collection_name = 'protocol-labs-network'
        ORDER BY p.display_name
        """,
        engine=pyoso_db_conn,
        output=False
    )
    return (df_project_list,)


@app.cell
def _(mo, pd, pyoso_db_conn, ref_month):
    df_project_timeseries = mo.sql(
        f"""
        SELECT 
          p.display_name AS project,
          ts.sample_date,
          SUM(ts.amount) AS total_active
        FROM timeseries_metrics_by_project_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN projects_v1 p USING (project_id)
        JOIN projects_by_collection_v1 pbc USING (project_id)
        WHERE pbc.collection_name = 'protocol-labs-network'
        AND m.metric_event_source = 'GITHUB'
        AND m.metric_model IN ('active_full_time_contributor', 'active_part_time_contributor')
        AND m.metric_time_aggregation = 'monthly'
        AND ts.sample_date <= DATE('{ref_month}')
        GROUP BY p.display_name, ts.sample_date
        ORDER BY ts.sample_date
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_project_timeseries['sample_date'] = pd.to_datetime(df_project_timeseries['sample_date'])
    return (df_project_timeseries,)


@app.cell
def _(df_project_timeseries, pd):
    # PLN average for comparison - calculated from project timeseries data
    df_pln_avg = df_project_timeseries.groupby('sample_date', as_index=False)['total_active'].mean()
    df_pln_avg['sample_date'] = pd.to_datetime(df_pln_avg['sample_date'])
    return (df_pln_avg,)


@app.cell(hide_code=True)
def _():
    # Human-readable labels for lifecycle states (matching draft notebook)
    LIFECYCLE_LABELS = {
        'first_time_contributor': 'first time',
        'active_full_time_contributor': 'full time',
        'new_full_time_contributor': 'new full time',
        'part_time_to_full_time_contributor': 'part time to full time',
        'reactivated_full_time_contributor': 'dormant to full time',
        'active_part_time_contributor': 'part time',
        'new_part_time_contributor': 'new part time',
        'full_time_to_part_time_contributor': 'full time to part time',
        'reactivated_part_time_contributor': 'dormant to part time',
        'churned_contributors': 'dormant',
        'churned_after_first_time_contributor': 'churned (after first time)',
        'churned_after_part_time_contributor': 'churned (after reaching part time)',
        'churned_after_full_time_contributor': 'churned (after reaching full time)',
    }

    # Colors keyed by human-readable labels
    LIFECYCLE_COLORS = {
        'first time': '#4C78A8',
        'full time': '#7A4D9B',
        'new full time': '#9C6BD3',
        'part time to full time': '#B48AEC',
        'dormant to full time': '#C7A7F2',
        'part time': '#41AB5D',
        'new part time': '#74C476',
        'full time to part time': '#A1D99B',
        'dormant to part time': '#C7E9C0',
        'dormant': '#F39C12',
        'first time to dormant': '#F5B041',
        'part time to dormant': '#F8C471',
        'full time to dormant': '#FAD7A0',
        'churned (after first time)': '#D62728',
        'churned (after reaching part time)': '#E57373',
        'churned (after reaching full time)': '#F1948A',
    }

    # Logical ordering for stacking (bottom to top)
    LIFECYCLE_ORDER = [
        'first time',
        'full time',
        'new full time',
        'part time to full time',
        'dormant to full time',
        'part time',
        'new part time',
        'full time to part time',
        'dormant to part time',
        'dormant',
        'first time to dormant',
        'part time to dormant',
        'full time to dormant',
        'churned (after first time)',
        'churned (after reaching part time)',
        'churned (after reaching full time)',
    ]
    return LIFECYCLE_COLORS, LIFECYCLE_LABELS, LIFECYCLE_ORDER


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
