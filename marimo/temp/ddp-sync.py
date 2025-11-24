import marimo

__generated_with = "0.17.5"
app = marimo.App(width="full")


@app.cell
def _(mo):
    mo.md(r"""
    # DDP Sync Meeting

    *25 November 2025*

    # Repo Discovery

    - [ ] Projects that have received grants
    - [ ] Ethereum package dependencies
    - [ ] Repository discovery algorithm

    ---
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 1. Funding from Ethereum-aligned sources (Octant, Gitcoin, Optimism Retro Funding)

    This query gives us a longlist of ~20K repos to consider. To qualify, the repo must have received at least $5000 in lifetime funding from Ethereum public goods funding sources.

    ```sql
    WITH funded_projects AS (
      SELECT DISTINCT project_id
      FROM timeseries_metrics_by_project_v0
      JOIN projects_v1 USING project_id
      JOIN metrics_v0 USING metric_id
      WHERE
        metric_model LIKE 'funding_awarded'
        AND project_source = 'OSS_DIRECTORY'
        AND metric_time_aggregation = 'over_all_time'
        AND metric_event_source IN (
          'OCTANT',
          'OPTIMISM_GOVGRANTS',
          'ARBITRUMFOUNDATION',
          'OPTIMISM_RETROFUNDING',
          'CLRFUND',
          'GITCOIN_MATCHING',
          'GITCOIN_DONATIONS'
        )
        AND amount >= 5000
    ),
    project_repos AS (
      SELECT
        artifact_id,
        artifact_namespace,
        project_name
      FROM artifacts_by_project_v1
      JOIN funded_projects USING project_id
      WHERE artifact_source = 'GITHUB'
    ),
    ce_check AS (
      SELECT
        pr.artifact_id,
        (ce.artifact_id IS NOT NULL) AS is_in_crypto_ecosystems,
        (ce_maintainer.artifact_id IS NOT NULL) AS is_maintainer_in_crypto_ecosystems
      FROM project_repos AS pr
      LEFT JOIN oso.int_artifacts_by_project_in_crypto_ecosystems AS ce
        ON pr.artifact_id = ce.artifact_id
        AND ce.project_source = 'CRYPTO_ECOSYSTEMS'
        AND ce.project_namespace = 'eco'
      LEFT JOIN oso.int_artifacts_by_project_in_crypto_ecosystems AS ce_maintainer
        ON pr.artifact_namespace = ce_maintainer.artifact_namespace
        AND ce_maintainer.project_source = 'CRYPTO_ECOSYSTEMS'
        AND ce_maintainer.project_namespace = 'eco'
    )
    SELECT DISTINCT
      project_name,
      url,
      is_in_crypto_ecosystems,
      is_maintainer_in_crypto_ecosystems,
      repo_maintainer,
      is_personal_repo,
      is_current_repo,
      contributor_count,
      has_packages,
      last_activity_time,
      star_count,
      fork_count
    FROM project_repos
    JOIN int_ddp_repo_features USING artifact_id
    JOIN ce_check USING artifact_id
    WHERE is_ethereum IS NULL
    ORDER BY contributor_count DESC
    ```

    Here is the full list of repos:
    """)
    return


@app.cell
def _(mo, pyoso_db_conn):
    df_funded_projects = mo.sql(
        f"""
        WITH funded_projects AS (
          SELECT DISTINCT project_id
          FROM timeseries_metrics_by_project_v0
          JOIN projects_v1 USING project_id
          JOIN metrics_v0 USING metric_id
          WHERE
            metric_model LIKE 'funding_awarded'
            AND project_source = 'OSS_DIRECTORY'
            AND metric_time_aggregation = 'over_all_time'
            AND metric_event_source IN (
              'OCTANT',
              'OPTIMISM_GOVGRANTS',
              'ARBITRUMFOUNDATION',
              'OPTIMISM_RETROFUNDING',
              'CLRFUND',
              'GITCOIN_MATCHING',
              'GITCOIN_DONATIONS'
            )
            AND amount >= 5000
        ),
        project_repos AS (
          SELECT
            artifact_id,
            artifact_namespace,
            project_name
          FROM artifacts_by_project_v1
          JOIN funded_projects USING project_id
          WHERE artifact_source = 'GITHUB'
        ),
        ce_check AS (
          SELECT
            pr.artifact_id,
            (ce.artifact_id IS NOT NULL) AS is_in_crypto_ecosystems,
            (ce_maintainer.artifact_id IS NOT NULL) AS is_maintainer_in_crypto_ecosystems
          FROM project_repos AS pr
          LEFT JOIN oso.int_artifacts_by_project_in_crypto_ecosystems AS ce
            ON pr.artifact_id = ce.artifact_id
            AND ce.project_source = 'CRYPTO_ECOSYSTEMS'
            AND ce.project_namespace = 'eco'
          LEFT JOIN oso.int_artifacts_by_project_in_crypto_ecosystems AS ce_maintainer
            ON pr.artifact_namespace = ce_maintainer.artifact_namespace
            AND ce_maintainer.project_source = 'CRYPTO_ECOSYSTEMS'
            AND ce_maintainer.project_namespace = 'eco'
        )
        SELECT DISTINCT
          project_name,
          url,
          is_in_crypto_ecosystems,
          is_maintainer_in_crypto_ecosystems,
          repo_maintainer,
          is_personal_repo,
          is_current_repo,
          contributor_count,
          has_packages,
          last_activity_time,
          star_count,
          fork_count
        FROM project_repos
        JOIN int_ddp_repo_features USING artifact_id
        JOIN ce_check USING artifact_id
        WHERE is_ethereum IS NULL
        ORDER BY contributor_count DESC
        """,
        engine=pyoso_db_conn
    )
    return (df_funded_projects,)


