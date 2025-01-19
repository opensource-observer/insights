from streamlit_dashboard.utils import connect_bq_client, get_addresses_condition
import pandas as pd 
import json

def main() -> None:
    with open("data/updated_grants_reviewed.json", "r") as f:
        grants = json.load(f)

    mapping = {"optimism": "op"}
    client = connect_bq_client("oso_gcp_credentials.json", False)

    # helper function for single/multiple addresses
    def get_chains_condition(chains):
        print(chains)
        if len(chains) == 1:
            return f"= '{chains[0]}'"
        return f"IN {tuple(chains)}"

    for grant in grants:
        grant_chains = []
        grant_addresses = []
        curr_addresses = grant["addresses"]
        grant_approval_date = "2024-09-01"

        for address in curr_addresses:
            addy = list(address.keys())[0]
            if "wallet" in address[addy]["tags"]:
                grant_addresses.append(addy)
                chains = address[addy]["networks"]
                for chain in chains:
                    target = mapping.get(chain, chain)
                    grant_chains.append(target)
                grant_addresses = list(set(grant_addresses))
        grant_chains = list(set(grant_chains))

        chains_condition = get_chains_condition(grant_chains)
        address_condition = get_addresses_condition(grant_addresses)

        query = f"""
        SELECT
            min(dt) as minimum_date
            FROM (
                SELECT
                    to_address AS address,
                    dt
                FROM `oso-data-436717.oso_production.int_superchain_transactions_sandbox`
                WHERE to_address {address_condition} 
                    AND chain {chains_condition}
                    AND dt >= DATE('{grant_approval_date}')
            )"""

        # execute the queries
        if len(grant_addresses) >= 1 and len(grant_chains) >= 1:
            result = client.query(query)
            df = result.to_dataframe()

            if not df.empty:
                min_date = df["minimum_date"].iloc[0]
                # Handle NaT by replacing with a default value
                if pd.isnull(min_date):  # Check if the value is NaT or null
                    min_date = "2024-09-01"
                grant["funds_recieved_date"] = str(min_date)  # Ensure date is a string
                print(f"project {grant['project_name']} minimum date: {min_date}")
            else:
                print(f"project {grant['project_name']} has no transactions.")
                grant["funds_recieved_date"] = "2024-09-01"

    with open("data/new_grants_reviewed.json", "w") as f:
        json.dump(grants, f, indent=4)

if __name__ == "__main__":
    main()
