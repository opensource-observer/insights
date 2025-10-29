import marimo

__generated_with = "0.16.2"
app = marimo.App(width="medium")


@app.cell
def about_app(mo):
    _author = 'OSO Team'
    _updated_at = '2025-10-28'
    mo.vstack([
        mo.md(f"""
        # Synthetic Control Analysis
        <small>Author: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">{_author}</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">{_updated_at}</span></small>
        """),
        mo.md("""
        This notebook performs synthetic control analysis to estimate causal effects by creating a synthetic counterfactual. 
        """),
        mo.accordion({
            "<b>Methodology</b>": """
            Synthetic Control Method

            The synthetic control method creates a weighted combination of control units (networks) that best approximates 
            the treatment unit (target network) in the pre-intervention period. This synthetic control serves as a 
            counterfactual for what would have happened to the treatment unit in the absence of the intervention.

            Key Steps:
            1. Training Period: Uses predictor variables to find optimal weights that make the synthetic control 
               closely match the treatment unit's pre-intervention trajectory
            2. Optimization Period: Minimizes the sum of squared residuals between treatment and synthetic control
            3. Post-Intervention Comparison: The gap between actual and synthetic values estimates the treatment effect

            Interpretation:
            - A positive gap suggests the intervention had a positive effect
            - The pre-intervention fit quality indicates how reliable the counterfactual is
            - Control weights show which networks most closely resemble the treatment network
            """,
            "<b>Data Sources</b>": """
            - [Goldsky / Superchain Data](https://bit.ly/superchaindata)
            - [Defillama](https://defillama.com)
            - [growthepie](https://growthepie.com)
            - [L2Beat](https://l2beat.com)
            - Consolidated chain metrics from `oso.int_chain_metrics` table
            """,
            "<b>Further Resources</b>": """
            - [Pyoso API](https://docs.opensource.observer/docs/get-started/python)
            - [Synthetic Control Method Overview](https://en.wikipedia.org/wiki/Synthetic_control_method)
            - [pysyncon Documentation](https://github.com/sdfordham/pysyncon)
            - [Marimo Documentation](https://docs.marimo.io/)
            """
        })    
    ])
    return


@app.cell
def define_constants():
    AVAILABLE_CHAINS = [
      "ARBITRUM_ONE", "BASE", "BLAST", "CELO", "FRAX", "INK", "LINEA", "LISK", "LOOPRING",
      "MANTA", "MANTLE", "METIS", "MINT", "MODE", "OPTIMISM", "ORDERLY", "PLUME", "POLYGON_ZKEVM",
      "REDSTONE", "SCROLL", "SONEIUM", "STARKNET", "SWELL", "TAIKO", "UNICHAIN", "WORLDCHAIN",
      "ZKSYNC_ERA", "ZORA"
    ]
    AVAILABLE_METRICS = {
        'TVL - USD (Defillama)': 'DEFILLAMA_TVL',
        'TVL - ETH (growthepie)': 'TVL_ETH',
        'TVS - Canonical (L2Beat)': 'L2BEAT_TVS_CANONICAL',
        'TVS - External (L2Beat)': 'L2BEAT_TVS_EXTERNAL',
        'TVS - Native (L2Beat)': 'L2BEAT_TVS_NATIVE',
        'Market Cap - ETH (growthepie)': 'MARKET_CAP_ETH',
        'Market Cap - USD (growthepie)': 'MARKET_CAP_USD',
        'Stablecoin Value - USD (growthepie)': 'STABLES_MCAP',
        'Stablecoin Value - ETH (growthepie)': 'STABLES_MCAP_ETH',

        'Profit - USD (growthepie)': 'PROFIT_USD',
        'Fees Paid - ETH (growthepie)': 'FEES_PAID_ETH',
        'App Fees - USD (growthepie)': 'APP_FEES_USD',
        'App Fees - ETH (growthepie)': 'APP_FEES_ETH',
        'Gas Per Second (growthepie)': 'GAS_PER_SECOND',
        'L1 Gas Fees (growthepie)': 'LAYER1_GAS_FEES',
        'Tx Costs Median - ETH (growthepie)': 'TXCOSTS_MEDIAN_ETH',
        'Activity - Userops (L2Beat)': 'L2BEAT_ACTIVITY_UOPS_COUNT',
        'Transaction Count (growthepie)': 'TXCOUNT',    
        'Active Addresses - 7D (growthepie)': 'AA_LAST7D',
        'Active Addresses - 1D (growthepie)': 'DAA',
    }
    DEFAULT_TREATMENT = 'OPTIMISM'
    DEFAULT_CONTROLS = ['ARBITRUM_ONE', 'BASE', 'ZKSYNC_ERA', 'SCROLL', 'TAIKO', 'LINEA', 'POLYGON_ZKEVM']
    DEFAULT_DEPENDENT = 'Fees Paid - ETH (growthepie)'
    DEFAULT_PREDICTORS = [
        'TVL - USD (Defillama)', 'Market Cap - USD (growthepie)', 
        'Stablecoin Value - USD (growthepie)', 'Tx Costs Median - ETH (growthepie)',
        'Gas Per Second (growthepie)'
    ]
    return (
        AVAILABLE_CHAINS,
        AVAILABLE_METRICS,
        DEFAULT_CONTROLS,
        DEFAULT_DEPENDENT,
        DEFAULT_PREDICTORS,
        DEFAULT_TREATMENT,
    )


