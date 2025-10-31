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
def tuning_controls(mo):
    # Tuning knobs (model-only; no refetch)
    lambda_cov_input = mo.ui.number(label='Predictor balance (lambda_cov)', start=0.0, stop=10.0, step=0.1, value=1.0)
    alpha_equal_input = mo.ui.number(label='Weight spread (alpha_equal)', start=0.0001, stop=0.01, step=0.0001, value=0.001)
    weight_cap_input = mo.ui.number(label='Max donor weight (cap)', start=0.60, stop=1.00, step=0.05, value=0.85)
    resample_weekly_input = mo.ui.switch(label='Resample to weekly means', value=False)
    return (
        alpha_equal_input,
        lambda_cov_input,
        resample_weekly_input,
        weight_cap_input,
    )


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
        'TVL - USD (Defillama)',
        'Market Cap - USD (growthepie)',
        'Stablecoin Value - USD (growthepie)',
        'Tx Costs Median - ETH (growthepie)',
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
        # Do NOT fillna globally to zero; preserve NaNs for missing values
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
    ORDER BY sample_date, chain
    """

    mo.status.spinner(title='Fetching data...')
    df_metrics = client.to_pandas(query)
    return (df_metrics,)


@app.cell
def prepare_data(
    controls_input,
    dependent_input,
    df_metrics,
    intervention_date_input,
    np,
    pd,
    pivot_metrics,
    predictors_input,
    resample_weekly_input,
    training_months_input,
    treatment_input,
):
    # Pivot the metrics
    df_wide = pivot_metrics(df_metrics)

    # Optional: resample to weekly means per chain (post-query smoothing)
    if resample_weekly_input.value:
        df_wide = (
            df_wide
            .set_index('sample_date')
            .groupby('chain', group_keys=False)
            .resample('W')
            .mean(numeric_only=True)
            .reset_index()
        )

    # Calculate date ranges
    intervention_date = pd.to_datetime(intervention_date_input.value)
    training_start = intervention_date - pd.DateOffset(months=training_months_input.value)

    # Keep data from training start onward for plotting later
    df_wide = df_wide[df_wide['sample_date'] >= training_start].copy()

    # --- Balanced-panel selection for the *pre* period only ---
    need_cols = [dependent_input.value] + list(predictors_input.value)
    units = [treatment_input.value] + list(controls_input.value)

    pre_mask = (df_wide['sample_date'] >= training_start) & (df_wide['sample_date'] < intervention_date)
    pre_df = df_wide.loc[pre_mask, ['sample_date','chain'] + need_cols].copy()

    # 1) Strict: all units complete on dependent+predictors
    pre_df['__complete_all__'] = pre_df[need_cols].notna().all(axis=1)
    counts_all = (
        pre_df[pre_df['__complete_all__'] & pre_df['chain'].isin(units)]
        .groupby('sample_date')['chain']
        .nunique()
        .rename('n_complete')
        .reset_index()
    )
    good_pre_dates = set(counts_all.loc[counts_all['n_complete'] == len(units), 'sample_date'])

    # 2) Fallback: require only dependent to be complete for all units
    if not good_pre_dates:
        dep = dependent_input.value
        pre_df['__complete_dep__'] = pre_df[[dep]].notna().all(axis=1)
        counts_dep = (
            pre_df[pre_df['__complete_dep__'] & pre_df['chain'].isin(units)]
            .groupby('sample_date')['chain']
            .nunique()
            .rename('n_complete')
            .reset_index()
        )
        good_pre_dates = set(counts_dep.loc[counts_dep['n_complete'] == len(units), 'sample_date'])

    # 3) Last-resort: allow partial balance on dependent (>=80% of units)
    if not good_pre_dates:
        k = max(2, int(np.ceil(0.8 * len(units))))
        dep = dependent_input.value
        pre_df['__complete_dep__'] = pre_df[[dep]].notna().all(axis=1)
        counts_k = (
            pre_df[pre_df['__complete_dep__'] & pre_df['chain'].isin(units)]
            .groupby('sample_date')['chain']
            .nunique()
            .rename('n_complete')
            .reset_index()
        )
        good_pre_dates = set(counts_k.loc[counts_k['n_complete'] >= k, 'sample_date'])

    # Build keep_mask: if we found any good pre-period dates, filter pre only; otherwise keep all rows
    if good_pre_dates:
        keep_mask = (
            ((df_wide['sample_date'] < intervention_date) & (df_wide['sample_date'].isin(good_pre_dates)))
            | (df_wide['sample_date'] >= intervention_date)
        )
    else:
        keep_mask = pd.Series(True, index=df_wide.index)

    df_wide = df_wide[keep_mask].copy()
    return df_wide, intervention_date, training_start


@app.cell
def run_synthetic_control(
    Dataprep,
    Synth,
    alpha_equal_input,
    controls_input,
    dependent_input,
    df_wide,
    intervention_date,
    lambda_cov_input,
    np,
    pd,
    predictors_input,
    training_start,
    treatment_input,
    weight_cap_input,
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

    # Convert to numeric float numpy arrays (robust to object dtypes, handles pd.NA)
    def _to_float_array(df_or_series):
        import pandas as _pd
        if isinstance(df_or_series, _pd.DataFrame):
            return df_or_series.to_numpy(dtype='float64', na_value=np.nan)
        elif isinstance(df_or_series, _pd.Series):
            return _pd.to_numeric(df_or_series, errors='coerce').to_numpy(dtype='float64')
        else:
            # Fallback for numpy arrays / lists
            arr = np.asarray(df_or_series)
            return arr.astype('float64', copy=False)

    X0_arr = _to_float_array(X0)
    X1_arr = _to_float_array(X1)
    Z0_arr = _to_float_array(Z0)
    Z1_arr = _to_float_array(Z1)

    # Hyperparameters from UI (model-only; no refetch)
    lambda_cov = float(lambda_cov_input.value)
    epsilon_ridge = 1e-10
    alpha_equal = float(alpha_equal_input.value)  # L2 toward uniform weights
    weight_cap = float(weight_cap_input.value)    # per-donor cap

    # Ensure 1D arrays for treated vectors when appropriate
    if X1_arr.ndim > 1 and X1_arr.shape[1] == 1:
        X1_arr_vec = X1_arr.ravel()
    else:
        X1_arr_vec = X1_arr

    if Z1_arr.ndim > 1 and Z1_arr.shape[1] == 1:
        Z1_arr_vec = Z1_arr.ravel()
    else:
        Z1_arr_vec = Z1_arr

    n_controls = len(controls_input.value)

    # --- Clean pre-period outcome rows: drop any time rows with NaNs in Z0 or Z1 ---
    if Z0_arr.ndim == 1:
        Z0_arr = Z0_arr.reshape(-1, 1)
    mask_pre_outcome = np.isfinite(Z1_arr_vec)
    if Z0_arr.size > 0:
        mask_pre_outcome &= np.all(np.isfinite(Z0_arr), axis=1)
    Z0_arr = Z0_arr[mask_pre_outcome]
    Z1_arr_vec = Z1_arr_vec[mask_pre_outcome]

    # Guardrail: need at least 3 pre-period rows to fit meaningfully
    min_rows = 3
    insufficient_pre_rows = (Z1_arr_vec.shape[0] < min_rows)

    # --- Clean predictor rows: drop predictors with any NaNs across controls or in treated ---
    # X0_arr: shape (p, n_controls); X1_arr_vec: shape (p,)
    if X0_arr.ndim == 1:
        X0_arr = X0_arr.reshape(-1, 1)
    mask_pred_rows = np.isfinite(X1_arr_vec)
    if X0_arr.size > 0:
        mask_pred_rows &= np.all(np.isfinite(X0_arr), axis=1)
    X0_arr = X0_arr[mask_pred_rows, :]
    X1_arr_vec = X1_arr_vec[mask_pred_rows]

    # If no valid predictor rows left, turn off covariate penalty
    if X1_arr_vec.size == 0 or X0_arr.shape[0] == 0:
        lambda_cov = 0.0

    # --- Outcome scaling for RMSPE: denom = synthetic_Z during optimization (guarded by epsilon) ---
    eps = 1e-9

    # --- Standardize predictors (z-score) across controls in pre-period ---
    # Center/scale each predictor row using control stats, then apply same transform to treated
    if X0_arr.size and X1_arr_vec.size and lambda_cov > 0.0:
        ctrl_mean = X0_arr.mean(axis=1, keepdims=True)
        ctrl_std = X0_arr.std(axis=1, ddof=1, keepdims=True)
        ctrl_std = np.where(ctrl_std < eps, 1.0, ctrl_std)
        X0_arr = (X0_arr - ctrl_mean)/ctrl_std
        X1_arr_vec = (X1_arr_vec - ctrl_mean.ravel())/ctrl_std.ravel()

    # Implement our own optimization to avoid pysyncon bug
    from scipy.optimize import minimize

    def objective(weights):
        # Nonnegative and sum-to-one (we also enforce with constraints below)
        w = np.clip(weights, 0, None)
        s = w.sum()
        if s == 0:
            return np.inf
        w = w / s

        # Outcome fit over pre period (RMSPE-style)
        synthetic_Z = Z0_arr @ w
        denom = np.where(np.isfinite(synthetic_Z) & (np.abs(synthetic_Z) > eps), synthetic_Z, eps)
        pe = (Z1_arr_vec - synthetic_Z)/denom
        pe = pe[np.isfinite(pe)]
        if pe.size < 3:
            return 1e12
        loss_outcome = np.sum(pe ** 2)

        # Predictor balance over pre period (z-scored, means, as per Dataprep predictors_op="mean")
        if lambda_cov == 0.0 or X0_arr.size == 0 or X1_arr_vec.size == 0:
            loss_cov = 0.0
        else:
            synthetic_X = X0_arr @ w
            diff_x = X1_arr_vec - synthetic_X
            diff_x = diff_x[np.isfinite(diff_x)]
            loss_cov = np.sum(diff_x ** 2) if diff_x.size else 0.0

        # Small ridge for numerical stability
        loss_ridge = epsilon_ridge * np.sum(w ** 2)

        # L2 penalty to keep weights near uniform and avoid extreme corners
        w_uniform = np.full_like(w, 1.0/len(w))
        loss_spread = alpha_equal * np.sum((w - w_uniform) ** 2)

        return float(loss_outcome + lambda_cov * loss_cov + loss_ridge + loss_spread)

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
            bounds=[(0, weight_cap) for _ in range(n_controls)],
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
            w = np.clip(weights, 0, None)
            s = w.sum()
            if s == 0:
                return np.inf
            w = w / s
            # Outcome RMSPE-style
            synthetic_Z = Z0_arr @ w
            denom = np.where(np.isfinite(synthetic_Z) & (np.abs(synthetic_Z) > eps), synthetic_Z, eps)
            pe = (Z1_arr_vec - synthetic_Z)/denom
            pe = pe[np.isfinite(pe)]
            if pe.size < 3:
                return 1e12
            loss_outcome = np.sum(pe ** 2)
            # Predictor z-loss
            if lambda_cov == 0.0 or X0_arr.size == 0 or X1_arr_vec.size == 0:
                loss_cov = 0.0
            else:
                synthetic_X = X0_arr @ w
                diff_x = X1_arr_vec - synthetic_X
                diff_x = diff_x[np.isfinite(diff_x)]
                loss_cov = np.sum(diff_x ** 2) if diff_x.size else 0.0
            loss_ridge = epsilon_ridge * np.sum(w ** 2)
            w_uniform = np.full_like(w, 1.0/len(w))
            loss_spread = alpha_equal * np.sum((w - w_uniform) ** 2)
            return float(loss_outcome + lambda_cov * loss_cov + loss_ridge + loss_spread)

        result = minimize(
            unconstrained_objective,
            x0,
            method='BFGS',
            options={'maxiter': 2000}
        )
        if result.success:
            weights = np.clip(result.x, 0, None)
            s = weights.sum()
            if s == 0:
                weights = np.ones_like(weights) / len(weights)
            else:
                weights = weights / s
            synthetic = Z0_arr @ weights
            # Compute loss using same logic as above for finite fallback
            denom = np.where(np.isfinite(synthetic) & (np.abs(synthetic) > eps), synthetic, eps)
            pe = (Z1_arr_vec - synthetic)/denom
            pe = pe[np.isfinite(pe)]
            loss = np.sum(pe ** 2) if pe.size else 0.0
            if lambda_cov > 0.0 and X0_arr.size and X1_arr_vec.size:
                synthetic_X = X0_arr @ weights
                diff_x = X1_arr_vec - synthetic_X
                diff_x = diff_x[np.isfinite(diff_x)]
                loss += lambda_cov * (np.sum(diff_x ** 2) if diff_x.size else 0.0)
            loss += epsilon_ridge * np.sum(weights ** 2)
            w_uniform = np.full_like(weights, 1.0/len(weights))
            loss += alpha_equal * np.sum((weights - w_uniform) ** 2)
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
            bounds=[(0, weight_cap) for _ in range(n_controls)],
            options={'maxiter': 2000}
        )
        if result.success and result.fun < best_loss:
            best_weights = result.x
            best_loss = result.fun
            optimization_method = "L-BFGS-B"
    except Exception as e:
        pass

    # Compute a finite fallback loss for equal weights (used if optimization fails)
    equal_w = np.ones(n_controls) / n_controls
    try:
        synth_eq_Z = Z0_arr @ equal_w if Z0_arr.size else np.array([])
        denom = np.where(np.isfinite(synth_eq_Z) & (np.abs(synth_eq_Z) > eps), synth_eq_Z, eps)
        pe = (Z1_arr_vec - synth_eq_Z)/denom
        pe = pe[np.isfinite(pe)]
        loss_eq = np.sum(pe ** 2) if pe.size else 0.0
        if lambda_cov > 0.0 and X0_arr.size and X1_arr_vec.size:
            synthetic_X = X0_arr @ equal_w
            diff_x = X1_arr_vec - synthetic_X
            diff_x = diff_x[np.isfinite(diff_x)]
            loss_eq += lambda_cov * (np.sum(diff_x ** 2) if diff_x.size else 0.0)
        # Add L2-to-uniform penalty (zero for equal weights, but keep for consistency)
        w_uniform = np.full_like(equal_w, 1.0/len(equal_w))
        loss_eq += alpha_equal * np.sum((equal_w - w_uniform) ** 2)
    except Exception:
        loss_eq = 0.0

    if best_weights is not None:
        optimal_weights = best_weights
        final_loss = best_loss
    else:
        optimal_weights = equal_w
        optimization_method = "Equal weights (optimization failed)"
        final_loss = float(loss_eq)

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
    - Loss: {final_loss:,.0f}
    - Optimal Weights: {', '.join([f'{name}: {weight:.3f}' for name, weight in zip(controls_input.value, optimal_weights)])}
    > (RMSPE-style pre-fit loss on outcome; lower is better)
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
    pd,
    treatment_input,
):
    fig = go.Figure()

    # Derive headline: average post-period percent gap (avoid exporting globals in marimo)
    def _compute_headline(_df: pd.DataFrame, _intervention) -> str:
        _post = _df[_df['date'] >= _intervention]
        _syn_mean = pd.to_numeric(_post['synthetic'], errors='coerce').mean()
        _gap_mean = pd.to_numeric(_post['gap'], errors='coerce').mean()
        if pd.notna(_syn_mean) and _syn_mean != 0 and pd.notna(_gap_mean):
            _pct = (_gap_mean / _syn_mean) * 100.0
            return (
                f"The treatment underperformed the counterfactual by ~{abs(_pct):.1f}% on average"
                if _pct < 0 else f"The treatment outperformed the counterfactual by ~{_pct:.1f}% on average"
            )
        return "Synthetic control comparison"

    headline = _compute_headline(df_results, intervention_date)
    mo.md(f"### {headline}")

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

    # Add intervention line (avoid annotation in add_vline for datetime values)
    x_vline = pd.to_datetime(intervention_date).to_pydatetime()
    fig.add_vline(
        x=x_vline,
        line_dash="dash",
        line_color="rgba(0, 0, 0, 0.5)",
        line_width=2
    )
    # Separate annotation pinned to the top of the plot
    fig.add_annotation(
        x=x_vline,
        y=1.02,
        xref="x",
        yref="paper",
        text="Intervention",
        showarrow=False,
        font=dict(size=11)
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
def display_tuning_controls(
    alpha_equal_input,
    lambda_cov_input,
    mo,
    resample_weekly_input,
    weight_cap_input,
):
    mo.md("#### Tuning (model-only; no refetch)")
    mo.hstack([lambda_cov_input, alpha_equal_input, weight_cap_input, resample_weekly_input], gap=8, justify='start', align='start')
    return


@app.cell
def display_summary_stats(
    analysis_summary,
    df_results,
    intervention_date,
    mo,
    np,
    pd,
    weights_dict,
):
    weights_formula = " + ".join([
        f"{chain} × {weight}" 
        for chain, weight in weights_dict.items()
    ])

    df_pre = df_results[df_results['date'] < intervention_date].copy()
    df_post = df_results[df_results['date'] >= intervention_date].copy()

    def _rmspe(y, yhat):
        y = pd.to_numeric(y, errors='coerce').to_numpy(dtype=float)
        yhat = pd.to_numeric(yhat, errors='coerce').to_numpy(dtype=float)
        mask = np.isfinite(y) & np.isfinite(yhat) & (yhat != 0)
        if mask.sum() == 0:
            return np.nan
        pct = (y[mask] - yhat[mask]) / yhat[mask]
        return float(np.sqrt(np.mean(pct ** 2)))

    pre_rmspe = _rmspe(df_pre['treatment'], df_pre['synthetic']) if len(df_pre) else np.nan
    post_rmspe = _rmspe(df_post['treatment'], df_post['synthetic']) if len(df_post) else np.nan
    rmspe_ratio = (post_rmspe / pre_rmspe) if (pre_rmspe and pre_rmspe > 0) else np.nan

    post_mean_gap = float(df_post['gap'].mean()) if len(df_post) else np.nan
    syn_mean_post = float(df_post['synthetic'].mean()) if len(df_post) else np.nan
    post_mean_gap_pct = (post_mean_gap / syn_mean_post * 100) if (syn_mean_post and syn_mean_post != 0) else np.nan
    cum_effect = float(df_post['gap'].sum()) if len(df_post) else np.nan

    mo.vstack([
        mo.md("## Model Results"),
        mo.hstack([
            mo.stat(
                label="Pre RMSPE",
                value=f"{pre_rmspe:,.3f}" if pre_rmspe == pre_rmspe else "—",
                caption="Lower is better pre-fit",
                bordered=True
            ),
            mo.stat(
                label="Post/Pre RMSPE Ratio",
                value=f"{rmspe_ratio:,.2f}" if rmspe_ratio == rmspe_ratio else "—",
                caption=">1 suggests worse post fit (signal)",
                bordered=True
            ),
            mo.stat(
                label="Avg Post Gap",
                value=f"{post_mean_gap:,.1f}" if post_mean_gap == post_mean_gap else "—",
                caption=(f"{post_mean_gap_pct:+.1f}% vs synthetic" if post_mean_gap_pct == post_mean_gap_pct else ""),
                bordered=True
            ),
            mo.stat(
                label="Cumulative Effect (post)",
                value=f"{cum_effect:,.1f}" if cum_effect == cum_effect else "—",
                caption="Sum of gaps",
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
