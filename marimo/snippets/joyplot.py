import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

def rgba_from_rgb(rgb, alpha):
    return rgb.replace("rgb", "rgba").replace(")", f",{alpha})")

def calc_cagr(start_val, end_val, num_years):
    if start_val <= 0 or num_years <= 0:
        return float('nan')
    return (end_val / start_val) ** (1 / num_years) - 1

def delta_caption(curr, prev):
    if not prev:
        return "--"
    v = (curr - prev) / prev * 100
    c = f"{v:,.1f}%"
    if v > 0:
        c = "+" + c
    return c

def make_joyplot(
    df,
    cagr_date,
    time_col='Date',
    value_col='Amount',
    label_col='Project',
    agg_func='sum',
    gap=1.10,
    colorscale='Greens',
    fill_alpha=0.40,
    smoothing_period=1
):

    wide = df.pivot_table(index=time_col, columns=label_col, values=value_col, aggfunc=agg_func).sort_index()
    if smoothing_period > 1:
        wide = wide.rolling(window=smoothing_period, min_periods=1, center=True).mean()

    cols = list(wide.columns)[::-1]
    cmap = getattr(px.colors.sequential, colorscale)
    cmap_subset = cmap[len(cmap)//2:][::-1]

    n = len(cols)
    proj_colors = {}
    for rank, col in enumerate(cols):
        idx = int(round(rank * (len(cmap_subset) - 1) / max(1, n - 1)))
        proj_colors[col] = cmap_subset[idx]

    first_date = wide.index.min()
    last_date = wide.index.max()
    cagr_date = pd.to_datetime(cagr_date)

    denom = wide.replace(0,np.nan).abs().max(axis=0)
    scaled = wide.divide(denom, axis=1).fillna(0)

    fig = go.Figure()
    tickvals, ticktext = [], []
    for i, col in enumerate(cols):
        y_offset = i * gap
        y_vals = scaled[col].fillna(0).values
        x_vals = wide.index

        color = proj_colors[col]
        fill_color = rgba_from_rgb(color, fill_alpha)

        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=np.full(y_vals.shape, y_offset, dtype=float),
                mode="lines",
                line=dict(width=0),
                hoverinfo="skip",
                showlegend=False
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals + y_offset,
                mode="lines",
                fill="tonexty",
                line=dict(color=color, width=1.5),
                line_shape="hvh", # spline
                fillcolor=fill_color,
                name=col,
                customdata=np.c_[wide[col]],
                hovertemplate="<b>%{fullData.name}</b><br>%{x|%d %b %Y}: %{customdata[0]:,.0f}<extra></extra>",
                showlegend=False
            )
        )
        tickvals.append(y_offset)

        # Calculate CAGR
        pre = wide.loc[cagr_date, col]
        post = wide.loc[last_date, col]
        years = (last_date - cagr_date).days / 365
        cagr = calc_cagr(pre, post, years) * 100

        if cagr > 0:
            annotation_text = f"+{cagr:,.0f}%"
        elif cagr < 0:
            annotation_text = f"{cagr:,.0f}%"
        else:
            annotation_text = "--"
        ticktext.append(f"<b>{col}</b>: {annotation_text}")

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(size=12, color="#111"),
        margin=dict(l=0, r=80, t=0, b=0),
        showlegend=False,
        title=dict(text="", x=0, xanchor="left", font=dict(size=14, color="#111"))
    )
    fig.update_xaxes(title="", showgrid=False, visible=False, linecolor="#000", linewidth=1)
    fig.update_yaxes(
        title="",
        side="right",
        showgrid=False,
        tickmode="array",
        ticklabelposition="outside top",
        #ticklabelshift=-1,
        ticklabelstandoff=5,
        tickvals=tickvals,
        ticktext=ticktext,
        zeroline=False,
        tickcolor="#000",
        showline=False
    )
    return fig