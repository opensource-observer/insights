import pandas as pd

TOTAL_FUNDING = 10_000_000
MAX_CAP = 500_000
MIN_CAP = 1000

PRIVATE_DIR = "data/private"
BALLOTS_CSV_PATH = f"{PRIVATE_DIR}/ballots final - export.csv"
DESTINATION_CSV_PATH = f"{PRIVATE_DIR}/rf4_results.csv"

# create the Impact Metrics Share dataframe
METRICS_CSV_PATH = "data/op_rf4_impact_metrics_by_project.csv"
DF_METRICS = pd.read_csv(METRICS_CSV_PATH, index_col=1)
METRIC_IDS = DF_METRICS.columns[-16:]
DF_METRICS[METRIC_IDS] = DF_METRICS[METRIC_IDS].div(DF_METRICS[METRIC_IDS].sum(axis=0), axis=1)


def score_projects(ballot):
    
    # get the OS multiplier for each project
    os_multiplier = DF_METRICS['is_oss'].apply(lambda x: ballot['os_multiplier'] if x else 1)
    metric_weights = ballot.drop('os_multiplier')
    
    # score each project
    scores = DF_METRICS[METRIC_IDS].multiply(metric_weights)
    raw_project_scores = scores.sum(axis=1)
    
    # apply the OS multiplier to each project's total score
    adjusted_project_scores = raw_project_scores * os_multiplier
    
    # return normalized scores
    return adjusted_project_scores / adjusted_project_scores.sum(axis=0)


def allocate_funding(project_scores, funding_available=TOTAL_FUNDING):

    allocations = {}

    # create a copy of projects so we can remove the ones above the cap
    remaining_projects = project_scores.copy()
    
    # iterate through the projects in descending order of score
    for project_id, score in project_scores.sort_values(ascending=False).items():
        
        # normalize and allocate the remaining funding
        alloc = score / remaining_projects.sum() * funding_available

        # cap the allocation and adjust the funding available
        if alloc >= MAX_CAP:
            del remaining_projects[project_id]
            allocations.update({project_id: MAX_CAP})
            funding_available -= MAX_CAP
        
        # allocate the funding with no cap
        else:
            allocations.update({project_id: alloc})

    return pd.Series(allocations)


def main():

    # load the ballots
    df_ballots_raw = (
        pd.read_csv(BALLOTS_CSV_PATH)
        .query("Badgeholder == True & Status == 'SUBMITTED'")
        .rename(columns={'Address': 'address', 'Os multiplier': 'os_multiplier'})
        .set_index('address')
    )

    # score the projects for each ballot
    parse_ballot = lambda x: pd.Series({k: v for d in eval(x) for k, v in d.items()})
    df_ballots = (
        pd.concat([
            df_ballots_raw['Ballot content'].apply(parse_ballot).fillna(0) / 100,
            df_ballots_raw['os_multiplier']
        ], axis=1)
    )
    df_scores = df_ballots.apply(score_projects, axis=1)

    # allocate funding for each badgeholder
    df_results = df_scores.apply(allocate_funding, axis=1).T

    # get the median funding for each project
    df_results['median'] = df_results.median(axis=1)

    # normalize and cap the funding again
    df_results['rf4_allocation'] = allocate_funding(df_results['median'])
    
    # set the funding for projects below the minimum cap to 0
    df_results.loc[df_results['rf4_allocation'] < MIN_CAP, 'rf4_allocation'] = 0
    
    # determine how much funding below the max cap is available
    filtered_projects = df_results[df_results['rf4_allocation']<MAX_CAP]
    remaining_funding = TOTAL_FUNDING - df_results[df_results['rf4_allocation']==MAX_CAP]['rf4_allocation'].sum()

    # allocate the funding for projects between the minimum and maximum cap
    df_results['rf4_allocation'].update(allocate_funding(filtered_projects['rf4_allocation'], remaining_funding))
    
    # save the results
    df_consolidated = DF_METRICS.join(df_results).sort_values(by='rf4_allocation', ascending=False)
    df_consolidated['rf4_allocation'].fillna(0)
    df_consolidated.to_csv(DESTINATION_CSV_PATH)

if __name__ == "__main__":
    main()