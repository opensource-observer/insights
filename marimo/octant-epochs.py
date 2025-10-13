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
def _(df_octant_funding, mo):
    mo.ui.table(
        data=df_octant_funding,
        show_data_types=False,
        show_column_summaries=False,
        format_mapping={
            "Amount (ETH)": "{:.2f}",
            "Amount (USD)": "${:,.0f}"
        }
    )
    return


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
def configuration_settings(df_metrics, df_octant_funding, mo):
    _available_epochs = sorted(df_octant_funding['Epoch'].unique())
    _metric_options = sorted(df_metrics['Metric'].unique())

    epoch_filter = mo.ui.multiselect(
        options=_available_epochs,
        value=_available_epochs[-1],
        label="**Select Epochs**",
        full_width=True
    )
    metric_selector = mo.ui.dropdown(
        options=_metric_options,
        value=_metric_options[0],
        label="**Select Developer Metric**",
        full_width=True
    )

    mo.vstack([
        mo.md("## Configuration"),
        epoch_filter,
        metric_selector
    ])
    return epoch_filter, metric_selector


@app.cell
def filter_and_combine_data(
    df_metrics,
    df_octant_funding,
    epoch_filter,
    metric_selector,
    pd,
):
    # Filter funding by selected epochs
    if len(df_octant_funding) > 0 and len(epoch_filter.value) > 0:
        _df_funding_filtered = df_octant_funding[
            df_octant_funding['Epoch'].isin(epoch_filter.value)
        ].copy()
    else:
        _df_funding_filtered = pd.DataFrame(columns=df_octant_funding.columns if len(df_octant_funding) > 0 else [])

    # Filter metrics by selected metric type
    if len(df_metrics) > 0 and len(_df_funding_filtered) > 0:
        _df_metrics_filtered = df_metrics[
            df_metrics['Metric'] == metric_selector.value
        ].copy()

        # Aggregate funding by project and epoch
        _df_funding_agg = _df_funding_filtered.groupby(['OSO Slug', 'Epoch', 'Project']).agg({
            'Amount (USD)': 'sum',
            'Date': 'first'
        }).reset_index()

        # Get the month of the funding date for joining with metrics
        _df_funding_agg['Month'] = pd.to_datetime(_df_funding_agg['Date']).dt.to_period('M')
        _df_metrics_filtered['Month'] = pd.to_datetime(_df_metrics_filtered['Date']).dt.to_period('M')

        # Merge funding and metrics
        _df_combined = pd.merge(
            _df_funding_agg,
            _df_metrics_filtered[['OSO Slug', 'Month', 'Amount']],
            on=['OSO Slug', 'Month'],
            how='left'
        )
        _df_combined['Amount'] = _df_combined['Amount'].fillna(0)
        _df_combined = _df_combined.rename(columns={'Amount': 'Metric Value'})
    else:
        _df_combined = _df_funding_filtered.copy()
        if len(_df_combined) > 0:
            _df_combined['Metric Value'] = 0

    df_combined = _df_combined
    return (df_combined,)


@app.cell
def prepare_project_history(
    df_metrics,
    df_octant_funding,
    metric_selector,
    pd,
    project_selector,
):
    if project_selector.value is None or len(df_octant_funding) == 0:
        df_project_history = pd.DataFrame(columns=[
            'Date', 'Funding Amount', 'Metric Value'
        ])
    else:
        # Filter funding for selected project
        _df_funding_project = df_octant_funding[
            df_octant_funding['Project'] == project_selector.value
        ][['Date', 'Amount (USD)', 'Epoch']].copy()

        # Get the OSO Slug for this project
        _oso_slug = df_octant_funding[
            df_octant_funding['Project'] == project_selector.value
        ]['OSO Slug'].iloc[0] if len(_df_funding_project) > 0 else None

        # Filter metrics for selected project and metric
        if len(df_metrics) > 0 and _oso_slug is not None:
            _df_metrics_project = df_metrics[
                (df_metrics['Project Name'] == project_selector.value) &
                (df_metrics['Metric'] == metric_selector.value)
            ][['Date', 'Amount']].copy()
        else:
            _df_metrics_project = pd.DataFrame(columns=['Date', 'Amount'])

        # Get full date range by month
        if len(_df_funding_project) > 0 or len(_df_metrics_project) > 0:
            _funding_dates = pd.to_datetime(_df_funding_project['Date']) if len(_df_funding_project) > 0 else pd.Series(dtype='datetime64[ns]')
            _metric_dates = pd.to_datetime(_df_metrics_project['Date']) if len(_df_metrics_project) > 0 else pd.Series(dtype='datetime64[ns]')

            _all_dates = pd.concat([_funding_dates, _metric_dates]).dt.to_period('M').unique()
            _all_dates = pd.PeriodIndex(_all_dates).to_timestamp()
            _df_history = pd.DataFrame({'Date': sorted(_all_dates)})
            _df_history['Month'] = pd.to_datetime(_df_history['Date']).dt.to_period('M')

            # Prepare funding data
            if len(_df_funding_project) > 0:
                _df_funding_project['Date'] = pd.to_datetime(_df_funding_project['Date'])
                _df_funding_project['Month'] = _df_funding_project['Date'].dt.to_period('M')
                _df_funding_agg = _df_funding_project.groupby('Month')['Amount (USD)'].sum().reset_index()
                _df_funding_agg.columns = ['Month', 'Funding Amount']

                _df_history = pd.merge(
                    _df_history,
                    _df_funding_agg,
                    on='Month',
                    how='left'
                )
            else:
                _df_history['Funding Amount'] = 0

            # Prepare metrics data
            if len(_df_metrics_project) > 0:
                _df_metrics_project['Date'] = pd.to_datetime(_df_metrics_project['Date'])
                _df_metrics_project['Month'] = _df_metrics_project['Date'].dt.to_period('M')
                _df_metrics_agg = _df_metrics_project.groupby('Month')['Amount'].mean().reset_index()
                _df_metrics_agg.columns = ['Month', 'Metric Value']

                _df_history = pd.merge(
                    _df_history,
                    _df_metrics_agg,
                    on='Month',
                    how='left'
                )
            else:
                _df_history['Metric Value'] = 0

            _df_history['Funding Amount'] = _df_history['Funding Amount'].fillna(0)
            _df_history['Metric Value'] = _df_history['Metric Value'].fillna(0)
            _df_history = _df_history[['Date', 'Funding Amount', 'Metric Value']]
        else:
            _df_history = pd.DataFrame(columns=['Date', 'Funding Amount', 'Metric Value'])

        df_project_history = _df_history
    return (df_project_history,)


