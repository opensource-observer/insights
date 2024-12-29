from single_project_visualizations import process_project, generate_dates
from typing import Optional
from google.cloud import bigquery
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import t

# constants for querying the project network and the bigquery project
PROJECT_NETWORK = 'mainnet'
BIGQUERY_PROJECT_NAME = 'oso-data-436717'

# queries the minimum transaction date for a given set of project addresses and start date
def query_transactions_min_date(client: bigquery.Client, project_addresses: list[str], start_date: str) -> pd.Timestamp | None:
    try:
        # handles both single and multiple project addresses
        if len(project_addresses) == 1:
            addresses_condition = f"= '{project_addresses[0]}'"
        else:
            addresses_condition = f"IN {tuple(project_addresses)}"

        # sql query to fetch the minimum transaction date from the bigquery table
        min_date_query = f"""
        SELECT MIN(dt) AS transaction_date
        FROM `{BIGQUERY_PROJECT_NAME}.optimism_superchain_raw_onchain_data.transactions`
        WHERE network = '{PROJECT_NETWORK}'
            AND (to_address {addresses_condition}
            OR from_address {addresses_condition})
            AND dt >= '{start_date}'
        """

        # executes the query and converts the result to a dataframe
        min_date_result = client.query(min_date_query)
        min_date_df = min_date_result.to_dataframe()

        # checks if the result is not empty and parses the transaction date
        if not min_date_df.empty and min_date_df.loc[0, 'transaction_date']:
            return pd.to_datetime(min_date_df.loc[0, 'transaction_date'])

    except Exception as e:
        # logs any errors that occur during the query
        print(f"Error querying minimum transaction date: {e}")

    # returns None if the query fails
    return None

# splits a dataset into pre- and post-grant dataframes based on the grant date
def split_dataset(dataset: pd.DataFrame, grant_date: datetime) -> tuple[pd.DataFrame, pd.DataFrame]:
    # identifies the date column based on the dataset
    date_col = 'transaction_date' if 'transaction_date' in dataset.columns else 'readable_date'

    # ensures the date column is in datetime format
    dataset[date_col] = pd.to_datetime(dataset[date_col])

    # calculates the minimum date and the range of time since the grant
    min_date = dataset[date_col].min()
    time_since_grant = datetime.today() - grant_date

    # calculates the start date for the pre-grant dataset
    pre_grant_start_date = grant_date - time_since_grant

    # adjusts the start date to ensure it does not precede the dataset's minimum date
    pre_grant_start_date = max(pre_grant_start_date, min_date)

    # creates separate dataframes for pre- and post-grant data
    pre_grant_df = dataset[(dataset[date_col] < grant_date) & (dataset[date_col] >= pre_grant_start_date)]
    post_grant_df = dataset[dataset[date_col] >= grant_date]

    return pre_grant_df, post_grant_df

# aggregates metrics for datasets split by pre- and post-grant periods
def aggregate_metrics(split_datasets: list[tuple[pd.DataFrame, pd.DataFrame]], metrics: list[str]) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    aggregated_metrics = []

    # iterates through split datasets
    for pre_grant_df, post_grant_df in split_datasets:
        select_metrics = [metric for metric in metrics if metric in pre_grant_df.columns]
        date_col = 'transaction_date' if 'transaction_date' in pre_grant_df.columns else 'readable_date'
        agg_pre_grant_df, agg_post_grant_df = None, None

        # aggregates data by summing the metrics for each time period
        for metric in select_metrics:
            curr_pre_agg = pre_grant_df.groupby(date_col)[metric].sum().reset_index()
            if agg_pre_grant_df is not None:
                agg_pre_grant_df = agg_pre_grant_df.merge(curr_pre_agg, on=date_col, how='inner')
            else:
                agg_pre_grant_df = curr_pre_agg

            curr_post_agg = post_grant_df.groupby(date_col)[metric].sum().reset_index()
            if agg_post_grant_df is not None:
                agg_post_grant_df = agg_post_grant_df.merge(curr_post_agg, on=date_col, how='inner')
            else:
                agg_post_grant_df = curr_post_agg

        # calculates descriptive statistics for both periods
        if agg_pre_grant_df is not None:
            pre_grant_stats = agg_pre_grant_df[select_metrics].agg(['count', 'mean', 'std', 'var']).transpose()
        else:
            pre_grant_stats = pd.DataFrame()

        if agg_post_grant_df is not None:
            post_grant_stats = agg_post_grant_df[select_metrics].agg(['count', 'mean', 'std', 'var']).transpose()
        else:
            post_grant_stats = pd.DataFrame()

        aggregated_metrics.append((pre_grant_stats, post_grant_stats))

    return aggregated_metrics

