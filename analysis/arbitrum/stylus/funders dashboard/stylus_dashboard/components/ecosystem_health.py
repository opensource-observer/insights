import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ..config import DATA_PATHS, TIME_WINDOWS
from ..utils.data_processing import load_data, filter_data_by_time_window, calculate_pct_change, calculate_project_metrics
from ..utils.visualization import create_developer_trend_plot

def render_ecosystem_health():
    """Render the developer ecosystem health tab content."""
    st.header("Developer Ecosystem Health")
    st.markdown("""
    This dashboard tracks active developer engagement across three key segments of the Arbitrum ecosystem:

    1. **Arbitrum Ecosystem**: Total active developers across Arbitrum projects (see note below), representing the overall health and growth of the ecosystem.
    
    2. **Stylus Grantees**: Developers actively contributing to projects in the [Arbitrum Stylus Sprint](https://arbitrum.questbook.app/dashboard/?grantId=671a105a2047c84bb8a73770&chainId=10).
    
    3. **Stylus SDK Users**: Developers building on the Stylus SDK, including both grant recipients and independent projects, showing the broader adoption of the technology.
    """)
    st.caption("Note: The Arbitrum Ecosystem data is sourced from OSS-Directory, a curated directory of open source projects on OSO. To add new projects to the directory, follow the instructions [here](https://docs.opensource.observer/docs/projects/).")
    
    # Add time window selector
    time_window = st.radio(
        "Select Time Window",
        options=list(TIME_WINDOWS.keys()),
        horizontal=True,
        index=4  # Default to 36 months
    )
    
    # Load data from all three sources
    arb_df = load_data(DATA_PATHS["arb_projects"])
    stylus_df = load_data(DATA_PATHS["stylus_metrics"])
    deps_df = load_data(DATA_PATHS["dependencies"])
    
    # Filter data for active developers metric and selected time window
    arb_df = filter_data_by_time_window(
        arb_df[arb_df['metric_name'] == 'GITHUB_active_developers_monthly'],
        time_window
    )
    stylus_df = filter_data_by_time_window(
        stylus_df[stylus_df['metric_name'] == 'GITHUB_active_developers_monthly'],
        time_window
    )
    deps_df = filter_data_by_time_window(
        deps_df[deps_df['metric_name'] == 'GITHUB_active_developers_monthly'],
        time_window
    )
    
    # Aggregate data by date for each context
    arb_agg = arb_df.groupby('sample_date')['amount'].sum().reset_index()
    stylus_agg = stylus_df.groupby('sample_date')['amount'].sum().reset_index()
    deps_agg = deps_df.groupby('sample_date')['amount'].sum().reset_index()
    
    # Calculate percentage changes
    arb_agg = calculate_pct_change(arb_agg)
    stylus_agg = calculate_pct_change(stylus_agg)
    deps_agg = calculate_pct_change(deps_agg)

    # Add summary statistics
    st.subheader(f"Average Monthly Active Developers ({time_window})")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not arb_agg.empty:
            st.metric(
                "Arbitrum Ecosystem",
                f"{arb_agg['amount'].mean():.0f}",
                f"{arb_agg['pct_change'].mean():.1f}%"
            )
        else:
            st.metric("Arbitrum Ecosystem", "No data available")
    
    with col2:
        if not stylus_agg.empty:
            st.metric(
                "Stylus Grantees",
                f"{stylus_agg['amount'].mean():.0f}",
                f"{stylus_agg['pct_change'].mean():.1f}%"
            )
        else:
            st.metric("Stylus Grantees", "No data available")
    
    with col3:
        if not deps_agg.empty:
            st.metric(
                "Stylus SDK Dependents",
                f"{deps_agg['amount'].mean():.0f}",
                f"{deps_agg['pct_change'].mean():.1f}%"
            )
        else:
            st.metric("Stylus SDK Dependents", "No data available")
    
    st.subheader(f"Monthly Active Developers Trend ({time_window})")

    # Create the figure
    fig = go.Figure()
    
    # Add traces for each context
    fig.add_trace(go.Scatter(
        x=arb_agg['sample_date'],
        y=arb_agg['amount'],
        name='Arbitrum Ecosystem',
        line=dict(color='blue', width=2),
        hovertemplate='Date: %{x}<br>Developers: %{y}<br>MoM Change: %{customdata:.1f}%<extra></extra>',
        customdata=arb_agg['pct_change']
    ))
    
    fig.add_trace(go.Scatter(
        x=stylus_agg['sample_date'],
        y=stylus_agg['amount'],
        name='Stylus Grantees',
        line=dict(color='green', width=2),
        hovertemplate='Date: %{x}<br>Developers: %{y}<br>MoM Change: %{customdata:.1f}%<extra></extra>',
        customdata=stylus_agg['pct_change']
    ))
    
    fig.add_trace(go.Scatter(
        x=deps_agg['sample_date'],
        y=deps_agg['amount'],
        name='Stylus SDK Dependents',
        line=dict(color='orange', width=2),
        hovertemplate='Date: %{x}<br>Developers: %{y}<br>MoM Change: %{customdata:.1f}%<extra></extra>',
        customdata=deps_agg['pct_change']
    ))
    
    # Update layout
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Number of Active Developers',
        height=600,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=100)
    )
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True)

    # Add top projects tables
    st.subheader(f"Top Projects by Active Developers ({time_window})")
    st.caption("Click on the column headers to sort the projects by that metric.")
    
    def style_growth(val):
        if isinstance(val, str):
            try:
                num_val = float(val.rstrip('%'))
                color = 'red' if num_val < 0 else 'green'
                return f'color: {color}'
            except:
                return ''
        elif isinstance(val, (int, float)):
            color = 'red' if val < 0 else 'green'
            return f'color: {color}'
        return ''
    
    arb_projects = calculate_project_metrics(arb_df)
    stylus_projects = calculate_project_metrics(stylus_df)
    deps_projects = calculate_project_metrics(deps_df)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Arbitrum Ecosystem**")
        if arb_projects is not None:
            display_df = arb_projects.copy()
            display_df['Monthly Growth %'] = display_df['Monthly Growth %'].map('{:.1f}%'.format)
            styled_df = display_df.style.applymap(style_growth, subset=['Monthly Growth %'])
            st.dataframe(styled_df, hide_index=True)
        else:
            st.write("No data available")
    
    with col2:
        st.markdown("**Stylus Grantees**")
        if stylus_projects is not None:
            display_df = stylus_projects.copy()
            display_df['Monthly Growth %'] = display_df['Monthly Growth %'].map('{:.1f}%'.format)
            styled_df = display_df.style.applymap(style_growth, subset=['Monthly Growth %'])
            st.dataframe(styled_df, hide_index=True)
        else:
            st.write("No data available")
    
    with col3:
        st.markdown("**Stylus SDK Dependents**")
        if deps_projects is not None:
            display_df = deps_projects.copy()
            display_df['Monthly Growth %'] = display_df['Monthly Growth %'].map('{:.1f}%'.format)
            styled_df = display_df.style.applymap(style_growth, subset=['Monthly Growth %'])
            st.dataframe(styled_df, hide_index=True)
        else:
            st.write("No data available") 