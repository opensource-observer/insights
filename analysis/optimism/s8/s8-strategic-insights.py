import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # S8 Grants Council - TVL Intent - Observational Impact Analysis
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-21</span></small>

    This report provides transparency into the S8 Grants Council program performance, measuring TVL and (soon) revenue impact for grant recipients.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Part 1: Program Overview
    """)
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
    mo.md(r"""
    ---
    ## Part 2: Project Deep Dives

    Each section below shows individual project performance, measured from their OP delivery date.
    """)
    return


@app.cell(hide_code=True)
def _(
    PROGRAM_END_DATE,
    PROGRAM_START_DATE,
    df_metrics,
    df_op_balance_daily,
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
        _first_inflow_date = _row.get('first_inflow_date', None)
        _project_baseline_date = _row.get('project_baseline_date', _delivery_date)
        _baseline_date_source = _row.get('baseline_date_source', 'delivery_date')
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
        _l2_address = _row.get('l2_address', None)
        _est_op_balance = _row.get('est_op_balance', None)

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

        # Format Est OP Balance for display (show 0 if balance is zero)
        if pd.notna(_est_op_balance):
            if _est_op_balance >= 1_000_000:
                _est_op_balance_str = f"{_est_op_balance/1e6:.1f}M"
            elif _est_op_balance >= 1_000:
                _est_op_balance_str = f"{_est_op_balance/1e3:.0f}K"
            elif _est_op_balance > 0:
                _est_op_balance_str = f"{_est_op_balance:,.0f}"
            else:
                _est_op_balance_str = "0"
        else:
            _est_op_balance_str = None

        if isinstance(_chains, list):
            _chains_str = ", ".join(_chains)
        elif isinstance(_chains, str) and _chains:
            _chains_str = _chains
        else:
            _chains_str = "—"

        # Use project_baseline_date (already calculated as MIN of delivery/inflow dates)
        _baseline_date = _project_baseline_date if pd.notna(_project_baseline_date) else pd.to_datetime(PROGRAM_START_DATE)
        _baseline_str = _baseline_date.strftime('%Y-%m-%d')

        # Calculate days between baseline and current
        _current_date = pd.to_datetime(PROGRAM_END_DATE)
        _days_elapsed = (_current_date - _baseline_date).days

        # Build baseline date footnote showing how it was derived
        if _baseline_date_source == 'first_inflow':
            _delivery_str = _delivery_date.strftime('%Y-%m-%d') if pd.notna(_delivery_date) else 'N/A'
            _inflow_str = _first_inflow_date.strftime('%Y-%m-%d') if pd.notna(_first_inflow_date) else 'N/A'
            _baseline_footnote = f"Baseline date: {_baseline_str} (first token inflow, earlier than delivery date {_delivery_str})"
        elif _baseline_date_source == 'delivery_date':
            _inflow_str = _first_inflow_date.strftime('%Y-%m-%d') if pd.notna(_first_inflow_date) else 'N/A'
            if pd.notna(_first_inflow_date):
                _baseline_footnote = f"Baseline date: {_baseline_str} (delivery date, earlier than first inflow {_inflow_str})"
            else:
                _baseline_footnote = f"Baseline date: {_baseline_str} (delivery date, no token inflow data available)"
        elif _baseline_date_source == 'undelivered':
            _baseline_footnote = f"Baseline date: {_baseline_str} (not yet delivered)"
        else:
            _baseline_footnote = f"Baseline date: {_baseline_str} (program start, no delivery or inflow data available)"


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

        # Get attribution percentage for adjusted ROI calculation
        _attribution_pct = _row.get('calculated_attribution_pct', 1.0)
        _calculated_formula = _row.get('calculated_formula', '')
        _scope_pct = _row.get('scope_pct', 1.0)
        _coincentives_usd = _row.get('coincentives_usd', 0.0)
        _attribution_cap_applied = _row.get('attribution_cap_applied', False)

        # Calculate adjusted ROI = unadjusted ROI * attribution percentage
        _adjusted_roi = _roi * _attribution_pct

        _roi_color = "#00D395" if _adjusted_roi > 0 else "#FF0420"
        _roi_symbol = "+" if _adjusted_roi >= 0 else ""
        _unadjusted_symbol = "+" if _roi >= 0 else ""
        _roi_card = mo.md(f"""
    <div style="padding: 12px; border: 2px solid {_roi_color}; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">ROI (TVL change per OP)</div>
    <div style="font-size: 20px; font-weight: 700; color: {_roi_color}; margin-bottom: 4px;">{_roi_symbol}${_adjusted_roi:,.0f}</div>
    <div style="font-size: 11px; color: #888;">Adjusted for {_attribution_pct:.0%} attribution</div>
    <div style="font-size: 10px; color: #aaa; margin-top: 4px;">Unadjusted: {_unadjusted_symbol}${_roi:,.0f}/OP</div>
    </div>
    """)

        # Build attribution description with full formula breakdown
        # Format formula as multi-line HTML for the footnote
        if _calculated_formula:
            # Convert newlines to HTML breaks for display
            _formula_html = _calculated_formula.replace('\n', '<br>')
            _attribution_desc = f"""**Attribution: {_attribution_pct:.0%}**
