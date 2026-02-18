import marimo

__generated_with = "unknown"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def header_title(mo):
    mo.md(r"""
    # DeFi Developer Journeys
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-02-17</span></small>

    Analyze the health of the DeFi developer pipeline, working backwards from the top 50 projects on Ethereum and other L1s.
    """)
    return


@app.cell(hide_code=True)
def executive_framing(mo):
    mo.md("""
    **Framing.** This analysis covers 2020–2025 and focuses on *active DeFi developers*—operationalized here as developers with sustained (12+ months) observable open-source contribution to top TVL protocols. Structurally, inflow composition has shifted away from newcomers and non-crypto-native developers; the replacement rate for departing talent has declined. That shift matters now because it threatens long-run ecosystem vitality.

    **Core thesis.** Ethereum's biggest threat is not competition from other crypto ecosystems, but its declining ability to attract large numbers of newcomers and non-crypto-native developers.

    **What each section answers:**
    - **DeFi Landscape** — What is the universe of projects and developers we analyze?
    - **Year-by-Year Flows** — How do developers move between ecosystems over time?
    - **Feeder Projects** — Which projects attract and inspire future DeFi developers?
    - **Developer Imports & Exports** — What is the net talent balance across ecosystems?
    - **Cohort Retention** — How well does DeFi retain its developers over time?
    - **New Developer Inflow** — Where are new entrants coming from, and is that changing?
    - **Assumptions & Limitations** — What are the caveats and scope?
    - **Appendix** — Project-level application of the framework.
    """)
    return


@app.cell(hide_code=True)
def header_context_accordion(
    headline_1,
    headline_2,
    headline_3,
    headline_4,
    mo,
):
    _context = """
    **Thesis.** Ethereum DeFi is net accretive for developer talent. Most developer movement is either Ethereum → other Ethereum projects or within non-Ethereum ecosystems. Successful non-Ethereum DeFi projects are not primarily poaching from Ethereum.

    **Scope.** Top DeFi protocols by TVL with observable open-source activity — the economically meaningful layer of DeFi. High-TVL but low-OSS projects (custodial, TradFi-linked) are excluded or downweighted. This is not a census of all crypto developers; it is a structured analysis of visible OSS flows across the projects that matter most by locked capital.

    **Methodology.** "Qualified" developer = 12+ months sustained contribution to a top project. Onboarding = first month of home project activity; offboarding = 6+ months inactive. Activity data: 2018 through early 2026, via OpenDevData ecosystem mappings and GitHub Archive.
    """

    _insights = f"""
    1. {headline_1}.
    2. {headline_2}.
    3. {headline_3}.
    4. {headline_4}.
    """

    mo.accordion({
        "Context": _context,
        "Key Insights": _insights,
        "Data Sources": """
        - [DefiLlama](https://defillama.com/) - Top 50 DeFi protocols by TVL
        - [OSS Directory](https://github.com/opensource-observer/oss-directory) - Protocol to GitHub mapping
        - [OpenDevData (Electric Capital)](https://github.com/electric-capital/crypto-ecosystems) - Ecosystem classifications
        - [GitHub Archive](https://www.gharchive.org/) - Developer activity events
        - [OSO API](https://docs.opensource.observer/) - Data pipeline and metrics
        """
    })
    return


@app.cell(hide_code=True)
def ecosystem_toggle_cell(mo):
    ecosystem_toggle = mo.ui.radio(
        options={"Ethereum DeFi": "Ethereum", "Other DeFi": "Other"},
        value="Ethereum DeFi",
        label="",
    )
    return (ecosystem_toggle,)


@app.cell(hide_code=True)
def section_part1_header(df_activity, df_top_devs, mo, pct_eth_projects, pct_eth_tvl, pd):
    _total_devs = df_top_devs['canonical_developer_id'].nunique()
    _activity_min = pd.to_datetime(df_activity['month']).min()
    _activity_max = pd.to_datetime(df_activity['month']).max()
    mo.vstack([
        mo.md("---\n## We tracked developer movement across 50+ top DeFi projects on Ethereum and other chains"),
        mo.md(
            f'Every developer with at least 12 months of sustained contribution to a top project, '
            f'with activity spanning **{_activity_min.strftime("%B %Y")}** to **{_activity_max.strftime("%B %Y")}**.'
        ),
        mo.md(
            f'**{pct_eth_projects:.0f}%** of projects are native to the Ethereum ecosystem (including L2s like '
            f'Arbitrum and Base), accounting for **{pct_eth_tvl:.0f}%** of total TVL. The remainder spans Solana, BNB '
            f'Chain, Bitcoin, and other ecosystems.'
        ),
    ])
    return


@app.cell(hide_code=True)
def insight_part1_headline(ecosystem_toggle, pct_eth_projects, pct_eth_tvl):
    if ecosystem_toggle.value == 'Ethereum':
        headline_1 = f"{pct_eth_projects:.0f}% of top DeFi projects ({pct_eth_tvl:.0f}% of TVL) are in the Ethereum ecosystem"
    else:
        _pct_other = 100 - pct_eth_projects
        _pct_tvl_other = 100 - pct_eth_tvl
        headline_1 = f"{_pct_other:.0f}% of top DeFi projects ({_pct_tvl_other:.0f}% of TVL) are outside the Ethereum ecosystem"
    return (headline_1,)


@app.cell(hide_code=True)
def transform_protocol_table(
    df_monthly_devs,
    df_projects_with_eco,
    df_qualified_developers,
    df_tvl_history,
):
    # Prepare per-project stats for two SVG protocol tables (Ethereum / Other)
    import math as _math

    _projects = df_projects_with_eco[
        ['project_display_name', 'current_tvl', 'ecosystem_category', 'tvl_rank']
    ].copy()

    # --- Total qualified developers per project ---
    _total_devs = (
        df_qualified_developers
        .groupby('project_display_name')['canonical_developer_id']
        .nunique()
        .rename('total_devs')
    )
    _projects = _projects.merge(_total_devs, on='project_display_name', how='left')
    _projects['total_devs'] = _projects['total_devs'].fillna(0).astype(int)

    # --- Dev activity sparkline (monthly active devs since 2020) ---
    _monthly = df_monthly_devs[df_monthly_devs['month_str'] >= '2020-01'].copy()
    _all_dev_months = sorted(_monthly['month_str'].unique())
    _pivot = _monthly.pivot_table(
        index='project_display_name',
        columns='month_str',
        values='monthly_active_devs',
        aggfunc='sum',
        fill_value=0,
    ).reindex(columns=_all_dev_months, fill_value=0)
    _dev_sparklines = {}
    for _proj in _pivot.index:
        _dev_sparklines[_proj] = _pivot.loc[_proj].tolist()
    _projects['dev_sparkline'] = _projects['project_display_name'].map(_dev_sparklines)

    # --- TVL sparkline (monthly TVL since 2020) ---
    _tvl = df_tvl_history.copy()
    # Convert sample_date to month string for consistent ordering
    _tvl['month_str'] = _tvl['sample_date'].astype(str).str[:7]
    # Drop partial current month (Feb 2026)
    _all_tvl_months = sorted(_tvl['month_str'].unique())
    if len(_all_tvl_months) > 1:
        _all_tvl_months = _all_tvl_months[:-1]  # drop last partial month
        _tvl = _tvl[_tvl['month_str'].isin(_all_tvl_months)]
    _tvl_pivot = _tvl.pivot_table(
        index='project_display_name',
        columns='month_str',
        values='tvl',
        aggfunc='sum',
        fill_value=0,
    ).reindex(columns=_all_tvl_months, fill_value=0)
    _tvl_sparklines = {}
    for _proj in _tvl_pivot.index:
        _tvl_sparklines[_proj] = _tvl_pivot.loc[_proj].tolist()
    _projects['tvl_sparkline'] = _projects['project_display_name'].map(_tvl_sparklines)

    _projects['tvl_log'] = _projects['current_tvl'].apply(lambda x: _math.log10(max(x, 1)))
    _projects = _projects.sort_values('tvl_rank')

    df_protocol_table = _projects
    sparkline_months = _all_dev_months
    tvl_sparkline_months = _all_tvl_months
    return (df_protocol_table,)


