"""
Interactive workflow for analyzing repository dependencies.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import click

from ..pipeline.repository_manager import RepositoryManager
from ..pipeline.data_manager import DataManager
from ..pipeline.dependency_snapshot import DependencySnapshot
from ..processing.dependency_sources import GitHubApiSource, PackageFileSource, SpdxSbomSource
from ..utils.timeout import timeout, TimeoutError


class InteractiveWorkflow:
    """
    Interactive workflow for analyzing repository dependencies.
    """
    
    def __init__(self, data_manager: DataManager, repo_manager: RepositoryManager):
        """
        Initialize the workflow.
        
        Args:
            data_manager: Data manager instance.
            repo_manager: Repository manager instance.
        """
        self.data_manager = data_manager
        self.repo_manager = repo_manager
        self.github_api_source = GitHubApiSource()
        self.package_file_source = PackageFileSource()
        self.sbom_source = SpdxSbomSource()
        self.dependencies = {}
    
    def run(self, repo_url: Optional[str] = None) -> None:
        """
        Run the interactive workflow.
        
        Args:
            repo_url: Optional repository URL to analyze.
        """
        # Step 1: Add repository
        repo_url = self._add_repository(repo_url)
        if not repo_url:
            return
        
        # Step 2: Check for SBOM from GitHub API
        github_deps = self._fetch_from_github_api(repo_url)
        
        # Step 3: If GitHub API fails, provide manual options
        if not github_deps:
            self._handle_github_api_failure(repo_url)
        
        # Step 4: Package file analysis
        package_deps = self._analyze_package_files(repo_url)
        
        # Step 5: Export to dependencies JSON
        self._export_dependencies(repo_url, github_deps, package_deps)
        
        # Step 6: Generate dependency snapshot
        self._generate_snapshot()
    
    def _add_repository(self, repo_url: Optional[str] = None) -> Optional[str]:
        """
        Add a repository to analyze.
        
        Args:
            repo_url: Optional repository URL to analyze.
        
        Returns:
            Repository URL if successful, None otherwise.
        """
        if not repo_url:
            repo_url = click.prompt("Enter repository URL (e.g., https://github.com/username/repo)")
        
        # Validate repository URL
        if not repo_url.startswith("https://github.com/"):
            click.echo("Error: Only GitHub repositories are supported.")
            if not click.confirm("Try again?"):
                return None
            return self._add_repository(None)
        
        # Check if repository exists in repository_sources.json
        if repo_url not in self.repo_manager.get_all_repos():
            click.echo(f"Repository {repo_url} not found in repository sources.")
            if click.confirm("Add repository to repository sources?", default=True):
                self.repo_manager.add_repo(repo_url)
                click.echo(f"Added {repo_url} to repository sources.")
            else:
                click.echo("Aborted.")
                return None
        
        return repo_url
    
    def _fetch_from_github_api(self, repo_url: str) -> List[Dict[str, Any]]:
        """
        Fetch dependencies from GitHub API.
        
        Args:
            repo_url: Repository URL to analyze.
        
        Returns:
            List of dependencies if successful, empty list otherwise.
        """
        click.echo(f"Fetching dependencies for {repo_url} from GitHub API...")
        
        try:
            with timeout(30):  # 30 second timeout
                dependencies = self.github_api_source.fetch_dependencies(repo_url)
                click.echo(f"Found {len(dependencies)} dependencies from GitHub API.")
                return dependencies
        except TimeoutError:
            click.echo("GitHub API request timed out after 30 seconds.")
            return []
        except Exception as e:
            click.echo(f"Error fetching dependencies from GitHub API: {str(e)}")
            return []
    
    def _handle_github_api_failure(self, repo_url: str) -> None:
        """
        Handle GitHub API failure.
        
        Args:
            repo_url: Repository URL to analyze.
        """
        click.echo("GitHub API fetch failed or timed out.")
        
        options = [
            "Try again",
            "Download SBOM manually",
            "Skip to package file analysis",
            "Abort"
        ]
        
        option = click.prompt(
            "What would you like to do?",
            type=click.Choice(options),
            default=options[0]
        )
        
        if option == options[0]:  # Try again
            self._fetch_from_github_api(repo_url)
        elif option == options[1]:  # Download SBOM manually
            self._download_sbom_manually(repo_url)
        elif option == options[2]:  # Skip to package file analysis
            click.echo("Skipping to package file analysis.")
        else:  # Abort
            click.echo("Aborted.")
            sys.exit(0)
    
    def _download_sbom_manually(self, repo_url: str) -> None:
        """
        Provide instructions for downloading SBOM manually.
        
        Args:
            repo_url: Repository URL to analyze.
        """
        click.echo("To download SBOM manually:")
        click.echo("1. Go to the repository on GitHub")
        click.echo("2. Click on 'Security' tab")
        click.echo("3. Click on 'Dependency graph'")
        click.echo("4. Click on 'Export SBOM'")
        click.echo("5. Save the file to your computer")
        
        if click.confirm("Have you downloaded the SBOM file?"):
            sbom_path = click.prompt("Enter the path to the SBOM file")
            
            if not Path(sbom_path).exists():
                click.echo(f"Error: File {sbom_path} not found.")
                return
            
            try:
                # Use the repository manager to import SBOM
                dependencies = self.repo_manager.import_sbom(sbom_path, repo_url)
                click.echo(f"Found {len(dependencies)} dependencies in SBOM file.")
                
                # Save dependencies
                self.dependencies[repo_url] = dependencies
                self.data_manager.save_dependencies(
                    {repo_url: dependencies},
                    overwrite=False
                )
                
                # Update repository status
                self.data_manager.update_repo_status(
                    repo_url,
                    f"SBOM imported: {len(dependencies)} dependencies found"
                )
            except Exception as e:
                click.echo(f"Error importing SBOM file: {str(e)}")
    
    def _analyze_package_files(self, repo_url: str) -> List[Dict[str, Any]]:
        """
        Analyze package files.
        
        Args:
            repo_url: Repository URL to analyze.
        
        Returns:
            List of dependencies if successful, empty list otherwise.
        """
        click.echo("Checking for package files...")
        
        # Get dependency files for the repository
        dependency_files = self.repo_manager.get_dependency_files(repo_url)
        
        if not dependency_files:
            click.echo("No dependency files found.")
            
            if click.confirm("Would you like to add dependency files manually?"):
                self._add_dependency_files_manually(repo_url)
                dependency_files = self.repo_manager.get_dependency_files(repo_url)
        
        if not dependency_files:
            return []
        
        click.echo(f"Found {len(dependency_files)} dependency files:")
        for i, file_url in enumerate(dependency_files):
            click.echo(f"{i+1}. {file_url}")
        
        # Select files to analyze
        selected_indices = click.prompt(
            "Enter the numbers of the files to analyze (comma-separated, or 'all')",
            default="all"
        )
        
        if selected_indices.lower() == "all":
            selected_files = dependency_files
        else:
            try:
                indices = [int(i.strip()) - 1 for i in selected_indices.split(",")]
                selected_files = [dependency_files[i] for i in indices if 0 <= i < len(dependency_files)]
            except (ValueError, IndexError):
                click.echo("Invalid selection. Analyzing all files.")
                selected_files = dependency_files
        
        # Analyze selected files
        click.echo(f"Analyzing {len(selected_files)} package files...")
        
        dependencies = []
        for file_url in selected_files:
            click.echo(f"Analyzing {file_url}...")
            try:
                file_deps = self.package_file_source.analyze_file(repo_url, file_url)
                click.echo(f"Found {len(file_deps)} dependencies in {file_url}.")
                dependencies.extend(file_deps)
            except Exception as e:
                click.echo(f"Error analyzing {file_url}: {str(e)}")
        
        return dependencies
    
    def _add_dependency_files_manually(self, repo_url: str) -> None:
        """
        Add dependency files manually.
        
        Args:
            repo_url: Repository URL to analyze.
        """
        while True:
            file_url = click.prompt(
                "Enter dependency file URL (or 'done' to finish)",
                default="done"
            )
            
            if file_url.lower() == "done":
                break
            
            if not file_url.startswith(repo_url):
                click.echo(f"Error: File URL must start with {repo_url}")
                continue
            
            if self.repo_manager.add_dependency_file(repo_url, file_url):
                click.echo(f"Added dependency file {file_url}.")
            else:
                click.echo(f"Failed to add dependency file or file already exists.")
    
    def _export_dependencies(
        self,
        repo_url: str,
        github_deps: List[Dict[str, Any]],
        package_deps: List[Dict[str, Any]]
    ) -> None:
        """
        Export dependencies to JSON.
        
        Args:
            repo_url: Repository URL to analyze.
            github_deps: Dependencies from GitHub API.
            package_deps: Dependencies from package files.
        """
        # Merge dependencies
        all_deps = []
        
        # Add GitHub API dependencies
        if github_deps:
            all_deps.extend(github_deps)
        
        # Add package file dependencies
        if package_deps:
            all_deps.extend(package_deps)
        
        # Add any dependencies from SBOM import
        if repo_url in self.dependencies:
            all_deps.extend(self.dependencies[repo_url])
        
        # Remove duplicates (based on packageName and packageManager)
        unique_deps = {}
        for dep in all_deps:
            key = f"{dep.get('packageName', '')}-{dep.get('packageManager', '')}"
            unique_deps[key] = dep
        
        final_deps = list(unique_deps.values())
        
        click.echo(f"Total unique dependencies: {len(final_deps)}")
        
        # Save dependencies
        self.data_manager.save_dependencies(
            {repo_url: final_deps},
            overwrite=True
        )
        
        # Update repository status
        self.data_manager.update_repo_status(
            repo_url,
            f"Dependencies analyzed: {len(final_deps)} dependencies found"
        )
        
        click.echo(f"Dependencies saved to {self.data_manager.dependencies_path}")
    
    def _generate_snapshot(self) -> None:
        """Generate a dependency snapshot."""
        click.echo("Generating dependency snapshot...")
        
        # Get all dependencies from the dependencies.json file
        try:
            with open(self.data_manager.dependencies_path, 'r') as f:
                dependencies_data = json.load(f)
            
            # Create snapshot
            snapshot = DependencySnapshot(dependencies_data)
            
            # Save snapshot
            output_path = os.path.join(self.data_manager.output_dir, "dependency_snapshot.json")
            snapshot.save_snapshot(output_path)
            
            click.echo(f"Dependency snapshot saved to {output_path}")
            
            # Print summary
            full_snapshot = snapshot.generate_full_snapshot()
            
            click.echo("\nDependency Snapshot Summary:")
            click.echo(f"Total repositories: {full_snapshot['total_repositories']}")
            click.echo(f"Total dependencies: {full_snapshot['total_dependencies']}")
            
            click.echo("\nTop 5 languages:")
            languages = sorted(
                full_snapshot['by_language'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            for language, count in languages:
                click.echo(f"- {language}: {count}")
            
            click.echo("\nTop 5 package managers:")
            package_managers = sorted(
                full_snapshot['by_package_manager'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            for package_manager, count in package_managers:
                click.echo(f"- {package_manager}: {count}")
        except Exception as e:
            click.echo(f"Error generating dependency snapshot: {str(e)}")
