import warnings
warnings.filterwarnings("ignore")

from utils import connect_bq_client
from config import STORED_DATA_PATH, SERVICE_ACCOUNT_PATH
from queries.defillama import query_tvl_data_from_bq

client = connect_bq_client(service_account_path=SERVICE_ACCOUNT_PATH)
_, tvl_df, _, _ = query_tvl_data_from_bq(client, ["optimism_bridge_protocol"])

tvl_df.drop(['date','protocol'], axis=1, inplace=True)

tvl_df.to_csv(f"{STORED_DATA_PATH}optimism_bridge_tvl2.csv", index=False)