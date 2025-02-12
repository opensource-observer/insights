import warnings
import datetime
warnings.filterwarnings("ignore")

import pandas as pd

from utils import (read_in_stored_dfs_for_projects,
                   read_in_defi_llama_protocols, 
                   return_protocol, 
                   read_in_grants)

from config import (DEFI_LLAMA_PROTOCOLS_PATH,
                    STORED_DATA_PATH)

from sections.statistical_analysis_section import ttest_helper

from utils import (extract_addresses,
                   read_in_defi_llama_protocols, 
                   read_in_stored_dfs_for_projects,
                   return_protocol, 
                   read_in_grants)

from config import (DEFI_LLAMA_PROTOCOLS_PATH,
                    STORED_DATA_PATH)

from config import DEFI_LLAMA_PROTOCOLS_PATH, STORED_DATA_PATH

# helper function to add timestamps to print statements
def print_with_timestamp(message: str) -> None:
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

projects = read_in_grants(grants_path="updated_grants_reviewed.json")
defi_llama_protocols = read_in_defi_llama_protocols(path=DEFI_LLAMA_PROTOCOLS_PATH)

failed_projects = []
ttest_results = {"protocol": [],
                 "TVL-pvalue": [],
                 "TVL-percent_change": [],
                 "TVL-tstat": [],
                 "TVL_opchain-pvalue": [],
                 "TVL_opchain-percent_change": [],
                 "TVL_opchain-tstat": []}

for project_name, project in projects.items():
    try:
        print_with_timestamp(f"{project_name} started")
        clean_name = project_name.lower().replace(" ", "_").replace(".", "-").replace("/","-")

        chain = project['chain']
        grant_date = project['funds_recieved_date']
        token_conversion = 1E15

        just_addresses, project_addresses = extract_addresses(project_dict=project) 
        project_protocol = return_protocol(defi_llama_protocols=defi_llama_protocols, project=project_name)

        datasets = read_in_stored_dfs_for_projects(project_name=project_name, data_path=STORED_DATA_PATH, protocols=defi_llama_protocols)
        if 'tvl' in datasets.keys():
            project_tvl_df = datasets['tvl']
            project_forecasted_df = datasets['forecasted']

            if project_forecasted_df is not None and not project_forecasted_df.empty:
                protocols = set([protocol.split("-")[-1] for protocol in project_forecasted_df.columns if "forecasted_TVL" in protocol])

                for protocol in protocols:

                    # have to run ttest on pre-grant vs post-grant TVL, and then forecasted vs post-grant TVL
                    if project_tvl_df is not None and not project_tvl_df.empty:
                        project_tvl_df['readable_date'] = pd.to_datetime(
                            project_tvl_df['readable_date'].str.strip(), errors='coerce'
                        )

                        project_tvl_df.rename(columns={"totalLiquidityUSD":"TVL"}, inplace=True)
                        project_tvl_df = project_tvl_df[["readable_date", "TVL"]].dropna()

                        pre_grant_tvl_df = project_tvl_df[project_tvl_df["readable_date"] < grant_date].reset_index(drop=True)
                        post_grant_tvl_df = project_tvl_df[project_tvl_df["readable_date"] >= grant_date].reset_index(drop=True)

                        project_forecasted_df.rename(columns={f"forecasted_TVL-{protocol}":"TVL", f"forecasted_TVL_opchain-{protocol}":"TVL_opchain"}, inplace=True)
                        project_forecasted_df = project_forecasted_df[["date", "TVL", "TVL_opchain"]].dropna().reset_index(drop=True)

                        sample2 = post_grant_tvl_df
                        sample2_df = pd.DataFrame()
                        sample2_df["mean"] = sample2[["TVL"]].mean()
                        sample2_df["count"] = sample2[["TVL"]].count()
                        sample2_df["var"] = sample2[["TVL"]].var()

                        ttest_results["protocol"].append(protocol)

                        for sample1, target in [(pre_grant_tvl_df, "TVL"), (project_forecasted_df, "TVL_opchain")]:
                            # column of mean, count, var
                            sample1_df = pd.DataFrame()
                            sample1_df["mean"] = sample1[[target]].mean()
                            sample1_df["count"] = sample1[[target]].count()
                            sample1_df["var"] = sample1[[target]].var()

                            t_stat, percent_change, p_value, p_value_formatted = ttest_helper(sample1_df=sample1_df, sample2_df=sample2_df)

                            if target == "TVL":
                                ttest_results["TVL-percent_change"].append(percent_change)
                                ttest_results["TVL-pvalue"].append(p_value)
                                ttest_results["TVL-tstat"].append(t_stat)
                            if target == "TVL_opchain":
                                ttest_results["TVL_opchain-percent_change"].append(percent_change)
                                ttest_results["TVL_opchain-pvalue"].append(p_value)
                                ttest_results["TVL_opchain-tstat"].append(t_stat)
                                            
            print(f"project done")

    except Exception as e:
        print_with_timestamp(f"{project_name} project failed due to: {e}")
        failed_projects.append((clean_name, e))

ttest_results = pd.DataFrame(ttest_results).dropna().drop_duplicates().reset_index(drop=True)

print()
for failed, e in failed_projects:
    print(f"project: {failed}")
    print(f"exception: {e}")

# create a new csv that's each project and it's TVL
ttest_results.to_csv("data/tvl_ttest_results.csv", index=False)