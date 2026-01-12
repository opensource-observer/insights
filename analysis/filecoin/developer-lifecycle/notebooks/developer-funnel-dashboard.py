import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # PLN Developer Funnel Dashboard
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">Protocol Labs</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-12</span></small>
    """)
    return


@app.cell(hide_code=True)
def _(df_kpis, mo):
    if not df_kpis.empty:
        _total_active = df_kpis['total_active'].iloc[0] if 'total_active' in df_kpis.columns else 0
        _first_time = df_kpis['first_time'].iloc[0] if 'first_time' in df_kpis.columns else 0
        _full_time = df_kpis['full_time'].iloc[0] if 'full_time' in df_kpis.columns else 0
        _churned = df_kpis['churned'].iloc[0] if 'churned' in df_kpis.columns else 0
        _ref_month = df_kpis['ref_month'].iloc[0] if 'ref_month' in df_kpis.columns else 'N/A'
    else:
        _total_active = 0
        _first_time = 0
        _full_time = 0
        _churned = 0
        _ref_month = 'N/A'

    mo.hstack(
        [
            mo.stat(
                label="Total Active Contributors",
                value=f"{_total_active:,.0f}",
                caption=f"As of {_ref_month}",
                bordered=True
            ),
            mo.stat(
                label="First-Time Contributors",
                value=f"{_first_time:,.0f}",
                caption="New that month",
                bordered=True
            ),
            mo.stat(
                label="Full-Time Contributors",
                value=f"{_full_time:,.0f}",
                caption="10+ days active",
                bordered=True
            ),
            mo.stat(
                label="Churned Contributors",
                value=f"{_churned:,.0f}",
                caption="Left that month",
                bordered=True
            ),
        ],
        widths="equal",
        gap=2
    )
    return


@app.cell(hide_code=True)
def _(df_collections, mo):
    collection_filter = mo.ui.multiselect(
        options=df_collections['collection_name'].tolist() if not df_collections.empty else [],
        value=['protocol-labs-network'],
        label='Collections:'
    )

    show_inactive = mo.ui.switch(
        label='Show churned/dormant states',
        value=False
    )

    mo.hstack(
        [collection_filter, show_inactive],
        justify="start",
        gap=2,
        align="end"
    )
    return collection_filter, show_inactive


@app.cell(hide_code=True)
def _(by_collection_tab, by_project_tab, funnel_overview_tab, mo):
    mo.ui.tabs({
        "Funnel Overview": funnel_overview_tab,
        "By Collection": by_collection_tab,
        "By Project": by_project_tab
    })
    return


@app.cell(hide_code=True)
def _(
    LIFECYCLE_COLORS,
    LIFECYCLE_LABELS,
    LIFECYCLE_ORDER,
    PLOTLY_LAYOUT,
    collection_filter,
    df_lifecycle,
    mo,
    pd,
    px,
    show_inactive,
):
    # Filter by selected collections
    if collection_filter.value:
        _df = df_lifecycle[df_lifecycle['collection_name'].isin(collection_filter.value)].copy()
    else:
        _df = df_lifecycle.copy()

    _df['sample_date'] = pd.to_datetime(_df['sample_date'])

    # Filter inactive states if toggle is off
    _inactive_states = [
        'churned_after_first_time_contributor',
        'churned_after_part_time_contributor',
        'churned_after_full_time_contributor',
    ]

    if not show_inactive.value:
        _df = _df[~_df['lifecycle_state'].isin(_inactive_states)]

    # Map to human-readable labels
    _df['lifecycle_label'] = _df['lifecycle_state'].map(LIFECYCLE_LABELS)

    # Aggregate across collections
    _df_agg = _df.groupby(['sample_date', 'lifecycle_label'], as_index=False)['developer_count'].sum()

    # Order lifecycle states logically
    _df_agg['lifecycle_label'] = pd.Categorical(
        _df_agg['lifecycle_label'],
        categories=[s for s in LIFECYCLE_ORDER if s in _df_agg['lifecycle_label'].unique()],
        ordered=True
    )
    _df_agg = _df_agg.sort_values(['sample_date', 'lifecycle_label'])

    # Create stacked bar chart with explicit category ordering
    _fig = px.bar(
        data_frame=_df_agg,
        x='sample_date',
        y='developer_count',
        color='lifecycle_label',
        color_discrete_map=LIFECYCLE_COLORS,
        category_orders={'lifecycle_label': LIFECYCLE_ORDER},
        labels={'lifecycle_label': 'Lifecycle State', 'developer_count': 'Contributors', 'sample_date': ''}
    )
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(barmode='stack')

    funnel_overview_tab = mo.vstack([
        mo.md("### Developer Lifecycle Over Time"),
        mo.md(f"Showing data for: {', '.join(collection_filter.value) if collection_filter.value else 'All collections'}"),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
        mo.md("""
        **Lifecycle States:**
        - **First Time**: First contribution in this period
        - **Full/Part Time**: Engagement level (10+ days vs 1-9 days/month)
        - **New**: Just transitioned from first-time
        - **Reactivated**: Returned after gap
        - **Churned**: No longer active (hidden by default)
        """)
    ])
    return (funnel_overview_tab,)


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, collection_filter, df_lifecycle, mo, pd, px):
    # Filter by selected collections
    if collection_filter.value:
        _df = df_lifecycle[df_lifecycle['collection_name'].isin(collection_filter.value)].copy()
    else:
        _df = df_lifecycle.copy()

    _df['sample_date'] = pd.to_datetime(_df['sample_date'])

    # Aggregate active contributors by collection
    _active_states = [
        'first_time_contributor',
        'new_full_time_contributor',
        'new_part_time_contributor',
        'active_full_time_contributor',
        'active_part_time_contributor',
        'reactivated_full_time_contributor',
        'reactivated_part_time_contributor',
    ]

    _df_active = _df[_df['lifecycle_state'].isin(_active_states)]
    _df_by_collection = _df_active.groupby(['sample_date', 'collection_name'], as_index=False)['developer_count'].sum()

    # Line chart comparison
    _fig = px.line(
        data_frame=_df_by_collection,
        x='sample_date',
        y='developer_count',
        color='collection_name'
    )
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_traces(line=dict(width=2.5))

    # Summary table
    _latest = _df_by_collection.groupby('collection_name').apply(
        lambda x: x.nlargest(1, 'sample_date')
    ).reset_index(drop=True)
    _latest = _latest.rename(columns={
        'collection_name': 'Collection',
        'developer_count': 'Active Contributors',
        'sample_date': 'As Of'
    })

    by_collection_tab = mo.vstack([
        mo.md("### Active Contributors by Collection"),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
        mo.md("### Latest Snapshot"),
        mo.ui.table(
            _latest,
            format_mapping={'Active Contributors': '{:,.0f}'},
            show_column_summaries=False,
            show_data_types=False
        )
    ])
    return (by_collection_tab,)


@app.cell(hide_code=True)
def _(
    LIFECYCLE_COLORS,
    LIFECYCLE_LABELS,
    LIFECYCLE_ORDER,
    PLOTLY_LAYOUT,
    df_project_lifecycle,
    mo,
    pd,
    project_selector,
    px,
    show_inactive,
):
    if project_selector.value and not df_project_lifecycle.empty:
        _df = df_project_lifecycle[df_project_lifecycle['project'] == project_selector.value].copy()
        _df['sample_date'] = pd.to_datetime(_df['sample_date'])

        # Filter inactive states if toggle is off
        _inactive_states = [
            'churned_after_first_time_contributor',
            'churned_after_part_time_contributor',
            'churned_after_full_time_contributor',
        ]

        if not show_inactive.value:
            _df = _df[~_df['lifecycle_state'].isin(_inactive_states)]

        # Map to human-readable labels
        _df['lifecycle_label'] = _df['lifecycle_state'].map(LIFECYCLE_LABELS)

        # Order lifecycle states logically
        _df['lifecycle_label'] = pd.Categorical(
            _df['lifecycle_label'],
            categories=[s for s in LIFECYCLE_ORDER if s in _df['lifecycle_label'].unique()],
            ordered=True
        )
        _df = _df.sort_values(['sample_date', 'lifecycle_label'])

        _fig = px.bar(
            data_frame=_df,
            x='sample_date',
            y='developer_count',
            color='lifecycle_label',
            color_discrete_map=LIFECYCLE_COLORS,
            category_orders={'lifecycle_label': LIFECYCLE_ORDER},
            labels={'lifecycle_label': 'Lifecycle State', 'developer_count': 'Contributors', 'sample_date': ''}
        )
        _fig.update_layout(**PLOTLY_LAYOUT)
        _fig.update_layout(barmode='stack')

        _chart = mo.ui.plotly(_fig, config={'displayModeBar': False})
    else:
        _chart = mo.md("*Select a project to view its lifecycle data*")

    by_project_tab = mo.vstack([
        mo.md("### Project-Level Lifecycle Analysis"),
        project_selector,
        _chart
    ])
    return (by_project_tab,)


@app.cell(hide_code=True)
def _(df_project_lifecycle, mo):
    _projects = df_project_lifecycle['project'].unique().tolist() if not df_project_lifecycle.empty else []

    project_selector = mo.ui.dropdown(
        options=sorted(_projects),
        value=_projects[0] if _projects else None,
        label='Select Project:',
        full_width=True
    )
    return (project_selector,)


@app.cell
def _(mo, pyoso_db_conn):
    df_collections = mo.sql(
        f"""
        SELECT DISTINCT
          collection_name,
          display_name
        FROM collections_v1
        WHERE collection_source = 'OSS_DIRECTORY'
        AND collection_name IN ('protocol-labs-network', 'filecoin-core', 'filecoin-builders')
        ORDER BY collection_name
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_collections,)


