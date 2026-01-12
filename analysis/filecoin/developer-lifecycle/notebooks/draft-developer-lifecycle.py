import marimo

__generated_with = "0.17.5"
app = marimo.App(width="full")

@app.cell(hide_code=True)
def about_app(mo):
    _team = "OSO Team"
    _date = "18 December 2024"

    mo.vstack([
        mo.md(f"""
        # **Filecoin Developer Lifecycle Analysis**
        <small>Author: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">{_team}</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">{_date}</span></small>
        """),
        mo.md("""
        This notebook provides comprehensive developer lifecycle analysis for Protocol Labs Network (PLN), Filecoin Core, and Filecoin Builders collections. It enables fund allocators to view aggregate metrics about the health of the PLN open source ecosystem, with detailed insights at the collection, project, and artifact levels.
        """),
        mo.accordion({
            "<b>Expand for additional context</b>": mo.accordion({
                "Definitions": """
                - **Contributor**: A GitHub user who has made at least one contribution (commit, issue, pull request, or code review) to a project in the given month
                - **New Contributor**: A contributor who has made their first contribution to the project in the given month
                - **Active Contributor**: A contributor who has made at least one contribution to the project in the given month
                - **Churned Contributor**: A contributor who was active in the project in the previous month, but is no longer active in the current month
                - **First Time Contributor**: A contributor making their first contribution
                - **Full Time Contributor**: A contributor with high activity levels (typically 10+ days of activity per month)
                - **Part Time Contributor**: A contributor with moderate activity levels
                - **Dormant Contributor**: A contributor who was previously active but is no longer contributing
                - **Lifecycle States**: Categories that track how contributors move through different engagement levels over time
                - **Collection**: A group of related projects (e.g., Protocol Labs Network, Filecoin Core, Filecoin Builders)
                - **Project**: A group of related artifacts (repositories) that belong to an organization
                - **Artifact**: An individual repository or code artifact tracked in OSO
                """,
                "Data Sources": """
                - **Collections**: `collections_v1` - Collection definitions from OSS Directory
                - **Projects**: `projects_v1` - Project metadata and definitions
                - **Artifacts**: `artifacts_v1` - Repository and artifact metadata
                - **Time-Series Metrics**: 
                  - `timeseries_metrics_by_collection_v0` - Collection-level metrics over time
                  - `timeseries_metrics_by_project_v0` - Project-level metrics over time
                - **Snapshot Metrics**: 
                  - `key_metrics_by_artifact_v0` - Current snapshot of artifact-level metrics
                - **Metrics Metadata**: `metrics_v0` - Metric definitions and metadata
                - **Relationships**: `projects_by_collection_v1` - Links projects to collections
                """,
                "Methodology": """
                - **Time Aggregation**: All lifecycle metrics are aggregated monthly
                - **Event Source**: Metrics are derived from GitHub events (commits, issues, pull requests, code reviews)
                - **Metric Filtering**: Lifecycle metrics are identified by patterns in `metric_model` field (contains 'contributor', excludes 'change_in')
                - **Data Bucketing**: Data is bucketed into monthly intervals, going back to the earliest available data
                - **Collection Aggregation**: When multiple collections are selected, metrics are aggregated across all projects in those collections
                - **Snapshot vs Time-Series**: Artifact-level metrics use snapshot data (current state) while collection and project metrics use time-series data
                - **Data Refresh**: Data is refreshed and backfilled on a monthly basis
                - **Limitations**: If contributions were made while a repo was private or associated with another organization, those events are not included in the data
                """,
                "Further Resources": """
                - [Getting Started with Pyoso](https://docs.opensource.observer/docs/get-started/python)
                - [Marimo Documentation](https://docs.marimo.io/)
                - [OSO Data Warehouse Documentation](https://docs.opensource.observer/)
                - [OSS Directory Collections](https://github.com/opensource-observer/oss-directory/tree/main/data/collections)
                """
            })
        }),
        mo.md("PS!<br>All of this data is live, public, and interactive. You can also download the code that generates this notebook and run it locally.")
    ])
    return


