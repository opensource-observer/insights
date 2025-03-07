import csv
import dotenv
import os
import re
import json
from datetime import datetime
from githubkit import GitHub
from githubkit.exception import RequestFailed

dotenv.load_dotenv()
github = GitHub(os.getenv("GITHUB_API_KEY"))

def parse_repo_url(url):
    """Extracts the owner and repository name from a GitHub URL."""
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)', url)
    if match:
        return match.group(1), match.group(2).rstrip('.git')
    return None, None

def get_repo_metrics(owner, repo_name):
    """Get metrics for a specific repository."""
    try:
        # Check if repo exists and is accessible
        repo = github.rest.repos.get(owner=owner, repo=repo_name)
        is_fork = repo.parsed_data.fork
        fork_details = ""
        
        if is_fork:
            try:
                # Get parent repository info if it's a fork
                parent = repo.parsed_data.parent
                if parent:
                    fork_details = f"{parent.owner.login}/{parent.name}"
            except (AttributeError, TypeError):
                fork_details = "Unknown parent"
        
        try:
            # Get all commits
            commits = list(github.paginate(
                github.rest.repos.list_commits,
                owner=owner,
                repo=repo_name
            ))
            
            if not commits:
                return {
                    "is_available": True,
                    "is_fork": is_fork,
                    "fork_of": fork_details if is_fork else "",
                    "first_commit": None,
                    "last_commit": None,
                    "total_commits": 0,
                    "total_developers": 0
                }
            
            # Get unique developers
            developers = set()
            for commit in commits:
                try:
                    if commit.author and getattr(commit.author, 'login', None):
                        developers.add(commit.author.login)
                except (AttributeError, TypeError):
                    continue
            
            # Sort commits by date
            sorted_commits = sorted(
                commits,
                key=lambda x: datetime.strptime(x.commit.author.date, "%Y-%m-%dT%H:%M:%SZ")
            )
            
            return {
                "is_available": True,
                "is_fork": is_fork,
                "fork_of": fork_details if is_fork else "",
                "first_commit": sorted_commits[0].commit.author.date,
                "last_commit": sorted_commits[-1].commit.author.date,
                "total_commits": len(commits),
                "total_developers": len(developers)
            }
            
        except Exception as e:
            print(f"Error getting commit data for {owner}/{repo_name}: {str(e)}")
            return {
                "is_available": True,
                "is_fork": is_fork,
                "fork_of": fork_details if is_fork else "",
                "first_commit": None,
                "last_commit": None,
                "total_commits": 0,
                "total_developers": 0
            }
            
    except RequestFailed as e:
        if e.response.status_code == 404:
            return {
                "is_available": False,
                "is_fork": False,
                "fork_of": "",
                "first_commit": None,
                "last_commit": None,
                "total_commits": 0,
                "total_developers": 0
            }
        print(f"API error for {owner}/{repo_name}: {str(e)}")
        return {
            "is_available": False,
            "is_fork": False,
            "fork_of": "",
            "first_commit": None,
            "last_commit": None,
            "total_commits": 0,
            "total_developers": 0
        }

def load_progress(output_path):
    """Load previously processed results."""
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return {row['github_url']: row for row in reader}
        except Exception as e:
            print(f"Error loading progress: {str(e)}")
    return {}

def process_repos_from_csv(input_csv_path):
    """Process repositories from a CSV file and generate metrics."""
    output_path = input_csv_path.rsplit('.', 1)[0] + '_reviewed.csv'
    
    # Load existing progress
    processed_repos = load_progress(output_path)
    print(f"Loaded {len(processed_repos)} previously processed repositories")
    
    # Read input CSV
    repos = []
    with open(input_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            repos.append(row['github_url'])
    
    # Process each repo
    results = []
    total_repos = len(repos)
    
    for idx, repo_url in enumerate(repos, 1):
        # Skip if already processed
        if repo_url in processed_repos:
            print(f"[{idx}/{total_repos}] Skipping {repo_url} (already processed)")
            results.append(processed_repos[repo_url])
            continue
            
        owner, repo_name = parse_repo_url(repo_url)
        if not owner or not repo_name:
            print(f"[{idx}/{total_repos}] Could not parse repo URL: {repo_url}")
            continue
            
        print(f"[{idx}/{total_repos}] Processing repository: {owner}/{repo_name}")
        metrics = get_repo_metrics(owner, repo_name)
        
        result = {
            "github_url": repo_url,
            **metrics
        }
        results.append(result)
        
        # Save progress after each repo
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "github_url", "is_available", "is_fork", "fork_of",
                "first_commit", "last_commit", "total_commits", "total_developers"
            ])
            writer.writeheader()
            writer.writerows(results)
    
    print(f"\nProcessing complete! Results written to: {output_path}")
    print(f"Processed {len(results)} repositories")

if __name__ == "__main__":
    import sys
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "repos.csv"
    process_repos_from_csv(csv_path)