@app.cell
def configuration_settings(
    AVAILABLE_CHAINS,
    AVAILABLE_METRICS,
    DEFAULT_CONTROLS,
    DEFAULT_DEPENDENT,
    DEFAULT_PREDICTORS,
    DEFAULT_TREATMENT,
    datetime,
    mo,
    timedelta,
):
    # Calculate default dates
    _end_date = datetime.now().date()
    _start_date = _end_date - timedelta(days=365)
    _intervention_date = _end_date - timedelta(days=180)
    _training_months = 6

    treatment_input = mo.ui.dropdown(
        options=AVAILABLE_CHAINS,
        value=DEFAULT_TREATMENT,
        label='Treatment Network',
        full_width=True
    )

    controls_input = mo.ui.multiselect(
        options=AVAILABLE_CHAINS,
        value=DEFAULT_CONTROLS,
        label='Control Networks',
        full_width=True
    )

    dependent_input = mo.ui.dropdown(
        options=AVAILABLE_METRICS,
        value=DEFAULT_DEPENDENT,
        label='Target Variable',
        full_width=True
    )

    predictors_input = mo.ui.multiselect(
        options=AVAILABLE_METRICS,
        value=DEFAULT_PREDICTORS,
        label='Predictor Variables',
        full_width=True
    )

    intervention_date_input = mo.ui.date(
        label='Intervention Date',
        value=_intervention_date,
        full_width=True
    )

    training_months_input = mo.ui.number(
        start=3,
        stop=24,
        value=_training_months,
        label='Months of Training',
        full_width=True
    )

    compute_button = mo.ui.run_button(label='Compute')

    mo.vstack([
        mo.md('## Configuration'),
        mo.md('Select the treatment network, control networks, time period, and other variables for analysis:'),
        mo.hstack([treatment_input, dependent_input], gap=5, justify='start', align='start', widths='equal'),
        mo.hstack([controls_input, predictors_input], gap=5, justify='start', align='start', widths='equal'),
        mo.hstack([intervention_date_input, training_months_input], gap=5, justify='start', align='start', widths='equal'),
        compute_button
    ])
    return (
        compute_button,
        controls_input,
        dependent_input,
        intervention_date_input,
        predictors_input,
        training_months_input,
        treatment_input,
    )