@app.cell
def _(mo, pyoso_db_conn):
    # Use 2-month lag to avoid incomplete current-month data
    df_kpis = mo.sql(
        f"""
        WITH ref_month AS (
          SELECT DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '2' MONTH AS ref_date
        ),
        metrics AS (
          SELECT 
            m.metric_model,
            SUM(ts.amount) AS amount
          FROM timeseries_metrics_by_collection_v0 ts
          JOIN metrics_v0 m USING (metric_id)
          JOIN collections_v1 c USING (collection_id)
          CROSS JOIN ref_month rm
          WHERE c.collection_name = 'protocol-labs-network'
          AND m.metric_event_source = 'GITHUB'
          AND m.metric_model LIKE '%contributor%'
          AND m.metric_time_aggregation = 'monthly'
          AND ts.sample_date = rm.ref_date
          GROUP BY m.metric_model
        )
        SELECT
          (SELECT CAST(ref_date AS VARCHAR) FROM ref_month) AS ref_month,
          COALESCE(SUM(CASE WHEN metric_model IN ('active_full_time_contributor', 'active_part_time_contributor', 'first_time_contributor') THEN amount END), 0) AS total_active,
          COALESCE(SUM(CASE WHEN metric_model = 'first_time_contributor' THEN amount END), 0) AS first_time,
          COALESCE(SUM(CASE WHEN metric_model IN ('active_full_time_contributor', 'new_full_time_contributor', 'part_time_to_full_time_contributor', 'reactivated_full_time_contributor') THEN amount END), 0) AS full_time,
          COALESCE(SUM(CASE WHEN metric_model LIKE 'churned_after%' THEN amount END), 0) AS churned
        FROM metrics
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_kpis,)


@app.cell
def _(mo, pd, pyoso_db_conn):
    df_lifecycle = mo.sql(
        """
        SELECT 
          c.collection_name,
          ts.sample_date,
          m.metric_model AS lifecycle_state,
          SUM(ts.amount) AS developer_count
        FROM timeseries_metrics_by_collection_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN collections_v1 c USING (collection_id)
        WHERE c.collection_name IN ('protocol-labs-network', 'filecoin-core', 'filecoin-builders')
        AND m.metric_event_source = 'GITHUB'
        AND m.metric_model LIKE '%contributor%'
        AND m.metric_model NOT LIKE 'change_in%'
        AND m.metric_time_aggregation = 'monthly'
        GROUP BY c.collection_name, ts.sample_date, m.metric_model
        ORDER BY ts.sample_date, m.metric_model
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_lifecycle['sample_date'] = pd.to_datetime(df_lifecycle['sample_date'])
    return (df_lifecycle,)


@app.cell
def _(mo, pd, pyoso_db_conn):
    df_project_lifecycle = mo.sql(
        """
        SELECT 
          p.display_name AS project,
          ts.sample_date,
          m.metric_model AS lifecycle_state,
          SUM(ts.amount) AS developer_count
        FROM timeseries_metrics_by_project_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN projects_v1 p USING (project_id)
        JOIN projects_by_collection_v1 pbc USING (project_id)
        WHERE pbc.collection_name = 'protocol-labs-network'
        AND m.metric_event_source = 'GITHUB'
        AND m.metric_model LIKE '%contributor%'
        AND m.metric_model NOT LIKE 'change_in%'
        AND m.metric_time_aggregation = 'monthly'
        GROUP BY p.display_name, ts.sample_date, m.metric_model
        ORDER BY ts.sample_date, m.metric_model
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_project_lifecycle['sample_date'] = pd.to_datetime(df_project_lifecycle['sample_date'])
    return (df_project_lifecycle,)


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
        margin=dict(t=0, l=0, r=0, b=80),
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
    stringify = lambda arr: "'" + "','".join(arr) + "'"
    return


@app.cell(hide_code=True)
def _():
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