@app.cell
def _(mo):
    mo.md(r"""
    ### Part A: Repos in Crypto Ecosystems (but not Ethereum)

    This table shows repositories that have received funding from Ethereum-aligned sources and are currently tracked in Crypto Ecosystems, but are **not** classified as part of the Ethereum ecosystem. These repos are active (last activity since 2025-01-01) and represent current repositories (not renamed/archived). The table is grouped by maintainer, showing the maximum contributor, star, and fork counts across all repos from each maintainer.
    """)
    return


@app.cell
def _(df_funded_projects, mo):
    _df_filtered = df_funded_projects[
        (df_funded_projects['is_in_crypto_ecosystems'] == True)
        & (df_funded_projects['is_current_repo'] == True)
        & (df_funded_projects['last_activity_time'] >= '2025-01-01')
    ]
    _num_repos = len(_df_filtered)

    # Create flagged dataframe for consolidation
    funding_part_a_crypto_ecosystems = (
        _df_filtered[['url', 'repo_maintainer', 'contributor_count', 'last_activity_time']]
        .drop_duplicates(subset=['url', 'repo_maintainer'])
        .assign(funding_crypto_ecosystems_not_ethereum=True)
    )

    _df = (
        _df_filtered
        .groupby('repo_maintainer', as_index=False)
        .agg({
            'contributor_count': 'max',
            'star_count': 'max',
            'fork_count': 'max',
            'url': 'unique',
        })
        .sort_values(by='contributor_count', ascending=False)
        .reset_index(drop=True)
    )

    mo.vstack([
        mo.md(f"**Count:** {_num_repos:,.0f} repos"),
        mo.ui.table(_df, show_column_summaries=False, show_data_types=False)
    ])
    return (funding_part_a_crypto_ecosystems,)


@app.cell
def _(mo):
    mo.md(r"""
    ### Part B: Maintainers with no repos in Crypto Ecosystems

    This table shows repositories from maintainers where **none** of their repositories are currently tracked in Crypto Ecosystems, despite having received funding from Ethereum-aligned sources. These repos are active (last activity since 2025-01-01) and represent current repositories. The table is grouped by maintainer, showing the maximum contributor, star, and fork counts across all repos from each maintainer.
    """)
    return


@app.cell
def _(df_funded_projects, mo):
    _df_filtered = df_funded_projects[
        (df_funded_projects['is_maintainer_in_crypto_ecosystems'] == False)
        & (df_funded_projects['is_current_repo'] == True)
        & (df_funded_projects['last_activity_time'] >= '2025-01-01')
    ]
    _num_repos = len(_df_filtered)

    # Create flagged dataframe for consolidation
    funding_part_b_no_crypto_ecosystems = (
        _df_filtered[['url', 'repo_maintainer', 'contributor_count', 'last_activity_time']]
        .drop_duplicates(subset=['url', 'repo_maintainer'])
        .assign(funding_maintainer_no_crypto_ecosystems=True)
    )

    _df = (
        _df_filtered
        .groupby('repo_maintainer', as_index=False)
        .agg({
            'contributor_count': 'max',
            'star_count': 'max',
            'fork_count': 'max',
            'url': 'unique',
        })
        .sort_values(by='contributor_count', ascending=False)
        .reset_index(drop=True)
    )

    mo.vstack([
        mo.md(f"**Count:** {_num_repos:,.0f} repos"),
        mo.ui.table(_df, show_column_summaries=False, show_data_types=False)
    ])
    return (funding_part_b_no_crypto_ecosystems,)


@app.cell
def _(mo):
    mo.md(r"""
    ### Part C: Maintainers with mixed ecosystem presence

    This table shows repositories from maintainers who **do** have some repos in Crypto Ecosystems, but these specific repos are **not** currently tracked. These repos have received funding from Ethereum-aligned sources, are active (last activity since 2025-01-01), and represent current repositories. The table is grouped by maintainer, showing the maximum contributor, star, and fork counts across all repos from each maintainer.
    """)
    return


@app.cell
def _(df_funded_projects, mo):
    _df_filtered = df_funded_projects[
        (df_funded_projects['is_maintainer_in_crypto_ecosystems'] == True)
        & (df_funded_projects['is_in_crypto_ecosystems'] == False)
        & (df_funded_projects['is_current_repo'] == True)
        & (df_funded_projects['last_activity_time'] >= '2025-01-01')
    ]
    _num_repos = len(_df_filtered)

    # Create flagged dataframe for consolidation
    funding_part_c_mixed_ecosystem = (
        _df_filtered[['url', 'repo_maintainer', 'contributor_count', 'last_activity_time']]
        .drop_duplicates(subset=['url', 'repo_maintainer'])
        .assign(funding_mixed_ecosystem_presence=True)
    )

    _df = (
        _df_filtered
        .groupby('repo_maintainer', as_index=False)
        .agg({
            'contributor_count': 'max',
            'star_count': 'max',
            'fork_count': 'max',
            'url': 'unique',
        })
        .sort_values(by='contributor_count', ascending=False)
        .reset_index(drop=True)
    )

    mo.vstack([
        mo.md(f"**Count:** {_num_repos:,.0f} repos"),
        mo.ui.table(_df, show_column_summaries=False, show_data_types=False)
    ])
    return (funding_part_c_mixed_ecosystem,)


