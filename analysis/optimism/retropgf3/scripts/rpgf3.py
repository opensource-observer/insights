import pandas as pd
from oso_db import execute_query

# load data
df = pd.read_csv("data/RPGF3/indexed_attestations.csv")
df = df[df.urlType.isin(['github', 'etherscan', 'npm']) & df['attestationType'].isin(['impactMetric', 'contributionLink'])]

df['artifactInfo'] = df['artifactInfo'].apply(eval)
df['artifactFound'] = df['artifactInfo'].apply(lambda x: x[0] == 'success')
df['artifactName'] = df['artifactInfo'].apply(lambda x: x[1])


### PART 1 ###

# lookup artifacts
artifacts = "', '".join(set(df['artifactName'].dropna().to_list()))
query = f"""
        SELECT a.id, p.slug, LOWER(a.name) as "name", a.type
        FROM artifact a
        LEFT JOIN project_artifacts_artifact paa ON a."id" = paa."artifactId"
        LEFT JOIN project p ON paa."projectId" = p."id"        
        WHERE LOWER(a.name) IN ('{artifacts}')
        """
results = execute_query(query)
artifact_df = pd.DataFrame(results[1:], columns=results[0]).set_index('name')
artifact_df.columns = ['artifactId', 'projectSlug', 'artifactType']

# merge the datasets
merged_df = df.join(artifact_df, on='artifactName', how='left')
merged_df.to_csv("data/RPGF3/indexed_metrics_mapped_to_artifacts.csv")
print("Saved to data/RPGF3/indexed_metrics_mapped_to_artifacts.csv")

### PART 2 ###

temp_df = merged_df[['artifactId', 'artifactName']].dropna()
artifact_mapping = dict(zip(temp_df['artifactId'].apply(int), temp_df['artifactName']))
contract_ids = ",".join(
    set(
        merged_df[merged_df['artifactType'].isin(["CONTRACT_ADDRESS", "FACTORY_ADDRESS"])]
        ["artifactId"].dropna().apply(int).apply(str)
        .to_list()
    )
)

query = f"""
        SELECT 
            "toId" as "contractId",
            COUNT(*) AS total_transactions,
            COUNT(DISTINCT "fromId") AS unique_addresses,
            TO_CHAR(MIN(time),'YYYY-MM') AS first_date,
            TO_CHAR(MAX(time),'YYYY-MM') AS last_date
        FROM event 
        WHERE 
            "toId" in ({contract_ids})
        GROUP BY "toId"
        """

results = execute_query(query)
contract_df = pd.DataFrame(results[1:], columns=results[0])
contract_df['artifactName'] = contract_df['contractId'].map(artifact_mapping)
contract_df = contract_df[['artifactName', 'total_transactions', 'unique_addresses', 'first_date', 'last_date']]
contract_df.to_csv("data/RPGF3/available_contract_metrics.csv")
print("Saved to data/RPGF3/available_contract_metrics.csv")


### PART 3 ###

# lookup github orgs
github_orgs = "', '".join(set(merged_df[merged_df['artifactType'] == "GITHUB_ORG"]["artifactName"].dropna().to_list()))
query = f"""
        WITH github_org_artifacts AS (
            SELECT a.id AS "artifact_id", p.slug AS "project_slug", LOWER(a.name) AS "artifact_name", a.type AS "artifact_type"
            FROM artifact a
            LEFT JOIN project_artifacts_artifact paa ON a."id" = paa."artifactId"
            LEFT JOIN project p ON paa."projectId" = p."id"        
            WHERE EXISTS (
                SELECT 1
                FROM unnest(ARRAY['{github_orgs}']) AS param(value)
                WHERE LOWER(a.name) LIKE LOWER(param.value || '%')
            )
        )
        SELECT 
            goa."project_slug",
            COUNT(DISTINCT goa."artifact_name") AS "num_repos",
            COUNT(DISTINCT CASE WHEN e."typeId" = 21 THEN e."fromId" END) AS "stars_count",
            COUNT(DISTINCT CASE WHEN e."typeId" = 23 THEN e."fromId" END) AS "forks_count",
            COUNT(DISTINCT CASE WHEN e."typeId" IN (4, 18, 17) THEN e."fromId" END) AS "num_contributors",
            TO_CHAR(MIN(e.time), 'YYYY-MM') AS "first_date",
            TO_CHAR(MAX(e.time), 'YYYY-MM') AS "last_date"
        FROM github_org_artifacts goa
        LEFT JOIN event e ON goa."artifact_id" = e."toId"
        WHERE e."typeId" IN (4, 8, 17, 21, 23) AND goa."project_slug" IS NOT NULL
        GROUP BY goa."project_slug";
        """
results = execute_query(query)
github_org_df = pd.DataFrame(results[1:], columns=results[0]).set_index('project_slug')
github_org_df.to_csv("data/RPGF3/available_github_org_metrics.csv")
print("Saved to data/RPGF3/available_github_org_metrics.csv")


### PART 4 ###

temp_df = merged_df[merged_df['artifactType'] == "GIT_REPOSITORY"][['artifactId', 'artifactName']].dropna()
artifact_mapping = dict(zip(temp_df['artifactId'].apply(int), temp_df['artifactName']))
artifact_ids = ",".join(list(map(str,artifact_mapping.keys())))
query = f"""
        SELECT 
            "toId",
            COUNT(DISTINCT CASE WHEN "typeId" = 21 THEN "fromId" END) AS stars_count,
            COUNT(DISTINCT CASE WHEN "typeId" = 23 THEN "fromId" END) AS forks_count,
            COUNT(DISTINCT CASE WHEN "typeId" IN (4,18,17) THEN "fromId" END) AS num_contributors,
            TO_CHAR(MIN(time),'YYYY-MM') AS first_date,
            TO_CHAR(MAX(time),'YYYY-MM') AS last_date
        FROM event 
        WHERE 
            "toId" in ({artifact_ids})
            AND "typeId" in (4,8,17,21,23)
        GROUP BY "toId"
        """
results = execute_query(query)

git_repos_df = pd.DataFrame(results[1:], columns=results[0])
git_repos_df['artifactName'] = git_repos_df['toId'].map(artifact_mapping)
git_repos_df = git_repos_df[['artifactName', 'stars_count', 'forks_count', 'num_contributors', 'first_date', 'last_date']]
git_repos_df.to_csv("data/RPGF3/available_github_repo_metrics.csv", index=False)
print("Saved to data/RPGF3/available_github_repo_metrics.csv")