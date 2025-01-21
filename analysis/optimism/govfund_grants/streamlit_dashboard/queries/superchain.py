from google.cloud import bigquery
import pandas as pd
from datetime import datetime

from config import BIGQUERY_PROJECT_NAME
from processing import make_dates_df, generate_dates

# query the daily transaction data of the project addresses over the interval and store it in a dataframe
def query_daily_transactions_superchain(client: bigquery.Client, dates_df: pd.DataFrame, start_date: str, token_conversion: int, chain: str) -> pd.DataFrame:
    try:
        # query for transaction count, active users, and total transferred, for each address
        daily_transactions_query = f"""
            SELECT 
                CAST(TIMESTAMP_TRUNC(block_timestamp, DAY) AS DATETIME) AS transaction_date,
                COUNT(*) AS transaction_cnt,
                COUNT(DISTINCT from_address) AS active_users,
                SUM(TO_CODE_POINTS(value)[OFFSET(0)] << 0) AS total_transferred
            FROM `{BIGQUERY_PROJECT_NAME}.superchain.{chain}_transactions` 
            WHERE TIMESTAMP_TRUNC(block_timestamp, DAY) >= '{start_date}'
            GROUP BY transaction_date
            ORDER BY transaction_date;
        """

        # query for the amount of new unique users for each address each day
        daily_transactions_unique_users_query = f"""
            WITH firstseen AS (
                SELECT
                    address,
                    MIN(CAST(TIMESTAMP_TRUNC(block_timestamp, DAY) AS DATETIME)) AS first_seen_date
                FROM (
                    SELECT
                        to_address AS address,
                        block_timestamp
                    FROM `{BIGQUERY_PROJECT_NAME}.superchain.{chain}_transactions`
                    WHERE TIMESTAMP_TRUNC(block_timestamp, DAY) >= '{start_date}'

                    UNION ALL

                    SELECT
                        from_address AS address,
                        block_timestamp
                    FROM `{BIGQUERY_PROJECT_NAME}.superchain.{chain}_transactions`
                    WHERE TIMESTAMP_TRUNC(block_timestamp, DAY) >= '{start_date}'
                )
                GROUP BY address
            ),
            daily_unique_users AS (
                SELECT
                    first_seen_date AS transaction_date,
                    COUNT(address) AS daily_new_users
                FROM firstseen
                GROUP BY first_seen_date
            )
            SELECT 
                transaction_date,
                COALESCE(daily_new_users, 0) AS unique_users
            FROM daily_unique_users
            ORDER BY transaction_date;"""

        # execute the queries
        daily_transactions_result = client.query(daily_transactions_query)
        daily_transactions_df = daily_transactions_result.to_dataframe()

        daily_transactions_unique_users_result = client.query(daily_transactions_unique_users_query)
        daily_transactions_unique_users_df = daily_transactions_unique_users_result.to_dataframe()

        daily_transactions_df['transaction_date'] = pd.to_datetime(daily_transactions_df['transaction_date'])
        daily_transactions_unique_users_df['transaction_date'] = pd.to_datetime(daily_transactions_unique_users_df['transaction_date'])
        dates_df['transaction_date'] = pd.to_datetime(dates_df['transaction_date'])

        # merge results
        daily_transactions_df = pd.merge(
            daily_transactions_df,
            daily_transactions_unique_users_df,
            how='outer',
            on='transaction_date'
        )

        # merge with dates_df to ensure all dates are included
        daily_transactions_merged_df = pd.merge(
            daily_transactions_df,
            dates_df,
            how='outer',
            on='transaction_date'
        )

        # fill missing numeric values with 0, but leave other columns (e.g., transaction_date) unchanged
        numeric_columns = ['transaction_cnt', 'active_users', 'unique_users', 'total_transferred']
        daily_transactions_merged_df[numeric_columns] = daily_transactions_merged_df[numeric_columns].fillna(0).astype(int)

        # remove duplicated rows
        daily_transactions_merged_df = daily_transactions_merged_df.drop_duplicates(subset=['transaction_date']).reset_index(drop=True)

        # add a column for the total transferred represented in tokens
        daily_transactions_merged_df['total_transferred_in_tokens'] = daily_transactions_merged_df['total_transferred'] / token_conversion
        # add a column for the cumulative total transferred (by address)
        daily_transactions_merged_df['cum_transferred'] = (daily_transactions_merged_df['total_transferred'].cumsum())

        return daily_transactions_merged_df

    except Exception as e:
        raise RuntimeError(f"Failed to query daily transactions: {e}")
    
# connect to bigquery and query all necessary data for the passed project
def query_transaction_data_from_bq_superchain(client: bigquery.Client, grant_date: str, token_conversion: str, chain: str) -> pd.DataFrame:

    # create a pre-grant date range equal to the post-grant date length
    time_since_interval = datetime.today() - grant_date
    min_start = grant_date - time_since_interval
    min_start_string = min_start.strftime('%Y-%m-%d')

    # create a templated dataframe of each pair (dates, address) from the minimum start date
    dates = generate_dates(target_date=min_start)
    dates_df = make_dates_df(dates=dates, project_addresses=None)

    # query daily transactions data from bigquery
    daily_transactions = query_daily_transactions_superchain(client=client, dates_df=dates_df, start_date=min_start_string, token_conversion=token_conversion, chain=chain)
    
    return daily_transactions
