import pandas as pd


def shorten_name(name, max_len=32):
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


def process_projects(csv_path, project_categories):

    df_projects = pd.read_csv(csv_path)

    df_projects.columns = [c.lower().replace(' ','_') for c in df_projects.columns]
    df_projects.drop_duplicates(inplace=True)

    df_projects['project_id'] = df_projects['attestation_id'].str.lower()
    df_projects.drop(columns=['attestation_id'], inplace=True)
    
    df_projects['project_display_name'] = df_projects['project_name'].str.strip()
    df_projects['project_name'] = df_projects['project_name'].apply(shorten_name)

    project_categories_mapping = {}
    for c, plist in project_categories.items():
        for p in plist:
            project_categories_mapping.update({p:c})
    df_projects['project_category'] = df_projects['project_id'].map(project_categories_mapping)
    
    df_projects.set_index('project_id', inplace=True)
    df_projects.dropna(inplace=True)

    return df_projects