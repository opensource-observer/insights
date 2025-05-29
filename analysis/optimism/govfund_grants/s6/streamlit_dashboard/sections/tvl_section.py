import streamlit as st
from datetime import datetime
import plotly.express as px
import numpy as np
import pandas as pd
from typing import Optional

from utils import assign_grant_label, safe_execution

# plot tvl over time as a line chart
def tvl_over_time_chart(tvl_df: pd.DataFrame, grant_date: datetime) -> None:

    # filter to just show YTD
    filtered_tvl_df = tvl_df[tvl_df['readable_date'] >= datetime(2024, 1, 1)]
    filtered_tvl_df['grant_label'] = filtered_tvl_df.apply(assign_grant_label, axis=1, grant_date=grant_date)

    # pivot the dataset so pre grant and post grant have their own columns
    pivoted_tvl_df = filtered_tvl_df.pivot(index='readable_date', columns='grant_label', values='totalLiquidityUSD')

    fig = px.line(pivoted_tvl_df)
    fig.update_layout(
        legend_title_text='',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title='',
        yaxis_title='TVL (USD)',
        template="plotly_white"
    )

    st.plotly_chart(fig)

# plot tvl over time as a line chart, with chain and token selection offered for users
def tvl_by_chain_and_token_chart(chain_tvls_df: pd.DataFrame, grant_date: datetime) -> None:

    # filter data to start at the beginning of the year
    filtered_chain_tvl_df = chain_tvls_df[chain_tvls_df['readable_date'] >= datetime(2024, 1, 1)]
    filtered_chain_tvl_df['grant_label'] = filtered_chain_tvl_df.apply(assign_grant_label, axis=1, grant_date=grant_date)

    # allow user to select tokens
    all_chain_options = [f'All {chain} tokens' for chain in filtered_chain_tvl_df['chain'].unique()]
    token_options = all_chain_options + list(filtered_chain_tvl_df['token'].unique())
    selected_tokens = st.multiselect("Select Tokens", token_options)

    # check if any "All {chain} tokens" option is selected
    selected_all_chain_option = [opt for opt in selected_tokens if opt in all_chain_options]

    if selected_all_chain_option:
        if len(selected_tokens) > 1:
            st.warning("You can only select one 'All {chain} tokens' option at a time. Please deselect other options.")
            return
        else:
            # extract the chain name from the selected "All {chain} tokens" option
            chain = selected_all_chain_option[0].replace('All ', '').replace(' tokens', '')

            # filter the DataFrame to include only the selected chain
            filtered_chain_tvl_df = filtered_chain_tvl_df[filtered_chain_tvl_df['chain'] == chain]

            # clear other selections and display filtered data
            st.write(f"All {chain} tokens: {", ".join(filtered_chain_tvl_df['token'].unique())}")
    else:
        # filter by individual token selections
        filtered_chain_tvl_df = filtered_chain_tvl_df[filtered_chain_tvl_df['token'].isin(selected_tokens)]

        # allow user to select chains
        selected_chains = st.multiselect("Select Chains", filtered_chain_tvl_df['chain'].unique())
        filtered_chain_tvl_df = filtered_chain_tvl_df[filtered_chain_tvl_df['chain'].isin(selected_chains)]
    
    # group data by date and grant label, summing the values
    grouped_tvl = (
        filtered_chain_tvl_df
        .groupby(['readable_date', 'grant_label'], as_index=False)
        .agg({'value': 'sum'})
    )

    # create the line chart
    fig = px.line(grouped_tvl, x='readable_date', y='value', color='grant_label')

    # update layout for better visualization
    fig.update_layout(
        legend_title_text='',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title='',
        yaxis_title='TVL (USD)',
        template="plotly_white"
    )

    # display the chart
    st.plotly_chart(fig)

