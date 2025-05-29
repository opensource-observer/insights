from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict
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
    """
    This version uses only the most recent X rows of pre-grant data, 
    where X = number of rows in the post-grant dataframe.
    """

    rng = np.random.RandomState(random_state)

    # Identify the date column
    date_col = determine_date_col(df=pre_grant_df)

    # Group both pre- and post-grant by date (summing the target col)
    pre_grant_df = pre_grant_df.groupby(date_col)[target_col].sum().reset_index()
    post_grant_df = post_grant_df.groupby(date_col)[target_col].sum().reset_index()

    # Ensure we sort by date in ascending order
    pre_grant_df = pre_grant_df.sort_values(by=date_col).reset_index(drop=True)
    post_grant_df = post_grant_df.sort_values(by=date_col).reset_index(drop=True)

    # Determine how many rows to use from pre-grant
    n_post = len(post_grant_df)
    n_pre = len(pre_grant_df)
    n_take = min(n_pre, n_post)

    # Take only the *most recent* n_take rows of pre-grant
    pre_grant_df = pre_grant_df.tail(n_take).copy()

    # Extract the raw pre-grant series y
    y = pre_grant_df[target_col].values

    if len(y) == 0:
        raise ValueError(f"The input series for '{target_col}' is empty or invalid.")

    # If the pre-grant series is constant, skip ARIMA and forecast a constant
    if pre_grant_df[target_col].nunique() <= 1:
        print(f"Time-series for '{target_col}' is constant. Skipping ARIMA modeling.")
        constant_value = y[0] if len(y) > 0 else 0
        predictions = [constant_value] * len(post_grant_df)
        return pd.DataFrame({'date': post_grant_df[date_col], f'forecasted_{target_col}': predictions})

    # Handle potential negative values by shifting up if needed
    offset = 0
    if handle_negative:
        min_val = y.min()
        if min_val < 0:
            offset = abs(min_val) + 1
            y = y + offset

    # Log-transform in the offset domain
    y_train_trans = np.log1p(y)
    y_train_trans = np.nan_to_num(y_train_trans, nan=0.0, posinf=0.0, neginf=0.0)

    predictions = []
    predictions_left = len(post_grant_df)

    # Iteratively forecast in chunks
    while predictions_left > 0:
        forecast_window = min(chunk_size, predictions_left)

        # Optionally bootstrap a portion of the training data
        if bootstrap_ratio > 0:
            y_curr = bootstrap_series(y_train_trans, rng, bootstrap_ratio)
        else:
            y_curr = y_train_trans

        # Ensure no NaNs or inf
        y_curr = np.nan_to_num(y_curr, nan=0.0, posinf=0.0, neginf=0.0)

        # Fit ARIMA model on the log-transformed data
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

        # Forecast in the log-transformed domain
        forecasted_log = model.predict(n_periods=forecast_window)
        forecasted_vals = np.expm1(forecasted_log)

        # Add noise
        noise_factors = rng.normal(loc=1.0, scale=noise_std, size=forecast_window)
        forecasted_vals_noisy = forecasted_vals * noise_factors

        # Shift back to original domain if negative handling was used
        if handle_negative and offset > 0:
            forecasted_vals_noisy = forecasted_vals_noisy - offset

        # Store the chunk's forecasts
        predictions.extend(forecasted_vals_noisy)

        # Convert back to the "log1p + offset" domain for continuing the loop
        # Clip at a small positive value to avoid NaNs in log
        forecasted_log_noisy = np.log1p(np.clip(forecasted_vals_noisy + offset if handle_negative else forecasted_vals_noisy, 1e-9, None))
        y_train_trans = np.concatenate([y_train_trans, forecasted_log_noisy])

        predictions_left -= forecast_window

    # Build final DataFrame
    df_result = pd.DataFrame({
        'date': post_grant_df[date_col],
        f'forecasted_{target_col}': predictions
    })

    return df_result

