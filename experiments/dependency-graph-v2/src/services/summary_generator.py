import pandas as pd
from tqdm import tqdm
from ..core.data_manager import DataManager
from ..config.config_manager import ConfigManager
from .ai import AIService, SummaryOutput

class SummaryGeneratorStep:
    def __init__(self, data_manager: DataManager, config_manager: ConfigManager, ai_service: AIService):
        self.data_manager = data_manager
        self.config_manager = config_manager
        self.ai_service = ai_service

    def run(self, force_refresh: bool = False):
        """
        Generate summaries for repositories.
        Uses batch_size_summaries from config.
        """
        batch_size = 10
        
        if force_refresh:
            print("Force refresh enabled for summaries. Wiping existing summarized data.")
            self.data_manager.wipe_summaries_data()

        # Get repository data
        repos_df = self.data_manager.get_repos_data()
        if repos_df.empty:
            print("No repository data found to generate summaries. Skipping.")
            # Save an empty DataFrame to indicate the step ran if forced
            if force_refresh or not self.data_manager.summarized_parquet_path.exists():
                 self.data_manager.save_summaries_data(pd.DataFrame())
            return pd.DataFrame()

        if self.data_manager.summarized_parquet_path.exists() and not force_refresh:
            print("Summarized data already exists and force_refresh is false. Skipping summary generation.")
            return self.data_manager.get_summaries_data()
            
        print(f"Generating summaries for {len(repos_df)} repositories in batches of {batch_size}...")
        
        all_summaries_data = [] # To collect all rows with new summaries

        # Ensure 'readme_md' and 'repo_artifact_id' columns exist
        if 'readme_md' not in repos_df.columns:
            print("Error: 'readme_md' column not found in repository data. Cannot generate summaries.")
            return pd.DataFrame()
        if 'repo_artifact_id' not in repos_df.columns:
            print("Error: 'repo_artifact_id' column not found. This ID is crucial.")
            return pd.DataFrame()

        # Process in batches
        for start_idx in tqdm(range(0, len(repos_df), batch_size), desc="Generating Summaries"):
            end_idx = min(start_idx + batch_size, len(repos_df))
            batch_df_initial = repos_df.iloc[start_idx:end_idx]
            
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

        final_summarized_df = pd.concat(all_summaries_data, ignore_index=True)
            
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
