import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # PLN Contributor State Transitions (Libin Diagram)
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">Protocol Labs</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-12</span></small>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    _context = """
    - This notebook visualizes contributor state transitions across the PLN ecosystem
    - Contributors flow between 4 simplified states: First Time, Part Time, Full Time, and Churned
    - Multiple visualization formats are provided below to explore the data
    """

    _methodology = """
    **Simplified State Model:**

    | State | Includes These Lifecycle Metrics |
    |-------|----------------------------------|
    | First Time | first_time_contributor |
    | Part Time | new_part_time, active_part_time, reactivated_part_time, full_time_to_part_time |
    | Full Time | new_full_time, active_full_time, reactivated_full_time, part_time_to_full_time |
    | Churned | churned_contributors, churned_after_first_time, churned_after_part_time, churned_after_full_time |

    **Transition Metrics:**
    - `part_time_to_full_time_contributor` = Part Time → Full Time
    - `full_time_to_part_time_contributor` = Full Time → Part Time
    - `churned_after_*` = Various → Churned
    - `reactivated_*` = Churned → Active
    """

    _data_sources = """
    - [OSO Database](https://docs.oso.xyz/) - Developer lifecycle metrics
    - [OSS Directory](https://github.com/opensource-observer/oss-directory) - Project registry
    - [GitHub Archive](https://www.gharchive.org/) - Historical GitHub events
    """

    mo.accordion({
        "Context": _context,
        "Methodology": _methodology,
        "Data Sources": _data_sources
    })
    return


@app.cell(hide_code=True)
def _(df_kpis, kpi_reference_month, mo):
    if not df_kpis.empty:
        _first_time = df_kpis['first_time'].iloc[0] if 'first_time' in df_kpis.columns else 0
        _part_time = df_kpis['part_time'].iloc[0] if 'part_time' in df_kpis.columns else 0
        _full_time = df_kpis['full_time'].iloc[0] if 'full_time' in df_kpis.columns else 0
        _churned = df_kpis['churned'].iloc[0] if 'churned' in df_kpis.columns else 0
    else:
        _first_time = 0
        _part_time = 0
        _full_time = 0
        _churned = 0

    mo.hstack(
        [
            mo.stat(
                label="First Time",
                value=f"{_first_time:,.0f}",
                caption=f"New contributors ({kpi_reference_month})",
                bordered=True
            ),
            mo.stat(
                label="Part Time",
                value=f"{_part_time:,.0f}",
                caption=f"1-9 days/month ({kpi_reference_month})",
                bordered=True
            ),
            mo.stat(
                label="Full Time",
                value=f"{_full_time:,.0f}",
                caption=f"10+ days/month ({kpi_reference_month})",
                bordered=True
            ),
            mo.stat(
                label="Churned",
                value=f"{_churned:,.0f}",
                caption=f"Inactive ({kpi_reference_month})",
                bordered=True
            ),
        ],
        widths="equal",
        gap=2
    )
    return


@app.cell(hide_code=True)
def _(mo, pd):
    # Collection selector
    collection_selector = mo.ui.dropdown(
        options={
            'Protocol Labs Network': 'protocol-labs-network',
            'Filecoin Core': 'filecoin-core',
            'Filecoin Builders': 'filecoin-builders',
        },
        value='Protocol Labs Network',
        label='Collection:'
    )

    # Default dates: full year 2024
    _default_start = pd.Timestamp('2024-01-01')
    _default_end = pd.Timestamp('2024-12-31')

    start_date_picker = mo.ui.date(
        value=_default_start.date(),
        label='Start Date:'
    )

    end_date_picker = mo.ui.date(
        value=_default_end.date(),
        label='End Date:'
    )

    mo.hstack(
        [collection_selector, start_date_picker, end_date_picker],
        justify="start",
        gap=2,
        align="end"
    )
    return collection_selector, end_date_picker, start_date_picker


@app.cell(hide_code=True)
def _(collection_selector, end_date_picker, mo, start_date_picker):
    mo.md(f"""
    Showing contributor state transitions for **{collection_selector.value}** from **{start_date_picker.value}** to **{end_date_picker.value}**.
    """)
    return


# =============================================================================
# SECTION 1: CONTRIBUTOR ACTIVITY OVER TIME
# =============================================================================
@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 1. Contributor Activity Over Time

    Monthly breakdown of contributors by state. Positive bars show active contributors; negative bars show churned contributors.
    """)
    return


@app.cell(hide_code=True)
def _(PLOTLY_LAYOUT, STATE_COLORS, df_states, go, mo, pd):
    if not df_states.empty:
        _df = df_states.copy()
        _df['sample_date'] = pd.to_datetime(_df['sample_date'])
        _pivot = _df.pivot(index='sample_date', columns='state', values='count').fillna(0).reset_index()

        _fig = go.Figure()

        for state in ['First Time', 'Part Time', 'Full Time']:
            if state in _pivot.columns:
                _fig.add_trace(go.Bar(
                    name=state,
                    x=_pivot['sample_date'],
                    y=_pivot[state],
                    marker_color=STATE_COLORS[state]
                ))

        if 'Churned' in _pivot.columns:
            _fig.add_trace(go.Bar(
                name='Churned',
                x=_pivot['sample_date'],
                y=-_pivot['Churned'],
                marker_color=STATE_COLORS['Churned']
            ))

        _fig.update_layout(**PLOTLY_LAYOUT)
        _fig.update_layout(
            xaxis_title='Month',
            yaxis_title='Contributors',
            height=450
        )
        _fig.update_traces(
            hovertemplate='%{fullData.name}: %{y:,.0f}<extra></extra>',
            hoverlabel=dict(namelength=-1)
        )
        _fig.add_hline(y=0, line_width=1, line_color="black")

        transitions_chart = mo.ui.plotly(_fig, config={'displayModeBar': False})
    else:
        transitions_chart = mo.md("*No data available for the selected filters*")

    transitions_chart
    return (transitions_chart,)


# =============================================================================
# SECTION 2: TRANSITION MATRIX
# =============================================================================
@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 2. Where Do Contributors Go?

    Transition matrix showing flows between states. Rows = source state, columns = destination state. Color intensity indicates volume.
    """)
    return


@app.cell(hide_code=True)
def _(go, mo, transitions):
    def create_transition_matrix(trans):
        states = ['First Time', 'Part Time', 'Full Time', 'Churned']
        matrix = []
        for from_state in states:
            row = []
            for to_state in states:
                if from_state == to_state:
                    row.append(0)
                else:
                    count = trans.get((from_state, to_state), 0)
                    row.append(count)
            matrix.append(row)
        return states, matrix

    _states, _matrix = create_transition_matrix(transitions)

    _fig = go.Figure(data=go.Heatmap(
        z=_matrix,
        x=_states,
        y=_states,
        text=[[f"{v:,.0f}" if v > 0 else "" for v in row] for row in _matrix],
        texttemplate="%{text}",
        textfont={"size": 14, "color": "white"},
        colorscale=[
            [0.0, "#f7f7f7"],
            [0.2, "#92c5de"],
            [0.4, "#4393c3"],
            [0.6, "#2166ac"],
            [0.8, "#053061"],
            [1.0, "#053061"]
        ],
        showscale=True,
        colorbar=dict(title="Count", tickformat=",")
    ))

    _fig.update_layout(
        xaxis=dict(title="To State", side="bottom", tickangle=0),
        yaxis=dict(title="From State", autorange="reversed"),
        font=dict(size=12, color="#111"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(t=30, l=100, r=30, b=80),
        height=450
    )

    heatmap_chart = mo.ui.plotly(_fig, config={'displayModeBar': False})
    heatmap_chart
    return (heatmap_chart,)


# =============================================================================
# SECTION 3: SANKEY DIAGRAM
# =============================================================================
@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 3. Flow Visualization

    Sankey diagram showing contributor flows. Link thickness = number of contributors. Right-side nodes represent reactivations and downgrades.
    """)
    return


@app.cell(hide_code=True)
def _(STATE_COLORS, go, mo, state_counts, transitions):
    def generate_sankey(trans, counts):
        labels = [
            'Entry', 'First Time', 'Part Time', 'Full Time', 'Churned',
            'Reactivated (PT)', 'Reactivated (FT)', 'Downgraded (PT)'
        ]
        node_colors = [
            '#888888', STATE_COLORS['First Time'], STATE_COLORS['Part Time'],
            STATE_COLORS['Full Time'], STATE_COLORS['Churned'],
            STATE_COLORS['Part Time'], STATE_COLORS['Full Time'], STATE_COLORS['Part Time']
        ]

        node_x = [0.01, 0.18, 0.40, 0.40, 0.65, 0.88, 0.88, 0.88]
        node_y = [0.5, 0.5, 0.25, 0.75, 0.5, 0.15, 0.5, 0.85]

        transition_to_nodes = {
            ('Entry', 'First Time'): (0, 1),
            ('First Time', 'Part Time'): (1, 2),
            ('First Time', 'Full Time'): (1, 3),
            ('First Time', 'Churned'): (1, 4),
            ('Part Time', 'Full Time'): (2, 3),
            ('Part Time', 'Churned'): (2, 4),
            ('Full Time', 'Churned'): (3, 4),
            ('Churned', 'Part Time'): (4, 5),
            ('Churned', 'Full Time'): (4, 6),
            ('Full Time', 'Part Time'): (3, 7),
        }

        sources, targets, values, link_colors = [], [], [], []

        def hex_to_rgba(hex_color, alpha=0.4):
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return f'rgba({r},{g},{b},{alpha})'

        for (from_state, to_state), count in trans.items():
            if count > 0 and (from_state, to_state) in transition_to_nodes:
                src, tgt = transition_to_nodes[(from_state, to_state)]
                sources.append(src)
                targets.append(tgt)
                values.append(count)
                link_colors.append(hex_to_rgba(node_colors[tgt]))

        node_labels = [
            'New',
            f"First Time\n{counts.get('First Time', 0):,.0f}",
            f"Part Time\n{counts.get('Part Time', 0):,.0f}",
            f"Full Time\n{counts.get('Full Time', 0):,.0f}",
            f"Churned\n{counts.get('Churned', 0):,.0f}",
            'Reactivated\n(Part Time)',
            'Reactivated\n(Full Time)',
            'Downgraded\n(Part Time)',
        ]

        fig = go.Figure(data=[go.Sankey(
            arrangement='fixed',
            node=dict(
                pad=20, thickness=20,
                line=dict(color="white", width=1),
                label=node_labels, color=node_colors,
                x=node_x, y=node_y
            ),
            link=dict(
                source=sources, target=targets,
                value=values, color=link_colors
            )
        )])

        fig.update_layout(
            font=dict(size=10, color="#111"),
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(t=10, l=10, r=10, b=10),
            height=450
        )
        return fig

    if transitions:
        sankey_chart = mo.ui.plotly(generate_sankey(transitions, state_counts), config={'displayModeBar': False})
    else:
        sankey_chart = mo.md("*No transition data available*")

    sankey_chart
    return (sankey_chart,)


# =============================================================================
# SECTION 4: MERMAID DIAGRAM
# =============================================================================
@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 4. State Model Diagram

    Simplified flowchart showing all state transitions with counts on each edge. Arrows indicate direction of flow.
    """)
    return


@app.cell(hide_code=True)
def _(mo, transitions):
    # Generate Mermaid diagram with transition counts
    _entry = transitions.get(('Entry', 'First Time'), 0)
    _ft_to_pt = transitions.get(('First Time', 'Part Time'), 0)
    _ft_to_full = transitions.get(('First Time', 'Full Time'), 0)
    _ft_to_ch = transitions.get(('First Time', 'Churned'), 0)
    _pt_to_full = transitions.get(('Part Time', 'Full Time'), 0)
    _pt_to_ch = transitions.get(('Part Time', 'Churned'), 0)
    _full_to_pt = transitions.get(('Full Time', 'Part Time'), 0)
    _full_to_ch = transitions.get(('Full Time', 'Churned'), 0)
    _ch_to_pt = transitions.get(('Churned', 'Part Time'), 0)
    _ch_to_full = transitions.get(('Churned', 'Full Time'), 0)

    _mermaid_code = f"""
flowchart LR
    Entry["New Contributors"] --> FirstTime["First Time"]
    FirstTime -->|"{_ft_to_pt:,.0f}"| PartTime["Part Time"]
    FirstTime -->|"{_ft_to_full:,.0f}"| FullTime["Full Time"]
    FirstTime -->|"{_ft_to_ch:,.0f}"| Churned["Churned"]
    PartTime -->|"{_pt_to_full:,.0f}"| FullTime
    PartTime -->|"{_pt_to_ch:,.0f}"| Churned
    FullTime -->|"{_full_to_pt:,.0f}"| PartTime
    FullTime -->|"{_full_to_ch:,.0f}"| Churned
    Churned -->|"{_ch_to_pt:,.0f}"| PartTime
    Churned -->|"{_ch_to_full:,.0f}"| FullTime
"""

    mermaid_diagram = mo.mermaid(_mermaid_code)
    mermaid_diagram
    return (mermaid_diagram,)


# =============================================================================
# SECTION 5: SUMMARY
# =============================================================================
@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---
    ## 5. Summary
    """)
    return