@app.cell
def _(mo):
    mo.md(r"""
    ### Part D: Recently renamed/archived repos

    This table shows repositories that have **changed names recently** (not current repos) and are not in Crypto Ecosystems. These repos have received funding from Ethereum-aligned sources and are still active (last activity since 2025-01-01). These should be reviewed on a case-by-case basis to determine if they represent the same project under a new name. The table is grouped by maintainer and ecosystem status, showing the maximum contributor, star, and fork counts.
    """)
    return


@app.cell
def _(df_funded_projects, mo):
    _df_filtered = df_funded_projects[
        (df_funded_projects['is_current_repo'] == False)
        & (df_funded_projects['is_in_crypto_ecosystems'] == False)
        & (df_funded_projects['last_activity_time'] >= '2025-01-01')
    ]
    _num_repos = len(_df_filtered)

    # Create flagged dataframe for consolidation
    funding_part_d_renamed_archived = (
        _df_filtered[['url', 'repo_maintainer', 'contributor_count', 'last_activity_time']]
        .drop_duplicates(subset=['url', 'repo_maintainer'])
        .assign(funding_renamed_or_archived=True)
    )

    _df = (
        _df_filtered
        .groupby(['repo_maintainer', 'is_maintainer_in_crypto_ecosystems'], as_index=False)
        .agg({
            'contributor_count': 'max',
            'star_count': 'max',
            'fork_count': 'max',
            'url': 'unique',
        })
        .sort_values(by='contributor_count', ascending=False)
        .reset_index(drop=True)
    )

    mo.vstack([
        mo.md(f"**Count:** {_num_repos:,.0f} repos"),
        mo.ui.table(_df, show_column_summaries=False, show_data_types=False)
    ])
    return (funding_part_d_renamed_archived,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 2. Package dependencies with high Ethereum alignment

    This query gives us another 6000 repos to evaluate. To qualify, the repo must have a package imported by at least 10 repos already in the Ethereum ecosystem AND have a `centrality` score above the most popular dependency in all of OSS Directory.


    ```sql
    WITH baseline AS (
      SELECT ethereum_centrality_score AS threshold
      FROM int_ddp_package_centrality
      ORDER BY all_dependent_repos DESC
      LIMIT 1
    ),
    repo_alignment AS (
      SELECT
        artifact_id,
        repo_maintainer,
        repo_name,
        num_packages,
        ethereum_dependent_repos,
        all_dependent_repos,
        ethereum_centrality_score
      FROM int_ddp_package_centrality
      --CROSS JOIN baseline
      WHERE
        NOT is_ethereum
        AND ethereum_centrality_score > 0.5
        AND ethereum_dependent_repos >= 10
        AND repo_maintainer NOT IN (
            'vercel',
            'nextjs',
            'sindresorhus',
            'jshttp',
            'npm',
            'chalk',
            'ljharb',
            'isaacs',
            'pillarjs',
            'inspect-js',
            'qix-',
            'jsdom',
            'yargs',
            'expressjs',
            'nodejs',
            'juliangruber',
        	'mafintosh',
            'chaijs',
            'level',
            'websockets',
            'browserify',
            'form-data',
            'jprichardson',
            'salesforce',
            'jslicense',
            'mochajs',
            'handlebars-lang',
            'getsentry',
            'node-modules',
            'ts-essentials',
            'graphql',
            'es-shims',
            'gulpjs'
        )
      ORDER BY ethereum_centrality_score DESC
    ),
    ce_check AS (
      SELECT
        ra.artifact_id,
        (ce.artifact_id IS NOT NULL) AS is_in_crypto_ecosystems,
        (ce_maintainer.artifact_id IS NOT NULL) AS is_maintainer_in_crypto_ecosystems
      FROM repo_alignment AS ra
      LEFT JOIN oso.int_artifacts_by_project_in_crypto_ecosystems AS ce
        ON ra.artifact_id = ce.artifact_id
        AND ce.project_source = 'CRYPTO_ECOSYSTEMS'
        AND ce.project_namespace = 'eco'
      LEFT JOIN oso.int_artifacts_by_project_in_crypto_ecosystems AS ce_maintainer
        ON ra.repo_maintainer = ce_maintainer.artifact_namespace
        AND ce_maintainer.project_source = 'CRYPTO_ECOSYSTEMS'
        AND ce_maintainer.project_namespace = 'eco'
    ),
    last_update AS (
      SELECT
        artifact_id,
        MAX(last_commit_time) AS last_commit_time
      FROM int_first_last_commit_to_github_repository
      JOIN ce_check USING artifact_id
      GROUP BY 1
    )

    SELECT DISTINCT
      ra.repo_maintainer,
      CONCAT('https://github.com/', ra.repo_maintainer, '/', ra.repo_name) AS url,
      ce.is_in_crypto_ecosystems,
      ce.is_maintainer_in_crypto_ecosystems,
      (gu.artifact_id IS NOT NULL) AS is_personal_repo,
      ra.num_packages,
      ra.ethereum_dependent_repos,
      ra.all_dependent_repos,
      ra.ethereum_centrality_score,
      lu.last_commit_time
    FROM repo_alignment AS ra
    JOIN ce_check AS ce USING artifact_id
    JOIN last_update AS lu USING artifact_id
    LEFT JOIN int_github_users AS gu
      ON ra.repo_maintainer = gu.artifact_name
    ORDER BY ra.ethereum_centrality_score DESC
    ```

    Here is the full list of repos:
    """)
    return


@app.cell
def _(mo, pyoso_db_conn):
    df_packages = mo.sql(
        f"""
        WITH baseline AS (
          SELECT ethereum_centrality_score AS threshold
          FROM int_ddp_package_centrality
          ORDER BY all_dependent_repos DESC
          LIMIT 1
        ),
        repo_alignment AS (
          SELECT
            artifact_id,
            repo_maintainer,
            repo_name,
            num_packages,
            ethereum_dependent_repos,
            all_dependent_repos,
            ethereum_centrality_score
          FROM int_ddp_package_centrality
          --CROSS JOIN baseline
          WHERE
            NOT is_ethereum
            AND ethereum_centrality_score > 0.5
            AND ethereum_dependent_repos >= 10
            AND repo_maintainer NOT IN (
                'vercel',
                'nextjs',
                'sindresorhus',
                'jshttp',
                'npm',
                'chalk',
                'ljharb',
                'isaacs',
                'pillarjs',
                'inspect-js',
                'qix-',
                'jsdom',
                'yargs',
                'expressjs',
                'nodejs',
                'juliangruber',
            	'mafintosh',
                'chaijs',
                'level',
                'websockets',
                'browserify',
                'form-data',
                'jprichardson',
                'salesforce',
                'jslicense',
                'mochajs',
                'handlebars-lang',
                'getsentry',
                'node-modules',
                'ts-essentials',
                'graphql',
                'es-shims',
                'gulpjs'   
            )
          ORDER BY ethereum_centrality_score DESC
        ),
        ce_check AS (
          SELECT
            ra.artifact_id,
            (ce.artifact_id IS NOT NULL) AS is_in_crypto_ecosystems,
            (ce_maintainer.artifact_id IS NOT NULL) AS is_maintainer_in_crypto_ecosystems
          FROM repo_alignment AS ra
          LEFT JOIN oso.int_artifacts_by_project_in_crypto_ecosystems AS ce
            ON ra.artifact_id = ce.artifact_id
            AND ce.project_source = 'CRYPTO_ECOSYSTEMS'
            AND ce.project_namespace = 'eco'
          LEFT JOIN oso.int_artifacts_by_project_in_crypto_ecosystems AS ce_maintainer
            ON ra.repo_maintainer = ce_maintainer.artifact_namespace
            AND ce_maintainer.project_source = 'CRYPTO_ECOSYSTEMS'
            AND ce_maintainer.project_namespace = 'eco'
        ),
        last_update AS (
          SELECT
            artifact_id,
            MAX(last_commit_time) AS last_commit_time
          FROM int_first_last_commit_to_github_repository
          JOIN ce_check USING artifact_id
          GROUP BY 1
        )

        SELECT DISTINCT
          ra.repo_maintainer,
          CONCAT('https://github.com/', ra.repo_maintainer, '/', ra.repo_name) AS url,
          ce.is_in_crypto_ecosystems,
          ce.is_maintainer_in_crypto_ecosystems,
          (gu.artifact_id IS NOT NULL) AS is_personal_repo,
          ra.num_packages,
          ra.ethereum_dependent_repos,
          ra.all_dependent_repos,
          ra.ethereum_centrality_score,
          lu.last_commit_time
        FROM repo_alignment AS ra
        JOIN ce_check AS ce USING artifact_id
        JOIN last_update AS lu USING artifact_id
        LEFT JOIN int_github_users AS gu
          ON ra.repo_maintainer = gu.artifact_name
        ORDER BY ra.ethereum_centrality_score DESC
        """,
        engine=pyoso_db_conn
    )
    return (df_packages,)


@app.cell
def _(mo):
    mo.md(r"""
    For reference, here is the most popular dependency among all projects in OSS Directory:
    """)
    return


@app.cell
def _(int_ddp_package_centrality, mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT *
        FROM int_ddp_package_centrality
        ORDER BY all_dependent_repos DESC
        LIMIT 1
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Part A: Popular packages in Crypto Ecosystems (but not Ethereum)

    This table shows repositories that are popular among Ethereum builders (high Ethereum centrality score and dependent repos) but are **not** classified as part of the Ethereum ecosystem. These repos are currently tracked in Crypto Ecosystems and are active (last commit since 2025-01-01). The table is grouped by maintainer and personal repo status, showing aggregated package counts and dependency metrics.
    """)
    return