# 2-sample hypothesis test
def test_statistic(sample1: pd.Series, sample2: pd.Series) -> tuple[float, float]:
    # define our constants
    mu1, mu2 = sample1['mean'], sample2['mean']
    n1, n2 = sample1['count'], sample2['count']
    s1_squared, s2_squared = sample1['var'], sample2['var']

    # determine if we can consider variances to be equal
    var_ratio = sample1['var'] / sample2['var']
    if var_ratio <= 2 and var_ratio >= 0.5:
        # variances equal so use students t-test (pooled variance)
        s_pooled_squared = ((n1 - 1) * s1_squared + (n2 - 1) * s2_squared) / (n1 + n2 - 2)
        t_stat = (mu1 - mu2) / s_pooled_squared * np.sqrt((1/n1) + (1/n2))
        df = n1 + n2 - 2
        
    else:
        # variances not equal so use welch's t
        t_stat = (mu1 - mu2) / np.sqrt((s1_squared/n1) + (s2_squared/n2))
        df = (((s1_squared / n1) + (s2_squared / n2))**2) / ((((s1_squared/n1)**2)/(n1-1)) + (((s2_squared/n2)**2)/(n2-1)))

    return t_stat, df

# function to calculate p-value
def t_test(t_stat: float, df: float) -> float:
    # calculate the two-tailed p-value
    p_value = 2 * (1 - t.cdf(abs(t_stat), df))

    return p_value

# conduct the t-stat tests and result a dataframe of the results
def determine_statistics(sample1_df: pd.DataFrame, sample2_df: pd.DataFrame) -> pd.DataFrame:
    metric_table = []

    # iterate over the metrics (assumed to be the index of the DataFrame)
    for i, metric in enumerate(sample2_df.index):
        try:
            # calculate t-statistic and degrees of freedom
            t_stat, df = test_statistic(sample1_df.iloc[i, :], sample2_df.iloc[i, :])

            # handle division by zero in percent_change
            sample1_grant_mean = sample1_df.iloc[i]['mean']
            sample2_grant_mean = sample2_df.iloc[i]['mean']
            if sample1_grant_mean != 0:
                percent_change = round(((sample2_grant_mean - sample1_grant_mean) / sample1_grant_mean), 4)
            else:
                percent_change = None  # avoid division by zero

            # append the metric details to the metric_table
            metric_dict = {
                'metric': metric,
                'pre_grant_n': round(sample1_df.iloc[i]['count'], 4),
                'pre_grant_mean': round(sample1_grant_mean, 4),
                'pre_grant_std': round(sample1_df.iloc[i]['std'], 4),
                'post_grant_n': round(sample2_df.iloc[i]['count'], 4),
                'post_grant_mean': round(sample2_grant_mean, 4),
                'post_grant_std': round(sample2_df.iloc[i]['std'], 4),
                'percent_change': percent_change,
                'test_statistic': round(t_stat, 4),
                'degrees_of_freedom': round(df, 4),
                'p_value': round(t_test(t_stat, df), 4)
            }

            metric_table.append(metric_dict)

        except Exception as e:
            print(f"Error processing metric {metric}: {e}")
            continue

    # convert the list of dictionaries to a DataFrame
    return pd.DataFrame(metric_table)

