import marimo

__generated_with = "unknown"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Alignment

    The **alignment metric** measures how a developer's activity is distributed across ecosystems.
    It answers: "What percentage of this developer's work goes to each ecosystem?"

    **Preview:**
    ```sql
    SELECT
      canonical_developer_id,
      ecosystem_name,
      alignment_pct
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
    mo.md("""## Data Models""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Underlying Tables

    The alignment calculation relies on these key tables:

    | Table | Purpose |
    |:-------|:---------|
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
    mo.md("""## Live Data Exploration""")
    return


@app.cell(hide_code=True)
def _(mo):
    live_ecosystem = mo.ui.dropdown(
        options=["Ethereum", "Solana", "Optimism", "Arbitrum", "Base", "Polygon", "AI"],
        value="Ethereum",
        label="Select Ecosystem"
    )
    mo.hstack([live_ecosystem], justify="start")
    return (live_ecosystem,)


@app.cell(hide_code=True)
def live_stats(mo, pyoso_db_conn, live_ecosystem):
    _df_align = mo.sql(
        f"""
        WITH developer_ecosystem_activity AS (
            SELECT
                rda.canonical_developer_id,
                e.name AS ecosystem_name,
                SUM(rda.commits) AS ecosystem_commits
            FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
            JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
                ON rda.repo_id = err.repo_id
            JOIN oso.stg_opendevdata__ecosystems AS e
                ON err.ecosystem_id = e.id
            WHERE rda.day = (SELECT MAX(day) FROM oso.stg_opendevdata__repo_developer_28d_activities)
            GROUP BY 1, 2
        ),
        developer_totals AS (
            SELECT canonical_developer_id, SUM(ecosystem_commits) AS total_commits
            FROM developer_ecosystem_activity
            GROUP BY 1
        ),
        alignment AS (
            SELECT
                dea.canonical_developer_id,
                dea.ecosystem_name,
                ROUND(100.0 * dea.ecosystem_commits / dt.total_commits, 2) AS alignment_pct
            FROM developer_ecosystem_activity dea
            JOIN developer_totals dt ON dea.canonical_developer_id = dt.canonical_developer_id
            WHERE dt.total_commits >= 5
              AND dea.ecosystem_name = '{live_ecosystem.value}'
        )
        SELECT
            COUNT(*) AS total_developers,
            COUNT(CASE WHEN alignment_pct = 100 THEN 1 END) AS exclusive_developers,
            ROUND(AVG(alignment_pct), 1) AS avg_alignment_pct,
            ROUND(100.0 * COUNT(CASE WHEN alignment_pct >= 50 THEN 1 END) / COUNT(*), 1) AS pct_majority_aligned
        FROM alignment
        """,
        engine=pyoso_db_conn,
        output=False
    )

    if len(_df_align) == 0 or _df_align.iloc[0]['total_developers'] == 0:
        _ = mo.md("*No data available for this ecosystem.*")
    else:
        _row = _df_align.iloc[0]
        _ = mo.hstack([
            mo.stat(label="Active Developers", value=f"{int(_row['total_developers']):,}", bordered=True, caption=f"Contributing to {live_ecosystem.value}"),
            mo.stat(label="Exclusive (100%)", value=f"{int(_row['exclusive_developers']):,}", bordered=True, caption="Only work in this ecosystem"),
            mo.stat(label="Avg Alignment", value=f"{float(_row['avg_alignment_pct']):.1f}%", bordered=True, caption="Mean alignment percentage"),
            mo.stat(label="Majority Aligned", value=f"{float(_row['pct_majority_aligned']):.1f}%", bordered=True, caption="≥50% aligned developers"),
        ], widths="equal", gap=1)
    _
    return


@app.cell(hide_code=True)
def live_chart(mo, pyoso_db_conn, live_ecosystem, apply_ec_style, EC_COLORS):
    _df_dist = mo.sql(
        f"""
        WITH developer_ecosystem_activity AS (
            SELECT
                rda.canonical_developer_id,
                e.name AS ecosystem_name,
                SUM(rda.commits) AS ecosystem_commits
            FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
            JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
                ON rda.repo_id = err.repo_id
            JOIN oso.stg_opendevdata__ecosystems AS e
                ON err.ecosystem_id = e.id
            WHERE rda.day = (SELECT MAX(day) FROM oso.stg_opendevdata__repo_developer_28d_activities)
            GROUP BY 1, 2
        ),
        developer_totals AS (
            SELECT canonical_developer_id, SUM(ecosystem_commits) AS total_commits
            FROM developer_ecosystem_activity
            GROUP BY 1
        ),
        alignment AS (
            SELECT
                dea.canonical_developer_id,
                ROUND(100.0 * dea.ecosystem_commits / dt.total_commits, 2) AS alignment_pct
            FROM developer_ecosystem_activity dea
            JOIN developer_totals dt ON dea.canonical_developer_id = dt.canonical_developer_id
            WHERE dt.total_commits >= 5
              AND dea.ecosystem_name = '{live_ecosystem.value}'
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
        """,
        engine=pyoso_db_conn,
        output=False
    )

    if len(_df_dist) == 0:
        _ = mo.md("*No data available for this ecosystem.*")
    else:
        import plotly.graph_objects as _go
        _colors = [EC_COLORS['dark_blue'], EC_COLORS['medium_blue'], EC_COLORS['light_blue'],
                   EC_COLORS['orange'], '#B8CCE4']

        _fig = _go.Figure(_go.Bar(
            x=_df_dist['developer_count'],
            y=_df_dist['alignment_bucket'],
            orientation='h',
            marker_color=_colors[:len(_df_dist)],
            hovertemplate='%{y}: %{x:,} developers<extra></extra>'
        ))

        apply_ec_style(
            _fig,
            title=f"Developer Alignment Distribution: {live_ecosystem.value}",
            subtitle="How exclusively developers contribute to this ecosystem",
            y_title=""
        )
        _fig.update_layout(yaxis=dict(categoryorder='array', categoryarray=['1-24%', '25-49%', '50-74%', '75-99%', '100% (exclusive)']))
        _fig.update_xaxes(title="Number of Developers")

        _ = mo.ui.plotly(_fig, config={'displayModeBar': False})
    _
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""## Sample Queries""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""### Query 1: Calculate Alignment for Top Developers""")
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    sql_top_developer_alignment = """
    WITH developer_ecosystem_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem_name,
            rda.day,
            SUM(rda.commits) AS ecosystem_commits
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE rda.day = CURRENT_DATE - INTERVAL '1' DAY
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

    df_alignment = mo.sql(sql_top_developer_alignment, engine=pyoso_db_conn, output=False)

    mo.vstack([
        mo.md(f"""
        **Query**: Calculate ecosystem alignment for active developers (≥10 commits) on most recent day

        **Results**: {len(df_alignment):,} developer-ecosystem pairs
        """),
        mo.ui.table(df_alignment, selection=None, pagination=True)
    ])
    return (df_alignment,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""### Query 2: Top Developers by Ecosystem Alignment""")
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, ecosystem_selector):
    sql_top_aligned = f"""
    WITH developer_ecosystem_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem_name,
            rda.day,
            SUM(rda.commits) AS ecosystem_commits
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE rda.day = CURRENT_DATE - INTERVAL '1' DAY
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

    df_top_aligned = mo.sql(sql_top_aligned, engine=pyoso_db_conn, output=False)

    mo.vstack([
        mo.md(f"""
        **Top developers most aligned with {ecosystem_selector.value}**

        Showing developers with ≥5 commits, ranked by alignment percentage.
        """),
        mo.ui.table(df_top_aligned, selection=None, pagination=True)
    ])
    return (df_top_aligned,)


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
    mo.md("""### Query 3: Alignment Distribution for an Ecosystem""")
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn, ecosystem_selector, px):
    sql_alignment_distribution = f"""
    WITH developer_ecosystem_activity AS (
        SELECT
            rda.canonical_developer_id,
            e.name AS ecosystem_name,
            rda.day,
            SUM(rda.commits) AS ecosystem_commits
        FROM oso.stg_opendevdata__repo_developer_28d_activities AS rda
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS err
            ON rda.repo_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems AS e
            ON err.ecosystem_id = e.id
        WHERE rda.day = CURRENT_DATE - INTERVAL '1' DAY
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

    df_distribution = mo.sql(sql_alignment_distribution, engine=pyoso_db_conn, output=False)

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
    return (df_distribution,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Related Models

    **Metric Definitions**
    - **Activity**: [activity.py](./activity.py) — MAD metric methodology
    - **Lifecycle**: [lifecycle.py](./lifecycle.py) — Developer stage definitions
    - **Retention**: [retention.py](./retention.py) — Cohort-based developer retention

    **Data Models**
    - **Ecosystems**: [ecosystems.py](../models/ecosystems.py) — Ecosystem definitions and hierarchy
    - **Developers**: [developers.py](../models/developers.py) — Unified developer identities

    **Insights**
    - [DeFi Developer Journeys](../../insights/defi-developer-journeys.py) — Developer flows across ecosystems
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
    import pandas as _pd
    import plotly.express as px
    return (_pd, px)


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
