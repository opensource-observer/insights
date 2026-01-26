import marimo

__generated_with = "unknown"
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
def _(df_grants, df_metrics, mo, pd):
    """Summary metrics cards"""
    # Calculate summary statistics
    _total_op = df_grants['amount'].sum()
    _total_projects = df_grants['oso_project_slug'].nunique()

    # Format OP amount
    if _total_op >= 1_000_000:
        _op_str = f"{_total_op/1e6:.1f}M"
    else:
        _op_str = f"{_total_op/1e3:.0f}K"

    # Calculate Superchain Revenue (aggregate from metrics)
    _revenue_metrics = df_metrics[df_metrics['metric_name'].str.contains('revenue|gas', case=False, na=False)]
    _total_revenue = _revenue_metrics['amount'].sum() if not _revenue_metrics.empty else 0
    if _total_revenue >= 1_000_000:
        _revenue_str = f"Ξ {_total_revenue/1e6:.1f}M"
    else:
        _revenue_str = f"Ξ {_total_revenue/1e3:.0f}K"

    # Calculate TVL Growth (aggregate from metrics)
    _tvl_metrics = df_metrics[df_metrics['metric_name'].str.contains('tvl', case=False, na=False)]
    _total_tvl = _tvl_metrics['amount'].sum() if not _tvl_metrics.empty else 0
    if _total_tvl >= 1_000_000:
        _tvl_str = f"${_total_tvl/1e6:.1f}M"
    else:
        _tvl_str = f"${_total_tvl/1e3:.0f}K"

    # Create summary cards
    _card_total_op = mo.md(f"""
    <div style="padding: 16px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Total OP Allocated</div>
    <div style="font-size: 24px; font-weight: 700; margin-bottom: 4px;">{_op_str}</div>
    <div style="font-size: 11px; color: #888;">Across all programs</div>
    </div>
    """)

    _card_total_projects = mo.md(f"""
    <div style="padding: 16px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Total Projects</div>
    <div style="font-size: 24px; font-weight: 700; margin-bottom: 4px;">{_total_projects}</div>
    <div style="font-size: 11px; color: #888;">Funded projects</div>
    </div>
    """)

    _card_total_revenue = mo.md(f"""
    <div style="padding: 16px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Superchain Revenue</div>
    <div style="font-size: 24px; font-weight: 700; margin-bottom: 4px;">{_revenue_str}</div>
    <div style="font-size: 11px; color: #888;">Generated revenue</div>
    </div>
    """)

    _card_total_tvl = mo.md(f"""
    <div style="padding: 16px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Total TVL</div>
    <div style="font-size: 24px; font-weight: 700; margin-bottom: 4px;">{_tvl_str}</div>
    <div style="font-size: 11px; color: #888;">Total value locked</div>
    </div>
    """)

    # Display cards horizontally
    mo.hstack([_card_total_op, _card_total_projects, _card_total_revenue, _card_total_tvl], widths="equal")
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
def _(df_grants, df_metrics, mo, pd):
    """Season benchmarking table"""
    # Group grants by season
    _season_summary = df_grants.groupby('grants_season_or_mission').agg({
        'amount': 'sum',
        'oso_project_slug': 'nunique',
        'application_name': 'count'
    }).reset_index()
    _season_summary.columns = ['Season/Mission', 'Total OP', 'Projects', 'Total Grants']

    # Join with metrics to calculate aggregate performance
    # For each season, sum up the metrics for all projects that received grants in that season
    _season_metrics = []
    for _, _row in _season_summary.iterrows():
        _season = _row['Season/Mission']
        # Get oso_project_ids for projects in this season (matches project_id in metrics)
        _project_ids_in_season = df_grants[df_grants['grants_season_or_mission'] == _season]['oso_project_id'].dropna().unique()

        # Get metrics for these projects using project_id
        _season_df_metrics = df_metrics[df_metrics['project_id'].isin(_project_ids_in_season)]

        # Calculate revenue
        _revenue = _season_df_metrics[
            _season_df_metrics['metric_name'].str.contains('revenue|gas', case=False, na=False)
        ]['amount'].sum()

        # Calculate TVL
        _tvl = _season_df_metrics[
            _season_df_metrics['metric_name'].str.contains('tvl', case=False, na=False)
        ]['amount'].sum()

        _season_metrics.append({
            'Season/Mission': _season,
            'Revenue': _revenue,
            'TVL': _tvl
        })

    _metrics_df = pd.DataFrame(_season_metrics)
    _season_summary = _season_summary.merge(_metrics_df, on='Season/Mission', how='left')

    # Calculate ROI metrics
    _season_summary['Revenue ROI'] = (_season_summary['Revenue'] / _season_summary['Total OP']).fillna(0)
    _season_summary['TVL ROI'] = (_season_summary['TVL'] / _season_summary['Total OP']).fillna(0)

    # Format for display
    _display_df = _season_summary.copy()
    _display_df['Total OP'] = _display_df['Total OP'].apply(lambda x: f"{x:,.0f}")
    _display_df['Revenue'] = _display_df['Revenue'].apply(lambda x: f"Ξ {x/1e6:.1f}M" if x >= 1e6 else f"Ξ {x/1e3:.0f}K")
    _display_df['TVL'] = _display_df['TVL'].apply(lambda x: f"${x/1e6:.1f}M" if x >= 1e6 else f"${x/1e3:.0f}K")
    _display_df['Revenue ROI'] = _display_df['Revenue ROI'].apply(lambda x: f"{x:.2f}")
    _display_df['TVL ROI'] = _display_df['TVL ROI'].apply(lambda x: f"{x:.2f}")

    _season_table = mo.ui.table(
        data=_display_df,
        selection=None,
        label="Season Benchmarking"
    )

    _season_table
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
            "Superchain Revenue",
            "TVL",
            "Transactions",
            "User Ops",
            "Developer Activity"
        ],
        value="Superchain Revenue",
        label="Select Metric"
    )

    time_period_selector = mo.ui.dropdown(
        options=["6 months", "12 months", "18 months"],
        value="12 months",
        label="Time Period After Funding"
    )

    mo.hstack([season_selector, metric_selector, time_period_selector])
    return season_selector, metric_selector, time_period_selector


