"""
Script to initialize repository sources.

This script creates an empty repository sources file at data/repository_sources.json
if it doesn't exist. This file is used to store information about repositories and
their dependency sources.

Usage:
    python -m src.scripts.initialize_repository_sources
"""
import json
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.pipeline.repository_source_manager import RepositorySourceManager


def create_empty_sources_file():
    """
    Create an empty repository sources file.
    
    This function creates an empty repository sources file at data/repository_sources.json
    if it doesn't exist. It also creates the data directory if it doesn't exist.
    """
    sources_path = Path("data/repository_sources.json")
    sources_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(sources_path, 'w') as f:
        json.dump([], f, indent=2)
    
    print(f"Created empty repository sources file: {sources_path}")


def main():
    """
    Main entry point for initializing repository sources.
    
    This function creates an empty repository sources file if it doesn't exist.
    """
    print("Initializing repository sources...")
    
    # Create empty repository sources file
    create_empty_sources_file()
    
    print("Done!")


if __name__ == "__main__":
    main()
