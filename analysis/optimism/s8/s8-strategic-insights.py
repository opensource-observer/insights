import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # S8 Grants Council - TVL Intent - Observational Impact Analysis
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-16</span></small>

    This report provides transparency into the S8 Grants Council program performance, measuring TVL and (soon) revenue impact for grant recipients.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Part 1: Program Overview""")
    return


@app.cell(hide_code=True)
def _(df_grants, df_project_metrics, mo, pd):
    # Calculate program overview stats from ALL grants (not just those with TVL)
    _total_count = len(df_grants)
    _total_op_approved = df_grants['op_total_amount'].sum()
    _projects_with_deliveries = (df_grants['op_delivered'] > 0).sum()
    _total_op_delivered = df_grants['op_delivered'].sum()
    if _total_op_approved >= 1_000_000:
        _op_approved_str = f"{_total_op_approved/1e6:.1f}M"
    else:
        _op_approved_str = f"{_total_op_approved/1e3:.0f}K"

    if _total_op_delivered >= 1_000_000:
        _op_delivered_str = f"{_total_op_delivered/1e6:.1f}M"
    else:
        _op_delivered_str = f"{_total_op_delivered/1e3:.0f}K"

    overview_headline = f"{_total_count} projects approved for a total of {_op_approved_str} OP, of which {_projects_with_deliveries} have received first deliveries totaling {_op_delivered_str} OP"

    _card_total_projects = mo.md(f"""
    <div style="padding: 16px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Total Projects</div>
    <div style="font-size: 24px; font-weight: 700; margin-bottom: 4px;">{_total_count}</div>
    <div style="font-size: 11px; color: #888;">Approved for funding</div>
    </div>
    """)

    _card_total_approved = mo.md(f"""
    <div style="padding: 16px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Total OP Approved</div>
    <div style="font-size: 24px; font-weight: 700; margin-bottom: 4px;">{_op_approved_str}</div>
    <div style="font-size: 11px; color: #888;">Across all projects</div>
    </div>
    """)

    _card_delivered_projects = mo.md(f"""
    <div style="padding: 16px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Projects with Deliveries</div>
    <div style="font-size: 24px; font-weight: 700; margin-bottom: 4px;">{_projects_with_deliveries}</div>
    <div style="font-size: 11px; color: #888;">Received first payment</div>
    </div>
    """)

    _card_total_delivered = mo.md(f"""
    <div style="padding: 16px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Total OP Delivered</div>
    <div style="font-size: 24px; font-weight: 700; margin-bottom: 4px;">{_op_delivered_str}</div>
    <div style="font-size: 11px; color: #888;">Paid to date</div>
    </div>
    """)

    _df_table = df_grants[['title', 'karma_page', 'oso_project_artifacts', 'op_total_amount', 'op_delivered', 'status', 'chains']].copy()

    # Left join with TVL data where available
    if not df_project_metrics.empty:
        _tvl_lookup = df_project_metrics.set_index('title')['current_tvl'].to_dict()
    else:
        _tvl_lookup = {}

    _df_table['current_tvl'] = _df_table['title'].map(_tvl_lookup)

    _df_table['Grant Size (OP)'] = _df_table['op_total_amount'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
    _df_table['OP Delivered'] = _df_table['op_delivered'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else "0")
    _df_table['Current TVL'] = _df_table['current_tvl'].apply(lambda x: f"${x/1e6:,.1f}M" if pd.notna(x) and x > 0 else "—")
    _df_table['Chains'] = _df_table['chains'].apply(lambda x: ", ".join(x) if isinstance(x, list) else (x if pd.notna(x) else "—"))
    _display_df = _df_table[[
        'title', 'karma_page', 'oso_project_artifacts', 'Grant Size (OP)', 'OP Delivered', 'status', 'Chains', 'Current TVL'
    ]].copy()
    _display_df.columns = ['Project', 'Karma Link', 'OSO Link', 'Grant Size (OP)', 'OP Delivered', 'Status', 'Targeted Chains', 'Current TVL']
    _display_df = _display_df.sort_values('Project')

    _table = mo.ui.table(
        data=_display_df.reset_index(drop=True),
        show_column_summaries=False,
        show_data_types=False,
        page_size=50
    )

    mo.vstack([
        mo.md(f"### **{overview_headline}**"),
        mo.hstack([
            _card_total_projects,
            _card_total_approved,
            _card_delivered_projects,
            _card_total_delivered
        ], widths="equal", gap=1),
        mo.md("#### Project Details"),
        _table
    ], gap=1.5)
    return


@app.cell(hide_code=True)
def _(df_project_metrics, mo):
    _total_tvl_delta = df_project_metrics['tvl_delta'].sum()
    _total_op_delivered = df_project_metrics['op_delivered'].sum()
    _avg_roi = _total_tvl_delta / _total_op_delivered if _total_op_delivered > 0 else 0
    _positive_count = (df_project_metrics['tvl_delta'] > 0).sum()
    _total_count = len(df_project_metrics)
    if abs(_total_tvl_delta) >= 1_000_000:
        _tvl_str = f"${_total_tvl_delta/1e6:,.1f}M"
    else:
        _tvl_str = f"${_total_tvl_delta/1e3:,.0f}K"

    headline_1 = f"S8 grants have {_tvl_str} in overall TVL change (before applying any adjustments)"

    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_1}**

        The program has deployed **{_total_op_delivered:,.0f} OP** across **{_total_count} projects** with TVL available on Defillama.
        """),
    ])
    return


