import marimo

__generated_with = "unknown"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def title_cell(mo):
    mo.md("""
    # Retention Analysis
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-02-17</span></small>

    Analyze developer retention by ecosystem and cohort year — what percentage of developers who joined in Year X are still active after N years?
    """)
    return


@app.cell(hide_code=True)
def definitions_accordion(mo):
    mo.accordion({
        "Definitions": mo.md("""
- **Cohort**: Developers grouped by the year (or month) of their first contribution to the ecosystem
- **Retention Rate**: Percentage of the original cohort that remains active in subsequent periods
- **Years Since Join**: Time elapsed since first contribution (Year 0 = joined year, always 100%)
        """),
        "Data Sources": mo.md("""
- **Primary**: `stg_opendevdata__repo_developer_28d_activities` (Electric Capital data)
- **Ecosystem mapping**: `stg_opendevdata__ecosystems_repos_recursive`
- **Activity definition**: Any commit to a mapped repository
        """),
        "Methodology": mo.md("""
1. **Cohort Assignment**: Each developer is assigned to a cohort based on their first contribution date
2. **Activity Tracking**: We track whether the developer had any activity in subsequent time periods
3. **Retention Rate**: Percentage of the original cohort that remains active

**Limitations:**
- Multi-ecosystem developers may churn from one ecosystem but remain active in another
- Identity resolution is based on Electric Capital's developer fingerprinting
- Newer cohorts have less retention history to analyze
        """),
        "Retention Benchmarks": mo.md("""
| Timeframe | Typical SaaS | Mobile Apps | Gaming | Open Source | Strong OSS Ecosystem |
|:-----------|:-------------|:------------|:-------|:------------|:---------------------|
| 1 month | 80% | 25% | 40% | 50% | 65-75% |
| 3 months | 60% | 12% | 20% | 35% | 50-60% |
| 6 months | 40% | 6% | 15% | 25% | 40-50% |
| 12 months | 25% | 3% | 8% | 15% | 25-35% |

**Key factors**: Onboarding experience, community responsiveness, documentation quality, funding/incentives, project momentum.
        """),
    })
    return


@app.cell(hide_code=True)
def test_connection(mo, pyoso_db_conn):
    _test_df = mo.sql("""SELECT 1 AS test""", engine=pyoso_db_conn, output=False)
    return


@app.cell(hide_code=True)
def section_cohort_retention(mo):
    mo.md("""
    ## Cohort Retention
    *What percentage of developers who joined in Year X are still active after N years?*
    """)
    return


