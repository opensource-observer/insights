import warnings
import datetime
warnings.filterwarnings("ignore")

import pandas as pd
from pandas import Timedelta

from utils import (
    read_in_stored_dfs_for_projects,
    read_in_defi_llama_protocols,
    return_protocol,
    read_in_grants,
    extract_addresses
)
from config import (
    DEFI_LLAMA_PROTOCOLS_PATH,
    STORED_DATA_PATH
)
from sections.statistical_analysis_section import ttest_helper


# helper function to add timestamps to print statements
def print_with_timestamp(message: str) -> None:
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

projects = read_in_grants(grants_path="updated_grants_reviewed.json")
defi_llama_protocols = read_in_defi_llama_protocols(path=DEFI_LLAMA_PROTOCOLS_PATH)

failed_projects = []
ttest_results = {
    "project": [],
    "protocol": [],
    "TVL-pvalue": [],
    "TVL-percent_change": [],
    "TVL-tstat": [],
    "TVL_opchain-pvalue": [],
    "TVL_opchain-percent_change": [],
    "TVL_opchain-tstat": []
}

for project_name, project in projects.items():
    try:
        print_with_timestamp(f"{project_name} started")
        clean_name = project_name.lower().replace(" ", "_").replace(".", "-").replace("/","-")

        chain = project['chain']
        grant_date = project['funds_recieved_date']

        # gather addresses (though not used below, presumably needed for other logic)
        just_addresses, project_addresses = extract_addresses(project_dict=project)

        # determine the relevant DeFi Llama protocol
        project_protocol = return_protocol(
            defi_llama_protocols=defi_llama_protocols,
            project=project_name
        )

        datasets = read_in_stored_dfs_for_projects(
            project_name=project_name,
            data_path=STORED_DATA_PATH,
            protocols=defi_llama_protocols
        )

        # If there's a tvl dataset, proceed
        if 'tvl' in datasets.keys():
            project_tvl_df = datasets['tvl']
            project_forecasted_df = datasets.get('forecasted', None)

            # Only do comparisons if forecasted df is non-empty
            if project_forecasted_df is not None and not project_forecasted_df.empty:
                # Identify which protocols appear in forecasted columns
                # e.g., columns like "forecasted_TVL-<protocol>" or "forecasted_TVL_opchain-<protocol>"
                protocol_cols = [
                    c for c in project_forecasted_df.columns 
                    if c.startswith("forecasted_TVL")  # catches forecasted_TVL and forecasted_TVL_opchain
                ]
                protocols = set(col.split("-")[-1] for col in protocol_cols if "-" in col)

                # Convert date columns to datetime
                # so we can separate pre-/post-grant properly
                if project_tvl_df is not None and not project_tvl_df.empty:
                    project_tvl_df['readable_date'] = pd.to_datetime(
                        project_tvl_df['readable_date'].astype(str).str.strip(), 
                        errors='coerce'
                    )
                    # rename totalLiquidityUSD => TVL if it exists
                    if "totalLiquidityUSD" in project_tvl_df.columns:
                        project_tvl_df.rename(columns={"totalLiquidityUSD": "TVL"}, inplace=True)

                print_with_timestamp(f"{project_name} → procotols: {protocols}")

                for proto in protocols:
                    tvl_df_for_proto = project_tvl_df[project_tvl_df["protocol"] == proto].copy()

                    # We need to ensure we can rename forecasted_TVL-{proto} => TVL
                    # and forecasted_TVL_opchain-{proto} => TVL_opchain
                    # but only for the subset of columns that exist for this protocol
                    col_base = f"forecasted_TVL-{proto}"
                    col_op = f"forecasted_TVL_opchain-{proto}"
                    if (col_base not in project_forecasted_df.columns) or (col_op not in project_forecasted_df.columns):
                        # skip if we don't have both columns for this protocol
                        continue

                    # Build a fresh copy of only the relevant columns
                    df_proto = project_forecasted_df[["date", col_base, col_op]].copy()
                    df_proto.rename(
                        columns={
                            col_base: "TVL", 
                            col_op: "TVL_opchain"
                        }, 
                        inplace=True
                    )
                    df_proto.dropna(inplace=True)
                    df_proto['date'] = pd.to_datetime(df_proto['date'], errors='coerce')

                    # Now we do the pre-grant vs. post-grant actual for "TVL"
                    # and forecasted ("TVL_opchain") vs. post-grant actual for the t-test
                    if project_tvl_df is not None and not project_tvl_df.empty:
                        # Filter out rows lacking the "TVL" column if it doesn't exist
                        if "TVL" not in project_tvl_df.columns:
                            continue

                        if "readable_date" in tvl_df_for_proto.columns and "TVL" in tvl_df_for_proto.columns:
                            tvl_df_for_proto = tvl_df_for_proto[["readable_date", "TVL"]].dropna()
                            tvl_df_for_proto["readable_date"] = pd.to_datetime(tvl_df_for_proto["readable_date"])

                            if not df_proto.empty:
                                min_date = grant_date - Timedelta(days=len(df_proto))
                            else:
                                min_date = grant_date  

                            pre_grant_tvl_df = tvl_df_for_proto[
                                (tvl_df_for_proto["readable_date"] < grant_date) & 
                                (tvl_df_for_proto["readable_date"] >= min_date)
                            ].reset_index(drop=True)

                            post_grant_tvl_df = tvl_df_for_proto[tvl_df_for_proto["readable_date"] >= grant_date].reset_index(drop=True)

                        # We'll treat post_grant_tvl_df as sample2
                        sample2_df = pd.DataFrame()
                        sample2_df["mean"] = post_grant_tvl_df[["TVL"]].mean()
                        sample2_df["count"] = post_grant_tvl_df[["TVL"]].count()
                        sample2_df["var"] = post_grant_tvl_df[["TVL"]].var()

                        # Mark which protocol we're analyzing in results
                        ttest_results["project"].append(project_name)
                        ttest_results["protocol"].append(proto)

                        # We'll run two T-tests:
                        # 1) pre_grant_tvl_df["TVL"] vs post_grant_tvl_df["TVL"]
                        # 2) df_proto["TVL_opchain"] vs post_grant_tvl_df["TVL"]
                        comparisons = [
                            (pre_grant_tvl_df, "TVL"), 
                            (df_proto, "TVL_opchain")
                        ]

                        for sample1, target in comparisons:
                            # Build sample1_df
                            if target not in sample1.columns:
                                # skip if the column isn't actually present
                                continue

                            sample1_df = pd.DataFrame()
                            sample1_df["mean"] = sample1[[target]].mean()
                            sample1_df["count"] = sample1[[target]].count()
                            sample1_df["var"] = sample1[[target]].var()

                            # compute the t-test
                            t_stat, percent_change, p_value, p_value_formatted = ttest_helper(
                                sample1_df=sample1_df, 
                                sample2_df=sample2_df
                            )

                            if target == "TVL":
                                ttest_results["TVL-percent_change"].append(percent_change)
                                ttest_results["TVL-pvalue"].append(p_value)
                                ttest_results["TVL-tstat"].append(t_stat)
                            else:  # target == "TVL_opchain"
                                ttest_results["TVL_opchain-percent_change"].append(percent_change)
                                ttest_results["TVL_opchain-pvalue"].append(p_value)
                                ttest_results["TVL_opchain-tstat"].append(t_stat)

                print_with_timestamp(f"{project_name} → added results for {proto}")

            print(f"project done")

    except Exception as e:
        print_with_timestamp(f"{project_name} project failed due to: {e}")
        failed_projects.append((clean_name, e))

# Build a DataFrame of results, drop duplicates, etc.
ttest_results = pd.DataFrame(ttest_results).dropna().drop_duplicates().reset_index(drop=True)

print()
for failed, e in failed_projects:
    print(f"project: {failed}")
    print(f"exception: {e}")

# create a new csv that's each project and its TVL
ttest_results.to_csv("data/tvl_ttest_results2.csv", index=False)
