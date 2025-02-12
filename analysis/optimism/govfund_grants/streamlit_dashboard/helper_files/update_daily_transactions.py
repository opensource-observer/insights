from queries.superchain_sandbox import query_transaction_data_from_bq_superchain_sandbox
from utils import connect_bq_client, read_in_grants, extract_addresses, return_protocol, read_in_defi_llama_protocols

from config import GRANTS_PATH, DEFI_LLAMA_PROTOCOLS_PATH, SERVICE_ACCOUNT_PATH

projects = read_in_grants(grants_path=GRANTS_PATH)
defi_llama_protocols = read_in_defi_llama_protocols(path=DEFI_LLAMA_PROTOCOLS_PATH)

for project_name, project in projects.items():
    clean_name = project_name.lower().replace(" ", "_").replace(".", "-").replace("/","-")
    print(f"project: {clean_name} starting")
    
    chain = project['chain']
    token_conversion = project['token_conversion']
    grant_date = project['funds_recieved_date']

    just_addresses, project_addresses = extract_addresses(project_dict=project) 
    project_protocol = return_protocol(defi_llama_protocols=defi_llama_protocols, project=project_name)

    client = connect_bq_client(service_account_path=SERVICE_ACCOUNT_PATH)

    project_daily_transactions_df, _ = query_transaction_data_from_bq_superchain_sandbox(client=client, project_addresses=just_addresses, grant_date=grant_date, token_conversion=token_conversion, chain=chain)

    project_daily_transactions_df.to_csv(f"data/{clean_name}/{clean_name}_daily_transactions.csv", index=False)

    print(f"project: {clean_name} finished")