"""
Script for analyzing dependencies from multiple sources.

This script analyzes dependencies from multiple sources (GitHub API, package files, SBOM)
for specified repositories or all repositories. It supports selective updates for
specific repositories and sources.

Usage:
    python -m src.scripts.analyze_dependencies [--repos REPO_URL [REPO_URL ...]] 
                                              [--sources SOURCE [SOURCE ...]]
                                              [--no-merge] [--initialize]
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.pipeline.data_manager import DataManager
from src.pipeline.repository_manager import RepositoryManager
from src.config.config_manager import ConfigManager


def parse_args():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description="Analyze dependencies from multiple sources.")
    parser.add_argument("--repos", nargs="+", help="List of repository URLs to analyze. If not provided, analyze all repositories.")
    parser.add_argument("--sources", nargs="+", choices=["github_api", "package_files", "sbom"], 
                        help="List of dependency sources to use. If not provided, use enabled sources from repository_sources.json.")
    parser.add_argument("--no-merge", action="store_true", help="Don't merge with existing dependencies.")
    parser.add_argument("--initialize", action="store_true", help="Initialize repository sources from seed repositories.")
    return parser.parse_args()


def initialize_repository_sources():
    """
    Initialize repository sources from seed repositories.
    
    This function calls the initialize_repository_sources script to set up
    repository sources from seed repositories.
    """
    from src.scripts.initialize_repository_sources import main as initialize_main
    print("Initializing repository sources...")
    initialize_main()


def main():
    """
    Main entry point for analyzing dependencies.
    
    This function:
    1. Parses command line arguments
    2. Initializes repository sources if requested
    3. Fetches dependencies from specified sources
    4. Saves dependencies and updates repository status
    """
    args = parse_args()
    
    # Initialize repository sources if requested
    if args.initialize:
        initialize_repository_sources()
    
    # Initialize managers
    config_manager = ConfigManager()
    output_dir = config_manager.get_output_dir()
    data_manager = DataManager(output_dir=output_dir, config=config_manager)
    repo_manager = RepositoryManager()
    
    # Get repositories to analyze
    repo_urls = args.repos
    if not repo_urls:
        repo_urls = repo_manager.get_all_repos()
        print(f"No repositories specified, analyzing all {len(repo_urls)} repositories.")
    else:
        print(f"Analyzing {len(repo_urls)} specified repositories.")
    
    # Get sources to use
    sources = args.sources
    if sources:
        print(f"Using specified sources: {', '.join(sources)}")
    else:
        print("Using enabled sources from repository_sources.json.")
    
    # Fetch dependencies
    dependencies = repo_manager.fetch_dependencies(
        repo_urls=repo_urls,
        sources=sources,
        merge_with_existing=not args.no_merge
    )
    
    # Save dependencies
    data_manager.save_dependencies(dependencies, overwrite=args.no_merge)
    
    # Update repository status
    for repo_url, deps in dependencies.items():
        data_manager.update_repo_status(
            repo_url,
            f"Dependencies analyzed: {len(deps)} dependencies found"
        )
    
    print("\nDependency analysis complete.")
    print(f"Total repositories analyzed: {len(dependencies)}")
    total_deps = sum(len(deps) for deps in dependencies.values())
    print(f"Total dependencies found: {total_deps}")


if __name__ == "__main__":
    main()
