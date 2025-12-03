"""
Dependency Graph Analysis for GG24 Deep Funding

This Marimo notebook analyzes dependency data collected from 98 seed repositories.

Data Collection Process:
1. GitHub API (Primary): Fetch dependencies using GraphQL API
2. Paginated API (Fallback): For large repos, use pagination with retries
3. Local Parsing (Last Resort): Clone and parse manifest files locally

See README.md for detailed documentation.
"""

import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")

with app.setup:
    # Initialization code that runs before all other cells
    pass


@app.cell
def setup_pyoso():
    import marimo as mo
    from pyoso import Client
    import pandas as pd
    client = Client()
    try:
        pyoso_db_conn = client.dbapi_connection()
    except Exception:
        pyoso_db_conn = None
    return mo, pd, pyoso_db_conn


@app.cell
def about_app(mo):
    mo.vstack([
        mo.md("""
        # GG24 Dependency Graph Analysis
        <small>Author: <span style="background-color:#f0f0f0;padding:2px 4px;border-radius:3px;">OSO Team</span>
        · Last Updated: <span style="background-color:#f0f0f0;padding:2px 4px;border-radius:3px;">Dec 2025</span></small>
        """),
        mo.md("""
        This notebook analyzes dependency data for 98 seed repositories from the GG24 Deep Funding program.
        It builds a comprehensive dependency graph showing which repositories depend on which packages and repositories.
        """),
        mo.accordion({
            "<b>Click to see details</b>": mo.accordion({
                "Data Collection": """
                **Three-tier approach:**
                - **GitHub API (Primary)**: GraphQL queries for 89/98 repos
                - **Paginated API (Fallback)**: For large repos with timeouts
                - **Local Parsing (Last Resort)**: Clone and parse manifests for 7 problematic repos

                **Results**: 54,429 dependencies from 96 repos (2 have no standard manifests)
                """,
                "Cleanup Logic": """
                **Priority-based deduplication:**
                1. Transitive-only NPM packages (deprioritized)
                2. Parser direct dependencies
                3. Parser transitive dependencies
                4. OSO direct dependencies
                5. OSO indirect dependencies
                6. Unknown relationships

                **Filters:**
                - Remove GitHub Actions (not traditional dependencies)
                - Remove self-dependencies (same organization)
                - Normalize package managers (CARGO → RUST, etc.)
                """,
                "JSON Export": """
                **Incremental update strategy:**
                - If repo EXISTS in upstream with >1 dependency → KEEP existing data
                - If repo is NEW or has ≤1 dependency → USE our collected data
                - Prefer non-NPM for multi-language repos (more stable)

                This ensures existing curated data is preserved while adding new repos.
                """,
                "Further Resources": """
                - [README.md](./README.md) - Detailed process documentation
                - [Pyoso Docs](https://docs.opensource.observer/docs/get-started/python)
                - [Marimo Docs](https://docs.marimo.io/)
                """
            })
        })
    ])
    return


@app.cell(hide_code=True)
def _():
    stringify = lambda arr: "'" + "','".join(arr) + "'"
    return (stringify,)


@app.cell(hide_code=True)
def load_seed_repos(pd):
    _csv_url = "https://raw.githubusercontent.com/davidgasquez/gg24-deepfunding-market-weights/refs/heads/main/data/phase_2/weights/elo.csv"
    _df = pd.read_csv(_csv_url)
    seed_repos = list(_df['item'].str.lower())
    return (seed_repos,)


