import marimo

__generated_with = "0.15.3"
app = marimo.App(width="full")


@app.cell
def setup_pyoso():
    import pyoso
    import marimo as mo
    client = pyoso.Client()
    pyoso_db_conn = client.dbapi_connection(force_without_pyodide=True)
    return client, mo


@app.cell
def _(mo):
    refresh_data = mo.ui.run_button(label="Refresh data")
    refresh_data
    return (refresh_data,)


@app.cell
def _(
    fetch_github_metrics_by_project,
    fetch_sdk_dependencies,
    mo,
    refresh_data,
):
    mo.stop(not refresh_data.value)

    df_projects = fetch_github_metrics_by_project()
    df_sdk_deps = fetch_sdk_dependencies()
    return


@app.cell
def _(fetch_dev_leaderboard, fetch_dev_projects):
    def analyze_funnel():
    
        df = fetch_dev_leaderboard()
        artifact_list = df['repo_id'].unique()
    
        df_labeled = fetch_dev_projects(artifact_list)
        df_labeled = df_labeled.groupby('repo_id').max()
        df_labeled["tags"] = df_labeled.apply(lambda row: ";".join([col.replace('in_','') for col in df_labeled.columns if row[col]]), axis=1)
        df_merged = df.set_index('repo_id').join(df_labeled[["tags"]])

        def label_project(tags, dev_url, repo_url):
            if not isinstance(tags, str):
                tags = ''
            if 'stylus' in tags:
                return 'Project (Stylus Sprint)'
            if '/offchainlabs/' in repo_url:
                return 'Offchain Labs'
            if 'solana' in tags:
                if ';' in tags:
                    return 'Project (EVM + Solana Ecosystems)'
                else:
                    return 'Project (Solana Ecosystem)'
            if 'arbitrum' in tags:
                return 'Project (Arbitrum Ecosystem)'
            if len(tags) > 1:
                return 'Project (EVM Ecosystem)'
            if dev_url in repo_url:
                return 'Personal Project'
            return 'Project (Other)'

        df_merged['project_type'] = df_merged.apply(lambda x: label_project(x['tags'], x['dev_url'], x['repo_url']), axis=1)

        return df_merged
    
        df_grouped = (
            df_merged
            .reset_index()
            .groupby(['repo_id', 'repo_owner', 'project_type'], as_index=False)
            .agg({
                'dev_id': 'nunique',
                'star_count': 'max',
                'num_commits': 'sum',
                'first_fork': 'min',    
            })
            .sort_values(by=['dev_id', 'star_count', 'num_commits'], ascending=False)
            .set_index('repo_id')
        )
    
    

    d = analyze_funnel()    
    return (d,)


@app.cell
def _(d):
    d.groupby(['repo_owner', 'project_type']).agg({
                'dev_id': 'nunique',
                'star_count': 'max',
                'num_commits': 'sum',
                'first_fork': 'min',
                'repo_url': lambda x: '; '.join(sorted(set(x)))
            })
    return


@app.cell
def _(d):
    d.head().to_dict(orient='records')
    return


@app.cell
def import_libraries():
    import pandas as pd
    from datetime import datetime, date, timedelta
    from functools import wraps
    return pd, wraps


@app.cell
def _():
    START_DATE = '2022-01-01'
    COLLECTION_NAME = 'arb-stylus'
    ECOSYSTEMS = [
        'arbitrum',
        'ethereum_virtual_machine_stack',
        'solana'
    ]
    return COLLECTION_NAME, ECOSYSTEMS, START_DATE


@app.cell
def _(pd, wraps):
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
    return parse_dates, stringify


@app.cell
def _(df_dev_leaderboard):
    df_dev_leaderboard
    return


