from datetime import datetime, timedelta, timezone
import pandas as pd
from typing import List, Tuple, Optional
import json

from utils import determine_date_col

# create a list of all dates from now to the start date
def generate_dates(target_date: datetime) -> List[str]:
    dates = []
    todays_date = datetime.now()
    date_interval = (todays_date - target_date).days
    for i in range(date_interval):
        date = target_date + timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))

    return dates

# create a dataframe with a row for each date and address combination
def make_dates_df(dates: List[str], project_addresses: Optional[Tuple[str, ...]] = None) -> pd.DataFrame:
    data = []
    
    if project_addresses:  # if addresses are provided, generate rows for each address and date
        for address in project_addresses:
            for date in dates:
                data.append({'transaction_date': date, 'address': address})
    else:  # if no addresses are provided, generate rows for each date only
        for date in dates:
            data.append({'transaction_date': date, 'address': None})  # use None or an empty string for the address

    return pd.DataFrame(data)


# create a dataset that represents net transactions by factoring in transaction direction
def make_net_transaction_dataset(transaction_flow_df: pd.DataFrame) -> pd.DataFrame:

    # prepare cumulative transaction data
    transaction_direction_df = pd.concat([
        transaction_flow_df[['transaction_date', 'from_address', 'direction', 'cnt', 'total_transferred', 'total_transferred_in_tokens']]
        .rename(columns={'from_address': 'address'}),
        transaction_flow_df[['transaction_date', 'to_address', 'direction', 'cnt', 'total_transferred', 'total_transferred_in_tokens']]
        .rename(columns={'to_address': 'address'})
    ])

    # aggregate and calculate cumulative sum
    transaction_direction_df.drop_duplicates(inplace=True)
    transaction_direction_df = transaction_direction_df.groupby(['transaction_date', 'address', 'direction'], as_index=False).agg({
        'cnt': 'sum',
        'total_transferred': 'sum',
        'total_transferred_in_tokens': 'sum'
    })

    # convert outbound transactions to negative
    transaction_direction_df.loc[transaction_direction_df['direction'] == 'out', 'total_transferred'] *= -1
    transaction_direction_df.loc[transaction_direction_df['direction'] == 'out', 'total_transferred_in_tokens'] *= -1

    # ensure the data is sorted correctly
    transaction_direction_df.sort_values(by=['address', 'transaction_date'], inplace=True)
    # calculate the net transferred over time
    transaction_direction_df['net_transferred'] = transaction_direction_df.groupby('address')['total_transferred'].cumsum()
    transaction_direction_df['net_transferred_in_tokens'] = transaction_direction_df.groupby('address')['total_transferred_in_tokens'].cumsum()

    return transaction_direction_df

