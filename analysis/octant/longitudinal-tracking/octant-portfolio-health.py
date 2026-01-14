import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Octant Project Portfolio: Tracking OSS Activity Through Open Data
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-12</span></small>
    """)
    return


@app.cell(hide_code=True)
def _(
    headline_1,
    headline_2,
    headline_3,
    headline_4,
    headline_5,
    headline_6,
    headline_7,
    headline_8,
    headline_treemap,
    mo,
):
    mo.md(f"""
    ## Context

    This analysis examines the health and impact of Octant's grant portfolio across all funding epochs.
    All amounts are displayed in **ETH**. Developer metrics are based on GitHub activity data.

    > **Open Data**: Every metric in this analysis is derived from publicly accessible sources and can be independently verified. See [Methodology](#methodology-details) for details.

    ## Sources

    - [OSO](https://docs.oso.xyz/) 
    - [OSS Funding](https://github.com/opensource-observer/oss-funding)
    - [OpenDevData](https://opendevdata.org/)
    """)
    return


@app.cell(hide_code=True)
def _(
    PLOTLY_LAYOUT,
    TIER_COLORS,
    df_funding_with_tiers,
    mo,
    pd,
    px,
    sort_epochs,
):
    # Calculate totals
    _total_eth = df_funding_with_tiers['amount_eth'].sum()

    # Aggregate by epoch for chart
    _df_by_epoch = (
        df_funding_with_tiers
        .groupby('octant_epoch', as_index=False)['amount_eth']
        .sum()
    )
    # Sort epochs numerically
    _epochs_sorted = sort_epochs(_df_by_epoch['octant_epoch'].unique())
    _df_by_epoch['octant_epoch'] = pd.Categorical(_df_by_epoch['octant_epoch'], categories=_epochs_sorted, ordered=True)
    _df_by_epoch = _df_by_epoch.sort_values('octant_epoch')

    # Find peak epoch
    _peak_idx = _df_by_epoch['amount_eth'].idxmax()
    _peak_epoch = _df_by_epoch.loc[_peak_idx, 'octant_epoch']
    _peak_eth = _df_by_epoch.loc[_peak_idx, 'amount_eth']
    _avg_eth = _df_by_epoch['amount_eth'].mean()

    headline_1 = f"Where did Octant's {_total_eth:,.0f} ETH go?"

    _fig = px.bar(
        _df_by_epoch,
        x='octant_epoch',
        y='amount_eth',
        category_orders={'octant_epoch': _epochs_sorted},
        labels={'octant_epoch': 'Epoch', 'amount_eth': 'ETH Allocated'}
    )
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_traces(marker_color=TIER_COLORS['Active Development'])

    # Add average reference line
    _fig.add_hline(
        y=_avg_eth, line_dash="dash", line_color="gray",
        annotation_text=f"Avg: {_avg_eth:.0f} ETH",
        annotation_position="right"
    )

    # Annotate peak
    _fig.add_annotation(
        x=_peak_epoch, y=_peak_eth,
        text=f"Peak: {_peak_eth:.0f} ETH",
        showarrow=True, arrowhead=2, ay=-40
    )

    mo.vstack([
        mo.md(f"### **{headline_1}**"),
        mo.md(f"Funding peaked at **{_peak_epoch}** with {_peak_eth:,.0f} ETH. The average per epoch is {_avg_eth:,.0f} ETH."),
        _fig
    ])
    return (headline_1,)


@app.cell(hide_code=True)
def _(
    PLOTLY_LAYOUT,
    TIER_COLORS,
    TIER_ORDER,
    df_funding_with_tiers,
    df_project_tiers,
    mo,
    px,
):
    # INSIGHT 2: Tier distribution + Funding by tier (side-by-side) - introduces the tier concept

    # Count projects by tier
    _tier_counts = (
        df_project_tiers
        .groupby('tier_label', as_index=False)
        .size()
        .rename(columns={'size': 'project_count'})
    )

    _total_projects = _tier_counts['project_count'].sum()
    _active_count = _tier_counts[_tier_counts['tier_label'] == 'Active Development']['project_count'].sum()
    _mature_count = _tier_counts[_tier_counts['tier_label'] == 'Mature/Stable']['project_count'].sum()
    _no_oss_count = _tier_counts[_tier_counts['tier_label'] == 'No OSS Footprint']['project_count'].sum()
    _software_proj_pct = ((_active_count + _mature_count) / _total_projects * 100) if _total_projects > 0 else 0

    # Aggregate funding by tier
    _tier_funding = (
        df_funding_with_tiers
        .groupby('tier_label', as_index=False)['amount_eth']
        .sum()
    )
    _total_eth = _tier_funding['amount_eth'].sum()
    _active_eth = _tier_funding[_tier_funding['tier_label'] == 'Active Development']['amount_eth'].sum()
    _mature_eth = _tier_funding[_tier_funding['tier_label'] == 'Mature/Stable']['amount_eth'].sum()
    _software_eth = _active_eth + _mature_eth
    _software_eth_pct = (_software_eth / _total_eth * 100) if _total_eth > 0 else 0

    headline_2 = f"What types of projects is Octant funding?"

    # Chart 1: Project counts by tier
    _fig1 = px.bar(
        _tier_counts,
        x='tier_label',
        y='project_count',
        color='tier_label',
        color_discrete_map=TIER_COLORS,
        category_orders={'tier_label': TIER_ORDER},
        labels={'tier_label': '', 'project_count': 'Projects'}
    )
    _fig1.update_layout(**PLOTLY_LAYOUT)
    _fig1.update_layout(showlegend=False, title="Project Count by Type", title_x=0.5)

    # Chart 2: ETH by tier
    _fig2 = px.bar(
        _tier_funding,
        x='tier_label',
        y='amount_eth',
        color='tier_label',
        color_discrete_map=TIER_COLORS,
        category_orders={'tier_label': TIER_ORDER},
        labels={'tier_label': '', 'amount_eth': 'ETH'}
    )
    _fig2.update_layout(**PLOTLY_LAYOUT)
    _fig2.update_layout(showlegend=False, title="ETH Allocated by Type", title_x=0.5)

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_2}**

    **{_active_count}** projects are actively developing, **{_mature_count}** are mature/stable, 
    and **{_no_oss_count}** have no matched OSS footprint.

    **{_software_proj_pct:.0f}%** of projects have meaningful OSS activity, and they receive **{_software_eth_pct:.0f}%** of funding ({_software_eth:,.0f} ETH).
    """),
        mo.hstack([_fig1, _fig2], justify="center", gap=2)
    ])
    return (headline_2,)


@app.cell(hide_code=True)
def _(
    PLOTLY_LAYOUT,
    TIER_COLORS,
    TIER_ORDER,
    df_funding_with_tiers,
    mo,
    pd,
    px,
    sort_epochs,
):
    # INSIGHT 3: Projects funded by epoch (now comes after tier intro)
    _df_epoch_tier = (
        df_funding_with_tiers
        .groupby(['octant_epoch', 'tier_label'])['oso_project_name']
        .nunique()
        .reset_index()
        .rename(columns={'oso_project_name': 'project_count'})
    )

    _total_projects = df_funding_with_tiers['oso_project_name'].nunique()
    _epochs_sorted = sort_epochs(df_funding_with_tiers['octant_epoch'].unique())
    _first_epoch = _epochs_sorted[0] if _epochs_sorted else 'Unknown'

    # Sort epochs numerically
    _df_epoch_tier['octant_epoch'] = pd.Categorical(_df_epoch_tier['octant_epoch'], categories=_epochs_sorted, ordered=True)
    _df_epoch_tier = _df_epoch_tier.sort_values('octant_epoch')

    headline_3 = f"How many projects has Octant funded? {_total_projects} since {_first_epoch}"

    _fig = px.bar(
        _df_epoch_tier,
        x='octant_epoch',
        y='project_count',
        color='tier_label',
        barmode='stack',
        color_discrete_map=TIER_COLORS,
        category_orders={'tier_label': TIER_ORDER, 'octant_epoch': _epochs_sorted},
        labels={'octant_epoch': 'Epoch', 'project_count': 'Projects Funded', 'tier_label': 'Project Type'}
    )
    _fig.update_layout(**PLOTLY_LAYOUT)

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_3}**

    Each bar shows how many projects were funded in that epoch, colored by their tier.
    Projects can receive funding in multiple epochs.
    """),
        _fig
    ])
    return (headline_3,)


@app.cell(hide_code=True)
def _(df_with_growth, mo):
    # Create 4 focused mini-tables (Top 10 each)
    # Exclude Minimal OSS Presence from Growth/Decliners (low denominator)

    # Top 10 by ETH
    _top_eth = df_with_growth.nlargest(10, 'Total ETH')[['Project', 'Tier', 'Total ETH', 'Avg Devs/Mo', 'growth_pct']].copy()
    _top_eth['Total ETH'] = _top_eth['Total ETH'].round(1)
    _top_eth['Avg Devs/Mo'] = _top_eth['Avg Devs/Mo'].round(1)
    _top_eth['Growth'] = _top_eth['growth_pct'].apply(lambda x: f"+{x:.0f}%" if x > 0 else f"{x:.0f}%")
    _top_eth = _top_eth.drop(columns=['growth_pct'])

    # Top 10 by Growth (exclude Minimal OSS Presence - low denominator)
    _growing = df_with_growth[
        (df_with_growth['devs_2024'] > 0) & 
        (df_with_growth['Tier'] != 'Minimal OSS Presence')
    ].nlargest(10, 'growth_pct')[['Project', 'Tier', 'Total ETH', 'devs_2024', 'devs_2025', 'growth_pct']].copy()
    _growing['Total ETH'] = _growing['Total ETH'].round(1)
    _growing['2024 Devs'] = _growing['devs_2024'].round(1)
    _growing['2025 Devs'] = _growing['devs_2025'].round(1)
    _growing['Growth'] = _growing['growth_pct'].apply(lambda x: f"+{x:.0f}%" if x > 0 else f"{x:.0f}%")
    _growing = _growing.drop(columns=['growth_pct', 'devs_2024', 'devs_2025'])

    # Biggest decliners (exclude Minimal OSS Presence - low denominator)
    _declining = df_with_growth[
        (df_with_growth['devs_2024'] > 0) & 
        (df_with_growth['Tier'] != 'Minimal OSS Presence')
    ].nsmallest(10, 'growth_pct')[['Project', 'Tier', 'Total ETH', 'devs_2024', 'devs_2025', 'growth_pct']].copy()
    _declining['Total ETH'] = _declining['Total ETH'].round(1)
    _declining['2024 Devs'] = _declining['devs_2024'].round(1)
    _declining['2025 Devs'] = _declining['devs_2025'].round(1)
    _declining['Growth'] = _declining['growth_pct'].apply(lambda x: f"{x:.0f}%")
    _declining = _declining.drop(columns=['growth_pct', 'devs_2024', 'devs_2025'])

    # Top 10 Most Devs for the ETH (filter to projects with >5 ETH)
    _roi = df_with_growth[(df_with_growth['Total ETH'] > 5) & (df_with_growth['Avg Devs/Mo'] > 0)].nlargest(10, 'devs_per_eth')[['Project', 'Tier', 'Total ETH', 'Avg Devs/Mo', 'devs_per_eth']].copy()
    _roi['Total ETH'] = _roi['Total ETH'].round(1)
    _roi['Avg Devs/Mo'] = _roi['Avg Devs/Mo'].round(1)
    _roi['Devs/ETH'] = _roi['devs_per_eth'].round(2)
    _roi = _roi.drop(columns=['devs_per_eth'])

    headline_4 = "Which projects received the most funding and growth?"

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_4}**
    """),
        mo.hstack([
            mo.vstack([
                mo.md("**Top 10 by Funding**"),
                mo.ui.table(_top_eth.reset_index(drop=True), page_size=10, show_column_summaries=False, show_data_types=False)
            ]),
            mo.vstack([
                mo.md("**Top 10 by Growth (YoY)**"),
                mo.ui.table(_growing.reset_index(drop=True), page_size=10, show_column_summaries=False, show_data_types=False)
            ])
        ], justify="start", gap=2),
        mo.hstack([
            mo.vstack([
                mo.md("**Biggest Decliners**"),
                mo.ui.table(_declining.reset_index(drop=True), page_size=10, show_column_summaries=False, show_data_types=False)
            ]),
            mo.vstack([
                mo.md("**Most Devs for the ETH**"),
                mo.ui.table(_roi.reset_index(drop=True), page_size=10, show_column_summaries=False, show_data_types=False)
            ])
        ], justify="start", gap=2)
    ])
    return (headline_4,)


