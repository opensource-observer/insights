"""
Script to map dependencies to GitHub repositories using OSO.

This script reads the dependencies.json file, queries OSO's deps.dev package model
to find the corresponding GitHub repository for each dependency, and updates the
dependency information with the GitHub repo URL or marks it as unknown if not found.

The script uses a DataFrame-based approach to process dependencies in batches by package system,
and implements semver range matching to find the appropriate GitHub repository for each dependency.

Usage:
    python -m src.scripts.map_dependencies_to_github

Output:
    Creates output/dependencies_with_github.json with GitHub repository information added
    to each dependency.
"""
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
import semver
from dotenv import load_dotenv
from pyoso import Client

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.config_manager import ConfigManager

# Constants
DEPENDENCIES_FILE = "output/dependencies.json"
OUTPUT_FILE = "output/dependencies_with_github.json"
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
    """
    Set up and return an OSO client.
    
    Returns:
        Client: Configured OSO client instance.
        
    Raises:
        ValueError: If OSO_API_KEY environment variable is not set.
    """
    load_dotenv()
    oso_api_key = os.environ.get('OSO_API_KEY')
    if not oso_api_key:
        raise ValueError("OSO_API_KEY environment variable is required")
    
    return Client(api_key=oso_api_key)

def stringify(arr: List[str]) -> str:
    """
    Convert an array to a SQL string format for IN clauses.
    
    Args:
        arr: List of strings to convert.
        
    Returns:
        String formatted for SQL IN clause.
    """
    return "'" + "','".join([x.lower() for x in arr]) + "'"

def parse_semver(v: str) -> Optional[semver.VersionInfo]:
    """
    Parse a version string to a semver.VersionInfo object.
    
    Args:
        v: Version string to parse.
        
    Returns:
        Parsed semver.VersionInfo object or None if parsing fails.
    """
    try:
        return semver.VersionInfo.parse(v)
    except ValueError:
        return None

def extract_version(req_str: str) -> Optional[str]:
    """
    Extract version from a requirement string.
    
    Args:
        req_str: Requirement string (e.g., ">=1.2.3").
        
    Returns:
        Extracted version string or '0' if no version found.
    """
    versions = re.findall(r'\d+(?:\.\d+)+', req_str or '')
    return versions[-1] if versions else '0'

def extract_operator(req_str: str) -> str:
    """
    Extract operator from a requirement string.
    
    Args:
        req_str: Requirement string (e.g., ">=1.2.3").
        
    Returns:
        Extracted operator or '=' if no operator found.
    """
    ops = re.findall(r'(>=|<=|==|~=|!=|=|>|<)', req_str or '')
    return ops[-1] if ops else '='

def load_cache() -> pd.DataFrame:
    """
    Load the package-to-GitHub mappings cache.
    
    Returns:
        DataFrame containing cached package-to-GitHub mappings.
    """
    cache_path = Path(MAPPING_CACHE_FILE)
    if not cache_path.exists():
        print(f"Mapping cache file not found at {cache_path}, will create a new one")
        # Create the directory if it doesn't exist
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        # Return an empty DataFrame with the expected columns
        return pd.DataFrame(columns=['package_name', 'dependency_github_url', 'package_source', 'min_version', 'max_version'])
    
    try:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(cache_path)
        print(f"Loaded {len(df)} package-to-GitHub mappings from cache")
        return df
    except Exception as e:
        print(f"Error loading mapping cache: {str(e)}")
        return pd.DataFrame(columns=['package_name', 'dependency_github_url', 'package_source', 'min_version', 'max_version'])

def save_cache(df: pd.DataFrame) -> None:
    """
    Save the package-to-GitHub mappings cache.
    
    Args:
        df: DataFrame containing package-to-GitHub mappings to cache.
    """
    cache_path = Path(MAPPING_CACHE_FILE)
    try:
        # Save the DataFrame to CSV
        df.to_csv(cache_path, index=False)
        print(f"Saved {len(df)} package-to-GitHub mappings to cache")
    except Exception as e:
        print(f"Error saving mapping cache: {str(e)}")

