import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.vstack([
        mo.md(r"""# Ecosystem Alignment Metric Definition"""),
        mo.md(r"""
        This notebook documents how developer alignment with ecosystems is calculated and measured.

        **Alignment** measures how a developer's activity is distributed across ecosystems within a given
        time interval. It answers the question: "What percentage of this developer's work goes to each ecosystem?"

        Key properties:
        - Alignment percentages **must sum to 100%** per developer per time period
        - Based on commit activity across repositories mapped to ecosystems
        - Calculated using rolling 28-day windows (consistent with MAD methodology)
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
    ### Alignment Calculation

    For a given developer `d` and time period `t`, alignment to ecosystem `e` is calculated as:

    ```
    Alignment(d, e, t) = Commits_to_ecosystem_e(d, t) / Total_commits(d, t) × 100%
    ```

    **Where:**
    - `Commits_to_ecosystem_e(d, t)` = Number of commits by developer `d` to repositories in ecosystem `e` during period `t`
    - `Total_commits(d, t)` = Total commits by developer `d` across all ecosystems during period `t`

    ### Properties

    1. **Mutually Exclusive Assignment**: Each repository belongs to one or more ecosystems
    2. **Complete Coverage**: Sum of alignments equals 100% for each developer-period combination
    3. **Activity-Based**: Uses commit counts (could alternatively use commit days or other activity measures)

    ### Example

    If developer Alice made 100 commits in March 2025:
    - 70 commits to Ethereum repositories
    - 20 commits to Optimism repositories
    - 10 commits to AI repositories

    Her March 2025 alignment would be:
    - **Ethereum: 70%**
    - **Optimism: 20%**
    - **AI: 10%**
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

    The alignment calculation relies on these key tables:

    | Table | Purpose |
    |-------|---------|
    | `stg_opendevdata__repo_developer_28d_activities` | Developer commit activity per repository (28-day rolling) |
    | `stg_opendevdata__ecosystems` | Ecosystem definitions and hierarchy |
    | `stg_opendevdata__ecosystems_repos_recursive` | Maps repositories to ecosystems (including child ecosystems) |
    | `int_opendevdata__repositories_with_repo_id` | Repository ID mappings across systems |

    ### Key Fields

    - `canonical_developer_id`: Unique developer identifier (Electric Capital fingerprinted)
    - `repo_id`: Repository identifier in OpenDevData
    - `ecosystem_id`: Ecosystem identifier
    - `day`: The date of the rolling 28-day window end
    - `commits`: Number of commits in the window
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Sample Queries""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Query 1: Calculate Alignment for Top Developers""")
    return


@app.cell(hide_code=True)
def _(client, mo):
    sql_top_developer_alignment = """
    WITH developer_ecosystem_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem_name,
            rda.day,
            SUM(rda.commits) AS ecosystem_commits
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE rda.day = DATE('2025-01-15')
            AND e.name IN ('Ethereum', 'Solana', 'Optimism', 'Arbitrum', 'Base', 'AI')
        GROUP BY 1, 2, 3
    ),

    developer_totals AS (
        SELECT
            canonical_developer_id,
            day,
            SUM(ecosystem_commits) AS total_commits
        FROM developer_ecosystem_activity
        GROUP BY 1, 2
    ),

    alignment AS (
        SELECT
            dea.canonical_developer_id,
            dea.ecosystem_name,
            dea.ecosystem_commits,
            dt.total_commits,
            ROUND(100.0 * dea.ecosystem_commits / dt.total_commits, 2) AS alignment_pct
        FROM developer_ecosystem_activity dea
        JOIN developer_totals dt
            ON dea.canonical_developer_id = dt.canonical_developer_id
            AND dea.day = dt.day
        WHERE dt.total_commits >= 10
    )

    SELECT
        canonical_developer_id,
        ecosystem_name,
        ecosystem_commits,
        total_commits,
        alignment_pct
    FROM alignment
    ORDER BY total_commits DESC, alignment_pct DESC
    LIMIT 100
    """

    df_alignment = client.to_pandas(sql_top_developer_alignment)

    mo.vstack([
        mo.md(f"""
        **Query**: Calculate ecosystem alignment for active developers (≥10 commits) on 2025-01-15

        **Results**: {len(df_alignment):,} developer-ecosystem pairs
        """),
        mo.ui.table(df_alignment, selection=None, pagination=True)
    ])
    return df_alignment, sql_top_developer_alignment


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Query 2: Top Developers by Ecosystem Alignment""")
    return


@app.cell(hide_code=True)
def _(client, mo, ecosystem_selector):
    sql_top_aligned = f"""
    WITH developer_ecosystem_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem_name,
            rda.day,
            SUM(rda.commits) AS ecosystem_commits
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE rda.day = DATE('2025-01-15')
        GROUP BY 1, 2, 3
    ),

    developer_totals AS (
        SELECT
            canonical_developer_id,
            day,
            SUM(ecosystem_commits) AS total_commits
        FROM developer_ecosystem_activity
        GROUP BY 1, 2
    ),

    alignment AS (
        SELECT
            dea.canonical_developer_id,
            dea.ecosystem_name,
            dea.ecosystem_commits,
            dt.total_commits,
            ROUND(100.0 * dea.ecosystem_commits / dt.total_commits, 2) AS alignment_pct
        FROM developer_ecosystem_activity dea
        JOIN developer_totals dt
            ON dea.canonical_developer_id = dt.canonical_developer_id
            AND dea.day = dt.day
        WHERE dt.total_commits >= 5
    )

    SELECT
        canonical_developer_id,
        ecosystem_commits,
        total_commits,
        alignment_pct
    FROM alignment
    WHERE ecosystem_name = '{ecosystem_selector.value}'
    ORDER BY alignment_pct DESC, total_commits DESC
    LIMIT 50
    """

    df_top_aligned = client.to_pandas(sql_top_aligned)

    mo.vstack([
        mo.md(f"""
        **Top developers most aligned with {ecosystem_selector.value}**

        Showing developers with ≥5 commits, ranked by alignment percentage.
        """),
        mo.ui.table(df_top_aligned, selection=None, pagination=True)
    ])
    return df_top_aligned, sql_top_aligned


@app.cell(hide_code=True)
def _(mo):
    ecosystem_selector = mo.ui.dropdown(
        options=["Ethereum", "Solana", "Optimism", "Arbitrum", "Base", "Polygon", "AI"],
        value="Ethereum",
        label="Select Ecosystem"
    )
    mo.hstack([ecosystem_selector], justify="start")
    return (ecosystem_selector,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Query 3: Alignment Distribution for an Ecosystem""")
    return


