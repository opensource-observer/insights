import marimo

__generated_with = "0.16.2"
app = marimo.App(width="full")


@app.cell
def about_app(mo):
    mo.vstack([
        mo.md("""
        # Eigen Developer Ecosystem
        <small>Author: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2025-10-21</span></small>
        """)
    ])
    return


@app.cell
def configuration_settings(datetime, timedelta):
    # Configuration constants
    COHORT_START_DATE = '2025-03-01'
    PROJECT_START_DATE = '2023-07-01'

    # Calculate ecosystem start date dynamically (3 years ago)
    ECOSYSTEM_START_DATE_YEARS = 3
    ECOSYSTEM_START_DATE = (datetime.now() - timedelta(days=365*ECOSYSTEM_START_DATE_YEARS)).strftime('%Y-%m-%d')

    # Display settings
    DISPLAY_MONTHS = 6

    # Set to None to disable collection-based features
    COLLECTION_NAME = None

    # Owner namespace for developer funnel analysis
    OWNER_ARTIFACT_NAMESPACE = 'layr-labs'

    ECOSYSTEM_NAME = 'EigenLayer'
    PACKAGES_TO_MONITOR=[
        ("layr-labs", "eigensdk-go", "github.com/layr-labs/eigensdk-go"), 
        ("layr-labs", "eigensdk-rs", "eigensdk"),
    ]

    SDK_PROJECT_MAINTAINERS = ['layr-labs']

    EVM_ECOSYSTEMS = [
        'eigenlayer',
        'arbitrum',
        'base',
        'bnb_chain',
        'evm_toolkit',
        'ethereum',
        'ethereum_l2s',
        'ethereum_virtual_machine_stack',
        'foundry',
        'polygon',
        'solidity',
    ]
    OTHER_ECOSYSTEMS = [
        'bitcoin',
        'filecoin',
        'solana',
        'aptos'
    ]
    ECOSYSTEMS = EVM_ECOSYSTEMS + OTHER_ECOSYSTEMS
    MONTHLY_METRICS = [
        'GITHUB_active_developers_monthly',
        'GITHUB_full_time_developers_monthly',
        'GITHUB_commits_monthly',    
        'GITHUB_releases_monthly',
        'GITHUB_forks_monthly',
        'GITHUB_stars_monthly',
        'GITHUB_opened_pull_requests_monthly',    
        'GITHUB_merged_pull_requests_monthly',
        'GITHUB_opened_issues_monthly',
        'GITHUB_closed_issues_monthly',
        'GITHUB_project_velocity_monthly',
        'GITHUB_bot_activity_monthly',
    ]
    WEEKLY_METRICS = [
        'GITHUB_commits_weekly',    
        'GITHUB_forks_weekly',
        'GITHUB_stars_weekly',
        'GITHUB_opened_pull_requests_weekly',    
        'GITHUB_merged_pull_requests_weekly',
        'GITHUB_opened_issues_weekly',
        'GITHUB_closed_issues_weekly',
        'GITHUB_project_velocity_weekly',
        'GITHUB_contributors_weekly'
    ]
    DAILY_METRICS = [
        'GITHUB_project_velocity_daily'
    ]
    METRIC_NAMES = MONTHLY_METRICS + WEEKLY_METRICS + DAILY_METRICS
    return (
        COHORT_START_DATE,
        COLLECTION_NAME,
        DISPLAY_MONTHS,
        ECOSYSTEMS,
        ECOSYSTEM_NAME,
        ECOSYSTEM_START_DATE,
        EVM_ECOSYSTEMS,
        METRIC_NAMES,
        MONTHLY_METRICS,
        OTHER_ECOSYSTEMS,
        OWNER_ARTIFACT_NAMESPACE,
        PACKAGES_TO_MONITOR,
        PROJECT_START_DATE,
        SDK_PROJECT_MAINTAINERS,
    )


@app.cell
def create_overview_tab(dev_funnel_stats, ecosystem_stats, mo, sdk_stats):
    _intro = mo.vstack([
        mo.md("## Overview"),
        mo.Html("""
        Eigen Network ...
        """),
    ])

    # Build stats list conditionally
    _stats_items = [mo.md("### Selected Metrics")]

    if sdk_stats is not None:
        _stats_items.extend([
            mo.md("#### Eigen SDK Usage"),
            sdk_stats,
        ])

    _stats_items.extend([
        mo.md("#### Ecosystem Benchmarks"),
        ecosystem_stats,
    ])

    if dev_funnel_stats is not None:
        _stats_items.extend([
            mo.md("#### Eigen Developer Funnel"),
            dev_funnel_stats,
        ])

    _stats = mo.vstack(_stats_items)

    _resources = mo.vstack([
        mo.md("### Further Resources"),
        mo.accordion({
            "Data": """
            - [OSO API](https://docs.opensource.observer/docs/get-started/python) - GitHub metrics and developer activity data
            - [Electric Capital Crypto Ecosystems](https://github.com/electric-capital/crypto-ecosystems) - Ecosystem repository data
            - [Open Source Insights (aka deps.dev)](https://deps.dev) - SDK usage and adoption metrics
            - [GH Archive](https://www.gharchive.org/) - a public archive of historical events to GitHub
            """,
            "Docs": """
            - [Project Velocity Definition](https://chaoss.community/kb/metric-project-velocity/) - We use the CHAOSS metric for "velocity"
            - [Getting Started with Pyoso](https://docs.opensource.observer/docs/get-started/python) - Run your own queries
            - [Marimo Documentation](https://docs.marimo.io/) - Make your own dashboard on OSO
            """,
            "Caveats": """
            - We can only see developer activity on *public* GitHub repos. We are not able to identify teams using Eigen's SDK in private repos.
            - We don't have visibility into the very top of the developer funnel. For instance, we are unable to capture how many developers
              have read the docs or browsed the use case examples.
            - We rely on Electric Capital's Crypto Ecosystems registry for comparing Arbitrum to other ecosystems. The registry is
              community-maintained and not always accurate / up-to-date for new projects.
            - We are not yet linking developer activity to onchain activity. We currently do not have a robust way of distinguishing
              between developers who are tinkering on personal projects and ones who are using Eigen's SDK in a high-value application.
            """
        }, multiple=True)
    ])    

    overview_tab = mo.vstack([
        _intro,
        _stats,
        _resources
    ])
    return (overview_tab,)


