import pandas as pd


def build_project_metrics_dataset(df):
    
    website_mapping = {
        'github': 'GitHub',
        'npmjs': 'Package Manager',
        'pypistats': 'Package Manager',
        'opensea': 'NFT Marketplace',
        'sound': 'NFT Marketplace',
        'zora': 'NFT Marketplace',
        'optimism': 'Gov Forum',
        'discord': 'Group Chat',
        'telegram': 'Group Chat',
        'notion': 'Document',
        'google': 'Document',
        'twitter': 'Twitter',
        'etherscan': 'Etherscan',
        'dune': 'Dune Dashboard',
        'youtube': 'YouTube',
        'substack': 'Blog',
        'mirror': 'Blog',
        'medium': 'Blog'
    }

    filtered_df = df[(df['attestationType'] == 'impactMetric') & df['number'].notnull() & df['urlType'].notnull()].copy()
    filtered_df['urlType'] = filtered_df['urlType'].map(website_mapping)
    project_cols = ['name', 'applicationMetadataPtr', 'bio or description', 'applicantType', 'impactCategory(ies)']
    cols = project_cols + ['urlType', 'number', 'attestationDescription']
    filtered_df = filtered_df[cols].dropna()
    filtered_df['metric'] = filtered_df.apply(lambda x: f"{x['urlType']}: {x['number']} {x['attestationDescription']}", axis=1)
    grouped_df = filtered_df.groupby(project_cols)['metric'].apply(lambda x: ", ".join(list(x))).reset_index()
    grouped_df['summary'] = grouped_df.apply(lambda x: f"a {x['applicantType']} that {x['bio or description']}. Impact metrics include: {x['metric']}", axis=1)

    return grouped_df


def main():
    datapath = 'notebooks/data/2023-10-07_indexed_attestations.csv'
    df = pd.read_csv(datapath)
    grouped_df = build_project_metrics_dataset(df)
    grouped_df.to_csv(datapath.replace("indexed_attestations.csv", "project_impact_metrics.csv"), index=False)


if __name__ == "__main__":
    main()
