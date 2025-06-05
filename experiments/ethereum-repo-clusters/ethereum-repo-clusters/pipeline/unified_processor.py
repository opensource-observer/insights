import pandas as pd
import datetime
import json
from typing import List, Dict, Any, Optional
from tqdm import tqdm
from .data_manager import DataManager
from ..config.config_manager import ConfigManager
from ..processing.ai_service import AIService, SummaryOutput, ClassificationOutput
from ..processing.fetcher import DataFetcher

class UnifiedProcessor:
    def __init__(self, data_manager: DataManager, config_manager: ConfigManager, ai_service: AIService):
        self.data_manager = data_manager
        self.config_manager = config_manager
        self.ai_service = ai_service
        self.fetcher = DataFetcher()
        
    def run(self, 
            force_refresh: bool = False, 
            include_forks: bool = False, 
            inactive_repos: bool = False,
            limit: Optional[int] = None):
        """
        Unified processing pipeline that fetches repositories, READMEs, generates summaries,
        and categorizes them in a single pass.
        
        Args:
            force_refresh: If True, wipe existing data and process everything fresh
            include_forks: If True, include forked repositories in processing
            inactive_repos: If True, include repositories not updated in the last year
            limit: Optional limit on number of repositories to process
        """
        # Get test mode settings
        is_test = self.config_manager.is_test_mode()
        if is_test:
            test_limit = self.config_manager.get_test_mode_limit()
            if limit is None or limit > test_limit:
                limit = test_limit
            print(f"Running in TEST MODE: Limiting to {limit} repositories, sorted by stars DESC.")
        
        # Determine batch sizes
        batch_size = min(
            self.config_manager.get_batch_size_summaries(),
            self.config_manager.get_batch_size_categorization()
        )
        
        # Get existing data if not forcing refresh
        if force_refresh:
            print("Force refresh enabled. Wiping existing data.")
            self.data_manager.wipe_repos_data()
            existing_df = pd.DataFrame()
        else:
            existing_df = self.data_manager.get_repos_data()
            if not existing_df.empty:
                print(f"Found existing data with {len(existing_df)} repositories.")
        
        # Fetch repositories from OSO
        print("Fetching repositories from OSO...")
        repos_df = self.fetcher.fetch_repositories(limit=limit, sort_by_stars=True)
        
        if repos_df.empty:
            print("No repositories found from OSO fetch.")
            return pd.DataFrame()
        
        print(f"Found {len(repos_df)} repositories from OSO.")
        
        # Filter repositories based on parameters
        if not include_forks:
            repos_df = repos_df[~repos_df['is_fork']]
            print(f"Filtered out forks. {len(repos_df)} repositories remaining.")
        
        if not inactive_repos:
            repos_df = repos_df[repos_df['is_actively_maintained']]
            print(f"Filtered out inactive repositories. {len(repos_df)} repositories remaining.")
        
        # Determine which repositories need processing
        if not existing_df.empty and not force_refresh:
            # Identify repositories that have already been fully processed
            processed_repos = set()
            if 'categorizations' in existing_df.columns:
                processed_repos = set(
                    existing_df[existing_df['categorizations'].apply(lambda x: isinstance(x, list) and len(x) > 0)]['repo_artifact_id']
                )
            
            # Filter out already processed repositories
            repos_to_process = repos_df[~repos_df['repo_artifact_id'].isin(processed_repos)]
            print(f"Found {len(repos_to_process)} repositories that need processing.")
            
            # Combine with existing data for final output
            combined_df = pd.concat([
                existing_df[existing_df['repo_artifact_id'].isin(processed_repos)],
                self._process_repositories(repos_to_process, batch_size)
            ], ignore_index=True)
            
            # Save the combined data
            self.data_manager.save_unified_data(combined_df)
            return combined_df
        else:
            # Process all repositories
            processed_df = self._process_repositories(repos_df, batch_size)
            self.data_manager.save_unified_data(processed_df)
            return processed_df
    
    def _process_repositories(self, repos_df: pd.DataFrame, batch_size: int) -> pd.DataFrame:
        """
        Process repositories in batches: fetch READMEs, generate summaries, and categorize.
        
        Args:
            repos_df: DataFrame containing repositories to process
            batch_size: Number of repositories to process in each batch
            
        Returns:
            DataFrame with processed repositories
        """
        print(f"Processing {len(repos_df)} repositories in batches of {batch_size}...")
        
        # Get personas for categorization
        personas = self.config_manager.get_personas()
        if not personas:
            print("No personas found for categorization.")
            return repos_df
        
        # Process in batches
        all_processed_data = []
        
        for start_idx in tqdm(range(0, len(repos_df), batch_size), desc="Processing Repositories"):
            end_idx = min(start_idx + batch_size, len(repos_df))
            batch_df = repos_df.iloc[start_idx:end_idx].copy()
            
            # Fetch READMEs for this batch
            batch_df = self.fetcher.get_all_readmes(batch_df)
            
            # Initialize the categorizations column with empty lists
            batch_df['categorizations'] = [[] for _ in range(len(batch_df))]
            batch_df['final_recommendation'] = 'UNCATEGORIZED'
            batch_df['processing_timestamp'] = datetime.datetime.now().isoformat()
            batch_df['summary'] = ''
            
            # Process each repository in the batch
            for idx, row in tqdm(batch_df.iterrows(), desc="Processing repositories in batch", total=len(batch_df), leave=False):
                # Initialize categorizations list
                categorizations = []
                
                # Get README status
                readme_status = row.get('readme_status', 'ERROR')
                
                # Generate summary if README is available
                summary = ""
                if readme_status == "SUCCESS":
                    readme_content = row.get('readme_md', "")
                    summary_output: SummaryOutput = self.ai_service.make_summary(readme_content)
                    summary = summary_output.summary
                    
                    # Categorize with each persona
                    for persona in tqdm(personas, desc=f"Categorizing {row.get('repo_artifact_name', 'repo')} with personas", leave=False):
                        try:
                            # Prepare project data for categorization
                            project_data = {
                                'summary': summary,
                                'repo_artifact_id': row.get('repo_artifact_id', 'UNKNOWN_ID'),
                                'star_count': row.get('star_count', 0),
                                'fork_count': row.get('fork_count', 0),
                                'created_at': row.get('created_at'),
                                'updated_at': row.get('updated_at')
                            }
                            
                            # Get categorization from this persona
                            classifications = self.ai_service.classify_projects_batch_for_persona(
                                [project_data],
                                persona
                            )
                            
                            if classifications and len(classifications) > 0:
                                classification = classifications[0]
                                categorizations.append({
                                    'persona_name': persona['name'],
                                    'category': classification.assigned_tag,
                                    'reason': classification.reason,
                                    'timestamp': datetime.datetime.now().isoformat()
                                })
                            else:
                                categorizations.append({
                                    'persona_name': persona['name'],
                                    'category': 'UNCATEGORIZED',
                                    'reason': 'Failed to get classification from AI service',
                                    'timestamp': datetime.datetime.now().isoformat()
                                })
                        except Exception as e:
                            print(f"Error categorizing with persona {persona['name']}: {e}")
                            categorizations.append({
                                'persona_name': persona['name'],
                                'category': 'UNCATEGORIZED',
                                'reason': f'Error: {str(e)}',
                                'timestamp': datetime.datetime.now().isoformat()
                            })
                else:
                    # If README is empty or error, mark all categorizations as UNCATEGORIZED
                    for persona in tqdm(personas, desc=f"Marking {row.get('repo_artifact_name', 'repo')} as UNCATEGORIZED", leave=False):
                        categorizations.append({
                            'persona_name': persona['name'],
                            'category': 'UNCATEGORIZED',
                            'reason': f'README {readme_status}',
                            'timestamp': datetime.datetime.now().isoformat()
                        })
                
                # Determine final recommendation based on categorizations
                final_recommendation = self._determine_final_recommendation(categorizations, row.get('star_count', 0))
                
                # Update the row with processed data
                batch_df.at[idx, 'summary'] = summary
                batch_df.at[idx, 'categorizations'] = categorizations
                batch_df.at[idx, 'final_recommendation'] = final_recommendation
                batch_df.at[idx, 'processing_timestamp'] = datetime.datetime.now().isoformat()
            
            all_processed_data.append(batch_df)
        
        if not all_processed_data:
            print("No data was processed.")
            return pd.DataFrame()
        
        return pd.concat(all_processed_data, ignore_index=True)
    
    def _determine_final_recommendation(self, categorizations: List[Dict[str, Any]], star_count: int) -> str:
        """
        Determine the final recommendation based on categorizations from all personas.
        
        Args:
            categorizations: List of categorization dictionaries
            star_count: Star count of the repository (for potential future weighting)
            
        Returns:
            Final category recommendation
        """
        # Filter out UNCATEGORIZED entries
        valid_categories = [c['category'] for c in categorizations if c['category'] != 'UNCATEGORIZED']
        
        if not valid_categories:
            return 'UNCATEGORIZED'
        
        # Count occurrences of each category
        category_counts = {}
        for category in valid_categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Find the most common category
        max_count = 0
        final_category = 'UNCATEGORIZED'
        
        for category, count in category_counts.items():
            if count > max_count:
                max_count = count
                final_category = category
        
        return final_category


if __name__ == '__main__':
    # Example Usage
    cfg_manager = ConfigManager()
    ai_svc = AIService(config_manager=cfg_manager)
    output_dir = cfg_manager.get_output_dir()
    dt_manager = DataManager(output_dir=output_dir, config=cfg_manager)
    
    processor = UnifiedProcessor(
        data_manager=dt_manager,
        config_manager=cfg_manager,
        ai_service=ai_svc
    )
    
    print("\nRunning UnifiedProcessor...")
    processed_data = processor.run(
        force_refresh=False,
        include_forks=False,
        inactive_repos=False
    )
    
    if not processed_data.empty:
        print(f"\nProcessed data head:\n{processed_data.head()}")
        print(f"Number of rows processed: {len(processed_data)}")