<details style="margin-top: 4px;">
<summary style="cursor: pointer; color: #888; font-size: 11px;">Show calculation details</summary>
<div style="margin-top: 6px; padding: 8px; background: #f5f5f5; border-radius: 4px; font-family: monospace; font-size: 10px; line-height: 1.6;">
{_formula_html}
</div>
</details>"""
        else:
            # Fallback if no formula available
            _scope_pct_display = _scope_pct if pd.notna(_scope_pct) else 1.0
            _coincentives_display = f"${_coincentives_usd:,.0f}" if pd.notna(_coincentives_usd) and _coincentives_usd > 0 else "None"
            _cap_status = "Cap applied" if _attribution_cap_applied else "No cap"
            _attribution_desc = f"**Attribution: {_attribution_pct:.0%}** · Scope: {_scope_pct_display:.0%} of TVL in scope · Co-incentives: {_coincentives_display} · {_cap_status}"

        _proj_tvl = df_metrics[
            (df_metrics['project_title'] == _project) &
            (df_metrics['metric_display_name'] == 'Defillama TVL')
        ].copy()

        # Get OP balance data for this project (keyed by title)
        _proj_balance = df_op_balance_daily[
            df_op_balance_daily['project_name'] == _title
        ].copy() if not df_op_balance_daily.empty else pd.DataFrame()

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
                    showlegend=True,
                    yaxis='y'
                ))

            # Add OP balance line on secondary Y axis (if data exists)
            if not _proj_balance.empty:
                _proj_balance = _proj_balance.sort_values('date')
                _fig.add_trace(go.Scatter(
                    x=_proj_balance['date'],
                    y=_proj_balance['op_balance'],
                    mode='lines',
                    name='OP Balance',
                    line=dict(width=3, color='black', shape='hvh'),
                    showlegend=True,
                    yaxis='y2'
                ))

            # Add vertical line at baseline date with annotation
            # Map baseline_date_source to display label
            _source_labels = {
                'first_inflow': 'first inflow',
                'delivery_date': 'delivery',
                'undelivered': 'not yet delivered',
                'program_start': 'program start'
            }
            _source_label = _source_labels.get(_baseline_date_source, _baseline_date_source)
            _baseline_annotation_text = f"Baseline Date ({_source_label})"

            if pd.notna(_baseline_date):
                _fig.add_shape(
                    type="line",
                    x0=_baseline_date.to_pydatetime(),
                    x1=_baseline_date.to_pydatetime(),
                    y0=0,
                    y1=1,
                    yref="paper",
                    line=dict(color="#666", dash="dash", width=2)
                )

                # Add annotation label for baseline date
                _fig.add_annotation(
                    x=_baseline_date.to_pydatetime(),
                    y=1,
                    yref="paper",
                    text=_baseline_annotation_text,
                    showarrow=False,
                    yshift=10,
                    font=dict(size=10, color="#666"),
                    bgcolor="white",
                    bordercolor="#666",
                    borderwidth=1,
                    borderpad=4
                )

            _layout = get_stacked_area_layout(y_title='TVL ($)', right_margin=40)
            _layout['height'] = 280
            _layout['showlegend'] = True
            # Move legend to top horizontal
            _layout['legend'] = dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='left',
                x=0,
                bgcolor='rgba(255,255,255,0.9)'
            )
            # Add secondary Y axis for OP balance (no ticks/labels, range starts at 0)
            _layout['yaxis2'] = dict(
                overlaying='y',
                side='right',
                showgrid=False,
                showticklabels=False,
                showline=False,
                zeroline=False,
                rangemode='tozero'
            )
            _fig.update_layout(**_layout)

            _chart_element = mo.ui.plotly(_fig, config={'displayModeBar': False})
        else:
            _chart_element = mo.md("*No TVL data available*")

        # Build links line with optional L2 address
        _links_parts = [
            f"[View Karma Application]({_karma_page})",
            f"[View OSO Project Definition]({_oso_artifacts})"
        ]
        if pd.notna(_l2_address) and _l2_address:
            _etherscan_url = f"https://optimistic.etherscan.io/address/{_l2_address}"
            _links_parts.append(f"[View L2 Address Activity]({_etherscan_url})")
        _links_str = " | ".join(_links_parts)

        # Build stats line with Status first (default to "Not Sent")
        _status_display = _status if _status else "Not Sent"
        _stats_parts = [
            f"**Status:** {_status_display}",
            f"**Grant Size:** {_op_total_str} OP",
            f"**OP Delivered:** {_op_delivered_str} OP"
        ]
        if _est_op_balance_str is not None:
            _stats_parts.append(f"**Est Balance:** {_est_op_balance_str} OP")
        _stats_str = " · ".join(_stats_parts)

        # Build section with vertical flow (Targeted Chains on separate line)
        _section = mo.vstack([
            mo.md(f"""
    ---
    ### {_title}
    {_links_str}<br>
    {_stats_str}<br>
    **Targeted Chains:** {_chains_str}
    """),
            mo.hstack([
                _baseline_card,
                _current_card,
                _change_card,
                _roi_card
            ], widths="equal", gap=1),
            _chart_element,
            mo.md(f"""<div style='color: #666; font-size: 12px;'>
{_baseline_footnote}
<div style='margin-top: 4px;'>{_attribution_desc}</div>
</div>""")
        ], gap=0.8)

        _sections.append(_section)

    mo.vstack(_sections)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Part 3: Summary

    This section provides a consolidated view of all projects with attribution-adjusted metrics.
    """)
    return


