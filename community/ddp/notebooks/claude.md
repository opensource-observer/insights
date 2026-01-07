# DDP Notebooks Style Guide

This file documents the conventions and patterns for creating and editing marimo notebooks in the Developer Data Portal (DDP).

## Notebook Structure

DDP data model notebooks should follow this structure (top to bottom):

1. **Setup cell** (`setup_pyoso`) - Initialize pyoso client and database connection
2. **Helper utilities cell** - Define reusable functions for table previews and formatting
3. **Title** - Simple markdown header (e.g., `# Events`)
4. **Overview section** - What the model is and why it matters
5. **Data source comparison** (if applicable) - Compare Open Dev Data vs GitHub Archive
6. **Data lineage** - ASCII diagram showing transformation flow
7. **Model previews** - Accordion previews with SQL snippets and row counts
8. **Live data exploration** - Executed queries with visualizations
9. **Sample queries** - Copy/paste SQL snippets in markdown code blocks
10. **Related models** - Links to related notebooks

## Required Cells

### Setup Cell
```python
@app.cell
def setup_pyoso():
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn
```

### Helper Utilities Cell
```python
@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    def get_model_preview(model_name, limit=5):
        return mo.sql(f"SELECT * FROM {model_name} LIMIT {limit}", 
                      engine=pyoso_db_conn, output=False)

    def get_row_count(model_name):
        result = mo.sql(f"SHOW STATS FOR {model_name}", 
                        engine=pyoso_db_conn, output=False)
        return result['row_count'].sum()    
    
    def generate_sql_snippet(model_name, df_results, limit=5):
        column_names = df_results.columns.tolist()
        columns_formatted = ',\n  '.join(column_names)
        sql_snippet = f"""```sql
SELECT 
  {columns_formatted}
FROM {model_name}
LIMIT {limit}
```
"""
        return mo.md(sql_snippet)

    def render_table_preview(model_name):
        df = get_model_preview(model_name)
        if df.empty:
            return mo.md(f"**{model_name}**\n\nUnable to retrieve preview.")
        sql_snippet = generate_sql_snippet(model_name, df, limit=5)
        fmt = {c: '{:.0f}' for c in df.columns if df[c].dtype == 'int64' and ('_id' in c or c == 'id')}
        table = mo.ui.table(df, format_mapping=fmt, show_column_summaries=False, show_data_types=False)
        row_count = get_row_count(model_name)
        col_count = len(df.columns)
        title = f"{model_name} | {row_count:,.0f} rows, {col_count} cols"
        return mo.accordion({title: mo.vstack([sql_snippet, table])})
    
    import pandas as pd
    
    def get_format_mapping(df, include_percentage=False):
        fmt = {}
        for c in df.columns:
            if df[c].dtype in ['int64', 'float64']:
                if include_percentage and 'percentage' in c.lower():
                    fmt[c] = '{:.2f}'
                elif '_id' in c or c == 'id' or 'count' in c.lower():
                    fmt[c] = '{:.0f}'
                elif include_percentage:
                    fmt[c] = '{:.0f}'
        return fmt
    
    return (render_table_preview, pd, get_format_mapping)
```

## Visualization Patterns

### Import Plotly
```python
@app.cell(hide_code=True)
def _():
    import plotly.express as px
    return (px,)
```

### Chart Styling
Use consistent plotly styling:
```python
_fig.update_layout(
    template='plotly_white',
    margin=dict(t=20, l=0, r=0, b=0),
    height=400,
    hovermode='x unified'
)
_fig.update_xaxes(
    title='',
    showgrid=False,
    linecolor="#000",
    linewidth=1
)
_fig.update_yaxes(
    title='Your Y-Axis Label',
    showgrid=True,
    gridcolor="#E5E5E5",
    linecolor="#000",
    linewidth=1
)
```

### Color Palette
- Primary: `#4C78A8` (blue)
- Secondary: `#F58518` (orange)
- Tertiary: `#72B7B2` (teal)