@app.cell(hide_code=True)
def fetch_seed_repos_from_oso(mo, pyoso_db_conn, seed_repos, stringify):
    seed_repos_oso = mo.sql(
        f"""
        SELECT *
        FROM int_repositories__ossd
        WHERE name_with_owner IN ({stringify(seed_repos)})
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (seed_repos_oso,)


@app.cell
def extract_seed_repo_ids(seed_repos_oso, seed_repos):
    print("Repos not in OSO currently:")
    _oso_names = seed_repos_oso['name_with_owner'].unique()
    seed_repo_ids = seed_repos_oso['artifact_id'].unique()
    for _r in sorted(set(seed_repos).difference(set(_oso_names))):
        print("-", _r)
    return (seed_repo_ids,)


@app.cell(hide_code=True)
def fetch_deps_from_oso(mo, seed_repo_ids, pyoso_db_conn, stringify):
    deps_oso = mo.sql(
        f"""
        WITH seed_repos_to_owners AS (
          SELECT DISTINCT
            dependent_artifact_id,
            package_owner_artifact_id
          FROM int_code_dependencies
          WHERE dependent_artifact_id IN ({stringify(seed_repo_ids)})
            AND dependent_artifact_source='GITHUB'
        ),
        indirect_pairs AS (
          SELECT DISTINCT
            sr2o.dependent_artifact_id AS dependent_artifact_id,
            cd.package_owner_artifact_id AS package_owner_artifact_id
          FROM seed_repos_to_owners sr2o
          JOIN int_code_dependencies cd
            ON cd.dependent_artifact_id=sr2o.package_owner_artifact_id
        )
        SELECT
          CONCAT(d.dependent_artifact_namespace, '/', d.dependent_artifact_name) AS seed_repo,
          CONCAT(d.package_owner_artifact_namespace, '/', d.package_owner_artifact_name) AS dependent_repo,
          d.package_artifact_source,  
          d.package_artifact_name,
          CASE
            WHEN i.dependent_artifact_id IS NOT NULL THEN 'indirect'
            ELSE 'direct'
          END AS dependency_type
        FROM int_code_dependencies d
        JOIN seed_repos_to_owners s
          ON d.dependent_artifact_id=s.dependent_artifact_id
         AND d.package_owner_artifact_id=s.package_owner_artifact_id
        LEFT JOIN indirect_pairs i
          ON i.dependent_artifact_id=d.dependent_artifact_id
         AND i.package_owner_artifact_id=d.package_owner_artifact_id
        WHERE d.dependent_artifact_id IN ({stringify(seed_repo_ids)})
        """,
        engine=pyoso_db_conn
    )
    return (deps_oso,)


@app.cell
def load_parsed_deps(pd):
    # Load raw CSV data
    deps_raw = pd.read_csv("data/dependencies.csv")

    # Keep only relevant columns and deduplicate
    deps_raw = deps_raw[['repo_name', 'package_name', 'package_manager', 'relationship']].drop_duplicates()

    # Normalize package names (lowercase for consistent matching)
    deps_raw['package_name'] = deps_raw['package_name'].str.lower()

    # Normalize package manager names
    deps_raw['package_manager'] = deps_raw['package_manager'].apply(
        lambda x: {'CARGO': 'RUST', 'RUBYGEMS': 'GEM'}.get(x, x)
    )

    package_names = list(deps_raw['package_name'].unique())

    return deps_raw, package_names


@app.cell
def map_packages_to_owners(mo, package_names, pyoso_db_conn, stringify):
    packages_with_owners = mo.sql(
        f"""
        SELECT DISTINCT
          CONCAT(package_owner_artifact_namespace, '/', package_owner_artifact_name) AS package_repo,
          package_artifact_name,
          package_artifact_source
        FROM package_owners_v0
        WHERE package_artifact_name IN ({stringify(package_names)})
        """,
        engine=pyoso_db_conn
    )
    return (packages_with_owners,)


@app.cell
def show_package_mapping(mo, packages_with_owners):
    mo.vstack([
        mo.md("### Package to Repository Mapping"),
        mo.md(f"Mapped **{len(packages_with_owners):,}** packages to their source repositories"),
        mo.ui.table(packages_with_owners.head(100))
    ])
    return


@app.cell
def join_deps_with_owners(packages_with_owners, deps_raw):
    deps_with_owners = deps_raw.merge(
        packages_with_owners,
        left_on=['package_name', 'package_manager'],
        right_on=['package_artifact_name', 'package_artifact_source'],
        how='left'
    )
    deps_with_owners = deps_with_owners[['repo_name', 'package_repo', 'package_manager', 'package_name', 'relationship']].drop_duplicates()

    # Remove GitHub Actions (not traditional dependencies)
    deps_with_owners = deps_with_owners[~deps_with_owners['package_manager'].isin(['ACTIONS'])]

    return (deps_with_owners,)


@app.cell
def identify_npm_transitive_only(deps_with_owners):
    # Find packages that have only one relationship type
    _npm = deps_with_owners[deps_with_owners['package_manager'] == 'NPM']
    _single_rel = _npm.groupby('package_name')['relationship'].nunique()
    _single_rel = _single_rel[_single_rel == 1].index

    # Filter to those that are only transitive
    npm_transitive_only = deps_with_owners[
        (deps_with_owners['package_manager'] == 'NPM')
        & (deps_with_owners['package_name'].isin(_single_rel))
        & (deps_with_owners['relationship'] == 'transitive')
    ]['package_name'].unique()

    return (npm_transitive_only,)


@app.cell
def merge_deps(deps_oso, deps_with_owners, pd, npm_transitive_only):
    # Prepare OSO data
    _oso = deps_oso.rename(columns={
        'seed_repo': 'repo_name',
        'dependent_repo': 'package_repo',
        'package_artifact_source': 'package_manager',
        'package_artifact_name': 'package_name',
        'dependency_type': 'relationship'
    }).copy()
    _oso['source'] = 'oso'

    # Prepare parser data
    _parser = deps_with_owners.copy()
    _parser['source'] = 'parser'

    # Combine both sources
    deps_merged = pd.concat([_oso, _parser], axis=0, ignore_index=True)

    # Label each dependency by priority
    def _labeler(source, relationship, manager, name):
        if manager == 'NPM' and name in npm_transitive_only:
            return '0 - transitive shortlist'
        if source == 'parser':
            if relationship == 'direct':
                return '1 - parser direct'
            if relationship == 'transitive':
                return '2 - parser transitive'
            if relationship == 'unknown':
                return '5 - unknown'
        if source == 'oso':
            if relationship == 'direct':
                return '3 - direct'
            if relationship == 'indirect':
                return '4 - unknown'

    deps_merged['label'] = deps_merged.apply(lambda x: _labeler(x['source'], x['relationship'], x['package_manager'], x['package_name']), axis=1)

    # Sort by priority and deduplicate (keeps first = highest priority)
    deps_merged.sort_values(by=['repo_name', 'package_manager', 'package_name', 'label'], inplace=True)
    deps_merged = deps_merged.drop_duplicates(keep='first', subset=['repo_name', 'package_manager', 'package_name'])

    deps_merged
    return (deps_merged,)


@app.cell
def build_repo_level_graph(deps_merged):
    deps_repo_level = deps_merged.copy()

    # Sort and deduplicate
    deps_repo_level = deps_repo_level.sort_values(by=['repo_name', 'package_repo', 'package_manager', 'label'])
    deps_repo_level = deps_repo_level.drop_duplicates(subset=['repo_name', 'package_repo', 'package_manager', 'label'], keep='first')

    # Keep only dependencies with known source repos
    deps_repo_level = deps_repo_level[~deps_repo_level['package_repo'].isna()]

    # Remove self-dependencies (same organization)
    deps_repo_level = deps_repo_level[(deps_repo_level['repo_name'].apply(lambda x: x.split('/')[0]) != deps_repo_level['package_repo'].apply(lambda x: x.split('/')[0]))]

    # Remove transitive-only packages
    deps_repo_level = deps_repo_level[deps_repo_level['label'] != '2 - parser transitive']
    deps_repo_level = deps_repo_level[deps_repo_level['label'] != '0 - transitive shortlist']

    deps_repo_level
    return (deps_repo_level,)


@app.cell
def check_missing_repos(deps_repo_level, seed_repos):
    _missing = set(seed_repos).difference(set(deps_repo_level['repo_name'].unique()))
    if _missing:
        print(f"Seed repos without dependencies: {len(_missing)}")
        for _r in sorted(_missing):
            print(f"  - {_r}")
    else:
        print("All seed repos have at least one dependency")
    return


@app.cell
def load_existing_graph():
    import requests
    _url = 'https://raw.githubusercontent.com/deepfunding/dependency-graph/refs/heads/main/datasets/gg24/seedReposWithDependencies.json'
    _response = requests.get(_url)
    graph_existing = _response.json()
    return (graph_existing,)


@app.cell
def build_final_graph(deps_repo_level, graph_existing, seed_repos):
    graph_final = {}

    for _seed in sorted(seed_repos):
        _url = 'https://github.com/' + _seed

        # Check if existing data has this repo with substantial dependencies
        _existing = graph_existing.get(_url, [])

        # PRESERVE existing data if it has >1 dependency
        if len(_existing) > 1:
            graph_final[_url] = sorted(_existing)
            continue

        # USE our collected data for new/incomplete repos
        _deps = deps_repo_level[deps_repo_level['repo_name'] == _seed]

        # If repo uses multiple package managers, prefer non-NPM
        _managers = _deps['package_manager'].unique()
        if len(_managers) > 1:
            _deps = _deps[_deps['package_manager'] != 'NPM']

        # Get unique dependency repos
        _dep_repos = _deps['package_repo'].unique()
        _dep_urls = ['https://github.com/' + x for x in _dep_repos]

        if len(_dep_urls) > 1:
            graph_final[_url] = sorted(_dep_urls)
        else:
            graph_final[_url] = []

    return (graph_final,)


@app.cell
def show_graph_stats(mo, graph_final):
    _repos_with_deps = sum(1 for v in graph_final.values() if len(v) > 0)
    _repos_without_deps = len(graph_final) - _repos_with_deps
    
    mo.vstack([
        mo.md("### Dependency Graph Statistics"),
        mo.hstack([
            mo.stat(label="Total Repos", value=f"{len(graph_final)}"),
            mo.stat(label="With Dependencies", value=f"{_repos_with_deps}"),
            mo.stat(label="Without Dependencies", value=f"{_repos_without_deps}"),
        ])
    ])
    return


@app.cell
def export_dependency_graph(graph_final, json):
    with open('data/seedReposWithDependencies.json', 'w') as _f:
        json.dump(graph_final, _f, indent=2)
    return


@app.cell
def export_seed_list(json, seed_repos):
    with open('data/seedRepos.json', 'w') as _f:
        json.dump(sorted(seed_repos), _f, indent=2)
    return


@app.cell
def _():
    import json
    return (json,)


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