@app.cell(hide_code=True)
def _(client, ecosystem_selector, mo, px):
    sql_alignment_distribution = f"""
    WITH developer_ecosystem_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem_name,
            rda.day,
            SUM(rda.commits) AS ecosystem_commits
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE rda.day = DATE('2025-01-15')
        GROUP BY 1, 2, 3
    ),

    developer_totals AS (
        SELECT
            canonical_developer_id,
            day,
            SUM(ecosystem_commits) AS total_commits
        FROM developer_ecosystem_activity
        GROUP BY 1, 2
    ),

    alignment AS (
        SELECT
            dea.canonical_developer_id,
            dea.ecosystem_name,
            ROUND(100.0 * dea.ecosystem_commits / dt.total_commits, 2) AS alignment_pct
        FROM developer_ecosystem_activity dea
        JOIN developer_totals dt
            ON dea.canonical_developer_id = dt.canonical_developer_id
            AND dea.day = dt.day
        WHERE dt.total_commits >= 5
            AND dea.ecosystem_name = '{ecosystem_selector.value}'
    )

    SELECT
        CASE
            WHEN alignment_pct = 100 THEN '100% (exclusive)'
            WHEN alignment_pct >= 75 THEN '75-99%'
            WHEN alignment_pct >= 50 THEN '50-74%'
            WHEN alignment_pct >= 25 THEN '25-49%'
            ELSE '1-24%'
        END AS alignment_bucket,
        COUNT(*) AS developer_count
    FROM alignment
    GROUP BY 1
    ORDER BY
        CASE alignment_bucket
            WHEN '100% (exclusive)' THEN 1
            WHEN '75-99%' THEN 2
            WHEN '50-74%' THEN 3
            WHEN '25-49%' THEN 4
            ELSE 5
        END
    """

    df_distribution = client.to_pandas(sql_alignment_distribution)

    _fig = px.bar(
        df_distribution,
        x='alignment_bucket',
        y='developer_count',
        title=f'Developer Alignment Distribution: {ecosystem_selector.value}',
        labels={'alignment_bucket': 'Alignment Level', 'developer_count': 'Number of Developers'}
    )
    _fig.update_layout(
        template='plotly_white',
        showlegend=False
    )

    mo.vstack([
        mo.md(f"""
        **Alignment distribution for {ecosystem_selector.value}**

        Shows how many developers fall into each alignment bucket.
        - **100% (exclusive)**: Developers who only contribute to {ecosystem_selector.value}
        - **75-99%**: Primarily {ecosystem_selector.value} with some cross-ecosystem work
        - Lower percentages indicate more distributed activity
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
        mo.ui.table(df_distribution, selection=None)
    ])
    return df_distribution, sql_alignment_distribution


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Alignment Over Time""")
    return


@app.cell(hide_code=True)
def _(client, mo, pd, px):
    sql_alignment_trend = """
    WITH developer_ecosystem_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem_name,
            DATE_TRUNC('month', rda.day) AS month,
            SUM(rda.commits) AS ecosystem_commits
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE rda.day >= DATE('2024-01-01')
            AND e.name IN ('Ethereum', 'Solana', 'AI')
        GROUP BY 1, 2, 3
    ),

    monthly_totals AS (
        SELECT
            month,
            ecosystem_name,
            SUM(ecosystem_commits) AS total_commits
        FROM developer_ecosystem_activity
        GROUP BY 1, 2
    ),

    all_ecosystems_monthly AS (
        SELECT
            month,
            SUM(total_commits) AS grand_total
        FROM monthly_totals
        GROUP BY 1
    )

    SELECT
        mt.month,
        mt.ecosystem_name,
        mt.total_commits,
        ROUND(100.0 * mt.total_commits / ae.grand_total, 2) AS share_pct
    FROM monthly_totals mt
    JOIN all_ecosystems_monthly ae
        ON mt.month = ae.month
    ORDER BY mt.month, mt.ecosystem_name
    """

    df_trend = client.to_pandas(sql_alignment_trend)

    _fig = px.area(
        df_trend,
        x='month',
        y='share_pct',
        color='ecosystem_name',
        title='Ecosystem Activity Share Over Time',
        labels={'month': 'Month', 'share_pct': 'Share of Activity (%)', 'ecosystem_name': 'Ecosystem'}
    )
    _fig.update_layout(
        template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    mo.vstack([
        mo.md("""
        **Ecosystem activity share trends**

        This shows how the relative share of developer activity shifts across ecosystems over time.
        Note: This is aggregate activity, not per-developer alignment.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return df_trend, sql_alignment_trend


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Example Use Cases""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Use Case 1: Identify Cross-Ecosystem Developers

    Find developers who work across multiple ecosystems (alignment < 100% for any single ecosystem):

    ```sql
    -- Developers with significant contributions to multiple ecosystems
    WITH alignment AS (
        -- ... alignment calculation ...
    )
    SELECT canonical_developer_id
    FROM alignment
    GROUP BY canonical_developer_id
    HAVING MAX(alignment_pct) < 80  -- No single ecosystem > 80%
    AND COUNT(DISTINCT ecosystem_name) >= 2
    ```

    ### Use Case 2: Track Developer Migration

    Identify developers whose alignment shifted over time:

    ```sql
    -- Developers who moved from Ethereum to Solana
    WITH monthly_alignment AS (
        -- ... calculate monthly alignment ...
    )
    SELECT canonical_developer_id
    FROM monthly_alignment
    WHERE ecosystem_name = 'Ethereum' AND month = '2024-01' AND alignment_pct > 70
    INTERSECT
    SELECT canonical_developer_id
    FROM monthly_alignment
    WHERE ecosystem_name = 'Solana' AND month = '2025-01' AND alignment_pct > 70
    ```

    ### Use Case 3: Ecosystem Talent Concentration

    Measure how concentrated vs distributed an ecosystem's developer base is:

    ```sql
    -- Average alignment of developers to each ecosystem
    SELECT
        ecosystem_name,
        AVG(alignment_pct) AS avg_alignment,
        COUNT(*) AS developer_count,
        COUNT(CASE WHEN alignment_pct = 100 THEN 1 END) AS exclusive_devs
    FROM alignment
    GROUP BY ecosystem_name
    ORDER BY avg_alignment DESC
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Methodology Notes""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Alignment Calculation Considerations

    | Factor | Current Approach | Alternative |
    |--------|------------------|-------------|
    | **Activity Metric** | Commit count | Could use commit days, lines of code |
    | **Time Window** | Rolling 28-day | Could use calendar month |
    | **Minimum Threshold** | 5+ commits shown | Could filter at different levels |
    | **Multi-ecosystem Repos** | Repo assigned to all applicable ecosystems | Could use primary ecosystem only |

    ### Known Limitations

    1. **Repository Mapping**: Some repositories may not be mapped to ecosystems, leading to incomplete alignment calculations
    2. **Ecosystem Overlap**: A repository can belong to multiple ecosystems (e.g., Optimism is also Ethereum), which can cause alignment percentages to exceed 100% if not handled carefully
    3. **Activity Type**: Currently uses commits only; other activity types (issues, PRs) not included
    4. **Developer Identity**: Relies on Electric Capital's developer fingerprinting for identity resolution

    ### Validation

    To validate alignment calculations:
    1. Sum of alignments per developer-period should equal 100% (±rounding)
    2. Spot-check individual developers against known contribution patterns
    3. Compare aggregate ecosystem activity to Electric Capital reports
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
