import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Octant Portfolio Health: Measuring Grant Impact Through Open Data
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-12</span></small>
    """)
    return


@app.cell(hide_code=True)
def _(
    headline_1,
    headline_10,
    headline_11,
    headline_2,
    headline_3,
    headline_4,
    headline_5,
    headline_6,
    headline_7,
    headline_8,
    headline_9,
    mo,
):
    mo.md(f"""
    ## Context

    This analysis examines the health and impact of Octant's grant portfolio across all funding epochs.
    All amounts are displayed in **ETH**. Developer metrics (commits, contributors) only apply to 
    projects with GitHub repositories—not all funded projects are software-focused.

    Projects are classified into 4 tiers based on their open source activity level:
    1. **No OSS Footprint** - No GitHub repos matched
    2. **Minimal OSS Presence** - Has repos but very low activity
    3. **Mature/Stable** - High historical activity, declining recently
    4. **Active Development** - Steady or growing recent activity

    ## Key Insights

    1. {headline_1}
    2. {headline_2}
    3. {headline_3}
    4. {headline_4}
    5. {headline_5}
    6. {headline_6}
    7. {headline_7}
    8. {headline_8}
    9. {headline_9}
    10. {headline_10}
    11. {headline_11}

    ## Data Sources

    - [OSO Data Pipeline](https://docs.opensource.observer/) - Open source metrics and funding data
    - [OSS Directory](https://github.com/opensource-observer/oss-directory) - Project registry
    - [OpenDevData](https://opendevdata.org/) - Developer activity metrics
    """)
    return


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, TIER_COLORS, df_funding_with_tiers, mo, px):
    # Calculate totals
    _total_eth = df_funding_with_tiers['amount_eth'].sum()
    _total_projects = df_funding_with_tiers['oso_project_name'].nunique()
    _total_epochs = df_funding_with_tiers['octant_epoch'].nunique()

    # Aggregate by epoch for chart
    _df_by_epoch = (
        df_funding_with_tiers
        .groupby('octant_epoch', as_index=False)['amount_eth']
        .sum()
        .sort_values('octant_epoch')
    )

    headline_1 = f"Octant has deployed {_total_eth:,.0f} ETH to {_total_projects} projects across {_total_epochs} epochs"

    _fig = px.bar(
        _df_by_epoch,
        x='octant_epoch',
        y='amount_eth',
        labels={'octant_epoch': 'Epoch', 'amount_eth': 'ETH Allocated'}
    )
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(xaxis=dict(tickformat=None))
    _fig.update_traces(marker_color=TIER_COLORS['Active Development'])

    mo.vstack([
        mo.md(f"### **{headline_1}**"),
        mo.md("Funding has been distributed across multiple epochs, with varying allocation sizes based on community voting and project applications."),
        _fig
    ])
    return (headline_1,)


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, TIER_COLORS, TIER_ORDER, df_funding_with_tiers, mo, px):
    # Count projects per epoch per tier
    _df_epoch_tier = (
        df_funding_with_tiers
        .groupby(['octant_epoch', 'tier_label'])['oso_project_name']
        .nunique()
        .reset_index()
        .rename(columns={'oso_project_name': 'project_count'})
    )

    _total_projects = df_funding_with_tiers['oso_project_name'].nunique()
    _epochs_list = sorted(df_funding_with_tiers['octant_epoch'].unique())
    _first_epoch = _epochs_list[0] if _epochs_list else 'Unknown'

    headline_2 = f"{_total_projects} unique projects have received Octant funding since {_first_epoch}"

    _fig = px.bar(
        _df_epoch_tier,
        x='octant_epoch',
        y='project_count',
        color='tier_label',
        barmode='stack',
        color_discrete_map=TIER_COLORS,
        category_orders={'tier_label': TIER_ORDER},
        labels={'octant_epoch': 'Epoch', 'project_count': 'Projects Funded', 'tier_label': 'Project Type'}
    )
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(xaxis=dict(tickformat=None))

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_2}**

    Each bar shows how many projects were funded in that epoch, colored by their open source activity classification.
    Projects can receive funding in multiple epochs.
    """),
        _fig
    ])
    return (headline_2,)


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, TIER_COLORS, TIER_ORDER, df_project_tiers, mo, px):
    # Count projects by tier
    _tier_counts = (
        df_project_tiers
        .groupby('tier_label', as_index=False)
        .size()
        .rename(columns={'size': 'project_count'})
    )

    _total_projects = _tier_counts['project_count'].sum()
    _active_count = _tier_counts[_tier_counts['tier_label'] == 'Active Development']['project_count'].sum()
    _active_pct = (_active_count / _total_projects * 100) if _total_projects > 0 else 0

    headline_3 = f"{_active_pct:.0f}% of funded projects ({_active_count} of {_total_projects}) are actively developing open source software"

    _fig = px.bar(
        _tier_counts,
        x='tier_label',
        y='project_count',
        color='tier_label',
        color_discrete_map=TIER_COLORS,
        category_orders={'tier_label': TIER_ORDER},
        labels={'tier_label': 'Project Type', 'project_count': 'Number of Projects'}
    )
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(showlegend=False, xaxis=dict(tickformat=None, categoryorder='array', categoryarray=TIER_ORDER))

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_3}**

    Projects are classified based on their GitHub activity level. This distribution reflects Octant's 
    diverse funding approach—supporting community initiatives alongside software development.
    """),
        _fig
    ])
    return (headline_3,)


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, TIER_COLORS, TIER_ORDER, df_funding_with_tiers, mo, px):
    # Aggregate funding by tier
    _tier_funding = (
        df_funding_with_tiers
        .groupby('tier_label', as_index=False)['amount_eth']
        .sum()
    )

    _total_eth = _tier_funding['amount_eth'].sum()
    _active_eth = _tier_funding[_tier_funding['tier_label'] == 'Active Development']['amount_eth'].sum()
    _active_pct = (_active_eth / _total_eth * 100) if _total_eth > 0 else 0

    headline_4 = f"{_active_pct:.0f}% of ETH ({_active_eth:,.0f} of {_total_eth:,.0f}) went to actively developed software projects"

    _fig = px.bar(
        _tier_funding,
        x='tier_label',
        y='amount_eth',
        color='tier_label',
        color_discrete_map=TIER_COLORS,
        category_orders={'tier_label': TIER_ORDER},
        labels={'tier_label': 'Project Type', 'amount_eth': 'ETH Allocated'}
    )
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(showlegend=False, xaxis=dict(tickformat=None, categoryorder='array', categoryarray=TIER_ORDER))

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_4}**

    This shows how funding (in ETH) is distributed across project types. The allocation pattern 
    reflects both community preferences and the types of projects applying for Octant grants.
    """),
        _fig
    ])
    return (headline_4,)