@app.cell(hide_code=True)
def _(OP_PRICE_USD, df_project_metrics_with_tvl, mo):
    # Part 3: Summary Stats
    # Program-level metrics with attribution

    if df_project_metrics_with_tvl.empty:
        _stats_output = mo.md("*No project data available for summary stats.*")
    else:
        # Calculate summary statistics
        _df = df_project_metrics_with_tvl.copy()

        # 1. Total OP Delivered
        _total_op_delivered = _df['op_delivered'].sum()
        if _total_op_delivered >= 1_000_000:
            _op_delivered_str = f"{_total_op_delivered/1e6:.1f}M"
        else:
            _op_delivered_str = f"{_total_op_delivered/1e3:.0f}K"

        # 2. Est. Coincentive Leverage = total coincentives / (total OP delivered * OP price)
        _total_coincentives = _df['coincentives_usd'].fillna(0).sum()
        _total_op_usd = _total_op_delivered * OP_PRICE_USD
        _coincentive_leverage = _total_coincentives / _total_op_usd if _total_op_usd > 0 else 0
        _leverage_str = f"{_coincentive_leverage:.1f}x"

        # 3. Attributable TVL Inflows = sum of (tvl_delta * attribution_pct) for positive deltas only
        _df['attributable_tvl'] = _df['tvl_delta'] * _df['calculated_attribution_pct']
        _positive_attributable = _df[_df['tvl_delta'] > 0]['attributable_tvl'].sum()
        if abs(_positive_attributable) >= 1_000_000:
            _attributable_tvl_str = f"${_positive_attributable/1e6:,.1f}M"
        else:
            _attributable_tvl_str = f"${_positive_attributable/1e3:,.0f}K"

        # 4. Attributable ROI = attributable_tvl_inflows / op_delivered
        _attributable_roi = _positive_attributable / _total_op_delivered if _total_op_delivered > 0 else 0
        _roi_color = "#00D395" if _attributable_roi > 0 else "#FF0420"
        _roi_symbol = "+" if _attributable_roi >= 0 else ""
        _attributable_roi_str = f"{_roi_symbol}${_attributable_roi:,.0f}/OP"

        # Build stat cards (consistent with Part 1 styling)
        _card_op_delivered = mo.md(f"""
    <div style="padding: 16px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">OP Delivered</div>
    <div style="font-size: 24px; font-weight: 700; margin-bottom: 4px;">{_op_delivered_str}</div>
    <div style="font-size: 11px; color: #888;">Total across all projects</div>
    </div>
    """)

        _card_leverage = mo.md(f"""
    <div style="padding: 16px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Est. Coincentive Leverage</div>
    <div style="font-size: 24px; font-weight: 700; margin-bottom: 4px;">{_leverage_str}</div>
    <div style="font-size: 11px; color: #888;">Co-incentives / OP grant value</div>
    </div>
    """)

        _card_attributable_tvl = mo.md(f"""
    <div style="padding: 16px; border: 1px solid #ddd; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Attributable TVL Inflows</div>
    <div style="font-size: 24px; font-weight: 700; margin-bottom: 4px;">{_attributable_tvl_str}</div>
    <div style="font-size: 11px; color: #888;">TVL gains × attribution %</div>
    </div>
    """)

        _card_attributable_roi = mo.md(f"""
    <div style="padding: 16px; border: 2px solid {_roi_color}; border-radius: 4px; background: #fafafa;">
    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 4px;">Attributable ROI</div>
    <div style="font-size: 24px; font-weight: 700; color: {_roi_color}; margin-bottom: 4px;">{_attributable_roi_str}</div>
    <div style="font-size: 11px; color: #888;">TVL inflows per OP delivered</div>
    </div>
    """)

        _stats_output = mo.hstack([
            _card_op_delivered,
            _card_leverage,
            _card_attributable_tvl,
            _card_attributable_roi
        ], widths="equal", gap=1)

    _stats_output
    return


