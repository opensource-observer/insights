import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.vstack([
        mo.md(r"""# Developer Retention Dashboard"""),
        mo.md(r"""
        Comprehensive retention analysis by ecosystem and cohort year. This dashboard helps answer:

        - What percentage of developers who joined in Year X are still active after N years?
        - Is retention improving or declining over time?
        - How does our ecosystem compare to others?

        **Methodology**: Retention is calculated as the percentage of developers from a cohort
        (defined by first contribution date) who remain active in subsequent periods.
        """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Ecosystem & Cohort Selection""")
    return


@app.cell(hide_code=True)
def _(mo):
    ecosystem_selector = mo.ui.dropdown(
        options=["Ethereum", "Solana", "Optimism", "Arbitrum", "Base", "Polygon", "AI"],
        value="Ethereum",
        label="Select Ecosystem"
    )

    cohort_years = mo.ui.multiselect(
        options=["2020", "2021", "2022", "2023", "2024", "2025"],
        value=["2021", "2022", "2023", "2024"],
        label="Cohort Years to Display"
    )

    mo.hstack([ecosystem_selector, cohort_years], justify="start", gap=2)
    return cohort_years, ecosystem_selector


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Retention Curves by Cohort Year""")
    return


@app.cell(hide_code=True)
def _(client, cohort_years, ecosystem_selector, mo, px):
    cohort_list = ", ".join([f"'{y}'" for y in cohort_years.value])

    sql_retention_curves = f"""
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            EXTRACT(YEAR FROM MIN(rda.day))::INT AS cohort_year,
            MIN(rda.day) AS first_active_date
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{ecosystem_selector.value}'
        GROUP BY 1
    ),

    cohort_sizes AS (
        SELECT
            cohort_year,
            COUNT(*) AS cohort_size
        FROM first_activity
        WHERE cohort_year::TEXT IN ({cohort_list})
        GROUP BY 1
    ),

    yearly_activity AS (
        SELECT DISTINCT
            fa.canonical_developer_id,
            fa.cohort_year,
            EXTRACT(YEAR FROM rda.day)::INT AS activity_year
        FROM first_activity fa
        JOIN stg_opendevdata__repo_developer_28d_activities rda
            ON fa.canonical_developer_id = rda.canonical_developer_id
        JOIN stg_opendevdata__ecosystems_repos_recursive err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{ecosystem_selector.value}'
            AND fa.cohort_year::TEXT IN ({cohort_list})
    ),

    retention_data AS (
        SELECT
            ya.cohort_year,
            ya.activity_year - ya.cohort_year AS years_since_join,
            COUNT(DISTINCT ya.canonical_developer_id) AS active_count
        FROM yearly_activity ya
        GROUP BY 1, 2
    )

    SELECT
        rd.cohort_year,
        rd.years_since_join,
        rd.active_count,
        cs.cohort_size,
        ROUND(100.0 * rd.active_count / cs.cohort_size, 1) AS retention_rate
    FROM retention_data rd
    JOIN cohort_sizes cs
        ON rd.cohort_year = cs.cohort_year
    WHERE rd.years_since_join >= 0
        AND rd.years_since_join <= 5
    ORDER BY rd.cohort_year, rd.years_since_join
    """

    df_curves = client.to_pandas(sql_retention_curves)
    df_curves['cohort_label'] = df_curves['cohort_year'].astype(str) + ' Cohort'

    _fig = px.line(
        df_curves,
        x='years_since_join',
        y='retention_rate',
        color='cohort_label',
        title=f'{ecosystem_selector.value} Developer Retention by Cohort Year',
        labels={
            'years_since_join': 'Years After First Contribution',
            'retention_rate': 'Retention Rate (%)',
            'cohort_label': 'Cohort'
        },
        markers=True
    )
    _fig.update_layout(
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text=''
        ),
        xaxis=dict(dtick=1, range=[-0.2, 5.2]),
        yaxis=dict(range=[0, 105])
    )
    _fig.update_traces(line=dict(width=3))

    mo.vstack([
        mo.md(f"""
        **Retention curves for {ecosystem_selector.value}**

        Each line represents a cohort of developers grouped by the year they first contributed.
        - **Year 0** is always 100% (by definition, all developers were active when they joined)
        - Steeper drop-off indicates lower retention
        - Compare lines to see if retention is improving over time
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return cohort_list, df_curves, sql_retention_curves


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Key Retention Metrics""")
    return


@app.cell(hide_code=True)
def _(df_curves, ecosystem_selector, mo):
    # Calculate key metrics for display
    metrics_1yr = df_curves[df_curves['years_since_join'] == 1].copy()
    metrics_2yr = df_curves[df_curves['years_since_join'] == 2].copy()

    if len(metrics_1yr) > 0:
        avg_1yr = metrics_1yr['retention_rate'].mean()
        best_1yr = metrics_1yr.loc[metrics_1yr['retention_rate'].idxmax()]
        worst_1yr = metrics_1yr.loc[metrics_1yr['retention_rate'].idxmin()]
    else:
        avg_1yr = 0
        best_1yr = {'cohort_year': 'N/A', 'retention_rate': 0}
        worst_1yr = {'cohort_year': 'N/A', 'retention_rate': 0}

    if len(metrics_2yr) > 0:
        avg_2yr = metrics_2yr['retention_rate'].mean()
    else:
        avg_2yr = 0

    mo.vstack([
        mo.md(f"### {ecosystem_selector.value} Retention Summary"),
        mo.hstack([
            mo.stat(
                value=f"{avg_1yr:.1f}%",
                label="Avg 1-Year Retention",
                bordered=True
            ),
            mo.stat(
                value=f"{avg_2yr:.1f}%",
                label="Avg 2-Year Retention",
                bordered=True
            ),
            mo.stat(
                value=f"{best_1yr['cohort_year']}",
                label=f"Best Cohort ({best_1yr['retention_rate']:.1f}% @ 1yr)",
                bordered=True
            ),
            mo.stat(
                value=f"{worst_1yr['cohort_year']}",
                label=f"Lowest Cohort ({worst_1yr['retention_rate']:.1f}% @ 1yr)",
                bordered=True
            ),
        ], justify="start", gap=2)
    ])
    return avg_1yr, avg_2yr, best_1yr, metrics_1yr, metrics_2yr, worst_1yr


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Cohort Details Table""")
    return


@app.cell(hide_code=True)
def _(df_curves, mo, pd):
    # Pivot to create retention matrix
    retention_matrix = df_curves.pivot(
        index='cohort_year',
        columns='years_since_join',
        values='retention_rate'
    ).reset_index()

    retention_matrix.columns = ['Cohort Year'] + [f'Year {int(c)}' for c in retention_matrix.columns[1:]]

    # Add cohort size
    cohort_sizes_df = df_curves[df_curves['years_since_join'] == 0][['cohort_year', 'cohort_size']].drop_duplicates()
    retention_matrix = retention_matrix.merge(
        cohort_sizes_df,
        left_on='Cohort Year',
        right_on='cohort_year'
    )[['Cohort Year', 'cohort_size'] + [c for c in retention_matrix.columns if c.startswith('Year')]]
    retention_matrix = retention_matrix.rename(columns={'cohort_size': 'Cohort Size'})

    mo.vstack([
        mo.md("""
        **Retention matrix by cohort**

        Shows retention rates (%) at each year mark for each cohort.
        """),
        mo.ui.table(retention_matrix, selection=None)
    ])
    return cohort_sizes_df, retention_matrix


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Cross-Ecosystem Comparison""")
    return


@app.cell(hide_code=True)
def _(client, mo, px):
    sql_cross_ecosystem = """
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem,
            EXTRACT(YEAR FROM MIN(rda.day))::INT AS cohort_year,
            MIN(rda.day) AS first_active_date
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name IN ('Ethereum', 'Solana', 'Optimism')
        GROUP BY 1, 2
    ),

    cohort_sizes AS (
        SELECT
            ecosystem,
            cohort_year,
            COUNT(*) AS cohort_size
        FROM first_activity
        WHERE cohort_year = 2023
        GROUP BY 1, 2
    ),

    yearly_activity AS (
        SELECT DISTINCT
            fa.canonical_developer_id,
            fa.ecosystem,
            fa.cohort_year,
            EXTRACT(YEAR FROM rda.day)::INT AS activity_year
        FROM first_activity fa
        JOIN stg_opendevdata__repo_developer_28d_activities rda
            ON fa.canonical_developer_id = rda.canonical_developer_id
        JOIN stg_opendevdata__ecosystems_repos_recursive err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems e
            ON err.ecosystem_id = e.id
        WHERE fa.ecosystem = e.name
            AND fa.cohort_year = 2023
    ),

    retention_data AS (
        SELECT
            ya.ecosystem,
            ya.cohort_year,
            ya.activity_year - ya.cohort_year AS years_since_join,
            COUNT(DISTINCT ya.canonical_developer_id) AS active_count
        FROM yearly_activity ya
        GROUP BY 1, 2, 3
    )

    SELECT
        rd.ecosystem,
        rd.years_since_join,
        rd.active_count,
        cs.cohort_size,
        ROUND(100.0 * rd.active_count / cs.cohort_size, 1) AS retention_rate
    FROM retention_data rd
    JOIN cohort_sizes cs
        ON rd.ecosystem = cs.ecosystem
        AND rd.cohort_year = cs.cohort_year
    WHERE rd.years_since_join >= 0
        AND rd.years_since_join <= 3
    ORDER BY rd.ecosystem, rd.years_since_join
    """

    df_cross = client.to_pandas(sql_cross_ecosystem)

    _fig = px.line(
        df_cross,
        x='years_since_join',
        y='retention_rate',
        color='ecosystem',
        title='2023 Cohort Retention: Cross-Ecosystem Comparison',
        labels={
            'years_since_join': 'Years After First Contribution',
            'retention_rate': 'Retention Rate (%)',
            'ecosystem': 'Ecosystem'
        },
        markers=True,
        color_discrete_map={
            'Ethereum': '#627EEA',
            'Solana': '#9945FF',
            'Optimism': '#FF0420'
        }
    )
    _fig.update_layout(
        template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(dtick=1),
        yaxis=dict(range=[0, 105])
    )
    _fig.update_traces(line=dict(width=3))

    mo.vstack([
        mo.md("""
        **Cross-ecosystem retention comparison (2023 cohort)**

        Comparing how well different ecosystems retain developers who joined in 2023.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return df_cross, sql_cross_ecosystem


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Monthly Cohort Analysis""")
    return


@app.cell(hide_code=True)
def _(client, ecosystem_selector, mo, px):
    sql_monthly_cohorts = f"""
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

    cohort_sizes AS (
        SELECT
            cohort_month,
            COUNT(*) AS cohort_size
        FROM first_activity
        WHERE cohort_month >= DATE('2023-01-01')
            AND cohort_month <= DATE('2024-06-01')
        GROUP BY 1
    ),

    monthly_activity AS (
        SELECT DISTINCT
            fa.canonical_developer_id,
            fa.cohort_month,
            DATE_TRUNC('month', rda.day) AS activity_month
        FROM first_activity fa
        JOIN stg_opendevdata__repo_developer_28d_activities rda
            ON fa.canonical_developer_id = rda.canonical_developer_id
        JOIN stg_opendevdata__ecosystems_repos_recursive err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{ecosystem_selector.value}'
            AND fa.cohort_month >= DATE('2023-01-01')
            AND fa.cohort_month <= DATE('2024-06-01')
    ),

    retention_data AS (
        SELECT
            ma.cohort_month,
            EXTRACT(YEAR FROM AGE(ma.activity_month, ma.cohort_month)) * 12 +
            EXTRACT(MONTH FROM AGE(ma.activity_month, ma.cohort_month)) AS months_since_join,
            COUNT(DISTINCT ma.canonical_developer_id) AS active_count
        FROM monthly_activity ma
        GROUP BY 1, 2
    )

    SELECT
        rd.cohort_month,
        rd.months_since_join,
        rd.active_count,
        cs.cohort_size,
        ROUND(100.0 * rd.active_count / cs.cohort_size, 1) AS retention_rate
    FROM retention_data rd
    JOIN cohort_sizes cs
        ON rd.cohort_month = cs.cohort_month
    WHERE rd.months_since_join >= 0
        AND rd.months_since_join <= 12
    ORDER BY rd.cohort_month, rd.months_since_join
    """

    df_monthly = client.to_pandas(sql_monthly_cohorts)

    # Select a few cohorts for visualization
    selected = ['2023-01-01', '2023-07-01', '2024-01-01']
    df_monthly_filtered = df_monthly[df_monthly['cohort_month'].astype(str).str[:10].isin(selected)].copy()
    df_monthly_filtered['cohort_label'] = df_monthly_filtered['cohort_month'].astype(str).str[:7]

    _fig = px.line(
        df_monthly_filtered,
        x='months_since_join',
        y='retention_rate',
        color='cohort_label',
        title=f'{ecosystem_selector.value} Monthly Cohort Retention',
        labels={
            'months_since_join': 'Months Since First Contribution',
            'retention_rate': 'Retention Rate (%)',
            'cohort_label': 'Cohort Month'
        },
        markers=True
    )
    _fig.update_layout(
        template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(dtick=1),
        yaxis=dict(range=[0, 105])
    )

    mo.vstack([
        mo.md(f"""
        **Monthly cohort retention for {ecosystem_selector.value}**

        More granular view showing month-by-month retention curves.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return df_monthly, df_monthly_filtered, selected, sql_monthly_cohorts


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Retention Benchmarks""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Industry Comparison

    How does open source developer retention compare to other contexts?

    | Timeframe | Typical SaaS | Mobile Apps | Gaming | Open Source | Strong OSS Ecosystem |
    |-----------|--------------|-------------|--------|-------------|---------------------|
    | 1 month | 80% | 25% | 40% | 50% | 65-75% |
    | 3 months | 60% | 12% | 20% | 35% | 50-60% |
    | 6 months | 40% | 6% | 15% | 25% | 40-50% |
    | 12 months | 25% | 3% | 8% | 15% | 25-35% |

    **Interpretation:**
    - Open source has naturally lower retention than SaaS (no payment commitment)
    - Strong ecosystems with good onboarding show significantly better retention
    - First 90 days are critical for long-term retention

    ### Factors Affecting Retention

    | Factor | Impact |
    |--------|--------|
    | **Onboarding experience** | High - clear contribution paths improve retention |
    | **Community responsiveness** | High - quick PR reviews and welcoming culture |
    | **Documentation quality** | Medium - reduces friction for new contributors |
    | **Funding/incentives** | Medium - grants and retrospective funding |
    | **Project momentum** | Medium - active projects attract ongoing contribution |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Methodology""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### How Retention is Calculated

    1. **Cohort Assignment**: Each developer is assigned to a cohort based on their first
       contribution date to the ecosystem
    2. **Activity Tracking**: We track whether the developer had any activity in subsequent
       time periods (months or years)
    3. **Retention Rate**: The percentage of the original cohort that remains active

    ### Data Sources

    - **Primary**: `stg_opendevdata__repo_developer_28d_activities` (Electric Capital data)
    - **Ecosystem mapping**: `stg_opendevdata__ecosystems_repos_recursive`
    - **Activity definition**: Any commit to a mapped repository

    ### Limitations

    1. **Multi-ecosystem developers**: A developer may churn from one ecosystem but remain
       active in another; we track per-ecosystem retention
    2. **Identity resolution**: Based on Electric Capital's developer fingerprinting
    3. **Recent cohorts**: Newer cohorts have less retention history to analyze

    ### Related Resources

    - [Retention Metric Definition](../data/metric-definitions/retention.py)
    - [Developer Lifecycle](../data/metric-definitions/lifecycle.py)
    - [Activity Metric Definition](../data/metric-definitions/activity.py)
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
