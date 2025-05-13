import base64
import requests
import pandas as pd
from pyoso import Client
from ..config.settings import OSO_API_KEY, GITHUB_HEADERS

class DataFetcher:
    def __init__(self):
        self.oso_client = Client(api_key=OSO_API_KEY)

    def fetch_repositories(self, limit: int = None, sort_by_stars: bool = True) -> pd.DataFrame:
        """
        Fetch repositories from OSO.
        
        Args:
            limit: Optional limit on number of repositories to fetch.
            sort_by_stars: If True, sort repositories by star_count descending.
        """
        query = """
        SELECT DISTINCT
          re.artifact_id AS repo_artifact_id,
          p.project_id,
          p.project_name AS atlas_id,
          p.display_name,
          re.artifact_namespace AS repo_artifact_namespace,
          re.artifact_name AS repo_artifact_name,
          re.created_at,
          re.updated_at,
          re.star_count,
          re.fork_count,
          re.num_packages_in_deps_dev
        FROM stg_op_atlas_application AS a
        JOIN projects_v1 AS p
          ON p.project_id = a.project_id
        JOIN stg_op_atlas_project_repository AS pr
          ON p.project_id = pr.project_id
        JOIN int_repositories_enriched AS re
          ON re.artifact_namespace = pr.artifact_namespace
          AND re.artifact_name = pr.artifact_name
        WHERE a.round_id = '7'
        """
        # The table int_superchain_s7_devtooling_repositories should have star_count
        # If not, this sort will fail or do nothing. Assuming 'r.star_count' is valid.
        if sort_by_stars:
            query += " ORDER BY re.star_count DESC, p.project_name ASC"

        if limit is not None and isinstance(limit, int) and limit > 0:
            query += f" LIMIT {limit}"
            
        return self.oso_client.to_pandas(query)

    def fetch_readme(self, owner: str, repo: str) -> str:
        """Fetch README.md content from GitHub repository with debug logging."""
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        print(f"Fetching README for {owner}/{repo} ...", flush=True)
        resp = requests.get(url, headers=GITHUB_HEADERS)
        print(f"Status code: {resp.status_code}", flush=True)
        if resp.status_code == 200:
            data = resp.json()
            try:
                content = base64.b64decode(data["content"]).decode("utf-8")
                print(f"Successfully fetched README for {owner}/{repo}", flush=True)
                return content
            except Exception as e:
                print(f"Error decoding README for {owner}/{repo}: {e}", flush=True)
                return ""
        else:
            print(f"Failed to fetch README for {owner}/{repo}: {resp.text}", flush=True)
        return ""

    def get_all_readmes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add README content to the dataframe for each repository with debug logging."""
        print("First 5 repo_artifact_namespace:", df["repo_artifact_namespace"].head().tolist(), flush=True)
        print("First 5 repo_artifact_name:", df["repo_artifact_name"].head().tolist(), flush=True)
        df["readme_md"] = df.apply(
            lambda row: self.fetch_readme(row.repo_artifact_namespace, row.repo_artifact_name),
            axis=1
        )
        return df