@app.cell(hide_code=True)
def _(df_project_metrics_with_tvl, mo, pd):
    # Part 3: Summary Tables
    # Extended project details table and leaderboard

    if df_project_metrics_with_tvl.empty:
        _summary_output = mo.md("*No project data available for summary tables.*")
    else:
        # Calculate adjusted ROI for all projects
        _df_summary = df_project_metrics_with_tvl.copy()
        _df_summary['adjusted_roi'] = _df_summary['roi'] * _df_summary['calculated_attribution_pct']

        # Format columns for display
        _df_summary['Baseline Date'] = _df_summary['project_baseline_date'].apply(
            lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else '—'
        )
        _df_summary['Baseline TVL'] = _df_summary['baseline_tvl'].apply(
            lambda x: f"${x/1e6:,.2f}M" if pd.notna(x) and x > 0 else '—'
        )
        _df_summary['TVL Delta'] = _df_summary['tvl_delta'].apply(
            lambda x: f"+${x/1e6:,.2f}M" if x > 0 else f"-${abs(x)/1e6:,.2f}M" if x < 0 else "$0"
        )
        _df_summary['Attribution %'] = _df_summary['calculated_attribution_pct'].apply(
            lambda x: f"{x:.0%}" if pd.notna(x) else '—'
        )
        _df_summary['Adjusted ROI'] = _df_summary['adjusted_roi'].apply(
            lambda x: f"+${x:,.0f}/OP" if x > 0 else f"-${abs(x):,.0f}/OP" if x < 0 else "$0/OP"
        )

        # Extended project details table
        _extended_details = _df_summary[[
            'title', 'Baseline Date', 'Baseline TVL', 'TVL Delta', 'Attribution %', 'Adjusted ROI'
        ]].copy()
        _extended_details.columns = ['Project', 'Baseline Date', 'Baseline TVL', 'TVL Delta', 'Attribution %', 'Adjusted ROI']
        _extended_details = _extended_details.sort_values('Project')

        _details_table = mo.ui.table(
            data=_extended_details.reset_index(drop=True),
            show_column_summaries=False,
            show_data_types=False,
            page_size=50
        )

        # Leaderboard table sorted by adjusted ROI descending
        _leaderboard = _df_summary[[
            'title', 'op_delivered', 'tvl_delta', 'calculated_attribution_pct', 'adjusted_roi'
        ]].copy()
        _leaderboard = _leaderboard.sort_values('adjusted_roi', ascending=False)

        # Format leaderboard columns
        _leaderboard['OP Delivered'] = _leaderboard['op_delivered'].apply(
            lambda x: f"{x/1e3:,.0f}K" if x >= 1000 else f"{x:,.0f}"
        )
        _leaderboard['TVL Delta'] = _leaderboard['tvl_delta'].apply(
            lambda x: f"+${x/1e6:,.2f}M" if x > 0 else f"-${abs(x)/1e6:,.2f}M" if x < 0 else "$0"
        )
        _leaderboard['Attribution %'] = _leaderboard['calculated_attribution_pct'].apply(
            lambda x: f"{x:.0%}" if pd.notna(x) else '—'
        )
        _leaderboard['Attributable ROI'] = _leaderboard['adjusted_roi'].apply(
            lambda x: f"+${x:,.0f}/OP" if x > 0 else f"-${abs(x):,.0f}/OP" if x < 0 else "$0/OP"
        )

        _leaderboard_display = _leaderboard[[
            'title', 'OP Delivered', 'TVL Delta', 'Attribution %', 'Attributable ROI'
        ]].copy()
        _leaderboard_display.columns = ['Project', 'OP Delivered', 'TVL Delta', 'Attribution %', 'Attributable ROI']

        _leaderboard_table = mo.ui.table(
            data=_leaderboard_display.reset_index(drop=True),
            show_column_summaries=False,
            show_data_types=False,
            page_size=50
        )

        _summary_output = mo.vstack([
            mo.md("#### Extended Project Details"),
            _details_table,
            mo.md("#### Leaderboard by Attributable ROI"),
            _leaderboard_table
        ], gap=1.5)

    _summary_output
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Methodology

    ### Data Collection
    - Key assumptions tracked in this [Google Sheet](https://docs.google.com/spreadsheets/d/1E8Cz_3SFhxrrMEiNMI4yChgM6DfwtSRKVCXPGf7xf_U/edit?usp=sharing)
    - Project data comes from Karma
    - OSO project files include Defillama adapters and Superchain addresses linked to projects
    - Defillama data is currently fetched on a weekly basis
    - OP token transfers are tracked via on-chain event logs from project L2 addresses

    ### Token Transfer Verification
    To ensure data accuracy, token inflows are verified against expected grant amounts:
    - **Expected vs Actual**: The first inflow amount is compared to the expected grant delivery amount
    - **Tolerance**: Discrepancies within 2% are considered valid
    - **Warning Flags**: Projects with inflow discrepancies > 2% receive a warning flag for manual review
    - **Edge Cases**: Some projects may receive other grants (e.g., audit grants) around the same time as TVL grants, which can cause discrepancies
    - **Test Cases**: Verification is validated against known amounts for Truemarkets (70K OP), Super DCA (30K OP), and 40acres.finance (200K OP)

    ### True Baseline Date Calculation
    The baseline date for TVL measurement is calculated as the **minimum** of:
    1. **Initial Delivery Date**: The reported delivery date from the Grants Council
    2. **First Token Inflow Date**: The on-chain timestamp of the first OP token transfer to the project

    This ensures the baseline captures TVL at the earliest point when the project received grant funds, accounting for cases where:
    - Tokens were transferred before the official delivery date was recorded
    - On-chain data provides more accurate timing than reported dates

    The `baseline_date_source` field tracks which date was used ('delivery_date', 'first_inflow', or 'program_start' if neither is available).

    ### Baseline Calculation
    - Each project's baseline is calculated using the 7-day average TVL centered around their **true baseline date** (±3 days)
    - Current values use the most recent 7-day average
    - TVL Delta = Current TVL - Baseline TVL

    ### Attribution Calculation
    Attribution determines what percentage of TVL change can be attributed to the OP grant (vs. other factors like co-incentives):

    **Step 1: Calculate Incentive Share**
    $$
    \text{Incentive Share} = \frac{\text{OP Grant Value (USD)}}{\text{OP Grant Value (USD)} + \text{Co-incentives (USD)}}
    $$

    **Step 2: Apply Scope**
    $$
    \text{Raw Attribution} = \text{Scope \%} \times \text{Incentive Share}
    $$

    Where **Scope %** represents the fraction of TVL that is within the scope of the grant (e.g., if the grant only covers certain chains or products).

    **Step 3: Apply Cap (if applicable)**
    For some projects, an attribution cap is applied based on grant size relative to TVL.

    **Step 4: Round to Bucket**
    The final attribution is rounded to the nearest standard bucket: **1%, 2%, 5%, 10%, 20%, 50%, 100%**

    **Example**: A project with 80% scope, $100K OP grant, and $50K co-incentives:
    - Incentive Share = $100K / ($100K + $50K) = 67%
    - Raw Attribution = 80% × 67% = 53%
    - Final (rounded) = 50%

    ### ROI Calculation
    **Unadjusted ROI** measures the total TVL change per OP delivered:

    $$
    \text{Unadjusted ROI} = \frac{\text{TVL Delta}}{\text{OP Delivered}}
    $$

    **Adjusted ROI** accounts for attribution:
    $$
    \text{Adjusted ROI} = \text{Unadjusted ROI} \times \text{Attribution \%}
    $$

    This represents the TVL change **attributable to the grant** per OP delivered.

    ### OP Price Assumption
    - **Current OP Price**: $0.35 per OP token (fixed)
    - This price is used to convert OP grant amounts to USD for attribution calculations
    - To adjust: Modify the `OP_PRICE_USD` constant in the notebook configuration cell
    - Note: This is a simplifying assumption; actual OP prices vary over time

    ### OP Balance Tracking
    - **Est Balance**: Tracks OP token inflows and outflows for each project's L2 address
    - Inflows are detected from the Optimism Grants Council address
    - Outflows are any OP transfers out of the project's L2 address after receiving grants
    - The chart displays the **daily peak balance** (maximum balance reached each day before outflows)
    - Balance values are clamped to zero (negative balances not shown)

    ### Metrics Summary
    | Metric | Description |
    |--------|-------------|
    | **TVL** | Total Value Locked from DefiLlama via OSO pipeline |
    | **OP Balance** | Estimated OP token balance in project's L2 address (daily peak) |
    | **Unadjusted ROI** | TVL change per OP token delivered ($/OP) |
    | **Adjusted ROI** | TVL change × Attribution % per OP delivered |
    | **Attribution %** | Percentage of TVL change attributable to the OP grant |

    ### Limitations
    - Attribution is estimated based on available data about co-incentives and scope; actual attribution may differ
    - OP Balance tracking only covers the designated L2 address; tokens moved to other wallets are counted as outflows
    - Some projects may have incomplete data coverage
    - Market conditions not isolated
    - OP token price is fixed at $0.35; actual prices fluctuate
    """)
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


@app.cell
def fetch_project_data(mo, pyoso_db_conn):
    # Load grant metadata from optimism.grants
    df_grants_raw = mo.sql(
        f"""
        SELECT
          kp.title,
          s8.status,
          s8.op_total_amount,
          s8.op_delivered,
          s8.l2_address,
          s8.initial_delivery_date,
          s8.chains,
          s8.defillama_slugs AS defillama_adapters,
          kp.oso_project_name AS oso_project_slug,
          'https://gap.karmahq.xyz/project/' || kp.slug AS karma_page,
          'https://github.com/opensource-observer/oss-directory/tree/main/data/projects/' || SUBSTR(kp.oso_project_name, 1, 1) || '/' || kp.oso_project_name || '.yaml' AS oso_project_artifacts,
          CAST(REPLACE(a.scope_pct, '%', '') AS DOUBLE) / 100.0 AS scope_pct,
          a.scope_notes,
          a.coincentives_usd,
          a.coincentives_notes,
          a.attribution_cap_applied::BOOLEAN AS attribution_cap_applied
        FROM optimism.grants.s8_tvl__projects AS s8
        JOIN oso_community.karma.projects AS kp
          ON s8.project_name = kp.title
        JOIN optimism.govfund.s8_attribution AS a
          ON s8.project_name = a.project_name
        WHERE
          s8.op_total_amount > 0
          AND kp.title NOT LIKE '%TEST%'
        ORDER BY UPPER(kp.title)
        """,
        engine=pyoso_db_conn
    )
    return (df_grants_raw,)


@app.cell(hide_code=True)
def fetch_project_metrics(
    ANALYSIS_END_DATE,
    ANALYSIS_START_DATE,
    mo,
    pyoso_db_conn,
):
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
def fetch_token_events(mo, pyoso_db_conn):
    df_token_events = mo.sql(
        f"""
        WITH token_events AS (
            WITH const AS (
              SELECT CAST('18446744073709551616' AS DECIMAL(38,0)) AS two64
            ),
            events AS (
              SELECT
                l.block_timestamp,
                l.transaction_hash,
                l.log_index,
                l.from_address AS tx_from_address,
                l.to_address AS called_contract,
                l.function_selector,
                CASE
                  WHEN CARDINALITY(l.indexed_args_list) >= 1
                    AND l.indexed_args_list[1].element IS NOT NULL
                    AND LENGTH(l.indexed_args_list[1].element) >= 66
                  THEN LOWER(CONCAT('0x', SUBSTRING(l.indexed_args_list[1].element, 27)))
                END AS op_from_address,
                CASE
                  WHEN CARDINALITY(l.indexed_args_list) >= 2
                    AND l.indexed_args_list[2].element IS NOT NULL
                    AND LENGTH(l.indexed_args_list[2].element) >= 66
                  THEN LOWER(CONCAT('0x', SUBSTRING(l.indexed_args_list[2].element, 27)))
                END AS op_to_address,
                CASE
                  WHEN l.data_hex IS NOT NULL
                    AND l.data_hex <> '0x'
                    AND LENGTH(l.data_hex) >= 66
                  THEN
                    CAST((
                      (
                        CASE
                          WHEN from_big_endian_64(from_hex(SUBSTRING(LOWER(SUBSTRING(l.data_hex, 3)), 33, 16))) < 0
                          THEN CAST(from_big_endian_64(from_hex(SUBSTRING(LOWER(SUBSTRING(l.data_hex, 3)), 33, 16))) AS DECIMAL(38,0)) + c.two64
                          ELSE CAST(from_big_endian_64(from_hex(SUBSTRING(LOWER(SUBSTRING(l.data_hex, 3)), 33, 16))) AS DECIMAL(38,0))
                        END
                      ) * c.two64
                      +
                      (
                        CASE
                          WHEN from_big_endian_64(from_hex(SUBSTRING(LOWER(SUBSTRING(l.data_hex, 3)), 49, 16))) < 0
                          THEN CAST(from_big_endian_64(from_hex(SUBSTRING(LOWER(SUBSTRING(l.data_hex, 3)), 49, 16))) AS DECIMAL(38,0)) + c.two64
                          ELSE CAST(from_big_endian_64(from_hex(SUBSTRING(LOWER(SUBSTRING(l.data_hex, 3)), 49, 16))) AS DECIMAL(38,0))
                        END
                      )
                    ) AS DOUBLE) / 1e18
                  ELSE 0.0
                END AS value_op
              FROM oso.stg_optimism__enriched_logs AS l
              CROSS JOIN const AS c
              WHERE
                l.contract_address = '0x4200000000000000000000000000000000000042'
                AND l.topic0 = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
                AND CARDINALITY(l.indexed_args_list) >= 2    
            )
            SELECT 
              block_timestamp,
              transaction_hash,
              log_index,
              tx_from_address,
              called_contract,
              function_selector,
              op_from_address,
              op_to_address,
              value_op
            FROM events    
            WHERE block_timestamp >= DATE('2025-09-01')
        ),

        inflows AS (
        	SELECT
              op.block_timestamp,  
              s8.project_name,
              op.op_to_address AS project_address,
              op.value_op,
              'inflow' AS event_type,
              op.transaction_hash,
              op.function_selector
            FROM token_events AS op
            JOIN optimism.grants.s8_tvl__projects AS s8
              ON op.op_to_address = LOWER(s8.l2_address)
            WHERE op.op_from_address = LOWER('0x8A2725a6f04816A5274dDD9FEaDd3bd0C253C1A6')  
        ),
        first_inflow AS (
            SELECT
              project_address,
              MIN(block_timestamp) AS block_timestamp 
            FROM inflows
            GROUP BY 1
        ),
        outflows AS (
        	SELECT
              op.block_timestamp,  
              s8.project_name,
              op.op_from_address AS project_address,
              (-op.value_op) AS value_op,
              'outflow' AS event_type,
              op.transaction_hash,
              op.function_selector    
            FROM token_events AS op
            JOIN optimism.grants.s8_tvl__projects AS s8
              ON op.op_from_address = LOWER(s8.l2_address)
            JOIN first_inflow
              ON op.op_from_address = first_inflow.project_address
            WHERE op.block_timestamp > first_inflow.block_timestamp 
        ),
        unioned AS (
            SELECT * FROM inflows
            UNION ALL
            SELECT * FROM outflows
        )
        SELECT
          project_name,
          block_timestamp,    
          value_op,
          event_type,
          project_address,    
          transaction_hash,
          function_selector
        FROM unioned
        ORDER BY project_name, block_timestamp
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_token_events,)


