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

    def run(self, force_refresh: bool = False, target_persona_name: str = None):
        """
        Categorize projects using AI personas.
        Uses batch_size_categorization from config.
        If target_persona_name is specified, only that persona is processed.
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
        if 'repo_artifact_id' not in summaries_df.columns: # or 'project_id'
            print("Error: 'repo_artifact_id' (or 'project_id') not found in summarized data.")
            return pd.DataFrame()

        personas_to_process = []
        if target_persona_name:
            persona = next((p for p in self.config_manager.get_personas() if p['name'] == target_persona_name), None)
            if persona:
                personas_to_process.append(persona)
            else:
                print(f"Persona '{target_persona_name}' not found in configuration.")
                return self.data_manager.get_categories_data() # Return existing data
        else:
            personas_to_process = self.config_manager.get_personas()

        if not personas_to_process:
            print("No personas configured or specified for categorization.")
            return self.data_manager.get_categories_data()

        print(f"Categorizing {len(summaries_df)} projects using {len(personas_to_process)} persona(s) in batches of {batch_size}...")

        # This will hold the dataframe with all persona classifications
        # Start with the summaries_df and add columns for each persona
        # This is complex because each persona's data is saved separately.
        # The DataManager's get_categories_data(persona_name=None) handles merging.
        
        for persona in tqdm(personas_to_process, desc="Processing Personas"):
            persona_name = persona["name"]
            
            # Skip if already processed for this persona and not forcing refresh
            if not force_refresh and self.data_manager.has_categories_for_persona(persona_name):
                print(f"Category data for persona '{persona_name}' already exists and force_refresh is false. Skipping.")
                continue

            print(f"\nProcessing persona: {persona_name}")
            
            # Dataframe for this persona's results
            # We need to select relevant columns from summaries_df to avoid large duplications.
            # Key identifier (e.g. repo_artifact_id) and summary are important.
            # Other columns from summaries_df might also be useful context.
            persona_results_df_list = []

            for start_idx in tqdm(range(0, len(summaries_df), batch_size), desc=f"Categorizing ({persona_name})", leave=False):
                end_idx = min(start_idx + batch_size, len(summaries_df))
                batch_df = summaries_df.iloc[start_idx:end_idx]
                
                # Prepare list of dicts, each containing summary and metadata for a project
                project_data_batch = []
                required_metadata_cols = ['star_count', 'fork_count', 'created_at', 'updated_at']
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
                        project_data_batch, # Pass list of dicts
                        persona
                    )
                
                # Create a temporary DataFrame for this batch's results
                # batch_df is the slice of summaries_df, so it's suitable as a base
                temp_batch_df = batch_df.copy() 
                temp_batch_df[f"{persona_name}_tag"] = [c.assigned_tag for c in classifications]
                temp_batch_df[f"{persona_name}_reason"] = [c.reason for c in classifications]
                
                persona_results_df_list.append(temp_batch_df)
            
            if persona_results_df_list:
                # Concatenate all batch results for the current persona
                full_persona_df = pd.concat(persona_results_df_list, ignore_index=True)
                # Select only necessary columns to save for this persona to avoid massive duplication
                # Key ID, summary, and this persona's tag/reason.
                # Other columns from summaries_df can be joined back during consolidation.
                cols_to_save = ['repo_artifact_id', 'project_id', 'summary', f"{persona_name}_tag", f"{persona_name}_reason"]
                # Filter out columns not present in full_persona_df
                cols_to_save = [col for col in cols_to_save if col in full_persona_df.columns]

                self.data_manager.save_categories_data(full_persona_df[cols_to_save], persona_name=persona_name)
            else:
                print(f"No categorization results generated for persona '{persona_name}'.")
                # Save an empty df for this persona if force_refresh was true, to mark it as "processed"
                if force_refresh:
                     self.data_manager.save_categories_data(pd.DataFrame(columns=['repo_artifact_id', 'project_id', 'summary', f"{persona_name}_tag", f"{persona_name}_reason"]), persona_name=persona_name)


        print("Categorization step complete.")
        # The DataManager will handle merging these when get_categories_data() is called without a persona name.
        return self.data_manager.get_categories_data()


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
