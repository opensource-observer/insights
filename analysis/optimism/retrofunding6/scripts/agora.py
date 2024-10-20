from dotenv import load_dotenv
import json
import os
import pandas as pd
import requests


CURRENT_DIR = os.path.dirname(__file__)
LOCALDATA_DIR = os.path.join(CURRENT_DIR, '../data/_local/')
APPLICATIONS_PATH = os.path.join(LOCALDATA_DIR, 'applications.json')

load_dotenv()
AGORA_API_KEY = os.environ['AGORA_API_KEY']


def agora_api(endpoint, params=None):
    url = f'https://vote.optimism.io/api/v1/{endpoint}'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {AGORA_API_KEY}'
    }
    agora_data = []
    
    has_params = params is not None
    if not has_params:
        offset = 0
        limit = 100
        params = {'limit': limit, 'offset': offset}

    while True:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            json_data = response.json()
            new_data = json_data.get('data', [])
            agora_data.extend(new_data)
            
            if has_params or len(new_data) < limit:
                break
            
            params['offset'] += limit
            print(f"Fetched {len(new_data)} items, offset now at {params['offset']}")
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)
            break

    print(f"Fetched a total of {len(agora_data)} items from {endpoint}.")
    return agora_data

def fetch_delegates():
    url = 'https://vote.optimism.io/api/v1/delegates'
    params = {'limit': 100, 'offset': 0, 'sort': 'most_delegators'}
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {AGORA_API_KEY}'
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        agora_data = response.json()
    else:
        print(f"Request failed with status code: {response.status_code}")
        print(response.text)
    return agora_data


def load_json(json_path):
    with open(json_path, "r") as f:
        records = json.load(f)
    return records


def json_to_parquet(json_dict, outpath):
    dataframe = pd.DataFrame(json_dict)
    dataframe.to_parquet(outpath)
    print(f"Exported {len(dataframe)} rows to: {outpath}.")


def parse_applications(apps):
    data = {'projects': [], 'impactStatements': []}
    for app in apps:
        attestationId = app['attestationId']
        data['projects'].append({'attestationId': attestationId, **app['project']})
        for statement in app['impactStatementAnswer']:
            data['impactStatements'].append({'attestationId': attestationId, **statement})
    return data


def main():
    apps = load_json(APPLICATIONS_PATH)
    data = parse_applications(apps)
    for dataset_name, dataset in data.items():
        outpath = os.path.join(LOCALDATA_DIR, f"{dataset_name}.parquet")
        json_to_parquet(dataset, outpath)


if __name__ == "__main__":
    main()
    