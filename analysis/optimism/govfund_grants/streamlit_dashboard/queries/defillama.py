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
            current_chain_tvls,
            raises,
            metrics
        from `{BIGQUERY_PROJECT_NAME}.defillama_tvl.{protocol}`
    """

    # execute the query
    protocol_result = client.query(sql_query)
    protocol_df = protocol_result.to_dataframe()

    return protocol_df

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