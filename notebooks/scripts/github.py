from dotenv import load_dotenv
import os
import requests


def is_fork(repo_path):

    load_dotenv()
    token = os.getenv("GITHUB_API_KEY")
    owner, repo_name = repo_path.split('/')

    url = "https://api.github.com/graphql"
    query = """
        query IsRepoFork($owner: String!, $repoName: String!) {
            repository(owner: $owner, name: $repoName) {
                isFork
            }
        }
    """
    variables = {
        "owner": owner,
        "repoName": repo_name
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        try:
            is_fork = data["data"]["repository"]["isFork"]
            return is_fork
        except:
            print("Error:", repo_path)
            print(data)
    else:
        print("Error:", response.status_code)
        print(response.text)



def get_license(repo_path):

    load_dotenv()
    token = os.getenv("GITHUB_API_KEY")
    owner, repo_name = repo_path.split('/')

    url = "https://api.github.com/graphql"
    query = """
        query getLicense($owner: String!, $repoName: String!) {
        repository(owner: $owner, name: $repoName) {
            licenseInfo {
            spdxId,
            url
            }
        }
        }
    """
    variables = {
        "owner": owner,
        "repoName": repo_name
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        try:
            license_info = data["data"]["repository"]["licenseInfo"]
            if license_info:
                license = license_info.get("spdxId", None)
                return license
            return None
        except Exception as e:
            print("Error:", repo_path)
            print(e)
            print(data)
    else:
        print("Error:", response.status_code)
        print(response.text)        
