from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, Optional
from pmdarima import auto_arima
from sklearn.linear_model import LinearRegression

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

def forecast_based_on_pregrant(
        pre_grant_df: pd.DataFrame,
        post_grant_df: pd.DataFrame,
        target_col: str,
        bootstrap_ratio: float,
        seasonality: int = 0,
        chunk_size: int = 3,
        noise_std: float = 0.25,
        random_state: np.random.RandomState = None,
        handle_negative: bool = False
) -> pd.DataFrame:
    rng = np.random.RandomState(random_state)

    date_col = determine_date_col(df=pre_grant_df)
    pre_grant_df = pre_grant_df.groupby(date_col)[target_col].sum().reset_index()
    post_grant_df = post_grant_df.groupby(date_col)[target_col].sum().reset_index()

    y = pre_grant_df[target_col].values

    if len(y) == 0:
        raise ValueError(f"The input series for '{target_col}' is empty.")

    if pre_grant_df[target_col].nunique() <= 1:
        print(f"Time-series for '{target_col}' is constant. Skipping ARIMA modeling.")
        constant_value = y[0] if len(y) > 0 else 0
        predictions = [constant_value] * len(post_grant_df)
        return pd.DataFrame({'date': post_grant_df[date_col], f'forecasted_{target_col}': predictions})

    if handle_negative:
        offset = abs(y.min()) + 1 if y.min() < 0 else 0
        y = y + offset

    y_train_trans = np.log1p(y)
    y_train_trans = np.nan_to_num(y_train_trans, nan=0.0, posinf=0.0, neginf=0.0)

    predictions = []
    predictions_left = len(post_grant_df)
    while predictions_left > 0:
        forecast_window = min(chunk_size, predictions_left)

        if bootstrap_ratio > 0:
            y_curr = bootstrap_series(y_train_trans, rng, bootstrap_ratio)
        else:
            y_curr = y_train_trans

        y_curr = np.nan_to_num(y_curr, nan=0.0, posinf=0.0, neginf=0.0)

        model = auto_arima(
            y_curr,
            seasonal=(seasonality > 0),
            m=seasonality,
            suppress_warnings=True,
            stepwise=True,
            trace=False,
            error_action='ignore',
            ensure_all_finite=True
        )

        forecasted_log = model.predict(n_periods=forecast_window)
        forecasted_vals = np.expm1(forecasted_log)

        noise_factors = rng.normal(loc=1.0, scale=noise_std, size=forecast_window)
        forecasted_vals_noisy = forecasted_vals * noise_factors

        if handle_negative:
            forecasted_vals_noisy = forecasted_vals_noisy - offset

        predictions.extend(forecasted_vals_noisy)
        forecasted_log_noisy = np.log1p(np.clip(forecasted_vals_noisy, 1e-9, None))
        y_train_trans = np.concatenate([y_train_trans, forecasted_log_noisy])

        predictions_left -= forecast_window

    return pd.DataFrame({'date': post_grant_df[date_col], f'forecasted_{target_col}': predictions})

