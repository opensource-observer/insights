from oso_db import execute_query
import pandas as pd
import time


TABLES = {
    'artifact': ['createdAt', 'updatedAt', 'name', 'url', 'deletedAt', 'namespace', 'type', 'id'],
    'collection': ['deletedAt', 'verified', 'id', 'slug', 'description', 'name', 'createdAt', 'updatedAt'],
    'collection_projects_project': ['projectId', 'collectionId'],
    'event': ['toId', 'amount', 'time', 'details', 'typeId', 'sourceId', 'fromId', 'id'],
    'event_type': ['version', 'deletedAt', 'updatedAt', 'createdAt', 'id', 'name'],
    'project_artifacts_artifact': ['projectId', 'artifactId']
}
ARTIFACTS = {
    'OPTIMISM': ['EOA_ADDRESS', 'SAFE_ADDRESS', 'CONTRACT_ADDRESS', 'FACTORY_ADDRESS'],
    'GITHUB': ['GIT_REPOSITORY', 'GIT_EMAIL', 'GIT_NAME', 'GITHUB_ORG', 'GITHUB_USER'],
    'NPM_REGISTRY': ['NPM_PACKAGE']
}
EVENT_TYPES = {
    'FUNDING': 1,
    'PULL_REQUEST_CREATED': 2,
    'PULL_REQUEST_MERGED': 3,
    'COMMIT_CODE': 4,
    'ISSUE_FILED': 5,
    'ISSUE_CLOSED': 6,
    'DOWNSTREAM_DEPENDENCY_COUNT': 7,
    'UPSTREAM_DEPENDENCY_COUNT': 8,
    'DOWNLOADS': 9,
    'CONTRACT_INVOKED': 10,
    'USERS_INTERACTED': 11,
    'CONTRACT_INVOKED_AGGREGATE_STATS': 12,
    'PULL_REQUEST_CLOSED': 13,
    'STAR_AGGREGATE_STATS': 14,
    'PULL_REQUEST_REOPENED': 15,
    'PULL_REQUEST_REMOVED_FROM_PROJECT': 16,
    'PULL_REQUEST_APPROVED': 17,
    'ISSUE_CREATED': 18,
    'ISSUE_REOPENED': 19,
    'ISSUE_REMOVED_FROM_PROJECT': 20,
    'STARRED': 21,
    'FORK_AGGREGATE_STATS': 22,
    'FORKED': 23,
    'WATCHER_AGGREGATE_STATS': 24,
    'CONTRACT_INVOCATION_DAILY_COUNT': 25,
    'CONTRACT_INVOCATION_DAILY_FEES': 26
}

CSV_OUTPATH = "data/RPGF3/RPGF3_OSO_project_stats_DRAFT.csv"


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time} seconds to execute.")
        return result
    return wrapper


@timing_decorator
def get_slugs_by_collection(collection):
    query = f"""
        SELECT DISTINCT p.slug
        FROM collection c
        JOIN collection_projects_project cpp ON c."id" = cpp."collectionId"
        JOIN project p on cpp."projectId" = p."id"
        WHERE c.slug = '{collection}'
        ORDER BY p.slug;
    """
    return [row[0] for row in execute_query(query, col_names=False)]


@timing_decorator
def get_active_devs(slugs_param, start_date):
    query = f"""
        WITH Devs AS (
            SELECT 
                p."slug" AS "slug",
                e."fromId" AS "fromId",
                time_bucket(INTERVAL '1 month', e."time") AS "month",
                CASE WHEN COUNT(DISTINCT e."time") >= 10 THEN 1 ELSE 0 END AS "active_developer"
                    FROM event e             
            JOIN project_artifacts_artifact paa ON e."toId" = paa."artifactId"            
            JOIN project p ON paa."projectId" = p.id         
            WHERE
                e."typeId" = 4 -- COMMIT CODE EVENTS ONLY
                AND p.slug IN ({slugs_param})
                AND e.time >= '{start_date}'
            GROUP BY
                p."slug",
                e."fromId",
                time_bucket(INTERVAL '1 month', e."time")
        )
        SELECT 
            slug,
            month,
            SUM("active_developer")
        FROM Devs
        GROUP BY slug, month;
    """
    return execute_query(query, col_names=True)


