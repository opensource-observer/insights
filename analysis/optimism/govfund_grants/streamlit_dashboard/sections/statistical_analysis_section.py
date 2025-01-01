from typing import Optional
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np
from functools import reduce
from pmdarima import auto_arima
from scipy.stats import t

from processing import split_dataset_by_date
from utils import assign_grant_label
from config import GRANT_DATE

##### Hypothesis Testing Section #####

# aggregates metrics for datasets split by pre- and post-grant periods
def aggregate_split_datasets_by_metrics(split_datasets: list[tuple[pd.DataFrame, pd.DataFrame]], metrics: list[str]) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    aggregated_metrics = []

    # iterates through split datasets
    for pre_grant_df, post_grant_df in split_datasets:
        select_metrics = [metric for metric in metrics if metric in pre_grant_df.columns]
        if 'transaction_date' in pre_grant_df.columns:
            date_col = 'transaction_date'
        elif 'readable_date' in pre_grant_df.columns:
            date_col = 'readable_date'
        else:
            date_col = 'date'
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
                'p_value': round(ttest(t_stat, df), 4)
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
def plot_ttest_streamlit(selected_metric, selected_metric_stats) -> None:

    alpha = st.slider(
        label="Select an alpha value",
        min_value=0.0,
        max_value=1.0,
        value=0.05,  # default value
        step=0.01   # step size
    )

    df = selected_metric_stats['degrees_of_freedom'].iloc[0]

    # create x values for the t-distribution
    x = np.linspace(-10, 10, 1000)  # extended range for t-stat visibility
    y = t.pdf(x, df)

    # critical values for two-tailed test
    critical_value = t.ppf(1 - alpha / 2, df)

    # get the t-statistic for the selected metric
    t_stat = selected_metric_stats['test_statistic'].iloc[0]

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

##### Synthetic Controls Section #####

# return a bootstraped sample (same length) of the input series
def bootstrap_series(series, rng, bootstrap_ratio=0.33):
    n = len(series)
    num_bootstrap = int(bootstrap_ratio * n)
    bootstrap_indices = rng.choice(n, size=num_bootstrap, replace=True)  # sample with replacement
    fixed_indices = rng.choice(n, size=n - num_bootstrap, replace=False)  # sample without replacement
    indices = np.concatenate([bootstrap_indices, fixed_indices])
    rng.shuffle(indices)
    return series[indices]


def time_series_cv_expanding_weekly(
        pre_grant_df,
        post_grant_df,
        target_col,
        chunk_size=3,  # number of days to predict at each iteration
        noise_std=0.25,  # increased noise for sharp day-to-day variability
        random_state=None,
        handle_negative=False
    ):
    rng = np.random.RandomState(random_state)

    # Identify the date column
    date_col = 'transaction_date' if 'transaction_date' in pre_grant_df.columns else 'readable_date'

    # Aggregate and sort the data
    pre_grant_df = pre_grant_df.groupby(date_col)[target_col].sum().reset_index()
    post_grant_df = post_grant_df.groupby(date_col)[target_col].sum().reset_index()

    pre_grant_df[date_col] = pd.to_datetime(pre_grant_df[date_col])
    post_grant_df[date_col] = pd.to_datetime(post_grant_df[date_col])

    y = pre_grant_df[target_col].values
    if handle_negative:
        offset = abs(y.min()) + 1 if y.min() < 0 else 0
        y = y + offset

    y_train_trans = np.log1p(y)  # Log-transform to stabilize variance

    predictions = []
    predictions_left = len(post_grant_df)

    while predictions_left > 0:
        forecast_window = min(chunk_size, predictions_left)

        # Bootstrapping
        y_bootstrap = bootstrap_series(y_train_trans, rng, bootstrap_ratio=0.33)

        # Fit ARIMA model
        model = auto_arima(
            y_bootstrap,
            seasonal=True,
            m=7,  # weekly seasonality
            suppress_warnings=True,
            stepwise=True,
            trace=False,
            error_action='ignore'
        )

        # Forecast
        forecasted_log = model.predict(n_periods=forecast_window)
        forecasted_vals = np.expm1(forecasted_log)

        # Add variability with noise
        noise_factors = rng.normal(loc=1.0, scale=noise_std, size=forecast_window)
        forecasted_vals_noisy = forecasted_vals * noise_factors

        if handle_negative:
            forecasted_vals_noisy = forecasted_vals_noisy - offset

        predictions.extend(forecasted_vals_noisy)

        # Update the training set with the forecast
        forecasted_log_noisy = np.log1p(np.clip(forecasted_vals_noisy, 1e-9, None))
        y_train_trans = np.concatenate([y_train_trans, forecasted_log_noisy])

        predictions_left -= forecast_window

    # Create a DataFrame for results
    result_df = pd.DataFrame({
        'date': post_grant_df[date_col],
        f'forecasted_{target_col}': predictions
    })

    return result_df


