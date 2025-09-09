import marimo

__generated_with = "0.15.2"
app = marimo.App(width="medium")


@app.cell
def setup_pyoso():
    import marimo as mo
    from pyoso import Client
    client = Client()
    pyoso_db_conn = client.dbapi_connection()
    return mo, client, pyoso_db_conn


@app.cell
def _():
    
    import pandas as pd
    import plotly.express as px

    stringify = lambda arr: "'" + "','".join(arr) + "'"
    return pd, px, stringify


@app.cell
def _(mo):
    # client.to_pandas("""
    # SELECT
    #   project_name,
    #   projects_v1.display_name,
    #   metric_name,
    #   amount
    # FROM projects_v1
    # JOIN key_metrics_by_project_v0 USING project_id
    # JOIN metrics_v0 USING metric_id
    # WHERE
    #   project_source = 'CRYPTO_ECOSYSTEMS'
    #   AND project_namespace = 'eco'
    #   AND metric_name LIKE '%stars%'
    #   AND project_name IN (
    #     'evm_compatible_layer_2s',
    #     'ethereum_l2s',
    #     'ethereum',
    #     'solana',
    #     'polygon',
    #     'arbitrum',
    #     'base'
    #   )
    # ORDER BY amount DESC
    # LIMIT 50
    # """)

    TARGET_ECOSYSTEM = 'Optimism'
    COMPARISON_ECOSYSTEMS = [
        'Ethereum',
        'EVM Compatible Layer 2s',
        'Ethereum L2s',
        'Solana',
        'Polygon',
        'Arbitrum',
        'Base'
    ]
    ecosystem_dropdown = mo.ui.dropdown(options=COMPARISON_ECOSYSTEMS, label='Select an ecosystem to compare with', full_width=True)
    ecosystem_dropdown
    return TARGET_ECOSYSTEM, ecosystem_dropdown


@app.cell
def _(mo):
    # client.to_pandas(f"""
    # SELECT
    #   metric_name,
    #   display_name
    # FROM metrics_v0
    # WHERE
    #   metric_name LIKE 'GITHUB_%'
    #   AND metric_name LIKE '%_weekly'
    #   AND display_name IN ({stringify(METRICS)})
    # """)


    METRICS = sorted([
        'Commits',
        'Opened Pull Requests',
        'Merged Pull Requests',
        'Stars',
        'Forks',
        'Burstiness',
        #'Contributor Absence Factor',
        'Contributors',
        'Repositories',
        'Project Velocity',
        #'Self Merge Rates',
        #'Median Issue Age'
    ])
    metric_dropdown = mo.ui.dropdown(options=METRICS, label="Select a weekly GitHub metric", full_width=True)
    metric_dropdown
    return (metric_dropdown,)


@app.cell
def _(TARGET_ECOSYSTEM, client, ecosystem_dropdown, metric_dropdown):
    query = f"""
    SELECT
      sample_date,
      projects_v1.display_name,
      amount
    FROM timeseries_metrics_by_project_v0
    JOIN projects_v1 USING project_id
    JOIN metrics_v0 USING metric_id
    WHERE
      metrics_v0.display_name = '{metric_dropdown.value}'
      AND metric_name LIKE '%_weekly'
      AND projects_v1.display_name IN ('{TARGET_ECOSYSTEM}','{ecosystem_dropdown.value}')
      AND project_source = 'CRYPTO_ECOSYSTEMS'
      AND project_namespace = 'eco'
    ORDER BY 1,2
    """

    df = client.to_pandas(query)
    return (df,)


@app.cell
def _(TARGET_ECOSYSTEM, df, ecosystem_dropdown, metric_dropdown, mo, px):
    df_pivot = df.pivot(index='sample_date', columns='display_name', values='amount')
    df_pivot = df_pivot.reset_index()

    fig = px.line(df_pivot, x='sample_date', y=df_pivot.columns[1:],
                  labels={'value': metric_dropdown.value, 'sample_date': 'Date', 'display_name': 'Ecosystem'},
                  title=f'<b>{metric_dropdown.value} Over Time</b>',
                  color_discrete_map={TARGET_ECOSYSTEM: '#ff0420', ecosystem_dropdown.value: '#007bff'})

    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_family="Arial",
        title_font_family="Arial",
        title_x=0,
        xaxis_title="",
        yaxis_title="",
        legend_title="",
        autosize=True,
        margin=dict(t=50, l=0, r=0, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray',
            linecolor='black',
            linewidth=1,
            ticks='outside',
            rangemode='tozero',  
        ),
        xaxis=dict(
            showgrid=False,
            linecolor='black',
            linewidth=1,
            ticks='outside',
            tickformat="%b %Y",
            dtick="M6",
            tickangle=-45
        ),
        hovermode="x unified"
    )
    fig.update_traces(
        hovertemplate="%{y:.2f}",
        selector=dict(mode='lines')
    )
    mo.ui.plotly(fig)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
