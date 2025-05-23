"""
Script to clean the dependencies_with_github.json file.

This script reads the dependencies_with_github.json file, flattens the structure
by removing the high-level nesting, and renames fields according to the specified
mapping. The cleaned data is written to a new file.

Field mapping:
- repo_url -> seed_repo
- github_repo -> dependency_repo
- packageName -> package_name
- packageManager -> package_manager
- requirements -> package_requirements
- packageUrl -> package_url
- relationship (unchanged)
- source_type -> methodology

Usage:
    python -m src.scripts.clean_dependencies

Input:
    output/dependencies_with_github.json

Output:
    output/cleaned_dependencies.json
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.config_manager import ConfigManager

# Constants
INPUT_FILE = "output/dependencies_with_github.json"
OUTPUT_FILE = "output/cleaned_dependencies.json"

def main() -> None:
    """
    Main entry point for cleaning dependencies data.
    
    This function:
    1. Loads dependencies from dependencies_with_github.json
    2. Flattens the structure and renames fields
    3. Saves the cleaned data to cleaned_dependencies.json
    """
    print("Cleaning dependencies data...")
    
    try:
        # Load input file
        input_path = Path(INPUT_FILE)
        if not input_path.exists():
            print(f"Error: Input file not found at {input_path}")
            return
        
        print(f"Loading dependencies from {input_path}...")
        with open(input_path, 'r') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} repositories with dependencies.")
        
        # Process and flatten data
        cleaned_records = process_dependencies(data)
        total_dependencies = sum(len(repo_data.get('dependencies', [])) for repo_data in data)
        
        # Write output file
        output_path = Path(OUTPUT_FILE)
        with open(output_path, 'w') as f:
            json.dump(cleaned_records, f, indent=2)
        
        print(f"\nDone! Cleaned {len(cleaned_records)} dependency records.")
        print(f"Output saved to {output_path}")
        
        # Print summary
        print(f"\nSummary:")
        print(f"  Total repositories: {len(data)}")
        print(f"  Total dependencies: {total_dependencies}")
        print(f"  Cleaned records: {len(cleaned_records)}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

def process_dependencies(data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Process dependencies data by flattening the structure and renaming fields.
    
    Args:
        data: List of repository data dictionaries.
        
    Returns:
        List of flattened dependency records.
    """
    cleaned_records = []
    
    for repo_data in data:
        seed_repo = repo_data.get('repo_url', 'Unknown')
        dependencies = repo_data.get('dependencies', [])
        
        print(f"Processing {len(dependencies)} dependencies from {seed_repo}")
        
        for dep in dependencies:
            # Create flattened record with renamed fields
            cleaned_record = {
                'seed_repo': seed_repo,
                'dependency_repo': dep.get('github_repo', 'unknown'),
                'package_name': dep.get('packageName', ''),
                'package_manager': dep.get('packageManager', ''),
                'package_requirements': dep.get('requirements', ''),
                'package_url': dep.get('packageUrl', ''),
                'relationship': dep.get('relationship', ''),
                'methodology': dep.get('source_type', '')
            }
            cleaned_records.append(cleaned_record)
    
    return cleaned_records

if __name__ == "__main__":
    main()
