import marimo

__generated_with = "0.17.5"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def about_app(mo):
    _team = "OSO Team"
    _date = "22 December 2025"

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
                - **Part Time Contributor**: A contributor with moderate activity levels (1-9 days of activity per month)
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
                - **Lifecycle Metrics**: `int_pln_developer_lifecycle_monthly_enriched` - Developer lifecycle states for PLN projects
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
                - **Activity Classification**: Contributors are classified based on days active per month:
                  - *Full Time*: 10+ days of activity per month
                  - *Part Time*: 1-9 days of activity per month
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
def _(mo):
    mo.md(r"""
    # Ecosystem Health Overview
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    COLLECTIONS = [
        'protocol-labs-network',
        'filecoin-builders',
        'filecoin-core',
        'filecoin-dependencies',
        'filecoin-infra-for-builders',
    ]
    GITHUB_METRICS = [
        'opened_issues',
        'closed_issues',
        'commits',
        'opened_pull_requests',
        'merged_pull_requests',
        'contributors',
        'comments',
        'repositories',
        'releases',
        'stars',
        'forks',        
    ]
    df_collections = mo.sql(
        f"""
        WITH collections AS (
          SELECT 
            collection_id,
            display_name AS collection
          FROM collections_v1
          WHERE
            collection_source = 'OSS_DIRECTORY'
            AND collection_name IN ({stringify(COLLECTIONS)})
        ),
        metrics AS (
          SELECT
            metric_id,
            display_name AS metric
          FROM metrics_v0
          WHERE
            metric_event_source = 'GITHUB'
            AND metric_model IN ({stringify(GITHUB_METRICS)})
        )
        SELECT
          collection AS "Collection",
          metric AS "Metric",
          amount AS "Amount"
        FROM key_metrics_by_collection_v0
        JOIN metrics USING metric_id
        JOIN collections USING collection_id
        ORDER BY 1,2
        """,
        output=False,
        engine=pyoso_db_conn
    )
    df_collections_monthly_metrics = mo.sql(
        f"""
        WITH collections AS (
          SELECT 
            collection_id,
            display_name AS collection
          FROM collections_v1
          WHERE
            collection_source = 'OSS_DIRECTORY'
            AND collection_name IN ({stringify(COLLECTIONS)})
        ),
        metrics AS (
          SELECT
            metric_id,
            CASE WHEN display_name = 'Repositories' THEN 'Active Repositories' ELSE display_name END AS metric
          FROM metrics_v0
          WHERE
            metric_event_source = 'GITHUB'
            AND metric_model IN ({stringify(GITHUB_METRICS)})
            AND metric_time_aggregation = 'monthly'
        )
        SELECT
          collection AS "Collection",
          metric AS "Metric",
          sample_date AS "Date",
          amount AS "Amount"
        FROM timeseries_metrics_by_collection_v0
        JOIN metrics USING metric_id
        JOIN collections USING collection_id
        ORDER BY 1,2,3
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return COLLECTIONS, df_collections, df_collections_monthly_metrics


@app.cell(hide_code=True)
def _(df_collections_monthly_metrics, mo):
    _collections = df_collections_monthly_metrics['Collection'].unique()
    _metrics = df_collections_monthly_metrics['Metric'].unique()
    _default_collection = 'Protocol Labs Network'
    _default_metric = 'Contributors'
    monthly_metric_collection_select = mo.ui.dropdown(
        options=_collections,
        value=_default_collection,
        allow_select_none=False
    )
    monthly_metric_metric_select = mo.ui.dropdown(
        options=_metrics,
        value=_default_metric,
        allow_select_none=False
    )
    return monthly_metric_collection_select, monthly_metric_metric_select


@app.cell(hide_code=True)
def _(
    LAYOUT_SETTINGS,
    df_collections,
    df_collections_monthly_metrics,
    mo,
    monthly_metric_collection_select,
    monthly_metric_metric_select,
    pd,
    px,
    show_insight,
    show_plotly,
    show_table,
):
    def _chart(collection, metric):
        df = df_collections_monthly_metrics[
            (df_collections_monthly_metrics['Collection'] == collection)
            & (df_collections_monthly_metrics['Metric'] == metric)
        ].copy()
        df['Date'] = pd.to_datetime(df['Date'])
        df.sort_values(by='Date', inplace=True)
        fig = px.area(data_frame=df, x='Date', y='Amount', line_shape='hvh', color_discrete_sequence=['teal'])
        fig.update_layout(hovermode='x unified', **LAYOUT_SETTINGS)
        annotation_date = pd.Timestamp("2025-05-01")
        fig.add_annotation(
            x=annotation_date,
            y=df.loc[df['Date'] == annotation_date, 'Amount'].iloc[0],
            text="Issue with gharchive",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-100,
            xanchor="center",
            yanchor="bottom",
        )
        return fig

    _df = (
        df_collections.pivot_table(index='Collection', columns='Metric', values='Amount', fill_value=0)
        .map(int)
        [[
            'Repositories', 'Contributors', 'Releases',
            'Forks', 'Stars', 'Commits', 
            'Opened Pull Requests', 'Merged Pull Requests',
            'Opened Issues', 'Closed Issues', 'Comments'
        ]]
        .reset_index()
    )

    _chart_title = mo.hstack([
        mo.md("Analyze"),
        monthly_metric_metric_select,
        mo.md("for all projects in the"),
        monthly_metric_collection_select,
        mo.md("collection")
    ], align='start', justify='start')

    _fig = _chart(monthly_metric_collection_select.value, monthly_metric_metric_select.value)

    _num_repos = _df['Repositories'].max()
    _num_contribs = _df['Contributors'].max()
    _collections = len(_df)
    show_insight(
        headline=f"OSO is currently tracking >{_num_repos:,.0f} repos and >{_num_contribs:,.0f} contributors across {_collections:,.0f} collections",
        level=2,
        elements=[
            show_table(_df),
            mo.md("### Since May 2025, there has been a [documented issue](https://github.com/igrigorik/gharchive.org/issues/310) with gharchive missing some events"),
            _chart_title,
            show_plotly(_fig)        
        ]
    )
    return


@app.cell(hide_code=True)
def _(
    COLLECTIONS,
    artifacts_by_collection_v1,
    int_opendevdata__repositories_with_repo_id,
    mo,
    pyoso_db_conn,
    stg_opendevdata__developer_activities,
    stg_opendevdata__ecosystems,
    stg_opendevdata__ecosystems_repos_recursive,
):
    ECOSYSTEMS = ['Filecoin', 'IPFS', 'Protocol Labs', 'libp2p']

    df_opendevdata_repos = mo.sql(
        f"""
        WITH artifacts AS (
          SELECT DISTINCT CAST(artifact_source_id AS integer) AS repo_id
          FROM artifacts_by_collection_v1
          WHERE
            collection_name IN ({stringify(COLLECTIONS)})
            AND artifact_source = 'GITHUB'
        )
        SELECT
          SPLIT(repo_name, '/')[1] AS "Maintainer",
          CONCAT('https://github.com/', repo_name) AS "Repo URL",
          repo_created_at AS "Repo Created At",
          fork_count AS "Fork Count",
          star_count AS "Star Count",
          opendevdata_id IN (
            SELECT repo_id
            FROM stg_opendevdata__ecosystems_repos_recursive AS rr
            JOIN stg_opendevdata__ecosystems AS e ON rr.ecosystem_id = e.id
            WHERE e.name IN ({stringify(ECOSYSTEMS)})
          ) AS "Included in Electric Capital"
        FROM int_opendevdata__repositories_with_repo_id
        JOIN artifacts USING repo_id
        """,
        output=False,
        engine=pyoso_db_conn
    )

    df_opendevdata_metrics = mo.sql(
        f"""
        WITH artifacts AS (
          SELECT DISTINCT CAST(artifact_source_id AS integer) AS repo_id
          FROM artifacts_by_collection_v1
          WHERE collection_name IN ({stringify(COLLECTIONS)})
            AND artifact_source='GITHUB'
        ),
        oso_repos AS (
          SELECT DISTINCT r.opendevdata_id AS repo_id
          FROM int_opendevdata__repositories_with_repo_id r
          JOIN artifacts a ON r.repo_id=a.repo_id
        ),
        ec_repos AS (
          SELECT DISTINCT rr.repo_id
          FROM stg_opendevdata__ecosystems_repos_recursive rr
          JOIN stg_opendevdata__ecosystems e ON rr.ecosystem_id=e.id
          WHERE e.name IN ({stringify(ECOSYSTEMS)})
        ),
        oso_metrics AS (
          SELECT
            DATE_TRUNC('MONTH', d.day) AS bucket_month,
            APPROX_DISTINCT(d.canonical_developer_id) AS dev_count,
            APPROX_DISTINCT(d.repo_id) AS repo_count,
            SUM(d.num_commits) AS commit_count,
            'OSO-Tracked Repos' AS label
          FROM stg_opendevdata__developer_activities d
          JOIN oso_repos r ON d.repo_id=r.repo_id
          GROUP BY 1
        ),
        ec_metrics AS (
          SELECT
            DATE_TRUNC('MONTH', d.day) AS bucket_month,
            APPROX_DISTINCT(d.canonical_developer_id) AS dev_count,
            APPROX_DISTINCT(d.repo_id) AS repo_count,
            SUM(d.num_commits) AS commit_count,
            'Electric Capital Repos' AS label
          FROM stg_opendevdata__developer_activities d
          JOIN ec_repos r ON d.repo_id=r.repo_id
          GROUP BY 1
        ),
        unioned AS (
          SELECT * FROM oso_metrics
          UNION ALL
          SELECT * FROM ec_metrics
        )
        SELECT
          bucket_month AS "Date",
          dev_count AS "Active Developers",
          repo_count AS "Active Repos",
          commit_count AS "Commits",
          label AS "Label"
        FROM unioned
        ORDER BY 1
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return ECOSYSTEMS, df_opendevdata_metrics, df_opendevdata_repos


@app.cell(hide_code=True)
def _(mo):
    _metrics = ['Active Developers', 'Active Repos', 'Commits']
    _default_metric = 'Active Developers'
    opendevdata_metric_select = mo.ui.dropdown(
        options=_metrics,
        value=_default_metric,
        allow_select_none=False
    )
    return (opendevdata_metric_select,)


@app.cell(hide_code=True)
def _(
    ECOSYSTEMS,
    LAYOUT_SETTINGS,
    df_opendevdata_metrics,
    df_opendevdata_repos,
    mo,
    opendevdata_metric_select,
    pd,
    px,
    show_insight,
    show_plotly,
    show_table,
):
    def _chart(metric):
        df = df_opendevdata_metrics.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        df.sort_values(by='Date', inplace=True)
        fig = px.line(data_frame=df, x='Date', y=metric, color='Label', line_shape='hvh')
        fig.update_layout(hovermode='x unified', **LAYOUT_SETTINGS)
        annotation_date = pd.Timestamp("2023-03-01")
        y = df.loc[df['Date'] == annotation_date, metric].iloc[0]
        fig.add_annotation(
            x=annotation_date,
            y=y,
            text="Figures start getting stale",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=200,
            xanchor="center",
            yanchor="bottom",
        )
        return fig

    _chart_title = mo.hstack([
        mo.md("Analyze"),
        opendevdata_metric_select,
        mo.md("for all repos tracked by Electric Capital's Open Dev Data")
    ], align='start', justify='start')

    _fig = _chart(opendevdata_metric_select.value)

    _df_repos = df_opendevdata_repos.sort_values(by='Fork Count', ascending=False).copy()
    _df_repos['Maintainer'] = _df_repos['Repo URL']

    _num_repos = len(df_opendevdata_repos)
    _included_repos = len(df_opendevdata_repos[df_opendevdata_repos['Included in Electric Capital']])
    show_insight(
        headline=f"OSO can diff these metrics against the ~{_num_repos:,.0f} repos currently tracked by Electric Capital",
        level=2,
        elements=[
            mo.md(f"Of these, only {_included_repos:,.0f} are listed as part of one or more of the following Electric Capital ecosystems: {', '.join(sorted(ECOSYSTEMS))}"),
            show_table(_df_repos),
            _chart_title,
            show_plotly(_fig)        
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Detailed Repository Metrics
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    repository_input = mo.ui.text(kind='url', label='Enter a repository url', value='https://github.com/opensource-observer/oso', full_width=True)
    repository_input
    return (repository_input,)


@app.cell(hide_code=True)
def _(
    int_artifacts__github,
    int_opendevdata__repositories_with_repo_id,
    mo,
    pd,
    pyoso_db_conn,
    repositories_v0,
    repository_input,
    stg_opendevdata__developer_activities,
):
    df_repo_snapshot = mo.sql(
        f"""
        SELECT
          artifact_id,
          artifact_source_id AS repo_id,
          star_count,
          fork_count,
          license_name,
          language,
          created_at,
          updated_at
        FROM repositories_v0
        WHERE artifact_url = '{repository_input.value}'
        """,
        engine=pyoso_db_conn,
        output=False
    )

    _repo_id = df_repo_snapshot['repo_id'].iloc[0]
    df_repo_lineage = mo.sql(
        f"""
        SELECT DISTINCT
          artifact_id,
          artifact_url AS repo_url,
        FROM int_artifacts__github
        WHERE artifact_source_id = '{_repo_id}'
        """,
        engine=pyoso_db_conn,
        output=False
    )

    _artifact_ids = df_repo_lineage['artifact_id'].to_list()
    _df_repo_opendevdata_metrics = mo.sql(
        f"""
        WITH metrics AS (
          SELECT
            DATE_TRUNC('MONTH', d.day) AS bucket_month,
            APPROX_DISTINCT(d.canonical_developer_id) AS dev_count,
            SUM(d.num_commits) AS commit_count
          FROM stg_opendevdata__developer_activities d
          JOIN int_opendevdata__repositories_with_repo_id r
            ON d.repo_id = r.opendevdata_id
          WHERE r.repo_id = {_repo_id}
          GROUP BY 1
        ),
        unpivoted AS (
          SELECT
            bucket_month,
            'Active Developers' AS metric,
            dev_count AS amount
          FROM metrics
          UNION ALL
          SELECT
            bucket_month,
            'Commits' AS metric,
            commit_count AS amount
          FROM metrics
        )
        SELECT
          bucket_month AS "Date",
          metric AS "Metric",
          amount AS "Amount"
        FROM unpivoted
        ORDER BY 1,2
        """,
        engine=pyoso_db_conn,
        output=False
    )

    def _metric_query(metric, repo_artifact_ids, start_date='2022-01-01'):
        metric_name = metric.replace('_', ' ').title()
        return f"""
            SELECT
              metrics_sample_date AS "Date",
              '{metric_name}' AS "Metric",
              amount AS "Amount"
            FROM {metric}_to_artifact_monthly
            WHERE
              to_artifact_id IN ({stringify(repo_artifact_ids)})
              AND metrics_sample_date >= DATE('{start_date}')
            """

    _repo_metrics = [
        'closed_issues',
        'comments',
        'contributors',
        'forks',
        'merged_pull_requests',
        'opened_issues',
        'opened_pull_requests',
        'stars',
        'issue_age_median',
        'issue_age_max',
    #    'full_time_developers',
    #    'part_time_developers',
        'bot_activity',
        'project_velocity',
    #    'new_contributors',
        'self_merge_rates',
        'contributor_absence_factor',
        'releases',
        'burstiness'
    ]
    _df_repo_timeseries_metrics = mo.sql(
        "UNION ALL".join([_metric_query(m, _artifact_ids) for m in _repo_metrics]),
        engine=pyoso_db_conn,
        output=False
    )

    df_repo_metrics = pd.concat([_df_repo_timeseries_metrics, _df_repo_opendevdata_metrics], axis=0, ignore_index=True)
    return df_repo_lineage, df_repo_metrics, df_repo_snapshot


@app.cell(hide_code=True)
def _(df_repo_metrics, mo):
    _metrics = sorted(df_repo_metrics['Metric'].unique())
    _default_metric = 'Active Developers'
    repo_metric_select = mo.ui.dropdown(
        options=_metrics,
        value=_default_metric,
        allow_select_none=False
    )
    return (repo_metric_select,)


@app.cell(hide_code=True)
def _(
    LAYOUT_SETTINGS,
    df_opendevdata_repos,
    df_repo_lineage,
    df_repo_metrics,
    df_repo_snapshot,
    mo,
    pd,
    px,
    repo_metric_select,
    repository_input,
    show_insight,
    show_plotly,
    show_table,
):
    def _chart(metric):
        df = df_repo_metrics.copy()
        df["Date"] = pd.to_datetime(df["Date"])
        df["Date"] = df["Date"].dt.to_period("M").dt.to_timestamp()
        start = df["Date"].min()
        end = df["Date"].max()
        df = df[df["Metric"] == metric]
        df = df.groupby(["Date", "Metric"], as_index=False)["Amount"].sum()
        full_dates = pd.date_range(start=start, end=end, freq="MS")
        grid = pd.DataFrame({"Date": full_dates})
        grid["Metric"] = metric
        df = (
            grid.merge(df, on=["Date", "Metric"], how="left")
                .fillna({"Amount": 0})
                .sort_values("Date")
        )
        fig = px.area(data_frame=df, x="Date", y="Amount", line_shape="hvh", color_discrete_sequence=['teal'])
        fig.update_layout(hovermode="x unified", **LAYOUT_SETTINGS)
        return fig

    _name = repository_input.value.replace('https://github.com/', '')

    _chart_title = mo.hstack([
        mo.md("Analyze"),
        repo_metric_select,
        mo.md(f"for {_name}")
    ], align='start', justify='start')

    _fig = _chart(repo_metric_select.value)


    _lineage = [x for x in df_repo_lineage['repo_url'].unique() if x != repository_input.value]
    _lineage_md = f"Also known as {';'.join(_lineage)}" if _lineage else ""

    _num_repos = len(df_opendevdata_repos)
    _included_repos = len(df_opendevdata_repos[df_opendevdata_repos['Included in Electric Capital']])
    show_insight(
        headline=f"Showing GitHub related metrics for: {_name}",
        level=2,
        elements=[
            mo.md(_lineage_md),
            show_table(df_repo_snapshot),
            _chart_title,
            show_plotly(_fig)        
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Developer Lifecycle Analysis

    This section provides detailed developer lifecycle analysis using granular data from the Protocol Labs Network.
    The lifecycle model tracks contributors through different engagement states over time, from first contribution
    through to becoming full-time contributors or churning out of the ecosystem.
    """)
    return


@app.cell(hide_code=True)
def lifecycle_configuration(
    COLLECTIONS,
    mo,
    projects_by_collection_v1,
    projects_v1,
    pyoso_db_conn,
):
    # Get all projects in the PLN collections
    df_pln_projects = mo.sql(
        f"""
        SELECT DISTINCT
          project_id,
          p.project_name,
          p.display_name AS project_display_name,
          pbc.collection_name
        FROM projects_by_collection_v1 pbc
        JOIN projects_v1 p USING (project_id)
        WHERE pbc.collection_name IN ({stringify(COLLECTIONS)})
        ORDER BY p.display_name
        """,
        engine=pyoso_db_conn,
        output=False
    )

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
        'churned': '#999999',
        'unknown': '#CCCCCC',
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
        'churned',
        'unknown',
    ]

    # Active labels (non-churned, non-dormant)
    ACTIVE_LABELS = [
        'first time',
        'full time',
        'new full time',
        'part time to full time',
        'dormant to full time',
        'part time',
        'new part time',
        'full time to part time',
        'dormant to part time',
    ]

    # Show inactive toggle
    show_inactive_input = mo.ui.switch(
        label='Include dormant & churned states',
        value=False
    )

    return (
        ACTIVE_LABELS,
        LIFECYCLE_COLORS,
        LIFECYCLE_LABEL_ORDER,
        show_inactive_input,
    )


