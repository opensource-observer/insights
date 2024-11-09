import pandas as pd


PAIRWISE_VOTER_LIST = []

CATEGORY_MAP = {
    "A - Governance infrastructure & tooling": "GOVERNANCE_INFRA_AND_TOOLING",
    "A": "GOVERNANCE_INFRA_AND_TOOLING",
    "B - Governance Analytics": "GOVERNANCE_ANALYTICS",
    "B": "GOVERNANCE_ANALYTICS",
    "C - Governance Leadership": "GOVERNANCE_LEADERSHIP",
    "C": "GOVERNANCE_LEADERSHIP"
}


def process_voters(csv_path):
    
    df_voters = pd.read_csv(csv_path)

    df_voters.columns = [c.lower().replace(' ','_') for c in df_voters.columns]
    df_voters = df_voters[['wallet','voting_group','voter_type','farcaster_id','farcaster_username' ]]
    
    df_voters.rename(columns={'wallet':'voter_address'}, inplace=True)
    df_voters['voter_address'] = df_voters['voter_address'].str.lower()

    df_voters['category'] = df_voters['voting_group'].map(CATEGORY_MAP)
    df_voters['is_citizen'] = df_voters['voter_type'] == 'Citizen'

    df_voters['used_pairwise'] = df_voters['voter_address'].isin([x.lower() for x in PAIRWISE_VOTER_LIST])

    df_voters.set_index('voter_address', inplace=True, drop=True)

    return df_voters


def process_voter_survey(csv_path):

    df_surveys = pd.read_csv(csv_path)
    df_surveys = df_surveys.iloc[:,[1,3,4,5,7,9]]
    df_surveys.columns = [
        'voter_address', 'survey_hours_spent', 'survey_rate_voting_ux', 'survey_rate_worry_results',
        'survey_rate_confidence_results', 'survey_rate_funding_influence'
    ]
    df_surveys['voter_address'] = df_surveys['voter_address'].str.lower()
    df_surveys.set_index('voter_address', inplace=True)

    return df_surveys

