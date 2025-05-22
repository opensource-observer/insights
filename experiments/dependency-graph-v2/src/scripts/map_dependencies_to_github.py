"""
Script to map dependencies to GitHub repositories using OSO.

This script reads the dependencies.json file, queries OSO's deps.dev package model
to find the corresponding GitHub repository for each dependency, and updates the
dependency information with the GitHub repo URL or marks it as unknown if not found.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from dotenv import load_dotenv
from pyoso import Client
import time

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Constants
DEPENDENCIES_FILE = "output/dependencies.json"
OUTPUT_FILE = "output/dependencies_with_github.json"
BATCH_SIZE = 50  # Number of dependencies to process in a batch
SLEEP_TIME = 1  # Time to sleep between batches to avoid rate limiting
MAPPING_CACHE_FILE = "data/package_github_mappings.csv"

# GitHub repositories are mapped to package managers: 
# NPM, GO, PIP, RUST, GRADLE, RUBYGEMS, NUGET, GITHUBACTIONS, ACTIONS
# OSO only supports these package managers: NPM, NUGET, PYPI, MAVEN, GO, RUBYGEMS, CARGO
PACKAGE_MANAGER_TO_SYSTEM = {
    # Directly supported package managers
    "NPM": "NPM",
    "NUGET": "NUGET",
    "PYPI": "PYPI",
    "MAVEN": "MAVEN",
    "GO": "GO",
    "RUBYGEMS": "RUBYGEMS",
    "CARGO": "CARGO",
    
    # Aliases and related package managers
    "CRATES.IO": "CARGO",
    "RUST": "CARGO",
    "PIP": "PYPI",    
    "YARN": "NPM",
    "PNPM": "NPM",
    "GRADLE": "MAVEN",
    "SBT": "MAVEN",
    "IVY": "MAVEN",
    
    # Unsupported package managers (mapped to None)
    "COMPOSER": None,
    "PACKAGIST": None,
    "COCOAPODS": None,
    "SWIFT": None,
    "DART": None,
    "PUB": None,
    "BOWER": None,
    "CONDA": None,
    "HOMEBREW": None,
    "APT": None,
    "YUM": None,
    "ALPINE": None,
    "DEBIAN": None,
    "ACTIONS": None,
    "GITHUBACTIONS": None,
    "UNKNOWN": None
}

def setup_oso_client() -> Client:
    """Set up and return an OSO client."""
    load_dotenv()
    oso_api_key = os.environ.get('OSO_API_KEY')
    if not oso_api_key:
        raise ValueError("OSO_API_KEY environment variable is required")
    
    return Client(api_key=oso_api_key)

def parse_package_url(package_url: str) -> Dict[str, str]:
    """
    Parse a package URL (purl) to extract system, name, and version.
    
    Example purl: pkg:npm/content-disposition@0.5.4
    """
    result = {
        "system": None,
        "name": None,
        "version": None
    }
    
    if not package_url or not isinstance(package_url, str) or not package_url.startswith("pkg:"):
        return result
    
    # Remove 'pkg:' prefix
    package_url = package_url[4:]
    
    # Split by '/' to get system and the rest
    parts = package_url.split('/', 1)
    if len(parts) < 2:
        return result
    
    system, rest = parts
    result["system"] = system.upper()
    
    # Handle namespace if present
    if '/' in rest:
        # For namespaced packages like pkg:npm/@babel/core@7.12.3
        # or pkg:maven/org.springframework/spring-core@5.3.9
        if rest and rest.startswith('@'):
            # NPM scoped package
            name_version = rest
            at_pos = name_version.rfind('@')
            if at_pos > 0:
                result["name"] = name_version[:at_pos]
                result["version"] = name_version[at_pos+1:]
            else:
                result["name"] = name_version
        else:
            # Maven-like groupId/artifactId
            namespace_rest = rest.split('/', 1)
            if len(namespace_rest) == 2:
                namespace, name_version = namespace_rest
                at_pos = name_version.rfind('@')
                if at_pos > 0:
                    result["name"] = f"{namespace}/{name_version[:at_pos]}"
                    result["version"] = name_version[at_pos+1:]
                else:
                    result["name"] = f"{namespace}/{name_version}"
            else:
                result["name"] = rest
    else:
        # For non-namespaced packages like pkg:npm/lodash@4.17.21
        at_pos = rest.rfind('@')
        if at_pos > 0:
            result["name"] = rest[:at_pos]
            result["version"] = rest[at_pos+1:]
        else:
            result["name"] = rest
    
    return result

# Helper function to convert array to SQL string format
def stringify(arr):
    """Convert an array to a SQL string format for IN clauses."""
    return "'" + "','".join([a.lower() for a in arr]) + "'"

def load_mapping_cache() -> Dict[str, str]:
    """
    Load existing package-to-GitHub mappings from the cache file.
    
    Returns:
        Dictionary mapping package keys (system:name@version) to GitHub repository URLs
    """
    cache_path = Path(MAPPING_CACHE_FILE)
    if not cache_path.exists():
        print(f"Mapping cache file not found at {cache_path}, will create a new one")
        # Create the directory if it doesn't exist
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        return {}
    
    try:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(cache_path)
        
        # Convert DataFrame to dictionary
        mapping = {}
        for _, row in df.iterrows():
            key = f"{row['system']}:{row['name']}@{row['version']}"
            mapping[key] = row['github_repo']
        
        print(f"Loaded {len(mapping)} package-to-GitHub mappings from cache")
        return mapping
    except Exception as e:
        print(f"Error loading mapping cache: {str(e)}")
        return {}

def save_mapping_cache(mapping: Dict[str, str]):
    """
    Save package-to-GitHub mappings to the cache file.
    
    Args:
        mapping: Dictionary mapping package keys (system:name@version) to GitHub repository URLs
    """
    cache_path = Path(MAPPING_CACHE_FILE)
    
    # Debug output
    print(f"Debug: Mapping cache contains {len(mapping)} entries")
    for key, value in list(mapping.items())[:5]:  # Print first 5 entries for debugging
        print(f"Debug: Cache entry - {key}: {value}")
    
    try:
        # Convert new mappings from dictionary to DataFrame
        new_data = []
        for key, github_repo in mapping.items():
            if github_repo == "unknown":
                continue  # Don't cache unknown mappings
                
            try:
                # Parse the key (system:name@version)
                if ':' not in key:
                    print(f"Debug: Invalid key format (missing colon): {key}")
                    continue
                    
                system, name_version = key.split(':', 1)
                
                if '@' not in name_version:
                    print(f"Debug: Invalid name_version format (missing @): {name_version}")
                    continue
                    
                name, version = name_version.split('@', 1)
                
                new_data.append({
                    'system': system,
                    'name': name,
                    'version': version,
                    'github_repo': github_repo
                })
            except Exception as e:
                print(f"Error parsing key {key}: {str(e)}")
                continue
        
        # Debug output
        print(f"Debug: Processed {len(new_data)} valid entries for saving to cache")
        
        # If we have new data to save
        if new_data:
            new_df = pd.DataFrame(new_data)
            
            # Check if the cache file exists
            if cache_path.exists():
                try:
                    # Load existing cache
                    existing_df = pd.read_csv(cache_path)
                    
                    # Create a unique key for each row to identify duplicates
                    def create_key(row):
                        return f"{row['system']}:{row['name']}@{row['version']}"
                    
                    # Add key column to both dataframes
                    existing_df['key'] = existing_df.apply(create_key, axis=1)
                    new_df['key'] = new_df.apply(create_key, axis=1)
                    
                    # Remove duplicates from existing_df that are in new_df
                    existing_df = existing_df[~existing_df['key'].isin(new_df['key'])]
                    
                    # Combine dataframes and remove the key column
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    combined_df = combined_df.drop('key', axis=1)
                    
                    # Save combined DataFrame to CSV
                    combined_df.to_csv(cache_path, index=False)
                    print(f"Saved {len(combined_df)} package-to-GitHub mappings to cache (appended {len(new_df)} new entries)")
                except Exception as e:
                    print(f"Error loading existing cache, creating new one: {str(e)}")
                    # Save just the new DataFrame to CSV
                    new_df.to_csv(cache_path, index=False)
                    print(f"Saved {len(new_df)} package-to-GitHub mappings to new cache")
            else:
                # Save just the new DataFrame to CSV
                new_df.to_csv(cache_path, index=False)
                print(f"Saved {len(new_df)} package-to-GitHub mappings to new cache")
        else:
            # If no new data and file doesn't exist, create an empty DataFrame with the correct columns
            if not cache_path.exists():
                df = pd.DataFrame(columns=['system', 'name', 'version', 'github_repo'])
                df.to_csv(cache_path, index=False)
                print("Created empty cache file")
            else:
                print("No new mappings to save to cache")
    except Exception as e:
        print(f"Error saving mapping cache: {str(e)}")

def batch_query_github_repos(client: Client, system: str, packages: List[Dict], cache: Dict[str, str] = None) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Query OSO's deps.dev package model to find GitHub repositories for multiple packages at once.
    
    Args:
        client: OSO client
        system: Package system (e.g., NPM, MAVEN)
        packages: List of package dictionaries with 'name' and 'version' keys
        cache: Optional dictionary of cached mappings
        
    Returns:
        Dictionary mapping package keys (name@version) to GitHub repository URLs
    """
    if not system or not packages:
        return {}
    
    # Initialize cache if not provided
    if cache is None:
        cache = {}
    
    # Extract unique package names and versions
    package_names = []
    package_versions = []
    package_keys = []  # name@version format for mapping back
    packages_to_query = []  # Packages not in cache that need to be queried
    
    result_map = {}  # Final result map
    
    # First check cache for each package
    for pkg in packages:
        name = pkg.get('name')
        version = pkg.get('version')
        if name and version:
            key = f"{name}@{version}"
            cache_key = f"{system}:{key}"
            
            # Check if in cache
            if cache_key in cache:
                result_map[key] = cache[cache_key]
            else:
                # Need to query this package
                packages_to_query.append(pkg)
                package_names.append(name)
                package_versions.append(version)
                package_keys.append(key)
    
    if not packages_to_query:
        print(f"All {len(packages)} {system} packages found in cache")
        return result_map, cache
    
    print(f"Found {len(result_map)} packages in cache, querying OSO for {len(packages_to_query)} packages")
    
    # Create batches of 500 packages at a time to avoid query size limits
    batch_size = 500
    new_mappings = {}  # New mappings to add to cache
    
    for i in range(0, len(package_names), batch_size):
        batch_names = package_names[i:i+batch_size]
        batch_keys = package_keys[i:i+batch_size]
        
        try:
            # Construct the query with IN clauses
            query = f"""
            SELECT
              LOWER(p.name) as name,
              LOWER(p.version) AS version,
              LOWER(p.project_name) AS project_name
            FROM stg_deps_dev__packages AS p
            WHERE 
              p.snapshot_at BETWEEN DATE '2025-05-12' AND DATE '2025-05-13'
              AND LOWER(p.name) IN ({stringify(batch_names)})            
              AND p.project_type = 'GITHUB'
              AND p.system = '{system}'
            """
            
            # Execute the query using the client's to_pandas method
            result = client.to_pandas(query)
            
            # Process the results
            if result is not None and not result.empty:
                # Create a mapping of name@version to project_name
                for _, row in result.iterrows():
                    pkg_name = row['name']
                    pkg_version = row['version']
                    project_name = row['project_name']
                    key = f"{pkg_name}@{pkg_version}"
                    
                    if project_name:
                        github_repo = f"https://github.com/{project_name}"
                        result_map[key] = github_repo
                        
                        # Add to new mappings for cache
                        cache_key = f"{system}:{key}"
                        new_mappings[cache_key] = github_repo
                        
                        # Also update the main cache
                        cache[cache_key] = github_repo
                        print(f"Debug: Added to cache - {cache_key}: {github_repo}")
            
            # Mark packages not found as unknown in the result map
            for key in batch_keys:
                if key not in result_map:
                    result_map[key] = "unknown"
            
            found_count = sum(1 for key in batch_keys if result_map.get(key) != "unknown")
            print(f"Processed batch of {len(batch_names)} {system} packages, found {found_count} GitHub repos")
            
        except Exception as e:
            print(f"Error querying OSO for batch of {system} packages: {str(e)}")
            
            # Mark all packages in this batch as unknown
            for key in batch_keys:
                if key not in result_map:
                    result_map[key] = "unknown"
        
        try:
            save_mapping_cache(cache)
        except Exception as e:
            print(f"Warning: failed to save cache after {system} batch starting at index {i}: {e}")
    
    # Update cache with new mappings
    cache.update(new_mappings)
    
    # Debug output to see what's in the cache before returning
    print(f"Debug: At the end of batch_query_github_repos, cache contains {len(cache)} entries")
    
    return result_map, cache