@app.cell(hide_code=True)
def _(mo, transitions):
    _entry = transitions.get(('Entry', 'First Time'), 0)
    _to_churned = transitions.get(('First Time', 'Churned'), 0) + transitions.get(('Part Time', 'Churned'), 0) + transitions.get(('Full Time', 'Churned'), 0)
    _reactivated = transitions.get(('Churned', 'Part Time'), 0) + transitions.get(('Churned', 'Full Time'), 0)
    _upgraded = transitions.get(('Part Time', 'Full Time'), 0)
    _downgraded = transitions.get(('Full Time', 'Part Time'), 0)
    _net_change = _entry + _reactivated - _to_churned

    _flow_table = f"""
| Transition | Count |
|------------|------:|
| New Contributors | {_entry:,.0f} |
| Upgraded (PT → FT) | {_upgraded:,.0f} |
| Downgraded (FT → PT) | {_downgraded:,.0f} |
| Churned | {_to_churned:,.0f} |
| Reactivated | {_reactivated:,.0f} |
"""

    if _net_change >= 0:
        _callout_kind = "success"
        _callout_text = f"**Net contributor change: +{_net_change:,.0f}** ({_entry:,.0f} new + {_reactivated:,.0f} reactivated - {_to_churned:,.0f} churned)"
    else:
        _callout_kind = "warn"
        _callout_text = f"**Net contributor change: {_net_change:,.0f}** ({_entry:,.0f} new + {_reactivated:,.0f} reactivated - {_to_churned:,.0f} churned)"

    mo.vstack([
        mo.callout(mo.md(_callout_text), kind=_callout_kind),
        mo.md(_flow_table)
    ])
    return


