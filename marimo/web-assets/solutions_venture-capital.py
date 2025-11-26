import marimo

__generated_with = "0.17.5"
app = marimo.App(width="full")


@app.cell
def title_markdown(mo):
    mo.md(r"""
    # How do these companies compare?
    """)
    return


@app.cell
def analysis_settings(mo, startup_list):
    startup_1 = mo.ui.dropdown(
        options=startup_list,
        value=startup_list[0],
        label="Startup 1:"
    )
    startup_2 = mo.ui.dropdown(
        options=startup_list,
        value=startup_list[1],
        label="Startup 2:"
    )
    metric_selector = mo.ui.dropdown(
        options=["Developers", "Users", "Onchain Revenue"],
        value="Developers",
        label="Metric:"
    )
    mo.vstack([
        mo.md("### Analysis Settings"),
        mo.hstack([startup_1, startup_2, metric_selector], widths="equal", gap=2)
    ])
    return metric_selector, startup_1, startup_2


@app.cell
def analysis_results(
    df_funding,
    df_metrics,
    make_figure,
    metric_selector,
    mo,
    startup_1,
    startup_2,
):
    # Get selected metric column name
    metric_map = {
        "Developers": "developers",
        "Users": "users", 
        "Onchain Revenue": "revenue"
    }
    selected_metric = metric_map[metric_selector.value]

    # Get data for selected startups
    startup_1_data = df_metrics[df_metrics['startup'] == startup_1.value][['month', selected_metric]].copy()
    startup_2_data = df_metrics[df_metrics['startup'] == startup_2.value][['month', selected_metric]].copy()

    # Get funding data for selected startups
    startup_1_funding = df_funding[df_funding['startup'] == startup_1.value]
    startup_2_funding = df_funding[df_funding['startup'] == startup_2.value]

    # Calculate summary metrics
    p1_current = startup_1_data[selected_metric].iloc[-1]
    p1_start = startup_1_data[selected_metric].iloc[0]
    p1_growth = ((p1_current / p1_start) - 1) * 100 if p1_start > 0 else 0

    p2_current = startup_2_data[selected_metric].iloc[-1]
    p2_start = startup_2_data[selected_metric].iloc[0]
    p2_growth = ((p2_current / p2_start) - 1) * 100 if p2_start > 0 else 0

    # Total funding
    p1_total_funding = startup_1_funding['amount'].sum()
    p2_total_funding = startup_2_funding['amount'].sum()

    # Metric formatting
    def format_metric(value, metric):
        if metric == "revenue":
            return f"${value:,.0f}"
        else:
            return f"{value:,.0f}"

    # Generate the figure
    _fig = make_figure(
        startup_1_data=startup_1_data,
        startup_2_data=startup_2_data,
        startup_1_funding=startup_1_funding,
        startup_2_funding=startup_2_funding,
        startup_1_name=startup_1.value,
        startup_2_name=startup_2.value,
        metric_col=selected_metric,
        metric_name=metric_selector.value
    )

    # Create stats widgets
    stat1 = mo.stat(
        label=f"{startup_1.value} Current", 
        bordered=True, 
        value=format_metric(p1_current, selected_metric),
        caption=f"{p1_growth:+.0f}% growth from start"
    )
    stat2 = mo.stat(
        label=f"{startup_1.value} Funding", 
        bordered=True, 
        value=f"${p1_total_funding:,.0f}M",
        caption=f"{len(startup_1_funding)} rounds"
    )
    stat3 = mo.stat(
        label=f"{startup_2.value} Current", 
        bordered=True, 
        value=format_metric(p2_current, selected_metric),
        caption=f"{p2_growth:+.0f}% growth from start"
    )
    stat4 = mo.stat(
        label=f"{startup_2.value} Funding", 
        bordered=True, 
        value=f"${p2_total_funding:,.0f}M",
        caption=f"{len(startup_2_funding)} rounds"
    )

    # Generate the results dashboard
    mo.vstack([
        mo.md("### Comparison Results"),
        mo.hstack([stat1, stat2, stat3, stat4], widths="equal", gap=1),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return


@app.cell
def make_figure(go):
    COLOR_STARTUP_1 = '#253494'   # Darker blue/purple
    COLOR_STARTUP_2 = '#2C7FB8'   # Blue

    def make_figure(startup_1_data, startup_2_data, startup_1_funding, startup_2_funding, 
                    startup_1_name, startup_2_name, metric_col, metric_name):
        fig = go.Figure()

        # Add startup 1 line
        fig.add_trace(go.Scatter(
            x=startup_1_data['month'],
            y=startup_1_data[metric_col],
            mode='lines+markers',
            name=startup_1_name,
            line=dict(color=COLOR_STARTUP_1, width=3),
            marker=dict(size=6, color=COLOR_STARTUP_1),
            hovertemplate='%{x|%b %Y}<br>%{y:,.0f}<extra></extra>'
        ))

        # Add startup 2 line
        fig.add_trace(go.Scatter(
            x=startup_2_data['month'],
            y=startup_2_data[metric_col],
            mode='lines+markers',
            name=startup_2_name,
            line=dict(color=COLOR_STARTUP_2, width=3),
            marker=dict(size=6, color=COLOR_STARTUP_2),
            hovertemplate='%{x|%b %Y}<br>%{y:,.0f}<extra></extra>'
        ))

        # Add funding event annotations for startup 1
        shapes = []
        annotations = []

        for _, row in startup_1_funding.iterrows():
            funding_date = row['month']
            funding_amount = row['amount']
            round_name = row['round_name']

            # Add vertical dashed line
            shapes.append(dict(
                type='line',
                x0=funding_date,
                x1=funding_date,
                y0=0,
                y1=1,
                yref='paper',
                line=dict(color=COLOR_STARTUP_1, width=1.5, dash='dash')
            ))

            # Add annotation
            annotations.append(dict(
                x=funding_date,
                y=0.98,
                xref='x',
                yref='paper',
                text=f"{round_name} for {startup_1_name}<br>${funding_amount}M",
                showarrow=False,
                textangle=0,
                yanchor='top',
                font=dict(size=10, color=COLOR_STARTUP_1),
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor=COLOR_STARTUP_1,
                borderwidth=1
            ))

        # Add funding event annotations for startup 2
        for _, row in startup_2_funding.iterrows():
            funding_date = row['month']
            funding_amount = row['amount']
            round_name = row['round_name']

            # Add vertical dashed line
            shapes.append(dict(
                type='line',
                x0=funding_date,
                x1=funding_date,
                y0=0,
                y1=1,
                yref='paper',
                line=dict(color=COLOR_STARTUP_2, width=1.5, dash='dash')
            ))

            # Add annotation
            annotations.append(dict(
                x=funding_date,
                y=0.90,
                xref='x',
                yref='paper',
                text=f"{round_name} for {startup_2_name}<br>${funding_amount}M",
                showarrow=False,
                textangle=0,
                yanchor='top',
                font=dict(size=10, color=COLOR_STARTUP_2),
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor=COLOR_STARTUP_2,
                borderwidth=1
            ))

        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(size=12, color="#111"),
            margin=dict(l=60, r=20, t=20, b=50),
            title="",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            hovermode='x unified',
            shapes=shapes,
            annotations=annotations
        )
        fig.update_xaxes(
            title="",
            showgrid=True,
            gridcolor="#E5E5E5",
            visible=True,
            linecolor="#000",
            linewidth=1
        )
        fig.update_yaxes(
            title=metric_name,
            showgrid=True,
            gridcolor="#E5E5E5",
            visible=True,
            linecolor="#000",
            linewidth=1,
            zeroline=True
        )

        return fig
    return (make_figure,)


@app.cell
def get_data(pd):
    # Dummy metrics data
    months = pd.date_range(start='2023-01-01', end='2024-12-01', freq='MS')

    # Startup A: Fast growing startup
    startup_a_devs = [12, 15, 18, 22, 28, 35, 42, 48, 55, 62, 70, 78, 85, 92, 98, 105, 112, 118, 125, 132, 138, 145, 152, 158]
    startup_a_users = [500, 650, 850, 1100, 1500, 2000, 2600, 3300, 4200, 5200, 6300, 7500, 8800, 10200, 11700, 13300, 15000, 16800, 18700, 20700, 22800, 25000, 27300, 29700]
    startup_a_revenue = [5000, 7000, 9500, 13000, 18000, 25000, 34000, 45000, 58000, 73000, 90000, 109000, 130000, 153000, 178000, 205000, 234000, 265000, 298000, 333000, 370000, 409000, 450000, 493000]

    # Startup B: Steady growth
    startup_b_devs = [25, 28, 30, 32, 35, 38, 40, 43, 46, 49, 52, 55, 58, 61, 64, 67, 70, 73, 76, 79, 82, 85, 88, 91]
    startup_b_users = [2000, 2200, 2400, 2650, 2900, 3200, 3500, 3850, 4200, 4600, 5000, 5450, 5900, 6400, 6900, 7450, 8000, 8600, 9200, 9850, 10500, 11200, 11900, 12650]
    startup_b_revenue = [30000, 33000, 36000, 40000, 44000, 49000, 54000, 60000, 66000, 73000, 80000, 88000, 97000, 106000, 116000, 127000, 139000, 152000, 166000, 181000, 197000, 214000, 232000, 251000]

    # Startup C: Mature with slower growth
    startup_c_devs = [50, 52, 53, 55, 56, 58, 60, 61, 63, 65, 66, 68, 70, 71, 73, 75, 76, 78, 80, 81, 83, 85, 86, 88]
    startup_c_users = [8000, 8400, 8800, 9250, 9700, 10200, 10700, 11250, 11800, 12400, 13000, 13650, 14300, 15000, 15700, 16450, 17200, 18000, 18800, 19650, 20500, 21400, 22300, 23250]
    startup_c_revenue = [120000, 126000, 132000, 139000, 146000, 153000, 161000, 169000, 177000, 186000, 195000, 205000, 215000, 226000, 237000, 249000, 261000, 274000, 287000, 301000, 316000, 332000, 348000, 365000]

    df_metrics = pd.DataFrame({
        'startup': ['Startup A'] * len(months) + ['Startup B'] * len(months) + ['Startup C'] * len(months),
        'month': list(months) * 3,
        'developers': startup_a_devs + startup_b_devs + startup_c_devs,
        'users': startup_a_users + startup_b_users + startup_c_users,
        'revenue': startup_a_revenue + startup_b_revenue + startup_c_revenue
    })

    # Funding rounds data
    df_funding = pd.DataFrame({
        'startup': ['Startup A', 'Startup A', 'Startup B', 'Startup B', 'Startup C'],
        'month': pd.to_datetime(['2023-03-01', '2024-02-01', '2023-05-01', '2024-06-01', '2023-08-01']),
        'amount': [0.5, 3.5, 2.5, 20.0, 10.0],  # in millions
        'round_name': ['Seed', 'Series A', 'Series A', 'Series B', 'Seed']
    })

    startup_list = ['Startup A', 'Startup B', 'Startup C']
    return df_funding, df_metrics, startup_list


@app.cell
def import_libraries():
    import pandas as pd
    import plotly.graph_objects as go
    return go, pd


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return (mo,)


if __name__ == "__main__":
    app.run()