# generate the forecasted dataset for the target project
def forecast_project(datasets: Dict[str, pd.DataFrame], grant_date: datetime) -> pd.DataFrame:
    optimism_bridge_tvl = pd.read_csv("data/optimism_bridge_tvl.csv")
    
    # extract the relevant datasets
    if 'daily_transactions' in datasets.keys() and datasets['daily_transactions'] is not None:
        daily_transactions_df = datasets.get('daily_transactions').copy()
    else:
        daily_transactions_df = pd.DataFrame()

    if 'net_transaction_flow' in datasets.keys() and datasets['net_transaction_flow'] is not None:
        net_transaction_flow_df = datasets.get('net_transaction_flow').copy()
    else:
        net_transaction_flow_df = pd.DataFrame()

    if 'tvl' in datasets.keys() and datasets['tvl'] is not None:
        tvl_df = datasets.get('tvl').copy()
    else:
        tvl_df = pd.DataFrame()

    # combine all metrics into a single aggregated dataset
    aggregated_dataset = aggregate_datasets(
        daily_transactions_df=daily_transactions_df, 
        net_transaction_flow_df=net_transaction_flow_df, 
        tvl_df=tvl_df,
        grant_date=grant_date
    )

    # split the dataset into pre-grant and post-grant based on the grant date
    pre_grant_df, post_grant_df = split_dataset_by_date(aggregated_dataset, grant_date=grant_date)

    if len(pre_grant_df) >= 10:
        # identify target columns for forecasting
        if 'protocol' in aggregated_dataset.columns:
            target_cols = aggregated_dataset.drop(['date', 'grant_label', 'protocol'], axis=1).columns
        else:
            target_cols = aggregated_dataset.drop(['date', 'grant_label'], axis=1).columns

        # initialize the forecasted dataframe
        forecasted_df = None

        for col in target_cols:
            # adjust forecasting parameters based on the column
            if col == 'TVL':
                protocols = aggregated_dataset["protocol"].dropna().unique().tolist()

                for protocol in protocols:
                    curr_protocol_aggregated_dataset = aggregated_dataset[aggregated_dataset["protocol"] == protocol].drop("protocol", axis=1)
                    curr_protocol_pre_grant_df = pre_grant_df[pre_grant_df["protocol"] == protocol].drop("protocol", axis=1)
                    curr_protocol_post_grant_df = post_grant_df[post_grant_df["protocol"] == protocol].drop("protocol", axis=1)

                    if len(curr_protocol_aggregated_dataset) > 10 and len(curr_protocol_pre_grant_df) > 10 and len(curr_protocol_post_grant_df) > 10:
                        
                        col_forecasted_df2 = forecast_based_on_chain_tvl(
                            chain_tvl=optimism_bridge_tvl, 
                            target_protocol=curr_protocol_aggregated_dataset,
                            grant_date=grant_date
                        )

                        col_forecasted_df = forecast_based_on_pregrant(
                            curr_protocol_pre_grant_df, 
                            curr_protocol_post_grant_df, 
                            bootstrap_ratio=0, 
                            noise_std=0.05, 
                            target_col=col
                        )

                        if col_forecasted_df is not None and col_forecasted_df2 is not None:
                            col_forecasted_df.rename(columns={"forecasted_TVL": f"forecasted_TVL-{protocol}"}, inplace=True)
                            col_forecasted_df2.rename(columns={"forecasted_TVL_opchain": f"forecasted_TVL_opchain-{protocol}"}, inplace=True)
                            col_forecasted_df = col_forecasted_df.merge(col_forecasted_df2, how='outer', on='date')
                        elif col_forecasted_df2 is not None and col_forecasted_df is None:
                            col_forecasted_df = col_forecasted_df2
                            col_forecasted_df2.rename(columns={"forecasted_TVL_opchain": f"forecasted_TVL_opchain-{protocol}"}, inplace=True)
                        else:
                            col_forecasted_df = None

            else:

                if 'protocol' in pre_grant_df.columns:
                    col_forecasted_df = forecast_based_on_pregrant(
                        pre_grant_df.drop("protocol", axis=1), 
                        post_grant_df.drop("protocol", axis=1), 
                        bootstrap_ratio=0.33, 
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

        print(forecasted_df)
        return forecasted_df

    return None

# use a linear regression model to forecast based on the growth of a reference chain
def forecast_based_on_chain_tvl(
    chain_tvl: pd.DataFrame,
    target_protocol: pd.DataFrame,
    grant_date: datetime,
    chunk_size: int = 3,
    random_state: np.random.RandomState = None,
    noise_std: float = 0.05,
) -> Optional[pd.DataFrame | None]:

    chain_tvl_date_col = determine_date_col(df=chain_tvl)
    target_protocol_date_col = determine_date_col(df=target_protocol)

    # convert dates to datetime format
    chain_tvl[chain_tvl_date_col] = pd.to_datetime(chain_tvl[chain_tvl_date_col], errors="coerce")
    target_protocol[target_protocol_date_col] = pd.to_datetime(target_protocol[target_protocol_date_col], errors="coerce")

    chain_tvl_col = "totalLiquidityUSD" if "totalLiquidityUSD" in chain_tvl.columns else "TVL"
    target_protocol_col = "totalLiquidityUSD" if "totalLiquidityUSD" in target_protocol.columns else "TVL"

    # normalize the TVL data
    chain_tvl_max = chain_tvl[chain_tvl_col].max()
    chain_tvl["TVL_normalized"] = chain_tvl[chain_tvl_col] / chain_tvl_max

    target_protocol_max = target_protocol[target_protocol_col].max()
    target_protocol["TVL_normalized"] = target_protocol[target_protocol_col] / target_protocol_max

    # determine the common date range
    chain_tvl_min_date = chain_tvl[chain_tvl_date_col].min()
    target_protocol_min_date = target_protocol[target_protocol_date_col].min()
    min_date = max(chain_tvl_min_date, target_protocol_min_date)

    chain_tvl_max_date = chain_tvl[chain_tvl_date_col].max()
    target_protocol_max_date = target_protocol[target_protocol_date_col].max()
    max_date = min(chain_tvl_max_date, target_protocol_max_date)

    # filter pre- and post-grant data with dates preserved
    chain_tvl_pre_grant = chain_tvl[(chain_tvl[chain_tvl_date_col] < grant_date) & (chain_tvl[chain_tvl_date_col] >= min_date)]
    chain_tvl_post_grant = chain_tvl[(chain_tvl[chain_tvl_date_col] >= grant_date) & (chain_tvl[chain_tvl_date_col] <= max_date)]

    target_protocol_pre_grant = target_protocol[(target_protocol[target_protocol_date_col] < grant_date) & (target_protocol[target_protocol_date_col] >= min_date)]
    target_protocol_post_grant = target_protocol[(target_protocol[target_protocol_date_col] >= grant_date) & (target_protocol[target_protocol_date_col] <= max_date)]

    # extract normalized TVL values
    X_pre_grant = chain_tvl_pre_grant["TVL_normalized"].values.reshape(-1, 1)
    X_post_grant = chain_tvl_post_grant["TVL_normalized"].values.reshape(-1, 1)

    y_pre_grant = target_protocol_pre_grant["TVL_normalized"].values
    y_post_grant = target_protocol_post_grant["TVL_normalized"].values

    if len(X_pre_grant) < 20 or len(y_pre_grant) < 20:
        return None
    
    predictions = []
    model = LinearRegression()
    rng = np.random.RandomState(random_state)
    # iterate until predictions are made for every day of the post-grant period
    predictions_left = len(X_post_grant)

    X_pre_grant_curr = X_pre_grant.copy()
    X_post_grant_curr = X_post_grant.copy()
    y_pre_grant_curr = y_pre_grant.copy()
    y_post_grant_curr = y_post_grant.copy()

    while predictions_left > 0:
        # how much to forecast
        forecast_window = min(chunk_size, predictions_left)

        # ensure all values in X_pre_grant and y_pre_grant are finite
        X_pre_grant_curr = np.nan_to_num(X_pre_grant_curr, nan=0.0, posinf=0.0, neginf=0.0)
        y_pre_grant_curr = np.nan_to_num(y_pre_grant_curr, nan=0.0, posinf=0.0, neginf=0.0)

        # train the Linear Regression model
        pre_grant_min = min(len(X_pre_grant_curr), len(y_pre_grant_curr))
        model.fit(X=X_pre_grant_curr[:pre_grant_min], y=y_pre_grant_curr[:pre_grant_min])

        # predict post-grant TVL
        pred = model.predict(X_post_grant_curr[:forecast_window])

        # add variability with noise
        noise_factors = rng.normal(loc=1.0, scale=noise_std, size=forecast_window)
        pred_noisy = pred * noise_factors

        predictions.extend(pred_noisy)
        # update the training set with the forecast
        X_pre_grant_curr = np.concatenate([X_pre_grant_curr, pred_noisy.reshape(-1, 1)])
        y_pre_grant_curr = np.concatenate([y_pre_grant_curr, y_post_grant_curr[:forecast_window]])

        predictions_left -= forecast_window
        X_post_grant_curr = X_post_grant_curr[forecast_window:]
        y_post_grant_curr = y_post_grant_curr[forecast_window:]

    min_length = min(len(predictions), len(y_post_grant), len(X_post_grant))

    predictions = np.array(predictions)

    # ensure lengths align
    y_post_grant = y_post_grant[:min_length]
    X_post_grant = X_post_grant[:min_length]
    predictions = predictions[:min_length]
    dates_post_grant = chain_tvl_post_grant[chain_tvl_date_col].values[:len(X_post_grant)]

    # create a dataframe for results
    post_grant_df = pd.DataFrame({
        'date': dates_post_grant,
        'chain_tvl_tvl': X_post_grant.flatten() * chain_tvl_max,
        'forecasted_TVL_opchain': predictions * target_protocol_max,
        'actual_tvl': y_post_grant * target_protocol_max
    })

    return post_grant_df[["date", "forecasted_TVL_opchain"]]
