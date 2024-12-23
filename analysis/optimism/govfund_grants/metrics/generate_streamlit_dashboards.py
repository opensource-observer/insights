import streamlit as st
from google.cloud import bigquery
import pandas as pd
import json
import os

# NEW IMPORTS FOR NEW PLOT FUNCTIONS (adjust as needed):
from single_project_visualizations import (
    process_project,
    generate_dates,
    extract_addresses,
    plot_transaction_count,
    plot_active_users,
    plot_unique_users,
    plot_total_op_transferred,
    plot_top_addresses,
    plot_net_op_flow,
)

BIGQUERY_PROJECT_NAME = 'oso-data-436717'
GRANTS_PATH = "metrics/temp_grants.json"


def read_in_grants(grants_path):
    clean_grants = {}
    with open(grants_path, "r") as f:
        grants = json.load(f)

    for project in grants:
        clean_grants[project['project_name']] = {
            "round": project.get("round", "N/A"),
            "cycle": project.get("cycle", "N/A"),
            "status": project.get("status", "N/A"),
            "proposal_link": project.get("proposal_link", "#"),
            "amount": project.get("amount", "N/A"),
            "meta": project.get("meta", {}),
            "relevant_metrics": project.get("relevant_metrics", {}),
            "relevant_dates": project.get("relevant_dates", {}),
            "relevant_chains": project.get("relevant_chains", []),
            "addresses": project.get("addresses", []),
            "project_name": project.get('project_name', "N/A")  # ensure name is stored
        }

    return clean_grants


def display_addresses_table(addresses):
    address_data = []
    for address in addresses:
        for addr, details in address.items():
            address_data.append({
                "Address": str(addr),
                "Networks": ", ".join(details.get("networks", [])),
                "Tags": ", ".join(details.get("tags", [])),
                "Name": str(details.get("name", "N/A")),
                "Count of Transactions": str(details.get("count_txns", "N/A")),
            })

    df = pd.DataFrame(address_data)

    df_style = (
        df.style.hide(axis='index')
    )

    st.subheader("Addresses")
    st.table(df_style)


def display_project_details(project):
    rows = [
        ("Project Name", str(project.get("project_name", "N/A"))),
        ("Round", str(project.get("round", "N/A"))),
        ("Cycle", str(project.get("cycle", "N/A"))),
        ("Status", str(project.get("status", "N/A"))),
        ("Amount", str(project.get("amount", "N/A"))),
        ("Proposal Link", str(project.get("proposal_link", "N/A"))),
    ]
    df = pd.DataFrame(rows, columns=["Field", "Value"])

    df_style = (
        df.style.hide(axis='index').set_table_styles([
            {"selector": "th", "props": [("display", "none")]}
        ])
    )

    st.subheader("Project Details")
    st.table(df_style)


