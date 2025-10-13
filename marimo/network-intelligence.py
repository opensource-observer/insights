import marimo

__generated_with = "0.15.3"
app = marimo.App(width="full")


@app.cell
def about_app(mo):
    mo.vstack([
        mo.md("""
        # OSO Network Intelligence
        <small>Author: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2025-10-13</span></small>
        """),
        mo.md("""
        OSO maintains a large repository of open source projects called [oss-directory](https://github.com/opensource-observer/oss-directory). It's more than just an awesome list ... it's the starting point of the OSO data pipeline. We run indexers on every artifact linked to projects in the directory to produce metrics for our API and dashboards. We also use other project registries, including [OP Atlas](https://atlas.optimism.io/), [Crypto Ecosystems](https://github.com/electric-capital/crypto-ecosystems), [DefiLlama](https://github.com/DefiLlama/DefiLlama-Adapters), [OpenLabelsInitiative](https://github.com/openlabelsinitiative/OLI). This dashboard provides an overview of all the labeling we and our partners have done!

        """),
        mo.accordion({
            "<b>Click to see details on how app was made</b>": mo.accordion({
                "Methodology": """
                - Artifacts are categorized by source type (OSO, Software, Packages, Data Aggregators, Websites, Superchain, Other Blockchains)
                - Project counts and artifact counts are aggregated by source
                - Data is organized in a pivot table format for easy comparison
                - Coverage metrics show the breadth of OSO's data collection across different ecosystems
                ![img](https://docs.opensource.observer/assets/images/project-directory-7f628a5f09a6983c43ea4da6750b8b67.png)
                """,
                "Data Sources": """
                - [OSO Directory](https://github.com/opensource-observer/oss-directory) - Primary project registry
                - [OP Atlas](https://atlas.optimism.io/) - Optimism ecosystem projects
                - [Crypto Ecosystems](https://cryptoecosystems.com/) - Blockchain project registry
                - [DefiLlama](https://defillama.com/) - DeFi protocol data
                - [OpenLabelsInitiative](https://openlabels.org/) - Project labeling standards
                - Various package registries (NPM, PyPI, Go, NuGet, Rust, Gem)
                """,
                "Further Resources": """
                - [Getting Started with Pyoso](https://docs.opensource.observer/docs/get-started/python)
                - [Using the Semantic Layer](https://docs.opensource.observer/docs/get-started/using-semantic-layer)
                - [Marimo Documentation](https://docs.marimo.io/)
                """
            })
        })    
    ])
    return


@app.cell
def display_assets(display_graph, display_stats, display_table, mo):
    mo.vstack([
        display_stats,
        mo.md("""
        ### Project Registries -> Artifact Categories -> Artifact Types
        Click a parent node to explore its children
        """),
        display_graph,
        display_table
    ])
    return


@app.cell
def generate_stats(df, mo):
    total_projects = df['num_projects'].sum()
    total_artifacts = df['num_artifacts'].sum()
    unique_sources = df['artifact_source'].nunique()
    unique_project_sources = df['project_source'].nunique()

    total_projects_stat = mo.stat(
        label="Total Projects",
        bordered=True,
        value=f"{total_projects:,.0f}",
    )

    total_artifacts_stat = mo.stat(
        label="Total Artifacts",
        bordered=True,
        value=f"{total_artifacts:,.0f}",
    )

    unique_project_sources_stat = mo.stat(
        label="Project Sources",
        bordered=True,
        value=f"{unique_project_sources:,.0f}",
    )

    unique_sources_stat = mo.stat(
        label="Artifact Sources",
        bordered=True,
        value=f"{unique_sources:,.0f}",
    )

    display_stats = mo.hstack(
        [total_projects_stat, total_artifacts_stat, unique_project_sources_stat, unique_sources_stat],
        widths="equal",
        gap=1,
    )
    return (display_stats,)