@timing_decorator
def get_project_stats(slugs_param, start_date):
    query = f"""
        SELECT 

            p.slug AS slug,

            COUNT(DISTINCT CASE WHEN a."type" = 'GIT_REPOSITORY' THEN a."id" END) AS "# GitHub Repos",
            MIN(CASE WHEN e."typeId" IN (2,4) THEN e."time" END) AS "Date First Commit",
            MAX(CASE WHEN e."typeId" = 14 THEN e."amount" END) AS "Total Stars",
            MAX(CASE WHEN e."typeId" = 22 THEN e."amount" END) AS "Total Forks",
            COUNT(DISTINCT CASE WHEN e."typeId" IN (2,4,18) THEN e."fromId" END) AS "Total Contributors",
            COUNT(DISTINCT CASE WHEN e."typeId" IN (2,4,18) AND e."time" >= NOW() - INTERVAL '180 days' THEN e."fromId" END) AS "Contributors Last 6 Months",

            COUNT(DISTINCT CASE WHEN a."type" IN ('CONTRACT_ADDRESS', 'FACTORY_ADDRESS') AND a.namespace = 'OPTIMISM' THEN a."id" END) AS "# OP Contracts",
            MIN(CASE WHEN e."typeId" = 25 THEN e."time" END) AS "Date First Txn",
            COUNT(DISTINCT CASE WHEN e."typeId" = 25 THEN e."fromId" END) AS "Total Onchain Users",
            COUNT(DISTINCT CASE WHEN e."typeId" = 25 AND e."time" >= '{start_date}' THEN e."fromId" END) AS "Onchain Users Last 6 Months",        
            SUM(CASE WHEN e."typeId" = 25 THEN e."amount"  END) AS "Total Txns",
            SUM(CASE WHEN e."typeId" = 26 THEN e."amount" / 10e18 END) AS "Total Txn Fees (ETH)",
            SUM(CASE WHEN e."typeId" = 26 AND e."time" >= '{start_date}' THEN e."amount" / 10e18 END) AS "Txn Fees Last 6 Months (ETH)",

            COUNT(DISTINCT CASE WHEN a."type" = 'NPM_PACKAGE' THEN a."id" END) AS "# NPM Packages",
            MIN(CASE WHEN e."typeId" = 9 AND e."amount" > 0 THEN e."time" END) AS "Date First Download",
            SUM(CASE WHEN e."typeId" = 9 THEN e."amount" END) AS "Total Downloads",
            SUM(CASE WHEN e."typeId" = 9 AND e."time" >= '{start_date}' THEN e."amount" END) AS "Downloads Last 6 Months"

        FROM project p
        JOIN project_artifacts_artifact paa ON p."id" = paa."projectId"
        LEFT JOIN artifact a ON paa."artifactId" = a."id"
        LEFT JOIN event e ON e."toId" = paa."artifactId" 
        WHERE p.slug IN ({slugs_param})
        GROUP BY p.slug;
    """
    return execute_query(query, col_names=True)


def generate_snapshot():

    rpgf3_slugs = get_slugs_by_collection('op-rpgf3')
    slugs_param = "'" + "','".join(rpgf3_slugs) + "'"

    start_date = '2023-05-01'
    active_devs_results = get_active_devs(slugs_param, start_date)
    project_stats_results = get_project_stats(slugs_param, start_date)

    months_back = 6
    df_devs = pd.DataFrame(active_devs_results[1:], columns=active_devs_results[0])
    monthly_active_devs = (df_devs.groupby('slug')['sum'].sum()/months_back).rename('Avg Monthly Active Devs')

    df = pd.DataFrame(
        project_stats_results[1:], 
        columns=project_stats_results[0]
    ).join(monthly_active_devs, on='slug')
    date_cols = ['Date First Commit', 'Date First Txn', 'Date First Download']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col]).apply(lambda x: x.date())

    df.to_csv(CSV_OUTPATH, index=False)


if __name__ == "__main__":
    generate_snapshot()    