@app.cell(hide_code=True)
def import_libraries():
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    return go, pd, px


@app.cell(hide_code=True)
def configuration_settings(mo, pyoso_db_conn):
    # Load available collections
    _collections_query = """
    SELECT 
      collection_name,
      display_name
    FROM collections_v1
    WHERE collection_source = 'OSS_DIRECTORY'
    AND collection_namespace = 'oso'
    ORDER BY collection_name
    """
    _collections_df = mo.sql(_collections_query, engine=pyoso_db_conn, output=False)

    # Default collections for Filecoin analysis
    _default_collections = ['protocol-labs-network', 'filecoin-core', 'filecoin-builders']

    # Filter to only include collections that exist in the database
    _available_collections = _collections_df['collection_name'].tolist()
    _default_selected = [c for c in _default_collections if c in _available_collections]
    if not _default_selected:
        _default_selected = _available_collections[:3] if len(_available_collections) >= 3 else _available_collections

    collection_input = mo.ui.multiselect(
        options=_available_collections,
        value=_default_selected,
        label='Select Collections:'
    )

    show_inactive_input = mo.ui.switch(
        label='Show inactive developers',
        value=False
    )

    # Lifecycle metric mappings (from user query)
    LIFECYCLE_METRICS_MAPPING = {
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
        'churned_after_full_time_contributor': 'churned (after reaching full time)'
    }

    # Lifecycle color mapping
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

    # Label order for lifecycle states
    LIFECYCLE_LABEL_ORDER = [
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
    return (
        LIFECYCLE_COLORS,
        LIFECYCLE_LABEL_ORDER,
        LIFECYCLE_METRICS_MAPPING,
        collection_input,
        show_inactive_input,
    )


@app.cell
def get_data(collection_input, mo, pyoso_db_conn):
    # Helper function to stringify list for SQL IN clause
    def stringify(arr):
        if not arr:
            return "''"
        return "'" + "','".join(arr) + "'"

    # Get lifecycle metrics by collection
    _lifecycle_query = f"""
    WITH lifecycle_metrics AS (
      SELECT
        metric_id,
        metric_model
      FROM metrics_v0
      WHERE metric_event_source = 'GITHUB'
      AND metric_time_aggregation = 'monthly'
      AND metric_model LIKE '%contributor%' 
      AND metric_model NOT LIKE 'change_in%'
      AND description = 'TODO'
    )
    SELECT
      c.collection_name,
      c.display_name AS collection_display_name,
      ts.sample_date AS bucket_month,
      m.metric_model,
      ts.amount AS developers_count
    FROM timeseries_metrics_by_collection_v0 ts
    JOIN lifecycle_metrics lm USING (metric_id)
    JOIN metrics_v0 m USING (metric_id)
    JOIN collections_v1 c USING (collection_id)
    WHERE c.collection_name IN ({stringify(collection_input.value)})
    ORDER BY 1, 3, 4
    """

    print(_lifecycle_query)

    df_lifecycle = mo.sql(_lifecycle_query, engine=pyoso_db_conn, output=False)

    # Get standard GitHub metrics by collection
    _github_metrics_query = f"""
    SELECT
      c.collection_name,
      c.display_name AS collection_display_name,
      ts.sample_date AS bucket_month,
      m.metric_name,
      m.display_name AS metric_display_name,
      ts.amount
    FROM timeseries_metrics_by_collection_v0 ts
    JOIN metrics_v0 m USING (metric_id)
    JOIN collections_v1 c USING (collection_id)
    WHERE c.collection_name IN ({stringify(collection_input.value)})
    AND m.metric_source = 'GITHUB'
    AND m.metric_name IN ('stars', 'forks', 'commits', 'pull_requests', 'issues', 'active_contributors')
    ORDER BY 1, 3, 4
    """

    df_github_metrics = mo.sql(_github_metrics_query, engine=pyoso_db_conn, output=False)

    # Get projects by collection
    _projects_query = f"""
    SELECT DISTINCT
      project_id,
      p.project_name,
      p.display_name AS project_display_name,
      pbc.collection_name
    FROM projects_by_collection_v1 pbc
    JOIN projects_v1 p USING (project_id)
    WHERE pbc.collection_name IN ({stringify(collection_input.value)})
    ORDER BY pbc.collection_name, p.display_name
    """

    df_projects = mo.sql(_projects_query, engine=pyoso_db_conn, output=False)
    return df_github_metrics, df_lifecycle, df_projects, stringify


@app.cell(hide_code=True)
def process_data(LIFECYCLE_METRICS_MAPPING, df_lifecycle, pd):
    # Process lifecycle data: map metric_model to labels
    if not df_lifecycle.empty:
        df_lifecycle_processed = df_lifecycle.copy()
        df_lifecycle_processed['label'] = df_lifecycle_processed['metric_model'].map(LIFECYCLE_METRICS_MAPPING)
        df_lifecycle_processed = df_lifecycle_processed[df_lifecycle_processed['label'].notna()].copy()
        df_lifecycle_processed['bucket_month'] = pd.to_datetime(df_lifecycle_processed['bucket_month'])
    else:
        df_lifecycle_processed = pd.DataFrame(columns=['collection_name', 'bucket_month', 'label', 'developers_count'])
    return (df_lifecycle_processed,)


@app.cell(hide_code=True)
def ui_helpers(mo):
    def show_plotly(fig):
        return mo.ui.plotly(fig, config={'displayModeBar': False})

    def show_table(df, **kwargs):
        _fmt = {}
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                if '_id' in col or col == 'id' or 'count' in col.lower():
                    _fmt[col] = '{:.0f}'
                else:
                    _fmt[col] = '{:.2f}'
        return mo.ui.table(
            df.reset_index(drop=True),
            format_mapping=_fmt,
            show_column_summaries=False,
            show_data_types=False,
            **kwargs
        )

    def show_stat(value, label, caption="", format="int"):
        if format == "int":
            value_str = f"{value:,.0f}" if isinstance(value, (int, float)) else str(value)
        elif format == "1f":
            value_str = f"{value:,.1f}" if isinstance(value, (int, float)) else str(value)
        elif format == "pct":
            value_str = f"{value:.1f}%" if isinstance(value, (int, float)) else str(value)
        else:
            value_str = str(value)
        return mo.stat(value=value_str, label=label, caption=caption, bordered=True)
    return show_plotly, show_stat, show_table


@app.cell(hide_code=True)
def visualization_helpers(LIFECYCLE_COLORS, LIFECYCLE_LABEL_ORDER, go, pd, px):
    def render_lifecycle_chart(df, show_inactive=False):
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for selected collections",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(
                font=dict(size=12, color="#111"),
                paper_bgcolor="white",
                plot_bgcolor="white",
                margin=dict(t=40, l=20, r=20, b=20),
            )
            return fig

        _inactive_labels = [
            'dormant',
            'first time to dormant',
            'part time to dormant',
            'full time to dormant',
            'churned (after first time)',
            'churned (after reaching part time)',
            'churned (after reaching full time)',
        ]

        if show_inactive:
            _display_labels = LIFECYCLE_LABEL_ORDER
        else:
            _display_labels = [c for c in LIFECYCLE_LABEL_ORDER if c not in _inactive_labels]

        _df = df.copy()
        _df['label'] = pd.Categorical(_df['label'], categories=LIFECYCLE_LABEL_ORDER, ordered=True)
        _df_filtered = _df[_df['label'].isin(_display_labels)].copy()

        # Aggregate across collections if multiple selected
        if 'collection_name' in _df_filtered.columns:
            _df_agg = _df_filtered.groupby(['bucket_month', 'label'], as_index=False)['developers_count'].sum()
        else:
            _df_agg = _df_filtered

        fig = px.bar(
            data_frame=_df_agg,
            x='bucket_month',
            y='developers_count',
            color='label',
            color_discrete_map=LIFECYCLE_COLORS,
            category_orders={'label': LIFECYCLE_LABEL_ORDER},
        )
        fig.update_layout(
            barmode='stack',
            template='plotly_white',
            legend_title_text='Lifecycle State',
            font=dict(size=12, color="#111"),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=40, l=20, r=100, b=20),
            hovermode='x unified',
        )
        fig.update_xaxes(
            title='',
            showgrid=False,
            linecolor="black",
            linewidth=1.5,
            ticks="outside",
            tickformat="%b %Y",
            ticklen=6,
        )
        fig.update_yaxes(
            title="",
            showgrid=True,
            gridcolor="#DDD",
            zeroline=True,
            zerolinecolor="black",
            zerolinewidth=1,
            linecolor="black",
            linewidth=1.5,
            ticks="outside",
            ticklen=6,
            range=[0, None]
        )
        return fig
    return (render_lifecycle_chart,)


