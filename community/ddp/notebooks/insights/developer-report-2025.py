import marimo

__generated_with = "unknown"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def header_title(mo):
    mo.md("""
    # 2025 Developer Trends
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO Team</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-02-17</span></small>

    Explore an interactive reproduction of the [Electric Capital Developer Report](https://www.developerreport.com), updated with 2025 data.
    """)
    return


@app.cell(hide_code=True)
def header_accordion(mo):
    mo.accordion({
        "Overview": mo.md("""
- As of December 2025, the total number of monthly active developers (MADs) across all crypto ecosystems reached its highest recorded level, driven by growth in newer chains and Layer 2s
- Ethereum remains the largest single ecosystem by MAD count, though its share of total crypto developers continued to decline as multi-chain activity increases
- Newcomer developers (those active for less than 1 year) represented a significant portion of 2025 MADs, indicating continued onboarding despite broader market fluctuations
- Full-time developers (active 10+ months of the year) showed resilience, with retention rates improving year-over-year compared to the 2022-2023 downturn
        """),
        "Context": mo.md("""
- This analysis covers monthly active developers across all crypto ecosystems
- Data source: Open Dev Data (Electric Capital) via OSO data warehouse
- Time period: January 2015 to December 2025 (full historical data)
- Developers are original code authors (merge/PR integrators are not counted unless they authored commits)
- Monthly active developers are measured using a 28-day rolling activity window
- Uses curated Open Dev Data repository set (not comprehensive GitHub coverage)
- Developer identity resolution may miss some connections across accounts or pseudonyms
- Data freshness depends on Open Dev Data and OSO pipeline update cadence
        """),
        "Data Sources": mo.md("""
- **Open Dev Data** — Electric Capital's developer activity dataset, [github.com/electric-capital/crypto-ecosystems](https://github.com/electric-capital/crypto-ecosystems)
- **OSO API** — Data pipeline and metrics, [docs.oso.xyz](https://docs.oso.xyz/)
- **Metric Definitions** — [Activity](/data/metric-definitions/activity)
- **Key Models** — `oso.stg_opendevdata__eco_mads`, `oso.stg_opendevdata__ecosystems`
        """),
    })
    return


@app.cell(hide_code=True)
def setup_imports():
    import pandas as pd
    import plotly.graph_objects as go
    return go, pd


@app.cell(hide_code=True)
def setup_pyoso():
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


@app.cell(hide_code=True)
def setup_constants():
    # Electric Capital color palette (matching the reference charts)
    EC_LIGHT_BLUE = "#7EB8DA"   # Primary fill color for area charts
    EC_DARK_BLUE = "#1B4F72"    # For established developers / titles
    EC_MEDIUM_BLUE = "#5499C7"  # For emerging developers
    EC_TITLE_BLUE = "#1B4F72"   # Title color
    EC_SUBTITLE_GRAY = "#666666"  # Subtitle color

    # Tenure colors (matching EC report: light=newcomers at top, dark=established at bottom)
    TENURE_COLORS = {
        "Newcomers": "#B5D5E8",      # Lightest blue (top of stack)
        "Emerging": "#5DADE2",        # Medium blue (middle)
        "Established": "#1B4F72"      # Dark blue (bottom of stack)
    }

    # Activity level colors
    ACTIVITY_COLORS = {
        "One-time": "#F5B041",   # Orange/gold
        "Part-time": "#EC7063",  # Coral/red
        "Full-time": "#5DADE2"   # Blue
    }

    # Ecosystems to query
    ECOSYSTEMS = ["All Web3 Ecosystems", "Bitcoin", "Ethereum", "Solana"]
    SUPPORTED_ECOSYSTEMS = ["Bitcoin", "Ethereum", "Solana"]
    return (
        ACTIVITY_COLORS,
        ECOSYSTEMS,
        EC_LIGHT_BLUE,
        SUPPORTED_ECOSYSTEMS,
        TENURE_COLORS,
    )


@app.cell(hide_code=True)
def related(mo):
    mo.md("""
    ## Related

    **Metric Definitions**
    - [Activity](../data/metric-definitions/activity.py) — Monthly Active Developer (MAD) methodology

    **Other Insights**
    - [Lifecycle Analysis](./developer-lifecycle.py)
    - [Retention Analysis](./developer-retention.py)
    - [DeFi Developer Journeys](./defi-developer-journeys.py)
    - [Speedrun Ethereum](./speedrun-ethereum.py)
    """)
    return


@app.cell(hide_code=True)
def helper_apply_ec_style():
    def apply_ec_style(fig, title=None, subtitle=None, y_title=None, show_legend=True,
                       right_margin=180):
        # Build title text with HTML styling
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

        # Style x-axis (clean, minimal)
        fig.update_xaxes(
            showgrid=False,
            showline=True,
            linecolor="#1F2937",
            linewidth=1,
            tickfont=dict(size=11, color="#666"),
            title="",
            tickformat="%b %Y"  # Format as "Jan 2020"
        )

        # Style y-axis (light gridlines, clean labels)
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
            tickformat=",d"  # Format with thousands separator
        )

        return fig
    return (apply_ec_style,)


@app.cell(hide_code=True)
def helper_add_callout_annotation():
    def add_callout_annotation(fig, y_value, label, value, description,
                               color="#1B4F72", y_position=None):
        # Build annotation text with line breaks
        text = f"<b>{label}</b><br><br><span style='font-size:18px'>{value}</span><br><br><span style='font-size:11px'>{description}</span>"

        fig.add_annotation(
            x=1.02,
            y=y_value if y_position is None else y_position,
            xref="paper",
            yref="y" if y_position is None else "paper",
            text=text,
            showarrow=True,
            arrowhead=0,
            arrowwidth=1,
            arrowcolor="#999999",
            ax=20,
            ay=0,
            bordercolor="#CCCCCC",
            borderwidth=1,
            borderpad=8,
            bgcolor="white",
            font=dict(size=11, color=color),
            align="left",
            xanchor="left"
        )
        return fig
    return (add_callout_annotation,)


@app.cell(hide_code=True)
def helper_add_tenure_legend():
    def add_tenure_legend(fig, newcomers, emerging, established, colors):
        # Position annotations vertically on right side
        annotations = [
            (0.85, f"<b>{newcomers:,.0f}</b>", "Newcomers", "<1 year in crypto", colors["Newcomers"]),
            (0.55, f"<b>{emerging:,.0f}</b>", "Emerging", "1-2 yrs in crypto", colors["Emerging"]),
            (0.25, f"<b>{established:,.0f}</b>", "Established", "2+ years in crypto", colors["Established"]),
        ]

        for y_pos, value, label, desc, color in annotations:
            fig.add_annotation(
                x=1.02,
                y=y_pos,
                xref="paper",
                yref="paper",
                text=f"{value}<br><b style='color:{color}'>{label}</b><br><span style='font-size:10px;color:#666'>{desc}</span>",
                showarrow=False,
                font=dict(size=12, color="#333"),
                align="left",
                xanchor="left",
                bgcolor="white",
                bordercolor=color,
                borderwidth=2,
                borderpad=6
            )

        return fig
    return (add_tenure_legend,)


