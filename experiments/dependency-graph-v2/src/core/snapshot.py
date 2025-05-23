"""
Module for generating dependency snapshots.
"""
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Optional


class DependencySnapshot:
    """
    Class for generating dependency snapshots.
    """
    
    def __init__(self, dependencies: Dict[str, Any]):
        """
        Initialize the snapshot generator.
        
        Args:
            dependencies: Dictionary mapping repository URLs to dependencies data.
        """
        # Convert dependencies to a consistent format
        self.dependencies = {}
        
        # If dependencies is a list, convert it to a dictionary
        if isinstance(dependencies, list):
            for repo_data in dependencies:
                if isinstance(repo_data, dict) and 'repo_url' in repo_data and 'dependencies' in repo_data:
                    repo_url = repo_data['repo_url']
                    self.dependencies[repo_url] = repo_data['dependencies']
        else:
            # Process dictionary format
            for repo_url, repo_data in dependencies.items():
                if isinstance(repo_data, dict) and 'dependencies' in repo_data:
                    # Format: {repo_url: {repo_url: "...", dependencies: [...]}}
                    self.dependencies[repo_url] = repo_data['dependencies']
                elif isinstance(repo_data, list):
                    # Format: {repo_url: [...]}
                    self.dependencies[repo_url] = repo_data
                else:
                    # Unknown format, skip
                    print(f"Warning: Unknown dependency format for {repo_url}")
    
    def generate_by_language(self) -> Dict[str, int]:
        """
        Generate a snapshot of dependencies grouped by programming language.
        
        Returns:
            Dictionary mapping languages to dependency counts.
        """
        languages = defaultdict(int)
        
        for repo_url, deps in self.dependencies.items():
            for dep in deps:
                # Map package managers to languages
                if isinstance(dep, dict):
                    package_manager = dep.get('packageManager', '').lower()
                    language = self._map_package_manager_to_language(package_manager)
                    languages[language] += 1
                else:
                    # Handle case where dep is not a dictionary
                    languages['Unknown'] += 1
        
        return dict(languages)
    
    def generate_by_package_manager(self) -> Dict[str, int]:
        """
        Generate a snapshot of dependencies grouped by package manager.
        
        Returns:
            Dictionary mapping package managers to dependency counts.
        """
        package_managers = defaultdict(int)
        
        for repo_url, deps in self.dependencies.items():
            for dep in deps:
                if isinstance(dep, dict):
                    package_manager = dep.get('packageManager', 'unknown')
                    package_managers[package_manager] += 1
                else:
                    package_managers['unknown'] += 1
        
        return dict(package_managers)
    
    def generate_by_repository(self) -> Dict[str, Dict[str, int]]:
        """
        Generate a snapshot of dependencies grouped by repository.
        
        Returns:
            Dictionary mapping repositories to dependency counts by package manager.
        """
        repo_stats = {}
        
        for repo_url, deps in self.dependencies.items():
            package_managers = defaultdict(int)
            for dep in deps:
                if isinstance(dep, dict):
                    package_manager = dep.get('packageManager', 'unknown')
                    package_managers[package_manager] += 1
                else:
                    package_managers['unknown'] += 1
            
            repo_stats[repo_url] = dict(package_managers)
        
        return repo_stats
    
    def generate_full_snapshot(self) -> Dict[str, Any]:
        """
        Generate a full snapshot with all metrics.
        
        Returns:
            Dictionary containing all snapshot metrics.
        """
        return {
            'by_language': self.generate_by_language(),
            'by_package_manager': self.generate_by_package_manager(),
            'by_repository': self.generate_by_repository(),
            'total_dependencies': sum(len(deps) for deps in self.dependencies.values()),
            'total_repositories': len(self.dependencies)
        }
    
    def save_snapshot(self, output_path: str) -> None:
        """
        Save the full snapshot to a JSON file.
        
        Args:
            output_path: Path to save the snapshot to.
        """
        snapshot = self.generate_full_snapshot()
        
        # Ensure the directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save the snapshot
        with open(output_path, 'w') as f:
            json.dump(snapshot, f, indent=2)
    
    @staticmethod
    def _map_package_manager_to_language(package_manager: str) -> str:
        """
        Map a package manager to a programming language.
        
        Args:
            package_manager: Package manager name.
        
        Returns:
            Programming language name.
        """
        mapping = {
            'npm': 'JavaScript',
            'yarn': 'JavaScript',
            'pnpm': 'JavaScript',
            'pip': 'Python',
            'poetry': 'Python',
            'conda': 'Python',
            'maven': 'Java',
            'gradle': 'Java',
            'nuget': 'C#',
            'cargo': 'Rust',
            'go': 'Go',
            'composer': 'PHP',
            'gem': 'Ruby',
            'bundler': 'Ruby',
            'cocoapods': 'Swift',
            'carthage': 'Swift',
            'hex': 'Elixir',
            'rebar': 'Erlang',
            'cpan': 'Perl',
            'cran': 'R',
            'pub': 'Dart',
            'swift': 'Swift',
            'cabal': 'Haskell',
            'stack': 'Haskell',
            'dub': 'D',
            'vcpkg': 'C++',
            'conan': 'C++',
            'luarocks': 'Lua',
            'nimble': 'Nim',
            'opam': 'OCaml',
            'clojure': 'Clojure',
            'leiningen': 'Clojure',
            'boot': 'Clojure',
            'julia': 'Julia',
            'mix': 'Elixir',
            'sbt': 'Scala',
            'mill': 'Scala',
            'dotnet': '.NET',
            'paket': '.NET',
            'bower': 'JavaScript',
            'pypi': 'Python',
            'crates.io': 'Rust',
            'npmjs.com': 'JavaScript',
            'rubygems.org': 'Ruby',
            'packagist.org': 'PHP',
            'nuget.org': 'C#',
            'maven.org': 'Java',
            'pkg-go-dev': 'Go',
            'hackage.haskell.org': 'Haskell',
            'melpa.org': 'Emacs Lisp',
            'ctan.org': 'TeX',
        }
        
        for key, value in mapping.items():
            if key in package_manager.lower():
                return value
        
        return 'Other'
