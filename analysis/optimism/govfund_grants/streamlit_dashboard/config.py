from datetime import datetime
import streamlit as st

PULL_FROM_BIGQUERY = False
LIVE_STREAMLIT_INSTANCE = False

TOKEN_CONVERSION = 1E15

NUMERIC_COLS = ['transaction_cnt', 'active_users', 'unique_users', 'total_op_transferred']

GRANT_DATE = datetime(2024, 9, 1)
GRANT_DATE_STR = '2024-09-01'

PROJECT_NETWORK = 'mainnet'

BIGQUERY_PROJECT_NAME = 'oso-data-436717'

DEFI_LLAMA_PROTOCOLS_PATH = "defillama.json"
GRANTS_PATH = "temp_grants.json"
SERVICE_ACCOUNT_PATH = 'oso_gcp_credentials.json'
STORED_DATA_PATH = 'data/'