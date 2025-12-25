import marimo

__generated_with = "0.17.5"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # S7 Grants Council Observational Impact Analysis
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">Optimism</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2025-12-23</span></small>
    """)
    return


@app.cell(hide_code=True)
def _(headline_1, headline_3, headline_4, headline_5, mo):
    _context = """
    - This analysis covers S7 Grants Council grants targeting TVL growth on the Superchain
    - Data was locked on 2025-07-12, 30 days after the program ended
    - The program start date (2025-04-14) represents the weighted average delivery date across all recipients
    - Impact is measured using TVL inflows and onchain activity metrics
    """

    _insights = f"""
    1. {headline_1}.
    2. {headline_3}.
    3. {headline_4}.
    4. {headline_5}.
    """

    mo.accordion({
        "Context": _context,
        "Key Insights": _insights,
        "Data Sources": """
        - [Grants Council Public Tracker](https://docs.google.com/spreadsheets/d/1Ul8iMTsOFUKUmqz6MK0zpgt8Ki8tFtoWKGlwXj-Op34/edit?usp=sharing) - Official grant delivery tracking
        - [OSO Normalized Metadata](https://docs.google.com/spreadsheets/d/1PKCZoQ6la7_VSIXOit6hENVNpU5VtcTygnhqNuewY9g/edit?usp=sharing) - Attribution and measurement assumptions
        - [DefiLlama API](https://defillama.com/) - TVL and volume data via OSO pipeline
        - [OSO Database](https://docs.opensource.observer/docs/) - Processed metrics and event data
        """
    })
    return


@app.cell(hide_code=True)
def _(mo):
    use_op_delivered_input = mo.ui.dropdown(
        options=["Yes", "No"],
        value="Yes",
        label="Use OP Delivered (vs OP Total Amount):"
    )

    use_project_date_ranges_input = mo.ui.dropdown(
        options=["Yes", "No"],
        value="Yes",
        label="Use individualized project date ranges:"
    )

    mo.vstack([
        mo.md("### Settings"),
        use_op_delivered_input,
        use_project_date_ranges_input
    ])
    return (use_op_delivered_input,)


@app.cell(hide_code=True)
def _():
    # Analysis parameters (constants)
    ANALYSIS_START_DATE = "2024-12-20"
    ANALYSIS_END_DATE = "2025-07-31"
    TRAILING_DAYS = 7
    INTERPOLATE_MISSING_DATES = True
    return (
        ANALYSIS_END_DATE,
        ANALYSIS_START_DATE,
        INTERPOLATE_MISSING_DATES,
        TRAILING_DAYS,
    )


@app.cell(hide_code=True)
def _(pd, weighted_datetime):
    # Load grants data from CSV
    from pathlib import Path

    # Try to find the CSV file
    csv_path = Path('analysis/optimism/s7/gc-impact-analysis/s7_grants_council.csv')

    # If not found, try relative to current directory
    if not csv_path.exists():
        csv_path = Path('s7_grants_council.csv')

    df_grants = pd.read_csv(csv_path)

    # Clean up column names
    df_grants.columns = [c.replace(' ', '_').lower() for c in df_grants.columns]
    df_grants['initial_delivery_date'] = pd.to_datetime(df_grants['initial_delivery_date'])
    df_grants['attribution'] = df_grants['attribution'].apply(
        lambda x: int(x.replace('%', ''))/100 if isinstance(x, str) else None
    )
    df_grants['op_total_amount'] = df_grants['op_total_amount'].str.replace(',', '').astype(float)
    df_grants['op_delivered'] = df_grants['op_delivered'].str.replace(',', '').astype(float).fillna(0)
    df_grants['coincentives'] = df_grants['coincentives'].apply(
        lambda x: True if isinstance(x, str) and (x == 'Yes') else False
    )
    df_grants['recipient_address'] = df_grants['recipient_address'].apply(
        lambda x: f"https://optimistic.etherscan.io/address/{x}#tokentxns"
    )

    # Filter TVL grants only
    df_grants_defillama = df_grants[
        ~df_grants['defillama_slugs'].isnull() & 
        (df_grants['intent'] == 'TVL')
    ].copy()

    # Calculate weighted start date
    weighted_start_date = weighted_datetime(
        df_grants_defillama['initial_delivery_date'],
        df_grants_defillama['op_delivered']
    )

    # Derive program dates
    PROGRAM_START_DATE = pd.Timestamp('2025-04-14')
    PROGRAM_END_DATE = pd.Timestamp('2025-06-12')
    return PROGRAM_END_DATE, PROGRAM_START_DATE, df_grants, df_grants_defillama


@app.cell(hide_code=True)
def _(df_grants_defillama):
    # Normalize grant metadata (explode slugs and chains)
    df_normalized_grant_metadata = (
        df_grants_defillama
        .assign(
            slugs=df_grants_defillama.defillama_slugs.str.split(';'),
            chains=df_grants_defillama.chains.str.split(';')
        )
        .explode('slugs')
        .explode('chains')
        .rename(columns={'slugs': 'slug', 'chains': 'chain'})
        [['slug', 'chain', 'attribution', 'proposal_name']]
        .sort_values(by=['slug', 'chain'])
        .reset_index(drop=True)
    )
    df_normalized_grant_metadata['slug'] = df_normalized_grant_metadata['slug'].str.strip()
    df_normalized_grant_metadata['chain'] = df_normalized_grant_metadata['chain'].str.strip()

    DEFILLAMA_SLUGS = list(df_normalized_grant_metadata['slug'].dropna().unique())
    DEFILLAMA_CHAINS = list(df_normalized_grant_metadata['chain'].dropna().unique())
    return DEFILLAMA_CHAINS, DEFILLAMA_SLUGS, df_normalized_grant_metadata


@app.cell(hide_code=True)
def _(
    ANALYSIS_END_DATE,
    ANALYSIS_START_DATE,
    DEFILLAMA_CHAINS,
    DEFILLAMA_SLUGS,
    mo,
    pyoso_db_conn,
    stringify,
):
    _query = f"""
    SELECT
        bucket_day,
        to_artifact_name AS slug,
        UPPER(from_artifact_namespace) AS chain,
        'TVL' AS event_type,
        MAX(amount) AS amount
    FROM int_events_daily__defillama
    WHERE 
        to_artifact_name IN ({stringify(DEFILLAMA_SLUGS)})
        AND bucket_day BETWEEN DATE('{ANALYSIS_START_DATE}') AND DATE('{ANALYSIS_END_DATE}')
        AND UPPER(from_artifact_namespace) IN ({stringify(DEFILLAMA_CHAINS)})
        AND event_type = 'DEFILLAMA_TVL'
    GROUP BY 1,2,3,4
    ORDER BY 1,2,3,4
    """
    df_metrics_raw = mo.sql(_query, engine=pyoso_db_conn, output=False)
    event_types = df_metrics_raw['event_type'].unique().tolist() if 'event_type' in df_metrics_raw.columns else []
    return (df_metrics_raw,)


@app.cell(hide_code=True)
def _(
    INTERPOLATE_MISSING_DATES,
    df_metrics_raw,
    df_normalized_grant_metadata,
    pd,
):
    # Merge DefiLlama data with grant metadata
    df_metrics_base = (
        df_metrics_raw
        .merge(df_normalized_grant_metadata, on=['slug', 'chain'], how='left')
        .dropna()
        .reset_index(drop=True)
    )
    df_metrics_base['bucket_day'] = pd.to_datetime(df_metrics_base['bucket_day'])

    # Interpolate missing dates to fill gaps in the data
    if INTERPOLATE_MISSING_DATES and len(df_metrics_base) > 0:
        # Interpolate for each protocol-chain-event_type combination
        interpolated_frames = []
        for (proposal_name, slug, chain, event_type), group in df_metrics_base.groupby(
            ['proposal_name', 'slug', 'chain', 'event_type']
        ):
            # Get the date range for THIS specific protocol-chain combination
            group_min_date = group['bucket_day'].min()
            group_max_date = group['bucket_day'].max()
            group_dates = pd.date_range(start=group_min_date, end=group_max_date, freq='D')

            # Create a complete date range for this group
            complete_df = pd.DataFrame({'bucket_day': group_dates})

            # Merge with existing data
            merged = complete_df.merge(
                group[['bucket_day', 'amount']],
                on='bucket_day',
                how='left'
            )

            # Interpolate missing values (only between existing data points)
            merged['amount'] = merged['amount'].interpolate(method='linear', limit_direction='forward')

            # Forward fill any remaining NaN at the end
            merged['amount'] = merged['amount'].ffill()

            # Add back the grouping columns
            merged['proposal_name'] = proposal_name
            merged['slug'] = slug
            merged['chain'] = chain
            merged['event_type'] = event_type

            # Add back other columns from the first row of the group
            for col in df_metrics_base.columns:
                if col not in ['bucket_day', 'amount', 'proposal_name', 'slug', 'chain', 'event_type']:
                    merged[col] = group.iloc[0][col]

            interpolated_frames.append(merged)

        df_metrics = pd.concat(interpolated_frames, ignore_index=True)
    else:
        df_metrics = df_metrics_base.copy()
    return (df_metrics,)


@app.cell(hide_code=True)
def _(PROGRAM_END_DATE, PROGRAM_START_DATE, TRAILING_DAYS, df_metrics, mo, pd):
    # Define 7-day windows
    window = pd.Timedelta(days=TRAILING_DAYS - 1)
    windows = {
        'Pre-Incentive': (PROGRAM_START_DATE - window, PROGRAM_START_DATE),
        'Post-Incentive': (PROGRAM_END_DATE - window, PROGRAM_END_DATE),
    }

    # Aggregate daily sums
    daily = (
        df_metrics.groupby(['proposal_name', 'event_type', 'bucket_day'], as_index=False)
        ['amount']
        .sum()
    )

    # Compute window means
    frames = []
    for label, (win_start, win_end) in windows.items():
        means = (
            daily[daily['bucket_day'].between(win_start, win_end)]
            .groupby(['proposal_name', 'event_type'])['amount']
            .mean()
            .rename(label)
        )
        frames.append(means)

    # Combine, compute delta, pivot, and format columns
    df_results = (
        pd.concat(frames, axis=1)
        .fillna(0)
        .assign(Delta=lambda d: d['Post-Incentive'] - d['Pre-Incentive'])
        .round()
        .reset_index()
        .pivot(index='proposal_name', columns='event_type', 
               values=['Pre-Incentive', 'Post-Incentive', 'Delta'])
    )

    # Rename and order columns
    events = df_metrics['event_type'].unique()
    periods = ['Pre-Incentive', 'Post-Incentive', 'Delta']
    df_results.columns = [f'{evt.replace("_", " ").upper()}: {period}' 
                          for period, evt in df_results.columns]
    df_results = df_results.reindex(
        columns=[f'{e.replace("_", " ").upper()}: {p}' for e in events for p in periods],
        fill_value=0
    )

    # Add trading volume per TVL metrics
    if 'TRADING VOLUME: Pre-Incentive' in df_results.columns and 'TVL: Pre-Incentive' in df_results.columns:
        df_results['Trading Volume per TVL: Pre-Incentive'] = (
            df_results['TRADING VOLUME: Pre-Incentive'] / df_results['TVL: Pre-Incentive']
        )
        df_results['Trading Volume per TVL: Post-Incentive'] = (
            df_results['TRADING VOLUME: Post-Incentive'] / df_results['TVL: Post-Incentive']
        )
        df_results['Trading Volume per TVL: Delta'] = (
            df_results['TRADING VOLUME: Delta'] / df_results['TVL: Delta']
        )

    # Check if we have TVL data
    has_tvl = any('TVL:' in str(col) for col in df_results.columns)
    if not has_tvl:
        mo.callout(mo.md("⚠️ No TVL columns in results. The DefiLlama data may not contain 'tvl' event_type for these protocols."), kind="warn")
    return (df_results,)


@app.cell(hide_code=True)
def _(
    PROGRAM_END_DATE,
    TRAILING_DAYS,
    calculate_unique_tvl_uplift,
    df_grants_defillama,
    df_metrics,
    use_op_delivered_input,
):
    # Calculate individualized TVL uplift
    df_unique_tvl = calculate_unique_tvl_uplift(
        df_grants_defillama=df_grants_defillama,
        df_metrics=df_metrics,
        op_column='op_delivered' if use_op_delivered_input.value == 'Yes' else 'op_total_amount',
        program_end_date=PROGRAM_END_DATE,
        trailing_days=TRAILING_DAYS
    )
    individualized_cols = [c for c in df_unique_tvl.columns if 'Individualized' in c]
    return df_unique_tvl, individualized_cols


@app.cell(hide_code=True)
def _(
    df_grants_defillama,
    df_results,
    df_unique_tvl,
    individualized_cols,
    np,
    use_op_delivered_input,
):
    # Create project summary
    OP_COLUMN = 'op_delivered' if use_op_delivered_input.value == 'Yes' else 'op_total_amount'

    df_project_summary = (
        df_grants_defillama
        .copy()
        .rename(columns=lambda c: c.replace('_', ' ').title())
        .set_index('Proposal Name')
        .sort_index()
        .join(df_results)
        .join(df_unique_tvl.set_index('Proposal Name')[individualized_cols])
        .reset_index()
    )

    # Filter to projects with OP delivered
    df_project_summary = df_project_summary[df_project_summary[OP_COLUMN.replace('_', ' ').title()] > 0]
    df_project_summary['Net TVL Inflows per OP'] = (
        df_project_summary['TVL: Delta'] / df_project_summary[OP_COLUMN.replace('_', ' ').title()]
    )
    df_project_summary['Attributable TVL Inflows per OP'] = (
        (df_project_summary['TVL: Delta'] * df_project_summary['Attribution']) / 
        df_project_summary[OP_COLUMN.replace('_', ' ').title()]
    )
    df_project_summary['Impact Rank'] = df_project_summary['Attributable TVL Inflows per OP'].rank(ascending=False)
    df_project_summary = df_project_summary.replace(np.inf, None)
    return (df_project_summary,)


@app.cell(hide_code=True)
def _(df_project_summary, mo):
    _total_projects = len(df_project_summary)
    _has_tvl = 'TVL: Delta' in df_project_summary.columns
    _total_tvl_delta = df_project_summary['TVL: Delta'].sum() if _has_tvl else 0
    _total_op = df_project_summary.get('Op Delivered', df_project_summary.get('Op Total Amount', 0)).sum()
    _avg_roi = df_project_summary['Net TVL Inflows per OP'].mean() if _has_tvl else 0

    headline_1 = f"{_total_projects} protocols received incentives, generating ${_total_tvl_delta/1_000_000:,.1f}M in net TVL inflows" if _has_tvl else f"{_total_projects} protocols received incentives"

    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_1}**

        A total of {_total_op:,.0f} OP was distributed across these grants, with an average ROI of ${_avg_roi:,.2f} in TVL per OP token.
        """) if _has_tvl else mo.callout(mo.md(f"⚠️ TVL data not available. {_total_projects} protocols received {_total_op:,.0f} OP in incentives."), kind="warn")
    ])
    return (headline_1,)


@app.cell(hide_code=True)
def _(df_project_summary, mo):
    # Top performers by attributable ROI
    _has_tvl = 'TVL: Delta' in df_project_summary.columns
    if len(df_project_summary) > 0 and _has_tvl:
        _cols = ['Proposal Name', 'Attributable TVL Inflows per OP', 'TVL: Delta']
        _top_3 = df_project_summary.nsmallest(3, 'Impact Rank')[_cols]
        _top_project = _top_3.iloc[0]['Proposal Name']
        _top_roi = _top_3.iloc[0]['Attributable TVL Inflows per OP']
        headline_3 = f"{_top_project} is the top performer with ${_top_roi:,.2f} in attributable TVL inflows per OP token"
    else:
        headline_3 = "No TVL data available for top performers analysis" if not _has_tvl else "No data available for top performers analysis"

    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_3}**

        Performance varies significantly across the portfolio, with attribution adjustments accounting for co-incentives and scope limitations.
        """) if _has_tvl else mo.callout(mo.md("⚠️ TVL data not available"), kind="warn")
    ])
    return (headline_3,)


@app.cell(hide_code=True)
def _(df_project_summary, mo):
    # Attribution adjustments
    _high_attr = len(df_project_summary[df_project_summary['Attribution'] >= 0.5])
    _total = len(df_project_summary)
    _pct = (_high_attr / _total) * 100

    headline_4 = f"{_pct:.0f}% of grants have 50% or higher attribution, reflecting minimal co-incentive dilution"

    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_4}**

        Attribution adjustments account for co-incentives from SuperStacks, ACS campaigns, and protocol-specific programs running concurrently.
        """)
    ])
    return (headline_4,)


