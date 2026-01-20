import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.vstack([
        mo.md(r"""# Developer Retention Metric Definition"""),
        mo.md(r"""
        This notebook documents how developer retention is measured within ecosystems.

        **Retention** measures what percentage of developers who joined in a given cohort remain
        active over time. It answers the question: "Of the developers who started contributing in
        Month X, how many are still active N months later?"

        Key properties:
        - Cohort-based analysis (group developers by first contribution month)
        - Tracks activity presence over time using OSO activity definitions
        - Enables comparison across ecosystems and time periods
        """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Definition & Formula""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
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
    mo.md(r"""## Data Models""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Underlying Tables

    | Table | Purpose |
    |-------|---------|
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
    mo.md(r"""## Sample Queries""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Query 1: Build Cohort Retention Table""")
    return


@app.cell(hide_code=True)
def _(client, ecosystem_selector, mo):
    sql_cohort_retention = f"""
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            DATE_TRUNC('month', MIN(rda.day)) AS cohort_month
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{ecosystem_selector.value}'
        GROUP BY 1
    ),

    monthly_activity AS (
        SELECT DISTINCT
            rda.canonical_developer_id,
            DATE_TRUNC('month', rda.day) AS activity_month
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
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
            EXTRACT(YEAR FROM AGE(ma.activity_month, fa.cohort_month)) * 12 +
            EXTRACT(MONTH FROM AGE(ma.activity_month, fa.cohort_month)) AS months_since_cohort,
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

    df_retention = client.to_pandas(sql_cohort_retention)

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
    return df_retention, sql_cohort_retention


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
    mo.md(r"""### Query 2: Retention Curves Visualization""")
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
    mo.md(r"""### Query 3: Cross-Ecosystem Retention Comparison""")
    return


@app.cell(hide_code=True)
def _(client, mo, px):
    sql_cross_ecosystem = """
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem,
            DATE_TRUNC('month', MIN(rda.day)) AS cohort_month
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name IN ('Ethereum', 'Solana')
        GROUP BY 1, 2
    ),

    monthly_activity AS (
        SELECT DISTINCT
            rda.canonical_developer_id,
            e.name AS ecosystem,
            DATE_TRUNC('month', rda.day) AS activity_month
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
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
            EXTRACT(YEAR FROM AGE(ma.activity_month, fa.cohort_month)) * 12 +
            EXTRACT(MONTH FROM AGE(ma.activity_month, fa.cohort_month)) AS months_since_cohort,
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

    df_cross = client.to_pandas(sql_cross_ecosystem)

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
    return df_cross, sql_cross_ecosystem


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Query 4: Retention by Cohort Year Summary""")
    return


@app.cell(hide_code=True)
def _(client, ecosystem_selector, mo):
    sql_yearly_summary = f"""
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            DATE_TRUNC('year', MIN(rda.day)) AS cohort_year
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{ecosystem_selector.value}'
        GROUP BY 1
    ),

    activity_after_6_months AS (
        SELECT DISTINCT
            fa.canonical_developer_id,
            fa.cohort_year
        FROM first_activity fa
        JOIN stg_opendevdata__repo_developer_28d_activities rda
            ON fa.canonical_developer_id = rda.canonical_developer_id
        JOIN stg_opendevdata__ecosystems_repos_recursive err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{ecosystem_selector.value}'
            AND rda.day >= fa.cohort_year + INTERVAL '6 months'
            AND rda.day < fa.cohort_year + INTERVAL '7 months'
    ),

    activity_after_12_months AS (
        SELECT DISTINCT
            fa.canonical_developer_id,
            fa.cohort_year
        FROM first_activity fa
        JOIN stg_opendevdata__repo_developer_28d_activities rda
            ON fa.canonical_developer_id = rda.canonical_developer_id
        JOIN stg_opendevdata__ecosystems_repos_recursive err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{ecosystem_selector.value}'
            AND rda.day >= fa.cohort_year + INTERVAL '12 months'
            AND rda.day < fa.cohort_year + INTERVAL '13 months'
    ),

    cohort_sizes AS (
        SELECT cohort_year, COUNT(*) AS cohort_size
        FROM first_activity
        WHERE cohort_year >= DATE('2020-01-01')
            AND cohort_year <= DATE('2023-01-01')
        GROUP BY 1
    )

    SELECT
        EXTRACT(YEAR FROM cs.cohort_year)::INT AS cohort_year,
        cs.cohort_size,
        COUNT(DISTINCT a6.canonical_developer_id) AS active_at_6mo,
        ROUND(100.0 * COUNT(DISTINCT a6.canonical_developer_id) / cs.cohort_size, 1) AS retention_6mo_pct,
        COUNT(DISTINCT a12.canonical_developer_id) AS active_at_12mo,
        ROUND(100.0 * COUNT(DISTINCT a12.canonical_developer_id) / cs.cohort_size, 1) AS retention_12mo_pct
    FROM cohort_sizes cs
    LEFT JOIN activity_after_6_months a6
        ON cs.cohort_year = a6.cohort_year
    LEFT JOIN activity_after_12_months a12
        ON cs.cohort_year = a12.cohort_year
    GROUP BY 1, cs.cohort_size
    ORDER BY 1
    """

    df_yearly = client.to_pandas(sql_yearly_summary)

    mo.vstack([
        mo.md(f"""
        **Annual cohort retention summary for {ecosystem_selector.value}**

        Shows 6-month and 12-month retention rates for each cohort year.
        """),
        mo.ui.table(df_yearly, selection=None)
    ])
    return df_yearly, sql_yearly_summary


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Example Use Cases""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Use Case 1: Measure Program Effectiveness

    Compare retention of developers who participated in an educational program vs. control group:

    ```sql
    WITH program_participants AS (
        SELECT developer_id FROM speedrun_ethereum_graduates
    ),
    control_group AS (
        SELECT developer_id FROM ethereum_developers
        WHERE developer_id NOT IN (SELECT * FROM program_participants)
    )
    -- Calculate retention for each group separately
    ```

    **Example Finding**: Speedrun Ethereum graduates show 68% retention at 6 months vs 35% for control group.

    ### Use Case 2: Identify Retention Trends

    Is ecosystem retention improving over time?

    ```sql
    SELECT
        cohort_year,
        AVG(CASE WHEN months_since_cohort = 6 THEN retention_rate END) AS avg_6mo_retention,
        AVG(CASE WHEN months_since_cohort = 12 THEN retention_rate END) AS avg_12mo_retention
    FROM cohort_retention
    GROUP BY cohort_year
    ORDER BY cohort_year
    ```

    ### Use Case 3: Benchmark Against Industry

    Compare ecosystem retention to industry benchmarks:

    | Timeframe | Typical SaaS | Gaming | Open Source | Strong OSS |
    |-----------|--------------|--------|-------------|------------|
    | 1 month | 80% | 40% | 50% | 70% |
    | 6 months | 40% | 15% | 25% | 45% |
    | 12 months | 25% | 8% | 15% | 30% |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Methodology Notes""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Retention Calculation Considerations

    | Factor | Current Approach | Alternative |
    |--------|------------------|-------------|
    | **Cohort Definition** | Month of first contribution | Could use quarter or week |
    | **Activity Threshold** | Any activity = retained | Could require minimum commits |
    | **Ecosystem Scope** | Per-ecosystem | Could be cross-ecosystem |
    | **Time Window** | Calendar month | Could use rolling windows |

    ### Known Limitations

    1. **Multi-Ecosystem Developers**: A developer may be "retained" in Ethereum but also active in Solana; we measure per-ecosystem
    2. **Seasonal Effects**: Some developers have cyclical patterns; monthly granularity may miss this
    3. **Identity Resolution**: Based on Electric Capital fingerprinting; some developers may have multiple identities
    4. **Activity Definition**: Currently uses commits only; other activity types not included

    ### Validation Approach

    To validate retention calculations:
    1. Spot-check individual developer journeys
    2. Compare aggregate retention rates to Electric Capital reports
    3. Verify Month 0 = 100% for all cohorts
    4. Ensure retention monotonically decreases or stays flat (can't increase without reactivation logic)
    """)
    return


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.express as px
    return pd, px


@app.cell(hide_code=True)
def setup_pyoso():
    import pyoso
    import marimo as mo
    import os
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    client = pyoso.Client(os.getenv("OSO_API_KEY"))
    return client, mo, os, pyoso_db_conn


if __name__ == "__main__":
    app.run()
