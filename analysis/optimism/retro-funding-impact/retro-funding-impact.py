import marimo

__generated_with = "unknown"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def setup():
    # Local, self-contained setup. Reads pre-exported Parquet snapshots from
    # ./data — no OSO API key or network access required.
    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go
    from pathlib import Path

    try:
        _base = Path(__file__).parent
    except NameError:
        _base = Path.cwd()
    DATA = _base / "data"
    return DATA, go, mo, pd


@app.cell(hide_code=True)
def style_config():
    # Optimism stylesheet — editorial neutrals + serif headlines, with the
    # Optimism red reserved as the single brand accent (used for funding only).
    colors = {
        "ink": "#1a1814",
        "ink_2": "#3a342b",
        "ink_3": "#5d5445",
        "paper": "#f5f1ea",
        "paper_2": "#f0eeeb",
        "rule": "#d5cfc5",
        "accent": "#ff0420",
        "signal": "#c8341d",
        "healthy": "#1e8a7a",
        "warm": "#d97c2a",
        "purple": "#7b5ea7",
    }

    fonts = {
        "headline": "Georgia, 'Iowan Old Style', 'Times New Roman', serif",
        "body": "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
        "mono": "'SF Mono', 'JetBrains Mono', 'Cascadia Code', monospace",
    }

    CHART_LAYOUT = dict(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family=fonts["body"], size=12, color=colors["ink"]),
        margin=dict(t=16, l=60, r=48, b=44),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(showgrid=False, linecolor=colors["ink"], linewidth=1, ticks="outside"),
        yaxis=dict(showgrid=True, gridcolor=colors["rule"], linecolor=colors["ink"], linewidth=1, ticks="outside"),
    )

    LINE_COLORS = ["#2a3d8f", colors["healthy"], colors["purple"], colors["warm"], colors["ink_2"]]
    return CHART_LAYOUT, LINE_COLORS, colors, fonts


@app.cell(hide_code=True)
def helpers():
    FAMILY_ORDER = ["onchain_op", "onchain_superchain", "defillama", "github"]

    ROUND_NAMES = {
        "RF2": "RetroPGF 2",
        "RF3": "RetroPGF 3",
        "RF4": "Retro Funding 4",
        "RF5": "Retro Funding 5",
        "RF6": "Retro Funding 6",
        "S7": "Season 7",
        "S8": "Season 8",
    }

    def fmt_op(v):
        if v is None:
            return "-"
        v = float(v)
        if abs(v) >= 1e6:
            return f"{v / 1e6:.1f}M OP"
        if abs(v) >= 1e3:
            return f"{v / 1e3:.0f}K OP"
        return f"{v:,.0f} OP"

    def fmt_usd(v):
        if v is None:
            return "-"
        v = float(v)
        if abs(v) >= 1e6:
            return f"${v / 1e6:.1f}M"
        if abs(v) >= 1e3:
            return f"${v / 1e3:.0f}K"
        return f"${v:,.0f}"

    return FAMILY_ORDER, ROUND_NAMES, fmt_op, fmt_usd


@app.cell(hide_code=True)
def header(colors, fonts, mo):
    mo.Html(
        f'<div style="padding:40px 0 26px; border-bottom:2px solid {colors["accent"]}; margin-bottom:34px;">'
        f'<h1 style="font-family:{fonts["headline"]}; font-size:2.4rem; font-weight:400; '
        f'color:{colors["ink"]}; margin:0 0 16px; line-height:1.05; letter-spacing:-0.025em;">'
        f'Optimism Retro Funding</h1>'
        f'<p style="font-family:{fonts["body"]}; font-size:1.02rem; color:{colors["ink_2"]}; '
        f'margin:0; line-height:1.55;">'
        f'Funding awarded to every Optimism Retro Funding recipient (RetroPGF 2 through Season 8), '
        f'alongside onchain and developer metrics for recipients mapped to an OSS Directory project. '
        f'This is a local snapshot; data is read from Parquet files in ./data.'
        f'</p>'
        f'</div>'
    )
    return


