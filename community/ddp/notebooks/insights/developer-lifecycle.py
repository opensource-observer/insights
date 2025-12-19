import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")

@app.cell(hide_code=True)
def _(mo):
    mo.vstack([
            mo.md("""
            # **Ethereum Developer Lifecycle**
            """),
            mo.md("""
            This app visualizes monthly trends of new, churned, and active contributors to open source software projects in Ethereum and other Crypto Ecosystems.
            """),            
        ])
    return


@app.cell(hide_code=True)
def _(df, mo):
    project_list = sorted(list(df['project_display_name'].unique()))
    project_input = mo.ui.dropdown(
        options=project_list,
        value='Ethereum',
        label='Select an Ecosystem:',
        full_width=True
    )
    activity_input = mo.ui.switch(
        label='Show inactive developers',
        value=False
    )
    mo.vstack([
        mo.md("### Configuration:"),
        mo.hstack([project_input, activity_input], widths=[1,1], gap=5, align="end", justify="end")
    ])
    return activity_input, project_input


@app.cell(hide_code=True)
def _(activity_input, df, mo, pd, project_input, px):
    _df = df[df['project_display_name'] == project_input.value].copy()

    _color_mapping = {
        # Onboarding
        'first time': '#4C78A8',                 # blue

        # Full-time family
        'full time': '#7A4D9B',                  # purple
        'new full time': '#9C6BD3',
        'part time to full time': '#B48AEC',
        'dormant to full time': '#C7A7F2',

        # Part-time family
        'part time': '#41AB5D',                  # green
        'new part time': '#74C476',
        'full time to part time': '#A1D99B',
        'dormant to part time': '#C7E9C0',

        # Dormant
        'dormant': '#F39C12',                    # amber
        'first time to dormant': '#F5B041',
        'part time to dormant': '#F8C471',
        'full time to dormant': '#FAD7A0',

        # Churned
        'churned (after first time)': '#D62728',  # red
        'churned (after reaching part time)': '#E57373',
        'churned (after reaching full time)': '#F1948A',
    }
    _label_order = [
        'first time',

        'full time',
        'new full time',
        'part time to full time',
        'dormant to full time',

        'part time',
        'new part time',
        'full time to part time',
        'dormant to part time',

        'dormant',
        'first time to dormant',
        'part time to dormant',
        'full time to dormant',

        'churned (after first time)',
        'churned (after reaching part time)',
        'churned (after reaching full time)',
    ]
    _inactive_labels = [
        'dormant',
        'first time to dormant',
        'part time to dormant',
        'full time to dormant',

        'churned (after first time)',
        'churned (after reaching part time)',
        'churned (after reaching full time)',
    ]
    if activity_input.value:
        _display_labels = _label_order
    else:
        _display_labels = [c for c in _label_order if c not in _inactive_labels]

    _df['label'] = pd.Categorical(_df['label'], categories=_label_order, ordered=True)
    _fig = px.bar(
        data_frame=_df[_df['label'].isin(_display_labels)],
        x='bucket_month',
        y='developers_count',
        color='label',
        color_discrete_map=_color_mapping,
        category_orders={'label': _label_order},
    )
    _fig.update_layout(
        barmode='stack',
        template='plotly_white',
        legend_title_text='Lifecycle State',
        margin=dict(t=0, l=0, r=100, b=0),
    )
    _fig.update_xaxes(title='', showgrid=False,
                linecolor="#000", linewidth=1,
                ticks="outside", tickformat="%b %Y")
    _fig.update_yaxes(title="",
                showgrid=True, gridcolor="#DDD",
                zeroline=True, zerolinecolor="black", zerolinewidth=1,
                linecolor="#000", linewidth=1,
                ticks="outside", range=[0, None])
    mo.vstack([
        mo.md("### Developer Lifecycle Analysis"),
        mo.ui.plotly(_fig, config={'displayModeBar': False}),
        mo.md("""
            - Contributions include commits, issues, pull requests, and code reviews
            - A *contributor* is defined as a GitHub user who has made at least one contribution to the project in the given month
            - *New* contributors are contributors who have made their first contribution to the project in the given month
            - *Churned* contributors are contributors who were active in the project in the previous month, but are no longer active in the current month
            - *Active* contributors are contributors who have made at least one contribution to the project in the given month
            - Data is bucketed into monthly intervals, going back to the earliest available data for the project
            - If contributions were made while a repo was private or associated with another organization, those events are not included in the data
            - Data is refreshed and backfilled on a monthly basis
            """),    
    ])
    return


@app.cell
def _(mo, pyoso_db_conn):
    df = mo.sql(
        f"""
        SELECT
          project_display_name,
          bucket_month, 
          label,
          developers_count
        FROM int_crypto_ecosystems_developer_lifecycle_monthly_aggregated
        ORDER BY 1,2,3
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df,)


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    return pd, px


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
