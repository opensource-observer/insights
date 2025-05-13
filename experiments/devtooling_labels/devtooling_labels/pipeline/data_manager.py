import pandas as pd
from pathlib import Path
import shutil

class DataManager:
    def __init__(self, output_dir: Path, config=None):
        self.output_dir = output_dir
        self.config = config  # For future use, e.g., different storage backends
        self.raw_parquet_path = self.output_dir / "devtooling_raw.parquet"
        self.summarized_parquet_path = self.output_dir / "devtooling_summarized.parquet"
        self.categorized_dir = self.output_dir / "categorized"
        self.final_parquet_path = self.output_dir / "devtooling_full.parquet"
        self.consolidated_csv_path = self.output_dir / "devtooling_consolidated.csv"

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
