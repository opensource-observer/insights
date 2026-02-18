import marimo

__generated_with = "unknown"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Lifecycle

    The **lifecycle metric** classifies developers into stages based on their activity patterns, enabling analysis of developer journeys, churn prediction, and ecosystem health monitoring.

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
      m.devs_2y_plus AS established
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

    Every developer in an ecosystem follows a lifecycle — they arrive, contribute at varying intensity, and eventually slow down or leave. The lifecycle model captures this journey by assigning each developer to one of five stages based on their recent activity:

    - **New** → **Active** (full-time or part-time) → **Dormant** → **Churned**

    Tracking these stages over time reveals whether an ecosystem is growing (more new developers than churned), healthy (strong full-time core), or at risk (rising dormancy).

    The underlying data comes from `oso.stg_opendevdata__eco_mads`, which provides pre-calculated daily snapshots per ecosystem including activity-level and tenure breakdowns.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Stage Definitions

    | Stage | Definition | Threshold |
    |:------|:-----------|:----------|
    | **New** | First observed contribution to crypto | First activity in any ecosystem |
    | **Full-Time Active** | High sustained activity | ≥10 active days per rolling 28-day window |
    | **Part-Time Active** | Moderate or intermittent activity | 1-9 active days per rolling 28-day window |
    | **Dormant** | Previously active, now inactive | 0 active days for 1-6 months |
    | **Churned** | Long-term inactive | 0 active days for >6 months |

    Activity levels (full-time, part-time, one-time) are assessed over an 84-day rolling window per Electric Capital's methodology. The "new" designation uses the tenure dimension — developers with <1 year in crypto (`devs_0_1y`) are newcomers.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## State Transitions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.mermaid("""
    graph LR
        NEW["🆕 New<br/><small>First contribution</small>"] --> FT["💼 Full-Time<br/><small>≥10 days / 28d</small>"]
        NEW --> PT["🔧 Part-Time<br/><small>1-9 days / 28d</small>"]
        FT <-->|"activity changes"| PT
        FT -->|"stops contributing"| DORMANT["💤 Dormant<br/><small>1-6 months inactive</small>"]
        PT -->|"stops contributing"| DORMANT
        DORMANT -->|"resumes activity"| FT
        DORMANT -->|"resumes activity"| PT
        DORMANT -->|">6 months"| CHURNED["🚪 Churned<br/><small>>6 months inactive</small>"]
        CHURNED -.->|"rare return"| FT
        CHURNED -.->|"rare return"| PT
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Transition Rules

    | From | To | Trigger |
    |:-----|:---|:--------|
    | New | Full-Time / Part-Time | Continues contributing after first period |
    | New | Dormant | No activity after initial contribution |
    | Full-Time | Part-Time | Activity drops below 10 days / 28d |
    | Part-Time | Full-Time | Activity rises to ≥10 days / 28d |
    | Full-Time / Part-Time | Dormant | 0 active days |
    | Dormant | Full-Time / Part-Time | Any activity resumes |
    | Dormant | Churned | >6 months of continuous inactivity |
    | Churned | Full-Time / Part-Time | Activity resumes (rare) |
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
        value="Last 5 Years",
        label="Time Range"
    )
    mo.hstack([ecosystem_dropdown, time_range], gap=2)
    return ecosystem_dropdown, time_range


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, pd, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    df_lifecycle = mo.sql(
        f"""
        SELECT
          m.day,
          m.all_devs,
          m.full_time_devs,
          m.part_time_devs,
          m.one_time_devs,
          m.devs_0_1y AS newcomers,
          m.devs_1_2y AS emerging,
          m.devs_2y_plus AS established
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
    df_lifecycle['day'] = pd.to_datetime(df_lifecycle['day'])
    return (df_lifecycle,)


@app.cell(hide_code=True)
def _(mo, df_lifecycle, pd, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    _current = df_lifecycle.iloc[-1]
    _current_date = _current['day']
    _mad = int(_current['all_devs'])
    _ft = int(_current['full_time_devs'])
    _pt = int(_current['part_time_devs'])
    _ot = int(_current['one_time_devs'])
    _newcomers = int(_current['newcomers'])
    _ft_pct = (_ft / _mad * 100) if _mad > 0 else 0
    _newcomer_pct = (_newcomers / _mad * 100) if _mad > 0 else 0

    _year_ago = _current_date - pd.DateOffset(years=1)
    _year_ago_df = df_lifecycle[df_lifecycle['day'] <= _year_ago]
    if len(_year_ago_df) > 0:
        _prev_ft = int(_year_ago_df.iloc[-1]['full_time_devs'])
        _ft_yoy = ((_ft - _prev_ft) / _prev_ft * 100) if _prev_ft > 0 else 0
        _ft_caption = f"{_ft_yoy:+.1f}% YoY"
    else:
        _ft_caption = "N/A"

    mo.vstack([
        mo.md(f"## {_eco} Lifecycle Overview"),
        mo.hstack([
            mo.stat(label="Full-Time Devs", value=f"{_ft:,}", bordered=True, caption=_ft_caption),
            mo.stat(label="Part-Time Devs", value=f"{_pt:,}", bordered=True, caption=f"{100 - _ft_pct - (_ot / _mad * 100 if _mad > 0 else 0):.0f}% of active"),
            mo.stat(label="One-Time Devs", value=f"{_ot:,}", bordered=True, caption="Minimal / sporadic"),
            mo.stat(label="Newcomers (<1yr)", value=f"{_newcomers:,}", bordered=True, caption=f"{_newcomer_pct:.0f}% of active devs"),
        ], widths="equal", gap=1),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Lifecycle Stage Composition

    How the mix of full-time, part-time, and one-time developers changes over time.
    A healthy ecosystem maintains a strong full-time core while attracting new part-time contributors.
    """)
    return


