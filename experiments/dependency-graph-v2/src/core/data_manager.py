import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union


class DataManager:
    def __init__(self, output_dir: Path, config=None):
        self.output_dir = output_dir
        self.config = config
        
        # Define file paths
        self.dependencies_path = self.output_dir / "dependencies.json"
        self.analyzed_dependencies_path = self.output_dir / "analyzed_dependencies.json"
        self.repo_status_path = self.output_dir / "repo_status.txt"
        
        # Legacy paths (kept for backward compatibility)
        self.raw_json_path = self.output_dir / "devtooling_raw.json"
        self.summarized_json_path = self.output_dir / "devtooling_summarized.json"
        self.final_json_path = self.output_dir / "devtooling_full.json"

        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_dependencies(self, repo_url: Optional[str] = None) -> Dict:
        """
        Get dependencies data for all repositories or a specific repository.
        
        Args:
            repo_url: Optional repository URL to filter by.
            
        Returns:
            Dictionary mapping repository URLs to their dependencies.
        """
        if not self.dependencies_path.exists():
            return {}
        
        try:
            with open(self.dependencies_path, 'r') as f:
                all_dependencies = json.load(f)
            
            if repo_url:
                # Filter for a specific repository
                for repo_data in all_dependencies:
                    if repo_data.get("repo_url") == repo_url:
                        return {repo_url: repo_data}
                return {}
            else:
                # Convert to dictionary with repo_url as key
                result = {}
                for repo_data in all_dependencies:
                    repo_url = repo_data.get("repo_url")
                    if repo_url:
                        result[repo_url] = repo_data
                return result
        except Exception as e:
            print(f"Error loading dependencies: {str(e)}")
            return {}

    def save_dependencies(self, dependencies_data: Dict[str, List[Dict]], overwrite: bool = False):
        """
        Save dependencies data for repositories.
        
        Args:
            dependencies_data: Dictionary mapping repository URLs to their dependencies.
            overwrite: If True, overwrite existing data. If False, merge with existing data.
        """
        from ..utils.url_utils import normalize_url
        
        # Normalize repository URLs
        normalized_dependencies_data = {}
        for repo_url, deps in dependencies_data.items():
            normalized_url = normalize_url(repo_url)
            normalized_dependencies_data[normalized_url] = deps
        
        # Format for storage
        formatted_data = []
        for repo_url, deps in normalized_dependencies_data.items():
            formatted_data.append({
                "repo_url": repo_url,
                "dependencies": deps
            })
        
        if not overwrite and self.dependencies_path.exists():
            try:
                # Load existing data
                with open(self.dependencies_path, 'r') as f:
                    existing_data = json.load(f)
                
                # Create a map of existing data with normalized URLs
                existing_map = {}
                for item in existing_data:
                    if item.get("repo_url"):
                        normalized_url = normalize_url(item.get("repo_url"))
                        existing_map[normalized_url] = item
                
                # Update or add new data
                for item in formatted_data:
                    repo_url = item.get("repo_url")
                    if repo_url in existing_map:
                        # Merge dependencies instead of replacing
                        existing_deps = existing_map[repo_url].get("dependencies", [])
                        new_deps = item.get("dependencies", [])
                        
                        # Create a unique identifier for each dependency to avoid duplicates
                        existing_deps_map = {}
                        for dep in existing_deps:
                            # Create a unique key based on package name, manager, and source type
                            key = f"{dep.get('packageName', '')}-{dep.get('packageManager', '')}-{dep.get('source_type', '')}"
                            existing_deps_map[key] = dep
                        
                        # Add or update dependencies
                        for dep in new_deps:
                            key = f"{dep.get('packageName', '')}-{dep.get('packageManager', '')}-{dep.get('source_type', '')}"
                            existing_deps_map[key] = dep
                        
                        # Update the dependencies list
                        existing_map[repo_url]["dependencies"] = list(existing_deps_map.values())
                    else:
                        # Add new entry
                        existing_data.append(item)
                
                # Save updated data
                with open(self.dependencies_path, 'w') as f:
                    json.dump(existing_data, f, indent=2)
                
                print(f"Updated dependencies data saved to {self.dependencies_path}")
                return
            except Exception as e:
                print(f"Error updating dependencies: {str(e)}")
                # Fall back to overwriting
        
        # Save new data (overwrite or fallback)
        try:
            # If overwrite is True but we still want to preserve other repositories
            if overwrite and self.dependencies_path.exists():
                try:
                    # Load existing data
                    with open(self.dependencies_path, 'r') as f:
                        existing_data = json.load(f)
                    
                    # Create a map of existing data with normalized URLs
                    existing_map = {}
                    for item in existing_data:
                        if item.get("repo_url"):
                            normalized_url = normalize_url(item.get("repo_url"))
                            existing_map[normalized_url] = item
                    
                    # Replace or add new data
                    for item in formatted_data:
                        repo_url = item.get("repo_url")
                        existing_map[repo_url] = item
                    
                    # Convert back to list
                    final_data = list(existing_map.values())
                    
                    # Save updated data
                    with open(self.dependencies_path, 'w') as f:
                        json.dump(final_data, f, indent=2)
                    
                    print(f"Updated dependencies data saved to {self.dependencies_path}")
                    return
                except Exception as e:
                    print(f"Error updating dependencies during overwrite: {str(e)}")
                    # Fall back to complete overwrite
            
            # Complete overwrite or fallback
            with open(self.dependencies_path, 'w') as f:
                json.dump(formatted_data, f, indent=2)
            
            print(f"Dependencies data saved to {self.dependencies_path}")
        except Exception as e:
            print(f"Error saving dependencies: {str(e)}")

    def save_analyzed_dependencies(self, analyzed_data: List[Dict], overwrite: bool = False):
        """
        Save analyzed dependencies data.
        
        Args:
            analyzed_data: List of analyzed dependency data.
            overwrite: If True, overwrite existing data. If False, merge with existing data.
        """
        if not overwrite and self.analyzed_dependencies_path.exists():
            try:
                # Load existing data
                with open(self.analyzed_dependencies_path, 'r') as f:
                    existing_data = json.load(f)
                
                # Create a map of existing data
                existing_map = {item.get("repo_url"): item for item in existing_data if item.get("repo_url")}
                
                # Update or add new data
                for item in analyzed_data:
                    repo_url = item.get("repo_url")
                    if repo_url in existing_map:
                        # Update existing entry
                        existing_map[repo_url] = item
                    else:
                        # Add new entry
                        existing_data.append(item)
                
                # Save updated data
                with open(self.analyzed_dependencies_path, 'w') as f:
                    json.dump(existing_data, f, indent=2)
                
                print(f"Updated analyzed dependencies data saved to {self.analyzed_dependencies_path}")
                return
            except Exception as e:
                print(f"Error updating analyzed dependencies: {str(e)}")
                # Fall back to overwriting
        
        # Save new data (overwrite or fallback)
        with open(self.analyzed_dependencies_path, 'w') as f:
            json.dump(analyzed_data, f, indent=2)
        
        print(f"Analyzed dependencies data saved to {self.analyzed_dependencies_path}")

    def update_repo_status(self, repo_url: str, status: str):
        """
        Update the status of a repository.
        
        Args:
            repo_url: URL of the repository.
            status: Status message.
        """
        status_data = {}
        
        # Load existing status data if available
        if self.repo_status_path.exists():
            try:
                with open(self.repo_status_path, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.strip()
                        # Find the position of the first colon after the protocol (https:)
                        protocol_end = line.find("://")
                        if protocol_end != -1:
                            # Find the next colon after the protocol
                            status_start = line.find(":", protocol_end + 3)
                            if status_start != -1:
                                url = line[:status_start]
                                stat = line[status_start + 1:].strip()
                                status_data[url] = stat
            except Exception as e:
                print(f"Error reading repo status: {str(e)}")
        
        # Update status
        status_data[repo_url] = status
        
        # Write updated status
        try:
            with open(self.repo_status_path, 'w') as f:
                # Sort the URLs alphabetically before writing
                for url in sorted(status_data.keys()):
                    f.write(f"{url}: {status_data[url]}\n")
            print(f"Updated status for {repo_url}: {status}")
        except Exception as e:
            print(f"Error updating repo status: {str(e)}")

    def get_repo_status(self, repo_url: Optional[str] = None) -> Union[Dict[str, str], str]:
        """
        Get the status of repositories.
        
        Args:
            repo_url: Optional repository URL to get status for.
            
        Returns:
            If repo_url is provided, returns the status string for that repository.
            Otherwise, returns a dictionary mapping repository URLs to their status.
        """
        if not self.repo_status_path.exists():
            return {} if repo_url is None else ""
        
        status_data = {}
        try:
            with open(self.repo_status_path, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    # Find the position of the first colon after the protocol (https:)
                    protocol_end = line.find("://")
                    if protocol_end != -1:
                        # Find the next colon after the protocol
                        status_start = line.find(":", protocol_end + 3)
                        if status_start != -1:
                            url = line[:status_start]
                            status = line[status_start + 1:].strip()
                            status_data[url] = status
            
            if repo_url is not None:
                # Normalize the URL for comparison
                from ..utils.url_utils import normalize_url
                normalized_url = normalize_url(repo_url)
                for url, status in status_data.items():
                    if normalize_url(url) == normalized_url:
                        return status
                return ""
            return status_data
        except Exception as e:
            print(f"Error reading repo status: {str(e)}")
            return {} if repo_url is None else ""

    # Legacy methods (kept for backward compatibility)
    
    def get_repos_data(self) -> pd.DataFrame:
        """Get the latest repository data"""
        if self.raw_json_path.exists():
            with open(self.raw_json_path, 'r') as f:
                data = json.load(f)
            return pd.DataFrame(data)
        return pd.DataFrame()

    def get_summaries_data(self) -> pd.DataFrame:
        """Get the latest summaries data"""
        if self.summarized_json_path.exists():
            with open(self.summarized_json_path, 'r') as f:
                data = json.load(f)
            return pd.DataFrame(data)
        return pd.DataFrame()

    def save_repos_data(self, data: pd.DataFrame):
        """Save repository data"""
        # Convert DataFrame to list of dictionaries
        data_dict = data.to_dict(orient='records')
        with open(self.raw_json_path, 'w') as f:
            json.dump(data_dict, f, indent=2)
        print(f"Repository data saved to {self.raw_json_path}")

    def save_summaries_data(self, data: pd.DataFrame, append: bool = False):
        """Save summaries data. If append is True, appends to existing file if it exists."""
        if append and self.summarized_json_path.exists():
            with open(self.summarized_json_path, 'r') as f:
                existing_data = json.load(f)
            # Convert both to DataFrames for easier merging
            existing_df = pd.DataFrame(existing_data)
            combined_df = pd.concat([existing_df, data]).drop_duplicates(subset=['repo_url'], keep='last')
            data_to_save = combined_df.to_dict(orient='records')
        else:
            data_to_save = data.to_dict(orient='records')
            
        with open(self.summarized_json_path, 'w') as f:
            json.dump(data_to_save, f, indent=2)
        print(f"Summaries data saved to {self.summarized_json_path}")

    def save_consolidated_data(self, data: pd.DataFrame):
        """Save consolidated data to JSON"""
        data_dict = data.to_dict(orient='records')
        with open(self.final_json_path, 'w') as f:
            json.dump(data_dict, f, indent=2)
        print(f"Consolidated data saved to {self.final_json_path}")

    def wipe_repos_data(self):
        """Wipe repository data"""
        if self.raw_json_path.exists():
            self.raw_json_path.unlink()
            print(f"Wiped repository data: {self.raw_json_path}")

    def wipe_summaries_data(self):
        """Wipe summaries data"""
        if self.summarized_json_path.exists():
            self.summarized_json_path.unlink()
            print(f"Wiped summaries data: {self.summarized_json_path}")

    def get_final_json_path(self) -> Path:
        return self.final_json_path