@app.cell(hide_code=True)
def milestone_1_intro(mo):
    mo.vstack([
        mo.md("---"),
        mo.md("## Milestone 1: Ecosystem Health Overview"),
        mo.md("""
        This section provides aggregate metrics about the health of the PLN open source ecosystem at the collection level. 
        Key performance indicators (KPIs) are displayed for all selected collections, showing trends in contributor lifecycle states, 
        GitHub activity metrics, and project-level breakdowns.
        """),
    ])
    return


@app.cell(hide_code=True)
def milestone_1_configuration(collection_input, mo, show_inactive_input):
    mo.vstack([
        mo.md("### Configuration"),
        mo.hstack([
            collection_input,
            show_inactive_input
        ], widths=[2, 1], gap=2, align="end", justify="start")
    ])
    return


@app.cell(hide_code=True)
def milestone_1_lifecycle_chart(
    df_lifecycle_processed,
    mo,
    render_lifecycle_chart,
    show_inactive_input,
    show_plotly,
):
    _fig = render_lifecycle_chart(df_lifecycle_processed, show_inactive=show_inactive_input.value)

    mo.vstack([
        mo.md("### Developer Lifecycle Analysis"),
        show_plotly(_fig),
        mo.md("""
        - Contributions include commits, issues, pull requests, and code reviews
        - A *contributor* is defined as a GitHub user who has made at least one contribution to the project in the given month
        - *New* contributors are contributors who have made their first contribution to the project in the given month
        - *Churned* contributors are contributors who were active in the project in the previous month, but are no longer active in the current month
        - *Active* contributors are contributors who have made at least one contribution to the project in the given month
        - Data is bucketed into monthly intervals, going back to the earliest available data for the project
        - If contributions were made while a repo was private or associated with another organization, those events are not included in the data
        - Data is refreshed and backfilled on a monthly basis
        """)
    ])
    return