@app.cell(hide_code=True)
def _(df_project_summary, mo):
    # Individualized impact
    _with_individual = df_project_summary[
        df_project_summary['Net TVL Inflows (Individualized) per OP'].notna()
    ]
    _positive_individual = len(_with_individual[
        _with_individual['Net TVL Inflows (Individualized) per OP'] > 0
    ])
    _total_individual = len(_with_individual)

    headline_5 = f"{_positive_individual} out of {_total_individual} protocols show positive TVL growth when measured from their individual grant delivery dates"

    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_5}**

        Individualized measurements account for different grant timing and baseline TVL at the point of first delivery.
        """)
    ])
    return (headline_5,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Visualizations
    """)
    return


@app.cell(hide_code=True)
def _(alt, df_project_summary, mo):
    # Impact summary bar chart
    _chart_data = (
        df_project_summary[['Proposal Name', 'Attributable TVL Inflows per OP']]
        .dropna()
        .sort_values('Attributable TVL Inflows per OP', ascending=True)
    )

    _fig = alt.Chart(_chart_data).mark_bar().encode(
        x=alt.X('Attributable TVL Inflows per OP:Q', 
                title='Attributable TVL Inflows ($) per OP'),
        y=alt.Y('Proposal Name:N', 
                sort='-x',
                title='Project'),
        color=alt.condition(
            alt.datum['Attributable TVL Inflows per OP'] > 0,
            alt.value('#2C7FB8'),
            alt.value('#E45756')
        ),
        tooltip=[
            'Proposal Name:N', 
            alt.Tooltip('Attributable TVL Inflows per OP:Q', format='$,.2f')
        ]
    ).properties(
        width='container',
        height=500,
        title='Attributable TVL Inflows per OP Token (Ranked)'
    ).configure_axis(
        gridColor='#f0f0f0'
    ).configure_view(
        strokeWidth=0
    )

    mo.vstack([
        mo.md("### Impact Summary: Attributable ROI by Project"),
        mo.ui.altair_chart(_fig)
    ])
    return


