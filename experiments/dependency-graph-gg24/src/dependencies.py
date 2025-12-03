import os
import time
import random
import pandas as pd
import requests
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
from dotenv import load_dotenv
from pyoso import Client

# Import local parser for fallback
try:
    from local_parser import fetch_dependencies_locally
    LOCAL_PARSER_AVAILABLE = True
except ImportError:
    LOCAL_PARSER_AVAILABLE = False
    print("Warning: local_parser not available. Install dependencies: pip install toml")

load_dotenv()

def stringify(arr: List[str]) -> str:
    """Join a list of strings for use in a SQL IN (...) clause, escaping single quotes."""
    escaped = [s.replace("'", "''") for s in arr]
    return "'" + "','".join(escaped) + "'"

CSV_URL = "https://raw.githubusercontent.com/davidgasquez/gg24-deepfunding-market-weights/refs/heads/main/data/phase_2/weights/elo.csv"

def get_seed_repos():
    df_seed_repos = pd.read_csv(CSV_URL)
    seed_repo_list = list(df_seed_repos['item'].str.lower())
    return seed_repo_list

def get_oso_client() -> Client:
    api_key = os.getenv("OSO_API_KEY")
    if not api_key:
        raise ValueError("OSO_API_KEY environment variable is required")
    return Client(api_key=api_key)

def get_dependencies(repo_list):
    oso_client = get_oso_client()
    query = f"""
    SELECT
      artifact_id,
      artifact_url,
      node_id AS github_graphql_repo_id,
      name_with_owner
    FROM oso.int_repositories__ossd
    WHERE name_with_owner IN ({stringify(repo_list)})
    """
    df = oso_client.to_pandas(query)
    return df

