from utils import (
    read_in_grants,
    read_in_stored_dfs_for_projects,
    read_in_defi_llama_protocols,
    return_protocol
)
from config import GRANTS_PATH, STORED_DATA_PATH, DEFI_LLAMA_PROTOCOLS_PATH

from sections.statistical_analysis_section import ttest_helper

import pandas as pd
import numpy as np

projects = read_in_grants(GRANTS_PATH)
defi_llama_protocols = read_in_defi_llama_protocols(path=DEFI_LLAMA_PROTOCOLS_PATH)

target_metrics = ["TVL", "active_users", "DAA/MAA", "transaction_cnt", "gas_fee", "new_delegators", "new_voters"]

ttest_results = pd.read_csv("data/ttest_results.csv", header=[0,1])
tvl_ttest_results = pd.read_csv("data/tvl_ttest_results.csv")

# Results containers
north_star_results = {
    "project": [],
    "north_star": [],
    "synthetic_control_group": [],  # Forecast / baseline
    "post_grant_actual": [],        # Real post-grant data
    "percent_change": [],
    "p_value": []
}

tvl_north_star_results = {
    "project": [],
    "protocol": [],
    "north_star": [],
    "synthetic_control_group": [],
    "post_grant_actual": [],
    "percent_change": [],
    "p_value": []
}

not_in = []

