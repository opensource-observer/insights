import pandas as pd
import re


def shorten_name(name, max_len=32):
    name = clean_text(name)
    name = name.split(': ')[0]
    name = name.split(' - ')[0]
    name = name.strip()
    if len(name) <= max_len:
        return name
    
    if ' ' not in name:
        return name[:max_len]
        
    while len(name) > max_len:
        name = " ".join(name.split(' ')[:-1])
    return name


def clean_text(text):
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s.,!?\'"()\-;:&@#*/\\]', '', text)
    return cleaned_text


def process_projects(csv_path):

    df_projects = pd.read_csv(csv_path, index_col=0)

    project_categories = df_projects.groupby('applicationCategory')['applicationId'].apply(list).to_dict()

    df_projects['project_id'] = df_projects['applicationId'].str.lower()
    df_projects.drop(columns=['applicationId'], inplace=True)
    df_projects.set_index('project_id', inplace=True)

    df_projects.rename(columns={'applicationCategory': 'category'}, inplace=True)
    
    df_projects['project_display_name'] = df_projects['name'].str.strip()
    df_projects['project_name'] = df_projects['name'].apply(shorten_name)

    return df_projects