# create a dataframe for TVL data by chain
def chain_tvls_col_to_df(df: pd.DataFrame) -> pd.DataFrame:
    try:
        # grab the data from the respective column
        chain_tvls = pd.DataFrame(json.loads(df.iloc[0, 1]))

        # helper function to unroll the dictionary
        def normalize_chain_data(chain_name, chain_data):
            if not chain_data:  # check if chain_data is None or empty
                return pd.DataFrame()  # return an empty dataframe
            
            records = []
            for entry in chain_data:
                date = entry["date"]
                for token, value in entry.get("tokens", {}).items():
                    records.append({"chain": chain_name, "date": date, "token": token, "value": value})
            return pd.DataFrame(records)

        all_chains_data = []
        for chain in chain_tvls.columns:
            chain_data = chain_tvls[chain].iloc[0]
            if chain_data is None:  # skip if chain_data is None
                print(f"Skipping chain: {chain} due to missing data.")
                continue
            normalized_data = normalize_chain_data(chain_name=chain, chain_data=chain_data)
            all_chains_data.append(normalized_data)

        if not all_chains_data:  # if no valid data is found
            return pd.DataFrame()  # return an empty dataframe

        # concatenate all chain dataframes
        cleaned_df = pd.concat(all_chains_data, ignore_index=True)

        # create a new column of a readable date
        cleaned_df['readable_date'] = cleaned_df['date'].apply(
            lambda x: datetime.fromtimestamp(x, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        )
        cleaned_df['readable_date'] = pd.to_datetime(cleaned_df['readable_date'])

        return cleaned_df
    except Exception as e:
        print(f"Error processing chain TVLs: {e}")
        return pd.DataFrame()  # return an empty DataFrame if there's an error

# Create a dataframe for aggregate TVL data
def tvl_col_to_df(df: pd.DataFrame) -> pd.DataFrame:
    try:
        # Extract TVL data from its respective column
        tvl_data = json.loads(df.iloc[0, 2])
        tvl_df = pd.DataFrame(tvl_data)
        
        if tvl_df.empty:
            print("TVL data is empty or malformed. Skipping processing.")
            return pd.DataFrame()  # Return an empty DataFrame

        # Create a new column of a readable date
        tvl_df['readable_date'] = tvl_df['date'].apply(
            lambda x: datetime.fromtimestamp(x, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        )
        tvl_df['readable_date'] = pd.to_datetime(tvl_df['readable_date'])

        return tvl_df
    except Exception as e:
        print(f"Error processing TVL data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame if there's an error

# create a dataframe for token data (in USD)
def tokens_in_usd_col_to_df(df: pd.DataFrame) -> pd.DataFrame:
    try:
        # extract tokens_in_usd data from the column
        tokens_data = json.loads(df.iloc[0, 3])
        tokens_df = pd.DataFrame(tokens_data)

        if tokens_df.empty:
            print("Tokens in USD data is empty or malformed. Skipping processing.")
            return pd.DataFrame()  # Return an empty DataFrame

        # flatten the tokens dictionary for each date
        records = []
        for _, row in tokens_df.iterrows():
            date = row["date"]
            tokens = row.get("tokens", {})
            for token, value in tokens.items():
                records.append({"date": date, "token": token, "value": value})

        if not records:
            return pd.DataFrame()
        
        flattened_tokens_df = pd.DataFrame(records)

        # create a new column of a readable date
        flattened_tokens_df['readable_date'] = flattened_tokens_df['date'].apply(
            lambda x: datetime.fromtimestamp(x, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        )
        flattened_tokens_df['readable_date'] = pd.to_datetime(flattened_tokens_df['readable_date'])

        return flattened_tokens_df
    except Exception as e:
        print(f"Error processing tokens in USD data: {e}")
        return pd.DataFrame()  # return an empty dataframe if there's an error

# create a dataframe for token data
def tokens_col_to_df(df: pd.DataFrame) -> pd.DataFrame:
    try:
        # extract tokens data from the column
        tokens_data = json.loads(df.iloc[0, 4])
        tokens_df = pd.DataFrame(tokens_data)

        if tokens_df.empty:
            print("Tokens data is empty or malformed. Skipping processing.")
            return pd.DataFrame()  # return an empty DataFrame

        # flatten the tokens dictionary for each date
        records = []
        for _, row in tokens_df.iterrows():
            date = row["date"]
            tokens = row.get("tokens", {})
            for token, value in tokens.items():
                records.append({"date": date, "token": token, "value": value})

        if not records:
            return pd.DataFrame()
        
        flattened_tokens_df = pd.DataFrame(records)

        # create a new column of a readable date
        flattened_tokens_df['readable_date'] = flattened_tokens_df['date'].apply(
            lambda x: datetime.fromtimestamp(x, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        )
        flattened_tokens_df['readable_date'] = pd.to_datetime(flattened_tokens_df['readable_date'])

        return flattened_tokens_df
    except Exception as e:
        print(f"Error processing tokens data: {e}")
        return pd.DataFrame()  # return an empty DataFrame if there's an error

# splits a dataset into pre- and post-grant dataframes based on the grant date
def split_dataset_by_date(dataset: pd.DataFrame, grant_date: datetime) -> tuple[pd.DataFrame, pd.DataFrame]:
    # identifies the date column based on the dataset
    date_col = determine_date_col(df=dataset)

    # ensures the date column is in datetime format
    dataset[date_col] = pd.to_datetime(dataset[date_col])

    # calculates the minimum date and the range of time since the grant
    min_date = dataset[date_col].min()
    time_since_grant = datetime.today() - grant_date

    # calculates the start date for the pre-grant dataset
    pre_grant_start_date = grant_date - time_since_grant

    # adjusts the start date to ensure it does not precede the dataset's minimum date
    pre_grant_start_date = max(pre_grant_start_date, min_date)

    # creates separate dataframes for pre- and post-grant data
    pre_grant_df = dataset[(dataset[date_col] < grant_date) & (dataset[date_col] >= pre_grant_start_date)]
    post_grant_df = dataset[dataset[date_col] >= grant_date]

    return pre_grant_df, post_grant_df