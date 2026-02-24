import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Ecosystems

    Open Dev Data organizes repositories into **ecosystems** — logical groupings by chain, protocol, foundation, or category — with hierarchical parent-child relationships and recursive repository mappings.

    Preview:
    ```sql
    SELECT * FROM oso.stg_opendevdata__ecosystems LIMIT 10
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Overview

    Ecosystems are groupings of repositories representing chains, protocols, projects, foundations, organizations, or broader categories. They provide a meaningful unit of analysis by aggregating developer activity beyond the repository level.

    - **What they are**: Collections of repos organized by chain (Ethereum, Solana), protocol (Uniswap, Aave), or category (DeFi, NFTs)
    - **Metadata flags**: Each ecosystem has `is_crypto`, `is_chain`, and `is_category` booleans for filtering
    - **Why they matter**: Aggregation (roll up repos to ecosystem-level metrics), comparison (benchmark across ecosystems), discovery (find repos in a domain), and hierarchy (navigate parent-child relationships)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Ecosystem Hierarchy

    Ecosystems form a directed graph (usually a tree or forest). A parent ecosystem is a higher-level grouping (e.g., Ethereum), and a child ecosystem is a project that belongs to it (e.g., Uniswap as a child of Ethereum). Nesting can be multi-level — a child can itself be a parent of other ecosystems.

    ### Key Models

    | Model | Purpose | Key Fields |
    |:------|:--------|:-----------|
    | `stg_opendevdata__ecosystems` | Ecosystem definitions | `id`, `name`, `is_crypto`, `is_chain`, `is_category` |
    | `stg_opendevdata__ecosystems_child_ecosystems` | Parent-child links | `parent_id`, `child_id` |
    | `stg_opendevdata__ecosystems_repos` | Direct repo mapping | `ecosystem_id`, `repo_id` |
    | `stg_opendevdata__ecosystems_repos_recursive` | Recursive repo mapping | `ecosystem_id`, `repo_id`, `distance`, `path` |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.mermaid("""
    graph TD
        A[stg_opendevdata__ecosystems<br/>Definitions: name, flags] --> D
        B[stg_opendevdata__ecosystems_child_ecosystems<br/>Parent-child links] --> D
        C[stg_opendevdata__ecosystems_repos<br/>Direct repo mapping] --> D
        D[stg_opendevdata__ecosystems_repos_recursive<br/>Recursive repo mapping with distance + path]
        D --> E[Bridge to GitHub Archive<br/>via int_opendevdata__repositories_with_repo_id]
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Working with Recursive Repository Mappings

    The `oso.stg_opendevdata__ecosystems_repos_recursive` table is the primary tool for mapping repositories to ecosystems. It resolves the hierarchy so you don't have to traverse parent-child links yourself.

    ### Key Fields
    - **`ecosystem_id`**: The ID of the ecosystem
    - **`repo_id`**: The ID of the repository
    - **`distance`**: Depth of the relationship (0 = direct, 1 = one level of nesting, etc.)
    - **`path`**: The lineage path from the repo's immediate ecosystem up to the queried ecosystem

    ### When to Use Each Model

    | Use Case | Model | Why |
    |:---------|:------|:----|
    | All repos in an ecosystem (including nested children) | `ecosystems_repos_recursive` | Resolves full hierarchy automatically |
    | Only directly-owned repos | `ecosystems_repos` | No hierarchy traversal, direct mapping only |
    | Navigate the ecosystem tree | `ecosystems_child_ecosystems` | Explore parent-child relationships |
    """)
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview("oso.stg_opendevdata__ecosystems")
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview("oso.stg_opendevdata__ecosystems_repos_recursive")
    return


@app.cell(hide_code=True)
def _(render_table_preview):
    render_table_preview("oso.stg_opendevdata__ecosystems_child_ecosystems")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Best Practices

    | Goal | Recommended Approach | Why? |
    |:------|:---------------------|:------|
    | **All repos in an ecosystem** | Use `ecosystems_repos_recursive` | Resolves the full hierarchy — no manual traversal needed |
    | **Filter by ecosystem type** | Use `is_crypto`, `is_chain`, `is_category` flags | Quickly narrow to chains, protocols, or categories |
    | **Bridge to GitHub Archive** | Join `ecosystems_repos_recursive` → `int_opendevdata__repositories_with_repo_id` | Maps ODD repo IDs to GitHub `repo_id` for cross-source joins |
    | **Compare ecosystem sizes** | Group by `ecosystem_id` with `COUNT(DISTINCT repo_id)` on recursive table | Includes all nested repos for accurate counts |
    | **Explore hierarchy** | Use `ecosystems_child_ecosystems` with recursive CTEs | Navigate up or down the ecosystem tree |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Live Data Exploration

    The following charts show actual data from the ecosystem tables to demonstrate typical data patterns and ecosystem sizes.
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _query = """
    SELECT
      e.name AS ecosystem_name,
      COUNT(DISTINCT er.repo_id) AS repo_count
    FROM oso.stg_opendevdata__ecosystems_repos_recursive er
    JOIN oso.stg_opendevdata__ecosystems e ON er.ecosystem_id = e.id
    GROUP BY e.name
    ORDER BY repo_count DESC
    LIMIT 20
    """

    with mo.persistent_cache("top_ecosystems"):
        df_top_ecosystems = mo.sql(_query, engine=pyoso_db_conn, output=False)
    return (df_top_ecosystems,)


@app.cell(hide_code=True)
def _(df_top_ecosystems, mo, px):
    _total_ecosystems_query_note = "across all ecosystems"
    _total_repos = int(df_top_ecosystems['repo_count'].sum())
    _largest = df_top_ecosystems.iloc[0]['ecosystem_name'] if len(df_top_ecosystems) > 0 else "N/A"
    _largest_count = int(df_top_ecosystems.iloc[0]['repo_count']) if len(df_top_ecosystems) > 0 else 0

    _fig = px.bar(
        df_top_ecosystems,
        x='repo_count',
        y='ecosystem_name',
        orientation='h',
        text='repo_count',
        labels={'repo_count': 'Repository Count', 'ecosystem_name': 'Ecosystem'},
        color_discrete_sequence=['#4C78A8']
    )

    _fig.update_traces(
        texttemplate='%{text:,.0f}',
        textposition='outside',
        marker_color='#4C78A8'
    )

    _fig.update_layout(
        template='plotly_white',
        margin=dict(t=20, l=0, r=0, b=0),
        height=400,
        showlegend=False,
        xaxis=dict(
            title='Repository Count',
            showgrid=True,
            gridcolor="#E5E5E5",
            linecolor="#000",
            linewidth=1
        ),
        yaxis=dict(
            title='',
            showgrid=False,
            categoryorder='total ascending',
            linecolor="#000",
            linewidth=1
        )
    )

    mo.vstack([
        mo.hstack([
            mo.stat(label="Top 20 Ecosystems", value=f"{len(df_top_ecosystems)}", bordered=True, caption="Shown in chart"),
            mo.stat(label="Total Repos (Top 20)", value=f"{_total_repos:,}", bordered=True, caption="Recursive repo count"),
            mo.stat(label="Largest Ecosystem", value=_largest, bordered=True, caption=f"{_largest_count:,} repos"),
        ], widths="equal", gap=1),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("### Ethereum Child Ecosystems")
    return


@app.cell(hide_code=True)
def _(mo, px, pyoso_db_conn):
    _query = """
    SELECT
      child.name AS child_name,
      COUNT(DISTINCT er.repo_id) AS repo_count
    FROM oso.stg_opendevdata__ecosystems_child_ecosystems rel
    JOIN oso.stg_opendevdata__ecosystems parent ON rel.parent_id = parent.id
    JOIN oso.stg_opendevdata__ecosystems child ON rel.child_id = child.id
    LEFT JOIN oso.stg_opendevdata__ecosystems_repos_recursive er ON child.id = er.ecosystem_id
    WHERE parent.name = 'Ethereum'
    GROUP BY child.name
    ORDER BY repo_count DESC
    LIMIT 20
    """

    _df = mo.sql(_query, engine=pyoso_db_conn)

    _num_children = len(_df)
    _total_child_repos = int(_df['repo_count'].sum())

    _fig = px.bar(
        _df,
        x='repo_count',
        y='child_name',
        orientation='h',
        text='repo_count',
        labels={'repo_count': 'Repository Count', 'child_name': 'Child Ecosystem'},
        color_discrete_sequence=['#F58518']
    )

    _fig.update_traces(
        texttemplate='%{text:,.0f}',
        textposition='outside',
        marker_color='#F58518'
    )

    _fig.update_layout(
        template='plotly_white',
        margin=dict(t=20, l=0, r=0, b=0),
        height=400,
        showlegend=False,
        xaxis=dict(
            title='Repository Count',
            showgrid=True,
            gridcolor="#E5E5E5",
            linecolor="#000",
            linewidth=1
        ),
        yaxis=dict(
            title='',
            showgrid=False,
            categoryorder='total ascending',
            linecolor="#000",
            linewidth=1
        )
    )

    mo.vstack([
        mo.hstack([
            mo.stat(label="Child Ecosystems", value=f"{_num_children}", bordered=True, caption="Direct children of Ethereum"),
            mo.stat(label="Total Repos", value=f"{_total_child_repos:,}", bordered=True, caption="Across all children"),
        ], widths="equal", gap=1),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Queries

    ### 1. All Repos in an Ecosystem (Recursive)

    Get all repositories in the Ethereum ecosystem, including repos from nested child ecosystems.

    ```sql
    SELECT
      r.name AS repo_name,
      r.link AS repo_url,
      er.distance,
      er.path
    FROM oso.stg_opendevdata__ecosystems_repos_recursive er
    JOIN oso.stg_opendevdata__repos r ON er.repo_id = r.id
    JOIN oso.stg_opendevdata__ecosystems e ON er.ecosystem_id = e.id
    WHERE e.name = 'Ethereum'
    ORDER BY er.distance, r.name
    LIMIT 20
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          r.name AS repo_name,
          r.link AS repo_url,
          er.distance,
          er.path
        FROM oso.stg_opendevdata__ecosystems_repos_recursive er
        JOIN oso.stg_opendevdata__repos r ON er.repo_id = r.id
        JOIN oso.stg_opendevdata__ecosystems e ON er.ecosystem_id = e.id
        WHERE e.name = 'Ethereum'
        ORDER BY er.distance, r.name
        LIMIT 20
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 2. Ecosystem Hierarchy (Children of Ethereum)

    List all direct children of a parent ecosystem.

    ```sql
    SELECT
      parent.name AS parent_name,
      child.name AS child_name
    FROM oso.stg_opendevdata__ecosystems_child_ecosystems rel
    JOIN oso.stg_opendevdata__ecosystems parent ON rel.parent_id = parent.id
    JOIN oso.stg_opendevdata__ecosystems child ON rel.child_id = child.id
    WHERE parent.name = 'Ethereum'
    ORDER BY child.name
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          parent.name AS parent_name,
          child.name AS child_name
        FROM oso.stg_opendevdata__ecosystems_child_ecosystems rel
        JOIN oso.stg_opendevdata__ecosystems parent ON rel.parent_id = parent.id
        JOIN oso.stg_opendevdata__ecosystems child ON rel.child_id = child.id
        WHERE parent.name = 'Ethereum'
        ORDER BY child.name
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 3. Repository Counts by Ecosystem (with Metadata Flags)

    Rank ecosystems by size and see their classification flags.

    ```sql
    SELECT
      e.name AS ecosystem_name,
      e.is_crypto,
      e.is_chain,
      e.is_category,
      COUNT(DISTINCT er.repo_id) AS repo_count
    FROM oso.stg_opendevdata__ecosystems e
    JOIN oso.stg_opendevdata__ecosystems_repos_recursive er ON e.id = er.ecosystem_id
    GROUP BY e.name, e.is_crypto, e.is_chain, e.is_category
    ORDER BY repo_count DESC
    LIMIT 20
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          e.name AS ecosystem_name,
          e.is_crypto,
          e.is_chain,
          e.is_category,
          COUNT(DISTINCT er.repo_id) AS repo_count
        FROM oso.stg_opendevdata__ecosystems e
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive er ON e.id = er.ecosystem_id
        GROUP BY e.name, e.is_crypto, e.is_chain, e.is_category
        ORDER BY repo_count DESC
        LIMIT 20
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 4. Bridging Ecosystems to GitHub Archive (Developer Activity)

    Join ecosystem repos to GitHub Archive developer activity data for cross-source analysis.

    ```sql
    SELECT
      e.name AS ecosystem_name,
      COUNT(DISTINCT da.actor_id) AS unique_developers,
      SUM(da.num_events) AS total_events
    FROM oso.int_gharchive__developer_activities da
    JOIN oso.int_opendevdata__repositories_with_repo_id r
      ON da.repo_id = r.repo_id
    JOIN oso.stg_opendevdata__ecosystems_repos_recursive err
      ON r.opendevdata_id = err.repo_id
    JOIN oso.stg_opendevdata__ecosystems e
      ON err.ecosystem_id = e.id
    WHERE
      da.bucket_day >= CURRENT_DATE - INTERVAL '30' DAY
      AND e.name = 'Ethereum'
    GROUP BY e.name
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        f"""
        SELECT
          e.name AS ecosystem_name,
          COUNT(DISTINCT da.actor_id) AS unique_developers,
          SUM(da.num_events) AS total_events
        FROM oso.int_gharchive__developer_activities da
        JOIN oso.int_opendevdata__repositories_with_repo_id r
          ON da.repo_id = r.repo_id
        JOIN oso.stg_opendevdata__ecosystems_repos_recursive err
          ON r.opendevdata_id = err.repo_id
        JOIN oso.stg_opendevdata__ecosystems e
          ON err.ecosystem_id = e.id
        WHERE
          da.bucket_day >= CURRENT_DATE - INTERVAL '30' DAY
          AND e.name = 'Ethereum'
        GROUP BY e.name
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Generic Query Template

    To query any ecosystem, replace the ecosystem name in the WHERE clause:

    ```sql
    SELECT
      r.name AS repo_name,
      e.name AS ecosystem_name
    FROM oso.stg_opendevdata__ecosystems_repos_recursive er
    JOIN oso.stg_opendevdata__ecosystems e ON er.ecosystem_id = e.id
    JOIN oso.stg_opendevdata__repos r ON er.repo_id = r.id
    WHERE e.name = 'YOUR_ECOSYSTEM_NAME'
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Related Models

    - **Commits**: [commits.py](./commits.py) — Unified commit data across ODD and GHA
    - **Developers**: [developers.py](./developers.py) — Unified developer identities across ODD and GHA
    - **Events**: [events.py](./events.py) — GitHub Archive event data and activity metrics
    """)
    return


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
            return mo.md(f"**{model_name}**\n\nUnable to retrieve preview (table might be empty or inaccessible).")
        sql_snippet = generate_sql_snippet(model_name, df, limit=5)
        fmt = {c: '{:.0f}' for c in df.columns if df[c].dtype == 'int64' and ('_id' in c or c == 'id')}
        table = mo.ui.table(df, format_mapping=fmt, show_column_summaries=False, show_data_types=False)
        row_count = get_row_count(model_name)
        col_count = len(df.columns)
        title = f"{model_name} | {row_count:,.0f} rows, {col_count} cols"
        return mo.accordion({title: mo.vstack([sql_snippet, table])})

    return (render_table_preview,)


@app.cell(hide_code=True)
def imports():
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