# filters the displayed tvl data based on user inputted chains and tokens
def adjusted_tvl_metrics(filtered_chain_tvl_df: pd.DataFrame, grant_date: datetime) -> Optional[pd.DataFrame]:
    # user selection for tokens
    selected_tokens = st.multiselect("Select Tokens", filtered_chain_tvl_df['token'].unique())
    filtered_chain_tvl_df = filtered_chain_tvl_df[filtered_chain_tvl_df['token'].isin(selected_tokens)]

    # user selection for chains
    selected_chains = st.multiselect("Select Chains", filtered_chain_tvl_df['chain'].unique())
    filtered_chain_tvl_df = filtered_chain_tvl_df[filtered_chain_tvl_df['chain'].isin(selected_chains)]

    # ensure there's data after filtering
    if filtered_chain_tvl_df is not None and filtered_chain_tvl_df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # split the dataset based on grant date
    pre_grant_tvl_df, post_grant_tvl_df = split_dataset(filtered_chain_tvl_df, grant_date)

    # ensure that there are enough data points on both ends of the split
    if len(pre_grant_tvl_df) < 10 or len(post_grant_tvl_df) < 10:
        st.warning("Not enough data available for the selected filters.")
        return

    # determine the sample metrics
    aggregated_metrics = aggregate_metrics([(pre_grant_tvl_df, post_grant_tvl_df)], ['value'])

    # conduct the t-test and return the results
    updated_tvl_metrics = determine_statistics(aggregated_metrics[0][0], aggregated_metrics[0][1])
    updated_tvl_metrics['metric'] = updated_tvl_metrics['metric'].replace('value', 'TVL by Token and Chain (USD)')
    return updated_tvl_metrics