@app.cell
def generate_epoch_overview_stats(df_combined, epoch_filter, mo):
    if len(df_combined) > 0 and 'Amount (USD)' in df_combined.columns:
        _total_projects = df_combined['Project'].nunique()
        _total_funding = df_combined['Amount (USD)'].sum()
        _avg_metric = df_combined['Metric Value'].mean() if 'Metric Value' in df_combined.columns else 0

        _stat1 = mo.stat(
            label="Projects Funded",
            value=f"{_total_projects:,}",
            caption=f"across {len(epoch_filter.value)} epoch(s)"
        )

        _stat2 = mo.stat(
            label="Total Funding",
            value=f"${_total_funding:,.0f}",
            caption="USD awarded"
        )

        _stat3 = mo.stat(
            label=f"Avg Metric",
            value=f"{_avg_metric:,.1f}",
            caption="average value"
        )
    else:
        _stat1 = mo.stat(label="Projects Funded", value="0")
        _stat2 = mo.stat(label="Total Funding", value="$0")
        _stat3 = mo.stat(label="Avg Metric", value="0")

    mo.vstack([
        mo.md("## Epoch Overview"),
        mo.hstack([_stat1, _stat2, _stat3])
    ])
    return


@app.cell
def generate_epoch_overview_table(df_combined, mo, pd):
    if len(df_combined) > 0 and 'Amount (USD)' in df_combined.columns:
        _cols_to_show = ['Epoch', 'Project', 'Amount (USD)']
        if 'Metric Value' in df_combined.columns:
            _cols_to_show.append('Metric Value')

        _df_table = df_combined[_cols_to_show].copy()
        _df_table.columns = ['Epoch', 'Project', 'Funding (USD)'] + (['Metric Value'] if 'Metric Value' in df_combined.columns else [])
        _df_table = _df_table.sort_values(['Epoch', 'Funding (USD)'], ascending=[True, False])
    else:
        _df_table = pd.DataFrame(columns=['Epoch', 'Project', 'Funding (USD)', 'Metric Value'])

    mo.ui.table(_df_table, page_size=10)
    return


@app.cell
def generate_epoch_overview_plot(df_combined, go, metric_selector, mo, px):
    if len(df_combined) > 0 and 'Amount (USD)' in df_combined.columns and 'Metric Value' in df_combined.columns:
        _fig = px.scatter(
            df_combined,
            x='Amount (USD)',
            y='Metric Value',
            color='Epoch',
            hover_data=['Project'],
            labels={
                'Amount (USD)': 'Funding Amount (USD)',
                'Metric Value': metric_selector.value,
                'Epoch': 'Epoch'
            },
            title=f"<b>Funding vs {metric_selector.value}</b>"
        )

        _fig.update_layout(
            font=dict(size=12, color="#111"),
            title=dict(x=0, xanchor="left"),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=40, l=20, r=20, b=20),
            legend=dict(
                title="Epoch",
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            )
        )

        _fig.update_xaxes(showgrid=True, gridcolor='#f0f0f0')
        _fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0')
    else:
        _fig = go.Figure()
        _fig.add_annotation(
            text="No data available for selected epochs",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="#999")
        )
        _fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=40, l=20, r=20, b=20)
        )

    mo.ui.plotly(_fig)
    return


@app.cell
def generate_project_history_plot(mo, project_selector):
    mo.md(f"""## Project History: {project_selector.value if project_selector.value else 'None Selected'}""")
    return


@app.cell
def generate_project_history_chart(
    df_project_history,
    go,
    metric_selector,
    mo,
    project_selector,
):
    if len(df_project_history) > 0 and project_selector.value is not None:
        _fig = go.Figure()

        # Add funding bars
        _fig.add_trace(go.Bar(
            x=df_project_history['Date'],
            y=df_project_history['Funding Amount'],
            name='Funding (USD)',
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
                text=f"<b>Funding & {metric_selector.value} Over Time</b>",
                x=0,
                xanchor="left"
            ),
            font=dict(size=12, color="#111"),
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=60, l=20, r=80, b=40),
            hovermode='x unified',
            yaxis=dict(
                title="Funding (USD)",
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
    else:
        _fig = go.Figure()
        _fig.add_annotation(
            text="No data available" if project_selector.value is None else f"No data for {project_selector.value}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="#999")
        )
        _fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=40, l=20, r=20, b=20)
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
    return go, pd, px


if __name__ == "__main__":
    app.run()
