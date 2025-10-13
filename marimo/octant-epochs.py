import marimo

__generated_with = "0.16.2"
app = marimo.App(width="full")


@app.cell
def about_app(mo):
    mo.vstack([
        mo.md("""
        # Octant Epochs Dashboard
        <small>Author: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2025-10-13</span></small>
        """),
        mo.md("""
        This dashboard tracks funding and OSS developer metrics for projects in Octant funding rounds. 
        Explore funding patterns across epochs and analyze how developer activity correlates with funding received.
        """),
        mo.accordion({
            "<b>Click to see details on how app was made</b>": mo.accordion({
                "Methodology": """
                - Octant funding data is sourced from timeseries metrics in the OSO database
                - Epochs are identified by biannual funding periods based on sample dates
                - Developer metrics include active developers, full-time developers, commits, and contributors
                - Projects can be compared across epochs or analyzed individually over time
                - Funding amounts are displayed alongside selected developer metrics for correlation analysis
                """,
                "Data Sources": """
                - [OSS Directory](https://github.com/opensource-observer/oss-directory)
                - [Octant Funding Events](https://docs.opensource.observer/docs/get-started/using-semantic-layer)
                - [GitHub Activity Metrics](https://www.gharchive.org/)
                - [Pyoso API](https://docs.opensource.observer/docs/get-started/python)
                """,
                "Further Resources": """
                - [Getting Started with Pyoso](https://docs.opensource.observer/docs/get-started/python)
                - [Using the Semantic Layer](https://docs.opensource.observer/docs/get-started/using-semantic-layer)
                - [Marimo Documentation](https://docs.marimo.io/)
                - [Octant Website](https://octant.app/)
                """
            })
        })    
    ])
    return


@app.cell
def get_octant_funding_data(client):
    _query = """
    SELECT
      JSON_EXTRACT_SCALAR(metadata, '$.application_name') as "Project",
      to_project_name AS "OSO Slug",
      CAST(JSON_EXTRACT_SCALAR(metadata, '$.token_amount') AS DOUBLE) as "Amount (ETH)",
      amount AS "Amount (USD)",
      REPLACE(grant_pool_name, 'epoch_', '') AS "Epoch",
      DATE(funding_date) AS "Date"
    FROM stg_ossd__current_funding
    WHERE lower(from_funder_name) LIKE 'octant%'
    ORDER BY 3 DESC
    """

    df_octant_funding = client.to_pandas(_query)
    return (df_octant_funding,)


@app.cell
def get_developer_metrics_data(client, df_octant_funding, pd, stringify):
    _metrics_subset = [
        #"Average Issue Age",
        #"Bot Activity",
        #"Burstiness",
        "Closed Issues",
        "Comments",
        "Commits",
        #"Contributor Absence Factor",
        "Contributors",
        "Forks",
        #"Maximum Issue Age",
        #"Median Issue Age",
        "Merged Pull Requests",
        #"Minimum Issue Age",
        "New Contributors",
        "Opened Issues",
        "Opened Pull Requests",
        #"Project Velocity",
        "Pull Request Comments",
        "Releases",
        "Repositories",
        #"Self Merge Rates",
        "Stars"
    ]

    _project_slugs = df_octant_funding['OSO Slug'].dropna().unique()
    _query = f"""
    SELECT
      p.project_name AS "OSO Slug",
      p.display_name AS "Project Name",
      tm.sample_date AS "Date",
      m.display_name AS "Metric",
      tm.amount AS "Amount"
    FROM timeseries_metrics_by_project_v0 tm
    JOIN metrics_v0 m USING (metric_id)
    JOIN projects_v1 p USING (project_id)
    WHERE
      p.project_name IN ({stringify(_project_slugs)})
      AND p.project_source = 'OSS_DIRECTORY'
      AND m.metric_event_source = 'GITHUB'
      AND m.metric_time_aggregation = 'monthly'
      AND tm.amount IS NOT NULL
      AND m.display_name IN ({stringify(_metrics_subset)})

    ORDER BY 1,3,4
    """

    _df_raw = client.to_pandas(_query)
    _df_raw['Date'] = pd.to_datetime(_df_raw['Date'])
    df_metrics = _df_raw
    return (df_metrics,)


