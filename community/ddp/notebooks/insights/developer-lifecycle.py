import marimo

__generated_with = "unknown"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def header_title(mo):
    mo.md("""
    # Lifecycle Analysis
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-02-17</span></small>

    Visualize the full lifecycle of a developer joining, contributing, and leaving an ecosystem.
    """)
    return


@app.cell(hide_code=True)
def header_accordion(mo):
    mo.accordion({
        "Overview": mo.md("""
- This notebook tracks developer lifecycle states — the month-by-month progression of developers joining, contributing, and eventually churning from an ecosystem
- It reveals how the balance between newcomers, established contributors, and churned developers shifts over time and across ecosystems
- Key metrics: monthly active developers by lifecycle state, churn ratio, dormant developer count
        """),
        "Context": mo.md("""
**Lifecycle labels** classify each developer's monthly activity into one of 16 granular states. These roll up into 4 categories used in the summary chart:

| Category | Label | Description |
|:---------|:------|:------------|
| **First Time** | `first time` | First-ever contribution to the ecosystem |
| **Full Time** | `full time` | 10+ active days, continuing from prior month |
| | `new full time` | First month reaching 10+ active days |
| | `part time to full time` | Transitioned from part-time level |
| | `dormant to full time` | Returned from dormancy at full-time level |
| **Part Time** | `part time` | 1-9 active days, continuing from prior month |
| | `new part time` | First month at part-time level |
| | `full time to part time` | Stepped down from full-time level |
| | `dormant to part time` | Returned from dormancy at part-time level |
| **Churned / Dormant** | `dormant` | No activity this month (previously active) |
| | `first time to dormant` | Dormant after first contribution |
| | `part time to dormant` | Dormant after part-time activity |
| | `full time to dormant` | Dormant after full-time activity |
| | `churned (after first time)` | Extended inactivity after first contribution |
| | `churned (after reaching part time)` | Extended inactivity after reaching part time |
| | `churned (after reaching full time)` | Extended inactivity after reaching full time |

**Active** = First Time + Full Time + Part Time (all 9 labels above the Churned/Dormant group)

**Churn Ratio** = sum(churned + dormant) / sum(active) over the trailing window (12mo or all-time)

Data is bucketed monthly; private repos excluded; contributions include commits, issues, pull requests, and code reviews.

**Metric Definitions**
- [Lifecycle](/data/metric-definitions/lifecycle) — Developer stage definitions
- [Activity](/data/metric-definitions/activity) — Monthly Active Developer (MAD) methodology
        """),
        "Data Sources": mo.md("""
- **Open Dev Data (Electric Capital)** — Ecosystem and developer taxonomy, [github.com/electric-capital/crypto-ecosystems](https://github.com/electric-capital/crypto-ecosystems)
- **Key Models** — `oso.int_crypto_ecosystems_developer_lifecycle_monthly_aggregated`
        """),
    })
    return


@app.cell(hide_code=True)
def label_constants():
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
def section_ecosystem_overview(mo):
    mo.md("""
    ## Ecosystem Overview
    *Monthly developer snapshot for the selected ecosystem*
    """)
    return


@app.cell(hide_code=True)
def ecosystem_controls(df, mo):
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
def stats_panel(ACTIVE_LABELS, CHURNED_LABELS, DORMANT_LABELS, FT_LABELS, PT_LABELS, df, mo, pd, project_input):
    _df = df[df['project_display_name'] == project_input.value].copy()

    _latest_month = _df['bucket_month'].max()
    _latest = _df[_df['bucket_month'] == _latest_month]

    _active_count = int(_latest[_latest['label'].isin(ACTIVE_LABELS)]['developers_count'].sum())
    _ft_count = int(_latest[_latest['label'].isin(FT_LABELS)]['developers_count'].sum())
    _pt_count = int(_latest[_latest['label'].isin(PT_LABELS)]['developers_count'].sum())
    _new_count = int(_latest[_latest['label'].isin(['first time'])]['developers_count'].sum())

    _twelve_months_ago = _latest_month - pd.DateOffset(months=12)
    _trailing_12 = _df[_df['bucket_month'] > _twelve_months_ago]
    _churn_12_sum = int(_trailing_12[_trailing_12['label'].isin(CHURNED_LABELS + DORMANT_LABELS)]['developers_count'].sum())
    _active_12_sum = int(_trailing_12[_trailing_12['label'].isin(ACTIVE_LABELS)]['developers_count'].sum())
    _churn_ratio_12 = (_churn_12_sum / _active_12_sum * 100) if _active_12_sum > 0 else 0

    _churn_all_sum = int(_df[_df['label'].isin(CHURNED_LABELS + DORMANT_LABELS)]['developers_count'].sum())
    _active_all_sum = int(_df[_df['label'].isin(ACTIVE_LABELS)]['developers_count'].sum())
    _churn_ratio_all = (_churn_all_sum / _active_all_sum * 100) if _active_all_sum > 0 else 0

    _dormant_current = int(_latest[_latest['label'].isin(DORMANT_LABELS)]['developers_count'].sum())

    _six_months_ago = _latest_month - pd.DateOffset(months=6)
    _trailing_6 = _df[_df['bucket_month'] > _six_months_ago]
    _dormant_6_monthly = _trailing_6[_trailing_6['label'].isin(DORMANT_LABELS)].groupby('bucket_month')['developers_count'].sum()
    _dormant_6_avg = int(_dormant_6_monthly.mean()) if len(_dormant_6_monthly) > 0 else 0

    _row1 = mo.hstack([
        mo.stat(value=f"{_active_count:,}", label="Active Developers", bordered=True, caption=f"Latest month ({str(_latest_month)[:7]})"),
        mo.stat(value=f"{_ft_count:,}", label="Full-Time", bordered=True, caption="10+ active days/month"),
        mo.stat(value=f"{_pt_count:,}", label="Part-Time", bordered=True, caption="1-9 active days/month"),
        mo.stat(value=f"{_new_count:,}", label="First-Time Contributors", bordered=True, caption="New this month"),
    ], widths="equal", gap=1)

    _row2 = mo.hstack([
        mo.stat(value=f"{_churn_ratio_12:.1f}%", label="Churn Ratio (12mo)", bordered=True, caption="Churned+dormant / active"),
        mo.stat(value=f"{_churn_ratio_all:.1f}%", label="Churn Ratio (All-Time)", bordered=True, caption="Churned+dormant / active"),
        mo.stat(value=f"{_dormant_current:,}", label="Dormant (Current)", bordered=True, caption=f"Latest month ({str(_latest_month)[:7]})"),
        mo.stat(value=f"{_dormant_6_avg:,}", label="Dormant (6mo Avg)", bordered=True, caption="Average over last 6 months"),
    ], widths="equal", gap=1)

    mo.vstack([_row1, _row2], gap=1)
    return


