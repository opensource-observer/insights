import marimo

__generated_with = "0.15.3"
app = marimo.App(width="medium")


@app.cell
def setup_pyoso():
    import marimo as mo
    from pyoso import Client
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    import plotly.express as px

    client = Client()
    pyoso_db_conn = None
    return client, go, mo, np, pd, px


@app.cell
def _(mo):
    mo.md(
        """
    # Builder Velocity

    This dashboard visualizes the monthly change in full-time contributors for projects in [oss-directory](https://github.com/opensource-observer/oss-directory) using data from the Pyoso API.

    It focuses on the top 50 projects based on the total change in full-time contributors over the past 3 years.

    You can add your project by submitting a PR!
    """
    )
    return


@app.cell
def _(client):
    df_top_projects = client.to_pandas("""
    WITH params AS (
      SELECT
        date_trunc('month', current_date) - INTERVAL '36' month AS analysis_start,
        date_trunc('month', current_date) AS analysis_end,
        (SELECT metric_id FROM metrics_v0 WHERE metric_name='GITHUB_change_in_full_time_contributors_monthly') AS metric_id
    ),
    oss_projects AS (
      SELECT project_id FROM projects_v1 WHERE project_source='OSS_DIRECTORY'
    ),
    top_projects AS (
      SELECT ts.project_id, sum(ts.amount) AS total_change
      FROM timeseries_metrics_by_project_v0 ts
      JOIN oss_projects op ON ts.project_id=op.project_id
      CROSS JOIN params pr
      WHERE ts.metric_id=pr.metric_id
        AND ts.sample_date>=pr.analysis_start
        AND ts.sample_date<=pr.analysis_end
      GROUP BY ts.project_id
      ORDER BY total_change DESC
      LIMIT 50
    )
    SELECT
      ts.sample_date,
      p.project_name,
      ts.amount
    FROM timeseries_metrics_by_project_v0 ts
    JOIN top_projects tp ON ts.project_id=tp.project_id
    JOIN projects_v1 p ON ts.project_id=p.project_id
    CROSS JOIN params pr
    WHERE ts.metric_id=pr.metric_id
      AND ts.sample_date>=pr.analysis_start
      AND ts.sample_date<pr.analysis_end
    ORDER BY ts.sample_date, ts.amount DESC
    """)
    return (df_top_projects,)


@app.cell
def _(df_top_projects, go, mo, np, pd, px):
    def _rgba_from_rgb(rgb: str, alpha: float) -> str:
        return rgb.replace("rgb", "rgba").replace(")", f",{alpha})")

    def joyplot_timeseries(
        df: pd.DataFrame,
        date_col: str = "sample_date",
        group_col: str = "project_name",
        value_col: str = "amount",
        normalize: bool = True,
        gap: float = 1.2,
        smoothing: int = 0,
        top_n: int | None = None,
        color_mode: str = "sequential",
        cmap_name: str = "Viridis",
        qual_name: str = "Set3",
        fill_alpha: float = 0.5,
        annotate_totals: bool = True
    ) -> go.Figure:

        d = df[[date_col, group_col, value_col]].copy()
        d[date_col] = pd.to_datetime(d[date_col])

        # Pivot and cumulative sum
        wide = d.pivot_table(index=date_col, columns=group_col, values=value_col, aggfunc="sum").sort_index()
        if smoothing and smoothing > 1:
            wide = wide.rolling(window=smoothing, min_periods=1, center=True).mean()
        wide_cum = wide.fillna(0).cumsum()

        # Current (final) cumulative total per project for leaderboard sorting
        finals = wide_cum.ffill().iloc[-1].fillna(0).sort_values(ascending=False)

        # Limit by top_n using current totals
        if top_n is not None:
            keep = finals.index[:top_n]
            wide_cum = wide_cum[keep]
            finals = finals.loc[keep]
            finals.sort_values(inplace=True)

        # Normalize per series if requested (after cumsum)
        if normalize:
            denom = wide_cum.max(skipna=True).replace(0, np.nan)
            wide_norm = wide_cum.divide(denom, axis=1)
        else:
            wide_norm = wide_cum

        # Build color lookup keyed by leaderboard order (current totals)
        if color_mode == "qualitative":
            palette = getattr(px.colors.qualitative, qual_name)
            proj_colors = {col: palette[i % len(palette)] for i, col in enumerate(finals.index)}
        else:
            cmap = getattr(px.colors.sequential, cmap_name)
            n = len(finals)
            proj_colors = {}
            for rank, col in enumerate(finals.index):
                idx = int(round(rank * (len(cmap) - 1) / max(1, n - 1)))
                proj_colors[col] = cmap[idx]

        fig = go.Figure()

        ordered_cols = list(finals.index)
        tickvals, ticktext, annotations = [], [], []
        x_final = wide_norm.index.max()

        for i, col in enumerate(ordered_cols):
            y_offset = i * gap
            y_vals = wide_norm[col].fillna(0).values
            cum_vals = wide_cum[col].fillna(0).values
            color = proj_colors[col]
            fill_color = _rgba_from_rgb(color, fill_alpha)

            # Baseline
            fig.add_trace(
                go.Scatter(
                    x=wide_norm.index,
                    y=np.full_like(y_vals, y_offset, dtype=float),
                    mode="lines",
                    line=dict(width=0),
                    hoverinfo="skip",
                    showlegend=False
                )
            )
            # Ridge
            fig.add_trace(
                go.Scatter(
                    x=wide_norm.index,
                    y=y_vals + y_offset,
                    mode="lines",
                    fill="tonexty",
                    line=dict(color=color, width=1.5),
                    line_shape="spline",
                    fillcolor=fill_color,
                    name=col,
                    customdata=np.c_[cum_vals],
                    hovertemplate="<b>%{fullData.name}</b><br>%{x|%b %Y}<br>Cumulative: %{customdata[0]:,.0f}<extra></extra>",
                    showlegend=False
                )
            )

            tickvals.append(y_offset)
            ticktext.append(col)

            if annotate_totals:
                final_val = cum_vals[-1]
                annotations.append(dict(
                    x=x_final,
                    y=y_offset,
                    xanchor="left",
                    yanchor="bottom",
                    text=f"+{final_val:,.0f}",
                    font=dict(color='black', size=12),
                    showarrow=False,
                    xshift=5
                ))

        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(size=12, color="black"),
            margin=dict(l=20, r=80, t=0, b=30),
            showlegend=False,
            height=1500,
            annotations=annotations
        )
        fig.update_xaxes(
            title="",
            showgrid=False,
            visible=False
        )
        fig.update_yaxes(
            title="",
            showgrid=False,
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            zeroline=False,
            linecolor="black",
            tickcolor="black",
            showline=False
        )
        return fig

    fig = joyplot_timeseries(
        df_top_projects,
        normalize=True,
        smoothing=0,
        gap=1.2,
        top_n=50,
        color_mode="sequential",
        cmap_name="Tealgrn",
        fill_alpha=0.55,
        annotate_totals=True
    )
    mo.ui.plotly(fig)
    return


if __name__ == "__main__":
    app.run()