@app.cell(hide_code=True)
def _():
    # Expected first inflow amounts for verification (test cases)
    # These are known amounts from the S8 TVL grants - first milestone payments (40% of total)
    EXPECTED_FIRST_INFLOWS = {
        'Truemarkets': 28000,  # 40% of 70,000 total
        'Super DCA': 12000,    # 40% of 30,000 total
        '40acres.finance': 80000,  # 40% of 200,000 total
    }
    return (EXPECTED_FIRST_INFLOWS,)


@app.cell(hide_code=True)
def _():
    # Attribution calculation constants
    OP_PRICE_USD = 0.35  # Fixed OP price for calculations (can be adjusted per project)
    ATTRIBUTION_BUCKETS = [0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 1.0]  # Available attribution percentages
    return ATTRIBUTION_BUCKETS, OP_PRICE_USD


@app.cell(hide_code=True)
def _(ATTRIBUTION_BUCKETS):
    def calculate_attribution(scope_pct, op_total_usd, coincentives_usd, tvl, attribution_cap_applied):
        """
        Calculate attribution percentage for a project's TVL change.

        Attribution = MIN(Scope × Incentive Share, Cap)
        where:
        - Incentive Share = OP USD / (OP USD + Co-incentives USD)
        - Cap = OP USD / Baseline TVL (only if attribution_cap_applied=True)

        Args:
            scope_pct: Fraction of TVL in scope (0.0 to 1.0)
            op_total_usd: USD value of OP grant
            coincentives_usd: USD value of co-incentives from other sources
            tvl: Current TVL (used for cap calculation if attribution_cap_applied)
            attribution_cap_applied: Boolean indicating if attribution should be capped

        Returns:
            tuple: (final_pct, formula_text) where:
                - final_pct: Attribution percentage rounded to nearest bucket (0.0 to 1.0)
                - formula_text: Human-readable explanation of the calculation
        """
        import math

        # Handle edge cases
        if scope_pct is None or (isinstance(scope_pct, float) and math.isnan(scope_pct)):
            scope_pct = 1.0  # Default to 100% scope if not specified

        if coincentives_usd is None or (isinstance(coincentives_usd, float) and math.isnan(coincentives_usd)):
            coincentives_usd = 0.0

        if op_total_usd is None or op_total_usd <= 0:
            return (0.0, "No OP grant value")

        # Step 1: Calculate incentive share: OP / (OP + coincentives)
        total_incentives = op_total_usd + coincentives_usd
        incentive_share = op_total_usd / total_incentives

        # Step 2: Calculate raw attribution: scope * incentive_share
        raw_attribution = scope_pct * incentive_share

        # Step 3: Apply cap if specified
        if attribution_cap_applied and tvl and tvl > 0:
            # Cap based on grant size relative to TVL
            cap = min(1.0, op_total_usd / tvl)
            capped_attribution = min(raw_attribution, cap)
            cap_was_applied = capped_attribution < raw_attribution
        else:
            cap = None
            capped_attribution = raw_attribution
            cap_was_applied = False

        # Step 4: Round to nearest bucket
        def round_to_bucket(value, buckets):
            """Round value to the nearest bucket."""
            if value <= 0:
                return buckets[0]
            if value >= buckets[-1]:
                return buckets[-1]
            # Handle values smaller than smallest bucket
            if value < buckets[0]:
                return buckets[0]

            # Find the two buckets that value falls between
            for i in range(len(buckets) - 1):
                if buckets[i] <= value <= buckets[i + 1]:
                    # Return the closer bucket
                    if value - buckets[i] <= buckets[i + 1] - value:
                        return buckets[i]
                    else:
                        return buckets[i + 1]
            return buckets[-1]

        final_pct = round_to_bucket(capped_attribution, ATTRIBUTION_BUCKETS)

        # Build detailed formula text showing all intermediate values
        # Multi-line format for readability in footnotes
        formula_lines = []

        # Cap calculation (if applicable)
        if attribution_cap_applied and tvl and tvl > 0:
            cap_raw_pct = op_total_usd / tvl
            cap_bucket = round_to_bucket(min(1.0, cap_raw_pct), ATTRIBUTION_BUCKETS)
            formula_lines.append(f"Cap = (OP Value / Baseline TVL) = ${op_total_usd:,.0f} / ${tvl:,.0f} = {cap_raw_pct:.2%} → Lookup: {cap_bucket:.0%}")
        else:
            formula_lines.append("Cap = N/A (cap not applied)")

        # Incentive share
        formula_lines.append(f"Incentive Share = OP Value / (OP Value + Co-incentives) = ${op_total_usd:,.0f} / (${op_total_usd:,.0f} + ${coincentives_usd:,.0f}) = {incentive_share:.2%}")

        # Scope
        formula_lines.append(f"Scope = {scope_pct:.0%} of TVL in scope")

        # Raw attribution
        formula_lines.append(f"Raw = Scope × Incentive Share = {scope_pct:.0%} × {incentive_share:.2%} = {raw_attribution:.2%}")

        # Final (with cap if applied)
        if cap is not None and cap_was_applied:
            formula_lines.append(f"Final = MIN(Raw, Cap) = MIN({raw_attribution:.2%}, {cap:.2%}) = {capped_attribution:.2%} → Rounded to {final_pct:.0%}")
        else:
            formula_lines.append(f"Final = {capped_attribution:.2%} → Rounded to {final_pct:.0%}")

        formula_text = "\n".join(formula_lines)

        # Debug logging for verification
        print(f"[Attribution Debug] scope={scope_pct:.2%}, op_usd=${op_total_usd:,.0f}, coincentives=${coincentives_usd:,.0f}, tvl=${tvl:,.0f if tvl else 0}, cap_applied={attribution_cap_applied}")
        print(f"  -> incentive_share={incentive_share:.4f}, raw={raw_attribution:.4f}, capped={capped_attribution:.4f}, final={final_pct:.4f}")

        return (final_pct, formula_text)
    return (calculate_attribution,)