def fetch_github_dependencies_simple(owner: str, repo: str, github_token: str, timeout: int = 120) -> Dict:
    """
    Fetch repository dependencies using GitHub's GraphQL API (simple approach).
    
    This is the faster approach that works for most repositories. Falls back to
    paginated approach if timeout is encountered.
    
    Args:
        owner: Repository owner
        repo: Repository name
        github_token: GitHub API token
        timeout: Request timeout in seconds (default: 60)
    
    Returns:
        Dictionary containing dependency data or empty structure on failure/timeout
    """
    graphql_url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Content-Type": "application/json",
    }
    
    query = """
    query($owner: String!, $repo: String!, $depFirst: Int!) {
        repository(owner: $owner, name: $repo) {
            dependencyGraphManifests(first: 100) {
                nodes {
                    filename
                    dependencies(first: $depFirst) {
                        pageInfo {
                            hasNextPage
                        }
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
        "repo": repo,
        "depFirst": 100  # Maximum allowed by GitHub API for dependencies per manifest
    }
    
    try:
        response = requests.post(
            graphql_url,
            headers=headers,
            json={"query": query, "variables": variables},
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            errors = data["errors"]
            # Check if this is a timeout error
            is_timeout = any(
                "timeout" in str(e.get("message", "")).lower() 
                or "timedout" in str(e.get("message", "")).lower()
                for e in errors
            )
            if is_timeout:
                print(f"  Timeout detected for {owner}/{repo} - will try paginated approach")
                return {"timeout": True, "data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
            print(f"GraphQL errors for {owner}/{repo}: {errors}")
            return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
        
        if not data.get("data", {}).get("repository"):
            print(f"No repository data found for {owner}/{repo}")
            return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
        
        manifests = data["data"]["repository"]["dependencyGraphManifests"]["nodes"]
        if manifests:
            total_deps = sum(len(m.get("dependencies", {}).get("nodes", [])) for m in manifests)
            # Check if any manifest has more dependencies that need pagination
            has_more_deps = any(
                m.get("dependencies", {}).get("pageInfo", {}).get("hasNextPage", False)
                for m in manifests
            )
            if has_more_deps:
                print(f"Found {len(manifests)} manifests with {total_deps}+ dependencies (some need pagination) for {owner}/{repo}")
                print(f"  Falling back to paginated approach to get all dependencies...")
                return {"timeout": True, "data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
            print(f"Found {len(manifests)} manifests with {total_deps} total dependencies for {owner}/{repo}")
        
        return data
    except requests.exceptions.Timeout:
        print(f"  Request timeout for {owner}/{repo} - will try paginated approach")
        return {"timeout": True, "data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
    except Exception as e:
        print(f"Error fetching dependencies for {owner}/{repo}: {str(e)}")
        return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}

def fetch_github_dependencies_paginated(owner: str, repo: str, github_token: str, max_retries: int = 7, timeout: int = 120) -> Dict:
    """
    Fetch repository dependencies using GitHub's GraphQL API with pagination and retry logic.
    
    Uses pagination to fetch manifests and dependencies in smaller chunks to avoid timeouts
    for repositories with large dependency graphs. This is the fallback approach when the
    simple method encounters timeouts.
    
    Args:
        owner: Repository owner
        repo: Repository name
        github_token: GitHub API token
        max_retries: Maximum number of retry attempts (default: 3)
        timeout: Request timeout in seconds (default: 60)
    
    Returns:
        Dictionary containing dependency data or empty structure on failure
    """
    graphql_url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Content-Type": "application/json",
    }
    
    # Use smaller page sizes to avoid timeouts - start with 50, can reduce further if needed
    dependency_page_size = 50  # Reduced from 100 to avoid timeouts on large manifests
    
    # Step 1: Get all manifest filenames first (lightweight query)
    manifest_filenames = []
    manifest_cursor = None
    has_more_manifests = True
    
    print(f"  Fetching manifest list for {owner}/{repo} (paginated approach)...")
    while has_more_manifests:
        manifest_list_query = """
        query($owner: String!, $repo: String!, $after: String, $first: Int!) {
            repository(owner: $owner, name: $repo) {
                dependencyGraphManifests(first: $first, after: $after) {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    nodes {
                        filename
                    }
                }
            }
        }
        """
        
        variables = {
            "owner": owner,
            "repo": repo,
            "first": 100,  # Can fetch many filenames at once
            "after": manifest_cursor
        }
        
        try:
            response = requests.post(
                graphql_url,
                headers=headers,
                json={"query": manifest_list_query, "variables": variables},
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                errors = data["errors"]
                is_timeout = any("timeout" in str(e.get("message", "")).lower() or "timedout" in str(e.get("message", "")).lower() for e in errors)
                is_retryable = is_timeout or any(
                    "502" in str(e.get("message", "")) or
                    "503" in str(e.get("message", "")) or
                    "504" in str(e.get("message", "")) or
                    "something went wrong" in str(e.get("message", "")).lower()
                    for e in errors
                )
                if is_retryable:
                    # Retry manifest list fetching with exponential backoff
                    for retry in range(3):
                        wait_time = (5 * (2 ** retry)) + random.uniform(0, 2)
                        print(f"  Error fetching manifest list (retry {retry + 1}/3). Waiting {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        try:
                            retry_response = requests.post(
                                graphql_url,
                                headers=headers,
                                json={"query": manifest_list_query, "variables": variables},
                                timeout=timeout
                            )
                            retry_response.raise_for_status()
                            retry_data = retry_response.json()
                            if "errors" not in retry_data:
                                data = retry_data
                                break
                        except Exception:
                            if retry == 2:
                                print(f"  Failed to fetch manifest list after 3 retries")
                                return {"timeout": True, "data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
                            continue
                    else:
                        print(f"  Failed to fetch manifest list after retries")
                        return {"timeout": True, "data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
                else:
                    print(f"Error fetching manifest list: {errors}")
                    return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
            
            manifests_data = data.get("data", {}).get("repository", {}).get("dependencyGraphManifests", {})
            page_info = manifests_data.get("pageInfo", {})
            has_more_manifests = page_info.get("hasNextPage", False)
            manifest_cursor = page_info.get("endCursor")
            
            for node in manifests_data.get("nodes", []):
                manifest_filenames.append(node.get("filename"))
                
        except requests.exceptions.Timeout:
            print(f"Timeout fetching manifest list for {owner}/{repo}")
            return {"timeout": True, "data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code >= 500:
                print(f"HTTP {e.response.status_code} error fetching manifest list for {owner}/{repo}")
                return {"timeout": True, "data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
            print(f"HTTP error fetching manifest list for {owner}/{repo}: {e}")
            return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
        except Exception as e:
            print(f"Error fetching manifest list for {owner}/{repo}: {e}")
            return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
    
    print(f"  Found {len(manifest_filenames)} manifests, fetching dependencies...")
    
    # Step 2: Fetch all manifests with first page of dependencies, storing cursor for each
    manifest_data_map = {}  # filename -> {all_deps, dep_cursor, has_more_deps, manifest_cursor}
    manifest_cursor = None
    has_more_manifests = True
    
    while has_more_manifests:
        query = """
        query($owner: String!, $repo: String!, $after: String, $first: Int!, $depFirst: Int!) {
            repository(owner: $owner, name: $repo) {
                dependencyGraphManifests(first: $first, after: $after) {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    nodes {
                        filename
                        dependencies(first: $depFirst) {
                            pageInfo {
                                hasNextPage
                                endCursor
                            }
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
            "repo": repo,
            "first": 5,  # Reduced from 10 to 5 to avoid timeouts
            "after": manifest_cursor,
            "depFirst": dependency_page_size
        }
        
        success = False
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    graphql_url,
                    headers=headers,
                    json={"query": query, "variables": variables},
                    timeout=timeout
                )
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data:
                    errors = data["errors"]
                    is_timeout = any(
                        "timeout" in str(e.get("message", "")).lower() 
                        or "timedout" in str(e.get("message", "")).lower()
                        for e in errors
                    )
                    
                    # Check for retryable errors (timeouts, 502-like errors, or transient GraphQL errors)
                    is_retryable = is_timeout or any(
                        "502" in str(e.get("message", "")) or
                        "503" in str(e.get("message", "")) or
                        "504" in str(e.get("message", "")) or
                        "something went wrong" in str(e.get("message", "")).lower()
                        for e in errors
                    )
                    
                    if is_retryable and attempt < max_retries:
                        wait_time = (10 * (2 ** attempt)) + random.uniform(0, 5)  # Longer waits
                        print(f"Timeout/error fetching manifests (attempt {attempt + 1}/{max_retries + 1}). Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        if is_timeout:
                            print(f"GraphQL timeout for {owner}/{repo} after {max_retries + 1} attempts.")
                            return {"timeout": True, "data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
                        print(f"GraphQL errors: {errors}")
                        # For non-retryable errors, still try to return partial data if we have any
                        if manifest_data_map:
                            print(f"  Returning partial data: {len(manifest_data_map)} manifests")
                        return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
                
                manifests_data = data.get("data", {}).get("repository", {}).get("dependencyGraphManifests", {})
                page_info = manifests_data.get("pageInfo", {})
                has_more_manifests = page_info.get("hasNextPage", False)
                
                # Store cursor BEFORE updating it
                current_page_cursor = manifest_cursor
                manifest_cursor = page_info.get("endCursor")
                
                for manifest_node in manifests_data.get("nodes", []):
                    filename = manifest_node.get("filename")
                    deps_data = manifest_node.get("dependencies", {})
                    dep_page_info = deps_data.get("pageInfo", {})
                    
                    manifest_data_map[filename] = {
                        "all_deps": deps_data.get("nodes", []),
                        "dep_cursor": dep_page_info.get("endCursor"),
                        "has_more_deps": dep_page_info.get("hasNextPage", False),
                        "manifest_cursor": current_page_cursor  # Cursor used to fetch this manifest
                    }
                
                success = True
                break
                
            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    wait_time = (10 * (2 ** attempt)) + random.uniform(0, 5)
                    print(f"Request timeout (attempt {attempt + 1}/{max_retries + 1}). Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    return {"timeout": True, "data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
            except requests.exceptions.HTTPError as e:
                # Retry on 5xx errors
                if e.response and e.response.status_code >= 500 and attempt < max_retries:
                    wait_time = (10 * (2 ** attempt)) + random.uniform(0, 5)
                    print(f"HTTP {e.response.status_code} error (attempt {attempt + 1}/{max_retries + 1}). Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"HTTP error: {e}")
                    return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
            except Exception as e:
                if attempt < max_retries:
                    wait_time = (5 * (2 ** attempt)) + random.uniform(0, 3)
                    print(f"Error (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Error: {e}")
                    return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
        
        if not success:
            return {"data": {"repository": {"dependencyGraphManifests": {"nodes": []}}}}
        
        if has_more_manifests:
            time.sleep(0.5)  # Longer delay between manifest pages
    
    # Step 3: Paginate remaining dependencies for manifests that need it
    for filename, manifest_info in manifest_data_map.items():
        if not manifest_info["has_more_deps"]:
            continue
        
        dep_cursor = manifest_info["dep_cursor"]
        has_more_deps = True
        current_manifest_cursor = manifest_info["manifest_cursor"]
        
        initial_count = len(manifest_info["all_deps"])
        if has_more_deps:
            print(f"  {filename}: {initial_count} deps (first page), paginating...")
        
        while has_more_deps:
            # Fetch all manifests and find the one we need by filename
            # This is more reliable than trying to use cursors
            dep_query = """
            query($owner: String!, $repo: String!, $depAfter: String, $depFirst: Int!) {
                repository(owner: $owner, name: $repo) {
                    dependencyGraphManifests(first: 50) {
                        nodes {
                            filename
                            dependencies(first: $depFirst, after: $depAfter) {
                                pageInfo {
                                    hasNextPage
                                    endCursor
                                }
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
            
            dep_variables = {
                "owner": owner,
                "repo": repo,
                "depFirst": dependency_page_size,
                "depAfter": dep_cursor
            }
            
            dep_success = False
            for dep_attempt in range(max_retries + 1):
                try:
                    dep_response = requests.post(
                        graphql_url,
                        headers=headers,
                        json={"query": dep_query, "variables": dep_variables},
                        timeout=timeout
                    )
                    dep_response.raise_for_status()
                    dep_data = dep_response.json()
                    
                    if "errors" in dep_data:
                        dep_errors = dep_data["errors"]
                        is_timeout = any(
                            "timeout" in str(e.get("message", "")).lower() 
                            or "timedout" in str(e.get("message", "")).lower()
                            for e in dep_errors
                        )
                        
                        # Check for retryable errors
                        is_retryable = is_timeout or any(
                            "502" in str(e.get("message", "")) or
                            "503" in str(e.get("message", "")) or
                            "504" in str(e.get("message", "")) or
                            "something went wrong" in str(e.get("message", "")).lower()
                            for e in dep_errors
                        )
                        
                        if is_retryable and dep_attempt < max_retries:
                            wait_time = (10 * (2 ** dep_attempt)) + random.uniform(0, 5)
                            print(f"    Timeout/error for {filename} dependencies (attempt {dep_attempt + 1}/{max_retries + 1}). Retrying in {wait_time:.1f}s...")
                            time.sleep(wait_time)
                            continue
                        else:
                            if is_timeout:
                                print(f"    Timeout for {filename} after {max_retries + 1} attempts. Got {len(manifest_info['all_deps'])} deps so far.")
                                has_more_deps = False
                                break
                            print(f"    GraphQL errors for {filename}: {dep_errors}")
                            has_more_deps = False
                            break
                    
                    dep_manifests = dep_data.get("data", {}).get("repository", {}).get("dependencyGraphManifests", {}).get("nodes", [])
                    found_manifest = None
                    for m in dep_manifests:
                        if m.get("filename") == filename:
                            found_manifest = m
                            break
                    
                    if found_manifest:
                        dep_data_node = found_manifest.get("dependencies", {})
                        new_deps = dep_data_node.get("nodes", [])
                        manifest_info["all_deps"].extend(new_deps)
                        dep_page_info = dep_data_node.get("pageInfo", {})
                        has_more_deps = dep_page_info.get("hasNextPage", False)
                        dep_cursor = dep_page_info.get("endCursor")
                        dep_success = True
                        if has_more_deps:
                            print(f"    {filename}: +{len(new_deps)} deps (total: {len(manifest_info['all_deps'])}), more pages...")
                        break
                    else:
                        # If we can't find the manifest, try fetching all manifests and searching
                        # This is a fallback - the cursor might not be working correctly
                        print(f"    Warning: Could not find {filename} with cursor. Trying to find it in all manifests...")
                        # Search through all returned manifests
                        for m in dep_manifests:
                            if m.get("filename") == filename:
                                found_manifest = m
                                break
                        
                        if found_manifest:
                            dep_data_node = found_manifest.get("dependencies", {})
                            new_deps = dep_data_node.get("nodes", [])
                            manifest_info["all_deps"].extend(new_deps)
                            dep_page_info = dep_data_node.get("pageInfo", {})
                            has_more_deps = dep_page_info.get("hasNextPage", False)
                            dep_cursor = dep_page_info.get("endCursor")
                            dep_success = True
                            break
                        else:
                            print(f"    Could not find {filename} even in all manifests. Got {len(manifest_info['all_deps'])} deps so far.")
                            has_more_deps = False
                            break
                            
                except requests.exceptions.Timeout:
                    if dep_attempt < max_retries:
                        wait_time = (10 * (2 ** dep_attempt)) + random.uniform(0, 5)
                        print(f"    Request timeout (attempt {dep_attempt + 1}/{max_retries + 1}). Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"    Request timeout for {filename} dependencies after {max_retries + 1} attempts.")
                        has_more_deps = False
                        break
                except requests.exceptions.HTTPError as e:
                    # Retry on 5xx errors
                    if e.response and e.response.status_code >= 500 and dep_attempt < max_retries:
                        wait_time = (10 * (2 ** dep_attempt)) + random.uniform(0, 5)
                        print(f"    HTTP {e.response.status_code} error (attempt {dep_attempt + 1}/{max_retries + 1}). Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"    HTTP error for {filename}: {e}")
                        has_more_deps = False
                        break
                except Exception as e:
                    if dep_attempt < max_retries:
                        wait_time = (5 * (2 ** dep_attempt)) + random.uniform(0, 3)
                        print(f"    Error (attempt {dep_attempt + 1}/{max_retries + 1}): {e}. Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"    Error fetching dependencies for {filename}: {e}")
                        has_more_deps = False
                        break
            
            if not dep_success:
                break
            
            if has_more_deps:
                time.sleep(0.5)  # Longer delay between dependency pages
        
        if len(manifest_info["all_deps"]) > initial_count:
            print(f"  {filename}: Complete! {initial_count} + {len(manifest_info['all_deps']) - initial_count} = {len(manifest_info['all_deps'])} total deps")
    
    # Build final manifest list
    all_manifests = []
    for filename, manifest_info in manifest_data_map.items():
        all_manifests.append({
            "filename": filename,
            "dependencies": {
                "nodes": manifest_info["all_deps"]
            }
        })
    
    # Format the response to match the expected structure
    total_deps = sum(len(m.get("dependencies", {}).get("nodes", [])) for m in all_manifests)
    if all_manifests:
        print(f"Found {len(all_manifests)} manifests with {total_deps} total dependencies for {owner}/{repo}")
    
    return {"data": {"repository": {"dependencyGraphManifests": {"nodes": all_manifests}}}}

def fetch_github_dependencies(owner: str, repo: str, github_token: str) -> Dict:
    """
    Fetch repository dependencies using GitHub's GraphQL API with automatic fallback.
    
    First tries the simple approach (faster for most repos). If a timeout is encountered,
    automatically falls back to the paginated approach for handling large dependency graphs.
    
    Args:
        owner: Repository owner
        repo: Repository name
        github_token: GitHub API token
    
    Returns:
        Dictionary containing dependency data or empty structure on failure
    """
    # Try simple approach first
    result = fetch_github_dependencies_simple(owner, repo, github_token)
    
    # If timeout detected, fall back to paginated approach
    if result.get("timeout"):
        print(f"  Falling back to paginated approach for {owner}/{repo}...")
        result = fetch_github_dependencies_paginated(owner, repo, github_token)
    
    return result

def fetch_all_dependencies_from_github(repo_list: List[str], output_file: str = "data/dependencies.csv") -> pd.DataFrame:
    """
    Fetch dependencies for all seed repositories from GitHub API and save to normalized CSV file.
    
    This function is idempotent and resumable:
    - Writes each successful repo immediately to the CSV
    - Skips repos that have already been processed
    - Can resume from where it left off if interrupted
    - Uses sidecar .processed file to track repos even when they have no dependencies
    
    Returns:
        DataFrame with normalized dependency data (one row per dependency)
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    
    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Track processed repositories in a sidecar file so we can resume even when a repo has no deps
    processed_path = output_path.with_suffix(output_path.suffix + ".processed")

    # Load existing data to determine which repos have already been processed
    processed_repos: set[str] = set()

    # Sidecar file: one repo_name per line
    if processed_path.exists():
        try:
            with processed_path.open("r") as f:
                processed_repos |= {line.strip() for line in f if line.strip()}
        except Exception as e:
            print(f"Warning: Could not read processed repos file: {e}. Rebuilding from CSV only.")

    file_exists = output_path.exists()

    if file_exists:
        try:
            existing_df = pd.read_csv(output_path, quoting=1)  # quoting=1 means QUOTE_ALL
            if not existing_df.empty and 'repo_name' in existing_df.columns:
                processed_repos |= set(existing_df['repo_name'].unique())
                print(f"Found existing data: {len(processed_repos)} repos already processed, {len(existing_df)} dependency records")
        except Exception as e:
            print(f"Warning: Could not read existing CSV: {e}. Starting fresh.")
            file_exists = False
            processed_repos = set()
    
    # Filter out repos that have already been processed
    repos_to_process = [repo for repo in repo_list if repo not in processed_repos]
    
    if not repos_to_process:
        print("All repositories have already been processed!")
        if file_exists:
            return pd.read_csv(output_path, quoting=1)  # quoting=1 means QUOTE_ALL
        return pd.DataFrame()
    
    print(f"Processing {len(repos_to_process)} new repositories (skipping {len(processed_repos)} already processed)")
    
    # Process each repo and write immediately
    for repo_name in tqdm(repos_to_process, desc="Fetching dependencies"):
        try:
            # Split owner/repo format
            parts = repo_name.split("/")
            if len(parts) != 2:
                print(f"Skipping invalid repo format: {repo_name}")
                continue

            owner, repo = parts[0], parts[1]

            # Small delay between requests to avoid rate limiting
            time.sleep(1.0)  # Increased from 0.5 to 1.0 to reduce rate limiting

            # Fetch dependencies (with automatic fallback)
            deps_data = fetch_github_dependencies(owner, repo, github_token)

            # Check if this was a timeout - try local parsing as fallback
            if deps_data.get("timeout"):
                if LOCAL_PARSER_AVAILABLE:
                    print(f"  ⏸ API timeout for {repo_name} - trying local parsing fallback...")
                    try:
                        local_records = fetch_dependencies_locally(owner, repo)
                        if local_records:
                            # Write local records
                            repo_df = pd.DataFrame(local_records)
                            repo_df.to_csv(output_path, mode='a', header=not file_exists, index=False, quoting=1)
                            file_exists = True
                            print(f"  ✓ Saved {len(local_records)} dependencies from local parsing for {repo_name}")
                            
                            # Mark as processed
                            try:
                                with processed_path.open("a") as f:
                                    f.write(repo_name + "\n")
                            except Exception as e:
                                print(f"Warning: Failed to update processed repos file for {repo_name}: {e}")
                            continue
                        else:
                            print(f"  ✗ Local parsing found no dependencies for {repo_name}")
                    except Exception as e:
                        print(f"  ✗ Local parsing failed for {repo_name}: {e}")
                
                print(f"  ⏸ Skipping {repo_name} due to timeout - will retry on next run")
                continue

            # Extract dependency data and normalize
            manifests = deps_data.get("data", {}).get("repository", {}).get("dependencyGraphManifests", {}).get("nodes", [])

            # Flatten: one row per dependency
            repo_records = []
            for manifest in manifests:
                manifest_filename = manifest.get("filename", "")
                manifest_deps = manifest.get("dependencies", {}).get("nodes", [])

                for dep in manifest_deps:
                    # Create normalized record
                    record = {
                        "repo_name": repo_name,
                        "owner": owner,
                        "repo": repo,
                        "manifest_filename": manifest_filename,
                        "package_name": dep.get("packageName", ""),
                        "package_manager": dep.get("packageManager", ""),
                        "package_url": dep.get("packageUrl", ""),
                        "requirements": dep.get("requirements", ""),
                        "relationship": dep.get("relationship", ""),
                        "has_dependencies": dep.get("hasDependencies", False)
                    }
                    repo_records.append(record)

            # Write this repo's dependencies immediately (append mode)
            # Only write if we have data OR confirmed no dependencies (not timeout)
            repo_df = pd.DataFrame(repo_records)
            # Append to CSV with proper escaping (write header only if file doesn't exist)
            repo_df.to_csv(output_path, mode='a', header=not file_exists, index=False, quoting=1)  # quoting=1 means QUOTE_ALL
            file_exists = True  # After first write, header is written

            if repo_records:
                print(f"  ✓ Saved {len(repo_records)} dependencies for {repo_name}")
            else:
                # Mark as processed even if no dependencies found (confirmed no deps, not timeout)
                print(f"  ✓ No dependencies found for {repo_name} (marked as processed)")

            # Record this repo as processed so we don't re-fetch it on the next run
            try:
                with processed_path.open("a") as f:
                    f.write(repo_name + "\n")
            except Exception as e:
                print(f"Warning: Failed to update processed repos file for {repo_name}: {e}")

        except Exception as e:
            print(f"Error processing {repo_name}: {str(e)}")
            continue
    
    # Load and return the complete dataset
    if output_path.exists():
        try:
            final_df = pd.read_csv(output_path, quoting=1)  # quoting=1 means QUOTE_ALL
            print(f"\nTotal dependency records: {len(final_df)}")
            print(f"Total repositories processed: {final_df['repo_name'].nunique()}")
            if len(final_df) > 0:
                print(f"Unique packages: {final_df['package_name'].nunique()}")
                print(f"Package manager distribution:\n{final_df['package_manager'].value_counts()}")
            return final_df
        except Exception as e:
            print(f"\nWarning: Error reading CSV file: {e}")
            print("The CSV file may be corrupted. You may need to delete it and re-run.")
            return pd.DataFrame()
    
    return pd.DataFrame()


if __name__ == "__main__":
    # Get seed repositories from CSV
    seed_repos = get_seed_repos()
    print(f"Found {len(seed_repos)} seed repositories")
    
    # Fetch dependencies from GitHub API
    fetch_all_dependencies_from_github(seed_repos)

