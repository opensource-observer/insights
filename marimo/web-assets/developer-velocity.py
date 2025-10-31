import marimo

__generated_with = "0.17.5"
app = marimo.App(width="full")


@app.cell
def _(mo):
    mo.md(r"""
    # Has developer velocity changed since the launch of ChatGPT 4o?
    """)
    return


@app.cell
def _(df_all, mo):
    project_list = sorted(df_all['display_name'].unique())
    selected_projects = mo.ui.multiselect(
        options=project_list,
        value=project_list,
        label="Select a Cohort of OSS Projects to Benchmark",
        full_width=True
    )
    start_date = mo.ui.date(
        value="2023-11-13",
        label="Start Comparison Period",
        full_width=True
    )
    milestone_date = mo.ui.date(
        value="2024-05-13",
        label="Milestone Date",
        full_width=True
    )
    mo.vstack([
        mo.md("### Analysis Settings:"),
        mo.hstack([
            selected_projects,
            mo.hstack([milestone_date, start_date], widths="equal", gap=5)
        ], widths='equal', gap=5)
    ])
    return milestone_date, selected_projects, start_date


@app.cell
def _(
    calculate_velocity_stats,
    df_all,
    make_joyplot,
    milestone_date,
    mo,
    pd,
    selected_projects,
    start_date,
):
    num_projects = len(selected_projects.value)
    df_filtered = df_all[df_all['display_name'].isin(selected_projects.value)].copy()

    stats = calculate_velocity_stats(
        df_filtered,
        milestone_date=pd.to_datetime(milestone_date.value),
        start_analysis_date=pd.to_datetime(start_date.value)
    )

    projects_stat = mo.stat(
        label="Number of Projects Analyzed",
        bordered=True,
        value=f"{num_projects}",
        caption="Out of 5,365 projects in OSS Directory"
    )

    overall_change = stats['overall_change']
    if overall_change > 0:
        overall_change_str = f"+{overall_change:.1f}%"
    elif overall_change < 0:
        overall_change_str = f"{overall_change:.1f}%"
    else:
        overall_change_str = "0%"

    velocity_stat = mo.stat(
        label="Overall Velocity Change",
        bordered=True,
        value=overall_change_str,
        caption="In aggregate, across the selected cohort"
    )

    median_change = stats['median_change']
    if median_change > 0:
        median_change_str = f"+{median_change:.1f}%"
    elif median_change < 0:
        median_change_str = f"{median_change:.1f}%"
    else:
        median_change_str = "0%"

    median_stat = mo.stat(
        label="Median Velocity Change",
        bordered=True,
        value=median_change_str,
        caption="By project, across the selected cohort"
    )

    top_quartile_avg = stats['top_quartile_avg']
    if top_quartile_avg > 0:
        top_quartile_str = f"+{top_quartile_avg:.1f}%"
    elif top_quartile_avg < 0:
        top_quartile_str = f"{top_quartile_avg:.1f}%"
    else:
        top_quartile_str = "0%"

    top_quartile_stat = mo.stat(
        label="Top Quartile Avg Change",
        bordered=True,
        value=top_quartile_str,
        caption="By project, across the selected cohort"
    )

    fig = make_joyplot(
        df_filtered, 
        milestone_date=pd.to_datetime(milestone_date.value),
        start_analysis_date=pd.to_datetime(start_date.value)
    )

    mo.vstack([
        mo.md("### Analysis Results:"),
        mo.hstack([projects_stat, velocity_stat, median_stat, top_quartile_stat], widths="equal", gap=1),
        mo.ui.plotly(fig, config={'displayModeBar': False})
    ])
    return


