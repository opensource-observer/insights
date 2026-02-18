# Insights Notebooks Polish — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Polish five insights notebooks and four metric definition notebooks for a broader audience — adding cross-links, hiding internal tooling output, fixing style guide violations, and upgrading draft metric definitions to production quality.

**Architecture:** Each task is a targeted edit to a single file. Verification for every notebook task is `uv run marimo check <path>` (catches cycles, multiple definitions, import errors). No unit tests exist for these notebooks; marimo check is the automated gate.

**Tech Stack:** marimo (Python notebooks), Next.js (web app), TypeScript (Sidebar.tsx), plotly (charts), pyoso (database client)

**Design doc:** `docs/plans/2026-02-17-insights-notebooks-polish-design.md`

---

## Task 1: Sidebar.tsx — Add Retention to Metric Definitions nav

**Files:**
- Modify: `app/components/Sidebar.tsx:43-49`

**Step 1: Open the file and find the Metric Definitions children array**

```
Lines 45-48 currently read:
  children: [
    { label: 'Activity', href: '/data/metric-definitions/activity' },
    { label: 'Alignment', href: '/data/metric-definitions/alignment' },
    { label: 'Lifecycle', href: '/data/metric-definitions/lifecycle' },
  ],
```

**Step 2: Add Retention entry (alphabetical order between Alignment and Lifecycle)**

```typescript
children: [
  { label: 'Activity', href: '/data/metric-definitions/activity' },
  { label: 'Alignment', href: '/data/metric-definitions/alignment' },
  { label: 'Lifecycle', href: '/data/metric-definitions/lifecycle' },
  { label: 'Retention', href: '/data/metric-definitions/retention' },
],
```

**Step 3: Verify TypeScript compiles**

```bash
cd app && npx tsc --noEmit
```

Expected: No errors.

**Step 4: Commit**

```bash
git add app/components/Sidebar.tsx
git commit -m "feat(sidebar): add Retention to Metric Definitions navigation"
```

---

## Task 2: activity.py — Title badge + insights cross-links in Related Models

**Files:**
- Modify: `notebooks/data/metric-definitions/activity.py`

**Step 1: Add title badge to the header cell (lines 7-35)**

The title cell currently starts `mo.md("""` then `# Activity`. Add the badge line immediately after the `# Activity` heading:

```python
    mo.md("""
    # Activity
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-02-17</span></small>

    The **Monthly Active Developer (MAD)** metric measures...
```

**Step 2: Add insights cross-links to Related Models (lines 681-693)**

The current Related Models cell ends with:
```python
    - **Alignment**: [alignment.py](./alignment.py) — Developer ecosystem alignment metric
    - **Lifecycle**: [lifecycle.py](./lifecycle.py) — Developer lifecycle stages
    """)
```

Add an "Insights" sub-section before the closing triple-quote:
```python
    - **Alignment**: [alignment.py](./alignment.py) — Developer ecosystem alignment metric
    - **Lifecycle**: [lifecycle.py](./lifecycle.py) — Developer lifecycle stages
    - **Retention**: [retention.py](./retention.py) — Cohort-based developer retention

    **Insights**
    - [2025 Developer Trends](../../insights/developer-report-2025.py)
    - [Lifecycle Analysis](../../insights/developer-lifecycle.py)
    - [Retention Analysis](../../insights/developer-retention.py)
    - [DeFi Developer Journeys](../../insights/defi-developer-journeys.py)
    - [Speedrun Ethereum](../../insights/speedrun-ethereum.py)
    """)
```

**Step 3: Verify**

```bash
uv run marimo check notebooks/data/metric-definitions/activity.py
```

Expected: `✓ activity.py` (no errors)

**Step 4: Commit**

```bash
git add notebooks/data/metric-definitions/activity.py
git commit -m "feat(notebook): add title badge and insights cross-links to activity metric definition"
```

---

## Task 3: lifecycle.py — Title badge + insights cross-link in Related Models

**Files:**
- Modify: `notebooks/data/metric-definitions/lifecycle.py`

**Step 1: Add title badge to the header cell (lines 7-)**

Same pattern as activity.py — find `# Lifecycle` in the first `mo.md` cell and add the badge line:

```python
    mo.md("""
    # Lifecycle
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-02-17</span></small>

    The **lifecycle metric** classifies developers...
```

**Step 2: Add Lifecycle Analysis insight cross-link to Related Models (lines 517-529)**

Current Related Models ends with:
```python
    - **Timeseries Metrics**: [timeseries-metrics.py](../models/timeseries-metrics.py) — Aggregated time series
    """)
```

