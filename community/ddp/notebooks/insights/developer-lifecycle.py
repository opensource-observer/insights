import marimo

__generated_with = "unknown"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Lifecycle Analysis
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-02-17</span></small>

    Visualize the full lifecycle of a developer joining, contributing, and leaving an ecosystem.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion({
        "Definitions & Methodology": mo.md("""
**Lifecycle labels** classify each developer's monthly activity into one of 16 states. These roll up into 4 categories used in the summary chart:

| Category | Label | Description |
|:---------|:------|:------------|
| **First Time** `#4C78A8` | `first time` | First-ever contribution to the ecosystem |
| **Full Time** `#7A4D9B` | `full time` | 10+ active days, continuing from prior month |
| | `new full time` | First month reaching 10+ active days |
| | `part time to full time` | Transitioned from part-time level |
| | `dormant to full time` | Returned from dormancy at full-time level |
| **Part Time** `#41AB5D` | `part time` | 1-9 active days, continuing from prior month |
| | `new part time` | First month at part-time level |
| | `full time to part time` | Stepped down from full-time level |
| | `dormant to part time` | Returned from dormancy at part-time level |
| **Churned / Dormant** `#D62728` | `dormant` | No activity this month (previously active) |
| | `first time to dormant` | Dormant after first contribution |
| | `part time to dormant` | Dormant after part-time activity |
| | `full time to dormant` | Dormant after full-time activity |
| | `churned (after first time)` | Extended inactivity after first contribution |
| | `churned (after reaching part time)` | Extended inactivity after reaching part time |
| | `churned (after reaching full time)` | Extended inactivity after reaching full time |

**Active** = First Time + Full Time + Part Time (all 9 labels above the Churned/Dormant group)

**Derived metrics:**
- **Churn Ratio** = sum(churned + dormant) / sum(active) over the trailing window (12mo or all-time)
- **Dormant (Current)** = dormant-label developers in the latest month
- **Dormant (6mo Avg)** = mean monthly dormant count over the last 6 months

**Data source:** `int_crypto_ecosystems_developer_lifecycle_monthly_aggregated` with ecosystem definitions from Electric Capital's taxonomy. Contributions include commits, issues, pull requests, and code reviews. Monthly bucketed; private repos excluded.
        """),
    })
    return


@app.cell(hide_code=True)
def _():
    ACTIVE_LABELS = [
        'first time', 'full time', 'new full time', 'part time to full time',
        'dormant to full time', 'part time', 'new part time',
        'full time to part time', 'dormant to part time',
    ]
    FT_LABELS = ['full time', 'new full time', 'part time to full time', 'dormant to full time']
    PT_LABELS = ['part time', 'new part time', 'full time to part time', 'dormant to part time']
    DORMANT_LABELS = [
        'dormant', 'first time to dormant', 'part time to dormant', 'full time to dormant',
    ]
    CHURNED_LABELS = [
        'churned (after first time)', 'churned (after reaching part time)',
        'churned (after reaching full time)',
    ]
    return ACTIVE_LABELS, CHURNED_LABELS, DORMANT_LABELS, FT_LABELS, PT_LABELS


@app.cell(hide_code=True)
def _(df, mo):
    project_list = sorted(list(df['project_display_name'].unique()))
    project_input = mo.ui.dropdown(
        options=project_list,
        value='Ethereum',
        label='Select Ecosystem',
        full_width=False
    )
    project_input
    return (project_input,)


