import warnings
import datetime
warnings.filterwarnings("ignore")

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

projects = read_in_grants(grants_path="errored_projects.json")
defi_llama_protocols = read_in_defi_llama_protocols(path=DEFI_LLAMA_PROTOCOLS_PATH)

grab_from_bigquery = True
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

        if grab_from_bigquery:
            client = connect_bq_client(service_account_path=SERVICE_ACCOUNT_PATH, use_streamlit_secrets=False)
            datasets = {}

            project_daily_transactions_df, project_net_transaction_flow_df = query_transaction_data_from_bq_superchain_sandbox(client=client, project_addresses=just_addresses, grant_date=grant_date, token_conversion=token_conversion, chain=chain)
            if chain == "op":
                project_net_transaction_flow_df = make_net_transaction_dataset(transaction_flow_df=project_net_transaction_flow_df)

            datasets['net_transaction_flow'] = project_net_transaction_flow_df
            print_with_timestamp("daily transaction dataset queried")
            datasets['daily_transactions'] = project_daily_transactions_df

            if project_protocol and project_protocol is not None:
                project_chain_tvls_df, project_tvl_df, project_tokens_in_usd_df, project_tokens_df = query_tvl_data_from_bq(client=client, protocol=project_protocol)

                datasets['chain_tvls'] = project_chain_tvls_df
                datasets['tvl'] = project_tvl_df
                datasets['tokens_in_usd'] = project_tokens_in_usd_df

                print_with_timestamp("tvl datasets queried and created")

        else:
            datasets = read_in_stored_dfs_for_projects(project_name=project_name, data_path=STORED_DATA_PATH, protocols=defi_llama_protocols)

        project_forecasted_df = forecast_project(datasets=datasets, grant_date=grant_date)
        print_with_timestamp("forecasting completed")
        datasets['forecasted_metrics'] = project_forecasted_df

        save_datasets(project_name=clean_name, datasets=datasets, data_path=STORED_DATA_PATH)
        print_with_timestamp("datasets saved")
        print()

    except Exception as e:
        print_with_timestamp(f"{project_name} project failed due to: {e}")
        failed_projects.append((clean_name, e))


print()
for failed, e in failed_projects:
    print(f"project: {failed}")
    print(f"exception: {e}")