@app.cell(hide_code=True)
def load_funding(DATA, pd):
    df_funding = pd.read_parquet(DATA / "rf_funding_by_project.parquet").sort_values(
        "total_op", ascending=False
    )
    return (df_funding,)


@app.cell(hide_code=True)
def load_program_totals(DATA, pd):
    df_program = pd.read_parquet(DATA / "rf_program_summary.parquet")
    return (df_program,)


@app.cell(hide_code=True)
def kpi_cards(df_program, fmt_op, fmt_usd, mo):
    _p = df_program.iloc[0]
    _first = str(_p["first_date"])[:7]
    _last = str(_p["last_date"])[:7]

    mo.hstack(
        [
            mo.stat(
                label="Total OP awarded",
                value=fmt_op(_p["total_op"]),
                bordered=True,
                caption="RF2 through Season 8",
            ),
            mo.stat(
                label="Value at award",
                value=fmt_usd(_p["total_usd"]),
                bordered=True,
                caption="USD at time of award",
            ),
            mo.stat(
                label="Recipients",
                value=f"{int(_p['num_recipients']):,}",
                bordered=True,
                caption=f"{int(_p['num_mapped']):,} with impact metrics",
            ),
            mo.stat(
                label="Active period",
                value=f"{_first} to {_last}",
                bordered=True,
                caption=f"{int(_p['num_programs'])} funding programs",
            ),
        ],
        widths="equal",
        gap=1,
    )
    return


@app.cell(hide_code=True)
def kpi_note(colors, df_program, fmt_op, fmt_usd, fonts, mo):
    _p = df_program.iloc[0]
    mo.Html(
        f'<p style="font-family:{fonts["body"]}; font-size:0.85rem; color:{colors["ink_3"]}; '
        f'margin:12px 0 0; line-height:1.5;">'
        f'{fmt_op(_p["mapped_op"])} ({fmt_usd(_p["mapped_usd"])}) of the total went to the '
        f'{int(_p["num_mapped"])} recipients mapped to an OSS Directory project. Impact metrics '
        f'are available for those recipients only.'
        f'</p>'
    )
    return


@app.cell(hide_code=True)
def load_round_totals(DATA, pd):
    df_rounds = pd.read_parquet(DATA / "rf_funding_by_round.parquet").sort_values("first_date")
    return (df_rounds,)


@app.cell(hide_code=True)
def rounds_header(colors, fonts, mo):
    mo.Html(
        f'<div style="margin:46px 0 18px;">'
        f'<h2 style="font-family:{fonts["headline"]}; font-size:1.5rem; font-weight:500; '
        f'color:{colors["ink"]}; margin:0 0 8px; letter-spacing:-0.01em;">Funding by round</h2>'
        f'<p style="font-family:{fonts["body"]}; font-size:0.92rem; color:{colors["ink_3"]}; '
        f'margin:0; line-height:1.55;">'
        f'OP awarded in each round, from RetroPGF 2 (2023) to Season 8 (2026).</p>'
        f'</div>'
    )
    return


