import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # AI Agent Guide
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    _agent_prompt = (
        "You are a data analyst with access to the OSO (Open Source Observer) data warehouse.\n"
        "\n"
        "## Connection\n"
        "\n"
        "Install pyoso and set your API key:\n"
        "\n"
        "```bash\n"
        "uv add pyoso  # or: pip install pyoso\n"
        "export OSO_API_KEY=<your_key>\n"
        "```\n"
        "\n"
        "Query the warehouse:\n"
        "\n"
        "```python\n"
        "from pyoso import Client\n"
        "client = Client()  # reads OSO_API_KEY from environment\n"
        'df = client.to_pandas("SELECT * FROM oso.projects_v1 LIMIT 10")\n'
        "```\n"
        "\n"
        "## SQL Dialect\n"
        "\n"
        "Use **Trino SQL**:\n"
        "- `CAST(x AS VARCHAR)` not `SAFE_CAST`\n"
        "- `DATE_TRUNC('month', dt)` not `DATE_TRUNC(dt, MONTH)`\n"
        "- `COALESCE` not `IFNULL`\n"
        "- `CURRENT_DATE - INTERVAL '30' DAY` for date math\n"
        "\n"
        "## Key Tables\n"
        "\n"
        "### Ecosystem & Repository Data (Open Dev Data)\n"
        "- `oso.stg_opendevdata__ecosystems` -- Ecosystem definitions (name, is_crypto, is_chain)\n"
        "- `oso.stg_opendevdata__ecosystems_repos_recursive` -- Repos in each ecosystem (with distance)\n"
        "- `oso.int_opendevdata__repositories_with_repo_id` -- Repository bridge (maps GraphQL IDs to REST IDs)\n"
        "\n"
        "### Developer & Activity Data\n"
        "- `oso.int_ddp__developers` -- Unified developer identities (Open Dev Data + GitHub Archive)\n"
        "- `oso.int_gharchive__developer_activities` -- Daily developer activity rollup (for MAD metrics)\n"
        "- `oso.int_gharchive__github_events` -- Standardized GitHub events (pushes, PRs, issues, stars, forks)\n"
        "\n"
        "### Pre-Calculated Metrics\n"
        "- `oso.stg_opendevdata__eco_mads` -- Monthly active developers per ecosystem\n"
        "- `oso.stg_opendevdata__repo_developer_28d_activities` -- 28-day rolling activity per repo per developer\n"
        "\n"
        "### Projects\n"
        "- `oso.projects_v1` -- Curated project registry with metadata\n"
        "\n"
        "## Starter Queries\n"
        "\n"
        "**Largest ecosystems by repo count:**\n"
        "```sql\n"
        "SELECT e.name, COUNT(DISTINCT er.repo_id) AS repo_count\n"
        "FROM oso.stg_opendevdata__ecosystems e\n"
        "JOIN oso.stg_opendevdata__ecosystems_repos_recursive er ON e.id = er.ecosystem_id\n"
        "GROUP BY e.name ORDER BY repo_count DESC LIMIT 15\n"
        "```\n"
        "\n"
        "**Monthly active developers for an ecosystem:**\n"
        "```sql\n"
        "SELECT m.day, m.all_devs AS monthly_active_developers, m.full_time_devs\n"
        "FROM oso.stg_opendevdata__eco_mads m\n"
        "JOIN oso.stg_opendevdata__ecosystems e ON m.ecosystem_id = e.id\n"
        "WHERE e.name = 'Ethereum' AND m.day >= DATE('2024-01-01')\n"
        "ORDER BY m.day\n"
        "```\n"
        "\n"
        "**Cross-source join -- active developers per ecosystem (last 30 days):**\n"
        "```sql\n"
        "SELECT e.name, COUNT(DISTINCT da.actor_id) AS active_devs\n"
        "FROM oso.int_gharchive__developer_activities da\n"
        "JOIN oso.int_opendevdata__repositories_with_repo_id r ON da.repo_id = r.repo_id\n"
        "JOIN oso.stg_opendevdata__ecosystems_repos_recursive err ON r.opendevdata_id = err.repo_id\n"
        "JOIN oso.stg_opendevdata__ecosystems e ON err.ecosystem_id = e.id\n"
        "WHERE da.bucket_day >= CURRENT_DATE - INTERVAL '30' DAY\n"
        "GROUP BY e.name ORDER BY active_devs DESC LIMIT 10\n"
        "```\n"
        "\n"
        "## Important Notes\n"
        "- GitHub Archive data can be ~3 days behind real-time\n"
        "- Only public GitHub events (no private repos)\n"
        "- Use narrow date ranges (7-30 days) for fast queries\n"
        "- Full data catalog: https://docs.oso.xyz"
    )
    mo.vstack([
        mo.md("## Setup"),
        mo.md("Set up your agent in three steps:"),
        mo.accordion({
            "Step 1. Get an API key": mo.md("Sign up at [oso.xyz/start](https://www.oso.xyz/start), then go to **Settings > API Keys** and create a new key."),
            "Step 2. Copy the agent prompt": mo.md(f"~~~markdown\n{_agent_prompt}\n~~~"),
            "Step 3. Paste into your AI tool": mo.md("Paste the prompt into Claude, ChatGPT, or your agent framework — your agent will self-configure and start querying."),
        }),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    _guide = (
        "# Creating an Interactive Notebook\n"
        "\n"
        "DDP notebooks are marimo notebooks (`.py` files, not `.ipynb`). Marimo uses a DAG of cells\n"
        "with automatic dependency resolution — cell order in the file doesn't affect execution order.\n"
        "For the full style guide, see `notebooks/CLAUDE.md` in the repo.\n"
        "\n"
        "## Required Boilerplate\n"
        "\n"
        "Every notebook needs three things:\n"
        "\n"
        "**1. File header** (top of file):\n"
        "```python\n"
        "import marimo\n"
        "\n"
        '__generated_with = "unknown"\n'
        "app = marimo.App(width=\"full\")\n"
        "```\n"
        "\n"
        "**2. Setup cell** (can be placed at the bottom — marimo resolves deps automatically):\n"
        "```python\n"
        "@app.cell(hide_code=True)\n"
        "def setup_pyoso():\n"
        "    # This code sets up pyoso to be used as a database provider for this notebook\n"
        "    # This code is autogenerated. Modification could lead to unexpected results :)\n"
        "    import pyoso\n"
        "    import marimo as mo\n"
        "    pyoso_db_conn = pyoso.Client().dbapi_connection()\n"
        "    return mo, pyoso_db_conn\n"
        "```\n"
        "\n"
        "**3. Entry point** (bottom of file):\n"
        "```python\n"
        'if __name__ == "__main__":\n'
        "    app.run()\n"
        "```\n"
        "\n"
        "## Running & Validating\n"
        "\n"
        "```bash\n"
        "# Check structure (catches cycles, multiple definitions, import errors)\n"
        "uv run marimo check notebooks/my-notebook.py\n"
        "\n"
        "# Edit interactively in browser (cells don't auto-execute on open)\n"
        "uv run marimo edit notebooks/my-notebook.py\n"
        "\n"
        "# Run headless — executes all cells, useful for verifying end-to-end\n"
        "uv run marimo run notebooks/my-notebook.py\n"
        "```\n"
        "\n"
        "Always run `marimo check` before committing. It catches problems that\n"
        "won't surface until runtime.\n"
        "\n"
        "## Cell Conventions\n"
        "\n"
        "- **All cells** use `@app.cell(hide_code=True)` — no exceptions\n"
        "- Use `mo.sql(query, engine=pyoso_db_conn)` for SQL queries\n"
        "- Prefix throwaway variables with `_` to avoid \"multiple definitions\" errors\n"
        "- Use `\"\"\"` for markdown strings, not `r\"\"\"`\n"
        "- Named data for downstream cells should be descriptive: `df_top_ecosystems`\n"
        "- Each cell must explicitly `return` all variables other cells need\n"
        "- Declare dependencies via function args: `def _(mo, px, df_data):`\n"
        "\n"
        "## Common Anti-Patterns\n"
        "\n"
        "| Don't | Do Instead |\n"
        "|-------|------------|\n"
        "| `conn = pyoso.Client()` in random cells | Use `pyoso_db_conn` from `setup_pyoso` |\n"
        "| `conn.to_pandas(sql)` | `mo.sql(sql, engine=pyoso_db_conn)` |\n"
        "| Import `mo` in multiple cells | Get `mo` from `setup_pyoso` via function args |\n"
        "| `from dotenv import load_dotenv` | Rely on `direnv` — keys load automatically |\n"
        "| Reuse a variable name across cells | Prefix with `_` or give a unique name |\n"
        "| `@app.cell` without `hide_code=True` | Always include `hide_code=True` |\n"
        "| `r\"\"\"` raw strings for markdown | Use plain `\"\"\"` triple-quote strings |\n"
        "| Circular references between cells | Restructure so data flows one direction |\n"
        "| `SELECT *` in queries | List columns explicitly for clarity |\n"
        "| Wide date ranges in live queries | Use `CURRENT_DATE - INTERVAL '30' DAY` or narrower |\n"
        "\n"
        "## Notebook Structure (recommended order)\n"
        "\n"
        "1. Title + intro\n"
        "2. Overview section\n"
        "3. Data lineage (`mo.mermaid()`)\n"
        "4. Model previews (accordion with SQL snippets)\n"
        "5. Live data exploration (stats + charts)\n"
        "6. Sample queries (markdown + executed pairs)\n"
        "7. Related models\n"
        "8. Helper utilities cell\n"
        "9. Imports cell (`plotly.express`, `pandas`)\n"
        "10. Setup cell (`setup_pyoso`)\n"
    )
    _advanced_guide = (
        "# Advanced Notebook Patterns\n"
        "\n"
        "Deeper patterns for polished DDP notebooks. Assumes familiarity with the basics above.\n"
        "\n"
        "## Caching Expensive Queries\n"
        "\n"
        "Use `mo.persistent_cache` to avoid re-running slow queries during development.\n"
        "The cache persists across sessions and is keyed by cell content — if the SQL changes,\n"
        "the cache invalidates automatically.\n"
        "\n"
        "```python\n"
        "@app.cell(hide_code=True)\n"
        "def _(mo, pyoso_db_conn):\n"
        "    with mo.persistent_cache(\"my_query_data\"):\n"
        "        df_results = mo.sql(\n"
        '            """\n'
        "            SELECT ecosystem_name, day, total_devs\n"
        "            FROM oso.stg_opendevdata__eco_mads\n"
        "            WHERE day >= CURRENT_DATE - INTERVAL '365' DAY\n"
        '            """,\n'
        "            engine=pyoso_db_conn,\n"
        "            output=False\n"
        "        )\n"
        "    return (df_results,)\n"
        "```\n"
        "\n"
        "**Tips:**\n"
        "- Give each cache a unique, descriptive name\n"
        "- Use `output=False` when you need the DataFrame for downstream processing rather than inline display\n"
        "- Wrap the entire query block — the `with` block defines what gets cached\n"
        "- Especially useful for queries that scan large date ranges or join multiple tables\n"
        "\n"
        "## Plotly Chart Templates\n"
        "\n"
        "All charts use `plotly_white` template with consistent axis styling.\n"
        "\n"
        "### Bar Chart (horizontal)\n"
        "```python\n"
        "_fig = px.bar(\n"
        "    df_data,\n"
        "    x='value_column',\n"
        "    y='label_column',\n"
        "    orientation='h',\n"
        "    text='value_column',\n"
        "    color_discrete_sequence=['#4C78A8']\n"
        ")\n"
        "_fig.update_traces(\n"
        "    texttemplate='%{text:,.0f}',\n"
        "    textposition='outside'\n"
        ")\n"
        "_fig.update_layout(\n"
        "    template='plotly_white',\n"
        "    margin=dict(t=20, l=0, r=0, b=0),\n"
        "    height=400,\n"
        "    showlegend=False,\n"
        "    yaxis=dict(categoryorder='total ascending')\n"
        ")\n"
        "```\n"
        "\n"
        "### Line / Area Chart (time series)\n"
        "```python\n"
        "_fig = px.area(\n"
        "    df_timeseries,\n"
        "    x='day',\n"
        "    y='value',\n"
        "    color='series_name',\n"
        "    color_discrete_sequence=['#4C78A8', '#F58518', '#72B7B2']\n"
        ")\n"
        "_fig.update_layout(\n"
        "    template='plotly_white',\n"
        "    margin=dict(t=20, l=0, r=0, b=0),\n"
        "    height=400,\n"
        "    hovermode='x unified',\n"
        "    xaxis=dict(tickformat='%b %Y'),\n"
        "    legend=dict(\n"
        "        orientation='h', yanchor='bottom', y=1.02,\n"
        "        xanchor='right', x=1, title_text=''\n"
        "    )\n"
        ")\n"
        "```\n"
        "\n"
        "### Shared Axis Styling\n"
        "Apply to all charts:\n"
        "```python\n"
        "_fig.update_xaxes(title='', showgrid=False, linecolor='#000', linewidth=1)\n"
        "_fig.update_yaxes(title='Y Label', showgrid=True, gridcolor='#E5E5E5',\n"
        "                  linecolor='#000', linewidth=1)\n"
        "```\n"
        "\n"
        "### Rendering\n"
        "Always render with the mode bar hidden:\n"
        "```python\n"
        "mo.ui.plotly(_fig, config={'displayModeBar': False})\n"
        "```\n"
        "\n"
        "### Color Palette\n"
        "- Primary: `#4C78A8` (blue) — default for single-series\n"
        "- Secondary: `#F58518` (orange) — second series\n"
        "- Tertiary: `#72B7B2` (teal) — third series\n"
        "- Area fill: 0.2 opacity (e.g., `rgba(76, 120, 168, 0.2)`)\n"
        "\n"
        "## Stats Widgets\n"
        "\n"
        "Place summary stats above charts using `mo.stat`:\n"
        "```python\n"
        "mo.vstack([\n"
        "    mo.hstack([\n"
        '        mo.stat(label="Active Devs", value=f"{dev_count:,}",\n'
        '                bordered=True, caption="Last 30 days"),\n'
        '        mo.stat(label="Total Repos", value=f"{repo_count:,}",\n'
        '                bordered=True, caption="Recursive mapping"),\n'
        '        mo.stat(label="Peak MAD", value=f"{peak:,}",\n'
        '                bordered=True, caption=f"{peak_date:%b %Y}"),\n'
        "    ], widths='equal', gap=1),\n"
        "    mo.ui.plotly(_fig, config={'displayModeBar': False}),\n"
        "])\n"
        "```\n"
        "\n"
        "**Rules:** Always `bordered=True`, always include `caption`, 3-4 stats per row.\n"
        "\n"
        "## Table Formatting\n"
        "\n"
        "Use `mo.ui.table` with formatting for large numeric IDs:\n"
        "```python\n"
        "# Format integer ID columns to avoid scientific notation\n"
        "fmt = {\n"
        "    c: '{:.0f}'\n"
        "    for c in df.columns\n"
        "    if df[c].dtype == 'int64' and ('_id' in c or c == 'id')\n"
        "}\n"
        "mo.ui.table(\n"
        "    df,\n"
        "    format_mapping=fmt,\n"
        "    show_column_summaries=False,\n"
        "    show_data_types=False\n"
        ")\n"
        "```\n"
        "\n"
        "For read-only metric tables, disable selection and enable pagination:\n"
        "```python\n"
        "mo.ui.table(df_metrics, selection=None, pagination=True)\n"
        "```\n"
        "\n"
        "## Table Previews with Accordion\n"
        "\n"
        "The `render_table_preview` helper wraps a model preview in an accordion\n"
        "with row count, column count, and a SQL snippet:\n"
        "```python\n"
        "# In your helper utilities cell:\n"
        "def render_table_preview(model_name):\n"
        "    df = get_model_preview(model_name)\n"
        "    sql_snippet = generate_sql_snippet(model_name, df)\n"
        "    row_count = get_row_count(model_name)\n"
        "    col_count = len(df.columns)\n"
        '    title = f"{model_name} | {row_count:,.0f} rows, {col_count} cols"\n'
        "    return mo.accordion({title: mo.vstack([sql_snippet, table])})\n"
        "\n"
        "# Then in content cells:\n"
        "render_table_preview('oso.stg_opendevdata__ecosystems')\n"
        "```\n"
        "\n"
        "## Data Lineage Diagrams\n"
        "\n"
        "Use `mo.mermaid()` for showing model relationships:\n"
        "```python\n"
        '@app.cell(hide_code=True)\n'
        "def _(mo):\n"
        '    mo.mermaid("""\n'
        "    graph TD\n"
        "        A[source_model<br/>Raw data] --> B[int_model<br/>Cleaned]\n"
        "        B --> C[final_model<br/>Ready to query]\n"
        '    """)\n'
        "    return\n"
        "```\n"
    )
    mo.vstack([
        mo.md("## Create an Interactive Notebook"),
        mo.md("Skill template for creating new notebooks using DDP data with marimo. Copy the guide below. Point your agent to existing notebooks we've created for inspiration."),
        mo.accordion({
            "Notebook Creation Guide": mo.md(f"~~~markdown\n{_guide}\n~~~"),
            "Advanced Patterns": mo.md(f"~~~markdown\n{_advanced_guide}\n~~~"),
        }),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Additional Resources

    - **OSO Documentation**: [docs.oso.xyz](https://docs.oso.xyz) — API reference, data catalog, and SQL dialect guide
    - **Marimo Documentation**: [docs.marimo.io](https://docs.marimo.io) — Notebook framework reference
    - **Open Dev Data**: [opendevdata.org](https://opendevdata.org) — Developer ecosystem data powering the DDP models
    - **Trino**: [trino.io](https://trino.io/docs/current/language.html) — SQL dialect guide
    """)
    return


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