Append an Insights section:
```python
    - **Timeseries Metrics**: [timeseries-metrics.py](../models/timeseries-metrics.py) — Aggregated time series

    **Insights**
    - [Lifecycle Analysis](../../insights/developer-lifecycle.py) — Stage transitions and ecosystem health over time
    - [Retention Analysis](../../insights/developer-retention.py) — Cohort retention rates by ecosystem
    """)
```

**Step 3: Verify**

```bash
uv run marimo check notebooks/data/metric-definitions/lifecycle.py
```

Expected: `✓ lifecycle.py`

**Step 4: Commit**

```bash
git add notebooks/data/metric-definitions/lifecycle.py
git commit -m "feat(notebook): add title badge and insights cross-links to lifecycle metric definition"
```

---

## Task 4: retention.py (major) — Full upgrade to production quality

**Files:**
- Modify: `notebooks/data/metric-definitions/retention.py`

This is the largest task. Work through the steps in order.

### Step 4.1: Fix `__generated_with` and `r"""` strings

Change `__generated_with = "0.18.4"` → `__generated_with = "unknown"` (line 3).

Replace ALL occurrences of `r"""` with `"""` (there are ~15 occurrences throughout the file). Use find-and-replace.

### Step 4.2: Add `oso.` prefix to all SQL table references

In every SQL query string, add `oso.` prefix to these tables:
- `stg_opendevdata__repo_developer_28d_activities` → `oso.stg_opendevdata__repo_developer_28d_activities`
- `stg_opendevdata__ecosystems_repos_recursive` → `oso.stg_opendevdata__ecosystems_repos_recursive`
- `stg_opendevdata__ecosystems` → `oso.stg_opendevdata__ecosystems`

There are ~4 query cells. Use find-and-replace for each table name.

### Step 4.3: Add title badge to header cell (lines 7-24)

The header cell currently uses `mo.vstack([mo.md(r"""# Developer Retention..."""), mo.md(r"""...""")])`.

Simplify and add badge — replace the entire cell body:

```python
@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Retention
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-02-17</span></small>

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
```

### Step 4.4: Add live data exploration section

Insert a new section between the `## Data Models` section and `## Sample Queries`. The section needs three new cells: (a) a header + ecosystem selector, (b) a SQL stat query, and (c) an EC-styled chart.

Insert these three cells BEFORE the `## Sample Queries` header cell (currently at line ~124):

```python
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
        mo.md("*No data available for this ecosystem.*")
    else:
        _cohort_size = int(_df_stats.iloc[0]['cohort_size']) if len(_df_stats) > 0 else 0
        _ret_1mo = float(_df_stats[_df_stats['months_since_cohort'] == 1]['retention_rate'].iloc[0]) if len(_df_stats[_df_stats['months_since_cohort'] == 1]) > 0 else 0
        _ret_6mo = float(_df_stats[_df_stats['months_since_cohort'] == 6]['retention_rate'].iloc[0]) if len(_df_stats[_df_stats['months_since_cohort'] == 6]) > 0 else 0
        _ret_12mo = float(_df_stats[_df_stats['months_since_cohort'] == 12]['retention_rate'].iloc[0]) if len(_df_stats[_df_stats['months_since_cohort'] == 12]) > 0 else 0

        mo.hstack([
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
        mo.md("*No data available for this ecosystem.*")
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

        mo.ui.plotly(_fig, config={'displayModeBar': False})
    return
```

### Step 4.5: Fix styling of existing Query 2 retention curves chart

The existing Query 2 chart cell (around line 235) uses bare `px.line` with default plotly styling. Update it to use `apply_ec_style`. The cell signature is `def _(df_retention, ecosystem_selector, mo, px):` — update to also accept `apply_ec_style`:

```python
@app.cell(hide_code=True)
def _(df_retention, ecosystem_selector, mo, go, pd, apply_ec_style, EC_COLORS):
```

Replace the `px.line` chart with a `go.Figure` version using EC styling (same pattern as the live chart above, but drawing from `df_retention` and the existing `selected_cohorts` filter).

### Step 4.6: Add EC infrastructure cells

Add these three cells BEFORE the `setup_pyoso` cell at the bottom of the file:

```python
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
```

Note: The existing imports cell `import pandas as pd; import plotly.express as px` stays as-is since `px` may be used elsewhere. The new infrastructure cell adds `go` separately.

### Step 4.7: Add Related Models section

