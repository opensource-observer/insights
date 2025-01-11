from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict
from pmdarima import auto_arima

from processing import split_dataset_by_date
from utils import determine_date_col
from sections.statistical_analysis_section import aggregate_datasets

# return a partially bootstrapped sample of the input series while preserving the original order
def bootstrap_series(series: np.ndarray, rng: np.random.Generator, bootstrap_ratio: float = 0.33) -> np.ndarray:
    n = len(series)
    num_bootstrap = int(bootstrap_ratio * n)

    # randomly choose indices to replace
    bootstrap_indices = rng.choice(n, size=num_bootstrap, replace=False)

    # copy the series to avoid modifying the original
    bootstrapped_series = series.copy()

    # replace selected indices with values randomly sampled from the series
    replacement_values = rng.choice(series, size=num_bootstrap, replace=True)
    bootstrapped_series[bootstrap_indices] = replacement_values

    return bootstrapped_series

# train an arima model on the pre grant data to forecast what the post grant data would look like if the grant never occured
def forecast_based_on_pregrant(
        pre_grant_df: pd.DataFrame,
        post_grant_df: pd.DataFrame,
        target_col: str,
        bootstrap_ratio: float,
        seasonality: int = 0,
        chunk_size: int = 3,  # number of days to predict at each iteration
        noise_std: float = 0.25,  # amount of relative noise for day-to-day variability
        random_state: np.random.RandomState = None,
        handle_negative: bool = False
) -> pd.DataFrame:
    rng = np.random.RandomState(random_state)

    # identify the date column
    date_col = determine_date_col(df=pre_grant_df)

    # aggregate and sort the data
    pre_grant_df = pre_grant_df.groupby(date_col)[target_col].sum().reset_index()
    post_grant_df = post_grant_df.groupby(date_col)[target_col].sum().reset_index()

    pre_grant_df[date_col] = pd.to_datetime(pre_grant_df[date_col])
    post_grant_df[date_col] = pd.to_datetime(post_grant_df[date_col])

    y = pre_grant_df[target_col].values

    # check if the series is constant
    if pre_grant_df[target_col].nunique() <= 1:
        print(f"Time-series for '{target_col}' is constant. Skipping ARIMA modeling.")
        # create a forecast by simply repeating the constant value
        constant_value = y[0] if len(y) > 0 else 0
        predictions = [constant_value] * len(post_grant_df)
    else:
        # handle negative values if necessary
        if handle_negative:
            offset = abs(y.min()) + 1 if y.min() < 0 else 0
            y = y + offset

        y_train_trans = np.log1p(y)  # log-transform to stabilize variance

        predictions = []
        # iterate until predictions are made for every day of the post-grant period
        predictions_left = len(post_grant_df)
        while predictions_left > 0:
            # how much to forecast
            forecast_window = min(chunk_size, predictions_left)

            # bootstrapping to combat overfitting
            if bootstrap_ratio > 0:
                y_curr = bootstrap_series(y_train_trans, rng, bootstrap_ratio)
            else:
                y_curr = y_train_trans

            # fit the ARIMA model
            model = auto_arima(
                y_curr,
                seasonal=(seasonality > 0),
                m=seasonality,  # weekly seasonality
                suppress_warnings=True,
                stepwise=True,
                trace=False,
                error_action='ignore'
            )

            # forecast
            forecasted_log = model.predict(n_periods=forecast_window)
            forecasted_vals = np.expm1(forecasted_log)

            # add variability with noise
            noise_factors = rng.normal(loc=1.0, scale=noise_std, size=forecast_window)
            forecasted_vals_noisy = forecasted_vals * noise_factors

            # subtract offset to return to original data
            if handle_negative:
                forecasted_vals_noisy = forecasted_vals_noisy - offset

            predictions.extend(forecasted_vals_noisy)

            # update the training set with the forecast
            forecasted_log_noisy = np.log1p(np.clip(forecasted_vals_noisy, 1e-9, None))
            y_train_trans = np.concatenate([y_train_trans, forecasted_log_noisy])

            predictions_left -= forecast_window

    # create a dataframe for results
    result_df = pd.DataFrame({
        'date': post_grant_df[date_col],
        f'forecasted_{target_col}': predictions
    })

    return result_df

# generate the forecasted dataset for the target project
def forecast_project(datasets: Dict[str, pd.DataFrame], grant_date: datetime) -> pd.DataFrame:
    # extract the relevant datasets
    daily_transactions_df = datasets.get('daily_transactions', pd.DataFrame()).copy()
    net_transaction_flow_df = datasets.get('net_transaction_flow', pd.DataFrame()).copy()
    tvl_df = datasets.get('tvl', pd.DataFrame()).copy()

    # combine all metrics into a single aggregated dataset
    aggregated_dataset = aggregate_datasets(
        daily_transactions_df=daily_transactions_df, 
        net_transaction_flow_df=net_transaction_flow_df, 
        tvl_df=tvl_df,
        grant_date=grant_date
    )

    # split the dataset into pre-grant and post-grant based on the grant date
    pre_grant_df, post_grant_df = split_dataset_by_date(aggregated_dataset, grant_date=grant_date)

    # identify target columns for forecasting
    target_cols = aggregated_dataset.drop(['date', 'grant_label'], axis=1).columns

    # initialize the forecasted dataframe
    forecasted_df = None

    for col in target_cols:
        # adjust forecasting parameters based on the column
        if col == 'TVL':
            col_forecasted_df = forecast_based_on_pregrant(
                pre_grant_df, 
                post_grant_df, 
                bootstrap_ratio=0, 
                noise_std=0.05, 
                target_col=col
            )
        else:
            col_forecasted_df = forecast_based_on_pregrant(
                pre_grant_df, 
                post_grant_df, 
                bootstrap_ratio=0.33, 
                target_col=col
            )

        # merge the forecasts for each column
        if forecasted_df is None:
            forecasted_df = col_forecasted_df
        else:
            forecasted_df = forecasted_df.merge(col_forecasted_df, on='date', how='outer')

    return forecasted_df
