import marimo

__generated_with = "unknown"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Retention

    The **retention metric** measures what percentage of developers who joined an ecosystem in a given
    cohort remain active over time. It answers: "Of developers who first contributed in Month X, how many
    are still active N months later?"

    **Preview:**
    ```sql
    SELECT
      cohort_month,
      months_since_cohort,
      active_count,
      cohort_size,
      retention_rate
    FROM oso.stg_opendevdata__repo_developer_28d_activities
    LIMIT 5
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""## Definition & Formula""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Retention Calculation

    For each (developer, ecosystem) pair:

    1. **Month 0** = The month of first observed contribution to the ecosystem
    2. **Month N** = N months after Month 0
    3. **Active in Month N** = Developer had at least one qualifying activity in that month

    **Retention Rate Formula:**

    ```
    Retention(cohort, month_N) = Active_in_month_N(cohort) / Cohort_size × 100%
    ```

    **Where:**
    - `cohort` = All developers whose Month 0 was a specific month (e.g., "January 2023 cohort")
    - `Active_in_month_N(cohort)` = Count of cohort developers with activity in Month N
    - `Cohort_size` = Total developers in the cohort

    ### Example

    If 100 developers first contributed to Ethereum in January 2023:
    - Month 0 (Jan 2023): 100 active (100% by definition)
    - Month 1 (Feb 2023): 75 active → 75% retention
    - Month 3 (Apr 2023): 50 active → 50% retention
    - Month 6 (Jul 2023): 35 active → 35% retention
    - Month 12 (Jan 2024): 25 active → 25% retention

    This creates a **retention curve** showing drop-off over time.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""## Data Models""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Underlying Tables

    | Table | Purpose |
    |:-------|:---------|
    | `stg_opendevdata__repo_developer_28d_activities` | Developer activity per repository (28-day rolling) |
    | `stg_opendevdata__ecosystems` | Ecosystem definitions |
    | `stg_opendevdata__ecosystems_repos_recursive` | Repository-to-ecosystem mapping |

    ### Derived Calculations

    **Step 1: Identify First Activity Month (Month 0)**
    ```sql
    SELECT
        canonical_developer_id,
        DATE_TRUNC('month', MIN(day)) AS cohort_month
    FROM stg_opendevdata__repo_developer_28d_activities
    -- ... join to ecosystem ...
    GROUP BY canonical_developer_id
    ```

    **Step 2: Track Monthly Activity**
    ```sql
    SELECT
        canonical_developer_id,
        DATE_TRUNC('month', day) AS activity_month,
        1 AS was_active
    FROM stg_opendevdata__repo_developer_28d_activities
    -- ... join to ecosystem ...
    GROUP BY 1, 2
    ```

    **Step 3: Calculate Retention by Cohort**
    ```sql
    SELECT
        cohort_month,
        months_since_cohort,
        COUNT(DISTINCT canonical_developer_id) AS active_count,
        cohort_size,
        ROUND(100.0 * active_count / cohort_size, 2) AS retention_rate
    FROM cohort_activity
    GROUP BY 1, 2, cohort_size
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""## Live Data Exploration""")
    return


@app.cell(hide_code=True)
def live_selector(mo):
    live_ecosystem = mo.ui.dropdown(
        options=["Ethereum", "Solana", "Optimism", "Arbitrum", "Base", "Polygon"],
        value="Ethereum",
        label="Select Ecosystem"
    )
    mo.hstack([live_ecosystem], justify="start")
    return (live_ecosystem,)