Add a new cell BEFORE the imports cell at the bottom:

```python
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
    - [Retention Analysis](../../insights/developer-retention.py) — Cohort retention rates by ecosystem
    - [DeFi Developer Journeys](../../insights/defi-developer-journeys.py) — Developer flows in DeFi
    """)
    return
```

### Step 4.8: Verify

```bash
uv run marimo check notebooks/data/metric-definitions/retention.py
```

Expected: `✓ retention.py`

If you get "Multiple definitions" errors, prefix any repeated variable names with `_`. If you get "Cycle detected", check that no cell references a variable defined only in a later cell that itself depends on an earlier cell.

### Step 4.9: Commit

```bash
git add notebooks/data/metric-definitions/retention.py
git commit -m "feat(notebook): upgrade retention metric definition to production quality"
```

---

## Task 5: alignment.py (major) — Full upgrade to production quality

**Files:**
- Modify: `notebooks/data/metric-definitions/alignment.py`

Same pattern as Task 4. Work through sub-steps:

### Step 5.1: Fix `__generated_with` and `r"""` strings

Change `__generated_with = "0.18.4"` → `__generated_with = "unknown"`.

Replace ALL `r"""` → `"""` throughout the file.

### Step 5.2: Add `oso.` prefix to all SQL table references

Tables to prefix:
- `stg_opendevdata__repo_developer_28d_activities` → `oso.stg_opendevdata__repo_developer_28d_activities`
- `stg_opendevdata__ecosystems_repos_recursive` → `oso.stg_opendevdata__ecosystems_repos_recursive`
- `stg_opendevdata__ecosystems` → `oso.stg_opendevdata__ecosystems`

Query 1 (line ~111) uses hardcoded `DATE('2025-01-15')` — update to `CURRENT_DATE - INTERVAL '1' DAY` for live data.
Query 2 (line ~183) also uses `DATE('2025-01-15')` — update same way.
Query 3 (line ~265) uses `DATE('2025-01-15')` — update same way.
The trend query (line ~362) uses monthly data and a date range — leave the WHERE clause as-is but fix the oso. prefix.

### Step 5.3: Add title badge to header cell (lines 7-23)

Replace the `mo.vstack([...])` title cell with a clean single `mo.md(...)`:

```python
@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Alignment
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-02-17</span></small>

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
```

### Step 5.4: Add live data exploration section

Insert three new cells BEFORE the `## Sample Queries` header cell:

```python
@app.cell(hide_code=True)
def _(mo):
    mo.md("""## Live Data Exploration""")
    return


@app.cell(hide_code=True)
def live_selector(mo):
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
            WHERE rda.day = CURRENT_DATE - INTERVAL '1' DAY
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
        mo.md("*No data available for this ecosystem.*")
    else:
        _row = _df_align.iloc[0]
        mo.hstack([
            mo.stat(label="Active Developers", value=f"{int(_row['total_developers']):,}", bordered=True, caption=f"Contributing to {live_ecosystem.value}"),
            mo.stat(label="Exclusive (100%)", value=f"{int(_row['exclusive_developers']):,}", bordered=True, caption="Only work in this ecosystem"),
            mo.stat(label="Avg Alignment", value=f"{float(_row['avg_alignment_pct']):.1f}%", bordered=True, caption="Mean alignment percentage"),
            mo.stat(label="Majority Aligned", value=f"{float(_row['pct_majority_aligned']):.1f}%", bordered=True, caption="≥50% aligned developers"),
        ], widths="equal", gap=1)
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
            WHERE rda.day = CURRENT_DATE - INTERVAL '1' DAY
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
        mo.md("*No data available for this ecosystem.*")
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

        mo.ui.plotly(_fig, config={'displayModeBar': False})
    return
```

### Step 5.5: Fix styling of existing Query 3 distribution chart (around line 265)

The existing `px.bar` chart in Query 3 uses default plotly styling. Update it to use EC colors and `apply_ec_style`. The cell should depend on `apply_ec_style` and `EC_COLORS`:

Change the cell signature from `def _(mo, pyoso_db_conn, ecosystem_selector, px):` to:
```python
def _(mo, pyoso_db_conn, ecosystem_selector, apply_ec_style, EC_COLORS):
```

Then replace the `px.bar` call with a `go.Figure` bar chart using EC styling (same pattern as `live_chart` above).

### Step 5.6: Add EC infrastructure cells

Add the same three infrastructure cells as in Task 4.6 BEFORE the `setup_pyoso` cell. Copy exactly from Task 4.6.