@app.cell(hide_code=True)
def test_connection(mo, pyoso_db_conn):
    _test_df = mo.sql("""SELECT 1 AS test""", engine=pyoso_db_conn, output=False)
    return


@app.cell(hide_code=True)
def query_all_data(ECOSYSTEMS, mo, pd, pyoso_db_conn):
    ecosystems_str = ", ".join(f"'{e}'" for e in ECOSYSTEMS)

    df_all = mo.sql(
        f"""
        SELECT
            e.name AS ecosystem_name,
            m.day,
            m.all_devs AS total_devs,
            m.devs_0_1y AS newcomers,
            m.devs_1_2y AS emerging,
            m.devs_2y_plus AS established,
            m.one_time_devs AS one_time,
            m.part_time_devs AS part_time,
            m.full_time_devs AS full_time
        FROM oso.stg_opendevdata__eco_mads m
        JOIN oso.stg_opendevdata__ecosystems e ON m.ecosystem_id = e.id
        WHERE e.name IN ({ecosystems_str})
          AND m.day >= DATE '2015-01-01'
          AND m.day < DATE '2026-01-01'
        ORDER BY e.name, m.day
        """,
        engine=pyoso_db_conn,
        output=False
    )

    df_all['day'] = pd.to_datetime(df_all['day'])

    # Add time period columns for aggregation
    df_all['year'] = df_all['day'].dt.year
    df_all['quarter'] = df_all['day'].dt.to_period('Q').dt.to_timestamp()
    df_all['month'] = df_all['day'].dt.to_period('M').dt.to_timestamp()
    return (df_all,)


@app.cell(hide_code=True)
def data_summary(df_all, mo):
    _ecosystems = df_all['ecosystem_name'].unique()
    _date_range = f"{df_all['day'].min().strftime('%Y-%m-%d')} to {df_all['day'].max().strftime('%Y-%m-%d')}"
    _rows = len(df_all)
    mo.md(f"**Data loaded:** {_rows:,} rows across {len(_ecosystems)} ecosystems ({_date_range})")
    return


@app.cell(hide_code=True)
def section_overall_trends(mo):
    mo.md("""
    ## Overall Developer Trends
    *High-level patterns across all crypto ecosystems*
    """)
    return


@app.cell(hide_code=True)
def chart1_controls(mo):
    chart1_time_range = mo.ui.dropdown(
        options=["All Time", "Last 5 Years", "Last 3 Years", "Last Year"],
        value="All Time",
        label="Time Range"
    )

    mo.hstack([chart1_time_range], gap=2)
    return (chart1_time_range,)


@app.cell(hide_code=True)
def chart1_total_mads(
    EC_LIGHT_BLUE,
    add_callout_annotation,
    apply_ec_style,
    chart1_time_range,
    df_all,
    go,
    mo,
    pd,
):
    """Chart 1: Total Monthly Active Developers Over Time"""

    # Filter to "All Web3 Ecosystems"
    _df = df_all[df_all['ecosystem_name'] == 'All Web3 Ecosystems'].copy()

    # Filter by time range
    if chart1_time_range.value == "Last 5 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]
    elif chart1_time_range.value == "Last 3 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2022-01-01')]
    elif chart1_time_range.value == "Last Year":
        _df = _df[_df['day'] >= pd.Timestamp('2024-01-01')]

    # Get current values
    _current_date = _df['day'].max()
    _current_value = _df[_df['day'] == _current_date]['total_devs'].values[0]

    _fig = go.Figure()

    # Area chart with EC styling
    _fig.add_trace(go.Scatter(
        x=_df['day'],
        y=_df['total_devs'],
        fill='tozeroy',
        fillcolor=EC_LIGHT_BLUE,
        line=dict(color=EC_LIGHT_BLUE, width=1),
        mode='lines',
        name='Monthly Active Developers',
        hovertemplate='<b>%{x|%b %Y}</b><br>Developers: %{y:,.0f}<extra></extra>'
    ))

    # Apply EC styling
    apply_ec_style(
        _fig,
        title=f"{_current_value:,.0f} monthly active open-source developers contribute to crypto",
        subtitle="All crypto monthly active developers",
        y_title="Developers",
        show_legend=False,
        right_margin=180
    )

    # Annotate: start/end of current year + peak
    _year = int(_current_date.year)
    _df_year = _df[_df["day"].dt.year == _year]

    if len(_df_year) > 0:
        _start_date = _df_year["day"].min()
        _end_date = _df_year["day"].max()
        _start_value = _df_year[_df_year["day"] == _start_date]["total_devs"].iloc[0]
        _end_value = _df_year[_df_year["day"] == _end_date]["total_devs"].iloc[0]

        _fig.add_trace(
            go.Scatter(
                x=[_start_date, _end_date],
                y=[_start_value, _end_value],
                mode="markers",
                marker=dict(size=7, color="#1B4F72", line=dict(width=1, color="white")),
                showlegend=False,
                hovertemplate="<b>%{x|%b %Y}</b><br>Developers: %{y:,.0f}<extra></extra>",
            )
        )

        # Start-of-year value label
        _fig.add_annotation(
            x=_start_date,
            y=_start_value,
            text=f"<b>{_start_date.strftime('%b %Y')}</b><br>{_start_value:,.0f}",
            showarrow=False,
            yshift=-22,
            font=dict(size=10, color="#333"),
            align="center",
            bgcolor="white",
            bordercolor="#CCCCCC",
            borderwidth=1,
            borderpad=5,
        )

        # End-of-year value label
        _fig.add_annotation(
            x=_end_date,
            y=_end_value,
            text=f"<b>{_end_date.strftime('%b %Y')}</b><br>{_end_value:,.0f}",
            showarrow=False,
            yshift=-22,
            font=dict(size=10, color="#333"),
            align="center",
            bgcolor="white",
            bordercolor="#CCCCCC",
            borderwidth=1,
            borderpad=5,
        )

    _peak_idx = _df["total_devs"].idxmax()
    _peak_date = _df.loc[_peak_idx, "day"]
    _peak_value = _df.loc[_peak_idx, "total_devs"]

    _fig.add_trace(
        go.Scatter(
            x=[_peak_date],
            y=[_peak_value],
            mode="markers",
            marker=dict(size=8, color="#1B4F72", line=dict(width=1, color="white")),
            showlegend=False,
            hovertemplate="<b>Peak</b><br>%{x|%b %Y}<br>Developers: %{y:,.0f}<extra></extra>",
        )
    )
    _fig.add_annotation(
        x=_peak_date,
        y=_peak_value,
        text=f"<b>Peak</b><br>{_peak_value:,.0f}<br><span style='font-size:10px;color:#666'>{_peak_date.strftime('%b %Y')}</span>",
        showarrow=True,
        arrowhead=0,
        arrowcolor="#666",
        ax=0,
        ay=-55,
        font=dict(size=11, color="#333"),
        align="center",
        bgcolor="white",
        bordercolor="#CCCCCC",
        borderwidth=1,
        borderpad=6,
    )

    # Prevent annotations from changing the x-axis padding/range
    _fig.update_xaxes(range=[_df["day"].min(), _df["day"].max()], autorange=False)

    _fig.update_layout(height=500)

    mo.ui.plotly(_fig, config={"displayModeBar": False})
    return