@app.cell(hide_code=True)
def _(mo, df_lifecycle, go, apply_ec_style, time_range, pd, ACTIVITY_COLORS, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    _df = df_lifecycle.copy()

    if time_range.value == "Last 5 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]
    elif time_range.value == "Last 3 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2022-01-01')]
    elif time_range.value == "Last Year":
        _df = _df[_df['day'] >= pd.Timestamp('2024-01-01')]

    # Calculate percentages
    _df = _df.copy()
    _df['ft_pct'] = _df['full_time_devs'] / _df['all_devs'] * 100
    _df['pt_pct'] = _df['part_time_devs'] / _df['all_devs'] * 100
    _df['ot_pct'] = _df['one_time_devs'] / _df['all_devs'] * 100

    _current = _df.iloc[-1]

    _fig = go.Figure()

    for _label, _col in [("Full-time", "ft_pct"), ("Part-time", "pt_pct"), ("One-time", "ot_pct")]:
        _fig.add_trace(go.Scatter(
            x=_df['day'], y=_df[_col],
            name=f"{_label} ({_current[_col]:.0f}%)",
            mode='lines', stackgroup='one',
            fillcolor=ACTIVITY_COLORS[_label],
            line=dict(width=0.5, color=ACTIVITY_COLORS[_label]),
            hovertemplate=f'<b>{_label}</b>: %{{y:.1f}}%<extra></extra>'
        ))

    apply_ec_style(_fig,
        title=f"{_eco} Developer Mix by Activity Level",
        subtitle="Percentage of monthly active developers in each lifecycle stage",
        y_title="% of Active Developers"
    )
    _fig.update_yaxes(ticksuffix="%", tickformat=".0f")
    _fig.update_layout(height=450)

    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### New Developer Acquisition

    The flow of newcomers (<1 year in crypto) reflects ecosystem attractiveness and onboarding health.
    Sustained newcomer flow is critical — without it, the ecosystem ages and eventually shrinks.
    """)
    return


@app.cell(hide_code=True)
def _(mo, df_lifecycle, go, apply_ec_style, time_range, pd, EC_COLORS, ecosystem_dropdown):
    _eco = ecosystem_dropdown.value
    _df = df_lifecycle.copy()

    if time_range.value == "Last 5 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]
    elif time_range.value == "Last 3 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2022-01-01')]
    elif time_range.value == "Last Year":
        _df = _df[_df['day'] >= pd.Timestamp('2024-01-01')]

    _current = _df.iloc[-1]
    _peak_idx = _df['newcomers'].idxmax()
    _peak_val = int(_df.loc[_peak_idx, 'newcomers'])
    _peak_date = _df.loc[_peak_idx, 'day']

    _fig = go.Figure()

    _fig.add_trace(go.Scatter(
        x=_df['day'], y=_df['newcomers'],
        name="Newcomers (<1yr)",
        mode='lines', fill='tozeroy',
        fillcolor=EC_COLORS['light_blue_fill'],
        line=dict(color=EC_COLORS['light_blue'], width=2),
        hovertemplate='<b>Newcomers</b>: %{y:,.0f}<extra></extra>'
    ))

    _fig.add_trace(go.Scatter(
        x=_df['day'], y=_df['established'],
        name="Established (2+yr)",
        mode='lines',
        line=dict(color=EC_COLORS['dark_blue'], width=2),
        hovertemplate='<b>Established</b>: %{y:,.0f}<extra></extra>'
    ))

    apply_ec_style(_fig,
        title=f"{_eco}: Newcomers vs Established Developers",
        subtitle="New developer acquisition compared to the established core (2+ years in crypto)",
        y_title="Developers"
    )
    _fig.update_layout(height=450)

    mo.vstack([
        mo.hstack([
            mo.stat(label="Current Newcomers", value=f"{int(_current['newcomers']):,}", bordered=True, caption="<1 year in crypto"),
            mo.stat(label="Current Established", value=f"{int(_current['established']):,}", bordered=True, caption="2+ years in crypto"),
            mo.stat(label="Peak Newcomers", value=f"{_peak_val:,}", bordered=True, caption=_peak_date.strftime('%b %Y')),
        ], widths="equal", gap=1),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Methodology

    ### Threshold Justification

    | Threshold | Value | Rationale |
    |:----------|:------|:----------|
    | Full-Time | ≥10 days / 28d window | Aligns with Electric Capital; ~2+ days/week of sustained contribution |
    | Part-Time | 1-9 days / 28d window | Regular but not intensive; hobbyists, consultants, multi-ecosystem devs |
    | One-Time | Sporadic over 84d window | Minimal engagement; may be exploring or making one-off contributions |
    | Dormant | 1-6 months inactive | Balances early detection with false positives from holidays/breaks |
    | Churned | >6 months inactive | Industry standard for "lost" users; return is rare but possible |

    ### Comparison to Electric Capital

    | Aspect | DDP Lifecycle | Electric Capital |
    |:-------|:-------------|:-----------------|
    | Full-Time threshold | 10 days / 28-day window | 10 days / 28-day window |
    | Part-Time threshold | 1-9 days / 28-day window | <10 days / 28-day window |
    | One-Time tracking | Via one_time_devs in eco_mads | 84-day rolling window |
    | Identity resolution | Canonical developer ID (ODD) | Cross-email fingerprinting |
    | Tenure segmentation | <1yr, 1-2yr, 2+yr | Same |

    ### Limitations

    | Factor | Impact |
    |:-------|:-------|
    | **Commits only** | Activity is based on commits; PRs, issues, and reviews are not counted |
    | **Multi-ecosystem** | A developer may be full-time in one ecosystem but part-time in another |
    | **Seasonal patterns** | Academic schedules, holidays, and funding cycles create natural fluctuations |
    | **Dormant/churned not in eco_mads** | The pre-calculated model only tracks currently active developers; dormant and churned developers must be derived from raw activity data |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Queries

    ### 1. Current Lifecycle Stage Distribution

    Get the latest stage breakdown for an ecosystem from the pre-calculated model.

    ```sql
    SELECT
      m.day,
      m.all_devs AS total_active,
      m.full_time_devs,
      m.part_time_devs,
      m.one_time_devs,
      ROUND(100.0 * m.full_time_devs / m.all_devs, 1) AS full_time_pct,
      ROUND(100.0 * m.part_time_devs / m.all_devs, 1) AS part_time_pct,
      ROUND(100.0 * m.one_time_devs / m.all_devs, 1) AS one_time_pct
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
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          m.day,
          m.all_devs AS total_active,
          m.full_time_devs,
          m.part_time_devs,
          m.one_time_devs,
          ROUND(100.0 * m.full_time_devs / m.all_devs, 1) AS full_time_pct,
          ROUND(100.0 * m.part_time_devs / m.all_devs, 1) AS part_time_pct,
          ROUND(100.0 * m.one_time_devs / m.all_devs, 1) AS one_time_pct
        FROM oso.stg_opendevdata__eco_mads AS m
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON m.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
        ORDER BY m.day DESC
        LIMIT 10
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 2. Developer-Level Stage Transitions

    Compute actual per-developer transitions between activity levels using raw activity data.
    This query uses a tight 2-month window for performance.

    ```sql
    WITH monthly_activity AS (
        SELECT
          rda.canonical_developer_id,
          DATE_TRUNC('month', rda.day) AS month,
          COUNT(DISTINCT rda.day) AS active_days
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
          ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
          ON err.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
          AND rda.day BETWEEN DATE '2025-01-01' AND DATE '2025-02-28'
        GROUP BY 1, 2
    ),
    with_stages AS (
        SELECT
          canonical_developer_id,
          month,
          CASE WHEN active_days >= 10 THEN 'Full-Time'
               ELSE 'Part-Time'
          END AS stage,
          LAG(CASE WHEN active_days >= 10 THEN 'Full-Time'
                   ELSE 'Part-Time'
              END) OVER (
            PARTITION BY canonical_developer_id ORDER BY month
          ) AS prev_stage
        FROM monthly_activity
    )
    SELECT
      prev_stage AS from_stage,
      stage AS to_stage,
      COUNT(*) AS transition_count
    FROM with_stages
    WHERE prev_stage IS NOT NULL
      AND prev_stage != stage
    GROUP BY 1, 2
    ORDER BY transition_count DESC
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        WITH monthly_activity AS (
            SELECT
              rda.canonical_developer_id,
              DATE_TRUNC('month', rda.day) AS month,
              COUNT(DISTINCT rda.day) AS active_days
            FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
            JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
              ON rda.repo_id = err.repo_id
            JOIN oso.stg_opendevdata__ecosystems AS e
              ON err.ecosystem_id = e.id
            WHERE e.name = 'Ethereum'
              AND rda.day BETWEEN DATE '2025-01-01' AND DATE '2025-02-28'
            GROUP BY 1, 2
        ),
        with_stages AS (
            SELECT
              canonical_developer_id,
              month,
              CASE WHEN active_days >= 10 THEN 'Full-Time'
                   ELSE 'Part-Time'
              END AS stage,
              LAG(CASE WHEN active_days >= 10 THEN 'Full-Time'
                       ELSE 'Part-Time'
                  END) OVER (
                PARTITION BY canonical_developer_id ORDER BY month
              ) AS prev_stage
            FROM monthly_activity
        )
        SELECT
          prev_stage AS from_stage,
          stage AS to_stage,
          COUNT(*) AS transition_count
        FROM with_stages
        WHERE prev_stage IS NOT NULL
          AND prev_stage != stage
        GROUP BY 1, 2
        ORDER BY transition_count DESC
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Related Models

    - **Activity**: [activity.py](./activity.py) — MAD metric with EC-style charts and data source validation
    - **Alignment**: [alignment.py](./alignment.py) — Developer ecosystem alignment metric
    - **Retention**: [retention.py](./retention.py) — Cohort-based developer retention
    - **Ecosystems**: [ecosystems.py](../models/ecosystems.py) — Ecosystem definitions and hierarchy
    - **Developers**: [developers.py](../models/developers.py) — Unified developer identities
    - **Timeseries Metrics**: [timeseries-metrics.py](../models/timeseries-metrics.py) — Aggregated time series
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

    ACTIVITY_COLORS = {
        "Full-time": "#5DADE2",
        "Part-time": "#EC7063",
        "One-time": "#F5B041",
    }
    return EC_COLORS, ACTIVITY_COLORS


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