@app.cell(hide_code=True)
def live_stats(mo, pyoso_db_conn, live_ecosystem):
    _df_stats = mo.sql(
        f"""
        WITH first_activity AS (
            SELECT
                rda.canonical_developer_id,
                DATE_TRUNC('month', MIN(rda.day)) AS cohort_month
            FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
            JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
                ON rda.repo_id = err.repo_id
            JOIN oso.stg_opendevdata__ecosystems AS e
                ON err.ecosystem_id = e.id
            WHERE e.name = '{live_ecosystem.value}'
            GROUP BY 1
        ),
        monthly_activity AS (
            SELECT DISTINCT
                rda.canonical_developer_id,
                DATE_TRUNC('month', rda.day) AS activity_month
            FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
            JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
                ON rda.repo_id = err.repo_id
            JOIN oso.stg_opendevdata__ecosystems AS e
                ON err.ecosystem_id = e.id
            WHERE e.name = '{live_ecosystem.value}'
        ),
        cohort_sizes AS (
            SELECT cohort_month, COUNT(*) AS cohort_size
            FROM first_activity
            WHERE cohort_month = DATE_TRUNC('month', DATE_ADD('month', -13, CURRENT_DATE))
            GROUP BY 1
        ),
        cohort_activity AS (
            SELECT
                fa.cohort_month,
                DATE_DIFF('month', fa.cohort_month, ma.activity_month) AS months_since_cohort,
                COUNT(DISTINCT fa.canonical_developer_id) AS active_count
            FROM first_activity fa
            JOIN monthly_activity ma
                ON fa.canonical_developer_id = ma.canonical_developer_id
                AND ma.activity_month >= fa.cohort_month
            WHERE fa.cohort_month = DATE_TRUNC('month', DATE_ADD('month', -13, CURRENT_DATE))
            GROUP BY 1, 2
        )
        SELECT
            ca.months_since_cohort,
            ca.active_count,
            cs.cohort_size,
            ROUND(100.0 * ca.active_count / cs.cohort_size, 2) AS retention_rate
        FROM cohort_activity ca
        JOIN cohort_sizes cs ON ca.cohort_month = cs.cohort_month
        WHERE ca.months_since_cohort <= 12
        ORDER BY ca.months_since_cohort
        """,
        engine=pyoso_db_conn,
        output=False
    )

    if len(_df_stats) == 0:
        _ = mo.md("*No data available for this ecosystem.*")
    else:
        _cohort_size = int(_df_stats.iloc[0]['cohort_size']) if len(_df_stats) > 0 else 0
        _ret_1mo = float(_df_stats[_df_stats['months_since_cohort'] == 1]['retention_rate'].iloc[0]) if len(_df_stats[_df_stats['months_since_cohort'] == 1]) > 0 else 0
        _ret_6mo = float(_df_stats[_df_stats['months_since_cohort'] == 6]['retention_rate'].iloc[0]) if len(_df_stats[_df_stats['months_since_cohort'] == 6]) > 0 else 0
        _ret_12mo = float(_df_stats[_df_stats['months_since_cohort'] == 12]['retention_rate'].iloc[0]) if len(_df_stats[_df_stats['months_since_cohort'] == 12]) > 0 else 0

        _ = mo.hstack([
            mo.stat(label="Cohort Size", value=f"{_cohort_size:,}", bordered=True, caption="Developers in 13-month-ago cohort"),
            mo.stat(label="1-Month Retention", value=f"{_ret_1mo:.1f}%", bordered=True, caption="Active 1 month after joining"),
            mo.stat(label="6-Month Retention", value=f"{_ret_6mo:.1f}%", bordered=True, caption="Active 6 months after joining"),
            mo.stat(label="12-Month Retention", value=f"{_ret_12mo:.1f}%", bordered=True, caption="Active 12 months after joining"),
        ], widths="equal", gap=1)
    return


