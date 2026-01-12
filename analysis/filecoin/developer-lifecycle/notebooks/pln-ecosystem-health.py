import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


# =============================================================================
# HEADER
# =============================================================================


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Protocol Labs Network Ecosystem Health
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">Protocol Labs</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-11</span></small>
    """
    )
    return


# =============================================================================
# EXECUTIVE SUMMARY
# =============================================================================


@app.cell(hide_code=True)
def _(
    headline_1,
    headline_2,
    headline_3,
    headline_4,
    headline_5,
    mo,
):
    _context = f"""
    - This analysis covers Protocol Labs Network (PLN) developer activity from 2020 to present
    - Collections in scope: protocol-labs-network, filecoin-core, filecoin-builders
    - Lifecycle metrics are based on GitHub activity (commits, issues, PRs, code reviews)
    - Full-time contributors have 10+ days of activity per month; part-time have 1-9 days
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


# =============================================================================
# INSIGHT 1: TOTAL ACTIVE CONTRIBUTORS
# =============================================================================


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_active_contributors, mo, pd, px):
    _df = df_active_contributors.copy()
    _df['sample_date'] = pd.to_datetime(_df['sample_date'])
    
    # Calculate metrics for headline
    _latest_month = _df['sample_date'].max()
    _latest_active = _df[_df['sample_date'] == _latest_month]['total_active'].sum()
    _historical_avg = _df['total_active'].mean()
    _pct_vs_avg = ((_latest_active - _historical_avg) / _historical_avg) * 100 if _historical_avg > 0 else 0
    
    headline_1 = f"PLN has {_latest_active:,.0f} active contributors in the latest month, {'above' if _pct_vs_avg > 0 else 'below'} the historical average by {abs(_pct_vs_avg):.0f}%"
    
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


# =============================================================================
# INSIGHT 2: LIFECYCLE DISTRIBUTION
# =============================================================================


@app.cell(hide_code=True)
def _(LIFECYCLE_COLORS, df_lifecycle_breakdown, mo, pd, px):
    _df = df_lifecycle_breakdown.copy()
    _df['sample_date'] = pd.to_datetime(_df['sample_date'])
    
    # Get latest month breakdown
    _latest_month = _df['sample_date'].max()
    _latest = _df[_df['sample_date'] == _latest_month]
    
    _full_time = _latest[_latest['lifecycle_state'].str.contains('full_time', na=False)]['developer_count'].sum()
    _part_time = _latest[_latest['lifecycle_state'].str.contains('part_time', na=False) & ~_latest['lifecycle_state'].str.contains('full_time', na=False)]['developer_count'].sum()
    _first_time = _latest[_latest['lifecycle_state'] == 'first_time_contributor']['developer_count'].sum()
    _total = _full_time + _part_time + _first_time
    
    _full_time_pct = (_full_time / _total * 100) if _total > 0 else 0
    
    headline_2 = f"Full-time contributors make up {_full_time_pct:.0f}% of active developers, with {_full_time:,.0f} full-time, {_part_time:,.0f} part-time, and {_first_time:,.0f} first-time contributors"
    
    # Stacked area chart
    _df_pivot = _df.pivot_table(
        index='sample_date', 
        columns='lifecycle_state', 
        values='developer_count', 
        aggfunc='sum'
    ).fillna(0).reset_index()
    
    _df_melted = _df_pivot.melt(id_vars='sample_date', var_name='State', value_name='Count')
    
    _fig = px.area(
        data_frame=_df_melted, 
        x='sample_date', 
        y='Count', 
        color='State',
        color_discrete_map=LIFECYCLE_COLORS
    )
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(legend=dict(orientation="h", y=-0.15))
    
    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_2}**
        
        Breakdown of contributor lifecycle states over time. Full-time contributors (10+ active days/month) drive sustained development.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return (headline_2,)


# =============================================================================
# INSIGHT 3: COLLECTION COMPARISON
# =============================================================================


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_collection_comparison, mo, pd, px):
    _df = df_collection_comparison.copy()
    _df['sample_date'] = pd.to_datetime(_df['sample_date'])
    
    # Get latest totals by collection
    _latest_month = _df['sample_date'].max()
    _latest = _df[_df['sample_date'] == _latest_month].groupby('collection')['developer_count'].sum().reset_index()
    _top_collection = _latest.loc[_latest['developer_count'].idxmax(), 'collection']
    _top_count = _latest['developer_count'].max()
    
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


# =============================================================================
# INSIGHT 4: TOP PROJECTS
# =============================================================================


@app.cell(hide_code=True)
def _(df_top_projects, mo):
    _df = df_top_projects.copy()
    
    _top_project = _df.iloc[0]['project'] if len(_df) > 0 else 'N/A'
    _top_contributors = _df.iloc[0]['avg_monthly_contributors'] if len(_df) > 0 else 0
    _top_10_total = _df.head(10)['avg_monthly_contributors'].sum()
    
    headline_4 = f"{_top_project} leads with {_top_contributors:.0f} average monthly full-time contributors; top 10 projects account for {_top_10_total:.0f} contributors"
    
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


