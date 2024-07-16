import json
import pandas as pd

TOTAL_FUNDING = 10_000_000
MAX_CAP = 500_000
MIN_CAP = 1000

PRIVATE_DIR = "data/private"
#BALLOTS_CSV_PATH = f"{PRIVATE_DIR}/ballots final - export.csv"
BALLOTS_CSV_PATH = f"{PRIVATE_DIR}/EarlyBallotData.csv"
DESTINATION_CSV_PATH = f"{PRIVATE_DIR}/rf4_results.csv"

# create the Impact Metrics Share dataframe
METRICS_CSV_PATH = "data/op_rf4_impact_metrics_by_project.csv"
DF_METRICS = pd.read_csv(METRICS_CSV_PATH, index_col=1)
METRIC_IDS = DF_METRICS.columns[-16:]


def parse_payload(json_payload):
    ballot = json.loads(json_payload)
    return {
        'allocations': {
            metric_id: weight
            for metric_dict in ballot['allocations']
            for metric_id, weight in metric_dict.items()
        },
        'os_multiplier': ballot['os_multiplier']
    }


def score_projects(ballot):
    
    # get the OS multiplier for each project
    os_multiplier = DF_METRICS['is_oss'].apply(lambda x: ballot['os_multiplier'] if x else 1)
    
    # apply the OS multiplier to each metric, normalize, and apply the ballot weights
    scores = DF_METRICS[METRIC_IDS].copy()
    for metric in METRIC_IDS:
        scores[metric] = scores[metric] * os_multiplier
        scores[metric] = scores[metric] / scores[metric].sum()
        weight = ballot['allocations'].get(metric,0) / 100.
        scores[metric] *= weight

    # sum the score for each project
    project_scores = scores.sum(axis=1)
    
    return project_scores


def allocate_funding(project_scores, funding_balance=TOTAL_FUNDING):

    allocations = {}
    score_balance = project_scores.sum()
    
    # iterate through the projects in descending order of score
    for project_id, score in project_scores.sort_values(ascending=False).items():
        
        # determine the scaled, capped funding allocation for the project
        uncapped_funding_alloc = score / score_balance * funding_balance
        alloc = min(uncapped_funding_alloc, MAX_CAP)

        # allocate funding to the project
        allocations.update({project_id: alloc})

        # update the funding and score balances
        funding_balance -= alloc
        score_balance -= score

    project_allocations = pd.Series(allocations)

    return project_allocations


def main():

    # load the ballots
    df_ballots_raw = (
        pd.read_csv(BALLOTS_CSV_PATH)
        .query("Badgeholder == True & Status == 'SUBMITTED'")
        .set_index('Address')
    )

    # score the projects for each ballot
    df_ballots = df_ballots_raw['Payload'].apply(parse_payload)
    df_scores = df_ballots.apply(score_projects)

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