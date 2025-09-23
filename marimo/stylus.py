import marimo

__generated_with = "0.15.3"
app = marimo.App(width="full")


@app.cell
def setup_pyoso():
    import pyoso
    import marimo as mo
    client = pyoso.Client()
    pyoso_db_conn = client.dbapi_connection(force_without_pyodide=True)
    return (client,)


@app.cell
def _(get_metrics_by_stylus_project, get_stylus_sdk_dependents):
    df_stylus_project_metrics = get_metrics_by_stylus_project()
    df_stylus_sdk_deps = get_stylus_sdk_dependents()
    return


@app.cell
def _(dev_pagerank, get_devs_who_forked_examples, label_repos):
    df_fork_devs = get_devs_who_forked_examples()
    df_fork_devs_labeled = label_repos(df_fork_devs)
    df_fork_devs_ranked = dev_pagerank(df_fork_devs)
    return df_fork_devs_labeled, df_fork_devs_ranked


@app.cell
def _():
    return


@app.cell
def _(df_fork_devs_labeled, df_fork_devs_ranked):
    df_projects_from_devs = (
        df_fork_devs_labeled.merge(df_fork_devs_ranked[['dev_id', 'dev_score']], on='dev_id')
        .groupby(['repo_owner', 'project_type'], as_index=False)
        .agg(
            repo_rank=('dev_score', 'sum'),
            first_fork=('first_fork','min'),    
            num_devs=('dev_id', 'nunique'),
            dev_names=('dev_url', lambda x: ' | '.join(sorted(set(x.replace('https://github.com/',''))))),
            repos_worked_on_by_those_devs=('repo_url', lambda x: ' | '.join(sorted(set(x))))
        )
        .sort_values(by=['repo_rank', 'num_devs', 'first_fork'], ascending=[False, False, True])
        .reset_index(drop=True)
        .drop(columns=['repo_rank'])
    )
    df_projects_from_devs
    return


@app.cell
def post_processing(get_repo_alignment_tags, np, nx, pd):
    def label_repos(df):

        _repos = df['repo_id'].unique()

        df_labeled = get_repo_alignment_tags(_repos)
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
                return 'Personal'
            return 'Project (Other)'

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
        repo_stars     = repos.set_index("repo_url")["star_count"].fillna(0)

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

        # Helpful diagnostics
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
def query_data(client, pd, wraps):
    # QUERY SETTINGS
    START_DATE = '2022-01-01'
    COLLECTION_NAME = 'arb-stylus'
    ECOSYSTEMS = [
        'arbitrum',
        'ethereum_virtual_machine_stack',
        'solana'
    ]

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
    def get_metrics_by_stylus_project():
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
    def get_metrics_by_stylus_repo():
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

    def get_stylus_sdk_dependents():
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
    def get_devs_who_forked_examples():
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
        get_devs_who_forked_examples,
        get_metrics_by_stylus_project,
        get_repo_alignment_tags,
        get_stylus_sdk_dependents,
    )


@app.cell
def import_libraries():
    import pandas as pd
    from datetime import datetime, date, timedelta
    from functools import wraps
    import networkx as nx
    import numpy as np
    return np, nx, pd, wraps


if __name__ == "__main__":
    app.run()
