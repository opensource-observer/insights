# /// script
# [tool.marimo.runtime]
# auto_instantiate = false
# ///

import marimo
import pyoso

app = marimo.App(width="full")


@app.cell
def _(mo):
    mo.md(
        """
        # Unified Repository Model

        The `int_opendevdata__repositories_with_repo_id` model serves as the central bridge between curated project data and GitHub's technical identifiers. It ensures that every repository tracked in the OSS Directory is mapped to its corresponding **REST API ID** (`repo_id`), enabling precise joins with GitHub event data and other technical metrics.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## Matching Strategy

        To maintain high data integrity, the model employs a multi-tiered matching strategy to resolve repositories to their REST API IDs:

        1. **OSS Directory**: High-trust match via `github_graphql_id`.
        2. **Node ID Map**: Decoded `github_graphql_id` to `repo_id`.
        3. **GitHub Archive**: Fallback match via `repo_name` (least reliable due to renames).
        """
    )
    return


@app.cell
def __():
    # Placeholder for future content (Tasks 3-5)
    return


@app.cell
def setup_pyoso():
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