def main():
    st.title("S6 Growth Grants Analysis")

    # Sidebar: Project Selection
    st.sidebar.header("Project Selection")
    projects = read_in_grants(GRANTS_PATH)
    project_names = list(projects.keys())
    selected_project_name = st.sidebar.selectbox("Select a Project", project_names)

    if not selected_project_name:
        st.warning("Please select a project from the dropdown.")
        return

    # Retrieve selected project data
    project = projects[selected_project_name]

    # Header 1: Project Specifics / Overview
    st.header("Project Specifics / Overview")
    display_project_details(project)

    # Addresses Table
    addresses = project.get("addresses", [])
    if addresses:
        display_addresses_table(addresses)

    # Query and process data
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '../../../oso_gcp_credentials.json'
    client = bigquery.Client(BIGQUERY_PROJECT_NAME)
    dates = generate_dates()
    project_addresses = extract_addresses(project)

    try:
        # Process the selected project
        project_daily_transactions, project_op_flow = process_project(client, project_addresses, dates)

        # Helper to compute difference & % growth from last two days of data
        def compute_growth(df, column_name):
            """
            Compute difference and % growth between the last two days 
            for the specified 'column_name'.
            Returns (difference, percent_change).
            If insufficient data, returns (None, None).
            """
            if len(df) < 2:
                return None, None
            last_value = df[column_name].iloc[-1]
            prev_value = df[column_name].iloc[-2]
            difference = last_value - prev_value
            if prev_value == 0:
                percent_change = 0
            else:
                percent_change = (difference / prev_value) * 100
            return difference, percent_change

        ###################################################################
        # Header 2: Core Metrics
        ###################################################################
        st.header("Core Metrics")

        # Transaction Count
        total_tx_count = project_daily_transactions['transaction_cnt'].sum()
        last_day_tx_count = project_daily_transactions['transaction_cnt'].iloc[-1] if not project_daily_transactions.empty else 0
        tx_diff, tx_growth = compute_growth(project_daily_transactions, 'transaction_cnt')

        st.subheader("Transaction Count")

        # Display KPIs using st.metric
        st.metric(
            label="All-Time",
            value=int(total_tx_count)
        )
        if tx_diff is not None:
            st.metric(
                label="Last Day",
                value=int(last_day_tx_count),
                delta=f"{int(tx_diff)} ({tx_growth:.2f}%)"
            )
        else:
            # If no growth data, just show the value
            st.metric(label="Last Day", value=int(last_day_tx_count))

        # Plot
        transaction_count_plot = plot_transaction_count(project_daily_transactions, selected_project_name)
        st.pyplot(transaction_count_plot)

        # Active Users
        total_active_users = project_daily_transactions['active_users'].sum()
        last_day_active_users = project_daily_transactions['active_users'].iloc[-1] if not project_daily_transactions.empty else 0
        act_diff, act_growth = compute_growth(project_daily_transactions, 'active_users')

        st.subheader("Active Users")

        st.metric(label="All-Time", value=int(total_active_users))
        if act_diff is not None:
            st.metric(
                label="Last Day",
                value=int(last_day_active_users),
                delta=f"{int(act_diff)} ({act_growth:.2f}%)"
            )
        else:
            st.metric(label="Last Day", value=int(last_day_active_users))

        active_users_plot = plot_active_users(project_daily_transactions, selected_project_name)
        st.pyplot(active_users_plot)

        # Unique Users
        total_unique_users = project_daily_transactions['unique_users'].sum()
        last_day_unique_users = project_daily_transactions['unique_users'].iloc[-1] if not project_daily_transactions.empty else 0
        uniq_diff, uniq_growth = compute_growth(project_daily_transactions, 'unique_users')

        st.subheader("Unique Users")

        st.metric(label="All-Time", value=int(total_unique_users))
        if uniq_diff is not None:
            st.metric(
                label="Last Day",
                value=int(last_day_unique_users),
                delta=f"{int(uniq_diff)} ({uniq_growth:.2f}%)"
            )
        else:
            st.metric(label="Last Day", value=int(last_day_unique_users))

        unique_users_plot = plot_unique_users(project_daily_transactions, selected_project_name)
        st.pyplot(unique_users_plot)

        ###################################################################
        # Header 3: OP Flow Metrics
        ###################################################################
        st.header("OP Flow Metrics")

        # Total OP Transferred
        total_op_transferred = project_op_flow['total_op_transferred'].sum()
        last_day_op_transferred = project_op_flow['total_op_transferred'].iloc[-1] if not project_op_flow.empty else 0
        op_diff, op_growth = compute_growth(project_op_flow, 'total_op_transferred')
        st.subheader("Total OP Transferred")

        st.metric(label="All-Time", value=round(total_op_transferred, 2))
        if op_diff is not None:
            st.metric(
                label="Last Day",
                value=round(last_day_op_transferred, 2),
                delta=f"{round(op_diff, 2)} ({op_growth:.2f}%)"
            )
        else:
            st.metric(label="Last Day", value=round(last_day_op_transferred, 2))

        total_op_transferred_plot = plot_total_op_transferred(project_daily_transactions, selected_project_name)
        st.pyplot(total_op_transferred_plot)

        # Net OP Flow (if present in the DF)
        net_op_flow_col = 'net_op_flow'  # or whatever your column is named
        if net_op_flow_col in project_op_flow.columns:
            net_op_transferred = project_op_flow[net_op_flow_col].sum()
            last_day_net_op_transferred = project_op_flow[net_op_flow_col].iloc[-1]
            net_diff, net_growth = compute_growth(project_op_flow, net_op_flow_col)
        else:
            net_op_transferred = 0
            last_day_net_op_transferred = 0
            net_diff, net_growth = (None, None)

        st.subheader("Net OP Transferred")

        st.metric(label="All-Time", value=round(net_op_transferred, 2))
        if net_diff is not None:
            st.metric(
                label="Last Day",
                value=round(last_day_net_op_transferred, 2),
                delta=f"{round(net_diff, 2)} ({net_growth:.2f}%)"
            )
        else:
            st.metric(label="Last Day", value=round(last_day_net_op_transferred, 2))

        net_op_flow_plot_figure = plot_net_op_flow(project_op_flow, project_addresses)
        st.pyplot(net_op_flow_plot_figure)

        # Top Addresses by OP Flow
        st.subheader("Top Addresses by OP Flow")
        top_addresses_plot_figure = plot_top_addresses(project_op_flow, selected_project_name)
        st.pyplot(top_addresses_plot_figure)

        # TVL (if you have a TVL metric, similarly add subheader, KPI, and chart here)

    except Exception as e:
        st.error(f"Failed to process the project: {e}")


if __name__ == "__main__":
    main()