@app.cell
def _(df_packages, mo):
    _df_filtered = df_packages[
        (df_packages['is_in_crypto_ecosystems'] == True)
        & (df_packages['last_commit_time'] >= '2025-01-01')
    ]
    _num_repos = len(_df_filtered)

    # Create flagged dataframe for consolidation
    packages_part_a_crypto_ecosystems = (
        _df_filtered[['url', 'repo_maintainer', 'last_commit_time']]
        .drop_duplicates(subset=['url', 'repo_maintainer'])
        .assign(packages_crypto_ecosystems_not_ethereum=True)
    )

    _df = (
        _df_filtered
        .groupby(['repo_maintainer', 'is_personal_repo'], as_index=False)
        .agg({
            'num_packages': 'sum',
            'ethereum_dependent_repos': 'sum',
            'all_dependent_repos': 'sum',
            'url': 'unique',
        })
        .sort_values(by='ethereum_dependent_repos', ascending=False)
        .reset_index(drop=True)
    )

    mo.vstack([
        mo.md(f"**Count:** {_num_repos:,.0f} repos"),
        mo.ui.table(_df, show_column_summaries=False, show_data_types=False)
    ])
    return (packages_part_a_crypto_ecosystems,)


@app.cell
def _(mo):
    mo.md(r"""
    ### Part B: Popular packages not in any Crypto Ecosystem

    This table shows repositories that are popular among Ethereum builders (high Ethereum centrality score and dependent repos) but are **not** currently tracked in any Crypto Ecosystem. These repos are active (last commit since 2025-01-01). The table is grouped by maintainer and personal repo status, showing aggregated package counts and dependency metrics.
    """)
    return