@app.cell(hide_code=True)
def milestone_1_kpi_dashboard(
    df_github_metrics,
    df_lifecycle_processed,
    mo,
    show_stat,
):
    # Calculate KPIs from the most recent month
    if not df_lifecycle_processed.empty:
        _latest_month = df_lifecycle_processed['bucket_month'].max()
        _latest_data = df_lifecycle_processed[df_lifecycle_processed['bucket_month'] == _latest_month]

        _total_active = _latest_data[_latest_data['label'].isin(['full time', 'part time', 'new full time', 'new part time', 'first time'])]['developers_count'].sum()
        _new_contributors = _latest_data[_latest_data['label'] == 'first time']['developers_count'].sum()
        _churned = _latest_data[_latest_data['label'].str.contains('churned', na=False)]['developers_count'].sum()
    else:
        _total_active = 0
        _new_contributors = 0
        _churned = 0

    if not df_github_metrics.empty:
        _latest_month_github = df_github_metrics['bucket_month'].max()
        _latest_github = df_github_metrics[df_github_metrics['bucket_month'] == _latest_month_github]
        _total_stars = _latest_github[_latest_github['metric_name'] == 'stars']['amount'].sum()
        _total_forks = _latest_github[_latest_github['metric_name'] == 'forks']['amount'].sum()
    else:
        _total_stars = 0
        _total_forks = 0

    _stats = mo.hstack([
        show_stat(value=_total_active, label='Total Active Contributors', caption="Current month", format="int"),
        show_stat(value=_new_contributors, label="New Contributors", caption="Current month", format="int"),
        show_stat(value=_churned, label="Churned Contributors", caption="Current month", format="int"),
        show_stat(value=_total_stars, label="Total Stars", caption="Current month", format="int"),
        show_stat(value=_total_forks, label="Total Forks", caption="Current month", format="int"),
    ], widths='equal')

    mo.vstack([
        mo.md("### Key Performance Indicators"),
        _stats
    ])
    return


