from processing import make_net_transaction_dataset
from queries.optimism import query_transaction_data_from_bq_optimism
from queries.defillama import query_tvl_data_from_bq
from forecasting import forecast_project

from utils import (extract_addresses,
                   read_in_defi_llama_protocols, 
                   return_protocol, 
                   read_in_grants, 
                   connect_bq_client,
                   save_datasets)

from config import (GRANTS_PATH, 
                    DEFI_LLAMA_PROTOCOLS_PATH, 
                    SERVICE_ACCOUNT_PATH,
                    STORED_DATA_PATH)

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

def generate_datasets_for_project(project_name: str) -> None:
    
    # read in the stored projects and select the project
    projects = read_in_grants(grants_path=GRANTS_PATH)
    project = projects[project_name]
    
    # read in a dictionary of each project's corresponding defi llama protocol
    defi_llama_protocols = read_in_defi_llama_protocols(path=DEFI_LLAMA_PROTOCOLS_PATH)

    # get the relevant wallet/contract addresses associated with the selected project
    just_addresses, _ = extract_addresses(project_dict=project) 
    # check if the selected project has an associated defi llama protocol
    project_protocol = return_protocol(defi_llama_protocols=defi_llama_protocols, project=project_name)

    datasets = {}

    # if this project is connected to a live streamlit instance it connects to bigquery differently
    client = connect_bq_client(service_account_path=SERVICE_ACCOUNT_PATH, use_streamlit_secrets=False)
    # query transaction count, active users, unique users, and total transferred for the passed project
    project_daily_transactions_df, project_transaction_flow_df = query_transaction_data_from_bq_optimism(client=client, project_addresses=just_addresses)
    datasets['daily_transactions'] = project_daily_transactions_df
    # use the op flow dataset (which looks at abs(op amount)) to create a dataset that considers the direction of the transactions
    project_net_transaction_flow_df = make_net_transaction_dataset(transaction_flow_df=project_transaction_flow_df)
    datasets['net_transaction_flow'] = project_net_transaction_flow_df

    # only query the tvl data if the project has an associated defi llama protocol
    if project_protocol and project_protocol is not None:
        project_chain_tvls_df, project_tvl_df, project_tokens_in_usd_df, project_tokens_df = query_tvl_data_from_bq(client=client, protocol=project_protocol)
        datasets['chain_tvls'] = project_chain_tvls_df
        datasets['tvl'] = project_tvl_df
        datasets['tokens_in_used'] = project_tokens_in_usd_df

    forecasted_df = forecast_project(datasets=datasets)
    datasets['forecasted_metrics'] = forecasted_df

    clean_project_name = project_name.lower().replace(" ", "_").replace(".", "-")
            
    save_datasets(project_name=clean_project_name, datasets=datasets, data_path=STORED_DATA_PATH)

def main():
    ... 
    #generate_datasets_for_project("Cyber")
    #generate_datasets_for_project("Fraxtal Application")

if __name__ == "__main__":
    main()