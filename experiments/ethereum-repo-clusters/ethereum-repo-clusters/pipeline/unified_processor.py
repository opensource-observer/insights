import pandas as pd
import datetime
import json
import time
from typing import List, Dict, Any, Optional, Set
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
        
        # Load checkpoint or initialize a new one
        if force_refresh:
            print("Force refresh enabled. Wiping existing data and checkpoint.")
            self.data_manager.wipe_unified_data()
            self._initialize_checkpoint()
            existing_df = pd.DataFrame()
        else:
            existing_df = self.data_manager.get_unified_data()
            if not existing_df.empty:
                print(f"Found existing data with {len(existing_df)} repositories.")
        
        # Fetch repositories from OSO
        print("Fetching repositories from OSO...")
        repos_df = self.fetcher.fetch_repositories(limit=limit, sort_by_stars=True, min_stars=self.config_manager.get_min_stars())
        
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
        
        # Load checkpoint to determine which repositories need processing
        checkpoint = self.data_manager.load_checkpoint()
        processed_repos = set(checkpoint.get("processed_repos", []))
        
        # Determine which repositories need processing
        if not force_refresh:
            # Filter out already processed repositories
            repos_to_process = repos_df[~repos_df['repo_artifact_id'].isin(processed_repos)]
            print(f"Found {len(repos_to_process)} repositories that need processing.")
            
            # Process the repositories
            processed_df = self._process_repositories(repos_to_process, batch_size)
            
            # Return the combined data (existing + newly processed)
            return self.data_manager.get_unified_data()
        else:
            # Process all repositories
            processed_df = self._process_repositories(repos_df, batch_size)
            return self.data_manager.get_unified_data()
    
    def _initialize_checkpoint(self):
        """Initialize a new checkpoint file"""
        checkpoint = {
            "last_processed_repo_id": None,
            "processed_repos": [],
            "partial_results": {}
        }
        self.data_manager.save_checkpoint(checkpoint)
        print("Initialized new processing checkpoint.")
        
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
        
        # Load checkpoint
        checkpoint = self.data_manager.load_checkpoint()
        processed_repos = set(checkpoint.get("processed_repos", []))
        partial_results = checkpoint.get("partial_results", {})
        
        # Process in batches
        all_processed_data = []
        
        for start_idx in tqdm(range(0, len(repos_df), batch_size), desc="Processing Repositories"):
            end_idx = min(start_idx + batch_size, len(repos_df))
            batch_df = repos_df.iloc[start_idx:end_idx].copy()
            
            # Process each repository in the batch
            for idx, row in tqdm(batch_df.iterrows(), desc="Processing repositories in batch", total=len(batch_df), leave=False):
                repo_id = row.get('repo_artifact_id')
                repo_name = row.get('repo_artifact_name', 'repo')
                
                # Skip if already fully processed
                if repo_id in processed_repos:
                    print(f"Skipping {repo_name} (already processed)")
                    continue
                
                # Get partial progress for this repository
                partial = partial_results.get(repo_id, {})
                
                # Initialize repository data
                repo_data = row.to_dict()
                repo_data['categorizations'] = []
                repo_data['final_recommendation'] = 'UNCATEGORIZED'
                repo_data['processing_timestamp'] = datetime.datetime.now().isoformat()
                repo_data['summary'] = ''
                
                # Fetch README if needed
                if not partial.get('readme_fetched', False):
                    try:
                        print(f"Fetching README for {repo_name}...")
                        readme_content, readme_status = self.fetcher.fetch_readme(
                            repo_data['repo_artifact_namespace'],
                            repo_data['repo_artifact_name']
                        )
                        repo_data['readme_md'] = readme_content
                        repo_data['readme_status'] = readme_status
                        
                        # Update checkpoint
                        partial['readme_fetched'] = True
                        partial['readme_status'] = repo_data['readme_status']
                        partial_results[repo_id] = partial
                        checkpoint['partial_results'] = partial_results
                        self.data_manager.save_checkpoint(checkpoint)
                    except Exception as e:
                        print(f"Error fetching README for {repo_name}: {e}")
                        repo_data['readme_md'] = ''
                        repo_data['readme_status'] = 'ERROR'
                        
                        # Update checkpoint
                        partial['readme_fetched'] = True
                        partial['readme_status'] = 'ERROR'
                        partial_results[repo_id] = partial
                        checkpoint['partial_results'] = partial_results
                        self.data_manager.save_checkpoint(checkpoint)
                else:
                    # Use README status from checkpoint
                    repo_data['readme_status'] = partial.get('readme_status', 'ERROR')
                
                # Generate summary if needed
                if not partial.get('summary_generated', False) and repo_data['readme_status'] == 'SUCCESS':
                    try:
                        print(f"Generating summary for {repo_name}...")
                        readme_content = repo_data.get('readme_md', '')
                        summary_output: SummaryOutput = self.ai_service.make_summary(readme_content)
                        repo_data['summary'] = summary_output.summary
                        
                        # Update checkpoint
                        partial['summary_generated'] = True
                        partial['summary'] = summary_output.summary
                        partial_results[repo_id] = partial
                        checkpoint['partial_results'] = partial_results
                        self.data_manager.save_checkpoint(checkpoint)
                    except Exception as e:
                        print(f"Error generating summary for {repo_name}: {e}")
                        repo_data['summary'] = ''
                        
                        # Update checkpoint
                        partial['summary_generated'] = True  # Mark as attempted
                        partial_results[repo_id] = partial
                        checkpoint['partial_results'] = partial_results
                        self.data_manager.save_checkpoint(checkpoint)
                elif partial.get('summary_generated', False) and 'summary' in partial:
                    # Use summary from checkpoint
                    repo_data['summary'] = partial.get('summary', '')
                
                # Initialize personas completed
                if 'personas_completed' not in partial:
                    partial['personas_completed'] = []
                
                # Initialize categorizations
                categorizations = []
                
                # Categorize with each persona if README is available
                if repo_data['readme_status'] == 'SUCCESS':
                    for persona in tqdm(personas, desc=f"Categorizing {repo_name} with personas", leave=False):
                        # Skip if already categorized by this persona
                        if persona['name'] in partial.get('personas_completed', []):
                            # Use existing categorization from checkpoint
                            if 'categorizations' in partial:
                                for cat in partial['categorizations']:
                                    if cat['persona_name'] == persona['name']:
                                        categorizations.append(cat)
                                        break
                            continue
                        
                        try:
                            # Prepare project data for categorization
                            project_data = {
                                'summary': repo_data['summary'],
                                'readme_md': repo_data.get('readme_md', ''),
                                'repo_artifact_id': repo_id,
                                'star_count': repo_data.get('star_count', 0),
                                'fork_count': repo_data.get('fork_count', 0),
                                'language': repo_data.get('language', 'Unknown'),
                                'created_at': repo_data.get('created_at'),
                                'updated_at': repo_data.get('updated_at')
                            }
                            
                            # Get categorization from this persona
                            classifications = self.ai_service.classify_projects_batch_for_persona(
                                [project_data],
                                persona
                            )
                            
                            if classifications and len(classifications) > 0:
                                classification = classifications[0]
                                cat_entry = {
                                    'persona_name': persona['name'],
                                    'category': classification.assigned_tag,
                                    'reason': classification.reason,
                                    'timestamp': datetime.datetime.now().isoformat()
                                }
                                categorizations.append(cat_entry)
                                
                                # Update checkpoint
                                if 'categorizations' not in partial:
                                    partial['categorizations'] = []
                                partial['categorizations'].append(cat_entry)
                                partial['personas_completed'].append(persona['name'])
                                partial_results[repo_id] = partial
                                checkpoint['partial_results'] = partial_results
                                self.data_manager.save_checkpoint(checkpoint)
                            else:
                                cat_entry = {
                                    'persona_name': persona['name'],
                                    'category': 'UNCATEGORIZED',
                                    'reason': 'Failed to get classification from AI service',
                                    'timestamp': datetime.datetime.now().isoformat()
                                }
                                categorizations.append(cat_entry)
                                
                                # Update checkpoint
                                if 'categorizations' not in partial:
                                    partial['categorizations'] = []
                                partial['categorizations'].append(cat_entry)
                                partial['personas_completed'].append(persona['name'])
                                partial_results[repo_id] = partial
                                checkpoint['partial_results'] = partial_results
                                self.data_manager.save_checkpoint(checkpoint)
                        except Exception as e:
                            print(f"Error categorizing {repo_name} with persona {persona['name']}: {e}")
                            cat_entry = {
                                'persona_name': persona['name'],
                                'category': 'UNCATEGORIZED',
                                'reason': f'Error: {str(e)}',
                                'timestamp': datetime.datetime.now().isoformat()
                            }
                            categorizations.append(cat_entry)
                            
                            # Update checkpoint
                            if 'categorizations' not in partial:
                                partial['categorizations'] = []
                            partial['categorizations'].append(cat_entry)
                            partial['personas_completed'].append(persona['name'])
                            partial_results[repo_id] = partial
                            checkpoint['partial_results'] = partial_results
                            self.data_manager.save_checkpoint(checkpoint)
                            
                        # Add a small delay to avoid rate limiting
                        time.sleep(0.1)
                else:
                    # If README is empty or error, mark all categorizations as UNCATEGORIZED
                    for persona in tqdm(personas, desc=f"Marking {repo_name} as UNCATEGORIZED", leave=False):
                        # Skip if already categorized by this persona
                        if persona['name'] in partial.get('personas_completed', []):
                            # Use existing categorization from checkpoint
                            if 'categorizations' in partial:
                                for cat in partial['categorizations']:
                                    if cat['persona_name'] == persona['name']:
                                        categorizations.append(cat)
                                        break
                            continue
                            
                        cat_entry = {
                            'persona_name': persona['name'],
                            'category': 'UNCATEGORIZED',
                            'reason': f'README {repo_data["readme_status"]}',
                            'timestamp': datetime.datetime.now().isoformat()
                        }
                        categorizations.append(cat_entry)
                        
                        # Update checkpoint
                        if 'categorizations' not in partial:
                            partial['categorizations'] = []
                        partial['categorizations'].append(cat_entry)
                        partial['personas_completed'].append(persona['name'])
                        partial_results[repo_id] = partial
                        checkpoint['partial_results'] = partial_results
                        self.data_manager.save_checkpoint(checkpoint)
                
                # Determine final recommendation based on categorizations
                final_recommendation = self._determine_final_recommendation(categorizations, repo_data.get('star_count', 0))
                
                # Update the repository data
                repo_data['categorizations'] = categorizations
                repo_data['final_recommendation'] = final_recommendation
                repo_data['processing_timestamp'] = datetime.datetime.now().isoformat()
                
                # Create a DataFrame for this repository
                repo_df = pd.DataFrame([repo_data])
                
                # Save this repository to the unified data
                self.data_manager.append_unified_data(repo_df)
                
                # Mark as fully processed
                processed_repos.add(repo_id)
                checkpoint['processed_repos'] = list(processed_repos)
                checkpoint['last_processed_repo_id'] = repo_id
                
                # Remove from partial results to save space
                if repo_id in partial_results:
                    del partial_results[repo_id]
                    
                checkpoint['partial_results'] = partial_results
                self.data_manager.save_checkpoint(checkpoint)
                
                # Add to processed data
                all_processed_data.append(repo_df)
        
        if not all_processed_data:
            print("No data was processed.")
            return pd.DataFrame()
        
        return pd.concat(all_processed_data, ignore_index=True) if all_processed_data else pd.DataFrame()
    
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