@app.cell(hide_code=True)
def chart2_controls(mo):
    chart2_time_range = mo.ui.dropdown(
        options=["All Time", "Last 5 Years", "Last 3 Years", "Last Year"],
        value="All Time",
        label="Time Range"
    )

    mo.hstack([chart2_time_range], gap=2)
    return (chart2_time_range,)


@app.cell(hide_code=True)
def chart2_tenure_composition(
    TENURE_COLORS,
    add_tenure_legend,
    apply_ec_style,
    chart2_time_range,
    df_all,
    go,
    mo,
    pd,
):
    """Chart 2: Developer Composition by Tenure - Stacked Area Chart"""

    # Filter to "All Web3 Ecosystems"
    _df = df_all[df_all['ecosystem_name'] == 'All Web3 Ecosystems'].copy()

    if chart2_time_range.value == "Last 5 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]
    elif chart2_time_range.value == "Last 3 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2022-01-01')]
    elif chart2_time_range.value == "Last Year":
        _df = _df[_df['day'] >= pd.Timestamp('2024-01-01')]

    _fig = go.Figure()

    # Stack order: Established (bottom), Emerging (middle), Newcomers (top)
    # This matches the EC report visual
    for _segment, _col in [("Established", "established"), ("Emerging", "emerging"), ("Newcomers", "newcomers")]:
        _fig.add_trace(go.Scatter(
            x=_df['day'],
            y=_df[_col],
            name=_segment,
            mode='lines',
            stackgroup='one',
            fillcolor=TENURE_COLORS[_segment],
            line=dict(width=0.5, color=TENURE_COLORS[_segment]),
            hovertemplate=f'<b>{_segment}</b><br>%{{x|%b %Y}}<br>Developers: %{{y:,.0f}}<extra></extra>'
        ))

    # Get current values for legend
    _current_row = _df.iloc[-1]
    _current_newcomers = _current_row['newcomers']
    _current_emerging = _current_row['emerging']
    _current_established = _current_row['established']

    apply_ec_style(
        _fig,
        title="But devs working in crypto for 1+ years grew steadily",
        subtitle="All crypto monthly active developers by tenure",
        y_title="Developers",
        show_legend=False,  # We use custom legend
        right_margin=180
    )

    # Add tenure legend on right side
    add_tenure_legend(_fig, _current_newcomers, _current_emerging, _current_established, TENURE_COLORS)

    _fig.update_layout(height=500)

    mo.ui.plotly(_fig, config={"displayModeBar": False})
    return


@app.cell(hide_code=True)
def chart3_controls(mo):
    chart3_period = mo.ui.dropdown(
        options=["YoY (2024 vs 2025)", "3-Year (2022 vs 2025)", "5-Year (2020 vs 2025)"],
        value="YoY (2024 vs 2025)",
        label="Comparison Period"
    )

    mo.hstack([chart3_period], gap=2)
    return (chart3_period,)


@app.cell(hide_code=True)
def chart3_experienced_devs(
    TENURE_COLORS,
    apply_ec_style,
    chart3_period,
    df_all,
    go,
    mo,
):
    """Chart 3: The Experienced Developer Story - Stacked area with comparison annotations"""

    # Filter to "All Web3 Ecosystems"
    _df = df_all[df_all['ecosystem_name'] == 'All Web3 Ecosystems'].copy()

    # Calculate experienced devs (Emerging + Established)
    _df['experienced'] = _df['emerging'] + _df['established']

    # Determine comparison dates based on selection
    _period_map = {
        "YoY (2024 vs 2025)": (2024, 2025, 1),
        "3-Year (2022 vs 2025)": (2022, 2025, 3),
        "5-Year (2020 vs 2025)": (2020, 2025, 5)
    }
    _start_year, _end_year, _years = _period_map[chart3_period.value]

    # Get values at start and end of period
    _start_df = _df[_df['year'] == _start_year]
    _end_df = _df[_df['year'] == _end_year]

    _start_row = _start_df.iloc[-1] if len(_start_df) > 0 else None
    _end_row = _end_df.iloc[-1] if len(_end_df) > 0 else None

    if _start_row is not None and _end_row is not None:
        _start_exp = _start_row['experienced']
        _end_exp = _end_row['experienced']
        _exp_change = _end_exp - _start_exp
        _exp_change_pct = ((_end_exp - _start_exp) / _start_exp) * 100
        _exp_color = "#27AE60" if _exp_change_pct > 0 else "#E74C3C"
        _start_date = _start_row['day']
        _end_date = _end_row['day']
    else:
        _start_exp = _end_exp = _exp_change = _exp_change_pct = 0
        _exp_color = "#666"
        _start_date = _end_date = _df['day'].max()

    # Create stacked area chart (same as tenure composition)
    _fig = go.Figure()

    # Stack order: Established (bottom), Emerging (middle), Newcomers (top)
    for _segment, _col in [("Established", "established"), ("Emerging", "emerging"), ("Newcomers", "newcomers")]:
        _fig.add_trace(go.Scatter(
            x=_df['day'],
            y=_df[_col],
            name=_segment,
            mode='lines',
            stackgroup='one',
            fillcolor=TENURE_COLORS[_segment],
            line=dict(width=0.5, color=TENURE_COLORS[_segment]),
            hovertemplate=f'<b>{_segment}</b><br>%{{x|%b %Y}}<br>Developers: %{{y:,.0f}}<extra></extra>'
        ))

    # Add vertical dashed lines for comparison period
    _fig.add_vline(x=_start_date, line_dash="dash", line_color="#666", line_width=1)
    _fig.add_vline(x=_end_date, line_dash="dash", line_color="#666", line_width=1)

    # Add shaded region between comparison dates
    _fig.add_vrect(
        x0=_start_date, x1=_end_date,
        fillcolor="rgba(200, 200, 200, 0.1)",
        line_width=0
    )

    # Add comparison period label at top
    _fig.add_annotation(
        x=_start_date + (_end_date - _start_date) / 2,
        y=1.02, yref="paper",
        text=f"Dec {_start_year} - {_end_year}",
        showarrow=False,
        font=dict(size=11, color="#666")
    )

    apply_ec_style(
        _fig,
        title=f"Experienced devs (1+ years) grew by <span style='color:{_exp_color}'>{_exp_change_pct:+.0f}%</span> ({_exp_change:+,.0f}) in {_end_year}",
        subtitle=f"This reflects an increase of {_exp_change:+,.0f} developers outside of Newcomers",
        y_title="Developers",
        show_legend=False,
        right_margin=180
    )

    # Add legend on right with current values
    _current = _df.iloc[-1]
    _annotations_data = [
        (0.88, "Newcomers", _current['newcomers'], "<1 year in crypto", TENURE_COLORS["Newcomers"]),
        (0.58, "Emerging", _current['emerging'], "1-2 years in crypto", TENURE_COLORS["Emerging"]),
        (0.28, "Established", _current['established'], "2+ years in crypto", TENURE_COLORS["Established"]),
    ]

    for _y, _label, _val, _desc, _color in _annotations_data:
        _fig.add_annotation(
            x=1.02, y=_y, xref="paper", yref="paper",
            text=f"<span style='color:{_color}'>\u25CF</span> <b>{_label}</b><br><span style='font-size:10px;color:#666'>{_desc}</span>",
            showarrow=False, font=dict(size=11), align="left", xanchor="left"
        )

    # Add point annotations for start/end experienced values
    _fig.add_annotation(
        x=_start_date, y=_start_exp,
        text=f"{_start_exp:,.0f}",
        showarrow=True, arrowhead=0, arrowcolor="#666",
        ax=-30, ay=20,
        font=dict(size=10, color="#666"),
        bgcolor="white", borderpad=2
    )

    _fig.add_annotation(
        x=_end_date, y=_end_exp,
        text=f"<span style='color:{_exp_color}'>{_exp_change_pct:+.0f}%</span><br>{_exp_change:+,.0f} devs",
        showarrow=True, arrowhead=0, arrowcolor=_exp_color,
        ax=40, ay=-20,
        font=dict(size=11),
        bgcolor="white", bordercolor=_exp_color, borderwidth=1, borderpad=4
    )

    _fig.add_annotation(
        x=_end_date, y=_end_exp,
        text=f"{_end_exp:,.0f}",
        showarrow=False,
        yshift=-25,
        font=dict(size=10, color="#666")
    )

    _fig.update_layout(height=500)

    mo.ui.plotly(_fig, config={"displayModeBar": False})
    return