@app.cell(hide_code=True)
def diverging_bar_chart(ACTIVE_LABELS, CHURNED_LABELS, DORMANT_LABELS, FT_LABELS, LIFECYCLE_COLORS, apply_ec_style, df, go, mo, project_input):
    _df = df[df['project_display_name'] == project_input.value].copy()

    _latest_month = _df['bucket_month'].max()
    _latest = _df[_df['bucket_month'] == _latest_month]
    _active_count = int(_latest[_latest['label'].isin(ACTIVE_LABELS)]['developers_count'].sum())

    def _categorize(label):
        if label == 'first time':
            return 'First Time'
        elif label in FT_LABELS:
            return 'Full Time'
        elif label in DORMANT_LABELS or label in CHURNED_LABELS:
            return 'Churned / Dormant'
        else:
            return 'Part Time'  # part time, new part time, full time to part time, dormant to part time

    _df['category'] = _df['label'].apply(_categorize)
    _grouped = _df.groupby(['bucket_month', 'category'])['developers_count'].sum().reset_index()

    _fig = go.Figure()

    for _cat in ['First Time', 'Part Time', 'Full Time']:
        _cat_data = _grouped[_grouped['category'] == _cat]
        _fig.add_trace(go.Bar(
            x=_cat_data['bucket_month'],
            y=_cat_data['developers_count'],
            name=_cat,
            marker_color=LIFECYCLE_COLORS[_cat],
            hovertemplate=f'<b>{_cat}</b><br>%{{x|%b %Y}}<br>Developers: %{{y:,.0f}}<extra></extra>',
        ))

    _cat_data = _grouped[_grouped['category'] == 'Churned / Dormant']
    _fig.add_trace(go.Bar(
        x=_cat_data['bucket_month'],
        y=-_cat_data['developers_count'],
        name='Churned / Dormant',
        marker_color=LIFECYCLE_COLORS['Churned / Dormant'],
        hovertemplate='<b>Churned / Dormant</b><br>%{x|%b %Y}<br>Developers: %{customdata:,.0f}<extra></extra>',
        customdata=_cat_data['developers_count'],
    ))

    _fig.update_layout(barmode='relative', height=500)

    apply_ec_style(
        _fig,
        title=f"{_active_count:,} monthly active developers in {project_input.value}",
        subtitle="Developer lifecycle transitions — active (above zero) vs. churned/dormant (below zero)",
        show_legend=True,
        right_margin=60,
    )

    _fig.update_yaxes(
        zeroline=True,
        zerolinecolor="#1F2937",
        zerolinewidth=1.5,
    )

    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def detailed_transitions_header(mo):
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
def detailed_stacked_bar(activity_input, df, mo, pd, project_input, px):
    _df = df[df['project_display_name'] == project_input.value].copy()

    _color_mapping = {
        'first time': '#4C78A8',
        'full time': '#7A4D9B',
        'new full time': '#9C6BD3',
        'part time to full time': '#B48AEC',
        'dormant to full time': '#C7A7F2',
        'part time': '#41AB5D',
        'new part time': '#74C476',
        'full time to part time': '#A1D99B',
        'dormant to part time': '#C7E9C0',
        'dormant': '#F39C12',
        'first time to dormant': '#F5B041',
        'part time to dormant': '#F8C471',
        'full time to dormant': '#FAD7A0',
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
        font=dict(family="Arial, sans-serif", size=12, color="#333"),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=20, l=70, r=60, b=60),
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text='',
            bgcolor="rgba(255,255,255,0.8)"
        )
    )
    _fig.update_xaxes(
        title='',
        showgrid=False,
        linecolor="#1F2937",
        linewidth=1,
        tickformat="%b %Y",
        tickfont=dict(size=11, color="#666"),
    )
    _fig.update_yaxes(
        title="",
        showgrid=True,
        gridcolor="#E5E7EB",
        linecolor="#1F2937",
        linewidth=1,
        range=[0, None],
        tickformat=",d",
        tickfont=dict(size=11, color="#666"),
    )
    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def section_ecosystem_comparison(mo):
    mo.md("""
    ## Ecosystem Comparison
    *Compare lifecycle patterns across Bitcoin, Ethereum, and Solana*
    """)
    return


