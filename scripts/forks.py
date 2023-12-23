import json
import os
import pandas as pd
from github import is_fork


repo_data = pd.read_csv("notebooks/data/2023-10-15_repo_stats.csv")

if not os.path.exists("notebooks/data/2023-10-15_forks.json"):
    json_data = {
        repo: "unknown"
        for repo in repo_data["artifact_name"]
    }
    with open("notebooks/data/2023-10-15_forks.json", "w") as f:
        json.dump(json_data, f, indent=4)
    
else:
    with open("notebooks/data/2023-10-15_forks.json", "r") as f:
        json_data = json.load(f)


for repo, status in json_data.items():
    if status == "unknown":
        print(repo)
        result = is_fork(repo)
        if result is None:
            break
        json_data[repo] = result

with open("notebooks/data/2023-10-15_forks.json", "w") as f:
    json.dump(json_data, f, indent=4)    
