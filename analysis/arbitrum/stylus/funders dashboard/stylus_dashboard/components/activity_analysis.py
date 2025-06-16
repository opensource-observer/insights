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
        
    # Group by grantee, package, and dependent project to get dependency counts
    impact_data = df.groupby(['package_owner_artifact_namespace', 'to_package_artifact_name', 'from_artifact_namespace', 'from_artifact_name']).size().reset_index(name='dependency_count')
    
    # Get unique values for each step
    grantees = impact_data['package_owner_artifact_namespace'].unique()
    packages = impact_data['to_package_artifact_name'].unique()
    dependents = impact_data.apply(lambda x: f"{x['from_artifact_namespace']}/{x['from_artifact_name']}", axis=1).unique()
    
    # Create node labels (combine all three steps)
    node_labels = list(grantees) + list(packages) + list(dependents)
    
    # Create source and target indices for first step (grantees to packages)
    source_indices_step1 = [list(grantees).index(grantee) for grantee in impact_data['package_owner_artifact_namespace']]
    target_indices_step1 = [len(grantees) + list(packages).index(pkg) for pkg in impact_data['to_package_artifact_name']]
    
    # Create source and target indices for second step (packages to dependents)
    source_indices_step2 = [len(grantees) + list(packages).index(pkg) for pkg in impact_data['to_package_artifact_name']]
    target_indices_step2 = [len(grantees) + len(packages) + list(dependents).index(f"{ns}/{name}") 
                          for ns, name in zip(impact_data['from_artifact_namespace'], impact_data['from_artifact_name'])]
    
    # Combine the steps
    source_indices = source_indices_step1 + source_indices_step2
    target_indices = target_indices_step1 + target_indices_step2
    values = list(impact_data['dependency_count']) * 2  # Duplicate values for both steps
    
    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = node_labels,
            color = ["#1f77b4"] * len(grantees) + ["#2ca02c"] * len(packages) + ["#ff7f0e"] * len(dependents)  # Different colors for each step
        ),
        link = dict(
            source = source_indices,
            target = target_indices,
            value = values,
            color = ["rgba(31, 119, 180, 0.4)"] * len(source_indices)  # Semi-transparent blue for flows
        )
    )])
    
    # Update layout
    fig.update_layout(
        title_text="Stylus Sprint Grantee Impact",
        font_size=10,
        height=2000
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
    """)
    
    # Load project attributes first
    project_attributes = pd.read_csv(DATA_PATHS["project_attributes"])
    
    # Get unique values for each attribute type
    onchain_statuses = sorted(project_attributes['onchain_status'].unique())
    stylus_usages = sorted(project_attributes['stylus_usage'].unique())
    origins = sorted(project_attributes['origin'].unique())
    all_categories = sorted(list(set([cat.strip() for cats in project_attributes['categories'].fillna('').str.split(',') for cat in cats if cat.strip()])))
    
    st.info("""
    **Note:** The metrics on this page are measured at the GitHub organization level, not just the specific repositories involved in the Stylus Sprint. This means:
    - For projects using a monorepo structure, all activity in that repository is included
    - For projects with multiple repositories, activity across all repositories in their organization is included
    - These metrics may include work unrelated to Stylus Sprint
    
    For repository-specific insights by project, please see the project deep dive section.
    """)

    # Create attribute filters
    st.subheader("Filter by Project Attributes")
    
    # Create filter columns
    col1, col2 = st.columns(2)
    
    with col1:
        selected_onchain = st.multiselect(
            "Onchain Component",
            options=onchain_statuses,
            default=onchain_statuses,
            help="Does the project write to or read from the blockchain?"
        )
        selected_stylus = st.multiselect(
            "Stylus Usage",
            options=stylus_usages,
            default=stylus_usages,
            help="Contract logic or computation on Stylus (Direct)"
        )
    
    with col2:
        selected_origin = st.multiselect(
            "Origin",
            options=origins,
            default=origins,
            help="Project with working product on other chains expanding support to Stylus (Established) versus project was conceived specifically for Arbitrum Stylus (Stylus-Native)"
        )
        selected_categories = st.multiselect(
            "Categories",
            options=all_categories,
            default=all_categories,
            help="Project Type / Primary Function"
        )
    
    # Validate that at least one option is selected for each filter
    if not selected_onchain or not selected_stylus or not selected_origin or not selected_categories:
        st.warning("Please select at least one option for each filter category to view the analysis.")
        return
    
    # Filter projects based on selected attributes
    filtered_projects = project_attributes[
        project_attributes['onchain_status'].isin(selected_onchain) &
        project_attributes['stylus_usage'].isin(selected_stylus) &
        project_attributes['origin'].isin(selected_origin) &
        project_attributes['categories'].fillna('').apply(lambda x: any(cat in x for cat in selected_categories))
    ]['project_name'].tolist()
    
    # Display filtered projects
    with st.expander(f"View {len(filtered_projects)} Projects in Scope"):
        if filtered_projects:
            st.write("The following projects match your selected filters:")
            for project in sorted(filtered_projects):
                st.write(f"- {project}")
        else:
            st.warning("No projects match the selected filters. Please adjust your filter criteria.")
    
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
    
    # Filter data by selected projects
    df = df[df['project_name'].isin(filtered_projects)]
    
    # Aggregate data across all projects
    aggregated_df = df.groupby('sample_date')['amount'].sum().reset_index()
    aggregated_df = calculate_pct_change(aggregated_df)
    
    # Create and display the trend plot
    fig = create_developer_trend_plot(aggregated_df)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"### Project Activity Analysis ({time_window})")

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
    
    # Filter heatmap data by selected projects
    heatmap_data = heatmap_data[heatmap_data['project_name'].isin(filtered_projects)]
    
    # Aggregate data to handle duplicates
    heatmap_data = heatmap_data.groupby(['display_name', 'sample_date'])['amount'].sum().reset_index()
    
    # Create and display the heatmap
    fig = create_activity_heatmap(heatmap_data, AVAILABLE_METRICS[selected_metric])
    st.plotly_chart(fig, use_container_width=True)

    