def get_github_repo_from_oso(client: Client, system: str, name: str, version: str) -> Optional[str]:
    """
    Query OSO's deps.dev package model to find the GitHub repository for a single package.
    This is a wrapper around batch_query_github_repos for backward compatibility.
    
    Args:
        client: OSO client
        system: Package system (e.g., NPM, MAVEN)
        name: Package name
        version: Package version
        
    Returns:
        GitHub repository URL or None if not found
    """
    if not system or not name or not version:
        return None
    
    packages = [{'name': name, 'version': version}]
    result_map, _ = batch_query_github_repos(client, system, packages)
    
    key = f"{name}@{version}"
    return result_map.get(key)

def process_dependencies(dependencies: List[Dict], client: Client, cache: Dict[str, str] = None) -> Tuple[List[Dict], Dict[str, str]]:
    """
    Process dependencies to add GitHub repository information.
    
    Args:
        dependencies: List of dependency objects
        client: OSO client
        cache: Optional dictionary of cached mappings
        
    Returns:
        Updated list of dependency objects with GitHub repository information
    """
    # Debug output to see what's in the cache at the start of process_dependencies
    if cache is not None:
        print(f"Debug: At the start of process_dependencies, cache contains {len(cache)} entries")
    total_deps = len(dependencies)
    print(f"Processing {total_deps} dependencies...")
    
    # Parse all dependencies and group by system
    system_packages = {}  # system -> list of package dicts with name and version
    dep_mapping = {}  # (system, name, version) -> dependency object index
    
    for i, dep in enumerate(dependencies):
        try:
            # Debug output for problematic dependencies
            if i < 5 or i % 10 == 0:  # Print first 5 and every 10th dependency for debugging
                print(f"Debug: Processing dependency {i}: {dep.get('packageName', 'Unknown')} - {dep.get('packageManager', 'Unknown')}")
            
            # Parse package URL to get system, name, and version
            package_url = dep.get("packageUrl", "")
            parsed = parse_package_url(package_url)
            
            # Get system from packageManager if not found in package URL
            if not parsed["system"] and "packageManager" in dep:
                system_name = dep["packageManager"].upper() if dep["packageManager"] else "UNKNOWN"
                parsed["system"] = PACKAGE_MANAGER_TO_SYSTEM.get(system_name)
                if i < 5 or i % 10 == 0:
                    print(f"Debug: Using packageManager: {system_name} -> {parsed['system']}")
            
            # Get name from packageName if not found in package URL
            if not parsed["name"] and "packageName" in dep:
                parsed["name"] = dep["packageName"]
                if i < 5 or i % 10 == 0:
                    print(f"Debug: Using packageName: {parsed['name']}")
            
            # Get version from requirements if not found in package URL
            if not parsed["version"] and "requirements" in dep:
                # Clean up version string (remove constraints like ^, ~, >=, etc.)
                version = dep.get("requirements")
                if version and isinstance(version, str):  # Check if version is not None, empty, and is a string
                    try:
                        for prefix in ["^", "~", ">=", "<=", ">", "<", "="]:
                            if version.startswith(prefix):
                                version = version[len(prefix):]
                        parsed["version"] = version.strip()
                        if i < 5 or i % 10 == 0:
                            print(f"Debug: Using requirements: {parsed['version']}")
                    except Exception as e:
                        print(f"Error processing version '{version}': {str(e)}")
                        # Set a default version if there's an error
                        parsed["version"] = "0.0.0"
                else:
                    # If requirements exists but is not a valid string, set a default version
                    if i < 5 or i % 10 == 0:
                        print(f"Debug: Invalid requirements value: {version}, type: {type(version)}")
                    parsed["version"] = "0.0.0"
            
            # Store the parsed information
            system = parsed["system"]
            name = parsed["name"]
            version = parsed["version"]
            
            if system and name and version:
                if system not in system_packages:
                    system_packages[system] = []
                
                system_packages[system].append({
                    'name': name,
                    'version': version
                })
                
                dep_mapping[(system, name, version)] = i
        except Exception as e:
            print(f"Error processing dependency {i}: {str(e)}")
            print(f"Dependency data: {dep}")
    
    # Create a copy of the dependencies list for updating
    updated_dependencies = [dep.copy() for dep in dependencies]
    
    # Process each system's packages in batches
    for system, packages in system_packages.items():
        print(f"\nProcessing {len(packages)} {system} packages...")

        # Special handling for GOLANG packages - extract GitHub repo directly from package name
        if system == "GOLANG" or system == "GO":
            print(f"Using direct extraction for {len(packages)} {system} packages...")
            repo_map = {}
            new_mappings = {}
            
            for pkg in packages:
                name = pkg['name']
                version = pkg['version']
                key = f"{name}@{version}"
                
                # Check if the name is not None and starts with "github.com/"
                if name and name.startswith("github.com/"):
                    # Extract the GitHub repository path (remove "github.com/")
                    repo_path = name[len("github.com/"):]
                    github_repo = f"https://github.com/{repo_path}"
                    repo_map[key] = github_repo
                    
                    # Add to cache
                    cache_key = f"{system}:{key}"
                    new_mappings[cache_key] = github_repo
                    cache[cache_key] = github_repo
                    print(f"Debug: Added to cache from direct extraction - {cache_key}: {github_repo}")
                else:
                    repo_map[key] = "unknown"
            
            # Update cache with new mappings
            cache.update(new_mappings)
            print(f"Extracted {len(new_mappings)} GitHub repos directly from package names")
        else:
            # Query OSO for GitHub repositories in batches for other package systems
            repo_map, cache = batch_query_github_repos(client, system, packages, cache)
        
        # Update dependencies with GitHub repository information
        for pkg in packages:
            name = pkg['name']
            version = pkg['version']
            key = f"{name}@{version}"
            
            # Find the corresponding dependency
            dep_idx = dep_mapping.get((system, name, version))
            if dep_idx is not None:
                # Update with GitHub repository information
                github_repo = repo_map.get(key)
                updated_dependencies[dep_idx]["github_repo"] = github_repo if github_repo else "unknown"
    
    # Mark any dependencies that weren't processed as unknown
    for i, dep in enumerate(updated_dependencies):
        if "github_repo" not in dep:
            dep["github_repo"] = "unknown"
    
    # Debug output to see what's in the cache at the end of process_dependencies
    if cache is not None:
        print(f"Debug: At the end of process_dependencies, cache contains {len(cache)} entries")
    
    return updated_dependencies, cache

