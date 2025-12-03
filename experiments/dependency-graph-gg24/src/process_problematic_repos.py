"""
Process problematic repositories using local parsing.

This script uses local cloning and parsing for repos that consistently timeout on GitHub API.
"""

import pandas as pd
from pathlib import Path
from local_parser import fetch_dependencies_locally

# Problematic repositories that timeout on GitHub API
PROBLEMATIC_REPOS = [
    "nomicfoundation/hardhat",
    "remix-project-org/remix-project",
    "wevm/viem",
    "chainsafe/lodestar",
    "taikoxyz/taiko-mono",
    "lambdaclass/ethrex",
    "evmts/tevm-monorepo",
    "offchainlabs/stylus-sdk-rs",
]

def process_repo_locally(repo_name: str, output_path: Path, processed_path: Path):
    """Process a single repository using local parsing."""
    owner, repo = repo_name.split('/')
    
    print(f"\n{'='*70}")
    print(f"Processing {repo_name} locally...")
    print('='*70)
    
    try:
        # Fetch dependencies locally
        records = fetch_dependencies_locally(owner, repo)
        
        if not records:
            print(f"  ✗ No dependencies found for {repo_name}")
            return False
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Check if file exists to determine if we need header
        file_exists = output_path.exists()
        
        # Append to CSV
        df.to_csv(output_path, mode='a', header=not file_exists, index=False, quoting=1)
        
        print(f"  ✓ Saved {len(records)} dependencies for {repo_name}")
        
        # Mark as processed
        with processed_path.open("a") as f:
            f.write(repo_name + "\n")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error processing {repo_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    data_dir = Path(__file__).parent.parent / "data"
    output_path = data_dir / "dependencies.csv"
    processed_path = data_dir / "dependencies.csv.processed"
    
    print("="*70)
    print("Processing Problematic Repositories with Local Parsing")
    print("="*70)
    
    # Load existing processed repos
    processed_repos = set()
    if processed_path.exists():
        with processed_path.open("r") as f:
            processed_repos = {line.strip() for line in f if line.strip()}
    
    # Filter to only unprocessed repos
    repos_to_process = [r for r in PROBLEMATIC_REPOS if r not in processed_repos]
    
    if not repos_to_process:
        print("\n✓ All problematic repositories have already been processed!")
        return
    
    print(f"\nRepositories to process: {len(repos_to_process)}")
    for i, repo in enumerate(repos_to_process, 1):
        print(f"  {i}. {repo}")
    
    # Process each repo
    successful = 0
    failed = 0
    
    for i, repo_name in enumerate(repos_to_process, 1):
        print(f"\n[{i}/{len(repos_to_process)}]")
        if process_repo_locally(repo_name, output_path, processed_path):
            successful += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "="*70)
    print("Processing Complete!")
    print("="*70)
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total: {len(repos_to_process)}")
    
    # Show final stats
    if output_path.exists():
        df = pd.read_csv(output_path, quoting=1)
        print(f"\nFinal dataset:")
        print(f"  Total dependency records: {len(df):,}")
        print(f"  Total repositories: {df['repo_name'].nunique()}")
        print(f"  Total unique packages: {df['package_name'].nunique()}")

if __name__ == "__main__":
    main()