@app.cell(hide_code=True)
def chart4_controls(mo):
    chart4_comparison = mo.ui.dropdown(
        options=["2025 vs 2024", "2024 vs 2023", "2023 vs 2022", "2022 vs 2021"],
        value="2025 vs 2024",
        label="Comparison Period"
    )

    mo.hstack([chart4_comparison], gap=2)
    return (chart4_comparison,)


@app.cell(hide_code=True)
def chart4_developer_changes(
    TENURE_COLORS,
    apply_ec_style,
    chart4_comparison,
    df_all,
    go,
    mo,
):
    """Chart 4: Where Did Developers Go? - Multi-line chart with change annotations"""

    # Filter to "All Web3 Ecosystems"
    _df = df_all[df_all['ecosystem_name'] == 'All Web3 Ecosystems'].copy()

    # Parse comparison years
    _years = chart4_comparison.value.split(" vs ")
    _end_year = int(_years[0])
    _start_year = int(_years[1])

    # Get comparison values
    _start_df = _df[_df['year'] == _start_year]
    _end_df = _df[_df['year'] == _end_year]

    if len(_start_df) == 0 or len(_end_df) == 0:
        _output = mo.md("*Insufficient data for selected comparison period*")
    else:
        _start_row = _start_df.iloc[-1]
        _end_row = _end_df.iloc[-1]
        _start_date = _start_row['day']
        _end_date = _end_row['day']

        # Calculate changes
        _changes = {}
        for _seg in ['newcomers', 'emerging', 'established']:
            _s = _start_row[_seg]
            _e = _end_row[_seg]
            _changes[_seg] = {
                'start': _s,
                'end': _e,
                'diff': _e - _s,
                'pct': ((_e - _s) / _s) * 100 if _s > 0 else 0
            }

        # Find biggest decline for title
        _min_seg = min(_changes.keys(), key=lambda k: _changes[k]['pct'])
        _min_pct = _changes[_min_seg]['pct']

        _fig = go.Figure()

        # Add each tenure segment as a separate line
        _segment_config = [
            ("Newcomers", "newcomers", TENURE_COLORS["Newcomers"]),
            ("Emerging", "emerging", TENURE_COLORS["Emerging"]),
            ("Established", "established", TENURE_COLORS["Established"]),
        ]

        for _label, _col, _color in _segment_config:
            _fig.add_trace(go.Scatter(
                x=_df['day'],
                y=_df[_col],
                name=_label,
                mode='lines',
                line=dict(width=2, color=_color),
                hovertemplate=f'<b>{_label}</b><br>%{{x|%b %Y}}<br>Developers: %{{y:,.0f}}<extra></extra>'
            ))

        # Add vertical dashed lines for comparison period
        _fig.add_vline(x=_start_date, line_dash="dash", line_color="#666", line_width=1)
        _fig.add_vline(x=_end_date, line_dash="dash", line_color="#666", line_width=1)

        # Add comparison period label
        _fig.add_annotation(
            x=_start_date + (_end_date - _start_date) / 2,
            y=1.02, yref="paper",
            text=f"Dec {_start_year} - {_end_year}",
            showarrow=False,
            font=dict(size=11, color="#666")
        )

        apply_ec_style(
            _fig,
            title=f"Developer losses came from the least tenured developers:<br>Newcomers fell by <span style='color:#E74C3C'>{_changes['newcomers']['pct']:.0f}%</span>",
            subtitle="All crypto monthly active developers by tenure",
            y_title="Developers",
            show_legend=False,
            right_margin=180
        )

        # Add change annotations on the right for each segment
        _y_positions = [0.85, 0.50, 0.20]  # Approximate y positions
        for _i, (_label, _col, _color) in enumerate(_segment_config):
            _c = _changes[_col]
            _pct_color = "#27AE60" if _c['pct'] > 0 else "#E74C3C"

            _fig.add_annotation(
                x=1.02, y=_y_positions[_i], xref="paper", yref="paper",
                text=f"<b>{_label}</b><br><span style='font-size:18px;color:{_pct_color}'>{_c['pct']:+.0f}%</span><br><span style='font-size:10px;color:#666'>{_c['diff']:+,.0f} devs</span>",
                showarrow=False,
                font=dict(size=11),
                align="left",
                xanchor="left",
                bgcolor="white",
                bordercolor=_color,
                borderwidth=2,
                borderpad=6
            )

        # Add point markers at comparison dates
        for _label, _col, _color in _segment_config:
            _fig.add_trace(go.Scatter(
                x=[_start_date, _end_date],
                y=[_changes[_col]['start'], _changes[_col]['end']],
                mode='markers',
                marker=dict(size=8, color=_color, line=dict(width=1, color='white')),
                showlegend=False,
                hoverinfo='skip'
            ))

        # Add value labels at start points
        for _label, _col, _color in _segment_config:
            _fig.add_annotation(
                x=_start_date, y=_changes[_col]['start'],
                text=f"{_changes[_col]['start']:,.0f}",
                showarrow=False,
                xshift=-35,
                font=dict(size=9, color="#666")
            )

        _fig.update_layout(height=500)

        _output = mo.ui.plotly(_fig, config={"displayModeBar": False})

    _output
    return