# generate the forecasted dataset for the target project
def forecast_project(datasets: Dict[str, pd.DataFrame], grant_date: datetime) -> pd.DataFrame:
    optimism_bridge_tvl = pd.read_csv("data/optimism_bridge_tvl.csv")
    
    # extract the relevant datasets
    if 'daily_transactions' in datasets.keys() and datasets['daily_transactions'] is not None:
        daily_transactions_df = datasets.get('daily_transactions').copy()
        daily_transactions_df["transaction_date"] = pd.to_datetime(daily_transactions_df['transaction_date'])
        daily_transactions_df = daily_transactions_df[daily_transactions_df["transaction_date"] <= datetime(2025, 2, 11)]
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

        forecasted_df = None

        for col in target_cols:
            if col == 'TVL':
                protocols = aggregated_dataset["protocol"].dropna().unique().tolist()
                protocol_forecasts = []

                for protocol in protocols:
                    curr_protocol_aggregated_dataset = aggregated_dataset[aggregated_dataset["protocol"] == protocol].drop("protocol", axis=1)
                    curr_protocol_pre_grant_df = pre_grant_df[pre_grant_df["protocol"] == protocol].drop("protocol", axis=1)
                    curr_protocol_post_grant_df = post_grant_df[post_grant_df["protocol"] == protocol].drop("protocol", axis=1)

                    if len(curr_protocol_aggregated_dataset) > 10 and len(curr_protocol_pre_grant_df) > 10 and len(curr_protocol_post_grant_df) > 10:
                        col_forecasted_df = forecast_based_on_pregrant(
                            curr_protocol_pre_grant_df, 
                            curr_protocol_post_grant_df, 
                            bootstrap_ratio=0, 
                            noise_std=0.05, 
                            target_col=col
                        )

                        col_forecasted_df2 = forecast_based_on_chain_tvl(
                            chain_tvl=optimism_bridge_tvl, 
                            target_protocol=curr_protocol_aggregated_dataset,
                            grant_date=grant_date
                        )

                        if col_forecasted_df is not None:
                            col_forecasted_df.rename(columns={"forecasted_TVL": f"forecasted_TVL-{protocol}"}, inplace=True)
                        if col_forecasted_df2 is not None:
                            col_forecasted_df2.rename(columns={"forecasted_TVL_opchain": f"forecasted_TVL_opchain-{protocol}"}, inplace=True)

                        if col_forecasted_df is not None and col_forecasted_df2 is not None:
                            combined_df = col_forecasted_df.merge(col_forecasted_df2, on="date", how="outer")
                            protocol_forecasts.append(combined_df)
                        elif col_forecasted_df is not None:
                            protocol_forecasts.append(col_forecasted_df)
                        elif col_forecasted_df2 is not None:
                            protocol_forecasts.append(col_forecasted_df2)

                # merge all protocol forecasts
                if protocol_forecasts:
                    col_forecasted_df = protocol_forecasts[0]
                    for df in protocol_forecasts[1:]:
                        col_forecasted_df = col_forecasted_df.merge(df, on="date", how="outer")
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

            # merge into the full forecasted_df
            if forecasted_df is None:
                forecasted_df = col_forecasted_df
            elif col_forecasted_df is not None:
                forecasted_df = forecasted_df.merge(col_forecasted_df, on="date", how="outer")

        return forecasted_df

    return None

