import streamlit as st
from datetime import datetime
import plotly.express as px
import numpy as np
import pandas as pd
from typing import Any, Dict, Tuple, Callable, Optional

from config import GRANT_DATE
from utils import assign_grant_label, safe_execution

# plot tvl over time as a line chart
def tvl_over_time_chart(tvl_df: pd.DataFrame) -> None:

    filtered_tvl_df = tvl_df[tvl_df['readable_date'] >= datetime(2024, 1, 1)]

    filtered_tvl_df['grant_label'] = filtered_tvl_df.apply(assign_grant_label, axis=1)

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
def tvl_by_chain_and_token_chart(chain_tvls_df: pd.DataFrame) -> None:

    # filter data to start at the beginning of the year
    filtered_chain_tvl_df = chain_tvls_df[chain_tvls_df['readable_date'] >= datetime(2024, 1, 1)]

    filtered_chain_tvl_df['grant_label'] = filtered_chain_tvl_df.apply(assign_grant_label, axis=1)

    # allow user to select tokens
    selected_tokens = st.multiselect("Select Tokens", filtered_chain_tvl_df['token'].unique())
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
def tvl_over_time_section(tvl_df: pd.DataFrame, chain_tvls_df: pd.DataFrame) -> None:

    st.subheader("TVL Trends Over Time (YTD)")

    high_level, focused = st.tabs(['Overview Across Chains', 'Detailed by Chain and Token'])

    with high_level:
        tvl_over_time_chart(tvl_df)
    
    with focused:
        tvl_by_chain_and_token_chart(chain_tvls_df)

# plot tvl across all chains, comparing pre and post grant numbers
def tvl_across_chains_chart(chain_tvls_df: pd.DataFrame) -> None:
    # group by chain and sum the TVL values for pre- and post-grant periods
    chain_tvl_pre_grant = chain_tvls_df[chain_tvls_df['readable_date'] < GRANT_DATE].groupby('chain')['value'].sum().reset_index()
    chain_tvl_post_grant = chain_tvls_df[chain_tvls_df['readable_date'] >= GRANT_DATE].groupby('chain')['value'].sum().reset_index()

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
    st.plotly_chart(fig)

# plot tvl of each token as a bar chart
def tvl_across_tokens_chart(tokens_in_usd_df: pd.DataFrame) -> None:

    # group by token and sum the TVL values
    token_tvl_pre_grant = tokens_in_usd_df[tokens_in_usd_df['readable_date'] < GRANT_DATE].groupby('token')['value'].sum().reset_index()
    token_tvl_post_grant = tokens_in_usd_df[tokens_in_usd_df['readable_date'] >= GRANT_DATE].groupby('token')['value'].sum().reset_index()

    # filter out rows with non-positive values (to avoid log errors)
    token_tvl_pre_grant = token_tvl_pre_grant[token_tvl_pre_grant['value'] > 0]
    token_tvl_post_grant = token_tvl_post_grant[token_tvl_post_grant['value'] > 0]

    # compute the log of the TVL values and drop the original values
    token_tvl_pre_grant['pre_grant'] = np.log(token_tvl_pre_grant['value'])
    token_tvl_pre_grant.drop('value', axis=1, inplace=True)
    token_tvl_post_grant['post_grant'] = np.log(token_tvl_post_grant['value'])
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
def tvl_volatility_by_chain_chart(chain_tvls_df: pd.DataFrame) -> None:
    # calculate daily changes
    chain_tvls_df['daily_change'] = chain_tvls_df.groupby(['chain', 'token'])['value'].diff()
    chain_tvls_df.dropna(subset=['daily_change'], inplace=True)
    chain_tvls_df['grant_label'] = chain_tvls_df.apply(assign_grant_label, axis=1)

    # user selects tokens
    selected_tokens = st.multiselect("Select Tokens", chain_tvls_df['token'].unique())
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
def tvl_distribution_section(chain_tvls_df: pd.DataFrame, tvl_df: pd.DataFrame) -> None:

    st.subheader("Distribution of Relative Daily Changes in TVL (YTD)")

    # filter dates to compare pre- and post-grant date
    tvl_df['readable_date'] = pd.to_datetime(tvl_df['readable_date'])

    # filter data to start at the beginning of the year
    tvl_df = tvl_df[tvl_df['readable_date'] >= datetime(2024, 1, 1)]

    tvl_df = tvl_df.sort_values(by='readable_date')
    tvl_df['tvl_diff'] = tvl_df['totalLiquidityUSD'].diff()
    tvl_df['relative_change'] = tvl_df['tvl_diff'] / tvl_df['totalLiquidityUSD'].shift(1)

    # assign pre/post-grant labels
    tvl_df['grant_label'] = tvl_df.apply(assign_grant_label, axis=1)

    # define tabs
    tab1, tab2, tab3 = st.tabs(['Distribution of Daily Changes', 'Daily Changes Over Time', 'Volatility by Chain'])

    with tab1:
        tvl_daily_changes_chart(tvl_df)
    
    with tab2:
        daily_tvl_changes_chart(tvl_df)

    with tab3:
        tvl_volatility_by_chain_chart(chain_tvls_df)


# main function to visualize the full tvl section
def tvl_section(chain_tvls_df, tvl_df, tokens_in_usd_df) -> None:
    st.header("Defi Llama Metrics")

    chain_tvls_df['readable_date'] = pd.to_datetime(chain_tvls_df['readable_date'])
    tvl_df['readable_date'] = pd.to_datetime(tvl_df['readable_date'])
    tokens_in_usd_df['readable_date'] = pd.to_datetime(tokens_in_usd_df['readable_date'])
    
    try:
    # execute each section safely (don't display and skip the plot if the execution fails)
        safe_execution(tvl_over_time_section, tvl_df, chain_tvls_df)
        safe_execution(tvl_across_chains_chart, chain_tvls_df)
        safe_execution(tvl_across_tokens_chart, tokens_in_usd_df)
        safe_execution(tvl_distribution_section, chain_tvls_df, tvl_df)
    except Exception:
        pass