def update_repo_dependencies(repo_data: Dict, client: Client, cache: Dict[str, str] = None) -> Tuple[Dict, Dict[str, str]]:
    """
    Update repository dependencies with GitHub repository information.
    
    Args:
        repo_data: Repository data object
        client: OSO client
        cache: Optional dictionary of cached mappings
        
    Returns:
        Tuple of (updated repository data object, updated cache)
    """
    if "dependencies" in repo_data:
        updated_dependencies, updated_cache = process_dependencies(repo_data["dependencies"], client, cache)
        repo_data["dependencies"] = updated_dependencies
        cache = updated_cache
    
    return repo_data, cache

def main():
    """Main entry point."""
    print("Mapping dependencies to GitHub repositories using OSO...")
    
    try:
        # Set up OSO client
        client = setup_oso_client()
        
        # Load mapping cache
        mapping_cache = load_mapping_cache()
        
        # Load dependencies
        dependencies_path = Path(DEPENDENCIES_FILE)
        if not dependencies_path.exists():
            print(f"Error: Dependencies file not found at {dependencies_path}")
            return
        
        with open(dependencies_path, 'r') as f:
            repos_data = json.load(f)
        
        # Process each repository
        updated_repos_data = []
        for i, repo_data in enumerate(repos_data):
            print(f"\nProcessing repository {i + 1}/{len(repos_data)}: {repo_data.get('repo_url', 'Unknown')}")
            
            # Update repository dependencies using the mapping cache
            updated_repo_data, mapping_cache = update_repo_dependencies(repo_data, client, mapping_cache)
            updated_repos_data.append(updated_repo_data)
        
        # Save the updated mapping cache
        save_mapping_cache(mapping_cache)
        
        # Save updated dependencies
        output_path = Path(OUTPUT_FILE)
        with open(output_path, 'w') as f:
            json.dump(updated_repos_data, f, indent=2)
        
        print(f"\nDone! Updated dependencies saved to {output_path}")
        
        # Print summary
        total_deps = sum(len(repo_data.get("dependencies", [])) for repo_data in updated_repos_data)
        mapped_deps = sum(
            sum(1 for dep in repo_data.get("dependencies", []) if dep.get("github_repo") != "unknown")
            for repo_data in updated_repos_data
        )
        unknown_deps = total_deps - mapped_deps
        
        print(f"\nSummary:")
        print(f"  Total dependencies: {total_deps}")
        mapped_percentage = (mapped_deps / total_deps) * 100 if total_deps > 0 else 0
        unknown_percentage = (unknown_deps / total_deps) * 100 if total_deps > 0 else 0
        print(f"  Mapped to GitHub: {mapped_deps} ({mapped_percentage:.1f}%)")
        print(f"  Unknown: {unknown_deps} ({unknown_percentage:.1f}%)")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
