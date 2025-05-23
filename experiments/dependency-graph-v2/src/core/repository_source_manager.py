"""
Repository source manager for handling repository dependency sources.
"""
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from ..utils.url_utils import normalize_url


class RepositorySourceManager:
    """
    Repository source manager for handling repository dependency sources.
    """
    
    def __init__(self, sources_path: Path = Path("data/repository_sources.json")):
        """
        Initialize the repository source manager.
        
        Args:
            sources_path: Path to the repository sources JSON file.
        """
        self.sources_path = sources_path
        self.sources = self._load_sources()
    
    def _load_sources(self) -> List[Dict[str, Any]]:
        """Load repository sources from JSON file."""
        try:
            if self.sources_path.exists():
                with open(self.sources_path, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading repository sources: {str(e)}")
            return []
    
    def _save_sources(self):
        """Save repository sources to JSON file."""
        try:
            self.sources_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.sources_path, 'w') as f:
                json.dump(self.sources, f, indent=2)
        except Exception as e:
            print(f"Error saving repository sources: {str(e)}")
    
    def get_all_sources(self) -> List[Dict[str, Any]]:
        """Get all repository sources."""
        return self.sources
    
    def get_repo_sources(self, repo_url: str) -> Optional[Dict[str, Any]]:
        """
        Get sources for a specific repository.
        
        Args:
            repo_url: URL of the repository.
            
        Returns:
            Repository sources or None if not found.
        """
        normalized_url = normalize_url(repo_url)
        for repo_source in self.sources:
            if normalize_url(repo_source["repo_url"]) == normalized_url:
                return repo_source
        return None
    
    def add_repo(self, repo_url: str) -> Dict[str, Any]:
        """
        Add a repository to the sources.
        
        Args:
            repo_url: URL of the repository to add.
            
        Returns:
            The created repository source entry.
        """
        # Normalize the URL
        normalized_url = normalize_url(repo_url)
        
        # Check if the repository already exists
        existing = self.get_repo_sources(normalized_url)
        if existing:
            return existing
        
        # Create a new repository source entry with default settings
        new_repo = {
            "repo_url": normalized_url,
            "sources": [
                {
                    "type": "github_api",
                    "enabled": True,
                    "priority": 1
                },
                {
                    "type": "package_files",
                    "enabled": True,
                    "priority": 2,
                    "files": []
                },
                {
                    "type": "sbom",
                    "enabled": False,
                    "priority": 3,
                    "format": "json",
                    "location": {
                        "type": "local",
                        "path": ""
                    }
                }
            ],
            "last_updated": None
        }
        
        self.sources.append(new_repo)
        self._save_sources()
        return new_repo
    
    def remove_repo(self, repo_url: str) -> bool:
        """
        Remove a repository from the sources.
        
        Args:
            repo_url: URL of the repository to remove.
            
        Returns:
            True if the repository was removed, False otherwise.
        """
        normalized_url = normalize_url(repo_url)
        for i, repo_source in enumerate(self.sources):
            if normalize_url(repo_source["repo_url"]) == normalized_url:
                del self.sources[i]
                self._save_sources()
                return True
        return False
    
    def update_repo_sources(self, repo_url: str, sources: List[Dict[str, Any]]) -> bool:
        """
        Update sources for a specific repository.
        
        Args:
            repo_url: URL of the repository.
            sources: List of source configurations.
            
        Returns:
            True if the sources were updated, False otherwise.
        """
        normalized_url = normalize_url(repo_url)
        for repo_source in self.sources:
            if normalize_url(repo_source["repo_url"]) == normalized_url:
                repo_source["sources"] = sources
                self._save_sources()
                return True
        return False
    
    def update_repo_last_updated(self, repo_url: str) -> bool:
        """
        Update the last_updated timestamp for a repository.
        
        Args:
            repo_url: URL of the repository.
            
        Returns:
            True if the timestamp was updated, False otherwise.
        """
        normalized_url = normalize_url(repo_url)
        for repo_source in self.sources:
            if normalize_url(repo_source["repo_url"]) == normalized_url:
                repo_source["last_updated"] = datetime.datetime.now().isoformat()
                self._save_sources()
                return True
        return False
    
    def add_package_file(self, repo_url: str, file_url: str) -> bool:
        """
        Add a package file to a repository's package_files source.
        
        Args:
            repo_url: URL of the repository.
            file_url: URL of the package file.
            
        Returns:
            True if the file was added, False otherwise.
        """
        normalized_url = normalize_url(repo_url)
        normalized_file_url = normalize_url(file_url)
        
        repo_source = self.get_repo_sources(normalized_url)
        if not repo_source:
            repo_source = self.add_repo(normalized_url)
        
        for source in repo_source["sources"]:
            if source["type"] == "package_files":
                if "files" not in source:
                    source["files"] = []
                
                if normalized_file_url not in source["files"]:
                    source["files"].append(normalized_file_url)
                    self._save_sources()
                    return True
                return False
        
        return False
    
    def remove_package_file(self, repo_url: str, file_url: str) -> bool:
        """
        Remove a package file from a repository's package_files source.
        
        Args:
            repo_url: URL of the repository.
            file_url: URL of the package file.
            
        Returns:
            True if the file was removed, False otherwise.
        """
        normalized_url = normalize_url(repo_url)
        normalized_file_url = normalize_url(file_url)
        
        repo_source = self.get_repo_sources(normalized_url)
        if not repo_source:
            return False
        
        for source in repo_source["sources"]:
            if source["type"] == "package_files" and "files" in source:
                if normalized_file_url in source["files"]:
                    source["files"].remove(normalized_file_url)
                    self._save_sources()
                    return True
        
        return False
    
    def set_sbom_source(
        self, 
        repo_url: str, 
        format: str, 
        location_type: str, 
        location_path: str,
        enabled: bool = True
    ) -> bool:
        """
        Set SBOM source for a repository.
        
        Args:
            repo_url: URL of the repository.
            format: Format of the SBOM file ('json' or 'csv').
            location_type: Type of location ('local', 'url', or 'github_release').
            location_path: Path or URL to the SBOM file.
            enabled: Whether the SBOM source is enabled.
            
        Returns:
            True if the SBOM source was set, False otherwise.
        """
        normalized_url = normalize_url(repo_url)
        
        repo_source = self.get_repo_sources(normalized_url)
        if not repo_source:
            repo_source = self.add_repo(normalized_url)
        
        for source in repo_source["sources"]:
            if source["type"] == "sbom":
                source["format"] = format
                source["enabled"] = enabled
                source["location"] = {
                    "type": location_type,
                    "path" if location_type == "local" else "url": location_path
                }
                self._save_sources()
                return True
        
        # If no SBOM source exists, add one
        repo_source["sources"].append({
            "type": "sbom",
            "enabled": enabled,
            "priority": len(repo_source["sources"]) + 1,
            "format": format,
            "location": {
                "type": location_type,
                "path" if location_type == "local" else "url": location_path
            }
        })
        self._save_sources()
        return True
    
    def enable_source(self, repo_url: str, source_type: str, enabled: bool = True) -> bool:
        """
        Enable or disable a source for a repository.
        
        Args:
            repo_url: URL of the repository.
            source_type: Type of source ('github_api', 'package_files', or 'sbom').
            enabled: Whether the source is enabled.
            
        Returns:
            True if the source was enabled/disabled, False otherwise.
        """
        normalized_url = normalize_url(repo_url)
        
        repo_source = self.get_repo_sources(normalized_url)
        if not repo_source:
            return False
        
        for source in repo_source["sources"]:
            if source["type"] == source_type:
                source["enabled"] = enabled
                self._save_sources()
                return True
        
        return False
    
    def get_enabled_sources(self, repo_url: str) -> List[str]:
        """
        Get enabled source types for a repository.
        
        Args:
            repo_url: URL of the repository.
            
        Returns:
            List of enabled source types.
        """
        normalized_url = normalize_url(repo_url)
        
        repo_source = self.get_repo_sources(normalized_url)
        if not repo_source:
            return []
        
        return [
            source["type"] 
            for source in repo_source["sources"] 
            if source.get("enabled", False)
        ]
    
    def initialize_from_seed_repos(self, seed_repos: List[str], dependency_files: Dict[str, List[str]]) -> None:
        """
        Initialize repository sources from seed repositories and dependency files.
        
        Args:
            seed_repos: List of seed repository URLs.
            dependency_files: Dictionary mapping repository URLs to lists of dependency file URLs.
        """
        for repo_url in seed_repos:
            repo_source = self.get_repo_sources(repo_url)
            if not repo_source:
                repo_source = self.add_repo(repo_url)
            
            # Add dependency files if available
            if repo_url in dependency_files:
                for source in repo_source["sources"]:
                    if source["type"] == "package_files":
                        source["files"] = dependency_files[repo_url]
        
        self._save_sources()