# create the section that displays both tvl over time line charts
def tvl_over_time_section(tvl_df: pd.DataFrame, chain_tvls_df: pd.DataFrame, grant_date: datetime) -> None:

    st.subheader("TVL Trends Over Time (YTD)")
    high_level, focused = st.tabs(['Overview Across Chains', 'Detailed by Chain and Token'])

    with high_level:
        try:
            tvl_over_time_chart(tvl_df=tvl_df, grant_date=grant_date)
        except:
            st.warning("Error occured while creating these visualizations")
    
    with focused:
        try:
            tvl_by_chain_and_token_chart(chain_tvls_df=chain_tvls_df, grant_date=grant_date)
        except:
            st.warning("Error occured while creating these visualizations")

# plot tvl across all chains, comparing pre and post grant numbers
def tvl_across_chains_chart(chain_tvls_df: pd.DataFrame, grant_date: datetime) -> None:
    # group by chain and sum the TVL values for pre- and post-grant periods
    chain_tvl_pre_grant = chain_tvls_df[chain_tvls_df['readable_date'] < grant_date].groupby('chain')['value'].sum().reset_index()
    chain_tvl_post_grant = chain_tvls_df[chain_tvls_df['readable_date'] >= grant_date].groupby('chain')['value'].sum().reset_index()

    # filter out rows with non-positive values (to avoid log errors)
    chain_tvl_pre_grant = chain_tvl_pre_grant[chain_tvl_pre_grant['value'] > 0]
    chain_tvl_post_grant = chain_tvl_post_grant[chain_tvl_post_grant['value'] > 0]

    # compute the log of the TVL values
    chain_tvl_pre_grant['pre_grant'] = np.log(chain_tvl_pre_grant['value'])
    chain_tvl_post_grant['post_grant'] = np.log(chain_tvl_post_grant['value'])

    # drop the original 'value' column
    chain_tvl_pre_grant.drop('value', axis=1, inplace=True)
    chain_tvl_post_grant.drop('value', axis=1, inplace=True)

    # merge the two tables together
    chain_tvl_summary = chain_tvl_pre_grant.merge(chain_tvl_post_grant, on='chain')

    # set 'chain' as the index for streamlit bar chart
    chain_tvl_summary = chain_tvl_summary.set_index('chain')

    # create the bar chart
    fig = px.bar(chain_tvl_summary, title='TVL Distribution Across Chains (Log Scale)')

    # update the layout to improve the legend and axis labels
    fig.update_layout(
        legend_title_text='',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title='Chain',
        yaxis_title='Log of TVL (USD)',
    )

    # display the chart
    if chain_tvl_summary is not None and not chain_tvl_summary.empty:
        st.plotly_chart(fig)

# plot tvl of each token as a bar chart
def tvl_across_tokens_chart(tokens_in_usd_df: pd.DataFrame, grant_date: datetime) -> None:

    # group by token and sum the TVL values
    token_tvl_pre_grant = tokens_in_usd_df[tokens_in_usd_df['readable_date'] < grant_date].groupby('token')['value'].sum().reset_index()
    token_tvl_post_grant = tokens_in_usd_df[tokens_in_usd_df['readable_date'] >= grant_date].groupby('token')['value'].sum().reset_index()

    # filter out rows with non-positive values (to avoid log errors)
    token_tvl_pre_grant = token_tvl_pre_grant[token_tvl_pre_grant['value'] > 0]
    token_tvl_post_grant = token_tvl_post_grant[token_tvl_post_grant['value'] > 0]

    # compute the log of the TVL values and drop the original values
    token_tvl_pre_grant['pre grant'] = np.log(token_tvl_pre_grant['value'])
    token_tvl_pre_grant.drop('value', axis=1, inplace=True)
    token_tvl_post_grant['post grant'] = np.log(token_tvl_post_grant['value'])
    token_tvl_post_grant.drop('value', axis=1, inplace=True)

    # merge the two tables together
    token_tvl_summary = token_tvl_pre_grant.merge(token_tvl_post_grant, on='token')

    # set 'token' as the index for streamlit bar chart
    token_tvl_summary = token_tvl_summary.set_index('token')

    # plot the bar chart
    fig = px.bar(token_tvl_summary, title="TVL Composition by Token (Log Scale)")

    fig.update_layout(
        legend_title_text='',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title='Token',
        yaxis_title='Log of TVL (USD)',
    )

    if token_tvl_summary is not None and not token_tvl_summary.empty:
        st.plotly_chart(fig)

