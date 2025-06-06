import pandas as pd
import numpy as np
from .data_manager import DataManager
from ..config.config_manager import ConfigManager
# from ..config.prompts.tag_mappings import TAG_TO_CATEGORY # Removed

class ConsolidatorStep:
    def __init__(self, data_manager: DataManager, config_manager: ConfigManager):
        self.data_manager = data_manager
        self.config_manager = config_manager

    def run(self):
        """Consolidate and analyze the classification results from all personas."""
        print("\nConsolidating analysis...")

        # Get the merged data from all personas
        # DataManager's get_categories_data() without persona_name should provide this.
        categorized_df = self.data_manager.get_categories_data()

        if categorized_df.empty:
            print("No categorized data found to consolidate. Skipping.")
            return pd.DataFrame()

        # Ensure essential columns are present
        if 'repo_artifact_id' not in categorized_df.columns and 'project_id' not in categorized_df.columns:
            print("Error: 'repo_artifact_id' or 'project_id' not found in categorized data.")
            return pd.DataFrame()
        
        # Use 'project_id' for grouping if available, else 'repo_artifact_id'
        # The original code used 'project_id' for project-level aggregation.
        # The raw data from OSO has 'project_id'. Summaries and categories should retain it.
        
        # Identify persona tag columns
        personas = self.config_manager.get_personas()
        persona_tag_cols = [f"{persona['name']}_tag" for persona in personas if f"{persona['name']}_tag" in categorized_df.columns]

        if not persona_tag_cols:
            print("No persona tag columns found in the categorized data. Cannot consolidate.")
            return categorized_df # Return as is, or an empty DF

        # Fill NaNs in numeric columns that might be used for weighting (e.g., star_count)
        # These columns should ideally come from the raw_repos_data or summaries_data.
        # The categorized_df from DataManager should already have these if merged correctly.
        numeric_cols_to_fill = ['star_count', 'fork_count', 'num_packages_in_deps_dev']
        for col in numeric_cols_to_fill:
            if col in categorized_df.columns:
                categorized_df[col] = categorized_df[col].fillna(0)
            else:
                # If star_count is missing, we can't do weighted summary as originally designed.
                # For now, we'll proceed without it if missing.
                print(f"Warning: Column '{col}' not found for consolidation. Weighted summary might be affected.")
        
        # Drop readme_md if it exists, as it's large and not needed for consolidation
        if 'readme_md' in categorized_df.columns:
            categorized_df = categorized_df.drop(columns=['readme_md'])

        # Group by project_id to consolidate recommendations
        # Define grouping keys. project_id is essential.
        grouping_keys = ['project_id']
        # Add other descriptive columns that should be unique per project or take the first
        if 'display_name' in categorized_df.columns: grouping_keys.append('display_name')
        if 'atlas_id' in categorized_df.columns: grouping_keys.append('atlas_id')
        
        # Ensure grouping keys are valid and exist in the DataFrame
        valid_grouping_keys = [key for key in grouping_keys if key in categorized_df.columns]
        if 'project_id' not in valid_grouping_keys:
            print("Critical error: 'project_id' is missing. Cannot perform project-level consolidation.")
            # Save the repo-level data with repo-level recommendations if project_id is missing
            # This part re-uses the previous logic for repo-level recommendation if grouping fails
            repo_recommendations = []
            if not categorized_df.empty and persona_tag_cols:
                for index, row in categorized_df.iterrows():
                    assignments = [row[col] for col in persona_tag_cols if pd.notna(row[col]) and row[col] not in ["Error", "N/A", "Other"]]
                    if assignments:
                        mode_series = pd.Series(assignments).mode()
                        repo_recommendations.append(mode_series[0] if not mode_series.empty else 'Other')
                    else:
                        repo_recommendations.append('Other')
                categorized_df['recommendation'] = repo_recommendations
            else:
                categorized_df['recommendation'] = 'Other'
            self.data_manager.save_consolidated_data(categorized_df)
            print("Consolidated analysis saved (repo-level due to missing project_id).")
            return categorized_df

        print(f"Consolidating at project level using keys: {valid_grouping_keys}")

        def aggregate_project_data(group):
            # New logic for star-weighted recommendation
            category_star_weights = {} # Stores sum of stars for each category

            for _, repo_row in group.iterrows(): # Iterate over each repo in the project
                stars = repo_row.get('star_count', 0) # star_count was already filled with 0 for NaNs
                
                # Ensure stars is a non-negative number (already handled by fillna(0) but good practice)
                if pd.isna(stars) or not isinstance(stars, (int, float)) or stars < 0:
                    stars = 0
                else:
                    stars = int(stars) # Ensure it's an integer for summation
                
                for p_col in persona_tag_cols: # Iterate over each persona's tag column
                    category = repo_row.get(p_col)
                    # Check if category is valid
                    if pd.notna(category) and category not in ["Error", "N/A", "Other"]:
                        category_star_weights[category] = category_star_weights.get(category, 0) + stars

            if not category_star_weights:
                recommendation = 'Other'
            else:
                # Find the category with the maximum accumulated star weight
                # pd.Series(category_star_weights).idxmax() returns the category (index) with the max value
                recommendation = pd.Series(category_star_weights).idxmax()

            # Aggregate other fields
            agg_data = {
                'recommendation': recommendation,
                'repo_artifact_namespaces': list(group['repo_artifact_namespace'].unique()) if 'repo_artifact_namespace' in group else [],
                'repo_count': group['repo_artifact_id'].nunique() if 'repo_artifact_id' in group else 0,
                'total_stars': group['star_count'].sum() if 'star_count' in group else 0,
                'total_forks': group['fork_count'].sum() if 'fork_count' in group else 0,
                # Add summaries of the top N repos or a combined summary if needed
                # For now, let's take the summary of the first repo in the group (by original order)
                'sample_summary': group['summary'].iloc[0] if 'summary' in group and not group['summary'].empty else ""
            }
            # Add persona tags for the project (e.g., mode of each persona's tags for this project)
            for p_col in persona_tag_cols:
                persona_project_tags = group[p_col].dropna().tolist()
                valid_persona_tags = [tag for tag in persona_project_tags if tag not in ["Error", "N/A", "Other"]]
                if valid_persona_tags:
                    agg_data[f"{p_col}_mode"] = pd.Series(valid_persona_tags).mode()[0] if pd.Series(valid_persona_tags).mode().any() else "N/A"
                else:
                    agg_data[f"{p_col}_mode"] = "N/A"

            return pd.Series(agg_data)

        # Group by valid_grouping_keys and apply aggregation
        # Use as_index=False if valid_grouping_keys are to be columns, otherwise they become index
        project_consolidated_df = categorized_df.groupby(valid_grouping_keys, as_index=False).apply(aggregate_project_data)
        
        # If groupby().apply() changes the structure unexpectedly (e.g. multi-index if as_index=True was used)
        # ensure project_consolidated_df is flat. With as_index=False, it should be.
        # If aggregate_project_data returns a Series, and groupby has as_index=False,
        # the result should be a DataFrame where grouping keys are columns, and new columns from Series.
        # If apply returns a DataFrame, it might need reset_index().
        # Let's ensure it's flat:
        if not isinstance(project_consolidated_df.index, pd.RangeIndex):
             project_consolidated_df = project_consolidated_df.reset_index()


        final_df = project_consolidated_df

        # Save results
        print(f"\nSaving consolidated analysis (project-level)...")
        self.data_manager.save_consolidated_data(final_df)
        print("Consolidated analysis saved successfully.")
        return final_df

if __name__ == '__main__':
    # Example Usage
    cfg_manager = ConfigManager()
    output_dir = cfg_manager.get_output_dir()
    dt_manager = DataManager(output_dir=output_dir, config=cfg_manager)

    # Ensure categorized data exists (run categorizer.py example first if needed)
    # DataManager's get_categories_data() should merge individual persona files.
    if dt_manager.get_categories_data().empty:
         print("No categorized data found. Please run CategorizerStep first or ensure data exists.")
    else:
        consolidator_step = ConsolidatorStep(
            data_manager=dt_manager,
            config_manager=cfg_manager
        )
        print("\nRunning ConsolidatorStep...")
        consolidated_df = consolidator_step.run()
        
        if not consolidated_df.empty:
            print(f"\nConsolidated data head:\n{consolidated_df.head()}")
            print(f"Number of rows in consolidated data: {len(consolidated_df)}")
            print(f"Consolidated columns: {consolidated_df.columns.tolist()}")
            print(f"\nRecommendations sample:\n{consolidated_df[['project_id', 'display_name', 'recommendation']].head() if 'project_id' in consolidated_df.columns and 'display_name' in consolidated_df.columns else consolidated_df['recommendation'].head()}")

        else:
            print("No data returned from consolidation step.")
