from datetime import datetime, timedelta
from google.cloud import bigquery
import matplotlib.pyplot as plt
import pandas as pd
import os

PROJECT_START_DATE = '2024-08-31'
PROJECT_NETWORK = 'mainnet'
NUMERIC_COLS = ['transaction_cnt', 'active_users', 'unique_users', 'total_op_transferred']
BIGQUERY_PROJECT_NAME = 'oso-data-436717'


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
    try:
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
    
    except Exception as e:
        raise RuntimeError(f"Failed to query daily transactions: {e}")


def query_op_flow(client, project_addresses):
    try:
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

    except Exception as e:
        raise RuntimeError(f"Failed to query op flow: {e}")


def plot_top_addresses(op_flow, project_title):
    # Create a bar chart for top addresses by transaction count
    address_counts = op_flow.groupby('from_address')['cnt'].sum().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(12, 6))
    address_counts.head(10).plot(kind='barh', ax=ax, color='skyblue')

    # Customize plot
    ax.set_title(f'Top 10 From Addresses by Transaction Count ({project_title})', fontsize=14)
    ax.set_xlabel('Transaction Count')
    ax.set_ylabel('From Address')
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()

    return fig


def plot_net_op_flow(op_flow_df, project_addresses):
    def transaction_direction(row):
        if row['from_address'] in project_addresses:
            return "out"
        elif row['to_address'] in project_addresses:
            return "in"
        return ""

    # Apply direction logic
    op_flow_df['direction'] = op_flow_df.apply(transaction_direction, axis=1)

    # Prepare cumulative transaction data
    transaction_direction_df = pd.concat([
        op_flow_df[['transaction_date', 'from_address', 'direction', 'cnt', 'total_op_transferred']]
        .rename(columns={'from_address': 'wallet_address'}),
        op_flow_df[['transaction_date', 'to_address', 'direction', 'cnt', 'total_op_transferred']]
        .rename(columns={'to_address': 'wallet_address'})
    ])

    # Aggregate and calculate cumulative sum
    transaction_direction_df.drop_duplicates(inplace=True)
    transaction_direction_df = transaction_direction_df.groupby(['transaction_date', 'wallet_address', 'direction'], as_index=False).agg({
        'cnt': 'sum',
        'total_op_transferred': 'sum'
    })

    transaction_direction_df.loc[transaction_direction_df['direction'] == 'out', 'total_op_transferred'] *= -1
    transaction_direction_df.sort_values(by=['wallet_address', 'transaction_date'], inplace=True)
    transaction_direction_df['cum_op_transferred'] = transaction_direction_df.groupby('wallet_address')['total_op_transferred'].cumsum()

    # Pivot for plotting
    transaction_direction_pivoted_df = transaction_direction_df.pivot(
        index='transaction_date',
        columns='wallet_address',
        values='cum_op_transferred'
    ).fillna(0)

    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))
    for wallet_address in project_addresses:
        ax.plot(transaction_direction_pivoted_df.index, transaction_direction_pivoted_df[wallet_address], label=wallet_address)

    # Customize plot
    ax.set_title('Cumulative OP Transferred Over Time by Wallet Address', fontsize=14)
    ax.set_xlabel('Transaction Date')
    ax.set_ylabel('Cumulative OP Transferred')
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.tight_layout()

    return fig


def _plot_single_metric(daily_transactions, metric, metric_title, project_title):
    daily_transactions['transaction_date'] = pd.to_datetime(daily_transactions['transaction_date'])

    data_grouped = daily_transactions.groupby(['transaction_date', 'contract_address'])[metric].sum().reset_index()
    pivoted_data = data_grouped.pivot(index='transaction_date', columns='contract_address', values=metric).fillna(0)

    fig, ax = plt.subplots(figsize=(12, 6))

    for contract in pivoted_data.columns:
        ax.plot(pivoted_data.index, pivoted_data[contract], label=contract)

    ax.set_title(f'{metric_title} Over Time ({project_title})', fontsize=14)
    ax.set_xlabel('Transaction Date', fontsize=12)
    ax.set_ylabel(metric_title, fontsize=12)
    ax.legend()

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    return fig


def plot_transaction_count(daily_transactions, project_title):
    return _plot_single_metric(
        daily_transactions, 
        metric="transaction_cnt", 
        metric_title="Transaction Count", 
        project_title=project_title
    )

def plot_active_users(daily_transactions, project_title):
    return _plot_single_metric(
        daily_transactions, 
        metric="active_users", 
        metric_title="Active Users", 
        project_title=project_title
    )

def plot_unique_users(daily_transactions, project_title):
    return _plot_single_metric(
        daily_transactions, 
        metric="unique_users", 
        metric_title="Unique Users", 
        project_title=project_title
    )

def plot_total_op_transferred(daily_transactions, project_title):
    return _plot_single_metric(
        daily_transactions, 
        metric="total_op_transferred", 
        metric_title="Total OP Transferred", 
        project_title=project_title
    )


def generate_visualizations(project_addresses, daily_transactions, op_flow, project_title):
    transaction_count_plot = plot_transaction_count(daily_transactions, project_title)
    active_users_plot = plot_active_users(daily_transactions, project_title)
    unique_users_plot = plot_unique_users(daily_transactions, project_title)
    total_op_transferred_plot = plot_total_op_transferred(daily_transactions, project_title)
    top_addresses_plot = plot_top_addresses(op_flow, project_title)

    net_op_flow_plot = None
    if len(project_addresses) < 12:
        net_op_flow_plot = plot_net_op_flow(op_flow, project_addresses, project_title)

    return transaction_count_plot, active_users_plot, unique_users_plot, total_op_transferred_plot, top_addresses_plot, net_op_flow_plot


def process_project(client, project_addresses, dates):
    dates_df = make_dates_df(dates, project_addresses)

    daily_transactions = query_daily_transactions(client, project_addresses, dates_df)
    op_flow = query_op_flow(client, project_addresses)

    return daily_transactions, op_flow
