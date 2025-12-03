"""Process the remaining missing repositories using local parsing."""

import pandas as pd
from pathlib import Path
from local_parser import fetch_dependencies_locally

MISSING_REPOS = [
    "remix-project-org/remix-project",
    "aestus-relay/mev-boost-relay",
    "defillama/defillama-adapters",
    "ethstaker/eth-docker",
    "intellij-solidity/intellij-solidity",
    "ipsilon/evmone",
]

def main():
    data_dir = Path(__file__).parent.parent / "data"
    output_path = data_dir / "dependencies.csv"
    processed_path = data_dir / "dependencies.csv.processed"
    
    file_exists = output_path.exists()
    
    for i, repo_name in enumerate(MISSING_REPOS, 1):
        print(f"\n[{i}/{len(MISSING_REPOS)}] Processing {repo_name}...")
        
        owner, repo = repo_name.split('/')
        
        try:
            records = fetch_dependencies_locally(owner, repo)
            
            if records:
                df = pd.DataFrame(records)
                df.to_csv(output_path, mode='a', header=not file_exists, index=False, quoting=1)
                file_exists = True
                print(f"  ✓ Saved {len(records)} dependencies")
                
                # Mark as processed
                with processed_path.open("a") as f:
                    f.write(repo_name + "\n")
            else:
                print(f"  ⚠ No dependencies found")
                # Still mark as processed
                with processed_path.open("a") as f:
                    f.write(repo_name + "\n")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Final summary
    if output_path.exists():
        df = pd.read_csv(output_path, quoting=1)
        print("\n" + "="*70)
        print("Final Dataset Summary")
        print("="*70)
        print(f"Total dependency records: {len(df):,}")
        print(f"Total repositories: {df['repo_name'].nunique()}")
        print(f"Total unique packages: {df['package_name'].nunique()}")

if __name__ == "__main__":
    main()