@app.cell(hide_code=True)
def get_lifecycle_data(
    int_pln_developer_lifecycle_monthly_enriched,
    mo,
    pyoso_db_conn,
):
    # Get developer lifecycle data from the enriched PLN lifecycle model
    df_lifecycle_raw = mo.sql(
        f"""
        SELECT
          bucket_month,
          project_id,
          project_name,
          project_display_name,
          git_user,
          is_bot,
          label,
          days_active,
          activity_level,
          current_state,
          prev_state,
          highest_engaged_state,
          first_contribution_month,
          last_contribution_month
        FROM int_pln_developer_lifecycle_monthly_enriched
        WHERE is_bot = FALSE
        ORDER BY bucket_month, project_name
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_lifecycle_raw,)


@app.cell(hide_code=True)
def process_lifecycle_data(df_lifecycle_raw, pd):
    # Process lifecycle data
    if not df_lifecycle_raw.empty:
        df_lifecycle = df_lifecycle_raw.copy()
        df_lifecycle['bucket_month'] = pd.to_datetime(df_lifecycle['bucket_month'])
    else:
        df_lifecycle = pd.DataFrame(columns=[
            'bucket_month', 'project_id', 'project_name', 'project_display_name',
            'git_user', 'label', 'days_active', 'activity_level'
        ])
    return (df_lifecycle,)


@app.cell(hide_code=True)
def lifecycle_collection_view(
    ACTIVE_LABELS,
    LIFECYCLE_COLORS,
    LIFECYCLE_LABEL_ORDER,
    df_lifecycle,
    go,
    mo,
    pd,
    px,
    show_inactive_input,
    show_plotly,
    show_stat,
):

    # Aggregate lifecycle data by month and label (across all projects)
    if not df_lifecycle.empty:
        _df_agg = df_lifecycle.groupby(['bucket_month', 'label'], as_index=False).agg(
            developers_count=('git_user', 'nunique')
        )

        # Filter based on show_inactive toggle
        if show_inactive_input.value:
            _display_labels = LIFECYCLE_LABEL_ORDER
        else:
            _display_labels = ACTIVE_LABELS

        _df_filtered = _df_agg[_df_agg['label'].isin(_display_labels)].copy()
        _df_filtered['label'] = pd.Categorical(_df_filtered['label'], categories=LIFECYCLE_LABEL_ORDER, ordered=True)

        # Create stacked bar chart
        _fig = px.bar(
            data_frame=_df_filtered,
            x='bucket_month',
            y='developers_count',
            color='label',
            color_discrete_map=LIFECYCLE_COLORS,
            category_orders={'label': LIFECYCLE_LABEL_ORDER},
            labels={'bucket_month': 'Month', 'developers_count': 'Contributors', 'label': 'Lifecycle State'}
        )
        _fig.update_layout(
            barmode='stack',
            template='plotly_white',
            legend_title_text='Lifecycle State',
            font=dict(size=12, color="#111"),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=40, l=20, r=100, b=20),
            hovermode='x unified',
        )
        _fig.update_xaxes(
            title='',
            showgrid=False,
            linecolor="black",
            linewidth=1.5,
            ticks="outside",
            tickformat="%b %Y",
            ticklen=6,
        )
        _fig.update_yaxes(
            title="Contributors",
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

        # Calculate KPIs for the most recent month
        _latest_month = _df_agg['bucket_month'].max()
        _latest_data = _df_agg[_df_agg['bucket_month'] == _latest_month]

        _total_active = _latest_data[_latest_data['label'].isin(ACTIVE_LABELS)]['developers_count'].sum()
        _new_contributors = _latest_data[_latest_data['label'] == 'first time']['developers_count'].sum()
        _full_time = _latest_data[_latest_data['label'].isin(['full time', 'new full time', 'part time to full time', 'dormant to full time'])]['developers_count'].sum()
        _part_time = _latest_data[_latest_data['label'].isin(['part time', 'new part time', 'full time to part time', 'dormant to part time'])]['developers_count'].sum()
        _churned = _latest_data[_latest_data['label'].str.contains('churned', na=False)]['developers_count'].sum()

    else:
        _fig = go.Figure()
        _fig.add_annotation(
            text="No lifecycle data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        _total_active = 0
        _new_contributors = 0
        _full_time = 0
        _part_time = 0
        _churned = 0

    # Display KPIs
    _stats = mo.hstack([
        show_stat(value=_total_active, label='Active Contributors', caption="Current month", format="int"),
        show_stat(value=_new_contributors, label="First Time Contributors", caption="Current month", format="int"),
        show_stat(value=_full_time, label="Full Time Contributors", caption="Current month", format="int"),
        show_stat(value=_part_time, label="Part Time Contributors", caption="Current month", format="int"),
        show_stat(value=_churned, label="Churned Contributors", caption="Current month", format="int"),
    ], widths='equal')

    mo.vstack([
        mo.md("## Collection-Level Lifecycle Analysis"),
        mo.md("""
        This view aggregates developer lifecycle states across all projects in the Protocol Labs Network.
        Use the toggle below to include or exclude dormant and churned contributors.
        """),
        show_inactive_input,
        mo.md("### Key Performance Indicators"),
        _stats,
        mo.md("### Lifecycle State Distribution Over Time"),
        show_plotly(_fig),
        mo.md("""
        **Understanding Lifecycle States:**
        - **First Time**: Contributors making their first contribution to any project in the ecosystem
        - **Full Time**: Contributors with 10+ days of activity per month  
        - **Part Time**: Contributors with 1-9 days of activity per month
        - **Dormant**: Contributors who were active but have no recent activity
        - **Churned**: Contributors who have permanently left the ecosystem
        """)
    ])
    return


@app.cell(hide_code=True)
def project_selector(df_lifecycle, mo):
    # Create project selector dropdown with all available projects
    # Default to "Filecoin" if available, otherwise use the first project
    if not df_lifecycle.empty:
        _projects = sorted(df_lifecycle['project_display_name'].unique().tolist())
        # Prefer Filecoin as the default for this Filecoin-focused notebook
        _preferred_defaults = ['Filecoin', 'libp2p', 'IPFS']
        _default_project = None
        for _pref in _preferred_defaults:
            if _pref in _projects:
                _default_project = _pref
                break
        if _default_project is None:
            _default_project = _projects[0] if _projects else None
    else:
        _projects = []
        _default_project = None

    project_select = mo.ui.dropdown(
        options=_projects,
        value=_default_project,
        label='Select a project:',
        allow_select_none=False,
        full_width=True
    )
    return (project_select,)


@app.cell(hide_code=True)
def lifecycle_project_view(
    ACTIVE_LABELS,
    LIFECYCLE_COLORS,
    LIFECYCLE_LABEL_ORDER,
    df_lifecycle,
    go,
    mo,
    pd,
    project_select,
    px,
    show_inactive_input,
    show_plotly,
    show_stat,
    show_table,
):

    # Filter lifecycle data for selected project
    if not df_lifecycle.empty and project_select.value:
        _df_project = df_lifecycle[df_lifecycle['project_display_name'] == project_select.value].copy()

        # Aggregate by month and label
        _df_agg = _df_project.groupby(['bucket_month', 'label'], as_index=False).agg(
            developers_count=('git_user', 'nunique')
        )

        # Filter based on show_inactive toggle
        if show_inactive_input.value:
            _display_labels = LIFECYCLE_LABEL_ORDER
        else:
            _display_labels = ACTIVE_LABELS

        _df_filtered = _df_agg[_df_agg['label'].isin(_display_labels)].copy()
        _df_filtered['label'] = pd.Categorical(_df_filtered['label'], categories=LIFECYCLE_LABEL_ORDER, ordered=True)

        # Create stacked bar chart
        _fig = px.bar(
            data_frame=_df_filtered,
            x='bucket_month',
            y='developers_count',
            color='label',
            color_discrete_map=LIFECYCLE_COLORS,
            category_orders={'label': LIFECYCLE_LABEL_ORDER},
            labels={'bucket_month': 'Month', 'developers_count': 'Contributors', 'label': 'Lifecycle State'}
        )
        _fig.update_layout(
            barmode='stack',
            template='plotly_white',
            legend_title_text='Lifecycle State',
            font=dict(size=12, color="#111"),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=40, l=20, r=100, b=20),
            hovermode='x unified',
        )
        _fig.update_xaxes(
            title='',
            showgrid=False,
            linecolor="black",
            linewidth=1.5,
            ticks="outside",
            tickformat="%b %Y",
            ticklen=6,
        )
        _fig.update_yaxes(
            title="Contributors",
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

        # Calculate KPIs for the most recent month for this project
        _latest_month = _df_agg['bucket_month'].max()
        _latest_data = _df_agg[_df_agg['bucket_month'] == _latest_month]

        _total_active = _latest_data[_latest_data['label'].isin(ACTIVE_LABELS)]['developers_count'].sum()
        _new_contributors = _latest_data[_latest_data['label'] == 'first time']['developers_count'].sum()
        _full_time = _latest_data[_latest_data['label'].isin(['full time', 'new full time', 'part time to full time', 'dormant to full time'])]['developers_count'].sum()

        # Get top contributors for this project
        _df_top_contributors = _df_project.groupby('git_user', as_index=False).agg(
            total_days_active=('days_active', 'sum'),
            months_active=('bucket_month', 'nunique'),
            first_contribution=('first_contribution_month', 'min'),
            last_contribution=('last_contribution_month', 'max'),
        ).sort_values('total_days_active', ascending=False).head(10)
        _df_top_contributors = _df_top_contributors.rename(columns={
            'git_user': 'Contributor',
            'total_days_active': 'Total Days Active',
            'months_active': 'Months Active',
            'first_contribution': 'First Contribution',
            'last_contribution': 'Last Contribution'
        })

    else:
        _fig = go.Figure()
        _fig.add_annotation(
            text="No lifecycle data available for selected project",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        _total_active = 0
        _new_contributors = 0
        _full_time = 0
        _df_top_contributors = pd.DataFrame(columns=['Contributor', 'Total Days Active', 'Months Active', 'First Contribution', 'Last Contribution'])

    # Display KPIs
    _stats = mo.hstack([
        show_stat(value=_total_active, label='Active Contributors', caption="Current month", format="int"),
        show_stat(value=_new_contributors, label="First Time Contributors", caption="Current month", format="int"),
        show_stat(value=_full_time, label="Full Time Contributors", caption="Current month", format="int"),
    ], widths='equal')

    _project_name = project_select.value if project_select.value else "No Project Selected"
    _project_count = df_lifecycle['project_display_name'].nunique() if not df_lifecycle.empty else 0
    
    mo.vstack([
        mo.md("## Project-Level Lifecycle Analysis"),
        mo.md(f"""
        Select a specific project from the **{_project_count} projects** in the Protocol Labs Network 
        to view its developer lifecycle patterns and top contributors.
        """),
        project_select,
        mo.md(f"### {_project_name} - Key Metrics"),
        _stats,
        mo.md(f"### {_project_name} - Lifecycle State Distribution"),
        show_plotly(_fig),
        mo.md(f"### {_project_name} - Top Contributors"),
        show_table(_df_top_contributors)
    ])
    return


@app.cell(hide_code=True)
def project_comparison(
    ACTIVE_LABELS,
    df_lifecycle,
    go,
    mo,
    pd,
    px,
    show_plotly,
    show_table,
):

    if not df_lifecycle.empty:
        # Aggregate by project and month
        _df_project_agg = df_lifecycle[df_lifecycle['label'].isin(ACTIVE_LABELS)].groupby(
            ['bucket_month', 'project_display_name'],
            as_index=False
        ).agg(
            active_contributors=('git_user', 'nunique')
        )

        # Get top 10 projects by recent activity
        _latest_month = _df_project_agg['bucket_month'].max()
        _top_projects = _df_project_agg[_df_project_agg['bucket_month'] == _latest_month].nlargest(10, 'active_contributors')['project_display_name'].tolist()

        _df_top = _df_project_agg[_df_project_agg['project_display_name'].isin(_top_projects)]

        _fig = px.line(
            data_frame=_df_top,
            x='bucket_month',
            y='active_contributors',
            color='project_display_name',
            labels={
                'bucket_month': 'Month',
                'active_contributors': 'Active Contributors',
                'project_display_name': 'Project'
            }
        )
        _fig.update_layout(
            template='plotly_white',
            font=dict(size=12, color="#111"),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=40, l=20, r=20, b=20),
            hovermode='x unified',
            legend=dict(
                orientation="v",
                x=1.00,
                y=1.00,
                xanchor="left",
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
        _fig.update_traces(line=dict(width=2))

        # Create summary table
        _df_summary = df_lifecycle.groupby('project_display_name', as_index=False).agg(
            total_contributors=('git_user', 'nunique'),
            total_days_active=('days_active', 'sum'),
            first_contribution=('first_contribution_month', 'min'),
            latest_contribution=('last_contribution_month', 'max'),
        ).sort_values('total_contributors', ascending=False)
        _df_summary = _df_summary.rename(columns={
            'project_display_name': 'Project',
            'total_contributors': 'Total Contributors',
            'total_days_active': 'Total Days Active',
            'first_contribution': 'First Contribution',
            'latest_contribution': 'Latest Contribution'
        })

    else:
        _fig = go.Figure()
        _fig.add_annotation(
            text="No comparison data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        _df_summary = pd.DataFrame(columns=['Project', 'Total Contributors', 'Total Days Active', 'First Contribution', 'Latest Contribution'])

    mo.vstack([
        mo.md("## Project Comparison"),
        mo.md("""
        Compare active contributor counts across the top projects in the Protocol Labs Network.
        The chart below shows the top 10 projects by recent contributor activity.
        """),
        mo.md("### Active Contributors by Project (Top 10)"),
        show_plotly(_fig),
        mo.md("### All Projects Summary"),
        mo.md("""
        This table shows all projects in the ecosystem with their total contributor counts and activity span.
        Sort by any column to find specific projects.
        """),
        show_table(_df_summary)
    ])
    return


@app.cell(hide_code=True)
def retention_analysis(
    ACTIVE_LABELS,
    df_lifecycle,
    go,
    mo,
    pd,
    px,
    show_plotly,
    show_stat,
):

    if not df_lifecycle.empty:
        # Calculate retention metrics by cohort (first contribution month)
        _df_cohorts = df_lifecycle.copy()
        _df_cohorts['cohort_month'] = pd.to_datetime(_df_cohorts['first_contribution_month']).dt.to_period('M').dt.to_timestamp()
        _df_cohorts['months_since_first'] = (
            pd.to_datetime(_df_cohorts['bucket_month']).dt.to_period('M').astype(int) -
            pd.to_datetime(_df_cohorts['first_contribution_month']).dt.to_period('M').astype(int)
        )

        # Count active contributors by cohort and months since first contribution
        _df_retention = _df_cohorts[_df_cohorts['label'].isin(ACTIVE_LABELS)].groupby(
            ['cohort_month', 'months_since_first'],
            as_index=False
        ).agg(
            active_contributors=('git_user', 'nunique')
        )

        # Get cohort sizes (month 0)
        _cohort_sizes = _df_retention[_df_retention['months_since_first'] == 0][['cohort_month', 'active_contributors']].rename(
            columns={'active_contributors': 'cohort_size'}
        )

        _df_retention = _df_retention.merge(_cohort_sizes, on='cohort_month')
        _df_retention['retention_rate'] = (_df_retention['active_contributors'] / _df_retention['cohort_size'] * 100).round(1)

        # Filter to show meaningful cohorts (at least 6 months old, at least 5 contributors)
        _min_cohort_date = _df_retention['cohort_month'].max() - pd.DateOffset(months=6)
        _df_retention_filtered = _df_retention[
            (_df_retention['cohort_month'] <= _min_cohort_date) &
            (_df_retention['cohort_size'] >= 5) &
            (_df_retention['months_since_first'] <= 12)
        ]

        # Average retention by months since first contribution
        _df_avg_retention = _df_retention_filtered.groupby('months_since_first', as_index=False).agg(
            avg_retention_rate=('retention_rate', 'mean')
        )

        _fig = px.line(
            data_frame=_df_avg_retention,
            x='months_since_first',
            y='avg_retention_rate',
            labels={
                'months_since_first': 'Months Since First Contribution',
                'avg_retention_rate': 'Retention Rate (%)'
            },
            markers=True
        )
        _fig.update_traces(line=dict(color='teal', width=3), marker=dict(size=8))
        _fig.update_layout(
            template='plotly_white',
            font=dict(size=12, color="#111"),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=40, l=20, r=20, b=20),
            hovermode='x unified',
        )
        _fig.update_xaxes(
            showline=True,
            linewidth=1.5,
            linecolor="black",
            ticks="outside",
        )
        _fig.update_yaxes(
            showline=True,
            linewidth=1.5,
            linecolor="black",
            ticks="outside",
            range=[0, 100]
        )

        # Calculate summary retention metrics
        _month_1_retention = _df_avg_retention[_df_avg_retention['months_since_first'] == 1]['avg_retention_rate'].values
        _month_3_retention = _df_avg_retention[_df_avg_retention['months_since_first'] == 3]['avg_retention_rate'].values
        _month_6_retention = _df_avg_retention[_df_avg_retention['months_since_first'] == 6]['avg_retention_rate'].values
        _month_12_retention = _df_avg_retention[_df_avg_retention['months_since_first'] == 12]['avg_retention_rate'].values

        _m1 = _month_1_retention[0] if len(_month_1_retention) > 0 else 0
        _m3 = _month_3_retention[0] if len(_month_3_retention) > 0 else 0
        _m6 = _month_6_retention[0] if len(_month_6_retention) > 0 else 0
        _m12 = _month_12_retention[0] if len(_month_12_retention) > 0 else 0

    else:
        _fig = go.Figure()
        _m1, _m3, _m6, _m12 = 0, 0, 0, 0

    _stats = mo.hstack([
        show_stat(value=_m1, label='1 Month Retention', caption="Average across cohorts", format="pct"),
        show_stat(value=_m3, label='3 Month Retention', caption="Average across cohorts", format="pct"),
        show_stat(value=_m6, label='6 Month Retention', caption="Average across cohorts", format="pct"),
        show_stat(value=_m12, label='12 Month Retention', caption="Average across cohorts", format="pct"),
    ], widths='equal')

    mo.vstack([
        mo.md("## Contributor Retention Analysis"),
        mo.md("""
        Retention analysis shows what percentage of contributors who joined in a given month remain active over time.
        This helps understand how well the ecosystem is retaining developers after their first contribution.
        """),
        _stats,
        mo.md("### Average Retention Curve"),
        mo.md("""
        The curve below shows the average retention rate across all contributor cohorts. 
        A higher retention rate indicates better developer engagement and stickiness.
        """),
        show_plotly(_fig)
    ])
    return


@app.cell(hide_code=True)
def summary_section(mo):
    mo.vstack([
        mo.md("---"),
        mo.md("## Summary"),
        mo.md("""
        This notebook provides comprehensive developer lifecycle analysis for the Protocol Labs Network and Filecoin ecosystems. 
        Key insights can be derived from:

        - **Collection-level trends**: Overall ecosystem health and contributor engagement patterns
        - **Project-level analysis**: Individual project performance and lifecycle states
        - **Contributor retention**: How well the ecosystem retains developers over time
        - **Project comparison**: Relative performance across different projects

        For more detailed analysis, consider:
        - Filtering by specific time ranges
        - Comparing individual projects within collections
        - Examining artifact-level metrics for specific repositories
        - Using the OSO data warehouse directly for custom queries
        """),
    ])
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Code
    """)
    return


