import streamlit as st

from processing import make_net_transaction_dataset
from forecasting import forecast_project
from queries.optimism import query_transaction_data_from_bq_optimism
from queries.cyber import query_transaction_data_from_bq_cyber
from queries.superchain import query_transaction_data_from_bq_superchain
from queries.defillama import query_tvl_data_from_bq

from utils import (read_in_stored_dfs_for_projects,
                   connect_bq_client,
                   extract_addresses,
                   read_in_defi_llama_protocols, 
                   save_datasets,
                   return_protocol, 
                   read_in_grants)

from config import (GRANTS_PATH, 
                    DEFI_LLAMA_PROTOCOLS_PATH,
                    SERVICE_ACCOUNT_PATH,
                    STORED_DATA_PATH)

from sections.overview_section import overview_section
from sections.core_metrics_section import core_metrics_section
from sections.tvl_section import tvl_section
from sections.statistical_analysis_section import stat_analysis_section

# display the detailed description and overview of each aspect of the project
def display_dashboard_overview() -> None:
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
            - **Total Transferred**, **Net Transferred**, and **Cumulative Transferred**
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

    # display title and description
    st.title("S6 Growth Grants Performance Analysis")
    display_dashboard_overview()

    st.divider()

    # read in a dictionary of each project's corresponding defi llama protocol
    defi_llama_protocols = read_in_defi_llama_protocols(path=DEFI_LLAMA_PROTOCOLS_PATH)

    # allow for users to select a desired project
    projects = read_in_grants(grants_path=GRANTS_PATH)
    project_names = list(projects.keys())
    selected_project_name = st.selectbox("Select a Project", project_names) # project selection dropdown

    if not selected_project_name:
        st.warning("Please select a project from the dropdown.")
        return
    
    # retrieve selected project data
    project = projects[selected_project_name]

    # retrieve relevant information from the project
    project_name = project['project_name']
    chain = project['chain']
    pull_from_bigquery = project['pull_from_bigquery']
    store_bq_datasets = project['store_bq_datasets']
    live_streamlit_instance = project['live_streamlit_instance']
    display_by_address = project['display_by_address']
    token_conversion = project['token_conversion']
    grant_date = project['grant_date']

    # get the relevant wallet/contract addresses associated with the selected project
    just_addresses, project_addresses = extract_addresses(project_dict=project) 
    # check if the selected project has an associated defi llama protocol
    project_protocol = return_protocol(defi_llama_protocols=defi_llama_protocols, project=selected_project_name)
    
    # if pull from bigquery is true, pull the necessary datasets directly from bigquery
    if pull_from_bigquery:
        # connect to the bigquery client with the service account at the passed path
        # if this project is connected to a live streamlit instance it connects to bigquery differently
        client = connect_bq_client(service_account_path=SERVICE_ACCOUNT_PATH, use_streamlit_secrets=live_streamlit_instance)
        
        datasets = {}

        # query transaction count, active users, unique users, and total transferred for the passed project based on the target chain
        if chain == "optimism":
            project_daily_transactions_df, project_transaction_flow_df = query_transaction_data_from_bq_optimism(client=client, project_addresses=just_addresses, grant_date=grant_date, token_conversion=token_conversion)
            
            # use the transaction flow dataset (which looks at abs(op amount)) to create a dataset that considers the direction of the transactions
            project_net_transaction_flow_df = make_net_transaction_dataset(transaction_flow_df=project_transaction_flow_df)
            datasets['net_transaction_flow'] = project_net_transaction_flow_df
        else:
            project_daily_transactions_df = query_transaction_data_from_bq_superchain(client=client, grant_date=grant_date, token_conversion=token_conversion, chain=chain)
            project_net_transaction_flow_df = None

        datasets['daily_transactions'] = project_daily_transactions_df

        # only query the tvl data if the project has an associated defi llama protocol
        if project_protocol and project_protocol is not None:
            project_chain_tvls_df, project_tvl_df, project_tokens_in_usd_df, project_tokens_df = query_tvl_data_from_bq(client=client, protocol=project_protocol)

            datasets['chain_tvls'] = project_chain_tvls_df
            datasets['tvl'] = project_tvl_df
            datasets['tokens_in_usd'] = project_tokens_in_usd_df

        project_forecasted_df = forecast_project(datasets=datasets, grant_date=grant_date)
        datasets['forecasted_metrics'] = project_forecasted_df

        if store_bq_datasets:
            save_datasets(project_name=project_name, datasets=datasets, data_path=STORED_DATA_PATH)

    else:
        # otherwise pull the datasets from the stored database at the passed path
        project_datasets = read_in_stored_dfs_for_projects(project_name=project_name, data_path=STORED_DATA_PATH, protocol=project_protocol)
        project_daily_transactions_df = project_datasets['daily_transactions']
        project_net_transaction_flow_df = project_datasets['net_transaction_flow']
        project_chain_tvls_df = project_datasets['chain_tvls']
        project_tokens_in_usd_df = project_datasets['tokens_in_usd']
        project_tvl_df = project_datasets['tvl']
        project_forecasted_df = project_datasets['forecasted']

    # define the tabs that will be displayed
    if project_protocol and project_protocol is not None:
        overview, core_metrics, tvl, stat_analysis = st.tabs(['Project Overview', 'Core Metrics', 'TVL', 'Statistical Analysis'])

    else:
        overview, core_metrics, stat_analysis = st.tabs(['Project Overview', 'Core Metrics', 'Statistical Analysis'])

    # display the project specifics and relevant addresses
    with overview: 
        overview_section(project=project)

    # display the line charts for the daily transactions data
    with core_metrics:
        core_metrics_section(daily_transactions_df=project_daily_transactions_df, net_transaction_flow_df=project_net_transaction_flow_df, project_addresses=project_addresses, grant_date=grant_date, display_by_address=display_by_address)

    # if the project has a corresponding defi llama protocol display the tvl related charts
    if project_protocol and project_protocol is not None:
        with tvl:
            tvl_section(chain_tvls_df=project_chain_tvls_df, tvl_df=project_tvl_df, tokens_in_usd_df=project_tokens_in_usd_df, grant_date=grant_date)

    # display the results of the synthetic control methods and hypothesis testing
    with stat_analysis:
        # if data is being pulled from bigquery, pass none for the project forecasted data so a new one will get generated in the stat_analysis_section function
        project_forecasted_df = None if pull_from_bigquery else project_forecasted_df
                
        if project_protocol and project_protocol is not None:
            stat_analysis_section(
                daily_transactions_df = project_daily_transactions_df,
                net_transaction_flow_df = project_net_transaction_flow_df,
                forecasted_df = project_forecasted_df,
                grant_date = grant_date,
                tvl_df = project_tvl_df
            )            
        else:
            stat_analysis_section(
                daily_transactions_df = project_daily_transactions_df,
                net_transaction_flow_df = project_net_transaction_flow_df,
                forecasted_df = project_forecasted_df,
                grant_date = grant_date,
                tvl_df = None
            )


if __name__ == "__main__":
    main()
