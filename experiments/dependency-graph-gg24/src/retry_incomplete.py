"""
Script to retry repositories that had incomplete dependency data.

This script:
1. Removes incomplete repos from the .processed file
2. Removes their entries from the CSV
3. Allows them to be re-fetched with the main script
"""

import pandas as pd
from pathlib import Path

# Repositories that need to be retried
INCOMPLETE_REPOS = [
    "nomicfoundation/hardhat",
    "remix-project-org/remix-project",
    "wevm/viem",
    "chainsafe/lodestar",
    "taikoxyz/taiko-mono",
    "lambdaclass/ethrex",
    "evmts/tevm-monorepo",
    "offchainlabs/stylus-sdk-rs",  # GraphQL error
]

def remove_from_processed(processed_file: str):
    """Remove incomplete repos from the .processed file."""
    processed_path = Path(processed_file)
    
    if not processed_path.exists():
        print(f"Processed file not found: {processed_file}")
        return
    
    # Read existing processed repos
    with processed_path.open("r") as f:
        processed_repos = [line.strip() for line in f if line.strip()]
    
    # Remove incomplete repos
    original_count = len(processed_repos)
    processed_repos = [repo for repo in processed_repos if repo not in INCOMPLETE_REPOS]
    removed_count = original_count - len(processed_repos)
    
    # Write back
    with processed_path.open("w") as f:
        for repo in processed_repos:
            f.write(repo + "\n")
    
    print(f"Removed {removed_count} incomplete repos from {processed_file}")
    print(f"Remaining processed repos: {len(processed_repos)}")

def remove_from_csv(csv_file: str):
    """Remove incomplete repos from the CSV file."""
    csv_path = Path(csv_file)
    
    if not csv_path.exists():
        print(f"CSV file not found: {csv_file}")
        return
    
    # Read CSV
    df = pd.read_csv(csv_path, quoting=1)  # quoting=1 means QUOTE_ALL
    
    original_count = len(df)
    original_repos = df['repo_name'].nunique()
    
    # Remove rows for incomplete repos
    df = df[~df['repo_name'].isin(INCOMPLETE_REPOS)]
    
    removed_count = original_count - len(df)
    removed_repos = original_repos - df['repo_name'].nunique()
    
    # Write back
    df.to_csv(csv_path, index=False, quoting=1)
    
    print(f"Removed {removed_count} rows ({removed_repos} repos) from {csv_file}")
    print(f"Remaining rows: {len(df)}")
    print(f"Remaining repos: {df['repo_name'].nunique()}")

def main():
    data_dir = Path(__file__).parent.parent / "data"
    processed_file = data_dir / "dependencies.csv.processed"
    csv_file = data_dir / "dependencies.csv"
    
    print("=" * 60)
    print("Retry Incomplete Repositories")
    print("=" * 60)
    print(f"\nRepositories to retry ({len(INCOMPLETE_REPOS)}):")
    for i, repo in enumerate(INCOMPLETE_REPOS, 1):
        print(f"  {i}. {repo}")
    
    print("\n" + "=" * 60)
    print("Removing from processed file...")
    remove_from_processed(processed_file)
    
    print("\n" + "=" * 60)
    print("Removing from CSV file...")
    remove_from_csv(csv_file)
    
    print("\n" + "=" * 60)
    print("Done! You can now run dependencies.py to retry these repositories.")
    print("=" * 60)

if __name__ == "__main__":
    main()

