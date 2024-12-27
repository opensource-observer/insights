from datetime import datetime, timedelta
from google.cloud import bigquery
import matplotlib.pyplot as plt
import pandas as pd
import json
import os

GRANTS_PATH = "s6/data/updated_grants_reviewed.json"
METRICS_PATH = "metrics/pipeline_testing/temp_metrics.json"
OUTPUT_PATH = 'metrics/pipeline_testing'

PROJECT_START_DATE = '2024-08-31'
PROJECT_NETWORK = 'mainnet'
NUMERIC_COLS = ['transaction_cnt', 'active_users', 'unique_users', 'total_op_transferred']
BIGQUERY_PROJECT_NAME = 'oso-data-436717'


def read_in_projects(grants_path, metrics_path):
    clean_grants = {}
    with open(grants_path, "r") as f:
        grants = json.load(f)

    for project in grants:
        clean_grants[project['project_name']] = project
    
    # will add metric comparisons and compatability soon

    #clean_metrics = {}
    #with open(metrics_path, "r") as f:
    #    grant_metrics = json.load(f)

    #for project in grant_metrics:
    #    clean_metrics[project['project_name']] = project

    #projects = {}

    #for project_name, project in clean_grants.items():
    #    projects[project_name] = project
    #    project["extracted_metrics"] = clean_metrics[project_name]

    return clean_grants


def generate_dates():
    dates = []
    todays_date = datetime.now()
    target_date = datetime(2024, 9, 1)
    date_interval = (todays_date - target_date).days
    for i in range(date_interval):
        date = target_date + timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))

    return dates


def extract_addresses(project_dict):
    project_address_dict = project_dict['addresses']

    project_addresses = []
    for address in project_address_dict:
        project_addresses.extend(list(address.keys()))
    
    return tuple(project_addresses)


def make_dates_df(dates, project_addresses):
    data = []
    for address in project_addresses:
        for date in dates:
            data.append({'transaction_date': date, 'contract_address': address})

    return pd.DataFrame(data)


def query_daily_transactions(client, project_addresses, dates_df):
    
    daily_transactions_query = f"""
        SELECT 
            dt AS transaction_date,
            to_address AS contract_address,
            COUNT(*) AS transaction_cnt,
            COUNT(from_address) AS active_users,
            COUNT(DISTINCT from_address) AS unique_users,
            SUM(value_64) AS total_op_transferred
        FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions` 
        WHERE to_address IN {project_addresses}
            AND network = '{PROJECT_NETWORK}'
            AND dt >= '{PROJECT_START_DATE}'
        GROUP BY dt, to_address
        ORDER BY dt, to_address"""
    
    daily_transactions_result = client.query(daily_transactions_query)
    daily_transactions_df = daily_transactions_result.to_dataframe()

    daily_transactions_merged_df = pd.merge(daily_transactions_df, dates_df, how='outer', on=['transaction_date', 'contract_address']).fillna(0) 
    
    daily_transactions_merged_df[NUMERIC_COLS] = daily_transactions_merged_df[NUMERIC_COLS].astype(int)

    daily_transactions_merged_df = (daily_transactions_merged_df
        .groupby(['transaction_date', 'contract_address'], as_index=False)
        .agg({
            'transaction_cnt': 'sum',
            'active_users': 'sum',
            'unique_users': 'sum',
            'total_op_transferred': 'sum'
        })
    )

    return daily_transactions_merged_df


def query_op_flow(client, project_addresses):
    op_flow_query = f"""
    (SELECT 
        dt AS transaction_date,
        from_address,
        to_address,
        COUNT(*) AS cnt,
        SUM(value_64) AS total_op_transferred
    FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions`
    WHERE network = '{PROJECT_NETWORK}'
        AND to_address IN {project_addresses}
        AND dt >= '{PROJECT_START_DATE}'
    GROUP BY dt, from_address, to_address
    ORDER BY 3 DESC)

    UNION ALL 

    (SELECT 
        dt AS transaction_date,
        from_address,
        to_address,
        COUNT(*) AS cnt,
        SUM(value_64) AS total_op_transferred
    FROM `oso-data-436717.optimism_superchain_raw_onchain_data.transactions`
    WHERE network = '{PROJECT_NETWORK}'
        AND from_address IN {project_addresses}
        AND dt >= '{PROJECT_START_DATE}'
    GROUP BY dt, from_address, to_address
    ORDER BY 3 DESC)"""

    op_flow_result = client.query(op_flow_query)
    op_flow_df = op_flow_result.to_dataframe()

    return op_flow_df


def daily_transactions_plot(daily_transactions, op_flow, project_title, project_folder):
    # Convert transaction_date to datetime for consistency
    daily_transactions['transaction_date'] = pd.to_datetime(daily_transactions['transaction_date'])
    op_flow['transaction_date'] = pd.to_datetime(op_flow['transaction_date'])

    # Determine the total number of plots: one for each NUMERIC_COL
    num_plots = len(NUMERIC_COLS)

    # Create a single figure for all plots
    fig, axes = plt.subplots(num_plots, 1, figsize=(15, 6 * num_plots))

    # Add a global title for the entire figure
    fig.suptitle(f'{project_title} - Metrics and Visualizations', fontsize=25)

    # Loop through NUMERIC_COLS to create line plots for each target_column
    for i, target_column in enumerate(NUMERIC_COLS):
        data_grouped = daily_transactions.groupby(['transaction_date', 'contract_address'])[target_column].sum().reset_index()
        data_grouped = data_grouped.sort_values('transaction_date').reset_index(drop=True)

        pivoted_data = data_grouped.pivot(
            index='transaction_date',
            columns='contract_address',
            values=target_column
        )

        ax = axes[i]
        for contract in pivoted_data.columns:
            ax.plot(pivoted_data.index, pivoted_data[contract], label=contract)

        ax.set_title(f'{target_column} Over Time by Contract Address ({project_title})')
        ax.set_xlabel('Transaction Date', fontsize=12)
        ax.set_ylabel(target_column, fontsize=12)
        ax.legend()

    # Adjust layout for all subplots
    plt.tight_layout(rect=[0, 0, 1, 0.98])

    # Save the figure
    file_name = f'{project_title.lower().replace(" ", "_").replace(".", "-")}_visualizations.png'
    full_path = os.path.join(project_folder, file_name)
    plt.savefig(full_path)
    plt.close()