@app.cell
def _(df_packages, mo):
    _df_filtered = df_packages[
        (df_packages['is_in_crypto_ecosystems'] == False)
        & (df_packages['last_commit_time'] >= '2025-01-01')
    ]
    _num_repos = len(_df_filtered)

    # Create flagged dataframe for consolidation
    packages_part_b_no_crypto_ecosystems = (
        _df_filtered[['url', 'repo_maintainer', 'last_commit_time']]
        .drop_duplicates(subset=['url', 'repo_maintainer'])
        .assign(packages_no_crypto_ecosystems=True)
    )

    _df = (
        _df_filtered
        .groupby(['repo_maintainer', 'is_personal_repo'], as_index=False)
        .agg({
            'num_packages': 'sum',
            'ethereum_dependent_repos': 'sum',
            'all_dependent_repos': 'sum',
            'url': 'unique',
        })
        .sort_values(by='ethereum_dependent_repos', ascending=False)
        .reset_index(drop=True)
    )

    mo.vstack([
        mo.md(f"**Count:** {_num_repos:,.0f} repos"),
        mo.ui.table(_df, show_column_summaries=False, show_data_types=False)
    ])
    return (packages_part_b_no_crypto_ecosystems,)


@app.cell
def _(mo):
    mo.md(r"""
    ### Part C: Older popular packages not in any Crypto Ecosystem

    This table shows **older repositories** (last commit between 2023-01-01 and 2025-01-01) that are popular among Ethereum builders (at least 100 Ethereum-dependent repos) but are **not** currently tracked in any Crypto Ecosystem. These may represent legacy or archived projects that were historically important. The table is grouped by maintainer and personal repo status, showing aggregated package counts and dependency metrics.
    """)
    return


@app.cell
def _(df_packages, mo):
    _df_filtered = df_packages[
        (df_packages['is_in_crypto_ecosystems'] == False)
        & (df_packages['last_commit_time'] < '2025-01-01')
        & (df_packages['last_commit_time'] >= '2023-01-01')
        & (df_packages['ethereum_dependent_repos'] >= 100)
    ]
    _num_repos = len(_df_filtered)

    # Create flagged dataframe for consolidation
    packages_part_c_older_no_crypto_ecosystems = (
        _df_filtered[['url', 'repo_maintainer', 'last_commit_time']]
        .drop_duplicates(subset=['url', 'repo_maintainer'])
        .assign(packages_older_no_crypto_ecosystems=True)
    )

    _df = (
        _df_filtered
        .groupby(['repo_maintainer', 'is_personal_repo'], as_index=False)
        .agg({
            'num_packages': 'sum',
            'ethereum_dependent_repos': 'sum',
            'all_dependent_repos': 'sum',
            'url': 'unique',
        })
        .sort_values(by='ethereum_dependent_repos', ascending=False)
        .reset_index(drop=True)
    )

    mo.vstack([
        mo.md(f"**Count:** {_num_repos:,.0f} repos"),
        mo.ui.table(_df, show_column_summaries=False, show_data_types=False)
    ])
    return (packages_part_c_older_no_crypto_ecosystems,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 3. Page-rank style algo results over the complete dependency graph

    This query returns a pre-computed shortlist, that we filter a bit more to only include projects with more than 1 contributor. In total, this gives us another ~18K repos to consider.


    ```sql
    SELECT
      repo_maintainer,
      url,
      is_personal_repo,
      is_in_crypto_ecosystems,
      is_in_lineage_family,
      is_maintainer_in_crypto_ecosystems,
      last_commit_time,
      contributor_count,
      final_score
    FROM int_ddp_repo_discovery_v0_shortlist
    WHERE contributor_count > 1
    ORDER BY final_score DESC
    ```

    Here is the full list of repos:
    """)
    return


@app.cell
def _(int_ddp_repo_discovery_v0_shortlist, mo, pyoso_db_conn):
    df_repo_rank = mo.sql(
        f"""
        SELECT
          repo_maintainer,
          url,
          is_personal_repo,
          is_in_crypto_ecosystems,
          is_in_lineage_family,
          is_maintainer_in_crypto_ecosystems,    
          last_commit_time,
          contributor_count,
          final_score
        FROM int_ddp_repo_discovery_v0_shortlist
        WHERE contributor_count > 1
        ORDER BY final_score DESC
        """,
        engine=pyoso_db_conn
    )
    return (df_repo_rank,)


@app.cell
def _(mo):
    mo.md(r"""
    The complete, unfiltered list of repos included in the graph is more than 18M...
    """)
    return


@app.cell
def _(int_ddp_repo_discovery_v0, mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT COUNT(DISTINCT repo_artifact_id) AS num_repos FROM int_ddp_repo_discovery_v0
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Part A: High-ranking repos from organizations not in Crypto Ecosystems

    This table shows repositories that rank highly in the PageRank-style dependency graph algorithm. These repos are from organizations that are **not** currently tracked in Crypto Ecosystems, are active (last commit since 2025-01-01), and are organizational repos (not personal). The table is grouped by maintainer, showing the maximum final score and contributor count across all repos from each maintainer.
    """)
    return