@app.cell
def create_sdk_usage_tab(
    COHORT_START_DATE,
    DISPLAY_MONTHS,
    cohort_velocity_change,
    df_sdk_deps,
    df_sdk_deps_project_metrics,
    make_joyplot,
    mo,
    summarize_monthly_metrics,
):
    # Only create tab if we have SDK dependency data
    if df_sdk_deps.empty or df_sdk_deps_project_metrics.empty:
        sdk_stats = None
        sdk_tab = None
    else:
        _df = df_sdk_deps_project_metrics[df_sdk_deps_project_metrics['metric_name'] == 'GITHUB_project_velocity_daily']
        _mm = summarize_monthly_metrics(df_sdk_deps_project_metrics, num_months=DISPLAY_MONTHS)

        _df_dep_repos = df_sdk_deps.copy()
        _df_dep_repos['Project Name'] = _df_dep_repos['dependent_project_name'].map(
            _df
            .drop_duplicates(subset=['display_name', 'project_name'])
            .set_index('project_name')['display_name']
            .to_dict()       
        )
        _df_dep_repos['Dependent Repo URL'] = _df_dep_repos.apply(lambda x: f"https://github.com/{x['repo_owner']}/{x['repo_name']}", axis=1)
        _ossd_base_url = 'https://github.com/opensource-observer/oss-directory/tree/main/data/projects'
        _df_dep_repos['OSS Directory URL'] = _df_dep_repos['dependent_project_name'].apply(lambda x: f"{_ossd_base_url}/{x[0]}/{x}.yaml")
        _df_dep_repos.drop(columns=['dependent_project_name', 'repo_owner', 'repo_name', 'artifact_id'], inplace=True)

        # Calculate SDK usage stats
        _total_dependents = len(_df_dep_repos)
        _active_devs = _mm['Active Developers'].sum()
        _change_in_velocity = cohort_velocity_change(
            df=df_sdk_deps_project_metrics,
            metric_name="GITHUB_project_velocity_weekly",
            cohort_start=COHORT_START_DATE
        )

        sdk_stats = mo.hstack(
            items=[
                mo.stat(
                    label="Eigen SDK Dependents",
                    bordered=True,
                    value=f"{_total_dependents:,.0f}",
                    caption="Linked to (known) teams with public GitHub activity"
                ),
                mo.stat(
                    label="Active Developers using Eigen SDK",
                    bordered=True,
                    value=f"{_active_devs:,.0f}",
                    caption=f"All dependent teams, averaged over last {DISPLAY_MONTHS} months"
                ),
                mo.stat(
                    label="Change in Velocity",
                    bordered=True,
                    value=f"{_change_in_velocity*100:.1f}%",
                    caption=f"All dependent teams, before/after {COHORT_START_DATE}"
                )
            ],
            widths="equal",
            gap=1
        )

        sdk_tab = mo.vstack([
            mo.md("## Eigen SDK Usage"),
            mo.Html("""
            This tab tracks (public) development activity of teams with repos that import the Eigen SDK as a direct dependency. 
            """),

            sdk_stats,

            mo.callout("""Note: We rely on the GitHub API for tracing a project's SBOM (software bill of materials).
            We only fetch SBOMs for projects registered on OSO, which is a curated subset of all GitHub repos. New projects are
            being added continuously. We try to fetch the current state of each project's SBOM on a monthly basis.
            """, kind="warn"),

            mo.md("### Developer Velocity"),
            mo.Html(f"""
            The chart shows normalized velocity patterns for projects using the Eigen SDK over the last {DISPLAY_MONTHS} months. 
            The percentage indicates velocity change before and after the cohort start date.
            """),
            mo.ui.plotly(
                figure=make_joyplot(df=_df, smoothing=7, display_months=DISPLAY_MONTHS),
                config={'displayModeBar': False}
            ),

            mo.md(f"### Activities Over Last {DISPLAY_MONTHS} Months"),
            mo.Html(f"""
            Monthly averages across key development metrics. Active developers and velocity are particularly important indicators of project health.
            """),
            mo.ui.table(
                data=_mm,
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                page_size=25,
                format_mapping={c: '{:,.0f}' for c in _mm.columns if c != 'Project'},
                freeze_columns_left=['Project']
            ),

            mo.md("### Registry of (Known) Projects"),
            mo.Html("""
            This registry lists projects with identified dependencies on the Eigen SDK. Projects must be registered in the OSO directory to appear here.
            """),
            mo.ui.table(
                data=_df_dep_repos.reset_index(drop=True),
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                page_size=50
            ),

        ])   
    return sdk_stats, sdk_tab


@app.cell
def create_ecosystem_tab(
    COHORT_START_DATE,
    DISPLAY_MONTHS,
    ECOSYSTEM_NAME,
    cohort_velocity_change,
    df_ecosystem_metrics,
    df_repo_overlap,
    get_total_repos_in_crypto_ecosystems,
    make_joyplot,
    make_repo_overlap_barchart,
    mo,
    summarize_monthly_metrics,
):
    _df = df_ecosystem_metrics[df_ecosystem_metrics['metric_name'] == 'GITHUB_project_velocity_daily']
    _mm = summarize_monthly_metrics(df_ecosystem_metrics, num_months=DISPLAY_MONTHS)

    # Calculate ecosystem stats
    _total_repos = get_total_repos_in_crypto_ecosystems()

    _eco_repos = df_repo_overlap[df_repo_overlap['ecosystem_name'] == ECOSYSTEM_NAME]['total_repos'].sum()
    _active_devs = _mm[_mm['Project'] == ECOSYSTEM_NAME]['Active Developers'].sum()
    _change_in_velocity = cohort_velocity_change(
        df=df_ecosystem_metrics,
        metric_name="GITHUB_project_velocity_weekly",
        cohort_start=COHORT_START_DATE
    )


    ecosystem_stats = mo.hstack(
        items=[
            mo.stat(
                label="All Repositories",
                bordered=True,
                value=f"{_total_repos:,.0f}",
                caption="Repos included in the latest Electric Capital registry"
            ),
            mo.stat(
                label=f"{ECOSYSTEM_NAME} Repositories",
                bordered=True,
                value=f"{_eco_repos:,.0f}",
                caption="Repos included in the latest Electric Capital registry"
            ),
            mo.stat(
                label=f"Active Developers in {ECOSYSTEM_NAME} Ecosystem",
                bordered=True,
                value=f"{_active_devs:,.0f}",
                caption=f"All '{ECOSYSTEM_NAME}' repos, averaged over last {DISPLAY_MONTHS} months"
            ),
            mo.stat(
                label="Change in Velocity",
                bordered=True,
                value=f"{_change_in_velocity*100:.1f}%",
                caption=f"All '{ECOSYSTEM_NAME}' repos, before/after {COHORT_START_DATE}"
            )
        ],
        widths="equal",
        gap=1
    )

    ecosystem_tab = mo.vstack([
        mo.md("## Ecosystem Benchmarks"),
        mo.Html(f"""
        This tab tracks (public) development activity on {ECOSYSTEM_NAME} compared to other crypto ecosystems registered by Electric Capital.
        """),

        ecosystem_stats,

        mo.callout("""
        Note: Electric Capital's Crypto Ecosystems registry is community-maintained and not always accurate / up-to-date for
        new projects. There is also significant overlap between ecosystems, ie, the same repository belongs to multiple ecosystems.
        New repositories can be added by making a pull request to the Crypto Ecosystems GitHub.
         """, kind="warn"),


        mo.md("### Developer Velocity"),
        mo.Html(f"""
        Comparing velocity trends across major crypto ecosystems over the last {DISPLAY_MONTHS*3} months. 
        Ecosystems are ranked by recent activity levels.
        """),
        mo.ui.plotly(
            figure=make_joyplot(df=_df, smoothing=7, display_months=DISPLAY_MONTHS*3),
            config={'displayModeBar': False}
        ),

        mo.md(f"### Activities Over Last {DISPLAY_MONTHS} Months"),
        mo.Html("""
        Monthly development metrics averaged across ecosystems. Use these benchmarks to understand relative ecosystem health and activity.
        """),
        mo.ui.table(
            data=_mm,
            selection=None,
            show_column_summaries=False,
            show_data_types=False,
            page_size=20,
            format_mapping={c: '{:,.0f}' for c in _mm.columns if c != 'Project'},
            freeze_columns_left=['Project']
        ),

        mo.md("### Repository Overlap"),
        mo.Html(f"""
        Shows how many repositories are shared between {ECOSYSTEM_NAME} and other ecosystems. 
        High overlap indicates common tooling and multi-chain development.
        """),
        mo.ui.plotly(
            figure=make_repo_overlap_barchart(
                df=df_repo_overlap,
                target_ecosystem=ECOSYSTEM_NAME
            ),
            config={'displayModeBar': False}
        ),

    ])   
    return ecosystem_stats, ecosystem_tab


