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
    df_superchain_tvl_protocols = client.to_pandas("""
    WITH metrics AS (
      SELECT
        sample_date,
        regexp_extract(metric_name, '^(.*)_defillama_tvl_weekly', 1) AS chain,
        project_id,
        amount
      FROM timeseries_metrics_by_project_v0
      JOIN metrics_v0 USING metric_id
      WHERE metric_name LIKE '%_defillama_tvl_weekly'
    )
    SELECT
      sample_date,
      chain,
      display_name AS protocol_name,
      amount,
      project_id
    FROM metrics
    JOIN int_superchain_s8_chains USING chain
    JOIN projects_v1 USING project_id
    WHERE project_source = 'OSS_DIRECTORY'
    ORDER BY 1,2,3
    """)
    df_superchain_tvl_protocols
    return


@app.cell
def _(client):
    df_project_funding = client.to_pandas("""
    SELECT
      p.project_id,
      p.display_name,
      SUM(
        CASE WHEN metric_name = 'OPTIMISM_GOVGRANTS_funding_awarded_over_all_time' THEN amount ELSE 0 END
      ) AS gov_grants,
      SUM(
        CASE WHEN metric_name = 'OPTIMISM_RETROFUNDING_funding_awarded_over_all_time' THEN amount ELSE 0 END
      ) AS retro_funding,
      SUM(amount) AS total_funding
    FROM key_metrics_by_project_v0 AS km
    JOIN metrics_v0 USING metric_id
    JOIN projects_v1 AS p ON km.project_id = p.project_id
    WHERE metric_name IN (
      'OPTIMISM_GOVGRANTS_funding_awarded_over_all_time',
      'OPTIMISM_RETROFUNDING_funding_awarded_over_all_time'
    )
    GROUP BY 1,2
    ORDER BY 5 DESC
    """)
    df_project_funding
    return


@app.cell
def _(client):
    df_project_tvl = client.to_pandas("""
      WITH metrics AS (
        SELECT DISTINCT
          sample_date,
          regexp_extract(metric_name, '^(.*)_defillama_tvl_weekly', 1) AS chain,
          projects_v1.display_name AS protocol,
          projects_v1.project_id,
          amount
        FROM timeseries_metrics_by_project_v0
        JOIN projects_v1 USING project_id
        JOIN metrics_v0 USING metric_id
        WHERE metric_name LIKE '%_defillama_tvl_weekly'
      ),
      SELECT
        m.sample_date,
        m.project,
        m.chain,
        c.chain IS NOT NULL AS is_superchain,
        m.amount
      FROM metrics AS m
      LEFT JOIN projects_by_collection_v1
        ON project_id
      LEFT JOIN int_superchain_s8_chains AS c
      ON m.chain = c.chain
      WHERE m.chain NOT IN ('MAINNET', 'BINANCE', 'AVALANCHE')
      ORDER BY 1,2,3
    """)
    return


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
def _():
    SOURCE_PALETTE = {
        'OPTIMISM': '#ff0420',
        'BASE': '#0052FF',
        'MODE': '#DFFE00',
        'WORLDCHAIN': '#FF6F0F',
        'SONEIUM': '#57F8FE',
        'INK': '#7132F5',
        'UNICHAIN': '#FF007A',
        'OTHER': '#aaa'
    }

    SOURCE_NAMES = list(SOURCE_PALETTE.keys())
    SOURCE_COLORS = list(SOURCE_PALETTE.values())
    return


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
