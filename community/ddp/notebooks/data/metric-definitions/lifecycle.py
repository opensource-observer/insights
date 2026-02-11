import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.vstack([
        mo.md(r"""# Developer Lifecycle Metric Definition"""),
        mo.md(r"""
        This notebook documents developer lifecycle stages and state transitions over time.

        The **lifecycle model** classifies developers into distinct stages based on their activity patterns.
        Each developer is assigned exactly one lifecycle stage per time period, enabling analysis of
        developer journeys, churn prediction, and ecosystem health monitoring.
        """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Lifecycle Stages""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Stage Definitions

    | Stage | Definition | Activity Threshold (28-day window) |
    |:-------|:------------|:-----------------------------------|
    | **New** | First observed contribution to ecosystem | First activity month |
    | **Full-Time Active** | High sustained activity | ≥10 active days |
    | **Part-Time Active** | Moderate sustained activity | 1-9 active days |
    | **Dormant** | Previously active, now inactive | 0 active days (1-6 months of inactivity) |
    | **Churned** | Long-term inactive | 0 active days (>6 months of inactivity) |

    ### Stage Characteristics

    **New Developer**
    - First month of any contribution to the ecosystem
    - May transition to Full-Time, Part-Time, or even Dormant based on activity
    - Important for measuring ecosystem growth and onboarding effectiveness

    **Full-Time Active Developer**
    - High engagement: ≥10 days with qualifying activity in rolling 28-day window
    - Core contributors who drive most of the ecosystem's development
    - Aligns with Electric Capital's "Full-Time Developer" classification

    **Part-Time Active Developer**
    - Moderate engagement: 1-9 days with qualifying activity in rolling 28-day window
    - May be hobbyists, consultants, or developers with multiple ecosystem commitments
    - Important segment for understanding ecosystem breadth

    **Dormant Developer**
    - No activity in recent period but was active within past 6 months
    - May return to active status (recovery is possible)
    - Early warning indicator for potential churn

    **Churned Developer**
    - No activity for >6 months
    - Unlikely to return (though some do)
    - Important for calculating churn rates and ecosystem health
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## State Transitions""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Valid State Transitions

    ```
    ┌─────────────┐
    │     NEW     │
    └──────┬──────┘
           │
           ▼
    ┌─────────────────────────────────────┐
    │                                     │
    │    ┌──────────────┐                 │
    │    │  FULL-TIME   │◄───────────────┐│
    │    │   ACTIVE     │                ││
    │    └──────┬───────┘                ││
    │           │                        ││
    │           ▼                        ││
    │    ┌──────────────┐                ││
    │    │  PART-TIME   │────────────────┘│
    │    │   ACTIVE     │                 │
    │    └──────┬───────┘                 │
    │           │                         │
    │           ▼                         │
    │    ┌──────────────┐                 │
    │    │   DORMANT    │─────────────────┤
    │    │ (1-6 months) │                 │
    │    └──────┬───────┘                 │
    │           │                         │
    │           ▼                         │
    │    ┌──────────────┐                 │
    │    │   CHURNED    │                 │
    │    │  (>6 months) │                 │
    │    └──────────────┘                 │
    │                                     │
    └─────────────────────────────────────┘
    ```

    ### Transition Rules

    | From State | To State | Trigger |
    |:------------|:----------|:---------|
    | New | Full-Time Active | ≥10 active days in next period |
    | New | Part-Time Active | 1-9 active days in next period |
    | New | Dormant | 0 active days in next period |
    | Full-Time Active | Part-Time Active | <10 active days |
    | Part-Time Active | Full-Time Active | ≥10 active days |
    | Full-Time/Part-Time | Dormant | 0 active days |
    | Dormant | Full-Time/Part-Time | Any activity resumes |
    | Dormant | Churned | >6 months of inactivity |
    | Churned | Full-Time/Part-Time | Activity resumes (rare) |
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
    |:-------|:---------|
    | `stg_opendevdata__repo_developer_28d_activities` | Developer activity per repository (28-day rolling) |
    | `stg_opendevdata__ecosystems` | Ecosystem definitions |
    | `stg_opendevdata__ecosystems_repos_recursive` | Repository-to-ecosystem mapping |

    ### Derived Fields for Lifecycle

    ```sql
    -- Activity days calculation for lifecycle stage
    CASE
        WHEN active_days >= 10 THEN 'full_time_active'
        WHEN active_days >= 1 THEN 'part_time_active'
        WHEN months_since_last_activity <= 6 THEN 'dormant'
        ELSE 'churned'
    END AS lifecycle_stage
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Sample Queries""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Query 1: Lifecycle Stage Distribution for Ecosystem""")
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, ecosystem_filter):
    sql_lifecycle_distribution = f"""
    WITH developer_activity AS (
        SELECT
            rda.canonical_developer_id,
            rda.day,
            COUNT(DISTINCT rda.day) AS active_days
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{ecosystem_filter.value}'
            AND rda.day >= DATE('2025-01-01')
            AND rda.day <= DATE('2025-01-15')
        GROUP BY 1, 2
    ),

    lifecycle_stages AS (
        SELECT
            canonical_developer_id,
            CASE
                WHEN active_days >= 10 THEN 'Full-Time Active'
                WHEN active_days >= 1 THEN 'Part-Time Active'
                ELSE 'Inactive'
            END AS lifecycle_stage
        FROM developer_activity
        WHERE day = DATE('2025-01-15')
    )

    SELECT
        lifecycle_stage,
        COUNT(*) AS developer_count,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentage
    FROM lifecycle_stages
    GROUP BY lifecycle_stage
    ORDER BY
        CASE lifecycle_stage
            WHEN 'Full-Time Active' THEN 1
            WHEN 'Part-Time Active' THEN 2
            ELSE 3
        END
    """

    df_lifecycle_dist = mo.sql(sql_lifecycle_distribution, engine=pyoso_db_conn, output=False)

    mo.vstack([
        mo.md(f"""
        **Lifecycle stage distribution for {ecosystem_filter.value}** (as of 2025-01-15)
        """),
        mo.ui.table(df_lifecycle_dist, selection=None)
    ])
    return (df_lifecycle_dist,)


@app.cell(hide_code=True)
def _(mo):
    ecosystem_filter = mo.ui.dropdown(
        options=["Ethereum", "Solana", "Optimism", "Arbitrum", "Base", "Polygon"],
        value="Ethereum",
        label="Select Ecosystem"
    )
    mo.hstack([ecosystem_filter], justify="start")
    return (ecosystem_filter,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Query 2: Lifecycle Stage Trends Over Time""")
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, ecosystem_filter, px):
    sql_lifecycle_trend = f"""
    WITH monthly_activity AS (
        SELECT
            rda.canonical_developer_id,
            DATE_TRUNC('month', rda.day) AS month,
            COUNT(DISTINCT rda.day) AS active_days
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{ecosystem_filter.value}'
            AND rda.day >= DATE('2024-01-01')
        GROUP BY 1, 2
    ),

    lifecycle_stages AS (
        SELECT
            canonical_developer_id,
            month,
            CASE
                WHEN active_days >= 10 THEN 'Full-Time Active'
                ELSE 'Part-Time Active'
            END AS lifecycle_stage
        FROM monthly_activity
    )

    SELECT
        month,
        lifecycle_stage,
        COUNT(*) AS developer_count
    FROM lifecycle_stages
    GROUP BY 1, 2
    ORDER BY month, lifecycle_stage
    """

    df_lifecycle_trend = mo.sql(sql_lifecycle_trend, engine=pyoso_db_conn, output=False)

    _fig = px.area(
        df_lifecycle_trend,
        x='month',
        y='developer_count',
        color='lifecycle_stage',
        title=f'Lifecycle Stage Distribution Over Time: {ecosystem_filter.value}',
        labels={'month': 'Month', 'developer_count': 'Developers', 'lifecycle_stage': 'Stage'},
        color_discrete_map={
            'Full-Time Active': '#2E86AB',
            'Part-Time Active': '#A23B72'
        }
    )
    _fig.update_layout(
        template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    mo.vstack([
        mo.md(f"""
        **Lifecycle stage trends for {ecosystem_filter.value}**

        Shows how the composition of active developers changes over time.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return (df_lifecycle_trend,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Query 3: New Developer Onboarding""")
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, ecosystem_filter, px):
    sql_new_developers = f"""
    WITH first_activity AS (
        SELECT
            rda.canonical_developer_id,
            MIN(rda.day) AS first_active_day
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = '{ecosystem_filter.value}'
        GROUP BY 1
    )

    SELECT
        DATE_TRUNC('month', first_active_day) AS cohort_month,
        COUNT(*) AS new_developers
    FROM first_activity
    WHERE first_active_day >= DATE('2023-01-01')
    GROUP BY 1
    ORDER BY 1
    """

    df_new_devs = mo.sql(sql_new_developers, engine=pyoso_db_conn, output=False)

    _fig = px.bar(
        df_new_devs,
        x='cohort_month',
        y='new_developers',
        title=f'New Developer Onboarding: {ecosystem_filter.value}',
        labels={'cohort_month': 'Month', 'new_developers': 'New Developers'}
    )
    _fig.update_layout(
        template='plotly_white',
        showlegend=False
    )

    mo.vstack([
        mo.md(f"""
        **New developers joining {ecosystem_filter.value} by month**

        A "new developer" is one whose first observed contribution to the ecosystem occurred in that month.
        """),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
        mo.ui.table(df_new_devs.tail(12), selection=None)
    ])
    return (df_new_devs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### Query 4: State Transition Analysis""")
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    sql_transitions = """
    WITH monthly_activity AS (
        SELECT
            rda.canonical_developer_id,
            DATE_TRUNC('month', rda.day) AS month,
            COUNT(DISTINCT rda.day) AS active_days
        FROM stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
            AND rda.day >= DATE('2024-10-01')
        GROUP BY 1, 2
    ),

    lifecycle_with_lag AS (
        SELECT
            canonical_developer_id,
            month,
            CASE
                WHEN active_days >= 10 THEN 'Full-Time'
                ELSE 'Part-Time'
            END AS current_stage,
            LAG(CASE
                WHEN active_days >= 10 THEN 'Full-Time'
                ELSE 'Part-Time'
            END) OVER (PARTITION BY canonical_developer_id ORDER BY month) AS prev_stage
        FROM monthly_activity
    )

    SELECT
        prev_stage AS from_stage,
        current_stage AS to_stage,
        COUNT(*) AS transition_count
    FROM lifecycle_with_lag
    WHERE prev_stage IS NOT NULL
        AND prev_stage != current_stage
    GROUP BY 1, 2
    ORDER BY transition_count DESC
    """

    df_transitions = mo.sql(sql_transitions, engine=pyoso_db_conn, output=False)

    mo.vstack([
        mo.md("""
        **State transitions for Ethereum** (Oct 2024 - Present)

        Shows how many developers transitioned between lifecycle stages.
        """),
        mo.ui.table(df_transitions, selection=None)
    ])
    return (df_transitions,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Example Use Cases""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Use Case 1: Find Developers at Risk of Churning

    Identify developers who recently became dormant (early intervention opportunity):

    ```sql
    WITH current_inactive AS (
        SELECT canonical_developer_id
        FROM developer_activity
        WHERE month = CURRENT_DATE - INTERVAL '1 month'
            AND active_days = 0
    ),
    recently_active AS (
        SELECT canonical_developer_id
        FROM developer_activity
        WHERE month BETWEEN CURRENT_DATE - INTERVAL '4 months'
                        AND CURRENT_DATE - INTERVAL '2 months'
            AND active_days > 0
    )
    SELECT *
    FROM current_inactive
    INTERSECT
    SELECT * FROM recently_active
    ```

    ### Use Case 2: Measure Full-Time to Part-Time Transition Rate

    ```sql
    SELECT
        month,
        SUM(CASE WHEN prev_stage = 'Full-Time' AND current_stage = 'Part-Time' THEN 1 ELSE 0 END) AS ft_to_pt,
        SUM(CASE WHEN prev_stage = 'Part-Time' AND current_stage = 'Full-Time' THEN 1 ELSE 0 END) AS pt_to_ft
    FROM lifecycle_with_lag
    GROUP BY month
    ORDER BY month
    ```

    ### Use Case 3: Developer Journey Analysis

    Track a specific developer's lifecycle journey:

    ```sql
    SELECT
        month,
        active_days,
        lifecycle_stage,
        LAG(lifecycle_stage) OVER (ORDER BY month) AS previous_stage
    FROM developer_lifecycle
    WHERE canonical_developer_id = 'developer_123'
    ORDER BY month
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
    ### Threshold Justification

    | Threshold | Value | Rationale |
    |:-----------|:-------|:-----------|
    | Full-Time threshold | 10 days | Aligns with Electric Capital methodology; ~2+ days/week |
    | Dormant period | 1-6 months | Balances false positives with early detection |
    | Churned period | >6 months | Industry standard for "lost" users |

    ### Limitations

    1. **Activity Types**: Currently uses commits only; PRs, issues, reviews not included
    2. **Multi-Ecosystem**: Developer may be Full-Time in Ecosystem A but Part-Time in Ecosystem B
    3. **Seasonal Effects**: Some developers have cyclical patterns (academic schedules, etc.)
    4. **New vs Returning**: First activity in an ecosystem may not be developer's first open source contribution

    ### Comparison to Electric Capital

    | Aspect | OSO Lifecycle | Electric Capital |
    |:--------|:---------------|:------------------|
    | Full-Time threshold | 10 days/28-day window | 10 days/28-day window |
    | Part-Time threshold | 1-9 days/28-day window | <10 days/28-day window |
    | One-Time tracking | Via dormant/churned | 84-day rolling window |
    | Identity resolution | GitHub actor_id | Cross-email fingerprinting |
    """)
    return


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.express as px
    return pd, px


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
