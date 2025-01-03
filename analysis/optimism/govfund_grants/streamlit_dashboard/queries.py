from google.cloud import bigquery
import pandas as pd
from typing import Tuple, Any

from config import BIGQUERY_PROJECT_NAME, PROJECT_NETWORK, GRANT_DATE_STR, TOKEN_CONVERSION
from utils import get_project_min_date, get_addresses_condition, get_project_network_condition
from processing import make_dates_df, generate_dates, tvl_col_to_df, chain_tvls_col_to_df, tokens_col_to_df, tokens_in_usd_col_to_df

# query the daily transaction data of the project addresses over the interval and store it in a dataframe
def query_daily_transactions(client: bigquery.Client, project_addresses: Tuple[str, ...], dates_df: pd.DataFrame, start_date: str = GRANT_DATE_STR) -> pd.DataFrame:
    try:
       # handle single or multiple addresses in the query
        addresses_condition = get_addresses_condition(project_addresses=project_addresses)
        # handle single or multiple project networks
        project_network_condition = get_project_network_condition(project_network=PROJECT_NETWORK)

        # query for transaction count, active users, and total op transferred, for each address
        daily_transactions_query = f"""
            SELECT 
                dt AS transaction_date,
                to_address AS address,
                COUNT(*) AS transaction_cnt,
                COUNT(DISTINCT from_address) AS active_users,
                SUM(value_64) AS total_op_transferred
            FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions` 
            WHERE to_address {addresses_condition}
                AND network '{project_network_condition}'
                AND dt >= '{start_date}'
            GROUP BY dt, to_address
            ORDER BY dt, to_address"""

        # query for the amount of new unique users for each address each day
        daily_transactions_unique_users_query = f"""
            WITH firstseen AS (
                SELECT
                    to_address,
                    from_address,
                    MIN(dt) transaction_date
                FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions`
                WHERE to_address {addresses_condition}
                    AND network = '{PROJECT_NETWORK}'
                    AND dt >= '{start_date}'
                GROUP BY to_address, from_address
            ), cum_sum_count AS (
                SELECT
                    transaction_date,
                    to_address,
                    COUNT(from_address) OVER (PARTITION BY to_address ORDER BY transaction_date) AS daily_cumulative_count
                FROM firstseen
            )
            SELECT 
                transaction_date,
                to_address AS address,
                daily_cumulative_count - COALESCE(LAG(daily_cumulative_count) OVER (PARTITION BY to_address ORDER BY transaction_date), 0) AS unique_users
            FROM cum_sum_count
            ORDER BY transaction_date"""

        # execute the queries
        daily_transactions_result = client.query(daily_transactions_query)
        daily_transactions_df = daily_transactions_result.to_dataframe()

        daily_transactions_unique_users_result = client.query(daily_transactions_unique_users_query)
        daily_transactions_unique_users_df = daily_transactions_unique_users_result.to_dataframe()

        # merge results
        daily_transactions_df = pd.merge(
            daily_transactions_df,
            daily_transactions_unique_users_df,
            how='outer',
            on=['transaction_date', 'address']
        )

        # merge with dates_df to ensure all dates are included
        daily_transactions_merged_df = pd.merge(
            daily_transactions_df,
            dates_df,
            how='outer',
            on=['transaction_date', 'address']
        )

        # fill missing numeric values with 0, but leave other columns (e.g., transaction_date) unchanged
        numeric_columns = ['transaction_cnt', 'active_users', 'unique_users', 'total_op_transferred']
        daily_transactions_merged_df[numeric_columns] = daily_transactions_merged_df[numeric_columns].fillna(0).astype(int)

        # remove duplicated rows
        daily_transactions_merged_df = daily_transactions_merged_df.drop_duplicates(subset=['transaction_date', 'address']).reset_index(drop=True)

        # add a column for the total op transferred represented in tokens
        daily_transactions_merged_df['total_op_transferred_in_tokens'] = daily_transactions_merged_df['total_op_transferred'] / TOKEN_CONVERSION
        # add a column for the cumulative total op transferred (by address)
        daily_transactions_merged_df['cum_op_transferred'] = (daily_transactions_merged_df.groupby('address')['total_op_transferred'].cumsum())

        return daily_transactions_merged_df

    except Exception as e:
        raise RuntimeError(f"Failed to query daily transactions: {e}")