# =============================================================================
# INSIGHT 5: RETENTION
# =============================================================================


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_retention, mo, pd, px):
    _df = df_retention.copy()
    _df['sample_date'] = pd.to_datetime(_df['sample_date'])
    
    # Calculate retention ratio (returning / (returning + churned))
    _df_pivot = _df.pivot_table(
        index='sample_date',
        columns='category',
        values='count',
        aggfunc='sum'
    ).fillna(0).reset_index()
    
    if 'returning' in _df_pivot.columns and 'churned' in _df_pivot.columns:
        _df_pivot['retention_rate'] = _df_pivot['returning'] / (_df_pivot['returning'] + _df_pivot['churned']) * 100
        _avg_retention = _df_pivot['retention_rate'].mean()
        _latest_retention = _df_pivot['retention_rate'].iloc[-1] if len(_df_pivot) > 0 else 0
    else:
        _avg_retention = 0
        _latest_retention = 0
    
    headline_5 = f"Average contributor retention rate is {_avg_retention:.0f}%, with {_latest_retention:.0f}% of contributors returning in the latest month"
    
    # Dual bar chart: returning vs churned
    _fig = px.bar(
        data_frame=_df,
        x='sample_date',
        y='count',
        color='category',
        barmode='group',
        color_discrete_map={'returning': '#2ecc71', 'churned': '#e74c3c'}
    )
    _fig.update_layout(**PLOTLY_LAYOUT)
    
    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_5}**
        
        Comparing returning contributors (reactivated) vs churned contributors over time.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return (headline_5,)


# =============================================================================
# METHODOLOGY
# =============================================================================


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
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
    """
    )
    return


# =============================================================================
# DATA QUERIES
# =============================================================================


@app.cell
def _(mo, pd, pyoso_db_conn):
    df_active_contributors = mo.sql(
        """
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
        GROUP BY ts.sample_date
        ORDER BY ts.sample_date
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_active_contributors['sample_date'] = pd.to_datetime(df_active_contributors['sample_date'])
    return (df_active_contributors,)


@app.cell
def _(mo, pd, pyoso_db_conn):
    df_lifecycle_breakdown = mo.sql(
        """
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
        GROUP BY ts.sample_date, m.metric_model
        ORDER BY ts.sample_date, m.metric_model
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_lifecycle_breakdown['sample_date'] = pd.to_datetime(df_lifecycle_breakdown['sample_date'])
    return (df_lifecycle_breakdown,)


@app.cell
def _(mo, pd, pyoso_db_conn):
    df_collection_comparison = mo.sql(
        """
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
        GROUP BY c.display_name, ts.sample_date, m.metric_model
        ORDER BY ts.sample_date
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_collection_comparison['sample_date'] = pd.to_datetime(df_collection_comparison['sample_date'])
    return (df_collection_comparison,)


@app.cell
def _(mo, pyoso_db_conn):
    df_top_projects = mo.sql(
        """
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
        AND ts.sample_date >= DATE_ADD('year', -1, CURRENT_DATE)
        GROUP BY p.display_name, pbc.collection_name
        HAVING AVG(ts.amount) > 0
        ORDER BY avg_monthly_contributors DESC
        LIMIT 20
        """,
        engine=pyoso_db_conn,
        output=False
    )
    return (df_top_projects,)


@app.cell
def _(mo, pd, pyoso_db_conn):
    df_retention = mo.sql(
        """
        WITH returning_contributors AS (
          SELECT 
            ts.sample_date,
            'returning' AS category,
            SUM(ts.amount) AS count
          FROM timeseries_metrics_by_collection_v0 ts
          JOIN metrics_v0 m USING (metric_id)
          JOIN collections_v1 c USING (collection_id)
          WHERE c.collection_name = 'protocol-labs-network'
          AND m.metric_event_source = 'GITHUB'
          AND m.metric_model LIKE 'reactivated%'
          AND m.metric_time_aggregation = 'monthly'
          GROUP BY ts.sample_date
        ),
        churned_contributors AS (
          SELECT 
            ts.sample_date,
            'churned' AS category,
            SUM(ts.amount) AS count
          FROM timeseries_metrics_by_collection_v0 ts
          JOIN metrics_v0 m USING (metric_id)
          JOIN collections_v1 c USING (collection_id)
          WHERE c.collection_name = 'protocol-labs-network'
          AND m.metric_event_source = 'GITHUB'
          AND m.metric_model LIKE 'churned%'
          AND m.metric_time_aggregation = 'monthly'
          GROUP BY ts.sample_date
        )
        SELECT * FROM returning_contributors
        UNION ALL
        SELECT * FROM churned_contributors
        ORDER BY sample_date, category
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_retention['sample_date'] = pd.to_datetime(df_retention['sample_date'])
    return (df_retention,)


# =============================================================================
# CONFIGURATION
# =============================================================================


@app.cell(hide_code=True)
def _():
    LIFECYCLE_COLORS = {
        'first_time_contributor': '#4C78A8',
        'active_full_time_contributor': '#7A4D9B',
        'new_full_time_contributor': '#9C6BD3',
        'part_time_to_full_time_contributor': '#B48AEC',
        'reactivated_full_time_contributor': '#C7A7F2',
        'active_part_time_contributor': '#41AB5D',
        'new_part_time_contributor': '#74C476',
        'full_time_to_part_time_contributor': '#A1D99B',
        'reactivated_part_time_contributor': '#C7E9C0',
        'churned_after_first_time_contributor': '#D62728',
        'churned_after_part_time_contributor': '#E57373',
        'churned_after_full_time_contributor': '#F1948A',
    }
    return (LIFECYCLE_COLORS,)


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


# =============================================================================
# BOILERPLATE
# =============================================================================


@app.cell(hide_code=True)
def _():
    import numpy as np
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    return go, np, pd, px


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