@app.cell(hide_code=True)
def _(df_with_growth, mo, px):
    # Treemap showing portfolio shape: size = ETH, color = growth
    _df = df_with_growth[df_with_growth['Total ETH'] > 0].copy()

    # Clip growth for better color scale
    _df['growth_clipped'] = _df['growth_pct'].clip(-100, 200)

    headline_treemap = "How does funding size relate to developer growth?"

    _fig = px.treemap(
        _df,
        path=['Tier', 'Project'],
        values='Total ETH',
        color='growth_clipped',
        color_continuous_scale='RdYlGn',
        color_continuous_midpoint=0,
        hover_data={'Total ETH': ':.1f', 'Avg Devs/Mo': ':.1f', 'growth_pct': ':.0f'}
    )
    _fig.update_layout(
        margin=dict(t=30, l=10, r=10, b=10),
        coloraxis_colorbar=dict(title="Growth %", ticksuffix="%")
    )
    _fig.update_traces(
        hovertemplate="<b>%{label}</b><br>ETH: %{value:.1f}<br>Growth: %{color:.0f}%<extra></extra>"
    )

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_treemap}**

    Box size = total ETH received. Color = YoY developer growth (red = declining, green = growing).
    Hover over boxes to see project details.
    """),
        _fig
    ])
    return (headline_treemap,)


@app.cell(hide_code=True)
def _(TIER_COLORS, df_project_tiers, df_repos, mo, np, px):
    # Filter to Tier 3+4 projects (software projects)
    _software_projects = df_project_tiers[
        df_project_tiers['tier_label'].isin(['Mature/Stable', 'Active Development'])
    ]['project_name'].unique()

    _software_repos = df_repos[df_repos['project_name'].isin(_software_projects)]
    _total_repos = _software_repos['repo_name'].nunique()

    # Get stars and forks
    _total_stars = int(_software_repos['star_count'].sum())
    _total_forks = int(_software_repos['fork_count'].sum())
    _project_count = len(_software_projects)

    headline_5 = f"How large is the software portfolio? {_total_repos:,} repos, {_total_stars:,} stars"

    # Aggregate per project for scatter plot
    _project_stats = (
        _software_repos
        .groupby('project_name', as_index=False)
        .agg({
            'repo_name': 'nunique',
            'star_count': 'sum',
            'fork_count': 'sum'
        })
        .rename(columns={'repo_name': 'repo_count'})
    )
    _project_stats = _project_stats.merge(
        df_project_tiers[['project_name', 'tier_label']],
        on='project_name',
        how='left'
    )

    # Filter out projects with zero stars or forks for log scale
    _project_stats = _project_stats[
        (_project_stats['star_count'] > 0) & 
        (_project_stats['fork_count'] > 0)
    ]

    # Use log(repos + 1) for bubble size
    _project_stats = _project_stats.copy()
    _project_stats['log_repos'] = np.log1p(_project_stats['repo_count'])

    # Create scatter plot: Stars vs Forks, sized by log(repos+1)
    _fig = px.scatter(
        _project_stats,
        x='star_count',
        y='fork_count',
        size='log_repos',
        color='tier_label',
        color_discrete_map=TIER_COLORS,
        hover_name='project_name',
        text='project_name',
        log_x=True,
        log_y=True,
        labels={
            'star_count': 'GitHub Stars (log)',
            'fork_count': 'Forks (log)',
            'log_repos': 'Repos (log)',
            'tier_label': 'Tier'
        },
        size_max=60
    )
    _fig.update_traces(
        textposition='top center',
        textfont=dict(size=8)
    )
    _fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=40, l=60, r=20, b=50),
        legend=dict(
            orientation="v",
            yanchor="top", y=0.98,
            xanchor="left", x=0.02,
            bordercolor="black", borderwidth=1,
            bgcolor="white"
        ),
        xaxis=dict(
            title="GitHub Stars (log)",
            showgrid=True, gridcolor='#DDD',
            linecolor="#000", linewidth=1,
            ticks="outside"
        ),
        yaxis=dict(
            title="Forks (log)",
            showgrid=True, gridcolor='#DDD',
            linecolor="#000", linewidth=1,
            ticks="outside"
        )
    )

    # Styled stat cards with borders
    _card_style = "background-color: #f8f9fa; padding: 16px; border-radius: 8px; text-align: center; border: 1px solid #ddd;"

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_5}**

    Focusing on projects with meaningful open source presence (Active Development + Mature/Stable tiers).
    """),
        mo.hstack([
            mo.md(f'<div style="{_card_style}"><strong>Software Projects</strong><br/><span style="font-size: 24px; font-weight: bold;">{_project_count:,}</span></div>'),
            mo.md(f'<div style="{_card_style}"><strong>Repositories</strong><br/><span style="font-size: 24px; font-weight: bold;">{_total_repos:,}</span></div>'),
            mo.md(f'<div style="{_card_style}"><strong>GitHub Stars</strong><br/><span style="font-size: 24px; font-weight: bold;">{_total_stars:,}</span></div>'),
            mo.md(f'<div style="{_card_style}"><strong>Forks</strong><br/><span style="font-size: 24px; font-weight: bold;">{_total_forks:,}</span></div>')
        ], widths="equal", gap=2),
        mo.md("**Portfolio Shape**: Bubble size = log(repos + 1)"),
        _fig
    ])
    return (headline_5,)




