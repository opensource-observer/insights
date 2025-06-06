import pandas as pd
import json
from pathlib import Path
import shutil
from typing import List, Dict, Any
from ..config.settings import PROJECT_ROOT

class DataManager:
    def __init__(self, output_dir: Path, config=None):
        self.output_dir = output_dir
        self.config = config  # For future use, e.g., different storage backends
        
        # Legacy paths
        self.raw_parquet_path = self.output_dir / "devtooling_raw.parquet"
        self.summarized_parquet_path = self.output_dir / "devtooling_summarized.parquet"
        self.categorized_dir = self.output_dir / "categorized"
        self.final_parquet_path = self.output_dir / "devtooling_full.parquet"
        self.consolidated_csv_path = self.output_dir / "devtooling_consolidated.csv"
        
        # New unified data paths - ensure they're in the current repo's output directory
        local_output_dir = Path(PROJECT_ROOT) / "output"
        local_output_dir.mkdir(parents=True, exist_ok=True)
        self.unified_parquet_path = local_output_dir / "ethereum_repos_unified.parquet"
        self.unified_csv_path = local_output_dir / "ethereum_repos_unified.csv"

        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.categorized_dir.mkdir(parents=True, exist_ok=True)

    def get_repos_data(self) -> pd.DataFrame:
        """Get the latest repository data"""
        if self.raw_parquet_path.exists():
            return pd.read_parquet(self.raw_parquet_path)
        return pd.DataFrame()

    def get_summaries_data(self) -> pd.DataFrame:
        """Get the latest summaries data"""
        if self.summarized_parquet_path.exists():
            return pd.read_parquet(self.summarized_parquet_path)
        return pd.DataFrame()

    def get_categories_data(self, persona_name: str = None) -> pd.DataFrame:
        """Get the latest categories data, optionally for a specific persona or all."""
        if persona_name:
            persona_file = self.categorized_dir / f"{persona_name}.parquet"
            if persona_file.exists():
                return pd.read_parquet(persona_file)
            return pd.DataFrame()
        else:
            # Combine all persona files
            all_persona_dfs = []
            for persona_file in self.categorized_dir.glob("*.parquet"):
                df = pd.read_parquet(persona_file)
                all_persona_dfs.append(df)
            
            if not all_persona_dfs:
                return pd.DataFrame()

            # Concatenate all dataframes. If a project appears in multiple files,
            # the last one read will take precedence for shared columns (like 'summary').
            # Persona-specific columns (e.g., 'persona_X_tag') will be unique.
            # We need a more robust way to merge these if there are overlapping non-persona columns.
            # For now, assuming 'project_id' or 'repo_artifact_id' is the key.
            
            # A simple concat might lead to duplicate columns if not handled carefully.
            # Let's assume each persona file has unique columns for its tags/reasons.
            # And common columns like 'project_id', 'summary' are present.
            
            # Start with the summaries data as the base
            base_df = self.get_summaries_data()
            if base_df.empty:
                 # If no summaries, try to load from the first persona file as a base
                if all_persona_dfs:
                    base_df = all_persona_dfs[0][['project_id', 'repo_artifact_id', 'summary']].copy() # Adjust columns as needed
                else:
                    return pd.DataFrame()


            # Set index for joining
            if 'repo_artifact_id' in base_df.columns:
                base_df = base_df.set_index('repo_artifact_id')
            elif 'project_id' in base_df.columns:
                 base_df = base_df.set_index('project_id')
            else:
                # Fallback if no clear index, this might lead to issues
                print("Warning: No clear index (project_id or repo_artifact_id) for merging category data.")


            for df_persona in all_persona_dfs:
                # Identify the persona name from its columns (e.g., "keyword_spotter_tag")
                current_persona_name = None
                for col_name in df_persona.columns:
                    if col_name.endswith("_tag"):
                        current_persona_name = col_name.replace("_tag", "")
                        break
                
                if not current_persona_name:
                    print(f"Warning: Could not determine persona name from columns in a categorized file. Skipping this file.")
                    continue

                # Columns to join are just the tag and reason for this specific persona
                persona_tag_col = f"{current_persona_name}_tag"
                persona_reason_col = f"{current_persona_name}_reason"
                
                cols_from_persona_df = []
                if persona_tag_col in df_persona.columns:
                    cols_from_persona_df.append(persona_tag_col)
                if persona_reason_col in df_persona.columns:
                    cols_from_persona_df.append(persona_reason_col)

                if not cols_from_persona_df:
                    print(f"Warning: No tag/reason columns found for persona {current_persona_name} in its file. Skipping join for this persona.")
                    continue
                
                # Set index for df_persona before selecting columns for join
                if base_df.index.name in df_persona.columns: # base_df.index.name is 'repo_artifact_id' or 'project_id'
                    df_persona_indexed = df_persona.set_index(base_df.index.name)
                else:
                    print(f"Warning: Index column '{base_df.index.name}' not found in persona DataFrame for {current_persona_name}. Attempting join without re-indexing persona df, might be incorrect.")
                    df_persona_indexed = df_persona # This might lead to issues if not indexed properly

                # Ensure only existing columns are selected from df_persona_indexed
                valid_cols_to_join = [col for col in cols_from_persona_df if col in df_persona_indexed.columns]

                if not valid_cols_to_join:
                     print(f"Warning: Persona specific columns {cols_from_persona_df} not found as actual columns in indexed persona dataframe for {current_persona_name}. Skipping join for this persona.")
                     continue
                
                base_df = base_df.join(df_persona_indexed[valid_cols_to_join], how='left', rsuffix=f'_{current_persona_name}_dup')
                
                # Clean up duplicate columns if any (this is a basic cleanup for rsuffix)
                cols_to_drop = [col for col in base_df.columns if '_dup' in col]
                base_df.drop(columns=cols_to_drop, inplace=True, errors='ignore')

            return base_df.reset_index()


    def save_repos_data(self, data: pd.DataFrame):
        """Save repository data"""
        data.to_parquet(self.raw_parquet_path, index=False)
        print(f"Repository data saved to {self.raw_parquet_path}")

    def save_summaries_data(self, data: pd.DataFrame, append: bool = False):
        """Save summaries data. If append is True, appends to existing file if it exists."""
        if append and self.summarized_parquet_path.exists():
            existing_df = pd.read_parquet(self.summarized_parquet_path)
            # Ensure no duplicate columns before concat, especially if 'summary' is regenerated
            # A more robust merge/update might be needed depending on exact requirements
            data_to_save = pd.concat([existing_df, data]).drop_duplicates(subset=['repo_artifact_id'], keep='last') # Assuming repo_artifact_id is unique key
        else:
            data_to_save = data
        data_to_save.to_parquet(self.summarized_parquet_path, index=False)
        print(f"Summaries data saved to {self.summarized_parquet_path}")

    def save_categories_data(self, data: pd.DataFrame, persona_name: str):
        """Save categories data for a specific persona"""
        persona_file = self.categorized_dir / f"{persona_name}.parquet"
        data.to_parquet(persona_file, index=False)
        print(f"Categories data for persona {persona_name} saved to {persona_file}")
        
    def save_consolidated_data(self, data: pd.DataFrame):
        """Save consolidated data to Parquet and CSV"""
        data.to_parquet(self.final_parquet_path, index=False)
        print(f"Consolidated Parquet data saved to {self.final_parquet_path}")
        data.to_csv(self.consolidated_csv_path, index=False)
        print(f"Consolidated CSV data saved to {self.consolidated_csv_path}")

    def wipe_repos_data(self):
        """Wipe repository data"""
        if self.raw_parquet_path.exists():
            self.raw_parquet_path.unlink()
            print(f"Wiped repository data: {self.raw_parquet_path}")

    def wipe_summaries_data(self):
        """Wipe summaries data"""
        if self.summarized_parquet_path.exists():
            self.summarized_parquet_path.unlink()
            print(f"Wiped summaries data: {self.summarized_parquet_path}")

    def wipe_categories_data(self, persona_name: str = None):
        """Wipe categories data, optionally for a specific persona or all."""
        if persona_name:
            persona_file = self.categorized_dir / f"{persona_name}.parquet"
            if persona_file.exists():
                persona_file.unlink()
                print(f"Wiped categories data for persona {persona_name}: {persona_file}")
        else:
            if self.categorized_dir.exists():
                shutil.rmtree(self.categorized_dir)
                self.categorized_dir.mkdir(parents=True, exist_ok=True) # Recreate after wiping
                print(f"Wiped all categories data in {self.categorized_dir}")
                
    def has_categories_for_persona(self, persona_name: str) -> bool:
        """Check if category data exists for a specific persona."""
        persona_file = self.categorized_dir / f"{persona_name}.parquet"
        return persona_file.exists()

    def get_final_parquet_path(self) -> Path:
        return self.final_parquet_path

    def get_consolidated_csv_path(self) -> Path:
        return self.consolidated_csv_path
        
    # New methods for unified data structure
    
    def save_unified_data(self, data: pd.DataFrame):
        """
        Save unified repository data to Parquet and CSV.
        This data includes all repositories, summaries, and categorizations in a single structure.
        """
        # Ensure categorizations column is properly serialized for Parquet
        if 'categorizations' in data.columns:
            # Convert categorizations to strings for storage
            # This is necessary because Parquet doesn't handle complex nested structures well
            data_copy = data.copy()
            data_copy['categorizations_json'] = data_copy['categorizations'].apply(
                lambda x: json.dumps(x) if isinstance(x, list) else '[]'
            )
            
            # Save to Parquet (without the original categorizations column)
            parquet_data = data_copy.drop(columns=['categorizations'])
            parquet_data.to_parquet(self.unified_parquet_path, index=False)
            print(f"Unified data saved to {self.unified_parquet_path}")
            
            # Save to CSV for easier viewing (also without the complex column)
            csv_data = parquet_data.copy()
            
            # Remove README text and truncate long text fields for CSV readability
            if 'readme_md' in csv_data.columns:
                csv_data = csv_data.drop(columns=['readme_md'])
                
            if 'summary' in csv_data.columns:
                csv_data['summary'] = csv_data['summary'].apply(
                    lambda x: (x[:100] + '...') if isinstance(x, str) and len(x) > 100 else x
                )
                
            # Truncate other potentially long text fields
            for col in ['categorizations_json']:
                if col in csv_data.columns:
                    csv_data[col] = csv_data[col].apply(
                        lambda x: (x[:50] + '...') if isinstance(x, str) and len(x) > 50 else x
                    )
                    
            csv_data.to_csv(self.unified_csv_path, index=False)
            print(f"Unified CSV data saved to {self.unified_csv_path} (README text removed)")
        else:
            # If no categorizations column, save as is
            data.to_parquet(self.unified_parquet_path, index=False)
            print(f"Unified data saved to {self.unified_parquet_path}")
            
            # Create a readable CSV version
            csv_data = data.copy()
            
            # Remove README text and truncate long text fields for CSV readability
            if 'readme_md' in csv_data.columns:
                csv_data = csv_data.drop(columns=['readme_md'])
                
            if 'summary' in csv_data.columns:
                csv_data['summary'] = csv_data['summary'].apply(
                    lambda x: (x[:100] + '...') if isinstance(x, str) and len(x) > 100 else x
                )
                
            csv_data.to_csv(self.unified_csv_path, index=False)
            print(f"Unified CSV data saved to {self.unified_csv_path} (README text removed)")
    
    def get_unified_data(self) -> pd.DataFrame:
        """
        Get the unified repository data with properly deserialized categorizations.
        """
        if not self.unified_parquet_path.exists():
            return pd.DataFrame()
            
        # Load the data from Parquet
        data = pd.read_parquet(self.unified_parquet_path)
        
        # Deserialize the categorizations from JSON if present
        if 'categorizations_json' in data.columns:
            data['categorizations'] = data['categorizations_json'].apply(
                lambda x: json.loads(x) if isinstance(x, str) else []
            )
            data = data.drop(columns=['categorizations_json'])
            
        return data
    
    def append_unified_data(self, new_repo_data: pd.DataFrame) -> None:
        """
        Append a single repository or multiple repositories to the existing unified data.
        
        Args:
            new_repo_data: DataFrame containing the new repository data to append
        """
        if new_repo_data.empty:
            return
            
        existing_data = self.get_unified_data()
        
        if existing_data.empty:
            # If no existing data, just save the new data
            self.save_unified_data(new_repo_data)
            return
            
        # Combine existing and new data
        combined_data = pd.concat([existing_data, new_repo_data], ignore_index=True)
        
        # Remove duplicates based on repo_artifact_id, keeping the newest version
        combined_data = combined_data.sort_values('processing_timestamp', ascending=False)
        combined_data = combined_data.drop_duplicates(subset=['repo_artifact_id'], keep='first')
        
        # Save the combined data
        self.save_unified_data(combined_data)
        
    def update_unified_data(self, updated_repo_data: pd.DataFrame) -> None:
        """
        Update specific repositories in the existing unified data.
        
        Args:
            updated_repo_data: DataFrame containing the updated repository data
        """
        if updated_repo_data.empty:
            return
            
        existing_data = self.get_unified_data()
        
        if existing_data.empty:
            # If no existing data, just save the updated data
            self.save_unified_data(updated_repo_data)
            return
            
        # Get the repo_artifact_ids of the updated repositories
        updated_ids = set(updated_repo_data['repo_artifact_id'])
        
        # Remove the repositories that are being updated from the existing data
        filtered_existing = existing_data[~existing_data['repo_artifact_id'].isin(updated_ids)]
        
        # Combine the filtered existing data with the updated data
        combined_data = pd.concat([filtered_existing, updated_repo_data], ignore_index=True)
        
        # Save the combined data
        self.save_unified_data(combined_data)
    
    def wipe_unified_data(self):
        """Wipe unified data files"""
        if self.unified_parquet_path.exists():
            self.unified_parquet_path.unlink()
            print(f"Wiped unified data: {self.unified_parquet_path}")
        if self.unified_csv_path.exists():
            self.unified_csv_path.unlink()
            print(f"Wiped unified CSV data: {self.unified_csv_path}")
            
    def get_checkpoint_path(self) -> Path:
        """Get the path to the processing checkpoint file"""
        local_output_dir = Path(PROJECT_ROOT) / "output"
        local_output_dir.mkdir(parents=True, exist_ok=True)
        return local_output_dir / "processing_checkpoint.json"
        
    def save_checkpoint(self, checkpoint_data: Dict[str, Any]) -> None:
        """
        Save the processing checkpoint data to a JSON file.
        
        Args:
            checkpoint_data: Dictionary containing checkpoint information
        """
        checkpoint_path = self.get_checkpoint_path()
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
            
    def load_checkpoint(self) -> Dict[str, Any]:
        """
        Load the processing checkpoint data from a JSON file.
        
        Returns:
            Dictionary containing checkpoint information, or empty dict if no checkpoint exists
        """
        checkpoint_path = self.get_checkpoint_path()
        if not checkpoint_path.exists():
            return {
                "last_processed_repo_id": None,
                "processed_repos": [],
                "partial_results": {}
            }
            
        try:
            with open(checkpoint_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading checkpoint: {e}")
            return {
                "last_processed_repo_id": None,
                "processed_repos": [],
                "partial_results": {}
            }