@app.cell(hide_code=True)
def section_newcomer_trends(mo):
    mo.md("""
    ## Newcomer Trends
    *How new developer acquisition tracks with market cycles*
    """)
    return


@app.cell(hide_code=True)
def chart5_controls(mo):
    chart5_granularity = mo.ui.dropdown(
        options=["Yearly", "Quarterly", "Monthly"],
        value="Yearly",
        label="Time Granularity"
    )
    chart5_range = mo.ui.dropdown(
        options=["All Time", "Last 5 Years", "Last 3 Years"],
        value="All Time",
        label="Date Range"
    )

    mo.hstack([chart5_granularity, chart5_range], gap=2)
    return chart5_granularity, chart5_range


@app.cell(hide_code=True)
def chart5_newcomer_volatility(
    EC_LIGHT_BLUE,
    apply_ec_style,
    chart5_granularity,
    chart5_range,
    df_all,
    go,
    mo,
    pd,
):
    """Chart 5: Newcomer Volatility - Bar Chart by Year"""

    # Filter to "All Web3 Ecosystems"
    _df = df_all[df_all['ecosystem_name'] == 'All Web3 Ecosystems'].copy()

    if chart5_range.value == "Last 5 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]
    elif chart5_range.value == "Last 3 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2022-01-01')]

    # Aggregate by selected granularity (take max for rolling window data)
    if chart5_granularity.value == "Yearly":
        _df_agg = _df.groupby('year').agg({'newcomers': 'max'}).reset_index()
        _df_agg['label'] = _df_agg['year'].astype(int).astype(str)
        _x_vals = _df_agg['label']
    elif chart5_granularity.value == "Quarterly":
        _df_agg = _df.groupby('quarter').agg({'newcomers': 'max'}).reset_index()
        _df_agg['label'] = _df_agg['quarter'].dt.strftime('%Y Q%q')
        _x_vals = _df_agg['quarter']
    else:  # Monthly
        _df_agg = _df.groupby('month').agg({'newcomers': 'max'}).reset_index()
        _df_agg['label'] = _df_agg['month'].dt.strftime('%b %Y')
        _x_vals = _df_agg['month']

    # Find peak year for subtitle
    _peak_idx = _df_agg['newcomers'].idxmax()
    _peak_year = _df_agg.loc[_peak_idx, 'label']
    _peak_value = _df_agg.loc[_peak_idx, 'newcomers']

    _fig = go.Figure()

    _fig.add_trace(go.Bar(
        x=_x_vals,
        y=_df_agg['newcomers'],
        marker_color=EC_LIGHT_BLUE,
        text=_df_agg['newcomers'].apply(lambda x: f'{x:,.0f}'),
        textposition='outside',
        textfont=dict(size=10, color="#666"),
        hovertemplate='<b>%{x}</b><br>Newcomers: %{y:,.0f}<extra></extra>'
    ))

    apply_ec_style(
        _fig,
        title="Newcomers tend to follow crypto asset price appreciation",
        subtitle=f"{_peak_value:,.0f} developers joined crypto in {_peak_year}",
        y_title="Developers",
        show_legend=False,
        right_margin=60  # Less margin needed for bar charts
    )

    # Adjust y-axis to fit text labels above bars
    _max_val = _df_agg['newcomers'].max()
    _fig.update_yaxes(range=[0, _max_val * 1.15])

    _fig.update_layout(height=450)

    mo.ui.plotly(_fig, config={"displayModeBar": False})
    return


@app.cell(hide_code=True)
def section_ecosystem_landscape(mo):
    mo.md("""
    ## Ecosystem Landscape
    *Developer distribution across major ecosystems*
    """)
    return


@app.cell(hide_code=True)
def chart6_controls(mo):
    chart6_view = mo.ui.dropdown(
        options=["Percentage (Stacked)", "Absolute Counts"],
        value="Percentage (Stacked)",
        label="View Type"
    )

    chart6_time_range = mo.ui.dropdown(
        options=["All Time", "Last 5 Years", "Last 3 Years", "Last Year"],
        value="All Time",
        label="Time Range"
    )

    mo.hstack([chart6_view, chart6_time_range], gap=2)
    return chart6_time_range, chart6_view


