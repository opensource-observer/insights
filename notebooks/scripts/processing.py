import pandas as pd
import warnings
warnings.filterwarnings('ignore')


BOTS = ['web-flow', 'dependabot', 'gitbook-bot', 'dependabot-support', 'snyk-bot', 'github-actions[bot]']


def github_event_processor(result, forks=[]):

    df = pd.DataFrame(result[1:], columns=result[0])
    
    # remove contributions from forked repos
    df = df[(~df['artifact_name'].isin(forks))]

    # handle commits merged by web-flow
    pr_merged_mapping = df[df['event_type'] == 'PULL_REQUEST_MERGED'].set_index('event_time')['contributor_name'].to_dict()
    web_flow_commits = df[(df['event_type'] == 'COMMIT_CODE') & (df['contributor_name'] == 'web-flow')]
    web_flow_commits['contributor_name'] = web_flow_commits['event_time'].map(pr_merged_mapping).fillna(web_flow_commits['contributor_name'])
    df.update(web_flow_commits)

    # remove contributions from bots
    df = df[~df['contributor_name'].isin(BOTS)]

    # transform dates
    df['date'] = df['event_time'].apply(lambda x: x.date())
    df['month'] = pd.PeriodIndex(df.event_time, freq='M')
    df['quarter'] = pd.PeriodIndex(df.event_time, freq='Q')
    
    df.rename(columns={'artifact_name': 'github_repo'}, inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df