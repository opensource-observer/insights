from google.cloud import bigquery
import pandas as pd
from typing import List, Dict, Tuple

from config import BIGQUERY_PROJECT_NAME, PROJECT_NETWORK, GRANT_DATE_STR, TOKEN_CONVERSION

# query the daily transaction data of the project addresses over the interval and store it in a dataframe
def query_daily_transactions(client: bigquery.Client, project_addresses: Tuple[str, ...], dates_df: pd.DataFrame, start_date: str = GRANT_DATE_STR) -> pd.DataFrame:
    try:
        # handle single or multiple addresses in the query
        if len(project_addresses) == 1:
            addresses_condition = f"= '{project_addresses[0]}'"
        else:
            addresses_condition = f"IN {tuple(project_addresses)}"

        daily_transactions_query = f"""
            SELECT 
                dt AS transaction_date,
                to_address AS address,
                COUNT(*) AS transaction_cnt,
                COUNT(DISTINCT from_address) AS active_users,
                SUM(value_64) AS total_op_transferred
            FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions` 
            WHERE to_address {addresses_condition}
                AND network = '{PROJECT_NETWORK}'
                AND dt >= '{start_date}'
            GROUP BY dt, to_address
            ORDER BY dt, to_address"""

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

        # Execute the queries
        daily_transactions_result = client.query(daily_transactions_query)
        daily_transactions_df = daily_transactions_result.to_dataframe()

        daily_transactions_unique_users_result = client.query(daily_transactions_unique_users_query)
        daily_transactions_unique_users_df = daily_transactions_unique_users_result.to_dataframe()

        # Merge results
        daily_transactions_df = pd.merge(
            daily_transactions_df,
            daily_transactions_unique_users_df,
            how='outer',
            on=['transaction_date', 'address']
        )

        # Merge with dates_df to ensure all dates are included
        daily_transactions_merged_df = pd.merge(
            daily_transactions_df,
            dates_df,
            how='outer',
            on=['transaction_date', 'address']
        )

        # Fill missing numeric values with 0, but leave other columns (e.g., transaction_date) unchanged
        NUMERIC_COLS = ['transaction_cnt', 'active_users', 'unique_users', 'total_op_transferred']
        daily_transactions_merged_df[NUMERIC_COLS] = daily_transactions_merged_df[NUMERIC_COLS].fillna(0).astype(int)

        daily_transactions_merged_df = daily_transactions_merged_df.drop_duplicates(subset=['transaction_date', 'address']).reset_index(drop=True)

        daily_transactions_merged_df['total_op_transferred_in_tokens'] = daily_transactions_merged_df['total_op_transferred'] / TOKEN_CONVERSION
        daily_transactions_merged_df['cum_op_transferred'] = (daily_transactions_merged_df.groupby('address')['total_op_transferred'].cumsum())

        return daily_transactions_merged_df

    except Exception as e:
        raise RuntimeError(f"Failed to query daily transactions: {e}")

# create a table of all transactions (in and out) involving one of the project addresses over the interval
def query_op_flow(client: bigquery.Client, project_addresses: Tuple[str, ...], start_date: str = GRANT_DATE_STR) -> pd.DataFrame:
    try:
        # handle single or multiple addresses in the query
        if len(project_addresses) == 1:
            addresses_condition = f"= '{project_addresses[0]}'"
        else:
            addresses_condition = f"IN {tuple(project_addresses)}"

        op_flow_query = f"""
        (SELECT 
            dt AS transaction_date,
            from_address,
            to_address,
            COUNT(*) AS cnt,
            SUM(value_64) AS total_op_transferred
        FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions`
        WHERE network = '{PROJECT_NETWORK}'
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
            SUM(value_64) AS total_op_transferred
        FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions`
        WHERE network = '{PROJECT_NETWORK}'
            AND from_address {addresses_condition}
            AND dt >= '{start_date}'
        GROUP BY dt, from_address, to_address
        ORDER BY 3 DESC)"""

        op_flow_result = client.query(op_flow_query)
        op_flow_df = op_flow_result.to_dataframe()

        op_flow_df['total_op_transferred_in_tokens'] = op_flow_df['total_op_transferred'] / TOKEN_CONVERSION

        return op_flow_df

    except Exception as e:
        raise RuntimeError(f"Failed to query op flow: {e}")
    
# queries the minimum transaction date for a given set of project addresses and start date
def query_transactions_min_date(client: bigquery.Client, project_addresses: list[str], start_date: str) -> pd.Timestamp | None:
    try:
        # handles both single and multiple project addresses
        if len(project_addresses) == 1:
            addresses_condition = f"= '{project_addresses[0]}'"
        else:
            addresses_condition = f"IN {tuple(project_addresses)}"

        # sql query to fetch the minimum transaction date from the bigquery table
        min_date_query = f"""
        SELECT MIN(dt) AS transaction_date
        FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions`
        WHERE network = '{PROJECT_NETWORK}'
            AND (to_address {addresses_condition}
            OR from_address {addresses_condition})
            AND dt >= '{start_date}'
        """

        # executes the query and converts the result to a dataframe
        min_date_result = client.query(min_date_query)
        min_date_df = min_date_result.to_dataframe()

        # checks if the result is not empty and parses the transaction date
        if not min_date_df.empty and min_date_df.loc[0, 'transaction_date']:
            return pd.to_datetime(min_date_df.loc[0, 'transaction_date'])

    except Exception as e:
        # logs any errors that occur during the query
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

    protocol_result = client.query(sql_query)
    protocol_df = protocol_result.to_dataframe()

    return protocol_df