# plot the distribution of how tvl changes with each consecutive day as a histogram
def tvl_daily_changes_chart(tvl_df: pd.DataFrame) -> None:
    # create histogram
    fig = px.histogram(
        tvl_df,
        x='relative_change',
        color='grant_label',
        nbins=50,
        marginal="box"  # add a boxplot on the top for distribution insights
    )

    fig.update_layout(
        legend_title_text='',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title="Relative Daily Change",
        yaxis_title="Frequency",
        template="plotly_white"
    )

    if tvl_df is not None and not tvl_df.empty:
        # display in streamlit
        st.plotly_chart(fig)

# plot the distribution of how tvl changes with each consecutive day as a line chart
def daily_tvl_changes_chart(tvl_df: pd.DataFrame) -> None:
    # create line chart
    fig = px.line(
        tvl_df,
        x='readable_date',
        y='relative_change',
        color='grant_label'
    )

    fig.update_layout(
        legend_title_text='',   
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title="",
        yaxis_title="Relative Daily Change",
        template="plotly_white"
    )

    # display in Streamlit
    st.plotly_chart(fig)

# plot the volatility of each chain with allowing for users to select target tokens
def tvl_volatility_by_chain_chart(chain_tvls_df: pd.DataFrame, grant_date: datetime) -> None:
    # calculate daily changes
    chain_tvls_df['daily_change'] = chain_tvls_df.groupby(['chain', 'token'])['value'].diff()
    chain_tvls_df.dropna(subset=['daily_change'], inplace=True)
    chain_tvls_df['grant_label'] = chain_tvls_df.apply(assign_grant_label, axis=1, grant_date=grant_date)

    # user selects tokens
    token_options = ["All tokens"] + list(chain_tvls_df['token'].unique())
    selected_tokens = st.multiselect("Select Tokens", token_options)

    if not selected_tokens:
        st.warning("Please select at least one address.")
        return

    # handle the "All" option
    if "All tokens" in selected_tokens and len(selected_tokens) > 1:
        st.warning("You cannot select individual tokens when 'All' is selected.")
        selected_tokens = ["All tokens"]
        return

    if "All tokens" in selected_tokens:
        # select all tokens
        selected_chain_tvls_df = chain_tvls_df
    else:
        # filter data for the selected tokens
        selected_chain_tvls_df = chain_tvls_df[chain_tvls_df['token'].isin(selected_tokens)]

    # create horizontal box plot
    fig = px.box(
        selected_chain_tvls_df,
        x='daily_change',
        y='chain',
        color='grant_label',  # separate pre- and post-grant labels
        title="Daily Changes in TVL by Chain and Grant Period",
        labels={'daily_change': 'Daily Change in TVL (USD)', 'chain': 'Blockchain Network'},
    )

    # update layout for better visualization
    fig.update_layout(
        legend_title_text='',   
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title="",
        yaxis_title="",
        template="plotly_white"
    )

    # display in streamlit
    st.plotly_chart(fig)

