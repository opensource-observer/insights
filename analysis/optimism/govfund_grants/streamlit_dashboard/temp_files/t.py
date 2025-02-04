import warnings
import datetime
warnings.filterwarnings("ignore")

from queries.defillama import query_tvl_data_from_bq

from utils import (connect_bq_client,
                   read_in_defi_llama_protocols, 
                   return_protocol, 
                   read_in_grants)

from config import (DEFI_LLAMA_PROTOCOLS_PATH,
                    SERVICE_ACCOUNT_PATH)

# helper function to add timestamps to print statements
def print_with_timestamp(message: str) -> None:
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

projects = read_in_grants(grants_path="updated_grants_reviewed.json")
defi_llama_protocols = read_in_defi_llama_protocols(path=DEFI_LLAMA_PROTOCOLS_PATH)

for project_name, project in projects.items():
    print_with_timestamp(f"{project_name} started")
    clean_name = project_name.lower().replace(" ", "_").replace(".", "-").replace("/","-")
    project_protocols = return_protocol(defi_llama_protocols=defi_llama_protocols, project=project_name)

    if project_protocols:
        client = connect_bq_client(service_account_path=SERVICE_ACCOUNT_PATH, use_streamlit_secrets=False)

        project_chain_tvls_df, project_tvl_df, project_tokens_in_usd_df, project_tokens_df = query_tvl_data_from_bq(client=client, protocols=project_protocols)
        print_with_timestamp("tvl datasets queried and created")

        project_chain_tvls_df.to_csv(f"data/{clean_name}/{clean_name}_chain_tvls.csv", index=False)
        project_tvl_df.to_csv(f"data/{clean_name}/{clean_name}_tvl.csv", index=False)
        project_tokens_in_usd_df.to_csv(f"data/{clean_name}/{clean_name}_tokens_in_usd.csv", index=False)
