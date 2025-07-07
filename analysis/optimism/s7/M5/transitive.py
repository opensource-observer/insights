import base64
import requests
import pandas as pd
from pyoso import Client
import os
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv
from urllib.parse import urlparse


load_dotenv()
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']


def get_checkpoint_file() -> str:
    """Get the path to the checkpoint file."""
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "checkpoint.json")


def save_checkpoint(processed_repos: List[str], results: Dict, total_repos: int):
    """Save current progress to checkpoint file."""
    checkpoint_file = get_checkpoint_file()
    checkpoint_data = {
        "processed_repos": processed_repos,
        "results": results,
        "total_repos": total_repos,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    try:
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        print(f"Checkpoint saved: {len(processed_repos)}/{total_repos} repositories processed")
    except Exception as e:
        print(f"Warning: Could not save checkpoint: {str(e)}")


def load_checkpoint() -> tuple:
    """Load progress from checkpoint file if it exists."""
    checkpoint_file = get_checkpoint_file()
    
    if not os.path.exists(checkpoint_file):
        return [], {}, 0
    
    try:
        with open(checkpoint_file, 'r') as f:
            checkpoint_data = json.load(f)
        
        processed_repos = checkpoint_data.get("processed_repos", [])
        results = checkpoint_data.get("results", {})
        total_repos = checkpoint_data.get("total_repos", 0)
        
        print(f"Resuming from checkpoint: {len(processed_repos)}/{total_repos} repositories already processed")
        return processed_repos, results, total_repos
    
    except Exception as e:
        print(f"Warning: Could not load checkpoint: {str(e)}")
        return [], {}, 0


def clear_checkpoint():
    """Clear the checkpoint file after successful completion."""
    checkpoint_file = get_checkpoint_file()
    if os.path.exists(checkpoint_file):
        try:
            os.remove(checkpoint_file)
            print("Checkpoint cleared")
        except Exception as e:
            print(f"Warning: Could not clear checkpoint: {str(e)}")


def load_repos_from_csv(csv_path: str = "m5_dependencies.csv", limit: int = None) -> List[str]:
    """Load unique repository URLs from m5_dependencies.csv."""
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, csv_path)
    
    try:
        df = pd.read_csv(csv_path)
        # Get unique onchain_builder_repo URLs
        unique_repos = df['onchain_builder_repo'].unique().tolist()
        
        # Apply limit if specified
        if limit:
            unique_repos = unique_repos[:limit]
            print(f"Loaded {len(unique_repos)} repositories (limited to first {limit}) from {csv_path}")
        else:
            print(f"Loaded {len(unique_repos)} unique repositories from {csv_path}")
        
        return unique_repos
    except Exception as e:
        print(f"Error loading repos from CSV: {str(e)}")
        return []


def load_dependency_names_from_csv(csv_path: str = "m5_dependencies.csv") -> set:
    """Load unique dependency names from m5_dependencies.csv."""
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, csv_path)
    
    try:
        df = pd.read_csv(csv_path)
        # Get unique dependency_name values
        unique_deps = set(df['dependency_name'].unique())
        print(f"Loaded {len(unique_deps)} unique dependency names from {csv_path}")
        return unique_deps
    except Exception as e:
        print(f"Error loading dependency names from CSV: {str(e)}")
        return set()


def fetch_dependencies(owner: str, repo: str) -> Dict:
    """Fetch repository dependencies using GitHub's GraphQL API."""
    graphql_url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    
    query = """
    query($owner: String!, $repo: String!) {
        repository(owner: $owner, name: $repo) {
            dependencyGraphManifests(first: 100) {
                nodes {
                    filename
                    dependencies(first: 100) {
                        nodes {
                            hasDependencies
                            packageName
                            packageManager
                            packageUrl
                            requirements
                            relationship
                        }
                    }
                }
            }
        }
    }
    """
    
    variables = {
        "owner": owner,
        "repo": repo
    }
    
    try:
        response = requests.post(
            graphql_url,
            headers=headers,
            json={"query": query, "variables": variables}
        )
        response.raise_for_status()
        data = response.json()
        
        # Add debug logging
        print(f"\nFetching dependencies for {owner}/{repo}")
        if "errors" in data:
            print(f"GraphQL errors: {data['errors']}")
            return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
        
        # Check if we got a valid response
        if not data.get("data", {}).get("repository"):
            print(f"No repository data found for {owner}/{repo}")
            return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
        
        manifests = data["data"]["repository"]["dependencyGraphManifests"]["nodes"]
        if not manifests:
            print(f"No dependency manifests found for {owner}/{repo}")
        else:
            print(f"Found {len(manifests)} dependency manifests")
            for manifest in manifests:
                deps = manifest.get("dependencies", {}).get("nodes", [])
                filename = manifest.get('filename', 'unknown')
                print(f"Manifest {filename}: {len(deps)} dependencies")
        
        return data
    except Exception as e:
        print(f"Error fetching dependencies for {owner}/{repo}: {str(e)}")
        return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}


