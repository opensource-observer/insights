import pandas as pd
from queries.superchain import query_delegates, query_voters

import warnings
import datetime
warnings.filterwarnings("ignore")

from utils import (connect_bq_client,
                   extract_addresses,
                   read_in_grants)

from config import (GRANTS_PATH, SERVICE_ACCOUNT_PATH)

# Helper function to add timestamps to print statements
def print_with_timestamp(message: str) -> None:
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

# Read grant projects
projects = read_in_grants(grants_path=GRANTS_PATH)
failed_projects = []

for project_name, project in projects.items():
    if project["north_star"] in ["new_delegators", "new_voters"]:
        try:
            print_with_timestamp(f"{project_name} started")
            clean_name = project_name.lower().replace(" ", "_").replace(".", "-").replace("/", "-")

            # Ensure grant_date is a datetime object
            grant_date = project['funds_recieved_date']
            if isinstance(grant_date, str):  
                grant_date = datetime.datetime.strptime(grant_date, "%Y-%m-%d")  # Adjust format if needed

            # Get current date
            current_date = datetime.datetime.today()

            # Compute "mirrored" start_date
            time_since_grant = current_date - grant_date
            start_date = grant_date - time_since_grant  # This ensures symmetry

            # Convert start_date to a SQL-compatible string
            start_date_str = start_date.strftime("%Y-%m-%d")

            # Extract addresses
            just_addresses, project_addresses = extract_addresses(project_dict=project) 

            # Connect BigQuery client
            client = connect_bq_client(service_account_path=SERVICE_ACCOUNT_PATH, use_streamlit_secrets=False)

            # Query data
            delegates_df = query_delegates(client, start_date_str, project_addresses)
            voters_df = query_voters(client, start_date_str, project_addresses)

            # Merge results
            final_df = pd.merge(delegates_df, voters_df, how='inner', on='date')

            print(final_df)

            # Save output
            final_df.to_csv(f"data/{clean_name}/{clean_name}_delegators_and_voters.csv", index=False)

            print_with_timestamp("datasets saved")
            print()

        except Exception as e:
            print_with_timestamp(f"{project_name} project failed due to: {e}")
            failed_projects.append((clean_name, e))

# Print failed projects
print()
for failed, e in failed_projects:
    print(f"project: {failed}")
    print(f"exception: {e}")
