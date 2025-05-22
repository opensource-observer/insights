"""
Script to import SBOM data from a CSV file.
"""
import argparse
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.pipeline.repository_manager import RepositoryManager
from src.pipeline.data_manager import DataManager


def main():
    """Main function to import SBOM data from a CSV file."""
    parser = argparse.ArgumentParser(description="Import SBOM data from a CSV file.")
    parser.add_argument("csv_file", help="Path to the CSV file containing SBOM data.")
    parser.add_argument("repo_url", help="URL of the repository the SBOM belongs to.")
    args = parser.parse_args()
    
    # Check if the CSV file exists
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file {args.csv_file} not found.")
        return 1
    
    # Initialize the data manager and repository manager
    output_dir = Path("output")
    data_dir = Path("data")
    data_manager = DataManager(output_dir)
    repo_manager = RepositoryManager(data_dir, data_manager)
    
    # Import the SBOM
    try:
        print(f"Importing SBOM file: {args.csv_file}")
        dependencies = repo_manager.import_sbom(args.csv_file, args.repo_url)
        print(f"Found {len(dependencies)} dependencies in SBOM file.")
        print(f"Successfully imported SBOM for {args.repo_url}.")
        return 0
    except Exception as e:
        print(f"Error importing SBOM file: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
