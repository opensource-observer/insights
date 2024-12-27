import streamlit as st
from google.cloud import bigquery
import pandas as pd
import plotly.express as px
import json
import os
from typing import Dict, List, Union, Optional, Tuple
from single_project_visualizations import process_project, generate_dates, extract_addresses
from defi_llama_visualizations import defi_llama_section, read_in_defi_llama_protocols, return_protocol, safe_execution

BIGQUERY_PROJECT_NAME = 'oso-data-436717'
DEFI_LLAMA_PROTOCOLS_PATH = "metrics/defillama.json"
GRANTS_PATH = "metrics/temp_grants.json"

# create a dictionary of the target grants to work with
def read_in_grants(grants_path: str) -> Dict[str, Dict[str, Union[str, List[str], Dict[str, Union[str, int]]]]]:
    clean_grants = {}
    with open(grants_path, "r") as f:
        grants = json.load(f)

    for project in grants:
        # creating a dictionary of desired format
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

# streamlit function to display a table of project details and project's link
def display_project_details(project: Dict[str, Union[str, List[str], Dict[str, Union[str, int]]]]) -> None:
    # prepare table rows excluding the proposal link
    rows = [
        ("Project Name", str(project.get("project_name", "N/A"))),
        ("Round", str(project.get("round", "N/A"))),
        ("Cycle", str(project.get("cycle", "N/A"))),
        ("Status", str(project.get("status", "N/A"))),
        ("Amount", str(project.get("amount", "N/A"))),
    ]
    df = pd.DataFrame(rows, columns=["Field", "Value"])

    # style the table (hide index and column headers)
    df_style = (
        df.style.hide(axis='index').set_table_styles([
            {"selector": "th", "props": [("display", "none")]}
        ])
    )

    st.table(df_style)

    # display the proposal link as a clickable hyperlink
    proposal_link = project.get("proposal_link", "N/A")
    if proposal_link != "N/A" and proposal_link != "#":
        st.markdown(f"**Proposal Link:** [View Proposal]({proposal_link})")

# streamlit function to display a dataframe of the projects addresses, along with general info on each
def display_addresses_table(addresses: List[Dict[str, Dict[str, Union[str, List[str]]]]]) -> None:
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

    st.subheader("Addresses")
    st.dataframe(df)

# helper function used to create KPIs that determine the amount of growth that occurred between two metrics 
def compute_growth(df: pd.DataFrame, column_name: str) -> Tuple[Optional[float], Optional[float]]:
    if len(df) < 2: return None, None

    last_value = df[column_name].iloc[-1]
    prev_value = df[column_name].iloc[-2]
    difference = last_value - prev_value

    if prev_value == 0: percent_change = 0
    else: percent_change = (difference / prev_value) * 100
    
    return difference, percent_change

# streamlit function to display 2 primary KPIs and then a line graph for a desired metric
def display_kpis_and_vis(project_daily_transactions: pd.DataFrame, target_metric: str, heading: str) -> None:
    st.subheader(heading)
    
    # work on a copy of the DataFrame to avoid modifying the original
    transactions = project_daily_transactions.copy()
    
    # initial calculations
    total_count = transactions[target_metric].sum()
    last_day = transactions["transaction_date"].iloc[-1]
    last_day_count = transactions.loc[transactions["transaction_date"] == last_day, target_metric].sum() if not transactions.empty else 0
    diff, growth = compute_growth(transactions, target_metric)

    # display growth KPIs (columns allow side-by-side)
    col1, col2 = st.columns(2)

    with col1:
        st.metric(label="Since 2024-09-01", value=round(float(total_count), 4))
    
    with col2:
        if diff is not None and diff != 0:
            st.metric(
                label=str(last_day),
                value=round(float(last_day_count), 4),
                delta=f"{round(float(diff), 4)} ({growth:.2f}%)"
            )
        else:
            # if no growth data, just show the value
            st.metric(label=str(last_day), value=round(float(last_day_count), 4))
    
    # ensure the transaction date is of the proper data type
    transactions['transaction_date'] = pd.to_datetime(transactions['transaction_date'])

    # plot the data
    data_grouped = transactions.groupby(['transaction_date', 'address'])[target_metric].sum().reset_index()

    fig = px.line(data_grouped, x='transaction_date', y=target_metric, color='address')

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

    st.plotly_chart(fig)


# helper function to call the display function for our 3 desired metrics
def display_core_metrics(project_daily_transactions: pd.DataFrame) -> None:
    st.header("Core Metrics (since grant)")

    metrics = ["transaction_cnt", "active_users", "unique_users"]
    headings = ["Transaction Count", "Active Users", "Unique Users"]
    
    for i, metric in enumerate(metrics):
        display_kpis_and_vis(project_daily_transactions, metric, headings[i])


def main() -> None:
    st.title("S6 Growth Grants Analysis")

    # retrieve updated projects
    projects = read_in_grants(GRANTS_PATH)
    project_names = list(projects.keys())

    # project selection dropdown
    selected_project_name = st.selectbox("Select a Project", project_names)

    if not selected_project_name:
        st.warning("Please select a project from the dropdown.")
        return

    # retrieve selected project data
    project = projects[selected_project_name]

    # header 1 - project specifics
    st.divider()
    st.header("Project Specifics / Overview")
    safe_execution(display_project_details, project)

    # addresses table
    addresses = project.get("addresses", [])
    if addresses:
        safe_execution(display_addresses_table, addresses)

    # query and process data
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '../../../oso_gcp_credentials.json'
    client = bigquery.Client(BIGQUERY_PROJECT_NAME)
    dates = generate_dates()
    project_addresses = extract_addresses(project)

    # process the selected project
    project_daily_transactions, project_op_flow, project_net_op_flow = process_project(client, project_addresses, dates)        

    # header 2 - core metrics
    st.divider()
    safe_execution(display_core_metrics, project_daily_transactions)

    # header 3 - op flow metrics
    st.divider()
    st.header("OP Flow Metrics (since grant)")

    # display the total OP transfered for each address
    safe_execution(display_kpis_and_vis, project_daily_transactions, "total_op_transferred_in_tokens", "Total OP Transferred (OP Tokens)")
    
    # filter the dataset to only display the net op of addresses from the project
    filtered_project_net_op_flow = project_net_op_flow[project_net_op_flow['address'].isin(project_addresses)]
    safe_execution(display_kpis_and_vis, filtered_project_net_op_flow, "total_op_transferred_in_tokens", "Net OP Transferred (OP Tokens)")

    # create a table that displays transaction count information and net op flow for each project address
    st.subheader("Contract-Specific Metrics")
    transaction_cnts_by_address = project_daily_transactions.groupby('address').agg({
        'transaction_cnt': ['sum', 'mean', 'max']
    }).reset_index()

    # flatten the multi-level column names created by .agg()
    transaction_cnts_by_address.columns = ['address', 'transaction_cnt_sum', 'transaction_cnt_avg', 'transaction_cnt_max']

    net_op_transferred_by_address = project_net_op_flow.groupby('address')['total_op_transferred_in_tokens'].sum().reset_index()
    metrics_by_address = transaction_cnts_by_address.merge(net_op_transferred_by_address, on='address')
    st.dataframe(metrics_by_address.head(10))

    st.divider()

    defi_llama_protocols = read_in_defi_llama_protocols(DEFI_LLAMA_PROTOCOLS_PATH)
    protocol = return_protocol(defi_llama_protocols, selected_project_name)
    if protocol:
        defi_llama_section(protocol)


if __name__ == "__main__":
    main()
