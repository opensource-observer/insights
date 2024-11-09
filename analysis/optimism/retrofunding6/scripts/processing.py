import json
import pandas as pd

from scripts.projects import process_projects
from scripts.voters import process_voters, process_voter_survey


CLEAN_VOTING_DATA_PATH = 'clean_voting_data.json'
NORMALIZED_VOTING_DATA_PATH = 'normalized_voting_data.csv'
VOTERS_DATA_PATH = 'voters.csv'
PROJECTS_DATA_PATH = 'projects.csv'

def set_categories(categories_path):
    project_categories = json.load(open(categories_path))
    return project_categories


def load_datasets(input_dir):
    with open(f'{input_dir}/{CLEAN_VOTING_DATA_PATH}') as f:
        clean_voting_data = json.load(f)
    with open(f'{input_dir}/{NORMALIZED_VOTING_DATA_PATH}') as f:
        normalized_voting_data = pd.read_csv(f)
    voters_dataframe = pd.read_csv(f'{input_dir}/{VOTERS_DATA_PATH}', index_col=0)
    projects_dataframe = pd.read_csv(f'{input_dir}/{PROJECTS_DATA_PATH}', index_col=0)
    return clean_voting_data, normalized_voting_data, voters_dataframe, projects_dataframe


def process_datasets(
    ballots_csv_path,
    voters_csv_path,
    projects_csv_path,
    output_dir
):
    
    projects_dataframe = process_projects(projects_csv_path)
    project_categories = projects_dataframe.reset_index().groupby('category')['project_id'].apply(list).to_dict()
    projects_dataframe.to_csv(f'{output_dir}/{PROJECTS_DATA_PATH}')

    clean_voting_data = process_csv_ballots(ballots_csv_path, project_categories)
    with open(f'{output_dir}/{CLEAN_VOTING_DATA_PATH}', 'w') as f:
        json.dump(clean_voting_data, f, indent=2)

    normalized_voting_data = normalize_ballots(clean_voting_data)
    normalized_voting_dataframe = pd.DataFrame(normalized_voting_data)
    normalized_voting_dataframe.to_csv(f'{output_dir}/{NORMALIZED_VOTING_DATA_PATH}', index=False)
    
    voters_dataframe = process_voters(voters_csv_path)
    print(f"Voters dataframe length: {len(voters_dataframe)}")

    actual_voters = normalized_voting_dataframe['voter_address'].unique()
    print(f"Actual voters length: {len(actual_voters)}")

    voters_dataframe = voters_dataframe[voters_dataframe.index.isin(actual_voters)]
    print(f"Voters dataframe length after filtering: {len(voters_dataframe)}")

    voters_dataframe.to_csv(f'{output_dir}/{VOTERS_DATA_PATH}')

    print("Processing complete.")


def process_csv_ballots(csv_path, project_categories):

    raw_voting_data = pd.read_csv(csv_path)

    processed_voting_data = []
    for _, row in raw_voting_data.iterrows():
        if row['Status'] != 'SUBMITTED' and not row['Badgeholder']:
            continue
        if not isinstance(row['Payload'], str):
            continue

        payload = json.loads(row['Payload'])
        projects_payload = payload['project_allocations']
        
        addr = row['Address'].lower()
        ballot_projects = []
        for votes in projects_payload:
            project_id = list(votes.keys())[0]
            ballot_projects.append(project_id)
        for cat, proj_list in project_categories.items():
            if set(ballot_projects).intersection(proj_list):
                payload.update({'voter_address': addr, 'category_assignment': cat})
                break
        processed_voting_data.append(payload)
    
    return processed_voting_data


def normalize_ballots(processed_voting_data):

    normalized_data = []
    for ballot in processed_voting_data:

        for cat_alloc in ballot['category_allocations']:
            category_name = list(cat_alloc.keys())[0]
            category_percentage = float(list(cat_alloc.values())[0]) / 100
            if category_name == ballot['category_assignment']:
                category_budget = category_percentage * ballot['budget']
                break
        
        for proj_alloc in ballot['project_allocations']:
            project_id = list(proj_alloc.keys())[0]
            project_vote = list(proj_alloc.values())[0]
            if pd.isnull(project_vote):
                project_percentage = None
                project_amount = None
            else:
                project_percentage = float(project_vote) / 100
                project_amount = project_percentage * category_budget
            normalized_data.append({
                'voter_address': ballot['voter_address'],
                'project_id': project_id,
                'project_percentage': project_percentage,
                'project_amount': project_amount
            })
    
    return normalized_data
