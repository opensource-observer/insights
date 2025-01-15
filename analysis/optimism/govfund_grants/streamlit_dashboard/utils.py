from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account
import streamlit as st
import pandas as pd
import json
import os
from typing import List, Dict, Tuple, Union, Optional, Callable, Any

# allow for projects that might not have the same data as others to only visualize the plots that execute
def safe_execution(func: Callable, *args: Any) -> None:
    try:
        func(*args)
    except Exception:
        pass

# create a dictionary of the target grants to work with
def read_in_grants(grants_path: str) -> Dict[str, Dict[str, Union[str, List[str], Dict[str, Union[str, int]]]]]:
    clean_grants = {}
    with open(file=grants_path, mode="r") as f:
        grants = json.load(f)

    for project in grants:
        # creating a dictionary of desired format
        clean_grants[project['project_name']] = {
            "chain": project.get("chain", "N/A"),
            "pull_from_bigquery": project.get("pull_from_bigquery", False),
            "store_bq_datasets": project.get("store_bq_datasets", False),
            "live_streamlit_instance": project.get("live_streamlit_instance", False),
            "display_by_address": project.get("display_by_address", False),
            "grant_date": datetime.strptime(project["grant_date_str"], "%Y-%m-%d") if project.get("grant_date_str") not in [None, "N/A"] else None,
            "grant_date_str": project.get("grant_date_str", "N/A"),
            "token_conversion": project.get("token_conversion", "N/A"),
            "round": project.get("round", "N/A"),
            "cycle": project.get("cycle", "N/A"),
            "status": project.get("status", "N/A"),
            "proposal_link": project.get("proposal_link", "#"),
            "amount": project.get("amount", "N/A"),
            "meta": project.get("meta", {}),
            "relevant_metrics": project.get("relevant_metrics", {}),
            "relevant_dates": project.get("relevant_dates", {}),
            "relevant_chains": project.get("relevant_chains", []),
            "addresses": project.get("addresses", []),
            "project_name": project.get('project_name', "N/A")  # ensure name is stored
        }

    return clean_grants

# returns max(oldest transaction for the project, grant date - time since grant date)
def get_project_min_date_optimism(client: bigquery.Client, project_addresses: Tuple[str, ...], grant_date: datetime):
    from queries.optimism import query_transactions_min_date_optimism # to avoid circular import

    # create a pre-grant date range equal to the post-grant date length
    time_since_interval = datetime.today() - grant_date
    min_start = grant_date - time_since_interval
    min_start_string = min_start.strftime('%Y-%m-%d')

    # determine the minimum date of a transaction from the dataset
    transactions_min_date = query_transactions_min_date_optimism(client=client, project_addresses=project_addresses, start_date=min_start_string)

    # ensure transactions_min_date is valid before comparison
    # determine the minimum start date we can use
    min_start = max(transactions_min_date, min_start)

    return min_start

# get all of the addresses relevant to the target project
def extract_addresses(project_dict: Dict[str, List[Dict[str, Dict[str, Union[str, int]]]]]) -> Tuple[Tuple[str, ...], List[Dict[str, Union[str, None]]]]:
    project_address_dict = project_dict['addresses']

    project_addresses = []
    for address in project_address_dict:
        current_address = list(address.keys())[0]
        tags = address[current_address]['tags']
        
        current_label = tuple(set(tags))

        project_addresses.append({'address':current_address, 'label':current_label})

    just_addresses = tuple(set([address['address'] for address in project_addresses]))

    return just_addresses, project_addresses

# read in a dictionary of projects mapped to their respective protocols
def read_in_defi_llama_protocols(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        defi_llama_protocols = json.load(f)

    return defi_llama_protocols

# search for the target project and return the corresponding protocol
def return_protocol(defi_llama_protocols: Dict[str, Any], project: str) -> Optional[Any]:
    return defi_llama_protocols.get(project, None)

# connect to the bigquery client to begin querying
def connect_bq_client(service_account_path: str=None, use_streamlit_secrets: bool=False) -> bigquery.Client:
    credentials = None

    # check the source of the credentials
    if use_streamlit_secrets:
        try:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"]
            )

        except (ImportError, KeyError):
            raise ValueError(
                "Streamlit secrets could not be accessed. Make sure to define `gcp_service_account` in `st.secrets`."
            )
        
    elif service_account_path:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path
        )

    else:
        raise ValueError(
            "No valid credentials provided. Either `use_streamlit_secrets` must be True or `service_account_path` must be provided."
        )

    # create and return the bigquery client
    client = bigquery.Client(credentials=credentials)
    return client

