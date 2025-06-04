import pandas as pd
from tqdm import tqdm
from .data_manager import DataManager
from ..config.config_manager import ConfigManager
from ..processing.ai_service import AIService, SummaryOutput

class SummaryGeneratorStep:
    def __init__(self, data_manager: DataManager, config_manager: ConfigManager, ai_service: AIService):
        self.data_manager = data_manager
        self.config_manager = config_manager
        self.ai_service = ai_service

    def run(self, force_refresh: bool = False, new_only: bool = False):
        """
        Generate summaries for repositories.
        Uses batch_size_summaries from config.
        
        Args:
            force_refresh: If True, wipe existing summaries and regenerate all
            new_only: If True, only generate summaries for repositories that don't have them yet
        """
        batch_size = self.config_manager.get_batch_size_summaries()
        
        if force_refresh:
            print("Force refresh enabled for summaries. Wiping existing summarized data.")
            self.data_manager.wipe_summaries_data()
            existing_summaries_df = pd.DataFrame()
        else:
            existing_summaries_df = self.data_manager.get_summaries_data()

        # Get repository data
        repos_df = self.data_manager.get_repos_data()
        if repos_df.empty:
            print("No repository data found to generate summaries. Skipping.")
            # Save an empty DataFrame to indicate the step ran if forced
            if force_refresh or not self.data_manager.summarized_parquet_path.exists():
                 self.data_manager.save_summaries_data(pd.DataFrame())
            return pd.DataFrame()

        # If we have existing summaries and not forcing refresh
        if not existing_summaries_df.empty and not force_refresh:
            if new_only:
                # Filter out repositories that already have summaries
                existing_repos = set(existing_summaries_df['repo_artifact_id'])
                repos_to_process = repos_df[~repos_df['repo_artifact_id'].isin(existing_repos)]
                if repos_to_process.empty:
                    print("No new repositories found to generate summaries for.")
                    return existing_summaries_df
                print(f"Found {len(repos_to_process)} new repositories to generate summaries for.")
            else:
                print("Summarized data already exists and force_refresh is false. Skipping summary generation.")
                return existing_summaries_df
        else:
            repos_to_process = repos_df

        # Ensure 'readme_md' and 'repo_artifact_id' columns exist
        if 'readme_md' not in repos_to_process.columns:
            print("Error: 'readme_md' column not found in repository data. Cannot generate summaries.")
            return pd.DataFrame()
        if 'repo_artifact_id' not in repos_to_process.columns:
            print("Error: 'repo_artifact_id' column not found. This ID is crucial.")
            return pd.DataFrame()

        print(f"Generating summaries for {len(repos_to_process)} repositories in batches of {batch_size}...")
        
        all_summaries_data = [] # To collect all rows with new summaries

        # Process in batches
        for start_idx in tqdm(range(0, len(repos_to_process), batch_size), desc="Generating Summaries"):
            end_idx = min(start_idx + batch_size, len(repos_to_process))
            batch_df_initial = repos_to_process.iloc[start_idx:end_idx]
            
            # Create a working copy for this batch to add summaries
            batch_df_processed = batch_df_initial.copy()

            summaries = []
            for _, row in batch_df_initial.iterrows():
                readme_content = row.get('readme_md', "")
                summary_output: SummaryOutput = self.ai_service.make_summary(readme_content)
                summaries.append(summary_output.summary)
            
            batch_df_processed["summary"] = summaries
            all_summaries_data.append(batch_df_processed)
        
        if not all_summaries_data:
            print("No summaries were generated.")
            # Save an empty DataFrame if no summaries were made but the step was intended to run
            if force_refresh or not self.data_manager.summarized_parquet_path.exists():
                self.data_manager.save_summaries_data(pd.DataFrame())
            return pd.DataFrame()

        new_summaries_df = pd.concat(all_summaries_data, ignore_index=True)
        
        # If we have existing summaries and not forcing refresh, combine with new ones
        if not existing_summaries_df.empty and not force_refresh:
            final_summarized_df = pd.concat([existing_summaries_df, new_summaries_df], ignore_index=True)
            # Remove any duplicates that might have been introduced
            final_summarized_df = final_summarized_df.drop_duplicates(
                subset=['repo_artifact_id'],
                keep='last'  # Keep the new summary if there was a duplicate
            )
            print(f"Combined data now contains {len(final_summarized_df)} repositories with summaries.")
        else:
            final_summarized_df = new_summaries_df
            
        self.data_manager.save_summaries_data(final_summarized_df)
        
        return final_summarized_df

if __name__ == '__main__':
    # Example Usage
    cfg_manager = ConfigManager()
    ai_svc = AIService(config_manager=cfg_manager)
    output_dir = cfg_manager.get_output_dir()
    dt_manager = DataManager(output_dir=output_dir, config=cfg_manager)
    
    # Ensure repo data exists (run repo_fetcher.py example first if needed)
    if dt_manager.get_repos_data().empty:
        print("No repository data found. Please run RepositoryFetcherStep first or ensure data exists.")
    else:
        summary_gen_step = SummaryGeneratorStep(
            data_manager=dt_manager, 
            config_manager=cfg_manager, 
            ai_service=ai_svc
        )
        
        print("\nRunning SummaryGeneratorStep...")
        # Set force_refresh=True to regenerate even if file exists
        summarized_data = summary_gen_step.run(force_refresh=False) 
        print(f"\nSummarized data head:\n{summarized_data.head()}")
        print(f"Number of rows with summaries: {len(summarized_data)}")