@app.cell(hide_code=True)
def _(ACTIVE_LABELS, CHURNED_LABELS, DORMANT_LABELS, FT_LABELS, PT_LABELS, df, mo, pd, project_input):
    _df = df[df['project_display_name'] == project_input.value].copy()

    # Latest month stats
    _latest_month = _df['bucket_month'].max()
    _latest = _df[_df['bucket_month'] == _latest_month]

    _active_count = int(_latest[_latest['label'].isin(ACTIVE_LABELS)]['developers_count'].sum())
    _ft_count = int(_latest[_latest['label'].isin(FT_LABELS)]['developers_count'].sum())
    _pt_count = int(_latest[_latest['label'].isin(PT_LABELS)]['developers_count'].sum())
    _new_count = int(_latest[_latest['label'].isin(['first time'])]['developers_count'].sum())

    # Churn ratio (trailing 12 months)
    _twelve_months_ago = _latest_month - pd.DateOffset(months=12)
    _trailing_12 = _df[_df['bucket_month'] > _twelve_months_ago]
    _churn_12_sum = int(_trailing_12[_trailing_12['label'].isin(CHURNED_LABELS + DORMANT_LABELS)]['developers_count'].sum())
    _active_12_sum = int(_trailing_12[_trailing_12['label'].isin(ACTIVE_LABELS)]['developers_count'].sum())
    _churn_ratio_12 = (_churn_12_sum / _active_12_sum * 100) if _active_12_sum > 0 else 0

    # Churn ratio (all-time)
    _churn_all_sum = int(_df[_df['label'].isin(CHURNED_LABELS + DORMANT_LABELS)]['developers_count'].sum())
    _active_all_sum = int(_df[_df['label'].isin(ACTIVE_LABELS)]['developers_count'].sum())
    _churn_ratio_all = (_churn_all_sum / _active_all_sum * 100) if _active_all_sum > 0 else 0

    # Dormant current month
    _dormant_current = int(_latest[_latest['label'].isin(DORMANT_LABELS)]['developers_count'].sum())

    # Dormant 6-month average
    _six_months_ago = _latest_month - pd.DateOffset(months=6)
    _trailing_6 = _df[_df['bucket_month'] > _six_months_ago]
    _dormant_6_monthly = _trailing_6[_trailing_6['label'].isin(DORMANT_LABELS)].groupby('bucket_month')['developers_count'].sum()
    _dormant_6_avg = int(_dormant_6_monthly.mean()) if len(_dormant_6_monthly) > 0 else 0

    _row1 = mo.hstack([
        mo.stat(
            value=f"{_active_count:,}",
            label="Active Developers",
            bordered=True,
            caption=f"Latest month ({str(_latest_month)[:7]})"
        ),
        mo.stat(
            value=f"{_ft_count:,}",
            label="Full-Time",
            bordered=True,
            caption="10+ active days/month"
        ),
        mo.stat(
            value=f"{_pt_count:,}",
            label="Part-Time",
            bordered=True,
            caption="1-9 active days/month"
        ),
        mo.stat(
            value=f"{_new_count:,}",
            label="First-Time Contributors",
            bordered=True,
            caption="New this month"
        ),
    ], widths="equal", gap=1)

    _row2 = mo.hstack([
        mo.stat(
            value=f"{_churn_ratio_12:.1f}%",
            label="Churn Ratio (12mo)",
            bordered=True,
            caption="Churned+dormant / active"
        ),
        mo.stat(
            value=f"{_churn_ratio_all:.1f}%",
            label="Churn Ratio (All-Time)",
            bordered=True,
            caption="Churned+dormant / active"
        ),
        mo.stat(
            value=f"{_dormant_current:,}",
            label="Dormant (Current)",
            bordered=True,
            caption=f"Latest month ({str(_latest_month)[:7]})"
        ),
        mo.stat(
            value=f"{_dormant_6_avg:,}",
            label="Dormant (6mo Avg)",
            bordered=True,
            caption="Average over last 6 months"
        ),
    ], widths="equal", gap=1)

    mo.vstack([_row1, _row2], gap=1)
    return


@app.cell(hide_code=True)
def _(CHURNED_LABELS, DORMANT_LABELS, FT_LABELS, PT_LABELS, df, go, mo, project_input):
    _df = df[df['project_display_name'] == project_input.value].copy()

    # Group 16 labels into 4 simplified categories
    def _categorize(label):
        if label == 'first time':
            return 'First Time'
        elif label in PT_LABELS:
            return 'Part Time'
        elif label in FT_LABELS:
            return 'Full Time'
        elif label in DORMANT_LABELS or label in CHURNED_LABELS:
            return 'Churned / Dormant'
        return None

    _df['category'] = _df['label'].apply(_categorize)
    _df = _df[_df['category'].notna()]
    _grouped = _df.groupby(['bucket_month', 'category'])['developers_count'].sum().reset_index()

    _cat_colors = {
        'First Time': '#4C78A8',
        'Part Time': '#41AB5D',
        'Full Time': '#7A4D9B',
        'Churned / Dormant': '#D62728',
    }

    _fig = go.Figure()

    # Positive traces (First Time closest to zero, Full Time on top)
    for _cat in ['First Time', 'Part Time', 'Full Time']:
        _cat_data = _grouped[_grouped['category'] == _cat]
        _fig.add_trace(go.Bar(
            x=_cat_data['bucket_month'],
            y=_cat_data['developers_count'],
            name=_cat,
            marker_color=_cat_colors[_cat],
        ))

    # Negative trace (below zero)
    _cat_data = _grouped[_grouped['category'] == 'Churned / Dormant']
    _fig.add_trace(go.Bar(
        x=_cat_data['bucket_month'],
        y=-_cat_data['developers_count'],
        name='Churned / Dormant',
        marker_color=_cat_colors['Churned / Dormant'],
    ))

    _fig.update_layout(
        barmode='relative',
        template='plotly_white',
        margin=dict(t=20, l=0, r=0, b=0),
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text=''
        )
    )
    _fig.update_xaxes(
        title='',
        showgrid=False,
        linecolor="#1F2937",
        linewidth=1,
        ticks="outside",
        tickformat="%b %Y"
    )
    _fig.update_yaxes(
        title="",
        showgrid=True,
        gridcolor="#E5E7EB",
        zeroline=True,
        zerolinecolor="#1F2937",
        zerolinewidth=1.5,
        linecolor="#1F2937",
        linewidth=1,
        ticks="outside",
    )
    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def _(mo):
    activity_input = mo.ui.switch(
        label='Show inactive developers',
        value=False
    )
    mo.hstack([
        mo.md("""### Detailed Lifecycle Transitions"""),
        activity_input,
    ], gap=2, align="end")
    return (activity_input,)


