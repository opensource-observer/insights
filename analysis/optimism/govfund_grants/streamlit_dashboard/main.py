import streamlit as st
from typing import Dict, List, Union, Optional, Tuple

from sections.overview_section import overview_section
from sections.core_metrics_section import core_metrics_section
from sections.tvl_section import tvl_section
from sections.statistical_analysis_section import stat_analysis_section
from processing import make_net_op_dataset
from utils import (extract_addresses,
                   read_in_defi_llama_protocols, 
                   return_protocol, 
                   read_in_grants, 
                   read_in_stored_dfs_for_projects, 
                   query_transaction_data_from_bq,
                   connect_bq_client,
                   query_tvl_data_from_bq)

from config import (GRANTS_PATH, 
                    DEFI_LLAMA_PROTOCOLS_PATH, 
                    PULL_FROM_BIGQUERY, 
                    LIVE_STREAMLIT_INSTANCE, 
                    SERVICE_ACCOUNT_PATH,
                    STORED_DATA_PATH)

def display_dashboard_overview():
    st.subheader("Dashboard Overview")
    st.write("""
        This dashboard provides an in-depth exploration of the performance of S6 Growth Grants, enabling detailed insights into project outcomes. It covers the following key sections:
    """)

    with st.expander("1. Project Overview"):
        st.write("""
            A high-level summary of the selected project, aiming to clarify the project's context and details:
            - **Project Name, Round, Cycle, and Status**
            - **Grant Amount** and a **link to the proposal**
            - **Relevant contract/wallet addresses**
        """)

    with st.expander("2. Core Metrics"):
        st.write("""
            Interactive line graph visualizations for key metrics. Users can filter data by contract addresses and date ranges for customized analysis:
            - **Transaction Count**, **Active Users**, **Unique Users**
            - **Total OP Transferred**, **Net OP Transferred**, and **Cumulative OP Transferred**
        """)

    with st.expander("3. TVL Analysis (if applicable)"):
        st.write("""
            For projects with an associated DeFi Llama protocol, this section explores **TVL (Total Value Locked)** trends and distributions, comparing pre-grant to post-grant performance. Key insights include:
            - **TVL trends over time across all chains**
            - Focused analysis on **specific tokens and chains**
            - **TVL distribution across chains** (pre vs. post-grant)
            - **TVL composition by token** (pre vs. post-grant)
            - **Volatility and relative daily changes in TVL**, visualized through histograms, box plots, and line graphs.
        """)

    with st.expander("4. Statistical Analysis"):
        st.write("""
            Users can explore the statistical impact of the grants by selecting a target metric and date range. This section includes:
            - **Comparison of post-grant data with forecasted data** using pre-grant data via synthetic control methods.
            - **2-sample t-test results** comparing pre- and post-grant performance.
            - An interactive **t-test distribution simulator** with adjustable alpha values.
            
            A dedicated explanation on interpreting these results is available at the section for deeper understanding.
        """)

def main() -> None:

    st.title("S6 Growth Grants Performance Analysis")
    # description goes here
    display_dashboard_overview()

    st.divider()

    # read in the defi_llama_protocols
    defi_llama_protocols = read_in_defi_llama_protocols(DEFI_LLAMA_PROTOCOLS_PATH)

    # allow for users to select a desired project
    projects = read_in_grants(GRANTS_PATH)
    project_names = list(projects.keys())
    selected_project_name = st.selectbox("Select a Project", project_names) # project selection dropdown

    if not selected_project_name:
        st.warning("Please select a project from the dropdown.")
        return
    
    # retrieve selected project data
    project = projects[selected_project_name]
    # get the relevant wallet/contract addresses associated with the selected project
    project_addresses = extract_addresses(project) 
    # check if the selected project has an associated defi llama protocol
    project_protocol = return_protocol(defi_llama_protocols, selected_project_name)

    # gathering all of the necessary data for the selected project
    if PULL_FROM_BIGQUERY:
        client = connect_bq_client(SERVICE_ACCOUNT_PATH, LIVE_STREAMLIT_INSTANCE)
        project_daily_transactions_df, project_op_flow_df = query_transaction_data_from_bq(client=client, project_addresses=project_addresses)
        project_net_op_flow_df = make_net_op_dataset(op_flow_df=project_op_flow_df, project_addresses=project_addresses)

        if project_protocol and project_protocol is not None:
            project_chain_tvls_df, project_tvl_df, project_tokens_in_usd_df, project_tokens_df = query_tvl_data_from_bq(client=client, protocol=project_protocol)

    else:
        project_datasets = read_in_stored_dfs_for_projects(project=project, data_path=STORED_DATA_PATH, protocol=project_protocol)
        project_daily_transactions_df = project_datasets['daily_transactions']
        project_net_op_flow_df = project_datasets['net_op_flow']
        project_chain_tvls_df = project_datasets['chain_tvls']
        project_tokens_in_usd_df = project_datasets['tokens_in_usd']
        project_tvl_df = project_datasets['tvl']
        project_forecasted_df = project_datasets['forecasted']

    # define the tabs that will be displayed
    if project_protocol and project_protocol is not None:
        overview, core_metrics, tvl, stat_analysis = st.tabs(['Project Overview', 'Core Metrics', 'TVL', 'Statistical Analysis'])

    else:
        overview, core_metrics, stat_analysis = st.tabs(['Project Overview', 'Core Metrics', 'Statistical Analysis'])

    with overview: 
        overview_section(project=project)

    with core_metrics:
        core_metrics_section(daily_transactions_df=project_daily_transactions_df, net_op_flow_df=project_net_op_flow_df, project_addresses=project_addresses)

    if project_protocol and project_protocol is not None:
        with tvl:
            tvl_section(chain_tvls_df=project_chain_tvls_df, tvl_df=project_tvl_df, tokens_in_usd_df=project_tokens_in_usd_df)

    with stat_analysis:
        project_forecasted_df = None if PULL_FROM_BIGQUERY else project_forecasted_df
        if project_protocol and project_protocol is not None:
            stat_analysis_section(daily_transactions_df=project_daily_transactions_df, net_op_flow_df=project_net_op_flow_df, tvl_df=project_tvl_df, forecasted_df=project_forecasted_df)            
        else:
            stat_analysis_section(daily_transactions_df=project_daily_transactions_df, net_op_flow_df=project_net_op_flow_df, forecasted_df=project_forecasted_df)

if __name__ == "__main__":
    main()