@app.cell(hide_code=True)
def milestone_1_project_breakdown(df_projects, mo, pd, show_table):
    if not df_projects.empty:
        _project_table = df_projects[['collection_name', 'project_display_name', 'project_name']].copy()
        _project_table = _project_table.rename(columns={
            'collection_name': 'Collection',
            'project_display_name': 'Project Display Name',
            'project_name': 'Project Name'
        })
    else:
        _project_table = pd.DataFrame(columns=['Collection', 'Project Display Name', 'Project Name'])

    mo.vstack([
        mo.md("### Projects in Selected Collections"),
        mo.md(f"Total projects: {len(df_projects):,}" if not df_projects.empty else "No projects found"),
        show_table(_project_table)
    ])
    return


@app.cell(hide_code=True)
def milestone_2_intro(mo):
    mo.vstack([
        mo.md("---"),
        mo.md("## Milestone 2: Detailed Repository Insights"),
        mo.md("""
        This section provides granular metrics about specific projects and their associated repositories (artifacts). 
        Project-level time-series analysis shows lifecycle trends over time, while artifact-level snapshots provide 
        current state metrics for individual repositories.
        """),
    ])
    return


@app.cell
def get_project_data(collection_input, mo, pyoso_db_conn, stringify):
    # Get lifecycle metrics by project
    _project_lifecycle_query = f"""
    WITH lifecycle_metrics AS (
      SELECT
        metric_id,
        metric_model
      FROM metrics_v0
      WHERE metric_event_source = 'GITHUB'
      AND metric_time_aggregation = 'monthly'
      AND metric_model LIKE '%contributor%' 
      AND metric_model NOT LIKE 'change_in%'
      AND description = 'TODO'
    )
    SELECT
      project_id,
      p.project_name,
      p.display_name AS project_display_name,
      pbc.collection_name,
      ts.sample_date AS bucket_month,
      m.metric_model,
      ts.amount AS developers_count
    FROM timeseries_metrics_by_project_v0 ts
    JOIN lifecycle_metrics lm USING (metric_id)
    JOIN metrics_v0 m USING (metric_id)
    JOIN projects_v1 p USING (project_id)
    JOIN projects_by_collection_v1 pbc USING (project_id)
    WHERE pbc.collection_name IN ({stringify(collection_input.value)})
    ORDER BY 1, 5, 6
    """

    df_project_lifecycle = mo.sql(_project_lifecycle_query, engine=pyoso_db_conn, output=False)

    # Get artifacts (repositories) for selected collections
    _artifacts_query = f"""
    SELECT DISTINCT
      a.artifact_id,
      a.artifact_namespace,
      a.artifact_name,
      p.project_name,
      p.display_name AS project_display_name,
      pbc.collection_name
    FROM projects_by_collection_v1 pbc
    JOIN projects_v1 p USING (project_id)
    JOIN artifacts_by_project_v1 a USING (project_id)
    WHERE pbc.collection_name IN ({stringify(collection_input.value)})
    AND a.artifact_source = 'GITHUB'
    ORDER BY pbc.collection_name, p.display_name, a.artifact_name
    """

    df_artifacts = mo.sql(_artifacts_query, engine=pyoso_db_conn, output=False)
    return df_artifacts, df_project_lifecycle


