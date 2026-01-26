# /// script
# [tool.marimo.runtime]
# auto_instantiate = false
# ///

import marimo
import pyoso

app = marimo.App(width="full")


@app.cell
def __():
    # Placeholder for future content (Tasks 2-5)
    return


@app.cell
def setup_pyoso():
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