@app.cell(hide_code=True)
def _(activity_input, df, mo, pd, project_input, px):
    _df = df[df['project_display_name'] == project_input.value].copy()

    _color_mapping = {
        # Onboarding
        'first time': '#4C78A8',

        # Full-time family
        'full time': '#7A4D9B',
        'new full time': '#9C6BD3',
        'part time to full time': '#B48AEC',
        'dormant to full time': '#C7A7F2',

        # Part-time family
        'part time': '#41AB5D',
        'new part time': '#74C476',
        'full time to part time': '#A1D99B',
        'dormant to part time': '#C7E9C0',

        # Dormant
        'dormant': '#F39C12',
        'first time to dormant': '#F5B041',
        'part time to dormant': '#F8C471',
        'full time to dormant': '#FAD7A0',

        # Churned
        'churned (after first time)': '#D62728',
        'churned (after reaching part time)': '#E57373',
        'churned (after reaching full time)': '#F1948A',
    }
    _label_order = [
        'first time',
        'full time', 'new full time', 'part time to full time', 'dormant to full time',
        'part time', 'new part time', 'full time to part time', 'dormant to part time',
        'dormant', 'first time to dormant', 'part time to dormant', 'full time to dormant',
        'churned (after first time)', 'churned (after reaching part time)', 'churned (after reaching full time)',
    ]
    _inactive_labels = [
        'dormant', 'first time to dormant', 'part time to dormant', 'full time to dormant',
        'churned (after first time)', 'churned (after reaching part time)', 'churned (after reaching full time)',
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
        margin=dict(t=20, l=0, r=0, b=0),
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text=''
        )
    )
    _fig.update_xaxes(
        title='',
        showgrid=False,
        linecolor="#1F2937",
        linewidth=1,
        ticks="outside",
        tickformat="%b %Y"
    )
    _fig.update_yaxes(
        title="",
        showgrid=True,
        gridcolor="#E5E7EB",
        zeroline=True,
        zerolinecolor="#1F2937",
        zerolinewidth=1,
        linecolor="#1F2937",
        linewidth=1,
        ticks="outside",
        range=[0, None]
    )
    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""### Ecosystem Comparison""")
    return


@app.cell(hide_code=True)
def _(df, mo):
    _ecosystem_list = sorted(list(df['project_display_name'].unique()))
    _default_ecosystems = [e for e in ['Ethereum', 'Solana', 'Bitcoin'] if e in _ecosystem_list]
    comparison_ecosystems = mo.ui.multiselect(
        options=_ecosystem_list,
        value=_default_ecosystems,
        label='Select Ecosystems',
    )
    comparison_metric = mo.ui.dropdown(
        options=['Monthly Active', 'Monthly Churn Rate', 'Full-Time Count', 'First-Time Count'],
        value='Monthly Active',
        label='Metric',
    )
    mo.hstack([comparison_ecosystems, comparison_metric], gap=2, align="end")
    return comparison_ecosystems, comparison_metric


@app.cell(hide_code=True)
def _(ACTIVE_LABELS, CHURNED_LABELS, DORMANT_LABELS, FT_LABELS, comparison_ecosystems, comparison_metric, df, go, mo):
    _selected = comparison_ecosystems.value
    _metric = comparison_metric.value

    _fig = go.Figure()
    if _selected:
        for _eco in _selected:
            _eco_df = df[df['project_display_name'] == _eco]

            if _metric == 'Monthly Active':
                _vals = _eco_df[_eco_df['label'].isin(ACTIVE_LABELS)].groupby('bucket_month')['developers_count'].sum()
            elif _metric == 'Full-Time Count':
                _vals = _eco_df[_eco_df['label'].isin(FT_LABELS)].groupby('bucket_month')['developers_count'].sum()
            elif _metric == 'First-Time Count':
                _vals = _eco_df[_eco_df['label'] == 'first time'].groupby('bucket_month')['developers_count'].sum()
            elif _metric == 'Monthly Churn Rate':
                _active = _eco_df[_eco_df['label'].isin(ACTIVE_LABELS)].groupby('bucket_month')['developers_count'].sum()
                _churn = _eco_df[_eco_df['label'].isin(CHURNED_LABELS + DORMANT_LABELS)].groupby('bucket_month')['developers_count'].sum()
                _vals = (_churn / _active * 100).replace([float('inf'), float('-inf')], 0).fillna(0)

            _fig.add_trace(go.Scatter(
                x=_vals.index,
                y=_vals.values,
                mode='lines',
                name=_eco,
            ))

    _fig.update_layout(
        template='plotly_white',
        margin=dict(t=20, l=0, r=0, b=0),
        height=400,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text=''
        )
    )
    _fig.update_xaxes(
        title='',
        showgrid=False,
        linecolor="#1F2937",
        linewidth=1,
        ticks="outside",
        tickformat="%b %Y"
    )
    _fig.update_yaxes(
        title=_metric,
        showgrid=True,
        gridcolor="#E5E7EB",
        linecolor="#1F2937",
        linewidth=1,
        ticks="outside",
    )
    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def _(mo, pd, pyoso_db_conn):
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
    df['bucket_month'] = pd.to_datetime(df['bucket_month'])
    return (df,)


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    return go, pd, px


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