@app.cell
def create_developer_funnel_tab(
    df_fork_devs,
    df_fork_devs_labeled,
    df_fork_devs_ranked,
    mo,
    px,
):
    # Only create tab if we have fork data
    if df_fork_devs.empty or df_fork_devs_labeled.empty or df_fork_devs_ranked.empty:
        dev_funnel_stats = None
        dev_funnel_tab = None
    else:
        # 1. Table of example repos and fork count
        _forks_table = df_fork_devs_labeled.groupby('first_fork_repo_url')['dev_id'].nunique().sort_values(ascending=False)
        _forks_table = _forks_table.reset_index()
        _forks_table.columns = ['Repo URL', 'Num. Developers']

        # 2. Area chart of cumulative forks
        _df_fork_count = df_fork_devs.groupby(['first_fork_repo_url', 'first_fork'], as_index=False)['dev_id'].nunique() 
        _df_fork_count.sort_values(by='first_fork', inplace=True)
        _df_fork_count['Fork Count (Cumulative)'] = _df_fork_count['dev_id'].cumsum()

        _forks_barchart = px.area(data_frame=_df_fork_count, x='first_fork', y='Fork Count (Cumulative)')
        _forks_barchart.update_traces(line=dict(color='#104C35', width=1.5), fillcolor=rgba_from_rgb(rgb='rgb(8, 135, 43)', alpha=0.80))
        _layout = dict(
            plot_bgcolor='white',
            paper_bgcolor='white',
            title_x=0,
            legend_title="",
            autosize=True,
            margin=dict(t=0, l=0, r=0, b=0),
            height=300,
            yaxis=dict(showgrid=True, gridcolor='lightgray', linecolor='black', linewidth=1, ticks='outside', rangemode='tozero', title=''),
            xaxis=dict(showgrid=False, linecolor='black', linewidth=1, ticks='outside', title=''),
        )
        _forks_barchart.update_layout(**_layout)

        # 3. Developer funnel, PageRanked
        df_devs_by_project = (
            df_fork_devs_labeled.merge(df_fork_devs_ranked[['dev_id', 'dev_score']], on='dev_id')
            .groupby(['dev_id', 'dev_url', 'dev_score'], as_index=False)
            .agg(
                first_fork=('first_fork','min'),    
                num_repos=('repo_url', 'nunique'),
                alignment=('project_type', lambda x: min(set(x))[3:]),
                #repos_worked_on_by_this_dev=('repo_url', lambda x: ' | '.join(sorted(set(x))))
            )
            .sort_values(by=['dev_score', 'num_repos', 'first_fork'], ascending=[False, False, True])
            .reset_index(drop=True)
            .drop(columns=['dev_id', 'dev_score'])    
            .rename(columns={
                'dev_url': 'Git Username',
                'first_fork': 'Earliest Fork',
                'num_repos': 'Num OSS Repos',
                'alignment': 'Contribution Type to Look For'
            })
        )

        # 4. Projects worked on by developers in the funnel
        df_projects_from_devs = (
            df_fork_devs_labeled.merge(df_fork_devs_ranked[['dev_id', 'dev_score']], on='dev_id')
            .groupby('repo_owner', as_index=False)
            .agg(
                repo_rank=('dev_score', 'sum'),
                alignment=('project_type', lambda x: min(set(x))[3:]),
                first_fork=('first_fork','min'),    
                num_devs=('dev_id', 'nunique'),
                dev_names=('dev_url', lambda x: ', '.join(sorted(set(x))).replace('https://github.com/',''))
            )
            .sort_values(by=['repo_rank', 'num_devs', 'first_fork'], ascending=[False, False, True])
            .query("repo_owner not in @SDK_PROJECT_MAINTAINERS")
            .drop(columns=['repo_rank'])
            .reset_index(drop=True)
        )
        df_projects_from_devs['repo_owner'] = df_projects_from_devs['repo_owner'].apply(lambda x: f'https://github.com/{x}')
        df_projects_from_devs.rename(columns={
            'repo_owner': 'GitHub Owner', 'first_fork': 'Earliest Fork', 'num_devs': 'Num Developers', 'dev_names': 'Git Username(s)', 'alignment': 'Alignment'
        }, inplace=True)


        # Calculate developer funnel stats
        _example_repos = len(_forks_table)
        _unique_developers = len(df_devs_by_project)
        _total_projects = len(df_projects_from_devs)
        _avg_forks_per_month = _unique_developers / ((df_fork_devs['first_fork'].max() - df_fork_devs['first_fork'].min()).days / 30)

        dev_funnel_stats = mo.hstack(
            items=[
                mo.stat(
                    label="Eigen Example Repos",
                    bordered=True,
                    value=f"{_example_repos:,.0f}",
                    #caption="Git users who forked Stylus examples"
                ),
                mo.stat(
                    label="Forking Developers",
                    bordered=True,
                    value=f"{_unique_developers:,.0f}",
                    #caption="Git users who forked Stylus examples"
                ),
                mo.stat(
                    label="Projects Linked to Forking Developers",
                    bordered=True,
                    value=f"{_total_projects:,.0f}",
                    #caption="Public GitHub repos with recent commits from developers identified"
                ),
                mo.stat(
                    label="Avg Forks/Month",
                    bordered=True,
                    value=f"{_avg_forks_per_month:.1f}",
                    #caption="Average developers per project"
                )
            ],
            widths="equal",
            gap=1
        )

        dev_funnel_tab = mo.vstack([
            mo.md("## Eigen Developer Funnel"),
            mo.Html(
            """
            This tab tracks when developers engage with Eigen by forking the example repositories created by Offchain Labs.
            It also applies a basic ranking algorithm to identify developers and projects worth watching.
            """),

            dev_funnel_stats,
            mo.hstack([
                mo.vstack([
                    mo.md("### Forks by Example Repo"),
                    mo.ui.table(
                        data=_forks_table,
                        show_column_summaries=False,
                        show_data_types=False,
                    )
                ]),
                mo.vstack([
                    mo.md("### Forking Developers"),
                    mo.ui.plotly(figure=_forks_barchart, config={'displayModeBar': False})
                ])
            ], widths='equal', wrap=True),

            mo.md("### Developers Identified"),
            mo.Html("""
            Developers ranked using PageRank algorithm based on their contributions and the popularity of repos they work on. 
            Higher-ranked developers are more likely to be influential contributors.
            """),
            mo.ui.table(
                data=df_devs_by_project[['Git Username', 'Num OSS Repos', 'Contribution Type to Look For', 'Earliest Fork']],
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                page_size=20
            ),

            mo.md("### Projects Linked to Forking Developers"),
            mo.Html("""
            Projects where forking developers are actively contributing. Alignment indicates ecosystem affiliation (EVM, non-EVM, etc).
            """),
            mo.ui.table(
                data=df_projects_from_devs[['GitHub Owner', 'Git Username(s)', 'Num Developers', 'Alignment', 'Earliest Fork']],
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                page_size=20
            ),

        ])
    return dev_funnel_stats, dev_funnel_tab


