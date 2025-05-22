"""
Script for managing repository sources.
"""
import argparse
import json
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.pipeline.repository_source_manager import RepositorySourceManager


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Manage repository sources.")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List sources command
    list_parser = subparsers.add_parser("list", help="List repository sources")
    list_parser.add_argument("--repo", help="Repository URL to list sources for")
    
    # Enable source command
    enable_parser = subparsers.add_parser("enable", help="Enable a source for a repository")
    enable_parser.add_argument("--repo", required=True, help="Repository URL")
    enable_parser.add_argument("--source", required=True, choices=["github_api", "package_files", "sbom"], 
                              help="Source type to enable")
    
    # Disable source command
    disable_parser = subparsers.add_parser("disable", help="Disable a source for a repository")
    disable_parser.add_argument("--repo", required=True, help="Repository URL")
    disable_parser.add_argument("--source", required=True, choices=["github_api", "package_files", "sbom"], 
                               help="Source type to disable")
    
    # Add package file command
    add_file_parser = subparsers.add_parser("add-file", help="Add a package file to a repository")
    add_file_parser.add_argument("--repo", required=True, help="Repository URL")
    add_file_parser.add_argument("--file", required=True, help="File URL")
    
    # Remove package file command
    remove_file_parser = subparsers.add_parser("remove-file", help="Remove a package file from a repository")
    remove_file_parser.add_argument("--repo", required=True, help="Repository URL")
    remove_file_parser.add_argument("--file", required=True, help="File URL")
    
    # Set SBOM source command
    set_sbom_parser = subparsers.add_parser("set-sbom", help="Set SBOM source for a repository")
    set_sbom_parser.add_argument("--repo", required=True, help="Repository URL")
    set_sbom_parser.add_argument("--format", required=True, choices=["json", "csv"], help="Format of the SBOM file")
    set_sbom_parser.add_argument("--location-type", required=True, choices=["local", "url", "github_release"], 
                                help="Type of location")
    set_sbom_parser.add_argument("--location-path", required=True, help="Path or URL to the SBOM file")
    set_sbom_parser.add_argument("--enable", action="store_true", help="Enable the SBOM source")
    
    return parser.parse_args()


def list_sources(source_manager: RepositorySourceManager, repo_url: str = None):
    """List repository sources."""
    if repo_url:
        # List sources for a specific repository
        repo_source = source_manager.get_repo_sources(repo_url)
        if repo_source:
            print(f"Sources for repository: {repo_url}")
            print(f"Last updated: {repo_source.get('last_updated', 'Never')}")
            print("\nEnabled sources:")
            for source in repo_source["sources"]:
                if source.get("enabled", False):
                    print(f"  - {source['type']} (priority: {source.get('priority', 'N/A')})")
                    if source["type"] == "package_files" and "files" in source:
                        print(f"    Files: {len(source['files'])}")
                        for file_url in source["files"]:
                            print(f"      - {file_url}")
                    elif source["type"] == "sbom":
                        location = source.get("location", {})
                        location_type = location.get("type", "N/A")
                        location_path = location.get("path" if location_type == "local" else "url", "N/A")
                        print(f"    Format: {source.get('format', 'N/A')}")
                        print(f"    Location: {location_type} - {location_path}")
            
            print("\nDisabled sources:")
            for source in repo_source["sources"]:
                if not source.get("enabled", False):
                    print(f"  - {source['type']}")
        else:
            print(f"No sources found for repository: {repo_url}")
    else:
        # List all repositories and their sources
        sources = source_manager.get_all_sources()
        if sources:
            print(f"Found {len(sources)} repositories with sources:")
            for repo_source in sources:
                repo_url = repo_source["repo_url"]
                enabled_sources = [
                    source["type"] 
                    for source in repo_source["sources"] 
                    if source.get("enabled", False)
                ]
                print(f"  - {repo_url}")
                print(f"    Enabled sources: {', '.join(enabled_sources) if enabled_sources else 'None'}")
                print(f"    Last updated: {repo_source.get('last_updated', 'Never')}")
        else:
            print("No repository sources found.")


def main():
    """Main entry point."""
    args = parse_args()
    
    # Initialize repository source manager
    source_manager = RepositorySourceManager()
    
    if args.command == "list":
        list_sources(source_manager, args.repo)
    
    elif args.command == "enable":
        if source_manager.enable_source(args.repo, args.source, True):
            print(f"Enabled {args.source} source for {args.repo}")
        else:
            print(f"Failed to enable {args.source} source for {args.repo}")
    
    elif args.command == "disable":
        if source_manager.enable_source(args.repo, args.source, False):
            print(f"Disabled {args.source} source for {args.repo}")
        else:
            print(f"Failed to disable {args.source} source for {args.repo}")
    
    elif args.command == "add-file":
        if source_manager.add_package_file(args.repo, args.file):
            print(f"Added package file {args.file} to {args.repo}")
        else:
            print(f"Failed to add package file {args.file} to {args.repo}")
    
    elif args.command == "remove-file":
        if source_manager.remove_package_file(args.repo, args.file):
            print(f"Removed package file {args.file} from {args.repo}")
        else:
            print(f"Failed to remove package file {args.file} from {args.repo}")
    
    elif args.command == "set-sbom":
        if source_manager.set_sbom_source(
            repo_url=args.repo,
            format=args.format,
            location_type=args.location_type,
            location_path=args.location_path,
            enabled=args.enable
        ):
            print(f"Set SBOM source for {args.repo}")
            if args.enable:
                print("SBOM source is enabled")
            else:
                print("SBOM source is disabled")
        else:
            print(f"Failed to set SBOM source for {args.repo}")
    
    else:
        print("No command specified. Use --help for usage information.")


if __name__ == "__main__":
    main()
