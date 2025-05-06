import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ..config import DATA_PATHS, TIME_WINDOWS, AVAILABLE_METRICS
from ..utils.data_processing import load_data, filter_data_by_time_window, calculate_pct_change
from ..utils.visualization import create_developer_trend_plot, create_activity_heatmap

def create_grantee_impact_sankey(df):
    """Create a Sankey diagram showing the impact of Stylus Sprint grantees."""
    # Filter out dependencies where source and dependent are from same org
    df = df[df['from_artifact_namespace'] != df['package_owner_artifact_namespace']]
    
    # Group by grantee and dependent project to get dependency counts
    impact_data = df.groupby(['package_owner_artifact_namespace', 'artifact_name']).size().reset_index(name='dependency_count')
    
    # Get unique grantees and dependent projects
    grantees = impact_data['package_owner_artifact_namespace'].unique()
    dependents = impact_data['artifact_name'].unique()
    
    # Create node labels (combine grantees and dependents)
    node_labels = list(grantees) + list(dependents)
    
    # Create source and target indices
    source_indices = [list(grantees).index(grantee) for grantee in impact_data['package_owner_artifact_namespace']]
    target_indices = [len(grantees) + list(dependents).index(dep) for dep in impact_data['artifact_name']]
    
    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = node_labels,
            color = ["#1f77b4"] * len(grantees) + ["#ff7f0e"] * len(dependents)  # Different colors for grantees vs dependents
        ),
        link = dict(
            source = source_indices,
            target = target_indices,
            value = impact_data['dependency_count'],
            color = ["rgba(31, 119, 180, 0.4)"] * len(source_indices)  # Semi-transparent blue for flows
        )
    )])
    
    # Update layout
    fig.update_layout(
        title_text="Stylus Sprint Grantee Impact",
        font_size=10,
        height=800
    )
    
    return fig

def render_activity_analysis():
    """Render the Stylus Sprint activity analysis tab content."""
    st.header("Stylus Sprint Activity Analysis")

    st.markdown("""
    This section provides a comprehensive analysis of developer engagement and project activity within the Stylus Sprint program. 
    You'll find:
    
    - **Developer Activity Trends**: Track the evolution of active developers over time
    - **Project Activity Heatmap**: Compare key metrics (commits, issues, PRs, etc.) across all projects
    - **Time-based Analysis**: Select different time windows to analyze patterns and growth
    - **Grantee Impact**: Visualize how Stylus Sprint grantees are being used across the ecosystem
    """)
    
    # Add time window selector
    time_window = st.radio(
        "Select a time window to analyze developer activity trends and project metrics:",
        options=list(TIME_WINDOWS.keys()),
        horizontal=True,
        index=1,  # Default to 6 months
        key="overview_time_window"
    )

    st.markdown(f"### Monthly Active Developers Trend ({time_window})")

    # Load and process data
    df = load_data(DATA_PATHS["stylus_metrics"])
    df = filter_data_by_time_window(
        df[df['metric_name'] == 'GITHUB_active_developers_monthly'],
        time_window
    )
    
    # Aggregate data across all projects
    aggregated_df = df.groupby('sample_date')['amount'].sum().reset_index()
    aggregated_df = calculate_pct_change(aggregated_df)
    
    # Create and display the trend plot
    fig = create_developer_trend_plot(aggregated_df)
    st.plotly_chart(fig, use_container_width=True)

    st.header(f"Project Activity Analysis ({time_window})")

    st.warning("""
    **Note:** Development metrics like commits, issues closed, and PRs merged can vary widely based on a project's workflow, team size, or codebase structure. These numbers aren't meant for head-to-head comparisons, but rather to track changes within the same project over time. Use them as directional signals to guide deeper, qualitative evaluation.
    """)
    
    # Metric selection with radio buttons
    selected_metric = st.radio(
        "Select Metric for Heatmap",
        options=list(AVAILABLE_METRICS.keys()),
        format_func=lambda x: AVAILABLE_METRICS[x],
        horizontal=True
    )
    
    # Filter data for selected metric and time window
    heatmap_data = load_data(DATA_PATHS["stylus_metrics"])
    heatmap_data = filter_data_by_time_window(
        heatmap_data[heatmap_data['metric_name'] == selected_metric],
        time_window
    )
    
    # Aggregate data to handle duplicates
    heatmap_data = heatmap_data.groupby(['display_name', 'sample_date'])['amount'].sum().reset_index()
    
    # Create and display the heatmap
    fig = create_activity_heatmap(heatmap_data, AVAILABLE_METRICS[selected_metric])
    st.plotly_chart(fig, use_container_width=True)


    # Add grantee impact visualization
    #st.header("Stylus Sprint Grantee Impact")
    #st.markdown("""
    #This Sankey diagram shows how Stylus Sprint grantees' work is being used across the ecosystem:
    #- Left side: Stylus Sprint grantees
    #- Right side: Projects using grantee packages
    #- Flow width: Number of dependencies
    #- Color coding: Blue for grantees, Orange for dependent projects
    #""")
    
    # Load dependency data
    #dependency_data = load_data(DATA_PATHS["downstream_dependencies"])
    #dependency_data = filter_data_by_time_window(dependency_data, time_window)
    
    # Create and display the Sankey diagram
    #fig = create_grantee_impact_sankey(dependency_data)
    #st.plotly_chart(fig, use_container_width=True)

    