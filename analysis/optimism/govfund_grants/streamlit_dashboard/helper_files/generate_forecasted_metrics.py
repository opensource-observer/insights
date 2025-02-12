import warnings
warnings.filterwarnings("ignore")

from forecasting import forecast_project
from utils import read_in_stored_dfs_for_projects, read_in_grants, extract_addresses, return_protocol, read_in_defi_llama_protocols

from config import GRANTS_PATH, DEFI_LLAMA_PROTOCOLS_PATH, STORED_DATA_PATH

projects = read_in_grants(grants_path="t.json")
defi_llama_protocols = read_in_defi_llama_protocols(path=DEFI_LLAMA_PROTOCOLS_PATH)

for project_name, project in projects.items():
    clean_name = project_name.lower().replace(" ", "_").replace(".", "-").replace("/","-")
    print(f"project: {clean_name} starting")

    chain = project['chain']
    grant_date = project['funds_recieved_date']

    just_addresses, project_addresses = extract_addresses(project_dict=project) 
    project_protocol = return_protocol(defi_llama_protocols=defi_llama_protocols, project=project_name)

    datasets = read_in_stored_dfs_for_projects(clean_name, STORED_DATA_PATH, project_protocol)

    forecasted_df = forecast_project(datasets, grant_date)

    if forecasted_df is not None and not forecasted_df.empty:
        forecasted_df.to_csv(f"{STORED_DATA_PATH}{clean_name}/{clean_name}_forecasted_metrics.csv", index=False)

    print(f"project: {clean_name} finished")