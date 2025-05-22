"""
Script to initialize repository sources.
"""
import json
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.pipeline.repository_source_manager import RepositorySourceManager


def create_empty_sources_file():
    """Create an empty repository sources file."""
    sources_path = Path("data/repository_sources.json")
    sources_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(sources_path, 'w') as f:
        json.dump([], f, indent=2)
    
    print(f"Created empty repository sources file: {sources_path}")


def main():
    """Main entry point."""
    print("Initializing repository sources...")
    
    # Create empty repository sources file
    create_empty_sources_file()
    
    print("Done!")


if __name__ == "__main__":
    main()
