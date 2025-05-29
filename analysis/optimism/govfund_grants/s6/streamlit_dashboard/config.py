# whether or not to pull al the data live from bigquery 
#PULL_FROM_BIGQUERY = False
# whether or not there's a live streamlit instance connected to this repo
#LIVE_STREAMLIT_INSTANCE = False

# the rate to convert bigquery transaction amounts into tokens
#TOKEN_CONVERSION = 1E15

# the date the grant occured
#GRANT_DATE = datetime(2024, 9, 1)
#GRANT_DATE_STR = '2024-09-01'

# the project name for the bigquery project
BIGQUERY_PROJECT_NAME = 'oso-data-436717'

# where the dictionary mapping each project to it's respective defi llama protocol is stored
DEFI_LLAMA_PROTOCOLS_PATH = "defillama.json"
# where the dictionary of the grants to be displayed is stored
GRANTS_PATH = "updated_grants_reviewed.json"
# where the service account credentials is stored
SERVICE_ACCOUNT_PATH = 'oso_gcp_credentials.json'
# where the previously queried datasets are stored
STORED_DATA_PATH = 'data/'