### Step 5.7: Add Related Models section

Add before the imports cell:

```python
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
```

### Step 5.8: Verify

```bash
uv run marimo check notebooks/data/metric-definitions/alignment.py
```

Expected: `✓ alignment.py`

### Step 5.9: Commit

```bash
git add notebooks/data/metric-definitions/alignment.py
git commit -m "feat(notebook): upgrade alignment metric definition to production quality"
```

---

## Task 6: developer-report-2025.py — Fix r""", hide test_connection, add Related footer

**Files:**
- Modify: `notebooks/insights/developer-report-2025.py`

**Step 1: Fix `r"""` in header_title cell (line 9)**

Change line 9 from:
```python
    mo.md(r"""
```
to:
```python
    mo.md("""
```

**Step 2: Hide test_connection output (lines 220-225)**

The `test_connection` cell currently ends with `mo.md(_status)` which renders text to the notebook. Remove that output line:

```python
@app.cell(hide_code=True)
def test_connection(mo, pyoso_db_conn):
    _test_df = mo.sql("""SELECT 1 AS test""", engine=pyoso_db_conn, output=False)
    return
```

(Remove both the `_status` variable and the `mo.md(_status)` call.)

**Step 3: Add Related footer cell**

Find the infrastructure section comment in the file (search for `# --- Infrastructure cells ---` or the first `@app.cell` of the infrastructure block). Add this new cell BEFORE the first infrastructure cell:

```python
@app.cell(hide_code=True)
def related(mo):
    mo.md("""
    ## Related

    **Metric Definitions**
    - [Activity](../data/metric-definitions/activity.py) — Monthly Active Developer (MAD) methodology

    **Other Insights**
    - [Lifecycle Analysis](./developer-lifecycle.py)
    - [Retention Analysis](./developer-retention.py)
    - [DeFi Developer Journeys](./defi-developer-journeys.py)
    - [Speedrun Ethereum](./speedrun-ethereum.py)
    """)
    return
```

**Step 4: Verify**

```bash
uv run marimo check notebooks/insights/developer-report-2025.py
```

Expected: `✓ developer-report-2025.py`

**Step 5: Commit**

```bash
git add notebooks/insights/developer-report-2025.py
git commit -m "feat(notebook): fix r-string, hide test_connection, add Related footer to 2025 Developer Trends"
```

---

## Task 7: developer-lifecycle.py — Fix schema prefix, hide test_connection, add Related footer

**Files:**
- Modify: `notebooks/insights/developer-lifecycle.py`

**Step 1: Fix schema prefix on lifecycle model query (line ~395)**

The SQL query at line ~395 uses:
```sql
FROM int_crypto_ecosystems_developer_lifecycle_monthly_aggregated
```

Change to:
```sql
FROM oso.int_crypto_ecosystems_developer_lifecycle_monthly_aggregated
```

Check if there are any other occurrences of this table name (search for `int_crypto_ecosystems`) — fix all of them.