for project_name, project in projects.items():
    north_star = project.get("north_star")
    grant_date = project.get("funds_recieved_date")

    if north_star in target_metrics:
        # Identify the protocol(s) relevant to this project
        project_protocol = return_protocol(
            defi_llama_protocols=defi_llama_protocols,
            project=project_name
        )
        
        # Read in all stored data for this project
        datasets = read_in_stored_dfs_for_projects(
            project_name=project_name,
            data_path=STORED_DATA_PATH,
            protocols=defi_llama_protocols  # or possibly project_protocol
        )
        
        if north_star == "TVL":
            # 1) Check we have tvl and forecasted data
            tvl_df = datasets.get("tvl")
            if tvl_df is not None and not tvl_df.empty:
                # Rename totalLiquidityUSD => TVL if present
                tvl_df = tvl_df.rename(columns={"totalLiquidityUSD": "TVL"}).copy()
                if "readable_date" in tvl_df.columns:
                    tvl_df["readable_date"] = pd.to_datetime(
                        tvl_df["readable_date"], errors='coerce'
                    )
                
                forecasted_df = datasets.get("forecasted")
                if forecasted_df is not None and not forecasted_df.empty:
                    # Parse 'date' in forecasted data
                    if "date" in forecasted_df.columns:
                        forecasted_df["date"] = pd.to_datetime(
                            forecasted_df["date"], errors='coerce'
                        )
                    
                    # Identify all protocols in the forecast columns
                    protocol_cols = [
                        c for c in forecasted_df.columns
                        if c.startswith("forecasted_TVL_opchain-")
                    ]
                    protocols = set(col.split("-")[-1] for col in protocol_cols)
                    
                    for protocol in protocols:
                        # Subset tvl_df for this protocol, if it has a 'protocol' column
                        # or else just use the entire tvl_df
                        if 'protocol' in tvl_df.columns:
                            curr_tvl_df = tvl_df[tvl_df["protocol"] == protocol]
                        else:
                            curr_tvl_df = tvl_df

                        # We'll do a t-test comparing (sample1=synthetic forecast) vs (sample2=post-grant actual)
                        tvl_north_star_results["project"].append(project_name)
                        tvl_north_star_results["protocol"].append(protocol)
                        tvl_north_star_results["north_star"].append(north_star)

                        #  sample2 -> post-grant actual
                        post_grant_actual = curr_tvl_df[curr_tvl_df["readable_date"] >= grant_date]

                        #  sample1 -> forecast (synthetic control)
                        col_forecast = f"forecasted_TVL_opchain-{protocol}"
                        if col_forecast not in forecasted_df.columns:
                            # Missing column => skip
                            tvl_north_star_results["synthetic_control_group"].append(np.nan)
                            tvl_north_star_results["post_grant_actual"].append(np.nan)
                            tvl_north_star_results["percent_change"].append(np.nan)
                            tvl_north_star_results["p_value"].append(np.nan)
                            continue
                        
                        synthetic_data = forecasted_df[forecasted_df["date"] >= grant_date]

                        # Build sample1_df => synthetic
                        sample1_df = pd.DataFrame()
                        sample1_df["mean"] = synthetic_data[[col_forecast]].mean()
                        sample1_df["count"] = synthetic_data[[col_forecast]].count()
                        sample1_df["var"] = synthetic_data[[col_forecast]].var()

                        # Build sample2_df => post-grant actual
                        sample2_df = pd.DataFrame()
                        sample2_df["mean"] = post_grant_actual[[north_star]].mean()
                        sample2_df["count"] = post_grant_actual[[north_star]].count()
                        sample2_df["var"] = post_grant_actual[[north_star]].var()

                        # If either sample is empty, skip
                        if sample1_df["count"].iloc[0] == 0 or sample2_df["count"].iloc[0] == 0:
                            tvl_north_star_results["synthetic_control_group"].append(np.nan)
                            tvl_north_star_results["post_grant_actual"].append(np.nan)
                            tvl_north_star_results["percent_change"].append(np.nan)
                            tvl_north_star_results["p_value"].append(np.nan)
                            continue
                        
                        # T-test => sample1=forecast, sample2=actual
                        _, percent_change, p_value, _ = ttest_helper(sample1_df, sample2_df)

                        # Store results
                        tvl_north_star_results["synthetic_control_group"].append(
                            float(sample1_df["mean"].iloc[0])
                        )
                        tvl_north_star_results["post_grant_actual"].append(
                            float(sample2_df["mean"].iloc[0])
                        )
                        tvl_north_star_results["percent_change"].append(percent_change)
                        tvl_north_star_results["p_value"].append(p_value)

        else:
            # The north star is one of: "active_users", "DAA/MAA", "transaction_cnt", "gas_fee", "new_delegators", "new_voters"
            # We'll do a pre-grant vs post-grant t-test
            north_star_results["project"].append(project_name)
            north_star_results["north_star"].append(north_star)

            transactions_df = datasets.get("daily_transactions")
            if transactions_df is None or transactions_df.empty:
                # If no data for daily_transactions, store NaNs
                north_star_results["synthetic_control_group"].append(np.nan)
                north_star_results["post_grant_actual"].append(np.nan)
                north_star_results["percent_change"].append(np.nan)
                north_star_results["p_value"].append(np.nan)
                continue

            if "transaction_date" in transactions_df.columns:
                transactions_df["transaction_date"] = pd.to_datetime(
                    transactions_df["transaction_date"], errors='coerce'
                )

            if north_star in ["new_delegators", "new_voters"]:
                delegators_and_voters_df = datasets.get("delegators_and_voters")
                delegators_and_voters_df["date"] = pd.to_datetime(delegators_and_voters_df["date"])
                transactions_df = pd.merge(transactions_df, delegators_and_voters_df, left_on="transaction_date", right_on="date", how="outer")
                transactions_df.rename(columns={"unique_delegates":"new_delegators", "unique_voters":"new_voters"}, inplace=True)

            # Ensure the chosen column (north_star) actually exists
            if north_star not in transactions_df.columns:
                north_star_results["synthetic_control_group"].append(np.nan)
                north_star_results["post_grant_actual"].append(np.nan)
                north_star_results["percent_change"].append(np.nan)
                north_star_results["p_value"].append(np.nan)
                continue

            # sample1 => pre-grant (control), sample2 => post-grant
            sample1 = transactions_df[transactions_df["transaction_date"] < grant_date]
            sample2 = transactions_df[transactions_df["transaction_date"] >= grant_date]

            sample1_df = pd.DataFrame()
            sample1_df["mean"] = sample1[[north_star]].mean()
            sample1_df["count"] = sample1[[north_star]].count()
            sample1_df["var"] = sample1[[north_star]].var()

            sample2_df = pd.DataFrame()
            sample2_df["mean"] = sample2[[north_star]].mean()
            sample2_df["count"] = sample2[[north_star]].count()
            sample2_df["var"] = sample2[[north_star]].var()

            if sample1_df["count"].iloc[0] == 0 or sample2_df["count"].iloc[0] == 0:
                north_star_results["synthetic_control_group"].append(np.nan)
                north_star_results["post_grant_actual"].append(np.nan)
                north_star_results["percent_change"].append(np.nan)
                north_star_results["p_value"].append(np.nan)
                continue

            _, percent_change, p_value, _ = ttest_helper(sample1_df, sample2_df)

            # Typically, pre-grant is the "control" or baseline => sample1
            north_star_results["synthetic_control_group"].append(
                float(sample1_df["mean"].iloc[0])
            )
            north_star_results["post_grant_actual"].append(
                float(sample2_df["mean"].iloc[0])
            )
            north_star_results["percent_change"].append(percent_change)
            north_star_results["p_value"].append(p_value)

    else:
        not_in.append({project_name : north_star})

# Convert to DataFrame and save
north_star_results = pd.DataFrame(north_star_results)
tvl_north_star_results = pd.DataFrame(tvl_north_star_results)

north_star_results.to_csv("data/north_star_results2.csv", index=False)
tvl_north_star_results.to_csv("data/tvl_north_star_results2.csv", index=False)