@app.cell(hide_code=True)
def chart6_btc_eth_share(
    apply_ec_style,
    chart6_time_range,
    chart6_view,
    df_all,
    go,
    mo,
    pd,
):
    """Chart 6: Developer Distribution - 100% stacked area showing ecosystem breakdown"""

    # Get all ecosystem data
    _df_total = df_all[df_all['ecosystem_name'] == 'All Web3 Ecosystems'].copy()
    _df_btc = df_all[df_all['ecosystem_name'] == 'Bitcoin'].copy()
    _df_eth = df_all[df_all['ecosystem_name'] == 'Ethereum'].copy()
    _df_sol = df_all[df_all['ecosystem_name'] == 'Solana'].copy()

    # Merge on day
    _df = _df_total[['day', 'total_devs']].rename(columns={'total_devs': 'total'})
    _df = _df.merge(_df_btc[['day', 'total_devs']].rename(columns={'total_devs': 'bitcoin'}), on='day', how='left')
    _df = _df.merge(_df_eth[['day', 'total_devs']].rename(columns={'total_devs': 'ethereum'}), on='day', how='left')
    _df = _df.merge(_df_sol[['day', 'total_devs']].rename(columns={'total_devs': 'solana'}), on='day', how='left')

    # Fill NaN with 0
    _df = _df.fillna(0)

    # Calculate "Other" ecosystems (total minus known)
    _df['other'] = _df['total'] - _df['bitcoin'] - _df['ethereum'] - _df['solana']
    _df['other'] = _df['other'].clip(lower=0)  # Ensure non-negative

    # Calculate percentages
    _df['btc_pct'] = (_df['bitcoin'] / _df['total']) * 100
    _df['eth_pct'] = (_df['ethereum'] / _df['total']) * 100
    _df['sol_pct'] = (_df['solana'] / _df['total']) * 100
    _df['other_pct'] = (_df['other'] / _df['total']) * 100

    # Apply time filter
    if chart6_time_range.value == "Last 5 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]
    elif chart6_time_range.value == "Last 3 Years":
        _df = _df[_df['day'] >= pd.Timestamp('2022-01-01')]
    elif chart6_time_range.value == "Last Year":
        _df = _df[_df['day'] >= pd.Timestamp('2024-01-01')]

    # Colors matching EC style
    _btc_color = "#F7931A"   # Bitcoin orange
    _eth_color = "#627EEA"   # Ethereum purple/blue
    _sol_color = "#14F195"   # Solana green
    _other_color = "#9CA3AF" # Gray for other

    _fig = go.Figure()

    # Current shares for legend
    _current = _df.iloc[-1]
    _btc_eth_share = _current['btc_pct'] + _current['eth_pct']

    if chart6_view.value == "Percentage (Stacked)":
        # 100% stacked area chart
        # Stack from bottom: Other, Solana, Ethereum, Bitcoin (so BTC+ETH are at top)
        _segments = [
            ("Other ecosystems", "other_pct", _other_color),
            ("Solana", "sol_pct", _sol_color),
            ("Ethereum", "eth_pct", _eth_color),
            ("Bitcoin", "btc_pct", _btc_color),
        ]

        for _name, _col, _color in _segments:
            _current_val = _current[_col]
            _fig.add_trace(go.Scatter(
                x=_df['day'],
                y=_df[_col],
                name=f"{_name} ({_current_val:.0f}%)",
                mode='lines',
                stackgroup='one',
                groupnorm='percent',
                fillcolor=_color,
                line=dict(width=0.5, color=_color),
                hovertemplate=f'<b>{_name}</b><br>%{{x|%b %Y}}<br>Share: %{{y:.1f}}%<extra></extra>'
            ))

        _fig.update_yaxes(range=[0, 100], ticksuffix="%")

    else:
        # Absolute counts stacked
        _segments = [
            ("Other ecosystems", "other", _other_color),
            ("Solana", "solana", _sol_color),
            ("Ethereum", "ethereum", _eth_color),
            ("Bitcoin", "bitcoin", _btc_color),
        ]

        for _name, _col, _color in _segments:
            _current_val = _current[_col]
            _fig.add_trace(go.Scatter(
                x=_df['day'],
                y=_df[_col],
                name=f"{_name} ({_current_val:,.0f})",
                mode='lines',
                stackgroup='one',
                fillcolor=_color,
                line=dict(width=0.5, color=_color),
                hovertemplate=f'<b>{_name}</b><br>%{{x|%b %Y}}<br>Developers: %{{y:,.0f}}<extra></extra>'
            ))

    apply_ec_style(
        _fig,
        title=f"Bitcoin and Ethereum account for {_btc_eth_share:.0f}% of all crypto developers",
        subtitle="Monthly active developers by ecosystem",
        y_title="% of Developers" if chart6_view.value == "Percentage (Stacked)" else "Developers",
        show_legend=True,
        right_margin=60
    )

    # Move legend to right side, vertical
    _fig.update_layout(
        height=500,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#CCCCCC",
            borderwidth=1
        )
    )

    mo.ui.plotly(_fig, config={"displayModeBar": False})
    return


@app.cell(hide_code=True)
def section_ecosystem_deep_dive(mo):
    mo.md("""
    ## Deep Dive: Ecosystem Analysis
    *Explore developer trends for specific ecosystems*
    """)
    return


@app.cell(hide_code=True)
def ecosystem_selector(SUPPORTED_ECOSYSTEMS, mo):
    ecosystem_dropdown = mo.ui.dropdown(
        options=SUPPORTED_ECOSYSTEMS,
        value="Ethereum",
        label="Select Ecosystem"
    )

    ecosystem_time_range = mo.ui.dropdown(
        options=["All Time", "Last 5 Years", "Last 3 Years", "Last Year"],
        value="All Time",
        label="Time Range"
    )

    mo.hstack([ecosystem_dropdown, ecosystem_time_range], gap=2)
    return ecosystem_dropdown, ecosystem_time_range


@app.cell(hide_code=True)
def ecosystem_header(df_all, ecosystem_dropdown, mo, pd):
    """Display ecosystem header with key stats."""

    _eco_name = ecosystem_dropdown.value
    _df_eco = df_all[df_all['ecosystem_name'] == _eco_name].copy()

    if len(_df_eco) == 0:
        _output = mo.md(f"## {_eco_name}\n\n*No data available*")
    else:
        _current_row = _df_eco[_df_eco['day'] == _df_eco['day'].max()].iloc[0]
        _current_devs = _current_row['total_devs']
        _current_date = _current_row['day']

        _year_ago = _current_date - pd.DateOffset(years=1)
        _year_ago_df = _df_eco[_df_eco['day'] <= _year_ago]
        if len(_year_ago_df) > 0:
            _year_ago_devs = _year_ago_df.iloc[-1]['total_devs']
            _yoy_pct = ((_current_devs - _year_ago_devs) / _year_ago_devs) * 100
            _yoy_str = f"{_yoy_pct:+.1f}%"
            _yoy_color = "green" if _yoy_pct > 0 else "red"
        else:
            _yoy_str = "N/A"
            _yoy_color = "gray"

        _output = mo.md(f"""
    ## {_eco_name}

    **{_current_devs:,.0f}** monthly active developers ({_current_date.strftime('%B %Y')}) · <span style="color: {_yoy_color}">{_yoy_str} YoY</span>
    """)

    _output
    return


