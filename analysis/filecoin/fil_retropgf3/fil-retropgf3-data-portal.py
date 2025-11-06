import marimo

__generated_with = "unknown"
app = marimo.App()


@app.cell
def _(mo):
    mo.md(
        r"""
    # Fil-RetroPGF3 Data Portal

    Created by: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2025-11-06</span>

    ⚠️ You will need to login into OSO ([click here](https://www.oso.xyz/login)) to interact with these charts, download CSV / JSON versions, etc.
    """
    )
    return


@app.cell
def _(mo):
    mo.accordion({
        "Click for instructions on how to get underlying data": """
        - Summary code metrics ([Google Sheet](https://docs.google.com/spreadsheets/d/1NC_Co1wBeCG---GwbnX0WKKqcfKfR1-mseCuGzAmnTE/edit?gid=1559587951#gid=1559587951))
        - Raw data snapshots ([GitHub](https://github.com/opensource-observer/insights/tree/main/analysis/filecoin/fil_retropgf3))
        - API access to the full data lake ([pyoso](https://docs.oso.xyz/docs/get-started/python))
        """
    })    
    return


@app.cell
def _(mo):
    mo.md(r"""### Developer activity over the last 6 months for repos in Fil-RetroPGF3""")
    return


@app.cell
def _(df_events, make_joyplot, mo):
    _fig = make_joyplot(df_events, height=1500, smoothing=1, gap=1.2)
    mo.ui.plotly(_fig, config={'displayModeBar': False})
    return


@app.cell
def _(mo):
    mo.md(r"""### Tree map of active developers by project""")
    return


@app.cell
def _(df_events, df_project_metrics, mo, px):
    _num_devs = df_events.query("event_type in ['COMMIT_CODE', 'ISSUE_OPENED', 'PULL_REQUEST_MERGED', 'PULL_REQUEST_OPENED']")['git_user'].nunique()
    _title = f"Fil-RetroPGF3 Developer Ecosystem ({_num_devs} Unique Contributors in Last 6 Months)"
    _df = df_project_metrics.groupby('Project Name')['Contributor Count (6 Months)'].max().reset_index()

    _fig = px.treemap(
        data_frame=_df,
        path=[px.Constant(_title), 'Project Name'],
        values='Contributor Count (6 Months)',
        color='Contributor Count (6 Months)',
        color_continuous_scale='Blues_r'
    )
    _fig.update_layout(coloraxis_showscale=False, margin=dict(t=0, l=0, r=0, b=0))
    mo.ui.plotly(_fig)
    return


@app.cell
def _(df_events, df_project_metrics, mo):
    mo.vstack([
        mo.md("""
        ### Appendix: Downloadable Datasets
        - Login to OSO ([click here](https://www.oso.xyz/login)) to download CSV / JSON versions.
        - We also have snapshots available [here](https://github.com/opensource-observer/insights/tree/main/analysis/filecoin/fil_retropgf3).

        """),
        mo.md("#### Project GitHub Summary Metrics"),
        mo.ui.table(
            data=df_project_metrics.sort_values(by='Contributor Count', ascending=False).reset_index(drop=True).drop(columns=['ID']),
            show_column_summaries=False,
            show_data_types=False,
            page_size=25,
            freeze_columns_left=['Project Name', 'GitHub URL']
        ),
        mo.md("#### Project GitHub Event Data (Last 6 Months, minimally processed)"),
        mo.ui.table(
            data=df_events.sort_values(by='date').reset_index(drop=True).drop(columns=['month']),
            show_column_summaries=False,
            show_data_types=False,
            page_size=25
        ),
    ])
    return


@app.cell
def _(mo, pd, pyoso_db_conn):
    _base_url = "https://raw.githubusercontent.com/opensource-observer/insights/refs/heads/main/"
    _csv_url = _base_url + "analysis/filecoin/fil_retropgf3/applications-fil-retropgf-3_final.csv"
    _df_csv = pd.read_csv(_csv_url)

    _df_csv['GitHub URL'] = _df_csv['GitHub URL'].str.lower()
    _url_list = list(_df_csv['GitHub URL'].unique())
    _url_list = sorted([u.lower() for u in _url_list])

    _query = f"""
      SELECT
        artifact_id,
        f.url,
        f.repo_maintainer,
        m.language,
        f.first_activity_time,
        f.last_activity_time,
        f.age_months,    
        f.has_packages,
        f.package_count,
        f.release_count,    
        m.star_count,
        m.fork_count,    
        f.contributor_count
      FROM int_ddp_repo_features AS f
      JOIN int_ddp_repo_metadata AS m USING artifact_id
      WHERE f.url IN ({stringify(_url_list)})
      """

    _df_repos = mo.sql(_query, engine=pyoso_db_conn, output=False)
    _df_repos.columns = [c.replace('_', ' ').title() for c in _df_repos.columns]

    df_projects = _df_csv.merge(_df_repos, left_on='GitHub URL', right_on='Url', how='left')
    artifact_ids = sorted(df_projects['Artifact Id'].dropna().unique())
    df_projects = df_projects.drop(columns=['Artifact Id', 'Url']).drop_duplicates()
    return artifact_ids, df_projects


