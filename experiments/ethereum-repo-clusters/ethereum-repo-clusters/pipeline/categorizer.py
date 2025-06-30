import pandas as pd
from tqdm import tqdm
from .data_manager import DataManager
from ..config.config_manager import ConfigManager
from ..processing.ai_service import AIService, ClassificationOutput

class CategorizerStep:
    def __init__(self, data_manager: DataManager, config_manager: ConfigManager, ai_service: AIService):
        self.data_manager = data_manager
        self.config_manager = config_manager
        self.ai_service = ai_service

    def run(self, force_refresh: bool = False, target_persona_name: str = None, new_only: bool = False):
        """
        Categorize projects using AI personas.
        Uses batch_size_categorization from config.
        
        Args:
            force_refresh: If True, wipe existing categories and regenerate all
            target_persona_name: If specified, only process this persona
            new_only: If True, only categorize repositories that don't have categories yet
        """
        batch_size = self.config_manager.get_batch_size_categorization()
        
        if force_refresh:
            if target_persona_name:
                print(f"Force refresh enabled for persona '{target_persona_name}'. Wiping existing category data for this persona.")
                self.data_manager.wipe_categories_data(persona_name=target_persona_name)
            else:
                print("Force refresh enabled for all personas. Wiping all existing category data.")
                self.data_manager.wipe_categories_data()

        # Get summaries data
        summaries_df = self.data_manager.get_summaries_data()
        if summaries_df.empty:
            print("No summarized data found to categorize. Skipping.")
            return pd.DataFrame()
        
        if 'summary' not in summaries_df.columns:
            print("Error: 'summary' column not found in summarized data. Cannot categorize.")
            return pd.DataFrame()
        if 'repo_artifact_id' not in summaries_df.columns:
            print("Error: 'repo_artifact_id' not found in summarized data.")
            return pd.DataFrame()

        # Get personas to process
        personas_to_process = []
        if target_persona_name:
            persona = self.config_manager.get_persona(target_persona_name)
            if persona:
                personas_to_process = [persona]
            else:
                print(f"Error: Persona '{target_persona_name}' not found.")
                return pd.DataFrame()
        else:
            personas_to_process = self.config_manager.get_personas()

        if not personas_to_process:
            print("No personas found to process.")
            return pd.DataFrame()

        # Process each persona
        for persona in personas_to_process:
            persona_name = persona['name']
            print(f"\nProcessing persona: {persona_name}")
            
            # Get existing categories for this persona if any
            existing_categories_df = pd.DataFrame()
            if not force_refresh:
                try:
                    existing_categories_df = self.data_manager.get_categories_data(persona_name)
                except FileNotFoundError:
                    pass  # No existing categories for this persona

            # If we have existing categories and not forcing refresh
            if not existing_categories_df.empty and not force_refresh:
                if new_only:
                    # Filter out repositories that already have categories
                    existing_repos = set(existing_categories_df['repo_artifact_id'])
                    repos_to_process = summaries_df[~summaries_df['repo_artifact_id'].isin(existing_repos)]
                    if repos_to_process.empty:
                        print(f"No new repositories found to categorize for persona '{persona_name}'.")
                        continue
                    print(f"Found {len(repos_to_process)} new repositories to categorize for persona '{persona_name}'.")
                else:
                    print(f"Categories already exist for persona '{persona_name}' and force_refresh is false. Skipping.")
                    continue
            else:
                repos_to_process = summaries_df

            # Process in batches
            all_categorized_data = []
            for start_idx in tqdm(range(0, len(repos_to_process), batch_size), desc=f"Categorizing ({persona_name})", leave=False):
                end_idx = min(start_idx + batch_size, len(repos_to_process))
                batch_df = repos_to_process.iloc[start_idx:end_idx]
                
                # Prepare list of dicts, each containing summary and metadata for a project
                project_data_batch = []
                required_metadata_cols = ['star_count', 'fork_count', 'language', 'created_at', 'updated_at']
                for _, row in batch_df.iterrows():
                    project_data = {
                        'summary': row.get('summary', ''),
                        'repo_artifact_id': row.get('repo_artifact_id', 'UNKNOWN_ID') 
                    }
                    for col in required_metadata_cols:
                        project_data[col] = row.get(col) # Will be None if missing, pandas NaT for dates
                    project_data_batch.append(project_data)

                if not project_data_batch or all(not item['summary'] for item in project_data_batch):
                    print(f"Skipping batch for {persona_name} as all summaries are effectively empty.")
                    classifications = [ClassificationOutput(assigned_tag="N/A", reason="Empty summary or batch")] * len(project_data_batch)
                else:
                    classifications: List[ClassificationOutput] = self.ai_service.classify_projects_batch_for_persona(
                        project_data_batch,
                        persona
                    )
                
                # Create a temporary DataFrame for this batch's results
                temp_batch_df = batch_df.copy() 
                temp_batch_df[f"{persona_name}_tag"] = [c.assigned_tag for c in classifications]
                temp_batch_df[f"{persona_name}_reason"] = [c.reason for c in classifications]
                all_categorized_data.append(temp_batch_df)

            if not all_categorized_data:
                print(f"No categories were generated for persona '{persona_name}'.")
                continue

            new_categories_df = pd.concat(all_categorized_data, ignore_index=True)
            
            # If we have existing categories and not forcing refresh, combine with new ones
            if not existing_categories_df.empty and not force_refresh:
                final_categories_df = pd.concat([existing_categories_df, new_categories_df], ignore_index=True)
                # Remove any duplicates that might have been introduced
                final_categories_df = final_categories_df.drop_duplicates(
                    subset=['repo_artifact_id'],
                    keep='last'  # Keep the new categorization if there was a duplicate
                )
                print(f"Combined data now contains {len(final_categories_df)} repositories with categories for persona '{persona_name}'.")
            else:
                final_categories_df = new_categories_df
                
            self.data_manager.save_categories_data(final_categories_df, persona_name)

        return pd.DataFrame()  # Return empty DataFrame as we've saved the data


if __name__ == '__main__':
    # Example Usage
    cfg_manager = ConfigManager()
    ai_svc = AIService(config_manager=cfg_manager)
    output_dir = cfg_manager.get_output_dir()
    dt_manager = DataManager(output_dir=output_dir, config=cfg_manager)

    if dt_manager.get_summaries_data().empty:
        print("No summarized data found. Please run SummaryGeneratorStep first or ensure data exists.")
    else:
        categorizer_step = CategorizerStep(
            data_manager=dt_manager,
            config_manager=cfg_manager,
            ai_service=ai_svc
        )
        print("\nRunning CategorizerStep...")
        # Set force_refresh=True to re-categorize.
        # Specify target_persona_name="keyword_spotter" to only run for one.
        categorized_data = categorizer_step.run(force_refresh=False, target_persona_name=None) 
        
        if not categorized_data.empty:
            print(f"\nCategorized data head:\n{categorized_data.head()}")
            print(f"Number of rows in categorized data: {len(categorized_data)}")
            print(f"Columns: {categorized_data.columns.tolist()}")
        else:
            print("No data returned from categorization step.")