@app.cell(hide_code=True)
def comparison_controls(df, mo):
    _ecosystem_list = sorted(list(df['project_display_name'].unique()))
    _default_ecosystems = [e for e in ['Ethereum', 'Bitcoin', 'Solana'] if e in _ecosystem_list]
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
def comparison_chart(ACTIVE_LABELS, CHURNED_LABELS, DORMANT_LABELS, FT_LABELS, apply_ec_style, comparison_ecosystems, comparison_metric, df, go, mo):
    _selected = comparison_ecosystems.value
    _metric = comparison_metric.value

    _eco_colors = ['#1B4F72', '#7EB8DA', '#5DADE2', '#E59866', '#A9CCE3', '#5DADE2']

    _fig = go.Figure()
    if _selected:
        for _i, _eco in enumerate(_selected):
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
                line=dict(color=_eco_colors[_i % len(_eco_colors)], width=2),
                hovertemplate=f'<b>{_eco}</b><br>%{{x|%b %Y}}<br>{_metric}: %{{y:,.0f}}<extra></extra>',
            ))

    _title_ecosystems = ', '.join(_selected) if _selected else 'No ecosystems selected'
    apply_ec_style(
        _fig,
        title=f"{_metric}: {_title_ecosystems}",
        subtitle="Monthly trends across selected ecosystems",
        y_title=_metric,
        show_legend=True,
        right_margin=60,
    )

    if _metric == 'Monthly Churn Rate':
        _fig.update_yaxes(tickformat='.1f', ticksuffix='%')

    _fig.update_layout(height=450)

    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell(hide_code=True)
def query_all_data(mo, pd, pyoso_db_conn):
    with mo.persistent_cache("lifecycle_data"):
        df = mo.sql(
            f"""
            SELECT
              project_display_name,
              bucket_month,
              label,
              developers_count
            FROM oso.int_crypto_ecosystems_developer_lifecycle_monthly_aggregated
            ORDER BY 1,2,3
            """,
            output=False,
            engine=pyoso_db_conn
        )
        df['bucket_month'] = pd.to_datetime(df['bucket_month'])
    return (df,)


@app.cell(hide_code=True)
def setup_imports():
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    return go, pd, px


@app.cell(hide_code=True)
def setup_constants():
    LIFECYCLE_COLORS = {
        'First Time': '#4C78A8',
        'Part Time': '#41AB5D',
        'Full Time': '#7A4D9B',
        'Churned / Dormant': '#D62728',
    }
    return (LIFECYCLE_COLORS,)


@app.cell(hide_code=True)
def helper_apply_ec_style():
    def apply_ec_style(fig, title=None, subtitle=None, y_title=None, show_legend=True, right_margin=180):
        title_text = ""
        if title:
            title_text = f"<b>{title}</b>"
            if subtitle:
                title_text += f"<br><span style='font-size:14px;color:#666666'>{subtitle}</span>"

        fig.update_layout(
            title=dict(
                text=title_text,
                font=dict(size=22, color="#1B4F72", family="Arial, sans-serif"),
                x=0,
                xanchor="left",
                y=0.95,
                yanchor="top"
            ) if title else None,
            template='plotly_white',
            font=dict(family="Arial, sans-serif", size=12, color="#333"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(t=100 if title else 40, l=70, r=right_margin, b=60),
            hovermode='x unified',
            showlegend=show_legend,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(255,255,255,0.8)"
            )
        )

        fig.update_xaxes(
            showgrid=False,
            showline=True,
            linecolor="#1F2937",
            linewidth=1,
            tickfont=dict(size=11, color="#666"),
            title="",
            tickformat="%b %Y"
        )

        fig.update_yaxes(
            showgrid=True,
            gridcolor="#E5E7EB",
            gridwidth=1,
            showline=True,
            linecolor="#1F2937",
            linewidth=1,
            tickfont=dict(size=11, color="#666"),
            title=y_title if y_title else "",
            title_font=dict(size=12, color="#666"),
            tickformat=",d"
        )

        return fig
    return (apply_ec_style,)


@app.cell(hide_code=True)
def test_connection(mo, pyoso_db_conn):
    _test_df = mo.sql("""SELECT 1 AS test""", engine=pyoso_db_conn, output=False)
    return


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