@app.cell(hide_code=True)
def live_chart(mo, pyoso_db_conn, live_ecosystem, apply_ec_style, EC_COLORS, pd, go):
    _df_curves = mo.sql(
        f"""
        WITH first_activity AS (
            SELECT
                rda.canonical_developer_id,
                DATE_TRUNC('month', MIN(rda.day)) AS cohort_month
            FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
            JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
                ON rda.repo_id = err.repo_id
            JOIN oso.stg_opendevdata__ecosystems AS e
                ON err.ecosystem_id = e.id
            WHERE e.name = '{live_ecosystem.value}'
            GROUP BY 1
        ),
        monthly_activity AS (
            SELECT DISTINCT
                rda.canonical_developer_id,
                DATE_TRUNC('month', rda.day) AS activity_month
            FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
            JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
                ON rda.repo_id = err.repo_id
            JOIN oso.stg_opendevdata__ecosystems AS e
                ON err.ecosystem_id = e.id
            WHERE e.name = '{live_ecosystem.value}'
        ),
        cohort_sizes AS (
            SELECT cohort_month, COUNT(*) AS cohort_size
            FROM first_activity
            WHERE cohort_month >= DATE_TRUNC('month', DATE_ADD('month', -25, CURRENT_DATE))
              AND cohort_month <= DATE_TRUNC('month', DATE_ADD('month', -13, CURRENT_DATE))
            GROUP BY 1
        ),
        cohort_activity AS (
            SELECT
                fa.cohort_month,
                DATE_DIFF('month', fa.cohort_month, ma.activity_month) AS months_since_cohort,
                COUNT(DISTINCT fa.canonical_developer_id) AS active_count
            FROM first_activity fa
            JOIN monthly_activity ma
                ON fa.canonical_developer_id = ma.canonical_developer_id
                AND ma.activity_month >= fa.cohort_month
            WHERE fa.cohort_month >= DATE_TRUNC('month', DATE_ADD('month', -25, CURRENT_DATE))
              AND fa.cohort_month <= DATE_TRUNC('month', DATE_ADD('month', -13, CURRENT_DATE))
            GROUP BY 1, 2
        )
        SELECT
            ca.cohort_month,
            ca.months_since_cohort,
            ca.active_count,
            cs.cohort_size,
            ROUND(100.0 * ca.active_count / cs.cohort_size, 2) AS retention_rate
        FROM cohort_activity ca
        JOIN cohort_sizes cs ON ca.cohort_month = cs.cohort_month
        WHERE ca.months_since_cohort <= 12
        ORDER BY ca.cohort_month, ca.months_since_cohort
        """,
        engine=pyoso_db_conn,
        output=False
    )

    if len(_df_curves) == 0:
        _ = mo.md("*No data available for this ecosystem.*")
    else:
        _df_curves['cohort_label'] = pd.to_datetime(_df_curves['cohort_month']).dt.strftime('%b %Y')
        _palette = [EC_COLORS['light_blue'], EC_COLORS['medium_blue'], EC_COLORS['dark_blue'],
                    EC_COLORS['orange'], '#7FB3D3']

        _fig = go.Figure()
        for _i, _cohort in enumerate(_df_curves['cohort_label'].unique()):
            _subset = _df_curves[_df_curves['cohort_label'] == _cohort]
            _fig.add_trace(go.Scatter(
                x=_subset['months_since_cohort'],
                y=_subset['retention_rate'],
                mode='lines+markers',
                name=_cohort,
                line=dict(color=_palette[_i % len(_palette)], width=2),
                marker=dict(size=6)
            ))

        apply_ec_style(
            _fig,
            title=f"Developer Retention Curves: {live_ecosystem.value}",
            subtitle="Percentage of cohort still active each month",
            y_title="Retention Rate (%)"
        )
        _fig.update_xaxes(tickformat="d", title="Months Since First Contribution")
        _fig.update_yaxes(range=[0, 105], tickformat=".0f")

        _ = mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""## Sample Queries""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""### Query 1: Build Cohort Retention Table""")
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, ecosystem_selector):
    sql_cohort_retention = f"""
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            DATE_TRUNC('month', MIN(rda.day)) AS cohort_month
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{ecosystem_selector.value}'
        GROUP BY 1
    ),

    monthly_activity AS (
        SELECT DISTINCT
            rda.canonical_developer_id,
            DATE_TRUNC('month', rda.day) AS activity_month
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{ecosystem_selector.value}'
    ),

    cohort_sizes AS (
        SELECT
            cohort_month,
            COUNT(*) AS cohort_size
        FROM first_activity
        WHERE cohort_month >= DATE('2023-01-01')
            AND cohort_month <= DATE('2024-06-01')
        GROUP BY 1
    ),

    cohort_activity AS (
        SELECT
            fa.cohort_month,
            ma.activity_month,
            DATE_DIFF('month', fa.cohort_month, ma.activity_month) AS months_since_cohort,
            COUNT(DISTINCT fa.canonical_developer_id) AS active_count
        FROM first_activity fa
        JOIN monthly_activity ma
            ON fa.canonical_developer_id = ma.canonical_developer_id
            AND ma.activity_month >= fa.cohort_month
        WHERE fa.cohort_month >= DATE('2023-01-01')
            AND fa.cohort_month <= DATE('2024-06-01')
        GROUP BY 1, 2
    )

    SELECT
        ca.cohort_month,
        ca.months_since_cohort,
        ca.active_count,
        cs.cohort_size,
        ROUND(100.0 * ca.active_count / cs.cohort_size, 2) AS retention_rate
    FROM cohort_activity ca
    JOIN cohort_sizes cs
        ON ca.cohort_month = cs.cohort_month
    WHERE ca.months_since_cohort <= 12
    ORDER BY ca.cohort_month, ca.months_since_cohort
    """

    df_retention = mo.sql(sql_cohort_retention, engine=pyoso_db_conn, output=False)

    mo.vstack([
        mo.md(f"""
        **Cohort retention table for {ecosystem_selector.value}**

        Shows retention rates for each monthly cohort over time.
        - **cohort_month**: When developers first contributed (Month 0)
        - **months_since_cohort**: Months elapsed since Month 0
        - **retention_rate**: Percentage of cohort still active
        """),
        mo.ui.table(df_retention, selection=None, pagination=True)
    ])
    return (df_retention,)