@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_contributors_by_project, df_funding, go, mo, pd):
    # Aggregate developer activity over time - USE FULL UNFILTERED DATA
    _df = df_contributors_by_project.copy()
    _df['day'] = pd.to_datetime(_df['day'])
    _df['total_devs'] = _df['full_time_devs'] + _df['part_time_devs']

    # Step 1: Get monthly average per project (mean of daily 28d rolling values)
    _df['month_str'] = _df['day'].dt.strftime('%Y-%m')
    _monthly_by_project = (
        _df
        .groupby(['month_str', 'project_name'], as_index=False)
        .agg({'total_devs': 'mean', 'full_time_devs': 'mean', 'part_time_devs': 'mean'})
    )

    # Step 2: Sum across projects for portfolio total
    _monthly = (
        _monthly_by_project
        .groupby('month_str', as_index=False)
        .agg({'total_devs': 'sum', 'full_time_devs': 'sum', 'part_time_devs': 'sum'})
    )
    # Convert back to datetime for plotting
    _monthly['day'] = _monthly['month_str'].apply(lambda x: pd.to_datetime(str(x) + '-01'))
    _monthly = _monthly.sort_values('day')

    # Add 3-month rolling average
    _monthly['rolling_avg'] = _monthly['total_devs'].rolling(window=3, min_periods=1).mean()

    # Calculate YoY growth: 2025 vs 2024
    _2024_avg = _monthly[_monthly['day'].dt.year == 2024]['total_devs'].mean()
    _2025_avg = _monthly[_monthly['day'].dt.year == 2025]['total_devs'].mean()
    if _2024_avg > 0 and not pd.isna(_2025_avg):
        _growth_pct = ((_2025_avg - _2024_avg) / _2024_avg * 100)
    else:
        _growth_pct = 0

    headline_6 = f"Is developer activity growing? {'+' if _growth_pct > 0 else ''}{_growth_pct:.0f}% year-over-year"

    # Create figure with both raw and rolling avg
    _fig = go.Figure()
    _fig.add_trace(go.Scatter(
        x=_monthly['day'], y=_monthly['total_devs'],
        mode='lines', name='Monthly Total',
        line=dict(color='rgba(31, 119, 180, 0.3)', width=1)
    ))
    _fig.add_trace(go.Scatter(
        x=_monthly['day'], y=_monthly['rolling_avg'],
        mode='lines', name='3-Month Rolling Avg',
        line=dict(color='#1f77b4', width=3)
    ))

    # Add epoch funding markers using add_shape + add_annotation (avoids Timestamp issues)
    _epoch_dates = (
        df_funding
        .groupby('octant_epoch', as_index=False)['funding_date']
        .min()
        .sort_values('funding_date')
    )
    _y_max = _monthly['total_devs'].max() * 1.1  # For annotation positioning

    for _i, _row in _epoch_dates.iterrows():
        try:
            _epoch_date = pd.to_datetime(_row['funding_date'])
            # Add vertical line as shape
            _fig.add_shape(
                type="line",
                x0=_epoch_date, x1=_epoch_date,
                y0=0, y1=_y_max,
                line=dict(color="#2D9B87", width=2, dash="dot"),
                yref="y"
            )
            # Add annotation separately
            _fig.add_annotation(
                x=_epoch_date, y=_y_max,
                text=_row['octant_epoch'],
                showarrow=False,
                font=dict(size=8, color="#2D9B87"),
                textangle=-45,
                yanchor="bottom"
            )
        except Exception as e:
            print(f"Error adding marker for {_row['octant_epoch']}: {e}")

    # Add year markers
    for _year in [2020, 2021, 2022, 2023, 2024, 2025]:
        _fig.add_shape(
            type="line",
            x0=pd.Timestamp(f"{_year}-01-01"), x1=pd.Timestamp(f"{_year}-01-01"),
            y0=0, y1=_y_max,
            line=dict(color="rgba(0,0,0,0.1)", width=1),
            yref="y"
        )

    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(xaxis=dict(range=[pd.Timestamp('2020-01-01'), _monthly['day'].max()]))

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_6}**

    Comparing 2025 average ({_2025_avg:.0f} devs/mo) to 2024 average ({_2024_avg:.0f} devs/mo).
    Vertical lines mark funding epochs.
    """),
        _fig
    ])
    return (headline_6,)


@app.cell(hide_code=True)
def _(OCTANT_PALETTE, PLOTLY_LAYOUT, df_contributors_by_project, df_funding, go, mo, pd):
    # Stacked area chart: active developers by project over time
    # Top 10 projects + "Other"

    _df = df_contributors_by_project.copy()
    _df['day'] = pd.to_datetime(_df['day'])
    _df['total_devs'] = _df['full_time_devs'] + _df['part_time_devs']

    # Filter to since 2020
    _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]

    # Step 1: Get monthly average per project
    _df['month_str'] = _df['day'].dt.strftime('%Y-%m')
    _monthly_by_project = (
        _df
        .groupby(['month_str', 'project_name'], as_index=False)
        .agg({'total_devs': 'mean'})
    )
    _monthly_by_project['day'] = _monthly_by_project['month_str'].apply(lambda x: pd.to_datetime(str(x) + '-01'))

    # Step 2: Identify top 10 projects by 2025 average developer activity
    _2025_data = _monthly_by_project[_monthly_by_project['day'].dt.year == 2025]
    _project_2025_avg = (
        _2025_data
        .groupby('project_name', as_index=False)['total_devs']
        .mean()
        .sort_values('total_devs', ascending=False)
    )
    _top_10_projects = _project_2025_avg.head(10)['project_name'].tolist()

    # Step 3: Create category - top 10 keep names, rest become "Other"
    _monthly_by_project['project_category'] = _monthly_by_project['project_name'].apply(
        lambda x: x if x in _top_10_projects else 'Other'
    )

    # Step 4: Aggregate by category
    _monthly_by_category = (
        _monthly_by_project
        .groupby(['day', 'project_category'], as_index=False)['total_devs']
        .sum()
    )

    # Step 5: Pivot for stacked area
    _pivot = _monthly_by_category.pivot(index='day', columns='project_category', values='total_devs').fillna(0)
    _pivot = _pivot.reset_index()

    # Order columns: top 10 by size (largest at bottom), then Other at top
    _ordered_cols = _top_10_projects[::-1] + ['Other'] if 'Other' in _pivot.columns else _top_10_projects[::-1]
    _ordered_cols = [c for c in _ordered_cols if c in _pivot.columns]

    # Create stacked area chart
    _fig = go.Figure()

    for _i, _col in enumerate(_ordered_cols):
        _fig.add_trace(go.Scatter(
            x=_pivot['day'],
            y=_pivot[_col],
            name=_col,
            mode='lines',
            stackgroup='one',
            line=dict(width=0.5),
            fillcolor=OCTANT_PALETTE[_i % len(OCTANT_PALETTE)],
            hovertemplate=f'{_col}: %{{y:.1f}} devs<extra></extra>'
        ))

    # Add epoch funding markers
    _epoch_dates = (
        df_funding
        .groupby('octant_epoch', as_index=False)['funding_date']
        .min()
        .sort_values('funding_date')
    )
    _y_max = _pivot[_ordered_cols].sum(axis=1).max() * 1.1

    for _i, _row in _epoch_dates.iterrows():
        try:
            _epoch_date = pd.to_datetime(_row['funding_date'])
            # Add vertical line
            _fig.add_shape(
                type="line",
                x0=_epoch_date, x1=_epoch_date,
                y0=0, y1=_y_max,
                line=dict(color="#2D9B87", width=2, dash="dot"),
                yref="y"
            )
            # Add epoch label annotation
            _fig.add_annotation(
                x=_epoch_date,
                y=_y_max,
                text=_row['octant_epoch'],
                showarrow=False,
                font=dict(size=8, color="#2D9B87"),
                textangle=-45,
                yanchor="bottom"
            )
        except Exception:
            # Silently skip if date parsing or annotation fails
            pass

    headline_7 = "Which projects contribute most to the developer community?"

    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(
        xaxis=dict(range=[pd.Timestamp('2020-01-01'), _pivot['day'].max()]),
        yaxis=dict(title="Active Developers (monthly avg)"),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
            font=dict(size=9)
        ),
        margin=dict(t=40, l=60, r=20, b=50),
        hovermode='x unified'
    )

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_7}**

    Stacked area showing developer activity by project since 2020. 
    **Top 10 projects** (by 2025 activity) shown individually, all others grouped as "Other".
    """),
        _fig
    ])
    return (headline_7,)


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_contributors_by_project, df_funding, mo, pd, px):
    # Aggregate full-time vs part-time over time - USE FULL UNFILTERED DATA
    _df = df_contributors_by_project.copy()
    _df['day'] = pd.to_datetime(_df['day'])

    # Step 1: Get monthly average per project (mean of daily 28d rolling values)
    _df['month_str'] = _df['day'].dt.strftime('%Y-%m')
    _monthly_by_project = (
        _df
        .groupby(['month_str', 'project_name'], as_index=False)
        .agg({'full_time_devs': 'mean', 'part_time_devs': 'mean'})
    )

    # Step 2: Sum across projects for portfolio total
    _monthly = (
        _monthly_by_project
        .groupby('month_str', as_index=False)
        .agg({'full_time_devs': 'sum', 'part_time_devs': 'sum'})
    )
    # Convert back to datetime for plotting
    _monthly['day'] = _monthly['month_str'].apply(lambda x: pd.to_datetime(str(x) + '-01'))
    _monthly = _monthly.sort_values('day')

    _avg_ft = _monthly['full_time_devs'].mean()
    _avg_pt = _monthly['part_time_devs'].mean()
    _avg_all = _avg_ft + _avg_pt
    _ft_pct = (_avg_ft / _avg_all * 100) if _avg_all > 0 else 0

    headline_8 = f"What's the full-time vs part-time mix? {_ft_pct:.0f}% full-time"

    # Melt for stacked area
    _monthly_melted = _monthly.melt(
        id_vars=['day'],
        value_vars=['full_time_devs', 'part_time_devs'],
        var_name='developer_type',
        value_name='count'
    )
    _monthly_melted['developer_type'] = _monthly_melted['developer_type'].map({
        'full_time_devs': 'Full-Time (10+ commits/28d)',
        'part_time_devs': 'Part-Time (<10 commits/28d)'
    })

    _fig = px.area(
        _monthly_melted,
        x='day',
        y='count',
        color='developer_type',
        color_discrete_map={
            'Full-Time (10+ commits/28d)': '#2D9B87',  # Teal (primary)
            'Part-Time (<10 commits/28d)': '#78B0A0'   # Lighter teal
        },
        labels={'day': '', 'count': 'Developer Count', 'developer_type': 'Type'}
    )
    _fig.update_layout(**PLOTLY_LAYOUT)

    # Add epoch funding markers
    _epoch_dates = (
        df_funding
        .groupby('octant_epoch', as_index=False)['funding_date']
        .min()
        .sort_values('funding_date')
    )
    _y_max = _monthly['full_time_devs'].max() + _monthly['part_time_devs'].max()

    for _, _row in _epoch_dates.iterrows():
        try:
            _epoch_date = pd.to_datetime(_row['funding_date'])
            _fig.add_shape(
                type="line",
                x0=_epoch_date, x1=_epoch_date,
                y0=0, y1=_y_max * 1.1,
                line=dict(color="#2D9B87", width=2, dash="dot"),
                yref="y"
            )
            _fig.add_annotation(
                x=_epoch_date, y=_y_max * 1.1,
                text=_row['octant_epoch'],
                showarrow=False,
                font=dict(size=8, color="#2D9B87"),
                textangle=-45,
                yanchor="bottom"
            )
        except Exception:
            # Silently skip if date parsing or annotation fails
            pass

    # Set x-axis range to start at 2020
    _fig.update_layout(xaxis=dict(range=[pd.Timestamp('2020-01-01'), _monthly['day'].max()]))

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_8}**

    Full-time contributors are defined as developers with 10+ commits in a 28-day window.
    A healthy mix of full-time and part-time contributors indicates sustainable project development.
    Vertical lines mark funding epochs.
    """),
        _fig
    ])
    return (headline_8,)




@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## Project Deep Dive

    Select a project to compare its developer activity against the portfolio average.
    """)
    return