@app.cell(hide_code=True)
def _(
    PRIMARY_METRIC,
    PROJECT_COLORS,
    all_projects,
    df_metrics,
    get_stacked_area_layout,
    go,
    mo,
):
    # Metric Over Time by Project (Stacked Area)
    _df_metric = df_metrics[
        (df_metrics['metric_display_name'] == PRIMARY_METRIC) &
        (df_metrics['project_title'].isin(all_projects))
    ].copy()

    # Aggregate by date and project
    _df_agg = _df_metric.groupby(['sample_date', 'project_title'], as_index=False)['amount'].sum()

    # Get top projects by total value for coloring
    _project_totals = _df_agg.groupby('project_title')['amount'].sum().sort_values(ascending=False)
    _top_projects = _project_totals.head(20).index.tolist()

    _fig = go.Figure()
    for _i, _project in enumerate(_top_projects):
        _proj_data = _df_agg[_df_agg['project_title'] == _project].sort_values('sample_date')
        _color = PROJECT_COLORS[_i % len(PROJECT_COLORS)]
        _fig.add_trace(go.Scatter(
            x=_proj_data['sample_date'],
            y=_proj_data['amount'],
            mode='lines',
            name=_project,
            stackgroup='metric',
            line=dict(width=0.5, color=_color),
            fillcolor=_color
        ))

    _fig.update_layout(**get_stacked_area_layout(y_title='TVL ($)'))

    mo.vstack([
        mo.md(f"#### {PRIMARY_METRIC} by Project"),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return


@app.cell(hide_code=True)
def _(
    PRIMARY_METRIC,
    all_projects,
    df_metrics,
    get_chain_color,
    get_stacked_area_layout,
    go,
    mo,
):
    # Metric Over Time by Chain (Stacked Area)
    _df_metric = df_metrics[
        (df_metrics['metric_display_name'] == PRIMARY_METRIC) &
        (df_metrics['project_title'].isin(all_projects))
    ].copy()

    # Aggregate by date and chain
    _df_agg = _df_metric.groupby(['sample_date', 'chain'], as_index=False)['amount'].sum()

    # Get chains sorted by total value
    _chain_totals = _df_agg.groupby('chain')['amount'].sum().sort_values(ascending=False)
    _chains = _chain_totals.index.tolist()

    _fig = go.Figure()
    for _i, _chain in enumerate(_chains):
        _chain_data = _df_agg[_df_agg['chain'] == _chain].sort_values('sample_date')
        _color = get_chain_color(_chain, _i)

        _fig.add_trace(go.Scatter(
            x=_chain_data['sample_date'],
            y=_chain_data['amount'],
            mode='lines',
            name=_chain,
            stackgroup='metric',
            line=dict(width=0.5, color=_color),
            fillcolor=_color
        ))

    _fig.update_layout(**get_stacked_area_layout(y_title='TVL ($)', right_margin=120))

    mo.vstack([
        mo.md(f"#### {PRIMARY_METRIC} by Chain"),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_project_metrics, go, mo):
    # Calculate positive/negative split and ROI distribution
    _positive = df_project_metrics[df_project_metrics['tvl_delta'] > 0]
    _negative = df_project_metrics[df_project_metrics['tvl_delta'] <= 0]
    _positive_count = len(_positive)
    _negative_count = len(_negative)
    _total = len(df_project_metrics)

    # Best and worst ROI
    _best_roi_proj = df_project_metrics.loc[df_project_metrics['roi'].idxmax()] if not df_project_metrics.empty else None
    _worst_roi_proj = df_project_metrics.loc[df_project_metrics['roi'].idxmin()] if not df_project_metrics.empty else None

    headline_5 = f"{_positive_count} of {_total} projects show positive TVL growth since receiving grants"

    # Create ROI bar chart with positive/negative coloring
    _df_roi = df_project_metrics[['title', 'roi']].copy()
    _df_roi = _df_roi.sort_values('roi', ascending=True)
    _df_roi['color'] = _df_roi['roi'].apply(lambda x: '#00D395' if x > 0 else '#FF0420')

    _fig = go.Figure()
    _fig.add_trace(go.Bar(
        x=_df_roi['roi'],
        y=_df_roi['title'],
        orientation='h',
        marker_color=_df_roi['color']
    ))
    _layout = PLOTLY_LAYOUT.copy()
    _layout['xaxis'] = dict(title="", showgrid=False, linecolor="#000", linewidth=1, ticks="outside", tickformat='$,.0s', zeroline=True, zerolinecolor='black', zerolinewidth=1)
    _layout['yaxis'] = dict(title="", showgrid=False, linecolor="#000", linewidth=1)
    _fig.update_layout(**_layout)

    mo.vstack([
        mo.md(f"""
        ---
        ### **{headline_5}**
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ---
    ## Part 2: Project Deep Dives

    Each section below shows individual project performance, measured from their OP delivery date.
    """
    )
    return


@app.cell(hide_code=True)
def _(
    PROGRAM_END_DATE,
    PROGRAM_START_DATE,
    df_metrics,
    df_project_metrics_with_tvl,
    get_chain_color,
    get_stacked_area_layout,
    go,
    mo,
    pd,
):
    _sections = []
    _df_sorted = df_project_metrics_with_tvl.sort_values('roi', ascending=False)
    _end_date_str = PROGRAM_END_DATE

    for _, _row in _df_sorted.iterrows():
        _project = _row['project']
        _title = _row['title']
        _delivery_date = _row['delivery_date']
        _op_delivered = _row['op_delivered']
        _op_total = _row['op_total']
        _status = _row['status']
        _baseline_tvl = _row['baseline_tvl']
        _current_tvl = _row['current_tvl']
        _tvl_delta = _row['tvl_delta']
        _roi = _row['roi']
        _chains = _row['chains']
        _karma_page = _row['karma_page']
        _oso_artifacts = _row['oso_project_artifacts']

        # Format OP total for display (e.g., 500K, 1.2M)
        if _op_total >= 1_000_000:
            _op_total_str = f"{_op_total/1e6:.1f}M"
        elif _op_total >= 1_000:
            _op_total_str = f"{_op_total/1e3:.0f}K"
        else:
            _op_total_str = f"{_op_total:,.0f}"

        # Format OP delivered for display
        if _op_delivered >= 1_000_000:
            _op_delivered_str = f"{_op_delivered/1e6:.1f}M"
        elif _op_delivered >= 1_000:
            _op_delivered_str = f"{_op_delivered/1e3:.0f}K"
        elif pd.isna(_op_delivered):
            _op_delivered_str = "0"
        else:
            _op_delivered_str = f"{_op_delivered:,.0f}"

        if isinstance(_chains, list):
            _chains_str = ", ".join(_chains)
        elif isinstance(_chains, str) and _chains:
            _chains_str = _chains
        else:
            _chains_str = "—"

        # Use delivery date for baseline, or default to program start
        _baseline_date = _delivery_date if pd.notna(_delivery_date) else pd.to_datetime(PROGRAM_START_DATE)
        _baseline_str = _baseline_date.strftime('%Y-%m-%d')

        # Calculate days between baseline and current
        _current_date = pd.to_datetime(PROGRAM_END_DATE)
        _days_elapsed = (_current_date - _baseline_date).days

        # Attribution (currently 100% for all projects)
        _attribution_pct = 100
        _attribution_desc = f"**Attribution: {_attribution_pct}%** · Assumes all TVL change is due to the grant (no co-incentive adjustment)"

        _baseline_card = mo.md(f"""
    <div style="padding: 12px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Baseline TVL</div>
    <div style="font-size: 18px; font-weight: 600; margin-bottom: 4px;">${_baseline_tvl/1e6:,.1f}M</div>
    <div style="font-size: 11px; color: #888;">{_baseline_str}</div>
    </div>
    """)

        _current_card = mo.md(f"""
    <div style="padding: 12px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Current TVL</div>
    <div style="font-size: 18px; font-weight: 600; margin-bottom: 4px;">${_current_tvl/1e6:,.1f}M</div>
    <div style="font-size: 11px; color: #888;">{_end_date_str}</div>
    </div>
    """)

        _change_color = "#00D395" if _tvl_delta > 0 else "#FF0420"
        _change_symbol = "+" if _tvl_delta >= 0 else ""
        _change_card = mo.md(f"""
    <div style="padding: 12px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">TVL Change</div>
    <div style="font-size: 18px; font-weight: 600; color: {_change_color}; margin-bottom: 4px;">{_change_symbol}${_tvl_delta/1e6:,.1f}M</div>
    <div style="font-size: 11px; color: #888;">over {_days_elapsed} days</div>
    </div>
    """)

        _roi_color = "#00D395" if _roi > 0 else "#FF0420"
        _roi_symbol = "+" if _roi >= 0 else ""
        _roi_card = mo.md(f"""
    <div style="padding: 12px; border: 2px solid {_roi_color}; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">ROI ($/OP)</div>
    <div style="font-size: 20px; font-weight: 700; color: {_roi_color}; margin-bottom: 4px;">{_roi_symbol}${_roi:,.0f}</div>
    <div style="font-size: 11px; color: #888;">TVL per OP delivered</div>
    </div>
    """)

        _proj_tvl = df_metrics[
            (df_metrics['project_title'] == _project) &
            (df_metrics['metric_display_name'] == 'Defillama TVL')
        ].copy()

        if not _proj_tvl.empty:
            _proj_tvl = _proj_tvl.sort_values(['sample_date', 'chain'])
            _chart_chains = _proj_tvl['chain'].unique()

            _fig = go.Figure()

            for _i, _chain in enumerate(_chart_chains):
                _chain_data = _proj_tvl[_proj_tvl['chain'] == _chain].sort_values('sample_date')
                _color = get_chain_color(_chain, _i)

                _fig.add_trace(go.Scatter(
                    x=_chain_data['sample_date'],
                    y=_chain_data['amount'],
                    mode='lines',
                    name=_chain,
                    stackgroup='tvl',
                    line=dict(width=0.5, color=_color),
                    fillcolor=_color,
                    showlegend=True
                ))

            # Add vertical line at delivery date with annotation
            if pd.notna(_delivery_date):
                _fig.add_shape(
                    type="line",
                    x0=_delivery_date.to_pydatetime(),
                    x1=_delivery_date.to_pydatetime(),
                    y0=0,
                    y1=1,
                    yref="paper",
                    line=dict(color="#666", dash="dash", width=2)
                )

                # Add annotation label for delivery date
                _fig.add_annotation(
                    x=_delivery_date.to_pydatetime(),
                    y=1,
                    yref="paper",
                    text="Grant Delivery",
                    showarrow=False,
                    yshift=10,
                    font=dict(size=10, color="#666"),
                    bgcolor="white",
                    bordercolor="#666",
                    borderwidth=1,
                    borderpad=4
                )

            _layout = get_stacked_area_layout(y_title='TVL ($)', right_margin=100)
            _layout['height'] = 280
            _layout['showlegend'] = True
            _fig.update_layout(**_layout)

            _chart_element = mo.ui.plotly(_fig, config={'displayModeBar': False})
        else:
            _chart_element = mo.md("*No TVL data available*")

        # Build section with vertical flow
        _section = mo.vstack([
            mo.md(f"""
    ---
    ### {_title}
    [View Karma Application]({_karma_page}) | [View OSO Project Definition]({_oso_artifacts})<br>
    **Grant Size:** {_op_total_str} OP · **OP Delivered:** {_op_delivered_str} OP · **Status:** {_status} · **Targeted Chains:** {_chains_str}
    """),
            mo.hstack([
                _baseline_card,
                _current_card,
                _change_card,
                _roi_card
            ], widths="equal", gap=1),
            _chart_element,
            mo.md(f"<small style='color: #666;'>{_attribution_desc}</small>")
        ], gap=0.8)

        _sections.append(_section)

    mo.vstack(_sections)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ---
    ## Methodology

    ### Data Collection
    - Key assumptions tracked in this [Google Sheet](https://docs.google.com/spreadsheets/d/1E8Cz_3SFhxrrMEiNMI4yChgM6DfwtSRKVCXPGf7xf_U/edit?usp=sharing)
    - Project data comes from Karma
    - OSO project files include Defillama adapters and Superchain addresses linked to projects
    - Defillama data is currently fetched on a weekly basis

    ### Baseline Calculation
    - Each project's baseline is calculated using the 7-day average TVL centered around their OP delivery date
    - Current values use the most recent 7-day average
    - TVL Delta = Current TVL - Baseline TVL

    ### ROI Calculation
    The primary metric for evaluating grant effectiveness is **ROI (Return on Investment)**:

    $$
    \text{ROI} = \frac{\text{TVL Delta}}{\text{OP Delivered}}
    $$

    This measures the dollar value of TVL change attributable to each unit of OP distributed.

    ### Metrics
    - **TVL**: Total Value Locked from DefiLlama via OSO pipeline
    - **Transaction Fees**: Transaction fees on Superchain networks (ETH)
    - **ROI**: TVL change per OP token delivered ($/OP)

    ### Limitations
    - Attribution assumes 100% of TVL change is due to the grant (no co-incentive adjustment in this view)
    - Some projects may have incomplete data coverage
    - Market conditions not isolated
    - OP token price fluctuations not accounted for
    """
    )
    return


@app.cell(hide_code=True)
def _():
    # Configuration constants
    ANALYSIS_START_DATE = "2025-09-01"
    ANALYSIS_END_DATE = "2026-03-01"
    MIN_TVL_THRESHOLD = 1
    TRAILING_DAYS = 7

    # Primary metric to use throughout the report (can be changed to "User Operations" etc.)
    PRIMARY_METRIC = "Defillama TVL"

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
    return (
        ANALYSIS_END_DATE,
        ANALYSIS_START_DATE,
        CHAIN_COLORS,
        MIN_TVL_THRESHOLD,
        PRIMARY_METRIC,
        PROJECT_COLORS,
    )


@app.cell(hide_code=True)
def _():
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
    # Helper functions

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

    stringify = lambda arr: "'" + "','".join(arr) + "'"
    return get_chain_color, get_stacked_area_layout


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    # Load grant metadata from optimism.grants
    df_grants_raw = mo.sql(
        f"""
        SELECT
          p.title,
          abp.status,
          abp.op_total_amount,
          abp.op_delivered,
          abp.initial_delivery_date,
          abp.chains,
          ARRAY_JOIN(ARRAY_SORT(abp.defillama_adapters), ',') AS defillama_adapters,
          p.oso_project_name AS oso_project_slug,
          'https://gap.karmahq.xyz/project/' || p.slug AS karma_page,
          'https://github.com/opensource-observer/oss-directory/tree/main/data/projects/' || SUBSTR(p.oso_project_name, 1, 1) || '/' || p.oso_project_name || '.yaml' AS oso_project_artifacts
        FROM optimism.grants.s8_artifacts_by_project AS abp
        JOIN oso_community.karma.projects AS p
          ON abp.project_name = p.title
        WHERE
          abp.op_total_amount > 0
          AND p.title NOT LIKE '%TEST%'
        ORDER BY UPPER(p.title)
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_grants_raw,)


@app.cell(hide_code=True)
def _(ANALYSIS_END_DATE, ANALYSIS_START_DATE, mo, pyoso_db_conn):
    # Load metrics from oso_community.karma
    df_metrics_raw = mo.sql(
        f"""
        SELECT
            sample_date,
            project_title,
            metric_display_name,
            chain,
            amount
        FROM oso_community.karma.timeseries_metrics_by_project
        WHERE sample_date BETWEEN DATE('{ANALYSIS_START_DATE}') AND DATE('{ANALYSIS_END_DATE}')
        ORDER BY sample_date, project_title
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_metrics_raw,)


@app.cell(hide_code=True)
def _(df_grants_raw, df_metrics_raw, pd):
    # Process grants data
    df_grants = df_grants_raw.copy()
    df_grants['initial_delivery_date'] = pd.to_datetime(df_grants['initial_delivery_date'])
    df_grants.columns = [c.lower().replace(' ', '_') for c in df_grants.columns]

    # Process metrics data
    df_metrics_unfiltered = df_metrics_raw.copy()
    df_metrics_unfiltered['sample_date'] = pd.to_datetime(df_metrics_unfiltered['sample_date'])
    df_metrics_unfiltered.columns = [c.lower().replace(' ', '_') for c in df_metrics_unfiltered.columns]

    # Chain name normalization mapping (Superchain networks only)
    # Valid chains: Base, Bob, Ink, Lisk, Mode, OP Mainnet, Soneium, Swell, Unichain, Worldchain
    CHAIN_NAME_ALIASES = {
        'op mainnet': ['op mainnet', 'optimism', 'op'],
        'optimism': ['op mainnet', 'optimism', 'op'],
        'base': ['base'],
        'bob': ['bob'],
        'ink': ['ink'],
        'lisk': ['lisk'],
        'mode': ['mode'],
        'soneium': ['soneium'],
        'swell': ['swell', 'swellchain'],
        'swellchain': ['swell', 'swellchain'],
        'unichain': ['unichain'],
        'worldchain': ['worldchain', 'world chain'],
    }

    def normalize_chain(chain_name):
        """Return a set of possible chain name variations."""
        if not chain_name:
            return set()
        lower = chain_name.lower().strip()
        # Check if we have explicit aliases
        if lower in CHAIN_NAME_ALIASES:
            return set(CHAIN_NAME_ALIASES[lower])
        # Otherwise return the lowercase version and without spaces
        return {lower, lower.replace(' ', '')}

    # Build project -> allowed chains mapping from grants data
    # The 'chains' column contains the chains targeted by each grant
    # Key by 'title' since that's what matches 'project_title' in metrics
    project_chain_map = {}
    for _, row in df_grants.iterrows():
        project_title = row.get('title')
        chains = row.get('chains')
        if pd.notna(project_title) and chains is not None:
            # Handle both list and string formats
            if isinstance(chains, list):
                chain_list = chains
            elif isinstance(chains, str):
                chain_list = [c.strip() for c in chains.split(',') if c.strip()]
            else:
                chain_list = []
            # Build normalized set of all acceptable chain names
            allowed = set()
            for c in chain_list:
                allowed.update(normalize_chain(c))
            project_chain_map[project_title] = allowed

    # Filter metrics to only include (project, chain) combinations from grants
    def is_valid_project_chain(row):
        project = row['project_title']
        chain = row['chain']
        if project not in project_chain_map:
            return False
        allowed_chains = project_chain_map[project]
        chain_lower = chain.lower().strip() if chain else ''
        return chain_lower in allowed_chains or chain_lower.replace(' ', '') in allowed_chains

    df_metrics = df_metrics_unfiltered[
        df_metrics_unfiltered.apply(is_valid_project_chain, axis=1)
    ].copy()
    return df_grants, df_metrics


@app.cell(hide_code=True)
def _(MIN_TVL_THRESHOLD, df_metrics):
    # Build project lists from latest TVL snapshots
    df_tvl = df_metrics[df_metrics['metric_display_name'] == 'Defillama TVL'].copy()

    # Get latest TVL per project
    latest_tvl = (
        df_tvl
        .groupby('project_title')
        .apply(lambda x: x.loc[x['sample_date'].idxmax(), 'amount'], include_groups=False)
        .reset_index()
    )
    latest_tvl.columns = ['project_title', 'latest_tvl']

    all_projects = latest_tvl['project_title'].tolist()
    qualified_projects = latest_tvl[latest_tvl['latest_tvl'] > MIN_TVL_THRESHOLD]['project_title'].tolist()
    return (all_projects,)


@app.cell(hide_code=True)
def _(df_grants, df_metrics):
    # Calculate program dates from data
    _delivery_dates = df_grants['initial_delivery_date'].dropna()

    PROGRAM_START_DATE = _delivery_dates.min().strftime('%Y-%m-%d') if len(_delivery_dates) > 0 else "2025-06-01"
    PROGRAM_END_DATE = df_metrics['sample_date'].max().strftime('%Y-%m-%d')
    total_projects = len(df_grants)
    return PROGRAM_END_DATE, PROGRAM_START_DATE


@app.cell(hide_code=True)
def _(
    MIN_TVL_THRESHOLD,
    PROGRAM_START_DATE,
    all_projects,
    df_grants,
    df_metrics,
    pd,
):
    # Calculate ROI metrics for each project
    # Baseline = TVL at delivery date, Current = latest TVL, ROI = Delta / OP delivered

    _df_tvl_all = df_metrics[df_metrics['metric_display_name'] == 'Defillama TVL'].copy()
    _df_userops_all = df_metrics[df_metrics['metric_display_name'] == 'User Operations'].copy()

    _project_metrics = []

    for _project in all_projects:
        # Get grant info for this project
        _grant_info = df_grants[df_grants['oso_project_slug'] == _project]
        if _grant_info.empty:
            # Try matching on title
            _grant_info = df_grants[df_grants['title'].str.lower() == _project.lower()]

        if _grant_info.empty:
            continue

        _grant_row = _grant_info.iloc[0]
        _delivery_date = _grant_row.get('initial_delivery_date')
        _op_delivered = _grant_row.get('op_delivered', 0) or 0
        _op_total = _grant_row.get('op_total_amount', 0) or 0

        # Get TVL data for this project
        _proj_tvl = _df_tvl_all[_df_tvl_all['project_title'] == _project].copy()
        if _proj_tvl.empty:
            continue

        # Calculate baseline TVL (7-day avg around delivery date, or program start if no delivery date)
        if pd.notna(_delivery_date):
            _baseline_date = _delivery_date
        else:
            _baseline_date = pd.to_datetime(PROGRAM_START_DATE)

        _baseline_window = _proj_tvl[
            (_proj_tvl['sample_date'] >= _baseline_date - pd.Timedelta(days=3)) &
            (_proj_tvl['sample_date'] <= _baseline_date + pd.Timedelta(days=3))
        ]
        _baseline_tvl = _baseline_window['amount'].mean() if not _baseline_window.empty else 0

        # Calculate current TVL (latest 7-day avg)
        _latest_date = _proj_tvl['sample_date'].max()
        _current_window = _proj_tvl[
            _proj_tvl['sample_date'] >= _latest_date - pd.Timedelta(days=7)
        ]
        _current_tvl = _current_window['amount'].mean() if not _current_window.empty else 0

        # Calculate delta and ROI
        _tvl_delta = _current_tvl - _baseline_tvl
        _roi = _tvl_delta / _op_delivered if _op_delivered > 0 else 0

        # Get user ops data
        _proj_userops = _df_userops_all[_df_userops_all['project_title'] == _project]
        _total_userops = _proj_userops['amount'].sum() if not _proj_userops.empty else 0

        _project_metrics.append({
            'project': _project,
            'title': _grant_row.get('title', _project),
            'delivery_date': _delivery_date,
            'op_delivered': _op_delivered,
            'op_total': _op_total,
            'status': _grant_row.get('status', ''),
            'baseline_tvl': _baseline_tvl,
            'current_tvl': _current_tvl,
            'tvl_delta': _tvl_delta,
            'roi': _roi,  # TVL $ per OP
            'total_userops': _total_userops,
            'chains': _grant_row.get('chains', ''),
            'karma_page': _grant_row.get('karma_page', ''),
            'oso_project_artifacts': _grant_row.get('oso_project_artifacts', ''),
            'defillama_adapters': _grant_row.get('defillama_adapters', '')
        })

    df_project_metrics = pd.DataFrame(_project_metrics)
    if df_project_metrics.empty:
        df_project_metrics_with_tvl = df_project_metrics.copy()
    else:
        df_project_metrics_with_tvl = df_project_metrics[df_project_metrics['current_tvl'] > MIN_TVL_THRESHOLD].copy()
    return df_project_metrics, df_project_metrics_with_tvl


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    return go, pd


@app.cell(hide_code=True)
def setup_pyoso():
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