@app.cell(hide_code=True)
def _(EXPECTED_FIRST_INFLOWS, df_token_events, pd):
    # Token transfer verification logic
    # Verifies that token inflows match expected grant amounts

    def verify_first_inflow(df_events, project_name, expected_amount, tolerance=0.02):
        """
        Verify that the first inflow for a project matches the expected amount.

        Args:
            df_events: DataFrame with token events (project_name, value_op, event_type)
            project_name: Name of the project to verify
            expected_amount: Expected OP amount for first inflow
            tolerance: Allowed discrepancy as a fraction (default 2%)

        Returns:
            tuple: (is_valid, actual_amount, discrepancy_pct)
        """
        if df_events.empty:
            return (False, 0, 1.0)

        # Get first inflow for this project
        _proj_inflows = df_events[
            (df_events['project_name'] == project_name) &
            (df_events['event_type'] == 'inflow')
        ].copy()

        if _proj_inflows.empty:
            return (False, 0, 1.0)

        # Sort by timestamp to get the first inflow
        _proj_inflows = _proj_inflows.sort_values('block_timestamp')
        _first_inflow = _proj_inflows.iloc[0]['value_op']

        # Calculate discrepancy
        if expected_amount == 0:
            _discrepancy_pct = 1.0 if _first_inflow != 0 else 0.0
        else:
            _discrepancy_pct = abs(_first_inflow - expected_amount) / expected_amount

        _is_valid = _discrepancy_pct <= tolerance

        return (_is_valid, _first_inflow, _discrepancy_pct)

    def get_first_inflow_date(df_events, project_name):
        """
        Get the timestamp of the first inflow for a project.

        Args:
            df_events: DataFrame with token events (project_name, block_timestamp, event_type)
            project_name: Name of the project

        Returns:
            pd.Timestamp or None: The timestamp of the first inflow, or None if no inflows found
        """
        if df_events.empty:
            return None

        # Get inflows for this project
        _proj_inflows = df_events[
            (df_events['project_name'] == project_name) &
            (df_events['event_type'] == 'inflow')
        ].copy()

        if _proj_inflows.empty:
            return None

        # Sort by timestamp and return the first date
        _proj_inflows = _proj_inflows.sort_values('block_timestamp')
        return pd.to_datetime(_proj_inflows.iloc[0]['block_timestamp'])

    # Build verification DataFrame for all projects with inflows
    _verification_records = []

    if not df_token_events.empty:
        _projects = df_token_events['project_name'].unique()

        for _proj in _projects:
            # Get first inflow for this project
            _proj_inflows = df_token_events[
                (df_token_events['project_name'] == _proj) &
                (df_token_events['event_type'] == 'inflow')
            ].copy()

            if _proj_inflows.empty:
                continue

            _proj_inflows = _proj_inflows.sort_values('block_timestamp')
            _first_inflow_amount = _proj_inflows.iloc[0]['value_op']
            _first_inflow_date = pd.to_datetime(_proj_inflows.iloc[0]['block_timestamp'])

            # Check if we have an expected amount for this project
            _expected = EXPECTED_FIRST_INFLOWS.get(_proj, None)

            if _expected is not None:
                _is_valid, _, _discrepancy_pct = verify_first_inflow(
                    df_token_events, _proj, _expected
                )
                _inflow_warning = None if _is_valid else (
                    f"Expected {_expected:,.0f} OP, got {_first_inflow_amount:,.0f} OP "
                    f"({_discrepancy_pct:.1%} discrepancy)"
                )
            else:
                _is_valid = True  # No expected amount, assume valid
                _discrepancy_pct = None
                _inflow_warning = None

            _verification_records.append({
                'project_name': _proj,
                'first_inflow_amount': _first_inflow_amount,
                'first_inflow_date': _first_inflow_date,
                'expected_amount': _expected,
                'is_valid': _is_valid,
                'discrepancy_pct': _discrepancy_pct,
                'inflow_warning': _inflow_warning
            })

    df_token_transfers_verified = pd.DataFrame(_verification_records)

    # Log verification results for test cases
    print("=== Token Transfer Verification Results ===")
    for _test_proj, _expected_amt in EXPECTED_FIRST_INFLOWS.items():
        _is_valid, _actual, _disc = verify_first_inflow(df_token_events, _test_proj, _expected_amt)
        _status = "✓ PASS" if _is_valid else "✗ FAIL"
        print(f"{_test_proj}: {_status} (expected {_expected_amt:,} OP, got {_actual:,.0f} OP, {_disc:.1%} discrepancy)")
    print("=" * 44)
    return (get_first_inflow_date,)


