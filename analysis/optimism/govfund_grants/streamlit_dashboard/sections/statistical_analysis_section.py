from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np
from typing import Tuple, Optional
from scipy.stats import t

from processing import split_dataset_by_date
from utils import assign_grant_label, determine_date_col

##### Hypothesis Testing Section #####

# aggregates metrics for datasets split by pre- and post-grant periods
def aggregate_split_datasets_by_metrics(split_datasets: list[tuple[pd.DataFrame, pd.DataFrame]], metrics: list[str]) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    aggregated_metrics = []

    # iterates through split datasets
    for pre_grant_df, post_grant_df in split_datasets:
        select_metrics = [metric for metric in metrics if metric in pre_grant_df.columns]
        date_col = determine_date_col(df=pre_grant_df)
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

# sum each datasets' metrics over all of the relevant addresses and then merge all 3 datasets
def aggregate_datasets(daily_transactions_df: pd.DataFrame, tvl_df: pd.DataFrame, grant_date: datetime, net_transaction_flow_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    
    # rename date columns so they all align
    daily_transactions_df.rename(columns={'transaction_date': 'date'}, inplace=True)
    daily_transactions_df['date'] = pd.to_datetime(daily_transactions_df['date'])

    if net_transaction_flow_df is not None and not net_transaction_flow_df.empty: 
        net_transaction_flow_df.rename(columns={"transaction_date": 'date'}, inplace=True)
        net_transaction_flow_df['date'] = pd.to_datetime(net_transaction_flow_df['date'])

    if tvl_df is not None and not tvl_df.empty: 
        tvl_df.drop('date', axis=1, inplace=True)
        tvl_df.rename(columns={'readable_date': 'date'}, inplace=True)
        tvl_df['date'] = pd.to_datetime(tvl_df['date'])

    # sum each day's metric over all of the relevant addresses
    daily_transactions_df = daily_transactions_df.groupby('date')[['transaction_cnt', 'active_users', 'unique_users', 'total_transferred']].sum().reset_index()
    
    if net_transaction_flow_df is not None and not net_transaction_flow_df.empty: 
        net_transaction_flow_df = net_transaction_flow_df.groupby('date')[['net_transferred_in_tokens']].sum().reset_index()
        net_transaction_flow_df['date'] = pd.to_datetime(net_transaction_flow_df['date'])
    
    if tvl_df is not None and not tvl_df.empty: 
        tvl_df = tvl_df.groupby('date')['totalLiquidityUSD'].sum().reset_index()

    # rename columns so for when they're displayed
    agg_df = daily_transactions_df.copy()
    agg_df.rename(columns={'transaction_cnt': 'Transaction Count', 
                            'active_users': 'Active Users', 
                            'unique_users': 'Unique Users',
                            'total_transferred': 'Total Transferred',
                            'cum_transferred': 'Cumulative Transferred'}, inplace=True)

    if net_transaction_flow_df is not None and not net_transaction_flow_df.empty:
        agg_df = agg_df.merge(net_transaction_flow_df, on='date', how='outer')
        agg_df['net_transferred_in_tokens'].fillna(0, inplace=True)
        agg_df.rename(columns={'net_transferred_in_tokens': 'Net Transferred'}, inplace=True)

    if tvl_df is not None and not tvl_df.empty: 
        tvl_df = tvl_df[tvl_df['date'] >= min(agg_df['date'])]
        agg_df = agg_df.merge(tvl_df, on='date', how='outer')
        agg_df['totalLiquidityUSD'].fillna(0, inplace=True)
        agg_df.rename(columns={'totalLiquidityUSD': 'TVL'}, inplace=True)

    agg_df[['Transaction Count', 'Active Users', 'Unique Users', 'Total Transferred']].fillna(0, inplace=True)
    agg_df['date'] = pd.to_datetime(agg_df['date'])
    # label rows based on whether they were pre or post grant
    agg_df['grant_label'] = agg_df.apply(assign_grant_label, axis=1, grant_date=grant_date)

    return agg_df

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
        t_stat = (mu1 - mu2) / np.sqrt(s_pooled_squared * ((1/n1) + (1/n2)))
        df = n1 + n2 - 2
        
    else:
        # variances not equal so use welch's t
        t_stat = (mu1 - mu2) / np.sqrt((s1_squared/n1) + (s2_squared/n2))
        df = (((s1_squared / n1) + (s2_squared / n2))**2) / ((((s1_squared/n1)**2)/(n1-1)) + (((s2_squared/n2)**2)/(n2-1)))

    return t_stat, df

# function to calculate p-value
def ttest(t_stat: float, df: float) -> float:
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

            p_value = ttest(t_stat, df)
            if p_value < 1e-4:  # adjust to the desired threshold
                p_value_formatted = f"{p_value:.2e}"  # scientific notation
            else:
                p_value_formatted = f"{p_value:.4f}"  # standard decimal format

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
                'p_value': p_value,
                'p_value_formatted': p_value_formatted
            }

            metric_table.append(metric_dict)

        except Exception as e:
            print(f"Error processing metric {metric}: {e}")
            continue

    # convert the list of dictionaries to a DataFrame
    return pd.DataFrame(metric_table)

