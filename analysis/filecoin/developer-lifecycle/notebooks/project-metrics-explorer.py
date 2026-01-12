import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # PLN Project Metrics Explorer
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">Protocol Labs</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-12</span></small>
    """)
    return


@app.cell(hide_code=True)
def _(df_kpis, mo, ref_month):
    if not df_kpis.empty:
        _total_projects = df_kpis['total_projects'].iloc[0] if 'total_projects' in df_kpis.columns else 0
        _total_repos = df_kpis['total_repos'].iloc[0] if 'total_repos' in df_kpis.columns else 0
        _total_stars = df_kpis['total_stars'].iloc[0] if 'total_stars' in df_kpis.columns else 0
        _total_forks = df_kpis['total_forks'].iloc[0] if 'total_forks' in df_kpis.columns else 0
    else:
        _total_projects = 0
        _total_repos = 0
        _total_stars = 0
        _total_forks = 0

    mo.hstack(
        [
            mo.stat(
                label="Projects",
                value=f"{_total_projects:,.0f}",
                caption="In Protocol Labs Network",
                bordered=True
            ),
            mo.stat(
                label="Repositories",
                value=f"{_total_repos:,.0f}",
                caption="GitHub repos",
                bordered=True
            ),
            mo.stat(
                label="Stars",
                value=f"{_total_stars:,.0f}",
                caption="Total across repos",
                bordered=True
            ),
            mo.stat(
                label="Forks",
                value=f"{_total_forks:,.0f}",
                caption="Total across repos",
                bordered=True
            ),
        ],
        widths="equal",
        gap=2
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Explore Project Metrics

    Select a project to view its contributor metrics over time. You can also select multiple metrics to compare.
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
def _(mo):
    metric_selector = mo.ui.multiselect(
        options={
            'active_full_time_contributor': 'Full-Time Contributors',
            'active_part_time_contributor': 'Part-Time Contributors',
            'first_time_contributor': 'First-Time Contributors',
            'commits': 'Commits',
            'pull_requests_opened': 'Pull Requests Opened',
            'issues_opened': 'Issues Opened',
        },
        value=['active_full_time_contributor', 'active_part_time_contributor'],
        label="Select Metrics:"
    )
    metric_selector
    return (metric_selector,)


@app.cell(hide_code=True)
def _(
    PLOTLY_LAYOUT,
    df_project_metrics,
    metric_selector,
    mo,
    pd,
    project_selector,
    px,
):
    if project_selector.value and metric_selector.value and not df_project_metrics.empty:
        _df = df_project_metrics[
            (df_project_metrics['project'] == project_selector.value) &
            (df_project_metrics['metric_model'].isin(metric_selector.value))
        ].copy()
        _df['sample_date'] = pd.to_datetime(_df['sample_date'])

        if not _df.empty:
            _fig = px.line(
                data_frame=_df,
                x='sample_date',
                y='amount',
                color='metric_model'
            )
            _fig.update_layout(**PLOTLY_LAYOUT)
            _fig.update_traces(line=dict(width=2.5))
            _chart = mo.ui.plotly(_fig, config={'displayModeBar': False})
        else:
            _chart = mo.md("*No data available for selected metrics*")
    else:
        _chart = mo.md("*Select a project and metrics to view data*")

    mo.vstack([
        mo.md(f"### {project_selector.value or 'Project'} - Metrics Over Time"),
        _chart
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Project Comparison

    Compare metrics across the top projects in the ecosystem.
    """)
    return


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_top_projects, mo, px):
    if not df_top_projects.empty:
        _fig = px.bar(
            data_frame=df_top_projects.head(15),
            x='avg_contributors',
            y='project',
            orientation='h',
            text='avg_contributors',
            color='collection_name'
        )
        _fig.update_traces(textposition='outside', texttemplate='%{text:,.1f}')
        _fig.update_layout(**PLOTLY_LAYOUT)
        _fig.update_layout(
            yaxis=dict(title="", autorange="reversed"),
            xaxis=dict(title="Avg Monthly Full-Time Contributors")
        )
        _chart = mo.ui.plotly(_fig, config={'displayModeBar': False})
    else:
        _chart = mo.md("*No data available*")

    mo.vstack([
        mo.md("### Top 15 Projects by Full-Time Contributors"),
        _chart
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Repository Details

    Browse repositories for the selected project. Data includes stars, forks, language, and license information.
    """)
    return


@app.cell(hide_code=True)
def _(df_project_repos, mo, project_selector):
    if project_selector.value and not df_project_repos.empty:
        _df = df_project_repos[df_project_repos['project'] == project_selector.value].copy()

        if not _df.empty:
            _display_df = _df[[
                'repository',
                'star_count',
                'fork_count',
                'language',
                'license_name',
                'is_fork'
            ]].copy()

            _display_df = _display_df.rename(columns={
                'repository': 'Repository',
                'star_count': 'Stars',
                'fork_count': 'Forks',
                'language': 'Language',
                'license_name': 'License',
                'is_fork': 'Is Fork'
            })

            _display_df = _display_df.sort_values('Stars', ascending=False)

            _table = mo.ui.table(
                _display_df.reset_index(drop=True),
                format_mapping={
                    'Stars': '{:,.0f}',
                    'Forks': '{:,.0f}'
                },
                show_column_summaries=False,
                show_data_types=False,
                page_size=20,
                freeze_columns_left=['Repository']
            )
        else:
            _table = mo.md("*No repositories found for this project*")
    else:
        _table = mo.md("*Select a project to view its repositories*")

    mo.vstack([
        mo.md(f"### Repositories for {project_selector.value or 'Selected Project'}"),
        _table
    ])
    return


@app.cell(hide_code=True)
def _(df_project_repos, mo, project_selector, px):
    if project_selector.value and not df_project_repos.empty:
        _df = df_project_repos[df_project_repos['project'] == project_selector.value].copy()

        if not _df.empty and len(_df) >= 2:
            # Language distribution pie chart
            _lang_counts = _df.groupby('language').size().reset_index(name='count')
            _lang_counts = _lang_counts.sort_values('count', ascending=False).head(10)

            _fig = px.pie(
                data_frame=_lang_counts,
                values='count',
                names='language',
                title=""
            )
            _fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(size=12, color="#111"),
                margin=dict(t=20, l=0, r=0, b=0)
            )
            _chart = mo.ui.plotly(_fig, config={'displayModeBar': False})
        else:
            _chart = mo.md("*Not enough repositories to show language distribution*")
    else:
        _chart = mo.md("*Select a project*")

    mo.vstack([
        mo.md("### Language Distribution"),
        _chart
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## All Projects Summary

    Complete list of projects with aggregated repository metrics.
    """)
    return


@app.cell(hide_code=True)
def _(df_project_summary, mo):
    if not df_project_summary.empty:
        _display_df = df_project_summary.copy()
        _display_df = _display_df.rename(columns={
            'project': 'Project',
            'collection_name': 'Collection',
            'repo_count': 'Repos',
            'total_stars': 'Stars',
            'total_forks': 'Forks'
        })

        _table = mo.ui.table(
            _display_df.reset_index(drop=True),
            format_mapping={
                'Repos': '{:,.0f}',
                'Stars': '{:,.0f}',
                'Forks': '{:,.0f}'
            },
            show_column_summaries=False,
            show_data_types=False,
            page_size=25
        )
    else:
        _table = mo.md("*No data available*")

    mo.vstack([
        mo.md(f"### All Projects ({len(df_project_summary)} total)"),
        _table
    ])
    return


@app.cell
def _(pd):
    # Reference month: 2 months before current date
    ref_month = (pd.Timestamp.now() - pd.DateOffset(months=2)).strftime('%Y-%m-01')
    return (ref_month,)


@app.cell
def _(df_project_summary, pd):
    # Calculate KPIs from the project summary data
    if not df_project_summary.empty:
        df_kpis = pd.DataFrame({
            'total_projects': [len(df_project_summary)],
            'total_repos': [df_project_summary['repo_count'].sum()],
            'total_stars': [df_project_summary['total_stars'].sum()],
            'total_forks': [df_project_summary['total_forks'].sum()]
        })
    else:
        df_kpis = pd.DataFrame({
            'total_projects': [0],
            'total_repos': [0],
            'total_stars': [0],
            'total_forks': [0]
        })
    return (df_kpis,)


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
    df_project_metrics = mo.sql(
        f"""
        SELECT 
          p.display_name AS project,
          ts.sample_date,
          m.metric_model,
          SUM(ts.amount) AS amount
        FROM timeseries_metrics_by_project_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN projects_v1 p USING (project_id)
        JOIN projects_by_collection_v1 pbc USING (project_id)
        WHERE pbc.collection_name = 'protocol-labs-network'
        AND m.metric_time_aggregation = 'monthly'
        AND m.metric_model IN (
          'active_full_time_contributor',
          'active_part_time_contributor',
          'first_time_contributor',
          'commits',
          'pull_requests_opened',
          'issues_opened'
        )
        AND ts.sample_date <= DATE('{ref_month}')
        GROUP BY p.display_name, ts.sample_date, m.metric_model
        ORDER BY ts.sample_date
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_project_metrics['sample_date'] = pd.to_datetime(df_project_metrics['sample_date'])
    return (df_project_metrics,)


@app.cell
def _(mo, pyoso_db_conn, ref_month):
    df_top_projects = mo.sql(
        f"""
        SELECT 
          p.display_name AS project,
          pbc.collection_name,
          AVG(ts.amount) AS avg_contributors
        FROM timeseries_metrics_by_project_v0 ts
        JOIN metrics_v0 m USING (metric_id)
        JOIN projects_v1 p USING (project_id)
        JOIN projects_by_collection_v1 pbc USING (project_id)
        WHERE pbc.collection_name IN ('protocol-labs-network', 'filecoin-core', 'filecoin-builders')
        AND m.metric_model = 'active_full_time_contributor'
        AND m.metric_time_aggregation = 'monthly'
        AND ts.sample_date >= DATE_ADD('year', -1, DATE('{ref_month}'))
        AND ts.sample_date <= DATE('{ref_month}')
        GROUP BY p.display_name, pbc.collection_name
        HAVING AVG(ts.amount) > 0
        ORDER BY avg_contributors DESC
        LIMIT 20
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_top_projects,)


@app.cell
def _(mo, pyoso_db_conn):
    df_project_repos = mo.sql(
        """
        SELECT 
          p.display_name AS project,
          r.artifact_namespace || '/' || r.artifact_name AS repository,
          r.star_count,
          r.fork_count,
          r.language,
          r.license_name,
          r.is_fork
        FROM repositories_v0 r
        JOIN artifacts_by_project_v1 a ON r.artifact_id = a.artifact_id
        JOIN projects_v1 p ON a.project_id = p.project_id
        JOIN projects_by_collection_v1 pbc ON p.project_id = pbc.project_id
        WHERE pbc.collection_name = 'protocol-labs-network'
        AND r.artifact_source = 'GITHUB'
        ORDER BY r.star_count DESC NULLS LAST
        """,
        engine=pyoso_db_conn,
        output=False
    )
    return (df_project_repos,)


@app.cell
def _(mo, pyoso_db_conn):
    df_project_summary = mo.sql(
        """
        SELECT 
          p.display_name AS project,
          pbc.collection_name,
          COUNT(DISTINCT r.artifact_id) AS repo_count,
          COALESCE(SUM(r.star_count), 0) AS total_stars,
          COALESCE(SUM(r.fork_count), 0) AS total_forks
        FROM projects_v1 p
        JOIN projects_by_collection_v1 pbc USING (project_id)
        JOIN artifacts_by_project_v1 a USING (project_id)
        LEFT JOIN repositories_v0 r ON a.artifact_id = r.artifact_id AND r.artifact_source = 'GITHUB'
        WHERE pbc.collection_name = 'protocol-labs-network'
        AND a.artifact_source = 'GITHUB'
        GROUP BY p.display_name, pbc.collection_name
        ORDER BY total_stars DESC
        """,
        engine=pyoso_db_conn,
        output=False
    )
    return (df_project_summary,)


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
