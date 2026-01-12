import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # PLN Downstream Impact Dashboard
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">Protocol Labs</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-12</span></small>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    _context = """
    - This dashboard tracks the downstream impact of Protocol Labs Network (PLN) packages
    - It identifies projects that depend on packages maintained by PLN organizations (libp2p, ipfs, filecoin, etc.)
    - Metrics include active developers working on downstream projects
    - Data is sourced from Software Bill of Materials (SBOM) analysis
    """

    _methodology = """
    **How it works:**

    1. **Package Discovery**: Queries the OSS Directory for packages owned by the selected organization
    2. **Dependency Mapping**: Uses SBOM data to find projects that list these packages as dependencies
    3. **Developer Activity**: Measures monthly active developers for each downstream project
    4. **Aggregation**: Summarizes impact across package managers and projects

    **Definitions:**
    - **Package Owner**: The GitHub organization that maintains the package (e.g., libp2p, ipfs)
    - **Downstream Project**: A project that depends on packages from the selected owner
    - **Active Developers**: Contributors with at least one commit, PR, or issue in the given month
    """

    _data_sources = """
    - [OSO Database](https://docs.oso.xyz/) - Open source project registry and metrics
    - [OSS Directory](https://github.com/opensource-observer/oss-directory) - Project registry with dependency information
    - [GitHub Archive](https://www.gharchive.org/) - Developer activity data
    """

    mo.accordion({
        "Context": _context,
        "Methodology": _methodology,
        "Data Sources": _data_sources
    })
    return


@app.cell(hide_code=True)
def _(df_kpis, mo, ref_month):
    if not df_kpis.empty:
        _total_packages = df_kpis['total_packages'].iloc[0] if 'total_packages' in df_kpis.columns else 0
        _dependent_projects = df_kpis['dependent_projects'].iloc[0] if 'dependent_projects' in df_kpis.columns else 0
        _downstream_devs = df_kpis['downstream_developers'].iloc[0] if 'downstream_developers' in df_kpis.columns else 0
        _package_sources = df_kpis['package_sources'].iloc[0] if 'package_sources' in df_kpis.columns else 0
    else:
        _total_packages = 0
        _dependent_projects = 0
        _downstream_devs = 0
        _package_sources = 0

    # Format reference month for display
    _ref_display = ref_month[:7]  # "2024-11" format

    mo.hstack(
        [
            mo.stat(
                label="Packages",
                value=f"{_total_packages:,.0f}",
                caption="Maintained by owner",
                bordered=True
            ),
            mo.stat(
                label="Dependent Projects",
                value=f"{_dependent_projects:,.0f}",
                caption="Using these packages",
                bordered=True
            ),
            mo.stat(
                label="Downstream Developers",
                value=f"{_downstream_devs:,.0f}",
                caption=f"Active in {_ref_display}",
                bordered=True
            ),
            mo.stat(
                label="Package Managers",
                value=f"{_package_sources:,.0f}",
                caption="Distribution channels",
                bordered=True
            ),
        ],
        widths="equal",
        gap=2
    )
    return


@app.cell(hide_code=True)
def _(mo):
    # PLN-focused package owners
    # Dict format is {label: value} - labels are display names, values are database values
    package_owner_dropdown = mo.ui.dropdown(
        options={
            'libp2p': 'libp2p',
            'IPFS': 'ipfs',
            'Filecoin': 'filecoin',
            'Protocol Labs': 'protocol',
            'Multiformats': 'multiformats',
            'IPLD': 'ipld',
            'Ceramic': 'ceramic-network',
        },
        value='libp2p',
        label='Package Owner:'
    )

    project_registry = mo.ui.dropdown(
        options=['OSS_DIRECTORY', 'CRYPTO_ECOSYSTEMS'],
        value='OSS_DIRECTORY',
        label='Project Registry:'
    )

    mo.hstack(
        [package_owner_dropdown, project_registry],
        justify="start",
        gap=2
    )
    return package_owner_dropdown, project_registry


@app.cell(hide_code=True)
def _(by_package_manager_tab, mo, overview_tab, top_projects_tab):
    mo.ui.tabs({
        "Overview": overview_tab,
        "By Package Manager": by_package_manager_tab,
        "Top Projects": top_projects_tab
    })
    return


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_dependents, mo, package_owner_dropdown, px):
    # Package manager distribution chart - shown in "By Package Manager" tab
    if not df_dependents.empty:
        _source_counts = df_dependents['package_artifact_source'].value_counts().reset_index()
        _source_counts.columns = ['Package Manager', 'Project Count']

        _fig = px.bar(
            _source_counts,
            x='Project Count',
            y='Package Manager',
            orientation='h',
            text='Project Count',
            labels={'Package Manager': 'Package Manager', 'Project Count': 'Number of Projects'}
        )
        _fig.update_traces(textposition='outside', marker_color='#4C78A8')
        _fig.update_layout(**PLOTLY_LAYOUT)
        _fig.update_layout(yaxis=dict(categoryorder='total ascending'))

        _chart = mo.ui.plotly(_fig, config={'displayModeBar': False})
    else:
        _chart = mo.md("*No dependency data found for this package owner*")

    by_package_manager_tab = mo.vstack([
        mo.md(f"### Package Manager Distribution for {package_owner_dropdown.value}"),
        mo.md("Shows how downstream projects consume packages across different package managers."),
        _chart
    ])
    return (by_package_manager_tab,)


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_developers, mo, package_owner_dropdown, pd, px):
    # Developer activity histogram with intelligent binning
    def create_bins(df):
        if df.empty or 'downstream_developers' not in df.columns:
            return pd.DataFrame(columns=['bin_range', 'count'])

        def assign_bin(dev_count):
            if dev_count == 1:
                return "1"
            elif dev_count <= 3:
                return "2-3"
            elif dev_count <= 5:
                return "4-5"
            elif dev_count <= 10:
                return "6-10"
            elif dev_count <= 20:
                return "11-20"
            elif dev_count <= 40:
                return "21-40"
            else:
                return "40+"

        df_binned = df.copy()
        df_binned['bin_range'] = df_binned['downstream_developers'].apply(assign_bin)

        bin_counts = df_binned['bin_range'].value_counts().reset_index()
        bin_counts.columns = ['bin_range', 'count']

        bin_order = ["1", "2-3", "4-5", "6-10", "11-20", "21-40", "40+"]
        bin_counts['bin_range'] = pd.Categorical(bin_counts['bin_range'], categories=bin_order, ordered=True)
        bin_counts = bin_counts.sort_values('bin_range')

        return bin_counts

    if not df_developers.empty:
        _bin_data = create_bins(df_developers)

        _fig = px.bar(
            _bin_data,
            x='bin_range',
            y='count',
            text='count',
            labels={'bin_range': 'Monthly Active Developers', 'count': 'Number of Projects'}
        )
        _fig.update_traces(textposition='outside', marker_color='#41AB5D')
        _fig.update_layout(**PLOTLY_LAYOUT)

        _chart = mo.ui.plotly(_fig, config={'displayModeBar': False})
    else:
        _chart = mo.md("*No developer data available*")

    overview_tab = mo.vstack([
        mo.md(f"### Developer Activity Distribution for {package_owner_dropdown.value} Dependents"),
        mo.md("Distribution of projects by their monthly active developer count."),
        _chart
    ])
    return (overview_tab,)


@app.cell(hide_code=True)
def _(df_consolidated, mo, package_owner_dropdown):
    if not df_consolidated.empty:
        _display_df = df_consolidated.head(20).copy()

        _table = mo.ui.table(
            _display_df.reset_index(drop=True),
            format_mapping={
                'downstream_developers': '{:,.0f}'
            },
            show_column_summaries=False,
            show_data_types=False,
            page_size=20,
            freeze_columns_left=['project_name']
        )
    else:
        _table = mo.md("*No projects found*")

    top_projects_tab = mo.vstack([
        mo.md(f"### Top Downstream Projects Using {package_owner_dropdown.value}"),
        mo.md("Projects ranked by monthly active developer count."),
        _table
    ])
    return (top_projects_tab,)


@app.cell
def _(mo, package_owner_dropdown, pd, pyoso_db_conn):
    # Reference month: 2 months before current date
    ref_month = (pd.Timestamp.now() - pd.DateOffset(months=2)).strftime('%Y-%m-01')

    # Get packages for the selected owner
    df_packages = mo.sql(
        f"""
        SELECT DISTINCT
          package_artifact_id,
          package_artifact_source,
          package_artifact_namespace,
          package_artifact_name
        FROM package_owners_v0
        WHERE package_owner_artifact_namespace = LOWER('{package_owner_dropdown.value}')
        """,
        engine=pyoso_db_conn,
        output=False
    )
    return df_packages, ref_month


@app.cell
def _(df_packages, mo, pd, project_registry, pyoso_db_conn, stringify):
    # Get dependent projects from SBOM data
    if not df_packages.empty:
        _package_ids = df_packages['package_artifact_id'].unique()

        df_dependents = mo.sql(
            f"""
            SELECT
              p.project_id,
              p.display_name AS project_name,
              sbom.package_artifact_source,
              ARRAY_JOIN(ARRAY_AGG(DISTINCT CONCAT(abp.artifact_namespace, '/', abp.artifact_name)), '; ') AS repos
            FROM sboms_v0 AS sbom
            JOIN artifacts_by_project_v1 AS abp
              ON abp.artifact_id = sbom.dependent_artifact_id
              AND abp.artifact_source = 'GITHUB'
              AND abp.project_source = '{project_registry.value}'
              AND abp.project_namespace IN ('oso', 'eco')
            JOIN projects_v1 AS p
              ON abp.project_id = p.project_id
            WHERE sbom.package_artifact_id IN ({stringify(_package_ids)})
            GROUP BY 1, 2, 3
            """,
            engine=pyoso_db_conn,
            output=False
        )
    else:
        df_dependents = pd.DataFrame(columns=['project_id', 'project_name', 'package_artifact_source', 'repos'])
    return (df_dependents,)


@app.cell
def _(df_dependents, mo, pd, pyoso_db_conn, ref_month, stringify):
    # Get developer metrics for dependent projects
    # Using metric_model = 'contributors' only
    # which matches the pattern in other notebooks
    if not df_dependents.empty:
        _project_ids = df_dependents['project_id'].unique()

        df_developers = mo.sql(
            f"""
            SELECT
              p.project_id,
              p.display_name AS project_name,
              SUM(ts.amount) AS downstream_developers
            FROM timeseries_metrics_by_project_v0 ts
            JOIN metrics_v0 m ON ts.metric_id = m.metric_id
            JOIN projects_v1 p ON ts.project_id = p.project_id
            WHERE
              ts.project_id IN ({stringify(_project_ids)})
              AND m.metric_model = 'contributors'
              AND m.metric_time_aggregation = 'monthly'
              AND ts.sample_date = DATE('{ref_month}')
            GROUP BY 1, 2
            ORDER BY 3 DESC
            """,
            engine=pyoso_db_conn,
            output=False
        )
    else:
        df_developers = pd.DataFrame(columns=['project_id', 'project_name', 'downstream_developers'])
    return (df_developers,)


@app.cell
def _(df_dependents, df_developers, pd):
    # Consolidate data for table display
    if not df_dependents.empty and not df_developers.empty:
        _base = (
            df_developers[['project_id', 'project_name', 'downstream_developers']]
            .merge(
                df_dependents[['project_id', 'package_artifact_source', 'repos']],
                on='project_id',
                how='left'
            )
            .drop_duplicates()
        )

        # Aggregate repos by source
        _repos_by_source = (
            _base
            .dropna(subset=['package_artifact_source', 'repos'])
            .assign(repo=lambda d: d['repos'].astype(str).str.split(';'))
            .explode('repo')
            .assign(repo=lambda d: d['repo'].str.strip())
            .query("repo != ''")
            .groupby(['project_id', 'project_name', 'package_artifact_source'], as_index=False)['repo']
            .agg(lambda s: '; '.join(sorted(s.dropna().unique())))
        )

        _rolled = (
            _repos_by_source
            .assign(source_blob=lambda d: d['package_artifact_source'].astype(str) + ': ' + d['repo'])
            .groupby(['project_id', 'project_name'], as_index=False)['source_blob']
            .agg(lambda s: '. '.join(s))
            .rename(columns={'source_blob': 'repos_by_source'})
        )

        df_consolidated = (
            _base[['project_id', 'project_name', 'downstream_developers']]
            .groupby(['project_id', 'project_name'], as_index=False)['downstream_developers']
            .max()
            .merge(_rolled, on=['project_id', 'project_name'], how='left')
            .sort_values('downstream_developers', ascending=False)
            [['project_name', 'downstream_developers', 'repos_by_source']]
            .reset_index(drop=True)
        )
    else:
        df_consolidated = pd.DataFrame(columns=['project_name', 'downstream_developers', 'repos_by_source'])
    return (df_consolidated,)


@app.cell
def _(df_dependents, df_developers, df_packages, pd):
    # Calculate KPIs
    _total_packages = len(df_packages) if not df_packages.empty else 0
    _dependent_projects = df_dependents['project_id'].nunique() if not df_dependents.empty else 0
    _downstream_devs = df_developers['downstream_developers'].sum() if not df_developers.empty else 0
    _package_sources = df_dependents['package_artifact_source'].nunique() if not df_dependents.empty else 0

    df_kpis = pd.DataFrame({
        'total_packages': [_total_packages],
        'dependent_projects': [_dependent_projects],
        'downstream_developers': [_downstream_devs],
        'package_sources': [_package_sources]
    })
    return (df_kpis,)


@app.cell(hide_code=True)
def _():
    stringify = lambda arr: "'" + "','".join([str(x) for x in arr]) + "'"
    return (stringify,)


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
            ticks="outside"
        ),
        yaxis=dict(
            title="",
            showgrid=True, gridcolor="#DDD",
            zeroline=True, zerolinecolor="black", zerolinewidth=1,
            linecolor="#000", linewidth=1,
            ticks="outside"
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