# filters the displayed tvl data based on user inputted chains and tokens
### deprecated function
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
    pre_grant_tvl_df, post_grant_tvl_df = split_dataset_by_date(dataset=filtered_chain_tvl_df, grant_date=grant_date)

    # ensure that there are enough data points on both ends of the split
    if len(pre_grant_tvl_df) < 10 or len(post_grant_tvl_df) < 10:
        st.warning("Not enough data available for the selected filters.")
        return

    # determine the sample metrics
    aggregated_metrics = aggregate_split_datasets_by_metrics([(pre_grant_tvl_df, post_grant_tvl_df)], ['value'])

    # conduct the t-test and return the results
    updated_tvl_metrics = determine_statistics(aggregated_metrics[0][0], aggregated_metrics[0][1])
    updated_tvl_metrics['metric'] = updated_tvl_metrics['metric'].replace('value', 'TVL by Token and Chain (USD)')
    return updated_tvl_metrics

# function to visualize the significance of the t-test
def plot_ttest_distribution(selected_metric_stats: pd.DataFrame, alpha: float) -> None:

    dof = selected_metric_stats['degrees_of_freedom'].iloc[0]

    # create x values for the t-distribution
    x = np.linspace(-10, 10, 1000)  # extended range for t-stat visibility
    y = t.pdf(x, dof)

    # critical values for two-tailed test
    critical_value = t.ppf(1 - alpha / 2, dof)

    # get the t-statistic for the selected metric
    t_stat = selected_metric_stats['test_statistic'].iloc[0]

    # adjust x-axis range to ensure t-stat is always visible
    x_min = min(-4, -1 * (abs(t_stat) + 1))
    x_max = max(4, abs(t_stat) + 1)

    # generate data for rejection regions
    rejection_x_left = x[x <= -critical_value]
    rejection_y_left = y[x <= -critical_value]
    rejection_x_right = x[x >= critical_value]
    rejection_y_right = y[x >= critical_value]

    # plot t-distribution
    fig = px.line(
        x=x,
        y=y,
        labels={'x': f't-value, dof={dof}', 'y': 'Probability Density'},
        title=f""
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
            showlegend=False  # hide duplicate legend entry
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

##### Synthetic Controls Section #####

# concat the forecasted metrics onto the pre and post grant data with it's respective label
def concat_aggregate_with_forecasted(aggregated_dataset: pd.DataFrame, forecasted_df: pd.DataFrame) -> pd.DataFrame:
    forecasted_df = forecasted_df.copy()
    forecasted_df['grant_label'] = 'forecast'
    
    # rename the columns so they are the same and can be concatted
    rename_dict = {
        col: col.replace("forecasted_", "")
        for col in forecasted_df.columns
    }
    forecasted_df.rename(columns=rename_dict, inplace=True)

    # rename the columns for when they're displayed
    forecasted_df.rename(columns={'transaction_cnt': 'Transaction Count', 
                           'active_users': 'Active Users', 
                           'unique_users': 'Unique Users',
                           'total_transferred': 'Total Transferred',
                           'net_transferred_in_tokens': 'Net Transferred'}, inplace=True)
    if 'cum_transferred_in_tokens' in forecasted_df.columns:
        forecasted_df.drop('cum_transferred_in_tokens', axis=1, inplace=True)
    if 'totalLiquidityUSD' in forecasted_df.columns:
        forecasted_df.rename(columns={'totalLiquidityUSD': 'TVL'}, inplace=True)

    # concat the datasets
    combined_df = pd.concat([aggregated_dataset, forecasted_df], ignore_index=True)
    combined_df['date'] = pd.to_datetime(combined_df['date'])
    combined_df['date'] = combined_df['date'].dt.date
    combined_df = combined_df.sort_values('date')

    return combined_df

# plot the forecasted data against the pre and post grant data as a line chart
def plot_forecast(curr_selection_df: pd.DataFrame, selected_metric: str, grant_date: datetime, dates: Tuple[datetime.date, datetime.date]) -> None:   
    # check if all forecast data for the selected metric is missing
    if curr_selection_df.loc[curr_selection_df['grant_label'] == 'forecast', selected_metric].isna().all():
        st.warning("No forecast data available for the selected metric.")
        return
    
    start_date, end_date = dates[0], dates[1]

    # plot
    fig = go.Figure()

    # add actual data and forecast data as separate traces
    for grant_label in curr_selection_df['grant_label'].unique():
        df_subset = curr_selection_df[curr_selection_df['grant_label'] == grant_label]
        fig.add_trace(
            go.Scatter(
                x=df_subset['date'],
                y=df_subset[selected_metric],
                mode='lines',
                name=grant_label,
            )
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

    fig.update_layout(
        title=f"{selected_metric} Forecast vs. Actuals",
        xaxis_title="Date",
        yaxis_title=selected_metric,
        legend_title="",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig)

# display the results of the 2-sample t-test
def display_ttest_table(metric_table: pd.DataFrame, alpha: float, selected_metric: str) -> None:
    # display most import results as KPIs
    perc_change, test_stat, p_val = st.columns(3)

    st.markdown(
        '''
        <style>
        /*center metric label*/
        [data-testid="stMetricLabel"] > div:nth-child(1) {
            justify-content: center;
        }

        /*center metric value*/
        [data-testid="stMetricValue"] > div:nth-child(1) {
            justify-content: center;
        }
        </style>
        ''', 
        unsafe_allow_html=True
    )

    # display the percentage change of the chosen metric over the pre to post grant period
    with perc_change:
        first_percent_change = metric_table['percent_change'].iloc[0]
        pos = '+' if first_percent_change > 0 else ''
        st.metric(label="Percent Change", value=f"{pos}{round(first_percent_change * 100, 2)}%")

     # display the test statistic of the t-test
    with test_stat:
        st.metric(label="Test Statistic", value=metric_table['test_statistic'].iloc[0])

     # display the p value of the t-test
    with p_val:
        st.metric(label="P-Value", value=metric_table['p_value_formatted'].iloc[0])

    # display sample statistics
    ttest_table = {
        'Grant Status': ['pre-grant', 'post-grant'],
        'Sample Size': [metric_table['pre_grant_n'].iloc[0], metric_table['post_grant_n'].iloc[0]],
        'Sample Mean': [metric_table['pre_grant_mean'].iloc[0], metric_table['post_grant_mean'].iloc[0]],
        'Sample Standard Deviation': [metric_table['pre_grant_std'].iloc[0], metric_table['post_grant_std'].iloc[0]]
    }

    ttest_table = pd.DataFrame(ttest_table)
    # display the pre and post grant metrics as a table
    st.dataframe(
        ttest_table.assign(hack='').set_index('hack'), # hide the dataframe index
        column_config={
            "hack": None,
            "Grant Status": st.column_config.TextColumn(width="medium"),
            "Sample Size": st.column_config.NumberColumn(width="medium"),
            "Sample Mean": st.column_config.NumberColumn(width="medium"),
            "Sample Standard Deviation": st.column_config.NumberColumn(width="medium")
        }
    )

    # write conclusion based on the p value and current alpha value
    p_value = metric_table['p_value'].iloc[0]
    p_value_formatted = metric_table['p_value_formatted'].iloc[0]
    selected_metric = selected_metric if selected_metric == "TVL" else selected_metric.lower()
    # we reject the null hypothesis
    if p_value <= alpha:
        st.write(
            f"The p-value is **{p_value_formatted}**, which is less than the significance level (**α = {alpha}**). "
            f"This indicates that the observed difference between the pre-grant and post-grant periods ***mean {selected_metric}*** is statistically significant. "
            f"We reject the null hypothesis and conclude that the grant likely had a measurable impact on {selected_metric}. "
            f"We are ***{round((1 - (alpha)) * 100, 4)}% confident*** in this conclusion."
        )
    # we fail to reject the null hypothesis
    else:
        st.write(
            f"The p-value is **{p_value_formatted}**, which is greater than the significance level (**α = {alpha}**). "
            f"This indicates that the observed difference between the pre-grant and post-grant periods ***mean {selected_metric}*** is not statistically significant. "
            f"We fail to reject the null hypothesis and conclude that the grant likely did not have a measurable impact on {selected_metric}. "
            f"We are ***{round((1 - (alpha)) * 100, 4)}% confident*** in this conclusion."
        )

# display the explanation for how the forecasted data was created
def forecasted_data_content() -> None:
    st.subheader("Comparing Post-Grant Metrics to Forecasted Data")
    
    with st.expander("The Process Behind The Forecasted Data"):
        st.write("""
            This visualization showcases three key data points for the selected metric:
            - **Pre-Grant Data**: Actual values before the grant was issued.
            - **Post-Grant Data**: Actual values after the grant was issued.
            - **Forecasted Data**: Values predicted using pre-grant data and/or related external factors as a baseline.

            **How It Was Done**:
            There are now two models used for forecasting based on the specific circumstances:
            1. **SARIMA Model**: 
                - Trained using only the pre-grant data.
                - Forecasting was done **three data points at a time**, iteratively adding predictions as new training data for subsequent forecasts.
                - Slight bootstrapping was applied to the training set to introduce randomness while maintaining overall trends and prevent overfitting.
                - A **noise distribution** (~Normal(mean=1, std=0.25)) was added to simulate real-world volatility and ensure realistic variability.
            2. **Linear Regression Model**:
                - Trained using the **Optimism chain TVL** (after normalization) as the independent variable and the **selected protocol TVL** as the target.
                - Predictions were made three days at a time, combined with a **slight noise distribution** (~Normal(mean=1, std=0.05)) to emulate real-world fluctuations.
                - The predictions were then concatenated to the dataset as additional data points.

            **Concepts Behind It**:
            - **SARIMA Model**:
                - Captures both trend and seasonality, making it suitable for metrics that exhibit periodic patterns.
                - Bootstrapping introduces slight variability, enhancing robustness and reducing overfitting.
                - Noise distribution ensures predictions reflect real-world random fluctuations.
            - **Linear Regression Model**:
                - Leverages external metrics (Optimism chain TVL) to model dependencies between related datasets.
                - Adding a noise distribution ensures realistic variability in predictions.
            
            **Interpreting the Results**:
            - The **forecasted lines** provide baselines for how the data might have trended based on either pre-grant trends (SARIMA) or external factors (Linear Regression).
            - Comparing the forecasted lines to the actual post-grant data highlights deviations potentially influenced by the grant.
            - While not conclusive, these insights help identify patterns and raise questions for further exploration.
        """)

# display the explanation for what a 2-sample t-test is
def ttest_table_content() -> None:
    st.subheader("Conducting a 2-Sample T-Test")

    with st.expander("Understanding The 2-Sample T-Test"):
        st.write("""
            **What Is a Two-Sample T-Test?**
            - A **two-sample t-test** is a statistical method used to compare the means of two groups to determine if they are significantly different from each other.
            - In this context, it compares the **pre-grant data** (group 1) to the **post-grant data** (group 2) for the selected metric.

            **Why It's Used**:
            - To evaluate whether the observed differences between pre-grant and post-grant performance are statistically significant or could be due to random chance.

            **Displayed Metrics**:
            - **pre_grant_n**: Number of data points in the pre-grant period.
            - **pre_grant_mean**: Average value of the metric during the pre-grant period.
            - **pre_grant_std**: Standard deviation of the metric during the pre-grant period.
            - **post_grant_n**: Number of data points in the post-grant period.
            - **post_grant_mean**: Average value of the metric during the post-grant period.
            - **post_grant_std**: Standard deviation of the metric during the post-grant period.
            - **percent_change**: The percentage difference between the pre-grant and post-grant means.
            - **test_statistic**: The calculated value used to determine statistical significance.
            - **p_value**: The probability that the observed difference occurred by chance.

            **Interpreting the Results**:
            - The **p_value** indicates whether the difference between pre-grant and post-grant means is statistically significant.
            - A **p_value < alpha** (commonly 0.05) suggests the difference is statistically significant.
            - For example, if the p_value is 0.03, we can reject the null hypothesis (no difference) and infer the grant had a measurable impact.
        """)

# display the explanation of how to understand the t-test distribution
def ttest_distribution_content() -> None:
    st.subheader("T-Test Distribution")

    with st.expander("How To Intepret The T-Test Distribution"):
        st.write("""
            **What Does This Visualization Show?**
            - This visualization plots the t-test distribution for the selected metric, highlighting:
            - The **test statistic** (calculated value for the t-test).
            - The **rejection region**, defined by the **alpha value** (significance level).
            - Whether the test statistic falls within or outside the rejection region.

            **How It Works**:
            - The **test statistic** is plotted on the t-distribution curve to visualize its relationship with the rejection region.
            - Users can adjust the **alpha value** to change the significance level, moving the rejection region boundaries.

            **Concepts Behind It**:
            - The **alpha value** determines the threshold for statistical significance. For example:
            - Alpha = 0.05 means there's a 5% chance of rejecting the null hypothesis incorrectly.
            - The **rejection region** is the area under the curve where the null hypothesis is rejected if the test statistic falls within it.

            **Interpreting the Results**:
            - If the test statistic falls within the rejection region, the null hypothesis (no difference) is rejected.
            - If it falls outside the region, the null hypothesis cannot be rejected.
            - **Example**: "If the test statistic is -2.5 and falls in the rejection region, the data suggests a statistically significant impact of the grant."

            **Easy-to-Understand Summary**:
            - **Test Statistic**: The value we're testing.
            - **Alpha Value**: The threshold for determining significance.
            - **Rejection Region**: If the test statistic lands here, the results are statistically significant.
        """)

# main function to generate the full statistical analysis section
def stat_analysis_section(daily_transactions_df: pd.DataFrame, forecasted_df: pd.DataFrame, grant_date: datetime, net_transaction_flow_df: Optional[pd.DataFrame], tvl_df: Optional[pd.DataFrame]=None) -> None:

    # combine all of the metrics into the same dataset for easy and quick filtering
    aggregated_dataset = aggregate_datasets(daily_transactions_df=daily_transactions_df, net_transaction_flow_df=net_transaction_flow_df, tvl_df=tvl_df, grant_date=grant_date)
    combined_df = concat_aggregate_with_forecasted(aggregated_dataset, forecasted_df)
    
    # allow user to select a target metric
    if 'TVL_opchain' in combined_df.columns: 
        metric_options = combined_df.columns.drop(['date', 'grant_label', 'TVL_opchain'])
    else:
        metric_options = combined_df.columns.drop(['date', 'grant_label'])

    selected_metric = st.selectbox("Select a target metric", metric_options)
    
    if selected_metric == "TVL":
        comparison_methods = ["Based on previous chain TVL trends", "Based on OP chain trends"]
        selected_comparison = st.selectbox("Select a forecast method", comparison_methods)

        if selected_comparison == "Based on OP chain trends":
            selected_metric_df = combined_df[['date', "TVL", "TVL_opchain", 'grant_label']]

            selected_metric_df.loc[selected_metric_df["grant_label"] == "forecast", "TVL"] = selected_metric_df["TVL_opchain"]
            selected_metric_df.drop("TVL_opchain", axis=1, inplace=True)

        else:
            selected_metric_df = combined_df[['date', selected_metric, 'grant_label']]
    else:
        selected_metric_df = combined_df[['date', selected_metric, 'grant_label']]

    min_date = combined_df['date'].min()
    max_date = combined_df['date'].max()

    # allow for users to input desired date range
    dates = st.slider(
        label="Select a date range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD"
    )

    start_date, end_date = dates[0], dates[1]

    curr_selection_df = selected_metric_df[(selected_metric_df['date'] >= start_date) & (selected_metric_df['date'] <= end_date)]

    st.divider()
   
    forecasted_data_content()
    
    plot_forecast(curr_selection_df=curr_selection_df, selected_metric=selected_metric, grant_date=grant_date, dates=(start_date, end_date))
    
    curr_selection_forecasted_df = curr_selection_df[curr_selection_df["grant_label"] == "forecast"]
    curr_selection_df = curr_selection_df[curr_selection_df["grant_label"] != "forecast"]
    pre_grant_df, post_grant_df = split_dataset_by_date(curr_selection_df, grant_date=grant_date)

    if len(pre_grant_df) < 10:
        st.warning("Not enough pre grant data points to conduct the t-test")
        return

    # display t-test results
    ttest_table_content()

    sample_1_options = ["Pre grant data"]
    if curr_selection_forecasted_df is not None and not curr_selection_forecasted_df.empty:
        sample_1_options.append("Forecasted data")

    selected_sample_1 = st.selectbox("Select sample 1 (sample 2 will always be post grant data)", sample_1_options)
    if selected_sample_1 == "Forecasted Data":
        sample_1 = curr_selection_forecasted_df
    else:
        sample_1 = pre_grant_df
    
    sample_2 = post_grant_df

    alpha = st.slider(
        label="Select an alpha value",
        min_value=0.01,
        max_value=0.99,
        value=0.05,  # default value
        step=0.01   # step size
    )

    st.markdown(f"#### This means that we are ***{round((1 - (alpha)) * 100, 4)}%*** confident in our results.")

    st.divider()

    st.subheader("T-Test Results")

    aggregated_metrics = aggregate_split_datasets_by_metrics([(sample_1, sample_2)], [selected_metric])

    # conduct the t-test and return the results
    metric_table = determine_statistics(aggregated_metrics[0][0], aggregated_metrics[0][1])

    display_ttest_table(metric_table, alpha, selected_metric)

    st.divider()

    # display the t-test distribution plot
    ttest_distribution_content()
    plot_ttest_distribution(selected_metric_stats=metric_table, alpha=alpha)