@app.cell
def _(df_repo_rank, mo):
    _df_filtered = df_repo_rank[
        (df_repo_rank['is_in_crypto_ecosystems'] == False)
        & (df_repo_rank['is_maintainer_in_crypto_ecosystems'] == False)
        & (df_repo_rank['last_commit_time'] >= '2025-01-01')
        & (df_repo_rank['is_personal_repo'] == False)
    ]
    _num_repos = len(_df_filtered)

    # Create flagged dataframe for consolidation
    pagerank_part_a_orgs_not_crypto = (
        _df_filtered[['url', 'repo_maintainer', 'contributor_count', 'last_commit_time']]
        .drop_duplicates(subset=['url', 'repo_maintainer'])
        .assign(pagerank_orgs_not_crypto_ecosystems=True)
    )

    _df = (
        _df_filtered
        .groupby(['repo_maintainer', 'is_personal_repo'], as_index=False)
        .agg({
            'final_score': 'max',
            'contributor_count': 'max',
            'url': 'unique',
        })
        .sort_values(by='final_score', ascending=False)
        .reset_index(drop=True)
    )

    mo.vstack([
        mo.md(f"**Count:** {_num_repos:,.0f} repos"),
        mo.ui.table(_df, show_column_summaries=False, show_data_types=False)
    ])
    return (pagerank_part_a_orgs_not_crypto,)


@app.cell
def _(mo):
    mo.md(r"""
    ### Part B: High-ranking repos from maintainers in Crypto Ecosystems

    This table shows repositories that rank highly in the PageRank-style dependency graph algorithm. These repos are **not** currently tracked in Crypto Ecosystems, but their maintainers **are** tracked. These repos are active (last commit since 2025-01-01). The table is grouped by maintainer, showing the maximum final score and contributor count across all repos from each maintainer.
    """)
    return


@app.cell
def _(df_repo_rank, mo):
    _df_filtered = df_repo_rank[
        (df_repo_rank['is_in_crypto_ecosystems'] == False)
        & (df_repo_rank['is_maintainer_in_crypto_ecosystems'] == True)
        & (df_repo_rank['last_commit_time'] >= '2025-01-01')
    ]
    _num_repos = len(_df_filtered)

    # Create flagged dataframe for consolidation
    pagerank_part_b_maintainers_in_crypto = (
        _df_filtered[['url', 'repo_maintainer', 'contributor_count', 'last_commit_time']]
        .drop_duplicates(subset=['url', 'repo_maintainer'])
        .assign(pagerank_maintainers_in_crypto=True)
    )

    _df = (
        _df_filtered
        .groupby(['repo_maintainer', 'is_personal_repo'], as_index=False)
        .agg({
            'final_score': 'max',
            'contributor_count': 'max',
            'url': 'unique',
        })
        .sort_values(by='final_score', ascending=False)
        .reset_index(drop=True)
    )

    mo.vstack([
        mo.md(f"**Count:** {_num_repos:,.0f} repos"),
        mo.ui.table(_df, show_column_summaries=False, show_data_types=False)
    ])
    return (pagerank_part_b_maintainers_in_crypto,)


@app.cell
def _(mo):
    mo.md(r"""
    # Consolidated Repository List

    This section consolidates all repositories identified by the three detection mechanisms into a single table. Each repository is listed with its maintainer and boolean flags indicating which detection mechanisms identified it.

    **Detection Mechanisms:**
    - **Funding**: Repository has received at least $5,000 in lifetime funding from Ethereum-aligned sources (Octant, Gitcoin, Optimism Retro Funding, etc.)
    - **Package Dependencies**: Repository has packages with high Ethereum alignment (centrality score > 0.5 and at least 10 Ethereum-dependent repos)
    - **PageRank Algorithm**: Repository ranks highly in the dependency graph PageRank-style algorithm
    """)
    return