@app.cell
def display_tabs(dev_funnel_tab, ecosystem_tab, mo, overview_tab, sdk_tab):
    # Build tabs dictionary dynamically based on available data
    tabs_dict = {"Overview": overview_tab}

    if sdk_tab is not None:
        tabs_dict["Eigen SDK Usage"] = sdk_tab

    tabs_dict["Ecosystem Benchmarks"] = ecosystem_tab

    if dev_funnel_tab is not None:
        tabs_dict["Eigen Developer Funnel"] = dev_funnel_tab

    mo.ui.tabs(tabs_dict, value="Overview")
    return


@app.cell
def get_data(
    COLLECTION_NAME,
    ECOSYSTEMS,
    ECOSYSTEM_START_DATE,
    EVM_ECOSYSTEMS,
    METRIC_NAMES,
    OTHER_ECOSYSTEMS,
    PROJECT_START_DATE,
    SDK_PROJECT_MAINTAINERS,
    client,
    pd,
    wraps,
):
    # QUERY HELPERS
    def parse_dates(*cols):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                df = func(*args, **kwargs)
                for col in cols:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col]).dt.date
                return df
            return wrapper
        return decorator

    stringify = lambda arr: "'" + "','".join(arr) + "'"

    # QUERIES
    @parse_dates("date")
    def get_metrics_by_developer_ecosystem():
        return client.to_pandas(f"""
            SELECT
              sample_date AS date,
              metric_name,
              projects_v1.display_name,
              amount
            FROM timeseries_metrics_by_project_v0
            JOIN metrics_v0 USING metric_id
            JOIN projects_v1 USING project_id
            WHERE
              sample_date >= DATE '{ECOSYSTEM_START_DATE}'
              AND metric_name IN ({stringify(METRIC_NAMES)})
              AND project_source = 'CRYPTO_ECOSYSTEMS'
              AND project_namespace = 'eco'
              AND project_name IN ({stringify(ECOSYSTEMS)})          
            ORDER BY 1,2,3  
            """)

    @parse_dates("date")
    def get_metrics_by_collection_project():
        """Get metrics for projects in a collection. Returns empty DataFrame if COLLECTION_NAME is None."""
        if COLLECTION_NAME is None:
            return pd.DataFrame(columns=['display_name', 'project_name', 'metric_name', 'date', 'amount'])

        return client.to_pandas(f"""
            SELECT DISTINCT
              p.display_name AS display_name,
              p.project_name AS project_name,
              m.metric_name AS metric_name,
              ts.sample_date AS date,
              ts.amount AS amount
            FROM timeseries_metrics_by_project_v0 ts        
            JOIN metrics_v0 m
              ON m.metric_id = ts.metric_id
            JOIN projects_v1 p
              ON p.project_id = ts.project_id
            JOIN projects_by_collection_v1 pc
              ON p.project_id = pc.project_id
            WHERE
              ts.sample_date >= DATE '{PROJECT_START_DATE}'
              AND m.metric_name IN ({stringify(METRIC_NAMES)})
              AND pc.collection_name = '{COLLECTION_NAME}'
              AND ts.amount IS NOT NULL
        """)

    @parse_dates("date")
    def get_metrics_by_sdk_dependent(repo_ids):
        return client.to_pandas(f"""
            WITH ossd_projects AS (
              SELECT DISTINCT project_id
              FROM artifacts_by_project_v1
              WHERE
                artifact_id IN ({stringify(repo_ids)})
                AND artifact_source = 'GITHUB'
                AND project_source = 'OSS_DIRECTORY'
                AND project_namespace = 'oso'
                AND project_name NOT IN ({stringify(SDK_PROJECT_MAINTAINERS)})
            )
            SELECT DISTINCT
              p.display_name AS display_name,
              p.project_name AS project_name,
              m.metric_name AS metric_name,
              ts.sample_date AS date,
              ts.amount AS amount
            FROM timeseries_metrics_by_project_v0 ts        
            JOIN metrics_v0 m
              ON m.metric_id = ts.metric_id
            JOIN projects_v1 p
              ON p.project_id = ts.project_id
            WHERE
              ts.sample_date >= DATE '{PROJECT_START_DATE}'
              AND m.metric_name IN ({stringify(METRIC_NAMES)})
              AND p.project_id IN (SELECT project_id FROM ossd_projects)
              AND ts.amount IS NOT NULL
        """)    

    @parse_dates("date")
    def get_metrics_by_collection_repo():
        """Get repo-level metrics for a collection. Returns empty DataFrame if COLLECTION_NAME is None."""
        if COLLECTION_NAME is None:
            return pd.DataFrame(columns=['artifact_name', 'project_name', 'metric_name', 'date', 'amount'])

        return client.to_pandas(f"""
            SELECT
              ap.artifact_name AS artifact_name,
              ap.project_name AS project_name,
              m.metric_name AS metric_name,
              ts.sample_date AS date,
              ts.amount AS amount
            FROM artifacts_by_project_v1 ap
            JOIN projects_by_collection_v1 pc
              ON ap.project_id = pc.project_id
            JOIN timeseries_metrics_by_artifact_v0 ts
              ON ts.artifact_id = ap.artifact_id
            JOIN metrics_v0 m
              ON m.metric_id = ts.metric_id
            WHERE
              pc.collection_name = '{COLLECTION_NAME}'
              AND ap.artifact_source = 'GITHUB'
              AND m.metric_name = 'GITHUB_active_developers_monthly'
              AND ts.sample_date >= DATE '{PROJECT_START_DATE}'
        """)

    def get_dependents_for_packages(*,
        packages: list[tuple[str, str, str]]
    ):
        """Gets dependents for the given set of packages

        Args:
          - package - a list of tuples for the packages to find dependents for 
            where each tuple is:

                (owner_artifact_namespace, owner_artifact_name, artifact_name)  
        """

        package_lookups = [f"{p[0]}/{p[1]}/{p[2]}" for p in packages]
        return client.to_pandas(f"""
            WITH stylus AS (
              SELECT DISTINCT
                package_artifact_id,
                package_owner_artifact_id
              FROM package_owners_v0
              WHERE
                CONCAT(package_owner_artifact_namespace, '/', package_owner_artifact_name, '/', package_artifact_name) in ({stringify(package_lookups)})
            )
            SELECT DISTINCT
              abp.project_name AS dependent_project_name,
              sboms_v0.dependent_artifact_namespace AS repo_owner,
              sboms_v0.dependent_artifact_name AS repo_name,
              sboms_v0.dependent_artifact_id AS artifact_id          
            FROM sboms_v0
            JOIN stylus
              ON sboms_v0.package_artifact_id = stylus.package_artifact_id
            JOIN artifacts_by_project_v1 AS abp
              ON
                sboms_v0.dependent_artifact_id = abp.artifact_id
                AND abp.project_source = 'OSS_DIRECTORY'
                AND abp.project_namespace = 'oso'
                AND abp.project_name NOT IN ({stringify(SDK_PROJECT_MAINTAINERS)})
            WHERE stylus.package_owner_artifact_id != sboms_v0.dependent_artifact_id
            ORDER BY 1,2,3
        """)    

    @parse_dates("first_fork")
    def get_devs_who_forked_examples(
        *,
        owner_artifact_namespace: str,
        packages: list[tuple[str, str, str]]
    ):
        """Gets devs who forked example repos

        Args:
          - owner_artifact_namespace - the namespace to look for example repos
          - packages - a list of tuples for the packages to find dependents for 
            where each tuple is:

                (owner_artifact_namespace, owner_artifact_name, artifact_name)  
        """

        package_lookups = [f"{p[0]}/{p[1]}/{p[2]}" for p in packages]
        return client.to_pandas(f"""
            WITH stylus AS (
              SELECT DISTINCT package_artifact_id
              FROM package_owners_v0
              WHERE
                CONCAT(package_owner_artifact_namespace, '/', package_owner_artifact_name, '/', package_artifact_name) in ({stringify(package_lookups)})
            ),
            example_repos AS (
              SELECT DISTINCT dependent_artifact_id
              FROM sboms_v0
              JOIN stylus USING package_artifact_id
              WHERE dependent_artifact_namespace = '{owner_artifact_namespace}'
            ),
            devs AS (
              SELECT
                artifact_id AS dev_id,
                artifact_url AS dev_url,
                MIN(time) AS first_fork,
                MIN_BY(to_artifact_id, time) AS forked_repo_id
              FROM int_first_of_event_from_artifact__github AS fe
              JOIN example_repos AS er
                ON fe.to_artifact_id = er.dependent_artifact_id
              JOIN int_github_users AS u
                ON fe.from_artifact_id = u.artifact_id
              WHERE
                event_type = 'FORKED'
                AND time >= DATE '{PROJECT_START_DATE}'
              GROUP BY 1,2
            ),
            dev_events AS (
              SELECT
                devs.dev_id,
                devs.first_fork,
                e.to_artifact_id AS repo_id,
                SUM(e.amount) AS num_commits
              FROM int_events_daily__github AS e
              JOIN devs ON e.from_artifact_id = devs.dev_id
              WHERE
                e.event_type = 'COMMIT_CODE'
                AND e.bucket_day >= devs.first_fork
              GROUP BY 1,2,3
            ),
            star_counts AS (
              SELECT
                de.repo_id,
                APPROX_DISTINCT(e.from_artifact_id) AS star_count
              FROM int_events_daily__github AS e
              JOIN dev_events AS de
                ON e.to_artifact_id = de.repo_id
              WHERE
                e.event_type = 'STARRED'
                AND e.bucket_day >= de.first_fork
                AND e.from_artifact_id != de.dev_id
              GROUP BY 1
            )
            SELECT DISTINCT
              devs.dev_url,
              fr.artifact_url AS first_fork_repo_url,
              a.artifact_url AS repo_url,
              devs.first_fork,
              de.num_commits,
              COALESCE(sc.star_count, 0) AS star_count,          
              a.artifact_namespace AS repo_owner,
              de.dev_id,
              de.repo_id          
            FROM dev_events AS de
            JOIN devs ON de.dev_id = devs.dev_id
            JOIN int_artifacts__github AS a
              ON de.repo_id = a.artifact_id
            LEFT JOIN star_counts AS sc
              ON a.artifact_id = sc.repo_id
            JOIN repositories_v0 AS fr
              ON devs.forked_repo_id = fr.artifact_id
        """)

    def get_repo_alignment_tags(list_of_repo_artifact_ids):
        df = client.to_pandas(f"""
            WITH projects AS (
              SELECT DISTINCT
                artifact_id,
                project_id,
                project_name,
                project_source
              FROM artifacts_by_project_v1
              WHERE
                artifact_id IN ({stringify(list_of_repo_artifact_ids)})
                AND project_source IN ('OSS_DIRECTORY', 'CRYPTO_ECOSYSTEMS')
                AND project_namespace IN ('oso', 'eco')
            ),
            alignment AS (
              SELECT
                project_id,
                MAX(CASE WHEN project_name = 'arbitrum' THEN True ELSE False END) AS in_arbitrum,
                MAX(CASE WHEN project_name IN ({stringify(OTHER_ECOSYSTEMS)}) THEN True ELSE False END) AS in_nonevm_ecosystem,
                MAX(CASE WHEN project_name IN ({stringify(EVM_ECOSYSTEMS)}) THEN True ELSE False END) AS in_evm_ecosystem
              FROM projects
              WHERE project_source = 'CRYPTO_ECOSYSTEMS'
              GROUP BY 1
            )
            SELECT DISTINCT
              projects.artifact_id AS repo_id,
              alignment.*
            FROM projects
            LEFT JOIN alignment USING project_id
        """)
        df = df.fillna(False)
        return df

    def get_artifact_overlap(target_ecosystem='Arbitrum'):
        return client.to_pandas(f"""
            WITH base AS (
              SELECT DISTINCT
                p.display_name AS ecosystem_name,
                ap.artifact_id
              FROM artifacts_by_project_v1 ap
              JOIN projects_v1 p ON p.project_id=ap.project_id
              WHERE
                ap.artifact_source='GITHUB'
                AND ap.project_source='CRYPTO_ECOSYSTEMS'
                AND ap.project_namespace='eco'
                AND ap.project_name IN ({stringify(ECOSYSTEMS)})
            ),
            target_set AS (
              SELECT artifact_id FROM base WHERE ecosystem_name='{target_ecosystem}'
            ),
            totals AS (
              SELECT
                ecosystem_name,
                COUNT(DISTINCT artifact_id) AS total_repos
              FROM base
              GROUP BY ecosystem_name
            ),
            shared AS (
              SELECT
                ecosystem_name,
                COUNT(DISTINCT artifact_id) AS shared_with_target
              FROM base
              WHERE artifact_id IN (SELECT artifact_id FROM target_set)
              GROUP BY ecosystem_name
            )
            SELECT
              t.ecosystem_name,
              COALESCE(s.shared_with_target,0) AS repos_shared_with_target,
              (t.total_repos - COALESCE(s.shared_with_target,0)) AS repos_not_shared_with_target,
              t.total_repos AS total_repos
            FROM totals t
            LEFT JOIN shared s
              ON t.ecosystem_name = s.ecosystem_name
            ORDER BY
              repos_shared_with_target DESC,
              ecosystem_name
    """)

    def get_total_repos_in_crypto_ecosystems():
        df = client.to_pandas("""
          SELECT APPROX_DISTINCT(artifact_id) AS count
          FROM artifacts_by_project_v1
          WHERE
            project_source = 'CRYPTO_ECOSYSTEMS'
            AND project_namespace = 'eco'
            AND artifact_source = 'GITHUB'
        """)
        return df['count'].sum()
    return (
        get_artifact_overlap,
        get_dependents_for_packages,
        get_devs_who_forked_examples,
        get_metrics_by_collection_project,
        get_metrics_by_developer_ecosystem,
        get_metrics_by_sdk_dependent,
        get_repo_alignment_tags,
        get_total_repos_in_crypto_ecosystems,
    )


