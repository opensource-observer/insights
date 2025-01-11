from google.cloud import bigquery
import pandas as pd
from typing import Tuple

from config import BIGQUERY_PROJECT_NAME
from utils import get_project_min_date_optimism, get_addresses_condition
from processing import make_dates_df, generate_dates

# query the daily transaction data of the project addresses over the interval and store it in a dataframe
def query_daily_transactions_optimism(client: bigquery.Client, project_addresses: Tuple[str, ...], dates_df: pd.DataFrame, start_date: str, token_conversion: int) -> pd.DataFrame:
    try:
       # handle single or multiple addresses in the query
        addresses_condition = get_addresses_condition(project_addresses=project_addresses)

        # query for transaction count, active users, and total transferred, for each address
        daily_transactions_query = f"""
            SELECT 
                dt AS transaction_date,
                to_address AS address,
                COUNT(*) AS transaction_cnt,
                COUNT(DISTINCT from_address) AS active_users,
                SUM(value_64) AS total_transferred
            FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions` 
            WHERE to_address {addresses_condition}
                AND network = 'mainnet'
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
                    AND network = 'mainnet'
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
        numeric_columns = ['transaction_cnt', 'active_users', 'unique_users', 'total_transferred']
        daily_transactions_merged_df[numeric_columns] = daily_transactions_merged_df[numeric_columns].fillna(0).astype(int)

        # remove duplicated rows
        daily_transactions_merged_df = daily_transactions_merged_df.drop_duplicates(subset=['transaction_date', 'address']).reset_index(drop=True)

        # add a column for the total transferred represented in tokens
        daily_transactions_merged_df['total_transferred_in_tokens'] = daily_transactions_merged_df['total_transferred'] / token_conversion
        # add a column for the cumulative total transferred (by address)
        daily_transactions_merged_df['cum_transferred'] = (daily_transactions_merged_df.groupby('address')['total_transferred'].cumsum())

        return daily_transactions_merged_df

    except Exception as e:
        raise RuntimeError(f"Failed to query daily transactions: {e}")

# create a table of all transactions (in and out) involving one of the project addresses over the interval
def query_transaction_flow_optimism(client: bigquery.Client, project_addresses: Tuple[str, ...], start_date: str, token_conversion: str) -> pd.DataFrame:
    try:
        # handle single or multiple addresses in the query
        addresses_condition = get_addresses_condition(project_addresses=project_addresses)

        # query the amount of op transferred in and out of the relevant addresses
        transaction_flow_query = f"""
        SELECT 
            dt AS transaction_date,
            from_address,
            to_address,
            COUNT(*) AS cnt,
            SUM(value_64) AS total_transferred,
            'in' AS direction
        FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions`
        WHERE network = 'mainnet'
            AND to_address {addresses_condition}
            AND dt >= '{start_date}'
        GROUP BY dt, from_address, to_address
        ORDER BY 3 DESC

        UNION ALL 

        SELECT 
            dt AS transaction_date,
            from_address,
            to_address,
            COUNT(*) AS cnt,
            SUM(value_64) AS total_transferred,
            'out' AS direction
        FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions`
        WHERE network = 'mainnet'
            AND from_address {addresses_condition}
            AND dt >= '{start_date}'
        GROUP BY dt, from_address, to_address
        ORDER BY 3 DESC"""

        # execute the query
        transaction_flow_result = client.query(transaction_flow_query)
        transaction_flow_df = transaction_flow_result.to_dataframe()

        # add a column for the total transferred represented in tokens
        transaction_flow_df['total_transferred_in_tokens'] = transaction_flow_df['total_transferred'] / token_conversion

        return transaction_flow_df

    except Exception as e:
        raise RuntimeError(f"Failed to query op flow: {e}")
    
# queries the minimum transaction date for a given set of project addresses and start date
def query_transactions_min_date_optimism(client: bigquery.Client, project_addresses: list[str], start_date: str) -> pd.Timestamp | None:
    try:
        # handles both single and multiple project addresses
        addresses_condition = get_addresses_condition(project_addresses=project_addresses)

        # sql query to fetch the minimum transaction date from the bigquery table
        min_date_query = f"""
        SELECT MIN(dt) AS transaction_date
        FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions`
        WHERE network = 'mainnet'
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

# connect to bigquery and query all necessary data for the passed project
def query_transaction_data_from_bq_optimism(client: bigquery.Client, project_addresses: Tuple[str, ...], grant_date: str, token_conversion: str) -> Tuple[pd.DataFrame, pd.DataFrame]:

    # get the minimum transaction date associated with the project
    min_start = get_project_min_date_optimism(client=client, project_addresses=project_addresses, grant_date=grant_date)
    min_start_string = min_start.strftime('%Y-%m-%d')

    # create a templated dataframe of each pair (dates, address) from the minimum start date
    dates = generate_dates(target_date=min_start)
    dates_df = make_dates_df(dates=dates, project_addresses=project_addresses)

    # query daily transactions data from bigquery
    daily_transactions = query_daily_transactions_optimism(client=client,project_addresses=project_addresses, dates_df=dates_df, start_date=min_start_string, token_conversion=token_conversion)
    
    # query transaction flow data from bigquery
    transaction_flow = query_transaction_flow_optimism(client=client, project_addresses=project_addresses, start_date=min_start_string, token_conversion=token_conversion)
    
    return daily_transactions, transaction_flow
