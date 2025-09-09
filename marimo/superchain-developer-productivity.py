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
def _(mo):
    mo.md(
        r"""
    # GitHub Metric Comparison

    This notebook compares weekly GitHub metrics for a selected ecosystem against a target ecosystem (Ethereum). The goal is to visualize and understand the trends of various GitHub metrics over time, providing insights into the development activity and community engagement of different crypto ecosystems.

    ## Methodology

    The notebook uses the [OSO](https://docs.opensource.observer/docs/get-started/python) API to query weekly GitHub metrics data. The analysis involves the following steps:

    1.  **Data Selection:** The user selects a comparison ecosystem and a GitHub metric from dropdown menus.
    2.  **Data Query:** The notebook queries the OSO API for the selected metric for both the target ecosystem (Ethereum) and the comparison ecosystem.
    3.  **Data Visualization:** The notebook generates a line chart to visualize the selected metric over time for both ecosystems.

    ## Visualizations

    The notebook generates two visualizations:

    1.  **Line Chart of Weekly GitHub Metrics:** A line chart displays the trend of the selected GitHub metric over time for both the target ecosystem (Ethereum) and the selected comparison ecosystem. This allows for a direct comparison of the two ecosystems' performance in the chosen metric.

    2.  **Normalized Line Chart of Weekly GitHub Metrics:** A line chart displays the trend of the selected GitHub metric over time for both the target ecosystem (Ethereum) and the selected comparison ecosystem, with the data normalized to the initial value of the metric. This allows for a comparison of the relative growth or decline of the metric over time, regardless of the absolute values.
    """
    )
    return


@app.cell
def _():
    import pandas as pd
    import plotly.express as px

    stringify = lambda arr: "'" + "','".join(arr) + "'"
    return pd, px


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

    TARGET_ECOSYSTEM = 'Ethereum'
    COMPARISON_ECOSYSTEMS = [
        'EVM Compatible Layer 2s',
        'Ethereum L2s',
        'Solana',
        'Polygon',
        'Arbitrum',
        'Base',
        'Optimism'
    ]
    ecosystem_dropdown = mo.ui.dropdown(
        options=COMPARISON_ECOSYSTEMS,
        label='Select an ecosystem to compare with',
        full_width=True,
        value='Solana'
    )
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
    metric_dropdown = mo.ui.dropdown(
        options=METRICS,
        label="Select a weekly GitHub metric",
        full_width=True,
        value='Project Velocity'
    )
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
    return (df_pivot,)


@app.cell
def _(
    TARGET_ECOSYSTEM,
    df_pivot,
    ecosystem_dropdown,
    metric_dropdown,
    mo,
    pd,
    px,
):
    df_pivot_normalized = df_pivot.copy()
    for col in df_pivot_normalized.columns[1:]:
        # Calculate the average value for 2025
        avg_2025 = df_pivot_normalized[col][pd.to_datetime(df_pivot_normalized['sample_date']).dt.year == 2025].mean()
        # Use the average value as the initial value for normalization
        initial_value = avg_2025 if pd.notna(avg_2025) and avg_2025 != 0 else df_pivot_normalized[col].iloc[0]
        df_pivot_normalized[col] = df_pivot_normalized[col] / initial_value if initial_value != 0 else 0

    fig_normalized = px.line(df_pivot_normalized, x='sample_date', y=df_pivot_normalized.columns[1:],
                             labels={'value': 'Normalized Value (Avg 2025 = 1)', 'sample_date': 'Date', 'display_name': 'Ecosystem'},
                             title=f'<b>Normalized {metric_dropdown.value} Over Time (Avg 2025 = 1)</b>',
                             color_discrete_map={TARGET_ECOSYSTEM: '#ff0420', ecosystem_dropdown.value: '#007bff'})

    fig_normalized.update_layout(
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
            title_text="Normalized Value"
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
    fig_normalized.update_traces(
        hovertemplate="%{y:.2f}",
        selector=dict(mode='lines')
    )
    mo.ui.plotly(fig_normalized)
    return


if __name__ == "__main__":
    app.run()