@app.cell(hide_code=True)
def rounds_chart(CHART_LAYOUT, ROUND_NAMES, colors, df_rounds, fmt_op, fmt_usd, go, mo):
    _d = df_rounds.copy()
    _d["label"] = _d["season"].map(ROUND_NAMES).fillna(_d["season"])

    _fig = go.Figure()
    _fig.add_trace(
        go.Bar(
            x=_d["label"],
            y=_d["total_op"],
            marker_color=colors["accent"],
            customdata=list(zip(_d["total_usd"], _d["num_projects"])),
            hovertemplate="%{y:,.0f} OP<br>$%{customdata[0]:,.0f}<br>%{customdata[1]} projects<extra></extra>",
        )
    )
    _layout = dict(CHART_LAYOUT)
    _layout["height"] = 320
    _layout["hovermode"] = "closest"
    _layout["xaxis"] = {**CHART_LAYOUT["xaxis"], "title": ""}
    _layout["yaxis"] = {**CHART_LAYOUT["yaxis"], "title": "OP awarded", "rangemode": "tozero"}
    _fig.update_layout(**_layout)

    _t = _d.copy()
    _t["Round"] = _t["label"]
    _t["OP awarded"] = _t["total_op"].apply(fmt_op)
    _t["Value (USD)"] = _t["total_usd"].apply(fmt_usd)
    _t["Projects"] = _t["num_projects"]
    _t["Awards"] = _t["num_awards"]

    mo.vstack(
        [
            mo.ui.plotly(_fig, config={"displayModeBar": False}),
            mo.ui.table(
                _t[["Round", "OP awarded", "Value (USD)", "Projects", "Awards"]].reset_index(drop=True),
                selection=None,
                show_column_summaries=False,
                show_data_types=False,
                page_size=10,
            ),
        ],
        gap=1,
    )
    return


@app.cell(hide_code=True)
def leaderboard_header(colors, fonts, mo):
    mo.Html(
        f'<div style="margin:46px 0 18px;">'
        f'<h2 style="font-family:{fonts["headline"]}; font-size:1.5rem; font-weight:500; '
        f'color:{colors["ink"]}; margin:0 0 8px; letter-spacing:-0.01em;">Funding leaderboard</h2>'
        f'<p style="font-family:{fonts["body"]}; font-size:0.92rem; color:{colors["ink_3"]}; '
        f'margin:0; line-height:1.55;">'
        f'All recipients, ranked by OP received across all rounds. USD values each award at the OP '
        f'price on its award date.</p>'
        f'</div>'
    )
    return


@app.cell(hide_code=True)
def leaderboard(df_funding, fmt_op, fmt_usd, mo):
    _t = df_funding.copy()
    _t["Recipient"] = _t["recipient_name"]
    _t["Total OP"] = _t["total_op"].apply(fmt_op)
    _t["Value (USD)"] = _t["total_usd"].apply(fmt_usd)
    _t["Rounds"] = _t["seasons"]
    _t["Awards"] = _t["num_awards"]
    _t["Impact data"] = _t["is_mapped"].map({True: "Yes", False: "-"})
    _t["First"] = _t["first_award_date"].astype(str)
    _t["Last"] = _t["last_award_date"].astype(str)
    _display = _t[["Recipient", "Total OP", "Value (USD)", "Rounds", "Awards", "Impact data", "First", "Last"]]

    mo.ui.table(
        _display.reset_index(drop=True),
        selection=None,
        show_column_summaries=False,
        show_data_types=False,
        page_size=15,
        freeze_columns_left=["Recipient"],
    )
    return


@app.cell(hide_code=True)
def explorer_header(colors, fonts, mo):
    mo.Html(
        f'<div style="margin:46px 0 18px;">'
        f'<h2 style="font-family:{fonts["headline"]}; font-size:1.5rem; font-weight:500; '
        f'color:{colors["ink"]}; margin:0 0 8px; letter-spacing:-0.01em;">'
        f'Project explorer</h2>'
        f'<p style="font-family:{fonts["body"]}; font-size:0.92rem; color:{colors["ink_3"]}; '
        f'margin:0; line-height:1.55;">'
        f'Select a project and one or more metrics. The red step line is cumulative OP awarded '
        f'(right axis); the other lines are the selected metrics (left axis).</p>'
        f'</div>'
    )
    return


@app.cell(hide_code=True)
def explorer_controls(df_funding, mo):
    # Only recipients mapped to an OSS Directory project have impact metrics.
    _mapped = df_funding[df_funding["is_mapped"]].sort_values("total_op", ascending=False)
    _names = _mapped["recipient_name"].tolist()
    _default_name = "Stargate Finance" if "Stargate Finance" in _names else (_names[0] if _names else None)

    project_dd = mo.ui.dropdown(
        options=_names,
        value=_default_name,
        label="**Project**",
        searchable=True,
    )
    funding_unit = mo.ui.radio(
        options=["OP", "USD"],
        value="OP",
        label="**Funding overlay**",
        inline=True,
    )
    mo.hstack([project_dd, funding_unit], justify="start", gap=2)
    return funding_unit, project_dd