@app.cell
def helper_labeling_and_pagerank(
    OWNER_ARTIFACT_NAMESPACE,
    get_repo_alignment_tags,
    np,
    nx,
    pd,
):
    def label_repos(df):

        _repos = df['repo_id'].unique()

        df_labeled = get_repo_alignment_tags(_repos)
        df_labeled = df_labeled.groupby('repo_id').max()
        df_labeled["tags"] = df_labeled.apply(lambda row: ";".join([col.replace('in_','') for col in df_labeled.columns if row[col]]), axis=1)
        df_merged = df.set_index('repo_id').join(df_labeled[["tags"]])

        def label_project(tags, dev_url, repo_url):
            if not isinstance(tags, str):
                tags = '7 - n/a'
            if 'Eigen Network' in tags:
                return '0 - Project (Eigen Network)'
            if f'/{OWNER_ARTIFACT_NAMESPACE}/' in repo_url:
                return f'1 - {OWNER_ARTIFACT_NAMESPACE.title()}'
            if 'nonevm' in tags:
                if ';' in tags:
                    return '3 - Project (EVM + Non-EVM Ecosystems)'
                else:
                    return '2 - Project (Non-EVM Ecosystem)'
            if len(tags) > 1:
                if dev_url in repo_url:
                    return '6 - Personal'
                else:
                    return '4 - Project (EVM Ecosystem)'
            return '5 - Project (Other)'

        df_merged['project_type'] = df_merged.apply(lambda x: label_project(x['tags'], x['dev_url'], x['repo_url']), axis=1)
        df_merged.drop(columns="tags", inplace=True)

        return df_merged



    def dev_pagerank(
        df,
        alpha=0.85,
        max_iter=100,
        star_exp=1.0,        # how strongly repo stars matter
        commit_exp=1.0,      # how strongly commit volume matters
        star_floor=0.0       # add to stars to avoid zero-sinks; e.g., 1.0
    ):

        # Nodes
        devs = df[['dev_id','dev_url']].drop_duplicates().reset_index(drop=True)
        repos = df[['repo_url','star_count']].drop_duplicates().reset_index(drop=True)

        G = nx.DiGraph()
        for _, r in devs.iterrows():
            G.add_node(("dev", r.dev_id), url=r.dev_url, ntype="dev")
        for _, r in repos.iterrows():
            stars = float(r.star_count or 0.0)
            G.add_node(("repo", r.repo_url), stars=stars, ntype="repo")

        # Edges (commit-weighted dev→repo, star-weighted repo→dev)
        for _, r in df.iterrows():
            d = ("dev", r.dev_id); rep = ("repo", r.repo_url)
            if d not in G or rep not in G: 
                continue

            c = max(0.0, float(r.num_commits or 0.0))
            s = max(0.0, float(r.star_count  or 0.0))
            w_dr = c**commit_exp
            w_rd = (s + star_floor)**star_exp

            if w_dr > 0: G.add_edge(d,   rep, weight=w_dr)
            if w_rd > 0: G.add_edge(rep, d,   weight=w_rd)

        # Personalization: devs by commits, repos by stars
        dev_commit_sum = df.groupby("dev_id")["num_commits"].sum().reindex(devs.dev_id).fillna(0)
        repo_stars = repos.set_index("repo_url")["star_count"].fillna(0)

        p = {}
        for n in G.nodes:
            ntype, key = n
            if ntype == "dev":
                p[n] = 1.0 + np.log1p(float(dev_commit_sum.get(key, 0.0)))
            else:
                p[n] = 1.0 + np.log1p(float(repo_stars.get(key, 0.0)) + star_floor)

        z = sum(p.values()) or 1.0
        p = {k:v/z for k,v in p.items()}

        pr = nx.pagerank(G, alpha=alpha, personalization=p, weight="weight", max_iter=max_iter)
        rows = []
        for (ntype, key), score in pr.items():
            if ntype != "dev": 
                continue
            rows.append({
                "dev_id": key,
                "dev_score": score,
                "dev_url": G.nodes[(ntype,key)]["url"]
            })
        dev_rank = pd.DataFrame(rows).sort_values("dev_score", ascending=False, kind="mergesort").reset_index(drop=True)

        # Some diagnostics
        dev_rank = dev_rank.merge(
            devs.assign(total_commits=dev_commit_sum.values), on=["dev_id","dev_url"], how="left"
        )
        repo_star_map = repos.set_index("repo_url")["star_count"].to_dict()
        exposure = (
            df.assign(w=lambda x: (x["num_commits"].clip(lower=0).astype(float)**commit_exp) 
             * (df["repo_url"].map(repo_star_map).fillna(0).astype(float)))
              .groupby("dev_id")["w"]
              .sum()
              .rename("star_exposure")
        )
        dev_rank = dev_rank.merge(exposure, on="dev_id", how="left").fillna({"star_exposure":0.0})

        return dev_rank    
    return dev_pagerank, label_repos