@app.cell(hide_code=True)
def _(df_project_tiers, mo):
    _projects = sorted(df_project_tiers[
        df_project_tiers['tier_label'].isin(['Mature/Stable', 'Active Development'])
    ]['project_name'].dropna().unique().tolist())

    project_selector = mo.ui.dropdown(
        options=_projects,
        value=_projects[0] if _projects else None,
        label="Select Project:"
    )
    project_selector
    return (project_selector,)


@app.cell(hide_code=True)
def _(
    PLOTLY_LAYOUT,
    df_contributors_by_project,
    df_funding_with_tiers,
    go,
    mo,
    pd,
    project_selector,
):

    _selected = project_selector.value

    # Get project-specific data - USE FULL UNFILTERED DATA
    _df_proj = df_contributors_by_project[
        df_contributors_by_project['project_name'] == _selected
    ].copy()


    _df_proj['day'] = pd.to_datetime(_df_proj['day'])
    _df_proj['total_devs'] = _df_proj['full_time_devs'] + _df_proj['part_time_devs']
    # Use string month to avoid timestamp groupby issues
    _df_proj['month_str'] = _df_proj['day'].dt.strftime('%Y-%m')

    # Calculate portfolio average
    _df_all = df_contributors_by_project.copy()
    _df_all['day'] = pd.to_datetime(_df_all['day'])
    _df_all['total_devs'] = _df_all['full_time_devs'] + _df_all['part_time_devs']
    _df_all['month_str'] = _df_all['day'].dt.strftime('%Y-%m')

    _df_proj_monthly = (
        _df_proj
        .groupby('month_str', as_index=False)
        ['total_devs'].mean()
    )
    # Convert string back to datetime for plotting (use apply to handle any edge cases)
    _df_proj_monthly['day'] = _df_proj_monthly['month_str'].apply(lambda x: pd.to_datetime(str(x) + '-01'))
    _df_proj_monthly = _df_proj_monthly.sort_values('day')

    # Calculate portfolio average across all projects (use mean since data is 28d rolling avg)
    _df_avg_monthly = (
        _df_all
        .groupby(['month_str', 'project_name'], as_index=False)
        ['total_devs'].mean()
        .groupby('month_str', as_index=False)
        ['total_devs'].mean()  # Average across projects
    )
    _df_avg_monthly['day'] = _df_avg_monthly['month_str'].apply(lambda x: pd.to_datetime(str(x) + '-01'))
    _df_avg_monthly = _df_avg_monthly.sort_values('day')

    # Get funding events for this project
    _funding_events = df_funding_with_tiers[
        df_funding_with_tiers['oso_project_name'] == _selected
    ][['funding_date', 'octant_epoch', 'amount_eth']].drop_duplicates()

    # Create comparison chart
    _fig = go.Figure()

    _fig.add_trace(go.Scatter(
        x=_df_avg_monthly['day'], y=_df_avg_monthly['total_devs'],
        mode='lines', name='Portfolio Avg',
        line=dict(color='#aaaaaa', width=2, dash='dot')
    ))
    _fig.add_trace(go.Scatter(
        x=_df_proj_monthly['day'], y=_df_proj_monthly['total_devs'],
        mode='lines', name=_selected,
        line=dict(color='#1f77b4', width=3)
    ))

    # Add funding event markers using add_shape + add_annotation
    _y_max = max(_df_proj_monthly['total_devs'].max() if not _df_proj_monthly.empty else 1,
                 _df_avg_monthly['total_devs'].max() if not _df_avg_monthly.empty else 1) * 1.1
    for _, _row in _funding_events.iterrows():
        try:
            _epoch_date = pd.to_datetime(_row['funding_date'])
            _amount = float(_row['amount_eth']) if pd.notna(_row['amount_eth']) else 0.0
            _epoch = str(_row['octant_epoch']) if pd.notna(_row['octant_epoch']) else 'Unknown'
            _fig.add_shape(
                type="line",
                x0=_epoch_date, x1=_epoch_date,
                y0=0, y1=_y_max,
                line=dict(color="#2D9B87", width=2, dash="dash"),
                yref="y"
            )
            _fig.add_annotation(
                x=_epoch_date, y=_y_max,
                text=f"{_epoch} ({_amount:.1f} ETH)",
                showarrow=False,
                font=dict(size=8, color="#2D9B87"),
                textangle=-45,
                yanchor="bottom"
            )
        except Exception:
            # Silently skip if date parsing or funding annotation fails
            pass

    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(range=[pd.Timestamp('2020-01-01'), _df_avg_monthly['day'].max() if not _df_avg_monthly.empty else pd.Timestamp('2025-12-31')])
    )

    # Get project tier info
    _tier = df_funding_with_tiers[
        df_funding_with_tiers['oso_project_name'] == _selected
    ]['tier_label'].iloc[0] if len(df_funding_with_tiers[df_funding_with_tiers['oso_project_name'] == _selected]) > 0 else 'Unknown'

    _total_eth = df_funding_with_tiers[
        df_funding_with_tiers['oso_project_name'] == _selected
    ]['amount_eth'].sum()

    _epochs_funded = df_funding_with_tiers[
        df_funding_with_tiers['oso_project_name'] == _selected
    ]['octant_epoch'].nunique()

    # Calculate average devs for this project
    _avg_devs = _df_proj['total_devs'].mean() if not _df_proj.empty else 0

    # Styled stat cards with borders
    _card_style = "background-color: #f8f9fa; padding: 16px; border-radius: 8px; text-align: center; border: 1px solid #ddd;"

    mo.vstack([
        mo.md(f"### {_selected}"),
        mo.hstack([
            mo.md(f'<div style="{_card_style}"><strong>Classification</strong><br/><span style="font-size: 18px; font-weight: bold;">{_tier}</span></div>'),
            mo.md(f'<div style="{_card_style}"><strong>Total ETH</strong><br/><span style="font-size: 18px; font-weight: bold;">{_total_eth:,.1f}</span></div>'),
            mo.md(f'<div style="{_card_style}"><strong>Epochs Funded</strong><br/><span style="font-size: 18px; font-weight: bold;">{_epochs_funded}</span></div>'),
            mo.md(f'<div style="{_card_style}"><strong>Avg Devs/Mo</strong><br/><span style="font-size: 18px; font-weight: bold;">{_avg_devs:.1f}</span></div>')
        ], widths="equal", gap=2),
        mo.md("Green dashed lines indicate funding events. Compare the project's developer activity trend against the portfolio average."),
        mo.ui.plotly(_fig)
    ])
    return