@app.cell(hide_code=True)
def _(df_classification_table, mo):
    _df = df_classification_table.copy()
    _total = len(_df)

    headline_5 = f"Here's how all {_total} funded projects were classified and why"

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_5}**

    This table shows every project funded by Octant, their tier classification, and the metrics used to determine that classification.
    Projects with no GitHub repos are classified as "No OSS Footprint". The Activity Ratio compares recent activity to historical peak—
    a low ratio indicates a mature/stable project, while a high ratio indicates active development.
    """),
        mo.ui.table(
            _df.reset_index(drop=True),
            page_size=len(_df),
            show_column_summaries=False,
            show_data_types=False,
            freeze_columns_left=['Project', 'Tier']
        )
    ])
    return (headline_5,)


@app.cell(hide_code=True)
def _(df_project_tiers, df_repos, mo):
    # Filter to Tier 3+4 projects (software projects)
    _software_projects = df_project_tiers[
        df_project_tiers['tier_label'].isin(['Mature/Stable', 'Active Development'])
    ]['project_name'].unique()

    _software_repos = df_repos[df_repos['project_name'].isin(_software_projects)]
    _total_repos = _software_repos['repo_name'].nunique()

    # Get stars and forks
    _total_stars = _software_repos['star_count'].sum()
    _total_forks = _software_repos['fork_count'].sum()

    headline_6 = f"The software portfolio spans {_total_repos} repos with {_total_stars:,.0f} stars and {_total_forks:,.0f} forks"

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_6}**

    Focusing on Tier 3 (Mature/Stable) and Tier 4 (Active Development) projects, 
    which have meaningful open source presence.

    | Metric | Value |
    |--------|------:|
    | Total Repositories | {_total_repos:,} |
    | Total Stars | {_total_stars:,} |
    | Total Forks | {_total_forks:,} |
    | Software Projects | {len(_software_projects):,} |
    """)
    ])
    return (headline_6,)


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_contributors_by_project, mo, pd, px):
    _df = df_contributors_by_project.copy()

    if _df.empty:
        headline_7 = "No developer activity data available yet"
        mo.vstack([mo.md(f"---\n### **{headline_7}**\n\n*Waiting for data...*")])
    else:
        _df['day'] = pd.to_datetime(_df['day'])
        _df['total_devs'] = _df['full_time_devs'] + _df['part_time_devs']

        # Create month column for grouping (use string to avoid timestamp issues)
        _df['month_str'] = _df['day'].dt.strftime('%Y-%m')

        # Get top 10 projects by average developer activity (data is 28d rolling avg, so use mean)
        _project_avgs = _df.groupby('project_name')['total_devs'].mean().nlargest(10)
        _top_projects = _project_avgs.index.tolist()
        _top_avg = _project_avgs.mean()
        _overall_avg = _df.groupby('project_name')['total_devs'].mean().mean()
        _top_pct = (_top_avg / _overall_avg * 100) if _overall_avg > 0 else 0

        # Filter to top projects and aggregate monthly (use mean since data is 28d rolling avg)
        _df_top = _df[_df['project_name'].isin(_top_projects)].copy()
        _df_monthly = (
            _df_top
            .groupby(['month_str', 'project_name'], as_index=False)
            ['total_devs'].mean()
        )
        # Convert back to datetime for plotting
        _df_monthly['month'] = _df_monthly['month_str'].apply(lambda x: pd.to_datetime(str(x) + '-01'))

        headline_7 = f"These top 10 projects drive the majority of developer activity in the portfolio"

        _fig = px.area(
            _df_monthly,
            x='month',
            y='total_devs',
            color='project_name',
            color_discrete_sequence=px.colors.qualitative.Set2,
            labels={'month': '', 'total_devs': 'Active Developers', 'project_name': 'Project'}
        )
        _fig.update_layout(**PLOTLY_LAYOUT)

        mo.vstack([
            mo.md(f"""
    ---
    ### **{headline_7}**

    This stacked area chart shows developer activity over time for the most active projects in the portfolio.
    Each layer represents one project's contribution to total developer activity.
    """),
            _fig
        ])
    return (headline_7,)


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_contributors_by_project, go, mo, pd):
    # Aggregate developer activity over time
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

    # Add 3-month rolling average
    _monthly['rolling_avg'] = _monthly['total_devs'].rolling(window=3, min_periods=1).mean()

    if len(_monthly) >= 2:
        _first_half_avg = _monthly.head(len(_monthly)//2)['total_devs'].mean()
        _second_half_avg = _monthly.tail(len(_monthly)//2)['total_devs'].mean()
        _growth_pct = ((_second_half_avg - _first_half_avg) / _first_half_avg * 100) if _first_half_avg > 0 else 0
    else:
        _growth_pct = 0

    headline_8 = f"Total developer activity {'grew' if _growth_pct >= 0 else 'declined'} by {abs(_growth_pct):.0f}% across the portfolio"

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
    _fig.update_layout(**PLOTLY_LAYOUT)

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_8}**

    This tracks the total active developers per month across all software projects in the portfolio.
    The bold line shows a 3-month rolling average to smooth out monthly fluctuations.
    """),
        _fig
    ])
    return (headline_8,)


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_cohort_retention, mo, pd, px):
    _df = df_cohort_retention.copy()

    if not _df.empty and 'retention_pct' in _df.columns:
        # Create cohort retention heatmap
        _pivot = _df.pivot_table(
            index='cohort_label',
            columns='months_since_funding',
            values='retention_pct'
        ).fillna(0)

        # Get average retention metrics (handle NaN)
        _avg_3mo = _df[_df['months_since_funding'] == 3]['retention_pct'].mean()
        _avg_6mo = _df[_df['months_since_funding'] == 6]['retention_pct'].mean()
        _avg_3mo = 0 if pd.isna(_avg_3mo) else _avg_3mo
        _avg_6mo = 0 if pd.isna(_avg_6mo) else _avg_6mo

        headline_9 = f"Project retention: {_avg_3mo:.0f}% active at 3 months, {_avg_6mo:.0f}% at 6 months after funding"

        _fig = px.imshow(
            _pivot,
            labels=dict(x="Months Since Funding", y="Funding Epoch", color="Active %"),
            aspect="auto",
            color_continuous_scale="Blues"
        )
        _fig.update_layout(**PLOTLY_LAYOUT)
        _fig.update_layout(
            margin=dict(t=20, l=100, r=20, b=50),
            coloraxis_colorbar=dict(title="Active %")
        )

        _chart = _fig
    else:
        headline_9 = "Cohort retention data is being calculated"
        _chart = mo.md("*Cohort data unavailable - need more historical data*")

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_9}**

    This heatmap tracks how many projects from each funding epoch maintain active development N months later.
    Darker blue indicates higher retention of developer activity.
    """),
        _chart
    ])
    return (headline_9,)


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, df_contributors_by_project, mo, pd, px):
    # Aggregate full-time vs part-time over time
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

    _avg_ft = _monthly['full_time_devs'].mean()
    _avg_pt = _monthly['part_time_devs'].mean()
    _avg_all = _avg_ft + _avg_pt
    _ft_pct = (_avg_ft / _avg_all * 100) if _avg_all > 0 else 0

    headline_10 = f"{_ft_pct:.0f}% of developer activity comes from full-time contributors"

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
            'Full-Time (10+ commits/28d)': '#1f77b4',
            'Part-Time (<10 commits/28d)': '#aec7e8'
        },
        labels={'day': '', 'count': 'Developer Count', 'developer_type': 'Type'}
    )
    _fig.update_layout(**PLOTLY_LAYOUT)

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_10}**

    Full-time contributors are defined as developers with 10+ commits in a 28-day window.
    A healthy mix of full-time and part-time contributors indicates sustainable project development.
    """),
        _fig
    ])
    return (headline_10,)


@app.cell(hide_code=True)
def _(mo):
    headline_11 = "This analysis was built entirely on open, auditable data"

    mo.vstack([
        mo.md(f"""
    ---
    ### **{headline_11}**

    Every data point in this analysis comes from publicly accessible sources:

    - **Funding data** is sourced from the [OSS Directory](https://github.com/opensource-observer/oss-directory), 
      a community-maintained registry of open source projects and their funding history.

    - **Developer metrics** come from [OpenDevData](https://opendevdata.org/), which provides 
      anonymized, aggregated statistics about GitHub activity.

    - **All queries are reproducible** using the [OSO API](https://docs.opensource.observer/), 
      enabling anyone to verify findings or extend this analysis.

    This transparency is fundamental to building trust in impact measurement. Open data enables:
    - **Accountability** - Stakeholders can verify claims independently
    - **Reproducibility** - Researchers can replicate and extend analyses
    - **Community contribution** - Anyone can improve the methodology
    """)
    ])
    return (headline_11,)


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

    # Get project-specific data
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
    _n_projects = max(_df_all['project_name'].nunique(), 1)

    _df_proj_monthly = (
        _df_proj
        .groupby('month_str', as_index=False)
        ['total_devs'].mean()
    )
    # Convert string back to datetime for plotting (use apply to handle any edge cases)
    _df_proj_monthly['day'] = _df_proj_monthly['month_str'].apply(lambda x: pd.to_datetime(str(x) + '-01'))

    # Calculate portfolio average across all projects (use mean since data is 28d rolling avg)
    _df_avg_monthly = (
        _df_all
        .groupby(['month_str', 'project_name'], as_index=False)
        ['total_devs'].mean()
        .groupby('month_str', as_index=False)
        ['total_devs'].mean()  # Average across projects
    )
    _df_avg_monthly['day'] = _df_avg_monthly['month_str'].apply(lambda x: pd.to_datetime(str(x) + '-01'))

    # Get funding events for this project
    _funding_events = df_funding_with_tiers[
        df_funding_with_tiers['oso_project_name'] == _selected
    ][['funding_date', 'octant_epoch', 'amount_eth']].drop_duplicates()

    # Create comparison chart
    _fig = go.Figure()

    # Add funding event markers (with defensive type handling)
    for _, _row in _funding_events.iterrows():
        try:
            _funding_date_str = pd.to_datetime(_row['funding_date']).strftime('%Y-%m-%d')
            _amount = float(_row['amount_eth']) if pd.notna(_row['amount_eth']) else 0.0
            _epoch = str(_row['octant_epoch']) if pd.notna(_row['octant_epoch']) else 'Unknown'
            _fig.add_vline(
                x=_funding_date_str,
                line_dash="dash",
                line_color="green",
                annotation_text=f"{_epoch} ({_amount:.1f} ETH)",
                annotation_position="top"
            )
        except Exception:
            pass  # Skip problematic funding events

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
    _fig.update_layout(**PLOTLY_LAYOUT)
    _fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))

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

    mo.vstack([
        mo.md(f"""
    ### {_selected}

    | Metric | Value |
    |--------|-------|
    | Classification | {_tier} |
    | Total ETH Received | {_total_eth:,.2f} |
    | Epochs Funded | {_epochs_funded} |

    Green dashed lines indicate funding events. Compare the project's developer activity trend against the portfolio average.
    """),
        mo.ui.plotly(_fig)
    ])
    return


@app.cell(hide_code=True)
def _(ACTIVITY_DECLINE_PCT, MIN_DEVS_FOR_ACTIVE, RECENT_WINDOW_MONTHS, mo):
    mo.md(f"""
    ---

    # Methodology Details

    ## Part 1. Data Collection

    This analysis uses three primary data sources, all accessible via the OSO API:

    1. **Funding Data** (`stg_ossd__current_funding`) - Grant allocations from Octant epochs, 
       including project names and amounts in ETH.

    2. **Repository Data** (`int_opendevdata__repositories_with_repo_id`) - GitHub repository 
       metadata including stars, forks, and creation dates.

    3. **Developer Activity** (`stg_opendevdata__repo_developer_28d_activities`) - Rolling 28-day 
       developer activity counts per repository.

    ## Part 2. Project Classification

    Projects are classified into 4 tiers based on their GitHub activity:

    | Tier | Label | Criteria |
    |------|-------|----------|
    | 1 | No OSS Footprint | No GitHub repos matched in OSO |
    | 2 | Minimal OSS Presence | Avg devs/month < {MIN_DEVS_FOR_ACTIVE} |
    | 3 | Mature/Stable | Activity declined > {ACTIVITY_DECLINE_PCT*100:.0f}% in last {RECENT_WINDOW_MONTHS} months |
    | 4 | Active Development | Steady or growing activity in last {RECENT_WINDOW_MONTHS} months |

    ## Part 3. Assumptions and Limitations

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
def _(project_names):
    project_names
    return


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
            project_name,
            repo_id
          FROM int_gharchive__repositories
          JOIN repos USING (repo_name)
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
def _(df_repos):
    df_repos[df_repos['project_name'] == 'argotorg']
    return


@app.cell
def _(mo, pyoso_db_conn):
    # Query developer activity at the PROJECT level (not repo level)
    # This ensures each developer is counted once per project even if they work on multiple repos
    df_contributors_by_project = mo.sql(
        f"""
        WITH projects AS (
          SELECT DISTINCT to_project_name AS project_name
          FROM stg_ossd__current_funding
          WHERE from_funder_name = 'octant-golemfoundation'
            AND to_project_name IS NOT NULL
        ),
        repos AS (
          SELECT DISTINCT
            project_name,
            CONCAT(artifact_namespace, '/', artifact_name) AS repo_name
          FROM artifacts_by_project_v1
          JOIN projects USING (project_name)
          WHERE artifact_source = 'GITHUB'
        ),
        repo_ids AS (
          SELECT DISTINCT
            project_name,
            repo_id
          FROM int_gharchive__repositories
          JOIN repos USING (repo_name)
        ),
        repo_to_opendevdata AS (
          SELECT DISTINCT
            project_name,
            opendevdata_id
          FROM int_opendevdata__repositories_with_repo_id
          JOIN repo_ids USING (repo_id)
        )
        SELECT
          day,
          project_name,
          COUNT(DISTINCT IF(l28_days>=10, canonical_developer_id, NULL)) AS full_time_devs,
          COUNT(DISTINCT IF(l28_days<10, canonical_developer_id, NULL)) AS part_time_devs
        FROM stg_opendevdata__repo_developer_28d_activities
        JOIN repo_to_opendevdata ON repo_id = opendevdata_id
        GROUP BY 1, 2
        ORDER BY 1, 2
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_contributors_by_project,)


@app.cell
def _(df_contributors_by_project, pd):
    # Ensure day column is datetime
    df_contributors_by_project['day'] = pd.to_datetime(df_contributors_by_project['day'])
    return


@app.cell
def _(
    ACTIVITY_DECLINE_PCT,
    MIN_DEVS_FOR_ACTIVE,
    RECENT_WINDOW_MONTHS,
    df_contributors_by_project,
    df_funding,
    df_repos,
    pd,
):
    # Get all funded projects
    _all_projects = df_funding['oso_project_name'].dropna().unique()

    # Get projects with repos
    _projects_with_repos = df_repos['project_name'].unique()

    # Calculate activity metrics per project
    _df_activity = df_contributors_by_project.copy()
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


@app.cell
def _(df_contributors_by_project, df_funding, pd):
    # Build cohort retention: for each funding epoch, track how many projects remain active N months later

    # Handle empty input data
    if df_funding.empty or df_contributors_by_project.empty:
        df_cohort_retention = pd.DataFrame(columns=['cohort_label', 'months_since_funding', 'active_count', 'cohort_size', 'retention_pct'])
    else:
        _df_funding = df_funding.copy()
        _df_funding['funding_date'] = pd.to_datetime(_df_funding['funding_date'])
        # Use string format for cohort to avoid timestamp issues
        _df_funding['cohort_str'] = _df_funding['funding_date'].dt.strftime('%Y-%m')

        # Get first funding date per project (using string cohort)
        _first_funding = (
            _df_funding
            .groupby('oso_project_name', as_index=False)
            .agg({'cohort_str': 'min', 'funding_date': 'min'})
            .rename(columns={'oso_project_name': 'project_name'})
        )

        # Get monthly activity per project
        _df_activity = df_contributors_by_project.copy()
        _df_activity['day'] = pd.to_datetime(_df_activity['day'])
        _df_activity['activity_str'] = _df_activity['day'].dt.strftime('%Y-%m')
        _df_activity['total_devs'] = _df_activity['full_time_devs'] + _df_activity['part_time_devs']

        _monthly_activity = (
            _df_activity
            .groupby(['project_name', 'activity_str'], as_index=False)['total_devs']
            .mean()  # Use mean since daily data is 28d rolling avg
        )
        _monthly_activity['is_active'] = _monthly_activity['total_devs'] > 0.5  # At least half a dev on average

        # Join with cohort data
        _cohort_data = _first_funding.merge(_monthly_activity, on='project_name', how='inner')

        if _cohort_data.empty:
            df_cohort_retention = pd.DataFrame(columns=['cohort_label', 'months_since_funding', 'active_count', 'cohort_size', 'retention_pct'])
        else:
            # Calculate months difference using parsed year/month from strings
            _cohort_data['cohort_year'] = _cohort_data['cohort_str'].str[:4].astype(int)
            _cohort_data['cohort_month_num'] = _cohort_data['cohort_str'].str[5:7].astype(int)
            _cohort_data['activity_year'] = _cohort_data['activity_str'].str[:4].astype(int)
            _cohort_data['activity_month_num'] = _cohort_data['activity_str'].str[5:7].astype(int)

            _cohort_data['months_since_funding'] = (
                (_cohort_data['activity_year'] - _cohort_data['cohort_year']) * 12 +
                (_cohort_data['activity_month_num'] - _cohort_data['cohort_month_num'])
            )

            # Filter to 0-12 months since funding
            _cohort_data = _cohort_data[(_cohort_data['months_since_funding'] >= 0) & (_cohort_data['months_since_funding'] <= 12)]

            # Calculate retention per cohort
            _cohort_sizes = _first_funding.groupby('cohort_str').size().reset_index(name='cohort_size')

            _retention = (
                _cohort_data[_cohort_data['is_active']]
                .groupby(['cohort_str', 'months_since_funding'])['project_name']
                .nunique()
                .reset_index(name='active_count')
            )

            _retention = _retention.merge(_cohort_sizes, on='cohort_str', how='left')
            _retention['retention_pct'] = (_retention['active_count'] / _retention['cohort_size'] * 100).round(1)
            _retention = _retention.rename(columns={'cohort_str': 'cohort_label'})

            df_cohort_retention = _retention
    return (df_cohort_retention,)


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
    TIER_COLORS = {
        'No OSS Footprint': '#d62728',      # Red
        'Minimal OSS Presence': '#ff7f0e',   # Orange
        'Mature/Stable': '#2ca02c',          # Green
        'Active Development': '#1f77b4'      # Blue
    }

    TIER_ORDER = ['No OSS Footprint', 'Minimal OSS Presence', 'Mature/Stable', 'Active Development']
    return TIER_COLORS, TIER_ORDER


@app.cell(hide_code=True)
def _():
    PLOTLY_LAYOUT = dict(
        title="",
        barmode="relative",
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=12, color="#111"),
        margin=dict(t=20, l=60, r=20, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
            bgcolor="rgba(255,255,255,0.8)"
        ),
        xaxis=dict(
            title="",
            showgrid=False,
            linecolor="#000", linewidth=1,
            ticks="outside"
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
def _():
    stringify = lambda arr: "'" + "','".join([str(x) for x in arr]) + "'"
    return (stringify,)


@app.cell(hide_code=True)
def _():
    import numpy as np
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    return go, pd, px


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