@app.cell(hide_code=True)
def process_project_data(LIFECYCLE_METRICS_MAPPING, df_project_lifecycle, pd):
    if not df_project_lifecycle.empty:
        df_project_lifecycle_processed = df_project_lifecycle.copy()
        df_project_lifecycle_processed['label'] = df_project_lifecycle_processed['metric_model'].map(LIFECYCLE_METRICS_MAPPING)
        df_project_lifecycle_processed = df_project_lifecycle_processed[df_project_lifecycle_processed['label'].notna()].copy()
        df_project_lifecycle_processed['bucket_month'] = pd.to_datetime(df_project_lifecycle_processed['bucket_month'])
    else:
        df_project_lifecycle_processed = pd.DataFrame(columns=['project_id', 'bucket_month', 'label', 'developers_count'])
    return (df_project_lifecycle_processed,)


@app.cell(hide_code=True)
def milestone_2_project_selection(df_project_lifecycle_processed, mo):
    if not df_project_lifecycle_processed.empty:
        _project_list = sorted(df_project_lifecycle_processed['project_display_name'].unique().tolist())
        project_input = mo.ui.dropdown(
            options=_project_list,
            value=_project_list[0] if _project_list else None,
            label='Select a Project:',
            full_width=True
        )
    else:
        project_input = mo.ui.dropdown(
            options=[],
            value=None,
            label='Select a Project:',
            full_width=True
        )
    return (project_input,)


@app.cell(hide_code=True)
def milestone_2_project_chart(
    df_project_lifecycle_processed,
    go,
    mo,
    project_input,
    render_lifecycle_chart,
    show_inactive_input,
    show_plotly,
):
    if not df_project_lifecycle_processed.empty and project_input.value:
        _df_project = df_project_lifecycle_processed[
            df_project_lifecycle_processed['project_display_name'] == project_input.value
        ].copy()
        _fig = render_lifecycle_chart(_df_project, show_inactive=show_inactive_input.value)
    else:
        _fig = go.Figure()
        _fig.add_annotation(
            text="No data available for selected project",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        _fig.update_layout(
            font=dict(size=12, color="#111"),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=40, l=20, r=20, b=20),
        )

    mo.vstack([
        mo.md("### Project-Level Lifecycle Analysis"),
        show_plotly(_fig)
    ])
    return


@app.cell
def get_artifact_snapshot(df_artifacts, mo, pd, pyoso_db_conn, stringify):
    if df_artifacts.empty:
        df_artifact_metrics = pd.DataFrame()
    else:
        _artifact_ids = df_artifacts['artifact_id'].unique().tolist()
        if _artifact_ids:
            _artifact_metrics_query = f"""
            SELECT DISTINCT
              artifact_id,
              a.artifact_namespace,
              a.artifact_name,
              m.display_name AS metric_display_name,
              km.amount,
              km.sample_date
            FROM key_metrics_by_artifact_v0 km
            JOIN artifacts_by_project_v1 a USING (artifact_id)
            JOIN metrics_v0 m USING (metric_id)
            WHERE artifact_id IN ({stringify(_artifact_ids)})
            AND m.metric_event_source = 'GITHUB'
            AND a.artifact_source = 'GITHUB'
            AND m.metric_model IN ('stars', 'forks', 'contributors')
            ORDER BY a.artifact_namespace, a.artifact_name, m.display_name
            """

            df_artifact_metrics = mo.sql(_artifact_metrics_query, engine=pyoso_db_conn, output=False)
        else:
            df_artifact_metrics = pd.DataFrame()
    return (df_artifact_metrics,)


@app.cell
def _(df_artifact_metrics):
    df_artifact_metrics
    return