def top_addresses_plot(op_flow, project_title, project_folder):
    # Create the bar chart for top addresses by transaction count
    address_counts = op_flow.groupby('from_address')['cnt'].sum().sort_values(ascending=False)

    plt.figure(figsize=(12, 6))
    address_counts.head(10).plot(kind='barh', color='skyblue')

    plt.title(f'Top 10 From Addresses by Transaction Count ({project_title})', fontsize=14)
    plt.xlabel('Transaction Count', fontsize=12)
    plt.ylabel('From Address', fontsize=12)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout(rect=[0, 0, 1, 0.98])

    # Save the figure
    file_name = f'{project_title.lower().replace(" ", "_").replace(".", "-")}_top_addresses.png'
    full_path = os.path.join(project_folder, file_name)
    plt.savefig(full_path)
    plt.close()


def net_op_flow_plot(op_flow_df, project_addresses, project_title, project_folder):
    def transaction_direction(row):
        if row['from_address'] in project_addresses:
            return "out"
        elif row['to_address'] in project_addresses:
            return "in"
        return ""

    op_flow_df['direction'] = op_flow_df.apply(transaction_direction, axis=1)

    transaction_direction_df = pd.concat([
        op_flow_df[['transaction_date', 'from_address', 'direction', 'cnt', 'total_op_transferred']].rename(columns={'from_address': 'wallet_address'}),
        op_flow_df[['transaction_date', 'to_address', 'direction', 'cnt', 'total_op_transferred']].rename(columns={'to_address': 'wallet_address'})
    ])

    transaction_direction_df.drop_duplicates(inplace=True)
    transaction_direction_df = transaction_direction_df.groupby(['transaction_date', 'wallet_address', 'direction'], as_index=False).agg({
        'cnt': 'sum',
        'total_op_transferred': 'sum'
    })

    transaction_direction_df.loc[transaction_direction_df['direction'] == 'out', 'total_op_transferred'] *= -1
    transaction_direction_df.sort_values(by=['wallet_address', 'transaction_date'], inplace=True)
    transaction_direction_df['cum_op_transferred'] = transaction_direction_df.groupby('wallet_address')['total_op_transferred'].cumsum()
    transaction_direction_df.reset_index(drop=True, inplace=True)

    transaction_direction_pivoted_df = transaction_direction_df.pivot(
        index='transaction_date',
        columns='wallet_address',
        values='cum_op_transferred'
    ).fillna(0)

    plt.figure(figsize=(12, 6))
    for wallet_address in project_addresses:
        if wallet_address not in transaction_direction_pivoted_df.columns:
            transaction_direction_pivoted_df[wallet_address] = 0
        
        plt.plot(transaction_direction_pivoted_df.index, transaction_direction_pivoted_df[wallet_address], label=wallet_address)

    plt.title('Cumulative OP Transferred Over Time by Wallet Address', fontsize=14)
    plt.xlabel('Transaction Date', fontsize=12)
    plt.ylabel('Cumulative OP Transferred', fontsize=12)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.tight_layout(rect=[0, 0, 1, 0.98])

    # Save the figure
    file_name = f'{project_title.lower().replace(" ", "_").replace(".", "-")}_net_op_flow.png'
    full_path = os.path.join(project_folder, file_name)
    plt.savefig(full_path)
    plt.close()


def generate_visualizations(daily_transactions, project_addresses, op_flow, output_path, project_title):
    # Create a directory for the project
    project_folder = os.path.join(output_path, project_title.lower().replace(" ", "_").replace(".", "-"))
    os.makedirs(project_folder, exist_ok=True)

    # Generate daily transactions plot
    daily_transactions_plot(daily_transactions, op_flow, project_title, project_folder)

    # Generate top addresses plot
    top_addresses_plot(op_flow, project_title, project_folder)

    # Generate net OP flow plot
    if len(project_addresses) < 12:
        net_op_flow_plot(op_flow, project_addresses, project_title, project_folder)

    return


def main():
    # Connect to the BigQuery client
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '../../../oso_gcp_credentials.json'
    client = bigquery.Client(BIGQUERY_PROJECT_NAME)

    dates = generate_dates()
    projects = read_in_projects(GRANTS_PATH, METRICS_PATH)

    for project_name, project in projects.items():
        try:
            # Extract project-specific data
            project_addresses = extract_addresses(project)
            dates_df = make_dates_df(dates, project_addresses)

            print(f'Querying transaction and op flow data for project: {project_name}')
            
            # Query daily transactions and OP flow data
            daily_transactions = query_daily_transactions(client, project_addresses, dates_df)
            op_flow = query_op_flow(client, project_addresses)

            # Generate visualizations
            generate_visualizations(daily_transactions, project_addresses, op_flow, OUTPUT_PATH, project_name)
            print(f'Completed visualizations for project: {project_name}')

        except Exception as e:
            # Catch any error, log the project name, and continue
            print(f"Error processing project {project_name}: {e}")
            continue  # Continue with the next project

    print("Processing completed.")
    return


if __name__ == "__main__":
    main()