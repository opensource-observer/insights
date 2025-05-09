import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Union, Optional, Tuple
from datetime import datetime

from utils import safe_execution, compute_growth


# normalize the metrics by grant amount
def add_normalized_metrics(project_daily_transactions: pd.DataFrame, grant_amount: int, project_net_transaction_flow: pd.DataFrame = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    daily_transaction_cols = ["transaction_cnt", "active_users", "total_transferred", "unique_users", "cum_transferred", "gas_fee"]
    net_transaction_flow_cols = ["total_transferred", "net_transferred", "net_transferred_in_tokens"]

    # normalize the metrics
    project_daily_transactions_normalized = project_daily_transactions[daily_transaction_cols] / grant_amount
    # rename columns to include "_normalized"
    project_daily_transactions_normalized.columns = [f"{col}_normalized" for col in daily_transaction_cols]
    # add the normalized columns back to the original DataFrames
    project_daily_transactions = pd.concat([project_daily_transactions, project_daily_transactions_normalized], axis=1)

    if project_net_transaction_flow is not None and not project_net_transaction_flow.empty:
        project_net_transaction_flow_normalized = project_net_transaction_flow[net_transaction_flow_cols] / grant_amount
        project_net_transaction_flow_normalized.columns = [f"{col}_normalized" for col in net_transaction_flow_cols]
        project_net_transaction_flow = pd.concat([project_net_transaction_flow, project_net_transaction_flow_normalized], axis=1)

    return project_daily_transactions, project_net_transaction_flow

# streamlit function to display KPIs and a line graph for a desired metric
def display_op_kpis_and_vis_for_core_metrics(
    project_daily_transactions: pd.DataFrame,
    project_net_transaction_flow: pd.DataFrame, 
    delegators_and_voters_df: Optional[pd.DataFrame],
    project_addresses: List[Dict[str, Union[str, None]]], 
    grant_date: str
) -> None:

    # preprocess and merge the datasets once
    data_merged = pd.merge(
        project_daily_transactions, 
        project_net_transaction_flow[['transaction_date', 'address', 'net_transferred']], 
        on=['transaction_date', 'address'], 
        how='outer'
    )

    data_merged.rename(columns={
        "transaction_cnt": "Transaction Count", 
        "active_users": "Active Users", 
        "unique_users": "Unique Users", 
        "total_transferred": "Total Transferred",
        "cum_transferred": "Cumulative Transferred",
        "gas_fee": "Gas Fees",
        "transaction_cnt_normalized": "Transaction Count (Normalized by Grant Amount)", 
        "active_users_normalized": "Active Users (Normalized by Grant Amount)", 
        "unique_users_normalized": "Unique Users (Normalized by Grant Amount)", 
        "total_transferred_normalized": "Total Transferred (Normalized by Grant Amount)",
        "cum_transferred_normalized": "Cumulative Transferred (Normalized by Grant Amount)",
        "gas_fee_normalized": "Gas Fees (Normalized by Grant Amount)"
    }, inplace=True)

    # fill nulls for numeric columns
    target_cols = ["Transaction Count", "Active Users", "Unique Users", "Total Transferred", "Gas Fees", "Gas Fees (Normalized by Grant Amount)",
                   "Transaction Count (Normalized by Grant Amount)", "Active Users (Normalized by Grant Amount)", "Unique Users (Normalized by Grant Amount)", "Total Transferred (Normalized by Grant Amount)"]
    data_merged["Cumulative Transferred"] = data_merged["Cumulative Transferred"].fillna(method="ffill")
    data_merged["Cumulative Transferred (Normalized by Grant Amount)"] = data_merged["Cumulative Transferred (Normalized by Grant Amount)"].fillna(method="ffill")
    data_merged[target_cols] = data_merged[target_cols].fillna(0)
    target_cols += ["Cumulative Transferred", "Cumulative Transferred (Normalized by Grant Amount)"]

    # precompute groupings
    # group by transaction date and address
    grouped_by_date_and_address = data_merged.groupby(['transaction_date', 'address'])[target_cols].sum().reset_index()

    # group by transaction date only (aggregate across all addresses)
    grouped_by_date = data_merged.groupby('transaction_date')[target_cols].sum().reset_index()

    # user selects a metric
    metrics = ["Transaction Count", "Active Users", "Unique Users", "Total Transferred", "Cumulative Transferred", "Gas Fees"]
    if delegators_and_voters_df is not None and not delegators_and_voters_df.empty:
        metrics.extend(["Unique Delegators", "Unique Voters"])
    selected_metric = st.selectbox("Select a metric", metrics)
    normalized = st.checkbox("Normalize by Grant Amount")

    if selected_metric == "Unique Delegators":
        delegators_and_voters_df["transaction_date"] = pd.to_datetime(delegators_and_voters_df["date"]).dt.date
        data_grouped = delegators_and_voters_df[["transaction_date", "unique_delegates"]]
        data_grouped.rename(columns={"unique_delegates":"Unique Delegators"}, inplace=True)

    elif selected_metric == "Unique Voters":
        delegators_and_voters_df["transaction_date"] = pd.to_datetime(delegators_and_voters_df["date"]).dt.date
        data_grouped = delegators_and_voters_df[["transaction_date", "unique_voters"]]
        data_grouped.rename(columns={"unique_voters":"Unique Voters"}, inplace=True)

    else:
        if normalized:
            selected_metric = selected_metric + " (Normalized by Grant Amount)"

        # add "All" option to the address list
        display_addresses = []
        for address in project_addresses:
            # check if transactions at 0
            if len(grouped_by_date_and_address[grouped_by_date_and_address['address'] == address['address']]) < 1:
                continue

            if address['label']:
                curr_address = f"{address['address']} {address['label']}"
            else:
                curr_address = address['address']

            display_addresses.append(curr_address)

        address_options = ["All addresses"] + display_addresses
        selected_addresses = st.multiselect("Select addresses", address_options)

        if not selected_addresses:
            st.warning("Please select at least one address.")
            return

        if "All addresses" in selected_addresses:
            # use precomputed data aggregated by transaction date
            data_grouped = grouped_by_date[['transaction_date', selected_metric]]
        else:
            # filter precomputed data for the selected addresses
            just_selected_addresses = [address.split(" ")[0] for address in selected_addresses]
            data_grouped = grouped_by_date_and_address[grouped_by_date_and_address['address'].isin(just_selected_addresses)]
            data_grouped = data_grouped[['transaction_date', 'address', selected_metric]]

        # ensure transaction_date is a date object
        data_grouped['transaction_date'] = pd.to_datetime(data_grouped['transaction_date']).dt.date
    
    min_date = data_grouped['transaction_date'].min()
    max_date = data_grouped['transaction_date'].max()
    
    # allow for users to input desired date range
    dates = st.slider(
        label="Select a date range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD",
        key="core_metrics_date_slider"
    )

    start_date, end_date = dates[0], dates[1]
    curr_selection_df = data_grouped[(data_grouped['transaction_date'] >= start_date) & (data_grouped['transaction_date'] <= end_date)]

    # initial calculations
    total_count = curr_selection_df[selected_metric].sum()
    last_day = end_date
    last_day_count = curr_selection_df.loc[curr_selection_df["transaction_date"] == last_day, selected_metric].sum() if not curr_selection_df.empty else 0
    diff, growth = compute_growth(curr_selection_df, selected_metric)

    # display growth KPIs (columns allow side-by-side)
    col1, col2 = st.columns(2)

    # the first KPI which represents the total of the metric since the current start date
    with col1:
        st.metric(label=f"Since {start_date.strftime('%Y-%m-%d')}", value=round(float(total_count), 4))
    
    # the second KPI which represents the metric on the current end date, as well as it's % growth from the day before
    with col2:
        if diff is not None and diff != 0:
            st.metric(
                label=str(end_date.strftime('%Y-%m-%d')),
                value=round(float(last_day_count), 4),
                delta=f"{round(float(diff), 4)} ({growth:.2f}%)"
            )
        else:
            # if no growth data, just show the value
            st.metric(label=str(last_day), value=round(float(last_day_count), 4))

    # plot the data
    fig = go.Figure()

    if selected_metric in ["Unique Delegators", "Unique Voters"] or "All addresses" in selected_addresses:
        fig.add_trace(
            go.Scatter(
                x=curr_selection_df['transaction_date'],
                y=curr_selection_df[selected_metric],
                mode='lines',
                name="All addresses"
            )
        )
    else:
        for project_address in just_selected_addresses:
            df_subset = curr_selection_df[curr_selection_df['address'] == project_address]
            fig.add_trace(
                go.Scatter(
                    x=df_subset['transaction_date'],
                    y=df_subset[selected_metric],
                    mode='lines',
                    name=project_address
                )
            )

        fig.update_layout(
            legend_title_text='Addresses',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="right",
            x=1.02
            ),
            xaxis_title='',
            yaxis_title='',
            template="plotly_white"
        )

    if (start_date <= grant_date.date()) and (end_date >= grant_date.date()):
        # add vertical line for grant date
        fig.add_vline(
            x=grant_date, 
            line_width=2, 
            line_dash="dash", 
            line_color="red"
        )

        # add a legend entry for the grant date
        fig.add_trace(
            go.Scatter(
                x=[grant_date], 
                y=[None],  # placeholder value
                mode="lines",
                name="Grant Date",  # legend entry
                line=dict(color="red", dash="dash", width=2),
                showlegend=True,
            )
        )

    st.plotly_chart(fig)

