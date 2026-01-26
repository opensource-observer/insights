# /// script
# [tool.marimo.runtime]
# auto_instantiate = false
# ///

import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"# Repository Model Analysis")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        This notebook explores the `int_opendevdata__repositories_with_repo_id` model, 
        which serves as a bridge between OpenDevData and GHArchive.
        """
    )
    return


@app.cell
def _(mo, pyoso_db_conn):
    _df_ids = mo.sql(
        f"""
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


@app.cell
def _(mo, pyoso_db_conn):
    _df_coverage = mo.sql(
        f"""
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
def _(_df_coverage):
    import plotly.express as _px
    _fig_coverage = _px.pie(
        _df_coverage, 
        names='repo_id_source', 
        values='count',
        title="Repository ID Source Coverage"
    )
    return (_fig_coverage,)


@app.cell
def _(mo, pyoso_db_conn):
    _df_age = mo.sql(
        f"""
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
def _(_df_age):
    import plotly.express as _px
    _fig_age = _px.bar(
        _df_age, 
        x='created_month', 
        y='count',
        title="Repository Age Distribution (by Month)"
    )
    return (_fig_age,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Edge Cases & Sample Queries

        ### Edge Cases
        - **Duplication**: One `github_graphql_id` might map to multiple `opendevdata_id`s if ODD tracks forks/renames separately, or if GitHub API changes occurred.
        - **Unmatched Repositories**: Repositories might lack a `repo_id` if they are very new (not yet in GHArchive sync) or very old (pre-2015) and inactive.
        """
    )
    return


@app.cell
def _(mo, pyoso_db_conn):
    _df_join = mo.sql(
        f"""
        -- Sample Query 1: Cross-Source Join (ODD + GHArchive)
        -- Demonstrates using repo_id as a bridge to other GHArchive-based models
        SELECT 
            r.repo_name, 
            r.repo_id, 
            r.opendevdata_id,
            r.star_count
        FROM int_opendevdata__repositories_with_repo_id r
        WHERE r.repo_id IS NOT NULL
          AND r.star_count > 1000
        LIMIT 5
        """,
        engine=pyoso_db_conn
    )
    return (_df_join,)


@app.cell
def _(mo, pyoso_db_conn):
    _df_by_id = mo.sql(
        f"""
        -- Sample Query 2: Finding Repositories by ID Type
        SELECT 
            repo_name, 
            repo_id, 
            opendevdata_id 
        FROM int_opendevdata__repositories_with_repo_id
        WHERE github_graphql_id = 'MDEwOlJlcG9zaXRvcnkyNDI0Nzg0' -- rails/rails
        """,
        engine=pyoso_db_conn
    )
    return (_df_by_id,)


@app.cell
def _(mo, pyoso_db_conn):
    _df_unmatched = mo.sql(
        f"""
        -- Sample Query 3: Identifying Unmatched Repositories
        SELECT 
            repo_name, 
            star_count, 
            repo_created_at
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
