import pandas as pd


PAIRWISE_VOTER_LIST = [
    "0x839395e20bbB182fa440d08F850E6c7A8f6F0780", "0x56EdF679B0C80D528E17c5Ffe514dc9a1b254b9c", 
    "0x7899d9b1181cbB427b0b1BE0684C096C260F7474", "0x8Eb9e5E5375b72eE7c5cb786CE8564D854C26A86", 
    "0xe53e89d978Ff1da716f80BaA6E6D8B3FA23f2284", "0x00409fC839a2Ec2e6d12305423d37Cd011279C09", 
    "0x826976d7C600d45FB8287CA1d7c76FC8eb732030", "0x5C30F1273158318D3DC8FFCf991421f69fD3B77d", 
    "0x3DB5b38ef4b433D9C6A664Bd35551BE73313189A", "0xF68D2BfCecd7895BBa05a7451Dd09A1749026454", 
    "0xcf79C7EaEC5BDC1A9e32D099C5D6BdF67E4cF6e8", "0x3B60e31CFC48a9074CD5bEbb26C9EAa77650a43F", 
    "0x7fC80faD32Ec41fd5CfcC14EeE9C31953b6B4a8B", "0xdb5781a835b60110298fF7205D8ef9678Ff1f800", 
    "0x1F5D295778796a8b9f29600A585Ab73D452AcB1c", "0xAc469c5dF1CE6983fF925d00d1866Ab780D402A4", 
    "0x15C6AC4Cf1b5E49c44332Fb0a1043Ccab19db80a", "0x5d36a202687fD6Bd0f670545334bF0B4827Cc1E2", 
    "0x9C949881084dCbd97237f786710aB8e52a457136", "0x64FeD9e56B548343E7bb47c49ecd7FFa9f1A34FE"
]

def process_voters(csv_path):
    
    df_voters = pd.read_csv(csv_path)
    
    df_voters = df_voters.iloc[:,[6,8,10,11,13]]
    df_voters.columns = [c.lower().replace(' ','_') for c in df_voters.columns]
    
    df_voters['wallet'] = df_voters['wallet'].str.lower()
    df_voters.rename(columns={'wallet':'voter_address'}, inplace=True)

    df_voters['op_stack_category'] = df_voters['op_stack_category'].apply(lambda x: x.split(' - ')[1])
    df_voters['expertise_score'] = pd.to_numeric(df_voters['expertise_score'], errors='coerce')
    df_voters['is_expert'] = df_voters['expertise_group'] == 'Expert'
    df_voters['is_citizen'] = df_voters['voter_type'] == 'Citizen'

    df_voters['used_pairwise'] = df_voters['voter_address'].isin([x.lower() for x in PAIRWISE_VOTER_LIST])

    df_voters.set_index('voter_address', inplace=True, drop=True)

    return df_voters


def process_voter_survey(csv_path):

    df_surveys = pd.read_csv(csv_path)
    df_surveys = df_surveys.drop_duplicates(subset='Wallet Address', keep='last')
    df_surveys = df_surveys.iloc[:,[2,3,4,6,8,10]]
    df_surveys.columns = [
        'survey_hours_spent', 'survey_rate_voting_ux', 'survey_rate_worry_results',
        'survey_rate_confidence_results', 'survey_rate_funding_influence', 'voter_address'
    ]
    df_surveys['voter_address'] = df_surveys['voter_address'].str.lower()
    df_surveys.set_index('voter_address', inplace=True)

    return df_surveys