# function to visualize the significance of the t-test
def plot_t_test_streamlit(
        metrics: pd.DataFrame,
        grant_date: datetime,
        filtered_chain_tvl_df: Optional[pd.DataFrame] = None
    ) -> None:
    st.subheader("T-Test Simulation for Selected Metric")

    # user selection for metric
    metric_options = metrics['metric'].unique()
    if filtered_chain_tvl_df is not None and not filtered_chain_tvl_df.empty:
        metric_options = np.append(metric_options, 'TVL by Token and Chain (USD)')
    selected_metric = st.selectbox("Select Metric", metric_options)

    alpha = st.slider(
        label="Select an alpha value",
        min_value=0.0,
        max_value=1.0,
        value=0.05,  # default value
        step=0.01   # step size
    )

    # handle tvl by token/chain separately
    if selected_metric == 'TVL by Token and Chain (USD)':
        metrics = adjusted_tvl_metrics(filtered_chain_tvl_df, grant_date)
        print(metrics)

    if metrics is not None:
        # filter for the selected metric
        metric_row = metrics.loc[metrics['metric'] == selected_metric]

        if metric_row is not None and metric_row.empty:
            st.warning(f"No data available for the selected metric: {selected_metric}")
            return

        if selected_metric == 'TVL by Token and Chain (USD)':
            st.write("T-Test Results")
            st.dataframe(metrics)

        # degrees of freedom for the selected metric
        df = metric_row['degrees_of_freedom'].iloc[0]

        # create x values for the t-distribution
        x = np.linspace(-10, 10, 1000)  # extended range for t-stat visibility
        y = t.pdf(x, df)

        # critical values for two-tailed test
        critical_value = t.ppf(1 - alpha / 2, df)

        # get the t-statistic for the selected metric
        t_stat = metric_row['test_statistic'].iloc[0]

        # adjust x-axis range to ensure t-stat is always visible
        x_min = min(-4, -1 * (t_stat + 1))
        x_max = max(4, t_stat + 1)

        # generate data for rejection regions
        rejection_x_left = x[x <= -critical_value]
        rejection_y_left = y[x <= -critical_value]
        rejection_x_right = x[x >= critical_value]
        rejection_y_right = y[x >= critical_value]

        # plot t-distribution
        fig = px.line(
            x=x,
            y=y,
            labels={'x': 't-value', 'y': 'Probability Density'},
            title=f"T-Test of {selected_metric} at alpha={alpha}"
        )

        # add rejection region shading (merged for left and right)
        fig.add_trace(
            go.Scatter(
                x=np.concatenate([rejection_x_left, rejection_x_left[::-1]]),
                y=np.concatenate([rejection_y_left, np.zeros_like(rejection_y_left)]),
                fill='toself',
                fillcolor='rgba(255, 0, 0, 0.3)',
                line=dict(color='rgba(255,0,0,0)'),
                name="Rejection Region"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=np.concatenate([rejection_x_right, rejection_x_right[::-1]]),
                y=np.concatenate([rejection_y_right, np.zeros_like(rejection_y_right)]),
                fill='toself',
                fillcolor='rgba(255, 0, 0, 0.3)',
                line=dict(color='rgba(255,0,0,0)'),
                showlegend=False  # hide duplicate legend entry
            )
        )

        # add critical value lines (red dotted, single legend)
        fig.add_trace(
            go.Scatter(
                x=[-critical_value, -critical_value],
                y=[0, max(y)],
                mode='lines',
                line=dict(color='red', dash='dot'),
                name="Critical Values"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[critical_value, critical_value],
                y=[0, max(y)],
                mode='lines',
                line=dict(color='red', dash='dot'),
                showlegend=False  # Hhde duplicate legend entry
            )
        )

        # add t-statistic line (green)
        fig.add_trace(
            go.Scatter(
                x=[t_stat, t_stat],
                y=[0, max(y)],  # extend the line to the top of the plot
                mode='lines',
                line=dict(color='green', width=2),
                name=f"T-Statistic: {t_stat:.2f}"
            )
        )

        # update layout for better visualization
        fig.update_layout(
            xaxis=dict(range=[x_min, x_max]),
            yaxis_title="Probability Density",
            legend_title="",
            template="plotly_white",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        # display the chart in Streamlit
        st.plotly_chart(fig)

# main function to generate the hypothesis testing section
def hypothesis_testing_section(client, project_addresses, grant_date, chain_tvls_df=None, tvl_df=None):
    st.header("Statistical Analysis Through Hypothesis Testing")

    # create a pre-grant date range equal to the post-grant date length
    time_since_interval = datetime.today() - grant_date
    min_start = grant_date - time_since_interval
    min_start_string = min_start.strftime('%Y-%m-%d')

    # determine the minimum date of a transaction from the dataset
    transactions_min_date = query_transactions_min_date(client, project_addresses, min_start_string)

    # ensure transactions_min_date is valid before comparison
    if transactions_min_date is not None:
        # determine the minimum start date we can use
        min_start = max(transactions_min_date, min_start)

    min_start_string = min_start.strftime('%Y-%m-%d')

    # create a templated dataframe of dates from the minimum start date
    dates = generate_dates(min_start)

    # query bigquery to retrieve the necessary data for the above dates
    daily_transactions, _, net_op_flow = process_project(client, project_addresses, dates, min_start_string)

    # aggregate all of the datasets to determine sample statistics
    all_aggregated_metrics = []

    # split each dataset based on the grant date and then aggregate within each split dataset
    daily_transactions_split = split_dataset(daily_transactions, grant_date)
    daily_transaction_targets = ['transaction_cnt', 'active_users', 'unique_users', 'total_op_transferred_in_tokens']
    all_aggregated_metrics.extend(aggregate_metrics([daily_transactions_split], daily_transaction_targets))

    # repeat for this dataset
    net_op_flow_split = split_dataset(net_op_flow, grant_date)
    net_op_flow_targets = ['cum_op_transferred_in_tokens']
    all_aggregated_metrics.extend(aggregate_metrics([net_op_flow_split], net_op_flow_targets))

    # repeat for this dataset if defi llama data is available
    if tvl_df is not None and not tvl_df.empty:
        defi_llama_split = split_dataset(tvl_df, grant_date)
        defi_llama_targets = ['totalLiquidityUSD']
        all_aggregated_metrics.extend(aggregate_metrics([defi_llama_split], defi_llama_targets))
    
    # conduct a t-test on each dataset
    metric_tables = []
    for pre_grant_metric, post_grant_metric in all_aggregated_metrics:
        metric_tables.append(determine_statistics(pre_grant_metric, post_grant_metric))

    st.subheader("T-Test Results For Core Metrics")

    # rename columns for when they're displayed on the dashboard
    metric_table = pd.concat(metric_tables)
    renamed_cols = {
        'transaction_cnt': 'Daily Transaction Count',
        'active_users': 'Daily Active Users',
        'unique_users': 'Daily Unique Users',
        'total_op_transferred_in_tokens': 'Total OP Transferred (Tokens)',
        'cum_op_transferred_in_tokens': 'Net OP Transferred (Tokens)',
        'totalLiquidityUSD': 'TVL (USD)'
    }
    metric_table['metric'] = metric_table['metric'].replace(renamed_cols)
    st.dataframe(metric_table)

    # plot the t-test simulator based on whether or not the defi llama is available
    if chain_tvls_df is not None and not chain_tvls_df.empty:
        chain_tvls_df['readable_date'] = pd.to_datetime(chain_tvls_df['readable_date'])
        filtered_chain_tvls_df = chain_tvls_df[chain_tvls_df['readable_date'] >= datetime(2024, 1, 1)]
        plot_t_test_streamlit(metric_table, grant_date, filtered_chain_tvls_df)
    else:
        plot_t_test_streamlit(metric_table, grant_date)