@app.cell(hide_code=True)
def chart_ecosystem_total_devs(
    EC_LIGHT_BLUE,
    add_callout_annotation,
    apply_ec_style,
    df_all,
    ecosystem_dropdown,
    ecosystem_time_range,
    go,
    mo,
    pd,
):
    """Deep Dive Chart 1: Ecosystem Total Active Developers"""

    _eco_name = ecosystem_dropdown.value
    _df = df_all[df_all['ecosystem_name'] == _eco_name].copy()

    if len(_df) == 0:
        _output = mo.md("*No data available for this ecosystem*")
    else:
        if ecosystem_time_range.value == "Last 5 Years":
            _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]
        elif ecosystem_time_range.value == "Last 3 Years":
            _df = _df[_df['day'] >= pd.Timestamp('2022-01-01')]
        elif ecosystem_time_range.value == "Last Year":
            _df = _df[_df['day'] >= pd.Timestamp('2024-01-01')]

        _current_row = _df.iloc[-1]
        _current_devs = _current_row['total_devs']
        _current_date = _current_row['day']

        _fig = go.Figure()

        _fig.add_trace(go.Scatter(
            x=_df['day'],
            y=_df['total_devs'],
            mode='lines',
            line=dict(color=EC_LIGHT_BLUE, width=2),
            fill='tozeroy',
            fillcolor=EC_LIGHT_BLUE,
            hovertemplate='<b>%{x|%b %Y}</b><br>Developers: %{y:,.0f}<extra></extra>'
        ))

        apply_ec_style(
            _fig,
            title=f"{_current_devs:,.0f} monthly active developers supported {_eco_name}",
            subtitle=f"{_eco_name} monthly active developers",
            y_title="Developers",
            show_legend=False,
            right_margin=180
        )

        add_callout_annotation(
            _fig,
            y_value=_current_devs,
            label=_current_date.strftime('%B %Y'),
            value=f"{_current_devs:,.0f}",
            description="monthly active<br>developers"
        )

        _fig.update_layout(height=450)

        _output = mo.ui.plotly(_fig, config={"displayModeBar": False})

    _output
    return


@app.cell(hide_code=True)
def chart_ecosystem_tenure(
    TENURE_COLORS,
    add_tenure_legend,
    apply_ec_style,
    df_all,
    ecosystem_dropdown,
    ecosystem_time_range,
    go,
    mo,
    pd,
):
    """Deep Dive Chart 2: Ecosystem Developer Composition by Tenure"""

    _eco_name = ecosystem_dropdown.value
    _df = df_all[df_all['ecosystem_name'] == _eco_name].copy()

    if len(_df) == 0:
        _output = mo.md("*No data available*")
    else:
        if ecosystem_time_range.value == "Last 5 Years":
            _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]
        elif ecosystem_time_range.value == "Last 3 Years":
            _df = _df[_df['day'] >= pd.Timestamp('2022-01-01')]
        elif ecosystem_time_range.value == "Last Year":
            _df = _df[_df['day'] >= pd.Timestamp('2024-01-01')]

        _fig = go.Figure()

        for _segment, _col in [("Established", "established"), ("Emerging", "emerging"), ("Newcomers", "newcomers")]:
            _fig.add_trace(go.Scatter(
                x=_df['day'],
                y=_df[_col],
                name=_segment,
                mode='lines',
                stackgroup='one',
                fillcolor=TENURE_COLORS[_segment],
                line=dict(width=0.5, color=TENURE_COLORS[_segment]),
                hovertemplate=f'<b>{_segment}</b><br>%{{x|%b %Y}}<br>Developers: %{{y:,.0f}}<extra></extra>'
            ))

        _current = _df.iloc[-1]

        apply_ec_style(
            _fig,
            title=f"{_eco_name} Developer Composition by Tenure",
            subtitle="Segmented by Newcomers, Emerging, and Established developers",
            y_title="Developers",
            show_legend=False,
            right_margin=180
        )

        add_tenure_legend(_fig, _current['newcomers'], _current['emerging'], _current['established'], TENURE_COLORS)

        _fig.update_layout(height=450)

        _output = mo.ui.plotly(_fig, config={"displayModeBar": False})

    _output
    return


@app.cell(hide_code=True)
def chart_ecosystem_activity(
    ACTIVITY_COLORS,
    apply_ec_style,
    df_all,
    ecosystem_dropdown,
    ecosystem_time_range,
    go,
    mo,
    pd,
):
    """Deep Dive Chart 3: Ecosystem Activity Levels"""

    _eco_name = ecosystem_dropdown.value
    _df = df_all[df_all['ecosystem_name'] == _eco_name].copy()

    if len(_df) == 0:
        _output = mo.md("*No data available*")
    else:
        if ecosystem_time_range.value == "Last 5 Years":
            _df = _df[_df['day'] >= pd.Timestamp('2020-01-01')]
        elif ecosystem_time_range.value == "Last 3 Years":
            _df = _df[_df['day'] >= pd.Timestamp('2022-01-01')]
        elif ecosystem_time_range.value == "Last Year":
            _df = _df[_df['day'] >= pd.Timestamp('2024-01-01')]

        _fig = go.Figure()

        for _level, _col in [("Full-time", "full_time"), ("Part-time", "part_time"), ("One-time", "one_time")]:
            _fig.add_trace(go.Scatter(
                x=_df['day'],
                y=_df[_col],
                name=_level,
                mode='lines',
                line=dict(width=2, color=ACTIVITY_COLORS[_level]),
                hovertemplate=f'<b>{_level}</b><br>%{{x|%b %Y}}<br>Developers: %{{y:,.0f}}<extra></extra>'
            ))

        apply_ec_style(
            _fig,
            title=f"{_eco_name} Developers by Activity Level",
            subtitle="Segmented by sustained activity patterns (84-day rolling window)",
            y_title="Developers",
            show_legend=True,
            right_margin=60
        )

        _fig.update_layout(height=450)

        _output = mo.ui.plotly(_fig, config={"displayModeBar": False})

    _output
    return


