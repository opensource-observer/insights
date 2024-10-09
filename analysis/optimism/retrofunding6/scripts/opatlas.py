import json
import os
import pandas as pd


CURRENT_DIR = os.path.dirname(__file__)
LOCALDATA_DIR = os.path.join(CURRENT_DIR, '../data/_local/')
APPLICATIONS_PATH = os.path.join(LOCALDATA_DIR, 'applications.json')


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
    