# streamlit function to display KPIs and a line graph for a desired metric
def display_superchain_kpis_and_vis_for_core_metrics(
    project_daily_transactions: pd.DataFrame, 
     delegators_and_voters_df: pd.DataFrame,
    grant_date: str
) -> None:
    
    target_df = project_daily_transactions.copy()

    # preprocess and merge the datasets once
    target_df.rename(columns={
        "transaction_cnt": "Transaction Count", 
        "active_users": "Active Users", 
        "unique_users": "Unique Users", 
        "total_transferred": "Total Transferred",
        "cum_transferred": "Cumulative Transferred",
        "retained_percent": "Retained Daily Active Users",
        "daa_to_maa_ratio": "DAA/MAA",
        "gas_fee": "Gas Fees",
        "unique_delegators": "Unique Delegators",
        "unique_voters": "Unique Voters",
        "transaction_cnt_normalized": "Transaction Count (Normalized by Grant Amount)", 
        "active_users_normalized": "Active Users (Normalized by Grant Amount)", 
        "unique_users_normalized": "Unique Users (Normalized by Grant Amount)", 
        "total_transferred_normalized": "Total Transferred (Normalized by Grant Amount)",
        "net_transferred_normalized": "Net Transferred (Normalized by Grant Amount)",
        "cum_transferred_normalized": "Cumulative Transferred (Normalized by Grant Amount)",
        "gas_fee_normalized": "Gas Fees (Normalized by Grant Amount)"
    }, inplace=True)

    target_cols = [
        "Transaction Count", "Active Users", "Unique Users", "Total Transferred",
        "Cumulative Transferred", "Retained Daily Active Users", "DAA/MAA", "Gas Fees"]

    # fill nulls for cumulative columns using forward fill
    cumulative_cols = ["Cumulative Transferred", "Retained Daily Active Users", "DAA/MAA"]
    target_df[cumulative_cols] = target_df[cumulative_cols].fillna(method="ffill")

    # fill nulls for other numeric columns with 0
    non_cumulative_cols = list(set(target_cols) - set(cumulative_cols))
    target_df[non_cumulative_cols] = target_df[non_cumulative_cols].fillna(0)

    # ensure transaction_date is a date object
    target_df['transaction_date'] = pd.to_datetime(target_df['transaction_date']).dt.date

    # user selects a metric
    if delegators_and_voters_df is not None and not delegators_and_voters_df.empty:
        target_cols.extend(["Unique Delegators", "Unique Voters"])
    selected_metric = st.selectbox("Select a metric", target_cols)
    normalized = st.checkbox("Normalize by Grant Amount")
    unable_to_normalize = ["Retained Daily Active Users", "DAA/MAA"]

    if normalized:
        if selected_metric in unable_to_normalize:
            st.warning("Selected metric cannot be normalized")
            return
        selected_metric = selected_metric + " (Normalized by Grant Amount)"

    # Use precomputed data aggregated by transaction date
    selected_data = target_df[['transaction_date', selected_metric]]
    
    min_date = selected_data['transaction_date'].min()
    max_date = selected_data['transaction_date'].max()
    
    # allow for users to input desired date range
    dates = st.slider(
        label="Select a date range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD",
        key="core_metrics_date_slider"
    )

    start_date, end_date = dates[0], dates[1]
    curr_selection_df = selected_data[(selected_data['transaction_date'] >= start_date) & (selected_data['transaction_date'] <= end_date)]

    # initial calculations
    metrics_to_avg = ["Retained Daily Active Users", "DAA/MAA"]
    if selected_metric in metrics_to_avg:
        kpi1 = curr_selection_df[selected_metric].mean()
    else:
        kpi1 = curr_selection_df[selected_metric].sum()
    last_day = end_date
    last_day_count = curr_selection_df.loc[curr_selection_df["transaction_date"] == last_day, selected_metric].sum() if not curr_selection_df.empty else 0
    diff, growth = compute_growth(curr_selection_df, selected_metric)

    # display growth KPIs (columns allow side-by-side)
    col1, col2 = st.columns(2)

    # the first KPI which represents the total of the metric since the current start date
    with col1:
        st.metric(label=f"Since {start_date.strftime('%Y-%m-%d')}", value=round(float(kpi1), 4))
    
    # the second KPI which represents the metric on the current end date, as well as it's % growth from the day before
    with col2:
        if diff is not None and diff != 0:
            st.metric(
                label=str(end_date.strftime('%Y-%m-%d')),
                value=round(float(last_day_count), 4),
                delta=f"{round(float(diff), 4)} ({growth:.2f}%)"
            )
        else:
            # if no growth data, just show the value
            st.metric(label=str(last_day), value=round(float(last_day_count), 4))

    # plot the data
    fig = go.Figure()

    # plot the line since there's only one line because we aren't plotting by address
    fig = px.line(
        curr_selection_df,
        x="transaction_date",
        y=selected_metric,
        title=f"{selected_metric} Over Time",
        labels={"transaction_date": "Date", selected_metric: selected_metric},
    )

    if (start_date <= grant_date.date()) and (end_date >= grant_date.date()):
        # add vertical line for grant date
        fig.add_vline(
            x=grant_date, 
            line_width=2, 
            line_dash="dash", 
            line_color="red"
        )

        # add a legend entry for the grant date
        fig.add_trace(
            go.Scatter(
                x=[grant_date], 
                y=[None],  # placeholder value
                mode="lines",
                name="Grant Date",  # legend entry
                line=dict(color="red", dash="dash", width=2),
                showlegend=True,
            )
        )

    st.plotly_chart(fig)


