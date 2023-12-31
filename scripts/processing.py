from itertools import combinations
import pandas as pd
import warnings
warnings.filterwarnings('ignore')


BOTS = ['web-flow', 'dependabot', 'gitbook-bot', 'dependabot-support', 'snyk-bot', 'github-actions[bot]', 'github-actions', 'upptime-bot',        
        'dependabot-preview', 'metamaskbot', 'semantic-release-bot', 'beefybot', 'hop-protocol-bot', 'mergify[bot]', 'action-bot@github.com', 
        'renovate-bot', 'uploaderbot@pokt.network', 'snyk-bot-wld', 'cache-bot@aave.com', 'credbot', 'nbc-bump-bot', 'crowdin-bot',
        'greenkeeper[bot]', 'cache-bot@bgd.com', 'axelar-cicd-bot', 'bot@worldcoin.org', 'traviscibot']

def github_event_processor(result, forks=[]):
    df = pd.DataFrame(result[1:], columns=result[0])
    
    # Remove contributions from forked repos
    df = df[~df['artifact_name'].isin(forks)]
    
    # Create a dictionary mapping PR event_time to contributor_name
    pr_merged_mapping = df[df['event_type'] == 'PULL_REQUEST_MERGED'].set_index('event_time')[['artifact_name', 'contributor_name']].to_dict()

    # Update web_flow_commits based on matching PRs
    web_flow_commits = df[(df['event_type'] == 'COMMIT_CODE') & (df['contributor_name'] == 'web-flow')]
    web_flow_commits['contributor_name'] = web_flow_commits.apply(
        lambda row: pr_merged_mapping.get(row['event_time'], {}).get('contributor_name', row['contributor_name']), axis=1
    )
    
    # Remove contributions from bots
    df = df[~df['contributor_name'].isin(BOTS)]

    # Transform dates
    df['date'] = df['event_time'].apply(lambda x: x.date())
    df['month'] = pd.PeriodIndex(df.event_time, freq='M')
    df['quarter'] = pd.PeriodIndex(df.event_time, freq='Q')
    
    df.rename(columns={'artifact_name': 'github_repo'}, inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def github_active_developers(dataframe, freq='month', min_ratio=0.3, event_filters=None, min_days=10):

    denoms = {
        'day': 1,
        'week': 7,
        'month': 30,
        'quarter': 90,
        'year': 365
    }

    if event_filters:
        df = dataframe[dataframe['event_type'].isin(event_filters)]
    else:
        df = dataframe

    pivot_table = df.pivot_table(index='contributor_name', columns=freq, values='date', aggfunc='nunique', fill_value=0)    
    pivot_table = pivot_table[pivot_table.sum(axis=1) >= min_days]
    pivot_table = pivot_table / denoms[freq]

    devs = pd.DataFrame(index=['full-time', 'part-time', 'inactive'], columns=pivot_table.columns)
    devs.loc['full-time'] = (pivot_table >= min_ratio).sum()
    devs.loc['part-time'] = ((pivot_table < min_ratio) & (pivot_table > 0)).sum()    

    for column in pivot_table.columns:
        before_specified_column = pivot_table.loc[:, :column].sum(axis=1) > 0
        current_devs = devs.loc[:,column].sum()
        devs.loc['inactive', column] = before_specified_column.sum() - current_devs
        
    return devs


def github_repos_analysis(dataframe, repo_col='github_repo', date_col='date', groupers = ['project_slug', 'project_name']):

    df = dataframe.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    repo_stats = df.groupby(groupers).agg(
        num_repos=pd.NamedAgg(column=repo_col, aggfunc='nunique'),
        first_date=pd.NamedAgg(column=date_col, aggfunc='min'),
        last_date=pd.NamedAgg(column=date_col, aggfunc='max')
    ).join(
        df[df['event_type']=='STARRED'].groupby(groupers).agg(
            stars_count=pd.NamedAgg(column='contributor_name', aggfunc='nunique')
        )
    )

    end_date = df[date_col].max()
    repo_stats['days_since_first_commit'] = (end_date - repo_stats['first_date']).apply(lambda x: x.days)
    repo_stats['days_since_last_commit'] = (end_date - repo_stats['last_date']).apply(lambda x: x.days)

    repo_stats['last_commit_category'] = pd.cut(
        repo_stats['days_since_last_commit'],
        bins=[-float('inf'), 30, 90, float('inf')],
        labels=['active', 'dormant', 'inactive'],
        right=False
    )

    repo_stats['stars_category'] = pd.cut(
        repo_stats['stars_count'],
        bins=[-float('inf'), 10, 1000, float('inf')],
        labels=['less popular', 'more popular', 'very popular'],
        right=False
    )

    repo_stats['project_age'] = pd.cut(
        repo_stats['days_since_first_commit'],
        bins=[-float('inf'), 365*2, 365*4, float('inf')],
        labels=['< 2 years', '2-4 years old', '> 4 years old'],
        right=False
    )

    return repo_stats


def github_network_graph(dataframe, contributor_col='contributor_name', project_col='project_name'):

    contribs_projects = dataframe.groupby(contributor_col)[project_col].apply(lambda x: [p for p,c in x.value_counts().items() if c>1]).to_dict()
    contribs_projects = {c:ps for c,ps in contribs_projects.items() if len(ps)>1}
    contribs_projects = {c: list(combinations(ps,2)) for c,ps in contribs_projects.items() if len(ps)>1}

    nodes = list(dataframe[project_col].unique())
    edges = [edge for combo in contribs_projects.values() for edge in combo]

    return nodes, edges
