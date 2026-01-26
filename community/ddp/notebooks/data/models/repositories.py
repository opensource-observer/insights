# /// script
# [tool.marimo.runtime]
# auto_instantiate = false
# ///

import marimo
import pyoso

app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    return mo.md(
        """
        # Unified Repository Model

        The `int_opendevdata__repositories_with_repo_id` model serves as the central bridge between curated project data and GitHub's technical identifiers. It ensures that every repository tracked in the OSS Directory is mapped to its corresponding **REST API ID** (`repo_id`), enabling precise joins with GitHub event data and other technical metrics.
        """
    )


@app.cell(hide_code=True)
def _(mo):
    return mo.md(
        """
        ## Matching Strategy

        To maintain high data integrity, the model employs a multi-tiered matching strategy to resolve repositories to their REST API IDs:

        1. **OSS Directory**: High-trust match via `github_graphql_id`.
        2. **Node ID Map**: Decoded `github_graphql_id` to `repo_id`.
        3. **GitHub Archive**: Fallback match via `repo_name` (least reliable due to renames).
        """
    )


@app.cell(hide_code=True)
def _(mo):
    return mo.md(
        """
        ## 3-ID System Comparison

        The repository model bridges different identifier systems used across the ecosystem:

        | ID Type | Name | Description |
        | :--- | :--- | :--- |
        | `opendevdata_id` | OpenDevData ID | Canonical internal ID. |
        | `github_graphql_id` | GitHub Node ID | GitHub Node ID (Base64). |
        | `repo_id` | GitHub REST ID | GitHub REST API ID (Primary Join Key). |
        """
    )


@app.cell
def _(mo, pyoso_db_conn):
    _df_ids = mo.sql(
        """
        SELECT 
            opendevdata_id, 
            github_graphql_id, 
            repo_id 
        FROM int_opendevdata__repositories_with_repo_id
        WHERE opendevdata_id IS NOT NULL 
          AND github_graphql_id IS NOT NULL 
          AND repo_id IS NOT NULL
        LIMIT 10
        """,
        engine=pyoso_db_conn
    )
    return (_df_ids,)


@app.cell(hide_code=True)
def _(_df_ids, mo):
    return mo.ui.table(
        _df_ids,
        format_mapping={
            "repo_id": "{:d}"
        }
    )


@app.cell(hide_code=True)
def _(mo):
    return mo.md(
        """
        ## Coverage Analysis

        This section visualizes the distribution of repository identifier sources, showing how many repositories were matched via each strategy.
        """
    )


@app.cell
def _(mo, pyoso_db_conn):
    _df_coverage = mo.sql(
        """
        SELECT 
            repo_id_source, 
            COUNT(*) as count 
        FROM int_opendevdata__repositories_with_repo_id 
        GROUP BY 1 
        ORDER BY 2 DESC
        """,
        engine=pyoso_db_conn
    )
    return (_df_coverage,)


@app.cell(hide_code=True)
def _(_df_coverage, mo):
    import plotly.express as px
    _fig_coverage = px.pie(
        _df_coverage, 
        names='repo_id_source', 
        values='count',
        title="Repository ID Source Coverage"
    )
    return mo.ui.plotly(_fig_coverage)


@app.cell(hide_code=True)
def _(mo):
    return mo.md(
        """
        ## Age Distribution

        This section shows the distribution of repository creation dates, helping identify the 'age' of the repositories in the dataset.
        """
    )


@app.cell
def _(mo, pyoso_db_conn):
    _df_age = mo.sql(
        """
        SELECT 
            DATE_TRUNC('month', repo_created_at) as created_month, 
            COUNT(*) as count 
        FROM int_opendevdata__repositories_with_repo_id 
        WHERE repo_created_at IS NOT NULL 
        GROUP BY 1 
        ORDER BY 1
        """,
        engine=pyoso_db_conn
    )
    return (_df_age,)


@app.cell(hide_code=True)
def _(_df_age, mo):
    import plotly.express as px
    _fig_age = px.bar(
        _df_age, 
        x='created_month', 
        y='count',
        title="Repository Age Distribution (by Month)"
    )
    return mo.ui.plotly(_fig_age)


@app.cell(hide_code=True)
def _(mo):
    return mo.md(
        """
        ## Edge Cases & Sample Queries

        ### Edge Cases
        - **Duplication**: One `github_graphql_id` might map to multiple `opendevdata_id`s if ODD tracks forks/renames separately, or if GitHub API changes occurred.
        - **Unmatched**: Repositories might lack a `repo_id` if they are very new (not yet in GHArchive sync) or very old (pre-2015) and inactive.
        """
    )


@app.cell
def _(mo, pyoso_db_conn):
    _df_join = mo.sql(
        """
        -- Bridge curated ODD data with GitHub Archive events using repo_id
        SELECT 
            r.repo_name, 
            r.repo_id, 
            e.event_type,
            COUNT(*) as event_count
        FROM int_opendevdata__repositories_with_repo_id r
        JOIN int_gharchive__github_events e ON r.repo_id = e.repo_id
        WHERE r.star_count > 1000
        GROUP BY 1, 2, 3
        LIMIT 10
        """,
        engine=pyoso_db_conn
    )
    return (_df_join,)


@app.cell
def _(mo, pyoso_db_conn):
    _df_find_by_id = mo.sql(
        """
        -- Find a specific repository across multiple identifier types
        SELECT 
            repo_name, 
            opendevdata_id, 
            github_graphql_id, 
            repo_id 
        FROM int_opendevdata__repositories_with_repo_id
        WHERE github_graphql_id = 'MDEwOlJlcG9zaXRvcnkyMjc3MDUz' -- Example: node_id for 'facebook/react'
           OR repo_id = 10270250 -- Example: repo_id for 'facebook/react'
        """,
        engine=pyoso_db_conn
    )
    return (_df_find_by_id,)


@app.cell
def _(mo, pyoso_db_conn):
    _df_unmatched = mo.sql(
        """
        -- Identify popular repositories missing a REST ID bridge
        SELECT 
            repo_name, 
            star_count, 
            fork_count
        FROM int_opendevdata__repositories_with_repo_id
        WHERE repo_id IS NULL
        ORDER BY star_count DESC
        LIMIT 10
        """,
        engine=pyoso_db_conn
    )
    return (_df_unmatched,)


@app.cell
def setup_pyoso():
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