@app.cell
def helper_velocity_calculation(np, pd):
    def cohort_velocity_change(
        df,
        metric_name,
        cohort_start,
        date_col = "date",
        amount_col = "amount",
        metric_col = "metric_name",
    ):

        d = df[df[metric_col] == metric_name].copy()
        d[date_col] = pd.to_datetime(d[date_col], utc=False, errors="coerce")

        if d[date_col].dt.tz is not None:
            d[date_col] = d[date_col].dt.tz_convert(None)

        cohort_start_ts = pd.to_datetime(cohort_start, utc=False, errors="coerce")
        if getattr(cohort_start_ts, "tzinfo", None) is not None:
            cohort_start_ts = cohort_start_ts.tz_localize(None)

        before = d[d[date_col] < cohort_start_ts]
        after  = d[d[date_col] >= cohort_start_ts]

        def week_span(x: pd.Series) -> float:
            if x.empty: return np.nan
            delta_days = (x.max() - x.min()).days
            return max(delta_days/7, np.nan)

        before_weeks = week_span(before[date_col])
        after_weeks  = week_span(after[date_col])

        def velocity(frame: pd.DataFrame, weeks: float) -> float:
            if frame.empty or not np.isfinite(weeks) or weeks <= 0:
                return np.nan
            return frame[amount_col].sum()/weeks

        v_before = velocity(before, before_weeks)
        v_after  = velocity(after,  after_weeks)

        if not np.isfinite(v_before) or v_before == 0:
            return np.nan
        return (v_after-v_before)/v_before
    return (cohort_velocity_change,)


