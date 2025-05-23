import base64
import requests
import pandas as pd
from pyoso import Client
from ..config.settings import OSO_API_KEY, GITHUB_HEADERS
import os
from typing import List, Dict, Optional
from github import Github
from github.Repository import Repository
from dotenv import load_dotenv
import google.generativeai as genai
from tqdm import tqdm
import json
from pathlib import Path

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
          p.project_name,
          p.display_name,
          re.artifact_namespace AS repo_artifact_namespace,
          re.artifact_name AS repo_artifact_name,
          re.created_at,
          re.updated_at,
          re.star_count,
          re.fork_count,
          re.num_packages_in_deps_dev
        FROM projects_v1 AS p
        JOIN int_repositories_enriched AS re
          ON p.project_id = re.project_id
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

class GitHubFetcher:
    def __init__(self):
        load_dotenv()
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.github = Github(self.github_token)
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # GraphQL endpoint
        self.graphql_url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Content-Type": "application/json",
        }

    def _extract_repo_info(self, repo_url: str) -> tuple[str, str]:
        """Extract owner and repo name from GitHub URL."""
        parts = repo_url.strip("/").split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        return parts[-2], parts[-1]

    def fetch_dependencies(self, owner: str, repo: str) -> Dict:
        """Fetch repository dependencies using GitHub's GraphQL API."""
        query = """
        query($owner: String!, $repo: String!) {
            repository(owner: $owner, name: $repo) {
                dependencyGraphManifests(first: 100) {
                    nodes {
                        filename
                        dependencies {
                            nodes {
                                hasDependencies
                                packageName
                                packageManager
                                packageUrl
                                requirements
                                relationship
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "owner": owner,
            "repo": repo
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                headers=self.headers,
                json={"query": query, "variables": variables}
            )
            response.raise_for_status()
            data = response.json()
            
            # Add debug logging
            print(f"\nFetching dependencies for {owner}/{repo}")
            if "errors" in data:
                print(f"GraphQL errors: {data['errors']}")
                return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
            
            # Check if we got a valid response
            if not data.get("data", {}).get("repository"):
                print(f"No repository data found for {owner}/{repo}")
                return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
            
            manifests = data["data"]["repository"]["dependencyGraphManifests"]["nodes"]
            if not manifests:
                print(f"No dependency manifests found for {owner}/{repo}")
            else:
                print(f"Found {len(manifests)} dependency manifests")
                for manifest in manifests:
                    deps = manifest.get("dependencies", {}).get("nodes", [])
                    print(f"Manifest {manifest.get('filename')}: {len(deps)} dependencies")
            
            return data
        except Exception as e:
            print(f"Error fetching dependencies for {owner}/{repo}: {str(e)}")
            return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}

    def fetch_repository_data(self, repo_url: str) -> Dict:
        """Fetch repository data from GitHub."""
        owner, repo_name = self._extract_repo_info(repo_url)
        repo = self.github.get_repo(f"{owner}/{repo_name}")
        
        # Get README content
        try:
            readme = repo.get_readme()
            readme_content = readme.decoded_content.decode('utf-8')
        except Exception as e:
            print(f"Error fetching README for {repo_url}: {str(e)}")
            readme_content = ""

        # Get repository metadata
        return {
            "repo_url": repo_url,
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description,
            "language": repo.language,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "readme_content": readme_content,
            "topics": repo.get_topics(),
            "created_at": repo.created_at.isoformat(),
            "updated_at": repo.updated_at.isoformat(),
        }

    def generate_summary(self, readme_content: str) -> str:
        """Generate AI summary of README content using Gemini."""
        if not readme_content:
            return ""
            
        try:
            prompt = f"""Please summarize this GitHub repository README. Focus on the main purpose, key features, and technical details:

{readme_content}"""

            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return ""

    def fetch_repositories(self, repo_urls: List[str]) -> pd.DataFrame:
        """Fetch data for multiple repositories."""
        data = []
        dependencies_data = []
        
        print("\nFetching repository data and READMEs...")
        for url in tqdm(repo_urls, desc="Repositories"):
            try:
                owner, repo_name = self._extract_repo_info(url)
                repo_data = self.fetch_repository_data(url)
                data.append(repo_data)
                
                # Fetch dependencies
                deps_data = self.fetch_dependencies(owner, repo_name)
                if deps_data.get("data", {}).get("repository", {}).get("dependencyGraphManifests", {}).get("nodes"):
                    dependencies_data.append({
                        "repo_url": url,
                        "dependencies": deps_data["data"]["repository"]["dependencyGraphManifests"]["nodes"]
                    })
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
                continue
        
        df = pd.DataFrame(data)
        
        print("\nGenerating summaries...")
        df['summary'] = [self.generate_summary(content) for content in tqdm(df['readme_content'], desc="Summaries")]
        
        # Save dependencies to a separate JSON file
        if dependencies_data:
            output_dir = Path("data")
            output_dir.mkdir(exist_ok=True)
            with open(output_dir / "dependencies.json", "w") as f:
                json.dump(dependencies_data, f, indent=2)
            print(f"\nSaved dependencies data to {output_dir / 'dependencies.json'}")
        
        return df

    def fetch_all_dependencies(self, repo_urls: List[str], output_file: str = "output/dependencies.json") -> None:
        """Fetch dependencies for all repositories and save to a JSON file."""
        dependencies_data = []
        
        for repo_url in tqdm(repo_urls, desc="Fetching dependencies"):
            try:
                owner, repo = self._extract_repo_info(repo_url)
                print(f"\nProcessing {owner}/{repo}")
                
                # Get repository metadata
                repo_data = self.fetch_repository_data(repo_url)
                
                # Get dependencies
                deps = self.fetch_dependencies(owner, repo)
                
                # Extract dependency data
                manifests = deps.get("data", {}).get("repository", {}).get("dependencyGraphManifests", {}).get("nodes", [])
                all_dependencies = []
                
                for manifest in manifests:
                    manifest_deps = manifest.get("dependencies", {}).get("nodes", [])
                    if manifest_deps:
                        all_dependencies.extend(manifest_deps)
                
                # Create the output entry
                entry = {
                    "repo_url": repo_url,
                    "owner": owner,
                    "repo": repo,
                    "name": repo_data["name"],
                    "full_name": repo_data["full_name"],
                    "description": repo_data["description"],
                    "language": repo_data["language"],
                    "stars": repo_data["stars"],
                    "forks": repo_data["forks"],
                    "topics": repo_data["topics"],
                    "created_at": repo_data["created_at"],
                    "updated_at": repo_data["updated_at"],
                    "dependency_manifests": manifests,
                    "dependencies": all_dependencies
                }
                
                print(f"Found {len(all_dependencies)} total dependencies for {owner}/{repo}")
                dependencies_data.append(entry)
                
            except Exception as e:
                print(f"Error processing {repo_url}: {str(e)}")
                continue
        
        # Create output directory if it doesn't exist
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save dependencies data to JSON file
        with open(output_path, 'w') as f:
            json.dump(dependencies_data, f, indent=2)
        
        print(f"\nSaved dependencies data to {output_file}")
