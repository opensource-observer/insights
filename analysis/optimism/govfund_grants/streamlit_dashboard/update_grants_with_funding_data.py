import pandas as pd 
import json
from utils import connect_bq_client

QUERY_ON = True

def main() -> None:
    with open("updated_grants_reviewed.json", "r") as f:
        grants = json.load(f)

    client = connect_bq_client("oso_gcp_credentials.json", False)

    for grant in grants:
        grant_amount = grant["amount"]
        grant_wallet = grant["grant_wallet"].lower()
        grant_approval_date = "2024-09-01"

        query = f"""
        SELECT
            COALESCE(MIN(CASE WHEN dt >= DATE("{grant_approval_date}") THEN dt END), DATE("{grant_approval_date}")) AS minimum_date,
            SUM(CASE WHEN dt < DATE("{grant_approval_date}") THEN value_64 ELSE 0 END) AS starting_balance,
            SUM(CASE WHEN dt >= DATE("{grant_approval_date}") THEN value_64 ELSE 0 END) AS inflow_total
        FROM `oso-data-436717.oso_production.int_superchain_transactions_sandbox`
        WHERE to_address = '{grant_wallet}'
            AND chain = "op"
        """

        # execute the query if enabled
        if QUERY_ON:
            result = client.query(query)
            df = result.to_dataframe()

            min_date = df["minimum_date"].iloc[0]
            starting_balance = df["starting_balance"].iloc[0]
            inflow_total = df["inflow_total"].iloc[0]

            # replace missing values with defaults
            if pd.isna(min_date):
                min_date = grant_approval_date
            if pd.isna(starting_balance):
                starting_balance = 0
            if pd.isna(inflow_total):
                inflow_total = 0

            # cast pandas types to native python types
            starting_balance = int(starting_balance) 
            inflow_total = int(inflow_total)
            min_date = str(min_date)  

            # update grant fields
            grant["funds_recieved_date"] = min_date
            grant["starting_balance"] = starting_balance
            grant["inflow_total_todate"] = min(grant_amount, inflow_total)
            grant["recieve_todate"] = inflow_total >= grant_amount
            grant["balance_left_todate"] = max(0, grant_amount - inflow_total)

            print(f"project {grant['project_name']} minimum date: {min_date} | starting balance: {starting_balance} | inflow total: {inflow_total}")

    # save the updated grants to a new json file
    with open("new_grants_reviewed.json", "w") as f:
        json.dump(grants, f, indent=4)

if __name__ == "__main__":
    main()