@app.cell(hide_code=True)
def ecosystem_controls(mo):
    ecosystem_selector = mo.ui.dropdown(
        options=["Ethereum", "Solana", "Bitcoin", "Arbitrum", "Base", "Polygon", "AI"],
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
def query_retention_curves(cohort_years, ecosystem_selector, mo, pyoso_db_conn):
    cohort_list = ", ".join([f"'{y}'" for y in cohort_years.value])

    sql_retention_curves = f"""
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            YEAR(MIN(rda.day)) AS cohort_year,
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
        WHERE CAST(cohort_year AS VARCHAR) IN ({cohort_list})
        GROUP BY 1
    ),

    yearly_activity AS (
        SELECT DISTINCT
            fa.canonical_developer_id,
            fa.cohort_year,
            YEAR(rda.day) AS activity_year
        FROM first_activity fa
        JOIN stg_opendevdata__repo_developer_28d_activities rda
            ON fa.canonical_developer_id = rda.canonical_developer_id
        JOIN stg_opendevdata__ecosystems_repos_recursive err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{ecosystem_selector.value}'
            AND CAST(fa.cohort_year AS VARCHAR) IN ({cohort_list})
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

    df_curves = mo.sql(sql_retention_curves, engine=pyoso_db_conn, output=False)
    df_curves['retention_rate'] = df_curves['retention_rate'].astype(float)
    df_curves['years_since_join'] = df_curves['years_since_join'].astype(int)
    df_curves['cohort_label'] = df_curves['cohort_year'].astype(str) + ' Cohort'
    return (df_curves,)


@app.cell(hide_code=True)
def retention_stats(df_curves, ecosystem_selector, mo):
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

    avg_2yr = metrics_2yr['retention_rate'].mean() if len(metrics_2yr) > 0 else 0

    mo.hstack([
        mo.stat(
            value=f"{avg_1yr:.1f}%",
            label="Avg 1-Year Retention",
            bordered=True,
            caption=f"{ecosystem_selector.value} across selected cohorts"
        ),
        mo.stat(
            value=f"{avg_2yr:.1f}%",
            label="Avg 2-Year Retention",
            bordered=True,
            caption=f"{ecosystem_selector.value} across selected cohorts"
        ),
        mo.stat(
            value=f"{best_1yr['cohort_year']}",
            label="Best Cohort",
            bordered=True,
            caption=f"{best_1yr['retention_rate']:.1f}% retention at 1 year"
        ),
        mo.stat(
            value=f"{worst_1yr['cohort_year']}",
            label="Lowest Cohort",
            bordered=True,
            caption=f"{worst_1yr['retention_rate']:.1f}% retention at 1 year"
        ),
    ], widths="equal", gap=1)
    return (avg_1yr,)


@app.cell(hide_code=True)
def retention_curves_chart(apply_ec_style, avg_1yr, df_curves, ecosystem_selector, go, mo):
    _fig = go.Figure()

    _cohort_colors = ['#1B4F72', '#7EB8DA', '#5DADE2', '#A9CCE3', '#2E86C1', '#85C1E9']

    for _i, _cohort in enumerate(sorted(df_curves['cohort_label'].unique())):
        _cdf = df_curves[df_curves['cohort_label'] == _cohort]
        _fig.add_trace(go.Scatter(
            x=_cdf['years_since_join'],
            y=_cdf['retention_rate'],
            mode='lines+markers',
            name=_cohort,
            line=dict(color=_cohort_colors[_i % len(_cohort_colors)], width=2.5),
            marker=dict(size=7),
            hovertemplate=f'<b>{_cohort}</b><br>Year %{{x}}<br>Retention: %{{y:.1f}}%<extra></extra>',
        ))

    _title_rate = f"{avg_1yr:.1f}%" if avg_1yr > 0 else "N/A"
    apply_ec_style(
        _fig,
        title=f"On average, {_title_rate} of {ecosystem_selector.value} developers are still active after 1 year",
        subtitle="Annual retention rate by cohort year",
        y_title="Retention Rate (%)",
        show_legend=True,
        right_margin=60,
    )

    _fig.update_layout(height=450)
    _fig.update_xaxes(dtick=1, range=[-0.2, 5.2])
    _fig.update_yaxes(range=[0, 105], tickformat='.0f', ticksuffix='%')

    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def cohort_matrix(df_curves, mo):
    retention_matrix = df_curves.pivot(
        index='cohort_year',
        columns='years_since_join',
        values='retention_rate'
    ).reset_index()

    retention_matrix.columns = ['Cohort Year'] + [f'Year {int(c)}' for c in retention_matrix.columns[1:]]

    cohort_sizes_df = df_curves[df_curves['years_since_join'] == 0][['cohort_year', 'cohort_size']].drop_duplicates()
    retention_matrix = retention_matrix.merge(
        cohort_sizes_df,
        left_on='Cohort Year',
        right_on='cohort_year'
    )[['Cohort Year', 'cohort_size'] + [c for c in retention_matrix.columns if c.startswith('Year')]]
    retention_matrix = retention_matrix.rename(columns={'cohort_size': 'Cohort Size'})
    retention_matrix['Cohort Year'] = retention_matrix['Cohort Year'].astype(str)

    mo.vstack([
        mo.md("### Cohort Details"),
        mo.ui.table(retention_matrix, selection=None)
    ])
    return


@app.cell(hide_code=True)
def section_cross_ecosystem(mo):
    mo.md("""
    ## Cross-Ecosystem Comparison
    *How do Ethereum, Solana, and Bitcoin retain their 2023 developer cohort?*
    """)
    return


@app.cell(hide_code=True)
def query_cross_ecosystem(mo, pyoso_db_conn):
    sql_cross_ecosystem = """
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem,
            YEAR(MIN(rda.day)) AS cohort_year,
            MIN(rda.day) AS first_active_date
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name IN ('Ethereum', 'Solana', 'Bitcoin')
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
            YEAR(rda.day) AS activity_year
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

    df_cross = mo.sql(sql_cross_ecosystem, engine=pyoso_db_conn, output=False)
    df_cross['retention_rate'] = df_cross['retention_rate'].astype(float)
    df_cross['years_since_join'] = df_cross['years_since_join'].astype(int)
    return (df_cross,)


@app.cell(hide_code=True)
def cross_ecosystem_chart(apply_ec_style, df_cross, go, mo):
    _eco_colors = {
        'Ethereum': '#1B4F72',
        'Solana': '#5DADE2',
        'Bitcoin': '#E59866',
    }

    _fig = go.Figure()
    for _eco in df_cross['ecosystem'].unique():
        _edf = df_cross[df_cross['ecosystem'] == _eco]
        _fig.add_trace(go.Scatter(
            x=_edf['years_since_join'],
            y=_edf['retention_rate'],
            mode='lines+markers',
            name=_eco,
            line=dict(color=_eco_colors.get(_eco, '#888'), width=2.5),
            marker=dict(size=7),
            hovertemplate=f'<b>{_eco}</b><br>Year %{{x}}<br>Retention: %{{y:.1f}}%<extra></extra>',
        ))

    _eth_1yr = df_cross[(df_cross['ecosystem'] == 'Ethereum') & (df_cross['years_since_join'] == 1)]['retention_rate'].values
    _eth_rate = f"{_eth_1yr[0]:.0f}%" if len(_eth_1yr) > 0 else "N/A"

    apply_ec_style(
        _fig,
        title=f"Ethereum retains {_eth_rate} of 2023 developers after 1 year",
        subtitle="Cross-ecosystem retention comparison — 2023 cohort",
        y_title="Retention Rate (%)",
        show_legend=True,
        right_margin=60,
    )

    _fig.update_layout(height=400)
    _fig.update_xaxes(dtick=1)
    _fig.update_yaxes(range=[0, 105], tickformat='.0f', ticksuffix='%')

    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def section_monthly_cohorts(mo):
    mo.md("""
    ## Monthly Cohort Detail
    *Month-by-month retention curves for recent cohorts*
    """)
    return


@app.cell(hide_code=True)
def query_monthly_cohorts(ecosystem_selector, mo, pyoso_db_conn):
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
            DATE_DIFF('month', ma.cohort_month, ma.activity_month) AS months_since_join,
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

    df_monthly = mo.sql(sql_monthly_cohorts, engine=pyoso_db_conn, output=False)
    df_monthly['retention_rate'] = df_monthly['retention_rate'].astype(float)
    df_monthly['months_since_join'] = df_monthly['months_since_join'].astype(int)
    return (df_monthly,)


@app.cell(hide_code=True)
def monthly_cohorts_chart(apply_ec_style, df_monthly, ecosystem_selector, go, mo):
    _selected_months = ['2023-01-01', '2023-07-01', '2024-01-01']
    _df = df_monthly[df_monthly['cohort_month'].astype(str).str[:10].isin(_selected_months)].copy()
    _df['cohort_label'] = _df['cohort_month'].astype(str).str[:7]

    _month_colors = ['#1B4F72', '#7EB8DA', '#5DADE2']

    _fig = go.Figure()
    for _i, _cohort in enumerate(sorted(_df['cohort_label'].unique())):
        _cdf = _df[_df['cohort_label'] == _cohort]
        _fig.add_trace(go.Scatter(
            x=_cdf['months_since_join'],
            y=_cdf['retention_rate'],
            mode='lines+markers',
            name=_cohort,
            line=dict(color=_month_colors[_i % len(_month_colors)], width=2.5),
            marker=dict(size=7),
            hovertemplate=f'<b>{_cohort}</b><br>Month %{{x}}<br>Retention: %{{y:.1f}}%<extra></extra>',
        ))

    apply_ec_style(
        _fig,
        title=f"{ecosystem_selector.value} developer retention month by month",
        subtitle="Jan 2023, Jul 2023, and Jan 2024 cohorts — first 12 months",
        y_title="Retention Rate (%)",
        show_legend=True,
        right_margin=60,
    )

    _fig.update_layout(height=400)
    _fig.update_xaxes(dtick=1, tickformat='d', title='Months Since First Contribution')
    _fig.update_yaxes(range=[0, 105], tickformat='.0f', ticksuffix='%')

    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def setup_imports():
    import plotly.graph_objects as go
    return (go,)


@app.cell(hide_code=True)
def related(mo):
    mo.md("""
    ## Related

    **Metric Definitions**
    - [Retention](../data/metric-definitions/retention.py) — Cohort-based retention methodology
    - [Activity](../data/metric-definitions/activity.py) — Monthly Active Developer (MAD) methodology

    **Other Insights**
    - [2025 Developer Trends](./developer-report-2025.py)
    - [Lifecycle Analysis](./developer-lifecycle.py)
    - [DeFi Developer Journeys](./defi-developer-journeys.py)
    - [Speedrun Ethereum](./speedrun-ethereum.py)
    """)
    return


@app.cell(hide_code=True)
def helper_apply_ec_style():
    def apply_ec_style(fig, title=None, subtitle=None, y_title=None, show_legend=True, right_margin=60):
        title_text = ""
        if title:
            title_text = f"<b>{title}</b>"
            if subtitle:
                title_text += f"<br><span style='font-size:14px;color:#666666'>{subtitle}</span>"

        fig.update_layout(
            title=dict(
                text=title_text,
                font=dict(size=20, color="#1B4F72", family="Arial, sans-serif"),
                x=0,
                xanchor="left",
                y=0.95,
                yanchor="top"
            ) if title else None,
            template='plotly_white',
            font=dict(family="Arial, sans-serif", size=12, color="#333"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(t=100 if title else 40, l=70, r=right_margin, b=60),
            hovermode='x unified',
            showlegend=show_legend,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(255,255,255,0.8)"
            )
        )

        fig.update_xaxes(
            showgrid=False,
            showline=True,
            linecolor="#1F2937",
            linewidth=1,
            tickfont=dict(size=11, color="#666"),
            title=""
        )

        fig.update_yaxes(
            showgrid=True,
            gridcolor="#E5E7EB",
            gridwidth=1,
            showline=True,
            linecolor="#1F2937",
            linewidth=1,
            tickfont=dict(size=11, color="#666"),
            title=y_title if y_title else "",
            title_font=dict(size=12, color="#666"),
        )

        return fig
    return (apply_ec_style,)


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
