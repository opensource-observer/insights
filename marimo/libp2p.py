import marimo

__generated_with = "0.15.2"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    
    client = pyoso.Client()
    return client, mo, pd, px


@app.cell
def _(mo):
    mo.md(
        """
    # Downstream Ecosystem Analysis: `libp2p`

    This notebook analyzes the downstream ecosystem of the `libp2p` package. The goal is to understand which open-source projects depend on `libp2p` and to gauge the development activity within those projects.

    ## Methodology

    We use the [OSO](https://docs.opensource.observer/docs/get-started/python) API to query data about open-source projects. The analysis proceeds in two main steps:

    1.  **Identifying Dependents:** We first query for all projects in the OSS Directory that list `libp2p` as a dependency in their Software Bill of Materials (SBOM).
    2.  **Measuring Activity:** For each of these dependent projects, we then query for the number of monthly active developers as of a specific snapshot date.

    ## Visualizations

    The notebook generates two visualizations to explore this data:

    1.  **Package Manager Distribution:** A pie chart shows the breakdown of `libp2p`'s downstream dependents by their package manager (e.g., Go Modules, NPM, etc.). This helps us understand where `libp2p` is most commonly used.
    2.  **Downstream Developer Activity:** A horizontal bar chart ranks the dependent projects by their number of monthly active developers. This highlights the most active and potentially most significant projects in `libp2p`'s ecosystem.
    """
    )
    return


@app.cell
def _():
    PACKAGE = 'libp2p'
    SNAPSHOT_DATE = '2025-08-01'
    METRIC_NAME = 'GITHUB_active_developers_monthly'

    stringify = lambda arr: "'" + "','".join(arr) + "'"
    return METRIC_NAME, PACKAGE, SNAPSHOT_DATE, stringify


@app.cell
def _(PACKAGE, client):
    df_dependents = client.to_pandas(f"""
    SELECT
      p.project_id,
      p.display_name AS project_name,
      sbom.package_artifact_source,
      array_join(ARRAY_AGG(DISTINCT CONCAT(abp.artifact_namespace, '/', abp.artifact_name)), '; ') AS repo
    FROM sboms_v0 AS sbom
    JOIN artifacts_by_project_v1 AS abp
    ON
      abp.artifact_id = sbom.dependent_artifact_id
      AND abp.artifact_source = 'GITHUB'
      AND abp.project_source = 'OSS_DIRECTORY'
    JOIN projects_v1 AS p
      ON abp.project_id = p.project_id
    WHERE
      sbom.package_artifact_name = '{PACKAGE}'
      OR sbom.package_artifact_name LIKE 'github.com/{PACKAGE}%'
    GROUP BY 1, 2, 3
    """)
    return (df_dependents,)


@app.cell
def _(METRIC_NAME, SNAPSHOT_DATE, client, project_ids, stringify):
    df_developers = client.to_pandas(f"""
    SELECT
      p.project_id,
      p.display_name AS project_name,
      SUM(tm.amount) AS downstream_developers
    FROM timeseries_metrics_by_project_v0 AS tm
    JOIN metrics_v0 USING metric_id
    JOIN projects_v1 AS p 
      ON p.project_id = tm.project_id
    WHERE
      tm.project_id IN ({stringify(project_ids)})
      AND metric_name = '{METRIC_NAME}'
      AND sample_date = DATE('{SNAPSHOT_DATE}')
    GROUP BY 1,2
    ORDER BY 3 DESC
    """)
    return (df_developers,)


@app.cell
def _(df_dependents, df_developers):
    base = (
        df_developers[['project_id','project_name','downstream_developers']]
        .merge(
            df_dependents[['project_id','package_artifact_source','repo']],
            on='project_id',
            how='left'
        )
        .drop_duplicates()
    )
    repos_by_source = (
        base
        .dropna(subset=['package_artifact_source','repo'])
        .assign(repo=lambda d: d['repo'].astype(str).str.split(';'))
        .explode('repo')
        .assign(repo=lambda d: d['repo'].str.strip())
        .query("repo != ''")
        .groupby(['project_id','project_name','package_artifact_source'], as_index=False)['repo']
        .agg(lambda s: '; '.join(sorted(s.dropna().unique())))
    )
    rolled = (
        repos_by_source
        .assign(source_blob=lambda d: d['package_artifact_source'].astype(str)+': '+d['repo'])
        .groupby(['project_id','project_name'], as_index=False)['source_blob']
        .agg(lambda s: '. '.join(s))
        .rename(columns={'source_blob':'repos_by_source'})
    )
    df_consolidated = (
        base[['project_id','project_name','downstream_developers']]
        .groupby(['project_id','project_name'], as_index=False)['downstream_developers']
        .max()
        .merge(rolled, on=['project_id','project_name'], how='left')
        .sort_values('downstream_developers', ascending=False)
        [['project_id','project_name','downstream_developers','repos_by_source']]
        .drop(columns=['project_id'])
        .reset_index(drop=True)
    )

    df_consolidated
    return


@app.cell
def _(PACKAGE, df_dependents, px):
    source_counts = df_dependents['package_artifact_source'].value_counts().reset_index()
    source_counts.columns = ['package_artifact_source', 'project_count']
    project_ids = df_dependents['project_id'].unique()
    num_projects = len(project_ids)

    fig_pie = px.pie(
        source_counts,
        names='package_artifact_source',
        values='project_count',
        title=f'<b>{PACKAGE}</b> usage by package manager',
        color_discrete_sequence=px.colors.sequential.gray_r
    )
    fig_pie.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        marker=dict(line=dict(color='black', width=1))
    )
    fig_pie
    return (project_ids,)


@app.cell
def _(PACKAGE, df_developers, px):
    fig = px.bar(
        df_developers,
        y='project_name',
        x='downstream_developers',
        orientation='h',
        title=f'Active developers at projects with one or more dependencies on <b>{PACKAGE}</b>',
        labels={
            'project_name': 'Project',
            'downstream_developers': 'Number of Active Developers (Monthly)'
        },
        height=max(400, len(df_developers) * 20),
        text='downstream_developers',
        template='plotly_white'
    )
    fig.update_traces(marker_color='black', textposition='outside')
    fig.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig
    return


if __name__ == "__main__":
    app.run()