@app.cell
def generate_overview_stats(df_octant_funding, mo):
    _total_eth = df_octant_funding['Amount (ETH)'].sum()
    _total_usd = df_octant_funding['Amount (USD)'].sum()
    _num_epochs = df_octant_funding['Epoch'].nunique()
    _num_projects = df_octant_funding['Project'].nunique()

    _stat1 = mo.stat(
        label="Total Funding (ETH)",
        value=f"{_total_eth:,.2f}",
        caption="ETH awarded",
        bordered=True
    )

    _stat2 = mo.stat(
        label="Total Funding (USD)",
        value=f"${_total_usd:,.0f}",
        caption="USD equivalent",
        bordered=True
    )

    _stat3 = mo.stat(
        label="Epochs",
        value=f"{_num_epochs}",
        caption="Funding rounds analyzed",
        bordered=True
    )

    _stat4 = mo.stat(
        label="Projects",
        value=f"{_num_projects}",
        caption="Unique projects funded",
        bordered=True
    )

    mo.vstack([
        mo.md("## Overview"),
        mo.hstack([_stat1, _stat2, _stat3, _stat4], widths="equal", gap=1)
    ])
    return


@app.cell
def show_funding_table(df_octant_funding, mo):
    mo.vstack([
        mo.md("## Funding Breakdown"),
        mo.ui.table(
            data=df_octant_funding,
            show_data_types=False,
            show_column_summaries=False,
            format_mapping={
                "Amount (ETH)": "{:.2f}",
                "Amount (USD)": "${:,.0f}"
            }
        )
    ])
    return


@app.cell
def epoch_metrics_section(mo):
    mo.md("""## Epoch Metrics Analysis""")
    return


@app.cell
def epoch_selector_ui(df_octant_funding, mo):
    _available_epochs = sorted(df_octant_funding['Epoch'].unique())

    epoch_selector = mo.ui.dropdown(
        options=_available_epochs,
        value=_available_epochs[-1],
        label="**Select Epoch**",
        full_width=True
    )

    mo.hstack([epoch_selector])
    return (epoch_selector,)


@app.cell
def calculate_epoch_metrics(df_metrics, df_octant_funding, epoch_selector, pd):
    # Get the funding date for the selected epoch
    _epoch_funding = df_octant_funding[df_octant_funding['Epoch'] == epoch_selector.value]
    _funding_date = pd.to_datetime(_epoch_funding['Date'].iloc[0])

    # Calculate the date 6 months before funding
    _start_date = _funding_date - pd.DateOffset(months=6)

    # Get all projects funded in this epoch
    _epoch_projects = _epoch_funding['OSO Slug'].unique()

    # Filter metrics for these projects in the 6-month window
    _df_metrics_filtered = df_metrics[
        (df_metrics['OSO Slug'].isin(_epoch_projects)) &
        (pd.to_datetime(df_metrics['Date']) >= _start_date) &
        (pd.to_datetime(df_metrics['Date']) < _funding_date)
    ].copy()

    # Calculate average for each metric and project
    _df_avg = _df_metrics_filtered.groupby(['OSO Slug', 'Project Name', 'Metric'])['Amount'].mean().reset_index()
    _df_avg.columns = ['OSO Slug', 'Project', 'Metric', 'Avg Value']

    # Pivot to get metrics as columns
    _df_pivot = _df_avg.pivot_table(
        index='Project',
        columns='Metric',
        values='Avg Value',
        aggfunc=lambda x: round(x.mean(),1)
    )
    
    df_epoch_metrics = _df_pivot.reset_index()
    return (df_epoch_metrics,)


@app.cell
def show_epoch_metrics_table(df_epoch_metrics, epoch_selector, mo):
    mo.vstack([
        mo.md(f"### 6-Month Average Metrics for OSS Projects (Epoch {epoch_selector.value})"),
        mo.ui.table(
            data=df_epoch_metrics,
            show_data_types=False,
            show_column_summaries=False
        )
    ])
    return


@app.cell
def project_history_section(mo):
    mo.md("""## Project History Analysis""")
    return


@app.cell
def project_history_controls(df_metrics, df_octant_funding, mo):
    _project_options = sorted(df_octant_funding['Project'].unique())
    _metric_options = sorted(df_metrics['Metric'].unique())

    project_selector = mo.ui.dropdown(
        options=_project_options,
        value=_project_options[0],
        label="**Select Project**",
        full_width=True
    )

    metric_selector = mo.ui.dropdown(
        options=_metric_options,
        value=_metric_options[0],
        label="**Select Metric**",
        full_width=True
    )

    currency_toggle = mo.ui.radio(
        options=["USD", "ETH"],
        value="USD",
        label="**Funding Currency**"
    )

    mo.hstack([project_selector, metric_selector, currency_toggle], widths=[1, 1, 1])
    return currency_toggle, metric_selector, project_selector