@app.cell(hide_code=True)
def plotly_layout():
    LAYOUT_SETTINGS = dict(
        font=dict(size=12, color="#111"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(t=0, l=20, r=20, b=0),
        legend=dict(
            orientation="v",
            x=0.01,
            y=1.00,
            xanchor="left",
            yanchor="top"
        ),
        xaxis=dict(
            showline=True,
            linewidth=1.5,
            linecolor="black",
            ticks="outside",
            tickwidth=1.5,
            tickcolor="black",
            ticklen=6,
        ),
        yaxis=dict(
            showline=True,
            linewidth=1.5,
            linecolor="black",
            ticks="outside",
            tickwidth=1.5,
            tickcolor="black",
            ticklen=6,
            rangemode="tozero"
        )
    )
    return (LAYOUT_SETTINGS,)


@app.cell(hide_code=True)
def ui_helpers(mo):
    def show_plotly(fig, **kwargs):
        return mo.ui.plotly(
            fig,
            config={'displayModeBar': False},
            **kwargs
        )

    def show_table(df, **kwargs):
        _fmt = {}
        for col in df.columns:
            if df[col].dtype == 'int64':
                _fmt[col] = '{:,.0f}'
            elif df[col].dtype == 'float64':
                _fmt[col] = '{:,.2f}'
        return mo.ui.table(
            df.reset_index(drop=True),
            format_mapping=_fmt,
            show_column_summaries=False,
            show_data_types=False,
            **kwargs
        )

    def show_stat(
        value,
        label,
        caption="",
        format="int"
    ):
        if format == "int":
            value_str = f"{value:,.0f}" if isinstance(value, (int, float)) else str(value)
        elif format == "1f":
            value_str = f"{value:,.1f}" if isinstance(value, (int, float)) else str(value)
        elif format == "pct":
            value_str = f"{value:.1f}%" if isinstance(value, (int, float)) else str(value)
        else:
            value_str = str(value)
        return mo.stat(
            value=value_str,
            label=label,
            caption=caption,
            bordered=True
        )

    def show_insight(
        headline:str='This is a sample headline',
        level:int=2,
        elements:list|None=None,
    ):
        if elements is None:
            elements = []

        level = max(1, min(level, 6))
        header_md = mo.md(f"{'#' * level} {headline}")
        return mo.vstack([header_md, *elements])
    return show_insight, show_plotly, show_stat, show_table


@app.function(hide_code=True)
def stringify(arr):
    return "'" + "','".join(arr) + "'"


@app.cell(hide_code=True)
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


if __name__ == "__main__":
    app.run()
