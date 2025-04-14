import datetime
from dotenv import load_dotenv
import os
import pandas as pd
from githubkit import GitHub
from githubkit.exception import RequestFailed
from pyoso import Client
import time

load_dotenv()
OSO_API_KEY = os.environ['OSO_API_KEY']
client = Client(api_key=OSO_API_KEY)

GITHUB_API_KEY = os.environ['GITHUB_TOKEN']
github = GitHub(GITHUB_API_KEY)

def stringify(arr):
    return "'" + "','".join(arr) + "'"

PROJECTS = [] # add all the OSO project slugs here


df_oso = client.to_pandas(f"""
SELECT DISTINCT
    project_name,
    artifact_namespace,
    artifact_name
FROM artifacts_by_project_v1
WHERE
    project_name IN ({stringify(PROJECTS)})
    AND artifact_source = 'GITHUB'
""")

csv_file = 'contributors.csv'

# --- Step 1: Load existing CSV data if present ---
if os.path.exists(csv_file):
    df_existing = pd.read_csv(csv_file)
    commit_data = df_existing.to_dict('records')
    processed_repos = set(df_existing[['project', 'owner', 'repo']].apply(tuple, axis=1))
    print(f"Found existing CSV with {len(df_existing)} entries. Skipping repos already in CSV.")
else:
    commit_data = []
    processed_repos = set()

# --- Step 2: Loop over each repository from the OSO query ---
for _, row in df_oso.iterrows():
    project = row['project_name']
    owner = row['artifact_namespace']
    repo = row['artifact_name']
    
    # Check BEFORE hitting the GitHub API.
    if (project, owner, repo) in processed_repos:
        #print(f"Skipping API call for {owner}/{repo} for project {project} as it is already processed.")
        continue

    retries = 0
    success = False
    commits = []
    
    # Attempt to fetch commits from GitHub with a simple retry logic.
    while not success and retries < 3:
        try:
            commits = list(github.paginate(
                github.rest.repos.list_commits,
                owner=owner,
                repo=repo
            ))
            success = True
        except RequestFailed as e:
            code = e.response.status_code
            if code in [404, 409]:
                print(f"Repository {owner}/{repo} not available ({code}). Skipping.")
                success = True
                commits = []
            else:
                retries += 1
                print(f"Error on {owner}/{repo}. Retrying ({retries}/3) after waiting 15 minutes. Error: {e}")
                time.sleep(60 * 15)

    # Create an empty entry to show we've processed this project
    commit_data.append({
        "date": '',
        "author": '',
        "committer": '',
        "sha": '',
        "project": project,
        "owner": owner,
        "repo": repo
    })
    for commit in commits:
        if commit.author and getattr(commit.author, 'login', None):
            commit_sha = commit.sha
            author = getattr(commit.author, 'login', '')
            committer = getattr(commit.committer, 'login', '')
            commit_date = getattr(commit.commit.author, 'date', '')
            # Filter commits by a specific date range.
            if commit_date >= '2023-08-01' and commit_date <= '2025-01-31':
                new_commit = {
                    "date": commit_date,
                    "author": author.lower(),
                    "committer": committer.lower(),
                    "sha": commit_sha,
                    "project": project,
                    "owner": owner,
                    "repo": repo
                }
                commit_data.append(new_commit)
    
    # Save the updated commit data to CSV after processing each repository.
    df = pd.DataFrame(commit_data)
    df.to_csv(csv_file, index=False)
    print(f"Updated CSV after processing repository {owner}/{repo}: {len(df)} total commits recorded.")