# create the section that displays the plots surrounding the tvl distribution
def tvl_distribution_section(chain_tvls_df: pd.DataFrame, tvl_df: pd.DataFrame, grant_date: datetime) -> None:

    st.subheader("Distribution of Relative Daily Changes in TVL (YTD)")

    # filter dates to compare pre- and post-grant date
    tvl_df['readable_date'] = pd.to_datetime(
            tvl_df['readable_date'], 
            format='%Y-%m-%d %H:%M:%S', 
            errors='coerce'
        )

    # filter data to start at the beginning of the year
    tvl_df = tvl_df[tvl_df['readable_date'] >= datetime(2024, 1, 1)]

    tvl_df = tvl_df.sort_values(by='readable_date')
    tvl_df['tvl_diff'] = tvl_df['totalLiquidityUSD'].diff()
    tvl_df['relative_change'] = tvl_df['tvl_diff'] / tvl_df['totalLiquidityUSD'].shift(1)

    # assign pre/post-grant labels
    tvl_df['grant_label'] = tvl_df.apply(assign_grant_label, axis=1, grant_date=grant_date)

    # define tabs
    tab1, tab2, tab3 = st.tabs(['Distribution of Daily Changes', 'Daily Changes Over Time', 'Volatility by Chain'])

    with tab1:
        try:
            tvl_daily_changes_chart(tvl_df)
        except:
            st.warning("Error occured while creating these visualizations")
    
    with tab2:
        try:
            daily_tvl_changes_chart(tvl_df)
        except:
            st.warning("Error occured while creating these visualizations")

    with tab3:
        try:
            tvl_volatility_by_chain_chart(chain_tvls_df, grant_date)
        except:
            st.warning("Error occured while creating these visualizations")

# main function to visualize the full tvl section
def tvl_section(grant_date: datetime, chain_tvls_df: Optional[pd.DataFrame] = None, tvl_df: Optional[pd.DataFrame] = None, tokens_in_usd_df: Optional[pd.DataFrame] = None) -> None:

    protocols = []

    if chain_tvls_df is not None and not chain_tvls_df.empty:
        chain_tvls_df['readable_date'] = pd.to_datetime(
            chain_tvls_df['readable_date'], 
            format='%Y-%m-%d %H:%M:%S', 
            errors='coerce'
        )
        protocols.extend(chain_tvls_df["protocol"].values)
    
    if tvl_df is not None and not tvl_df.empty:
        tvl_df['readable_date'] = pd.to_datetime(
            tvl_df['readable_date'], 
            format='%Y-%m-%d %H:%M:%S', 
            errors='coerce'
        )
        protocols.extend(tvl_df["protocol"].values)
    
    if tokens_in_usd_df is not None and not tokens_in_usd_df.empty:
        tokens_in_usd_df['readable_date'] = pd.to_datetime(
            tokens_in_usd_df['readable_date'], 
            format='%Y-%m-%d %H:%M:%S', 
            errors='coerce'
        )
        protocols.extend(tokens_in_usd_df["protocol"].values)
    
    protocols = list(set(protocols))

    for target_protocol in protocols:
        if (len(tvl_df[tvl_df["protocol"] == target_protocol]) < 2) and (len(chain_tvls_df[chain_tvls_df["protocol"] == target_protocol]) < 2) and (len(tokens_in_usd_df[tokens_in_usd_df["protocol"] == target_protocol]) < 2):
            protocols.remove(target_protocol)

    selected_protocol = st.selectbox("Select the desired DeFi-Llama protocol", protocols)

    if chain_tvls_df is not None and not chain_tvls_df.empty:
        chain_tvls_df_selected = chain_tvls_df[chain_tvls_df["protocol"] == selected_protocol]

    if tvl_df is not None and not tvl_df.empty:
        tvl_df_selected = tvl_df[tvl_df["protocol"] == selected_protocol]
    
    if tokens_in_usd_df is not None and not tokens_in_usd_df.empty:
        tokens_in_usd_df_selected = tokens_in_usd_df[tokens_in_usd_df["protocol"] == selected_protocol]

    try:
    # execute each section safely (don't display and skip the plot if the execution fails)
        safe_execution(tvl_over_time_section, tvl_df_selected, chain_tvls_df_selected, grant_date)
        safe_execution(tvl_across_chains_chart, chain_tvls_df_selected, grant_date)
        safe_execution(tvl_across_tokens_chart, tokens_in_usd_df_selected, grant_date)
        safe_execution(tvl_distribution_section, chain_tvls_df_selected, tvl_df_selected, grant_date)
    except Exception:
        pass