# =============================================================================
# DATA FETCHING AND PROCESSING
# =============================================================================
@app.cell(hide_code=True)
def _():
    PLOTLY_LAYOUT = dict(
        title="",
        barmode="relative",
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=12, color="#111"),
        margin=dict(t=0, l=0, r=0, b=50),
        legend=dict(
            orientation="v",
            yanchor="top", y=0.98,
            xanchor="left", x=0.02,
            bordercolor="black", borderwidth=1,
            bgcolor="white"
        ),
        xaxis=dict(
            title="",
            showgrid=False,
            linecolor="#000", linewidth=1,
            ticks="outside"
        ),
        yaxis=dict(
            title="",
            showgrid=True, gridcolor="#DDD",
            zeroline=True, zerolinecolor="black", zerolinewidth=1,
            linecolor="#000", linewidth=1,
            ticks="outside"
        )
    )

    STATE_COLORS = {
        'First Time': '#4C78A8',
        'Part Time': '#41AB5D',
        'Full Time': '#7A4D9B',
        'Churned': '#D62728',
    }

    STATE_ORDER = ['First Time', 'Part Time', 'Full Time', 'Churned']
    return PLOTLY_LAYOUT, STATE_COLORS, STATE_ORDER


@app.cell(hide_code=True)
def _(collection_selector, end_date_picker, mo, pyoso_db_conn, start_date_picker):
    df_lifecycle = mo.sql(
        f"""
        SELECT
          ts.sample_date,
          m.metric_model,
          SUM(ts.amount) AS contributor_count
        FROM timeseries_metrics_by_project_v0 ts
        JOIN metrics_v0 m ON ts.metric_id = m.metric_id
        JOIN projects_by_collection_v1 pbc ON ts.project_id = pbc.project_id
        WHERE pbc.collection_name = '{collection_selector.value}'
          AND m.metric_model IN (
            'first_time_contributor',
            'active_full_time_contributor', 'new_full_time_contributor',
            'part_time_to_full_time_contributor', 'reactivated_full_time_contributor',
            'active_part_time_contributor', 'new_part_time_contributor',
            'full_time_to_part_time_contributor', 'reactivated_part_time_contributor',
            'churned_contributors', 'churned_after_first_time_contributor',
            'churned_after_part_time_contributor', 'churned_after_full_time_contributor'
          )
          AND m.metric_time_aggregation = 'monthly'
          AND ts.sample_date >= DATE('{start_date_picker.value}')
          AND ts.sample_date <= DATE('{end_date_picker.value}')
        GROUP BY ts.sample_date, m.metric_model
        ORDER BY ts.sample_date
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_lifecycle,)


@app.cell(hide_code=True)
def _(df_lifecycle, pd):
    def aggregate_states(df):
        if df.empty:
            return pd.DataFrame(columns=['sample_date', 'state', 'count'])

        state_mapping = {
            'first_time_contributor': 'First Time',
            'new_part_time_contributor': 'Part Time',
            'active_part_time_contributor': 'Part Time',
            'reactivated_part_time_contributor': 'Part Time',
            'full_time_to_part_time_contributor': 'Part Time',
            'new_full_time_contributor': 'Full Time',
            'active_full_time_contributor': 'Full Time',
            'reactivated_full_time_contributor': 'Full Time',
            'part_time_to_full_time_contributor': 'Full Time',
            'churned_contributors': 'Churned',
            'churned_after_first_time_contributor': 'Churned',
            'churned_after_part_time_contributor': 'Churned',
            'churned_after_full_time_contributor': 'Churned',
        }

        df_agg = df.copy()
        df_agg['state'] = df_agg['metric_model'].map(state_mapping)
        df_agg = df_agg.groupby(['sample_date', 'state'], as_index=False)['contributor_count'].sum()
        df_agg = df_agg.rename(columns={'contributor_count': 'count'})
        return df_agg

    df_states = aggregate_states(df_lifecycle)
    return (df_states,)


@app.cell(hide_code=True)
def _(df_lifecycle):
    def calculate_transitions(df):
        if df.empty:
            return {}, {}

        transition_mapping = {
            'first_time_contributor': ('Entry', 'First Time'),
            'new_part_time_contributor': ('First Time', 'Part Time'),
            'new_full_time_contributor': ('First Time', 'Full Time'),
            'part_time_to_full_time_contributor': ('Part Time', 'Full Time'),
            'churned_after_first_time_contributor': ('First Time', 'Churned'),
            'churned_after_part_time_contributor': ('Part Time', 'Churned'),
            'churned_after_full_time_contributor': ('Full Time', 'Churned'),
            'reactivated_full_time_contributor': ('Churned', 'Full Time'),
            'reactivated_part_time_contributor': ('Churned', 'Part Time'),
            'full_time_to_part_time_contributor': ('Full Time', 'Part Time'),
        }

        transitions = {}
        for metric, (from_state, to_state) in transition_mapping.items():
            count = df[df['metric_model'] == metric]['contributor_count'].sum()
            if count > 0:
                key = (from_state, to_state)
                transitions[key] = transitions.get(key, 0) + count

        state_count_mapping = {
            'first_time_contributor': 'First Time',
            'active_part_time_contributor': 'Part Time',
            'active_full_time_contributor': 'Full Time',
            'churned_contributors': 'Churned',
        }

        state_counts = {}
        for metric, state in state_count_mapping.items():
            metric_df = df[df['metric_model'] == metric]
            if not metric_df.empty:
                latest = metric_df.sort_values('sample_date').iloc[-1]['contributor_count']
                state_counts[state] = state_counts.get(state, 0) + latest

        return transitions, state_counts

    transitions, state_counts = calculate_transitions(df_lifecycle)
    return state_counts, transitions


@app.cell(hide_code=True)
def _(df_states, pd):
    if not df_states.empty:
        _df = df_states.copy()
        _df['sample_date'] = pd.to_datetime(_df['sample_date'])
        _latest_date = _df['sample_date'].max()
        _latest = _df[_df['sample_date'] == _latest_date]

        _first_time = _latest[_latest['state'] == 'First Time']['count'].sum()
        _part_time = _latest[_latest['state'] == 'Part Time']['count'].sum()
        _full_time = _latest[_latest['state'] == 'Full Time']['count'].sum()
        _churned = _latest[_latest['state'] == 'Churned']['count'].sum()

        df_kpis = pd.DataFrame({
            'first_time': [_first_time],
            'part_time': [_part_time],
            'full_time': [_full_time],
            'churned': [_churned]
        })
        kpi_reference_month = _latest_date.strftime('%b %Y')
    else:
        df_kpis = pd.DataFrame({
            'first_time': [0],
            'part_time': [0],
            'full_time': [0],
            'churned': [0]
        })
        kpi_reference_month = "N/A"
    return df_kpis, kpi_reference_month


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
