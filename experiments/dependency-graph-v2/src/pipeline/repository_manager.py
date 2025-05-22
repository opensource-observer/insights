"""
Repository manager for handling repository operations.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union

from ..processing.dependency_sources import (
    DependencySource,
    GitHubApiSource,
    PackageFileSource,
    SpdxSbomSource
)
from .repository_source_manager import RepositorySourceManager
from ..utils.url_utils import normalize_url


class RepositoryManager:
    """
    Repository manager for handling repository operations.
    Supports selective updates for specific repositories.
    """
    
    def __init__(self):
        """
        Initialize the repository manager.
        """
        self.github_api_source = GitHubApiSource()
        self.package_file_source = PackageFileSource()
        self.sbom_source = SpdxSbomSource()
        
        # Initialize repository source manager
        self.source_manager = RepositorySourceManager()
    
    def get_all_repos(self) -> List[str]:
        """Get all repositories."""
        return [repo["repo_url"] for repo in self.source_manager.get_all_sources()]
    
    def add_repo(self, repo_url: str) -> bool:
        """
        Add a repository.
        
        Args:
            repo_url: URL of the repository to add.
            
        Returns:
            True if the repository was added, False otherwise.
        """
        # Normalize the URL
        normalized_url = normalize_url(repo_url)
        
        # Check if the repository already exists
        if normalized_url in [normalize_url(url) for url in self.get_all_repos()]:
            return False
        
        # Add to repository sources
        self.source_manager.add_repo(normalized_url)
        return True
    
    def remove_repo(self, repo_url: str) -> bool:
        """
        Remove a repository.
        
        Args:
            repo_url: URL of the repository to remove.
            
        Returns:
            True if the repository was removed, False otherwise.
        """
        return self.source_manager.remove_repo(normalize_url(repo_url))
    
    def fetch_dependencies(
        self, 
        repo_urls: Optional[List[str]] = None, 
        sources: Optional[List[str]] = None,
        merge_with_existing: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        Fetch dependencies for specified repositories using specified sources.
        
        Args:
            repo_urls: List of repository URLs to fetch dependencies for.
                       If None, fetch for all repositories.
            sources: List of dependency sources to use.
                     Options: "github_api", "package_files", "sbom"
                     If None, use enabled sources from repository_sources.json.
            merge_with_existing: If True, merge with existing dependencies.
                                If False, replace existing dependencies.
                     
        Returns:
            Dictionary mapping repository URLs to their dependencies.
        """
        if repo_urls is None:
            repo_urls = self.get_all_repos()
        
        result = {}
        
        # Load existing dependencies if merging
        existing_dependencies = {}
        if merge_with_existing:
            try:
                output_dir = Path("output")
                dependencies_path = output_dir / "dependencies.json"
                if dependencies_path.exists():
                    with open(dependencies_path, 'r') as f:
                        data = json.load(f)
                    
                    # Convert to dictionary with repo_url as key
                    for repo_data in data:
                        repo_url = repo_data.get("repo_url")
                        if repo_url:
                            existing_dependencies[repo_url] = repo_data.get("dependencies", [])
            except Exception as e:
                print(f"Error loading existing dependencies: {str(e)}")
        
        for repo_url in repo_urls:
            normalized_url = normalize_url(repo_url)
            print(f"\nProcessing repository: {normalized_url}")
            repo_dependencies = []
            
            # Get enabled sources for this repository
            repo_sources = sources
            if repo_sources is None:
                repo_sources = self.source_manager.get_enabled_sources(normalized_url)
                if not repo_sources:
                    repo_sources = ["github_api", "package_files"]  # Default if no sources configured
            
            print(f"Using sources: {', '.join(repo_sources)}")
            
            # Start with existing dependencies if merging
            if merge_with_existing and normalized_url in existing_dependencies:
                # Filter out dependencies from sources we're about to refresh
                repo_dependencies = [
                    dep for dep in existing_dependencies[normalized_url]
                    if "source_type" in dep and dep["source_type"] not in repo_sources
                ]
                print(f"Starting with {len(repo_dependencies)} existing dependencies from other sources")
            
            # Get repository source configuration
            repo_source_config = self.source_manager.get_repo_sources(normalized_url)
            
            if "github_api" in repo_sources:
                print("Fetching dependencies from GitHub API...")
                github_deps = self.github_api_source.fetch_dependencies(normalized_url)
                repo_dependencies.extend(github_deps)
                print(f"Found {len(github_deps)} dependencies from GitHub API")
            
            if "package_files" in repo_sources:
                print("Fetching dependencies from package files...")
                # Use package files from repository source configuration if available
                if repo_source_config:
                    for source in repo_source_config["sources"]:
                        if source["type"] == "package_files" and source.get("enabled", False):
                            # Update package file source with files from configuration
                            files = source.get("files", [])
                            if files:
                                print(f"Using {len(files)} package files from configuration")
                                # Analyze each file individually
                                package_deps = []
                                for file_url in files:
                                    normalized_file_url = normalize_url(file_url)
                                    deps = self.package_file_source.analyze_file(normalized_url, normalized_file_url)
                                    package_deps.extend(deps)
                                repo_dependencies.extend(package_deps)
                                print(f"Found {len(package_deps)} dependencies from package files")
                            break
                else:
                    # Fall back to default behavior
                    package_deps = self.package_file_source.fetch_dependencies(normalized_url)
                    repo_dependencies.extend(package_deps)
                    print(f"Found {len(package_deps)} dependencies from package files")
            
            if "sbom" in repo_sources and repo_source_config:
                # Check if there's an SBOM source configured
                for source in repo_source_config["sources"]:
                    if source["type"] == "sbom" and source.get("enabled", False):
                        location = source.get("location", {})
                        location_type = location.get("type")
                        
                        if location_type == "local":
                            path = location.get("path")
                            if path and os.path.exists(path):
                                print(f"Importing SBOM from local file: {path}")
                                sbom_deps = self.sbom_source.import_sbom(path, normalized_url)
                                repo_dependencies.extend(sbom_deps)
                                print(f"Found {len(sbom_deps)} dependencies from SBOM")
                        elif location_type == "url":
                            url = location.get("url")
                            if url:
                                print(f"SBOM URL source not implemented yet: {url}")
                                # TODO: Implement fetching SBOM from URL
                        break
            
            result[normalized_url] = repo_dependencies
            print(f"Total dependencies for {normalized_url}: {len(repo_dependencies)}")
            
            # Update last_updated timestamp
            self.source_manager.update_repo_last_updated(normalized_url)
        
        return result
    
    def import_sbom(self, file_path: str, repo_url: str) -> List[Dict]:
        """
        Import dependencies from an SPDX SBOM file.
        
        Args:
            file_path: Path to the SPDX SBOM file.
            repo_url: URL of the repository the SBOM belongs to.
            
        Returns:
            List of dependencies extracted from the SBOM.
        """
        # Normalize the URL
        normalized_url = normalize_url(repo_url)
        
        # Determine the format based on file extension
        format_type = "json" if file_path.lower().endswith(".json") else "csv"
        
        # Update repository sources configuration
        self.source_manager.set_sbom_source(
            repo_url=normalized_url,
            format=format_type,
            location_type="local",
            location_path=file_path,
            enabled=True
        )
        
        # Import SBOM dependencies
        return self.sbom_source.import_sbom(file_path, normalized_url)
    
    def add_dependency_file(self, repo_url: str, file_url: str) -> bool:
        """
        Add a dependency file to a repository.
        
        Args:
            repo_url: URL of the repository.
            file_url: URL of the dependency file.
            
        Returns:
            True if the file was added, False otherwise.
        """
        return self.source_manager.add_package_file(normalize_url(repo_url), normalize_url(file_url))
    
    def remove_dependency_file(self, repo_url: str, file_url: str) -> bool:
        """
        Remove a dependency file from a repository.
        
        Args:
            repo_url: URL of the repository.
            file_url: URL of the dependency file.
            
        Returns:
            True if the file was removed, False otherwise.
        """
        return self.source_manager.remove_package_file(normalize_url(repo_url), normalize_url(file_url))
    
    def get_dependency_files(self, repo_url: str) -> List[str]:
        """
        Get dependency files for a repository.
        
        Args:
            repo_url: URL of the repository.
            
        Returns:
            List of dependency file URLs.
        """
        repo_source = self.source_manager.get_repo_sources(normalize_url(repo_url))
        if not repo_source:
            return []
        
        for source in repo_source["sources"]:
            if source["type"] == "package_files":
                return source.get("files", [])
        
        return []