@app.cell(hide_code=True)
def _(PROGRAM_END_DATE, PROGRAM_START_DATE, alt, df_metrics, mo, pd):
    # TVL over time (stacked area by project)
    _df_tvl = df_metrics[df_metrics['event_type'] == 'TVL'].copy()
    _df_daily = _df_tvl.groupby(['bucket_day', 'proposal_name'], as_index=False)['amount'].sum()

    _base = alt.Chart(_df_daily).mark_area().encode(
        x=alt.X('bucket_day:T', title='Date'),
        y=alt.Y('amount:Q', title='TVL ($)', stack='zero'),
        color=alt.Color('proposal_name:N', legend=alt.Legend(title='Project', orient='top')),
        tooltip=['bucket_day:T', 'proposal_name:N', alt.Tooltip('amount:Q', format='$,.0f')]
    )

    # Add reference lines
    _ref_data = pd.DataFrame({
        'date': [PROGRAM_START_DATE, PROGRAM_END_DATE],
        'label': ['Program Start', 'Program End']
    })

    _rule_start = alt.Chart(_ref_data[_ref_data['label'] == 'Program Start']).mark_rule(
        color='gray',
        strokeDash=[5, 5]
    ).encode(
        x='date:T'
    )

    _rule_end = alt.Chart(_ref_data[_ref_data['label'] == 'Program End']).mark_rule(
        color='gray',
        strokeDash=[5, 5]
    ).encode(
        x='date:T'
    )

    _chart_area = (_base + _rule_start + _rule_end).properties(
        width='container',
        height=400,
        title='TVL Over Time by Project (Stacked Area)'
    ).configure_axis(
        gridColor='#f0f0f0'
    ).configure_view(
        strokeWidth=0
    )

    mo.vstack([
        mo.md("### TVL Growth Over Time"),
        mo.ui.altair_chart(_chart_area)
    ])
    return