@app.cell(hide_code=True)
def _(df_grants, df_metrics, metric_selector, mo, pd, season_selector, time_period_selector):
    """Grant comparison table"""
    if season_selector.value:
        # Filter grants for selected season
        _filtered_grants = df_grants[df_grants['grants_season_or_mission'] == season_selector.value]

        # Parse time period
        _months = int(time_period_selector.value.split()[0])

        # For each grant, calculate metric performance over the time period
        _grant_performance = []
        for _, _grant in _filtered_grants.iterrows():
            _project_id = _grant['oso_project_id']
            _funding_date = _grant['funding_date']
            _amount = _grant['amount']
            _end_date = _funding_date + pd.DateOffset(months=_months)

            # Filter metrics for this project in the time window using project_id
            _project_metrics = df_metrics[
                (df_metrics['project_id'] == _project_id) &
                (df_metrics['sample_date'] >= _funding_date) &
                (df_metrics['sample_date'] <= _end_date)
            ] if pd.notna(_project_id) else df_metrics.head(0)

            # Get metric value based on selection
            _metric_filter = {
                "Superchain Revenue": "revenue|gas",
                "TVL": "tvl",
                "Transactions": "transaction",
                "User Ops": "user.*op|contract.*call",
                "Developer Activity": "commit|contributor"
            }[metric_selector.value]

            _metric_value = _project_metrics[
                _project_metrics['metric_name'].str.contains(_metric_filter, case=False, na=False)
            ]['amount'].sum()

            _grant_performance.append({
                'Project': _grant['application_name'],
                'Grant Amount (OP)': _amount,
                'Metric Value': _metric_value,
                'ROI': _metric_value / _amount if _amount > 0 else 0
            })

        _perf_df = pd.DataFrame(_grant_performance)

        # Format for display based on metric type
        _perf_df['Grant Amount (OP)'] = _perf_df['Grant Amount (OP)'].apply(lambda x: f"{x:,.0f}")

        # Use ETH prefix for revenue, $ for TVL, no prefix for counts
        if metric_selector.value == "Superchain Revenue":
            _perf_df['Metric Value'] = _perf_df['Metric Value'].apply(
                lambda x: f"Ξ {x/1e6:.1f}M" if x >= 1e6 else f"Ξ {x/1e3:.0f}K" if x >= 1e3 else f"Ξ {x:.0f}"
            )
        elif metric_selector.value == "TVL":
            _perf_df['Metric Value'] = _perf_df['Metric Value'].apply(
                lambda x: f"${x/1e6:.1f}M" if x >= 1e6 else f"${x/1e3:.0f}K" if x >= 1e3 else f"${x:.0f}"
            )
        else:
            _perf_df['Metric Value'] = _perf_df['Metric Value'].apply(
                lambda x: f"{x/1e6:.1f}M" if x >= 1e6 else f"{x/1e3:.0f}K" if x >= 1e3 else f"{x:.0f}"
            )
        _perf_df['ROI'] = _perf_df['ROI'].apply(lambda x: f"{x:.2f}")

        mo.ui.table(_perf_df, label=f"{season_selector.value} - {metric_selector.value}")
    else:
        mo.md("Please select a season to view grant comparison.")
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
    """Winners and losers metric selector"""
    winners_metric_selector = mo.ui.dropdown(
        options=["Superchain Revenue", "TVL", "Transactions", "User Ops", "Developer Activity"],
        value="Superchain Revenue",
        label="Rank By Metric"
    )
    winners_metric_selector
    return (winners_metric_selector,)