@app.cell(hide_code=True)
def _(mo):
    ecosystem_selector = mo.ui.dropdown(
        options=["Ethereum", "Solana", "Optimism", "Arbitrum", "Base", "Polygon"],
        value="Ethereum",
        label="Select Ecosystem"
    )
    mo.hstack([ecosystem_selector], justify="start")
    return (ecosystem_selector,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""### Query 2: Retention Curves Visualization""")
    return


@app.cell(hide_code=True)
def _(df_retention, ecosystem_selector, mo, px):
    # Filter to a few cohorts for cleaner visualization
    selected_cohorts = ['2023-01-01', '2023-04-01', '2023-07-01', '2023-10-01', '2024-01-01']
    df_curves = df_retention[df_retention['cohort_month'].astype(str).str[:10].isin(selected_cohorts)]
    df_curves = df_curves.copy()
    df_curves['cohort_label'] = df_curves['cohort_month'].astype(str).str[:7]

    _fig = px.line(
        df_curves,
        x='months_since_cohort',
        y='retention_rate',
        color='cohort_label',
        title=f'Developer Retention Curves: {ecosystem_selector.value}',
        labels={
            'months_since_cohort': 'Months Since First Contribution',
            'retention_rate': 'Retention Rate (%)',
            'cohort_label': 'Cohort'
        },
        markers=True
    )
    _fig.update_layout(
        template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(dtick=1)
    )
    _fig.update_yaxes(range=[0, 105])

    mo.vstack([
        mo.md(f"""
        **Retention curves by cohort for {ecosystem_selector.value}**

        Each line represents a different cohort (grouped by first contribution month).
        - Month 0 is always 100% by definition
        - Steeper drop-off indicates lower retention
        - Compare cohorts to see if retention is improving over time
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return df_curves, selected_cohorts


@app.cell(hide_code=True)
def _(mo):
    mo.md("""### Query 3: Cross-Ecosystem Retention Comparison""")
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, px):
    sql_cross_ecosystem = """
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem,
            DATE_TRUNC('month', MIN(rda.day)) AS cohort_month
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name IN ('Ethereum', 'Solana')
        GROUP BY 1, 2
    ),

    monthly_activity AS (
        SELECT DISTINCT
            rda.canonical_developer_id,
            e.name AS ecosystem,
            DATE_TRUNC('month', rda.day) AS activity_month
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name IN ('Ethereum', 'Solana')
    ),

    cohort_sizes AS (
        SELECT
            ecosystem,
            cohort_month,
            COUNT(*) AS cohort_size
        FROM first_activity
        WHERE cohort_month = DATE('2023-01-01')
        GROUP BY 1, 2
    ),

    cohort_activity AS (
        SELECT
            fa.ecosystem,
            fa.cohort_month,
            DATE_DIFF('month', fa.cohort_month, ma.activity_month) AS months_since_cohort,
            COUNT(DISTINCT fa.canonical_developer_id) AS active_count
        FROM first_activity fa
        JOIN monthly_activity ma
            ON fa.canonical_developer_id = ma.canonical_developer_id
            AND fa.ecosystem = ma.ecosystem
            AND ma.activity_month >= fa.cohort_month
        WHERE fa.cohort_month = DATE('2023-01-01')
        GROUP BY 1, 2, ma.activity_month
    )

    SELECT
        ca.ecosystem,
        ca.months_since_cohort,
        ca.active_count,
        cs.cohort_size,
        ROUND(100.0 * ca.active_count / cs.cohort_size, 2) AS retention_rate
    FROM cohort_activity ca
    JOIN cohort_sizes cs
        ON ca.ecosystem = cs.ecosystem
        AND ca.cohort_month = cs.cohort_month
    WHERE ca.months_since_cohort <= 18
    ORDER BY ca.ecosystem, ca.months_since_cohort
    """

    df_cross = mo.sql(sql_cross_ecosystem, engine=pyoso_db_conn, output=False)

    _fig = px.line(
        df_cross,
        x='months_since_cohort',
        y='retention_rate',
        color='ecosystem',
        title='Retention Comparison: Ethereum vs Solana (Jan 2023 Cohort)',
        labels={
            'months_since_cohort': 'Months Since First Contribution',
            'retention_rate': 'Retention Rate (%)',
            'ecosystem': 'Ecosystem'
        },
        markers=True,
        color_discrete_map={'Ethereum': '#627EEA', 'Solana': '#9945FF'}
    )
    _fig.update_layout(
        template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(dtick=2)
    )
    _fig.update_yaxes(range=[0, 105])

    mo.vstack([
        mo.md("""
        **Cross-ecosystem retention comparison**

        Comparing the January 2023 cohort across Ethereum and Solana shows how different
        ecosystems retain developers over time.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return (df_cross,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Related Models

    **Metric Definitions**
    - **Activity**: [activity.py](./activity.py) — MAD metric methodology
    - **Lifecycle**: [lifecycle.py](./lifecycle.py) — Developer stage definitions
    - **Alignment**: [alignment.py](./alignment.py) — Developer ecosystem alignment

    **Data Models**
    - **Ecosystems**: [ecosystems.py](../models/ecosystems.py) — Ecosystem definitions and hierarchy
    - **Developers**: [developers.py](../models/developers.py) — Unified developer identities

    **Insights**
    - [Retention Analysis](/insights/developer-retention) — Cohort retention rates by ecosystem
    - [DeFi Developer Journeys](/insights/defi-developer-journeys) — Developer flows in DeFi
    """)
    return


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
            title=""
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
    return (EC_COLORS,)


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.graph_objects as go
    return pd, go


@app.cell(hide_code=True)
def _():
    import plotly.express as px
    return (px,)


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