def extract_direct_dependencies(data: Dict, target_dependencies: set) -> List[Dict]:
    """Extract direct dependencies from the GraphQL response, filtered by target dependencies."""
    direct_deps = []
    
    try:
        manifests = data.get("data", {}).get("repository", {}).get("dependencyGraphManifests", {}).get("nodes", [])
        
        for manifest in manifests:
            filename = manifest.get("filename", "unknown")
            dependencies = manifest.get("dependencies", {}).get("nodes", [])
            print(f"\nDEBUG: Manifest {filename} has {len(dependencies)} dependencies:")
            for dep in dependencies:
                print(f"  - packageName: {dep.get('packageName')}, relationship: {dep.get('relationship')}, packageManager: {dep.get('packageManager')}")
            # Skip lock files (package-lock.json, yarn.lock, etc.) as they contain transitive dependencies
            if any(lock_file in filename.lower() for lock_file in ['package-lock.json', 'yarn.lock', 'pnpm-lock.yaml']):
                continue
                
            for dep in dependencies:
                # Include dependencies where relationship is "DIRECT" or None (which often means direct)
                relationship = dep.get("relationship")
                package_name = dep.get("packageName")
                
                if (relationship == "DIRECT" or relationship is None or relationship == "direct") and package_name in target_dependencies:
                    dep_info = {
                        "filename": filename,
                        "package_name": package_name,
                        "package_manager": dep.get("packageManager"),
                        "package_url": dep.get("packageUrl"),
                        "requirements": dep.get("requirements"),
                        "has_dependencies": dep.get("hasDependencies", False),
                        "relationship": relationship
                    }
                    direct_deps.append(dep_info)
    
    except Exception as e:
        print(f"Error extracting dependencies: {str(e)}")
    
    print(f"\nDEBUG: direct_deps = {direct_deps}\n")
    return direct_deps


def parse_github_url(url: str) -> tuple:
    """Parse GitHub URL to extract owner and repo name."""
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    if len(path_parts) >= 2:
        return path_parts[0], path_parts[1]
    else:
        raise ValueError(f"Invalid GitHub URL: {url}")


def get_direct_dependencies_for_repos(repo_urls: List[str], target_dependencies: set, resume: bool = True) -> Dict[str, List[Dict]]:
    """Get direct dependencies for a list of GitHub repositories, filtered by target dependencies."""
    results = {}
    processed_repos = []
    
    # Load checkpoint if resuming
    if resume:
        processed_repos, results, total_repos = load_checkpoint()
        if total_repos != len(repo_urls):
            print("Checkpoint total_repos doesn't match current repo list. Starting fresh.")
            processed_repos, results, total_repos = [], {}, len(repo_urls)
    else:
        total_repos = len(repo_urls)
    
    # Filter out already processed repositories
    remaining_repos = [repo for repo in repo_urls if repo not in processed_repos]
    
    if not remaining_repos:
        print("All repositories already processed!")
        return results
    
    print(f"Processing {len(remaining_repos)} remaining repositories...")
    
    for i, repo_url in enumerate(remaining_repos, 1):
        try:
            owner, repo = parse_github_url(repo_url)
            print(f"\nProcessing: {owner}/{repo} ({i}/{len(remaining_repos)})")
            
            # Fetch dependencies
            data = fetch_dependencies(owner, repo)
            
            # Extract direct dependencies (filtered by target dependencies)
            direct_deps = extract_direct_dependencies(data, target_dependencies)
            
            results[f"{owner}/{repo}"] = {
                "repo_url": repo_url,
                "direct_dependencies": direct_deps,
                "total_direct_deps": len(direct_deps)
            }
            
            processed_repos.append(repo_url)
            print(f"Found {len(direct_deps)} matching direct dependencies")
            
            # Save checkpoint every 10 repositories
            if i % 10 == 0:
                save_checkpoint(processed_repos, results, total_repos)
            
        except Exception as e:
            print(f"Error processing {repo_url}: {str(e)}")
            results[repo_url] = {
                "repo_url": repo_url,
                "direct_dependencies": [],
                "total_direct_deps": 0,
                "error": str(e)
            }
            processed_repos.append(repo_url)
            
            # Save checkpoint on error
            save_checkpoint(processed_repos, results, total_repos)
    
    return results


def save_results_to_csv(results: Dict[str, List[Dict]], filename: str = "direct_dependencies.csv"):
    """Save results to a CSV file in the same directory as this script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, filename)
    all_deps = []
    
    for repo_key, repo_data in results.items():
        for dep in repo_data.get("direct_dependencies", []):
            dep_row = {
                "repository": repo_key,
                "repo_url": repo_data.get("repo_url"),
                **dep
            }
            all_deps.append(dep_row)
    
    if all_deps:
        df = pd.DataFrame(all_deps)
        df.to_csv(output_path, index=False)
        print(f"\nResults saved to {output_path}")
        print(f"Total direct dependencies found: {len(all_deps)}")
    else:
        print("\nNo dependencies found to save")


if __name__ == "__main__":
    # Load repositories and target dependencies from CSV
    print("Loading repositories and dependencies from m5_dependencies.csv...")
    repos = load_repos_from_csv()  # Remove limit for full run
    target_dependencies = load_dependency_names_from_csv()
    
    if not repos:
        print("No repositories found. Exiting.")
        exit(1)
    
    if not target_dependencies:
        print("No target dependencies found. Exiting.")
        exit(1)
    
    # Check if user wants to resume or start fresh
    resume = True
    if os.path.exists(get_checkpoint_file()):
        response = input("Checkpoint found. Resume from checkpoint? (y/n): ").lower().strip()
        resume = response in ['y', 'yes', '']
        if not resume:
            clear_checkpoint()
    
    # Get direct dependencies for all repos in the CSV
    print("Fetching direct dependencies for repositories...")
    results = get_direct_dependencies_for_repos(repos, target_dependencies, resume=resume)
    
    # Print summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    total_deps = 0
    for repo_key, repo_data in results.items():
        deps_count = repo_data['total_direct_deps']
        total_deps += deps_count
        print(f"{repo_key}: {deps_count} matching direct dependencies")
    
    print(f"\nTotal repositories processed: {len(results)}")
    print(f"Total matching dependencies found: {total_deps}")
    
    # Save to CSV
    save_results_to_csv(results)
    
    # Clear checkpoint on successful completion
    clear_checkpoint()