@app.cell(hide_code=True)
def _(df_metrics, df_token_events, pd):
    # Calculate daily OP balance time series with forward-fill
    # Shows peak balance per day (max balance reached before any outflows)

    if df_token_events.empty:
        df_op_balance_daily = pd.DataFrame(columns=['project_name', 'date', 'op_balance'])
        project_current_balance = {}
    else:
        # Get date range from metrics for consistent x-axis
        _min_date = df_metrics['sample_date'].min()
        _max_date = df_metrics['sample_date'].max()
        _date_range = pd.date_range(start=_min_date, end=_max_date, freq='D')

        # Calculate running balance per project with peak tracking
        _df_events = df_token_events.copy()
        _df_events['datetime'] = pd.to_datetime(_df_events['block_timestamp'])
        _df_events['date'] = _df_events['datetime'].dt.date

        _balance_records = []
        _current_balances = {}
        _projects = _df_events['project_name'].unique()

        for _proj in _projects:
            # Get all events for this project, sorted by timestamp
            _proj_events = _df_events[_df_events['project_name'] == _proj].copy()
            _proj_events = _proj_events.sort_values('datetime')

            # Calculate running balance at each event
            _proj_events['running_balance'] = _proj_events['value_op'].cumsum()

            # Group by date: get peak (max) and ending (last) balance
            _daily_stats = (
                _proj_events
                .groupby('date')
                .agg(
                    peak_balance=('running_balance', 'max'),
                    end_balance=('running_balance', 'last')
                )
                .reset_index()
            )
            _daily_stats['date'] = pd.to_datetime(_daily_stats['date'])
            _daily_stats = _daily_stats.set_index('date').sort_index()

            # Get first date with positive balance
            _first_positive = _daily_stats[_daily_stats['peak_balance'] > 0].index.min()
            if pd.isna(_first_positive):
                continue

            # Include day before first inflow to show hvh step from 0
            _day_before = _first_positive - pd.Timedelta(days=1)
            _start_date = _day_before if _day_before >= _min_date else _first_positive

            # Build daily series from day before first positive date
            _proj_date_range = _date_range[_date_range >= _start_date]
            if len(_proj_date_range) == 0:
                continue

            _proj_daily = pd.DataFrame({'date': _proj_date_range}).set_index('date')

            # Merge with daily stats
            _proj_daily = _proj_daily.join(_daily_stats)

            # Forward-fill ending balance for days with no events
            _proj_daily['end_balance'] = _proj_daily['end_balance'].ffill()

            # For display: use peak if available, otherwise use forward-filled end balance
            # Days before first inflow get 0, then clamp to 0 (no negative balances)
            _proj_daily['op_balance'] = _proj_daily['peak_balance'].fillna(_proj_daily['end_balance']).fillna(0).clip(lower=0)

            # Store current (actual) balance as the last ending balance (clamped to 0)
            _last_end_balance = _proj_daily['end_balance'].dropna()
            if not _last_end_balance.empty:
                _current_balances[_proj] = max(0, _last_end_balance.iloc[-1])

            for _date, _row in _proj_daily.iterrows():
                if pd.notna(_row['op_balance']):
                    _balance_records.append({
                        'project_name': _proj,
                        'date': _date,
                        'op_balance': _row['op_balance']
                    })

        df_op_balance_daily = pd.DataFrame(_balance_records)
        project_current_balance = _current_balances
    return df_op_balance_daily, project_current_balance


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
def _(df_grants, df_metrics, pd):
    # Calculate program dates from data
    _delivery_dates = df_grants['initial_delivery_date'].dropna()

    _min_delivery = _delivery_dates.min() if len(_delivery_dates) > 0 else None
    PROGRAM_START_DATE = _min_delivery.strftime('%Y-%m-%d') if pd.notna(_min_delivery) else "2025-06-01"
    _max_sample = df_metrics['sample_date'].max() if len(df_metrics) > 0 else None
    PROGRAM_END_DATE = _max_sample.strftime('%Y-%m-%d') if pd.notna(_max_sample) else "2025-12-31"
    total_projects = len(df_grants)
    return PROGRAM_END_DATE, PROGRAM_START_DATE


