from utils import read_in_grants, read_in_stored_dfs_for_projects, read_in_defi_llama_protocols, return_protocol
from config import GRANTS_PATH, STORED_DATA_PATH, DEFI_LLAMA_PROTOCOLS_PATH

from sections.statistical_analysis_section import ttest_helper

import pandas as pd


projects = read_in_grants(GRANTS_PATH)
defi_llama_protocols = read_in_defi_llama_protocols(path=DEFI_LLAMA_PROTOCOLS_PATH)

target_metrics = ["TVL", "active_users", "DAA/MAA", "transaction_cnt", "gas_fee"]

ttest_results = pd.read_csv("data/ttest_results.csv", header=[0,1])
tvl_ttest_results = pd.read_csv("data/tvl_ttest_results.csv")

# north star dataset
# protocol as index, north star metric, pre-grant total, post-grant total, growth amount

north_star_results = {
    "project": [],
    "north_star": [],
    "synthetic_control_group": [],
    "post_grant_actual": [],
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

for project_name, project in projects.items():
    north_star = project["north_star"]
    grant_date = project['funds_recieved_date']

    if north_star in target_metrics:
        project_protocol = return_protocol(defi_llama_protocols=defi_llama_protocols, project=project_name)
        datasets = read_in_stored_dfs_for_projects(project_name=project_name, data_path=STORED_DATA_PATH, protocols=defi_llama_protocols)
        #print(project_name)
        #print(north_star)
        #print()

        if north_star == "TVL":
            if "tvl" in datasets and datasets["tvl"] is not None and not datasets["tvl"].empty:
                tvl_df = datasets["tvl"].rename(columns={"totalLiquidityUSD": "TVL"})
                forecasted_df = datasets["forecasted"]
                tvl_df["readable_date"] = pd.to_datetime(tvl_df["readable_date"])

                if forecasted_df is not None and not forecasted_df.empty:
                    forecasted_df["date"] = pd.to_datetime(forecasted_df["date"])
                    
                    protocols = set([protocol.split("-")[-1] for protocol in forecasted_df.columns if "forecasted_TVL" in protocol])

                    for protocol in protocols:
                        tvl_north_star_results['project'].append(project_name)
                        tvl_north_star_results['protocol'].append(protocol)
                        tvl_north_star_results["north_star"].append(north_star)

                        sample1_df = pd.DataFrame()
                        sample1_df["mean"] = tvl_df[tvl_df["readable_date"] >= grant_date][[north_star]].mean()
                        sample1_df["count"] = tvl_df[tvl_df["readable_date"] >= grant_date][[north_star]].count()
                        sample1_df["var"] = tvl_df[tvl_df["readable_date"] >= grant_date][[north_star]].var()

                        sample2_df = pd.DataFrame()
                        sample2_df["mean"] = forecasted_df[forecasted_df["date"] >= grant_date][[f"forecasted_TVL_opchain-{protocol}"]].mean()
                        sample2_df["count"] = forecasted_df[forecasted_df["date"] >= grant_date][[f"forecasted_TVL_opchain-{protocol}"]].count()
                        sample2_df["var"] = forecasted_df[forecasted_df["date"] >= grant_date][[f"forecasted_TVL_opchain-{protocol}"]].var()

                        _, percent_change, p_value, _ = ttest_helper(sample1_df, sample2_df)

                        tvl_north_star_results["synthetic_control_group"].append(float(sample1_df["mean"].iloc[0]))
                        tvl_north_star_results["post_grant_actual"].append(float(sample2_df["mean"].iloc[0]))
                        tvl_north_star_results["percent_change"].append(percent_change)
                        tvl_north_star_results["p_value"].append(p_value)

        else:
            north_star_results['project'].append(project_name)
            north_star_results["north_star"].append(north_star)

            transactions_df = datasets["daily_transactions"]
            transactions_df["transaction_date"] = pd.to_datetime(transactions_df["transaction_date"])
            
            sample1_df = pd.DataFrame()
            sample1_df["mean"] = transactions_df[transactions_df["transaction_date"] < grant_date][[north_star]].mean()
            sample1_df["count"] = transactions_df[transactions_df["transaction_date"] < grant_date][[north_star]].count()
            sample1_df["var"] = transactions_df[transactions_df["transaction_date"] < grant_date][[north_star]].var()

            sample2_df = pd.DataFrame()
            sample2_df["mean"] = transactions_df[transactions_df["transaction_date"] >= grant_date][[north_star]].mean()
            sample2_df["count"] = transactions_df[transactions_df["transaction_date"] >= grant_date][[north_star]].count()
            sample2_df["var"] = transactions_df[transactions_df["transaction_date"] >= grant_date][[north_star]].var()

            _, percent_change, p_value, _ = ttest_helper(sample1_df, sample2_df)
        
            north_star_results["synthetic_control_group"].append(float(sample1_df["mean"].iloc[0]))
            north_star_results["post_grant_actual"].append(float(sample2_df["mean"].iloc[0]))
            north_star_results["percent_change"].append(percent_change)
            north_star_results["p_value"].append(p_value)

north_star_results = pd.DataFrame(north_star_results)
tvl_north_star_results = pd.DataFrame(tvl_north_star_results)

north_star_results.to_csv("data/north_star_results.csv", index=False)
tvl_north_star_results.to_csv("data/tvl_north_star_results.csv", index=False)