@app.cell(hide_code=True)
def _(ACTIVITY_DECLINE_PCT, MIN_DEVS_FOR_ACTIVE, RECENT_WINDOW_MONTHS, mo):
    mo.md(f"""
    ---

    # Methodology Details

    ## Open, Auditable Data

    Every data point in this analysis comes from publicly accessible sources:

    - **Funding data** is sourced from the [OSS Funding](https://github.com/opensource-observer/oss-funding) repo, 
      a community-maintained registry of open source projects and their funding history.
    - **Developer metrics** come from [OpenDevData](https://opendevdata.org/), which provides 
      anonymized, aggregated statistics about GitHub activity.
    - **All queries are reproducible** using the [OSO API](https://docs.oso.xyz/), 
      enabling anyone to verify findings or extend this analysis.

    This transparency enables **accountability** (stakeholders can verify claims), **reproducibility** (researchers can replicate analyses), and **community contribution** (anyone can improve the methodology).

    ## Data Sources

    This analysis uses three primary data sources, all accessible via the OSO API:

    1. **Funding Data** (`stg_ossd__current_funding`) — Grant allocations from Octant epochs, 
       including project names and amounts in ETH.

    2. **Repository Data** (`int_opendevdata__repositories_with_repo_id`) — GitHub repository 
       metadata including stars, forks, and creation dates.

    3. **Developer Activity** (`stg_opendevdata__repo_developer_28d_activities`) — Rolling 28-day 
       developer activity counts per repository. Developers working on multiple repos within the same project are counted once using their max activity level (`MAX(l28_days)`).

    ## Project Classification

    Projects are classified into 4 tiers based on their GitHub activity:

    | Tier | Label | Criteria |
    |------|-------|----------|
    | 1 | No OSS Footprint | No GitHub repos matched in OSO |
    | 2 | Minimal OSS Presence | Avg devs/month < {MIN_DEVS_FOR_ACTIVE} |
    | 3 | Mature/Stable | Activity declined > {ACTIVITY_DECLINE_PCT*100:.0f}% in last {RECENT_WINDOW_MONTHS} months |
    | 4 | Active Development | Steady or growing activity in last {RECENT_WINDOW_MONTHS} months |

    ## Assumptions and Limitations

    - **Currency**: All amounts are displayed in ETH (not USD) to avoid exchange rate fluctuations.
    - **Full-time threshold**: A developer is considered "full-time" if they have 10+ commits in a 28-day window.
    - **Recent activity window**: {RECENT_WINDOW_MONTHS} months is used as the lookback period for "recent" activity.
    - **Data coverage**: Only projects registered in the OSS Directory with matched GitHub repos have developer metrics.
    - **Attribution**: Developer activity is attributed to repos, not directly to funding events.
    """)
    return