@app.cell
def _(
    funding_part_a_crypto_ecosystems,
    funding_part_b_no_crypto_ecosystems,
    funding_part_c_mixed_ecosystem,
    funding_part_d_renamed_archived,
    packages_part_a_crypto_ecosystems,
    packages_part_b_no_crypto_ecosystems,
    packages_part_c_older_no_crypto_ecosystems,
    pagerank_part_a_orgs_not_crypto,
    pagerank_part_b_maintainers_in_crypto,
    pd,
):
    # Collect all dataframes created in individual sections
    all_parts = [
        funding_part_a_crypto_ecosystems,
        funding_part_b_no_crypto_ecosystems,
        funding_part_c_mixed_ecosystem,
        funding_part_d_renamed_archived,
        packages_part_a_crypto_ecosystems,
        packages_part_b_no_crypto_ecosystems,
        packages_part_c_older_no_crypto_ecosystems,
        pagerank_part_a_orgs_not_crypto,
        pagerank_part_b_maintainers_in_crypto,
    ]

    # Get all unique repo/maintainer combinations with metadata
    # Collect all data with metadata fields
    all_data = []
    for df_part in all_parts:
        # Get all columns except the flag column
        flag_col = [_col for _col in df_part.columns if _col not in ['url', 'repo_maintainer', 'contributor_count', 'last_activity_time', 'last_commit_time'] and _col != 'last_commit_date']
        if len(flag_col) > 0:
            flag_col = flag_col[0]
        else:
            flag_col = None
        # Select relevant columns
        cols_to_select = ['url', 'repo_maintainer']
        if flag_col:
            cols_to_select.append(flag_col)
        if 'contributor_count' in df_part.columns:
            cols_to_select.append('contributor_count')
        if 'last_activity_time' in df_part.columns:
            cols_to_select.append('last_activity_time')
        if 'last_commit_time' in df_part.columns:
            cols_to_select.append('last_commit_time')
        if 'last_commit_date' in df_part.columns:
            cols_to_select.append('last_commit_date')
        all_data.append(df_part[cols_to_select])

    # Concatenate all data
    df_all = pd.concat(all_data, ignore_index=True)

    # Group by url and repo_maintainer to aggregate metadata
    # Build aggregation dictionary - only aggregate specific columns we know about
    agg_dict = {}
    bool_cols = []

    # Collect all boolean flag columns from all parts
    for df_part in all_parts:
        flag_col = [_col for _col in df_part.columns if _col not in ['url', 'repo_maintainer', 'contributor_count', 'last_activity_time', 'last_commit_time', 'last_commit_date']]
        if len(flag_col) > 0:
            flag_col = flag_col[0]
            if flag_col not in bool_cols:
                bool_cols.append(flag_col)

    # Set aggregation functions only for columns we want to aggregate
    # Boolean flags - use max to get True if any part has it
    for _col in bool_cols:
        if _col in df_all.columns:
            agg_dict[_col] = 'max'

    # Contributor count - get maximum
    if 'contributor_count' in df_all.columns:
        agg_dict['contributor_count'] = 'max'

    # Date fields - get most recent
    if 'last_activity_time' in df_all.columns:
        agg_dict['last_activity_time'] = 'max'
        df_all['last_activity_time'] = pd.to_datetime(df_all['last_activity_time'])
    if 'last_commit_time' in df_all.columns:
        agg_dict['last_commit_time'] = 'max'
        df_all['last_commit_time'] = pd.to_datetime(df_all['last_commit_time'])
    if 'last_commit_date' in df_all.columns:
        agg_dict['last_commit_date'] = 'max'
        df_all['last_commit_date'] = pd.to_datetime(df_all['last_commit_date'])

    # Aggregate only the columns we specified
    df_consolidated = (
        df_all
        .groupby(['url', 'repo_maintainer'], as_index=False)
        .agg(agg_dict)
        .sort_values(by=['repo_maintainer', 'url'])
        .reset_index(drop=True)
    )

    # Normalize date fields - combine last_activity_time and last_commit_time into last_commit_date
    # Handle timezone-aware and timezone-naive datetimes
    if 'last_activity_time' in df_consolidated.columns and 'last_commit_time' in df_consolidated.columns:
        # Convert both to datetime, handling NaN and timezones
        _last_activity = pd.to_datetime(df_consolidated['last_activity_time'], errors='coerce')
        _last_commit = pd.to_datetime(df_consolidated['last_commit_time'], errors='coerce')

        # Remove timezone info to make them comparable (convert to naive)
        if _last_activity.dt.tz is not None:
            _last_activity = _last_activity.dt.tz_localize(None)
        if _last_commit.dt.tz is not None:
            _last_commit = _last_commit.dt.tz_localize(None)

        # Take max, ignoring NaT (NaN for datetime)
        df_consolidated['last_commit_date'] = pd.concat([_last_activity, _last_commit], axis=1).max(axis=1)
        df_consolidated = df_consolidated.drop(columns=['last_activity_time', 'last_commit_time'])
    elif 'last_activity_time' in df_consolidated.columns:
        _last_activity = pd.to_datetime(df_consolidated['last_activity_time'], errors='coerce')
        if _last_activity.dt.tz is not None:
            _last_activity = _last_activity.dt.tz_localize(None)
        df_consolidated['last_commit_date'] = _last_activity
        df_consolidated = df_consolidated.drop(columns=['last_activity_time'])
    elif 'last_commit_time' in df_consolidated.columns:
        _last_commit = pd.to_datetime(df_consolidated['last_commit_time'], errors='coerce')
        if _last_commit.dt.tz is not None:
            _last_commit = _last_commit.dt.tz_localize(None)
        df_consolidated['last_commit_date'] = _last_commit
        df_consolidated = df_consolidated.drop(columns=['last_commit_time'])

    # Convert boolean columns (they might be numeric from max aggregation)
    for _col in bool_cols:
        if _col in df_consolidated.columns:
            df_consolidated[_col] = df_consolidated[_col].astype(bool)

    # Reorder columns: url, repo_maintainer, contributor_count, last_commit_date, then all boolean flags
    metadata_cols = []
    if 'contributor_count' in df_consolidated.columns:
        metadata_cols.append('contributor_count')
    if 'last_commit_date' in df_consolidated.columns:
        metadata_cols.append('last_commit_date')

    other_cols = [_col for _col in df_consolidated.columns if _col not in ['url', 'repo_maintainer'] + metadata_cols]
    df_consolidated = df_consolidated[['url', 'repo_maintainer'] + metadata_cols + other_cols]
    return (df_consolidated,)


