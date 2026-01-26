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


@app.cell
def setup_pyoso():
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
