import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Union, Optional
from datetime import datetime

from utils import safe_execution, compute_growth

# streamlit function to display KPIs and a line graph for a desired metric
def display_op_kpis_and_vis_for_core_metrics(
    project_daily_transactions: pd.DataFrame,
    project_net_transaction_flow: pd.DataFrame, 
    project_addresses: List[Dict[str, Union[str, None]]], 
    grant_date: str, 
    display_by_address: bool
) -> None:

    # Preprocess and merge the datasets once
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
        "net_transferred": "Net Transferred"
    }, inplace=True)

    # Fill nulls for numeric columns
    target_cols = ["Transaction Count", "Active Users", "Unique Users", "Total Transferred", "Cumulative Transferred", "Net Transferred"]
    data_merged[target_cols] = data_merged[target_cols].fillna(0)

    # Precompute groupings
    # Group by transaction date and address
    grouped_by_date_and_address = data_merged.groupby(['transaction_date', 'address'])[target_cols].sum().reset_index()

    # Group by transaction date only (aggregate across all addresses)
    grouped_by_date = data_merged.groupby('transaction_date')[target_cols].sum().reset_index()

    # User selects a metric
    selected_metric = st.selectbox("Select a metric", target_cols)

    # User selects addresses if display_by_address is enabled
    if display_by_address:
        # Add "All" option to the address list
        display_addresses = [f"{address['address']} {address['label']}" if address['label'] else address['address'] for address in project_addresses]
        address_options = ["All addresses"] + display_addresses
        selected_addresses = st.multiselect("Select addresses", address_options)

        if not selected_addresses:
            st.warning("Please select at least one address.")
            return

        if "All addresses" in selected_addresses:
            # Use precomputed data aggregated by transaction date
            data_grouped = grouped_by_date[['transaction_date', selected_metric]]
        else:
            # Filter precomputed data for the selected addresses
            just_selected_addresses = [address.split(" ")[0] for address in selected_addresses]
            data_grouped = grouped_by_date_and_address[grouped_by_date_and_address['address'].isin(just_selected_addresses)]
            data_grouped = data_grouped[['transaction_date', 'address', selected_metric]]
    else:
        # Use precomputed data aggregated by transaction date
        data_grouped = grouped_by_date[['transaction_date', selected_metric]]

    # Ensure transaction_date is a date object
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

    if display_by_address:
        if "All addresses" in selected_addresses:
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

    else:
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

# streamlit function to display KPIs and a line graph for a desired metric
def display_superchain_kpis_and_vis_for_core_metrics(
    project_daily_transactions: pd.DataFrame, 
    project_addresses: List[Dict[str, Union[str, None]]], 
    grant_date: str, 
    display_by_address: bool
) -> None:
    
    target_df = project_daily_transactions.copy()

    # preprocess and merge the datasets once
    target_df.rename(columns={
        "transaction_cnt": "Transaction Count", 
        "active_users": "Active Users", 
        "unique_users": "Unique Users", 
        "total_transferred": "Total Transferred",
        "cum_transferred": "Cumulative Transferred"
    }, inplace=True)

    # fill nulls for numeric columns
    target_cols = ["Transaction Count", "Active Users", "Unique Users", "Total Transferred", "Cumulative Transferred"]
    target_df[target_cols] = target_df[target_cols].fillna(0)

    # ensure transaction_date is a date object
    target_df['transaction_date'] = pd.to_datetime(target_df['transaction_date']).dt.date

    # user selects a metric
    selected_metric = st.selectbox("Select a metric", target_cols)

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


def core_metrics_section(daily_transactions_df: pd.DataFrame, project_addresses: List[Dict[str, Union[str, None]]], grant_date: datetime, display_by_address: bool, net_transaction_flow_df: Optional[pd.DataFrame] = None) -> None:

    # display the core metrics visualizations
    st.header("Plotting Core Metrics by Day")

    if not display_by_address:
        daily_transactions_df = daily_transactions_df.groupby('transaction_date')[
            ['transaction_cnt', 'active_users', 'total_transferred', 'unique_users', 'total_transferred_in_tokens', 'cum_transferred']
        ].sum().reset_index()

    if net_transaction_flow_df is None:
        safe_execution(display_superchain_kpis_and_vis_for_core_metrics, daily_transactions_df, project_addresses, grant_date, display_by_address)
    else:
        safe_execution(display_op_kpis_and_vis_for_core_metrics, daily_transactions_df, net_transaction_flow_df, project_addresses, grant_date, display_by_address)