def core_metrics_section(daily_transactions_df: pd.DataFrame, project_addresses: List[Dict[str, Union[str, None]]], grant_date: datetime, chain: str, grant_amount: int, net_transaction_flow_df: Optional[pd.DataFrame] = None, delegators_and_voters_df: Optional[pd.DataFrame] = None) -> None:
    
    # display the core metrics visualizations
    st.header("Plotting Core Metrics by Day")

    with st.expander("Understanding and Interacting with the Charts"):
        st.write("""
        ### How to Use the Charts
        1. **Select a Metric**: Use the dropdown to choose the metric you want to visualize.
        2. **Choose a Date Range**: Narrow down the time period to analyze specific trends or events.
        3. **Select Addresses (if applicable)**: If the project is on the Optimism chain, you can select specific addresses to focus on.
        4. **Interpret the Line Graph**:
        - The x-axis shows the selected date range.
        - The y-axis represents the value of the chosen metric.
        - Each address is displayed as a separate line, allowing for comparison.       

        ### Metrics
        - **Transaction Count**: Displays the number of transactions processed each day within the selected date range. Use this to monitor daily activity and trends in transaction frequency.
        - **Active Users**: Shows the count of unique users who interacted with the project on each day. This metric helps evaluate daily engagement and adoption levels.
        - **Unique Users**: Represents the total number of distinct users interacting with the project over the selected date range. This provides an overview of the user base's size during the specified period.
        - **Total Transferred**: Tracks the daily transaction volume (sum of all transferred values) within the selected date range. Use this to analyze the overall activity level and economic throughput of the project.
        - **Net Transferred**: Takes into account the transaction direction for wallets:
            - Transfers **to** the selected addresses contribute positively (+).
            - Transfers **from** the selected addresses contribute negatively (-).
        - **Cumulative Transferred**: Cumulates the net transferred value over time, creating a running total. This shows the long-term accumulation of funds for the selected addresses.
        - **DAA/MAA (Daily Active Users to Monthly Active Users Ratio)**: Represents the ratio of daily active users to monthly active users. This metric provides insights into the intensity of daily engagement compared to the broader monthly activity, helping to assess user retention and stickiness.
        - **Retained Daily Active Users**: Shows the percentage of active users on a given day who were also active the previous day. This metric highlights short-term user retention and helps track consistent engagement levels over time.
        - **TVL (Total Value Locked)**: If the project is associated with a DeFiLlama protocol, this chart displays the total value locked over the date range. It reflects the overall assets deposited in the protocol and is a key indicator of the project's financial health.
        """)

    if chain == "op":
        daily_transactions_df = daily_transactions_df.groupby(['transaction_date', 'address'])[
            ['transaction_cnt', 'active_users', 'total_transferred', 'unique_users', 'cum_transferred', 'gas_fee']
        ].sum().reset_index()

        net_transaction_flow_df = net_transaction_flow_df.groupby(['transaction_date', 'address']).agg({
            'cnt': 'sum',
            'total_transferred': 'sum',
            'net_transferred': 'sum',
            'net_transferred_in_tokens': 'sum'
        }).reset_index()

        daily_transactions_df_normalized, net_transaction_flow_df_normalized = add_normalized_metrics(project_daily_transactions=daily_transactions_df, project_net_transaction_flow=net_transaction_flow_df, grant_amount=grant_amount)

        #safe_execution(display_op_kpis_and_vis_for_core_metrics, daily_transactions_df_normalized, net_transaction_flow_df_normalized, project_addresses, grant_date)
        display_op_kpis_and_vis_for_core_metrics(daily_transactions_df_normalized, net_transaction_flow_df_normalized, delegators_and_voters_df, project_addresses, grant_date)
    
    else:
        daily_transactions_df = daily_transactions_df.groupby('transaction_date')[
            ['transaction_cnt', 'active_users', 'total_transferred', 'unique_users', 'cum_transferred', 'retained_percent', 'daa_to_maa_ratio', 'gas_fee']
        ].sum().reset_index()
    
        daily_transactions_df_normalized, _ = add_normalized_metrics(project_daily_transactions=daily_transactions_df, project_net_transaction_flow=net_transaction_flow_df, grant_amount=grant_amount)

        #safe_execution(display_superchain_kpis_and_vis_for_core_metrics, daily_transactions_df_normalized, grant_date)
        display_superchain_kpis_and_vis_for_core_metrics(daily_transactions_df_normalized, delegators_and_voters_df, grant_date)