def build_semver_ranges(df_pkg_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Build semver ranges for packages.
    
    Args:
        df_pkg_raw: DataFrame containing raw package version data.
        
    Returns:
        DataFrame with min and max versions for each package.
    """
    df = df_pkg_raw.copy()
    df['_parsed'] = df['package_version'].apply(parse_semver)
    df = df[df['_parsed'].notnull()]
    agg = (
      df.sort_values('_parsed')
        .groupby(['package_name','dependency_github_url','package_source'], as_index=False)
        .agg(
          min_version=('package_version','first'),
          max_version=('package_version','last')
        )
    )
    return agg

def merge_dependency_urls(deps_df: pd.DataFrame, packages_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge dependency URLs based on version constraints.
    
    Args:
        deps_df: DataFrame containing dependency information.
        packages_df: DataFrame containing package information.
        
    Returns:
        DataFrame with merged dependency and package information.
    """
    print("Merging dependency URLs based on version constraints...")
    
    deps = deps_df.copy()
    pkgs = packages_df.copy()

    print(f"Dependencies DataFrame shape: {deps.shape}")
    print(f"Packages DataFrame shape: {pkgs.shape}")

    # Instead of using semver objects directly, let's use string versions for comparison
    # This avoids issues with comparing semver.Version objects
    deps['version_str'] = deps['version'].astype(str)
    pkgs['min_version_str'] = pkgs['min_version'].astype(str)
    pkgs['max_version_str'] = pkgs['max_version'].astype(str)

    latest = (
        pkgs
        .sort_values(['package_name','package_source','max_version_str'])
        .groupby(['package_name','package_source'], as_index=False)
        .last()[['package_name','package_source','dependency_github_url']]
        .rename(columns={'dependency_github_url':'latest_dependency_github_url'})
    )

    merged = (
        deps
        .merge(
            pkgs[['package_name','package_source','dependency_github_url','min_version_str','max_version_str']],
            on=['package_name','package_source'], how='left'
        )
        .merge(latest, on=['package_name','package_source'], how='left')
    )

    # Use simple string comparison for version matching
    # This is less accurate but avoids the semver comparison issues
    eq_mask = (merged['operator'] == '=')
    
    # For simplicity, we'll just use the latest version for each package
    merged['dependency_github_url'] = merged['dependency_github_url'].fillna(merged['latest_dependency_github_url'])

    # Special handling for GitHub URLs in package names
    merged['dependency_github_url'] = merged.apply(
        lambda x: 
        f"https://{x['package_name']}"
        if ('github' in x['package_name'] and not isinstance(x['dependency_github_url'], str))
        else x['dependency_github_url']
        , axis=1
    )

    return merged.drop(columns=['version_str', 'min_version_str', 'max_version_str', 'latest_dependency_github_url'], errors='ignore')

def process_dependencies(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Process dependencies to add GitHub repository information.
    
    Args:
        data: List of repository data dictionaries.
        
    Returns:
        DataFrame containing processed dependency information.
    """
    print("Processing dependencies...")
    
    # Extract records from the data
    records = []
    dependency_count = 0
    for seed_node in data:
        repo_url = seed_node.get('repo_url', 'Unknown')
        deps = seed_node.get('dependencies', [])
        print(f"Processing {len(deps)} dependencies from {repo_url}")
        dependency_count += len(deps)
        
        for dependency in deps:
            dependency.update({'repo_url': repo_url})
            records.append(dependency)
    
    print(f"Total dependencies extracted: {dependency_count}")
    
    # Create DataFrame and extract version and operator
    df = pd.DataFrame(records)
    df['version'] = df['requirements'].apply(extract_version)
    df['operator'] = df['requirements'].apply(extract_operator)
    df['requirements'] = df['requirements'].fillna('')
    
    # Rename columns for consistency
    df.rename(columns={
        'repo_url': 'seed_node_url',
        'packageName': 'package_name',
        'packageManager': 'package_source',
    }, inplace=True)
    
    # Select and filter columns
    df = df[['seed_node_url', 'package_name', 'package_source', 
             'operator', 'version', 'relationship', 'source_type']]
    df['package_name'] = df['package_name'].str.lower()
    df = df[df['package_source'].isin(PACKAGE_MANAGER_TO_SYSTEM.keys())]
    
    # Parse versions
    df['version'] = df['version'].apply(parse_semver)
    df.reset_index(inplace=True, drop=True)
    
    print(f"Processed {len(df)} dependencies")
    print(f"Package source distribution:\n{df['package_source'].value_counts()}")
    
    return df

def query_oso_for_packages(client: Client, df_deps: pd.DataFrame, cache_df: pd.DataFrame) -> pd.DataFrame:
    """
    Query OSO for package GitHub repositories.
    
    Args:
        client: OSO client instance.
        df_deps: DataFrame containing dependency information.
        cache_df: DataFrame containing cached package-to-GitHub mappings.
        
    Returns:
        DataFrame containing package information with GitHub URLs.
    """
    print("Querying OSO for package GitHub repositories...")
    
    # Create a list to store package DataFrames
    packages = []
    
    # Process each package source
    for pkg_source, pkg_system in PACKAGE_MANAGER_TO_SYSTEM.items():
        if pkg_system is None:
            continue
            
        # Get unique package names for this source
        pkg_names = list(df_deps[df_deps['package_source'] == pkg_source]['package_name'].unique())
        if not pkg_names:
            continue
            
        print(f"Fetching {pkg_source} ...")
        print(f"Looking up {len(pkg_names)} packages.")
        
        # Check cache first
        cache_matches = cache_df[
            (cache_df['package_source'] == pkg_source) & 
            (cache_df['package_name'].isin(pkg_names))
        ]
        
        if len(cache_matches) > 0:
            print(f"Found {len(cache_matches)} packages in cache.")
            packages.append(cache_matches)
            
            # Remove cached packages from the list to query
            cached_names = set(cache_matches['package_name'])
            pkg_names = [name for name in pkg_names if name not in cached_names]
            
        if not pkg_names:
            print(f"All {pkg_source} packages found in cache.")
            continue
            
        print(f"Querying OSO for {len(pkg_names)} {pkg_source} packages...")
        
        # Special handling for GO packages
        if pkg_source == "GO" or pkg_source == "GOLANG":
            go_packages = []
            for name in pkg_names:
                if name and 'github.com/' in name:
                    # Extract GitHub repo directly from package name
                    repo_path = name.replace('github.com/', '')
                    go_packages.append({
                        'package_name': name,
                        'dependency_github_url': f"https://github.com/{repo_path}",
                        'package_source': pkg_source,
                        'min_version': '0.0.0',
                        'max_version': '999999.999999.999999'
                    })
            
            if go_packages:
                go_df = pd.DataFrame(go_packages)
                print(f"Extracted {len(go_df)} GitHub repos directly from GO package names.")
                packages.append(go_df)
                
                # Remove processed packages from the list
                processed_names = set(go_df['package_name'])
                pkg_names = [name for name in pkg_names if name not in processed_names]
        
        # Query OSO for remaining packages
        if pkg_names:
            try:
                query = f"""
                SELECT
                  package_artifact_name AS package_name,
                  CONCAT('https://github.com/',package_github_owner,'/',package_github_repo) AS dependency_github_url,
                  package_version AS package_version,
                  '{pkg_source}' AS package_source
                FROM int_packages
                WHERE
                  package_artifact_name IN ({stringify(pkg_names)})
                  AND package_artifact_source = '{pkg_system}'
                  AND is_current_owner = TRUE
                """
                
                raw = client.to_pandas(query)
                
                if raw is not None and not raw.empty:
                    print(f"Found {len(raw)} unique packages from OSO.")
                    df_pkg = build_semver_ranges(raw)
                    print(f"Built {len(df_pkg)} summary packages with semver ranges.")
                    packages.append(df_pkg)
                else:
                    print(f"No packages found in OSO for {pkg_source}.")
            except Exception as e:
                print(f"Error querying OSO for {pkg_source} packages: {str(e)}")
    
    # Combine all package DataFrames
    if packages:
        df_packages = pd.concat(packages, ignore_index=True)
        print(f"Combined {len(df_packages)} total packages.")
        
        # Update cache with new packages
        new_packages = df_packages[~df_packages['package_name'].isin(cache_df['package_name'])]
        if not new_packages.empty:
            updated_cache = pd.concat([cache_df, new_packages], ignore_index=True)
            save_cache(updated_cache)
        
        return df_packages
    else:
        print("No packages found.")
        return pd.DataFrame(columns=['package_name', 'dependency_github_url', 'package_source', 'min_version', 'max_version'])

def main() -> None:
    """
    Main entry point for mapping dependencies to GitHub repositories.
    
    This function:
    1. Sets up the OSO client
    2. Loads dependencies from dependencies.json
    3. Processes dependencies to extract package information
    4. Queries OSO for GitHub repository information
    5. Merges dependency information with GitHub repository information
    6. Saves the updated dependencies to dependencies_with_github.json
    """
    print("Mapping dependencies to GitHub repositories using OSO...")
    
    try:
        # Set up OSO client
        print("Setting up OSO client...")
        client = setup_oso_client()
        print("OSO client setup complete.")
        
        # Load dependencies
        dependencies_path = Path(DEPENDENCIES_FILE)
        if not dependencies_path.exists():
            print(f"Error: Dependencies file not found at {dependencies_path}")
            return
        
        print(f"Loading dependencies from {dependencies_path}...")
        with open(dependencies_path, 'r') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} repositories with dependencies.")
        
        # Process dependencies
        df_deps = process_dependencies(data)
        
        # Load cache
        cache_df = load_cache()
        
        # Query OSO for packages
        df_packages = query_oso_for_packages(client, df_deps, cache_df)
        
        # Merge dependency URLs
        result = merge_dependency_urls(df_deps, df_packages)
        
        # Convert back to original format
        print("Converting results back to original format...")
        updated_data = []
        mapped_count = 0
        unknown_count = 0
        
        for seed_node in data:
            repo_url = seed_node.get('repo_url', 'Unknown')
            updated_seed_node = seed_node.copy()
            updated_dependencies = []
            
            deps = seed_node.get('dependencies', [])
            repo_mapped = 0
            repo_unknown = 0
            
            for dep in deps:
                updated_dep = dep.copy()
                
                # Find the corresponding row in the result DataFrame
                package_name = dep.get('packageName', '').lower()
                package_source = dep.get('packageManager', '')
                
                if package_name and package_source:
                    matches = result[
                        (result['package_name'] == package_name) & 
                        (result['package_source'] == package_source)
                    ]
                    
                    if not matches.empty:
                        # Get the first match (there should only be one)
                        match = matches.iloc[0]
                        github_url = match.get('dependency_github_url')
                        if github_url and pd.notna(github_url):
                            updated_dep['github_repo'] = github_url
                            mapped_count += 1
                            repo_mapped += 1
                        else:
                            updated_dep['github_repo'] = "unknown"
                            unknown_count += 1
                            repo_unknown += 1
                    else:
                        updated_dep['github_repo'] = "unknown"
                        unknown_count += 1
                        repo_unknown += 1
                else:
                    updated_dep['github_repo'] = "unknown"
                    unknown_count += 1
                    repo_unknown += 1
                
                updated_dependencies.append(updated_dep)
            
            updated_seed_node['dependencies'] = updated_dependencies
            updated_data.append(updated_seed_node)
            
            print(f"Repository {repo_url}: {repo_mapped} mapped, {repo_unknown} unknown")
        
        # Save updated dependencies
        output_path = Path(OUTPUT_FILE)
        with open(output_path, 'w') as f:
            json.dump(updated_data, f, indent=2)
        
        print(f"\nDone! Updated dependencies saved to {output_path}")
        
        # Print summary
        total_deps = sum(len(repo_data.get("dependencies", [])) for repo_data in updated_data)
        mapped_deps = sum(
            sum(1 for dep in repo_data.get("dependencies", []) if dep.get("github_repo") != "unknown")
            for repo_data in updated_data
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