def aggregate_datasets(daily_transactions_df, net_op_flow_df, tvl_df):
    
    daily_transactions_df.rename(columns={'transaction_date': 'date'}, inplace=True)
    daily_transactions_df['date'] = pd.to_datetime(daily_transactions_df['date'])
    net_op_flow_df.rename(columns={'transaction_date': 'date'}, inplace=True)
    if tvl_df is not None: 
        tvl_df.drop('date', axis=1, inplace=True)
        tvl_df.rename(columns={'readable_date': 'date'}, inplace=True)
        tvl_df['date'] = pd.to_datetime(tvl_df['date'])

    daily_transactions_df = daily_transactions_df.groupby('date')[['transaction_cnt', 'active_users', 'unique_users', 'total_op_transferred']].sum().reset_index()
    net_op_flow_df = net_op_flow_df.groupby('date')[['net_op_transferred_in_tokens']].sum().reset_index()
    net_op_flow_df['date'] = pd.to_datetime(net_op_flow_df['date'])
    if tvl_df is not None: 
        tvl_df = tvl_df.groupby('date')['totalLiquidityUSD'].sum().reset_index()

    agg_df = daily_transactions_df.merge(net_op_flow_df, on='date', how='outer')
    agg_df.rename(columns={'transaction_cnt': 'Transaction Count', 
                           'active_users': 'Active Users', 
                           'unique_users': 'Unique Users',
                           'total_op_transferred': 'Total OP Transferred',
                           'net_op_transferred_in_tokens': 'Net OP Transferred'}, inplace=True)
    if tvl_df is not None: 
        tvl_df = tvl_df[tvl_df['date'] >= min(agg_df['date'])]
        agg_df = agg_df.merge(tvl_df, on='date', how='outer')
        agg_df.rename(columns={'totalLiquidityUSD': 'TVL'}, inplace=True)

    agg_df['date'] = pd.to_datetime(agg_df['date'])
    agg_df['grant_label'] = agg_df.apply(assign_grant_label, axis=1)

    return agg_df


def plot_forecast(curr_selection_df, selected_metric, grant_date, dates):
    start_date, end_date = dates[0], dates[1]

    # plot
    fig = go.Figure()

    # Add actual data and forecast data as separate traces
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