@app.cell(hide_code=True)
def _(PROGRAM_END_DATE, PROGRAM_START_DATE, alt, df_metrics, mo, pd):
    # TVL over time (line chart by project)
    _df_tvl = df_metrics[df_metrics['event_type'] == 'TVL'].copy()
    _df_daily = _df_tvl.groupby(['bucket_day', 'proposal_name'], as_index=False)['amount'].sum()

    _base = alt.Chart(_df_daily).mark_line(strokeWidth=2).encode(
        x=alt.X('bucket_day:T', title='Date'),
        y=alt.Y('amount:Q', title='TVL ($)'),
        color=alt.Color('proposal_name:N', legend=alt.Legend(title='Project', orient='top')),
        tooltip=['bucket_day:T', 'proposal_name:N', alt.Tooltip('amount:Q', format='$,.0f')]
    )

    # Add reference lines
    _ref_data = pd.DataFrame({
        'date': [PROGRAM_START_DATE, PROGRAM_END_DATE],
        'label': ['Program Start', 'Program End']
    })

    _rule_start = alt.Chart(_ref_data[_ref_data['label'] == 'Program Start']).mark_rule(
        color='gray',
        strokeDash=[5, 5]
    ).encode(
        x='date:T'
    )

    _rule_end = alt.Chart(_ref_data[_ref_data['label'] == 'Program End']).mark_rule(
        color='gray',
        strokeDash=[5, 5]
    ).encode(
        x='date:T'
    )

    _chart_line = (_base + _rule_start + _rule_end).properties(
        width='container',
        height=400,
        title='TVL Over Time by Project (Line Chart)'
    ).configure_axis(
        gridColor='#f0f0f0'
    ).configure_view(
        strokeWidth=0
    )

    mo.ui.altair_chart(_chart_line)
    return