# read in already stored datasets at the respective path
def read_in_stored_dfs_for_projects(project_name: str, data_path: str, protocol: Any) -> Dict[str, Any]:
    # get the clean name of the project
    clean_name = project_name.lower().replace(" ", "_").replace(".", "-")

    # initialize everything to None
    daily_transactions = None
    net_transaction_flow = None
    chain_tvls_df = None
    tvl_df = None
    tokens_in_usd_df = None
    forecasted_df = None

    # read in daily transactions dataset
    try:
        daily_transactions = pd.read_csv(f"{data_path}{clean_name}/{clean_name}_daily_transactions.csv")
    except Exception:
        pass

    # read in net transaction flow dataset
    try:
        net_transaction_flow = pd.read_csv(f"{data_path}{clean_name}/{clean_name}_net_transaction_flow.csv")
    except Exception:
        pass

    # read in TVL datasets if protocol is provided
    if protocol is not None:
        try:
            chain_tvls_df = pd.read_csv(f"{data_path}{clean_name}/{clean_name}_chain_tvls.csv")
        except Exception:
            pass

        try:
            tvl_df = pd.read_csv(f"{data_path}{clean_name}/{clean_name}_tvl.csv")
        except Exception:
            pass

        try:
            tokens_in_usd_df = pd.read_csv(f"{data_path}{clean_name}/{clean_name}_tokens_in_usd.csv")
        except Exception:
            pass

    # read in the forecasted dataset 
    try:
        forecasted_df = pd.read_csv(f"{data_path}{clean_name}/{clean_name}_forecasted_metrics.csv")
    except Exception:
        pass

    # return a dict with each key = dataframe or None
    return {
        "daily_transactions": daily_transactions,
        "net_transaction_flow": net_transaction_flow,
        "forecasted" : forecasted_df,
        "chain_tvls" : chain_tvls_df,
        "tvl": tvl_df,
        "tokens_in_usd": tokens_in_usd_df
    }

# save all of the passed datasets to the desired path
def save_datasets(project_name: str, datasets: Dict[str, pd.DataFrame], data_path: str) -> None:
    # get the clean name of the project
    clean_name = project_name.lower().replace(" ", "_").replace(".", "-")

    for dataset_name, dataset in datasets.items():
        current_dataset_path = f"{data_path}{clean_name}/{clean_name}_{dataset_name}.csv"
        dataset.to_csv(current_dataset_path, index=False)

    return

# helper function used to create KPIs that determine the amount of growth that occurred between two metrics 
def compute_growth(df: pd.DataFrame, column_name: str) -> Tuple[Optional[float], Optional[float]]:
    if len(df) < 2: return None, None

    last_value = df[column_name].iloc[-1]
    prev_value = df[column_name].iloc[-2]
    difference = last_value - prev_value

    if prev_value == 0: percent_change = 0
    else: percent_change = (difference / prev_value) * 100
    
    return difference, percent_change

# helper function to assign pre/post-grant labels
def assign_grant_label(row: Any, grant_date: str) -> str:
    date_col = determine_date_col(row=row)

    # compare the row's date with GRANT_DATE
    if pd.to_datetime(row[date_col]) < pd.to_datetime(grant_date):
        return 'pre grant'
    else:
        return 'post grant'

# helper function for single/multiple addresses
def get_addresses_condition(project_addresses: Tuple[str, ...]) -> str:
    if len(project_addresses) == 1:
        return f"= '{project_addresses[0]}'"
    return f"IN {tuple(project_addresses)}"

# identifies the date column based on the dataset
def determine_date_col(df: pd.DataFrame=None, row: pd.Series=None):

    date_col = None
    
    if df is not None:
        if 'transaction_date' in df.columns:
            date_col = 'transaction_date'
        elif 'readable_date' in df.columns:
            date_col = 'readable_date'
        elif 'date' in df.columns:
            date_col = 'date'

    elif row is not None:
        if 'transaction_date' in row and pd.notnull(row['transaction_date']):
            date_col = 'transaction_date'
        elif 'readable_date' in row and pd.notnull(row['readable_date']):
            date_col = 'readable_date'
        elif 'date' in row and pd.notnull(row['date']):
            date_col = 'date'

    return date_col

# save the datasets at the respective path
def save_datasets(project_name: str, datasets: Dict[str, pd.DataFrame], data_path: str) -> None:
    # get the clean name of the project
    clean_name = project_name.lower().replace(" ", "_").replace(".", "-")

    # ensure the target directory exists
    project_path = os.path.join(data_path, clean_name)
    os.makedirs(project_path, exist_ok=True)

    for dataset_name, dataset in datasets.items():
        # save each dataset as a CSV file
        dataset.to_csv(f"{project_path}/{clean_name}_{dataset_name}.csv", index=False)

# save the tvl dataset at the passed protocol 
def save_tvl_dataset(data_path: str, dataset_label: str, service_account_path: str, use_streamlit_secrets: bool, protocol: str) -> None:
    from queries.defillama import query_tvl_data_from_bq
    
    # connect to the bigquery client
    client = connect_bq_client(service_account_path=service_account_path, use_streamlit_secrets=use_streamlit_secrets)

    # query the tvl data from bigquery
    chain_tvls_df, tvl_df, tokens_in_usd_df, tokens_df = query_tvl_data_from_bq(client=client, protocol=protocol)

    # save the datasets
    chain_tvls_df.to_csv(f"{data_path}{dataset_label}_chain_tvls.csv", index=False)
    tvl_df.to_csv(f"{data_path}{dataset_label}_tvl.csv", index=False)
    tokens_in_usd_df.to_csv(f"{data_path}{dataset_label}_tokens_in_usd.csv", index=False)