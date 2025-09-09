import marimo

__generated_with = "0.15.2"
app = marimo.App(width="medium")


@app.cell
def setup_pyoso():
    import marimo as mo
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
    df = client.to_pandas("""
      WITH metrics AS (
        SELECT DISTINCT
          sample_date,
          regexp_extract(metric_name, '^(.*)_defillama_tvl_weekly', 1) AS chain,
          projects_v1.display_name AS project,
          amount
        FROM timeseries_metrics_by_project_v0
        JOIN projects_v1 USING project_id
        JOIN projects_by_collection_v1 USING project_id
        JOIN metrics_v0 USING metric_id
        WHERE
          metric_name LIKE '%_defillama_tvl_weekly'
          AND collection_namespace = 'retro-funding'
      )
      SELECT
        m.sample_date,
        m.project,
        m.chain,
        c.chain IS NOT NULL AS is_superchain,
        m.amount
      FROM metrics AS m
      LEFT JOIN int_superchain_s8_chains AS c
      ON m.chain = c.chain
      WHERE m.chain NOT IN ('MAINNET', 'BINANCE', 'AVALANCHE')
      ORDER BY 1,2,3
    """)
    return (df,)


@app.cell
def _(df):
    import plotly.express as px
    df_grouped = df.groupby(['sample_date', 'chain'])['amount'].sum().reset_index()
    fig = px.area(df_grouped, x='sample_date', y='amount', color='chain',
                  title='TVL of Superchain vs. Non-Superchain Projects',
                  labels={'amount': 'TVL (USD)', 'sample_date': 'Date', 'is_superchain': 'Is Superchain'})
    fig
    return (px,)


@app.cell
def _(df):
    df['chain'].value_counts()
    return


@app.cell
def _(df, px):
    df_non_superchain = df[(df['is_superchain'] == False) & (df['sample_date'] < '2022-01-01')]
    df_grouped_non_superchain = df_non_superchain.groupby('chain')['amount'].sum().reset_index()
    df_grouped_non_superchain = df_grouped_non_superchain.sort_values(by='amount', ascending=False)
    fig_non_superchain = px.bar(df_grouped_non_superchain, x='chain', y='amount',
                                 title='TVL of Non-Superchain Chains',
                                 labels={'amount': 'TVL (USD)', 'chain': 'Chain'},
                                 color='chain',
                                 text_auto=True)
    fig_non_superchain
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