@app.cell(hide_code=True)
def insight_protocol_table(
    ETHEREUM_COLOR,
    OTHER_CRYPTO_COLOR,
    df_protocol_table,
    mo,
):
    # Single SVG protocol table — all projects, colored by ecosystem
    _df = df_protocol_table.copy().reset_index(drop=True)
    _n = len(_df)

    _FS_HDR = 14
    _FS_BODY = 12
    _FS_MUTED = 12

    _ROW_H = 18
    _HDR_H = 30
    _MTOP = 8
    _SPARK_W = 420  # same width for both sparklines

    # Column positions
    _C_RANK = 20
    _C_NAME = 44
    _C_TVL = 260
    _C_TVL_SPARK = 280
    _C_DEVS = 280 + _SPARK_W + 30  # 650
    _C_DEV_SPARK = _C_DEVS + 20    # 670
    _TABLE_R = _C_DEV_SPARK + _SPARK_W + 10  # 1020
    _VB_W = _TABLE_R + 20  # 1040
    _VB_H = _MTOP + _HDR_H + _n * _ROW_H + 12

    _svg = [
        f'<svg viewBox="0 0 {_VB_W} {_VB_H}" '
        f'style="width:100%;max-width:1040px;height:auto;display:block;margin:0;" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'font-family="system-ui, -apple-system, sans-serif">',
    ]

    # Header row
    _hy = _MTOP + _HDR_H - 9
    for _hx, _ha, _ht in [
        (_C_RANK + 12, 'end', '#'),
        (_C_NAME, 'start', 'PROJECT'),
        (_C_TVL, 'end', 'TVL'),
        (_C_TVL_SPARK + _SPARK_W // 2, 'middle', 'TVL HISTORY'),
        (_C_DEVS, 'end', 'DEVS'),
        (_C_DEV_SPARK + _SPARK_W // 2, 'middle', 'DEV ACTIVITY'),
    ]:
        _svg.append(
            f'<text x="{_hx}" y="{_hy}" text-anchor="{_ha}" '
            f'font-size="{_FS_HDR}" fill="#6B7280" font-weight="600" letter-spacing="0.6">{_ht}</text>'
        )

    _svg.append(
        f'<line x1="14" y1="{_MTOP + _HDR_H - 2}" x2="{_TABLE_R}" '
        f'y2="{_MTOP + _HDR_H - 2}" stroke="#E5E7EB" stroke-width="0.5"/>'
    )

    # Data rows
    for _idx, (_, _row) in enumerate(_df.iterrows()):
        _ry = _MTOP + _HDR_H + _idx * _ROW_H
        _ty = _ry + _ROW_H - 5
        _my = _ry + _ROW_H / 2
        _spark_color = ETHEREUM_COLOR if _row.get('ecosystem_category') == 'Ethereum' else OTHER_CRYPTO_COLOR
        # Alternating row bg
        if _idx % 2 == 0:
            _svg.append(
                f'<rect x="14" y="{_ry}" width="{_TABLE_R - 14}" '
                f'height="{_ROW_H}" fill="rgba(0,0,0,0.02)" rx="1"/>'
            )

        # Rank
        _svg.append(
            f'<text x="{_C_RANK + 12}" y="{_ty}" text-anchor="end" '
            f'font-size="{_FS_MUTED}" fill="#6B7280">{int(_row["tvl_rank"])}</text>'
        )

        # Project name
        _name = _row['project_display_name']
        if len(_name) > 26:
            _name = _name[:24] + '\u2026'

        _svg.append(
            f'<text x="{_C_NAME}" y="{_ty}" font-size="{_FS_BODY}" fill="#1F2937">{_name}</text>'
        )

        # TVL value
        _tvl = _row['current_tvl']
        if _tvl >= 1e9:
            _tvl_s = f'${_tvl / 1e9:.1f}B'
        elif _tvl >= 1e6:
            _tvl_s = f'${_tvl / 1e6:.0f}M'
        else:
            _tvl_s = f'${_tvl / 1e3:.0f}K'

        _svg.append(
            f'<text x="{_C_TVL}" y="{_ty}" text-anchor="end" '
            f'font-size="{_FS_MUTED}" fill="#6B7280">{_tvl_s}</text>'
        )

        # TVL sparkline
        _tvl_spark = _row.get('tvl_sparkline')
        if isinstance(_tvl_spark, list) and len(_tvl_spark) > 1:
            _sh = _ROW_H - 5
            _sy0 = _ry + 2.5
            _smax = max(_tvl_spark) or 1
            _pts = []
            for _si, _sv in enumerate(_tvl_spark):
                _px = _C_TVL_SPARK + (_si / (len(_tvl_spark) - 1)) * _SPARK_W
                _py = _sy0 + _sh - (_sv / _smax) * _sh
                _pts.append(f'{_px:.1f},{_py:.1f}')

            _area = (
                [f'{_C_TVL_SPARK:.1f},{_sy0 + _sh:.1f}'] + _pts
                + [f'{_C_TVL_SPARK + _SPARK_W:.1f},{_sy0 + _sh:.1f}']
            )

            _svg.append(f'<polygon points="{" ".join(_area)}" fill="{_spark_color}" opacity="0.25"/>')
            _svg.append(
                f'<polyline points="{" ".join(_pts)}" fill="none" '
                f'stroke="{_spark_color}" stroke-width="0.7" opacity="0.6"/>'
            )

        # Dev count (total qualified)
        _dev = int(_row['total_devs'])
        _svg.append(
            f'<text x="{_C_DEVS}" y="{_ty}" text-anchor="end" '
            f'font-size="{_FS_MUTED}" fill="#6B7280">{_dev}</text>'
        )

        # Dev activity sparkline
        _dev_spark = _row.get('dev_sparkline')
        if isinstance(_dev_spark, list) and len(_dev_spark) > 1:
            _sh = _ROW_H - 5
            _sy0 = _ry + 2.5
            _smax = max(_dev_spark) or 1
            _pts = []
            for _si, _sv in enumerate(_dev_spark):
                _px = _C_DEV_SPARK + (_si / (len(_dev_spark) - 1)) * _SPARK_W
                _py = _sy0 + _sh - (_sv / _smax) * _sh
                _pts.append(f'{_px:.1f},{_py:.1f}')

            _area = (
                [f'{_C_DEV_SPARK:.1f},{_sy0 + _sh:.1f}'] + _pts
                + [f'{_C_DEV_SPARK + _SPARK_W:.1f},{_sy0 + _sh:.1f}']
            )

            _svg.append(f'<polygon points="{" ".join(_area)}" fill="{_spark_color}" opacity="0.25"/>')
            _svg.append(
                f'<polyline points="{" ".join(_pts)}" fill="none" '
                f'stroke="{_spark_color}" stroke-width="0.7" opacity="0.6"/>'
            )
    _svg.append('</svg>')

    mo.vstack([
        mo.Html("\n".join(_svg)),
        mo.md(
            f'Sparklines show monthly data since 2020. Dev counts reflect total *qualified* developers (12+ months activity). '
            f'<span style="color:{ETHEREUM_COLOR}">&#9632;</span> Ethereum &nbsp; '
            f'<span style="color:{OTHER_CRYPTO_COLOR}">&#9632;</span> Other chains'
        ),
    ])
    return


@app.cell(hide_code=True)
def section_alluvial_pool(alluvial_stats, ecosystem_toggle, mo):
    _n = alluvial_stats.get('total_devs', 0) if not alluvial_stats.get('empty') else 0
    mo.vstack([
        mo.md("---"),
        ecosystem_toggle,
        mo.md(f"### This diagram displays the flow of all {_n} developers to/from each project and across ecosystems."),
    ])
    return


@app.cell(hide_code=True)
def section_alluvial_header(
    PROJECT_ECOSYSTEM,
    df_with_status,
    ecosystem_toggle,
    mo,
):
    # Scope available projects based on ecosystem toggle
    _active_eco = ecosystem_toggle.value
    _all_projects = sorted(df_with_status['project_display_name'].unique())
    if _active_eco == 'Ethereum':
        _available = [p for p in _all_projects if PROJECT_ECOSYSTEM.get(p) == 'Ethereum']
    else:
        _available = [p for p in _all_projects if PROJECT_ECOSYSTEM.get(p) != 'Ethereum']

    alluvial_project_filter = mo.ui.multiselect(
        options=_available,
        value=_available,
        label='Show projects individually:',
    )
    mo.vstack([
        alluvial_project_filter,
        mo.md('<small>*Flows show where developers were active before joining and where they went afterward, by ecosystem.*</small>'),
    ])
    return (alluvial_project_filter,)


@app.cell(hide_code=True)
def transform_alluvial_data(
    PROJECT_ECOSYSTEM,
    alluvial_project_filter,
    df_alignment,
    df_developer_lifecycle,
    df_with_status,
    ecosystem_toggle,
    pd,
):
    # Build yearly state classification for each developer (2020-2025)
    # Filter selects which projects' developers to include in the pool
    # Talent Sources (before) → Project Core → Talent Destinations (after)

    _DISPLAY_NAMES = {
        'Sky (prev. MakerDAO)': 'Sky/Maker',
        'Wormhole Foundation': 'Wormhole',
        'Spark Foundation': 'Spark',
        'Offchain Labs': 'Arbitrum',
        'Steakhouse Financial': 'Steakhouse',
        'Aerodrome Finance': 'Aerodrome',
        'Convex Finance': 'Convex',
        'Euler Finance': 'Euler',
        'Renzo Protocol': 'Renzo',
        'Jupiter Exchange': 'Jupiter',
        'Kamino Finance': 'Kamino',
        'Polygon zkEVM': 'Polygon zk',
        'Falcon Finance': 'Falcon',
        'Bedrock Technology': 'Bedrock',
        'Tornado Cash': 'Tornado',
        'BlackRock BUIDL': 'BlackRock',
        'Solv Protocol': 'Solv',
        'Kelp': 'Kelp DAO',
    }

    _YEARS = [2020, 2021, 2022, 2023, 2024, 2025]
    _selected = set(alluvial_project_filter.value) if alluvial_project_filter.value else set()

    if not _selected:
        alluvial_data = None
        alluvial_stats = {'empty': True}
    else:
        # --- 1. Filter developer pool to only those from selected projects ---
        _pool = df_developer_lifecycle[
            df_developer_lifecycle['project_display_name'].isin(_selected)
        ].copy()
        _pool_ids = _pool['canonical_developer_id'].unique()

        # Earliest onboard year per developer (across their selected projects)
        _onboard = _pool[['canonical_developer_id', 'onboard_month']].dropna(subset=['onboard_month']).copy()
        _onboard['onboard_year'] = _onboard['onboard_month'].dt.year
        _dev_onboard = (
            _onboard.groupby('canonical_developer_id')['onboard_year']
            .min()
            .reset_index()
        )

        # Background per developer (take first row per dev from df_with_status)
        _dev_bg = (
            df_with_status[df_with_status['canonical_developer_id'].isin(_pool_ids)]
            .drop_duplicates('canonical_developer_id')
            [['canonical_developer_id', 'is_direct_to_defi', 'pre_primary_ecosystem']]
        )

        # --- 2. Aggregate alignment data to yearly level ---
        _align = df_alignment[df_alignment['canonical_developer_id'].isin(_pool_ids)].copy()
        _align['year'] = _align['month'].dt.year
        _align = _align[_align['year'].between(2020, 2025)]

        # Yearly activity totals
        _yearly_totals = (
            _align.groupby(['canonical_developer_id', 'year'])
            .agg(
                home_days=('home_project_repo_event_days', 'sum'),
                crypto_days=('crypto_repo_event_days', 'sum'),
                oss_days=('oss_repo_event_days', 'sum'),
                personal_days=('personal_repo_event_days', 'sum'),
            )
            .reset_index()
        )

        # Primary home project per developer per year
        _home_activity = _align[_align['has_home_project_activity'] == True].copy()
        _home_by_year = (
            _home_activity.groupby(['canonical_developer_id', 'year', 'home_project_name'])
            .agg(days=('home_project_repo_event_days', 'sum'))
            .reset_index()
            .sort_values('days', ascending=False)
            .drop_duplicates(['canonical_developer_id', 'year'], keep='first')
            .rename(columns={'home_project_name': 'primary_project'})
            [['canonical_developer_id', 'year', 'primary_project']]
        )

        # Primary crypto ecosystem per developer per year (for non-home activity)
        _crypto_eco = (
            _align[_align['crypto_repo_event_days'] > 0]
            .groupby(['canonical_developer_id', 'year', 'crypto_primary_ecosystem'])
            .agg(days=('crypto_repo_event_days', 'sum'))
            .reset_index()
            .sort_values('days', ascending=False)
            .drop_duplicates(['canonical_developer_id', 'year'], keep='first')
            .rename(columns={'crypto_primary_ecosystem': 'crypto_ecosystem'})
            [['canonical_developer_id', 'year', 'crypto_ecosystem']]
        )

        # --- 3. Build full grid: pool devs × years ---
        _dev_ids = pd.DataFrame({'canonical_developer_id': _pool_ids})
        _years_df = pd.DataFrame({'year': _YEARS})
        _grid = _dev_ids.merge(_years_df, how='cross')
        _grid = _grid.merge(_dev_onboard, on='canonical_developer_id', how='left')
        _grid = _grid.merge(_dev_bg, on='canonical_developer_id', how='left')
        _grid = _grid.merge(_yearly_totals, on=['canonical_developer_id', 'year'], how='left')
        _grid = _grid.merge(_home_by_year, on=['canonical_developer_id', 'year'], how='left')
        _grid = _grid.merge(_crypto_eco, on=['canonical_developer_id', 'year'], how='left')
        _grid['home_days'] = _grid['home_days'].fillna(0)
        _grid['crypto_days'] = _grid['crypto_days'].fillna(0)
        _grid['oss_days'] = _grid['oss_days'].fillna(0)
        _grid['personal_days'] = _grid['personal_days'].fillna(0)

        # --- 4. Classify state ---
        # Ecosystem pools: combined before/after categories
        # Project Core: active on a selected project
        def _classify(row):
            # BEFORE ONBOARD: years before a known onboard year
            if pd.notna(row['onboard_year']) and row['year'] < row['onboard_year']:
                if pd.notna(row['pre_primary_ecosystem']) and row['pre_primary_ecosystem'] == 'Ethereum':
                    return 'Ethereum projects'
                if pd.notna(row['pre_primary_ecosystem']):
                    return 'Other crypto'
                if not row['is_direct_to_defi']:
                    return 'Non-crypto OSS'
                return 'Inactive'
            # PROJECT CORE: active on a selected project this year
            if row['home_days'] > 0 and pd.notna(row['primary_project']):
                _proj = row['primary_project']
                _short = _DISPLAY_NAMES.get(_proj, _proj)
                if _proj in _selected:
                    return _short
                # Active on a non-selected project
                _eco = PROJECT_ECOSYSTEM.get(_proj, 'Other')
                if _eco == 'Ethereum':
                    return 'Ethereum projects'
                return 'Other crypto'
            # Active in crypto but no home project — use crypto ecosystem
            if row['crypto_days'] > 0:
                if row.get('crypto_ecosystem') == 'Ethereum':
                    return 'Ethereum projects'
                return 'Other crypto'
            # Non-crypto OSS activity only
            if row['oss_days'] > 0 or row['personal_days'] > 0:
                return 'Non-crypto OSS'
            # No onboard year and no activity → classify by background
            if pd.isna(row['onboard_year']):
                if pd.notna(row['pre_primary_ecosystem']) and row['pre_primary_ecosystem'] == 'Ethereum':
                    return 'Ethereum projects'
                if pd.notna(row['pre_primary_ecosystem']):
                    return 'Other crypto'
                if not row['is_direct_to_defi']:
                    return 'Non-crypto OSS'
                return 'Inactive'
            return 'Inactive'

        _grid['display_state'] = _grid.apply(_classify, axis=1)

        # Track which states are "on selected project" for coloring
        _project_states = set()
        for _p in _selected:
            _project_states.add(_DISPLAY_NAMES.get(_p, _p))

        # --- 5. Build nodes and links ---
        _node_counts = (
            _grid.groupby(['year', 'display_state'])
            .size()
            .reset_index(name='count')
        )

        # Home projects (bottom) → same ecosystem → rival ecosystem → Non-crypto → Inactive (top)
        _is_eth = ecosystem_toggle.value == 'Ethereum'
        def _state_sort_key(state):
            # Zone 0 (top): Inactive
            if state == 'Inactive':
                return (0, 0, '')
            # Zone 1: Non-crypto OSS
            if state == 'Non-crypto OSS':
                return (1, 0, '')
            # Zone 2: Rival ecosystem
            if _is_eth and state == 'Other crypto':
                return (2, 0, '')
            if not _is_eth and state == 'Ethereum projects':
                return (2, 0, '')
            # Zone 3: Same ecosystem
            if _is_eth and state == 'Ethereum projects':
                return (3, 0, '')
            if not _is_eth and state == 'Other crypto':
                return (3, 0, '')
            # Zone 4 (bottom): Home projects
            if state in _project_states:
                return (4, 0, state)
            return (5, 0, state)

        _nodes_by_year = {}
        for _yr in _YEARS:
            _yr_nodes = _node_counts[_node_counts['year'] == _yr].copy()
            _yr_nodes['sort_key'] = _yr_nodes['display_state'].apply(_state_sort_key)
            _yr_nodes = _yr_nodes.sort_values('sort_key').reset_index(drop=True)
            _nodes_by_year[_yr] = _yr_nodes[['display_state', 'count']].to_dict('records')

        # Links: transitions between consecutive years
        _links = []
        for _i in range(len(_YEARS) - 1):
            _yr_a, _yr_b = _YEARS[_i], _YEARS[_i + 1]
            _left = _grid[_grid['year'] == _yr_a][['canonical_developer_id', 'display_state']].rename(
                columns={'display_state': 'source_state'}
            )
            _right = _grid[_grid['year'] == _yr_b][['canonical_developer_id', 'display_state']].rename(
                columns={'display_state': 'target_state'}
            )
            _transitions = _left.merge(_right, on='canonical_developer_id')
            _link_counts = (
                _transitions.groupby(['source_state', 'target_state'])
                .size()
                .reset_index(name='count')
            )
            for _, _row in _link_counts.iterrows():
                _links.append({
                    'source_year': _yr_a,
                    'target_year': _yr_b,
                    'source_state': _row['source_state'],
                    'target_state': _row['target_state'],
                    'count': _row['count'],
                })

        alluvial_data = {
            'nodes_by_year': _nodes_by_year,
            'links': _links,
            'years': _YEARS,
            'project_states': _project_states,
            '_selected_projects': _selected,
            '_display_names': _DISPLAY_NAMES,
            '_project_ecosystem': PROJECT_ECOSYSTEM,
        }
        alluvial_stats = {
            'empty': False,
            'total_devs': len(_pool_ids),
            'n_projects': len(_selected),
        }
    return alluvial_data, alluvial_stats


@app.cell(hide_code=True)
def insight_alluvial_journeys(ETHEREUM_COLOR, ETHEREUM_LIGHT, OTHER_CRYPTO_COLOR, OTHER_CRYPTO_LIGHT, INACTIVE_COLOR, alluvial_data, alluvial_stats, ecosystem_toggle, mo):
    if alluvial_data is None or alluvial_stats.get('empty'):
        _output = mo.callout(mo.md('**No projects selected.** Use the filter above to choose projects.'), kind='warn')
    else:
        _years = alluvial_data['years']
        _nodes_by_year = alluvial_data['nodes_by_year']
        _links = alluvial_data['links']
        _project_states = alluvial_data['project_states']

        # --- Color mapping ---
        # Fixed category colors + toggle-aware home projects
        _is_eth_active = ecosystem_toggle.value == 'Ethereum'
        _active_color = ETHEREUM_COLOR if _is_eth_active else OTHER_CRYPTO_COLOR
        _CLR_ETH_POOL = '#CDC4F5'      # pastel lavender (light Ethereum)
        _CLR_OTHER_POOL = '#A0DCD8'    # pastel teal (light Other crypto)
        _CLR_NON_CRYPTO = '#B8D9F8'    # pastel blue
        _CLR_INACTIVE = '#FEF7E0'      # pastel yellow

        def _state_color(state):
            if state == 'Ethereum projects':
                return _CLR_ETH_POOL
            if state == 'Other crypto':
                return _CLR_OTHER_POOL
            if state == 'Non-crypto OSS':
                return _CLR_NON_CRYPTO
            if state == 'Inactive':
                return _CLR_INACTIVE
            # Home projects — full active color
            if state in _project_states:
                return _active_color
            return INACTIVE_COLOR

        def _hex_to_rgba(hex_color, alpha=0.35):
            h = hex_color.lstrip('#')
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return f'rgba({r},{g},{b},{alpha})'

        # --- SVG layout (wider margins for labels) ---
        _VB_W = 1600
        _NW = 14
        _COL_X = [220, 450, 680, 910, 1140, 1360]
        _MTOP = 50
        _PAD = 4
        _MIN_H = 1.5

        _total = max(sum(n['count'] for n in _nodes_by_year[_years[0]]), 1)
        _max_nodes = max(len(_nodes_by_year[yr]) for yr in _years)
        _target_h = max(600, _max_nodes * 30)
        _avail = _target_h - 2 * _MTOP
        _pad_total = max(0, _max_nodes - 1) * _PAD
        _node_area = _avail - _pad_total
        _scale = _node_area / _total

        _all_counts = [n['count'] for yr in _years for n in _nodes_by_year[yr]]
        _min_count = min(_all_counts) if _all_counts else 1
        if _min_count * _scale < _MIN_H:
            _scale = _MIN_H / max(_min_count, 1)
            _target_h = _total * _scale + _pad_total + 2 * _MTOP
            _avail = _target_h - 2 * _MTOP

        # --- Position nodes ---
        _node_positions = {}
        for ci, yr in enumerate(_years):
            _col_nodes = _nodes_by_year[yr]
            _col_total = sum(n['count'] for n in _col_nodes)
            _col_pads = max(0, len(_col_nodes) - 1) * _PAD
            _col_h = _col_total * _scale + _col_pads
            _y = _MTOP + (_avail - _col_h) / 2
            for n in _col_nodes:
                _nh = max(_MIN_H, n['count'] * _scale)
                _key = (yr, n['display_state'])
                _node_positions[_key] = {
                    'y0': _y,
                    'y1': _y + _nh,
                    'x0': _COL_X[ci],
                    'x1': _COL_X[ci] + _NW,
                    'count': n['count'],
                    'state': n['display_state'],
                    'color': _state_color(n['display_state']),
                }
                _y += _nh + _PAD

        # --- Compute link paths ---
        _src_y_offsets = {k: v['y0'] for k, v in _node_positions.items()}
        _tgt_y_offsets = {k: v['y0'] for k, v in _node_positions.items()}
        _link_paths = []
        for _i in range(len(_years) - 1):
            _yr_a, _yr_b = _years[_i], _years[_i + 1]
            _zone_links = [l for l in _links if l['source_year'] == _yr_a]
            _zone_links.sort(key=lambda l: (
                _node_positions.get((_yr_a, l['source_state']), {}).get('y0', 0),
                _node_positions.get((_yr_b, l['target_state']), {}).get('y0', 0),
            ))
            for l in _zone_links:
                _sk = (_yr_a, l['source_state'])
                _tk = (_yr_b, l['target_state'])
                if _sk not in _node_positions or _tk not in _node_positions:
                    continue
                _s = _node_positions[_sk]
                _t = _node_positions[_tk]
                _lw = max(_MIN_H, l['count'] * _scale)
                _sy = _src_y_offsets[_sk]
                _src_y_offsets[_sk] += _lw
                _ty = _tgt_y_offsets[_tk]
                _tgt_y_offsets[_tk] += _lw
                _sx = _s['x1']
                _tx = _t['x0']
                _mx = (_sx + _tx) / 2
                _d = (
                    f"M {_sx:.1f},{_sy:.1f} "
                    f"C {_mx:.1f},{_sy:.1f} {_mx:.1f},{_ty:.1f} {_tx:.1f},{_ty:.1f} "
                    f"L {_tx:.1f},{_ty + _lw:.1f} "
                    f"C {_mx:.1f},{_ty + _lw:.1f} {_mx:.1f},{_sy + _lw:.1f} {_sx:.1f},{_sy + _lw:.1f} Z"
                )
                _color = _hex_to_rgba(_s['color'], 0.25)
                _link_paths.append((_d, _color, l['count'], l['source_state'], l['target_state']))

        # --- Assemble SVG ---
        _svg = [
            f'<svg viewBox="0 0 {_VB_W} {_target_h:.0f}" '
            f'style="width:100%;height:auto;" xmlns="http://www.w3.org/2000/svg" '
            f'font-family="system-ui, -apple-system, sans-serif">',
            '<style>.al-lk{transition:opacity .15s}.al-lk:hover{opacity:.7!important}</style>',
        ]

        for _d, _c, _v, _sl, _tl in _link_paths:
            _svg.append(
                f'<path class="al-lk" d="{_d}" fill="{_c}" opacity="0.4">'
                f'<title>{_sl} \u2192 {_tl}: {_v} developers</title></path>'
            )

        for _key, _n in _node_positions.items():
            _nh = max(_MIN_H, _n['y1'] - _n['y0'])
            _svg.append(
                f'<rect x="{_n["x0"]}" y="{_n["y0"]:.1f}" width="{_NW}" '
                f'height="{_nh:.1f}" fill="{_n["color"]}" stroke="#fff" stroke-width="0.5">'
                f'<title>{_n["state"]}: {_n["count"]} developers</title></rect>'
            )

        # Labels: single line "Name · count"
        for _key, _n in _node_positions.items():
            _yr, _state = _key
            _ym = (_n['y0'] + _n['y1']) / 2
            _display_label = _state
            if _yr == _years[0]:
                _lx = _n['x0'] - 6
                _anc = 'end'
                _fs = 10
            else:
                _lx = _n['x1'] + 5
                _anc = 'start'
                _fs = 9 if _yr == _years[-1] else 8
            _svg.append(
                f'<text x="{_lx}" y="{_ym:.1f}" dy="0.35em" text-anchor="{_anc}" '
                f'font-size="{_fs}" fill="#1F2937">'
                f'{_display_label} <tspan fill="#6B7280">\u00b7 {_n["count"]}</tspan></text>'
            )

        # Year column headers
        for _ci, _yr in enumerate(_years):
            _cx = _COL_X[_ci] + _NW / 2
            _label = f'{_yr}*' if _yr == 2025 else str(_yr)
            _svg.append(
                f'<text x="{_cx}" y="25" text-anchor="middle" font-size="13" '
                f'font-weight="600" fill="#6B7280">{_label}</text>'
            )

        _svg.append('</svg>')

        _legend = (
            f'<span style="color:{_active_color}">&#9632;</span> Home projects &nbsp; '
            f'<span style="color:{_CLR_ETH_POOL}">&#9632;</span> Ethereum &nbsp; '
            f'<span style="color:{_CLR_OTHER_POOL}">&#9632;</span> Other crypto &nbsp; '
            f'<span style="color:{_CLR_NON_CRYPTO}">&#9632;</span> Non-crypto OSS &nbsp; '
            f'<span style="color:{_CLR_INACTIVE}">&#9632;</span> Inactive'
        )

        _n_devs = alluvial_stats['total_devs']
        _n_proj = alluvial_stats['n_projects']
        _output = mo.vstack([
            mo.md('<small>' + _legend + '</small>'),
            mo.Html('\n'.join(_svg)),
            mo.md(
                f'**{_n_devs} developers from {_n_proj} project{"s" if _n_proj != 1 else ""}, tracked 2020\u20132025.** '
                'Ecosystem pools (top) and non-crypto/inactive (bottom) show where developers came from and went to. '
                'Home project nodes (middle) show active contributors. '
                '*2025 data is partial.*'
            ),
        ])
    _output
    return


@app.cell(hide_code=True)
def transform_qualified_developers(df_alignment, df_top_devs):
    # US-007: Filter to developers with 12+ months on home project
    # Count months with home project activity per developer
    _home_months = (
        df_alignment[df_alignment['has_home_project_activity'] == True]
        .groupby('canonical_developer_id')
        .size()
        .reset_index(name='home_project_months')
    )

    # Filter to 12+ months
    _qualified_ids = _home_months[_home_months['home_project_months'] >= 12]['canonical_developer_id']

    # Get qualified developers with their metadata
    df_qualified_developers = df_top_devs[
        df_top_devs['canonical_developer_id'].isin(_qualified_ids)
    ].merge(_home_months, on='canonical_developer_id')

    # Stats for reporting
    _total_devs = df_top_devs['canonical_developer_id'].nunique()
    _qualified_devs = len(df_qualified_developers)
    _pct_qualified = (_qualified_devs / _total_devs * 100) if _total_devs > 0 else 0
    return (df_qualified_developers,)


@app.cell(hide_code=True)
def transform_developer_lifecycle(df_alignment, df_qualified_developers):
    # US-008: Define onboarding and offboarding periods per (developer, project)
    # Onboarding = first month with home project activity
    # Offboarding = last activity 6+ months before end of timeseries

    _qualified_ids = df_qualified_developers['canonical_developer_id'].unique()

    # Filter alignment to qualified developers only
    _dev_activity = df_alignment[
        df_alignment['canonical_developer_id'].isin(_qualified_ids)
    ].copy().sort_values(['canonical_developer_id', 'month'])

    # Forward-fill home_project_name so inactive months inherit the last active project
    _dev_activity['home_project_name'] = _dev_activity.groupby('canonical_developer_id')['home_project_name'].ffill()

    # Calculate onboarding month per (developer, project) - first month with activity
    _onboard = (
        _dev_activity[_dev_activity['has_home_project_activity'] == True]
        .groupby(['canonical_developer_id', 'home_project_name'])
        .nth(0)  # 0-indexed, so 0 = 1st month
        .reset_index()[['canonical_developer_id', 'home_project_name', 'month']]
        .rename(columns={'month': 'onboard_month', 'home_project_name': 'project_display_name'})
    )

    # Calculate offboarding per (developer, project) - only look AFTER onboard date
    _dev_activity = _dev_activity.merge(
        _onboard,
        left_on=['canonical_developer_id', 'home_project_name'],
        right_on=['canonical_developer_id', 'project_display_name'],
        how='left'
    )
    _post_onboard = _dev_activity[_dev_activity['month'] >= _dev_activity['onboard_month']].copy()

    # Find each developer's last active month on home project
    _last_active = (
        _post_onboard[_post_onboard['has_home_project_activity'] == True]
        .groupby(['canonical_developer_id', 'home_project_name'])['month']
        .max()
        .reset_index()
        .rename(columns={'month': 'last_active_month', 'home_project_name': 'project_display_name'})
    )

    # Offboard if last activity was 6+ months before end of timeseries
    _latest_month = df_alignment['month'].max()
    _last_active['months_since_active'] = (
        (_latest_month - _last_active['last_active_month']).dt.days // 30
    )
    _offboard = _last_active[_last_active['months_since_active'] >= 6][
        ['canonical_developer_id', 'project_display_name', 'last_active_month']
    ].rename(columns={'last_active_month': 'offboard_month'})

    # Combine into lifecycle dataframe - join on (developer, project)
    df_developer_lifecycle = df_qualified_developers.merge(
        _onboard, on=['canonical_developer_id', 'project_display_name'], how='left'
    ).merge(
        _offboard, on=['canonical_developer_id', 'project_display_name'], how='left'
    )

    # Calculate tenure (vectorized)
    _latest_month = df_alignment['month'].max()
    _end_month = df_developer_lifecycle['offboard_month'].fillna(_latest_month)
    df_developer_lifecycle['tenure_months'] = (
        (_end_month - df_developer_lifecycle['onboard_month']).dt.days // 30
    )

    df_developer_lifecycle['is_still_active'] = df_developer_lifecycle['offboard_month'].isna()
    return (df_developer_lifecycle,)


@app.cell(hide_code=True)
def transform_onboarding_features(df_alignment, df_developer_lifecycle):
    # US-009: Engineer features for pre-onboarding period clustering
    # Look at what developers were doing BEFORE they onboarded to their DeFi project

    # Get onboard dates per (developer, project)
    _onboard_dates = df_developer_lifecycle[['canonical_developer_id', 'project_display_name', 'onboard_month']].dropna()

    # Merge onboard dates into alignment data - join only on developer ID
    # This keeps ALL activity for each developer, not just rows with matching home_project_name
    _activity = df_alignment.merge(
        _onboard_dates,
        on='canonical_developer_id',
        how='inner'
    )

    # Filter to pre-onboarding months only (all activity before first home project contribution)
    _pre_onboard = _activity[_activity['month'] < _activity['onboard_month']].copy()

    # Filter to only months with actual activity (total_repo_event_days > 0)
    # The alignment table has rows for all months, but many have zero activity
    _pre_active = _pre_onboard[_pre_onboard['total_repo_event_days'] > 0]

    # Aggregate pre-onboarding activity per (developer, project)
    _pre_features = _pre_active.groupby(['canonical_developer_id', 'project_display_name']).agg(
        pre_total_days=('total_repo_event_days', 'sum'),
        pre_crypto_days=('crypto_repo_event_days', 'sum'),
        pre_personal_days=('personal_repo_event_days', 'sum'),
        pre_oss_days=('oss_repo_event_days', 'sum'),
        pre_interest_days=('interest_repo_event_days', 'sum'),
        pre_months_active=('month', 'nunique'),  # Now only counts months with activity
        pre_crypto_events=('crypto_events', 'sum'),
        pre_personal_events=('personal_events', 'sum'),
        pre_oss_events=('oss_events', 'sum'),
    ).reset_index()

    # Calculate percentages (of total pre-onboarding activity)
    _pre_features['pre_crypto_pct'] = (
        _pre_features['pre_crypto_days'] / _pre_features['pre_total_days'].replace(0, 1) * 100
    )
    _pre_features['pre_personal_pct'] = (
        _pre_features['pre_personal_days'] / _pre_features['pre_total_days'].replace(0, 1) * 100
    )
    _pre_features['pre_oss_pct'] = (
        _pre_features['pre_oss_days'] / _pre_features['pre_total_days'].replace(0, 1) * 100
    )

    # Find primary pre-onboarding ecosystem (by months, then days as tiebreaker)
    _primary_eco = (
        _pre_active[_pre_active['crypto_primary_ecosystem'].notna()]
        .groupby(['canonical_developer_id', 'project_display_name', 'crypto_primary_ecosystem'])
        .agg(eco_months=('month', 'nunique'), eco_days=('crypto_repo_event_days', 'sum'))
        .reset_index()
        .sort_values(['eco_months', 'eco_days'], ascending=[False, False])
        .drop_duplicates(['canonical_developer_id', 'project_display_name'], keep='first')
        [['canonical_developer_id', 'project_display_name', 'crypto_primary_ecosystem']]
        .rename(columns={'crypto_primary_ecosystem': 'pre_primary_ecosystem'})
    )
    _pre_features = _pre_features.merge(_primary_eco, on=['canonical_developer_id', 'project_display_name'], how='left')

    # Merge back to lifecycle dataframe
    df_onboarding_features = df_developer_lifecycle.merge(
        _pre_features,
        on=['canonical_developer_id', 'project_display_name'],
        how='left'
    )

    # Fill NaN for developers with no pre-onboarding activity
    df_onboarding_features['pre_total_days'] = df_onboarding_features['pre_total_days'].fillna(0)
    df_onboarding_features['pre_months_active'] = df_onboarding_features['pre_months_active'].fillna(0)
    # Direct to DeFi: less than 6 months of activity before joining home project
    df_onboarding_features['is_direct_to_defi'] = df_onboarding_features['pre_months_active'] < 6
    return (df_onboarding_features,)


@app.cell(hide_code=True)
def transform_onboarding_clusters(df_onboarding_features):
    # Classify developers by onboarding background: Newcomer vs Experienced
    # Newcomer = < 6 months of pre-onboarding activity ("came in cold")
    # Experienced = 6+ months of pre-onboarding activity (crypto, OSS, or personal)

    _df = df_onboarding_features.copy()

    _df['onboarding_cluster_id'] = _df['is_direct_to_defi'].map({True: 0, False: 1})
    _df['onboarding_cluster'] = _df['is_direct_to_defi'].map({True: 'Newcomer', False: 'Experienced'})

    df_with_clusters = _df

    # Create cluster profile summary
    cluster_profiles = df_with_clusters.groupby('onboarding_cluster').agg(
        count=('canonical_developer_id', 'count'),
        avg_pre_months=('pre_months_active', 'mean'),
        avg_crypto_pct=('pre_crypto_pct', 'mean'),
        avg_personal_pct=('pre_personal_pct', 'mean'),
        avg_oss_pct=('pre_oss_pct', 'mean'),
        pct_still_active=('is_still_active', 'mean')
    ).round(1)

    cluster_debug = {}
    return (df_with_clusters,)


@app.cell(hide_code=True)
def section_feeder_header(mo):
    mo.md("""
    ---
    ## A relatively small number of projects played an outsized role in attracting and inspiring developers.
    """)
    return


@app.cell(hide_code=True)
def transform_feeder_projects(
    PROJECT_ECOSYSTEM,
    df_alignment,
    df_contribution_features,
    df_interest_projects,
    ecosystem_toggle,
    pd,
):
    # Feeder projects: 2x2 grid (home ecosystem × engagement) with crypto/OSS lists
    # Dedup: contributed wins over starred for the same (dev, project)
    # Category: from contribution track when available, interest track as fallback

    # --- NAME NORMALIZATION ---
    # Merge duplicate project names to canonical forms
    _NAME_MAP = {
        # Ecosystem categories → cleaner labels
        'ethereum w/o l2s': 'Ethereum Core',
        'ethereum dev tools': 'Ethereum Dev Tools',
        # Babylon variants
        'babylonchain': 'Babylon',
        'babylon chain': 'Babylon',
        'babylonchain-io': 'Babylon',
        # Uniswap variants
        'uniswap': 'Uniswap',
        # Aave variants
        'aave': 'Aave',
        # Cosmos variants
        'cosmos': 'Cosmos',
        'cosmos network': 'Cosmos',
        # Solana variants → unified
        'solana labs': 'Solana',
        'solana foundation': 'Solana',
        'solana developers': 'Solana',
        'solana': 'Solana',
        # Maker variants
        'maker': 'Sky (prev. MakerDAO)',
        # Compound variants
        'compound-developers': 'Compound',
        'compounddev': 'Compound',
        # Curve variants
        'curve-labs': 'Curve',
        'curveresearch': 'Curve',
        # Truffle variants
        'trufflesuite': 'Truffle',
        # Polkadot variants
        '@polkadot{.js}': 'Polkadot',
        'polkadot network': 'Polkadot',
        'polkadot-io': 'Polkadot',
        # Near variants
        'near-one': 'NEAR',
        'near': 'NEAR',
        # Facebook
        'facebook open source': 'Meta OSS',
        # Rust variants → unified
        'the rust programming language': 'Rust',
        'rust crypto': 'Rust',
        # Ethereum misc
        'ethereum miscellenia': 'Ethereum Core',
        'ethereum miscellaneous': 'Ethereum Core',
        'ethereum core': 'Ethereum Core',
        # Keep Network
        'keep-network': 'Keep Network',
        # Meta Research
        'meta research': 'Meta OSS',
        # sporkdao → cleaner name
        'sporkdaoofficial': 'SporkDAO',
    }

    # --- CLASSIFICATION OVERRIDES ---
    # Projects misclassified by the is_crypto heuristic
    _FORCE_CRYPTO = {
        'solana labs', 'solana', 'delvtech', 'polygon', 'trustwallet', 'cosmostation',
        'babylonchain', 'babylon chain', 'babylon', 'near', 'near-one',
        'avalanche', 'bnb chain', 'polkadot network', '@polkadot{.js}',
        'polkadot-io', 'cosmos', 'cosmos network', 'keep network', 'keep-network',
    }
    _FORCE_OSS = {
        'rust', 'the rust programming language', 'rust crypto', 'deno',
        'microsoft', 'google', 'vercel', 'openai', 'meta oss',
        'facebook open source', 'oven-sh',
    }

    # --- PROJECTS TO EXCLUDE ---
    # Not interpretable as feeders (org names, not projects)
    _EXCLUDE = {
        'ethereum-lists',  # just a list repo, not a project
    }

    def _normalize(name):
        """Normalize a project name: apply name map, then title-case."""
        key = name.strip().lower()
        if key in _EXCLUDE:
            return None
        return _NAME_MAP.get(key, name)

    def _classify(name_lower, original_type):
        """Override feeder_type classification."""
        if name_lower in _FORCE_CRYPTO:
            return 'Crypto'
        if name_lower in _FORCE_OSS:
            return 'OSS'
        return original_type

    _lifecycle = df_contribution_features[
        ['canonical_developer_id', 'project_display_name', 'onboard_month']
    ].drop_duplicates(subset='canonical_developer_id', keep='first')

    # Developer home ecosystem: Ethereum DeFi vs Other DeFi
    _lifecycle['home_ecosystem'] = _lifecycle['project_display_name'].map(
        lambda p: 'Ethereum DeFi' if PROJECT_ECOSYSTEM.get(p) == 'Ethereum' else 'Other DeFi'
    )

    # --- CONTRIBUTION FEEDERS ---
    _pre = df_alignment.merge(
        _lifecycle[['canonical_developer_id', 'onboard_month', 'home_ecosystem']],
        on='canonical_developer_id', how='inner',
    )
    _pre = _pre[_pre['month'] < _pre['onboard_month']]

    # Crypto contributions
    _crypto = _pre[
        _pre['crypto_primary_project'].notna() & (_pre['crypto_repo_event_days'] > 0)
    ][['canonical_developer_id', 'crypto_primary_project', 'crypto_repo_event_days', 'home_ecosystem']].copy()
    _crypto['feeder_type'] = 'Crypto'
    _crypto = _crypto.rename(columns={
        'canonical_developer_id': 'dev_id', 'crypto_primary_project': 'project',
        'crypto_repo_event_days': 'days',
    })[['dev_id', 'project', 'days', 'feeder_type', 'home_ecosystem']]

    # OSS contributions
    _oss = _pre[
        _pre['oss_primary_project'].notna() & (_pre['oss_repo_event_days'] > 0)
    ][['canonical_developer_id', 'oss_primary_project', 'oss_repo_event_days', 'home_ecosystem']].copy()
    _oss['feeder_type'] = 'OSS'
    _oss = _oss.rename(columns={
        'canonical_developer_id': 'dev_id', 'oss_primary_project': 'project',
        'oss_repo_event_days': 'days',
    })[['dev_id', 'project', 'days', 'feeder_type', 'home_ecosystem']]

    _contrib = pd.concat([_crypto, _oss], ignore_index=True)
    _contrib['engagement'] = 'Contributing'

    # Apply normalization and classification overrides
    _contrib['project'] = _contrib['project'].apply(_normalize)
    _contrib = _contrib[_contrib['project'].notna()]  # drop excluded
    _contrib['feeder_type'] = _contrib.apply(
        lambda r: _classify(r['project'].strip().lower(), r['feeder_type']), axis=1
    )
    _contrib['project_key'] = _contrib['project'].str.lower().str.strip()

    # --- INTEREST FEEDERS (Watch events, pre-onboard) ---
    _interest_pre = df_interest_projects.merge(
        _lifecycle[['canonical_developer_id', 'onboard_month', 'home_ecosystem']],
        on='canonical_developer_id', how='inner',
    )
    _interest_pre = _interest_pre[_interest_pre['month'] < _interest_pre['onboard_month']]

    _int = _interest_pre[['canonical_developer_id', 'interest_project', 'interest_days', 'is_crypto', 'home_ecosystem']].copy()
    _int['feeder_type'] = _int['is_crypto'].apply(lambda c: 'Crypto' if c else 'OSS')
    _int = _int.rename(columns={
        'canonical_developer_id': 'dev_id', 'interest_project': 'project', 'interest_days': 'days',
    })[['dev_id', 'project', 'days', 'feeder_type', 'home_ecosystem']]
    _int['engagement'] = 'Starred'

    # Apply normalization and classification overrides
    _int['project'] = _int['project'].apply(_normalize)
    _int = _int[_int['project'].notna()]  # drop excluded
    _int['feeder_type'] = _int.apply(
        lambda r: _classify(r['project'].strip().lower(), r['feeder_type']), axis=1
    )
    _int['project_key'] = _int['project'].str.lower().str.strip()

    # --- DEDUP: contributed wins over starred per (dev, project) ---
    _contrib_keys = set(zip(_contrib['dev_id'], _contrib['project_key']))
    _int_deduped = _int[~_int.apply(lambda r: (r['dev_id'], r['project_key']) in _contrib_keys, axis=1)]

    _all = pd.concat([_contrib, _int_deduped], ignore_index=True)

    # Display name: most common casing per project_key (post-normalization)
    _display = _all.groupby('project_key')['project'].agg(lambda x: x.mode().iloc[0])

    # Feeder type per project: from contribution records first, interest as fallback
    _contrib_type = _contrib.groupby('project_key')['feeder_type'].agg(lambda x: x.mode().iloc[0])
    _int_type = _int_deduped.groupby('project_key')['feeder_type'].agg(lambda x: x.mode().iloc[0])
    _proj_type = _contrib_type.combine_first(_int_type)

    # --- AGGREGATE per (home_ecosystem, engagement, feeder_type, project) ---
    _agg = _all.groupby(['home_ecosystem', 'engagement', 'project_key']).agg(
        devs=('dev_id', 'nunique'),
    ).reset_index()
    _agg['project_name'] = _agg['project_key'].map(_display)
    _agg['feeder_type'] = _agg['project_key'].map(_proj_type)

    # Build nested dict for grid
    # {(home_eco, engagement): {'Crypto': [(name, count), ...], 'OSS': [...]}}
    _grid = {}
    for (_eco, _eng), _grp in _agg.groupby(['home_ecosystem', 'engagement']):
        _cell = {}
        for _ft in ['Crypto', 'OSS']:
            _sub = _grp[_grp['feeder_type'] == _ft].sort_values('devs', ascending=False)
            _cell[_ft] = list(zip(_sub['project_name'], _sub['devs']))
        _grid[(_eco, _eng)] = _cell

    # Filter to active ecosystem only (1x2 layout)
    _active_label = 'Ethereum DeFi' if ecosystem_toggle.value == 'Ethereum' else 'Other DeFi'
    _grid = {k: v for k, v in _grid.items() if k[0] == _active_label}

    df_feeder_projects = _agg  # full data for reference

    # Stats
    _total_qualified = _lifecycle['canonical_developer_id'].nunique()
    _devs_with_contrib = _contrib['dev_id'].nunique()

    feeder_stats = {
        'total_qualified': _total_qualified,
        'devs_with_feeder': _devs_with_contrib,
        'pct_with_feeder': (_devs_with_contrib / _total_qualified * 100) if _total_qualified > 0 else 0,
        'grid': _grid,
    }
    return (feeder_stats,)


@app.cell(hide_code=True)
def insight_feeder_projects(
    ETHEREUM_COLOR,
    OTHER_CRYPTO_COLOR,
    ecosystem_toggle,
    feeder_stats,
    mo,
):
    # 1x2 grid: Contributing | Starred for active ecosystem only
    _grid = feeder_stats['grid']
    _N = 10  # top N per list

    _is_eth = ecosystem_toggle.value == 'Ethereum'
    _active_color = ETHEREUM_COLOR if _is_eth else OTHER_CRYPTO_COLOR
    _active_label = 'Ethereum DeFi' if _is_eth else 'Other DeFi'
    _header_bg = '#F3F1FD' if _is_eth else '#F0FAF9'
    _header_border = '#E8E4FA' if _is_eth else '#D5EDEC'

    def _render_list(items, color, n=_N):
        if not items:
            return '<div style="color:#6B7280;font-size:12px;padding:4px 0">\u2014</div>'
        _rows = []
        for _i, (_name, _count) in enumerate(items[:n]):
            _bold = 'font-weight:700;color:#1F2937' if _i < 3 else 'font-weight:400;color:#6B7280'
            _bg = '#FAFAFA' if _i % 2 == 1 else 'white'
            _rows.append(
                f'<div style="display:flex;justify-content:space-between;padding:3px 4px;'
                f'font-size:12px;border-bottom:1px solid #F3F4F6;background:{_bg}">'
                f'<span style="{_bold}">{_name}</span>'
                f'<span style="color:{color};font-weight:600;min-width:28px;text-align:right">{_count}</span>'
                f'</div>'
            )
        return ''.join(_rows)

    def _render_cell(eng):
        _cell = _grid.get((_active_label, eng), {'Crypto': [], 'OSS': []})
        _crypto_html = _render_list(_cell.get('Crypto', []), _active_color)
        _oss_html = _render_list(_cell.get('OSS', []), _active_color)
        return (
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">'
            f'<div>'
            f'<div style="font-size:11px;font-weight:600;color:{_active_color};'
            f'text-transform:uppercase;letter-spacing:0.5px;padding-bottom:4px;'
            f'border-bottom:2px solid {_active_color}">Crypto</div>'
            f'{_crypto_html}'
            f'</div>'
            f'<div>'
            f'<div style="font-size:11px;font-weight:600;color:{_active_color};'
            f'text-transform:uppercase;letter-spacing:0.5px;padding-bottom:4px;'
            f'border-bottom:2px solid {_active_color}">OSS</div>'
            f'{_oss_html}'
            f'</div>'
            f'</div>'
        )

    _html = f"""
    <div style="max-width:1000px;margin:0;font-family:system-ui,-apple-system,sans-serif">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:0;border:1px solid #E5E7EB;border-radius:8px;overflow:hidden">

        <!-- Header row -->
        <div style="background:{_header_bg};padding:10px 16px;border-bottom:1px solid {_header_border};border-right:1px solid #E5E7EB;text-align:center">
          <span style="font-size:13px;font-weight:700;color:#1F2937">Contributing</span>
          <span style="font-size:11px;color:#6B7280;display:block">Code contributions pre-onboard</span>
        </div>
        <div style="background:{_header_bg};padding:10px 16px;border-bottom:1px solid {_header_border};text-align:center">
          <span style="font-size:13px;font-weight:700;color:#1F2937">Starred</span>
          <span style="font-size:11px;color:#6B7280;display:block">GitHub stars pre-onboard</span>
        </div>

        <!-- Active ecosystem row -->
        <div style="border-right:1px solid #E5E7EB">
          <div style="background:{_header_bg};padding:8px 16px;border-bottom:1px solid {_header_border}">
            <span style="font-size:12px;font-weight:700;color:{_active_color}">{_active_label}</span>
            <span style="font-size:11px;color:#6B7280"> developers</span>
          </div>
          <div style="padding:8px 16px">{_render_cell('Contributing')}</div>
        </div>
        <div>
          <div style="background:{_header_bg};padding:8px 16px;border-bottom:1px solid {_header_border}">
            <span style="font-size:12px;font-weight:700;color:{_active_color}">{_active_label}</span>
            <span style="font-size:11px;color:#6B7280"> developers</span>
          </div>
          <div style="padding:8px 16px">{_render_cell('Starred')}</div>
        </div>

      </div>
    </div>
    """

    mo.vstack([
        mo.Html(_html),
        mo.md(
            f'Tooling projects (Foundry, Truffle, Hardhat) trained more future DeFi '
            f'contributors than educational programmes. '
            f'{feeder_stats["pct_with_feeder"]:.0f}% of qualified developers had prior '
            f'project engagement before joining DeFi.'
        ),
    ])
    return


@app.cell(hide_code=True)
def section_part3_header(ecosystem_toggle, mo):
    if ecosystem_toggle.value == 'Ethereum':
        _heading = 'Overall, Ethereum has been a net importer of DeFi talent from other ecosystems.'
    else:
        _heading = 'Overall, other chains have been a net exporter of DeFi talent to Ethereum.'
    mo.md(f"""
    ---
    ## {_heading}
    """)
    return


@app.cell(hide_code=True)
def transform_balance_of_trade(
    PROJECT_ECOSYSTEM,
    df_alignment,
    df_with_status,
    pd,
):
    # Yearly ecosystem snapshots → year-over-year Ethereum DeFi imports/exports
    _qualified_ids = df_with_status['canonical_developer_id'].unique()
    _align = df_alignment[df_alignment['canonical_developer_id'].isin(_qualified_ids)]
    # Only use fully complete calendar years (12 months) to avoid partial-year artifacts
    _month_counts = _align.groupby(_align['month'].dt.year)['month'].apply(lambda x: x.dt.month.nunique())
    _complete_years = sorted(_month_counts[_month_counts >= 12].index)
    # Focus on 2019+ (so flow chart starts at 2020)
    _years = [y for y in _complete_years if y >= 2019]

    def _classify_year(year_data):
        """Classify each developer's primary ecosystem for a given year's data."""
        _dev = year_data.groupby('canonical_developer_id').agg(
            home_days=('home_project_repo_event_days', 'sum'),
            crypto_days=('crypto_repo_event_days', 'sum'),
            oss_days=('oss_repo_event_days', 'sum'),
            personal_days=('personal_repo_event_days', 'sum'),
        ).reset_index()
        # Primary home project
        _home = (
            year_data[year_data['home_project_repo_event_days'] > 0]
            .groupby(['canonical_developer_id', 'home_project_name'])
            .agg(_m=('month', 'nunique'), _d=('home_project_repo_event_days', 'sum'))
            .reset_index().sort_values(['_m', '_d'], ascending=False)
            .drop_duplicates('canonical_developer_id', keep='first')
        )
        _dev = _dev.merge(_home[['canonical_developer_id', 'home_project_name']], on='canonical_developer_id', how='left')
        _dev['_heco'] = _dev['home_project_name'].map(PROJECT_ECOSYSTEM)
        # Primary crypto ecosystem
        _crypto = (
            year_data[year_data['crypto_repo_event_days'] > 0]
            .groupby(['canonical_developer_id', 'crypto_primary_ecosystem'])
            .agg(_m=('month', 'nunique'), _d=('crypto_repo_event_days', 'sum'))
            .reset_index().sort_values(['_m', '_d'], ascending=False)
            .drop_duplicates('canonical_developer_id', keep='first')
        )
        _dev = _dev.merge(_crypto[['canonical_developer_id', 'crypto_primary_ecosystem']], on='canonical_developer_id', how='left')

        def _classify(row):
            if row['home_days'] > 0 and pd.notna(row.get('_heco')):
                return 'Ethereum' if row['_heco'] == 'Ethereum' else 'Other Crypto'
            if row['crypto_days'] > 0:
                eco = row.get('crypto_primary_ecosystem')
                if pd.notna(eco) and eco == 'Ethereum':
                    return 'Ethereum'
                if pd.notna(eco):
                    return 'Other Crypto'
            if row['oss_days'] > 0 or row['personal_days'] > 0:
                return 'Non-Crypto OSS'
            return 'Inactive'

        _dev['eco'] = _dev.apply(_classify, axis=1)
        # Include all qualified devs (no activity in this year = Inactive)
        _all = pd.DataFrame({'canonical_developer_id': _qualified_ids})
        _dev = _all.merge(_dev[['canonical_developer_id', 'eco']], on='canonical_developer_id', how='left')
        _dev['eco'] = _dev['eco'].fillna('Inactive')
        return _dev.set_index('canonical_developer_id')['eco']

    # Build yearly ecosystem classifications
    _yearly_eco = {_y: _classify_year(_align[_align['month'].dt.year == _y]) for _y in _years}

    # Year-over-year flows for each focal ecosystem
    _FOCALS = ['Ethereum', 'Other Crypto']
    _records = []
    for _focal in _FOCALS:
        for _i in range(len(_years) - 1):
            _y1, _y2 = _years[_i], _years[_i + 1]
            _comp = pd.DataFrame({'before': _yearly_eco[_y1], 'after': _yearly_eco[_y2]})
            _imp = _comp[(_comp['before'] != _focal) & (_comp['after'] == _focal)]
            for _src, _cnt in _imp.groupby('before').size().items():
                _records.append({'focal': _focal, 'year': _y2, 'direction': 'import', 'partner': _src, 'count': int(_cnt)})
            _exp = _comp[(_comp['before'] == _focal) & (_comp['after'] != _focal)]
            for _dst, _cnt in _exp.groupby('after').size().items():
                _records.append({'focal': _focal, 'year': _y2, 'direction': 'export', 'partner': _dst, 'count': int(_cnt)})

    df_balance_flows = pd.DataFrame(_records)

    balance_stats = {}
    for _focal in _FOCALS:
        _before = int((_yearly_eco[_years[0]] == _focal).sum())
        _after = int((_yearly_eco[_years[-1]] == _focal).sum())
        balance_stats[_focal] = {
            'total_devs': len(_qualified_ids),
            'count_before': _before,
            'count_after': _after,
            'net': _after - _before,
            'first_year': _years[0],
            'last_year': _years[-1],
        }
    return balance_stats, df_balance_flows


@app.cell(hide_code=True)
def insight_balance_of_trade(
    ETHEREUM_COLOR,
    INACTIVE_COLOR,
    NET_LINE_COLOR,
    OTHER_CRYPTO_COLOR,
    PLOTLY_LAYOUT,
    balance_stats,
    df_balance_flows,
    df_non_eth_origins,
    ecosystem_toggle,
    go,
    mo,
    non_eth_stats,
):
    # Ethereum <-> Other flow at top, then net summary + partner chart
    _focal = ecosystem_toggle.value
    if _focal == 'Other':
        _focal = 'Other Crypto'
    _ALL_COLORS = {
        'Ethereum': ETHEREUM_COLOR,
        'Other Crypto': OTHER_CRYPTO_COLOR,
        'Non-Crypto OSS': INACTIVE_COLOR,
        'Inactive': INACTIVE_COLOR,
    }
    _PARTNERS = [k for k in _ALL_COLORS if k != _focal]
    _focal_label = 'Ethereum DeFi' if _focal == 'Ethereum' else 'Other Crypto'
    _other_label = 'Other Crypto' if _focal == 'Ethereum' else 'Ethereum DeFi'

    # Ethereum <-> Other simple chart (at top): unique devs who moved between chains
    if _focal == 'Ethereum':
        _cross_imp, _cross_exp = non_eth_stats['import_count'], non_eth_stats['export_count']
    else:
        _cross_imp, _cross_exp = non_eth_stats['export_count'], non_eth_stats['import_count']
    _cross_net = _cross_imp - _cross_exp
    _cross_sign = '+' if _cross_net >= 0 else ''
    _focal_color = ETHEREUM_COLOR if _focal == 'Ethereum' else OTHER_CRYPTO_COLOR
    _fig_cross = go.Figure()
    _fig_cross.add_trace(go.Bar(x=[_cross_imp], y=[''], orientation='h', marker_color=_focal_color, text=[f'  +{_cross_imp} to {_focal_label}'], textposition='outside', textfont=dict(size=13, color=_focal_color), showlegend=False, base=0))
    _fig_cross.add_trace(go.Bar(x=[-_cross_exp], y=[''], orientation='h', marker_color=f'rgba(176,183,195,0.7)', text=[f'{_cross_exp} to {_other_label}  '], textposition='outside', textfont=dict(size=13, color=INACTIVE_COLOR), showlegend=False, base=0))
    _max_bar = max(_cross_imp, _cross_exp)
    _fig_cross.add_annotation(x=0, y=0, yshift=36, text=f"<b>Net: {_cross_sign}{_cross_net} to {_focal_label}</b>", showarrow=False, font=dict(size=14, color=NET_LINE_COLOR))
    _fig_cross.update_layout(**{**PLOTLY_LAYOUT, "barmode": "overlay", "height": 100, "margin": dict(l=20, r=20, t=40, b=20), "showlegend": False, "xaxis": dict(zeroline=True, zerolinecolor=NET_LINE_COLOR, zerolinewidth=2, showgrid=False, showticklabels=False, range=[-_max_bar * 1.3, _max_bar * 1.3]), "yaxis": dict(showticklabels=False, showline=False, ticks='')})
    if _focal == 'Ethereum':
        _top_origins = df_non_eth_origins.head(5)
        _origins_list = ', '.join([f"{r['pre_primary_ecosystem']} ({r['developer_count']})" for _, r in _top_origins.iterrows()])
        _cross_caption = mo.md(
            f'**Ethereum ↔ Other Crypto** — *unique developers* who moved between chains (different method from totals below). '
            f'{_cross_imp} from other crypto → {_focal_label}; {_cross_exp} from {_focal_label} → others. Top origins: {_origins_list}.'
        )
    else:
        _cross_caption = mo.md(
            f'**Ethereum ↔ Other Crypto** — *unique developers* who moved between chains. '
            f'{_cross_imp} from {_other_label} → {_focal_label}; {_cross_exp} from {_focal_label} → {_other_label}.'
        )

    _df = df_balance_flows[df_balance_flows['focal'] == _focal]
    _years = sorted(_df['year'].unique())
    _year_pos = list(range(len(_years)))

    _net_vals = []
    for _y in _years:
        _imp = int(_df[(_df['year'] == _y) & (_df['direction'] == 'import')]['count'].sum())
        _exp = int(_df[(_df['year'] == _y) & (_df['direction'] == 'export')]['count'].sum())
        _net_vals.append(_imp - _exp)

    # Net by partner (imports - exports over all years)
    _net_by_partner = {}
    for _p in _PARTNERS:
        _imp_sum = int(_df[(_df['direction'] == 'import') & (_df['partner'] == _p)]['count'].sum())
        _exp_sum = int(_df[(_df['direction'] == 'export') & (_df['partner'] == _p)]['count'].sum())
        _net_by_partner[_p] = _imp_sum - _exp_sum

    # Takeaway (for Ethereum DeFi)
    _takeaway = (
        "**Takeaway.** Ethereum DeFi's challenge is not losing developers to other crypto ecosystems, "
        "but failing to replace departures with sufficient newcomers—especially developers new to crypto "
        "or coming from non-crypto backgrounds."
    )
    if _focal != 'Ethereum':
        _takeaway = (
            f"*For {_focal_label}, net balance reflects year-over-year changes in developer count. "
            "The thesis above applies to Ethereum DeFi.*"
        )

    # Partner breakdown: stacked bars colored by focal ecosystem + thick net line
    # Import bars: focal color at descending opacity per partner
    # Export bars: INACTIVE_COLOR at descending opacity per partner
    _focal_hex = _focal_color.lstrip('#')
    _fr, _fg, _fb = int(_focal_hex[0:2], 16), int(_focal_hex[2:4], 16), int(_focal_hex[4:6], 16)
    _inactive_hex = INACTIVE_COLOR.lstrip('#')
    _ir, _ig, _ib = int(_inactive_hex[0:2], 16), int(_inactive_hex[2:4], 16), int(_inactive_hex[4:6], 16)
    _partner_opacities = [1.0, 0.55, 0.35]  # one per partner

    _fig_detail = go.Figure()
    for _pi, _p in enumerate(_PARTNERS):
        _vals = []
        for _y in _years:
            _m = _df[
                (_df['year'] == _y) & (_df['direction'] == 'import')
                & (_df['partner'] == _p)
            ]
            _vals.append(int(_m['count'].sum()) if len(_m) > 0 else 0)
        _op = _partner_opacities[min(_pi, len(_partner_opacities) - 1)]
        _fig_detail.add_trace(go.Bar(
            x=_year_pos, y=_vals, name=_p,
            marker_color=f'rgba({_fr},{_fg},{_fb},{_op})',
        ))
    for _pi, _p in enumerate(_PARTNERS):
        _vals = []
        for _y in _years:
            _m = _df[
                (_df['year'] == _y) & (_df['direction'] == 'export')
                & (_df['partner'] == _p)
            ]
            _vals.append(-int(_m['count'].sum()) if len(_m) > 0 else 0)
        _op = _partner_opacities[min(_pi, len(_partner_opacities) - 1)]
        _fig_detail.add_trace(go.Bar(
            x=_year_pos, y=_vals, name=_p,
            marker_color=f'rgba({_ir},{_ig},{_ib},{_op})',
            showlegend=False,
        ))
    # Thick net line with net-only labels
    _fig_detail.add_trace(go.Scatter(
        x=_year_pos, y=_net_vals, mode='lines+markers+text',
        line=dict(color=NET_LINE_COLOR, width=4),
        marker=dict(size=8, color=NET_LINE_COLOR),
        text=[f'{"+" if v >= 0 else ""}{v}' for v in _net_vals],
        textposition=['top center' if v >= 0 else 'bottom center' for v in _net_vals],
        textfont=dict(size=13, color=NET_LINE_COLOR),
        showlegend=False,
    ))
    _fig_detail.update_layout(**{
        **PLOTLY_LAYOUT,
        "barmode": "relative",
        "title": dict(text="Annual developer inflows/outflows by source/destination", font=dict(size=14)),
        "height": 420,
        "margin": dict(l=50, r=20, t=80, b=40),
        "legend": dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, font=dict(size=12)),
        "xaxis": dict(
            showgrid=False,
            linecolor='#1F2937', linewidth=1, ticks='outside',
            tickvals=_year_pos, ticktext=[str(y) for y in _years],
        ),
        "yaxis": dict(
            showgrid=True, gridcolor='#E5E7EB',
            linecolor='#1F2937', linewidth=1, ticks='outside',
            zeroline=True, zerolinecolor='#1F2937', zerolinewidth=1.5,
        ),
    })

    _stats = balance_stats[_focal]
    _total_net = _stats['net']
    _total_sign = '+' if _total_net >= 0 else ''
    _stat_blocks = [
        mo.stat(
            value=f'{_total_sign}{_total_net}',
            label='Total net',
            bordered=True,
            caption=f'{_stats["count_before"]} → {_stats["count_after"]} developers ({_stats["first_year"]}–{_stats["last_year"]})',
        ),
        *[
            mo.stat(
                value=f'{"+" if _net_by_partner[_p] >= 0 else ""}{_net_by_partner[_p]}',
                label=f'net from {_p}',
                bordered=True,
                caption='of total',
            )
            for _p in _PARTNERS
        ],
    ]
    # Explicit formula: total = sum of partner nets (year-over-year flows)
    _breakdown_str = ' + '.join([str(_net_by_partner[_p]) for _p in _PARTNERS])
    _how_numbers_add = mo.md(
        f'**Year-over-year flows:** {_total_sign}{_total_net} = {_breakdown_str}. '
        'These sum to the total; the Ethereum ↔ Other chart above uses unique developers (different method) and does not add in.'
    )
    mo.vstack([
        mo.ui.plotly(_fig_cross, config={'displayModeBar': False}),
        _cross_caption,
        mo.md("---"),
        mo.hstack(_stat_blocks, widths='equal', gap=1),
        _how_numbers_add,
        mo.md(_takeaway),
        mo.md("---"),
        mo.ui.plotly(_fig_detail, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def transform_non_eth_origins(PROJECT_ECOSYSTEM, df_contribution_features):
    # Bidirectional talent flow: Ethereum ↔ Other ecosystems
    _df = df_contribution_features.copy()
    _df['home_ecosystem'] = _df['project_display_name'].map(PROJECT_ECOSYSTEM).fillna('Other')

    # Export: Ethereum-trained devs now working on non-Ethereum projects
    _non_eth_devs = _df[_df['home_ecosystem'] != 'Ethereum']
    _eth_exports = _non_eth_devs[_non_eth_devs['pre_primary_ecosystem'].fillna('') == 'Ethereum']
    _export_count = _eth_exports['canonical_developer_id'].nunique()

    # Import: Non-Ethereum-trained devs now working on Ethereum projects
    _eth_devs = _df[_df['home_ecosystem'] == 'Ethereum']
    _non_eth_imports = _eth_devs[
        (_eth_devs['pre_primary_ecosystem'].notna()) &
        (_eth_devs['pre_primary_ecosystem'] != 'Ethereum')
    ]
    _import_count = _non_eth_imports['canonical_developer_id'].nunique()

    # Import breakdown by origin ecosystem
    df_non_eth_origins = (
        _non_eth_imports
        .groupby('pre_primary_ecosystem')
        .agg(developer_count=('canonical_developer_id', 'nunique'))
        .reset_index()
        .sort_values('developer_count', ascending=False)
    )

    # Temporal pattern: imports by year
    _non_eth_imports_by_year = (
        _non_eth_imports.copy()
        .assign(onboard_year=lambda x: x['onboard_month'].dt.year)
        .groupby('onboard_year')
        .agg(imports=('canonical_developer_id', 'nunique'))
        .reset_index()
    )

    non_eth_stats = {
        'export_count': _export_count,
        'import_count': _import_count,
        'net_flow': _import_count - _export_count,
        'total_non_eth_devs': _non_eth_devs['canonical_developer_id'].nunique(),
        'total_eth_devs': _eth_devs['canonical_developer_id'].nunique(),
        'imports_by_year': _non_eth_imports_by_year,
    }
    return df_non_eth_origins, non_eth_stats


@app.cell(hide_code=True)
def insight_non_eth_origins(ecosystem_toggle, non_eth_stats):
    """Compute headline_3 for section guide. Ethereum <-> Other chart is in insight_balance_of_trade."""
    _focal = ecosystem_toggle.value
    if _focal == 'Other':
        _focal = 'Other Crypto'
    _focal_label = 'Ethereum DeFi' if _focal == 'Ethereum' else 'Other Crypto'
    if _focal == 'Ethereum':
        _import, _export = non_eth_stats['import_count'], non_eth_stats['export_count']
    else:
        _import, _export = non_eth_stats['export_count'], non_eth_stats['import_count']
    _net = _import - _export
    _net_sign = '+' if _net >= 0 else ''
    _net_word = 'importer' if _net >= 0 else 'exporter'
    headline_3 = f"{_focal_label} is a net {_net_word} of developer talent: {_net_sign}{_net} developers"
    return (headline_3,)


@app.cell(hide_code=True)
def transform_background_origins(PROJECT_ECOSYSTEM, df_with_clusters, pd):
    def _origin_bucket(row):
        if pd.notna(row.get('pre_primary_ecosystem')):
            return 'Ethereum' if row['pre_primary_ecosystem'] == 'Ethereum' else 'Other crypto'
        if row.get('is_direct_to_defi'):
            return 'Inactive / new'
        return 'Non-crypto OSS'

    _df = df_with_clusters.copy()
    _df['home_ecosystem'] = _df['project_display_name'].map(PROJECT_ECOSYSTEM).fillna('Other')
    _df['onboard_year'] = _df['onboard_month'].dt.year
    _df['origin_bucket'] = _df.apply(_origin_bucket, axis=1)
    df_origins = (
        _df.groupby(['home_ecosystem', 'onboard_year', 'origin_bucket'])
        .size()
        .reset_index(name='count')
    )
    df_origins = (
        _df.groupby(['home_ecosystem', 'onboard_year', 'origin_bucket'])
        .size()
        .reset_index(name='count')
    )
    df_origins['onboard_year'] = df_origins['onboard_year'].astype(int)
    return (df_origins,)



@app.cell(hide_code=True)
def transform_contribution_features(df_alignment, df_with_clusters):
    # US-012: Engineer features for contribution clustering
    # Look at how developers contributed DURING their time on the home project

    # Get lifecycle info per (developer, project)
    _lifecycle = df_with_clusters[['canonical_developer_id', 'project_display_name', 'onboard_month', 'offboard_month', 'tenure_months']].copy()

    # Merge with alignment data
    _activity = df_alignment.merge(
        _lifecycle,
        left_on=['canonical_developer_id', 'home_project_name'],
        right_on=['canonical_developer_id', 'project_display_name'],
        how='inner'
    )

    # Filter to post-onboarding activity only
    _post_onboard = _activity[_activity['month'] >= _activity['onboard_month']].copy()

    # For offboarded devs, also filter to before offboard
    _post_onboard = _post_onboard[
        (_post_onboard['offboard_month'].isna()) |
        (_post_onboard['month'] <= _post_onboard['offboard_month'])
    ]

    # Filter to months with home project activity
    _home_active = _post_onboard[_post_onboard['has_home_project_activity'] == True]

    # Aggregate contribution features per (developer, project)
    _contrib_features = _home_active.groupby(['canonical_developer_id', 'project_display_name']).agg(
        contrib_months=('month', 'nunique'),
        contrib_total_days=('home_project_repo_event_days', 'sum'),
        contrib_total_events=('home_project_events', 'sum'),
    ).reset_index()

    # Calculate derived features
    _contrib_features['avg_days_per_month'] = (
        _contrib_features['contrib_total_days'] / _contrib_features['contrib_months'].replace(0, 1)
    )

    # Merge tenure from lifecycle
    _contrib_features = _contrib_features.merge(
        _lifecycle[['canonical_developer_id', 'project_display_name', 'tenure_months']],
        on=['canonical_developer_id', 'project_display_name'],
        how='left'
    )

    # Consistency: what % of tenure months had activity
    _contrib_features['consistency'] = (
        _contrib_features['contrib_months'] / _contrib_features['tenure_months'].replace(0, 1) * 100
    )

    # Merge back to df_with_clusters
    df_contribution_features = df_with_clusters.merge(
        _contrib_features[['canonical_developer_id', 'project_display_name', 'contrib_months',
                          'contrib_total_days', 'avg_days_per_month', 'consistency']],
        on=['canonical_developer_id', 'project_display_name'],
        how='left'
    )

    # Fill NaN (shouldn't happen, but safety)
    df_contribution_features['contrib_months'] = df_contribution_features['contrib_months'].fillna(0)
    df_contribution_features['contrib_total_days'] = df_contribution_features['contrib_total_days'].fillna(0)
    df_contribution_features['avg_days_per_month'] = df_contribution_features['avg_days_per_month'].fillna(0)
    df_contribution_features['consistency'] = df_contribution_features['consistency'].fillna(0)

    # Classify contribution intensity
    def _classify_intensity(avg_days):
        if avg_days > 10:
            return 'Frequent Contributor'
        elif avg_days >= 5:
            return 'Regular Contributor'
        return 'Occasional Contributor'

    df_contribution_features['contribution_cluster'] = df_contribution_features['avg_days_per_month'].apply(_classify_intensity)
    return (df_contribution_features,)



@app.cell(hide_code=True)
def transform_current_status(df_alignment, df_contribution_features, pd):
    # US-020: Classify current developer status
    # "Current" = activity in the last 6 months of the timeseries

    _latest_month = df_alignment['month'].max()
    _cutoff_month = _latest_month - pd.DateOffset(months=6)

    # Get recent activity (last 6 months) for each developer
    _recent = df_alignment[df_alignment['month'] >= _cutoff_month].copy()

    # Aggregate recent activity by developer
    _recent_summary = _recent.groupby('canonical_developer_id').agg(
        recent_home_days=('home_project_repo_event_days', 'sum'),
        recent_crypto_days=('crypto_repo_event_days', 'sum'),
        recent_personal_days=('personal_repo_event_days', 'sum'),
        recent_oss_days=('oss_repo_event_days', 'sum'),
        recent_total_days=('total_repo_event_days', 'sum'),
    ).reset_index()

    # Classify current status
    def _classify_status(row):
        if row['recent_home_days'] > 0:
            return 'Still Active on Home Project'
        elif row['recent_crypto_days'] > 0:
            return 'Active Elsewhere in Crypto'
        elif row['recent_personal_days'] > 0 or row['recent_oss_days'] > 0:
            return 'Active in Non-Crypto'
        else:
            return 'Inactive'

    _recent_summary['current_status'] = _recent_summary.apply(_classify_status, axis=1)

    # Merge with contribution features
    df_with_status = df_contribution_features.merge(
        _recent_summary[['canonical_developer_id', 'current_status',
                        'recent_home_days', 'recent_crypto_days',
                        'recent_personal_days', 'recent_oss_days']],
        on='canonical_developer_id',
        how='left'
    )

    # Fill NaN (developers with no recent activity at all)
    df_with_status['current_status'] = df_with_status['current_status'].fillna('Inactive')

    # Calculate stats
    _total = len(df_with_status)
    _status_counts = df_with_status['current_status'].value_counts()

    current_status_stats = {
        'total_developers': _total,
        'still_active': _status_counts.get('Still Active on Home Project', 0),
        'active_crypto': _status_counts.get('Active Elsewhere in Crypto', 0),
        'active_non_crypto': _status_counts.get('Active in Non-Crypto', 0),
        'inactive': _status_counts.get('Inactive', 0),
        'cutoff_month': _cutoff_month.strftime('%Y-%m'),
        'latest_month': _latest_month.strftime('%Y-%m')
    }
    current_status_stats['pct_still_active'] = (
        current_status_stats['still_active'] / _total * 100 if _total > 0 else 0
    )
    current_status_stats['pct_left_crypto'] = (
        (current_status_stats['active_non_crypto'] + current_status_stats['inactive'])
        / _total * 100 if _total > 0 else 0
    )
    return current_status_stats, df_with_status


@app.cell(hide_code=True)
def compute_headline_4(current_status_stats):
    _pct_left = current_status_stats['pct_left_crypto']
    headline_4 = f"Developers don't defect to competitors — {_pct_left:.0f}% went inactive or left crypto entirely"
    return (headline_4,)


@app.cell(hide_code=True)
def transform_temporal_status(PROJECT_ECOSYSTEM, df_alignment, df_developer_lifecycle, ecosystem_toggle, pd):
    # Filter lifecycle to active ecosystem
    _eco_map = df_developer_lifecycle['project_display_name'].map(PROJECT_ECOSYSTEM).fillna('Other')
    if ecosystem_toggle.value == 'Ethereum':
        _lifecycle = df_developer_lifecycle[_eco_map == 'Ethereum']
    else:
        _lifecycle = df_developer_lifecycle[_eco_map != 'Ethereum']

    # Quarterly developer pool status for streamgraph
    _qualified_ids = _lifecycle['canonical_developer_id'].unique()
    _alignment = df_alignment[df_alignment['canonical_developer_id'].isin(_qualified_ids)].copy()
    _alignment['quarter'] = _alignment['month'].dt.to_period('Q')

    _quarterly = _alignment.groupby(['canonical_developer_id', 'quarter']).agg(
        home_days=('home_project_repo_event_days', 'sum'),
        crypto_days=('crypto_repo_event_days', 'sum'),
        personal_days=('personal_repo_event_days', 'sum'),
        oss_days=('oss_repo_event_days', 'sum'),
    ).reset_index()

    def _classify(row):
        if row['home_days'] > 0:
            return 'Active on Home Project'
        elif row['crypto_days'] > 0:
            return 'Active Elsewhere in Crypto'
        elif row['personal_days'] > 0 or row['oss_days'] > 0:
            return 'Active in Non-Crypto'
        return 'Inactive'

    _quarterly['status'] = _quarterly.apply(_classify, axis=1)

    # Earliest onboard quarter per developer
    _dev_onboard = (
        _lifecycle[['canonical_developer_id', 'onboard_month']]
        .groupby('canonical_developer_id')['onboard_month']
        .min()
        .reset_index()
    )
    _dev_onboard['onboard_quarter'] = _dev_onboard['onboard_month'].dt.to_period('Q')
    _dev_onboard['onboard_year'] = _dev_onboard['onboard_month'].dt.year

    # Full grid: every dev × every quarter from their onboard quarter onward
    _all_quarters = pd.DataFrame({'quarter': sorted(_quarterly['quarter'].unique())})
    _full_grid = _dev_onboard[['canonical_developer_id', 'onboard_quarter', 'onboard_year']].merge(
        _all_quarters, how='cross'
    )
    _full_grid = _full_grid[_full_grid['quarter'] >= _full_grid['onboard_quarter']]

    _full_grid = _full_grid.merge(
        _quarterly[['canonical_developer_id', 'quarter', 'status']],
        on=['canonical_developer_id', 'quarter'],
        how='left',
    )
    _full_grid['status'] = _full_grid['status'].fillna('Inactive')

    df_streamgraph = (
        _full_grid.groupby(['quarter', 'status'])
        .size()
        .reset_index(name='developer_count')
    )
    df_streamgraph['quarter_str'] = df_streamgraph['quarter'].astype(str)

    # Cohort retention curves: % still active by quarters since onboard
    def _p2i(s):
        return s.apply(lambda p: p.year * 4 + p.quarter - 1)

    _full_grid['quarters_since'] = _p2i(_full_grid['quarter']) - _p2i(_full_grid['onboard_quarter'])
    _full_grid['is_home_active'] = _full_grid['status'] == 'Active on Home Project'

    _agg = _full_grid.groupby(['onboard_year', 'quarters_since']).agg(
        active=('is_home_active', 'sum'),
        observable=('canonical_developer_id', 'count'),
    ).reset_index()

    _cohort_sizes = (
        _agg[_agg['quarters_since'] == 0][['onboard_year', 'observable']]
        .rename(columns={'observable': 'cohort_size'})
    )
    _agg = _agg.merge(_cohort_sizes, on='onboard_year')
    _agg['pct_active'] = _agg['active'] / _agg['cohort_size'] * 100
    _agg['observability'] = _agg['observable'] / _agg['cohort_size']
    df_cohort_retention = _agg[
        (_agg['observability'] >= 0.8) & (_agg['onboard_year'].between(2020, 2024))
    ].copy()
    return df_cohort_retention, df_streamgraph



@app.cell(hide_code=True)
def section_cohort_header(ecosystem_toggle, mo):
    if ecosystem_toggle.value == 'Ethereum':
        _heading = 'Retention of full-time developers in Ethereum has been steady across market cycles.'
    else:
        _heading = 'Retention of full-time developers in other chains has gotten better in recent years.'
    mo.md(f"""
    ---
    ## {_heading}
    """)
    return


@app.cell(hide_code=True)
def insight_cohort_retention(
    ETHEREUM_COLOR,
    INACTIVE_COLOR,
    OTHER_CRYPTO_COLOR,
    PLOTLY_LAYOUT,
    df_cohort_retention,
    ecosystem_toggle,
    go,
    mo,
):
    # Survival curves by cohort — single-hue opacity gradient from active toggle
    _years = sorted(df_cohort_retention['onboard_year'].unique())
    _base = ETHEREUM_COLOR if ecosystem_toggle.value == 'Ethereum' else OTHER_CRYPTO_COLOR
    _bh = _base.lstrip('#')
    _br, _bg, _bb = int(_bh[0:2], 16), int(_bh[2:4], 16), int(_bh[4:6], 16)
    _cohort_colors = {}
    for _i, _yr in enumerate(_years):
        _opacity = 0.3 + 0.7 * (_i / max(len(_years) - 1, 1))
        _cohort_colors[_yr] = f'rgba({_br},{_bg},{_bb},{_opacity})'

    _fig = go.Figure()
    for year in _years:
        _data = df_cohort_retention[df_cohort_retention['onboard_year'] == year].sort_values('quarters_since')
        _n = int(_data['cohort_size'].iloc[0])
        _fig.add_trace(go.Scatter(
            x=_data['quarters_since'] / 4,  # quarters → years
            y=_data['pct_active'],
            mode='lines',
            name=f'{int(year)} (n={_n})',
            line=dict(color=_cohort_colors.get(year, INACTIVE_COLOR), width=3),
            showlegend=False,
        ))
        # Direct label at right end of each line
        _last = _data.iloc[-1]
        _fig.add_annotation(
            x=_last['quarters_since'] / 4, y=_last['pct_active'],
            text=f' {int(year)}', showarrow=False, xanchor='left',
            font=dict(size=11, color=_cohort_colors.get(year, INACTIVE_COLOR)),
        )

    # Vertical marker at 2-year point with annotation
    _two_year = df_cohort_retention[df_cohort_retention['quarters_since'] == 8]
    _avg_2yr = _two_year['pct_active'].mean() if len(_two_year) > 0 else 0
    _fig.add_vline(x=2, line_dash='dot', line_color='#E5E7EB', line_width=1)
    _fig.add_annotation(
        x=2, y=105, text=f'~{_avg_2yr:.0f}% at 2 years',
        showarrow=False, font=dict(size=11, color='#6B7280'),
    )

    _fig.update_layout(
        **{
            **PLOTLY_LAYOUT,
            "height": 400,
            "margin": dict(l=60, r=60, t=20, b=50),
            "showlegend": False,
            "xaxis": dict(
                title='Years since onboarding', showgrid=False, dtick=1,
                linecolor='#1F2937', linewidth=1, ticks='outside',
            ),
            "yaxis": dict(
                title='% Still Active on Home Project', range=[0, 112],
                showgrid=False,
                linecolor='#1F2937', linewidth=1, ticks='outside',
            ),
        },
    )

    mo.vstack([
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
        mo.md(
            f'Average 2-year retention across cohorts is **{_avg_2yr:.0f}%**. '
            f'Note: "qualified" developers must have 12+ months of activity on their home project, '
            f'so these curves track developers who already cleared an initial commitment threshold.'
        ),
    ])
    return


@app.cell(hide_code=True)
def transform_pipeline_composition(PROJECT_ECOSYSTEM, df_contribution_features, ecosystem_toggle, pd):
    # Onboarding pipeline composition by year — filtered by ecosystem toggle
    _df = df_contribution_features.copy()
    _df['home_ecosystem'] = _df['project_display_name'].map(PROJECT_ECOSYSTEM).fillna('Other')
    if ecosystem_toggle.value == 'Ethereum':
        _df = _df[_df['home_ecosystem'] == 'Ethereum']
    else:
        _df = _df[_df['home_ecosystem'] != 'Ethereum']
    _df['onboard_year'] = _df['onboard_month'].dt.year

    _df['pipeline_category'] = 'Non-crypto experienced'
    _df.loc[_df['is_direct_to_defi'], 'pipeline_category'] = 'Newcomer'
    _df.loc[
        ~_df['is_direct_to_defi'] & _df['pre_primary_ecosystem'].notna(),
        'pipeline_category'
    ] = 'Crypto-experienced'

    df_pipeline = (
        _df.groupby(['onboard_year', 'pipeline_category'])
        .size()
        .reset_index(name='count')
    )
    df_pipeline = df_pipeline[df_pipeline['onboard_year'].between(2020, 2024)]

    pipeline_newcomer_counts = (
        _df[_df['pipeline_category'] == 'Newcomer']
        .groupby('onboard_year').size().to_dict()
    )
    return df_pipeline, pipeline_newcomer_counts


@app.cell(hide_code=True)
def section_inflow_header(mo):
    mo.md("""
    ---
    ## The talent inflow from newcomers and especially from non-crypto software ecosystems has slowed down.
    """)
    return


@app.cell(hide_code=True)
def insight_new_developer_inflow(
    ETHEREUM_COLOR,
    INACTIVE_COLOR,
    OTHER_CRYPTO_COLOR,
    PLOTLY_LAYOUT,
    df_pipeline,
    ecosystem_toggle,
    go,
    mo,
    pipeline_newcomer_counts,
):
    # Two strategic pipelines: Newcomers and Non-crypto experienced (2020-2024)
    _active_color = ETHEREUM_COLOR if ecosystem_toggle.value == 'Ethereum' else OTHER_CRYPTO_COLOR
    _cat_order = ['Newcomer', 'Non-crypto experienced']
    _cat_colors = {
        'Newcomer': INACTIVE_COLOR,
        'Non-crypto experienced': _active_color,
    }
    _cat_labels = {
        'Newcomer': 'Newcomers',
        'Non-crypto experienced': 'Non-Crypto Experienced',
    }

    _filtered = df_pipeline[df_pipeline['pipeline_category'].isin(_cat_order)]
    _pivot = _filtered.pivot(
        index='onboard_year', columns='pipeline_category', values='count'
    ).fillna(0).reindex(columns=_cat_order)

    _year_labels = [str(int(y)) for y in _pivot.index.tolist()]
    _year_pos = list(range(len(_year_labels)))

    _fig = go.Figure()
    for cat in _cat_order:
        if cat in _pivot.columns:
            _vals = _pivot[cat].tolist()
            _color = _cat_colors[cat]
            _label = _cat_labels.get(cat, cat)
            _fig.add_trace(go.Bar(
                x=_year_pos, y=_vals,
                name=_label,
                marker_color=_color,
                text=[str(int(v)) for v in _vals],
                textposition='inside',
                insidetextanchor='middle',
                textfont=dict(size=11, color='white'),
                showlegend=True,
            ))

    _fig.update_layout(
        **{
            **PLOTLY_LAYOUT,
            "barmode": "group",
            "height": 320,
            "margin": dict(l=60, r=20, t=20, b=40),
            "showlegend": True,
            "legend": dict(
                orientation="h",
                yanchor="bottom", y=1.05,
                xanchor="left", x=0,
                bgcolor="rgba(255,255,255,0)",
                font=dict(size=12),
            ),
            "xaxis": dict(
                title='Onboarding Year', showgrid=False,
                linecolor='#1F2937', linewidth=1, ticks='outside',
                tickvals=_year_pos, ticktext=_year_labels,
            ),
            "yaxis": dict(
                title='Developers', showgrid=False,
                linecolor='#1F2937', linewidth=1, ticks='outside',
            ),
        },
    )

    _newcomer_2021 = pipeline_newcomer_counts.get(2021, 0)
    _newcomer_2024 = pipeline_newcomer_counts.get(2024, 0)
    _drop_pct = (1 - _newcomer_2024 / max(_newcomer_2021, 1)) * 100

    headline_2 = "New and non-crypto developers represent a shrinking share of inflows"

    _output = mo.vstack([
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
        mo.md(
            f'Newcomer inflow peaked at {_newcomer_2021} in 2021 and has plateaued near {_newcomer_2024} '
            f'({_drop_pct:.0f}% decline). Non-crypto experienced developers have also declined steeply.'
        ),
    ])
    _output
    return (headline_2,)


@app.cell(hide_code=True)
def section_limitations(mo):
    _content = """
    **TVL as inclusion criterion.** *Assumption:* TVL identifies economically meaningful protocols. *Implication:* Low-stakes forks and testnet-only experiments are excluded; we focus on capital-securing DeFi.

    **Excluded protocols.** *Assumption:* Some high-TVL protocols have minimal observable OSS activity. *Implication:* Custodial/TradFi-linked projects appear in tables but contribute little to flow analysis.

    **Private repositories.** *Assumption:* Private repos are invisible to GitHub Archive. ***Implication:*** **Teams that develop behind closed doors, or move to private repos after open-source phases, will appear to "go inactive" in our data—this is one of the most consequential limitations.**

    **Post-hire behavior.** *Assumption:* Some developers are hired by crypto firms and stop public contributions. ***Implication:*** **The "inactive" count may be inflated; we cannot distinguish "left crypto" from "went private."**

    **Bot and noise filtering.** *Assumption:* We exclude known bots. *Implication:* Some automated contributions may slip through.

    **Identity resolution.** *Assumption:* OpenDevData maps multiple accounts to canonical IDs. *Implication:* Imperfect mapping may double-count some developers.

    **Scope.** This is a structured analysis of visible OSS developer flows across economically significant DeFi protocols—not a census of all crypto developers or proprietary development.
    """
    mo.vstack([
        mo.md("---"),
        mo.md("## Assumptions & Limitations"),
        mo.accordion({"Expand to read": _content}),
    ])
    return


@app.cell(hide_code=True)
def section_appendix_header(mo):
    mo.md("""
    ---

    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:16px 20px;margin:8px 0">
    <span style="font-size:11px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:1px">Appendix</span>

    ## Project Deep Dive

    This appendix demonstrates how the framework above applies at the project level. Select a project below to audit its developer composition and contribution patterns.
    </div>
    """)
    return


@app.cell(hide_code=True)
def appendix_project_selector(df_projects_with_eco, mo):
    # US-024: Project selector for deep dive
    _projects = sorted(df_projects_with_eco['project_display_name'].unique())
    project_selector = mo.ui.dropdown(
        options=_projects,
        value='Aave',
        label='Select a project:',
        full_width=True
    )
    mo.vstack([
        mo.md("Select a project to explore its developers:"),
        project_selector
    ])
    return (project_selector,)


@app.cell(hide_code=True)
def appendix_project_details(
    ETHEREUM_COLOR,
    PLOTLY_LAYOUT,
    df_contribution_features,
    go,
    make_subplots,
    mo,
    project_selector,
):
    # US-024: Display developers for selected project with charts
    _project = project_selector.value

    _project_devs = df_contribution_features[
        df_contribution_features['project_display_name'] == _project
    ].copy()

    _total = len(_project_devs)

    if _total == 0:
        _output = mo.md(f"No qualified developers found for **{_project}**")
    else:
        # Key metrics
        _active = _project_devs['is_still_active'].sum()
        _active_pct = (_active / _total * 100) if _total > 0 else 0
        _avg_tenure = _project_devs['tenure_months'].mean()
        _avg_intensity = _project_devs['avg_days_per_month'].mean()

        # Cluster distributions
        _onboard_counts = _project_devs['onboarding_cluster'].value_counts()
        _contrib_counts = _project_devs['contribution_cluster'].value_counts()

        # Create side-by-side bar charts
        _fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Onboarding Background', 'Contribution Intensity'),
            horizontal_spacing=0.15
        )

        # Onboarding clusters
        _onboard_colors = {
            'Newcomer': '#B0B7C3',
            'Experienced': ETHEREUM_COLOR,
        }
        _fig.add_trace(
            go.Bar(
                x=list(_onboard_counts.values),
                y=list(_onboard_counts.index),
                orientation='h',
                marker_color=[_onboard_colors.get(c, '#B0B7C3') for c in _onboard_counts.index],
                text=list(_onboard_counts.values),
                textposition='outside',
                showlegend=False
            ),
            row=1, col=1
        )

        # Contribution clusters
        _contrib_colors = {
            'Frequent Contributor': '#6F5AE0',
            'Regular Contributor': '#1F9E9A',
            'Occasional Contributor': '#B0B7C3'
        }
        _fig.add_trace(
            go.Bar(
                x=list(_contrib_counts.values),
                y=list(_contrib_counts.index),
                orientation='h',
                marker_color=[_contrib_colors.get(c, '#B0B7C3') for c in _contrib_counts.index],
                text=list(_contrib_counts.values),
                textposition='outside',
                showlegend=False
            ),
            row=1, col=2
        )

        _fig.update_layout(
            **{
                **PLOTLY_LAYOUT,
                "height": 250,
                "margin": dict(l=10, r=40, t=40, b=20),
            },
        )
        _fig.update_yaxes(autorange='reversed')

        _output = mo.vstack([
            mo.md(f"### {_project}"),
            mo.hstack([
                mo.stat(value=f"{_total}", label="Qualified Devs", bordered=True),
                mo.stat(value=f"{_active_pct:.0f}%", label="Still Active", bordered=True),
                mo.stat(value=f"{_avg_tenure:.0f} mo", label="Avg Tenure", bordered=True),
                mo.stat(value=f"{_avg_intensity:.1f}", label="Avg Days/Month", bordered=True),
            ], justify='space-around', widths='equal'),
            mo.md(""),
            mo.ui.plotly(_fig, config={'displayModeBar': False}),
        ])

    _output
    return


@app.cell(hide_code=True)
def section_conclusion(mo):
    mo.md("""
    ---

    *Analysis by [Open Source Observer](https://www.oso.xyz). Data from DefiLlama, GitHub Archive,
    OpenDevData (Electric Capital), and the OSO data warehouse.*
    """)
    return


@app.cell(hide_code=True)
def transform_monthly_active_devs(df_activity, df_projects_with_eco, pd):
    # US-005: Calculate monthly active developers per project
    # Filter to home project activity only
    _home_activity = df_activity[df_activity['is_home_project'] == True].copy()

    # Ensure month is datetime and filter to 2020+ (DeFi Summer onwards)
    _home_activity['month'] = pd.to_datetime(_home_activity['month'], errors='coerce')
    _home_activity = _home_activity[_home_activity['month'].notna()]
    _home_activity = _home_activity[_home_activity['month'] >= '2020-01-01']

    # Count unique developers per project per month
    df_monthly_devs = (
        _home_activity
        .groupby(['project_display_name', 'month'])['canonical_developer_id']
        .nunique()
        .reset_index()
        .rename(columns={'canonical_developer_id': 'monthly_active_devs'})
    )

    # Merge with project metadata
    df_monthly_devs = df_monthly_devs.merge(
        df_projects_with_eco[['project_display_name', 'tvl_rank', 'ecosystem_category', 'current_tvl']],
        on='project_display_name',
        how='left'
    )

    # Create month string for display (sorted chronologically)
    df_monthly_devs['month_str'] = df_monthly_devs['month'].dt.strftime('%Y-%m')
    return (df_monthly_devs,)


@app.cell(hide_code=True)
def transform_project_ecosystem_classification(
    PROJECT_ECOSYSTEM,
    df_defi_projects,
    pd,
):
    # US-002: Classify projects as Ethereum vs Other using manual mapping
    df_projects_with_eco = df_defi_projects.copy()

    # Apply manual ecosystem mapping (using display names)
    df_projects_with_eco['ecosystem_category'] = df_projects_with_eco['project_display_name'].map(PROJECT_ECOSYSTEM)
    # Default unmapped projects to 'Other'
    df_projects_with_eco['ecosystem_category'] = df_projects_with_eco['ecosystem_category'].fillna('Other')
    df_projects_with_eco['is_ethereum'] = df_projects_with_eco['ecosystem_category'] == 'Ethereum'

    # Add TVL rank
    df_projects_with_eco['tvl_rank'] = range(1, len(df_projects_with_eco) + 1)

    # Summary stats
    _total_projects = len(df_projects_with_eco)
    _eth_projects = df_projects_with_eco['is_ethereum'].sum()
    _eth_tvl = df_projects_with_eco[df_projects_with_eco['is_ethereum']]['current_tvl'].sum()
    _total_tvl = df_projects_with_eco['current_tvl'].sum()

    pct_eth_projects = (_eth_projects / _total_projects * 100) if _total_projects > 0 else 0
    pct_eth_tvl = (_eth_tvl / _total_tvl * 100) if _total_tvl > 0 else 0

    df_projects_summary = pd.DataFrame({
        'Category': ['Ethereum', 'Other', 'Total'],
        'Project Count': [
            _eth_projects,
            _total_projects - _eth_projects,
            _total_projects
        ],
        'TVL (USD)': [
            _eth_tvl,
            _total_tvl - _eth_tvl,
            _total_tvl
        ]
    })
    return df_projects_with_eco, pct_eth_projects, pct_eth_tvl


@app.cell(hide_code=True)
def query_defi_projects(
    mo,
    pyoso_db_conn,
):
    # US-002: Load top 50 DeFi projects with TVL (no local caching)
    df_defi_projects = mo.sql(
        """
        SELECT
          p.project_id,
          p.project_display_name,
          t.current_tvl,
          t.logo,
          t.defillama_urls
        FROM ethereum.devpanels.dim_projects_by_collection AS p
        LEFT JOIN ethereum.devpanels.mart_project_tvl AS t
          ON p.project_display_name = t.project_display_name
        WHERE p.collection_name = 'defillama-top-50-protocols'
        ORDER BY t.current_tvl DESC NULLS LAST
        """,
        engine=pyoso_db_conn,
        output=False,
    )
    return (df_defi_projects,)


@app.cell(hide_code=True)
def query_project_ecosystems(
    mo,
    pyoso_db_conn,
):
    # US-002: Get ecosystem classification for each project
    # Join to enriched activity to find the dominant ecosystem per project
    df_project_ecosystems = mo.sql(
        """
        SELECT
          p.project_display_name,
          t.farthest_eco AS ecosystem,
          COUNT(DISTINCT canonical_developer_id) AS dev_count
        FROM ethereum.devpanels.fact_top_dev_activity_monthly_enriched AS t
        JOIN ethereum.devpanels.dim_projects_by_collection AS p
          ON t.project_id = p.project_id
        WHERE p.collection_name = 'defillama-top-50-protocols'
          AND t.is_home_project = TRUE
          AND t.farthest_eco IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
        """,
        engine=pyoso_db_conn,
        output=False,
    )
    return (df_project_ecosystems,)


@app.cell(hide_code=True)
def query_tvl_history(mo, pyoso_db_conn):
    # Monthly TVL time series for top 50 DeFi protocols (no local caching)
    df_tvl_history = mo.sql(
        """
        SELECT
          project_name,
          project_display_name,
          sample_date,
          tvl,
          current_tvl
        FROM ethereum.devpanels.mart_project_tvl_history
        ORDER BY current_tvl DESC, sample_date
        """,
        engine=pyoso_db_conn,
        output=False,
    )
    return (df_tvl_history,)


@app.cell(hide_code=True)
def query_top_devs(mo, pyoso_db_conn):
    # US-003: Load top developers per project (no local caching)
    df_top_devs = mo.sql(
        """
        SELECT
          t.project_id,
          t.project_display_name,
          t.canonical_developer_id,
          t.dev_rank,
          t.total_active_days,
          t.first_commit_date,
          t.last_commit_date
        FROM ethereum.devpanels.mart_top_devs_by_project AS t
        JOIN ethereum.devpanels.dim_projects_by_collection AS p
          ON t.project_id = p.project_id
        WHERE p.collection_name = 'defillama-top-50-protocols'
        """,
        engine=pyoso_db_conn,
        output=False,
    )
    return (df_top_devs,)


@app.cell(hide_code=True)
def query_alignment(
    mo,
    pd,
    pyoso_db_conn,
):
    # US-003: Load five-track alignment data per developer-month
    # SCOPED to only developers in our DeFi project set
    df_alignment = mo.sql(
        """
        SELECT
          a.canonical_developer_id,
          a.actor_login,
          a.month,
          a.home_project_repo_event_days,
          a.home_project_events,
          a.home_project_primary_ecosystem,
          a.home_project_name,
          a.crypto_repo_event_days,
          a.crypto_events,
          a.crypto_primary_ecosystem,
          a.crypto_primary_project,
          a.personal_repo_event_days,
          a.personal_events,
          a.personal_primary_ecosystem,
          a.oss_repo_event_days,
          a.oss_events,
          a.oss_primary_ecosystem,
          a.oss_primary_project,
          a.interest_repo_event_days,
          a.interest_events,
          a.total_repo_event_days,
          a.has_home_project_activity,
          a.has_crypto_activity,
          a.has_personal_activity,
          a.has_oss_activity,
          a.has_interest_activity
        FROM ethereum.devpanels.mart_developer_alignment_monthly AS a
        JOIN ethereum.devpanels.mart_top_devs_by_project AS dpb
          ON a.canonical_developer_id = dpb.canonical_developer_id
        JOIN ethereum.devpanels.dim_projects_by_collection AS pbc
          ON dpb.project_id = pbc.project_id
        WHERE pbc.collection_name = 'defillama-top-50-protocols'
        ORDER BY a.canonical_developer_id, a.month
        """,
        engine=pyoso_db_conn,
        output=False,
    )
    df_alignment["month"] = pd.to_datetime(df_alignment["month"])
    return (df_alignment,)


@app.cell(hide_code=True)
def query_interest_projects(
    mo,
    pd,
    pyoso_db_conn,
):
    # Interest (Watch event) project names + ecosystem for feeder analysis
    df_interest_projects = mo.sql(
        """
        SELECT
          a.canonical_developer_id,
          a.month,
          COALESCE(
            a.project_display_name,
            a.nearest_eco,
            SPLIT_PART(a.repo_name, '/', 1)
          ) AS interest_project,
          BOOL_OR(COALESCE(a.is_crypto, FALSE)) AS is_crypto,
          MAX(a.farthest_eco) AS farthest_eco,
          SUM(a.count_days) AS interest_days,
          SUM(a.count_events) AS interest_events
        FROM ethereum.devpanels.fact_top_dev_activity_monthly_enriched AS a
        JOIN ethereum.devpanels.mart_top_devs_by_project AS dpb
          ON a.canonical_developer_id = dpb.canonical_developer_id
        JOIN ethereum.devpanels.dim_projects_by_collection AS pbc
          ON dpb.project_id = pbc.project_id
        WHERE pbc.collection_name = 'defillama-top-50-protocols'
          AND a.event_type = 'WatchEvent'
        GROUP BY 1, 2, 3
        ORDER BY 1, 2
        """,
        engine=pyoso_db_conn,
        output=False,
    )
    df_interest_projects["month"] = pd.to_datetime(df_interest_projects["month"])
    return (df_interest_projects,)


@app.cell(hide_code=True)
def query_activity(
    mo,
    pd,
    pyoso_db_conn,
):
    # US-003: Load detailed activity for heatmap (monthly active devs per project)
    df_activity = mo.sql(
        """
        SELECT
          p.project_display_name,
          t.month,
          t.canonical_developer_id,
          t.actor_login,
          t.event_type,
          t.count_days,
          t.count_events,
          t.farthest_eco,
          t.is_home_project
        FROM ethereum.devpanels.fact_top_dev_activity_monthly_enriched AS t
        JOIN ethereum.devpanels.dim_projects_by_collection AS p
          ON t.project_id = p.project_id
        WHERE p.collection_name = 'defillama-top-50-protocols'
          AND t.event_type IN ('PushEvent', 'PullRequestEvent', 'PullRequestReviewEvent')
        """,
        engine=pyoso_db_conn,
        output=False,
    )
    df_activity["month"] = pd.to_datetime(df_activity["month"])
    return (df_activity,)


@app.cell(hide_code=True)
def settings_analysis_window():
    # Analysis time range
    START_DATE = '2020-01-01'
    END_DATE = '2026-01-31'

    # Filtering thresholds
    MIN_HOME_PROJECT_MONTHS = 12  # Minimum months on home project to qualify
    OFFBOARD_INACTIVE_MONTHS = 6  # Consecutive inactive months to count as offboarded
    ONBOARD_ACTIVITY_THRESHOLD = 1  # 1st month with home project activity = onboard date
    return


@app.cell(hide_code=True)
def settings_color_palette():
    # Color palette — semantic colors reused across all charts
    ETHEREUM_COLOR = '#6F5AE0'
    OTHER_CRYPTO_COLOR = '#1F9E9A'
    INACTIVE_COLOR = '#B0B7C3'
    NON_CRYPTO_COLOR = '#B0B7C3'  # merged into inactive
    ETHEREUM_LIGHT = '#9A8CF0'
    OTHER_CRYPTO_LIGHT = '#5EC4BF'
    NET_LINE_COLOR = '#374151'

    ECOSYSTEM_COLORS = {
        'Ethereum': ETHEREUM_COLOR,
        'Other Crypto': OTHER_CRYPTO_COLOR,
        'Non-Crypto': INACTIVE_COLOR,
        'Inactive': INACTIVE_COLOR,
    }
    return ETHEREUM_COLOR, ETHEREUM_LIGHT, INACTIVE_COLOR, NET_LINE_COLOR, NON_CRYPTO_COLOR, OTHER_CRYPTO_COLOR, OTHER_CRYPTO_LIGHT


@app.cell(hide_code=True)
def settings_ecosystem_mapping():
    # Manual ecosystem classification for top DeFi projects
    # Ethereum = protocols native to or primarily deployed on Ethereum/L2s
    # Other = CEXs, non-Ethereum L1s (Solana, Tron, BNB Chain), TradFi
    # Manual ecosystem classification for top DeFi projects (by display name)
    # Ethereum = protocols native to or primarily deployed on Ethereum/L2s
    # Other = CEXs, non-Ethereum L1s (Solana, Tron, BNB Chain), TradFi
    PROJECT_ECOSYSTEM = {
        # Ethereum-native DeFi
        'Aave': 'Ethereum',
        'Lido': 'Ethereum',
        'EigenLayer': 'Ethereum',          # ETH restaking
        'WBTC': 'Ethereum',               # Wrapped Bitcoin on Ethereum
        'Etherfi': 'Ethereum',             # ETH liquid staking (prev. ether.fi)
        'Uniswap': 'Ethereum',
        'Ethena': 'Ethereum',
        'Morpho': 'Ethereum',              # Morpho lending
        'Sky (prev. MakerDAO)': 'Ethereum',
        'Spark Foundation': 'Ethereum',    # MakerDAO spinoff (prev. Spark)
        'Rocket Pool': 'Ethereum',         # ETH staking
        'Base': 'Ethereum',                # Base L2
        'Veda': 'Ethereum',
        'Pendle': 'Ethereum',              # Yield trading
        'Maple': 'Ethereum',               # Institutional lending (prev. Maple Finance)
        'Polygon zkEVM': 'Ethereum',       # Polygon zkEVM L2
        'Curve': 'Ethereum',
        'obolnetwork': 'Ethereum',         # Distributed validators
        'Wormhole Foundation': 'Ethereum', # Cross-chain, Ethereum ecosystem
        'Offchain Labs': 'Ethereum',       # Arbitrum
        'Steakhouse Financial': 'Ethereum',
        'Gauntlet': 'Ethereum',
        'Tydro': 'Ethereum',
        'Compound': 'Ethereum',            # Lending protocol
        'Fluid': 'Ethereum',               # Instadapp-based lending
        'Kelp': 'Ethereum',                # Liquid restaking
        'Convex Finance': 'Ethereum',      # Curve ecosystem
        'Euler Finance': 'Ethereum',       # Lending protocol
        'Tornado Cash': 'Ethereum',        # Privacy protocol
        'Renzo Protocol': 'Ethereum',      # Liquid restaking
        'Yearn': 'Ethereum',               # Yield aggregator
        'Aerodrome Finance': 'Ethereum',   # Base L2 DEX
        'Threshold Network': 'Ethereum',   # tBTC / Keep Network

        # Centralized Exchanges
        'Binance': 'Other',

        # Non-Ethereum L1s
        'JustLend DAO': 'Other',           # Tron
        'Babylon': 'Other',                # Bitcoin
        'Kamino Finance': 'Other',         # Solana
        'PancakeSwap': 'Other',            # BNB Chain
        'Hyperliquid': 'Other',            # Hyperliquid chain
        'Jupiter Exchange': 'Other',       # Solana
        'Sanctum': 'Other',                # Solana
        'jito-labs': 'Other',              # Solana
        'Solv Protocol': 'Other',          # Bitcoin/multi-chain
        'Bedrock Technology': 'Other',     # Bitcoin L2
        'B2 Buzz': 'Other',                # Bitcoin L2
        'Meteora': 'Other',                # Solana
        'Orca So': 'Other',                # Solana
        'Raydium Protocol': 'Other',       # Solana
        'Marinade': 'Other',               # Solana
        'Venus Protocol': 'Other',         # BNB Chain

        # Other/TradFi
        'Tether': 'Other',                 # Multi-chain stablecoin
        'Falcon Finance': 'Other',
        'BlackRock BUIDL': 'Other',        # TradFi (prev. BlackRock)
        'DoubleZero': 'Other',
        'Securitize': 'Other',             # TradFi tokenization
        'Spiko': 'Other',                  # TradFi tokenization
    }
    return (PROJECT_ECOSYSTEM,)


@app.cell(hide_code=True)
def settings_plotly_layout(ETHEREUM_COLOR, OTHER_CRYPTO_COLOR, INACTIVE_COLOR):
    PLOTLY_LAYOUT = dict(
        title="",
        barmode="relative",
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=12, color="#1F2937"),
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
            linecolor="#1F2937", linewidth=1,
            ticks="outside"
        ),
        yaxis=dict(
            title="",
            showgrid=True, gridcolor="#E5E7EB",
            zeroline=True, zerolinecolor="#1F2937", zerolinewidth=1,
            linecolor="#1F2937", linewidth=1,
            ticks="outside"
        ),
        colorway=[ETHEREUM_COLOR, OTHER_CRYPTO_COLOR, INACTIVE_COLOR, '#374151']
    )
    return (PLOTLY_LAYOUT,)


@app.cell(hide_code=True)
def helper_stringify_in_clause():
    # Helper for SQL IN clauses
    stringify = lambda arr: "'" + "','".join(arr) + "'"
    return


@app.cell(hide_code=True)
def related(mo):
    mo.md("""
    ## Related

    **Metric Definitions**
    - [Activity](../data/metric-definitions/activity.py) — Monthly Active Developer (MAD) methodology
    - [Lifecycle](../data/metric-definitions/lifecycle.py) — Developer stage definitions
    - [Retention](../data/metric-definitions/retention.py) — Cohort-based retention methodology

    **Other Insights**
    - [2025 Developer Trends](./developer-report-2025.py)
    - [Lifecycle Analysis](./developer-lifecycle.py)
    - [Retention Analysis](./developer-retention.py)
    - [Speedrun Ethereum](./speedrun-ethereum.py)
    """)
    return


@app.cell(hide_code=True)
def import_libraries():
    import numpy as np
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    return go, make_subplots, pd


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