@app.cell(hide_code=True)
def load_all_metrics(DATA, pd):
    # Load the full metrics table ONCE; the explorer filters it in-memory.
    df_all_metrics = pd.read_parquet(DATA / "rf_metrics_by_project_monthly.parquet")
    return (df_all_metrics,)


@app.cell(hide_code=True)
def load_project_metrics(df_all_metrics, df_funding, project_dd):
    _match = df_funding.loc[df_funding["recipient_name"] == project_dd.value, "project_id"]
    _pid = _match.iloc[0] if len(_match) else None
    df_proj = (
        df_all_metrics[df_all_metrics["project_id"] == _pid]
        .sort_values("sample_month")
        .reset_index(drop=True)
    )
    return (df_proj,)


@app.cell(hide_code=True)
def metric_controls(FAMILY_ORDER, df_proj, mo):
    _impact = df_proj[df_proj["metric_family"] != "funding"]
    _counts = (
        _impact.groupby(["metric_family", "metric_label"])["amount"]
        .count()
        .reset_index()
        .rename(columns={"amount": "n"})
    )
    _counts["_fam_rank"] = _counts["metric_family"].apply(
        lambda f: FAMILY_ORDER.index(f) if f in FAMILY_ORDER else 99
    )
    _counts = _counts.sort_values(["_fam_rank", "n"], ascending=[True, False])
    _labels = _counts["metric_label"].tolist()

    if _labels:
        metric_ms = mo.ui.multiselect(
            options=_labels,
            value=[_labels[0]],
            label="**Impact metrics**",
            full_width=True,
        )
        _widget = metric_ms
    else:
        metric_ms = mo.ui.multiselect(options=[], value=[], label="**Impact metrics**")
        _widget = mo.md("*No onchain, DeFi, or GitHub metrics for this project. Funding history is shown below.*")

    _widget
    return (metric_ms,)


@app.cell(hide_code=True)
def explorer_chart(
    CHART_LAYOUT,
    LINE_COLORS,
    colors,
    df_proj,
    fonts,
    funding_unit,
    go,
    metric_ms,
    mo,
    project_dd,
):
    _unit = funding_unit.value
    _fund_key = "funding_op" if _unit == "OP" else "funding_usd"
    _fund = df_proj[df_proj["metric_key"] == _fund_key].sort_values("sample_month")

    _fig = go.Figure()

    if not _fund.empty:
        _cum = _fund["amount"].cumsum()
        _fig.add_trace(
            go.Scatter(
                x=_fund["sample_month"],
                y=_cum,
                name=f"Cumulative funding ({_unit})",
                mode="lines",
                line=dict(color=colors["accent"], width=2.5, shape="hvh"),
                yaxis="y2",
                hovertemplate=(
                    "%{y:,.0f} OP cumulative<extra>Funding</extra>"
                    if _unit == "OP"
                    else "$%{y:,.0f} cumulative<extra>Funding</extra>"
                ),
            )
        )

    _selected = list(metric_ms.value) if metric_ms.value else []
    for _i, _label in enumerate(_selected):
        _m = df_proj[df_proj["metric_label"] == _label].sort_values("sample_month")
        if _m.empty:
            continue
        _fig.add_trace(
            go.Scatter(
                x=_m["sample_month"],
                y=_m["amount"],
                mode="lines",
                name=_label,
                line=dict(width=2.5, color=LINE_COLORS[_i % len(LINE_COLORS)], shape="hvh"),
                yaxis="y",
                hovertemplate="%{y:,.0f}<extra>" + _label + "</extra>",
            )
        )

    _layout = dict(CHART_LAYOUT)
    _layout["height"] = 420
    _layout["yaxis"] = {**CHART_LAYOUT["yaxis"], "title": "Impact metric", "rangemode": "tozero"}
    _layout["yaxis2"] = dict(
        title=dict(text=f"Cumulative funding ({_unit})", font=dict(color=colors["accent"])),
        overlaying="y",
        side="right",
        showgrid=False,
        rangemode="tozero",
        tickfont=dict(color=colors["accent"]),
    )
    _fig.update_layout(**_layout)

    mo.vstack(
        [
            mo.Html(
                f'<div style="font-family:{fonts["headline"]}; font-size:1.15rem; '
                f'color:{colors["ink"]}; margin:6px 0 2px;">{project_dd.value}</div>'
            ),
            mo.ui.plotly(_fig, config={"displayModeBar": False}),
        ]
    )
    return


