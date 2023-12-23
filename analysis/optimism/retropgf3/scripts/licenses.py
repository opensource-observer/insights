import json
from oso_db import execute_query
from github import get_license
import pandas as pd


JSON_PATH = "../data/2023-12-01_licenses.json"
CSV_PATH  = "../data/2023-12-01_project_licenses.csv"
CSV_PROJECTS = "../data/RPGF3/RPGF3_tagged_projects.csv"


def get_artifact_stats(artifacts):
    artifacts = ",".join([f"'{a}'" for a in artifacts])
    query = f"""
        SELECT
            a.name AS "Artifact",
            MAX(CASE WHEN e."typeId" = 14 THEN e."amount" END) AS "Total Stars",
            MAX(CASE WHEN e."typeId" = 22 THEN e."amount" END) AS "Total Forks",
            COUNT(DISTINCT CASE WHEN e."typeId" IN (2,4,18) THEN e."fromId" END) AS "Total Contributors"
        FROM event e
        JOIN artifact a ON e."toId" = a."id" 
        WHERE a.name IN ({artifacts})
        GROUP BY a.name;
    """
    results = execute_query(query, col_names=True)
    print(f"Got stats for {len(results)} artifacts.")
    return results


def get_repos():
    query = """
        SELECT 
            p.slug AS project, 
            a.name AS repo
        FROM artifact a
        JOIN project_artifacts_artifact paa ON a.id = paa."artifactId"
        JOIN project p ON paa."projectId" = p.id
        JOIN collection_projects_project cpp ON p.id = cpp."projectId"
        JOIN collection c ON cpp."collectionId" = c.id
        WHERE c.slug = 'op-rpgf3' AND a.type = 'GIT_REPOSITORY'
    """    
    print(f"Getting repos from DB...")
    repos = execute_query(query, col_names=False)
    print(f"Got {len(repos)} repos from DB.")
    return repos


def dump_data(data, filename=JSON_PATH):
    with open(filename, "w") as outfile:
        json.dump(data, outfile, indent=4)


def load_data(filename=JSON_PATH):
    with open(filename, "r") as infile:
        data = json.load(infile)
    return data
    

def update_data(repo_data):
    licenses = load_data()
    for (project, repo) in repo_data:
        if not any(d['repo'] == repo for d in licenses):
            try:
                license = get_license(repo)
                licenses.append({'project': project, 'repo': repo, 'license': license})        
            except Exception as e:
                print(f"Error getting license for {repo}: {e}")
                break
    dump_data(licenses)
    return licenses


def summarize_licenses_by_project(licenses):
    df = pd.DataFrame(licenses)
    df = df.groupby(['project', 'license']).count()
    df = df.reset_index()
    df = df.pivot(index='project', columns='license', values='repo')
    df = df.fillna(0)
    df = df.astype(int)
    df.to_csv(CSV_PATH)
    return df


def add_stats_to_json_data(data):
    artifacts = [d["repo"] for d in data]
    artifact_stats = get_artifact_stats(artifacts)
    print(artifact_stats[:5])
    for d in data:
        artifact = d["repo"]
        matches = [a for a in artifact_stats if a[0] == artifact]
        if not matches:
            continue
        stats = matches[0]
        print(stats)
        d.update({
            "Total Stars": stats[1],
            "Total Forks": stats[2],
            "Total Contributors": stats[3]
        })
    return data


def add_stats_to_project_data(license_data):
    project_df = pd.read_csv(CSV_PROJECTS)
    slugs_to_ids = {row['OSO Slug']: row['Project ID'] for _, row in project_df.iterrows() if row['OSO Slug']}
    ids_to_names = {row['Project ID']: row['Project Name'] for _, row in project_df.iterrows() if row['OSO Slug']}
    
    license_df = pd.DataFrame(license_data)
    license_df['Project ID'] = license_df['project'].apply(lambda x: slugs_to_ids.get(x, None))
    license_df['Project Name'] = license_df['Project ID'].apply(lambda x: ids_to_names.get(x, None))
    return license_df


if __name__ == "__main__":
    repos = get_repos()
    licenses = update_data(repos)
    data = add_stats_to_json_data(licenses)
    dump_data(data)
    df = add_stats_to_project_data(data)
    df.to_csv(CSV_PATH)
    
