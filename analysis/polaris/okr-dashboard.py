import marimo

__generated_with = "0.19.2"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Polaris OKR Dashboard
    <small>Owner: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">OSO</span> · Last Updated: <span style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px;">2026-01-21</span></small>

    This dashboard provides visibility into the status of OKRs across all Polaris network components.
    """)
    return


@app.cell(hide_code=True)
def _(STATUS_COLORS, df_okrs, go, mo):
    # Generate sections for each component
    _sections = []
    _components = df_okrs['component'].unique()

    for _component in sorted(_components):
        _df_comp = df_okrs[df_okrs['component'] == _component].copy()

        # Calculate current level (max level where ALL key results are green)
        # Levels are strings like "L1", "L2", "L3" - sort them properly
        _levels = sorted(_df_comp['level'].unique())
        _current_level = None
        _current_objective = "No levels fully achieved"

        for _level in _levels:
            _df_level = _df_comp[_df_comp['level'] == _level]
            if (_df_level['status_color'] == 'Green').all():
                _current_level = _level
                _current_objective = _df_level['objective'].iloc[0]
            else:
                break

        # Count statuses
        _green_count = (_df_comp['status_color'] == 'Green').sum()
        _yellow_count = (_df_comp['status_color'] == 'Yellow').sum()
        _red_count = (_df_comp['status_color'] == 'Red').sum()
        _gray_count = (_df_comp['status_color'] == 'Gray').sum()

        # Create stat cards
        _stats = mo.hstack([
            mo.stat(
                label="Current Level",
                value=_current_level if _current_level else "—",
                caption=_current_objective if _current_level else "No levels complete",
                bordered=True
            ),
            mo.stat(
                label="Fully Met",
                value=str(_green_count),
                caption="Clear evidence",
                bordered=True
            ),
            mo.stat(
                label="Partial Progress",
                value=str(_yellow_count),
                caption="Or unclear data",
                bordered=True
            ),
            mo.stat(
                label="Not Met",
                value=str(_red_count),
                caption="No progress",
                bordered=True
            )
        ], widths="equal", gap=1)

        # Create single horizontal bar where each segment is a key result
        # Sorted by level, then by status (Green first, then Yellow, then Red)
        # Each level gets equal width regardless of KR count
        _df_bar = _df_comp[['level', 'status_color', 'key_result']].copy()
        _status_order = {'Green': 0, 'Yellow': 1, 'Red': 2, 'Gray': 3}
        _df_bar['_status_order'] = _df_bar['status_color'].map(_status_order)
        _df_bar = _df_bar.sort_values(['level', '_status_order']).reset_index(drop=True)

        _fig = go.Figure()

        # Get all levels and assign equal-width segments
        _all_levels = sorted(_df_bar['level'].unique())
        _num_levels = len(_all_levels)
        _level_width = 1.0  # Each level gets width of 1

        # Track level positions (fixed, equal-width segments)
        _level_positions = {}
        for _i, _level in enumerate(_all_levels):
            _level_positions[_level] = (_i * _level_width, (_i + 1) * _level_width)

        # Add KRs for each level, distributed within the level's segment
        for _level in _all_levels:
            _level_krs = _df_bar[_df_bar['level'] == _level].reset_index(drop=True)
            _num_krs = len(_level_krs)
            _start, _end = _level_positions[_level]
            _kr_width = _level_width / _num_krs if _num_krs > 0 else _level_width

            for _kr_idx, _row in _level_krs.iterrows():
                _status = _row['status_color']
                _kr_start = _start + (_kr_idx * _kr_width)

                _fig.add_trace(go.Bar(
                    x=[_kr_width],
                    y=[''],
                    orientation='h',
                    marker_color=STATUS_COLORS.get(_status, '#999'),
                    showlegend=False,
                    hovertemplate=f"{_level}: {_row['key_result']}<extra></extra>",
                    base=_kr_start
                ))

        # Add vertical separator lines between levels
        # Current level gets a thicker line
        for _level, (_start, _end) in _level_positions.items():
            _is_current = (_level == _current_level)
            _fig.add_shape(
                type='line',
                x0=_end, x1=_end,
                y0=0, y1=1,
                yref='paper',
                line=dict(
                    color='black',
                    width=4 if _is_current else 1
                )
            )

        # Use annotations for level labels (more control over styling)
        # Current level is bold black, others are gray
        # Position below the bar chart
        _annotations = []
        for _level in _all_levels:
            _start, _end = _level_positions[_level]
            _is_current = (_level == _current_level)
            _annotations.append(dict(
                x=_end,
                y=-0.6,
                yref='paper',
                text=f"<b>{_level}</b>" if _is_current else _level,
                showarrow=False,
                font=dict(
                    size=14 if _is_current else 11,
                    color='black' if _is_current else '#999'
                ),
                xanchor='center'
            ))

        _total_width = _num_levels * _level_width
        _fig.update_layout(
            barmode='stack',
            height=110,
            margin=dict(t=10, l=20, r=20, b=60),
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=False,
            annotations=_annotations,
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                range=[0, _total_width],
                showticklabels=False
            ),
            yaxis=dict(
                showgrid=False,
                showticklabels=False,
                zeroline=False
            )
        )

        _chart = mo.ui.plotly(_fig, config={'displayModeBar': False})

        # Create table with colored status using style_cell
        _df_table = _df_comp[['level', 'objective', 'key_result', 'status_label', 'status_color']].copy()
        _df_table = _df_table.sort_values(['level', 'objective', 'key_result'])
        _df_display = _df_table[['level', 'objective', 'key_result', 'status_label']].copy()
        _df_display.columns = ['Level', 'Objective', 'Key Result', 'Status']

        # Create a mapping of row index to status color for styling
        _status_color_map = _df_table['status_color'].reset_index(drop=True).to_dict()

        def _style_cell(value, row_idx, col_name):
            if col_name == 'Status':
                _color = STATUS_COLORS.get(_status_color_map.get(row_idx, ''), '#999')
                return {'background-color': _color, 'color': 'white', 'border-radius': '4px', 'padding': '4px 8px'}
            return {}

        _table = mo.ui.table(
            _df_display.reset_index(drop=True),
            show_column_summaries=False,
            show_data_types=False,
            page_size=20,
            style_cell=_style_cell
        )

        # Build section: header, chart, accordion with stats and table
        _details = mo.vstack([
            _stats,
            mo.md("### Key Results Detail"),
            _table
        ], gap=1)

        _accordion = mo.accordion({"Click for details": _details})

        # Build subtitle showing current level and objective
        if _current_level:
            _subtitle = f"**Current Level: {_current_level}** · {_current_objective}"
        else:
            _subtitle = "*No levels fully achieved yet*"

        _section = mo.vstack([
            mo.md(f"## {_component}"),
            mo.md(f"<small style='color: #666;'>{_subtitle}</small>"),
            _chart,
            _accordion
        ], gap=1)

        _sections.append(_section)

    mo.vstack(_sections, gap=2)
    return


@app.cell(hide_code=True)
def _(mo, pyoso_db_conn):
    df_okrs = mo.sql(
        f"""
        SELECT
          component,
          level,
          objective,
          key_result,
          related_kpi,
          ryg AS status_label,
          CASE
            WHEN ryg = 'Fully met with clear evidence' THEN 'Green'
            WHEN ryg = 'Partial progress or unclear data' THEN 'Yellow'
            WHEN ryg = 'Not met or no progress' THEN 'Red'
            ELSE 'Gray'
          END AS status_color
        FROM polaris.network_levels_models.consolidated
        ORDER BY component, level, objective, key_result
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_okrs,)


@app.cell(hide_code=True)
def _():
    # Status colors for RYG indicators
    STATUS_COLORS = {
        'Green': '#22c55e',   # Tailwind green-500
        'Yellow': '#eab308',  # Tailwind yellow-500
        'Red': '#ef4444',     # Tailwind red-500
        'Gray': '#9ca3af'     # Tailwind gray-400
    }
    return (STATUS_COLORS,)


@app.cell(hide_code=True)
def _():
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    return (go,)


@app.cell(hide_code=True)
def setup_pyoso():
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