@app.cell
def query_data(
    COLLECTION_NAME,
    ECOSYSTEMS,
    START_DATE,
    client,
    parse_dates,
    stringify,
):
    @parse_dates("date")
    def fetch_developer_ecosystems():
        return client.to_pandas(f"""
            SELECT
              sample_date AS date,
              projects_v1.display_name AS developer_ecosystem,
              amount
            FROM timeseries_metrics_by_project_v0
            JOIN metrics_v0 USING metric_id
            JOIN projects_v1 USING project_id
            WHERE
              metric_name = 'GITHUB_active_developers_monthly'
              AND sample_date >= DATE '{START_DATE}'
              AND project_source = 'CRYPTO_ECOSYSTEMS'
              AND project_namespace = 'eco'
              AND project_name IN ({stringify(ECOSYSTEMS)})
            ORDER BY 1,2  
            """)

    @parse_dates("date")
    def fetch_github_metrics_by_project():
        return client.to_pandas(f"""
            SELECT DISTINCT
              p.display_name AS display_name,
              p.project_name AS project_name,
              m.metric_name AS metric_name,
              ts.sample_date AS date,
              ts.amount AS amount
            FROM metrics_v0 m
            JOIN timeseries_metrics_by_project_v0 ts
              ON m.metric_id = ts.metric_id
            JOIN projects_v1 p
              ON p.project_id = ts.project_id
            JOIN projects_by_collection_v1 pc
              ON p.project_id = pc.project_id
            WHERE
              metric_name like 'GITHUB_%'
              AND ts.sample_date >= DATE '{START_DATE}'
              AND pc.collection_name = '{COLLECTION_NAME}'
        """)

    @parse_dates("date")
    def fetch_github_metrics_by_repo():
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
              AND ts.sample_date BETWEEN
                DATE_ADD('MONTH', -12, DATE_TRUNC('MONTH', current_date))
                AND DATE_TRUNC('MONTH', current_date)
        """)

    def fetch_sdk_dependencies():
        return client.to_pandas("""
            WITH stylus AS (
              SELECT DISTINCT
                package_artifact_id,
                package_owner_artifact_id
              FROM package_owners_v0
              WHERE
                package_owner_artifact_namespace = 'offchainlabs'
                AND package_owner_artifact_name = 'stylus-sdk-rs'
                AND package_artifact_name = 'stylus-sdk'
            )
            SELECT DISTINCT
              dependent_artifact_id AS artifact_id,
              dependent_artifact_namespace AS repo_owner,
              dependent_artifact_name AS repo_name
            FROM sboms_v0
            JOIN stylus USING package_artifact_id
            WHERE package_owner_artifact_id != dependent_artifact_id
            ORDER BY 1,2
        """)    

    @parse_dates("first_fork")
    def fetch_dev_leaderboard():
        return client.to_pandas(f"""
            WITH stylus AS (
              SELECT DISTINCT package_artifact_id
              FROM package_owners_v0
              WHERE
                package_owner_artifact_namespace = 'offchainlabs'
                AND package_owner_artifact_name = 'stylus-sdk-rs'
                AND package_artifact_name = 'stylus-sdk'
            ),
            example_repos AS (
              SELECT DISTINCT dependent_artifact_id
              FROM sboms_v0
              JOIN stylus USING package_artifact_id
              WHERE dependent_artifact_namespace = 'offchainlabs'
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
                AND time >= DATE '{START_DATE}'
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
              de.dev_id,
              de.repo_id,
              devs.dev_url,
              a.artifact_namespace AS repo_owner,
              a.artifact_url AS repo_url,
              devs.first_fork,
              de.num_commits,
              COALESCE(sc.star_count, 0) AS star_count,
              fr.artifact_url AS first_fork_repo_url
            FROM dev_events AS de
            JOIN devs ON de.dev_id = devs.dev_id
            JOIN int_artifacts__github AS a
              ON de.repo_id = a.artifact_id
            LEFT JOIN star_counts AS sc
              ON a.artifact_id = sc.repo_id
            JOIN repositories_v0 AS fr
              ON devs.forked_repo_id = fr.artifact_id
        """)

    def fetch_dev_projects(artifact_list):
        df = client.to_pandas(f"""
            WITH projects AS (
              SELECT DISTINCT
                artifact_id,
                project_id,
                project_name,
                project_source
              FROM artifacts_by_project_v1
              WHERE
                artifact_id IN ({stringify(artifact_list)})
                AND project_source IN ('OSS_DIRECTORY', 'CRYPTO_ECOSYSTEMS')
                AND project_namespace IN ('oso', 'eco')
            ),
            stylus_collection AS (
              SELECT DISTINCT
                project_id,
                True AS in_stylus_collection
              FROM projects_by_collection_v1 AS pbc
              JOIN projects USING project_id
              WHERE pbc.collection_name = '{COLLECTION_NAME}'
            ),
            alignment AS (
              SELECT
                project_id,
                MAX(CASE WHEN project_name = '{ECOSYSTEMS[0]}' THEN True ELSE False END) AS in_{ECOSYSTEMS[0]},
                MAX(CASE WHEN project_name = '{ECOSYSTEMS[1]}' THEN True ELSE False END) AS in_{ECOSYSTEMS[1]},
                MAX(CASE WHEN project_name = '{ECOSYSTEMS[2]}' THEN True ELSE False END) AS in_{ECOSYSTEMS[2]}
              FROM projects
              WHERE project_source = 'CRYPTO_ECOSYSTEMS'
              GROUP BY 1
            )
            SELECT DISTINCT
              projects.artifact_id AS repo_id,
              stylus_collection.*,
              alignment.*
            FROM projects
            LEFT JOIN stylus_collection USING project_id
            LEFT JOIN alignment USING project_id
        """)
        df = df.fillna(False)
        return df
    return (
        fetch_dev_leaderboard,
        fetch_dev_projects,
        fetch_github_metrics_by_project,
        fetch_sdk_dependencies,
    )


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
