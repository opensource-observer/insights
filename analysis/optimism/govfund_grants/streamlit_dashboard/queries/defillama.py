from google.cloud import bigquery
import pandas as pd
from typing import Any, Tuple

from config import BIGQUERY_PROJECT_NAME
from processing import tvl_col_to_df, chain_tvls_col_to_df, tokens_col_to_df, tokens_in_usd_col_to_df

# query protocol data from bigquery
def query_tvl(client: bigquery.Client, protocol: str) -> pd.DataFrame:
    sql_query = f"""
        select
            name,
            chain_tvls,
            tvl,
            tokens_in_usd,
            tokens,
            current_chain_tvls
        from `{BIGQUERY_PROJECT_NAME}.defillama_tvl.{protocol}`
    """

    # execute the query
    protocol_result = client.query(sql_query)
    protocol_len = len(list(protocol_result.result()))

    if protocol_len > 0:
        protocol_df = protocol_result.to_dataframe()

        return protocol_df
    else:
        return None

# take in a bigquery client and target protocol and return its concatenated tvl data
def query_tvl_data_from_bq(client: bigquery.Client, protocols: Any) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # initialize empty lists to collect dataframes
    chain_tvls_list = []
    tvl_list = []
    tokens_in_usd_list = []
    tokens_list = []

    for protocol in protocols:
        # query the tvl dataset
        protocol_df = query_tvl(client=client, protocol=protocol)

        # unravel the relevant columns into their respective datasets
        chain_tvls_list.append(chain_tvls_col_to_df(df=protocol_df, protocol=protocol))
        tvl_list.append(tvl_col_to_df(df=protocol_df, protocol=protocol))
        tokens_in_usd_list.append(tokens_in_usd_col_to_df(df=protocol_df, protocol=protocol))
        tokens_list.append(tokens_col_to_df(df=protocol_df, protocol=protocol))

    # concatenate all the collected dataframes
    chain_tvls_df = pd.concat(chain_tvls_list, axis=0, ignore_index=True)
    tvl_df = pd.concat(tvl_list, axis=0, ignore_index=True)
    tokens_in_usd_df = pd.concat(tokens_in_usd_list, axis=0, ignore_index=True)
    tokens_df = pd.concat(tokens_list, axis=0, ignore_index=True)

    return chain_tvls_df, tvl_df, tokens_in_usd_df, tokens_df
