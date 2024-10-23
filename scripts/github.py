from dotenv import load_dotenv
import os
import requests

# Global variables initialized once
load_dotenv()
TOKEN = os.getenv("GITHUB_API_KEY")
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
BASE_URL = 'https://api.github.com'
URL = "https://api.github.com/graphql"

def send_graphql_request(query, variables):
    response = requests.post(URL, json={"query": query, "variables": variables}, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.status_code)
        print(response.text)
        return None

def extract_repo_owner_and_name(repo_path):
    parts = repo_path.split('/')
    return parts[0], (parts[1] if len(parts) > 1 else None)

def is_fork(repo_path):
    owner, repo_name = extract_repo_owner_and_name(repo_path)
    query = """
        query IsRepoFork($owner: String!, $repoName: String!) {
            repository(owner: $owner, name: $repoName) {
                isFork
            }
        }
    """
    variables = {"owner": owner, "repoName": repo_name}
    data = send_graphql_request(query, variables)
    try:
        return data["data"]["repository"]["isFork"]
    except Exception as e:
        print("Error parsing data:", e, data)
        return None

def get_license(repo_path):
    owner, repo_name = extract_repo_owner_and_name(repo_path)
    query = """
        query GetLicense($owner: String!, $repoName: String!) {
            repository(owner: $owner, name: $repoName) {
                licenseInfo {
                    spdxId,
                    url
                }
            }
        }
    """
    variables = {"owner": owner, "repoName": repo_name}
    data = send_graphql_request(query, variables)
    try:
        license_info = data["data"]["repository"]["licenseInfo"]
        return license_info.get("spdxId") if license_info else None
    except Exception as e:
        print("Error parsing data:", e, data)
        return None

def get_owner_type(repo_path):
    owner, _ = extract_repo_owner_and_name(repo_path)
    query = """
        query GetOwnerType($owner: String!) {
            user(login: $owner) {
                __typename
            }
            organization(login: $owner) {
                __typename
            }
        }
    """
    variables = {"owner": owner}
    data = send_graphql_request(query, variables)
    try:
        if data["data"]["user"]:
            return "User"
        elif data["data"]["organization"]:
            return "Organization"
        return None
    except Exception as e:
        print("Error parsing data:", e, data)
        return None
    

def get_repos(organization):
    query = """
        query GetRepositories($owner: String!) {
            organization(login: $owner) {
                repositories(first: 10, privacy: PUBLIC, isFork: false, isArchived: false) {
                edges {
                    node {
                    name
                    stargazerCount
                    licenseInfo {
                        name
                    }
                    }
                }
                }
            }
        }
    """
    variables = {"owner": organization}
    data = send_graphql_request(query, variables)
    try:
        return data["data"]["organization"]["repositories"]["edges"]
    except Exception as e:
        print("Error parsing data:", e, data)
        return None


def get_commit_data(repo_path):
    owner, repo_name = extract_repo_owner_and_name(repo_path)
    query = """
        query GetCommitData($owner: String!, $repoName: String!) {
            repository(owner: $owner, name: $repoName) {
                defaultBranchRef {
                    target {
                        ... on Commit {
                            history(first: 100) {
                                edges {
                                    node {
                                        author {
                                            date
                                            email
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    """
    variables = {"owner": owner, "repoName": repo_name}
    data = send_graphql_request(query, variables)
    result = {
        "commits": 0,
        "authors": 0,
        "unique_days": 0,
        "newest_commit_date": None,
        "oldest_commit_date": None
    }
    try:
        edges = data["data"]["repository"]["defaultBranchRef"]["target"]["history"]["edges"]
        emails = set()
        dates = []
        for node in edges:
            author = node["node"]["author"]
            if author:
                result["commits"] += 1
                emails.add(author["email"])
                dates.append(author["date"].split("T")[0])
        result["authors"] = len(emails)
        result["unique_days"] = len(set(dates))
        result["newest_commit_date"] = dates[0] if dates else None
        result["oldest_commit_date"] = dates[-1] if dates else None
        return result
    except Exception as e:
        print("Error parsing data:", e, data)
        return None


def validate_repo(repo):
    commit_data = get_commit_data(repo)
    if not commit_data:
        return {
            "Approved": False,
            "Reason": "Repo no longer available."
        }
    if commit_data["commits"] < 10:
        return {
            "Approved": False,
            "Reason": "Repositories must have at least 10 commits."
        }
    elif commit_data["commits"] < 100 and commit_data["oldest_commit_date"] > "2024-03-01":
        print(commit_data)
        return {
            "Approved": False,
            "Reason": "Repositories must have a commit older than 2024-03-01."
        }
    if commit_data["newest_commit_date"] < "2024-03-01":
        return {
            "Approved": False,
            "Reason": "Repositories must have a commit newer than 2024-03-01."
        }
    if commit_data["unique_days"] < 5:
        return {
            "Approved": False,
            "Reason": "Repositories must have commits on at least 5 different days."
        }
    return {
        "Approved": True,
        "Reason": None
    }


def validate_github_artifact(artifact):    
    if "/" in artifact:
        if is_fork(artifact):
            return {
                "Approved": False,
                "Reason": "Repositories must not be forks."
            }
        return validate_repo(artifact)
    elif get_owner_type(artifact) == "Organization":
        repos = get_repos(artifact)
        for repo_data in repos:
            repo_name = repo_data["node"]["name"]
            repo_path = f"{artifact}/{repo_name}"
            result = validate_github_artifact(repo_path)
            if result["Approved"]:
                return result
        return {
            "Approved": False,
            "Reason": f"No valid repositories found (n={len(repos)})."
        }
    else:
        return {
            "Approved": False,
            "Reason": "No repo provided and owner is a User not an Organization."
        }



def get_contributors(owner, repo):
    url = f'{BASE_URL}/repos/{owner}/{repo}/contributors'
    headers = {'Authorization': f'token {TOKEN}'}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        contributors = response.json()
        return [(owner, repo, contributor['login'], contributor['contributions']) for contributor in contributors]
    else:
        print(f"Error: Unable to fetch contributors (Status Code: {response.status_code})")
        return []



if __name__ == "__main__":
    site = "opensource-observer"
    print(validate_github_artifact(site))
    #print(get_repos(site))
    #print(get_owner_type(site))
    #print(get_commit_data(site))
    #print(is_fork(site))
    #print(get_license(site))