@app.cell(hide_code=True)
def _(df_grants, df_metrics, mo, pd, winners_metric_selector):
    """Winners and losers tables"""
    # Calculate total performance for each project
    _metric_filter = {
        "Superchain Revenue": "revenue|gas",
        "TVL": "tvl",
        "Transactions": "transaction",
        "User Ops": "user.*op|contract.*call",
        "Developer Activity": "commit|contributor"
    }[winners_metric_selector.value]

    # Aggregate grants by project - include oso_project_id for joining with metrics
    _project_grants = df_grants.groupby('oso_project_id').agg({
        'amount': 'sum',
        'application_name': 'first',
        'oso_project_slug': 'first'
    }).reset_index()
    _project_grants.columns = ['project_id', 'total_funding', 'project_name', 'project_slug']

    # Calculate metrics for each project using project_id
    _project_performance = []
    for _, _proj in _project_grants.iterrows():
        if pd.notna(_proj['project_id']):
            _project_metrics = df_metrics[df_metrics['project_id'] == _proj['project_id']]
            _metric_value = _project_metrics[
                _project_metrics['metric_name'].str.contains(_metric_filter, case=False, na=False)
            ]['amount'].sum()
        else:
            _metric_value = 0

        _project_performance.append({
            'Project': _proj['project_name'],
            'Total Funding (OP)': _proj['total_funding'],
            'Metric Value': _metric_value,
            'ROI': _metric_value / _proj['total_funding'] if _proj['total_funding'] > 0 else 0
        })

    _perf_df = pd.DataFrame(_project_performance)
    _perf_df = _perf_df.sort_values('ROI', ascending=False)

    # Determine formatting based on metric type
    def _format_metric(x):
        if winners_metric_selector.value == "Superchain Revenue":
            return f"Ξ {x/1e6:.1f}M" if x >= 1e6 else f"Ξ {x/1e3:.0f}K" if x >= 1e3 else f"Ξ {x:.0f}"
        elif winners_metric_selector.value == "TVL":
            return f"${x/1e6:.1f}M" if x >= 1e6 else f"${x/1e3:.0f}K" if x >= 1e3 else f"${x:.0f}"
        else:
            return f"{x/1e6:.1f}M" if x >= 1e6 else f"{x/1e3:.0f}K" if x >= 1e3 else f"{x:.0f}"

    # Top 10 Winners
    _winners = _perf_df.head(10).copy()
    _winners['Total Funding (OP)'] = _winners['Total Funding (OP)'].apply(lambda x: f"{x:,.0f}")
    _winners['Metric Value'] = _winners['Metric Value'].apply(_format_metric)
    _winners['ROI'] = _winners['ROI'].apply(lambda x: f"✅ {x:.2f}")

    # Bottom 10 Losers
    _losers = _perf_df.tail(10).copy()
    _losers['Total Funding (OP)'] = _losers['Total Funding (OP)'].apply(lambda x: f"{x:,.0f}")
    _losers['Metric Value'] = _losers['Metric Value'].apply(_format_metric)
    _losers['ROI'] = _losers['ROI'].apply(lambda x: f"❌ {x:.2f}")

    mo.vstack([
        mo.md("### Top 10 Performers"),
        mo.ui.table(_winners, label="Winners"),
        mo.md("### Bottom 10 Performers"),
        mo.ui.table(_losers, label="Losers")
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
def _(df_grants, mo):
    """Project selector"""
    _projects = sorted(df_grants['application_name'].dropna().unique().tolist())
    project_selector = mo.ui.dropdown(
        options=_projects,
        value=_projects[0] if _projects else None,
        label="Select Project"
    )
    project_selector
    return (project_selector,)


@app.cell(hide_code=True)
def _(df_grants, df_metrics, go, mo, pd, PLOTLY_LAYOUT, project_selector):
    """Project deep dive details"""
    if project_selector.value:
        # Get all grants for this project
        _project_grants = df_grants[df_grants['application_name'] == project_selector.value]
        _project_id = _project_grants['oso_project_id'].iloc[0] if len(_project_grants) > 0 else None

        # Format grants table
        _grants_table = _project_grants[['funding_date', 'grants_season_or_mission', 'amount']].copy()
        _grants_table['funding_date'] = _grants_table['funding_date'].dt.strftime('%Y-%m-%d')
        _grants_table['amount'] = _grants_table['amount'].apply(lambda x: f"{x:,.0f}")
        _grants_table.columns = ['Funding Date', 'Season/Mission', 'Amount (OP)']

        _total_funding = _project_grants['amount'].sum()

        # Get metrics time series for this project using project_id
        if pd.notna(_project_id):
            _project_metrics = df_metrics[df_metrics['project_id'] == _project_id].copy()
            _project_metrics = _project_metrics.sort_values('sample_date')

            # Create time series chart
            _fig = go.Figure()
            for _metric_name in _project_metrics['metric_name'].unique():
                _metric_data = _project_metrics[_project_metrics['metric_name'] == _metric_name]
                _fig.add_trace(go.Scatter(
                    x=_metric_data['sample_date'],
                    y=_metric_data['amount'],
                    name=_metric_name,
                    mode='lines'
                ))

            # Add vertical lines for grant funding dates
            for _, _grant in _project_grants.iterrows():
                _fig.add_vline(
                    x=_grant['funding_date'],
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Grant: {_grant['amount']:.0f} OP",
                    annotation_position="top"
                )

            _layout = PLOTLY_LAYOUT.copy()
            _layout['yaxis'] = {**PLOTLY_LAYOUT['yaxis'], 'title': 'Metric Value'}
            _layout['xaxis'] = {**PLOTLY_LAYOUT['xaxis'], 'title': 'Date'}
            _layout['height'] = 400
            _fig.update_layout(_layout)

            mo.vstack([
                mo.md(f"### {project_selector.value}"),
                mo.md(f"**Total Funding**: {_total_funding:,.0f} OP"),
                mo.md("#### Grants Received"),
                mo.ui.table(_grants_table),
                mo.md("#### Performance Over Time"),
                mo.ui.plotly(_fig)
            ])
        else:
            mo.md(f"No metrics data available for {project_selector.value}")
    else:
        mo.md("Please select a project to view deep dive.")
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
    """Chain selector"""
    _chains = sorted(df_metrics['metric_source'].dropna().unique().tolist())
    chain_selector = mo.ui.dropdown(
        options=_chains,
        value=_chains[0] if _chains else None,
        label="Select Chain"
    )
    chain_selector
    return (chain_selector,)


@app.cell(hide_code=True)
def _(chain_selector, df_grants, df_metrics, mo, pd):
    """Chain analysis"""
    if chain_selector.value:
        # Filter metrics for selected chain
        _chain_metrics = df_metrics[df_metrics['metric_source'] == chain_selector.value]

        # Get unique project_ids on this chain (use project_id to match with grants)
        _project_ids_on_chain = _chain_metrics['project_id'].dropna().unique()

        # Get funding for these projects using oso_project_id
        _chain_grants = df_grants[df_grants['oso_project_id'].isin(_project_ids_on_chain)]

        # Aggregate by project
        _project_summary = []
        for _project_id in _project_ids_on_chain:
            _funding = _chain_grants[_chain_grants['oso_project_id'] == _project_id]['amount'].sum()
            _project_metrics_on_chain = _chain_metrics[_chain_metrics['project_id'] == _project_id]
            _total_metric_value = _project_metrics_on_chain['amount'].sum()
            # Get project name from metrics (display name)
            _project_name = _project_metrics_on_chain['project_name'].iloc[0] if len(_project_metrics_on_chain) > 0 else str(_project_id)

            _project_summary.append({
                'Project': _project_name,
                'Total Funding (OP)': _funding,
                'Total Metric Value': _total_metric_value
            })

        _summary_df = pd.DataFrame(_project_summary)

        # Format for display (no currency prefix since metrics are mixed)
        _summary_df['Total Funding (OP)'] = _summary_df['Total Funding (OP)'].apply(lambda x: f"{x:,.0f}")
        _summary_df['Total Metric Value'] = _summary_df['Total Metric Value'].apply(
            lambda x: f"{x/1e6:.1f}M" if x >= 1e6 else f"{x/1e3:.0f}K" if x >= 1e3 else f"{x:.0f}"
        )

        # Chain-level totals
        _total_chain_funding = _chain_grants['amount'].sum()
        _total_chain_metric = _chain_metrics['amount'].sum()

        # Format chain metric (mixed units so no currency prefix)
        if _total_chain_metric >= 1e6:
            _chain_metric_str = f"{_total_chain_metric/1e6:.1f}M"
        else:
            _chain_metric_str = f"{_total_chain_metric/1e3:.0f}K"

        mo.vstack([
            mo.md(f"### {chain_selector.value}"),
            mo.hstack([
                mo.md(f"""
                <div style="padding: 16px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
                <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Total Funding on Chain</div>
                <div style="font-size: 24px; font-weight: 700;">{_total_chain_funding:,.0f} OP</div>
                </div>
                """),
                mo.md(f"""
                <div style="padding: 16px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
                <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Aggregate Activity</div>
                <div style="font-size: 24px; font-weight: 700;">{_chain_metric_str}</div>
                </div>
                """)
            ], widths="equal"),
            mo.md("#### Projects on Chain"),
            mo.ui.table(_summary_df, label=f"Projects on {chain_selector.value}")
        ])
    else:
        mo.md("Please select a chain to view analysis.")
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    """Load grants data with project mapping"""
    df_grants = mo.sql(
        f"""
        SELECT
            g.funding_date,
            g.application_name,
            g.oso_project_slug,
            g.amount,
            g.grant_type,
            g.grants_season_or_mission,
            pc.oso_project_id,
            pc.oso_project_name
        FROM optimism.grants.grants_consolidated g
        LEFT JOIN optimism.grants.projects_catalog pc
            ON g.oso_project_slug = pc.oso_project_slug
        ORDER BY g.funding_date
        """,
        output=False,
        engine=pyoso_db_conn
    )

    # Convert funding_date to datetime
    import pandas as pd
    df_grants['funding_date'] = pd.to_datetime(df_grants['funding_date'])

    return (df_grants,)


@app.cell(hide_code=True)
def _(mo, pd, pyoso_db_conn):
    """Load monthly metrics data"""
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

    return (df_metrics_catalog, df_projects_catalog)


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

    return (CHAIN_COLORS, PROJECT_COLORS)


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

    return get_chain_color, get_stacked_area_layout, stringify


@app.cell(hide_code=True)
def _():
    import plotly.express as px
    import plotly.graph_objects as go
    return go, px


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
