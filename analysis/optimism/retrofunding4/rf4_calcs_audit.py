import json
import pandas as pd

# Retro Funding 4 constants
TOTAL_FUNDING = 10_000_000
MAX_CAP = 500_000
MIN_CAP = 1000

# private data paths (hidden from git)
PRIVATE_DIR = "data/private"
BALLOTS_CSV_PATH = f"{PRIVATE_DIR}/Voting data export final.csv"
DESTINATION_CSV_PATH = f"{PRIVATE_DIR}/rf4_results.csv"

# load the Impact Metrics as a global dataframe
METRICS_CSV_PATH = "data/op_rf4_impact_metrics_by_project.csv"
DF_METRICS = pd.read_csv(METRICS_CSV_PATH, index_col=1)
METRIC_IDS = DF_METRICS.columns[-16:]


def parse_payload(json_payload):
    """
    Parse the JSON payload into a dictionary with allocations and OS multiplier.
    """
    ballot = json.loads(json_payload)
    allocations = {
        metric_id: weight
        for metric_dict in ballot['allocations']
        for metric_id, weight in metric_dict.items()
    }
    return {'allocations': allocations, 'os_multiplier': ballot['os_multiplier']}


def score_projects(ballot):
    """
    Score projects based on the ballot's allocations and the OS multiplier.
    """
    os_multiplier = DF_METRICS['is_oss'].apply(lambda x: ballot['os_multiplier'] if x else 1)
    scores = DF_METRICS[METRIC_IDS].copy()

    for metric in METRIC_IDS:
        scores[metric] *= os_multiplier
        scores[metric] /= scores[metric].sum()
        weight = ballot['allocations'].get(metric, 0) / 100.0
        scores[metric] *= weight

    return scores.sum(axis=1)


def allocate_funding(project_scores, funding_balance=TOTAL_FUNDING):
    """
    Allocate funding to projects based on their scores.
    """
    allocations = {}
    score_balance = project_scores.sum()

    for project_id, score in project_scores.sort_values(ascending=False).items():
        uncapped_funding_alloc = score / score_balance * funding_balance
        capped_funding_alloc = min(uncapped_funding_alloc, MAX_CAP)
        allocations[project_id] = capped_funding_alloc
        funding_balance -= capped_funding_alloc
        score_balance -= score

    return pd.Series(allocations)


def main():

    # 0. load the ballots
    df_ballots_raw = (
        pd.read_csv(BALLOTS_CSV_PATH)
        .query("Badgeholder == True & Status == 'SUBMITTED'")
        .set_index('Address')
    )

    # 1. score each ballot
    df_ballots = df_ballots_raw['Payload'].apply(parse_payload)
    df_scores = df_ballots.apply(score_projects)

    # 2. allocate funding for each badgeholder
    df_results = df_scores.apply(allocate_funding, axis=1).T

    # 3. get the median funding for each project
    df_results['median'] = df_results.median(axis=1)

    # 4. allocate funding based on the median badgeholder allocation
    df_results['rf4_allocation'] = allocate_funding(df_results['median'])
    
    # 5. set the funding for projects below the minimum cap to 0
    df_results.loc[df_results['rf4_allocation'] < MIN_CAP, 'rf4_allocation'] = 0
    
    # 6. allocate the remaining funding to projects below the maximum cap
    max_cap_funding = df_results[df_results['rf4_allocation']==MAX_CAP]['rf4_allocation'].sum()
    remaining_funding = TOTAL_FUNDING - max_cap_funding
    df_remaining = df_results[df_results['rf4_allocation']<MAX_CAP]
    df_results['rf4_allocation'].update(allocate_funding(df_remaining['rf4_allocation'], remaining_funding))
    
    # 7. dump the results
    df_consolidated = DF_METRICS.join(df_results).sort_values(by='rf4_allocation', ascending=False)
    df_consolidated['rf4_allocation'].fillna(0)
    df_consolidated.to_csv(DESTINATION_CSV_PATH)


if __name__ == "__main__":
    main()