from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from pysyncon import Dataprep, Synth
from typing import List, Optional, Dict


METRICS = [
    'market_cap_eth', 'txcount', 'fees_paid_eth', 
    'txcosts_median_eth', 'stables_mcap', 'gas_per_second', 
    'tvl_eth', 'tvl', 'stables_mcap_eth', 'fdv_eth'
]

DATE_COL = 'date'
METRIC_COL = 'metric_key'
ENTITY_COL = 'origin_key'
VALUE_COL = 'value'

class SynthControlRequest(BaseModel):
    time_predictors_prior_start: datetime = Field(
        ...,
        description="Start date for the predictor period used to train the synthetic control model"
    )
    time_predictors_prior_end: datetime = Field(
        ...,
        description="End date for the predictor period used to train the synthetic control model"
    )
    time_optimize_ssr_start: datetime = Field(
        ...,
        description="Start date for the optimization period where synthetic control weights are calculated"
    )
    time_optimize_ssr_end: datetime = Field(
        ...,
        description="End date for the optimization period where synthetic control weights are calculated"
    )
    dependent: str = Field(
        ...,
        description="The target variable to be predicted (e.g., 'market_cap_eth')"
    )
    treatment_identifier: str = Field(
        ...,
        description="The identifier for the treated unit (e.g., 'arbitrum')"
    )
    controls_identifier: List[str] = Field(
        ...,
        description="List of identifiers for the control units (e.g., ['optimism', 'base'])"
    )
    predictors: Optional[List[str]] = Field(
        default=METRICS,
        description="List of variables used to predict the dependent variable. Defaults to common blockchain metrics"
    )

class SynthControlResponse(BaseModel):
    weights: dict
    data: List[dict]


def reshape_to_metrics_columns(df):
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    df_wide = df.pivot(
        index=[DATE_COL, ENTITY_COL],
        columns=METRIC_COL,
        values=VALUE_COL
    ).reset_index()
    return df_wide.sort_values([DATE_COL, ENTITY_COL])


def create_synth_control(df: pd.DataFrame, request: SynthControlRequest):
    """
    Create a synthetic control analysis.

    Parameters:
    - time_predictors_prior_start: Start date for predictor period
    - time_predictors_prior_end: End date for predictor period
    - time_optimize_ssr_start: Start date for optimization period
    - time_optimize_ssr_end: End date for optimization period
    - dependent: Dependent variable name
    - treatment_identifier: Identifier for treatment group
    - controls_identifier: List of control group identifiers
    - predictors: Optional list of predictor variables

    Returns:
    - weights: Dictionary of control weights
    - data: Time series of treatment and synthetic values
    """
    
    # Process data
    df_wide = reshape_to_metrics_columns(df)
    df_wide = df_wide.fillna(0)

    # Create date ranges
    time_predictors_prior = pd.date_range(
        request.time_predictors_prior_start,
        request.time_predictors_prior_end,
        freq='D'
    )
    
    time_optimize_ssr = pd.date_range(
        request.time_optimize_ssr_start,
        request.time_optimize_ssr_end,
        freq='D'
    )

    # Initialize Dataprep
    dataprep = Dataprep(
        foo=df_wide,
        predictors=request.predictors,
        predictors_op="mean",
        time_predictors_prior=time_predictors_prior,
        time_optimize_ssr=time_optimize_ssr,
        dependent=request.dependent,
        unit_variable=ENTITY_COL,
        time_variable=DATE_COL,
        treatment_identifier=request.treatment_identifier,
        controls_identifier=request.controls_identifier,
    )

    # Fit synthetic control
    synth = Synth()
    synth.fit(dataprep)
    
    # Get weights and round them to 3 decimal places
    weights_df = synth.weights()
    weights_dict = {
        index: round(float(value), 3) 
        for index, value in weights_df.items()
    }

    # Calculate plot data
    plot_dates = pd.date_range(df[DATE_COL].min(), df[DATE_COL].max(), freq='D')
    Z0, Z1 = dataprep.make_outcome_mats(plot_dates)
    synthetic = synth._synthetic(Z0)

    # Create the data array with the new structure
    data = [
        {
            "date": date.strftime('%Y-%m-%d'),
            "treatment": float(treatment),
            "synthetic": float(synth)
        }
        for date, treatment, synth in zip(plot_dates, Z1, synthetic)
    ]

    response_data = SynthControlResponse(
        weights=weights_dict,
        data=data
    )


    return response_data