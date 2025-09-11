import marimo

__generated_with = "0.15.2"
app = marimo.App(width="medium")


@app.cell
def setup_pyoso():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    from pyoso import Client

    # client = Client()
    # pyoso_db_conn = client.dbapi_connection()

    import os
    from dotenv import load_dotenv
    load_dotenv()
    client = Client(api_key=os.environ['OSO_API_KEY'])
    return (client,)


@app.cell
def _(client):
    client.to_pandas("""
    SELECT
      event_source,
      round_name,
      round_id,
      round_number,
      gitcoin_project_name,
      MIN()
      SUM(amount_in_usd) AS total_donations
    FROM int_events__gitcoin_funding AS e
    JOIN int_projects__gitcoin AS g ON g.project_name = e.gitcoin_group_id
    WHERE g.display_name = 'protocol guild'
    GROUP BY 1,2,3,4,5
    """)
    return


@app.cell
def _(client):
    client.to_pandas("""
    SELECT SUM(amount_in_usd) AS total_donations
    FROM int_events__gitcoin_funding
    """)
    return


@app.cell
def _(client):
    client.to_pandas("""
    SELECT
      donor_address,
      SUM(amount_in_usd) AS total_donations
    FROM int_events__gitcoin_funding AS e
    JOIN int_projects__gitcoin AS g ON g.project_name = e.gitcoin_group_id
    WHERE LENGTH(donor_address) = 42
    GROUP BY 1
    ORDER BY 2 DESC
    LIMIT 100
    """)
    return


@app.cell
def _(client):
    client.to_pandas("""
    SELECT *
    FROM int_events__gitcoin_funding 
    WHERE donor_address = '0x386ea3171dcc9405311fd75b316cc2a87ecadeca'

    """)
    return


app._unparsable_cell(
    r"""
    web3.
    """,
    name="_"
)


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