@app.cell(hide_code=True)
def chart_ecosystem_newcomers_by_year(
    apply_ec_style,
    df_all,
    ecosystem_dropdown,
    go,
    mo,
):
    """Deep Dive Chart 4: Ecosystem New Developer Acquisition by Year"""

    _eco_name = ecosystem_dropdown.value
    _df = df_all[df_all['ecosystem_name'] == _eco_name].copy()

    # EC-style light purple/blue for bars
    _bar_color = "#B8C9E8"

    if len(_df) == 0:
        _output = mo.md("*No data available*")
    else:
        # Aggregate by year - take max newcomers per year (rolling window peak)
        _df_agg = _df.groupby('year').agg({'newcomers': 'max'}).reset_index()
        _df_agg = _df_agg[_df_agg['year'] >= 2015]  # Filter to reasonable range

        # Find recent years with high newcomer counts for title
        _recent_years = _df_agg[_df_agg['year'] >= _df_agg['year'].max() - 2]
        _recent_values = _recent_years['newcomers'].tolist()
        _recent_year_labels = _recent_years['year'].astype(int).tolist()

        # Find a threshold (round down to nearest 5000 or 1000)
        _min_recent = min(_recent_values) if _recent_values else 0
        if _min_recent >= 10000:
            _threshold = (_min_recent // 5000) * 5000
        elif _min_recent >= 1000:
            _threshold = (_min_recent // 1000) * 1000
        else:
            _threshold = 0

        # Build title based on threshold
        if _threshold > 0 and len(_recent_year_labels) >= 2:
            _years_str = ", ".join([f"'{str(y)[-2:]}" for y in _recent_year_labels])
            _title = f"{_threshold:,.0f}+ new devs supported {_eco_name} in {_years_str}"
        else:
            _title = f"{_eco_name} new developers"

        _fig = go.Figure()

        _fig.add_trace(go.Bar(
            x=_df_agg['year'].astype(int).astype(str),
            y=_df_agg['newcomers'],
            marker_color=_bar_color,
            text=_df_agg['newcomers'].apply(lambda x: f'{x:,.0f}'),
            textposition='outside',
            textfont=dict(size=10, color="#666"),
            hovertemplate='<b>%{x}</b><br>New Developers: %{y:,.0f}<extra></extra>'
        ))

        # Add threshold reference line if applicable
        if _threshold > 0:
            _fig.add_hline(
                y=_threshold,
                line_dash="dash",
                line_color="#999",
                line_width=1,
                annotation_text=f"{_threshold:,.0f}+ new developers supported {_eco_name} for the last {len(_recent_year_labels)} years",
                annotation_position="top left",
                annotation_font=dict(size=10, color="#666")
            )

        apply_ec_style(
            _fig,
            title=_title,
            subtitle=f"{_eco_name} new developers",
            y_title="Developers",
            show_legend=False,
            right_margin=60
        )

        # Adjust y-axis for text labels
        _max_val = _df_agg['newcomers'].max()
        _fig.update_yaxes(range=[0, _max_val * 1.18])

        _fig.update_layout(height=450)

        _output = mo.ui.plotly(_fig, config={"displayModeBar": False})

    _output
    return


@app.cell(hide_code=True)
def section_comparative(mo):
    mo.md("""
    ## Comparative Analysis
    *Compare metrics across ecosystems over time*
    """)
    return


@app.cell(hide_code=True)
def comparison_controls(SUPPORTED_ECOSYSTEMS, mo):
    compare_ecosystems = mo.ui.multiselect(
        options=SUPPORTED_ECOSYSTEMS,
        value=["Ethereum", "Bitcoin"],
        label="Select Ecosystems"
    )

    compare_metric = mo.ui.dropdown(
        options=[
            "Total Developers",
            "Newcomers",
            "Emerging",
            "Established",
            "Full-time",
            "Part-time",
            "One-time"
        ],
        value="Total Developers",
        label="Metric"
    )

    compare_time_range = mo.ui.dropdown(
        options=["All Time", "Last 5 Years", "Last 3 Years", "Last Year"],
        value="All Time",
        label="Time Range"
    )

    mo.hstack([compare_ecosystems, compare_metric, compare_time_range], gap=2)
    return compare_ecosystems, compare_metric, compare_time_range


@app.cell(hide_code=True)
def comparison_chart(
    apply_ec_style,
    compare_ecosystems,
    compare_metric,
    compare_time_range,
    df_all,
    go,
    mo,
    pd,
):
    """Comparative analysis - line chart comparing ecosystems over time."""

    _selected = compare_ecosystems.value

    if len(_selected) < 1:
        _output = mo.md("*Select at least one ecosystem to compare*")
    else:
        # Map metric names to column names
        _metric_map = {
            "Total Developers": "total_devs",
            "Newcomers": "newcomers",
            "Emerging": "emerging",
            "Established": "established",
            "Full-time": "full_time",
            "Part-time": "part_time",
            "One-time": "one_time"
        }
        _col = _metric_map[compare_metric.value]

        # Color palette for multiple ecosystems
        _colors = ["#5DADE2", "#F5B041", "#58D68D", "#AF7AC5", "#EC7063"]

        _fig = go.Figure()

        for _i, _eco in enumerate(_selected):
            _df_eco = df_all[df_all['ecosystem_name'] == _eco].copy()

            # Apply time filter
            if compare_time_range.value == "Last 5 Years":
                _df_eco = _df_eco[_df_eco['day'] >= pd.Timestamp('2020-01-01')]
            elif compare_time_range.value == "Last 3 Years":
                _df_eco = _df_eco[_df_eco['day'] >= pd.Timestamp('2022-01-01')]
            elif compare_time_range.value == "Last Year":
                _df_eco = _df_eco[_df_eco['day'] >= pd.Timestamp('2024-01-01')]

            if len(_df_eco) > 0:
                _color = _colors[_i % len(_colors)]
                _current_val = _df_eco.iloc[-1][_col]

                _fig.add_trace(go.Scatter(
                    x=_df_eco['day'],
                    y=_df_eco[_col],
                    name=f"{_eco} ({_current_val:,.0f})",
                    mode='lines',
                    line=dict(width=2, color=_color),
                    hovertemplate=f'<b>{_eco}</b><br>%{{x|%b %Y}}<br>{compare_metric.value}: %{{y:,.0f}}<extra></extra>'
                ))

        # Build title
        if len(_selected) == 1:
            _title = f"{_selected[0]}: {compare_metric.value} Over Time"
        elif len(_selected) == 2:
            _title = f"{_selected[0]} vs {_selected[1]}: {compare_metric.value}"
        else:
            _title = f"Ecosystem Comparison: {compare_metric.value}"

        apply_ec_style(
            _fig,
            title=_title,
            subtitle=f"{compare_metric.value} over time",
            y_title="Developers",
            show_legend=True,
            right_margin=60
        )

        # Move legend to top-left for line charts
        _fig.update_layout(
            height=450,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#CCCCCC",
                borderwidth=1
            )
        )

        _output = mo.ui.plotly(_fig, config={"displayModeBar": False})

    _output
    return


@app.cell(hide_code=True)
def footer(mo):
    mo.md("""
    ---

    ## Methodology

    - **Developers**: We count original code authors as developers. A developer who merges a pull request is not an active developer on the project unless they authored commits.
    - **Monthly Active Developers**: Measured using a 28-day rolling window to provide more stable metrics over time.
    - **Tenure Categories**:
      - Newcomers: < 1 year active in crypto
      - Emerging: 1-2 years active
      - Established: 2+ years active
    - **Activity Levels**:
      - Full-Time Contributors: consistently active across multiple weeks based on sustained activity patterns over an 84-day rolling window
      - Part-Time Contributors: intermittently active with regular contributions over an 84-day rolling window
      - One-Time Contributors: minimal or sporadic activity over an 84-day rolling window
      - *Note*: In the report methodology, “full-time” behavior is commonly operationalized as contributing code on 10+ days in a rolling 28-day period (and analyzed for persistence over longer windows).
          
    > This analysis is inspired by and seeks to reproduce highlights from the [Electric Capital Developer Report](https://www.developerreport.com).
    Data sourced from Open Dev Data via the OSO data warehouse.
    """)
    return


if __name__ == "__main__":
    app.run()