@app.cell(hide_code=True)
def _(
    MIN_TVL_THRESHOLD,
    OP_PRICE_USD,
    PROGRAM_START_DATE,
    all_projects,
    calculate_attribution,
    df_grants,
    df_metrics,
    df_token_events,
    get_first_inflow_date,
    pd,
    project_current_balance,
):
    # Calculate ROI metrics for each project
    # Baseline = TVL at project_baseline_date (min of delivery date and first inflow)
    # Current = latest TVL, ROI = Delta / OP delivered

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
        _l2_address = _grant_row.get('l2_address', None)
        _title = _grant_row.get('title', _project)

        # Get attribution parameters from grant data
        _scope_pct = _grant_row.get('scope_pct', 1.0)
        _coincentives_usd = _grant_row.get('coincentives_usd', 0.0)
        _attribution_cap_applied = _grant_row.get('attribution_cap_applied', False)

        # Get TVL data for this project
        _proj_tvl = _df_tvl_all[_df_tvl_all['project_title'] == _project].copy()
        if _proj_tvl.empty:
            continue

        # Get first inflow date from token events (keyed by title/project_name)
        _first_inflow_date = get_first_inflow_date(df_token_events, _title)

        # Get current TVL date (latest available TVL data)
        _latest_date = _proj_tvl['sample_date'].max()

        # Determine if grant is undelivered:
        # - No OP delivered yet, OR
        # - Delivery date is in the future
        _is_undelivered = (
            _op_delivered == 0 or
            (pd.notna(_delivery_date) and _delivery_date > _latest_date)
        )

        # Calculate project_baseline_date = MIN(initial_delivery_date, first_inflow_date)
        # and track which source was used
        # For undelivered grants, use current date so TVL delta = 0
        if _is_undelivered:
            # Grant not yet delivered - use current date as baseline
            # This ensures baseline_tvl = current_tvl and tvl_delta = 0
            _project_baseline_date = _latest_date
            _baseline_date_source = 'undelivered'
        elif pd.notna(_delivery_date) and _first_inflow_date is not None:
            # Both dates available - use the minimum
            if _first_inflow_date < _delivery_date:
                _project_baseline_date = _first_inflow_date
                _baseline_date_source = 'first_inflow'
            else:
                _project_baseline_date = _delivery_date
                _baseline_date_source = 'delivery_date'
        elif pd.notna(_delivery_date):
            # Only delivery date available
            _project_baseline_date = _delivery_date
            _baseline_date_source = 'delivery_date'
        elif _first_inflow_date is not None:
            # Only first inflow date available
            _project_baseline_date = _first_inflow_date
            _baseline_date_source = 'first_inflow'
        else:
            # Neither available - fall back to program start
            _project_baseline_date = pd.to_datetime(PROGRAM_START_DATE)
            _baseline_date_source = 'program_start'

        _baseline_window = _proj_tvl[
            (_proj_tvl['sample_date'] >= _project_baseline_date - pd.Timedelta(days=3)) &
            (_proj_tvl['sample_date'] <= _project_baseline_date + pd.Timedelta(days=3))
        ]
        _baseline_tvl = _baseline_window['amount'].mean() if not _baseline_window.empty else 0

        # Calculate current TVL (latest 7-day avg)
        # Note: _latest_date already calculated above for undelivered check
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

        # Get estimated OP balance from token events (keyed by title/project_name)
        _est_op_balance = project_current_balance.get(_title, None)

        # Calculate attribution percentage
        # OP grant value in USD for attribution calculation
        _op_total_usd = _op_total * OP_PRICE_USD
        _calculated_attribution_pct, _calculated_formula = calculate_attribution(
            scope_pct=_scope_pct,
            op_total_usd=_op_total_usd,
            coincentives_usd=_coincentives_usd,
            tvl=_current_tvl,
            attribution_cap_applied=_attribution_cap_applied
        )

        _project_metrics.append({
            'project': _project,
            'title': _title,
            'delivery_date': _delivery_date,
            'first_inflow_date': _first_inflow_date,
            'project_baseline_date': _project_baseline_date,
            'baseline_date_source': _baseline_date_source,
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
            'defillama_adapters': _grant_row.get('defillama_adapters', ''),
            'l2_address': _l2_address,
            'est_op_balance': _est_op_balance,
            'scope_pct': _scope_pct,
            'coincentives_usd': _coincentives_usd,
            'attribution_cap_applied': _attribution_cap_applied,
            'calculated_attribution_pct': _calculated_attribution_pct,
            'calculated_formula': _calculated_formula
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
