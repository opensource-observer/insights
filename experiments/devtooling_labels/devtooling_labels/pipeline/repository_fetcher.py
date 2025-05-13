import pandas as pd
from .data_manager import DataManager
from ..config.config_manager import ConfigManager
from ..processing.fetcher import DataFetcher

class RepositoryFetcherStep:
    def __init__(self, data_manager: DataManager, config_manager: ConfigManager):
        self.data_manager = data_manager
        self.config_manager = config_manager
        self.fetcher = DataFetcher() # Assuming DataFetcher doesn't need config for initialization

    def run(self, force_refresh: bool = False):
        """
        Fetch repositories and READMEs.
        Uses test_mode and test_mode_limit from config if test_mode is enabled.
        """
        limit = None
        sort_by_stars_in_test = False
        is_test = self.config_manager.is_test_mode()

        if is_test:
            limit = self.config_manager.get_test_mode_limit()
            sort_by_stars_in_test = True # Always sort by stars in test mode as per new req
            print(f"Running in TEST MODE: Targeting up to {limit} repositories, sorted by stars DESC.")

        if force_refresh:
            print("Force refresh enabled for repository data. Wiping existing raw data.")
            self.data_manager.wipe_repos_data()
        
        # Check if data already exists and not forcing refresh
        if not force_refresh:
            existing_df = self.data_manager.get_repos_data()
            if not existing_df.empty:
                print("Repository data already exists and force_refresh is false.")
                if is_test:
                    if 'star_count' in existing_df.columns:
                        print(f"Applying test mode (sort by stars, limit {limit}) to existing data.")
                        sorted_df = existing_df.sort_values(by='star_count', ascending=False)
                        return sorted_df.head(limit)
                    else:
                        print(f"Warning: 'star_count' not in existing data. Using first {limit} entries for test mode.")
                        return existing_df.head(limit)
                return existing_df # Not test mode, return all existing

        # If here, either force_refresh is true or data doesn't exist.
        print("Fetching repositories from OSO...")
        # Pass sort_by_stars only if in test_mode, limit is passed anyway (None if not test)
        repos_df = self.fetcher.fetch_repositories(limit=limit, sort_by_stars=sort_by_stars_in_test)
        
        if repos_df.empty:
            print("No repositories found from OSO fetch.")
            # Save an empty DataFrame to indicate the step ran
            self.data_manager.save_repos_data(pd.DataFrame())
            return pd.DataFrame()
            
        print(f"Found {len(repos_df)} repositories.")

        print("Fetching READMEs from GitHub...")
        # Ensure 'repo_artifact_namespace' and 'repo_artifact_name' exist
        if 'repo_artifact_namespace' not in repos_df.columns or 'repo_artifact_name' not in repos_df.columns:
            print("Error: 'repo_artifact_namespace' or 'repo_artifact_name' not in fetched data.")
            # Save what we have so far
            self.data_manager.save_repos_data(repos_df)
            return repos_df # Or handle error more gracefully

        repos_df = self.fetcher.get_all_readmes(repos_df)
        print(f"Retrieved READMEs for {len(repos_df[repos_df['readme_md'] != ''])} repositories.")

        self.data_manager.save_repos_data(repos_df)
        
        # If in test mode and fetched more than limit (e.g. limit was on OSO query but get_all_readmes changed row count)
        # This scenario is less likely if limit is applied correctly in fetch_repositories
        if limit is not None and len(repos_df) > limit:
            return repos_df.head(limit)
            
        return repos_df

if __name__ == '__main__':
    # Example Usage (requires .env file and OSO/GitHub credentials)
    # Ensure pipeline_config.json exists or is created with defaults
    cfg_manager = ConfigManager()
        
    output_dir = cfg_manager.get_output_dir()
    dt_manager = DataManager(output_dir=output_dir, config=cfg_manager)
    
    repo_fetch_step = RepositoryFetcherStep(data_manager=dt_manager, config_manager=cfg_manager)
    
    print("\nRunning RepositoryFetcherStep...")
    fetched_data = repo_fetch_step.run(force_refresh=False) # Set True to wipe and refetch
    print(f"\nFetched data head:\n{fetched_data.head()}")
    print(f"Number of rows fetched: {len(fetched_data)}")
