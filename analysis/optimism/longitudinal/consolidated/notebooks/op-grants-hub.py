import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    """Dashboard header"""
    mo.md(r"""
    # Optimism Grants Hub Dashboard
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-26</span></small>

    This interactive dashboard enables Optimism stakeholders to analyze grant program performance across programs, seasons, chains, and project categories. Look up any project or grant program and access comparable metrics for data-driven decision making.

    <i>Note: Grant and metrics data is updated regularly from OSO's consolidated data models.</i>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    """Context and methodology accordion"""
    mo.accordion({
        "Context": mo.md(r"""
        This dashboard provides comprehensive analysis of Optimism grant programs:

        - **Program Comparison**: Benchmark effectiveness and ROI across different grant seasons and missions
        - **Grant Deep Dive**: Compare performance of all grants within a single season across metrics and time periods
        - **Portfolio View**: Identify top and bottom performing funded projects
        - **Project Deep Dive**: View all grants received by a single project and its performance
        - **Chain Analysis**: Analyze projects on specific chains by funding and performance
        """),
        "Data Sources": mo.md(r"""
        **Data Models** (Location: `/Users/cerv1/GitHub/insights/analysis/optimism/longitudinal/consolidated/udms`)

        - `grants_consolidated.sql` - Funding data with dates, amounts, seasons, and project slugs
        - `monthly_metrics_by_project.sql` - Timeseries metrics by project
        - `metrics_catalog.sql` - Available metrics organized by category
        - `projects_catalog.sql` - Project mapping and metadata

        Data is refreshed regularly from OSO's data warehouse.
        """),
        "Methodology": mo.md(r"""
        **ROI Calculations**: ROI metrics are calculated as the metric growth per OP token spent:

        ```
        ROI = (Metric Value - Baseline) / OP Amount
        ```

        **Primary Metrics**:
        - **Superchain Revenue**: Gas fees × revshare scalar (1.0 or 0.15)
        - **Transactions**: Top-level transaction count
        - **User Ops**: Contract invocation count
        - **TVL Growth**: Total Value Locked from DefiLlama
        - **TVL Market Share**: Share of Superchain TVL
        - **Developer Activity**: Commits and contributors

        **Time Periods**: Analysis windows of 6, 12, and 18 months after funding_date
        """)
    })
    return


@app.cell(hide_code=True)
def _(mo):
    """Exchange Rate Settings section header"""
    mo.md(r"""
    ## Exchange Rate Settings
    Configure how currency conversions are applied throughout the dashboard.
    """)
    return


@app.cell(hide_code=True)
def _(df_prices, mo):
    """Exchange rate mode and currency selectors - create UI elements"""
    # Get available months where BOTH OP and ETH prices exist
    _op_months = set(df_prices[df_prices['token'] == 'OP']['date'].dt.strftime('%Y-%m').unique())
    _eth_months = set(df_prices[df_prices['token'] == 'ETH']['date'].dt.strftime('%Y-%m').unique())
    _available_months = sorted(_op_months & _eth_months, reverse=True)

    rate_mode_selector = mo.ui.dropdown(
        options=["Historical", "Fixed"],
        value="Historical",
        label="Rate Mode"
    )

    currency_selector = mo.ui.dropdown(
        options=["Default", "OP", "ETH", "USD"],
        value="Default",
        label="Currency"
    )

    fixed_rate_month = mo.ui.dropdown(
        options=_available_months,
        value=_available_months[0] if _available_months else None,
        label="Fixed Rate Month"
    )

    return currency_selector, fixed_rate_month, rate_mode_selector


@app.cell(hide_code=True)
def _(currency_selector, fixed_rate_month, mo, rate_mode_selector):
    """Exchange rate selectors - render with conditional display"""
    # Show fixed month selector only in Fixed mode
    if rate_mode_selector.value == "Fixed":
        _selectors = mo.hstack([rate_mode_selector, fixed_rate_month, currency_selector])
        _mode_help = mo.md("*Fixed mode: All conversions use the rate from the selected month.*")
    else:
        _selectors = mo.hstack([rate_mode_selector, currency_selector])
        _mode_help = mo.md("*Historical mode: Conversions use the rate from each transaction's date.*")

    mo.vstack([_selectors, _mode_help])
    return


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_prices, go, mo, pd):
    """Exchange rate time series chart"""
    # Pivot data for charting
    _op_prices = df_prices[df_prices['token'] == 'OP'].sort_values('date')
    _eth_prices = df_prices[df_prices['token'] == 'ETH'].sort_values('date')

    # Create dual-axis chart
    _fig = go.Figure()

    # OP price on primary y-axis (left)
    _fig.add_trace(go.Scatter(
        x=_op_prices['date'],
        y=_op_prices['price'],
        name='OP Price (USD)',
        mode='lines',
        line=dict(color='#FF0420', shape='hvh', width=2),
        yaxis='y1'
    ))

    # ETH price on secondary y-axis (right)
    _fig.add_trace(go.Scatter(
        x=_eth_prices['date'],
        y=_eth_prices['price'],
        name='ETH Price (USD)',
        mode='lines',
        line=dict(color='#627EEA', shape='hvh', width=2),
        yaxis='y2'
    ))

    # Apply layout with dual y-axes
    _layout = PLOTLY_LAYOUT.copy()
    _layout['height'] = 350
    _layout['margin'] = dict(t=10, l=60, r=60, b=40)
    _layout['yaxis'] = dict(
        title='OP Price ($)',
        title_font=dict(color='#FF0420'),
        tickfont=dict(color='#FF0420'),
        tickformat='$.2f',
        showgrid=True,
        gridcolor='#EEE',
        side='left'
    )
    _layout['yaxis2'] = dict(
        title='ETH Price ($)',
        title_font=dict(color='#627EEA'),
        tickfont=dict(color='#627EEA'),
        tickformat='$,.0f',
        overlaying='y',
        side='right',
        showgrid=False
    )
    _layout['legend'] = dict(
        orientation='h',
        yanchor='bottom',
        y=1.02,
        xanchor='left',
        x=0
    )
    _layout['xaxis'] = {**PLOTLY_LAYOUT['xaxis'], 'title': '', 'tickformat': '%Y-%m'}

    _fig.update_layout(**_layout)

    mo.vstack([
        mo.md("#### Token Prices Over Time"),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return


@app.cell(hide_code=True)
def _(df_prices, fixed_rate_month, get_price, mo, pd, rate_mode_selector):
    """Exchange rate summary stats"""
    # Determine which date to use for rates
    if rate_mode_selector.value == "Fixed" and fixed_rate_month.value:
        _rate_date = pd.to_datetime(fixed_rate_month.value + "-01")
        _caption = f"as of {fixed_rate_month.value}"
    else:
        _rate_date = df_prices['date'].max()
        _caption = "latest available"

    # Get prices
    _op_price = get_price(df_prices, 'OP', _rate_date)
    _eth_price = get_price(df_prices, 'ETH', _rate_date)

    # Calculate OP/ETH ratio (how many OP per 1 ETH)
    _op_per_eth = _eth_price / _op_price if _op_price and _op_price > 0 else 0

    # Format values
    _op_str = f"${_op_price:.2f}" if _op_price else "N/A"
    _eth_str = f"${_eth_price:,.0f}" if _eth_price else "N/A"
    _ratio_str = f"{_op_per_eth:,.0f}" if _op_per_eth else "N/A"

    # Create stat cards
    _card_op = mo.stat(
        label="OP Price",
        value=_op_str,
        caption=_caption,
        bordered=True
    )

    _card_eth = mo.stat(
        label="ETH Price",
        value=_eth_str,
        caption=_caption,
        bordered=True
    )

    _card_ratio = mo.stat(
        label="OP per ETH",
        value=_ratio_str,
        caption="exchange ratio",
        bordered=True
    )

    mo.hstack([_card_op, _card_eth, _card_ratio], widths="equal")
    return


@app.cell(hide_code=True)
def _(mo):
    """Exchange rate methodology accordion"""
    mo.accordion({
        "Currency Modes": mo.md(r"""
**Default**: Grants displayed in OP, Revenue displayed in ETH (no conversions applied)

**OP**: All values converted to OP tokens
- Grants: Displayed as-is (already in OP)
- Revenue: Converted from ETH → OP

**ETH**: All values converted to ETH
- Grants: Converted from OP → ETH
- Revenue: Displayed as-is (already in ETH)

**USD**: All values converted to US Dollars
- Grants: Converted from OP → USD
- Revenue: Converted from ETH → USD
        """),
        "Rate Modes": mo.md(r"""
**Historical**: Uses the exchange rate from each transaction's funding date. This reflects the actual value at the time of the grant.

**Fixed**: Uses a single exchange rate from a user-selected month for all conversions. Useful for comparing grants in consistent terms.

*Note: For mid-month dates, the rate from the nearest available month is used.*
        """)
    })
    return


@app.cell(hide_code=True)
def _(
    REVENUE_METRICS,
    convert_grant_amount,
    convert_revenue_amount,
    currency_selector,
    df_grants,
    df_metrics,
    df_prices,
    fixed_rate_month,
    format_amount_by_unit,
    get_grant_unit,
    get_metric_sum,
    get_revenue_unit,
    mo,
    pd,
    rate_mode_selector,
):
    """Summary metrics cards using mo.stat"""
    # Get current currency settings
    _currency_mode = currency_selector.value
    _rate_mode = rate_mode_selector.value
    _fixed_date = pd.to_datetime(fixed_rate_month.value + "-01") if fixed_rate_month.value else None

    # Get units for display
    _grant_unit = get_grant_unit(_currency_mode)
    _revenue_unit = get_revenue_unit(_currency_mode)

    # Calculate summary statistics
    _total_op = df_grants['amount'].sum()
    _total_projects = df_grants['oso_project_slug'].nunique()
    _total_grants = len(df_grants)
    _seasons = df_grants['grants_season_or_mission'].nunique()

    # Use latest date for aggregate conversions
    _latest_date = df_metrics['sample_date'].max() if not df_metrics.empty else None

    # Convert total funding based on currency setting
    _converted_funding = convert_grant_amount(
        _total_op, _latest_date, _currency_mode, _rate_mode, _fixed_date, df_prices
    )
    _op_str = format_amount_by_unit(_converted_funding, _grant_unit)

    # Calculate Superchain Revenue using metric constants
    _total_revenue = get_metric_sum(df_metrics, REVENUE_METRICS)

    # Convert revenue based on currency setting
    _converted_revenue = convert_revenue_amount(
        _total_revenue, _latest_date, _currency_mode, _rate_mode, _fixed_date, df_prices
    )
    _revenue_str = format_amount_by_unit(_converted_revenue, _revenue_unit)

    # Calculate TVL using metric constants (get latest snapshot, not sum)
    # TVL stays in USD regardless of currency mode
    _tvl_df = df_metrics[df_metrics['metric_name'] == 'TVL']
    if not _tvl_df.empty:
        _tvl_latest_date = _tvl_df['sample_date'].max()
        _total_tvl = _tvl_df[_tvl_df['sample_date'] == _tvl_latest_date]['amount'].sum()
        _tvl_date_str = _tvl_latest_date.strftime('%Y-%m-%d')
    else:
        _total_tvl = 0
        _tvl_date_str = 'N/A'

    if _total_tvl >= 1_000_000_000:
        _tvl_str = f"${_total_tvl/1e9:.1f}B"
    elif _total_tvl >= 1_000_000:
        _tvl_str = f"${_total_tvl/1e6:.1f}M"
    elif _total_tvl >= 1_000:
        _tvl_str = f"${_total_tvl/1e3:.0f}K"
    else:
        _tvl_str = f"${_total_tvl:.0f}"

    # Create summary cards using mo.stat with dynamic labels
    _card_total_op = mo.stat(
        label=f"Total Allocated ({_grant_unit})",
        value=_op_str,
        caption=f"{_total_grants:,} grants across {_seasons} seasons",
        bordered=True
    )

    _card_total_projects = mo.stat(
        label="Funded Projects",
        value=f"{_total_projects:,}",
        caption="unique projects",
        bordered=True
    )

    _card_total_revenue = mo.stat(
        label=f"Superchain Revenue ({_revenue_unit})",
        value=_revenue_str,
        caption="cumulative all time",
        bordered=True
    )

    _card_total_tvl = mo.stat(
        label="Current TVL",
        value=_tvl_str,
        caption=f"as of {_tvl_date_str}",
        bordered=True
    )

    # Get data freshness from metrics
    _freshness_str = _latest_date.strftime("%B %Y") if _latest_date else "Unknown"

    # Display cards horizontally with freshness indicator
    mo.vstack([
        mo.hstack([_card_total_op, _card_total_projects, _card_total_revenue, _card_total_tvl], widths="equal"),
        mo.md(f"*Data through {_freshness_str}*")
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    """Section: Season Benchmarking"""
    mo.md(r"""
    ## Part 1: Season Benchmarking
    Compare grant programs by season/mission to benchmark effectiveness and ROI.
    """)
    return


@app.cell(hide_code=True)
def _(
    REVENUE_METRICS,
    calculate_baseline_value,
    calculate_current_value,
    calculate_period_average,
    calculate_rate_of_change_roi,
    calculate_roi,
    convert_grant_amount,
    convert_revenue_amount,
    currency_selector,
    df_grants,
    df_metrics,
    df_prices,
    fixed_rate_month,
    format_amount_by_unit,
    get_grant_unit,
    get_revenue_unit,
    fmt_int,
    fmt_usd,
    fmt_delta_usd,
    mo,
    pd,
    rate_mode_selector,
):
    """Season benchmarking table with time-windowed ROI calculations"""
    # Get current currency settings
    _currency_mode = currency_selector.value
    _rate_mode = rate_mode_selector.value
    _fixed_date = pd.to_datetime(fixed_rate_month.value + "-01") if fixed_rate_month.value else None

    # Get units for display
    _grant_unit = get_grant_unit(_currency_mode)
    _revenue_unit = get_revenue_unit(_currency_mode)

    # Group grants by season
    _season_summary = df_grants.groupby('grants_season_or_mission').agg({
        'amount': 'sum',
        'oso_project_slug': 'nunique',
        'application_name': 'count',
        'funding_date': 'min'  # Earliest funding date in season
    }).reset_index()
    _season_summary.columns = ['Season/Mission', 'Total OP', 'Projects', 'Total Grants', 'Season Start']

    # Calculate metrics with proper baseline/current methodology
    _season_metrics = []
    for _, _row in _season_summary.iterrows():
        _season = _row['Season/Mission']
        _season_start = _row['Season Start']
        _total_op = _row['Total OP']

        # Convert grant amount based on currency setting
        _converted_funding = convert_grant_amount(
            _total_op, _season_start, _currency_mode, _rate_mode, _fixed_date, df_prices
        )

        # Get project IDs for this season
        _project_ids = df_grants[
            df_grants['grants_season_or_mission'] == _season
        ]['oso_project_id'].dropna().unique()

        # Get metrics for these projects
        _season_df = df_metrics[df_metrics['project_id'].isin(_project_ids)]

        # Revenue: sum of all revenue metrics (cumulative)
        _revenue_df = _season_df[_season_df['metric_name'].isin(REVENUE_METRICS)]
        _total_revenue = _revenue_df['amount'].sum() if not _revenue_df.empty else 0

        # Convert revenue based on currency setting
        _converted_revenue = convert_revenue_amount(
            _total_revenue, _season_start, _currency_mode, _rate_mode, _fixed_date, df_prices
        )

        # TVL: use funding month methodology (TVL stays in USD regardless of currency mode)
        # For monthly data, look at funding month (not 7-day window)
        _tvl_df = _season_df[_season_df['metric_name'] == 'TVL']
        _month_start = _season_start.replace(day=1)
        _month_end = (_month_start + pd.DateOffset(months=1)) - pd.Timedelta(days=1)
        _baseline_tvl_df = _tvl_df[
            (_tvl_df['sample_date'] >= _month_start) &
            (_tvl_df['sample_date'] <= _month_end)
        ]
        _baseline_tvl = _baseline_tvl_df['amount'].sum() if not _baseline_tvl_df.empty else 0
        _current_tvl = calculate_current_value(_tvl_df)
        _tvl_delta = _current_tvl - _baseline_tvl

        # Calculate ROIs using converted values
        _revenue_roi = calculate_roi(_converted_revenue, _converted_funding) if _converted_funding else 0
        _tvl_roi = calculate_roi(_tvl_delta, _converted_funding) if _converted_funding else 0

        _season_metrics.append({
            'Season/Mission': _season,
            'Total Funding': _converted_funding,
            'Revenue': _converted_revenue,
            'TVL Delta': _tvl_delta,
            'Current TVL': _current_tvl,
            'Revenue ROI': _revenue_roi,
            'TVL ROI': _tvl_roi
        })

    _metrics_df = pd.DataFrame(_season_metrics)

    # Build column headers with units
    _funding_col = f"Total Funding ({_grant_unit})"
    _revenue_col = f"Revenue ({_revenue_unit})"
    _revenue_roi_col = f"Revenue ROI ({_revenue_unit}/{_grant_unit})"
    _tvl_roi_col = f"TVL ROI ($/{_grant_unit})"

    # Rename for display and sort by Revenue ROI (descending)
    _display_df = _metrics_df[['Season/Mission', 'Total Funding', 'Revenue', 'TVL Delta', 'Revenue ROI', 'TVL ROI']].copy()
    _display_df = _display_df.merge(
        _season_summary[['Season/Mission', 'Projects', 'Total Grants']],
        on='Season/Mission',
        how='left'
    )
    # Sort by Revenue ROI descending before renaming columns
    _display_df = _display_df.sort_values('Revenue ROI', ascending=False)
    _display_df = _display_df[['Season/Mission', 'Total Funding', 'Projects', 'Total Grants',
                               'Revenue', 'TVL Delta', 'Revenue ROI', 'TVL ROI']].reset_index(drop=True)
    _display_df.columns = ['Season/Mission', _funding_col, 'Projects', 'Total Grants',
                           _revenue_col, 'TVL Delta', _revenue_roi_col, _tvl_roi_col]

    # Create formatters for each unit type
    def _fmt_funding(x):
        return format_amount_by_unit(x, _grant_unit)

    def _fmt_revenue(x):
        return format_amount_by_unit(x, _revenue_unit)

    # Updated ROI formatters to use proper sign format: -$X or +$X
    def _fmt_roi_revenue(x):
        if x is None or pd.isna(x):
            return "—"
        if _revenue_unit == "ETH":
            return f"+{x:.4f}" if x >= 0 else f"-{abs(x):.4f}"
        elif _revenue_unit == "OP":
            return f"+{x:.2f} OP" if x >= 0 else f"-{abs(x):.2f} OP"
        elif _revenue_unit == "USD":
            return f"+${x:.2f}" if x >= 0 else f"-${abs(x):.2f}"
        return f"+{x:.4f}" if x >= 0 else f"-{abs(x):.4f}"

    def _fmt_roi_tvl(x):
        if x is None or pd.isna(x):
            return "—"
        return f"+${x:.2f}" if x >= 0 else f"-${abs(x):.2f}"

    _season_table = mo.ui.table(
        data=_display_df,
        selection=None,
        label="Season Benchmarking",
        page_size=50,
        show_column_summaries=False,
        show_data_types=False,
        format_mapping={
            _funding_col: _fmt_funding,
            'Projects': fmt_int,
            'Total Grants': fmt_int,
            _revenue_col: _fmt_revenue,
            'TVL Delta': fmt_delta_usd,
            _revenue_roi_col: _fmt_roi_revenue,
            _tvl_roi_col: _fmt_roi_tvl,
        }
    )

    # Calculate weighted average ROI (weighted by funding amount) for context
    if not _metrics_df.empty:
        _total_funding_all = _metrics_df['Total Funding'].sum()
        if _total_funding_all > 0:
            _weighted_avg_roi = (_metrics_df['Revenue ROI'] * _metrics_df['Total Funding']).sum() / _total_funding_all
        else:
            _weighted_avg_roi = 0
    else:
        _weighted_avg_roi = 0

    # Find best performing season by Revenue ROI
    if not _display_df.empty and _revenue_roi_col in _display_df.columns:
        _best_idx = _display_df[_revenue_roi_col].idxmax()
        _best_season = _display_df.loc[_best_idx, 'Season/Mission']
        _best_roi = _display_df.loc[_best_idx, _revenue_roi_col]

        # Format best ROI
        if _revenue_unit == "ETH":
            _best_roi_fmt = f"+{_best_roi:.4f}/{_grant_unit}" if _best_roi >= 0 else f"-{abs(_best_roi):.4f}/{_grant_unit}"
            _avg_roi_fmt = f"{_weighted_avg_roi:.4f}/{_grant_unit}"
        elif _revenue_unit == "OP":
            _best_roi_fmt = f"+{_best_roi:.2f} OP/{_grant_unit}" if _best_roi >= 0 else f"-{abs(_best_roi):.2f} OP/{_grant_unit}"
            _avg_roi_fmt = f"{_weighted_avg_roi:.2f} OP/{_grant_unit}"
        else:
            _best_roi_fmt = f"+${_best_roi:.2f}/{_grant_unit}" if _best_roi >= 0 else f"-${abs(_best_roi):.2f}/{_grant_unit}"
            _avg_roi_fmt = f"${_weighted_avg_roi:.2f}/{_grant_unit}"

        _callout = mo.callout(
            mo.md(f"**Top Performer**: {_best_season} achieved the highest Revenue ROI at {_best_roi_fmt}. Weighted average across all seasons: {_avg_roi_fmt}"),
            kind="success"
        )
    else:
        _callout = None

    mo.vstack([_season_table, _callout] if _callout else [_season_table])
    return


@app.cell(hide_code=True)
def _(mo):
    """Section: Grant Comparison Within Season"""
    mo.md(r"""
    ## Part 2: Grant Comparison Within Season
    Deep dive on grants within a single season to compare performance across metrics and time periods.
    """)
    return


@app.cell(hide_code=True)
def _(df_grants, mo):
    """Grant comparison filters"""
    _seasons = sorted(df_grants['grants_season_or_mission'].dropna().unique().tolist())
    season_selector = mo.ui.dropdown(
        options=_seasons,
        value=_seasons[0] if _seasons else None,
        label="Select Season/Mission"
    )

    metric_selector = mo.ui.dropdown(
        options=[
            "TVL",
            "Superchain Revenue",
            "Transactions",
            "User Ops",
            "Developer Activity"
        ],
        value="TVL",
        label="Metric"
    )

    mo.hstack([season_selector, metric_selector])
    return metric_selector, season_selector


@app.cell(hide_code=True)
def _(
    METRIC_GROUPS,
    PLOTLY_LAYOUT,
    calculate_period_average,
    convert_grant_amount,
    convert_revenue_amount,
    currency_selector,
    df_grants,
    df_metrics,
    df_prices,
    fixed_rate_month,
    format_amount_by_unit,
    get_grant_unit,
    get_revenue_unit,
    fmt_date,
    fmt_int,
    fmt_usd,
    fmt_delta_usd,
    fmt_delta_eth,
    fmt_delta_int,
    go,
    metric_selector,
    mo,
    pd,
    rate_mode_selector,
    season_selector,
):
    """Grant comparison table and chart with multi-period columns"""
    if season_selector.value:
        # Get current currency settings
        _currency_mode = currency_selector.value
        _rate_mode = rate_mode_selector.value
        _fixed_date = pd.to_datetime(fixed_rate_month.value + "-01") if fixed_rate_month.value else None

        # Get units for display
        _grant_unit = get_grant_unit(_currency_mode)
        _revenue_unit = get_revenue_unit(_currency_mode)

        # Filter grants for selected season
        _filtered_grants = df_grants[df_grants['grants_season_or_mission'] == season_selector.value]

        # Get metric names for selected metric group (used for period calculations)
        _selected_metrics = METRIC_GROUPS.get(metric_selector.value, [])

        # For TVL, baseline uses 'TVL' (point-in-time), periods use 'TVL Inflows' (changes)
        _is_tvl = metric_selector.value == "TVL"
        _baseline_metric_names = ['TVL'] if _is_tvl else _selected_metrics

        # Determine if this is a revenue metric (needs currency conversion)
        _is_revenue = metric_selector.value == "Superchain Revenue"

        # For each grant, calculate metric performance at 6-month, 12-month, and total since funding
        _grant_performance = []
        _today = pd.Timestamp.now()

        for _, _grant in _filtered_grants.iterrows():
            _project_id = _grant['oso_project_id']
            _funding_date = _grant['funding_date']
            _amount = _grant['amount']

            # Convert grant amount based on currency setting
            _converted_amount = convert_grant_amount(
                _amount, _funding_date, _currency_mode, _rate_mode, _fixed_date, df_prices
            )

            if pd.notna(_project_id):
                # Get baseline metrics (TVL snapshot for TVL, or same as period metrics for others)
                _baseline_project_metrics = df_metrics[
                    (df_metrics['project_id'] == _project_id) &
                    (df_metrics['metric_name'].isin(_baseline_metric_names))
                ]

                # Get period metrics (TVL Inflows for TVL, or same metrics for others)
                _period_project_metrics = df_metrics[
                    (df_metrics['project_id'] == _project_id) &
                    (df_metrics['metric_name'].isin(_selected_metrics))
                ]
            else:
                _baseline_project_metrics = df_metrics.head(0)
                _period_project_metrics = df_metrics.head(0)

            # Calculate baseline: value in the funding month (summed across chains for that month)
            _funding_month_start = _funding_date.replace(day=1)
            _funding_month_end = (_funding_month_start + pd.DateOffset(months=1)) - pd.Timedelta(days=1)
            _baseline_metrics = _baseline_project_metrics[
                (_baseline_project_metrics['sample_date'] >= _funding_month_start) &
                (_baseline_project_metrics['sample_date'] <= _funding_month_end)
            ]
            _baseline_value = _baseline_metrics['amount'].sum()

            # Calculate 6-month AVERAGE monthly value (not cumulative sum)
            # This is for rate-of-change ROI: (avg_monthly - baseline) / funding
            _6m_avg, _6m_months = calculate_period_average(_period_project_metrics, _funding_date, 6)

            # Calculate 12-month AVERAGE monthly value
            _12m_avg, _12m_months = calculate_period_average(_period_project_metrics, _funding_date, 12)

            # Get period metrics after funding for total calculation
            _period_metrics_after = _period_project_metrics[_period_project_metrics['sample_date'] > _funding_date]
            _total_since_funding = _period_metrics_after['amount'].sum()

            # Convert revenue metrics based on currency setting
            if _is_revenue:
                _baseline_value = convert_revenue_amount(
                    _baseline_value, _funding_date, _currency_mode, _rate_mode, _fixed_date, df_prices
                )
                _6m_avg = convert_revenue_amount(
                    _6m_avg, _funding_date, _currency_mode, _rate_mode, _fixed_date, df_prices
                )
                _12m_avg = convert_revenue_amount(
                    _12m_avg, _funding_date, _currency_mode, _rate_mode, _fixed_date, df_prices
                )
                _total_since_funding = convert_revenue_amount(
                    _total_since_funding, _funding_date, _currency_mode, _rate_mode, _fixed_date, df_prices
                )

            # Calculate 6-month ROI using rate-of-change methodology
            # ROI = (avg_monthly_post_funding - baseline) / funding_amount
            _6m_delta = _6m_avg - _baseline_value
            _6m_roi = _6m_delta / _converted_amount if _converted_amount and _converted_amount > 0 else 0

            _grant_performance.append({
                'Project': _grant['application_name'],
                'Funding Date': _funding_date,
                'Grant': _converted_amount,
                'Baseline': _baseline_value,
                '6M Avg': _6m_avg,
                '12M Avg': _12m_avg,
                '6M Delta': _6m_delta,
                'Total Since Funding': _total_since_funding,
                '6M ROI': _6m_roi,
            })

        _perf_df = pd.DataFrame(_grant_performance)

        # Filter to grants with data and sort by 6M Delta (rate of change) for chart
        _chart_df = _perf_df[_perf_df['6M Avg'] != 0].copy()
        _chart_df = _chart_df.nlargest(15, '6M Delta')  # Sort by Delta value for the chart
        _chart_df = _chart_df.sort_values('6M Delta', ascending=True)  # Ascending for horizontal bar (top at top)
        _total_with_data = len(_perf_df[_perf_df['6M Avg'] != 0])

        # Create horizontal bar chart showing 6M delta (rate of change)
        _colors = ['#00D395' if x >= 0 else '#FF0420' for x in _chart_df['6M Delta']]

        _fig = go.Figure()
        _fig.add_trace(go.Bar(
            x=_chart_df['6M Delta'],
            y=_chart_df['Project'],
            orientation='h',
            marker_color=_colors,
            text=_chart_df['6M ROI'].apply(lambda x: f"ROI: {'+' if x >= 0 else ''}{x:.2f}"),
            textposition='auto'
        ))

        # Apply layout
        _layout = PLOTLY_LAYOUT.copy()
        _layout['height'] = max(300, min(len(_chart_df), 15) * 30)
        _layout['margin'] = dict(t=10, l=150, r=30, b=40)

        # Set axis formatting based on metric type and currency mode
        # Chart now shows rate of change (avg - baseline), not cumulative
        if metric_selector.value == "Superchain Revenue":
            _chart_title = f'6-Month Δ Revenue ({_revenue_unit}/mo vs baseline)'
            _tickformat = ',.0s' if _revenue_unit != "USD" else '$,.0s'
        elif metric_selector.value == "TVL":
            _chart_title = '6-Month Δ TVL ($/mo vs baseline)'
            _tickformat = '$,.0s'
        else:
            _chart_title = f'6-Month Δ {metric_selector.value} (/mo vs baseline)'
            _tickformat = ',.0s'

        _layout['xaxis'] = {**PLOTLY_LAYOUT['xaxis'], 'title': _chart_title, 'tickformat': _tickformat}
        _layout['yaxis'] = dict(title='', showgrid=False, linecolor='#000', linewidth=1)
        _fig.update_layout(**_layout)

        # Build column headers with units
        _grant_col = f"Grant ({_grant_unit})"
        if _is_revenue:
            _metric_unit = _revenue_unit
        elif _is_tvl:
            _metric_unit = "$"
        else:
            _metric_unit = ""

        _roi_col = f"6M ROI ({_metric_unit}/{_grant_unit})" if _metric_unit else f"6M ROI (/{_grant_unit})"

        # Filter table to exclude projects with all zero metrics and sort by ROI
        _total_grants = len(_perf_df)
        _display_df = _perf_df[
            (_perf_df['6M Avg'] != 0) | (_perf_df['12M Avg'] != 0) | (_perf_df['Total Since Funding'] != 0)
        ][['Project', 'Funding Date', 'Grant', 'Baseline', '6M Avg', '12M Avg', '6M Delta', '6M ROI']].copy()
        _display_df = _display_df.sort_values('6M ROI', ascending=False).reset_index(drop=True)
        _display_df.columns = ['Project', 'Funding Date', _grant_col, 'Baseline', '6M Avg', '12M Avg', '6M Delta', _roi_col]
        _grants_with_data = len(_display_df)

        # Create formatters for each unit type
        def _fmt_grant(x):
            return format_amount_by_unit(x, _grant_unit)

        # Choose metric formatter and delta formatter based on metric type
        if metric_selector.value == "Superchain Revenue":
            def _metric_fmt(x):
                return format_amount_by_unit(x, _revenue_unit)
            if _revenue_unit == "ETH":
                _delta_fmt = fmt_delta_eth
            elif _revenue_unit == "USD":
                _delta_fmt = fmt_delta_usd
            else:
                _delta_fmt = _metric_fmt  # For OP, use same format
            def _roi_fmt(x):
                if x is None or pd.isna(x):
                    return "—"
                if _revenue_unit == "ETH":
                    return f"+{x:.4f}" if x >= 0 else f"-{abs(x):.4f}"
                elif _revenue_unit == "OP":
                    return f"+{x:.2f} OP" if x >= 0 else f"-{abs(x):.2f} OP"
                elif _revenue_unit == "USD":
                    return f"+${x:.2f}" if x >= 0 else f"-${abs(x):.2f}"
                return f"+{x:.4f}" if x >= 0 else f"{x:.4f}"
        elif metric_selector.value == "TVL":
            _metric_fmt = fmt_usd
            _delta_fmt = fmt_delta_usd
            def _roi_fmt(x):
                if x is None or pd.isna(x):
                    return "—"
                return f"+${x:.2f}" if x >= 0 else f"-${abs(x):.2f}"
        else:
            _metric_fmt = fmt_int
            _delta_fmt = fmt_delta_int
            def _roi_fmt(x):
                if x is None or pd.isna(x):
                    return "—"
                return f"+{x:.2f}" if x >= 0 else f"-{abs(x):.2f}"

        # Handle empty state when no grants have metric data
        if _grants_with_data == 0:
            _output = mo.vstack([
                mo.md(f"*{_total_grants} grants in this season*"),
                mo.callout(
                    mo.md(f"No grants in this season have {metric_selector.value} data available yet."),
                    kind="warn"
                )
            ])
        else:
            _output = mo.vstack([
                mo.md(f"*Showing {_grants_with_data} of {_total_grants} grants with metric data, sorted by 6M ROI*"),
                mo.ui.table(
                    _display_df,
                    label=f"{season_selector.value} - {metric_selector.value}",
                    show_column_summaries=False,
                    show_data_types=False,
                    format_mapping={
                        'Funding Date': fmt_date,
                        _grant_col: _fmt_grant,
                        'Baseline': _metric_fmt,
                        '6M Avg': _metric_fmt,
                        '12M Avg': _metric_fmt,
                        '6M Delta': _delta_fmt,
                        _roi_col: _roi_fmt,
                    }
                ),
                mo.md(f"#### 6-Month Rate of Change: {'TVL' if metric_selector.value == 'TVL' else metric_selector.value}"),
                mo.ui.plotly(_fig, config={'displayModeBar': False}),
                mo.md(f"*Showing top {min(len(_chart_df), 15)} of {_total_with_data} grants by 6M Delta*")
            ])
    else:
        _output = mo.md("Please select a season to view grant comparison.")

    _output
    return


@app.cell(hide_code=True)
def _(mo):
    """Section: Winners and Losers"""
    mo.md(r"""
    ## Part 3: Winners and Losers
    Identify top and bottom performing funded projects across all programs.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    """Winners and losers metric selector with minimum OP filter"""
    winners_metric_selector = mo.ui.dropdown(
        options=["Superchain Revenue", "TVL", "Transactions", "User Ops", "Developer Activity"],
        value="Superchain Revenue",
        label="Metric"
    )

    min_op_slider = mo.ui.slider(
        start=0,
        stop=1_000_000,
        step=10_000,
        value=100_000,
        label="Minimum OP Received",
        show_value=True,
        full_width=False
    )

    log_scale_checkbox = mo.ui.checkbox(
        value=True,
        label="Use log scale"
    )

    mo.hstack([winners_metric_selector, min_op_slider, log_scale_checkbox])
    return log_scale_checkbox, min_op_slider, winners_metric_selector


@app.cell(hide_code=True)
def _(
    METRIC_GROUPS,
    PLOTLY_LAYOUT,
    calculate_period_average,
    convert_grant_amount,
    convert_revenue_amount,
    currency_selector,
    df_grants,
    df_metrics,
    df_prices,
    fixed_rate_month,
    format_amount_by_unit,
    get_grant_unit,
    get_revenue_unit,
    fmt_int,
    fmt_usd,
    fmt_delta_usd,
    fmt_delta_eth,
    fmt_delta_int,
    go,
    log_scale_checkbox,
    min_op_slider,
    mo,
    pd,
    rate_mode_selector,
    winners_metric_selector,
):
    """Winners and losers tables with scatter plot"""
    # Get current currency settings
    _currency_mode = currency_selector.value
    _rate_mode = rate_mode_selector.value
    _fixed_date = pd.to_datetime(fixed_rate_month.value + "-01") if fixed_rate_month.value else None

    # Get units for display
    _grant_unit = get_grant_unit(_currency_mode)
    _revenue_unit = get_revenue_unit(_currency_mode)

    # Determine if this is a revenue metric
    _is_revenue = winners_metric_selector.value == "Superchain Revenue"

    # Get metric names for selected metric group
    _selected_metrics = METRIC_GROUPS.get(winners_metric_selector.value, [])

    # Aggregate grants by project - include oso_project_id for joining with metrics
    _project_grants = df_grants.groupby('oso_project_id').agg({
        'amount': 'sum',
        'application_name': 'first',
        'oso_project_slug': 'first',
        'funding_date': ['count', 'min']  # Count of grants and earliest funding date
    }).reset_index()
    _project_grants.columns = ['project_id', 'total_funding', 'project_name', 'project_slug', 'grants_count', 'earliest_funding']

    # Apply minimum OP filter (before currency conversion)
    _min_op = min_op_slider.value
    _project_grants_filtered = _project_grants[_project_grants['total_funding'] >= _min_op]
    _total_projects = len(_project_grants)
    _filtered_projects = len(_project_grants_filtered)

    # Calculate metrics for each project using rate-of-change methodology
    _project_performance = []
    for _, _proj in _project_grants_filtered.iterrows():
        _earliest_date = _proj['earliest_funding']

        # Convert funding based on currency setting (use earliest date for Historical mode)
        _converted_funding = convert_grant_amount(
            _proj['total_funding'], _earliest_date, _currency_mode, _rate_mode, _fixed_date, df_prices
        )

        if pd.notna(_proj['project_id']):
            _project_metrics = df_metrics[df_metrics['project_id'] == _proj['project_id']]
            _filtered_metrics = _project_metrics[
                _project_metrics['metric_name'].isin(_selected_metrics)
            ]

            # Calculate baseline (funding month value)
            _funding_month_start = _earliest_date.replace(day=1)
            _funding_month_end = (_funding_month_start + pd.DateOffset(months=1)) - pd.Timedelta(days=1)
            _baseline_metrics = _filtered_metrics[
                (_filtered_metrics['sample_date'] >= _funding_month_start) &
                (_filtered_metrics['sample_date'] <= _funding_month_end)
            ]
            _baseline_value = _baseline_metrics['amount'].sum()

            # Calculate 6-month average (rate-of-change methodology)
            _6m_avg, _6m_months = calculate_period_average(_filtered_metrics, _earliest_date, 6)

            # Calculate delta (rate of change)
            _metric_delta = _6m_avg - _baseline_value
        else:
            _baseline_value = 0
            _6m_avg = 0
            _metric_delta = 0

        # Convert revenue metrics based on currency setting
        if _is_revenue:
            _baseline_value = convert_revenue_amount(
                _baseline_value, _earliest_date, _currency_mode, _rate_mode, _fixed_date, df_prices
            )
            _6m_avg = convert_revenue_amount(
                _6m_avg, _earliest_date, _currency_mode, _rate_mode, _fixed_date, df_prices
            )
            _metric_delta = _6m_avg - _baseline_value

        # Calculate ROI using rate-of-change: (avg - baseline) / funding
        _roi = _metric_delta / _converted_funding if _converted_funding and _converted_funding > 0 else 0

        _project_performance.append({
            'Project': _proj['project_name'],
            'Total Funding': _converted_funding,
            'Grants': _proj['grants_count'],
            'Baseline': _baseline_value,
            '6M Avg': _6m_avg,
            'Delta': _metric_delta,
            'ROI': _roi
        })

    _perf_df = pd.DataFrame(_project_performance)
    _perf_df = _perf_df.sort_values('ROI', ascending=False)

    # Build column headers with units
    _funding_col = f"Total Funding ({_grant_unit})"
    if _is_revenue:
        _metric_unit = _revenue_unit
    elif winners_metric_selector.value == "TVL":
        _metric_unit = "$"
    else:
        _metric_unit = ""

    _baseline_col = f"Baseline ({_metric_unit})" if _metric_unit else "Baseline"
    _avg_col = f"6M Avg ({_metric_unit})" if _metric_unit else "6M Avg"
    _delta_col = f"Delta ({_metric_unit})" if _metric_unit else "Delta"
    _roi_col = f"ROI ({_metric_unit}/{_grant_unit})" if _metric_unit else f"ROI (/{_grant_unit})"

    # Create formatters for each unit type
    def _fmt_funding(x):
        return format_amount_by_unit(x, _grant_unit)

    if _is_revenue:
        def _metric_fmt(x):
            return format_amount_by_unit(x, _revenue_unit)
        if _revenue_unit == "ETH":
            _delta_fmt = fmt_delta_eth
        elif _revenue_unit == "USD":
            _delta_fmt = fmt_delta_usd
        else:
            _delta_fmt = _metric_fmt
    elif winners_metric_selector.value == "TVL":
        _metric_fmt = fmt_usd
        _delta_fmt = fmt_delta_usd
    else:
        _metric_fmt = fmt_int
        _delta_fmt = fmt_delta_int

    # ROI formatter with proper sign format: -$X or +$X
    def _roi_fmt(x):
        if x is None or pd.isna(x):
            return "—"
        if _metric_unit == "ETH":
            return f"+{x:.4f}" if x >= 0 else f"-{abs(x):.4f}"
        elif _metric_unit == "OP":
            return f"+{x:.2f} OP" if x >= 0 else f"-{abs(x):.2f} OP"
        elif _metric_unit == "USD" or _metric_unit == "$":
            return f"+${x:.2f}" if x >= 0 else f"-${abs(x):.2f}"
        return f"+{x:.2f}" if x >= 0 else f"-{abs(x):.2f}"

    # Truncate long project names for display
    def _truncate_name(name):
        return name[:37] + '...' if len(str(name)) > 40 else name

    # Prepare display dataframe with new columns
    _perf_df_display = _perf_df[['Project', 'Total Funding', 'Grants', 'Baseline', '6M Avg', 'Delta', 'ROI']].copy()
    _perf_df_display.columns = ['Project', _funding_col, 'Grants', _baseline_col, _avg_col, _delta_col, _roi_col]

    # Top 10 Winners (highest positive ROI = highest growth rate)
    _winners = _perf_df_display.head(10).copy().reset_index(drop=True)
    _winners['Project'] = _winners['Project'].apply(_truncate_name)

    # Bottom 10 Losers - include projects with negative ROI (decline)
    _losers_pool = _perf_df_display[_perf_df_display[_delta_col] != 0]  # Has some metric data
    _losers = _losers_pool.tail(10).copy().reset_index(drop=True)
    _losers['Project'] = _losers['Project'].apply(_truncate_name)

    # Create scatter plot: X = Funding, Y = Delta (rate of change), Size = |ROI|, Color = sign(ROI)
    _chart_df = _perf_df.copy()

    # Assign colors based on ROI sign: green for positive, red for negative
    _colors = ['#00D395' if x >= 0 else '#FF0420' for x in _chart_df['ROI']]

    # Size based on absolute ROI (normalize to reasonable range)
    _abs_roi = _chart_df['ROI'].abs()
    _max_roi = _abs_roi.max() if _abs_roi.max() > 0 else 1
    _sizes = 10 + 40 * (_abs_roi / _max_roi)  # Size between 10 and 50

    _fig = go.Figure()
    _fig.add_trace(go.Scatter(
        x=_chart_df['Total Funding'],
        y=_chart_df['Delta'],  # Now shows rate of change (avg - baseline)
        mode='markers',
        marker=dict(
            size=_sizes,
            color=_colors,
            line=dict(width=1, color='white'),
            opacity=0.7
        ),
        text=_chart_df['Project'],
        hovertemplate='<b>%{text}</b><br>Funding: %{x:,.0f}<br>Δ (avg-baseline): %{y:,.0f}<br>ROI: %{customdata:.2f}<extra></extra>',
        customdata=_chart_df['ROI']
    ))

    # Apply layout
    _layout = PLOTLY_LAYOUT.copy()
    _layout['height'] = 500
    _layout['margin'] = dict(t=10, l=80, r=30, b=60)

    # X-axis: Funding with optional log scale
    _xaxis_type = 'log' if log_scale_checkbox.value else 'linear'
    _tickformat_x = '$,.0s' if _grant_unit == "USD" else ',.0s'
    _layout['xaxis'] = {
        **PLOTLY_LAYOUT['xaxis'],
        'title': f'Total Funding ({_grant_unit})',
        'tickformat': _tickformat_x,
        'type': _xaxis_type,
        'showgrid': True,
        'gridcolor': '#EEE'
    }

    # Y-axis: Delta (rate of change) with symlog scale for negative values
    # Use symlog (symmetric log) to handle both positive and negative values
    if log_scale_checkbox.value:
        # For symlog, we transform data and use linear scale with custom ticks
        # Plotly doesn't have native symlog, so we'll use linear for now when values can be negative
        _has_negative = (_chart_df['Delta'] < 0).any()
        _yaxis_type = 'linear' if _has_negative else 'log'
    else:
        _yaxis_type = 'linear'

    if _is_revenue:
        if _revenue_unit == "USD":
            _layout['yaxis'] = {**PLOTLY_LAYOUT['yaxis'], 'title': f'Δ Revenue ({_revenue_unit}/mo)', 'tickformat': '$,.0s', 'type': _yaxis_type}
        else:
            _layout['yaxis'] = {**PLOTLY_LAYOUT['yaxis'], 'title': f'Δ Revenue ({_revenue_unit}/mo)', 'tickformat': ',.0s', 'type': _yaxis_type}
    elif winners_metric_selector.value == "TVL":
        _layout['yaxis'] = {**PLOTLY_LAYOUT['yaxis'], 'title': 'Δ TVL ($/mo)', 'tickformat': '$,.0s', 'type': _yaxis_type}
    else:
        _layout['yaxis'] = {**PLOTLY_LAYOUT['yaxis'], 'title': f'Δ {winners_metric_selector.value} (/mo)', 'tickformat': ',.0s', 'type': _yaxis_type}

    _fig.update_layout(**_layout)

    # Format minimum OP for display
    if _min_op >= 1_000_000:
        _min_op_str = f"{_min_op/1e6:.1f}M"
    elif _min_op >= 1_000:
        _min_op_str = f"{_min_op/1e3:.0f}K"
    else:
        _min_op_str = f"{_min_op:,.0f}"

    # Format mapping for tables
    _table_fmt = {
        _funding_col: _fmt_funding,
        'Grants': fmt_int,
        _baseline_col: _metric_fmt,
        _avg_col: _metric_fmt,
        _delta_col: _delta_fmt,
        _roi_col: _roi_fmt,
    }

    # Create top performer callout
    if not _winners.empty:
        _top = _winners.iloc[0]
        _top_delta_fmt = _delta_fmt(_top[_delta_col])
        _top_roi_fmt = _roi_fmt(_top[_roi_col])
        _top_funding_fmt = _fmt_funding(_top[_funding_col])
        _top_callout = mo.callout(
            mo.md(f"**Top Performer**: {_top['Project']} gained {_top_delta_fmt}/mo in {winners_metric_selector.value} vs baseline from {_top_funding_fmt} ({_top_roi_fmt} ROI)"),
            kind="success"
        )
    else:
        _top_callout = mo.md("")

    mo.vstack([
        mo.md(f"*Showing {_filtered_projects} of {_total_projects} projects with ≥{_min_op_str} OP*"),
        _top_callout,
        mo.hstack([
            mo.vstack([
                mo.md("### Top 10 Performers"),
                mo.ui.table(_winners, label="Winners", show_column_summaries=False, show_data_types=False, format_mapping=_table_fmt)
            ]),
            mo.vstack([
                mo.md("### Bottom 10 Performers"),
                mo.ui.table(_losers, label="Losers", show_column_summaries=False, show_data_types=False, format_mapping=_table_fmt)
            ])
        ]),
        mo.md(f"### Funding vs {winners_metric_selector.value}"),
        mo.md("*Bubble size = ROI magnitude. Green = positive ROI, Red = negative ROI.*"),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    """Section: Project Deep Dive"""
    mo.md(r"""
    ## Part 4: Project Deep Dive
    Analyze all grants received by a single project and performance across all metrics.
    """)
    return


@app.cell(hide_code=True)
def _(df_grants, df_metrics, mo):
    """Project selector - filtered to projects with metrics and sorted by funding"""
    # Get all unique projects from grants
    _all_projects = df_grants['application_name'].dropna().unique().tolist()
    _total_funded = len(_all_projects)

    # Get project IDs that have metric data
    _project_ids_with_metrics = df_metrics['project_id'].dropna().unique()

    # Get project names that have metrics
    _projects_with_metrics = df_grants[
        df_grants['oso_project_id'].isin(_project_ids_with_metrics)
    ]['application_name'].dropna().unique()
    _with_metrics = len(_projects_with_metrics)

    # Aggregate funding per project and sort by total funding (descending)
    _project_funding = df_grants.groupby('application_name')['amount'].sum().reset_index()
    _project_funding = _project_funding.sort_values('amount', ascending=False)

    # Filter to only projects with metrics
    _project_funding_filtered = _project_funding[
        _project_funding['application_name'].isin(_projects_with_metrics)
    ]

    # Create sorted list of project names
    _projects_sorted = _project_funding_filtered['application_name'].tolist()

    # Coverage stats
    _coverage_pct = (_with_metrics / _total_funded * 100) if _total_funded > 0 else 0

    project_selector = mo.ui.dropdown(
        options=_projects_sorted,
        value=_projects_sorted[0] if _projects_sorted else None,
        label="Select Project"
    )

    # Metric selector for the time series chart - includes both TVL and TVL Inflows
    project_metric_selector = mo.ui.dropdown(
        options=["TVL", "TVL Inflows", "Superchain Revenue", "Transactions", "User Ops"],
        value="TVL",
        label="Metric"
    )

    mo.vstack([
        mo.md(f"*Showing {_with_metrics} of {_total_funded} projects with available metrics ({_coverage_pct:.0f}%)*"),
        mo.hstack([project_selector, project_metric_selector])
    ])
    return (project_selector, project_metric_selector)


@app.cell(hide_code=True)
def _(
    METRIC_GROUPS,
    PLOTLY_LAYOUT,
    calculate_baseline_value,
    calculate_current_value,
    calculate_period_average,
    calculate_roi,
    convert_grant_amount,
    convert_revenue_amount,
    currency_selector,
    df_grants,
    df_metrics,
    df_prices,
    fixed_rate_month,
    format_amount_by_unit,
    get_grant_unit,
    get_revenue_unit,
    fmt_date,
    go,
    mo,
    pd,
    project_metric_selector,
    project_selector,
    rate_mode_selector,
):
    """Project deep dive details with mo.stat cards and hvh chart"""
    if project_selector.value:
        # Get current currency settings
        _currency_mode = currency_selector.value
        _rate_mode = rate_mode_selector.value
        _fixed_date = pd.to_datetime(fixed_rate_month.value + "-01") if fixed_rate_month.value else None

        # Get units for display
        _grant_unit = get_grant_unit(_currency_mode)
        _revenue_unit = get_revenue_unit(_currency_mode)

        # Determine if this is a revenue metric
        _is_revenue = project_metric_selector.value == "Superchain Revenue"

        # Get all grants for this project
        _project_grants = df_grants[df_grants['application_name'] == project_selector.value]
        _project_id = _project_grants['oso_project_id'].iloc[0] if len(_project_grants) > 0 else None

        # Convert grant amounts based on currency setting
        _grants_with_conversion = []
        for _, _grant in _project_grants.iterrows():
            _converted_amt = convert_grant_amount(
                _grant['amount'], _grant['funding_date'], _currency_mode, _rate_mode, _fixed_date, df_prices
            )
            _grants_with_conversion.append({
                'Funding Date': _grant['funding_date'],
                'Season/Mission': _grant['grants_season_or_mission'],
                'Amount': _converted_amt
            })

        _grants_table = pd.DataFrame(_grants_with_conversion)
        _grants_table = _grants_table.sort_values('Funding Date', ascending=False).reset_index(drop=True)
        _amt_col = f"Amount ({_grant_unit})"
        _grants_table.columns = ['Funding Date', 'Season/Mission', _amt_col]

        _total_funding = _project_grants['amount'].sum()
        _first_funding_date = _project_grants['funding_date'].min()

        # Convert total funding based on currency setting
        _converted_total = convert_grant_amount(
            _total_funding, _first_funding_date, _currency_mode, _rate_mode, _fixed_date, df_prices
        )

        # Get metrics time series for this project using project_id
        if pd.notna(_project_id):
            _project_metrics = df_metrics[df_metrics['project_id'] == _project_id].copy()
            _project_metrics = _project_metrics.sort_values('sample_date')

            # Get selected metric names for stats calculation
            # Handle TVL Inflows as a separate option
            if project_metric_selector.value == "TVL Inflows":
                _selected_metric_names = ['TVL Inflows']
            else:
                _selected_metric_names = METRIC_GROUPS.get(project_metric_selector.value, ['TVL'])
            _metric_df = _project_metrics[_project_metrics['metric_name'].isin(_selected_metric_names)]

            # Calculate baseline, current, delta, and ROI based on metric type
            if project_metric_selector.value == "TVL":
                # TVL uses point-in-time values (baseline vs current snapshot)
                # For monthly data, look at funding month (not 7-day window)
                _tvl_snapshot_df = _project_metrics[_project_metrics['metric_name'] == 'TVL']
                _funding_month_start = _first_funding_date.replace(day=1)
                _funding_month_end = (_funding_month_start + pd.DateOffset(months=1)) - pd.Timedelta(days=1)
                _baseline_metrics = _tvl_snapshot_df[
                    (_tvl_snapshot_df['sample_date'] >= _funding_month_start) &
                    (_tvl_snapshot_df['sample_date'] <= _funding_month_end)
                ]
                _baseline_val = _baseline_metrics['amount'].sum() if not _baseline_metrics.empty else 0
                _current_val = calculate_current_value(_tvl_snapshot_df)
                _metric_delta = _current_val - _baseline_val
                _metric_label = "TVL"
                _metric_unit = "$"
            elif project_metric_selector.value == "TVL Inflows":
                # TVL Inflows are changes month-to-month (can be positive or negative)
                # Baseline = monthly average around funding date
                _funding_month_start = _first_funding_date.replace(day=1)
                _funding_month_end = (_funding_month_start + pd.DateOffset(months=1)) - pd.Timedelta(days=1)
                _baseline_metrics = _metric_df[
                    (_metric_df['sample_date'] >= _funding_month_start) &
                    (_metric_df['sample_date'] <= _funding_month_end)
                ]
                _baseline_val = _baseline_metrics['amount'].sum()
                # Current = 6-month average after funding using rate-of-change methodology
                _6m_avg, _6m_months = calculate_period_average(_metric_df, _first_funding_date, 6)
                _current_val = _6m_avg
                _metric_delta = _current_val - _baseline_val
                _metric_label = "TVL Inflows"
                _metric_unit = "$"
            else:
                # For all other metrics (Revenue, Transactions, User Ops):
                # Use rate-of-change methodology: baseline month vs 6-month average
                _funding_month_start = _first_funding_date.replace(day=1)
                _funding_month_end = (_funding_month_start + pd.DateOffset(months=1)) - pd.Timedelta(days=1)
                _baseline_metrics = _metric_df[
                    (_metric_df['sample_date'] >= _funding_month_start) &
                    (_metric_df['sample_date'] <= _funding_month_end)
                ]
                _baseline_val = _baseline_metrics['amount'].sum()
                # Current = 6-month average after funding
                _6m_avg, _6m_months = calculate_period_average(_metric_df, _first_funding_date, 6)
                _current_val = _6m_avg
                _metric_delta = _current_val - _baseline_val
                _metric_label = project_metric_selector.value
                if project_metric_selector.value == "Superchain Revenue":
                    _metric_unit = _revenue_unit
                else:
                    _metric_unit = ""  # Transactions and User Ops are counts

            # Convert revenue metrics based on currency setting
            if _is_revenue:
                _baseline_val = convert_revenue_amount(
                    _baseline_val, _first_funding_date, _currency_mode, _rate_mode, _fixed_date, df_prices
                )
                _current_val = convert_revenue_amount(
                    _current_val, _first_funding_date, _currency_mode, _rate_mode, _fixed_date, df_prices
                )
                _metric_delta = _current_val - _baseline_val

            # ROI = (avg_monthly - baseline) / funding
            _metric_roi = calculate_roi(_metric_delta, _converted_total) if _converted_total else 0

            # Format values based on metric type and currency
            def _fmt_value(x, unit):
                if x is None or pd.isna(x):
                    return "—"
                if unit == "$":
                    if abs(x) >= 1_000_000:
                        return f"${abs(x)/1e6:.1f}M"
                    elif abs(x) >= 1_000:
                        return f"${abs(x)/1e3:.0f}K"
                    return f"${abs(x):.0f}"
                elif unit == "ETH":
                    if abs(x) >= 1_000_000:
                        return f"{abs(x)/1e6:.1f}M"
                    elif abs(x) >= 1_000:
                        return f"{abs(x)/1e3:.1f}K"
                    return f"{abs(x):.4f}"
                elif unit == "OP":
                    if abs(x) >= 1_000_000:
                        return f"{abs(x)/1e6:.1f}M OP"
                    elif abs(x) >= 1_000:
                        return f"{abs(x)/1e3:.0f}K OP"
                    return f"{abs(x):,.0f} OP"
                elif unit == "USD":
                    if abs(x) >= 1_000_000:
                        return f"${abs(x)/1e6:.1f}M"
                    elif abs(x) >= 1_000:
                        return f"${abs(x)/1e3:.0f}K"
                    return f"${abs(x):.0f}"
                else:  # Counts
                    if abs(x) >= 1_000_000:
                        return f"{abs(x)/1e6:.1f}M"
                    elif abs(x) >= 1_000:
                        return f"{abs(x)/1e3:.0f}K"
                    return f"{abs(x):,.0f}"

            _sign = "+" if _metric_delta >= 0 else "-"
            _roi_sign = "+" if _metric_roi >= 0 else "-"

            # ROI unit depends on metric type and currency mode
            if project_metric_selector.value == "TVL":
                _roi_unit = "$"
            elif project_metric_selector.value == "Superchain Revenue":
                _roi_unit = _metric_unit
            else:
                _roi_unit = ""

            # Create mo.stat cards with dynamic labels
            # Labels reflect the rate-of-change methodology for non-TVL metrics
            _card_baseline = mo.stat(
                label=f"Baseline {_metric_label}",
                value=_fmt_value(_baseline_val, _metric_unit),
                caption="funding month",
                bordered=True
            )

            # For TVL, show current snapshot; for others, show 6-month average
            if project_metric_selector.value == "TVL":
                _current_label = f"Current {_metric_label}"
                _current_caption = "latest available"
            else:
                _current_label = f"6M Avg {_metric_label}"
                _current_caption = "post-funding monthly avg"

            _card_current = mo.stat(
                label=_current_label,
                value=_fmt_value(_current_val, _metric_unit),
                caption=_current_caption,
                bordered=True
            )

            _card_delta = mo.stat(
                label=f"{_metric_label} Δ",
                value=f"{_sign}{_fmt_value(abs(_metric_delta), _metric_unit)}",
                caption="avg vs baseline" if project_metric_selector.value != "TVL" else "since first grant",
                bordered=True
            )

            # Format ROI with proper units
            if _roi_unit == "ETH":
                _roi_str = f"{_roi_sign}{abs(_metric_roi):.4f} ETH/{_grant_unit}"
            elif _roi_unit == "OP":
                _roi_str = f"{_roi_sign}{abs(_metric_roi):.2f} OP/{_grant_unit}"
            elif _roi_unit == "$" or _roi_unit == "USD":
                _roi_str = f"{_roi_sign}${abs(_metric_roi):.2f}/{_grant_unit}"
            else:
                _roi_str = f"{_roi_sign}{abs(_metric_roi):.2f}/{_grant_unit}"

            _card_roi = mo.stat(
                label=f"{_metric_label} ROI",
                value=_roi_str,
                caption=f"per {_grant_unit} granted",
                bordered=True
            )

            # Get selected metric names for chart
            # TVL shows point-in-time snapshots, TVL Inflows shows monthly changes
            if project_metric_selector.value == "TVL":
                _chart_metric_names = ['TVL']  # Actual TVL snapshots
            elif project_metric_selector.value == "TVL Inflows":
                _chart_metric_names = ['TVL Inflows']  # Monthly changes
            else:
                _chart_metric_names = METRIC_GROUPS.get(project_metric_selector.value, [])
            _chart_metrics = _project_metrics[_project_metrics['metric_name'].isin(_chart_metric_names)]

            # Aggregate by date if multiple metrics in group
            _chart_data = _chart_metrics.groupby('sample_date')['amount'].sum().reset_index()
            _chart_data = _chart_data.sort_values('sample_date')

            # Create time series chart with hvh (step) line style
            _fig = go.Figure()
            _fig.add_trace(go.Scatter(
                x=_chart_data['sample_date'],
                y=_chart_data['amount'],
                name=project_metric_selector.value,
                mode='lines',
                line=dict(color='#FF0420', shape='hvh'),  # hvh = horizontal-vertical-horizontal
                fill='tozeroy',
                fillcolor='rgba(255, 4, 32, 0.1)'
            ))

            # Add vertical lines for grant funding dates with currency-aware amounts
            for _, _grant in _project_grants.iterrows():
                _grant_date = _grant['funding_date']
                _grant_amt = _grant['amount']

                # Convert and format grant amount
                _converted_grant = convert_grant_amount(
                    _grant_amt, _grant_date, _currency_mode, _rate_mode, _fixed_date, df_prices
                )
                _amt_str = format_amount_by_unit(_converted_grant, _grant_unit)

                _fig.add_shape(
                    type="line",
                    x0=_grant_date, x1=_grant_date,
                    y0=0, y1=1,
                    yref="paper",
                    line=dict(color="#666", width=2, dash="dash")
                )
                _fig.add_annotation(
                    x=_grant_date,
                    y=1.02,
                    yref="paper",
                    text=f"Grant: {_amt_str}",
                    showarrow=False,
                    font=dict(size=10),
                    bgcolor="white",
                    bordercolor="#666",
                    borderwidth=1
                )

            # Set y-axis format and chart title based on metric type and currency
            if project_metric_selector.value == "Superchain Revenue":
                _y_fmt = '$,.0s' if _revenue_unit == "USD" else ',.0s'
                _y_title = f'Revenue ({_revenue_unit})'
                _chart_title = 'Superchain Revenue Over Time'
            elif project_metric_selector.value == "TVL":
                _y_fmt = '$,.0s'
                _y_title = 'TVL ($)'
                _chart_title = 'TVL Over Time'
            elif project_metric_selector.value == "TVL Inflows":
                _y_fmt = '$,.0s'
                _y_title = 'TVL Inflows ($)'
                _chart_title = 'TVL Inflows Over Time'
            elif project_metric_selector.value == "Transactions":
                _y_fmt = ',.0s'
                _y_title = 'Transactions'
                _chart_title = 'Transactions Over Time'
            else:  # User Ops
                _y_fmt = ',.0s'
                _y_title = 'User Ops'
                _chart_title = 'User Ops Over Time'

            _layout = PLOTLY_LAYOUT.copy()
            _layout['yaxis'] = {**PLOTLY_LAYOUT['yaxis'], 'title': _y_title, 'tickformat': _y_fmt}
            _layout['xaxis'] = {**PLOTLY_LAYOUT['xaxis'], 'title': ''}
            _layout['height'] = 400
            _layout['margin'] = dict(t=50, l=60, r=30, b=40)
            _layout['showlegend'] = False
            _fig.update_layout(_layout)

            # Format total funding for display
            _total_funding_str = format_amount_by_unit(_converted_total, _grant_unit)

            # Create formatter for grants table
            def _fmt_grant(x):
                return format_amount_by_unit(x, _grant_unit)

            _output = mo.vstack([
                mo.md(f"### {project_selector.value}"),
                mo.md(f"**Total Funding**: {_total_funding_str} across {len(_project_grants)} grant(s)"),
                mo.md(f"#### {_metric_label} Performance"),
                mo.hstack([_card_baseline, _card_current, _card_delta, _card_roi], widths="equal"),
                mo.md("---"),
                mo.md("#### Grants Received"),
                mo.ui.table(
                    _grants_table,
                    show_column_summaries=False,
                    show_data_types=False,
                    format_mapping={
                        'Funding Date': fmt_date,
                        _amt_col: _fmt_grant,
                    }
                ),
                mo.md(f"#### {_chart_title}"),
                mo.ui.plotly(_fig, config={'displayModeBar': False})
            ])
        else:
            _output = mo.md(f"No metrics data available for {project_selector.value}")
    else:
        _output = mo.md("Please select a project to view deep dive.")

    _output
    return


@app.cell(hide_code=True)
def _(mo):
    """Section: Chain Analysis"""
    mo.md(r"""
    ## Part 5: Chain-Level Analysis
    Analyze projects on specific chains by funding and performance.
    """)
    return


@app.cell(hide_code=True)
def _(df_metrics, mo):
    """Chain selector with proper filtering"""
    # Get unique chains from metric_source, excluding 'Other'
    _all_chains = df_metrics['metric_source'].dropna().unique().tolist()

    # Define priority chains (Superchain networks)
    _priority_chains = ['OP Mainnet', 'Base', 'Mode', 'Ink', 'Lisk', 'Soneium', 'Swell', 'Unichain', 'Worldchain']

    # Filter to only include known chains and sort by priority
    _chains = [c for c in _priority_chains if c in _all_chains]
    # Add other chains (like GitHub) that aren't in priority list
    _other_chains = [c for c in sorted(_all_chains) if c not in _priority_chains and c != 'Other']
    _chains.extend(_other_chains)

    chain_selector = mo.ui.dropdown(
        options=_chains,
        value=_chains[0] if _chains else None,
        label="Select Chain"
    )

    # Also add a metric selector for chain analysis
    chain_metric_selector = mo.ui.dropdown(
        options=["TVL", "Superchain Revenue", "Transactions", "User Ops"],
        value="TVL",
        label="Metric"
    )

    mo.hstack([chain_selector, chain_metric_selector])
    return chain_metric_selector, chain_selector


@app.cell(hide_code=True)
def _(
    CHAIN_COLORS,
    PLOTLY_LAYOUT,
    PROJECT_COLORS,
    chain_metric_selector,
    chain_selector,
    convert_grant_amount,
    convert_revenue_amount,
    currency_selector,
    df_grants,
    df_metrics,
    df_prices,
    fixed_rate_month,
    format_amount_by_unit,
    get_grant_unit,
    get_revenue_unit,
    fmt_int,
    fmt_usd,
    go,
    mo,
    pd,
    rate_mode_selector,
):
    """Chain analysis with stacked area chart (Top 5 + Other)"""
    if chain_selector.value:
        # Get current currency settings
        _currency_mode = currency_selector.value
        _rate_mode = rate_mode_selector.value
        _fixed_date = pd.to_datetime(fixed_rate_month.value + "-01") if fixed_rate_month.value else None

        # Get units for display
        _grant_unit = get_grant_unit(_currency_mode)
        _revenue_unit = get_revenue_unit(_currency_mode)

        # Determine if this is a revenue metric
        _is_revenue = chain_metric_selector.value == "Superchain Revenue"

        # Filter metrics for selected chain
        _chain_metrics = df_metrics[df_metrics['metric_source'] == chain_selector.value]

        # Get metric names for selected metric
        _metric_map = {
            'TVL': ['TVL'],
            'Superchain Revenue': ['Revenue (Top Level)', 'Revenue (Trace Level)'],
            'Transactions': ['Transactions (Top Level)'],
            'User Ops': ['User Ops']
        }
        _selected_metric_names = _metric_map.get(chain_metric_selector.value, ['TVL'])

        # Filter to selected metric
        _chain_metrics_filtered = _chain_metrics[_chain_metrics['metric_name'].isin(_selected_metric_names)]

        # Get unique project_ids on this chain
        _project_ids_on_chain = _chain_metrics_filtered['project_id'].dropna().unique()

        # Get funding for these projects
        _chain_grants = df_grants[df_grants['oso_project_id'].isin(_project_ids_on_chain)]

        # Use latest date for aggregate conversions in Historical mode
        _latest_date = df_metrics['sample_date'].max() if not df_metrics.empty else None

        # Aggregate by project for table
        # For TVL, use current (latest) value instead of sum; for other metrics, use sum
        _project_summary = []
        _project_totals = {}
        _is_tvl = chain_metric_selector.value == "TVL"

        for _project_id in _project_ids_on_chain:
            _project_grants = _chain_grants[_chain_grants['oso_project_id'] == _project_id]
            _funding = _project_grants['amount'].sum()
            _earliest_date = _project_grants['funding_date'].min() if not _project_grants.empty else _latest_date
            _project_metrics_on_chain = _chain_metrics_filtered[_chain_metrics_filtered['project_id'] == _project_id]
            _project_name = _project_metrics_on_chain['project_name'].iloc[0] if len(_project_metrics_on_chain) > 0 else str(_project_id)

            # Convert funding based on currency setting
            _converted_funding = convert_grant_amount(
                _funding, _earliest_date, _currency_mode, _rate_mode, _fixed_date, df_prices
            )

            if _is_tvl and not _project_metrics_on_chain.empty:
                # For TVL, get the latest value (current TVL)
                _proj_latest_date = _project_metrics_on_chain['sample_date'].max()
                _current_value = _project_metrics_on_chain[_project_metrics_on_chain['sample_date'] == _proj_latest_date]['amount'].sum()
            else:
                # For other metrics, sum all values
                _current_value = _project_metrics_on_chain['amount'].sum()

            # Convert revenue metrics based on currency setting
            if _is_revenue:
                _current_value = convert_revenue_amount(
                    _current_value, _latest_date, _currency_mode, _rate_mode, _fixed_date, df_prices
                )

            _project_summary.append({
                'Project': _project_name,
                'Total Funding': _converted_funding,
                'Total Metric Value': _current_value,
            })
            _project_totals[_project_name] = _current_value

        _summary_df = pd.DataFrame(_project_summary)
        _summary_df = _summary_df.sort_values('Total Metric Value', ascending=False)

        # Get top 5 projects for stacked area chart, rest go to "Other"
        _top_projects = sorted(_project_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        _top_project_names = [p[0] for p in _top_projects]
        _other_project_names = [p for p in _project_totals.keys() if p not in _top_project_names]

        # Prepare time series data for stacked area chart
        _ts_data = _chain_metrics_filtered.copy()
        _ts_data = _ts_data.groupby(['sample_date', 'project_name'])['amount'].sum().reset_index()

        # Create stacked area chart with hvh line shape
        _fig = go.Figure()

        # Add Top 5 projects using PROJECT_COLORS palette
        for _idx, _project_name in enumerate(_top_project_names):
            _project_ts = _ts_data[_ts_data['project_name'] == _project_name].sort_values('sample_date')
            if not _project_ts.empty:
                _fig.add_trace(go.Scatter(
                    x=_project_ts['sample_date'],
                    y=_project_ts['amount'],
                    name=_project_name[:20] + '...' if len(_project_name) > 20 else _project_name,
                    mode='lines',
                    stackgroup='one',
                    fillcolor=PROJECT_COLORS[_idx % len(PROJECT_COLORS)],
                    line=dict(width=0.5, color='#333', shape='hvh')
                ))

        # Add "Other" category for remaining projects
        if _other_project_names:
            _other_ts = _ts_data[_ts_data['project_name'].isin(_other_project_names)]
            _other_ts = _other_ts.groupby('sample_date')['amount'].sum().reset_index()
            _other_ts = _other_ts.sort_values('sample_date')
            if not _other_ts.empty:
                _fig.add_trace(go.Scatter(
                    x=_other_ts['sample_date'],
                    y=_other_ts['amount'],
                    name='Other',
                    mode='lines',
                    stackgroup='one',
                    fillcolor='rgba(230, 230, 230, 0.5)',  # Very light gray for "Other"
                    line=dict(width=0.5, color='#999', shape='hvh')
                ))

        # Chain name for section title (using black text for consistency)

        # Apply layout
        _layout = PLOTLY_LAYOUT.copy()
        _layout['height'] = 400
        _layout['margin'] = dict(t=10, l=60, r=120, b=40)
        _layout['legend'] = dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            font=dict(size=10)
        )

        # Format axis based on metric type and currency
        if chain_metric_selector.value == "TVL":
            _layout['yaxis'] = {**PLOTLY_LAYOUT['yaxis'], 'title': 'TVL ($)', 'tickformat': '$,.0s'}
        elif chain_metric_selector.value == "Superchain Revenue":
            _y_fmt = '$,.0s' if _revenue_unit == "USD" else ',.0s'
            _layout['yaxis'] = {**PLOTLY_LAYOUT['yaxis'], 'title': f'Revenue ({_revenue_unit})', 'tickformat': _y_fmt}
        elif chain_metric_selector.value == "Transactions":
            _layout['yaxis'] = {**PLOTLY_LAYOUT['yaxis'], 'title': 'Transactions', 'tickformat': ',.0s'}
        else:  # User Ops
            _layout['yaxis'] = {**PLOTLY_LAYOUT['yaxis'], 'title': 'User Ops', 'tickformat': ',.0s'}

        _layout['xaxis'] = {**PLOTLY_LAYOUT['xaxis'], 'title': ''}
        _fig.update_layout(**_layout)

        # Build column headers with units
        _funding_col = f"Total Funding ({_grant_unit})"

        # Rename columns for display
        _display_df = _summary_df.copy()
        _display_df.columns = ['Project', _funding_col, 'Total Metric Value']

        # Truncate long project names for display
        _display_df['Project'] = _display_df['Project'].apply(
            lambda x: x[:37] + '...' if len(str(x)) > 40 else x
        )

        # Create formatters
        def _fmt_funding(x):
            return format_amount_by_unit(x, _grant_unit)

        # Choose metric formatter based on metric type
        if chain_metric_selector.value == "TVL":
            _metric_fmt = fmt_usd
        elif chain_metric_selector.value == "Superchain Revenue":
            def _metric_fmt(x):
                return format_amount_by_unit(x, _revenue_unit)
        else:  # Transactions or User Ops
            _metric_fmt = fmt_int

        # Chain-level totals
        _total_chain_funding = _chain_grants['amount'].sum()

        # Convert total chain funding based on currency setting
        _converted_chain_funding = convert_grant_amount(
            _total_chain_funding, _latest_date, _currency_mode, _rate_mode, _fixed_date, df_prices
        )

        # For TVL, sum the current values (already calculated per project above)
        # For other metrics, sum all values
        if _is_tvl:
            _total_chain_metric = sum(_project_totals.values())  # Sum of current TVL per project
            _metric_caption = "current"
        else:
            _total_chain_metric = sum(_project_totals.values())  # Already converted if revenue
            _metric_caption = "all time"

        # Format chain metric
        if chain_metric_selector.value == "TVL":
            _chain_metric_str = f"${_total_chain_metric/1e6:.1f}M" if _total_chain_metric >= 1e6 else f"${_total_chain_metric/1e3:.0f}K"
        elif chain_metric_selector.value == "Superchain Revenue":
            _chain_metric_str = format_amount_by_unit(_total_chain_metric, _revenue_unit)
        else:  # Transactions or User Ops
            _chain_metric_str = f"{_total_chain_metric/1e6:.1f}M" if _total_chain_metric >= 1e6 else f"{_total_chain_metric/1e3:.0f}K"

        # Format funding for stat card
        _chain_funding_str = format_amount_by_unit(_converted_chain_funding, _grant_unit)

        # Use mo.stat for chain summary cards with dynamic chain name
        _chain_name = chain_selector.value
        _card_funding = mo.stat(
            label=f"Total Grants to Projects on {_chain_name}",
            value=_chain_funding_str,
            caption=f"{len(_project_ids_on_chain)} recipient projects",
            bordered=True
        )
        _card_metric = mo.stat(
            label=f"Aggregate {chain_metric_selector.value} of Recipients",
            value=_chain_metric_str,
            caption=_metric_caption,
            bordered=True
        )

        # Reset index for table display (removes index column)
        _display_df = _display_df.reset_index(drop=True)

        _output = mo.vstack([
            mo.md(f"### {_chain_name}"),
            mo.hstack([_card_funding, _card_metric], widths="equal"),
            mo.md(f"#### {chain_metric_selector.value} Over Time (Top 5 + Other)"),
            mo.ui.plotly(_fig, config={'displayModeBar': False}),
            mo.md(f"#### Projects on {_chain_name}"),
            mo.ui.table(
                _display_df,
                label=f"Projects on {_chain_name}",
                show_column_summaries=False,
                show_data_types=False,
                format_mapping={
                    _funding_col: _fmt_funding,
                    'Total Metric Value': _metric_fmt,
                }
            )
        ])
    else:
        _output = mo.md("Please select a chain to view analysis.")

    _output
    return


@app.cell(hide_code=True)
def _(mo):
    """Section: Methodology"""
    mo.md(r"""
    ## Methodology

    This section documents the data sources, calculation methods, and assumptions used in this dashboard.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    """Methodology details"""
    mo.accordion({
        "📊 Data Sources": mo.md("""
    ### Data Sources

    This dashboard uses the following OSO Universal Data Models (UDMs):

    | Source | Description | Refresh |
    |--------|-------------|---------|
    | `optimism.grants.grants_consolidated` | Grant funding records from Retro Funding and Grants Council | Weekly |
    | `optimism.grants.monthly_metrics_by_project` | Project-level metrics aggregated monthly | Daily |
    | `optimism.grants.metrics_catalog` | Metric definitions and categories | Static |
    | `optimism.grants.projects_catalog` | Project metadata and ID mappings | Weekly |

    **Data Freshness**: Metrics data is updated daily from on-chain sources. Grant data is updated weekly from Optimism governance.
        """),

        "📐 Baseline Calculation": mo.md("""
    ### Baseline Calculation Methodology

    We use the **funding month value** as the baseline:

    ```
    baseline = metric_value_at_funding_month
    ```

    For projects with multiple grants, we use the **earliest funding date** as the baseline reference.

    **Chain Aggregation**: For multi-chain projects, we sum across all chains before calculating the baseline.
        """),

        "📈 ROI Calculation": mo.md("""
    ### ROI Calculation Formula (Rate-of-Change Method)

    ROI measures the **average monthly change** in metric per OP token spent:

    ```
    ROI = (Average Monthly Value - Baseline) / OP Amount
    ```

    **Components**:
    - **Baseline**: Metric value at funding date
    - **Average Monthly Value**: Average of monthly values over the analysis period (6M, 12M, or 18M)
    - **OP Amount**: Total OP tokens received in grant

    **Why Rate-of-Change?**
    This methodology shows **sustainable growth** rather than one-time spikes. A project must maintain elevated metric levels across months to achieve a high ROI.

    **Interpretation**:
    - **Positive ROI**: Project's average monthly value exceeds baseline
    - **Negative ROI**: Project's average monthly value is below baseline
    - **Note**: ROI does not imply causation; market conditions affect all projects

    **Example**: If a project received 100,000 OP, had baseline TVL of $1M, and averaged $6M TVL over 6 months, Delta = $5M and ROI = $50/OP
        """),

        "⏱️ Time Windows": mo.md("""
    ### Time Period Analysis

    The dashboard supports analyzing grant performance over different time windows:

    | Period | Use Case |
    |--------|----------|
    | **6 months** | Short-term impact, useful for recent grants |
    | **12 months** | Standard analysis window |
    | **18 months** | Long-term sustainability |
    | **All time** | From funding date to present |

    **Calculation**: `end_date = funding_date + N months`

    For projects with multiple grants, we use the **first funding date** as the baseline reference point.
        """),

        "📋 Primary Metrics": mo.md("""
    ### Primary Metrics

    | Metric | Category | Unit | Description |
    |--------|----------|------|-------------|
    | **TVL** | TVL | USD | Total Value Locked across all chains |
    | **Superchain TVL Share** | TVL | % | Project's share of total Superchain TVL |
    | **Revenue (Top Level)** | Revenue | ETH | Protocol revenue from top-level transactions |
    | **Revenue (Trace Level)** | Revenue | ETH | Protocol revenue from internal transactions |
    | **Transactions (Top Level)** | Activity | Count | Top-level transaction count |
    | **User Ops** | Activity | Count | ERC-4337 user operations |
    | **Active Developers** | Developer | Count | Developers with commits in period |
    | **Commits** | Developer | Count | Git commits to project repositories |

    **Chain Sources**: Metrics are available per-chain (OP Mainnet, Base, Mode, etc.) and aggregated.
        """),

        "⚠️ Limitations": mo.md("""
    ### Limitations and Assumptions

    **Limitations**:
    1. **Correlation ≠ Causation**: Growth after funding may be due to market conditions, not the grant
    2. **Data Coverage**: Some projects may have incomplete metric coverage
    3. **Price Volatility**: USD-denominated TVL affected by token price changes
    4. **Timing**: Projects may deploy capital with different time lags

    **Assumptions**:
    - Grant impact begins at `funding_date`
    - Multi-grant projects: baseline uses first funding date
    - Missing metrics treated as zero
    - 7-day windows provide sufficient smoothing

    **Best Practices**:
    - Compare projects within same season/cohort
    - Consider market conditions during the period
    - Use multiple metrics for holistic assessment
        """)
    })
    return


@app.cell(hide_code=True)
def _(df_projects_catalog, mo, pd, pyoso_db_conn):
    """Load grants data, consolidated by project + season (min date, sum amount)"""
    # Load raw grants and consolidate by project + season in SQL
    # This handles cases like Velodrome with monthly funding events in the same season
    df_grants_raw = mo.sql(
        f"""
        SELECT
            MIN(funding_date) as funding_date,
            application_name,
            oso_project_slug,
            SUM(amount) as amount,
            FIRST(grant_type) as grant_type,
            grants_season_or_mission
        FROM optimism.grants.grants_consolidated
        GROUP BY application_name, oso_project_slug, grants_season_or_mission
        ORDER BY funding_date
        """,
        output=False,
        engine=pyoso_db_conn
    )

    # Convert funding_date to datetime
    df_grants_raw['funding_date'] = pd.to_datetime(df_grants_raw['funding_date'])

    # Create project ID lookup from projects_catalog (deduplicated)
    # Take first oso_project_id per oso_project_slug to avoid duplicates
    _project_lookup = df_projects_catalog.drop_duplicates(
        subset=['oso_project_slug'], keep='first'
    )[['oso_project_slug', 'oso_project_id', 'oso_project_name']].copy()

    # Merge in Python (left join with deduplicated lookup)
    df_grants = df_grants_raw.merge(
        _project_lookup,
        on='oso_project_slug',
        how='left'
    )
    return (df_grants,)


@app.cell(hide_code=True)
def _(mo, pd, pyoso_db_conn):
    """Load monthly metrics data (excluding current month for data completeness)"""
    df_metrics = mo.sql(
        f"""
        SELECT
            sample_date,
            project_id,
            project_name,
            metric_source,
            metric_category,
            metric_name,
            amount
        FROM optimism.grants.monthly_metrics_by_project
        WHERE sample_date >= DATE('2022-01-01')
          AND sample_date < DATE_TRUNC('month', CURRENT_DATE)
        ORDER BY sample_date, project_name
        """,
        output=False,
        engine=pyoso_db_conn
    )

    # Convert sample_date to datetime
    df_metrics['sample_date'] = pd.to_datetime(df_metrics['sample_date'])
    return (df_metrics,)


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    """Load metrics catalog and projects catalog"""
    # Load metrics catalog
    df_metrics_catalog = mo.sql(
        f"""
        SELECT *
        FROM optimism.grants.metrics_catalog
        """,
        output=False,
        engine=pyoso_db_conn
    )

    # Load projects catalog
    df_projects_catalog = mo.sql(
        f"""
        SELECT *
        FROM optimism.grants.projects_catalog
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_projects_catalog,)


@app.cell(hide_code=True)
def _(mo, pd, pyoso_db_conn):
    """Load monthly token prices for currency conversions"""
    df_prices = mo.sql(
        f"""
        SELECT
            DATE_TRUNC('MONTH', date) AS date,
            token,
            AVG(price) AS price
        FROM optimism.prices.token_to_usd_daily
        GROUP BY 1, 2
        ORDER BY 1, 2
        """,
        output=False,
        engine=pyoso_db_conn
    )

    # Convert date to datetime
    df_prices['date'] = pd.to_datetime(df_prices['date'])
    return (df_prices,)


@app.cell(hide_code=True)
def _():
    """Metric constants from metrics_catalog - use these instead of regex patterns"""
    # Revenue metrics (ETH-denominated)
    REVENUE_METRICS = ['Revenue (Top Level)', 'Revenue (Trace Level)']

    # TVL metrics - use TVL Inflows for cumulative calculations (sum gives total change)
    # Regular 'TVL' is a point-in-time snapshot, summing it gives wrong results
    TVL_INFLOW_METRICS = ['TVL Inflows']

    # Transaction/activity metrics (counts)
    TRANSACTION_METRICS = ['Transactions (Top Level)', 'User Ops']

    # Developer metrics (counts)
    DEVELOPER_METRICS = [
        'Commits', 'Active Developers', 'Active Contributors',
        'PRs Merged', 'PRs Opened', 'Issues Opened', 'Issues Closed'
    ]

    # Mapping for dropdown labels to metric lists
    # Note: TVL uses 'TVL Inflows' which can be summed to get total change over time
    METRIC_GROUPS = {
        'Superchain Revenue': REVENUE_METRICS,
        'TVL': TVL_INFLOW_METRICS,
        'Transactions': TRANSACTION_METRICS,
        'User Ops': ['User Ops'],
        'Developer Activity': DEVELOPER_METRICS
    }
    return METRIC_GROUPS, REVENUE_METRICS


@app.cell(hide_code=True)
def _(pd):
    """Helper functions for metric filtering and calculations"""

    def filter_metrics_by_names(df, metric_names):
        """Filter df_metrics to only include specified metric names."""
        return df[df['metric_name'].isin(metric_names)]

    def get_metric_sum(df, metric_names):
        """Sum metric amounts for specified metric names."""
        filtered = filter_metrics_by_names(df, metric_names)
        return filtered['amount'].sum() if not filtered.empty else 0

    def get_metric_sum_by_project(df, metric_names, project_id):
        """Sum metric amounts for a specific project and metric names."""
        filtered = df[
            (df['metric_name'].isin(metric_names)) &
            (df['project_id'] == project_id)
        ]
        return filtered['amount'].sum() if not filtered.empty else 0

    def calculate_baseline_value(df, baseline_date, window_days=7):
        """
        Calculate 7-day centered average around baseline date.

        Methodology: Sum across chains per day, then average across days.
        This provides a stable baseline that isn't affected by single-day volatility.

        Args:
            df: DataFrame with 'sample_date' and 'amount' columns
            baseline_date: Center date for the window
            window_days: Total window size (default 7 = ±3 days)

        Returns:
            float: Average value over the window, or 0 if no data
        """
        if df.empty or pd.isna(baseline_date):
            return 0

        half_window = window_days // 2
        start_date = baseline_date - pd.Timedelta(days=half_window)
        end_date = baseline_date + pd.Timedelta(days=half_window)

        window_df = df[
            (df['sample_date'] >= start_date) &
            (df['sample_date'] <= end_date)
        ]

        if window_df.empty:
            return 0

        # Sum across chains per day, then average across days
        daily_totals = window_df.groupby('sample_date')['amount'].sum()
        return daily_totals.mean()

    def calculate_current_value(df, end_date=None, window_days=7):
        """
        Calculate 7-day trailing average up to end_date.

        Uses second-to-last date if end_date not specified to avoid
        data quality issues on the most recent date.

        Args:
            df: DataFrame with 'sample_date' and 'amount' columns
            end_date: End date for trailing window (default: second-to-last date)
            window_days: Trailing window size (default 7)

        Returns:
            float: Average value over the trailing window, or 0 if no data
        """
        if df.empty:
            return 0

        if end_date is None:
            # Use second-to-last date to avoid data quality issues
            unique_dates = df['sample_date'].drop_duplicates().sort_values()
            if len(unique_dates) >= 2:
                end_date = unique_dates.iloc[-2]
            elif len(unique_dates) == 1:
                end_date = unique_dates.iloc[0]
            else:
                return 0

        start_date = end_date - pd.Timedelta(days=window_days)

        window_df = df[
            (df['sample_date'] >= start_date) &
            (df['sample_date'] <= end_date)
        ]

        if window_df.empty:
            return 0

        # Sum across chains per day, then average across days
        daily_totals = window_df.groupby('sample_date')['amount'].sum()
        return daily_totals.mean()

    def calculate_metric_delta(df, start_date, end_date=None, window_days=7):
        """
        Calculate change in metric from start_date to end_date.

        Args:
            df: DataFrame with 'sample_date' and 'amount' columns
            start_date: Baseline date (will use centered window)
            end_date: Current date (will use trailing window)
            window_days: Window size for averaging

        Returns:
            float: (current - baseline) value
        """
        baseline = calculate_baseline_value(df, start_date, window_days)
        current = calculate_current_value(df, end_date, window_days)
        return current - baseline

    def calculate_roi(metric_delta, op_amount):
        """
        Calculate ROI as metric delta per OP spent.

        Args:
            metric_delta: Change in metric value
            op_amount: OP tokens spent

        Returns:
            float: Metric change per OP, or 0 if op_amount is 0
        """
        if op_amount is None or op_amount == 0 or pd.isna(op_amount):
            return 0
        return metric_delta / op_amount

    def calculate_period_average(df, start_date, months, use_cumulative=False):
        """
        Calculate average monthly value over a period after start_date.

        For rate-of-change ROI methodology:
        - Get monthly values for each month in the period
        - Return the average (not cumulative sum)

        Args:
            df: DataFrame with 'sample_date' and 'amount' columns
            start_date: Start date (typically funding date)
            months: Number of months in the period (6, 12, or 18)
            use_cumulative: If True, return sum instead of average (for backwards compatibility)

        Returns:
            tuple: (average_value, num_months_with_data)
        """
        if df.empty or pd.isna(start_date):
            return 0, 0

        # Get end date for the period
        end_date = start_date + pd.DateOffset(months=months)

        # Filter to dates after start and before end
        period_df = df[
            (df['sample_date'] > start_date) &
            (df['sample_date'] <= end_date)
        ]

        if period_df.empty:
            return 0, 0

        # Group by month and sum within each month (handles multiple chains)
        period_df = period_df.copy()
        period_df['month'] = period_df['sample_date'].dt.to_period('M')
        monthly_totals = period_df.groupby('month')['amount'].sum()

        num_months = len(monthly_totals)
        if num_months == 0:
            return 0, 0

        if use_cumulative:
            return monthly_totals.sum(), num_months
        else:
            return monthly_totals.mean(), num_months

    def calculate_rate_of_change_roi(df, funding_date, months, funding_amount, baseline_value=None):
        """
        Calculate ROI using rate-of-change methodology.

        Formula: ROI = (avg_monthly_post_funding - baseline) / funding_amount

        Args:
            df: DataFrame with 'sample_date' and 'amount' columns
            funding_date: Date of funding
            months: Analysis period in months (6, 12, 18)
            funding_amount: Amount of funding received
            baseline_value: Pre-calculated baseline (if None, will calculate)

        Returns:
            tuple: (roi, avg_post_funding, baseline, delta)
        """
        if funding_amount is None or funding_amount == 0 or pd.isna(funding_amount):
            return 0, 0, 0, 0

        # Calculate baseline if not provided
        if baseline_value is None:
            baseline_value = calculate_baseline_value(df, funding_date)

        # Calculate average monthly value over the period
        avg_post_funding, num_months = calculate_period_average(df, funding_date, months)

        # Calculate delta (rate of change)
        delta = avg_post_funding - baseline_value

        # Calculate ROI
        roi = delta / funding_amount if funding_amount > 0 else 0

        return roi, avg_post_funding, baseline_value, delta

    return (
        calculate_baseline_value,
        calculate_current_value,
        calculate_period_average,
        calculate_rate_of_change_roi,
        calculate_roi,
        get_metric_sum,
    )


@app.cell(hide_code=True)
def _(pd):
    """Currency conversion helper functions"""

    def get_price(df_prices, token, date):
        """
        Get price for a token at the nearest available month.

        Args:
            df_prices: DataFrame with 'date', 'token', 'price' columns
            token: 'OP' or 'ETH'
            date: Target date (will find nearest month)

        Returns:
            float: Price in USD, or None if not found
        """
        if df_prices is None or df_prices.empty or pd.isna(date):
            return None

        # Filter to the requested token
        token_prices = df_prices[df_prices['token'] == token].copy()
        if token_prices.empty:
            return None

        # Convert date to start of month for comparison
        target_date = pd.to_datetime(date).replace(day=1)

        # Find the nearest month
        token_prices['diff'] = abs(token_prices['date'] - target_date)
        nearest_idx = token_prices['diff'].idxmin()
        return token_prices.loc[nearest_idx, 'price']

    def convert_op_to_usd(amount, date, df_prices):
        """Convert OP amount to USD."""
        if amount is None or pd.isna(amount):
            return amount
        price = get_price(df_prices, 'OP', date)
        if price is None:
            return amount  # Return original if no price available
        return amount * price

    def convert_eth_to_usd(amount, date, df_prices):
        """Convert ETH amount to USD."""
        if amount is None or pd.isna(amount):
            return amount
        price = get_price(df_prices, 'ETH', date)
        if price is None:
            return amount
        return amount * price

    def convert_usd_to_op(amount, date, df_prices):
        """Convert USD amount to OP."""
        if amount is None or pd.isna(amount):
            return amount
        price = get_price(df_prices, 'OP', date)
        if price is None or price == 0:
            return amount
        return amount / price

    def convert_usd_to_eth(amount, date, df_prices):
        """Convert USD amount to ETH."""
        if amount is None or pd.isna(amount):
            return amount
        price = get_price(df_prices, 'ETH', date)
        if price is None or price == 0:
            return amount
        return amount / price

    def convert_op_to_eth(amount, date, df_prices):
        """Convert OP amount to ETH via USD."""
        usd = convert_op_to_usd(amount, date, df_prices)
        return convert_usd_to_eth(usd, date, df_prices)

    def convert_eth_to_op(amount, date, df_prices):
        """Convert ETH amount to OP via USD."""
        usd = convert_eth_to_usd(amount, date, df_prices)
        return convert_usd_to_op(usd, date, df_prices)

    return (
        get_price,
        convert_op_to_usd,
        convert_eth_to_usd,
        convert_usd_to_op,
        convert_usd_to_eth,
        convert_op_to_eth,
        convert_eth_to_op,
    )


@app.cell(hide_code=True)
def _(
    convert_eth_to_op,
    convert_eth_to_usd,
    convert_op_to_eth,
    convert_op_to_usd,
    pd,
):
    """Currency-aware conversion and formatting functions"""

    def convert_grant_amount(amount, date, currency_mode, rate_mode, fixed_date, df_prices):
        """
        Convert grant amount (originally in OP) based on currency mode.

        Args:
            amount: Grant amount in OP
            date: Transaction date (used for Historical mode)
            currency_mode: 'Default', 'OP', 'ETH', or 'USD'
            rate_mode: 'Historical' or 'Fixed'
            fixed_date: Date to use for Fixed mode
            df_prices: Price data DataFrame

        Returns:
            Converted amount
        """
        if amount is None or pd.isna(amount):
            return amount

        # Determine which date to use for rate lookup
        rate_date = fixed_date if rate_mode == "Fixed" else date

        if currency_mode in ["Default", "OP"]:
            return amount  # Keep as OP
        elif currency_mode == "ETH":
            return convert_op_to_eth(amount, rate_date, df_prices)
        elif currency_mode == "USD":
            return convert_op_to_usd(amount, rate_date, df_prices)
        return amount

    def convert_revenue_amount(amount, date, currency_mode, rate_mode, fixed_date, df_prices):
        """
        Convert revenue amount (originally in ETH) based on currency mode.

        Args:
            amount: Revenue amount in ETH
            date: Transaction date (used for Historical mode)
            currency_mode: 'Default', 'OP', 'ETH', or 'USD'
            rate_mode: 'Historical' or 'Fixed'
            fixed_date: Date to use for Fixed mode
            df_prices: Price data DataFrame

        Returns:
            Converted amount
        """
        if amount is None or pd.isna(amount):
            return amount

        # Determine which date to use for rate lookup
        rate_date = fixed_date if rate_mode == "Fixed" else date

        if currency_mode in ["Default", "ETH"]:
            return amount  # Keep as ETH
        elif currency_mode == "OP":
            return convert_eth_to_op(amount, rate_date, df_prices)
        elif currency_mode == "USD":
            return convert_eth_to_usd(amount, rate_date, df_prices)
        return amount

    def get_grant_unit(currency_mode):
        """Get the display unit for grants based on currency mode."""
        if currency_mode in ["Default", "OP"]:
            return "OP"
        elif currency_mode == "ETH":
            return "ETH"
        elif currency_mode == "USD":
            return "USD"
        return "OP"

    def get_revenue_unit(currency_mode):
        """Get the display unit for revenue based on currency mode."""
        if currency_mode in ["Default", "ETH"]:
            return "ETH"
        elif currency_mode == "OP":
            return "OP"
        elif currency_mode == "USD":
            return "USD"
        return "ETH"

    def format_amount_by_unit(amount, unit):
        """Format amount with appropriate symbol based on unit."""
        if amount is None or pd.isna(amount):
            return "—"

        if unit == "OP":
            if abs(amount) >= 1_000_000:
                return f"{amount/1e6:,.1f}M OP"
            elif abs(amount) >= 1_000:
                return f"{amount/1e3:,.0f}K OP"
            return f"{amount:,.0f} OP"
        elif unit == "ETH":
            if abs(amount) >= 1_000_000:
                return f"{amount/1e6:,.1f}M"
            elif abs(amount) >= 1_000:
                return f"{amount/1e3:,.1f}K"
            return f"{amount:,.4f}"
        elif unit == "USD":
            if abs(amount) >= 1_000_000_000:
                return f"${amount/1e9:,.1f}B"
            elif abs(amount) >= 1_000_000:
                return f"${amount/1e6:,.1f}M"
            elif abs(amount) >= 1_000:
                return f"${amount/1e3:,.0f}K"
            return f"${amount:,.0f}"
        return str(amount)

    return (
        convert_grant_amount,
        convert_revenue_amount,
        get_grant_unit,
        get_revenue_unit,
        format_amount_by_unit,
    )


@app.cell(hide_code=True)
def _():
    """Table formatting functions for format_mapping in mo.ui.table"""

    def fmt_op(x):
        """Format OP token amounts (e.g., 1.2M, 450K)"""
        if x is None or x != x:  # Check for NaN
            return "—"
        if abs(x) >= 1_000_000:
            return f"{x/1e6:,.1f}M"
        elif abs(x) >= 1_000:
            return f"{x/1e3:,.0f}K"
        return f"{x:,.0f}"

    def fmt_usd(x):
        """Format USD amounts (e.g., $1.2M, $450K)"""
        if x is None or x != x:
            return "—"
        if abs(x) >= 1_000_000_000:
            return f"${x/1e9:,.1f}B"
        elif abs(x) >= 1_000_000:
            return f"${x/1e6:,.1f}M"
        elif abs(x) >= 1_000:
            return f"${x/1e3:,.0f}K"
        return f"${x:,.0f}"

    def fmt_eth(x):
        """Format ETH amounts (e.g., 1.2M, 0.0012)"""
        if x is None or x != x:
            return "—"
        if abs(x) >= 1_000_000:
            return f"{x/1e6:,.1f}M"
        elif abs(x) >= 1_000:
            return f"{x/1e3:,.1f}K"
        return f"{x:,.4f}"

    def fmt_pct(x):
        """Format as percentage (e.g., 42.5%)"""
        if x is None or x != x:
            return "—"
        return f"{x:.1f}%"

    def fmt_roi_eth(x):
        """Format Revenue ROI in ETH per OP (e.g., +0.0012/OP, -0.0012/OP)"""
        if x is None or x != x:
            return "—"
        if x >= 0:
            return f"+{abs(x):.4f}/OP"
        return f"-{abs(x):.4f}/OP"

    def fmt_roi_usd(x):
        """Format TVL ROI in USD per OP (e.g., +$1.23/OP, -$1.23/OP)"""
        if x is None or x != x:
            return "—"
        if x >= 0:
            return f"+${abs(x):.2f}/OP"
        return f"-${abs(x):.2f}/OP"

    def fmt_roi(x):
        """Format generic ROI (e.g., +1.23, -0.45)"""
        if x is None or x != x:
            return "—"
        if x >= 0:
            return f"+{x:.2f}"
        return f"{x:.2f}"

    def fmt_delta_usd(x):
        """Format USD delta with sign (e.g., +$50K, -$1.2M)"""
        if x is None or x != x:
            return "—"
        sign = "+" if x >= 0 else "-"
        ax = abs(x)
        if ax >= 1_000_000_000:
            return f"{sign}${ax/1e9:.1f}B"
        elif ax >= 1_000_000:
            return f"{sign}${ax/1e6:.1f}M"
        elif ax >= 1_000:
            return f"{sign}${ax/1e3:.0f}K"
        return f"{sign}${ax:.0f}"

    def fmt_delta_eth(x):
        """Format ETH delta with sign (e.g., +0.0012, -1.2K)"""
        if x is None or x != x:
            return "—"
        sign = "+" if x >= 0 else "-"
        ax = abs(x)
        if ax >= 1_000_000:
            return f"{sign}{ax/1e6:.1f}M"
        elif ax >= 1_000:
            return f"{sign}{ax/1e3:.1f}K"
        return f"{sign}{ax:.4f}"

    def fmt_delta_int(x):
        """Format integer delta with sign (e.g., +1,234, -567)"""
        if x is None or x != x:
            return "—"
        sign = "+" if x >= 0 else "-"
        ax = abs(x)
        if ax >= 1_000_000:
            return f"{sign}{ax/1e6:.1f}M"
        elif ax >= 1_000:
            return f"{sign}{ax/1e3:.0f}K"
        return f"{sign}{int(ax):,}"

    def fmt_int(x):
        """Format integer with commas (e.g., 1,234,567)"""
        if x is None or x != x:
            return "—"
        return f"{int(x):,}"

    def fmt_date(x):
        """Format date as YYYY-MM-DD"""
        if x is None:
            return "—"
        try:
            return x.strftime('%Y-%m-%d')
        except:
            return str(x)

    return fmt_op, fmt_usd, fmt_eth, fmt_pct, fmt_roi_eth, fmt_roi_usd, fmt_roi, fmt_int, fmt_date, fmt_delta_usd, fmt_delta_eth, fmt_delta_int


@app.cell(hide_code=True)
def _():
    """Styling constants and color palettes"""
    # Muted color palette with ~20 distinct colors, ordered to avoid similar adjacent colors
    PROJECT_COLORS = [
        'rgba(239, 68, 68, 0.7)',    # Red
        'rgba(59, 130, 246, 0.7)',   # Blue
        'rgba(16, 185, 129, 0.7)',   # Green
        'rgba(245, 158, 11, 0.7)',   # Amber
        'rgba(139, 92, 246, 0.7)',   # Purple
        'rgba(20, 184, 166, 0.7)',   # Teal
        'rgba(236, 72, 153, 0.7)',   # Pink
        'rgba(107, 114, 128, 0.7)',  # Gray
        'rgba(251, 146, 60, 0.7)',   # Orange
        'rgba(34, 197, 94, 0.7)',    # Emerald
        'rgba(99, 102, 241, 0.7)',   # Indigo
        'rgba(234, 179, 8, 0.7)',    # Yellow
        'rgba(168, 85, 247, 0.7)',   # Violet
        'rgba(6, 182, 212, 0.7)',    # Cyan
        'rgba(244, 63, 94, 0.7)',    # Rose
        'rgba(132, 204, 22, 0.7)',   # Lime
        'rgba(217, 70, 239, 0.7)',   # Fuchsia
        'rgba(249, 115, 22, 0.7)',   # Orange-deep
        'rgba(45, 212, 191, 0.7)',   # Teal-light
        'rgba(129, 140, 248, 0.7)',  # Indigo-light
    ]

    # Superchain network colors (official brand colors with transparency)
    CHAIN_COLORS = {
        'OP Mainnet': 'rgba(255, 4, 32, 0.7)',
        'Base': 'rgba(0, 82, 255, 0.7)',
        'Mode': 'rgba(223, 254, 0, 0.7)',
        'Ink': 'rgba(123, 63, 228, 0.7)',
        'Lisk': 'rgba(0, 51, 204, 0.7)',
        'Soneium': 'rgba(80, 80, 80, 0.7)',
        'Swell': 'rgba(21, 180, 193, 0.7)',
        'Swellchain': 'rgba(21, 180, 193, 0.7)',
        'Unichain': 'rgba(255, 0, 122, 0.7)',
        'Worldchain': 'rgba(80, 80, 80, 0.7)',
        'Bob': 'rgba(255, 165, 0, 0.7)',
    }
    return CHAIN_COLORS, PROJECT_COLORS


@app.cell(hide_code=True)
def _():
    """Plotly layout configuration"""
    PLOTLY_LAYOUT = dict(
        title="",
        barmode="relative",
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=12, color="#111"),
        margin=dict(t=0, l=0, r=0, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
        ),
        xaxis=dict(
            title="",
            showgrid=False,
            linecolor="#000", linewidth=1,
            ticks="outside", tickformat="%Y-%m-%d"
        ),
        yaxis=dict(
            title="",
            showgrid=True, gridcolor="#DDD",
            zeroline=True, zerolinecolor="black", zerolinewidth=1,
            linecolor="#000", linewidth=1,
            ticks="outside", range=[0, None]
        )
    )
    return (PLOTLY_LAYOUT,)


@app.cell(hide_code=True)
def _(CHAIN_COLORS, PLOTLY_LAYOUT, PROJECT_COLORS):
    """Helper functions for styling"""
    def get_chain_color(chain, fallback_idx=0):
        """Get color for a chain, with fallback to PROJECT_COLORS."""
        if chain in CHAIN_COLORS:
            return CHAIN_COLORS[chain]
        return PROJECT_COLORS[fallback_idx % len(PROJECT_COLORS)]

    def get_stacked_area_layout(y_title='', y_format='$,.0s', right_margin=150):
        """Get layout config for stacked area charts with legend on right."""
        layout = PLOTLY_LAYOUT.copy()
        layout['yaxis'] = {**PLOTLY_LAYOUT['yaxis'], 'tickformat': y_format, 'title': y_title}
        layout['xaxis'] = {**PLOTLY_LAYOUT['xaxis'], 'title': ''}
        layout['margin'] = dict(t=10, l=60, r=right_margin, b=40)
        layout['legend'] = dict(
            orientation='v',
            yanchor='top', y=1,
            xanchor='left', x=1.02,
            bgcolor='rgba(255,255,255,0.9)'
        )
        return layout

    # Helper function for SQL IN clauses
    stringify = lambda arr: "'" + "','".join(arr) + "'"
    return


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.graph_objects as go
    return go, pd


@app.cell(hide_code=True)
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