@app.cell
def _(artifact_ids, mo, pyoso_db_conn):
    df_events = mo.sql(
        f"""
        SELECT
          bucket_day AS "date",
          date_trunc('MONTH', bucket_day) AS "month",
          r.name_with_owner AS git_repo,
          u.artifact_name AS git_user,
          event_type,
          amount
        FROM int_events_daily__github AS e
        JOIN int_github_users_bot_filtered AS u ON e.from_artifact_id = u.artifact_id
        JOIN int_repositories__ossd AS r ON e.to_artifact_id = r.artifact_id    
        WHERE
          to_artifact_id IN ({stringify(artifact_ids)})
          AND bucket_day BETWEEN DATE('2025-04-01') AND DATE('2025-09-30')
          AND NOT is_bot
        """,
        engine=pyoso_db_conn,
        output=False
    )
    return (df_events,)


@app.cell
def _(df_events, df_projects, pd):
    _star_forks = (
        df_events
            .query("event_type in ['STARRED', 'FORKED']")
            .pivot_table(
                index='git_repo',
                columns='event_type',
                values='git_user',
                aggfunc='nunique'
            )
            .rename(columns={'STARRED': 'Stars (6 Months)', 'FORKED': 'Forks (6 Months)'})
    )
    _contributors = (
        df_events
            .query("event_type in ['COMMIT_CODE', 'ISSUE_OPENED', 'PULL_REQUEST_MERGED', 'PULL_REQUEST_OPENED']")
            .groupby('git_repo')
            .agg({'git_user': 'nunique'})
            .rename(columns={'git_user':'Contributor Count (6 Months)'})
    )
    _active_developers = (
        df_events
            .query("event_type in ['COMMIT_CODE', 'PULL_REQUEST_MERGED', 'PULL_REQUEST_OPENED']")
            .groupby(['git_repo', 'month'])
            .agg({'git_user': 'nunique'})        
            .reset_index()
            .groupby('git_repo')
            .agg({'git_user': lambda x: round(sum(x)/6,1)})
            .rename(columns={'git_user': 'Avg Monthly Active Devs (6 Months)'})
    )

    _df_metrics = pd.concat([_star_forks, _contributors, _active_developers], axis=1)

    df_project_metrics = df_projects.copy()
    df_project_metrics['git_repo'] = df_project_metrics['GitHub URL'].apply(lambda x: x.replace('https://github.com/',''))

    df_project_metrics = df_project_metrics.merge(_df_metrics, on='git_repo', how='left').drop(columns=['git_repo'])
    df_project_metrics['First Activity Time'] = (
        pd.to_datetime(df_project_metrics['First Activity Time'], errors='coerce')
        .dt.strftime('%Y-%m-%d')
    )
    df_project_metrics['Last Activity Time'] = (
        pd.to_datetime(df_project_metrics['Last Activity Time'], errors='coerce')
        .dt.strftime('%Y-%m-%d')
    )
    return (df_project_metrics,)


@app.cell
def _(go, np, pd, px):
    def rgba_from_rgb(rgb, alpha):
        return rgb.replace("rgb", "rgba").replace(")", f",{alpha})")

    def make_joyplot(
        df,
        date_col = "date",
        project_col = "git_repo",
        value_col = "git_user",
        aggfunc="nunique",
        smoothing = 7,
        colorscale = 'Greens',
        gap = 1.1,
        fill_alpha = 0.40,
        height=800
    ):

        df[date_col] = pd.to_datetime(df[date_col])
        wide = df.pivot_table(index=date_col, columns=project_col, values=value_col, aggfunc=aggfunc).sort_index()

        if smoothing > 1:
            wide_display = wide.rolling(window=smoothing, min_periods=1, center=True).mean()
        else:
            wide_display = wide.copy()

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

        fig = go.Figure()
        tickvals, ticktext = [], []
        for i, col in enumerate(cols):
            ticktext.append(f"{col}")
            y_offset = i * gap
            tickvals.append(y_offset)
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
                           hovertemplate="<b>%{fullData.name}</b><br>Week of: %{x|%d %b %Y}<br>Activity: %{customdata[0]:,.0f}% of max<extra></extra>",
                           showlegend=False)
            )

        fig.update_layout(template="plotly_white", paper_bgcolor="white", plot_bgcolor="white", showlegend=False, height=height)
        fig.update_xaxes(title="", showgrid=True, visible=True, linecolor="white", linewidth=1, side="top", ticklabelposition="outside right")
    
        tickvals = [float(v) for v in tickvals]
        ticktext = [str(t) for t in ticktext]
    
        n=len(cols)
        ymin=-0.5*gap
        ymax=(n-1)*gap+1
    
        fig.update_yaxes(range=[ymin,ymax], showticklabels=False, showgrid=False, showline=True, zeroline=False)
        labels = [
            dict(
                xref="paper", x=0, xanchor="right",  # left margin of plot
                y=float(v), yref="y",
                text=t, showarrow=False,
                align="right",
                font=dict(size=11, color="#111"),
                yshift=1
            )
            for v, t in zip(tickvals, ticktext)
        ]
        fig.update_layout(annotations=labels, margin=dict(l=300, r=20, t=0, b=0)) 

        return fig
    return (make_joyplot,)


@app.function
def stringify(arr):
    return "'" + "','".join(arr) + "'"


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
