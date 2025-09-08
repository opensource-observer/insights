import marimo

__generated_with = "0.15.2"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.express as px

    client = pyoso.Client()
    return client, mo, pd, px


@app.cell
def _(mo):
    mo.md(
        """
    # Superchain Gas Guzzlers

    This notebook analyzes gas fees within the Superchain ecosystem. The goal is to understand the distribution of gas fees across different chains and projects, and to track the evolution of these fees over time.

    ## Methodology

    We use the [OSO](https://docs.opensource.observer/docs/get-started/python) API to query data about gas fees. The analysis proceeds in two main steps:

    1.  **Overall Gas Fee Distribution:** We query for the total amortized layer 2 gas fees for each project across all time, broken down by chain.
    2.  **Daily Gas Fee Trends:** We query for the daily layer 2 gas fees for each chain to observe trends over time.

    ## Visualizations

    The notebook generates two visualizations to explore this data:

    1.  **Treemap of Gas Fees:** A treemap visualizes the total gas fees, showing the hierarchical relationship between chains and projects. The size of each rectangle represents the total gas fees, and the color represents the magnitude of the fees.
    2.  **Area Chart of Daily Gas Fees:** An area chart displays the daily gas fees for each chain over time, allowing for the observation of trends and comparisons between chains.
    """
    )
    return
    


@app.cell
def _(client):
    df_projects = client.to_pandas("""
    WITH cte AS (
        SELECT DISTINCT
          p.display_name AS project,
          regexp_extract(metric_name, '^(.*)_layer2_gas_fees_amortized_over_all_time', 1) AS chain,
          amount / 1e18 AS amount
        FROM timeseries_metrics_by_project_v0 AS tm
        JOIN projects_v1 p USING (project_id)
        JOIN metrics_v0 m USING (metric_id)
        WHERE metric_name LIKE '%_layer2_gas_fees_amortized_over_all_time'
          AND project_source = 'OSS_DIRECTORY'
        ORDER BY 3 DESC
    )
    SELECT
      project,
      chain,
      amount AS gas_fees
    FROM cte
    JOIN int_superchain_s8_chains USING chain
    """)
    return (df_projects,)


@app.cell
def _(df_projects, mo, px):
    fig = px.treemap(
        data_frame=df_projects,
        path=['chain', 'project'],
        values='gas_fees',
        title='Superchain gas fees by chain and project (over all time)',
        color='gas_fees',
        color_continuous_scale='Reds',
        hover_data=['gas_fees']
    )
    fig.update_layout(
        autosize=True,
        margin=dict(t=50, l=0, r=0, b=0),
    )
    plot = mo.ui.plotly(fig)
    plot
    return


@app.cell
def _(client):
    df_rev = client.to_pandas("""
    SELECT
      bucket_day,
      event_source AS chain,
      SUM(l2_gas_fee / 1e18) AS l2_gas_fee
    FROM int_events_daily__l2_transactions AS t
    JOIN int_superchain_s8_chains AS c ON c.chain = t.event_source
    GROUP BY 1,2
    ORDER BY 1,2
    """)
    return (df_rev,)


@app.cell
def _(df_rev, mo, px):
    fig_chain = px.area(
        data_frame=df_rev,
        x='bucket_day',
        y='l2_gas_fee',
        color='chain'
    )
    fig_chain.update_layout(
        autosize=True,
        margin=dict(t=50, l=0, r=0, b=0),
    )
    mo.ui.plotly(fig_chain)
    return


@app.cell
def _(df_projects):
    df_projects
    return


if __name__ == "__main__":
    app.run()
