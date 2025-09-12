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
    return client, go, mo, pd


@app.cell
def _(mo):
    mo.md(
        """
    # Contributor Dynamics

    This page visualizes the monthly trends of new, churned, and active contributors for a given project sourced from the OSS Directory. The chart provides insights into the growth and attrition of contributors over time.
    """
    )
    return


@app.cell
def _(mo):
    project_name_input = mo.ui.text(value="opensource-observer", label="Enter the name of a project", full_width=True)
    project_name_input
    return (project_name_input,)


@app.cell
def _():
    LAYOUT = dict(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_family="PT Sans, sans-serif",
        title_font_family="Lora, serif",
        title_x=0,
        legend_title="",
        autosize=True,
        margin=dict(t=50, l=0, r=0, b=0),
        legend=dict(
            orientation="h",
            yanchor="middle",
            y=1,
            xanchor="left",
            x=0
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray',
            linecolor='black',
            linewidth=1,
            ticks='outside',
            rangemode='tozero'
        ),
        xaxis=dict(
            showgrid=False,
            linecolor='black',
            linewidth=1,
            ticks='outside',
        ),
        hovermode="x"
    )
    PRIMARY_COLOR = 'BLACK'
    SECONDARY_COLOR = '#AAA'
    return


@app.cell
def _(client, project_name_input):
    df_timeseries = client.to_pandas(f"""
    WITH timeseries_metrics AS (
      SELECT
        sample_date,
        CASE WHEN metric_name = 'GITHUB_new_contributors_monthly' THEN amount END AS new_contributors,
        CASE WHEN metric_name = 'GITHUB_churned_contributors_monthly' THEN -amount END AS churned_contributors,
        CASE WHEN metric_name = 'GITHUB_active_contributors_monthly' THEN amount END AS active_contributors
      FROM timeseries_metrics_by_project_v0
      JOIN metrics_v0 USING(metric_id)
      JOIN projects_v1 p USING(project_id)
      WHERE p.project_name='{project_name_input.value}'
        AND p.project_source = 'OSS_DIRECTORY'
        AND metric_name IN (
          'GITHUB_new_contributors_monthly',
          'GITHUB_churned_contributors_monthly',
          'GITHUB_active_contributors_monthly'
        )
    ),
    params AS (
      SELECT MIN(sample_date) AS start_month,
             date_trunc('month', current_date) AS end_month
      FROM timeseries_metrics
    ),
    months AS (
      SELECT m AS sample_date
      FROM UNNEST(SEQUENCE(
        (SELECT start_month FROM params),
        (SELECT end_month FROM params)-INTERVAL '1' month,
        INTERVAL '1' month
      )) t(m)
    )
    SELECT
      m.sample_date,
      SUM(COALESCE(t.new_contributors,0)) AS new_contributors,
      SUM(COALESCE(t.churned_contributors,0)) AS churned_contributors,
      SUM(COALESCE(t.active_contributors,0)) AS active_contributors  
    FROM months AS m
    LEFT JOIN timeseries_metrics AS t ON m.sample_date = t.sample_date
    GROUP BY 1
    ORDER BY 1
    """)
    return (df_timeseries,)


@app.cell
def _(df_timeseries, go, pd):
    def libin_chart(df, title=""):
        d = df.sort_values("sample_date").copy()
        d["sample_date"] = pd.to_datetime(d["sample_date"])

        fig = go.Figure()

        # Inflows
        fig.add_bar(
            name="New",
            x=d["sample_date"],
            y=d["new_contributors"],
            marker_color="#AAA",
            marker_line=dict(color="black", width=.5),
            opacity=0.8,
            hovertemplate="%{x|%b %Y}<br><b>New</b> %{y:,}<extra></extra>"
        )

        # Outflows (already negative)
        fig.add_bar(
            name="Churned",
            x=d["sample_date"],
            y=d["churned_contributors"],
            marker_color="white",
            marker_line=dict(color="black", width=.5),
            hovertemplate="%{x|%b %Y}<br><b>Churned</b> %{y:,}<extra></extra>"
        )

        # Active (overlay as black line on same y-axis)
        fig.add_scatter(
            name="Active (total)",
            x=d["sample_date"],
            y=d["active_contributors"],
            mode="lines",
            line=dict(color="black", width=2),
            hovertemplate="%{x|%b %Y}<br><b>Active</b> %{y:,}<extra></extra>"
        )

        fig.update_layout(
            title=title,
            barmode="relative",
            hovermode="x unified",
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="PT Sans, sans-serif", size=12, color="black"),
            title_font=dict(family="Lora, serif", size=20, color="black"),
            margin=dict(t=50, l=40, r=20, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom", y=1.02,
                xanchor="left", x=0,
                bordercolor="black", borderwidth=0
            ),
            xaxis=dict(
                showgrid=False,
                linecolor="black", linewidth=1,
                ticks="outside", tickformat="%b %Y"
            ),
            yaxis=dict(
                title="Contributors",
                showgrid=True, gridcolor="#D9D9D9",
                zeroline=True, zerolinecolor="black", zerolinewidth=1,
                linecolor="black", linewidth=1,
                ticks="outside"
            )
        )

        # subtle reference line at y=0
        fig.add_hline(y=0, line_width=1, line_color="black")

        return fig

    libin_chart(df_timeseries)    
    return


if __name__ == "__main__":
    app.run()
