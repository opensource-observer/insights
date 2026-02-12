import marimo

__generated_with = "unknown"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Activity

    The **Monthly Active Developer (MAD)** metric measures unique developers contributing code within a rolling 28-day window — the standard metric from the [Electric Capital Developer Report](https://www.developerreport.com).

    **Preview:**
    ```sql
    SELECT
      e.name AS ecosystem,
      m.day,
      m.all_devs,
      m.full_time_devs,
      m.part_time_devs,
      m.one_time_devs,
      m.devs_0_1y AS newcomers,
      m.devs_1_2y AS emerging,
      m.devs_2y_plus AS established,
      m.num_commits
    FROM oso.stg_opendevdata__eco_mads AS m
    JOIN oso.stg_opendevdata__ecosystems AS e
      ON m.ecosystem_id = e.id
    WHERE e.name = 'Ethereum'
    ORDER BY m.day DESC
    LIMIT 10
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Overview

    The `stg_opendevdata__eco_mads` model provides pre-calculated developer activity metrics per ecosystem per day, sourced from Electric Capital's Open Dev Data. Each row captures a snapshot of ecosystem health across three dimensions:

    - **Activity level**: How intensely developers contribute (full-time, part-time, one-time)
    - **Tenure**: How long developers have been in crypto (newcomers, emerging, established)
    - **Exclusivity**: Whether developers work in one ecosystem or many (exclusive vs multichain)

    These breakdowns enable the standard Electric Capital visualizations: total MAD trends, activity composition, and tenure distribution — all selectable by ecosystem.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Key Definitions

    | Metric | Definition | Window |
    |:-------|:-----------|:-------|
    | **Monthly Active Developers** | Unique developers with ≥1 commit | Rolling 28 days |
    | **Full-time** | ≥10 active days in window | 84-day rolling |
    | **Part-time** | <10 active days, regular contributions | 84-day rolling |
    | **One-time** | Minimal or sporadic activity | 84-day rolling |
    | **Newcomers** | <1 year contributing to crypto | Lifetime |
    | **Emerging** | 1-2 years contributing to crypto | Lifetime |
    | **Established** | 2+ years contributing to crypto | Lifetime |
    | **Exclusive** | Active only in this ecosystem | Rolling 28 days |
    | **Multichain** | Active across multiple ecosystems | Rolling 28 days |

    > Developers are original code authors — merge/PR integrators are not counted unless they authored commits. Identity resolution deduplicates developers across multiple accounts and emails.
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _eco_df = mo.sql("""
        SELECT DISTINCT e.name
        FROM oso.stg_opendevdata__eco_mads AS m
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON m.ecosystem_id = e.id
        WHERE m.day >= CURRENT_DATE - INTERVAL '90' DAY
        ORDER BY e.name
    """, engine=pyoso_db_conn, output=False)
    ecosystem_names = sorted(_eco_df['name'].tolist())
    return (ecosystem_names,)


@app.cell(hide_code=True)
def _(mo, ecosystem_names):
    ecosystem_dropdown = mo.ui.dropdown(
        options=ecosystem_names,
        value="Ethereum",
        label="Ecosystem"
    )
    time_range = mo.ui.dropdown(
        options=["All Time", "Last 5 Years", "Last 3 Years", "Last Year"],
        value="All Time",
        label="Time Range"
    )
    mo.hstack([ecosystem_dropdown, time_range], gap=2)
    return ecosystem_dropdown, time_range


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, pd, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    df_activity = mo.sql(
        f"""
        SELECT
          m.day,
          m.all_devs,
          m.full_time_devs,
          m.part_time_devs,
          m.one_time_devs,
          m.devs_0_1y AS newcomers,
          m.devs_1_2y AS emerging,
          m.devs_2y_plus AS established,
          m.exclusive_devs,
          m.multichain_devs,
          m.num_commits
        FROM oso.stg_opendevdata__eco_mads AS m
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON m.ecosystem_id = e.id
        WHERE e.name = '{_eco}'
          AND m.day >= DATE '2015-01-01'
        ORDER BY m.day
        """,
        engine=pyoso_db_conn,
        output=False
    )
    df_activity['day'] = pd.to_datetime(df_activity['day'])
    return (df_activity,)


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    _repo_df = mo.sql(
        f"""
        SELECT COUNT(DISTINCT err.repo_id) AS repo_count
        FROM oso.stg_opendevdata__ecosystems_repos_recursive AS err
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON err.ecosystem_id = e.id
        WHERE e.name = '{_eco}'
        """,
        engine=pyoso_db_conn,
        output=False
    )
    repo_count = int(_repo_df['repo_count'].iloc[0])
    return (repo_count,)


@app.cell(hide_code=True)
def _(mo, df_activity, repo_count, pd, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    _current = df_activity.iloc[-1]
    _current_date = _current['day']
    _mad = int(_current['all_devs'])
    _ft = int(_current['full_time_devs'])
    _commits = int(_current['num_commits'])

    _year_ago = _current_date - pd.DateOffset(years=1)
    _year_ago_df = df_activity[df_activity['day'] <= _year_ago]
    if len(_year_ago_df) > 0:
        _prev_mad = int(_year_ago_df.iloc[-1]['all_devs'])
        _yoy_pct = ((_mad - _prev_mad) / _prev_mad) * 100
        _yoy_caption = f"{_yoy_pct:+.1f}% YoY"
    else:
        _yoy_caption = "N/A"

    _peak_mad = int(df_activity['all_devs'].max())
    _peak_date = df_activity.loc[df_activity['all_devs'].idxmax(), 'day']

    mo.vstack([
        mo.md(f"## {_eco} Developer Activity"),
        mo.hstack([
            mo.stat(label="Monthly Active Devs", value=f"{_mad:,}", bordered=True, caption=_yoy_caption),
            mo.stat(label="Full-time Devs", value=f"{_ft:,}", bordered=True, caption="≥10 active days / 28d"),
            mo.stat(label="Total Repos", value=f"{repo_count:,}", bordered=True, caption="Recursive ecosystem mapping"),
            mo.stat(label="28d Commits", value=f"{_commits:,}", bordered=True, caption=f"Peak MAD: {_peak_mad:,} ({_peak_date.strftime('%b %Y')})"),
        ], widths="equal", gap=1),
    ])
    return


@app.cell(hide_code=True)
def _(mo, df_activity, go, apply_ec_style, time_range, pd, EC_COLORS, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    _df = df_activity.copy()

    if time_range.value == "Last 5 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]
    elif time_range.value == "Last 3 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2022-01-01')]
    elif time_range.value == "Last Year":
        _df = _df[_df['day'] >= pd.Timestamp('2024-01-01')]

    _current = _df.iloc[-1]

    _fig = go.Figure()

    _fig.add_trace(go.Scatter(
        x=_df['day'], y=_df['all_devs'],
        name=f"Monthly Active ({int(_current['all_devs']):,})",
        mode='lines', fill='tozeroy',
        fillcolor=EC_COLORS['light_blue_fill'],
        line=dict(color=EC_COLORS['light_blue'], width=2),
        hovertemplate='<b>MAD</b>: %{y:,.0f}<extra></extra>'
    ))

    _fig.add_trace(go.Scatter(
        x=_df['day'], y=_df['full_time_devs'],
        name=f"Full-time ({int(_current['full_time_devs']):,})",
        mode='lines',
        line=dict(color=EC_COLORS['dark_blue'], width=2),
        hovertemplate='<b>Full-time</b>: %{y:,.0f}<extra></extra>'
    ))

    _fig.add_trace(go.Scatter(
        x=_df['day'], y=_df['newcomers'],
        name=f"New Devs ({int(_current['newcomers']):,})",
        mode='lines',
        line=dict(color=EC_COLORS['orange'], width=2, dash='dot'),
        hovertemplate='<b>New Devs</b>: %{y:,.0f}<extra></extra>'
    ))

    apply_ec_style(_fig,
        title=f"{int(_current['all_devs']):,} monthly active developers in {_eco}",
        subtitle="Total MAD, full-time developers, and new developers (<1yr) over time",
        y_title="Developers"
    )
    _fig.update_layout(height=450)

    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Activity Level Breakdown

    Developers segmented by sustained activity patterns over an 84-day rolling window.
    Full-time developers (≥10 active days per 28-day window) represent the most committed contributors.
    """)
    return


@app.cell(hide_code=True)
def _(mo, df_activity, go, apply_ec_style, time_range, pd, ACTIVITY_COLORS, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    _df = df_activity.copy()

    if time_range.value == "Last 5 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]
    elif time_range.value == "Last 3 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2022-01-01')]
    elif time_range.value == "Last Year":
        _df = _df[_df['day'] >= pd.Timestamp('2024-01-01')]

    _current = _df.iloc[-1]

    _fig = go.Figure()

    for _label, _col in [("Full-time", "full_time_devs"), ("Part-time", "part_time_devs"), ("One-time", "one_time_devs")]:
        _fig.add_trace(go.Scatter(
            x=_df['day'], y=_df[_col],
            name=f"{_label} ({int(_current[_col]):,})",
            mode='lines', stackgroup='one',
            fillcolor=ACTIVITY_COLORS[_label],
            line=dict(width=0.5, color=ACTIVITY_COLORS[_label]),
            hovertemplate=f'<b>{_label}</b>: %{{y:,.0f}}<extra></extra>'
        ))

    apply_ec_style(_fig,
        title=f"{_eco} Developers by Activity Level",
        subtitle="Stacked by full-time, part-time, and one-time contributors",
        y_title="Developers"
    )
    _fig.update_layout(height=450)

    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Active Developers by Tenure

    Developer tenure reflects how long they have been contributing to crypto overall (not just this ecosystem).
    Established developers (2+ years) represent the core of sustained open source engagement.
    """)
    return


@app.cell(hide_code=True)
def _(mo, df_activity, go, apply_ec_style, time_range, pd, TENURE_COLORS, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    _df = df_activity.copy()

    if time_range.value == "Last 5 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]
    elif time_range.value == "Last 3 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2022-01-01')]
    elif time_range.value == "Last Year":
        _df = _df[_df['day'] >= pd.Timestamp('2024-01-01')]

    _current = _df.iloc[-1]

    _fig = go.Figure()

    for _label, _col in [("Established", "established"), ("Emerging", "emerging"), ("Newcomers", "newcomers")]:
        _fig.add_trace(go.Scatter(
            x=_df['day'], y=_df[_col],
            name=f"{_label} ({int(_current[_col]):,})",
            mode='lines', stackgroup='one',
            fillcolor=TENURE_COLORS[_label],
            line=dict(width=0.5, color=TENURE_COLORS[_label]),
            hovertemplate=f'<b>{_label}</b>: %{{y:,.0f}}<extra></extra>'
        ))

    apply_ec_style(_fig,
        title=f"{_eco} Developers by Tenure",
        subtitle="Stacked by newcomers (<1yr), emerging (1-2yr), and established (2+yr)",
        y_title="Developers"
    )
    _fig.update_layout(height=450)

    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Data Source Validation

    The charts above use Open Dev Data's pre-calculated MAD counts. How do those compare to MAD calculated independently from GitHub Archive? This section compares four sources during **February 2025** for the selected ecosystem:

    1. **Open Dev Data**: Pre-calculated rolling 28-day MAD from `eco_mads`
    2. **GitHub Archive**: Rolling 28-day MAD calculated from raw `developer_activities`
    3. **Mapped ODD**: ODD filtered to repos with valid OSO `repo_id` mapping
    4. **Mapped GHA**: GHA filtered to the same mapped repo set

    Sources 3 & 4 isolate the effect of repository mapping — any remaining gap is due to identity resolution and code filtering differences.
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, pd, go, apply_ec_style, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value

    _df_odd = mo.sql(
        f"""
        SELECT m.day, m.all_devs
        FROM oso.stg_opendevdata__eco_mads AS m
        JOIN oso.stg_opendevdata__ecosystems AS e ON m.ecosystem_id = e.id
        WHERE e.name = '{_eco}'
          AND m.day BETWEEN DATE '2025-02-01' AND DATE '2025-02-28'
        ORDER BY m.day
        """, engine=pyoso_db_conn, output=False)

    _df_gha = mo.sql(
        f"""
        WITH base AS (
            SELECT DISTINCT da.bucket_day, da.actor_id
            FROM oso.int_gharchive__developer_activities AS da
            JOIN oso.int_opendevdata__repositories_with_repo_id AS r
              ON da.repo_id = r.repo_id
            JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
              ON r.opendevdata_id = err.repo_id
            JOIN oso.stg_opendevdata__ecosystems AS e
              ON err.ecosystem_id = e.id
            WHERE e.name = '{_eco}'
              AND da.bucket_day BETWEEN DATE '2025-01-04' AND DATE '2025-02-28'
        ),
        rolling AS (
            SELECT d.bucket_day, COUNT(DISTINCT w.actor_id) AS all_devs
            FROM (SELECT DISTINCT bucket_day FROM base) d
            JOIN base w ON w.bucket_day BETWEEN d.bucket_day - INTERVAL '27' DAY AND d.bucket_day
            GROUP BY 1
        )
        SELECT bucket_day AS day, all_devs
        FROM rolling
        WHERE bucket_day BETWEEN DATE '2025-02-01' AND DATE '2025-02-28'
        ORDER BY 1
        """, engine=pyoso_db_conn, output=False)

    _df_odd_mapped = mo.sql(
        f"""
        WITH mapped_repos AS (
            SELECT DISTINCT r.opendevdata_id
            FROM oso.int_opendevdata__repositories_with_repo_id AS r
            JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
              ON r.opendevdata_id = err.repo_id
            JOIN oso.stg_opendevdata__ecosystems AS e
              ON err.ecosystem_id = e.id
            WHERE e.name = '{_eco}' AND r.repo_id IS NOT NULL
        )
        SELECT rda.day, COUNT(DISTINCT rda.canonical_developer_id) AS all_devs
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN mapped_repos AS mr ON rda.repo_id = mr.opendevdata_id
        WHERE rda.day BETWEEN DATE '2025-02-01' AND DATE '2025-02-28'
        GROUP BY 1
        ORDER BY 1
        """, engine=pyoso_db_conn, output=False)

    _df_gha_mapped = mo.sql(
        f"""
        WITH mapped_repos AS (
            SELECT DISTINCT r.repo_id
            FROM oso.int_opendevdata__repositories_with_repo_id AS r
            JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
              ON r.opendevdata_id = err.repo_id
            JOIN oso.stg_opendevdata__ecosystems AS e
              ON err.ecosystem_id = e.id
            WHERE e.name = '{_eco}' AND r.repo_id IS NOT NULL
        ),
        base AS (
            SELECT DISTINCT da.bucket_day, da.actor_id
            FROM oso.int_gharchive__developer_activities AS da
            JOIN mapped_repos AS mr ON da.repo_id = mr.repo_id
            WHERE da.bucket_day BETWEEN DATE '2025-01-04' AND DATE '2025-02-28'
        ),
        rolling AS (
            SELECT d.bucket_day, COUNT(DISTINCT w.actor_id) AS all_devs
            FROM (SELECT DISTINCT bucket_day FROM base) d
            JOIN base w ON w.bucket_day BETWEEN d.bucket_day - INTERVAL '27' DAY AND d.bucket_day
            GROUP BY 1
        )
        SELECT bucket_day AS day, all_devs
        FROM rolling
        WHERE bucket_day BETWEEN DATE '2025-02-01' AND DATE '2025-02-28'
        ORDER BY 1
        """, engine=pyoso_db_conn, output=False)

    _df_odd['source'] = 'Open Dev Data'
    _df_gha['source'] = 'GitHub Archive'
    _df_odd_mapped['source'] = 'Mapped ODD'
    _df_gha_mapped['source'] = 'Mapped GHA'
    for _d in [_df_odd, _df_gha, _df_odd_mapped, _df_gha_mapped]:
        _d['day'] = pd.to_datetime(_d['day'])

    _color_map = {
        'Open Dev Data': '#4C78A8',
        'GitHub Archive': '#E15759',
        'Mapped ODD': '#2E86AB',
        'Mapped GHA': '#A23B72',
    }

    _fig = go.Figure()
    for _src_df in [_df_odd, _df_gha, _df_odd_mapped, _df_gha_mapped]:
        _name = _src_df['source'].iloc[0]
        _fig.add_trace(go.Scatter(
            x=_src_df['day'], y=_src_df['all_devs'],
            name=_name, mode='lines',
            line=dict(width=2.5, color=_color_map[_name]),
            hovertemplate=f'<b>{_name}</b>: %{{y:,.0f}}<extra></extra>'
        ))

    apply_ec_style(_fig,
        title=f"MAD Comparison: 4 Data Sources ({_eco})",
        subtitle="February 2025 — differences reflect identity resolution, code filtering, and repo mapping",
        y_title="Monthly Active Developers"
    )
    _fig.update_layout(height=400)

    # Summary stats
    _avgs = {}
    for _d, _n in [(_df_odd, 'ODD'), (_df_gha, 'GHA'), (_df_odd_mapped, 'Mapped ODD'), (_df_gha_mapped, 'Mapped GHA')]:
        _avgs[_n] = int(_d['all_devs'].mean()) if len(_d) > 0 else 0

    _odd_avg = _avgs['ODD']
    _gha_avg = _avgs['GHA']
    _diff_pct = ((_gha_avg - _odd_avg) / _odd_avg * 100) if _odd_avg > 0 else 0

    mo.vstack([
        mo.hstack([
            mo.stat(label="ODD (avg)", value=f"{_odd_avg:,}", bordered=True, caption="Pre-calculated by EC"),
            mo.stat(label="GHA (avg)", value=f"{_gha_avg:,}", bordered=True, caption="Calculated from raw events"),
            mo.stat(label="GHA vs ODD", value=f"{_diff_pct:+.1f}%", bordered=True, caption="Identity + filtering gap"),
            mo.stat(label="Mapped ODD (avg)", value=f"{_avgs['Mapped ODD']:,}", bordered=True, caption="ODD repos with repo_id"),
        ], widths="equal", gap=1),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df_trunc = mo.sql(
        f"""
        SELECT
          COUNT(*) AS total_push_events,
          SUM(CASE WHEN actual_commits_count > 20 THEN 1 ELSE 0 END) AS truncated_events,
          SUM(available_commits_count) AS available_commits,
          SUM(actual_commits_count) AS actual_commits,
          SUM(actual_commits_count - available_commits_count) AS missing_commits
        FROM oso.stg_github__push_events
        WHERE created_at BETWEEN DATE '2025-02-01' AND DATE '2025-02-28'
          AND actual_commits_count IS NOT NULL
        """,
        engine=pyoso_db_conn,
        output=False
    )

    _total = int(_df_trunc['total_push_events'].iloc[0])
    _truncated = int(_df_trunc['truncated_events'].iloc[0])
    _available = int(_df_trunc['available_commits'].iloc[0])
    _actual = int(_df_trunc['actual_commits'].iloc[0])
    _missing = int(_df_trunc['missing_commits'].iloc[0])
    _pct_truncated = (_truncated / _total * 100) if _total > 0 else 0
    _pct_missing = (_missing / _actual * 100) if _actual > 0 else 0

    mo.vstack([
        mo.md("""
    ### PushEvent Commit Truncation (February 2025)

    GitHub's Events API caps PushEvent payloads at 20 commits. Pushes with >20 commits lose individual commit data, which can affect activity-day calculations for batch committers.
        """),
        mo.hstack([
            mo.stat(label="Total Push Events", value=f"{_total:,}", bordered=True, caption="Feb 2025, all repos"),
            mo.stat(label="Truncated (>20)", value=f"{_truncated:,}", bordered=True, caption=f"{_pct_truncated:.2f}% of events"),
            mo.stat(label="Actual Commits", value=f"{_actual:,}", bordered=True, caption="Real distinct_size total"),
            mo.stat(label="Missing Commits", value=f"{_missing:,}", bordered=True, caption=f"{_pct_missing:.1f}% of actual"),
        ], widths="equal", gap=1),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Methodology

    ### Data Source

    All metrics come from **Open Dev Data** (Electric Capital), accessed via `oso.stg_opendevdata__eco_mads`. This model provides pre-calculated daily snapshots per ecosystem.

    ### Definitions

    Per the [Electric Capital methodology](https://www.developerreport.com/about):

    - **Time Window**: Rolling 28-day window (not calendar month)
    - **Developer Classification**:
      - **Full-Time**: ≥10 active days in the rolling 28-day window
      - **Part-Time**: <10 active days in the rolling 28-day window
      - **One-Time**: Minimal/sporadic activity (tracked via 84-day rolling window)
    - **Identity Resolution**: Developers are "fingerprinted" to deduplicate across multiple accounts/emails
    - **Code Filtering**: Commits from forks and copy-pasted code are filtered out
    - **Tenure**: Measures total time a developer has been active in any crypto ecosystem

    ### Known Limitations

    | Factor | Impact |
    |:-------|:-------|
    | **Curated repo set** | Only repos tracked by Open Dev Data are included |
    | **Identity resolution** | Some developers with unusual patterns may be missed or merged |
    | **Code filtering** | Fork/copy detection is heuristic and may over- or under-filter |
    | **Latency** | Data may lag a few days behind real-time |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Queries

    ### 1. Monthly Active Developers for an Ecosystem

    Query the pre-calculated MAD metric with full breakdowns for any ecosystem.

    ```sql
    SELECT
      m.day,
      m.all_devs,
      m.full_time_devs,
      m.part_time_devs,
      m.one_time_devs,
      m.devs_0_1y AS newcomers,
      m.devs_1_2y AS emerging,
      m.devs_2y_plus AS established,
      m.num_commits
    FROM oso.stg_opendevdata__eco_mads AS m
    JOIN oso.stg_opendevdata__ecosystems AS e
      ON m.ecosystem_id = e.id
    WHERE e.name = 'Ethereum'
      AND m.day >= CURRENT_DATE - INTERVAL '90' DAY
    ORDER BY m.day DESC
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          m.day,
          m.all_devs,
          m.full_time_devs,
          m.part_time_devs,
          m.one_time_devs,
          m.devs_0_1y AS newcomers,
          m.devs_1_2y AS emerging,
          m.devs_2y_plus AS established,
          m.num_commits
        FROM oso.stg_opendevdata__eco_mads AS m
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON m.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
          AND m.day >= CURRENT_DATE - INTERVAL '90' DAY
        ORDER BY m.day DESC
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 2. Top Ecosystems by Current Developer Count

    Rank ecosystems by their most recent MAD count.

    ```sql
    SELECT
      e.name AS ecosystem,
      m.all_devs AS monthly_active_devs,
      m.full_time_devs,
      m.exclusive_devs,
      m.multichain_devs,
      m.num_commits
    FROM oso.stg_opendevdata__eco_mads AS m
    JOIN oso.stg_opendevdata__ecosystems AS e
      ON m.ecosystem_id = e.id
    WHERE m.day = (
      SELECT MAX(day)
      FROM oso.stg_opendevdata__eco_mads
    )
    ORDER BY m.all_devs DESC
    LIMIT 20
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          e.name AS ecosystem,
          m.all_devs AS monthly_active_devs,
          m.full_time_devs,
          m.exclusive_devs,
          m.multichain_devs,
          m.num_commits
        FROM oso.stg_opendevdata__eco_mads AS m
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON m.ecosystem_id = e.id
        WHERE m.day = (
          SELECT MAX(day)
          FROM oso.stg_opendevdata__eco_mads
        )
        ORDER BY m.all_devs DESC
        LIMIT 20
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Related Models

    - **Ecosystems**: [ecosystems.py](../models/ecosystems.py) — Ecosystem definitions and hierarchy
    - **Developers**: [developers.py](../models/developers.py) — Unified developer identities
    - **Commits**: [commits.py](../models/commits.py) — Unified commit data
    - **Timeseries Metrics**: [timeseries-metrics.py](../models/timeseries-metrics.py) — Aggregated time series
    - **Alignment**: [alignment.py](./alignment.py) — Developer ecosystem alignment metric
    - **Lifecycle**: [lifecycle.py](./lifecycle.py) — Developer lifecycle stages
    """)
    return


# --- Infrastructure cells ---


@app.cell(hide_code=True)
def _():
    def apply_ec_style(fig, title=None, subtitle=None, y_title=None, show_legend=True):
        """Apply Electric Capital chart styling to a plotly figure."""
        title_text = ""
        if title:
            title_text = f"<b>{title}</b>"
            if subtitle:
                title_text += f"<br><span style='font-size:14px;color:#666666'>{subtitle}</span>"

        fig.update_layout(
            title=dict(
                text=title_text,
                font=dict(size=20, color="#1B4F72", family="Arial, sans-serif"),
                x=0, xanchor="left", y=0.95, yanchor="top"
            ) if title else None,
            template='plotly_white',
            font=dict(family="Arial, sans-serif", size=12, color="#333"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(t=100 if title else 40, l=70, r=40, b=60),
            hovermode='x unified',
            showlegend=show_legend,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1, bgcolor="rgba(255,255,255,0.8)"
            )
        )
        fig.update_xaxes(
            showgrid=False, showline=True,
            linecolor="#CCCCCC", linewidth=1,
            tickfont=dict(size=11, color="#666"),
            title="", tickformat="%b %Y"
        )
        fig.update_yaxes(
            showgrid=True, gridcolor="#E8E8E8", gridwidth=1,
            showline=True, linecolor="#CCCCCC", linewidth=1,
            tickfont=dict(size=11, color="#666"),
            title=y_title or "",
            title_font=dict(size=12, color="#666"),
            tickformat=",d"
        )
        return fig
    return (apply_ec_style,)


@app.cell(hide_code=True)
def _():
    EC_COLORS = {
        'light_blue': '#7EB8DA',
        'light_blue_fill': 'rgba(126, 184, 218, 0.4)',
        'dark_blue': '#1B4F72',
        'medium_blue': '#5499C7',
        'orange': '#F5B041',
    }

    TENURE_COLORS = {
        "Newcomers": "#B5D5E8",
        "Emerging": "#5DADE2",
        "Established": "#1B4F72",
    }

    ACTIVITY_COLORS = {
        "Full-time": "#5DADE2",
        "Part-time": "#EC7063",
        "One-time": "#F5B041",
    }
    return EC_COLORS, TENURE_COLORS, ACTIVITY_COLORS


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.graph_objects as go
    return pd, go


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
