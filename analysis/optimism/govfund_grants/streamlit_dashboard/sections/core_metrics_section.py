import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List
from utils import safe_execution, compute_growth
from config import GRANT_DATE

# streamlit function to display 2 primary KPIs and then a line graph for a desired metric
def display_kpis_and_vis_for_core_metrics(project_daily_transactions: pd.DataFrame, project_net_op_flow, project_addresses, grant_date) -> None:

    data_merged = pd.merge(project_daily_transactions, project_net_op_flow[['transaction_date', 'address', 'net_op_transferred']], on=['transaction_date', 'address'], how='outer')
    data_merged.rename(columns={
        "transaction_cnt": "Transaction Count", 
        "active_users": "Active Users", 
        "unique_users": "Unique Users", 
        "total_op_transferred": "Total OP Transferred",
        "cum_op_transferred": "Cumulative OP Transferred",
        "net_op_transferred": "Net OP Transferred"
    }, inplace=True)

    target_cols = ["Transaction Count", "Active Users", "Unique Users", "Total OP Transferred", "Cumulative OP Transferred", "Net OP Transferred"]
    data_merged[target_cols] = data_merged[target_cols].fillna(0)

    selected_metric = st.selectbox("Select a metric", target_cols)

    # add an "All" option to the list of addresses
    address_options = ["All addresses"] + list(project_addresses)
    selected_addresses = st.multiselect("Select addresses", address_options)

    if not selected_addresses:
        st.warning("Please select at least one address.")
        return

    # handle the "All" option
    if "All addresses" in selected_addresses and len(selected_addresses) > 1:
        st.warning("You cannot select individual addresses when 'All' is selected.")
        selected_addresses = ["All addresses"]
        return

    if "All addresses" in selected_addresses:
        # aggregate data across all addresses
        data_grouped = data_merged.groupby('transaction_date')[selected_metric].sum().reset_index()
    else:
        # filter data for the selected addresses
        data_grouped = data_merged[data_merged['address'].isin(selected_addresses)] \
            .groupby(['transaction_date', 'address'])[selected_metric].sum().reset_index()

    data_grouped['transaction_date'] = pd.to_datetime(data_grouped['transaction_date'])
    data_grouped['transaction_date'] = data_grouped['transaction_date'].dt.date
    
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

    with col1:
        st.metric(label=f"Since {start_date.strftime('%Y-%m-%d')}", value=round(float(total_count), 4))
    
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
        for project_address in project_addresses:
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
        # Add vertical line for grant date
        fig.add_vline(
            x=grant_date, 
            line_width=2, 
            line_dash="dash", 
            line_color="red"
        )

        # Add a legend entry for the grant date
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

def core_metrics_section(daily_transactions_df, net_op_flow_df, project_addresses):
    st.header("Plotting Core Metrics by Day")

    #safe_execution(display_kpis_and_vis_for_core_metrics, daily_transactions_df, net_op_flow_df, project_addresses, GRANT_DATE)
    display_kpis_and_vis_for_core_metrics (daily_transactions_df, net_op_flow_df, project_addresses, GRANT_DATE)