@app.cell
def _(mo):
    mo.md(r"""
    ### Consolidated Repository List

    This table shows all unique repositories identified by one or more detection mechanisms. Each row represents a repository with its maintainer and boolean flags indicating which specific subquery/part detected it.
    """)
    return


@app.cell
def _(df_consolidated):
    mo.ui.table(df_consolidated, show_column_summaries=False, show_data_types=False)
    return


@app.cell
def _(df_consolidated, mo):
    _num_repos = len(df_consolidated)

    # Count by mechanism
    funding_cols = [_col for _col in df_consolidated.columns if _col.startswith('funding_')]
    packages_cols = [_col for _col in df_consolidated.columns if _col.startswith('packages_')]
    pagerank_cols = [_col for _col in df_consolidated.columns if _col.startswith('pagerank_')]

    _num_by_funding = df_consolidated[funding_cols].any(axis=1).sum()
    _num_by_packages = df_consolidated[packages_cols].any(axis=1).sum()
    _num_by_pagerank = df_consolidated[pagerank_cols].any(axis=1).sum()

    # Count by specific parts
    _num_by_part = {}
    for _col in df_consolidated.columns:
        if _col not in ['url', 'repo_maintainer', 'contributor_count', 'last_commit_date']:
            _num_by_part[_col] = df_consolidated[_col].sum()

    # Count repos detected by multiple mechanisms
    _num_by_multiple_mechanisms = (
        df_consolidated[funding_cols].any(axis=1).astype(int) + 
        df_consolidated[packages_cols].any(axis=1).astype(int) + 
        df_consolidated[pagerank_cols].any(axis=1).astype(int)
    ).gt(1).sum()

    # Create stats widgets for each detection flag
    # Funding mechanism
    stat_funding_a = mo.stat(
        label="Funding: Part A",
        bordered=True,
        value=f"{_num_by_part.get('funding_crypto_ecosystems_not_ethereum', 0):,.0f}",
        caption="Crypto Ecosystems (not Ethereum)"
    )
    stat_funding_b = mo.stat(
        label="Funding: Part B",
        bordered=True,
        value=f"{_num_by_part.get('funding_maintainer_no_crypto_ecosystems', 0):,.0f}",
        caption="Maintainer no Crypto Ecosystems"
    )
    stat_funding_c = mo.stat(
        label="Funding: Part C",
        bordered=True,
        value=f"{_num_by_part.get('funding_mixed_ecosystem_presence', 0):,.0f}",
        caption="Mixed ecosystem presence"
    )
    stat_funding_d = mo.stat(
        label="Funding: Part D",
        bordered=True,
        value=f"{_num_by_part.get('funding_renamed_or_archived', 0):,.0f}",
        caption="Renamed or archived"
    )

    # Package Dependencies mechanism
    stat_packages_a = mo.stat(
        label="Packages: Part A",
        bordered=True,
        value=f"{_num_by_part.get('packages_crypto_ecosystems_not_ethereum', 0):,.0f}",
        caption="Crypto Ecosystems (not Ethereum)"
    )
    stat_packages_b = mo.stat(
        label="Packages: Part B",
        bordered=True,
        value=f"{_num_by_part.get('packages_no_crypto_ecosystems', 0):,.0f}",
        caption="No Crypto Ecosystems"
    )
    stat_packages_c = mo.stat(
        label="Packages: Part C",
        bordered=True,
        value=f"{_num_by_part.get('packages_older_no_crypto_ecosystems', 0):,.0f}",
        caption="Older, no Crypto Ecosystems"
    )

    # PageRank mechanism
    stat_pagerank_a = mo.stat(
        label="PageRank: Part A",
        bordered=True,
        value=f"{_num_by_part.get('pagerank_orgs_not_crypto_ecosystems', 0):,.0f}",
        caption="Orgs not in Crypto Ecosystems"
    )
    stat_pagerank_b = mo.stat(
        label="PageRank: Part B",
        bordered=True,
        value=f"{_num_by_part.get('pagerank_maintainers_in_crypto', 0):,.0f}",
        caption="Maintainers in Crypto Ecosystems"
    )

    # Summary stats
    stat_total = mo.stat(
        label="Total Repos",
        bordered=True,
        value=f"{_num_repos:,.0f}",
        caption="Unique repositories"
    )
    stat_multiple = mo.stat(
        label="Multiple Mechanisms",
        bordered=True,
        value=f"{_num_by_multiple_mechanisms:,.0f}",
        caption="Detected by 2+ mechanisms"
    )

    mo.vstack([
        mo.md("### Detection Mechanism Summary"),
        mo.hstack([stat_total, stat_multiple], widths="equal", gap=2),
        mo.md("### Funding Mechanism"),
        mo.hstack([stat_funding_a, stat_funding_b, stat_funding_c, stat_funding_d], widths="equal", gap=1),
        mo.md("### Package Dependencies Mechanism"),
        mo.hstack([stat_packages_a, stat_packages_b, stat_packages_c], widths="equal", gap=1),
        mo.md("### PageRank Mechanism"),
        mo.hstack([stat_pagerank_a, stat_pagerank_b], widths="equal", gap=1),
        mo.md("### Full Repository List"),
        mo.ui.table(df_consolidated, show_column_summaries=False, show_data_types=False)
    ])
    return


@app.cell
def _():
    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    return (pd,)


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