@app.cell
def _(mo, pd, pyoso_db_conn):
    _df_funding_raw = mo.sql(
        f"""
        SELECT
          funding_date,
          grant_pool_name AS octant_epoch,    
          JSON_EXTRACT_SCALAR(metadata, '$.application_name') AS application,
          to_project_name AS oso_project_name,    
          COALESCE(CAST(JSON_EXTRACT_SCALAR(metadata, '$.token_amount') AS DOUBLE), 0) AS amount_eth,
          amount AS amount_usd
        FROM stg_ossd__current_funding
        WHERE
          from_funder_name = 'octant-golemfoundation'
        """,
        engine=pyoso_db_conn,
        output=False
    )

    # Handle projects with no OSO slugs
    _df_funding_raw['oso_project_name'] = _df_funding_raw['oso_project_name'].replace("", None)
    project_names = list(_df_funding_raw['oso_project_name'].dropna().unique())
    _mapping = _df_funding_raw[['application', 'oso_project_name']].drop_duplicates().dropna().set_index('application')['oso_project_name'].to_dict()
    _df_funding_raw['oso_project_name'] = _df_funding_raw['application'].apply(lambda x: _mapping.get(x, x))

    # Add Argot for Solidity
    project_names.append('argotorg')

    # Clean up epoch names: "epoch_2" -> "Epoch 2"
    def _format_epoch(epoch_str):
        if pd.isna(epoch_str):
            return epoch_str
        # Replace underscores with spaces and title case
        return epoch_str.replace('_', ' ').title()

    _df_funding_raw['octant_epoch'] = _df_funding_raw['octant_epoch'].apply(_format_epoch)
    _df_funding_raw['funding_date'] = pd.to_datetime(_df_funding_raw['funding_date'])

    # Filter out projects with < 1 ETH total funding
    df_funding = _df_funding_raw[_df_funding_raw['amount_eth'] > 1]
    return df_funding, project_names


@app.cell
def _(mo, project_names, pyoso_db_conn, stringify):
    df_repos = mo.sql(
        f"""
        WITH repos AS (
          SELECT DISTINCT
            project_name,
            CONCAT(artifact_namespace, '/', artifact_name) AS repo_name
          FROM artifacts_by_project_v1
          WHERE
            artifact_source = 'GITHUB'
            AND project_name IN ({stringify(project_names)})
        ),
        repo_ids AS (
          SELECT DISTINCT
            CASE
              WHEN project_name = 'argotorg' THEN 'solidity-ethereum'
              ELSE project_name
            END AS project_name,
            repo_id
          FROM int_gharchive__repositories
          JOIN repos USING (repo_name)
          WHERE repo_name NOT IN (
            'argotorg/fe',
            'argotorg/sourcify',
            'argotorg/hevm',
            'argotorg/act'
          )
        )
        SELECT DISTINCT
          project_name,
          repo_name,
          repo_created_at,
          star_count,
          fork_count,
          is_opendevdata_blacklist,    
          repo_id,
          opendevdata_id
        FROM int_opendevdata__repositories_with_repo_id
        JOIN repo_ids USING (repo_id)
        ORDER BY project_name, star_count DESC
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_repos,)


@app.cell
def _(mo, project_names, pyoso_db_conn, stringify):
    # Query developer activity at the PROJECT level (not repo level)
    # This ensures each developer is counted once per project even if they work on multiple repos
    df_contributors_by_project = mo.sql(
        f"""
        WITH repos AS (
          SELECT DISTINCT
            project_name,
            CONCAT(artifact_namespace, '/', artifact_name) AS repo_name
          FROM artifacts_by_project_v1
          WHERE
            artifact_source = 'GITHUB'
            AND project_name IN ({stringify(project_names)})
        ),
        repo_ids AS (
          SELECT DISTINCT
            CASE
              WHEN project_name = 'argotorg' THEN 'solidity-ethereum'
              ELSE project_name
            END AS project_name,
            repo_id
          FROM int_gharchive__repositories
          JOIN repos USING (repo_name)
          WHERE repo_name NOT IN (
            'argotorg/fe',
            'argotorg/sourcify',
            'argotorg/hevm',
            'argotorg/act'
          )
        ),
        repo_to_opendevdata AS (
          SELECT DISTINCT
            project_name,
            opendevdata_id
          FROM int_opendevdata__repositories_with_repo_id
          JOIN repo_ids USING (repo_id)
        ),
        -- Aggregate to project level first to avoid double-counting developers
        -- who work on multiple repos within the same project
        project_developer_activity AS (
          SELECT
            day,
            project_name,
            canonical_developer_id,
            MAX(l28_days) AS max_l28_days
          FROM stg_opendevdata__repo_developer_28d_activities
          JOIN repo_to_opendevdata ON repo_id = opendevdata_id
          GROUP BY 1, 2, 3
        )
        SELECT
          day,
          project_name,
          COUNT(DISTINCT IF(max_l28_days>=10, canonical_developer_id, NULL)) AS full_time_devs,
          COUNT(DISTINCT IF(max_l28_days<10, canonical_developer_id, NULL)) AS part_time_devs
        FROM project_developer_activity
        GROUP BY 1, 2
        ORDER BY 1, 2
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_contributors_by_project,)