@app.cell(hide_code=True)
def _(PROGRAM_END_DATE, PROGRAM_START_DATE, alt, df_metrics, mo, pd):
    # TVL over time (stacked area by chain)
    _df_tvl = df_metrics[df_metrics['event_type'] == 'TVL'].copy()
    _df_daily_chain = _df_tvl.groupby(['bucket_day', 'chain'], as_index=False)['amount'].sum()

    _base = alt.Chart(_df_daily_chain).mark_area().encode(
        x=alt.X('bucket_day:T', title='Date'),
        y=alt.Y('amount:Q', title='TVL ($)', stack='zero'),
        color=alt.Color('chain:N', legend=alt.Legend(title='Chain', orient='top')),
        tooltip=['bucket_day:T', 'chain:N', alt.Tooltip('amount:Q', format='$,.0f')]
    )

    # Add reference lines
    _ref_data = pd.DataFrame({
        'date': [PROGRAM_START_DATE, PROGRAM_END_DATE],
        'label': ['Program Start', 'Program End']
    })

    _rule_start = alt.Chart(_ref_data[_ref_data['label'] == 'Program Start']).mark_rule(
        color='gray',
        strokeDash=[5, 5]
    ).encode(
        x='date:T'
    )

    _rule_end = alt.Chart(_ref_data[_ref_data['label'] == 'Program End']).mark_rule(
        color='gray',
        strokeDash=[5, 5]
    ).encode(
        x='date:T'
    )

    _chart_chain = (_base + _rule_start + _rule_end).properties(
        width='container',
        height=400,
        title='TVL Over Time by Chain (Stacked Area)'
    ).configure_axis(
        gridColor='#f0f0f0'
    ).configure_view(
        strokeWidth=0
    )

    mo.vstack([
        mo.md("### TVL by Chain"),
        mo.ui.altair_chart(_chart_chain)
    ])
    return