@app.cell
def helper_monthly_metrics(MONTHLY_METRICS, datetime, pd):
    def summarize_monthly_metrics(df, num_months=6):    
        # Get the most recent date from the dataframe
        most_recent_month = df[df['metric_name'].str.endswith('monthly') == True]['date'].max()
        if most_recent_month is None:
            # Return empty dataframe if no monthly data
            return pd.DataFrame(columns=['Project'] + [clean_metric_name(c) for c in MONTHLY_METRICS])

        start_month = datetime(2025, most_recent_month.month - (num_months-1), 1).date()
        table = (
            df[
                (df['metric_name'].str.endswith('monthly') == True) &
                (df['date'].between(start_month, most_recent_month)) &
                (df['amount'].notna())
            ]
            .pivot_table(index='display_name', columns='metric_name', values='amount', aggfunc='sum', fill_value=0)
            .map(lambda x: round(x/num_months,2))
            [MONTHLY_METRICS]
            .rename(columns={c:clean_metric_name(c) for c in MONTHLY_METRICS})
            .reset_index()
            .rename(columns={'display_name': 'Project'})
        )
        return table
    return (summarize_monthly_metrics,)


@app.cell
def process_data(
    OWNER_ARTIFACT_NAMESPACE,
    PACKAGES_TO_MONITOR,
    dev_pagerank,
    get_artifact_overlap,
    get_dependents_for_packages,
    get_devs_who_forked_examples,
    get_metrics_by_collection_project,
    get_metrics_by_developer_ecosystem,
    get_metrics_by_sdk_dependent,
    label_repos,
):
    # Get the data
    df_ecosystem_metrics = get_metrics_by_developer_ecosystem()
    df_repo_overlap = get_artifact_overlap()
    df_collection_project_metrics = get_metrics_by_collection_project()
    df_sdk_deps = get_dependents_for_packages(packages=PACKAGES_TO_MONITOR)
    df_sdk_deps_project_metrics = get_metrics_by_sdk_dependent(df_sdk_deps['artifact_id'].unique())
    df_fork_devs = get_devs_who_forked_examples(packages=PACKAGES_TO_MONITOR, owner_artifact_namespace=OWNER_ARTIFACT_NAMESPACE)

    # Process developer data
    df_fork_devs_labeled = label_repos(df_fork_devs) if not df_fork_devs.empty else df_fork_devs
    df_fork_devs_ranked = dev_pagerank(df_fork_devs) if not df_fork_devs.empty else df_fork_devs
    return (
        df_ecosystem_metrics,
        df_fork_devs,
        df_fork_devs_labeled,
        df_fork_devs_ranked,
        df_repo_overlap,
        df_sdk_deps,
        df_sdk_deps_project_metrics,
    )