@app.cell
def _(df_funding):
    # Calculate the start of Octant funding (Epoch 1)
    # All developer metrics should be filtered to start from this date
    epoch1_start_date = df_funding['funding_date'].min()
    return (epoch1_start_date,)


@app.cell
def _(df_contributors_by_project, epoch1_start_date, pd):
    # Ensure day column is datetime and filter to only include data from Epoch 1 onwards
    _df = df_contributors_by_project.copy()
    _df['day'] = pd.to_datetime(_df['day'])
    # Filter to start from Octant's first funding
    df_contributors_filtered = _df[_df['day'] >= epoch1_start_date].copy()
    return (df_contributors_filtered,)


@app.cell
def _(
    ACTIVITY_DECLINE_PCT,
    MIN_DEVS_FOR_ACTIVE,
    RECENT_WINDOW_MONTHS,
    df_contributors_filtered,
    df_funding,
    df_repos,
    pd,
):
    # Get all funded projects
    _all_projects = df_funding['oso_project_name'].dropna().unique()

    # Get projects with repos
    _projects_with_repos = df_repos['project_name'].unique()

    # Calculate activity metrics per project
    _df_activity = df_contributors_filtered.copy()
    _df_activity['day'] = pd.to_datetime(_df_activity['day'])
    _df_activity['total_devs'] = _df_activity['full_time_devs'] + _df_activity['part_time_devs']

    # Calculate per-project metrics - handle empty dataframe case
    # Use a fixed cutoff date to avoid timestamp arithmetic issues
    _now = pd.Timestamp.now()
    _cutoff_date = pd.Timestamp(_now.year, _now.month, 1) - pd.DateOffset(months=RECENT_WINDOW_MONTHS)

    if not _df_activity.empty and _df_activity['day'].notna().any():
        _max_date = _df_activity['day'].dropna().max()
        if pd.notna(_max_date):
            _cutoff_date = pd.Timestamp(_max_date.year, _max_date.month, 1) - pd.DateOffset(months=RECENT_WINDOW_MONTHS)

    _project_metrics = []
    for _project in _projects_with_repos:
        _proj_data = _df_activity[_df_activity['project_name'] == _project].copy()
        if len(_proj_data) == 0:
            continue

        _avg_devs = _proj_data['total_devs'].mean()
        _recent_data = _proj_data[_proj_data['day'] >= _cutoff_date]
        _historical_data = _proj_data[_proj_data['day'] < _cutoff_date]

        _recent_avg = _recent_data['total_devs'].mean() if len(_recent_data) > 0 else 0
        _historical_avg = _historical_data['total_devs'].mean() if len(_historical_data) > 0 else _avg_devs
        _peak = _proj_data['total_devs'].max()

        _project_metrics.append({
            'project_name': _project,
            'avg_devs': _avg_devs,
            'recent_avg': _recent_avg,
            'historical_avg': _historical_avg,
            'peak': _peak,
            'activity_ratio': (_recent_avg / _peak) if _peak > 0 else 0
        })

    _metrics_df = pd.DataFrame(_project_metrics)

    # Classify projects
    _tier_assignments = []
    for _project in _all_projects:
        if _project not in _projects_with_repos:
            _tier = 'No OSS Footprint'
            _avg = 0
            _ratio = 0
        elif _project in _metrics_df['project_name'].values:
            _row = _metrics_df[_metrics_df['project_name'] == _project].iloc[0]
            _avg = _row['avg_devs']
            _ratio = _row['activity_ratio']
            if _row['avg_devs'] < MIN_DEVS_FOR_ACTIVE:
                _tier = 'Minimal OSS Presence'
            elif _row['recent_avg'] < _row['peak'] * ACTIVITY_DECLINE_PCT and _row['historical_avg'] > _row['recent_avg']:
                _tier = 'Mature/Stable'
            else:
                _tier = 'Active Development'
        else:
            _tier = 'Minimal OSS Presence'
            _avg = 0
            _ratio = 0

        _tier_assignments.append({
            'project_name': _project,
            'tier_label': _tier,
            'avg_devs': _avg,
            'activity_ratio': _ratio
        })

    df_project_tiers = pd.DataFrame(_tier_assignments)
    return (df_project_tiers,)


@app.cell
def _(df_funding, df_project_tiers, df_repos):
    # Create the full classification table for display
    _funding_summary = (
        df_funding
        .groupby('oso_project_name', as_index=False)
        .agg({
            'amount_eth': 'sum',
            'octant_epoch': 'nunique'
        })
        .rename(columns={'oso_project_name': 'project_name', 'octant_epoch': 'epochs_funded'})
    )

    _repo_summary = (
        df_repos
        .groupby('project_name', as_index=False)
        .agg({
            'repo_name': 'nunique',
            'star_count': 'sum',
            'fork_count': 'sum'
        })
        .rename(columns={'repo_name': 'repo_count'})
    )

    df_classification_table = (
        df_project_tiers
        .merge(_funding_summary, on='project_name', how='left')
        .merge(_repo_summary, on='project_name', how='left')
        .fillna({'repo_count': 0, 'star_count': 0, 'fork_count': 0, 'amount_eth': 0, 'epochs_funded': 0})
    )

    # Format for display
    df_classification_table = df_classification_table.rename(columns={
        'project_name': 'Project',
        'tier_label': 'Tier',
        'amount_eth': 'Total ETH',
        'epochs_funded': 'Epochs',
        'repo_count': 'Repos',
        'avg_devs': 'Avg Devs/Mo',
        'activity_ratio': 'Activity Ratio',
        'star_count': 'Stars',
        'fork_count': 'Forks'
    })

    # Reorder columns
    df_classification_table = df_classification_table[[
        'Project', 'Tier', 'Total ETH', 'Epochs', 'Repos', 'Avg Devs/Mo', 'Activity Ratio', 'Stars', 'Forks'
    ]]

    # Sort by tier then by funding
    _tier_order = {'Active Development': 0, 'Mature/Stable': 1, 'Minimal OSS Presence': 2, 'No OSS Footprint': 3}
    df_classification_table['_sort'] = df_classification_table['Tier'].map(_tier_order)
    df_classification_table = df_classification_table.sort_values(['_sort', 'Total ETH'], ascending=[True, False]).drop(columns=['_sort'])

    # Round numeric columns (fill NaN first to avoid conversion errors)
    df_classification_table['Total ETH'] = df_classification_table['Total ETH'].fillna(0).round(2)
    df_classification_table['Avg Devs/Mo'] = df_classification_table['Avg Devs/Mo'].fillna(0).round(1)
    df_classification_table['Activity Ratio'] = (df_classification_table['Activity Ratio'].fillna(0) * 100).round(0).astype(int).astype(str) + '%'
    df_classification_table['Stars'] = df_classification_table['Stars'].fillna(0).astype(int)
    df_classification_table['Forks'] = df_classification_table['Forks'].fillna(0).astype(int)
    df_classification_table['Repos'] = df_classification_table['Repos'].fillna(0).astype(int)
    df_classification_table['Epochs'] = df_classification_table['Epochs'].fillna(0).astype(int)
    return (df_classification_table,)