@app.cell
def generate_graph(df, mo, np, px):
    def sunburst_graph(
        df,
        min_artifacts = 25,
        cmap = 'Viridis'
    ):
        """
        df columns required:
          - artifact_source_type
          - artifact_source
          - project_source
          - num_projects (int)
          - num_artifacts (int)
        """

        d = df.copy()        
        d.columns = [clean_name(c) for c in d.columns]

        d = d[d["Num Artifacts"] >= min_artifacts]
        d = d[~d['Artifact Source Type'].isin(['0. OSO', '4. Websites'])]
    
        for (col,dtype) in d.dtypes.items():
            if dtype == 'string':
                d[col] = d[col].apply(clean_name)
    
        d["Log Artifacts"] = np.log(d["Num Artifacts"].replace(0, np.nan)).fillna(0)

        fig = px.sunburst(
            d,
            path=["Project Source", "Artifact Source Type", "Artifact Source"],
            values="Num Projects",
            color="Log Artifacts",
            color_continuous_scale=cmap,
            branchvalues="total",
            hover_data={
                "Num Projects": ":,",
                "Num Artifacts": ":,",
                "Log Artifacts": False
            }
        )

        fig.update_traces(
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Projects: %{customdata[0]:,} (%{percentParent:.1%} of parent)<br>"
                "Artifacts: %{customdata[1]:,}<extra></extra>"
            ),
            textinfo="label+percent entry"
        )

        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(l=50,r=50,t=50,b=50),
            coloraxis_showscale=False,
            uniformtext=dict(minsize=10),
            title="",
            height=1000
        )

        return fig

    display_graph = mo.ui.plotly(sunburst_graph(df))
    return (display_graph,)


@app.cell
def generate_table(df, mo):
    _col_order = list(df.groupby('project_source')['num_artifacts'].sum().sort_values(ascending=False).index)
    _col_format = {clean_name(c):'{:,.0f}' for c in _col_order}

    _pivot_table = df.pivot_table(
        columns='project_source',
        index=['artifact_source_type', 'artifact_source'],
        values='num_artifacts',
        fill_value=0
    )[_col_order].reset_index()

    _pivot_table.columns = [clean_name(c) for c in _pivot_table.columns]

    display_table = mo.ui.table(
        _pivot_table,
        show_data_types=False,
        show_column_summaries=False,
        page_size=100,
        format_mapping=_col_format
    )
    return (display_table,)


@app.function
def clean_name(x):
    if len(x) < 3:
        return x
    if x[1] == '.':
        return x[3:]
    if x == 'OSS_DIRECTORY':
        return 'OSS Directory'
    if x == 'OP_ATLAS':
        return 'OP Atlas'
    if x == 'NPM':
        return 'NPM'
    if x == 'WWW':
        return 'www'
    if x == 'OPENLABELSINITIATIVE':
        return 'OpenLabelsInitiative'
    return x.replace('_', ' ').title()


@app.cell
def get_data(client):
    _query = f"""
    WITH artifacts AS (
        SELECT 
            project_source,
            artifact_source,
            APPROX_DISTINCT(project_id) AS num_projects,
            APPROX_DISTINCT(artifact_id) AS num_artifacts
        FROM artifacts_by_project_v1
        GROUP BY 1,2
    )
    SELECT
        artifact_source,
        CASE
            WHEN artifact_source = 'OSS_DIRECTORY' THEN '0. OSO'
            WHEN artifact_source = 'GITHUB' THEN '1. Software'
            WHEN artifact_source IN ('NPM', 'GO', 'PIP', 'NUGET', 'RUST', 'GEM', 'MAVEN') THEN '2. Packages'
            WHEN artifact_source IN ('DEFILLAMA') THEN '3. Data Aggregators'
            WHEN artifact_source IN ('WWW', 'TWITTER', 'FARCASTER') THEN '4. Websites'	
            WHEN chains.chain IS NOT NULL THEN '5. Superchain'
            ELSE '6. Other Blockchains'
        END AS artifact_source_type,
        project_source,
        num_projects,
        num_artifacts
    FROM artifacts
    LEFT JOIN int_superchain_chain_names AS chains
        ON artifacts.artifact_source = chains.chain
    ORDER BY 2,1,3
    """

    df = client.to_pandas(_query)
    return (df,)


@app.cell
def import_libraries():
    import numpy as np
    import pandas as pd
    import plotly.express as px
    return np, px


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import marimo as mo
    from pyoso import Client
    client = Client()
    pyoso_db_conn = client.dbapi_connection()    
    return client, mo


if __name__ == "__main__":
    app.run()