@app.cell(hide_code=True)
def _(PROGRAM_END_DATE, PROGRAM_START_DATE, alt, df_metrics, mo, pd):
    # TVL over time (line chart by chain)
    _df_tvl = df_metrics[df_metrics['event_type'] == 'TVL'].copy()
    _df_daily_chain = _df_tvl.groupby(['bucket_day', 'chain'], as_index=False)['amount'].sum()

    _base = alt.Chart(_df_daily_chain).mark_line(strokeWidth=2).encode(
        x=alt.X('bucket_day:T', title='Date'),
        y=alt.Y('amount:Q', title='TVL ($)'),
        color=alt.Color('chain:N', legend=alt.Legend(title='Chain', orient='top')),
        tooltip=['bucket_day:T', 'chain:N', alt.Tooltip('amount:Q', format='$,.0f')]
    )

    # Add reference lines
    _ref_data = pd.DataFrame({
        'date': [PROGRAM_START_DATE, PROGRAM_END_DATE],
        'label': ['Program Start', 'Program End']
    })

    _rule_start = alt.Chart(_ref_data[_ref_data['label'] == 'Program Start']).mark_rule(
        color='gray',
        strokeDash=[5, 5]
    ).encode(
        x='date:T'
    )

    _rule_end = alt.Chart(_ref_data[_ref_data['label'] == 'Program End']).mark_rule(
        color='gray',
        strokeDash=[5, 5]
    ).encode(
        x='date:T'
    )

    _chart_chain_line = (_base + _rule_start + _rule_end).properties(
        width='container',
        height=400,
        title='TVL Over Time by Chain (Line Chart)'
    ).configure_axis(
        gridColor='#f0f0f0'
    ).configure_view(
        strokeWidth=0
    )

    mo.ui.altair_chart(_chart_chain_line)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Detailed Metrics Tables
    """)
    return


@app.cell(hide_code=True)
def _(df_results, mo):
    mo.vstack([
        mo.md("### Pre/Post Incentive Metrics Comparison"),
        mo.ui.table(
            data=df_results.reset_index(),
            show_column_summaries=False,
            show_data_types=False,
            page_size=20,
            freeze_columns_left=['proposal_name']
        )
    ])
    return


@app.cell(hide_code=True)
def _(df_unique_tvl, mo):
    mo.vstack([
        mo.md("""
        ### Individualized TVL Uplift Analysis

        This table shows TVL uplift calculated using each project's individual grant delivery date as the baseline, 
        rather than using a common program start date.
        """),
        mo.ui.table(
            data=df_unique_tvl,
            show_column_summaries=False,
            show_data_types=False,
            page_size=20,
            freeze_columns_left=['Proposal Name']
        )
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Project Deep Dive
    """)
    return


@app.cell(hide_code=True)
def _(df_grants_defillama):
    # Define project list as constant to avoid circular deps
    PROJECT_LIST = sorted(df_grants_defillama['proposal_name'].unique())
    return (PROJECT_LIST,)


@app.cell(hide_code=True)
def _(PROJECT_LIST, mo):
    project_selector_input = mo.ui.dropdown(
        options=PROJECT_LIST,
        value=PROJECT_LIST[0],
        label="Select a project for deep dive:",
        full_width=True
    )

    project_selector_input
    return (project_selector_input,)


@app.cell(hide_code=True)
def _(
    df_grants_defillama,
    df_metrics,
    df_project_summary,
    mo,
    project_selector_input,
):
    _selected = project_selector_input.value
    _project_summary_row = df_project_summary[
        df_project_summary['Proposal Name'] == _selected
    ]
    _project_metrics = df_metrics[
        df_metrics['proposal_name'] == _selected
    ]

    if len(_project_summary_row) > 0:
        _row = _project_summary_row.iloc[0]
        _project_metadata = df_grants_defillama[
            df_grants_defillama['proposal_name'] == _selected
        ].iloc[0].to_dict()

        _defillama_urls = "; ".join([
            f"https://defillama.com/protocol/{x.strip()}" 
            for x in _project_metadata['defillama_slugs'].split(';')
        ])

        _significant_prior_tvl = (
            _row.get('TVL: Pre-Incentive', 0) > (2 * _row.get('Op Total Amount', 0))
        )

        _context = f"""
        **Monitoring**
        - Grant Application: [{_project_metadata['proposal_name']}]({_project_metadata['proposal_link']})
        - Recipient Address: {_project_metadata['recipient_address']}

        **Measurement Assumptions**
        - Share of impact attributed to this grant: **{_row['Attribution']*100:.0f}%**
        - Rationale: {'only a ' + str(_project_metadata.get('scope', '')).lower() + ' were targeted;' if _project_metadata.get('scope') else ''} {'project had significant TVL (relative to the grant size) prior to the grant' if _significant_prior_tvl else 'project did not have significant TVL prior to the grant'}; {'other incentive programs' if _project_metadata.get('coincentives') else 'no other incentive programs'} were running at the same time.
        - Chains: {_project_metadata['chains'].title()}
        - Protocols: {_defillama_urls}

        **Key Metrics**
        - Net TVL Inflows per OP: ${_row.get('Net TVL Inflows per OP', 0):,.2f}
        - Attributable TVL Inflows per OP: ${_row.get('Attributable TVL Inflows per OP', 0):,.2f}
        - TVL Pre-Incentive: ${_row.get('TVL: Pre-Incentive', 0):,.0f}
        - TVL Post-Incentive: ${_row.get('TVL: Post-Incentive', 0):,.0f}
        - TVL Delta: ${_row.get('TVL: Delta', 0):,.0f}

        **Additional Context**
        {_project_metadata.get('comments', 'No additional comments')}
        """

        mo.vstack([
            mo.md(f"#### {_selected}"),
            mo.md(_context)
        ])
    else:
        mo.md("No data available for selected project")
    return


