# /// script
# [tool.marimo.runtime]
# auto_instantiate = false
# ///

import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Unified Repository Model
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Overview
    The `int_opendevdata__repositories_with_repo_id` model serves as a bridge between multiple data sources within the Open Source Observer (OSO) ecosystem. It provides a unified view of software repositories by mapping external identifiers to internal OSO project IDs.

    This model is critical for:
    - **Normalization**: Standardizing repository names and URLs across different schemas.
    - **Stability**: Providing a stable `repo_id` that can be used to join events, contributions, and project-level metrics.
    - **Cross-Platform Analysis**: Enabling analysis by linking GitHub, GitLab, and other repository hosts.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## ID Mapping Strategy
    The model employs a 3-tier priority logic to assign a `repo_id` to each record, ensuring the highest possible match rate with the OSO project directory.

    1. **Primary Match (OSS Directory)**: Records are first matched using the `github_graphql_id`. This is the most reliable method as it relies on persistent, immutable IDs provided by GitHub.
    2. **Fallback Match (GitHub Archive)**: If a GraphQL ID is unavailable or fails to match, the system falls back to matching by `repo_name` (e.g., `owner/repo`). This accounts for repositories discovered through event logs or historical data.
    3. **Unmatched**: If neither method yields a match, the `repo_id` is set to `NULL`. These repositories are still tracked but are not currently associated with a verified OSO project.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Related Models
    - `projects_v1`: The primary source of truth for project-level metadata.
    - `events.py`: Downstream model consuming repository IDs for event attribution.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 3-ID System Comparison
    | ID Type | Column Name | Description |
    |---|---|---|
    | OpenDevData ID | `opendevdata_id` | Primary ODD source ID. |
    | GraphQL Node ID | `github_graphql_id` | Global node ID (Base64). |
    | REST ID | `repo_id` | Numeric DB ID. Primary join key. |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Age Distribution
    """)
    return


@app.cell(hide_code=True)
def _(mo, px, pyoso_db_conn):
    _PLOTLY_LAYOUT = {
        'margin': dict(l=10, r=10, t=60, b=20),
        'xaxis': dict(showgrid=True, gridcolor='#f0f0f0'),
        'yaxis': dict(showgrid=False, categoryorder='total ascending'),
        'template': 'plotly_white',
        'height': 300
    }

    _df_coverage = mo.sql(
        f"""
        SELECT 
            repo_id_source, 
            COUNT(*) as count 
        FROM oso.int_opendevdata__repositories_with_repo_id 
        GROUP BY 1
        """,
        engine=pyoso_db_conn,
        output=False
    )

    _fig_coverage = px.pie(
        _df_coverage,
        values='count',
        names='repo_id_source',
        title='Repository ID Mapping Coverage',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    _fig_coverage.update_layout(_PLOTLY_LAYOUT)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Age Distribution
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    import plotly.express as px

    _PLOTLY_LAYOUT = {
        'margin': dict(l=10, r=10, t=60, b=20),
        'xaxis': dict(showgrid=True, gridcolor='#f0f0f0'),
        'yaxis': dict(showgrid=False, categoryorder='total ascending'),
        'template': 'plotly_white',
        'height': 300
    }

    _df_age = mo.sql(
        f"""
        SELECT 
            DATE_TRUNC('month', repo_created_at) as month, 
            COUNT(*) as count 
        FROM oso.int_opendevdata__repositories_with_repo_id 
        WHERE repo_created_at IS NOT NULL
        GROUP BY 1
        ORDER BY 1
        """,
        engine=pyoso_db_conn,
        output=False
    )

    _fig_age = px.bar(
        _df_age,
        x='month',
        y='count',
        title='Repository Creation Trend'
    )
    _fig_age.update_layout(_PLOTLY_LAYOUT)
    return (px,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Edge Cases
    - **Duplication**: Occurs when multiple OpenDevData records point to the same OSO `repo_id`. This often happens due to repository renames or forks that are tracked as distinct entries in the source data.
    - **Unmatched**: Records where `repo_id` is `NULL` indicate repositories that are present in the source dataset but haven't been successfully mapped to a project in the OSO directory.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sample Queries
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 1. Cross-Source Join (bridge ODD and GHArchive)
    """)
    return


@app.cell
def _(mo, pyoso_db_conn):
    _df_join = mo.sql(
        f"""
        SELECT r.repo_name, r.repo_id, r.opendevdata_id, r.star_count
        FROM oso.int_opendevdata__repositories_with_repo_id r
        WHERE r.repo_id IS NOT NULL AND r.star_count > 1000
        LIMIT 5
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 2. Finding by ID
    """)
    return


@app.cell
def _(mo, pyoso_db_conn):
    _df_by_id = mo.sql(
        f"""
        SELECT repo_name, repo_id, opendevdata_id 
        FROM oso.int_opendevdata__repositories_with_repo_id
        WHERE github_graphql_id = 'MDEwOlJlcG9zaXRvcnkyNDI0Nzg0' -- rails/rails
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### 3. Identifying Unmatched
    """)
    return


@app.cell
def _(mo, pyoso_db_conn):
    _df_unmatched = mo.sql(
        f"""
        SELECT repo_name, star_count, repo_created_at
        FROM oso.int_opendevdata__repositories_with_repo_id
        WHERE repo_id IS NULL
        ORDER BY star_count DESC
        LIMIT 10
        """,
        engine=pyoso_db_conn
    )
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
        # Format columns with one per line, indented
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
        sql_snippet = generate_sql_snippet(model_name, df, limit=5)
        fmt = {c: '{:.0f}' for c in df.columns if df[c].dtype == 'int64' and ('_id' in c or c == 'id')}
        table = mo.ui.table(df, format_mapping=fmt, show_column_summaries=False, show_data_types=False)
        row_count = get_row_count(model_name)
        col_count = len(df.columns)
        title = f"{model_name} | {row_count:,.0f} rows, {col_count} cols"
        return mo.accordion({title: mo.vstack([sql_snippet, table])})

    import pandas as pd
    import plotly.express as px

    def get_format_mapping(df, include_percentage=False):
        """Generate format mapping for table display"""
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
    return (render_table_preview, px)


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