# main function to generate the full statistical analysis section
def stat_analysis_section(daily_transactions_df, net_op_flow_df, chain_tvls_df=None, tvl_df=None, forecasted_df=None):

    aggregated_dataset = aggregate_datasets(daily_transactions_df=daily_transactions_df, net_op_flow_df=net_op_flow_df, tvl_df=tvl_df)
    # select a target metric
    metric_options = aggregated_dataset.columns.drop(['date', 'grant_label'])
    selected_metric = st.selectbox("Select a target metric", metric_options)
    to_forecast = {'Transaction Count': 'transaction_cnt', 
                   'Active Users': 'active_users', 
                   'Unique Users': 'unique_users',
                   'Total OP Transferred': 'total_op_transferred',
                   'Net OP Transferred': 'net_op_transferred_in_tokens',
                   'TVL': 'totalLiquidityUSD'}
    
    # prepare forecasted data in a matching format
    forecast_col = f'forecasted_{to_forecast[selected_metric]}'
    forecast_plot = forecasted_df[['date', forecast_col]].copy()
    forecast_plot.rename(columns={forecast_col: selected_metric}, inplace=True)
    forecast_plot['grant_label'] = 'forecast'
    
    # combine all into one dataframe
    combined_df = pd.concat([aggregated_dataset[['date', selected_metric, 'grant_label']], forecast_plot], ignore_index=True)

    combined_df['date'] = pd.to_datetime(combined_df['date'])
    combined_df['date'] = combined_df['date'].dt.date
    combined_df = combined_df.sort_values('date')

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
    curr_selection_df = combined_df[(combined_df['date'] >= start_date) & (combined_df['date'] <= end_date)]
    pre_grant_df, post_grant_df = split_dataset_by_date(aggregated_dataset, GRANT_DATE)

    st.divider()
   
    # display the forecast plot 
    if forecasted_df is None:
        forecasted_df = time_series_cv_expanding_weekly(pre_grant_df, post_grant_df, target_col=selected_metric)

    st.subheader("Comparing Post-Grant Metrics to Forecasted Data")
    
    with st.expander("The Process Behind The Forecasted Data"):
        st.write("""
            This visualization showcases three key data points for the selected metric:
            - **Pre-Grant Data**: Actual values before the grant was issued.
            - **Post-Grant Data**: Actual values after the grant was issued.
            - **Forecasted Data**: Values predicted using the pre-grant data as a baseline.

            **How It Was Done**:
            - A **SARIMA model** (Seasonal Autoregressive Integrated Moving Average) was trained for each metric using only the pre-grant data.
            - The forecasting process involved predicting **three data points at a time** and using those predictions iteratively as new training data for the next forecast.
            - To prevent overfitting, **slight bootstrapping** was applied to the training set, introducing randomness while maintaining overall trends.
            - A **noise distribution** (~Normal(mean=1, std=0.25)) was added to simulate real-world volatility and ensure the forecasted data captured realistic variability.

            **Concepts Behind It**:
            - SARIMA accounts for both trend and seasonality in the data, making it suitable for metrics that exhibit periodic patterns.
            - Bootstrapping introduces slight variability, making the model more robust and less overfit to the pre-grant data.
            - The noise distribution emulates random fluctuations commonly seen in real-world datasets, ensuring the forecast isn't overly smooth.

            **Interpreting the Results**:
            - The **forecasted line** provides a baseline for how the data might have trended without the grant, based purely on pre-grant trends.
            - Comparing the forecasted line to the actual post-grant data highlights deviations potentially influenced by the grant.
            - While not conclusive, this helps identify general patterns and raises questions for further exploration.
        """)
    
    plot_forecast(curr_selection_df=curr_selection_df, selected_metric=selected_metric, grant_date=GRANT_DATE, dates=(start_date, end_date))
    
    # display t-test results
    st.subheader("T-Test Results")

    with st.expander("Understanding The 2-sample T-Test"):
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
            - **degrees_of_freedom**: A value used in the t-test calculation to account for sample size.
            - **p_value**: The probability that the observed difference occurred by chance.

            **Interpreting the Results**:
            - The **p_value** indicates whether the difference between pre-grant and post-grant means is statistically significant.
            - A **p_value < alpha** (commonly 0.05) suggests the difference is statistically significant.
            - For example, if the p_value is 0.03, we can reject the null hypothesis (no difference) and infer the grant had a measurable impact.
        """)

    aggregated_metrics = aggregate_split_datasets_by_metrics([(pre_grant_df, post_grant_df)], [selected_metric])

    # conduct the t-test and return the results
    metric_table = determine_statistics(aggregated_metrics[0][0], aggregated_metrics[0][1])
    st.dataframe(metric_table)

    # display the t-test plot
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
            - Alpha = 0.05 means there’s a 5% chance of rejecting the null hypothesis incorrectly.
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

    plot_ttest_streamlit(selected_metric, selected_metric_stats=metric_table)
