import marimo

__generated_with = "0.17.5"
app = marimo.App(width="full")


@app.cell
def title_markdown(mo):
    mo.md(r"""
    # Did our ecosystem growth campaign have a positive ROI?
    """)
    return


@app.cell
def analysis_settings(
    BASELINE_1_NAME,
    BASELINE_2_NAME,
    INCENTIVE_1_NAME,
    INCENTIVE_2_NAME,
    mo,
):
    incentive_group = mo.ui.dropdown(
        options=[INCENTIVE_1_NAME, INCENTIVE_2_NAME],
        value=INCENTIVE_1_NAME,
        label="Incentive Group:"
    )
    baseline_group = mo.ui.dropdown(
        options=[BASELINE_1_NAME, BASELINE_2_NAME],
        value=BASELINE_1_NAME,
        label="Baseline Group:"
    )
    mo.vstack([
        mo.md("### Analysis Settings"),
        mo.hstack([incentive_group, baseline_group], widths="equal", gap=2)
    ])
    return baseline_group, incentive_group


@app.cell
def analysis_results(baseline_group, df, incentive_group, make_figure, mo):
    # Get selected groups data
    incentive_data = df[['Week', incentive_group.value]].rename(columns={incentive_group.value: 'retention'})
    baseline_data = df[['Week', baseline_group.value]].rename(columns={baseline_group.value: 'retention'})

    # Calculate retention metrics
    incentive_final = incentive_data['retention'].iloc[-1]
    baseline_final = baseline_data['retention'].iloc[-1]
    retention_lift = incentive_final - baseline_final  # percentage points
    relative_improvement = ((incentive_final / baseline_final) - 1) * 100

    # Business metrics (assuming cohort of 100 users)
    cohort_size = 100
    incentive_cost_per_user = 35  # dollars
    ltv_per_retained_user = 180  # dollars (lifetime value)

    # Calculate retained users
    incentive_retained = cohort_size * (incentive_final / 100)
    baseline_retained = cohort_size * (baseline_final / 100)
    incremental_retained = incentive_retained - baseline_retained

    # Cost metrics
    total_incentive_cost = cohort_size * incentive_cost_per_user
    cost_per_incremental_user = total_incentive_cost / incremental_retained if incremental_retained > 0 else 0

    # ROI calculation
    incremental_value = incremental_retained * ltv_per_retained_user
    roi = ((incremental_value - total_incentive_cost) / total_incentive_cost * 100) if total_incentive_cost > 0 else 0

    # Generate the figure
    _fig = make_figure(
        incentive_data=incentive_data,
        baseline_data=baseline_data,
        incentive_name=incentive_group.value,
        baseline_name=baseline_group.value
    )

    # Create stats widgets
    stat1 = mo.stat(
        label="10-Week Retention", 
        bordered=True, 
        value=f"{incentive_final:.0f}%",
        caption=f"vs {baseline_final:.0f}% in baseline group"
    )
    stat2 = mo.stat(
        label="Relative Improvement", 
        bordered=True, 
        value=f"+{relative_improvement:.0f}%",
        caption="Better than baseline"
    )
    stat3 = mo.stat(
        label="Cost per Incremental User", 
        bordered=True, 
        value=f"${cost_per_incremental_user:.0f}",
        caption=f"Incentive: ${incentive_cost_per_user}/user"
    )
    stat4 = mo.stat(
        label="ROI", 
        bordered=True, 
        value=f"{roi:+.0f}%",
        caption=f"LTV: ${ltv_per_retained_user}/user"
    )

    # Generate the results dashboard
    mo.vstack([
        mo.md("### Program Results"),
        mo.hstack([stat1, stat2, stat3, stat4], widths="equal", gap=1),
        mo.ui.plotly(_fig, config={'displayModeBar': False})
    ])
    return


@app.cell
def make_figure(go):
    COLOR_INCENTIVE = '#253494'   # Darker blue/purple
    COLOR_BASELINE =  '#2C7FB8'   # Blue

    def make_figure(incentive_data, baseline_data, incentive_name, baseline_name):
        fig = go.Figure()
        week_labels = [f'Week {w}' for w in incentive_data['Week']]
        fig.add_trace(go.Scatter(
            x=week_labels,
            y=incentive_data['retention'],
            mode='lines+markers',
            name=incentive_name,
            line=dict(color=COLOR_INCENTIVE, width=3),
            marker=dict(size=8, color=COLOR_INCENTIVE),
            hovertemplate='%{y:.0f}%'
        ))
        fig.add_trace(go.Scatter(
            x=week_labels,
            y=baseline_data['retention'],
            mode='lines+markers',
            name=baseline_name,
            line=dict(color=COLOR_BASELINE, width=3),
            marker=dict(size=8, color=COLOR_BASELINE),
            hovertemplate='%{y:.0f}%'
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
            hovermode='x unified'
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
            title="Retention Rate (%)",
            showgrid=True,
            gridcolor="#E5E5E5",
            visible=True,
            linecolor="#000",
            linewidth=1,
            zeroline=True,
            range=[0, 105],
            dtick=10
        )

        return fig
    return (make_figure,)


@app.cell
def get_data(pd):
    # Dummy data
    INCENTIVE_1_NAME = 'Points Program'
    INCENTIVE_2_NAME = 'Referral Program'
    BASELINE_1_NAME  = 'Organic Growth'
    BASELINE_2_NAME  = 'Standard Onboarding'

    df = pd.DataFrame({
        'Week': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        INCENTIVE_1_NAME: [100, 90, 81, 75, 69, 65, 62, 59, 56, 54, 52],
        INCENTIVE_2_NAME: [100, 85, 75, 68, 62, 57, 53, 50, 48, 46, 45],
        BASELINE_1_NAME: [100, 70, 56, 48, 42, 38, 35, 32, 30, 28, 27],
        BASELINE_2_NAME: [100, 75, 58, 46, 38, 32, 27, 24, 22, 20, 18]
    })
    return (
        BASELINE_1_NAME,
        BASELINE_2_NAME,
        INCENTIVE_1_NAME,
        INCENTIVE_2_NAME,
        df,
    )


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