@app.cell(hide_code=True)
def project_round_table(df_proj, fmt_op, fmt_usd, mo, project_dd):
    _f = df_proj[df_proj["metric_key"].isin(["funding_op", "funding_usd"])].copy()
    if _f.empty:
        _out = mo.md("*No mapped funding rows for this project.*")
    else:
        _piv = _f.pivot_table(
            index="sample_month", columns="metric_key", values="amount", aggfunc="sum"
        ).reset_index()
        _piv = _piv.sort_values("sample_month")
        _piv["Month"] = _piv["sample_month"].astype(str).str[:7]
        _piv["OP awarded"] = _piv.get("funding_op").apply(fmt_op)
        _piv["Value (USD)"] = _piv.get("funding_usd").apply(fmt_usd)
        _out = mo.vstack(
            [
                mo.md(f"**{project_dd.value} funding history**"),
                mo.ui.table(
                    _piv[["Month", "OP awarded", "Value (USD)"]].reset_index(drop=True),
                    selection=None,
                    show_column_summaries=False,
                    show_data_types=False,
                    page_size=12,
                ),
            ]
        )
    _out
    return


@app.cell(hide_code=True)
def methodology(colors, fonts, mo):
    mo.Html(
        f'<div style="margin-top:48px; padding-top:22px; border-top:1px solid {colors["rule"]};">'
        f'<div style="font-family:{fonts["mono"]}; font-size:10px; color:{colors["ink_3"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:10px;">METHODOLOGY</div>'
        f'<p style="font-family:{fonts["body"]}; font-size:0.86rem; color:{colors["ink_3"]}; '
        f'line-height:1.6; margin:0 0 10px;">'
        f'<b>Funding source.</b> Award amounts come from the OSO oss-funding registry, which records '
        f'both the native OP token amount and its USD value at the time of award, tagged by round. '
        f'Totals reconcile to the canonical round allocations (RF2 10M OP, RF3 30M, RF4 10M, RF5 8M, '
        f'RF6 2.4M, plus the Season 7 and 8 mission payouts).'
        f'</p>'
        f'<p style="font-family:{fonts["body"]}; font-size:0.86rem; color:{colors["ink_3"]}; '
        f'line-height:1.6; margin:0 0 10px;">'
        f'<b>Rounds covered.</b> RetroPGF 2 through Season 8. RetroPGF 1 (a small USDC pilot) is not '
        f'indexed. Optimism Governance Fund grants are a separate program and are excluded. Of the '
        f'$171M / 79.5M OP awarded, this snapshot maps $144M / 69.9M OP to 692 projects in OSS '
        f'Directory; the rest went to recipients not yet linked to a project.'
        f'</p>'
        f'<p style="font-family:{fonts["body"]}; font-size:0.86rem; color:{colors["ink_3"]}; '
        f'line-height:1.6; margin:0;">'
        f'<b>Impact metrics</b> come from OSO monthly timeseries, shown for OP Mainnet and, where '
        f'available, summed across the Superchain (cross-chain address counts can double-count, so '
        f'Superchain figures are directional). Funding is shown alongside activity and does not '
        f'imply causation.'
        f'</p>'
        f'</div>'
    )
    return


if __name__ == "__main__":
    app.run()