@app.cell
def pivot_metrics(pd):
    def pivot_metrics(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['sample_date'] = pd.to_datetime(df['sample_date'])
        df_wide = df.pivot_table(
            index=['sample_date', 'chain'],
            columns='metric_name',
            values='amount',
            aggfunc='sum'
        ).reset_index()
        df_wide = df_wide.fillna(0)
        return df_wide.sort_values(['sample_date', 'chain'])
    return (pivot_metrics,)


@app.cell
def get_chain_metrics(
    client,
    compute_button,
    controls_input,
    dependent_input,
    mo,
    predictors_input,
    treatment_input,
):
    mo.stop(not compute_button.value)

    # Get all unique metrics needed
    all_metrics = list(set([dependent_input.value] + list(predictors_input.value)))
    all_chains = [treatment_input.value] + list(controls_input.value)

    # Build query
    metrics_str = ", ".join([f"'{m}'" for m in all_metrics])
    chains_str = ", ".join([f"'{c}'" for c in all_chains])

    query = f"""
    SELECT
        sample_date,
        chain,
        metric_name,
        amount
    FROM int_chain_metrics
    WHERE metric_name IN ({metrics_str})
      AND chain IN ({chains_str})
      AND sample_date >= DATE '2022-01-01'
    ORDER BY sample_date, chain, metric_name
    """

    mo.status.spinner(title='Fetching data...')
    df_metrics = client.to_pandas(query)
    return (df_metrics,)


@app.cell
def prepare_data(
    df_metrics,
    intervention_date_input,
    pd,
    pivot_metrics,
    training_months_input,
):
    # Pivot the metrics
    df_wide = pivot_metrics(df_metrics)

    # Calculate date ranges
    intervention_date = pd.to_datetime(intervention_date_input.value)
    training_start = intervention_date - pd.DateOffset(months=training_months_input.value)

    # Filter to relevant date range (training period onwards)
    df_wide = df_wide[df_wide['sample_date'] >= training_start].copy()
    return df_wide, intervention_date, training_start


@app.cell
def run_synthetic_control(
    Dataprep,
    Synth,
    controls_input,
    dependent_input,
    df_wide,
    intervention_date,
    np,
    pd,
    predictors_input,
    training_start,
    treatment_input,
):
    # Create date ranges for pysyncon
    time_predictors_prior = pd.date_range(
        training_start,
        intervention_date - pd.Timedelta(days=1),
        freq='D'
    )

    time_optimize_ssr = pd.date_range(
        training_start,
        intervention_date - pd.Timedelta(days=1),
        freq='D'
    )

    _predictors = list(predictors_input.value)
    _dependent = dependent_input.value

    dataprep = Dataprep(
        foo=df_wide,
        predictors=_predictors,
        predictors_op="mean",
        time_predictors_prior=time_predictors_prior,
        time_optimize_ssr=time_optimize_ssr,
        dependent=_dependent,
        unit_variable="chain",
        time_variable="sample_date",
        treatment_identifier=treatment_input.value,
        controls_identifier=list(controls_input.value),
    )

    # Fit synthetic control
    synth = Synth()

    # Get the data matrices
    X0, X1 = dataprep.make_covariate_mats()
    Z0, Z1 = dataprep.make_outcome_mats()

    # Convert to numpy arrays
    X0_arr = X0.to_numpy()
    X1_arr = X1.to_numpy()
    Z0_arr = Z0.to_numpy()
    Z1_arr = Z1.to_numpy()

    n_controls = len(controls_input.value)

    # Implement our own optimization to avoid pysyncon bug
    from scipy.optimize import minimize

    def objective(weights):
        # Ensure weights sum to 1 and are non-negative
        weights = np.abs(weights)
        weights = weights / np.sum(weights)

        # Calculate synthetic control
        synthetic = Z0_arr @ weights

        # Calculate loss (sum of squared differences)
        loss = np.sum((Z1_arr - synthetic) ** 2)
        return loss

    # Constraint: weights must sum to 1
    from scipy.optimize import LinearConstraint
    constraint = LinearConstraint(np.ones(n_controls), 1, 1)

    # Initial guess: equal weights
    x0 = np.ones(n_controls) / n_controls

    # Ensure arrays are proper numpy arrays
    Z0_arr = np.asarray(Z0_arr, dtype=np.float64)
    Z1_arr = np.asarray(Z1_arr, dtype=np.float64)

    # Try different optimization approaches
    best_weights = None
    best_loss = float('inf')
    optimization_method = "None"

    # Method 1: SLSQP with tighter tolerance
    try:
        result = minimize(
            objective, 
            x0, 
            method='SLSQP',
            constraints=constraint,
            bounds=[(0, 1) for _ in range(n_controls)],
            options={'maxiter': 2000, 'ftol': 1e-9}
        )
        if result.success and result.fun < best_loss:
            best_weights = result.x
            best_loss = result.fun
            optimization_method = "SLSQP"
    except Exception as e:
        pass

    # Method 2: Try without constraints, normalize after
    try:
        def unconstrained_objective(weights):
            weights = np.abs(weights)
            if np.sum(weights) == 0:
                return float('inf')
            weights = weights / np.sum(weights)
            synthetic = Z0_arr @ weights
            loss = np.sum((Z1_arr - synthetic) ** 2)
            return loss

        result = minimize(
            unconstrained_objective,
            x0,
            method='BFGS',
            options={'maxiter': 2000}
        )
        if result.success:
            weights = np.abs(result.x)
            weights = weights / np.sum(weights)
            synthetic = Z0_arr @ weights
            loss = np.sum((Z1_arr - synthetic) ** 2)
            if loss < best_loss:
                best_weights = weights
                best_loss = loss
                optimization_method = "BFGS"
    except Exception as e:
        pass

    # Method 3: Try L-BFGS-B
    try:
        result = minimize(
            objective,
            x0,
            method='L-BFGS-B',
            bounds=[(0, 1) for _ in range(n_controls)],
            options={'maxiter': 2000}
        )
        if result.success and result.fun < best_loss:
            best_weights = result.x
            best_loss = result.fun
            optimization_method = "L-BFGS-B"
    except Exception as e:
        pass

    if best_weights is not None:
        optimal_weights = best_weights
    else:
        optimal_weights = np.ones(n_controls) / n_controls
        optimization_method = "Equal weights (optimization failed)"

    # Create a simple synthetic control object
    class SimpleSynth:
        def __init__(self, weights, Z0, Z1):
            self.W = weights
            self.Z0 = Z0
            self.Z1 = Z1
            self.W_names = Z0.columns

        def weights(self):
            return pd.Series(self.W, index=self.W_names)

        def _synthetic(self, Z0_mat):
            return Z0_mat @ self.W

    synth = SimpleSynth(optimal_weights, Z0, Z1)

    # Create analysis summary for display
    analysis_summary = f"""
    ### Analysis Configuration:

    - Treatment Unit: {treatment_input.value}
    - Control Units: {', '.join(controls_input.value)}
    - Dependent Variable: {dependent_input.value}
    - Predictors: {', '.join(_predictors)}
    - Data Points: {Z0_arr.shape[0]} time periods, {Z0_arr.shape[1]} control units

    ### Data Characteristics:

    - Treatment Mean: {Z1_arr.mean():,.0f}
    - Treatment Std: {Z1_arr.std():,.0f}
    - Control Means: {', '.join([f'{name}: {val:,.0f}' for name, val in zip(controls_input.value, Z0_arr.mean(axis=0))])}
    - Control Stds: {', '.join([f'{name}: {val:,.0f}' for name, val in zip(controls_input.value, Z0_arr.std(axis=0))])}

    ### Optimization Results:

    - Method: {optimization_method}
    - Loss: {best_loss:,.0f}
    - Optimal Weights: {', '.join([f'{name}: {weight:.3f}' for name, weight in zip(controls_input.value, optimal_weights)])}
    """

    # Get weights
    weights = synth.weights()
    weights_dict = {
        chain: round(float(weight), 3)
        for chain, weight in weights.items()
    }

    # Generate predictions for full time range
    plot_dates = pd.date_range(
        df_wide['sample_date'].min(),
        df_wide['sample_date'].max(),
        freq='D'
    )

    Z0, Z1 = dataprep.make_outcome_mats(plot_dates)
    synthetic = synth._synthetic(Z0)

    # Create results dataframe
    df_results = pd.DataFrame({
        'date': plot_dates,
        'treatment': Z1,
        'synthetic': synthetic,
        'gap': Z1 - synthetic
    })
    return analysis_summary, df_results, weights_dict


@app.cell
def generate_synthetic_control_plot(
    AVAILABLE_METRICS,
    dependent_input,
    df_results,
    go,
    intervention_date,
    mo,
    treatment_input,
):
    fig = go.Figure()

    # Add treatment line
    fig.add_trace(go.Scatter(
        x=df_results['date'],
        y=df_results['treatment'],
        mode='lines',
        name=treatment_input.value,
        line=dict(color='rgb(239, 85, 59)', width=2),
        hovertemplate='%{y:,.0f}<extra></extra>'
    ))

    # Add synthetic line
    fig.add_trace(go.Scatter(
        x=df_results['date'],
        y=df_results['synthetic'],
        mode='lines',
        name='Synthetic Control',
        line=dict(color='rgb(99, 110, 250)', width=2),
        hovertemplate='%{y:,.0f}<extra></extra>'
    ))

    # Add intervention line
    fig.add_vline(
        x=intervention_date.timestamp() * 1000,
        line_dash="dash",
        line_color="rgba(0, 0, 0, 0.5)",
        line_width=2,
        annotation_text="Intervention",
        annotation_position="top"
    )

    # Get the display name for the dependent variable
    from_metrics = {v: k for k, v in AVAILABLE_METRICS.items()}
    dependent_label = from_metrics.get(dependent_input.value, dependent_input.value)

    fig.update_layout(
        title=dict(
            text=f"<b>Synthetic Control: {dependent_label}</b>",
            x=0,
            xanchor="left"
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(size=12, color="#111", family="PT Sans, sans-serif"),
        margin=dict(t=60, l=20, r=20, b=40),
        hovermode='x unified',
        autosize=True,
        xaxis=dict(
            showgrid=False,
            linecolor='black',
            linewidth=1,
            ticks='outside',
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray',
            linecolor='black',
            linewidth=1,
            ticks='outside',
            rangemode='tozero'
        ),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            borderwidth=1
        )
    )
    mo.ui.plotly(fig)
    return


@app.cell
def display_summary_stats(
    analysis_summary,
    df_results,
    intervention_date,
    mo,
    np,
    weights_dict,
):
    weights_formula = " + ".join([
        f"{chain} × {weight}" 
        for chain, weight in weights_dict.items()
    ])

    df_pre = df_results[df_results['date'] < intervention_date]
    df_post = df_results[df_results['date'] >= intervention_date]

    pre_rmse = np.sqrt(np.mean(df_pre['gap'] ** 2))
    post_mean_gap = df_post['gap'].mean()
    post_mean_gap_pct = (post_mean_gap / df_post['synthetic'].mean()) * 100 if df_post['synthetic'].mean() != 0 else 0

    mo.vstack([
        mo.md("## Model Results"),
        mo.hstack([
            mo.stat(
                label="Pre-Intervention RMSE",
                value=f"{pre_rmse:,.1f}",
                caption="Lower is better fit",        
                bordered=True
            ),
            mo.stat(
                label="Post-Intervention Avg Gap",
                value=f"{post_mean_gap:,.1f}",
                caption=f"{post_mean_gap_pct:+.1f}% vs synthetic control",
                bordered=True
            ),
            mo.stat(
                label="Post-Intervention Days",
                value=f"{len(df_post):,}",
                caption="Days of data",
                bordered=True
            )
        ], justify='start', gap=2, widths='equal'),
        mo.md(analysis_summary)
    ])
    return


@app.cell
def import_libraries():
    import pandas as pd
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    from pysyncon import Dataprep, Synth
    from dataclasses import dataclass
    from typing import List, Optional
    from datetime import datetime, timedelta
    return Dataprep, Synth, datetime, go, np, pd, timedelta


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import marimo as mo
    from pyoso import Client
    client = Client()
    try:
        pyoso_db_conn = client.dbapi_connection()    
    except Exception as e:
        pyoso_db_conn = None
    return client, mo


if __name__ == "__main__":
    app.run()