Also check the inline mention at line ~50 (in a markdown cell):
```
`int_crypto_ecosystems_developer_lifecycle_monthly_aggregated`
```
This is documentation text inside backticks — leave it as-is (it's illustrative, not executed SQL).

**Step 2: Hide test_connection output (lines 486-491)**

```python
@app.cell(hide_code=True)
def test_connection(mo, pyoso_db_conn):
    _test_df = mo.sql("""SELECT 1 AS test""", engine=pyoso_db_conn, output=False)
    return
```

(Remove `_status` variable and `mo.md(_status)` call.)

**Step 3: Add Related footer cell before infrastructure cells**

```python
@app.cell(hide_code=True)
def related(mo):
    mo.md("""
    ## Related

    **Metric Definitions**
    - [Lifecycle](../data/metric-definitions/lifecycle.py) — Developer stage definitions
    - [Activity](../data/metric-definitions/activity.py) — Monthly Active Developer (MAD) methodology

    **Other Insights**
    - [2025 Developer Trends](./developer-report-2025.py)
    - [Retention Analysis](./developer-retention.py)
    - [DeFi Developer Journeys](./defi-developer-journeys.py)
    - [Speedrun Ethereum](./speedrun-ethereum.py)
    """)
    return
```

**Step 4: Verify**

```bash
uv run marimo check notebooks/insights/developer-lifecycle.py
```

Expected: `✓ developer-lifecycle.py`

**Step 5: Commit**

```bash
git add notebooks/insights/developer-lifecycle.py
git commit -m "feat(notebook): fix oso. schema prefix, hide test_connection, add Related footer to lifecycle insights"
```

---

## Task 8: developer-retention.py — Hide test_connection, add Related footer

**Files:**
- Modify: `notebooks/insights/developer-retention.py`

**Step 1: Hide test_connection output (lines 55-60)**

```python
@app.cell(hide_code=True)
def test_connection(mo, pyoso_db_conn):
    _test_df = mo.sql("""SELECT 1 AS test""", engine=pyoso_db_conn, output=False)
    return
```

**Step 2: Add Related footer cell before infrastructure cells**

```python
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
```

**Step 3: Verify**

```bash
uv run marimo check notebooks/insights/developer-retention.py
```

Expected: `✓ developer-retention.py`

**Step 4: Commit**

```bash
git add notebooks/insights/developer-retention.py
git commit -m "feat(notebook): hide test_connection and add Related footer to retention insights"
```

---

## Task 9: speedrun-ethereum.py — Remove trailing empty cell, add Related footer

**Files:**
- Modify: `notebooks/insights/speedrun-ethereum.py`

**Step 1: Remove trailing empty cell (lines 1747-1750)**

Find and delete these four lines:
```python
@app.cell
def _():
    return

```

(The cell is between the `setup_pyoso` cell and `if __name__ == "__main__":`. Delete just those four lines.)

**Step 2: Add Related footer cell before the setup_pyoso cell**

```python
@app.cell(hide_code=True)
def related(mo):
    mo.md("""
    ## Related

    **Metric Definitions**
    - [Activity](../data/metric-definitions/activity.py) — Monthly Active Developer (MAD) methodology
    - [Retention](../data/metric-definitions/retention.py) — Cohort-based retention methodology

    **Other Insights**
    - [2025 Developer Trends](./developer-report-2025.py)
    - [Lifecycle Analysis](./developer-lifecycle.py)
    - [Retention Analysis](./developer-retention.py)
    - [DeFi Developer Journeys](./defi-developer-journeys.py)
    """)
    return
```

**Step 3: Verify**

```bash
uv run marimo check notebooks/insights/speedrun-ethereum.py
```

Expected: `✓ speedrun-ethereum.py`

**Step 4: Commit**

```bash
git add notebooks/insights/speedrun-ethereum.py
git commit -m "feat(notebook): remove trailing empty cell and add Related footer to Speedrun Ethereum"
```

---

## Task 10: defi-developer-journeys.py — Add Related footer

**Files:**
- Modify: `notebooks/insights/defi-developer-journeys.py`

**Step 1: Find the infrastructure section**

The file is ~2862 lines. The infrastructure section starts near the bottom. Search for `def helper_stringify_in_clause` or `def import_libraries` — the Related footer goes BEFORE `def import_libraries`.

**Step 2: Add Related footer cell**

```python
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
```

**Step 3: Verify**

```bash
uv run marimo check notebooks/insights/defi-developer-journeys.py
```

Expected: `✓ defi-developer-journeys.py`

**Step 4: Commit**

```bash
git add notebooks/insights/defi-developer-journeys.py
git commit -m "feat(notebook): add Related footer to DeFi Developer Journeys"
```

---

## Final Verification

After all 10 tasks, run marimo check on all modified notebooks at once:

```bash
uv run marimo check \
  notebooks/data/metric-definitions/activity.py \
  notebooks/data/metric-definitions/lifecycle.py \
  notebooks/data/metric-definitions/retention.py \
  notebooks/data/metric-definitions/alignment.py \
  notebooks/insights/developer-report-2025.py \
  notebooks/insights/developer-lifecycle.py \
  notebooks/insights/developer-retention.py \
  notebooks/insights/speedrun-ethereum.py \
  notebooks/insights/defi-developer-journeys.py
```

Expected: All pass with no errors.

Optionally run `/notebook-verify` on each modified notebook to capture screenshots and confirm visual output.

---

## Common Marimo Errors and Fixes

| Error | Cause | Fix |
|:------|:-------|:----|
| `Multiple definitions of 'X'` | Two cells both define `X` in their return | Prefix one with `_` |
| `Cycle detected` | Cell A depends on B which depends on A | Restructure to break the loop |
| `Name 'X' is not defined` | Cell uses `X` but no cell returns it | Add `X` to a cell's return tuple |
| `Cell must return a value` | Cell has logic but no return | Add `return` at the end |

All content cells MUST have `hide_code=True`. Infrastructure cells (apply_ec_style, imports, setup_pyoso) also have `hide_code=True`.
