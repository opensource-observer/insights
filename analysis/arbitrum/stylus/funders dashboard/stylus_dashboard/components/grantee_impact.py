import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ..config import DATA_PATHS
from ..utils.data_processing import load_data

def create_sunburst_data(df):
    """Create data for sunburst chart showing owner -> package -> dependent relationships."""
    # Create hierarchical data structure
    sunburst_data = []
    
    # Add root node
    sunburst_data.append({
        'ids': ['root'],
        'labels': ['All'],
        'parents': [''],
        'values': [len(df)]
    })
    
    # Add owner level
    for owner in df['package_owner_artifact_namespace'].unique():
        owner_data = df[df['package_owner_artifact_namespace'] == owner]
        sunburst_data.append({
            'ids': [f'owner_{owner}'],
            'labels': [owner],
            'parents': ['root'],
            'values': [len(owner_data)]
        })
        
        # Add package level
        for package in owner_data['to_package_artifact_name'].unique():
            package_data = owner_data[owner_data['to_package_artifact_name'] == package]
            sunburst_data.append({
                'ids': [f'package_{package}'],
                'labels': [package],
                'parents': [f'owner_{owner}'],
                'values': [len(package_data)]
            })
            
            # Add dependent level
            for _, row in package_data.iterrows():
                dependent = f"{row['from_artifact_namespace']}/{row['from_artifact_name']}"
                sunburst_data.append({
                    'ids': [f'dependent_{dependent}'],
                    'labels': [dependent],
                    'parents': [f'package_{package}'],
                    'values': [1]
                })
    
    # Convert to DataFrame and ensure all lists are properly flattened
    sunburst_df = pd.DataFrame({
        'ids': [item for sublist in [d['ids'] for d in sunburst_data] for item in sublist],
        'labels': [item for sublist in [d['labels'] for d in sunburst_data] for item in sublist],
        'parents': [item for sublist in [d['parents'] for d in sunburst_data] for item in sublist],
        'values': [item for sublist in [d['values'] for d in sunburst_data] for item in sublist]
    })
    
    return sunburst_df

def render_grantee_impact():
    """Render the Stylus Sprint grantee impact visualization."""
    st.header("Project Adoption & Dependencies")
    
    st.markdown("""
    This visualization shows the hierarchical relationship between project owners, their packages, and the projects that depend on them.
    Use the filters below to explore specific parts of the dependency network.
    """)
    
    st.markdown("""
    **How to use the sunburst chart:**
    - Click on any segment to zoom in and see its details
    - Double-click to zoom out
    - Hover over segments to see detailed information
    - The chart shows three levels: Owner → Package → Dependent Repository
    """)

    st.info("""
    This visualization tracks downstream dependencies of packages developed by Stylus grantees. As projects progress through their grant life cycle 
    and meet milestones, this view will be refined to focus on packages specifically developed and maintained as part of the Stylus sprint program.
    """)
    
    # Load dependency data
    dependency_data = load_data(DATA_PATHS["downstream_dependencies"])
    
    # Get unique project owners
    project_owners = sorted(dependency_data['package_owner_artifact_namespace'].unique())
    
    # Create filters
    col1, col2 = st.columns(2)
    
    with col1:
        selected_owner = st.selectbox(
            "Select Project Owner",
            options=["All"] + list(project_owners),
            index=0
        )
    
    with col2:
        min_deps = st.number_input(
            "Minimum Number of Dependencies",
            min_value=1,
            value=1
        )
    
    # Filter data based on selection
    if selected_owner != "All":
        filtered_data = dependency_data[dependency_data['package_owner_artifact_namespace'] == selected_owner]
    else:
        filtered_data = dependency_data
    
    # Apply min_deps filter
    package_dep_counts = filtered_data.groupby(['to_package_artifact_name']).size()
    packages_with_min_deps = package_dep_counts[package_dep_counts >= min_deps].index
    filtered_data = filtered_data[filtered_data['to_package_artifact_name'].isin(packages_with_min_deps)]

    # Add summary statistics
    st.subheader("Summary Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Project Owners",
            len(filtered_data['package_owner_artifact_namespace'].unique())
        )
    
    with col2:
        st.metric(
            "Total Packages",
            len(filtered_data['to_package_artifact_name'].unique())
        )
    
    with col3:
        st.metric(
            "Total Dependent Projects",
            filtered_data.groupby(['from_artifact_namespace', 'from_artifact_name']).ngroups
        ) 
    
    # Create sunburst data
    sunburst_data = create_sunburst_data(filtered_data)
    
    # Create sunburst chart
    fig = go.Figure(go.Sunburst(
        ids=sunburst_data['ids'],
        labels=sunburst_data['labels'],
        parents=sunburst_data['parents'],
        values=sunburst_data['values'],
        branchvalues="total",
        maxdepth=3
    ))
    
    fig.update_layout(
        height=800,
        title="Dependency Hierarchy: Owner → Package → Dependent",
        sunburstcolorway=["#636efa","#ef553b","#00cc96"],
        extendsunburstcolors=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