# create a table of all transactions (in and out) involving one of the project addresses over the interval
def query_op_flow(client: bigquery.Client, project_addresses: Tuple[str, ...], start_date: str = GRANT_DATE_STR) -> pd.DataFrame:
    try:
        # handle single or multiple addresses in the query
        addresses_condition = get_addresses_condition(project_addresses=project_addresses)
        # handle single or multiple project networks
        project_network_condition = get_project_network_condition(project_network=PROJECT_NETWORK)

        # query the amount of op transferred in and out of the relevant addresses
        op_flow_query = f"""
        (SELECT 
            dt AS transaction_date,
            from_address,
            to_address,
            COUNT(*) AS cnt,
            SUM(value_64) AS total_op_transferred,
            'in' AS direction
        FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions`
        WHERE network '{project_network_condition}'
            AND to_address {addresses_condition}
            AND dt >= '{start_date}'
        GROUP BY dt, from_address, to_address
        ORDER BY 3 DESC)

        UNION ALL 

        (SELECT 
            dt AS transaction_date,
            from_address,
            to_address,
            COUNT(*) AS cnt,
            SUM(value_64) AS total_op_transferred,
            'out' AS direction
        FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions`
        WHERE network '{project_network_condition}'
            AND from_address {addresses_condition}
            AND dt >= '{start_date}'
        GROUP BY dt, from_address, to_address
        ORDER BY 3 DESC)"""

        # execute the query
        op_flow_result = client.query(op_flow_query)
        op_flow_df = op_flow_result.to_dataframe()

        # add a column for the total op transferred represented in tokens
        op_flow_df['total_op_transferred_in_tokens'] = op_flow_df['total_op_transferred'] / TOKEN_CONVERSION

        return op_flow_df

    except Exception as e:
        raise RuntimeError(f"Failed to query op flow: {e}")
    
# queries the minimum transaction date for a given set of project addresses and start date
def query_transactions_min_date(client: bigquery.Client, project_addresses: list[str], start_date: str) -> pd.Timestamp | None:
    try:
        # handles both single and multiple project addresses
        addresses_condition = get_addresses_condition(project_addresses=project_addresses)
        # handle single or multiple project networks
        project_network_condition = get_project_network_condition(project_network=PROJECT_NETWORK)

        # sql query to fetch the minimum transaction date from the bigquery table
        min_date_query = f"""
        SELECT MIN(dt) AS transaction_date
        FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions`
        WHERE network '{project_network_condition}'
            AND (to_address {addresses_condition}
            OR from_address {addresses_condition})
            AND dt >= '{start_date}'
        """

        # executes the query
        min_date_result = client.query(min_date_query)
        min_date_df = min_date_result.to_dataframe()

        # checks if the result is not empty and parses the transaction date
        if not min_date_df.empty and min_date_df.loc[0, 'transaction_date']:
            return pd.to_datetime(min_date_df.loc[0, 'transaction_date'])

    except Exception as e:
        print(f"Error querying minimum transaction date: {e}")

    # returns None if the query fails
    return None

# query protocol data from bigquery
def query_tvl(client: bigquery.Client, protocol: str) -> pd.DataFrame:
    sql_query = f"""
        select
            name,
            chain_tvls,
            tvl,
            tokens_in_usd,
            tokens,
            current_chain_tvls,
            raises,
            metrics
        from `{BIGQUERY_PROJECT_NAME}.defillama_tvl.{protocol}`
    """

    # execute the query
    protocol_result = client.query(sql_query)
    protocol_df = protocol_result.to_dataframe()

    return protocol_df

# connect to bigquery and query all necessary data for the passed project
def query_transaction_data_from_bq(client, project_addresses):

    # get the minimum transaction date associated with the project
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

# take in a bigquery client and target protocol and return it's tvl data
def query_tvl_data_from_bq(client: bigquery.Client, protocol: Any) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    # query the tvl dataset
    protocol_df = query_tvl(client=client, protocol=protocol)

    # the tvl data is stored by column, so each of the following functions unravel the relevant columns into it's respective dataset
    chain_tvls_df = chain_tvls_col_to_df(df=protocol_df)
    tvl_df = tvl_col_to_df(df=protocol_df)
    tokens_in_usd_df = tokens_in_usd_col_to_df(df=protocol_df)
    tokens_df = tokens_col_to_df(df=protocol_df)

    return chain_tvls_df, tvl_df, tokens_in_usd_df, tokens_df