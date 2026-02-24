import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Quick Start
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Sign Up
    Sign up at [oso.xyz/start](https://www.oso.xyz/start) for a free account.
    <br>This gives you full access to the OSO data lake with options to run queries in the browser or in your own environment.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.vstack([
        mo.md("## Choose Your Path"),
        mo.md("You can explore in the browser or query from your own environment."),
        mo.accordion({
            "Path 1: Create a Hosted Notebook on OSO": mo.md("""
1. Log in at [oso.xyz](https://www.oso.xyz), go to **Notebooks**, and click **New Notebook**
2. The `setup_pyoso` cell is auto-generated — you're already connected to the data warehouse
3. Add a new cell and paste a SQL query. Here's one to try — largest ecosystems by repo count:

```sql
SELECT
  e.name AS ecosystem_name,
  COUNT(DISTINCT er.repo_id) AS repo_count
FROM stg_opendevdata__ecosystems e
JOIN stg_opendevdata__ecosystems_repos_recursive er
  ON e.id = er.ecosystem_id
GROUP BY e.name
ORDER BY repo_count DESC
LIMIT 15
```

For more notebook patterns, see the [Agent Guide's notebook creation guide](/agent-guide).
"""),
            "Path 2: Query from Your Own Environment": mo.md("""
**1. Get an API key** — Go to **Settings > API Keys** and create a new key.

**2. Set your environment variable:**

```bash
export OSO_API_KEY=your_api_key_here
```

**3. Choose your workflow:**

**Option A: marimo notebooks (recommended)**

```bash
uv add pyoso marimo
uv run marimo edit notebook.py
```

Queries use `mo.sql()` with the pyoso database connection:

```python
import pyoso
import marimo as mo
pyoso_db_conn = pyoso.Client().dbapi_connection()
df = mo.sql("SELECT * FROM oso.projects_v1 LIMIT 10", engine=pyoso_db_conn)
```

**Option B: Any Python environment**

```bash
pip install pyoso
```

```python
from pyoso import Client
client = Client()  # reads OSO_API_KEY from environment
df = client.to_pandas("SELECT * FROM oso.projects_v1 LIMIT 10")
```

"""),
        }),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Understand the Data

    This portal combines three data sources, each with different strengths:

    | Source | What it provides | ID system |
    |:-------|:-----------------|:----------|
    | **Open Dev Data** | Developer identity, ecosystem mappings, commit history | Canonical / GraphQL IDs |
    | **GitHub Archive** | Full public GitHub timeline (pushes, PRs, issues, stars, forks) | REST API IDs |
    | **OSS Directory** | Curated project registry, bridges both ID systems | REST + GraphQL IDs |

    The most powerful feature is **cross-source joins**. Open Dev Data and GitHub Archive use different ID systems — the repository bridge model connects them:

    ```
    Open Dev Data (GraphQL ID)
        → int_opendevdata__repositories_with_repo_id (bridge)
            → GitHub Archive (REST API ID)
    ```

    Here's an example — active developers per ecosystem over the last 30 days, joining GitHub Archive activity through the bridge:

    ```sql
    SELECT
      e.name AS ecosystem,
      COUNT(DISTINCT da.actor_id) AS active_developers,
      SUM(da.num_events) AS total_events
    FROM int_gharchive__developer_activities da
    JOIN int_opendevdata__repositories_with_repo_id r
      ON da.repo_id = r.repo_id
    JOIN stg_opendevdata__ecosystems_repos_recursive err
      ON r.opendevdata_id = err.repo_id
    JOIN stg_opendevdata__ecosystems e
      ON err.ecosystem_id = e.id
    WHERE da.bucket_day >= CURRENT_DATE - INTERVAL '30' DAY
      AND e.name IN ('Ethereum', 'Solana', 'Optimism', 'Base')
    GROUP BY e.name
    ORDER BY active_developers DESC
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    _df = mo.sql(
        """
        SELECT
          e.name AS ecosystem,
          COUNT(DISTINCT da.actor_id) AS active_developers,
          SUM(da.num_events) AS total_events
        FROM int_gharchive__developer_activities da
        JOIN int_opendevdata__repositories_with_repo_id r
          ON da.repo_id = r.repo_id
        JOIN stg_opendevdata__ecosystems_repos_recursive err
          ON r.opendevdata_id = err.repo_id
        JOIN stg_opendevdata__ecosystems e
          ON err.ecosystem_id = e.id
        WHERE da.bucket_day >= CURRENT_DATE - INTERVAL '30' DAY
          AND e.name IN ('Ethereum', 'Solana', 'Optimism', 'Base')
        GROUP BY e.name
        ORDER BY active_developers DESC
        """,
        engine=pyoso_db_conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## SQL Dialect

    All queries use [Trino SQL](https://trino.io/docs/current/language.html). A few key differences from other SQL dialects:

    - `CAST(x AS VARCHAR)` not `SAFE_CAST`
    - `DATE_TRUNC('month', dt)` not `DATE_TRUNC(dt, MONTH)`
    - `COALESCE` not `IFNULL`
    - `CURRENT_DATE - INTERVAL '30' DAY` for date math
    """)
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
