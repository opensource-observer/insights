import base64
import requests
import pandas as pd
import datetime
from pyoso import Client
from ..config.settings import OSO_API_KEY, GITHUB_HEADERS

class DataFetcher:
    def __init__(self):
        self.oso_client = Client(api_key=OSO_API_KEY)

    def fetch_repositories(self, limit: int = None, sort_by_stars: bool = True, min_stars: int = 0) -> pd.DataFrame:
        """
        Fetch repositories from OSO.
        
        Args:
            limit: Optional limit on number of repositories to fetch.
            sort_by_stars: If True, sort repositories by star_count descending.
        """

        where_keywords = """
                collection_name LIKE '%ethereum%'
                OR collection_name LIKE '%arbitrum%'
                OR collection_name LIKE '%optimism%'
                OR collection_name LIKE '%scroll%'
                OR collection_name LIKE '%polygon%'
        """
        query = f"""
        SELECT DISTINCT
          re.artifact_id AS repo_artifact_id,
          re.artifact_namespace AS repo_artifact_namespace,
          re.artifact_name AS repo_artifact_name,
          re.created_at,
          re.updated_at,
          re.language,
          re.star_count,
          re.fork_count,
          re.is_fork,
          re.num_packages_in_deps_dev        
        FROM int_repositories_enriched AS re
        JOIN artifacts_by_project_v1 AS ap ON re.artifact_id = ap.artifact_id
        WHERE ap.project_id IN (
            SELECT DISTINCT project_id FROM oso.projects_by_collection_v1
            WHERE {where_keywords}
        )
        AND re.star_count > {min_stars}
        """
        if sort_by_stars:
            query += " ORDER BY re.star_count DESC, re.artifact_namespace ASC"

        if limit is not None and isinstance(limit, int) and limit > 0:
            query += f" LIMIT {limit}"
            
        df = self.oso_client.to_pandas(query)
        
        # Add is_actively_maintained field based on updated_at (active if updated in last year)
        # Use naive datetime (no timezone) for comparison
        one_year_ago = pd.Timestamp.now().tz_localize(None) - pd.Timedelta(days=365)
        
        # Convert updated_at to datetime if it's a string
        def check_if_active(date):
            if pd.isna(date):
                return False
            
            # Convert to datetime if it's a string
            if isinstance(date, str):
                try:
                    date = pd.to_datetime(date)
                except:
                    return False
            
            # Ensure datetime is naive (no timezone) for comparison
            if hasattr(date, 'tz_localize'):
                if date.tzinfo is not None:
                    date = date.tz_localize(None)
                    
            # Now compare with one_year_ago
            return date > one_year_ago
            
        df['is_actively_maintained'] = df['updated_at'].apply(check_if_active)
        
        # Ensure is_fork is a boolean
        if 'is_fork' not in df.columns:
            print("Warning: 'is_fork' field not available in OSO data. Setting all to False.")
            df['is_fork'] = False
        else:
            # Convert to boolean if it's not already
            df['is_fork'] = df['is_fork'].fillna(False).astype(bool)
            
        return df

    def fetch_readme(self, owner: str, repo: str) -> tuple:
        """
        Fetch README.md content from GitHub repository with debug logging.
        
        Returns:
            tuple: (readme_content, status) where status is one of:
                   "SUCCESS", "EMPTY", or "ERROR"
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        print(f"Fetching README for {owner}/{repo} ...", flush=True)
        resp = requests.get(url, headers=GITHUB_HEADERS)
        print(f"Status code: {resp.status_code}", flush=True)
        if resp.status_code == 200:
            data = resp.json()
            try:
                content = base64.b64decode(data["content"]).decode("utf-8")
                if not content.strip():
                    print(f"Empty README for {owner}/{repo}", flush=True)
                    return "", "EMPTY"
                print(f"Successfully fetched README for {owner}/{repo}", flush=True)
                return content, "SUCCESS"
            except Exception as e:
                print(f"Error decoding README for {owner}/{repo}: {e}", flush=True)
                return "", "ERROR"
        else:
            print(f"Failed to fetch README for {owner}/{repo}: {resp.text}", flush=True)
        return "", "ERROR"

    def get_all_readmes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add README content to the dataframe for each repository with debug logging."""
        print("First 5 repo_artifact_namespace:", df["repo_artifact_namespace"].head().tolist(), flush=True)
        print("First 5 repo_artifact_name:", df["repo_artifact_name"].head().tolist(), flush=True)
        
        # Apply fetch_readme and capture both content and status with progress bar
        from tqdm import tqdm
        tqdm.pandas(desc="Fetching READMEs")
        readme_results = df.progress_apply(
            lambda row: self.fetch_readme(row.repo_artifact_namespace, row.repo_artifact_name),
            axis=1
        )
        
        # Split the results into separate columns
        df["readme_md"] = [result[0] for result in readme_results]
        df["readme_status"] = [result[1] for result in readme_results]
        
        return df
