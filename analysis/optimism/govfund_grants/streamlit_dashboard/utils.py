from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account
import streamlit as st
import pandas as pd
import json
from typing import List, Dict, Tuple, Union, Optional, Callable, Any

from config import GRANT_DATE
from queries import query_transactions_min_date, query_daily_transactions, query_op_flow, query_tvl
from processing import make_dates_df, generate_dates, tvl_col_to_df, chain_tvls_col_to_df, tokens_col_to_df, tokens_in_usd_col_to_df

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
def get_project_min_date(client, project_addresses):
    # create a pre-grant date range equal to the post-grant date length
    time_since_interval = datetime.today() - GRANT_DATE
    min_start = GRANT_DATE - time_since_interval
    min_start_string = min_start.strftime('%Y-%m-%d')

    # determine the minimum date of a transaction from the dataset
    transactions_min_date = query_transactions_min_date(client=client, project_addresses=project_addresses, start_date=min_start_string)

    # ensure transactions_min_date is valid before comparison
    if transactions_min_date is not None:
        # determine the minimum start date we can use
        min_start = max(transactions_min_date, min_start)

    return min_start

# get all of the addresses relevant to the target project
def extract_addresses(project_dict: Dict[str, List[Dict[str, Dict[str, Union[str, int]]]]]) -> Tuple[str, ...]:
    project_address_dict = project_dict['addresses']

    project_addresses = []
    for address in project_address_dict:
        project_addresses.extend(list(address.keys()))
    
    return tuple(set(project_addresses))

# read in a dictionary of projects mapped to their respective protocols
def read_in_defi_llama_protocols(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        defi_llama_protocols = json.load(f)

    return defi_llama_protocols

# search for the target project and return the corresponding protocol
def return_protocol(defi_llama_protocols: Dict[str, Any], project: str) -> Optional[Any]:
    return defi_llama_protocols.get(project, None)

# connect to the bigquery client to begin querying
def connect_bq_client(service_account_path=None, use_streamlit_secrets=False):
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

# connect to bigquery and query all necessary data for the passed project
def query_transaction_data_from_bq(client, project_addresses):

    min_start = get_project_min_date(client=client, project_addresses=project_addresses)
    min_start_string = min_start.strftime('%Y-%m-%d')

    # create a templated dataframe of each pair (dates, address) from the minimum start date
    dates = generate_dates(target_date=min_start)
    dates_df = make_dates_df(dates=dates, project_addresses=project_addresses)

    # query daily transactions data from bigquery
    daily_transactions = query_daily_transactions(client=client,project_addresses=project_addresses, dates_df=dates_df, start_date=min_start_string)
    
    # query op flow data from bigquery
    op_flow = query_op_flow(client=client, project_addresses=project_addresses, start_date=min_start_string)
    
    return daily_transactions, op_flow

# read in already stored datasets at the respective path
def read_in_stored_dfs_for_projects(project, data_path, protocol):
    project_name = project['project_name']
    clean_name = project_name.lower().replace(" ", "_").replace(".", "-")

    # Initialize everything to None
    daily_transactions = None
    net_op_flow = None
    chain_tvls_df = None
    tvl_df = None
    tokens_in_usd_df = None
    forecasted_df = None

    # read in daily transactions dataset
    try:
        daily_transactions = pd.read_csv(f"{data_path}{clean_name}_daily_transactions.csv")
    except Exception:
        pass

    # read in net op flow dataset
    try:
        net_op_flow = pd.read_csv(f"{data_path}{clean_name}_net_op_flow.csv")
    except Exception:
        pass

    # read in TVL datasets if protocol is provided
    if protocol is not None:
        try:
            chain_tvls_df = pd.read_csv(f"{data_path}{clean_name}_chain_tvls_df.csv")
        except Exception:
            pass

        try:
            tvl_df = pd.read_csv(f"{data_path}{clean_name}_tvl_df.csv")
        except Exception:
            pass

        try:
            tokens_in_usd_df = pd.read_csv(f"{data_path}{clean_name}_tokens_in_usd_df.csv")
        except Exception:
            pass

    # read in the forecasted dataset 
    try:
        forecasted_df = pd.read_csv(f"{data_path}{clean_name}_forecasted_metrics.csv")
    except Exception:
        pass

    # Return a dict with each key = DataFrame or None
    return {
        "daily_transactions": daily_transactions,
        "net_op_flow": net_op_flow,
        "forecasted" : forecasted_df,
        "chain_tvls" : chain_tvls_df,
        "tvl": tvl_df,
        "tokens_in_usd": tokens_in_usd_df
    }

# take in a bigquery client and target protocol and return it's tvl data
def query_tvl_data_from_bq(client, protocol: Any) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    protocol_df = query_tvl(client, protocol)

    chain_tvls_df = chain_tvls_col_to_df(protocol_df)
    tvl_df = tvl_col_to_df(protocol_df)
    tokens_in_usd_df = tokens_in_usd_col_to_df(protocol_df)
    tokens_df = tokens_col_to_df(protocol_df)

    return chain_tvls_df, tvl_df, tokens_in_usd_df, tokens_df

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
def assign_grant_label(row: Any) -> str:
    if 'transaction_date' in row and pd.notnull(row['transaction_date']):
        date_col = 'transaction_date'
    elif 'readable_date' in row and pd.notnull(row['readable_date']):
        date_col = 'readable_date'
    elif 'date' in row and pd.notnull(row['date']):
        date_col = 'date'
    else:
        raise ValueError("None of the expected date columns ('transaction_date', 'readable_date', 'date') are available in the row.")

    # compare the row's date with GRANT_DATE
    if pd.to_datetime(row[date_col]) < pd.to_datetime(GRANT_DATE):
        return 'pre grant'
    else:
        return 'post grant'