@app.cell
def generate_joyplot(COHORT_START_DATE, go, np, pd, px):
    def make_joyplot(df, smoothing=7, display_months=None):

        colorscale = 'Greens'
        gap = 1.10
        fill_alpha = 0.40

        wide = df.pivot_table(index="date", columns="display_name", values="amount", aggfunc="sum").sort_index()

        # Apply smoothing to full dataset
        if smoothing > 1:
            wide = wide.rolling(window=smoothing, min_periods=1, center=True).mean()

        # Filter to display window if specified
        if display_months is not None and display_months > 0:
            last_date = wide.index.max()
            cutoff_date = pd.to_datetime(last_date) - pd.DateOffset(months=display_months)
            wide_display = wide[wide.index >= cutoff_date.date()]
        else:
            wide_display = wide

        wide_norm = wide_display.copy()
        for col in wide_display.columns:
            non_zero_count = (wide_display[col] > 0).sum()
            if non_zero_count > 50:
                threshold = int(wide_display[col].quantile(0.95))
                wide_norm[col] = wide_norm[col].clip(upper=threshold)
            denom = wide_norm[col].max(skipna=True)
            wide_norm[col] = wide_norm[col].divide(denom, axis=0)

        cols = list(wide_norm.columns)[::-1]
        cmap = getattr(px.colors.sequential, colorscale)
        cmap_subset = cmap[len(cmap)//2:][::-1]

        n = len(cols)
        proj_colors = {}
        for rank, col in enumerate(cols):
            idx = int(round(rank * (len(cmap_subset) - 1) / max(1, n - 1)))
            proj_colors[col] = cmap_subset[idx]

        cohort_start_date = pd.to_datetime(COHORT_START_DATE).date()
        last_date = wide_norm.index.max()

        fig = go.Figure()
        tickvals, ticktext = [], []

        for i, col in enumerate(cols):
            y_offset = i * gap
            y_vals = wide_norm[col].fillna(0).values
            x_vals = wide_norm.index

            color = proj_colors[col]
            fill_color = rgba_from_rgb(color, fill_alpha)

            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=np.full(y_vals.shape, y_offset, dtype=float),
                    mode="lines",
                    line=dict(width=0),
                    hoverinfo="skip",
                    showlegend=False
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals + y_offset,
                    mode="lines",
                    fill="tonexty",
                    line=dict(color=color, width=1.5),
                    line_shape="spline",
                    fillcolor=fill_color,
                    name=col,
                    customdata=np.c_[wide_norm[col].reindex(x_vals).fillna(0).values * 100],
                    hovertemplate="<b>%{fullData.name}</b><br>Week of: %{x|%d %b %Y}<br>Velocity: %{customdata[0]:,.0f}% of max<extra></extra>",
                    showlegend=False
                )
            )
            tickvals.append(y_offset)

            # Calculate velocity change using full dataset
            pre_cohort_data = wide[col][wide.index < cohort_start_date]
            post_cohort_data = wide[col][wide.index >= cohort_start_date]

            pre_cohort_avg = pre_cohort_data.fillna(0).mean()
            post_cohort_avg = post_cohort_data.fillna(0).mean()

            if pre_cohort_avg > 0:
                change = ((post_cohort_avg - pre_cohort_avg) / pre_cohort_avg) * 100
            else:
                change = 0

            if int(change) > 0:
                annotation_text = f"+{change:,.0f}%"
            elif int(change) < 0:
                annotation_text = f"{change:,.0f}%"
            else:
                annotation_text = "No change"

            ticktext.append(f"<b>{col}</b>: {annotation_text}")


        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(size=12, color="#111"),
            margin=dict(l=0, r=80, t=0, b=0),
            showlegend=False,
            title=dict(text="", x=0, xanchor="left", font=dict(size=14, color="#111"))
        )
        fig.update_xaxes(title="", showgrid=False, visible=False, linecolor="#000", linewidth=1)
        fig.update_yaxes(
            title="",
            side="right",
            showgrid=False,
            tickmode="array",
            ticklabelposition="outside top",
            #ticklabelshift=-1,
            ticklabelstandoff=5,
            tickvals=tickvals,
            ticktext=ticktext,
            zeroline=False,
            tickcolor="#000",
            showline=False
        )
        return fig
    return (make_joyplot,)


@app.cell
def generate_repo_overlap_barchart(go, np):
    def make_repo_overlap_barchart(df, target_ecosystem):
        # Expect columns: ecosystem_name, repos_shared_with_target, repos_not_shared_with_target, total_repos
        d = df.copy()
        d.sort_values(["repos_shared_with_target", "total_repos", "ecosystem_name"], ascending=[False,False,True], inplace=True)

        d["shared_val"] = d["repos_shared_with_target"]
        d["not_shared_val"] = d["repos_not_shared_with_target"]

        xaxis_title = "Repositories"
        hover_suffix = ""
        hover_shared_val = d["shared_val"]
        hover_not_shared_val = d["not_shared_val"]

        # Colors (fixed, readable on black)
        COLOR_SHARED = "#2ecc71"
        COLOR_NOT_SHARED = "#888888"
        COLOR_HILITE = "Green"  # slightly brighter for the highlighted ecosystem
        shared_colors = [COLOR_HILITE if name==target_ecosystem else COLOR_SHARED for name in d["ecosystem_name"]]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=d["ecosystem_name"],
            x=d["shared_val"],
            name=f"Shared with {target_ecosystem}",
            orientation="h",
            marker=dict(color=shared_colors),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Shared: %{customdata[0]:,.0f}"+hover_suffix+"<br>"
                "Not shared: %{customdata[1]:,.0f}"+hover_suffix+"<br>"
                "Total: %{customdata[2]:,.0f}<extra></extra>"
            ),
            customdata=np.stack([
                hover_shared_val,
                hover_not_shared_val,
                d["total_repos"]
            ], axis=-1)
        ))
        fig.add_trace(go.Bar(
            y=d["ecosystem_name"],
            x=d["not_shared_val"],
            name="Not shared",
            orientation="h",
            marker=dict(color=COLOR_NOT_SHARED),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Shared: %{customdata[1]:,.0f}"+hover_suffix+"<br>"
                "Not shared: %{customdata[0]:,.0f}"+hover_suffix+"<br>"
                "Total: %{customdata[2]:,.0f}<extra></extra>"
            ),
            customdata=np.stack([
                hover_not_shared_val,
                hover_shared_val,
                d["total_repos"]
            ], axis=-1)
        ))
        fig.update_layout(
            barmode="stack",
            title="",
            paper_bgcolor="white", plot_bgcolor="white",
            font=dict(size=12, color="black"),
            margin=dict(t=0, l=0, r=20, b=40),
            showlegend=True,
            legend=dict(orientation="h", y=1.02, x=1, xanchor='right')
        )
        fig.update_xaxes(title=xaxis_title, showgrid=True, gridcolor="#AAA", zeroline=False, color="black")
        fig.update_yaxes(title="", showgrid=False, color="black", automargin=True)

        return fig
    return (make_repo_overlap_barchart,)


@app.function
def clean_metric_name(col):
    return col.replace('GITHUB_','').replace('_monthly','').replace('_',' ').title()


@app.function
def rgba_from_rgb(rgb, alpha):
    return rgb.replace("rgb", "rgba").replace(")", f",{alpha})")


@app.cell
def import_libraries():
    from datetime import datetime, date, timedelta
    from functools import wraps
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    import networkx as nx
    import numpy as np
    return datetime, go, np, nx, pd, px, timedelta, wraps


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    client = pyoso.Client()
    pyoso_db_conn = client.dbapi_connection()
    return client, mo


if __name__ == "__main__":
    app.run()
