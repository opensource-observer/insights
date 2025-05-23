"""
Script to import SBOM data from a CSV file.

This script imports dependency data from a CSV SBOM file and associates it with
a specified GitHub repository. The dependencies are then saved to the dependencies.json file.

Usage:
    python -m src.scripts.import_csv_sbom path/to/sbom.csv https://github.com/username/repo
"""
import argparse
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.pipeline.repository_manager import RepositoryManager
from src.pipeline.data_manager import DataManager
from src.config.config_manager import ConfigManager


def main():
    """
    Main function to import SBOM data from a CSV file.
    
    Returns:
        int: 0 for success, 1 for failure
    """
    parser = argparse.ArgumentParser(description="Import SBOM data from a CSV file.")
    parser.add_argument("csv_file", help="Path to the CSV file containing SBOM data.")
    parser.add_argument("repo_url", help="URL of the repository the SBOM belongs to.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing dependency data.")
    args = parser.parse_args()
    
    # Check if the CSV file exists
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"Error: CSV file {args.csv_file} not found.")
        return 1
    
    # Initialize the config manager, data manager, and repository manager
    config_manager = ConfigManager()
    output_dir = config_manager.get_output_dir()
    data_manager = DataManager(output_dir=output_dir, config=config_manager)
    repo_manager = RepositoryManager()
    
    # Check if the repository exists in repository sources
    if args.repo_url not in repo_manager.get_all_repos():
        print(f"Repository {args.repo_url} not found in repository sources.")
        if input("Add repository to repository sources? (y/n): ").lower() == 'y':
            repo_manager.add_repo(args.repo_url)
        else:
            print("Aborted.")
            return 1
    
    # Import the SBOM
    try:
        print(f"Importing SBOM file: {args.csv_file}")
        dependencies = repo_manager.import_sbom(args.csv_file, args.repo_url)
        
        if not dependencies:
            print("No dependencies found in SBOM file.")
            return 1
            
        print(f"Found {len(dependencies)} dependencies in SBOM file.")
        
        # Save dependencies
        data_manager.save_dependencies(
            {args.repo_url: dependencies},
            overwrite=args.overwrite
        )
        
        # Update repository status
        data_manager.update_repo_status(
            args.repo_url,
            f"CSV SBOM imported: {len(dependencies)} dependencies found"
        )
        
        print(f"Successfully imported SBOM for {args.repo_url}.")
        return 0
    except Exception as e:
        print(f"Error importing SBOM file: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
