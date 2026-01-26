import marimo

__generated_with = "unknown"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Benchmarking performance of TVL grants on the Superchain
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">Optimism</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2025-12-02</span></small>
    """
    )
    return


@app.cell(hide_code=True)
def _(
    activity_headline,
    df_tvl_grants_summary,
    fee_rev_headline,
    fees_headline,
    market_share_headline,
    mo,
    top_apps_headline,
):
    _context = f"""
    - This analysis covers the period July 2021 through September 2025, and all prospective grants made through Season 7.
    - There are a total of {len(df_tvl_grants_summary)} projects with TVL on the Superchain that have received grants.
    """

    _insights = f"""
    1. {market_share_headline}.
    2. {fee_rev_headline}.
    3. {fees_headline}.
    4. {activity_headline}.
    5. {top_apps_headline}.
    """

    mo.accordion({
        "Context": _context,
        "Key Insights": _insights,
        "Data Sources": """
        - [Superchain Data (c/o Goldsky)](https://bit.ly/superchain-public-data) - Source of raw transaction and traces data
        - [DefiLlama](https://defillama.com/) - Source of raw TVL data
        - [OSS Directory](https://github.com/opensource-observer/oss-directory) - OSO's public project and address registry
        - [OSO API](https://docs.opensource.observer/docs/get-started/python) - Data and metrics pipeline
        """
    })    
    return


@app.cell(hide_code=True)
def _():
    SAMPLE_DATE = '2025-09-30'
    return (SAMPLE_DATE,)


@app.cell(hide_code=True)
def _(
    PLOTLY_LAYOUT,
    SAMPLE_DATE,
    df_project_metrics,
    df_tvl_grants_summary,
    mo,
    pd,
    px,
):
    _df = (
        df_project_metrics.merge(df_tvl_grants_summary[['OSO Slug', 'Vertical']], on='OSO Slug')
        .query("Metric == 'TVL (7D)'")
        .groupby(['Date', 'Vertical'], as_index=False)
        .agg({'Amount': 'sum'})
    )

    _fig = px.area(
        data_frame=_df,
        x='Date',
        y='Amount',
        color='Vertical'
    )
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(hovermode='x unified', xaxis=dict(hoverformat='<b>%d-%b-%Y</b>'))
    _fig.update_traces(
        hovertemplate='%{fullData.name}: $%{y:,.0f}<extra></extra>',
        hoverlabel=dict(namelength=-1)
    )

    _dff = _df[_df['Date'] == pd.to_datetime(SAMPLE_DATE)]
    _total_tvl = _dff['Amount'].sum()
    _lending_dexs = _dff[_dff['Vertical'].isin(['Lending', 'Dexs'])]['Amount'].sum()
    _ratio = _lending_dexs/_total_tvl * 100

    market_share_headline = f'{_ratio:,.0f}% of Superchain TVL comes from DEX and lending protocols'

    mo.vstack([
        mo.md(f"""
        ### **{market_share_headline}**

        A total of ${_total_tvl/1_000_000_000:,.1f}B TVL (trailing 7-day avg) is on the Superchain as of 2025-Sep-30
        """),
        mo.ui.plotly(_fig)
    ])
    return (market_share_headline,)


@app.cell(hide_code=True)
def _(
    PLOTLY_LAYOUT,
    df_project_metrics,
    df_tvl_grants_summary,
    go,
    make_subplots,
):
    def dual_axis_by_vertical(vertical_name, metric1, metric2):
        _map = df_tvl_grants_summary[['OSO Slug','Vertical']]
        _merged = df_project_metrics.merge(_map, on='OSO Slug', how='left')
        _merged = _merged[_merged['Vertical'].str.lower()==vertical_name.lower()].copy()

        _df_tvl = (
            _merged.query(f"Metric=='{metric1} (7D)'")
            .groupby(['Date'], as_index=False)
            .agg({'Amount':'sum'})
        )
        _df_userops = (
            _merged.query(f"Metric=='{metric2} (7D)'")
            .groupby(['Date'], as_index=False)
            .agg({'Amount':'sum'})
        )

        _fig = make_subplots(specs=[[{"secondary_y": True}]])
        _fig.add_trace(
            go.Scatter(
                x=_df_tvl['Date'],
                y=_df_tvl['Amount'],
                mode='lines',
                name=metric1,
                fill='tozeroy'
            ),
            secondary_y=False
        )
        _fig.add_trace(
            go.Scatter(
                x=_df_userops['Date'],
                y=_df_userops['Amount'],
                mode='lines',
                name=metric2,
            ),
            secondary_y=True
        )

        _fig.update_layout(**PLOTLY_LAYOUT)
        _fig.update_layout(hovermode='x unified', xaxis=dict(hoverformat='<b>%d-%b-%Y</b>'))
        _fig.update_layout(legend_title=vertical_name, legend_title_font_weight='bold')
        _fig.update_yaxes(title_text=f"{vertical_name} {metric1}", secondary_y=False)
        _fig.update_yaxes(title_text=metric2, secondary_y=True)
        _fig.update_traces(
            hovertemplate='%{fullData.name}: %{y:,.0f}<extra></extra>',
            hoverlabel=dict(namelength=-1)
        )
        return _fig
    return (dual_axis_by_vertical,)


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_project_metrics, mo, pd, px):
    _fee_metric = 'Fees (ETH) per $100M TVL'
    _rev_metric = 'Revenue (ETH) per $100M TVL'

    _df = df_project_metrics.pivot_table(index='Date', columns='Metric', values='Amount', aggfunc='sum', fill_value=0)
    _df[_fee_metric] = _df['Fees (7D)'] / (_df['TVL (7D)'] / 100_000_000)
    _df[_rev_metric] = _df['Revenue (7D)'] / (_df['TVL (7D)'] / 100_000_000)
    _df = _df[[_fee_metric, _rev_metric]].reset_index()
    _df = _df[_df[_rev_metric] > 0]

    _dff = _df[_df['Date'] >= pd.to_datetime('2024-10-01')]
    _fees = _dff[_fee_metric].mean()
    _revs = _dff[_rev_metric].mean()

    _df = _df.melt(id_vars=['Date'], value_vars=[_fee_metric, _rev_metric], value_name='Amount')

    _fig = px.line(
        data_frame=_df,
        x='Date',
        y='Amount',
        color='Metric'
    )
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(hovermode='x unified', xaxis=dict(hoverformat='<b>%d-%b-%Y</b>'))
    _fig.update_traces(
        hovertemplate='%{fullData.name}: %{y:,.4f}<extra></extra>',
        hoverlabel=dict(namelength=-1)
    )


    fee_rev_headline = f'Over the past year, every $100M in Superchain TVL has been associated with {_fees:,.4f} ETH / day in L2 fees'

    mo.vstack([
        mo.md(f"""
        ### **{fee_rev_headline}**

        This translates into an estimated {_revs:,.4f} ETH / day in revenue
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return (fee_rev_headline,)


@app.cell(hide_code=True)
def _(
    SAMPLE_DATE,
    df_project_metrics,
    df_tvl_grants_summary,
    dual_axis_by_vertical,
    mo,
    pd,
):
    _fig_dexs=dual_axis_by_vertical("Dexs", metric1="TVL", metric2="Fees")
    _fig_lending=dual_axis_by_vertical("Lending", metric1="TVL", metric2="Fees")

    _df = (
        df_project_metrics.merge(df_tvl_grants_summary[['OSO Slug', 'Vertical']], on='OSO Slug')
        .groupby(['Date', 'Vertical', 'Metric'], as_index=False)
        .agg({'Amount': 'sum'})
    )
    _df = _df[_df['Date'] == pd.to_datetime(SAMPLE_DATE)]
    _df = _df[_df['Vertical'].isin(['Lending', 'Dexs'])]
    _piv = (
        _df
        .pivot(index='Vertical', columns='Metric', values='Amount')
        .reindex(['Dexs','Lending'])
    )

    _per_hundred_million = _piv['Fees (7D)'] / (_piv['TVL (7D)'] / 100_000_000)
    _X = float(_per_hundred_million.loc['Dexs'])
    _Y = float(_per_hundred_million.loc['Lending'])
    _ratio = _X/_Y

    fees_headline = f'DEXs generate {_ratio:.0f}X more fees per unit of TVL than lending protocols'
    mo.vstack([
        mo.md(f"""
        ### **{fees_headline}**

        In September, the Superchain averaged {_X:,.4f} ETH in L2 fees for every $100M in DEX TVL, vs {_Y:,.4f} ETH for every $100M in lending TVL
        """),
        mo.hstack(
            [mo.ui.plotly(_fig_dexs), mo.ui.plotly(_fig_lending)],
            justify="space-between"
        )
    ])
    return (fees_headline,)


@app.cell(hide_code=True)
def _(
    SAMPLE_DATE,
    df_project_metrics,
    df_tvl_grants_summary,
    dual_axis_by_vertical,
    mo,
    pd,
):
    _fig_dexs=dual_axis_by_vertical("Dexs", metric1="TVL", metric2="Userops")
    _fig_lending=dual_axis_by_vertical("Lending", metric1="TVL", metric2="Userops")


    _df = (
        df_project_metrics.merge(df_tvl_grants_summary[['OSO Slug', 'Vertical']], on='OSO Slug')
        .groupby(['Date', 'Vertical', 'Metric'], as_index=False)
        .agg({'Amount': 'sum'})
    )
    _df = _df[_df['Date'] == pd.to_datetime(SAMPLE_DATE)]
    _df = _df[_df['Vertical'].isin(['Lending', 'Dexs'])]
    _piv = (
        _df
        .pivot(index='Vertical', columns='Metric', values='Amount')
        .reindex(['Dexs','Lending'])
    )

    _per_million = _piv['Userops (7D)'] / (_piv['TVL (7D)'] / 1_000_000)
    _X = float(_per_million.loc['Dexs'])
    _Y = float(_per_million.loc['Lending'])
    _ratio = _X/_Y

    activity_headline = f'DEXs are directly linked to {_ratio:.0f}X more onchain activity per unit of TVL than lending protocols'
    mo.vstack([
        mo.md(f"""
        ### **{activity_headline}**

        In September, there were {_X:,.0f} userops for every $1M in DEX TVL, vs {_Y:,.0f} userops for every $1M in lending TVL
        """),
        mo.hstack(
            [mo.ui.plotly(_fig_dexs), mo.ui.plotly(_fig_lending)],
            justify="space-between"
        )
    ])
    return (activity_headline,)


@app.cell(hide_code=True)
def _(df_tvl_grants_summary, mo, pd, pyoso_db_conn, stringify):
    df_ltv_snapshot = mo.sql(
        f"""
        SELECT * 
        FROM int_optimism_grants_rolling_defi_ltv_inputs_by_project
        WHERE
          sample_date = DATE('2025-09-30')
          AND oso_project_name IN ({stringify(df_tvl_grants_summary['OSO Slug'])})
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_ltv_snapshot['months_activity'] = pd.to_numeric(df_ltv_snapshot['months_activity'])
    df_ltv_summary = (
        df_ltv_snapshot
        .groupby('oso_project_name', as_index=False)
        .agg({
            'months_activity': 'max',
            'tvl_90day': 'sum',
            'revenue_90day': 'sum',
            'fees_90day': 'sum',
            'userops_90day': 'sum',
            'tvl_alltime': 'sum',
            'revenue_alltime': 'sum',
            'fees_alltime': 'sum',
            'userops_alltime': 'sum',
        })
    )
    df_ltv_summary.rename(
        columns={
            'oso_project_name': 'OSO Slug',
            'months_activity': 'Protocol Age (Months)',
            'tvl_90day': 'TVL ($) - 90D',
            'tvl_alltime': 'TVL ($) - ATH',
            'revenue_90day': 'Revenue (ETH) - 90D',
            'revenue_alltime': 'Revenue (ETH) - Lifetime',
            'fees_90day': 'Fees (ETH) - 90D',
            'fees_alltime': 'Fees (ETH) - Lifetime',
            'userops_90day': 'Userops - 90D',
            'userops_alltime': 'Userops - Lifetime',
        },
        inplace=True
    )
    df_ltv_summary['Fees (ETH) per $100M TVL - 90D'] = df_ltv_summary['Fees (ETH) - 90D'] / (df_ltv_summary['TVL ($) - 90D'] / 100_000_000)

    def _label(row):
        if row['Protocol Age (Months)'] < 12:
            return '🟢 New Protocol'
        if row['TVL ($) - 90D'] >= 75_000_000:
            return '🔴 Top Protocol'
        if row['TVL ($) - ATH'] >= 75_000_000:
            return '🟡 Former Top Protocol'
        else:
            return '⚪️ Less Relevant Protocol'

    df_ltv_summary['Cohort'] = df_ltv_summary.apply(lambda row: _label(row), axis=1)
    return (df_ltv_summary,)


@app.cell(hide_code=True)
def _(df_ltv_summary, df_tvl_grants_summary, mo):
    df_ltv_cac_summary = df_tvl_grants_summary.merge(df_ltv_summary, on='OSO Slug', how='left')

    df_top_apps = df_ltv_cac_summary[df_ltv_cac_summary['Cohort'] == '🔴 Top Protocol'].copy()
    df_top_apps.drop(columns=['OSO Slug', 'Vertical Tags'], inplace=True)
    df_top_apps = df_top_apps.sort_values(by='Fees (ETH) per $100M TVL - 90D', ascending=False).reset_index(drop=True)

    _fmt = {
        'Fees (ETH) per $100M TVL - 90D': '{:,.4f}',
        #'Maturity (Months)': '{:,.1f}',
        'Fees (ETH) - 90D': '{:,.4f}',
        'TVL ($) - 90D': '${:,.0f}',
        'Userops - 90D': '{:,.0f}',
        'Revenue (ETH) - 90D': '{:,.4f}',
        'TVL ($) - ATH': '${:,.0f}',
        'Fees (ETH) - Lifetime': '{:,.4f}',
        'Userops - Lifetime': '{:,.0f}',
        'Revenue (ETH) - Lifetime': '{:,.4f}',
    }

    _cols = ['Project', 'Vertical'] + list(_fmt.keys())
    _df = df_top_apps[_cols]

    _total_tvl = df_ltv_summary['TVL ($) - 90D'].sum()
    _top_app_tvl = _df['TVL ($) - 90D'].sum()
    _ratio = _top_app_tvl / _total_tvl * 100
    _top_app_fees = _df['Fees (ETH) - 90D'].sum()
    _top_app_revs = _df['Revenue (ETH) - 90D'].sum()


    top_apps_headline = f'The top {len(_df)} defi protocols currently hold {_ratio:,.0f}% of Superchain TVL'


    mo.vstack([
        mo.md(f"""
        ### **{top_apps_headline}**

        These apps generated a total of {_top_app_fees:,.0f} ETH L2 fees (~{_top_app_revs:,.0f} ETH collective revenue) over the last 90 days
        """),
        mo.ui.table(
            data=_df,
            format_mapping=_fmt,
            show_data_types=False,
            show_column_summaries=False,
            page_size=20
        )
    ])
    return df_ltv_cac_summary, df_top_apps, top_apps_headline


@app.cell(hide_code=True)
def _(EXPECTED_LIFETIME, OP_ETH_PRICE, df_top_apps, mo):
    def compute_ltv_cac(
        df,
        op_eth_price=OP_ETH_PRICE,
        lifetime_months=EXPECTED_LIFETIME
    ):
        _df = df[['Project', 'Vertical', 'Cohort', 'Protocol Age (Months)', 'All Grants Amount (OP)', 'Revenue (ETH) - Lifetime', 'Revenue (ETH) - 90D']].copy()
        _df['Monthly Revenue (ETH)'] = _df['Revenue (ETH) - 90D'] / 3
        _df['Expected Lifetime (Months)'] = lifetime_months - _df['Protocol Age (Months)']
        _df['Revenue (ETH) - Projected'] = (_df['Monthly Revenue (ETH)'] * _df['Expected Lifetime (Months)'])
        _df['LTV (ETH)'] = _df['Revenue (ETH) - Projected'] + _df['Revenue (ETH) - Lifetime']
        _df['CAC (ETH)'] = _df['All Grants Amount (OP)'] * op_eth_price
        _df['LTV/CAC'] = _df['LTV (ETH)'] / _df['CAC (ETH)']
        _df.rename(columns={'Revenue (ETH) - Lifetime': 'Revenue (ETH) - Actual to Date', 'Revenue (ETH) - 90D': 'Revenue (ETH) - Last 90D'}, inplace=True)
        _df = _df.sort_values(by='LTV/CAC', ascending=False).reset_index(drop=True)
        return _df

    df_top_apps_ltv = compute_ltv_cac(df_top_apps)
    _fmt = {
        'All Grants Amount (OP)': '{:,.0f}',         
        'Protocol Age (Months)': '{:,.1f}',
        'Expected Lifetime (Months)': '{:,.1f}',
        'Revenue (ETH) - Actual to Date': '{:,.4f}',
        'Revenue (ETH) - Last 90D': '{:,.4f}',
        'Revenue (ETH) - Projected': '{:,.4f}',
        'LTV (ETH)': '{:,.4f}',
        'CAC (ETH)': '{:,.4f}',
        'LTV/CAC': '{:,.2f}',
    }
    _cols = ['Project', 'Vertical'] + list(_fmt.keys())
    df_top_apps_ltv = df_top_apps_ltv[_cols]

    _actual_rev = df_top_apps_ltv['Revenue (ETH) - Actual to Date'].sum()
    _total_ltv = df_top_apps_ltv['LTV (ETH)'].sum()
    _total_cac = df_top_apps_ltv['CAC (ETH)'].sum()
    _total_op_grants = df_top_apps_ltv['All Grants Amount (OP)'].sum()

    top_apps_ltv_headline = f"A total of {_total_op_grants:,.0f} OP (~{_total_cac:,.0f} ETH at current prices) has been provided as incentives to these protocols"

    mo.vstack([
        mo.md(f"""
        ### **{top_apps_ltv_headline}**

        These protocols have generated {_actual_rev:,.0f} ETH in revenues to date. If we assume each protocol maintains its past 90D in revenues over a {EXPECTED_LIFETIME}-month period, then their (combined) lifetime value could increase to {_total_ltv:,.0f} ETH
        """),
        mo.ui.table(
            data=df_top_apps_ltv,
            format_mapping=_fmt,
            show_data_types=False,
            show_column_summaries=False,
            page_size=20,
            freeze_columns_left=['Project', 'Vertical', 'LTV/CAC']
        )
    ])
    return compute_ltv_cac, df_top_apps_ltv


@app.cell(hide_code=True)
def _(compute_ltv_cac, df_ltv_cac_summary, mo):
    df_alls_apps_ltv = compute_ltv_cac(df_ltv_cac_summary)
    _fmt = {
        'All Grants Amount (OP)': '{:,.0f}',         
        'Protocol Age (Months)': '{:,.1f}',
        'Expected Lifetime (Months)': '{:,.1f}',
        'Revenue (ETH) - Actual to Date': '{:,.4f}',
        'Revenue (ETH) - Last 90D': '{:,.4f}',
        'Revenue (ETH) - Projected': '{:,.4f}',
        'LTV (ETH)': '{:,.4f}',
        'CAC (ETH)': '{:,.4f}',
        'LTV/CAC': '{:,.2f}',
    }
    _cols = ['Project', 'Vertical', 'Cohort'] + list(_fmt.keys())
    df_alls_apps_ltv = df_alls_apps_ltv[_cols]

    _actual_rev = df_alls_apps_ltv['Revenue (ETH) - Actual to Date'].sum()
    _total_ltv = df_alls_apps_ltv['LTV (ETH)'].sum()
    _total_cac = df_alls_apps_ltv['CAC (ETH)'].sum()
    _total_op_grants = df_alls_apps_ltv['All Grants Amount (OP)'].sum()
    _positive = len(df_alls_apps_ltv[df_alls_apps_ltv['LTV/CAC'] >= 1.0])
    _all_apps = len(df_alls_apps_ltv)

    all_apps_ltv_headline = f"Overall, a total of {_total_op_grants:,.0f} OP (~{_total_cac:,.0f} ETH at current prices) has been provided as incentives to defi protocols"

    mo.vstack([
        mo.md(f"""
        ### **{all_apps_ltv_headline}**

        Only {_positive:,.0f} (out of {_all_apps:,.0f}) have an LTV/CAC ratio above 1.0, using the assumptions described earlier.
        """),
        mo.ui.table(
            data=df_alls_apps_ltv,
            format_mapping=_fmt,
            show_data_types=False,
            show_column_summaries=False,
            page_size=20,
            freeze_columns_left=['Project', 'Vertical', 'LTV/CAC']
        )
    ])
    return (df_alls_apps_ltv,)


@app.cell(hide_code=True)
def _(OP_ETH_PRICE, df_alls_apps_ltv, mo):
    _df = df_alls_apps_ltv.groupby('Vertical', as_index=False).agg({
        'Project': 'nunique',
        'All Grants Amount (OP)': 'sum',
        'Revenue (ETH) - Actual to Date': 'sum',
        'Revenue (ETH) - Last 90D': 'sum',
        'Revenue (ETH) - Projected': 'sum'
    })
    _df.rename(columns={'Project': 'Project Count'}, inplace=True)
    _df['LTV (ETH)'] = _df['Revenue (ETH) - Projected'] + _df['Revenue (ETH) - Actual to Date']
    _df['CAC (ETH)'] = _df['All Grants Amount (OP)'] * OP_ETH_PRICE
    _df['LTV/CAC'] = _df['LTV (ETH)'] /  _df['CAC (ETH)']
    _df.sort_values(by='LTV/CAC', ascending=False, inplace=True)
    _fmt = {
        'All Grants Amount (OP)': '{:,.0f}',         
        'Revenue (ETH) - Actual to Date': '{:,.4f}',
        'Revenue (ETH) - Last 90D': '{:,.4f}',
        'Revenue (ETH) - Projected': '{:,.4f}',
        'LTV (ETH)': '{:,.4f}',
        'CAC (ETH)': '{:,.4f}',
        'LTV/CAC': '{:,.2f}',
    }

    vertical_ltv_headline = f"DEXs have been the only ROI-positive category"

    mo.vstack([
        mo.md(f"""
        ### **{vertical_ltv_headline}**
        Derivatives received the most grants overall from Optimism
        """),
        mo.ui.table(
            data=_df.reset_index(drop=True),
            format_mapping=_fmt,
            show_data_types=False,
            show_column_summaries=False,
            page_size=20,
            freeze_columns_left=['Vertical']
        )
    ])
    return


@app.cell
def _(df_alls_apps_ltv, df_top_apps_ltv, mo):
    mo.md(
        f"""
    - Total LTV/CAC: {df_alls_apps_ltv['LTV (ETH)'].sum() / df_alls_apps_ltv['CAC (ETH)'].sum():,.2f}
    - Blue-chips LTV/CAC {df_top_apps_ltv['LTV (ETH)'].sum() / df_top_apps_ltv['CAC (ETH)'].sum():,.2f}
    - Total Revenue: {df_alls_apps_ltv['Revenue (ETH) - Actual to Date'].sum():,.0f} ETH
    """
    )
    return


@app.cell(hide_code=True)
def _(df_project_metrics, df_tvl_grants_summary, go, np, pd, px):
    def rgba_from_rgb(rgb_value, alpha):
        rgb_value = rgb_value.strip()
        if rgb_value.startswith("rgb"):
            inside = rgb_value[rgb_value.find("(")+1:rgb_value.find(")")]
            parts = [p.strip() for p in inside.split(",")]
            return f"rgba({','.join(parts[:3])},{alpha})"
        rgb_value = rgb_value.lstrip("#")
        r = int(rgb_value[0:2], 16)
        g = int(rgb_value[2:4], 16)
        b = int(rgb_value[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    def make_superchain_tvl_joyplot(
        project_list,
        smoothing: int = 7,
        colorscale: str = "Reds",
        gap: float = 1.10,
        fill_alpha: float = 0.40,
        resample="7D",
        downsample_every=3,
        ridge_cap_quantile=0.98
    ):

        dfp = df_project_metrics.copy()
        grants = df_tvl_grants_summary.copy()

        # Map slug -> project Project
        slug_to_project = dict(zip(grants["OSO Slug"], grants["Project"]))
        dfp["Project"] = dfp["OSO Slug"].map(slug_to_project).fillna(dfp["OSO Slug"])

        # For quick lookups
        display_to_grant = grants.set_index("Project")
        display_to_slug = {v: k for k, v in slug_to_project.items()}

        # TVL series (7-day metric)
        tvl = dfp[dfp["Metric"] == "TVL (7D)"][["Date","OSO Slug","Project","Amount"]].copy()

        # Optional filter to provided list
        if project_list is not None:
            tvl = tvl[tvl["Project"].isin(list(project_list))]

        # Wide “actual TVL”
        wide = tvl.pivot_table(index="Date", columns="Project", values="Amount", aggfunc="sum").sort_index()

        # Resample / downsample / smooth so hover shows actual values
        if resample:
            wide = wide.resample(resample).mean()
        if downsample_every and downsample_every > 1:
            wide = wide.iloc[::downsample_every]
        if smoothing and smoothing > 1:
            wide = wide.rolling(window=smoothing, min_periods=1, center=True).mean()

        # Normalized copy for ridge heights (cap extreme spikes)
        wide_norm = wide.copy()
        for col in wide.columns:
            if (wide[col] > 0).sum() > 50:
                cap = float(wide[col].quantile(ridge_cap_quantile))
                wide_norm[col] = wide_norm[col].clip(upper=cap)
            denom = wide_norm[col].max(skipna=True)
            wide_norm[col] = (wide_norm[col] / denom) if (pd.notna(denom) and denom > 0) else 0.0

        # Order projects by absolute TVL uplift since first grant
        def _uplift_abs(display_name: str) -> float:
            s = wide.get(display_name)
            if s is None or s.dropna().empty:
                return -float("inf")
            grant_date = display_to_grant.loc[display_name, "First Grant Delivery Date"] if display_name in display_to_grant.index else pd.NaT
            if pd.isna(grant_date):
                return -float("inf")
            s_clean = s.dropna()
            baseline = float(s_clean[s_clean.index <= grant_date].iloc[-1]) if (s_clean.index <= grant_date).any() else 0.0
            current = float(s_clean.iloc[-1])
            return current - baseline

        cols_all = list(wide.columns)
        cols_sorted = sorted(cols_all, key=_uplift_abs, reverse=True)
        cols = cols_sorted[::-1]  # highest uplift at bottom in ridge plot

        # Colors
        cmap = getattr(px.colors.sequential, colorscale)
        cmap_subset = cmap[len(cmap)//2:][::-1]
        n = len(cols)
        proj_colors = {col: cmap_subset[int(round(i*(len(cmap_subset)-1)/max(1,n-1)))] for i,col in enumerate(cols)}

        # Right-side annotations: TVL Δ (in $MM) & Gas since grant
        fees = dfp[dfp["Metric"] == "Fees"][["Date","OSO Slug","Amount"]].copy()

        def _stats(display_name: str):
            s = wide.get(display_name)
            if s is None or s.dropna().empty:
                return np.nan, np.nan
            if display_name not in display_to_grant.index:
                return np.nan, np.nan
            gd = display_to_grant.loc[display_name, "First Grant Delivery Date"]
            if pd.isna(gd):
                return np.nan, np.nan

            s_clean = s.dropna()
            baseline = float(s_clean[s_clean.index <= gd].iloc[-1]) if (s_clean.index <= gd).any() else 0.0
            current = float(s_clean.iloc[-1])
            uplift_mm = (current - baseline)/1_000_000.0

            slug = display_to_slug.get(display_name)
            if slug is None:
                inc_gas = np.nan
            else:
                fproj = fees[fees["OSO Slug"] == slug]
                inc_gas = float(fproj[fproj["Date"] >= gd]["Amount"].sum())
            return uplift_mm, inc_gas

        uplift_map = {}
        gas_map = {}
        for dname in cols:
            u, g = _stats(dname)
            uplift_map[dname] = u
            gas_map[dname] = g

        # Build figure
        fig = go.Figure()
        tickvals, ticktext = [], []
        x_vals = wide_norm.index

        for i, col in enumerate(cols):
            y_offset = i*gap
            y_vals = wide_norm[col].reindex(x_vals).fillna(0).values
            color = proj_colors[col]
            fill_color = rgba_from_rgb(color, fill_alpha)

            # Baseline
            fig.add_trace(go.Scatter(
                x=x_vals, y=np.full(y_vals.shape, y_offset, dtype=float),
                mode="lines", line=dict(width=0), hoverinfo="skip", showlegend=False
            ))

            actual = wide[col].reindex(x_vals).values
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals + y_offset,
                mode="lines",
                fill="tonexty",
                line=dict(color=color, width=1.5),
                line_shape="spline",
                fillcolor=fill_color,
                name=col,
                customdata=np.c_[actual],
                hovertemplate="<b>%{fullData.name}</b><br>Date: %{x|%d %b %Y}<br>TVL: %{customdata[0]:,.0f}<extra></extra>",
                showlegend=False
            ))

            # Y tick labels
            tickvals.append(y_offset)
            ticktext.append(f"<b>{col}</b>")

            # Grant line + OP label
            if col in display_to_grant.index:
                gd = display_to_grant.loc[col, "First Grant Delivery Date"]
                if pd.notna(gd):
                    fig.add_shape(
                        type="line", x0=gd, x1=gd, y0=y_offset, y1=y_offset+1.0,
                        line=dict(color="rgba(0,0,0,0.65)", width=1)
                    )
                    op_amt = display_to_grant.loc[col, "First Grant Amount (OP)"]
                    if pd.notna(op_amt):
                        fig.add_annotation(
                            x=gd, xref="x",
                            y=y_offset+1.0, yref="y",
                            xanchor="center", yanchor="top",
                            xshift=6,
                            text=f"First Grant:<br>{int(op_amt/1000):,}K OP",
                            showarrow=False,
                            font=dict(size=10, color="#444"),
                            bgcolor="rgba(255,255,255,0.8)",
                            bordercolor="rgba(0,0,0,0.8)",
                            borderwidth=0.5
                        )

            # Right-edge metrics
            u = uplift_map.get(col, np.nan)
            g = gas_map.get(col, np.nan)
            labels = []
            if pd.notna(u):
                labels.append(f"+${u:,.0f}M TVL" if u > 0 else f"-${abs(u):,.0f}M TVL")
            if pd.notna(g):
                labels.append(f"<br>{g:,.1f} ETH fees")
            if labels:
                fig.add_annotation(
                    x=1, xref="x domain",
                    y=y_offset, yref="y", align='left',
                    xanchor="left", yanchor="bottom",
                    text="; ".join(labels),
                    showarrow=False,
                    font=dict(size=10, color="#333"),
                    bgcolor="rgba(255,255,255,0.6)"
                )

        # Layout polish
        fig.update_layout(
            height=1500,
            template="plotly_white",
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(size=12, color="#111"),
            margin=dict(l=160, r=160, t=0, b=0),
            showlegend=False,
            title=dict(text="", x=0, xanchor="left", font=dict(size=14, color="#111"))
        )
        fig.update_xaxes(title="", showgrid=False, visible=False, linecolor="#000", linewidth=1)
        fig.update_yaxes(
            title="",
            side="left",
            showgrid=False,
            tickmode="array",
            ticklabelposition="outside",
            ticklabelstandoff=5,
            tickvals=tickvals,
            ticktext=ticktext,
            zeroline=False,
            tickcolor="#000",
            showline=False
        )
        fig.update_traces(line_simplify=True)
        return fig
    return (make_superchain_tvl_joyplot,)


@app.cell(hide_code=True)
def _(df_top_apps_ltv, make_superchain_tvl_joyplot, mo):
    _projects = list(df_top_apps_ltv['Project'].unique())
    _fig = make_superchain_tvl_joyplot(
        project_list=_projects,
        downsample_every=1,
        resample='1D'
    )    

    mo.vstack([
        mo.md(f"""
        ### **Overlay of defi grants and Superchain TVL**

        This chart shows Superchain TVL over time, with annotations for when Foundation grants were made to the protocol
        """),
        mo.ui.plotly(_fig)
    ])

    return


@app.cell
def _(df_ltv_cac_summary, mo):
    select_cohort = mo.ui.dropdown(
        options=df_ltv_cac_summary['Cohort'].unique(),
        value='⚪️ Less Relevant Protocol',
        label='Select a cohort:'
    )
    select_cohort
    return (select_cohort,)


@app.cell
def _(df_ltv_cac_summary, make_superchain_tvl_joyplot, mo, select_cohort):
    _projects = list(df_ltv_cac_summary[df_ltv_cac_summary['Cohort'] == select_cohort.value]['Project'].unique())
    _fig = make_superchain_tvl_joyplot(
        project_list=_projects,
        downsample_every=1,
        resample='1D',
        colorscale='Blues'
    )    

    mo.vstack([
        mo.md(f"""
        ### **Overlay of defi grants and Superchain TVL by cohort**

        This chart shows Superchain TVL over time, with annotations for when Foundation grants were made to the protocol
        """),
        mo.ui.plotly(_fig)
    ])

    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Methodology / Analysis Details""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## ✅ Part 1. Get all relevant projects

    Compile a comprehensive list of all grants / incentives targeting TVL increases.

    Spreadsheet version: [here](https://docs.google.com/spreadsheets/d/1JUNyjEkbtsSTDGTni5sVhZI-mvTc9kofxDrQt3CahaY/edit).
    """
    )
    return


@app.cell(hide_code=True)
def _(mo, pd, pyoso_db_conn, stringify):
    # Include direct grants (from CSV)
    _df_direct_grants = pd.DataFrame([
      {
        "Counterparty":"Oath Financial (Ethos)",
        "Project":"Oath Financial (Ethos)",
        "GrantID":"PAR0094",
        "Fund Name":"Partner",
        "Grant Type":"DeFi Applications",
        "Category":"DeFI Applications & Tooling",
        "ROI Driver":"TVL Growth",
        "Analysis Template":"TVL Incentives",
        "Agreement Date":" 02-Mar-2023",
        "Allocated (Escrow) Date":" 27-Jun-2024",
        "Circulating Supply Date":" 01-Jun-2024",
        "Total Grant (OP)": 1500000,
        "USD Value at Time of Agreement": 4000000,
        "OP Price: Agreement Date": 2.72,
        "OSO Slug": "byte-masons-ethos-reserve"
      },
      {
        "Counterparty":"Lido",
        "Project":"Lido",
        "GrantID":"PAR0033",
        "Fund Name":"Partner",
        "Grant Type":"DeFi Applications",
        "Category":"DeFI Applications & Tooling",
        "ROI Driver":"TVL Growth",
        "Analysis Template":"TVL Incentives",
        "Agreement Date":" 01-Mar-2023",
        "Allocated (Escrow) Date":" 03-Mar-2023",
        "Circulating Supply Date":" 01-Mar-2023",
        "Total Grant (OP)": 1000000,
        "USD Value at Time of Agreement": 3000000,
        "OP Price: Agreement Date": 2.77,
        "OSO Slug": "lido" 
      },
      {
        "Counterparty":"Exactly Protocol",
        "Project":"Exactly Protocol",
        "GrantID":"PAR0026",
        "Fund Name":"Partner",
        "Grant Type":"DeFi Applications",
        "Category":"DeFI Applications & Tooling",
        "ROI Driver":"TVL Growth",
        "Analysis Template":"TVL Incentives",
        "Agreement Date":" 23-Feb-2023",
        "Allocated (Escrow) Date":" 10-Mar-2023",
        "Circulating Supply Date":" 01-Mar-2023",
        "Total Grant (OP)": 600000,
        "USD Value at Time of Agreement": 2000000,
        "OP Price: Agreement Date": 2.88,
        "OSO Slug": "exactly"   
      }
    ])
    # Get Grants Council (Gov Fund) grants to all DeFi projects
    _df_tvl_grants = mo.sql("""
        WITH projects_with_tvl AS (
          SELECT oso_project_name
          FROM int_optimism_grants_metrics_by_project
          WHERE
            metric_event_source_category = 'SUPERCHAIN'
            AND metric_model = 'defillama_tvl'
            AND metric_time_aggregation = 'daily'
          GROUP BY oso_project_name
          HAVING MAX(amount) >= 1000000 -- ONLY CONSIDER PROJECTS WITH AT LEAST $1M TVL ON THE SUPERCHAIN (AT SOME POINT)
        )
        SELECT
          oso_project_name AS "OSO Slug",
          oso_project_display_name AS "Project",
          initial_delivery_date AS "Delivery Date",
          'Gov' AS "Fund Name",
          grant_round AS "Season",
          amount_op AS "Amount (OP)",
          amount_usd AS "Amount (USD)"
        FROM int_optimism_grants
        JOIN projects_with_tvl USING oso_project_name    
        WHERE
          grant_mechanism = 'GRANTS_COUNCIL'
          AND initial_delivery_date IS NOT NULL
        ORDER BY
          oso_project_display_name ASC,
          initial_delivery_date ASC
        """,
        engine=pyoso_db_conn,
        output=False
    )

    # Consolidate the data
    _df_tvl_grants['Delivery Date'] = pd.to_datetime(_df_tvl_grants['Delivery Date'])
    _df_tvl_grants['Season'] = _df_tvl_grants['Season'].apply(lambda x: x[-1])
    _df_direct_grants['Delivery Date'] = pd.to_datetime(_df_direct_grants['Allocated (Escrow) Date'])
    _df_direct_grants['Season'] = 0
    _df_direct_grants['Amount (OP)'] = _df_direct_grants['Total Grant (OP)']
    _df_direct_grants['Amount (USD)'] = round(_df_direct_grants['Amount (OP)'] *  _df_direct_grants['OP Price: Agreement Date'],0)
    _df_direct_grants = _df_direct_grants[['OSO Slug', 'Project', 'Delivery Date', 'Fund Name', 'Season', 'Amount (OP)', 'Amount (USD)']]
    df_tvl_grants_all = pd.concat([_df_tvl_grants, _df_direct_grants], axis=0, ignore_index=True)

    # Get project verticals
    _df_tvl_verticals = mo.sql(
        f"""
        SELECT
          oso_project_name AS "OSO Slug",
          best_vertical AS "Vertical",
          all_categories AS "Vertical Tags"
        FROM int_optimism_grants_to_defi_projects
        WHERE oso_project_name IN ({stringify(df_tvl_grants_all['OSO Slug'])})
        """,
        engine=pyoso_db_conn,
        output=False
    )

    # Generate grants summary table
    _agg_df = (
        df_tvl_grants_all.sort_values('Delivery Date')
          .groupby(['OSO Slug', 'Project'], as_index=False)
          .agg(
              count_grants=('Delivery Date', 'count'),
              delivery_date_of_first_grant=('Delivery Date', 'min'),
              all_grants_amount_op=('Amount (OP)', 'sum'),
              all_grants_amount_usd=('Amount (USD)', 'sum')
          )
          .rename(columns={
              'count_grants': 'Num Grants',
              'delivery_date_of_first_grant': 'First Grant Delivery Date',
              'all_grants_amount_op': 'All Grants Amount (OP)',
              'all_grants_amount_usd': 'All Grants Amount (USD)'
          })
    )
    _min_by = (
        df_tvl_grants_all.loc[df_tvl_grants_all.groupby(['OSO Slug', 'Project'])['Delivery Date'].idxmin(), 
               ['OSO Slug', 'Project', 'Season', 'Amount (OP)', 'Amount (USD)']]
        .rename(columns={
            'Season': 'First Grant Season',
            'Amount (OP)': 'First Grant Amount (OP)',
            'Amount (USD)': 'First Grant Amount (USD)'
        })
    )

    df_tvl_grants_summary = _agg_df.merge(_min_by, on=['OSO Slug', 'Project']).merge(_df_tvl_verticals, on=['OSO Slug'], how='left')
    return df_tvl_grants_all, df_tvl_grants_summary


@app.cell(hide_code=True)
def _(df_tvl_grants_all, df_tvl_grants_summary, mo):
    mo.vstack([
        mo.md("#### Summary"),
        mo.ui.table(data=df_tvl_grants_summary, show_column_summaries=False, show_data_types=False),
        mo.md("#### Detailed grants"),
        mo.ui.table(data=df_tvl_grants_all, show_column_summaries=False, show_data_types=False)
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## ✅ Part 2. Get key metrics at different intervals for all relevent projects

    Process: 

    - Get Superchain metrics for each project
    - Calculate 7 day trailing averages for TVL
    """
    )
    return


@app.cell(hide_code=True)
def _(
    METRIC_NAME_MAP,
    df_tvl_grants_summary,
    mo,
    pd,
    pyoso_db_conn,
    stringify,
):
    _query = f"""
        SELECT
          sample_date AS "Date",
          chain AS "Chain",
          oso_project_name AS "OSO Slug",
          metric AS "Metric",
          amount AS "Amount"  
        FROM int_optimism_grants_rolling_defi_metrics_by_project
        WHERE
          oso_project_name IN ({stringify(df_tvl_grants_summary['OSO Slug'])})
          AND metric IN ({stringify(METRIC_NAME_MAP.keys())})
    """
    df_project_metrics_by_chain = mo.sql(_query, engine=pyoso_db_conn, output=False)

    df_project_metrics_by_chain['Date'] = pd.to_datetime(df_project_metrics_by_chain['Date'])
    df_project_metrics_by_chain['Metric'] = df_project_metrics_by_chain['Metric'].map(METRIC_NAME_MAP)

    df_project_metrics = df_project_metrics_by_chain.groupby(['Date', 'OSO Slug', 'Metric'], as_index=False)['Amount'].sum()
    return df_project_metrics, df_project_metrics_by_chain


@app.cell(hide_code=True)
def _(df_project_metrics_by_chain, mo):
    sample_project = mo.ui.dropdown(
        options=sorted(df_project_metrics_by_chain['OSO Slug'].unique()),
        value='velodrome',
        label='Select a project:'
    )
    sample_metric = mo.ui.dropdown(
        options=sorted(df_project_metrics_by_chain['Metric'].unique()),
        value='TVL (7D)',
        label='Select a metric:'
    )

    mo.vstack([
        mo.md("#### Sanity check"),
        mo.hstack(
            [sample_project, sample_metric],
            align="stretch",
            justify="start",
            gap=2,
        )
    ])
    return sample_metric, sample_project


@app.cell(hide_code=True)
def _(
    EVALUATION_DATE,
    PLOTLY_LAYOUT,
    df_project_metrics,
    df_project_metrics_by_chain,
    mo,
    px,
    sample_metric,
    sample_project,
):
    _d1 = df_project_metrics_by_chain[(df_project_metrics_by_chain['OSO Slug'] == sample_project.value) & (df_project_metrics_by_chain['Metric'] == sample_metric.value)]
    _f = px.area(data_frame=_d1, x='Date', y='Amount', color='Chain')
    _f.update_layout(**PLOTLY_LAYOUT)

    _d2 = df_project_metrics[(df_project_metrics['OSO Slug'] == 'velodrome') & (df_project_metrics['Date'] == EVALUATION_DATE)]

    mo.vstack([
        mo.ui.plotly(_f),
        mo.md("#### Sanity check: sample metrics for Velodrome on 2025-09-30"),
        mo.ui.table(data=_d2.reset_index(drop=True), show_column_summaries=False, show_data_types=False),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## ✅ Part 3. Measure metrics at monthly intervals from the date of the first grant

    Process: 

    - Define relevant intervals from the date of the first grant delivery (currently: 1-36 months)
    - Calculate TVL uplift (7 day trailing average) from the grant delivery date to the time interval we care about
    - Also calculate incremental gas fees and contract invocations over the same time interval
    - Join on relevant project / grant metadata
    """
    )
    return


@app.cell(hide_code=True)
def _(
    EVALUATION_DATE,
    METRIC_NAME_MAP,
    MONTH_RANGE,
    df_project_metrics,
    df_tvl_grants_summary,
    np,
    pd,
    relativedelta,
):
    def summarize_results(df_grants, df_project_metrics):
        """Calculate metrics at monthly intervals from first grant delivery."""
        _df_g = df_grants.copy()
        _df_pm = df_project_metrics.copy()

        # Parse dates
        _df_pm['Date'] = pd.to_datetime(_df_pm['Date']).dt.tz_localize(None)
        _df_g['First Grant Delivery Date'] = pd.to_datetime(_df_g['First Grant Delivery Date']).dt.tz_localize(None)

        # Map OSO Slug → Project
        _slug_to_project = _df_g[['OSO Slug', 'Project']].drop_duplicates()
        _df_pm = _df_pm.merge(_slug_to_project, on='OSO Slug', how='left')

        # Evaluation offsets: 0..36 (0 for baseline, 1-36 monthly anniversaries)
        _rows = []
        for _, _r in _df_g[['Project', 'First Grant Delivery Date']].iterrows():
            _start = _r['First Grant Delivery Date']
            for _m in MONTH_RANGE:
                _rows.append({'Project': _r['Project'], 'Months': _m, 'Point Date': _start + relativedelta(months=_m)})
        _df_points = pd.DataFrame(_rows)

        # TVL (7D) values on each Point Date
        _tvl7 = (
            _df_pm[_df_pm['Metric'] == 'TVL (7D)'][['Project', 'Date', 'Amount']]
            .rename(columns={'Date': 'Point Date', 'Amount': 'TVL (7D)'})
        )
        _df_points = _df_points.merge(_tvl7, on=['Project', 'Point Date'], how='left')

        # Pivot to wide with Month i TVL for i=0..36
        _tvl_wide = _df_points.pivot_table(index='Project', columns='Months', values='TVL (7D)', aggfunc='first')
        if 0 in _tvl_wide.columns:
            _tvl_wide[0] = _tvl_wide[0].fillna(0).astype(float)

        # Rename to "Month i TVL"
        _tvl_rename = {_m: (f'Month {_m} TVL' if _m != 0 else 'Month 0 TVL') for _m in _tvl_wide.columns}
        _tvl_wide = _tvl_wide.rename(columns=_tvl_rename)

        # Add "Month i TVL Uplift" for i=1..36 vs Month 0
        for _m in range(1, 37):
            _base_col = 'Month 0 TVL'
            if _base_col in _tvl_wide.columns and f'Month {_m} TVL' in _tvl_wide.columns:
                _tvl_wide[f'Month {_m} TVL Uplift'] = _tvl_wide[f'Month {_m} TVL'] - _tvl_wide[_base_col]

        _tvl_wide = _tvl_wide.reset_index()

        # Cumulative metrics monthly (1..36)
        _sum_df = _df_pm[_df_pm['Metric'].isin(METRIC_NAME_MAP.values())][['Project', 'Date', 'Metric', 'Amount']]
        _sum_df = _sum_df.merge(_df_g[['Project', 'First Grant Delivery Date']], on='Project', how='left')
        _sum_df = _sum_df[_sum_df['Date'] >= _sum_df['First Grant Delivery Date']].copy()

        _targets = _df_points[['Project', 'Months', 'Point Date']].copy()

        _agg_pieces = []
        for _mname in METRIC_NAME_MAP.values():
            if _mname == 'TVL':
                continue
            if '(7D)' in _mname:
                continue
            _dfm = _sum_df[_sum_df['Metric'] == _mname].copy()

            _dfm = _dfm.groupby(['Project', 'Date'], as_index=False)['Amount'].sum().sort_values(['Project', 'Date'])
            _dfm['Cumulative Amount'] = _dfm.groupby('Project', observed=True)['Amount'].cumsum()

            _bounds = _dfm.groupby('Project')['Date'].agg(First='min', Last='max').reset_index()

            _tmp = _targets.merge(_dfm[['Project', 'Date', 'Cumulative Amount']], on='Project', how='left')
            _tmp = _tmp[_tmp['Date'] < _tmp['Point Date']]
            _tmp = (
                _tmp.sort_values(['Project', 'Point Date', 'Date'])
                   .groupby(['Project', 'Point Date'], as_index=False)
                   .tail(1)[['Project', 'Point Date', 'Cumulative Amount']]
            )

            _out = _targets.merge(_tmp, on=['Project', 'Point Date'], how='left').merge(_bounds, on='Project', how='left')
            _out['Cumulative Amount'] = np.where(
                _out['Point Date'] <= _out['First'], 0,
                np.where(_out['Point Date'] > _out['Last'], np.nan, _out['Cumulative Amount'])
            )

            # Pivot monthly 0..N then rename all (skip 0; cumulative-at-grant is not needed)
            _piece = _out.pivot_table(index='Project', columns='Months', values='Cumulative Amount', aggfunc='last')
            # Keep only Month 1..N named columns
            _keep_cols = [f'Month {_m} {_mname}' for _m in range(1, 37) if f'Month {_m} {_mname}' in _piece.columns]
            _piece = _piece[_keep_cols].reset_index()
            _agg_pieces.append(_piece)

        _agg_all = None
        for _p in _agg_pieces:
            _agg_all = _p if _agg_all is None else _agg_all.merge(_p, on='Project', how='outer')
        if _agg_all is None:
            _agg_all = pd.DataFrame({'Project': _df_g['Project'].unique()})

        # Current TVL (7D) as of EVALUATION_DATE (last value on/before)
        _as_of = pd.Timestamp(EVALUATION_DATE)
        _tvl_asof = (
            _df_pm[(_df_pm['Metric'] == 'TVL (7D)') & (_df_pm['Date'] <= _as_of)]
            .sort_values(['Project', 'Date'])
            .groupby('Project', as_index=False)
            .tail(1)[['Project', 'Amount']]
            .rename(columns={'Amount': 'Current TVL (7D)'})
        )

        # Final merge (includes All Grants and Vertical already present in _df_g)
        _final_cols = [
            'OSO Slug', 'Project', 'Vertical',
            'Num Grants', 'All Grants Amount (OP)', 'All Grants Amount (USD)',
            'First Grant Delivery Date', 'First Grant Season', 'First Grant Amount (OP)', 'First Grant Amount (USD)'
        ]
        _final = (
            _df_g[_final_cols]
            .merge(_tvl_wide, on='Project', how='left')
            .merge(_agg_all, on='Project', how='left')
            .merge(_tvl_asof, on='Project', how='left')
            .reset_index(drop=True)
        )

        # Incremental columns: choose deepest month with data using Contract Invocations (1..36)
        _months_desc = list(range(36, 0, -1))
        _tvl_cols = {_m: f'Month {_m} TVL Uplift' for _m in _months_desc}
        _gas_cols = {_m: f'Month {_m} Revenue' for _m in _months_desc}
        _inv_cols = {_m: f'Month {_m} Userops' for _m in _months_desc}

        def _pick_month(row):
            for _m in _months_desc:
                _v = row.get(_inv_cols[_m])
                if pd.notna(_v):
                    return _m
            return np.nan

        _final['Incremental Months'] = _final.apply(_pick_month, axis=1)

        def _get_value(row, colmap):
            _m = row['Incremental Months']
            if pd.isna(_m):
                return np.nan
            return row.get(colmap[int(_m)])

        _final['Incremental TVL'] = _final.apply(lambda r: _get_value(r, _tvl_cols), axis=1)
        _final['Incremental Revenue'] = _final.apply(lambda r: _get_value(r, _gas_cols), axis=1)
        _final['Incremental Invocations'] = _final.apply(lambda r: _get_value(r, _inv_cols), axis=1)

        # Clean up any stray merge remnants, if present
        for _c in ['0_x', '0_y']:
            if _c in _final.columns:
                _final.drop(columns=[_c], inplace=True)

        return _final

    df_analysis = summarize_results(df_grants=df_tvl_grants_summary, df_project_metrics=df_project_metrics)   
    return (df_analysis,)


@app.cell(hide_code=True)
def _(df_analysis, df_tvl_grants_summary, mo):
    _incremental_cols = [c for c in df_analysis.columns if 'Incremental' in c]
    _value_cols = [c for (c,d) in df_analysis.dtypes.items() if d in ('int64', 'float64')]
    _metadata_cols = [c for c in df_analysis.columns if c in df_tvl_grants_summary.columns]

    _month_cols = []
    for _x in (3,6,12,24,36):
        for _y in ('TVL', 'TVL Uplift', 'Revenues', 'Userops'):
            _month_cols.append(f'Month {_x} {_y}')

    _cols = _metadata_cols + _incremental_cols + _month_cols

    _fmt = {
        c: '{:,.1f}' if 'Rev' in c else '{:,.0f}'
        for c in _cols
        if c in _value_cols
    }
    mo.ui.table(
        data=(
            df_analysis#[_cols]
            .drop(columns=['OSO Slug'])
            .sort_values(by='Incremental TVL', ascending=False)
            .reset_index(drop=True)
        ),
        format_mapping=_fmt,
        freeze_columns_left=['Project', 'Vertical'],
        show_column_summaries=False,
        show_data_types=False,
        page_size=10
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## ✅ Part 4: Benchmark performance metrics by month since grant

    Process:

    - Use the same 3,6 ... 24, 36 month intervals as in Part 3
    - Take each key metric and divide by the first grant amount
    - Apply simple percentiles (0.25, 0.50, 0.75)
    """
    )
    return


@app.cell(hide_code=True)
def _(go, pd):
    def make_performance_bands(
        data,
        vertical: str|None=None,
        top_quantile=0.75,
        bottom_quantile=0.25,
        value_col="Revshare Estimate",
        month_col="Months Since Grant",
        project_col="Project",
        vertical_col="Vertical",
        show_project_traces=True
    ):
        df = pd.DataFrame(data)[[project_col, vertical_col, month_col, value_col]].copy()
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
        if vertical:
            df = df[df[vertical_col].str.lower()==vertical.lower()].copy()

        df["Month Label"] = df[month_col].astype(int).map(lambda x: f"Month {x}")

        def _agg(g):
            nonnull = g[g[value_col].notna()]
            return pd.Series({
                "Mean": g[value_col].mean(skipna=True),
                "Top Threshold": g[value_col].quantile(top_quantile, interpolation="linear"),
                "Bottom Threshold": g[value_col].quantile(bottom_quantile, interpolation="linear"),
                "N Projects": nonnull[project_col].nunique()
            })

        summary = (
            df.groupby([month_col,"Month Label"], as_index=False, observed=True)
              .apply(_agg)
              .reset_index(drop=True)
              .sort_values(month_col)
        )
        cat_order = summary["Month Label"].tolist()

        band_fill="rgba(33,150,243,0.10)"
        top_line="rgba(33,150,243,1.00)"
        bot_line="rgba(244,67,54,1.00)"
        mean_line="rgba(0,0,0,0.75)"

        fig = go.Figure()

        if show_project_traces:
            for proj, g in df.groupby(project_col):
                gg = g.sort_values(month_col)
                fig.add_trace(go.Scatter(
                    x=gg["Month Label"], y=gg[value_col], mode="lines",
                    line=dict(width=1), name=proj, opacity=0.3,
                    hovertemplate=f"{proj}: %{{y:.2f}} ETH<extra></extra>", showlegend=False
                ))

        fig.add_trace(go.Scatter(x=summary["Month Label"], y=summary["Top Threshold"], mode="lines",
                                 line=dict(width=0), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=summary["Month Label"], y=summary["Bottom Threshold"], mode="lines",
                                 line=dict(width=0), fill="tonexty", fillcolor=band_fill,
                                 name="Average (25th–75th)", hoverinfo="skip", showlegend=False))

        fig.add_trace(go.Scatter(x=summary["Month Label"], y=summary["Bottom Threshold"], mode="lines",
                                 line=dict(width=2, color=bot_line), name="Bottom Threshold (25th)",
                                 hovertemplate="Bottom ≤ %{y:.2f} ETH<extra></extra>"))
        fig.add_trace(go.Scatter(x=summary["Month Label"], y=summary["Mean"], mode="lines",
                                 line=dict(width=2, dash="dash", color=mean_line), name="Mean",
                                 hovertemplate="Mean: %{y:.2f} ETH<extra></extra>"))
        fig.add_trace(go.Scatter(x=summary["Month Label"], y=summary["Top Threshold"], mode="lines",
                                 line=dict(width=2, color=top_line), name="Top Threshold (75th)",
                                 hovertemplate="Top ≥ %{y:.2f} ETH<extra></extra>"))

        fig.update_layout(
            title="",
            template="simple_white", paper_bgcolor="white", plot_bgcolor="white",
            legend=dict(orientation="v", yanchor="top", y=1.0, xanchor="left", x=0.01),
            margin=dict(l=0, r=0, t=0, b=0),
            hovermode="x unified",
            xaxis=dict(type="category", categoryorder="array", categoryarray=cat_order)
        )
        fig.update_xaxes(title="Months Since Grant", range=[0,None])
        fig.update_yaxes(title="Revshare Estimate", range=[0,None])

        # Optional: show N Projects in the hover (uses the corrected count)
        fig.add_trace(go.Scatter(
            x=summary["Month Label"], y=[None]*len(summary), mode="markers",
            marker=dict(opacity=0), showlegend=False,
            hovertemplate="N Projects: %{customdata}<extra></extra>",
            customdata=summary["N Projects"]
        ))

        return fig, summary
    return


@app.cell(hide_code=True)
def _(np, pd):
    def benchmark_performance_by_month(df_analysis, month):

        tvl_col = f"Month {month} TVL Uplift"
        gas_col = f"Month {month} Revshare Estimate"
        inv_col = f"Month {month} Contract Invocations"
        op_col = "First Grant Amount (OP)"

        if not all(c in df_analysis.columns for c in [tvl_col, gas_col, inv_col, op_col]):
            raise KeyError(f"Missing required columns for month {month}")

        base = df_analysis[df_analysis[op_col] > 0].copy()

        tvl_per_op = base[tvl_col] / base[op_col]
        gas_per_op = base[gas_col] / base[op_col]
        inv_per_op = base[inv_col] / base[op_col]

        ratios = {
            "TVL uplift / OP": tvl_per_op.replace([np.inf, -np.inf], np.nan).dropna(),
            "Revenue / OP": gas_per_op.replace([np.inf, -np.inf], np.nan).dropna(),
            "Invocations / OP": inv_per_op.replace([np.inf, -np.inf], np.nan).dropna(),
        }

        rows = []
        for label, s in ratios.items():
            if s.empty:
                rows.append({"Metric": label, "Bottom 75% (P25)": np.nan, "Median (P50)": np.nan, "Top 25% (P75)": np.nan, "N": 0})
                continue
            q = s.quantile([0.25, 0.5, 0.75])
            rows.append({
                "Metric": label,
                "Bottom 75% (P25)": q.loc[0.25],
                "Median (P50)": q.loc[0.5],
                "Top 25% (P75)": q.loc[0.75],
                "N": int(s.shape[0])
            })

        out = pd.DataFrame(rows)
        out.insert(0, "Month", month)
        return out
    return


@app.cell
def _():
    # This section is currently disabled until we correctly re-map the metric names

    # months = [3,6,12,18,24,36]
    # summary_all = pd.concat([benchmark_performance_by_month(df_analysis, m) for m in months], ignore_index=True)
    # summary_all = summary_all.sort_values(by=['Metric', 'Month']).reset_index(drop=True)

    # mo.vstack([
    #     mo.md("#### Sample benchmarks"),
    #     mo.ui.table(
    #         data=summary_all,
    #         show_column_summaries=False,
    #         show_data_types=False,
    #         page_size=25
    #     )
    # ])
    return


@app.cell
def _():
    # ============================================================================
    # SECTION 4: GLOBAL SETTINGS
    # ============================================================================
    return


@app.cell
def _():
    EVALUATION_DATE = '2025-09-30'
    EXPECTED_LIFETIME = 60 # Months
    OP_ETH_PRICE = (0.7/4500)

    MONTH_INTERVALS = [3, 6, 12, 18, 24, 36]
    MONTH_RANGE = range(0, 37)

    MIN_TVL_THRESHOLD = 1_000_000  # Minimum TVL to include projects in analysis
    DEFAULT_MIN_TVL = 100_000_000
    DEFAULT_MIN_GRANT_OP = 100_000
    DEFAULT_MIN_GRANT_USD = 100_000
    QUANTILES = {'top': 0.75, 'bottom': 0.25}
    METRIC_NAME_MAP = {
        'fees': 'Fees',
        'fees_7day': 'Fees (7D)',
        'revenue': 'Revenue',
        'revenue_7day': 'Revenue (7D)',
        'userops': 'Userops',
        'userops_7day': 'Userops (7D)',
        'tvl': 'TVL',
        'tvl_7day': 'TVL (7D)'
    }
    COHORT_SUMMARY_COLUMNS = [
        'Project', 'Vertical', 
        'Annualized Revenue (ETH)', 'Current TVL (7D)', 'Annualized Revenue per Million TVL',
        'All Grants Amount (OP)', 'All Grants Amount (USD)',
        'First Grant Delivery Date', 'First Grant Amount (OP)', 'First Grant Amount (USD)',
        'Incremental Months', 'Incremental TVL', 'Incremental Revenue', 'Incremental Invocations',
        'Avg Revenue (Gwei) per Invocation',
    ]

    COHORT_SUMMARY_FORMAT = {
        'First Grant Delivery Date': '{:%Y-%m-%d}',
        'Annualized Revenue (ETH)': '{:,.2f}',
        'Current TVL (7D)': '{:,.0f}',
        'Avg Revenue (Gwei) per Invocation': '{:,.0f}',
        'All Grants Amount (OP)': '{:,.0f}',
        'All Grants Amount (USD)': '{:,.0f}',
        'First Grant Amount (OP)': '{:,.0f}',
        'First Grant Amount (USD)': '{:,.0f}',
        'Incremental TVL': '{:,.0f}',
        'Incremental Revenue': '{:,.2f}',
        'Incremental Invocations': '{:,.0f}',
        'Annualized Revenue per Million TVL': '{:,.2f}',
    }
    return (
        EVALUATION_DATE,
        EXPECTED_LIFETIME,
        METRIC_NAME_MAP,
        MONTH_RANGE,
        OP_ETH_PRICE,
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
            orientation="v",
            yanchor="top", y=0.98,
            xanchor="left", x=0.02,
            bordercolor="black", borderwidth=1,
            bgcolor="white"
        ),
        xaxis=dict(
            title="",
            showgrid=False,
            linecolor="#000", linewidth=1,
            ticks="outside", tickformat="%b %Y"
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


@app.cell
def _():
    # ============================================================================
    # SECTION 5: BOILERPLATE
    # ============================================================================
    return


@app.cell(hide_code=True)
def _():
    stringify = lambda arr: "'" + "','".join(arr) + "'"
    return (stringify,)


@app.cell(hide_code=True)
def _():
    from dateutil.relativedelta import relativedelta
    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    return go, make_subplots, np, pd, px, relativedelta


@app.cell(hide_code=True)
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
