import json
import pandas as pd
from pathlib import Path
from .data_manager import DataManager
from ..config.config_manager import ConfigManager
from ..processing.fetcher import GitHubFetcher

class RepositoryFetcherStep:
    def __init__(self, data_manager: DataManager, config_manager: ConfigManager):
        self.data_manager = data_manager
        self.config_manager = config_manager
        self.fetcher = GitHubFetcher()

    def run(self, force_refresh: bool = False):
        """
        Fetch repositories and READMEs from seed_repos.json.
        """
        if force_refresh:
            print("Force refresh enabled for repository data. Wiping existing raw data.")
            self.data_manager.wipe_repos_data()
        
        # Check if data already exists and not forcing refresh
        if not force_refresh:
            existing_df = self.data_manager.get_repos_data()
            if not existing_df.empty:
                print("Repository data already exists and force_refresh is false.")
                return existing_df

        # Read seed repositories from JSON file
        seed_repos_path = Path("data/seed_repos.json")
        if not seed_repos_path.exists():
            raise FileNotFoundError(f"Seed repositories file not found at {seed_repos_path}")
        
        with open(seed_repos_path) as f:
            repo_urls = json.load(f)
        
        print(f"Found {len(repo_urls)} seed repositories.")
        
        # Fetch repository data
        print("Fetching repository data from GitHub...")
        repos_df = self.fetcher.fetch_repositories(repo_urls)
        
        if repos_df.empty:
            print("No repositories found from GitHub fetch.")
            # Save an empty DataFrame to indicate the step ran
            self.data_manager.save_repos_data(pd.DataFrame())
            return pd.DataFrame()
            
        print(f"Successfully processed {len(repos_df)} repositories.")
        self.data_manager.save_repos_data(repos_df)
        return repos_df

if __name__ == '__main__':
    # Example Usage (requires .env file with GITHUB_TOKEN and GOOGLE_API_KEY)
    cfg_manager = ConfigManager()
    output_dir = cfg_manager.get_output_dir()
    dt_manager = DataManager(output_dir=output_dir, config=cfg_manager)
    
    repo_fetch_step = RepositoryFetcherStep(data_manager=dt_manager, config_manager=cfg_manager)
    
    print("\nRunning RepositoryFetcherStep...")
    fetched_data = repo_fetch_step.run(force_refresh=False) # Set True to wipe and refetch
    print(f"\nFetched data head:\n{fetched_data.head()}")
    print(f"Number of rows fetched: {len(fetched_data)}")
