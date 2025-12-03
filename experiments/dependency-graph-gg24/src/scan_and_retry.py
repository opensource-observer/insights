"""
Script to scan for incomplete repositories and automatically retry them.

This script:
1. Scans the CSV for potentially incomplete repos (e.g., manifests with exactly 100 deps)
2. Combines with known incomplete repos
3. Removes them from processed list and CSV
4. Optionally runs the main dependencies script
"""

import pandas as pd
import subprocess
import sys
from pathlib import Path
from typing import Set

# Known repositories that had issues
KNOWN_INCOMPLETE_REPOS = [
    "nomicfoundation/hardhat",
    "remix-project-org/remix-project",
    "wevm/viem",
    "chainsafe/lodestar",
    "taikoxyz/taiko-mono",
    "lambdaclass/ethrex",
    "evmts/tevm-monorepo",
    "offchainlabs/stylus-sdk-rs",
]

def scan_for_incomplete_repos(csv_file: str) -> Set[str]:
    """
    Scan CSV for potentially incomplete repositories.
    
    Looks for:
    - Manifests with exactly 100 dependencies (suggests pagination was cut off)
    - Repos with very few dependencies that might have timed out
    """
    csv_path = Path(csv_file)
    
    if not csv_path.exists():
        print(f"CSV file not found: {csv_file}")
        return set()
    
    try:
        df = pd.read_csv(csv_path, quoting=1)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return set()
    
    if df.empty:
        return set()
    
    # Group by repo and manifest to find manifests with exactly 100 deps
    suspicious_repos = set()
    
    # Check for manifests with exactly 100 dependencies (suggests pagination cutoff)
    manifest_counts = df.groupby(['repo_name', 'manifest_filename']).size()
    for (repo_name, manifest_filename), count in manifest_counts.items():
        if count == 100:  # Exactly 100 suggests pagination was cut off
            suspicious_repos.add(repo_name)
            print(f"  ⚠ {repo_name}/{manifest_filename}: exactly 100 deps (possible pagination cutoff)")
    
    return suspicious_repos

def remove_from_processed(processed_file: str, repos_to_remove: Set[str]):
    """Remove repos from the .processed file."""
    processed_path = Path(processed_file)
    
    if not processed_path.exists():
        print(f"Processed file not found: {processed_file}")
        return 0
    
    # Read existing processed repos
    with processed_path.open("r") as f:
        processed_repos = [line.strip() for line in f if line.strip()]
    
    # Remove repos
    original_count = len(processed_repos)
    processed_repos = [repo for repo in processed_repos if repo not in repos_to_remove]
    removed_count = original_count - len(processed_repos)
    
    # Write back
    with processed_path.open("w") as f:
        for repo in processed_repos:
            f.write(repo + "\n")
    
    return removed_count

def remove_from_csv(csv_file: str, repos_to_remove: Set[str]):
    """Remove repos from the CSV file."""
    csv_path = Path(csv_file)
    
    if not csv_path.exists():
        print(f"CSV file not found: {csv_file}")
        return 0, 0
    
    try:
        df = pd.read_csv(csv_path, quoting=1)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return 0, 0
    
    original_count = len(df)
    original_repos = df['repo_name'].nunique()
    
    # Remove rows for repos
    df = df[~df['repo_name'].isin(repos_to_remove)]
    
    removed_count = original_count - len(df)
    removed_repos = original_repos - df['repo_name'].nunique()
    
    # Write back
    df.to_csv(csv_path, index=False, quoting=1)
    
    return removed_count, removed_repos

def main(run_after_cleanup: bool = False):
    data_dir = Path(__file__).parent.parent / "data"
    processed_file = data_dir / "dependencies.csv.processed"
    csv_file = data_dir / "dependencies.csv"
    
    print("=" * 70)
    print("Scan and Retry Incomplete Repositories")
    print("=" * 70)
    
    # Step 1: Scan for suspicious repos
    print("\n[Step 1] Scanning CSV for potentially incomplete repositories...")
    suspicious_repos = scan_for_incomplete_repos(csv_file)
    
    # Step 2: Combine with known incomplete repos
    print(f"\n[Step 2] Combining with known incomplete repositories...")
    all_incomplete_repos = set(KNOWN_INCOMPLETE_REPOS) | suspicious_repos
    
    print(f"\nTotal repositories to retry: {len(all_incomplete_repos)}")
    print("\nRepositories to retry:")
    for i, repo in enumerate(sorted(all_incomplete_repos), 1):
        source = "known issue" if repo in KNOWN_INCOMPLETE_REPOS else "suspicious pattern"
        print(f"  {i:2d}. {repo:50s} ({source})")
    
    if not all_incomplete_repos:
        print("\n✓ No incomplete repositories found!")
        return
    
    # Step 3: Remove from processed file
    print(f"\n[Step 3] Removing from processed file...")
    removed_processed = remove_from_processed(processed_file, all_incomplete_repos)
    print(f"  Removed {removed_processed} repos from processed list")
    
    # Step 4: Remove from CSV
    print(f"\n[Step 4] Removing from CSV file...")
    removed_rows, removed_repos = remove_from_csv(csv_file, all_incomplete_repos)
    print(f"  Removed {removed_rows} rows ({removed_repos} repos) from CSV")
    
    print("\n" + "=" * 70)
    print("Cleanup complete!")
    print("=" * 70)
    
    # Step 5: Optionally run the main script
    if run_after_cleanup:
        print(f"\n[Step 5] Running dependencies.py to retry {len(all_incomplete_repos)} repositories...")
        print("=" * 70)
        try:
            script_path = Path(__file__).parent / "dependencies.py"
            subprocess.run([sys.executable, str(script_path)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"\nError running dependencies.py: {e}")
            sys.exit(1)
    else:
        print(f"\nTo retry these repositories, run:")
        print(f"  python src/dependencies.py")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scan for incomplete repos and retry them")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Automatically run dependencies.py after cleanup"
    )
    args = parser.parse_args()
    
    main(run_after_cleanup=args.run)

