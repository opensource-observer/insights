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
    # PLN Repository Explorer
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">Protocol Labs</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-11</span></small>
    """
    )
    return


# =============================================================================
# KPI SUMMARY CARDS
# =============================================================================


@app.cell(hide_code=True)
def _(df_kpis, mo):
    if not df_kpis.empty:
        _total_repos = df_kpis['total_repos'].iloc[0] if 'total_repos' in df_kpis.columns else 0
        _total_stars = df_kpis['total_stars'].iloc[0] if 'total_stars' in df_kpis.columns else 0
        _total_forks = df_kpis['total_forks'].iloc[0] if 'total_forks' in df_kpis.columns else 0
        _total_contributors = df_kpis['total_contributors'].iloc[0] if 'total_contributors' in df_kpis.columns else 0
    else:
        _total_repos = 0
        _total_stars = 0
        _total_forks = 0
        _total_contributors = 0

    mo.hstack(
        [
            mo.stat(
                label="Total Repositories",
                value=f"{_total_repos:,.0f}",
                caption="GitHub repos in PLN",
                bordered=True
            ),
            mo.stat(
                label="Total Stars",
                value=f"{_total_stars:,.0f}",
                caption="Across all repos",
                bordered=True
            ),
            mo.stat(
                label="Total Forks",
                value=f"{_total_forks:,.0f}",
                caption="Across all repos",
                bordered=True
            ),
            mo.stat(
                label="Total Contributors",
                value=f"{_total_contributors:,.0f}",
                caption="Unique contributors",
                bordered=True
            ),
        ],
        widths="equal",
        gap=2
    )
    return


# =============================================================================
# GLOBAL FILTERS
# =============================================================================


@app.cell(hide_code=True)
def _(df_collections, df_projects, mo):
    collection_filter = mo.ui.dropdown(
        options=['All'] + df_collections['collection_name'].tolist() if not df_collections.empty else ['All'],
        value='All',
        label='Collection:'
    )
    
    project_filter = mo.ui.dropdown(
        options=['All'] + sorted(df_projects['project_name'].unique().tolist()) if not df_projects.empty else ['All'],
        value='All',
        label='Project:'
    )
    
    min_stars = mo.ui.slider(
        start=0,
        stop=1000,
        value=0,
        step=10,
        label='Min Stars:'
    )

    mo.hstack(
        [collection_filter, project_filter, min_stars],
        justify="start",
        gap=2
    )
    return collection_filter, project_filter, min_stars


# =============================================================================
# FILTERED DATA
# =============================================================================


@app.cell
def _(collection_filter, df_repos, min_stars, project_filter):
    df_filtered = df_repos.copy()
    
    if collection_filter.value != 'All':
        df_filtered = df_filtered[df_filtered['collection_name'] == collection_filter.value]
    
    if project_filter.value != 'All':
        df_filtered = df_filtered[df_filtered['project_name'] == project_filter.value]
    
    if min_stars.value > 0:
        df_filtered = df_filtered[df_filtered['stars'] >= min_stars.value]
    
    df_filtered = df_filtered.sort_values('stars', ascending=False)
    return (df_filtered,)


# =============================================================================
# MAIN CONTENT
# =============================================================================


@app.cell(hide_code=True)
def _(df_filtered, mo, px):
    # Scatter plot: Stars vs Forks
    if not df_filtered.empty:
        _fig = px.scatter(
            data_frame=df_filtered,
            x='stars',
            y='forks',
            size='contributors',
            color='collection_name',
            hover_name='repository',
            hover_data=['project_display_name', 'stars', 'forks', 'contributors'],
            size_max=40
        )
        _fig.update_layout(
            title="",
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(size=12, color="#111"),
            margin=dict(t=20, l=0, r=0, b=50),
            xaxis=dict(
                title="Stars",
                showgrid=True, gridcolor="#EEE",
                linecolor="#000", linewidth=1
            ),
            yaxis=dict(
                title="Forks",
                showgrid=True, gridcolor="#EEE",
                linecolor="#000", linewidth=1
            ),
            legend=dict(orientation="h", y=-0.15)
        )
        _chart = mo.ui.plotly(_fig, config={'displayModeBar': False})
    else:
        _chart = mo.md("*No repositories match the current filters*")
    
    mo.vstack([
        mo.md("### Stars vs Forks"),
        mo.md("Bubble size represents contributor count. Hover for details."),
        _chart
    ])
    return


@app.cell(hide_code=True)
def _(df_filtered, mo):
    # Repository table
    if not df_filtered.empty:
        _display_df = df_filtered[[
            'repository',
            'project_display_name',
            'collection_name',
            'stars',
            'forks',
            'contributors'
        ]].copy()
        
        _display_df = _display_df.rename(columns={
            'repository': 'Repository',
            'project_display_name': 'Project',
            'collection_name': 'Collection',
            'stars': 'Stars',
            'forks': 'Forks',
            'contributors': 'Contributors'
        })
        
        _table = mo.ui.table(
            _display_df.reset_index(drop=True),
            format_mapping={
                'Stars': '{:,.0f}',
                'Forks': '{:,.0f}',
                'Contributors': '{:,.0f}'
            },
            show_column_summaries=False,
            show_data_types=False,
            page_size=25,
            freeze_columns_left=['Repository']
        )
    else:
        _table = mo.md("*No repositories match the current filters*")
    
    mo.vstack([
        mo.md(f"### Repository Details ({len(df_filtered):,} repos)"),
        _table
    ])
    return


# =============================================================================
# TOP REPOSITORIES BY METRIC
# =============================================================================


@app.cell(hide_code=True)
def _(df_filtered, mo, px):
    # Top 10 by stars
    if not df_filtered.empty:
        _top_stars = df_filtered.nlargest(10, 'stars')[['repository', 'stars', 'project_display_name']]
        
        _fig = px.bar(
            data_frame=_top_stars,
            x='stars',
            y='repository',
            orientation='h',
            text='stars',
            color='project_display_name',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        _fig.update_traces(textposition='outside', texttemplate='%{text:,.0f}')
        _fig.update_layout(
            title="",
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(size=12, color="#111"),
            margin=dict(t=0, l=0, r=80, b=50),
            xaxis=dict(title="Stars", showgrid=True, gridcolor="#EEE"),
            yaxis=dict(title="", autorange="reversed"),
            legend=dict(orientation="h", y=-0.2),
            showlegend=True
        )
        _chart = mo.ui.plotly(_fig, config={'displayModeBar': False})
    else:
        _chart = mo.md("*No data available*")
    
    mo.vstack([
        mo.md("### Top 10 Repositories by Stars"),
        _chart
    ])
    return


@app.cell(hide_code=True)
def _(df_filtered, mo, px):
    # Top 10 by contributors
    if not df_filtered.empty and 'contributors' in df_filtered.columns:
        _top_contributors = df_filtered.nlargest(10, 'contributors')[['repository', 'contributors', 'project_display_name']]
        
        _fig = px.bar(
            data_frame=_top_contributors,
            x='contributors',
            y='repository',
            orientation='h',
            text='contributors',
            color='project_display_name',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        _fig.update_traces(textposition='outside', texttemplate='%{text:,.0f}')
        _fig.update_layout(
            title="",
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(size=12, color="#111"),
            margin=dict(t=0, l=0, r=80, b=50),
            xaxis=dict(title="Contributors", showgrid=True, gridcolor="#EEE"),
            yaxis=dict(title="", autorange="reversed"),
            legend=dict(orientation="h", y=-0.2),
            showlegend=True
        )
        _chart = mo.ui.plotly(_fig, config={'displayModeBar': False})
    else:
        _chart = mo.md("*No data available*")
    
    mo.vstack([
        mo.md("### Top 10 Repositories by Contributors"),
        _chart
    ])
    return


# =============================================================================
# PROJECT SUMMARY
# =============================================================================


@app.cell(hide_code=True)
def _(df_filtered, mo):
    # Aggregate by project
    if not df_filtered.empty:
        _by_project = df_filtered.groupby(['project_display_name', 'collection_name']).agg({
            'repository': 'count',
            'stars': 'sum',
            'forks': 'sum',
            'contributors': 'sum'
        }).reset_index()
        
        _by_project = _by_project.rename(columns={
            'project_display_name': 'Project',
            'collection_name': 'Collection',
            'repository': 'Repos',
            'stars': 'Total Stars',
            'forks': 'Total Forks',
            'contributors': 'Total Contributors'
        })
        
        _by_project = _by_project.sort_values('Total Stars', ascending=False)
        
        _table = mo.ui.table(
            _by_project.reset_index(drop=True),
            format_mapping={
                'Repos': '{:,.0f}',
                'Total Stars': '{:,.0f}',
                'Total Forks': '{:,.0f}',
                'Total Contributors': '{:,.0f}'
            },
            show_column_summaries=False,
            show_data_types=False,
            page_size=20
        )
    else:
        _table = mo.md("*No data available*")
    
    mo.vstack([
        mo.md("### Project Summary"),
        mo.md("Aggregated metrics across all repositories for each project."),
        _table
    ])
    return


# =============================================================================
# DATA QUERIES
# =============================================================================


@app.cell
def _(mo, pyoso_db_conn):
    df_collections = mo.sql(
        """
        SELECT DISTINCT
          collection_name,
          display_name
        FROM collections_v1
        WHERE collection_source = 'OSS_DIRECTORY'
        AND collection_name IN ('protocol-labs-network', 'filecoin-core', 'filecoin-builders')
        ORDER BY collection_name
        """,
        engine=pyoso_db_conn,
        output=False
    )
    return (df_collections,)


@app.cell
def _(mo, pyoso_db_conn):
    df_projects = mo.sql(
        """
        SELECT DISTINCT
          p.project_name,
          p.display_name AS project_display_name
        FROM projects_by_collection_v1 pbc
        JOIN projects_v1 p USING (project_id)
        WHERE pbc.collection_name IN ('protocol-labs-network', 'filecoin-core', 'filecoin-builders')
        ORDER BY p.display_name
        """,
        engine=pyoso_db_conn,
        output=False
    )
    return (df_projects,)


@app.cell
def _(mo, pyoso_db_conn):
    df_kpis = mo.sql(
        """
        WITH repo_metrics AS (
          SELECT
            a.artifact_id AS artifact_id,
            MAX(CASE WHEN m.metric_model = 'stars' THEN km.amount END) AS stars,
            MAX(CASE WHEN m.metric_model = 'forks' THEN km.amount END) AS forks,
            MAX(CASE WHEN m.metric_model = 'contributors' THEN km.amount END) AS contributors
          FROM artifacts_by_project_v1 a
          JOIN projects_by_collection_v1 pbc ON a.project_id = pbc.project_id
          LEFT JOIN key_metrics_by_artifact_v0 km ON a.artifact_id = km.artifact_id
          LEFT JOIN metrics_v0 m ON km.metric_id = m.metric_id
          WHERE pbc.collection_name = 'protocol-labs-network'
          AND a.artifact_source = 'GITHUB'
          GROUP BY a.artifact_id
        )
        SELECT
          COUNT(DISTINCT artifact_id) AS total_repos,
          COALESCE(SUM(stars), 0) AS total_stars,
          COALESCE(SUM(forks), 0) AS total_forks,
          COALESCE(SUM(contributors), 0) AS total_contributors
        FROM repo_metrics
        """,
        engine=pyoso_db_conn,
        output=False
    )
    return (df_kpis,)


@app.cell
def _(mo, pyoso_db_conn):
    df_repos = mo.sql(
        """
        WITH repo_metrics AS (
          SELECT
            a.artifact_id AS artifact_id,
            a.artifact_namespace || '/' || a.artifact_name AS repository,
            a.artifact_namespace,
            a.artifact_name,
            p.project_name,
            p.display_name AS project_display_name,
            pbc.collection_name,
            MAX(CASE WHEN m.metric_model = 'stars' THEN km.amount END) AS stars,
            MAX(CASE WHEN m.metric_model = 'forks' THEN km.amount END) AS forks,
            MAX(CASE WHEN m.metric_model = 'contributors' THEN km.amount END) AS contributors
          FROM artifacts_by_project_v1 a
          JOIN projects_v1 p ON a.project_id = p.project_id
          JOIN projects_by_collection_v1 pbc ON a.project_id = pbc.project_id
          LEFT JOIN key_metrics_by_artifact_v0 km ON a.artifact_id = km.artifact_id
          LEFT JOIN metrics_v0 m ON km.metric_id = m.metric_id
          WHERE pbc.collection_name IN ('protocol-labs-network', 'filecoin-core', 'filecoin-builders')
          AND a.artifact_source = 'GITHUB'
          GROUP BY 
            a.artifact_id,
            a.artifact_namespace,
            a.artifact_name,
            p.project_name,
            p.display_name,
            pbc.collection_name
        )
        SELECT 
          repository,
          artifact_namespace,
          artifact_name,
          project_name,
          project_display_name,
          collection_name,
          COALESCE(stars, 0) AS stars,
          COALESCE(forks, 0) AS forks,
          COALESCE(contributors, 0) AS contributors
        FROM repo_metrics
        ORDER BY stars DESC
        """,
        engine=pyoso_db_conn,
        output=False
    )
    return (df_repos,)


# =============================================================================
# BOILERPLATE
# =============================================================================


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    return go, pd, px


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