@app.cell
def _(go, np, pd, px):
    def rgba_from_rgb(rgb, alpha):
        return rgb.replace("rgb", "rgba").replace(")", f",{alpha})")

    def calculate_velocity_stats(df, date_col="sample_date", project_col="display_name", 
                                 value_col="amount", smoothing=7,
                                 milestone_date=pd.to_datetime('2025-01-01'),
                                 start_analysis_date=pd.to_datetime('2024-07-01')):

        df[date_col] = pd.to_datetime(df[date_col])
        wide = df.pivot_table(index=date_col, columns=project_col, values=value_col, aggfunc="sum").sort_index()

        if smoothing > 1:
            wide = wide.rolling(window=smoothing, min_periods=1, center=True).mean()

        milestone_date = pd.to_datetime(milestone_date)
        start_analysis_date = pd.to_datetime(start_analysis_date)

        # Calculate change for each project
        project_changes = []
        for col in wide.columns:
            pre_milestone_data = wide[col][(wide.index < milestone_date) & (wide.index >= start_analysis_date)]
            post_milestone_data = wide[col][wide.index >= milestone_date]
            pre_milestone_avg = pre_milestone_data.fillna(0).mean()
            post_milestone_avg = post_milestone_data.fillna(0).mean()
            change = ((post_milestone_avg - pre_milestone_avg) / pre_milestone_avg) * 100 if pre_milestone_avg > 0 else 0
            project_changes.append(change)

        project_changes = np.array(project_changes)

        # Overall change is the average across all projects
        overall_change = np.mean(project_changes)

        # Median change
        median_change = np.median(project_changes) if len(project_changes) > 0 else 0

        # Top quartile average
        if len(project_changes) > 0:
            quartile_75 = np.percentile(project_changes, 75)
            top_quartile_avg = np.mean(project_changes[project_changes >= quartile_75])
        else:
            top_quartile_avg = 0

        return {
            'overall_change': overall_change,
            'median_change': median_change,
            'top_quartile_avg': top_quartile_avg
        }

    def make_joyplot(
        df,
        milestone_date,
        start_analysis_date,
        date_col = "sample_date",
        project_col = "display_name",
        value_col = "amount",
        smoothing = 7,
        colorscale = 'Greens',
        gap = 1.10,
        fill_alpha = 0.40,
        display_months = None,
    ):

        df[date_col] = pd.to_datetime(df[date_col])
        wide = df.pivot_table(index=date_col, columns=project_col, values=value_col, aggfunc="sum").sort_index()

        if smoothing > 1:
            wide = wide.rolling(window=smoothing, min_periods=1, center=True).mean()
        if display_months is not None and display_months > 0:
            last_date = wide.index.max()
            cutoff_date = pd.to_datetime(last_date) - pd.DateOffset(months=display_months)
            wide_display = wide[wide.index >= cutoff_date.date()]
        else:
            wide_display = wide

        wide_norm = wide_display.copy()
        for col in wide_display.columns:
            non_zero_count = (wide_display[col] > 0).sum()
            if non_zero_count > 50:
                threshold = int(wide_display[col].quantile(0.95))
                wide_norm[col] = wide_norm[col].clip(upper=threshold)
            denom = wide_norm[col].max(skipna=True)
            wide_norm[col] = wide_norm[col].divide(denom, axis=0)

        cols = list(wide_norm.columns)[::-1]
        cmap = getattr(px.colors.sequential, colorscale)
        cmap_subset = cmap[len(cmap)//2:][::-1]

        n = len(cols)
        proj_colors = {}
        for rank, col in enumerate(cols):
            idx = int(round(rank * (len(cmap_subset) - 1) / max(1, n - 1)))
            proj_colors[col] = cmap_subset[idx]

        milestone_date = pd.to_datetime(milestone_date)
        start_analysis_date = pd.to_datetime(start_analysis_date)

        last_date = wide_norm.index.max()

        fig = go.Figure()
        tickvals, ticktext = [], []
        for i, col in enumerate(cols):
            y_offset = i * gap
            y_vals = wide_norm[col].fillna(0).values
            x_vals = wide_norm.index
            color = proj_colors[col]
            fill_color = rgba_from_rgb(color, fill_alpha)

            fig.add_trace(
                go.Scatter(x=x_vals, y=np.full(y_vals.shape, y_offset, dtype=float),
                           mode="lines", line=dict(width=0), hoverinfo="skip",
                           showlegend=False)
            )
            fig.add_trace(
                go.Scatter(x=x_vals, y=y_vals+y_offset, name=col, fillcolor=fill_color,
                           mode="lines", fill="tonexty", line=dict(color=color, width=1.5), line_shape="spline",
                           customdata=np.c_[wide_norm[col].reindex(x_vals).fillna(0).values * 100],
                           hovertemplate="<b>%{fullData.name}</b><br>Week of: %{x|%d %b %Y}<br>Velocity: %{customdata[0]:,.0f}% of max<extra></extra>",
                           showlegend=False)
            )

            tickvals.append(y_offset)
            pre_milestone_data = wide[col][(wide.index < milestone_date) & (wide.index >= start_analysis_date)]
            post_milestone_data = wide[col][wide.index >= milestone_date]
            pre_milestone_avg = pre_milestone_data.fillna(0).mean()
            post_milestone_avg = post_milestone_data.fillna(0).mean()
            change = ((post_milestone_avg - pre_milestone_avg) / pre_milestone_avg) * 100 if pre_milestone_avg > 0 else 0
            if int(change) > 0:
                annotation_text = f"+{change:,.0f}%"
            elif int(change) < 0:
                annotation_text = f"{change:,.0f}%"
            else:
                annotation_text = "No change"
            ticktext.append(f"<b>{col}</b>: {annotation_text}")

        fig.update_layout(template="plotly_white", paper_bgcolor="white", plot_bgcolor="white",
                          font=dict(size=12, color="#111"), margin=dict(l=0, r=80, t=0, b=0),
                          title=dict(text="", x=0, xanchor="left", font=dict(size=14, color="#111")),
                          showlegend=False)
        fig.update_xaxes(title="", showgrid=False, visible=False, linecolor="#000", linewidth=1)
        fig.update_yaxes(title="", showgrid=False, side="right", showline=False, zeroline=False, 
                         tickmode="array", tickvals=tickvals, ticktext=ticktext,
                         ticklabelposition="outside top", ticklabelstandoff=5, tickcolor="#000")

        fig.add_vrect(
            x0=start_analysis_date, x1=milestone_date,
            fillcolor="rgba(128,128,128,0.05)",
            line_width=0.25,
            annotation_text="<i>  Comparison Period</i>",
            annotation_position="top left",
        )
        fig.add_vrect(
            x0=milestone_date, x1=last_date,
            fillcolor="rgba(128,128,128,0.05)",
            line_width=0.25,
            annotation_text="<i>  Results Period</i>",
            annotation_position="top left",
        )
        return fig
    return calculate_velocity_stats, make_joyplot


@app.cell
def _(mo, pd, pyoso_db_conn):
    _path = "marimo/web-assets/data/developer-velocity.csv"
    try:
        df_all = mo.sql(
            f"""
            SELECT
              sample_date,
              projects_v1.display_name,
              amount
            FROM timeseries_metrics_by_project_v0
            JOIN metrics_v0 USING metric_id
            JOIN projects_v1 USING project_id
            JOIN projects_by_collection_v1 USING project_id
            WHERE
              sample_date BETWEEN DATE('2023-01-01') AND DATE('2025-04-30')
              AND collection_name = 'octant-05'
              AND metric_event_source = 'GITHUB'
              AND metric_model = 'project_velocity'
              AND metric_time_aggregation = 'daily'
            """,
            output=False,
            engine=pyoso_db_conn
        )
        #df_all.to_csv(_path, index=False)
    except:
        df_all = pd.read_csv(f"https://raw.githubusercontent.com/opensource-observer/insights/refs/heads/main/{_path}")

    if df_all.empty:
        df_all = pd.read_csv(f"https://raw.githubusercontent.com/opensource-observer/insights/refs/heads/main/{_path}")
    return (df_all,)


@app.cell
def _():
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    import numpy as np
    return go, np, pd, px


@app.cell
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
