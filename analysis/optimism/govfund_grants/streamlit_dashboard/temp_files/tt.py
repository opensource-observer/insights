import warnings
import datetime
warnings.filterwarnings("ignore")

import pandas as pd

from utils import (read_in_stored_dfs_for_projects,
                   read_in_defi_llama_protocols, 
                   return_protocol, 
                   read_in_grants)

from config import (GRANTS_PATH, 
                    DEFI_LLAMA_PROTOCOLS_PATH,
                    STORED_DATA_PATH)

from sections.statistical_analysis_section import (aggregate_datasets, 
                                                   concat_aggregate_with_forecasted, 
                                                   split_dataset_by_date,
                                                   aggregate_split_datasets_by_metrics,
                                                   determine_statistics)

from processing import make_net_transaction_dataset
from forecasting import forecast_project
from queries.superchain_sandbox import query_transaction_data_from_bq_superchain_sandbox
from queries.defillama import query_tvl_data_from_bq

from utils import (connect_bq_client,
                   extract_addresses,
                   read_in_defi_llama_protocols, 
                   read_in_stored_dfs_for_projects,
                   save_datasets,
                   return_protocol, 
                   read_in_grants)

from config import (DEFI_LLAMA_PROTOCOLS_PATH,
                    SERVICE_ACCOUNT_PATH,
                    STORED_DATA_PATH)

from config import DEFI_LLAMA_PROTOCOLS_PATH, STORED_DATA_PATH

# helper function to add timestamps to print statements
def print_with_timestamp(message: str) -> None:
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

projects = read_in_grants(grants_path="updated_grants_reviewed.json")
defi_llama_protocols = read_in_defi_llama_protocols(path=DEFI_LLAMA_PROTOCOLS_PATH)

grab_from_bigquery = False
failed_projects = []

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

            protocols = project_tvl_df['protocol'].dropna().unique().tolist()

            for protocol in protocols:

                if project_tvl_df is not None and not project_tvl_df.empty:
                    project_tvl_df['readable_date'] = pd.to_datetime(
                        project_tvl_df['readable_date'].str.strip(), errors='coerce'
                    )

                combined_df = concat_aggregate_with_forecasted(project_tvl_df, project_forecasted_df)

                print(combined_df)

                pre_grant_df, post_grant_df = split_dataset_by_date(combined_df, grant_date=grant_date)
                post_grant_df = post_grant_df[post_grant_df["grant_label"] == "post grant"]
                curr_forecasted_df = combined_df[combined_df["grant_label"] == "forecast"]
                
            print(f"project done")

    except Exception as e:
        print_with_timestamp(f"{project_name} project failed due to: {e}")
        failed_projects.append((clean_name, e))


print()
for failed, e in failed_projects:
    print(f"project: {failed}")
    print(f"exception: {e}")

# create a new csv that's each project and it's TVL