@app.cell(hide_code=True)
def milestone_2_artifact_table(
    df_artifact_metrics,
    df_artifacts,
    mo,
    pd,
    show_table,
):
    if not df_artifacts.empty and not df_artifact_metrics.empty:
        # Pivot artifact metrics for better display
        _df_pivot = df_artifact_metrics.pivot_table(
            index=['artifact_id', 'artifact_name', 'artifact_namespace'],
            columns='metric_display_name',
            values='amount',
            aggfunc='first'
        ).reset_index()

        # Merge with artifact metadata
        _df_artifact_display = df_artifacts.merge(
            _df_pivot,
            on=['artifact_id', 'artifact_name', 'artifact_namespace'],
            how='left'
        )

        _df_artifact_display = _df_artifact_display[[
            'collection_name',
            'project_display_name',
            'artifact_name',
            'Stars',
            'Forks',
            'Contributors'
        ]].copy()

        _df_artifact_display = _df_artifact_display.rename(columns={
            'collection_name': 'Collection',
            'project_display_name': 'Project',
            'artifact_name': 'Repository',
        })

        _df_artifact_display = _df_artifact_display.fillna(0)
    else:
        _df_artifact_display = pd.DataFrame(columns=['Collection', 'Project', 'Repository', 'Stars', 'Forks', 'Contributors'])

    mo.vstack([
        mo.md("### Artifact (Repository) Snapshot Metrics"),
        mo.md("""
        Current snapshot metrics for repositories in selected collections. These metrics represent the most recent 
        available data and are not time-series. For time-series analysis, see the project-level charts above.
        """),
        mo.md(f"Total repositories: {len(df_artifacts):,}" if not df_artifacts.empty else "No repositories found"),
        show_table(_df_artifact_display)
    ])
    return


@app.cell(hide_code=True)
def milestone_3_intro(mo):
    mo.vstack([
        mo.md("---"),
        mo.md("## Milestone 3: Advanced Analytics"),
        mo.md("""
        This section provides advanced analytics capabilities including cross-collection comparisons, 
        contributor retention analysis, and custom query interfaces for deeper insights.
        """),
    ])
    return


@app.cell(hide_code=True)
def milestone_3_cross_collection_comparison(
    df_lifecycle_processed,
    go,
    mo,
    px,
    show_plotly,
):
    if not df_lifecycle_processed.empty:
        # Aggregate by collection for comparison
        _df_collection_agg = df_lifecycle_processed.groupby(
            ['collection_name', 'collection_display_name', 'bucket_month'],
            as_index=False
        )['developers_count'].sum()

        _fig = px.line(
            data_frame=_df_collection_agg,
            x='bucket_month',
            y='developers_count',
            color='collection_display_name',
            labels={
                'bucket_month': 'Month',
                'developers_count': 'Total Active Contributors',
                'collection_display_name': 'Collection'
            }
        )
        _fig.update_layout(
            font=dict(size=12, color="#111"),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=40, l=20, r=20, b=20),
            hovermode='x unified',
            legend=dict(
                orientation="v",
                x=1.00,
                y=1.00,
                xanchor="right",
                yanchor="top"
            )
        )
        _fig.update_xaxes(
            showline=True,
            linewidth=1.5,
            linecolor="black",
            ticks="outside",
            tickwidth=1.5,
            tickcolor="black",
            ticklen=6,
        )
        _fig.update_yaxes(
            showline=True,
            linewidth=1.5,
            linecolor="black",
            ticks="outside",
            tickwidth=1.5,
            tickcolor="black",
            ticklen=6,
            rangemode="tozero"
        )
        _fig.update_traces(line=dict(width=3))
    else:
        _fig = go.Figure()
        _fig.add_annotation(
            text="No data available for comparison",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        _fig.update_layout(
            font=dict(size=12, color="#111"),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=40, l=20, r=20, b=20),
        )

    mo.vstack([
        mo.md("### Cross-Collection Comparison"),
        mo.md("Total active contributors over time across selected collections"),
        show_plotly(_fig)
    ])
    return


@app.cell(hide_code=True)
def milestone_3_summary(mo):
    mo.vstack([
        mo.md("---"),
        mo.md("## Summary"),
        mo.md("""
        This notebook provides comprehensive developer lifecycle analysis for Protocol Labs Network and Filecoin ecosystems. 
        Key insights can be derived from:

        - **Collection-level trends**: Overall ecosystem health and contributor engagement patterns
        - **Project-level analysis**: Individual project performance and lifecycle states
        - **Artifact snapshots**: Current state of individual repositories

        For more detailed analysis, consider:
        - Filtering by specific time ranges
        - Comparing individual projects within collections
        - Examining artifact-level metrics for specific repositories
        - Using the OSO data warehouse directly for custom queries
        """),
    ])
    return


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