@app.cell(hide_code=True)
def _(
    ANALYSIS_END_DATE,
    ANALYSIS_START_DATE,
    PROGRAM_END_DATE,
    PROGRAM_START_DATE,
    alt,
    df_metrics,
    mo,
    pd,
    project_selector_input,
):
    # Project-specific TVL chart
    _selected = project_selector_input.value
    _project_metrics = df_metrics[df_metrics['proposal_name'] == _selected]
    _project_tvl = _project_metrics[_project_metrics['event_type'] == 'TVL'].copy()


    _df_daily_chain = _project_tvl.groupby(['bucket_day', 'chain'], as_index=False)['amount'].sum()

    _base = alt.Chart(_df_daily_chain).mark_area().encode(
        x=alt.X('bucket_day:T', title='Date', 
                scale=alt.Scale(domain=[pd.Timestamp(ANALYSIS_START_DATE), pd.Timestamp(ANALYSIS_END_DATE)])),
        y=alt.Y('amount:Q', title='TVL ($)', stack='zero'),
        color=alt.Color('chain:N', legend=alt.Legend(title='Chain')),
        tooltip=['bucket_day:T', 'chain:N', alt.Tooltip('amount:Q', format='$,.0f')]
    )

    # Add reference lines
    _ref_data = pd.DataFrame({
        'date': [PROGRAM_START_DATE, PROGRAM_END_DATE],
        'label': ['Program Start', 'Program End']
    })

    _rule_start = alt.Chart(_ref_data[_ref_data['label'] == 'Program Start']).mark_rule(
        color='gray',
        strokeDash=[5, 5]
    ).encode(
        x='date:T'
    )

    _rule_end = alt.Chart(_ref_data[_ref_data['label'] == 'Program End']).mark_rule(
        color='gray',
        strokeDash=[5, 5]
    ).encode(
        x='date:T'
    )

    _chart = (_base + _rule_start + _rule_end).properties(
        width='container',
        height=300,
        title=f'{_selected} TVL Over Time by Chain'
    ).configure_axis(
        gridColor='#f0f0f0'
    ).configure_view(
        strokeWidth=0
    )

    mo.ui.altair_chart(_chart)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    # Methodology Details

    ## Overview
    This analysis measures the impact of S7 Grants Council TVL grants by comparing pre- and post-incentive metrics across DeFi protocols on the Superchain.

    ## Part 1: Grant Identification
    - Source: Official Grants Council public tracker
    - Focus: Grants with "TVL" intent and DefiLlama integration
    - Period: Season 7 (delivery dates from March-May 2025)
    - Normalization: Grants mapped to DefiLlama protocol slugs and chains

    ## Part 2: Metrics Collection
    - TVL data from DefiLlama via OSO pipeline
        - Additional metrics: trading volume, userops
    - Time windows: 7-day trailing averages
    - Baseline: Pre-incentive (7 days before program start)
    - Evaluation: Post-incentive (7 days before program end)

    ## Part 3: Attribution Model
    - Base attribution from co-incentive analysis
    - Adjustments for:
      - SuperStacks overlapping campaigns
      - ACS (Alternative Chain Support) programs
      - Protocol-specific incentives
      - Scope limitations (subset of pools/vaults)
    - Individual project date ranges available for granular analysis

    ## Part 4: Impact Calculation
    - Net TVL Inflows = Post-incentive TVL - Pre-incentive TVL
    - ROI = Net TVL Inflows / OP Delivered
    - Attributable ROI = (Net TVL Inflows × Attribution%) / OP Delivered

    ## Limitations
    - Does not account for TVL retention beyond 30-day post-program window
    - Attribution percentages are estimates based on available information
    - Some protocols had incomplete DefiLlama data
    - Market conditions and external factors not isolated
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Grant Details & Metadata
    """)
    return


@app.cell(hide_code=True)
def _(df_normalized_grant_metadata, mo):
    mo.vstack([
        mo.md("""
        ### Normalized Grant Metadata

        This table shows the mapping between projects, DefiLlama slugs, chains, and attribution factors.
        Each row represents a unique protocol-chain combination.
        """),
        mo.ui.table(
            data=df_normalized_grant_metadata,
            show_column_summaries=False,
            show_data_types=False,
            page_size=20
        )
    ])
    return


@app.cell(hide_code=True)
def _(df_grants, mo):
    mo.vstack([
        mo.md("### All Grants (Including Non-TVL)"),
        mo.ui.table(
            data=df_grants[['proposal_name', 'oso_slug', 'status', 'initial_delivery_date', 
                           'op_delivered', 'op_total_amount', 'intent']],
            show_column_summaries=False,
            show_data_types=False,
            page_size=20
        )
    ])
    return


@app.cell(hide_code=True)
def _(df_project_summary, mo):
    mo.vstack([
        mo.md("### TVL-Targeted Grants Summary"),
        mo.ui.table(
            data=df_project_summary,
            show_column_summaries=False,
            show_data_types=False,
            page_size=20,
            freeze_columns_left=['Proposal Name']
        )
    ])
    return


@app.cell(hide_code=True)
def _(np, pd):
    def weighted_datetime(dates: pd.Series, weights: pd.Series) -> pd.Timestamp:
        """Calculate weighted average timestamp."""
        m = dates.notna() & weights.notna() & (weights > 0)
        if not m.any() or weights[m].sum() == 0:
            return pd.NaT
        t_ns = dates[m].astype('int64')
        w = weights[m].astype(float).to_numpy()
        avg_ns = np.average(t_ns, weights=w)
        return pd.to_datetime(avg_ns)

    def stringify(arr):
        """Convert array to SQL IN clause format."""
        return "'" + "','".join(arr) + "'"

    def calculate_unique_tvl_uplift(
        df_grants_defillama,
        df_metrics,
        op_column,
        program_end_date,
        trailing_days
    ):
        """Calculate TVL uplift using individualized project date ranges."""
        op_col_cleaned = op_column
        candidate_cols = [f'{op_col_cleaned}_date', 'initial_delivery_date', 'delivery_date']
        delivery_src = next((c for c in candidate_cols if c in df_grants_defillama.columns), None)
        if delivery_src is None:
            delivery_src = 'initial_delivery_date'

        m = (df_metrics['event_type'].str.upper() == 'TVL')
        tvl_daily = (
            df_metrics[m]
            .copy()
            .assign(bucket_day=lambda d: pd.to_datetime(d['bucket_day'], errors='coerce').dt.floor('D'))
            .groupby(['proposal_name', 'bucket_day'], as_index=False)['amount']
            .sum()
            .rename(columns={'amount': 'tvl'})
        )

        meta = df_grants_defillama[['proposal_name', delivery_src, op_col_cleaned]].copy()
        meta[delivery_src] = pd.to_datetime(meta[delivery_src], errors='coerce').dt.floor('D')
        meta = (
            meta
            .dropna(subset=[delivery_src])
            .rename(columns={delivery_src: 'delivery_date', op_col_cleaned: 'op_value'})
        )

        tvl_daily = tvl_daily.merge(meta[['proposal_name', 'delivery_date']], on='proposal_name', how='inner')
        program_end_date = pd.to_datetime(program_end_date).floor('D')
        window = pd.Timedelta(days=trailing_days - 1)

        pre_mask = (
            (tvl_daily['bucket_day'] >= tvl_daily['delivery_date'] - window) &
            (tvl_daily['bucket_day'] <= tvl_daily['delivery_date'])
        )
        post_mask = (
            (tvl_daily['bucket_day'] >= program_end_date - window) &
            (tvl_daily['bucket_day'] <= program_end_date)
        )

        pre = (
            tvl_daily[pre_mask]
            .groupby('proposal_name', as_index=False)['tvl']
            .mean()
            .rename(columns={'tvl': 'TVL: Pre-Incentive (Individualized)'})
        )
        post = (
            tvl_daily[post_mask]
            .groupby('proposal_name', as_index=False)['tvl']
            .mean()
            .rename(columns={'tvl': 'TVL Post'})
        )

        out = (
            meta[['proposal_name', 'delivery_date', 'op_value']].drop_duplicates()
            .merge(pre, on='proposal_name', how='left')
            .merge(post, on='proposal_name', how='left')
        )
        # Fill NaN values with proper dtype handling
        out['TVL: Pre-Incentive (Individualized)'] = out['TVL: Pre-Incentive (Individualized)'].fillna(0).infer_objects(copy=False)
        out['TVL Post'] = out['TVL Post'].fillna(0).infer_objects(copy=False)
        out['TVL: Delta (Individualized)'] = out['TVL Post'] - out['TVL: Pre-Incentive (Individualized)']
        out.rename(columns={
            'proposal_name': 'Proposal Name',
            'delivery_date': 'Delivery Date',
            'op_value': 'Op Delivered'
        }, inplace=True)
        out['Net TVL Inflows (Individualized) per OP'] = out['TVL: Delta (Individualized)'] / out['Op Delivered']
        return out.sort_values('TVL: Delta (Individualized)', ascending=False)
    return calculate_unique_tvl_uplift, stringify, weighted_datetime


@app.cell(hide_code=True)
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    import os
    import marimo as mo

    # Explicitly load .env if not already loaded by marimo
    # Marimo should auto-load based on pyproject.toml, but we'll ensure it's loaded
    try:
        from dotenv import load_dotenv, find_dotenv
        dotenv_path = find_dotenv(usecwd=True)
        if dotenv_path:
            load_dotenv(dotenv_path, override=False)
    except Exception:
        pass

    # Check if OSO_API_KEY is available
    api_key_available = bool(os.environ.get('OSO_API_KEY'))

    # Setup pyoso client
    import pyoso
    try:
        pyoso_db_conn = pyoso.Client().dbapi_connection()
    except Exception as e:
        print(f"⚠️ Error connecting to pyoso database: {e}")
        if not api_key_available:
            print("💡 Tip: Make sure OSO_API_KEY is set in your .env file")
            print("💡 Run marimo from the repo root directory to auto-load .env")
        pyoso_db_conn = None
    return mo, pyoso_db_conn


@app.cell(hide_code=True)
def _():
    import numpy as np
    import pandas as pd
    import altair as alt
    return alt, np, pd


if __name__ == "__main__":
    app.run()