@app.cell
def prepare_project_history(
    currency_toggle,
    df_metrics,
    df_octant_funding,
    metric_selector,
    pd,
    project_selector,
):
    # Filter funding for selected project
    _df_funding_project = df_octant_funding[
        df_octant_funding['Project'] == project_selector.value
    ].copy()

    # Get the OSO Slug for this project
    _oso_slug = _df_funding_project['OSO Slug'].iloc[0]

    # Filter metrics for selected project and metric
    _df_metrics_project = df_metrics[
        (df_metrics['OSO Slug'] == _oso_slug) &
        (df_metrics['Metric'] == metric_selector.value)
    ][['Date', 'Amount']].copy()

    # Get funding column based on currency selection
    _funding_col = f'Amount ({currency_toggle.value})'

    # Prepare funding data with dates
    _df_funding_project['Date'] = pd.to_datetime(_df_funding_project['Date'])
    _df_funding_project['Month'] = _df_funding_project['Date'].dt.to_period('M')
    _df_funding_agg = _df_funding_project.groupby('Month')[_funding_col].sum().reset_index()
    _df_funding_agg.columns = ['Month', 'Funding Amount']
    _df_funding_agg['Date'] = _df_funding_agg['Month'].dt.to_timestamp()

    # Prepare metrics data
    _df_metrics_project['Date'] = pd.to_datetime(_df_metrics_project['Date'])
    _df_metrics_project['Month'] = _df_metrics_project['Date'].dt.to_period('M')
    _df_metrics_agg = _df_metrics_project.groupby('Month')['Amount'].mean().reset_index()
    _df_metrics_agg.columns = ['Month', 'Metric Value']
    _df_metrics_agg['Date'] = _df_metrics_agg['Month'].dt.to_timestamp()

    # Merge on Date
    _df_history = pd.merge(
        _df_metrics_agg[['Date', 'Metric Value']],
        _df_funding_agg[['Date', 'Funding Amount']],
        on='Date',
        how='outer'
    ).sort_values('Date')

    _df_history['Funding Amount'] = _df_history['Funding Amount'].fillna(0)
    _df_history['Metric Value'] = _df_history['Metric Value'].fillna(0)

    df_project_history = _df_history
    return (df_project_history,)


@app.cell
def generate_project_history_chart(
    currency_toggle,
    df_project_history,
    go,
    metric_selector,
    mo,
    project_selector,
):
    _fig = go.Figure()

    # Add funding bars
    _fig.add_trace(go.Bar(
        x=df_project_history['Date'],
        y=df_project_history['Funding Amount'],
        name=f'Funding ({currency_toggle.value})',
        marker_color='rgba(99, 110, 250, 0.7)',
        yaxis='y'
    ))

    # Add metric line
    _fig.add_trace(go.Scatter(
        x=df_project_history['Date'],
        y=df_project_history['Metric Value'],
        name=metric_selector.value,
        mode='lines+markers',
        line=dict(color='rgba(239, 85, 59, 0.9)', width=2),
        marker=dict(size=6),
        yaxis='y2'
    ))

    _fig.update_layout(
        title=dict(
            text=f"<b>{project_selector.value}: Funding & {metric_selector.value} Over Time</b>",
            x=0,
            xanchor="left"
        ),
        font=dict(size=12, color="#111"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(t=60, l=20, r=80, b=40),
        hovermode='x unified',
        yaxis=dict(
            title=f"Funding ({currency_toggle.value})",
            side="left",
            showgrid=True,
            gridcolor='#f0f0f0'
        ),
        yaxis2=dict(
            title=metric_selector.value,
            side="right",
            overlaying="y",
            showgrid=False
        ),
        xaxis=dict(
            title="Date",
            showgrid=True,
            gridcolor='#f0f0f0'
        ),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )

    mo.ui.plotly(_fig)
    return


@app.cell
def _():
    stringify = lambda arr: "'" + "','".join(arr) + "'"
    return (stringify,)


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import marimo as mo
    from pyoso import Client
    client = Client()
    pyoso_db_conn = client.dbapi_connection()    
    return client, mo


@app.cell
def import_libraries():
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    return go, pd


if __name__ == "__main__":
    app.run()