@app.cell
def _(df_classification_table, df_contributors_filtered, pd):
    # Calculate per-project growth (2025 vs 2024) for mini-tables
    _df = df_contributors_filtered.copy()
    _df['day'] = pd.to_datetime(_df['day'])
    _df['total_devs'] = _df['full_time_devs'] + _df['part_time_devs']
    _df['year'] = _df['day'].dt.year

    # Monthly average per project per year
    _df['month_str'] = _df['day'].dt.strftime('%Y-%m')
    _monthly = _df.groupby(['project_name', 'month_str', 'year'], as_index=False)['total_devs'].mean()

    # Yearly averages
    _yearly = _monthly.groupby(['project_name', 'year'], as_index=False)['total_devs'].mean()
    _2024 = _yearly[_yearly['year'] == 2024].set_index('project_name')['total_devs']
    _2025 = _yearly[_yearly['year'] == 2025].set_index('project_name')['total_devs']

    _growth = pd.DataFrame({
        'project_name': _2024.index.union(_2025.index),
    })
    _growth['devs_2024'] = _growth['project_name'].map(_2024).fillna(0)
    _growth['devs_2025'] = _growth['project_name'].map(_2025).fillna(0)
    _growth['growth_pct'] = _growth.apply(
        lambda r: ((r['devs_2025'] - r['devs_2024']) / r['devs_2024'] * 100) if r['devs_2024'] > 0 else (100 if r['devs_2025'] > 0 else 0),
        axis=1
    )

    # Merge with classification table
    df_with_growth = df_classification_table.merge(
        _growth.rename(columns={'project_name': 'Project'}),
        on='Project',
        how='left'
    ).fillna({'devs_2024': 0, 'devs_2025': 0, 'growth_pct': 0})

    # Calculate ROI (devs per ETH)
    df_with_growth['devs_per_eth'] = df_with_growth.apply(
        lambda r: r['Avg Devs/Mo'] / r['Total ETH'] if r['Total ETH'] > 0 else 0,
        axis=1
    )
    return (df_with_growth,)


@app.cell
def _(df_funding, df_project_tiers):
    # Merge funding with tiers
    df_funding_with_tiers = df_funding.merge(
        df_project_tiers[['project_name', 'tier_label']],
        left_on='oso_project_name',
        right_on='project_name',
        how='left'
    )
    df_funding_with_tiers['tier_label'] = df_funding_with_tiers['tier_label'].fillna('No OSS Footprint')
    return (df_funding_with_tiers,)


@app.cell(hide_code=True)
def _():
    # Tier classification thresholds - easy to tune
    RECENT_WINDOW_MONTHS = 6          # Months to consider "recent" activity
    MIN_DEVS_FOR_ACTIVE = 2           # Tier 2→3/4 threshold: avg devs/month
    ACTIVITY_DECLINE_PCT = 0.50       # Tier 3 threshold: current < X% of peak
    return ACTIVITY_DECLINE_PCT, MIN_DEVS_FOR_ACTIVE, RECENT_WINDOW_MONTHS


@app.cell(hide_code=True)
def _():
    # Colors and ordering for tier visualizations
    # Octant brand palette (from brand kit)
    TIER_COLORS = {
        'No OSS Footprint': '#9BA19A',       # Gray (neutral)
        'Minimal OSS Presence': '#FF9601',   # Orange (primary)
        'Mature/Stable': '#1C4557',          # Navy (neutral dark)
        'Active Development': '#2D9B87'      # Teal (primary)
    }

    TIER_ORDER = ['No OSS Footprint', 'Minimal OSS Presence', 'Mature/Stable', 'Active Development']

    # Qualitative palette for multi-project charts (top 10 + Other)
    OCTANT_PALETTE = [
        '#2D9B87',  # Teal (primary)
        '#FF9601',  # Orange (primary)
        '#1C4557',  # Navy
        '#78B0A0',  # Lighter teal
        '#D97A00',  # Darker orange
        '#2A5F7A',  # Blue-gray
        '#4DB8A4',  # Mid teal
        '#E8A940',  # Golden
        '#3D7A9E',  # Steel blue
        '#6BC4B0',  # Light teal
        '#CDD1CE',  # Gray (for "Other")
    ]
    return OCTANT_PALETTE, TIER_COLORS, TIER_ORDER


@app.cell(hide_code=True)
def _():
    # Octant brand-aligned Plotly layout
    PLOTLY_LAYOUT = dict(
        title="",
        barmode="relative",
        hovermode="x unified",
        dragmode=False,  # Disable zoom/pan for static output
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=12, family="system-ui, sans-serif", color="#181818"),
        margin=dict(t=60, l=60, r=80, b=60),  # Extra padding for annotations
        legend=dict(
            orientation="v",
            yanchor="top", y=0.98,
            xanchor="left", x=0.02,
            bordercolor="#CDD1CE", borderwidth=1,
            bgcolor="rgba(255,255,255,0.9)"
        ),
        xaxis=dict(
            title="",
            showgrid=False,
            linecolor="#181818", linewidth=1,
            ticks="outside"
        ),
        yaxis=dict(
            title="",
            showgrid=True, gridcolor="#D9DDDA",
            zeroline=True, zerolinecolor="#181818", zerolinewidth=1,
            linecolor="#181818", linewidth=1,
            ticks="outside", range=[0, None]
        ),
        # Minimal modebar for static output (keep hover, hide zoom controls)
        modebar=dict(
            remove=["zoom", "pan", "select", "lasso", "zoomIn", "zoomOut", "autoScale", "resetScale"]
        )
    )
    return (PLOTLY_LAYOUT,)


@app.cell(hide_code=True)
def _():
    stringify = lambda arr: "'" + "','".join([str(x) for x in arr]) + "'"

    # Helper to sort epochs numerically (Epoch 1, Epoch 2, ... Epoch 10)
    def sort_epochs(epochs):
        def epoch_key(e):
            try:
                return int(e.split()[-1])
            except (ValueError, AttributeError, IndexError):
                return 999
        return sorted(epochs, key=epoch_key)
    return sort_epochs, stringify


@app.cell(hide_code=True)
def _(pd):
    def add_epoch_markers(fig, df_funding, y_max, *, color="#2D9B87", dash="dot", width=2, with_labels=True):
        """Add vertical lines and labels for each funding epoch to a Plotly figure."""
        _epoch_dates = (
            df_funding
            .groupby('octant_epoch', as_index=False)['funding_date']
            .min()
            .sort_values('funding_date')
        )
        for _i, _row in _epoch_dates.iterrows():
            try:
                _epoch_date = pd.to_datetime(_row['funding_date'])
                # Add vertical line as shape
                fig.add_shape(
                    type="line",
                    x0=_epoch_date, x1=_epoch_date,
                    y0=0, y1=y_max,
                    line=dict(color=color, width=width, dash=dash),
                    yref="y"
                )
                # Add annotation separately
                if with_labels:
                    fig.add_annotation(
                        x=_epoch_date, y=y_max,
                        text=_row['octant_epoch'],
                        showarrow=False,
                        font=dict(size=8, color=color),
                        textangle=-45,
                        yanchor="bottom"
                    )
            except Exception:
                # Silently skip if date parsing or annotation fails
                pass
        return fig
    return (add_epoch_markers,)


@app.cell(hide_code=True)
def _():
    def stat_card(title, value, *, subtitle=None):
        """Return HTML for a styled stat card matching Octant brand."""
        _style = "background-color: #F8F8F8; padding: 16px; border-radius: 8px; text-align: center; border: 1px solid #CDD1CE;"
        _subtitle_html = f'<br/><small style="color: #9BA19A;">{subtitle}</small>' if subtitle else ''
        return f'<div style="{_style}"><strong>{title}</strong><br/><span style="font-size: 24px; font-weight: bold;">{value}</span>{_subtitle_html}</div>'
    return (stat_card,)


@app.cell(hide_code=True)
def _():
    import numpy as np
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    return go, np, pd, px


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