## Stats Widgets

Use bordered stats with captions:
```python
mo.hstack([
    mo.stat(label="Label 1", value=f"{value1:,}", bordered=True, caption="Context info"),
    mo.stat(label="Label 2", value=f"{value2:,}", bordered=True, caption="Context info"),
], widths="equal", gap=1)
```

**Rules:**
- Always use `bordered=True`
- Always include a `caption` for context
- Use `widths="equal"` and `gap=1` for consistent spacing
- Place stats **above** charts, not below

## Live Data Queries

When executing queries for visualizations:
- **Always use narrow date ranges** (7-30 days) to keep execution fast
- Use `CURRENT_DATE - INTERVAL 'N' DAY` pattern
- Convert dates with `pd.to_datetime()` for plotly

Example:
```python
_query = """
SELECT
  bucket_day,
  COUNT(DISTINCT actor_id) AS daily_active_developers
FROM oso.int_gharchive__developer_activities
WHERE bucket_day >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY bucket_day
ORDER BY bucket_day
"""
df = mo.sql(_query, engine=pyoso_db_conn, output=False)
df['bucket_day'] = pd.to_datetime(df['bucket_day'])
```

## Markdown Conventions

### Headings
- Use regular markdown headings, **not** `mo.callout()` for important info
- Reserve callouts only for truly exceptional warnings

### Related Models Links
Use relative markdown links to other notebooks:
```python
mo.md("""
## Related Models

- **Commits**: [commits.py](./commits.py) — Description here
- **Repositories**: [repositories.py](./repositories.py) — Description here
- **Activity Metrics**: [activity.py](../metric-definitions/activity.py) — Description here
""")
```

### SQL Sample Queries
Present as markdown code blocks (not executed):
```python
mo.md("""
```sql
SELECT
  event_type,
  COUNT(*) AS event_count
FROM oso.int_gharchive__github_events
WHERE event_time >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY event_type
ORDER BY event_count DESC
```
""")
```

## Data Sources Reference

### GitHub Archive Models (broader event coverage)
- `oso.stg_github__events` — Raw events with nested fields
- `oso.int_gharchive__github_events` — Standardized events (canonical entrypoint)
- `oso.int_ddp_github_events` — Curated subset of event types
- `oso.int_ddp_github_events_daily` — Daily aggregation with normalized types
- `oso.int_gharchive__developer_activities` — Daily rollup for MAD metrics

### Open Dev Data Models (commit-centric, identity resolution)
- `oso.stg_opendevdata__commits` — Raw commits with identity resolution
- `oso.int_opendevdata__commits_with_repo_id` — Enriched with canonical repo_id
- `oso.int_opendevdata__repositories_with_repo_id` — Repository bridge model
- `oso.int_opendevdata__developers_with_dev_id` — Developer identity bridge

### DDP Curated Event Types
The DDP curated models include these event types:
- `PushEvent` — Commits pushed
- `PullRequestEvent` — PR activity
- `PullRequestReviewEvent` — Code reviews
- `PullRequestReviewCommentEvent` — Review comments
- `IssuesEvent` — Issue activity
- `WatchEvent` — Stars
- `ForkEvent` — Forks

Note: GitHub Archive contains many more event types. The DDP subset focuses on developer activity metrics.

## Key Expectations to Document

When writing model documentation, explicitly state:

1. **Data Freshness**: GitHub Archive can be ~3 days behind real-time
2. **Completeness**: Only public GitHub timeline; no private repos or deleted events
3. **Identity**: Distinguish between `actor_id` (GitHub) and `canonical_developer_id` (Open Dev Data)
4. **Join Keys**: Document which IDs to use for joins (e.g., `repo_id` for cross-source joins)

## File Naming

- Model notebooks: `data/models/{model_name}.py`
- Metric definitions: `data/metric-definitions/{metric_name}.py`
- Source documentation: `data/sources/{source_name}.py`
- Insights/dashboards: `insights/{insight_name}.py`