# use a linear regression model to forecast based on the growth of a reference chain
def forecast_based_on_chain_tvl(
    chain_tvl: pd.DataFrame,
    target_protocol: pd.DataFrame,
    grant_date: datetime,
    chunk_size: int = 3,
    random_state: int = None,
    noise_std: float = 0.05,
) -> pd.DataFrame | None:
    """
    Use a linear regression model to forecast the target protocol's TVL 
    based on the growth of a reference chain's TVL. Data is aligned by date,
    normalized, then chunk-forecasted post-grant. 
    """

    def determine_date_col(df: pd.DataFrame) -> str:
        # Identify which column is a date column; adapt this logic as needed
        for col in df.columns:
            if 'date' in col.lower():
                return col
        raise ValueError("No date column found")

    # Identify date columns
    chain_tvl_date_col = determine_date_col(chain_tvl)
    target_protocol_date_col = determine_date_col(target_protocol)

    # Convert to datetime
    chain_tvl[chain_tvl_date_col] = pd.to_datetime(chain_tvl[chain_tvl_date_col], errors="coerce")
    target_protocol[target_protocol_date_col] = pd.to_datetime(target_protocol[target_protocol_date_col], errors="coerce")

    # Identify TVL column names
    chain_tvl_col = "totalLiquidityUSD" if "totalLiquidityUSD" in chain_tvl.columns else "TVL"
    target_protocol_col = "totalLiquidityUSD" if "totalLiquidityUSD" in target_protocol.columns else "TVL"

    # Rename columns to standardize
    chain_df = chain_tvl[[chain_tvl_date_col, chain_tvl_col]].copy()
    chain_df.columns = ["date", "chain_tvl"]

    protocol_df = target_protocol[[target_protocol_date_col, target_protocol_col]].copy()
    protocol_df.columns = ["date", "protocol_tvl"]

    # Merge on date so X and Y align properly
    merged_df = pd.merge(chain_df, protocol_df, on="date", how="inner").dropna(subset=["chain_tvl","protocol_tvl"])

    if merged_df.empty:
        print(1)
        return None

    # Normalize across the entire dataset
    chain_tvl_max = merged_df["chain_tvl"].max()
    protocol_tvl_max = merged_df["protocol_tvl"].max()
    if chain_tvl_max == 0 or protocol_tvl_max == 0:
        print(2)
        return None  # Cannot normalize if max is 0

    merged_df["chain_norm"] = merged_df["chain_tvl"] / chain_tvl_max
    merged_df["proto_norm"] = merged_df["protocol_tvl"] / protocol_tvl_max

    # Split into pre-grant and post-grant
    pre_grant = merged_df[merged_df["date"] < grant_date].copy()
    post_grant = merged_df[merged_df["date"] >= grant_date].copy()
    if pre_grant.empty or post_grant.empty:
        print(3)
        return None

    # Extract X, y for training
    X_pre = pre_grant[["chain_norm"]].values
    y_pre = pre_grant["proto_norm"].values

    # Must have enough data
    if len(X_pre) < 20 or len(y_pre) < 20:
        print(4)
        return None

    # Fit model on pre-grant data
    model = LinearRegression()
    model.fit(X_pre, y_pre)

    # Prepare post-grant exogenous data
    X_post = post_grant[["chain_norm"]].values

    # Forecast in chunks
    predictions = []
    rng = np.random.RandomState(random_state)

    n_left = len(X_post)
    idx_start = 0
    while n_left > 0:
        forecast_window = min(chunk_size, n_left)
        # Slice out the next chunk
        X_chunk = X_post[idx_start : idx_start + forecast_window]

        # Predict
        pred_chunk = model.predict(X_chunk)

        # Add noise
        noise_factors = rng.normal(loc=1.0, scale=noise_std, size=len(pred_chunk))
        pred_chunk_noisy = pred_chunk * noise_factors

        # Store
        predictions.extend(pred_chunk_noisy)

        # Move index
        idx_start += forecast_window
        n_left -= forecast_window

    # Build result DataFrame
    # Align length in case of any mismatch
    predictions = np.array(predictions)
    n_pred = len(predictions)
    post_grant = post_grant.iloc[:n_pred].copy()

    # Denormalize
    post_grant["forecasted_TVL_opchain"] = predictions * protocol_tvl_max
    print(post_grant)

    # Return just date & forecast, or more if you like
    return post_grant[["date", "forecasted_TVL_opchain"]]